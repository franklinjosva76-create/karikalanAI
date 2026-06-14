"""
கரிகாலன் AI (Karikalan AI) — Core Engine v3.1
─────────────────────────────────────────────────────────────────────────────
v3.1 fixes over v3.0:
  • Fixed Crawl4AI: migrated from removed WebCrawler to AsyncWebCrawler
  • Fixed memory double-write: user messages no longer duplicated across turns
  • Fixed Gemini memory prefix: no longer echoes the current user query back
  • Fixed api.py import path: zeravaneai.backend.engine (was backend.engine)
  • Fixed scrape_multiple_urls: source labels now anchored at chunk boundaries
  • Fixed _infer use_memory=False leaving orphaned user entries in memory
  • Improved get_memory_context: truncates at sentence boundary, not mid-word
  • Improved chunk_text: respects paragraph/sentence boundaries where possible
"""

import os
import re
import json
import math
import asyncio
import ipaddress
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup

# ── Optional imports ────────────────────────────────────────────────────────

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

try:
    from google import genai
    from google.genai import types as genai_types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════════
# FALLBACK IN-MEMORY VECTOR STORE
# (used only when chromadb is not installed)
# ═══════════════════════════════════════════════════════════════════════════

class _Collection:
    """Lightweight in-memory vector store using word-overlap similarity."""

    def __init__(self):
        self._docs = {}  # id -> text

    def add(self, documents, ids, metadatas=None):
        for doc, did in zip(documents, ids):
            self._docs[did] = doc

    def count(self):
        return len(self._docs)

    def _score(self, query, doc):
        q_words = set(query.lower().split())
        d_words = doc.lower().split()
        if not q_words or not d_words:
            return 0.0
        d_freq = {}
        for w in d_words:
            d_freq[w] = d_freq.get(w, 0) + 1
        overlap = sum(d_freq.get(w, 0) for w in q_words)
        return overlap / (math.sqrt(len(q_words)) * math.sqrt(len(d_words)) + 1e-9)

    def query(self, query_texts, n_results=3):
        query = query_texts[0] if query_texts else ""
        scored = sorted(
            self._docs.items(),
            key=lambda kv: self._score(query, kv[1]),
            reverse=True,
        )
        top = [doc for _, doc in scored[:n_results]]
        return {"documents": [top]}

    def delete(self):
        self._docs = {}

    def peek(self, limit=1):
        items = list(self._docs.values())[:limit]
        return {"documents": [items]}


class _InMemoryClient:
    """Drop-in replacement for chromadb.PersistentClient when chromadb is absent."""

    def __init__(self):
        self._collections = {}

    def create_collection(self, name, **kwargs):
        col = _Collection()
        self._collections[name] = col
        return col

    def get_or_create_collection(self, name, **kwargs):
        if name not in self._collections:
            self._collections[name] = _Collection()
        return self._collections[name]

    def get_collection(self, name, **kwargs):
        if name not in self._collections:
            raise KeyError(f"Collection {name!r} not found")
        return self._collections[name]

    def delete_collection(self, name):
        self._collections.pop(name, None)

    def list_collections(self):
        return list(self._collections.keys())


# ═══════════════════════════════════════════════════════════════════════════
# KARIKALAN ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class KarikalanEngine:
    """
    Karikalan AI Core Engine v3.1

    LLM Tiers:
        Tier 1 — Gemini 2.5 Flash   (Google AI Studio — primary)
        Tier 2 — Groq  llama-3.3-70b (ultra-fast inference — fallback)
        Tier 3 — AI/ML API gpt-4o-mini (last cloud resort)
        Tier 4 — Ollama local       (always-on, zero-cost, offline fallback)

    Scraping Tiers:
        Tier 1 — Crawl4AI            (free, unlimited, LLM-optimised markdown)
        Tier 2 — ScraperAPI          (JS rendering, rotating proxies — optional)
        Tier 3 — Standard requests   (plain HTML fallback)

    Storage:
        Persistent ChromaDB          (survives restarts, stored in ./zeravane_db)
        Fallback: in-memory store    (when chromadb not installed)
    """

    SCRAPER_API_BASE = "https://api.scraperapi.com"
    MIN_TEXT_LENGTH  = 100
    DB_PATH          = os.path.join(os.path.dirname(__file__), "..", "data", "zeravane_db")

    # ── Init ────────────────────────────────────────────────────────────────

    def __init__(self):
        # API keys
        self.gemini_api_key  = self._get_secret("GEMINI_API_KEY") or self._get_secret("GOOGLE_API_KEY")
        self.groq_api_key    = self._get_secret("GROQ_API_KEY",    default="")
        self.aiml_api_key    = self._get_secret("AIML_API_KEY",    default="")
        self.scraper_api_key = self._get_secret("SCRAPER_API_KEY", default="")
        self.github_token    = self._get_secret("GITHUB_TOKEN",    default="")
        self.ollama_base     = self._get_secret("OLLAMA_BASE_URL", default="http://localhost:11434")
        self.ollama_model    = self._get_secret("OLLAMA_MODEL",    default="qwen2.5-coder:7b")

        # Feature flags
        self.gemini_enabled  = bool(self.gemini_api_key) and GEMINI_AVAILABLE
        self.groq_enabled    = bool(self.groq_api_key)
        self.aiml_enabled    = bool(self.aiml_api_key)
        self.scraper_enabled = bool(self.scraper_api_key)
        self.ollama_enabled  = self._check_ollama()

        # Gemini client
        self.client     = None
        self.model_name = "gemini-2.5-flash"
        if self.gemini_enabled:
            try:
                self.client = genai.Client(api_key=self.gemini_api_key)
            except Exception as e:
                print(f"[KarikalanEngine] Gemini init error: {e}")
                self.gemini_enabled = False

        # Persistent vector store
        self.chroma_client      = self._init_chroma()
        self._cached_url        = None
        self._cached_collection = "zeravane_cache"

        # Conversation memory: list of {"role": "user"|"assistant", "content": str}
        # FIX: memory is managed entirely inside _infer. execute_live_agent_query
        # no longer calls add_to_memory() to prevent double-writes.
        self.conversation_memory = []
        self.max_memory_turns    = 10  # keep last N turns (user + assistant = 2 each)

    # ── Secret resolution ───────────────────────────────────────────────────

    def _get_secret(self, key: str, default=None):
        try:
            import streamlit as st
            if hasattr(st, "secrets") and key in st.secrets:
                return st.secrets[key]
        except Exception:
            pass
        return os.environ.get(key) or default

    # ── ChromaDB initialisation ─────────────────────────────────────────────

    def _init_chroma(self):
        if CHROMADB_AVAILABLE:
            try:
                os.makedirs(self.DB_PATH, exist_ok=True)
                client = chromadb.PersistentClient(path=self.DB_PATH)
                print(f"[KarikalanEngine] ✅ Persistent ChromaDB at {self.DB_PATH}")
                return client
            except Exception as e:
                print(f"[KarikalanEngine] ChromaDB init failed, using in-memory fallback: {e}")
        else:
            print("[KarikalanEngine] chromadb not installed — using in-memory vector store")
        return _InMemoryClient()

    # ── Ollama health check ─────────────────────────────────────────────────

    def _check_ollama(self) -> bool:
        try:
            r = requests.get(
                f"{self._get_secret('OLLAMA_BASE_URL', 'http://localhost:11434')}/api/tags",
                timeout=3,
            )
            return r.status_code == 200
        except Exception:
            return False

    # ── SSRF protection ─────────────────────────────────────────────────────

    @staticmethod
    def _is_safe_url(url: str) -> bool:
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return False
            hostname = parsed.hostname or parsed.netloc.split(":")[0]
            if not hostname:
                return False
            if hostname in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
                return False
            try:
                ip = ipaddress.ip_address(hostname)
                if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                    return False
            except ValueError:
                pass  # hostname is a domain name, not an IP — safe
            return True
        except Exception:
            return False

    # ══════════════════════════════════════════════════════════════════════
    # SCRAPING — 3-Tier
    # ══════════════════════════════════════════════════════════════════════

    def _scrape_crawl4ai(self, url: str) -> str:
        """
        Tier 1 — Crawl4AI (free, unlimited, returns LLM-friendly markdown).
        FIX: migrated from removed WebCrawler to AsyncWebCrawler (crawl4ai >= 0.3).
        Runs the async crawler synchronously via asyncio.run().
        """
        if not self._is_safe_url(url):
            return "Error: URL failed SSRF safety check"
        try:
            from crawl4ai import AsyncWebCrawler

            async def _crawl():
                async with AsyncWebCrawler() as crawler:
                    result = await crawler.arun(url=url)
                    if result.success and result.markdown:
                        return result.markdown[:500_000]
                    return f"Crawl4AI_Error: {getattr(result, 'error_message', 'unknown error')}"

            # Use existing event loop if inside an async context (e.g. Streamlit),
            # otherwise create a new one.
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're inside an existing async context — use a thread executor
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(asyncio.run, _crawl())
                        return future.result(timeout=60)
                else:
                    return loop.run_until_complete(_crawl())
            except RuntimeError:
                return asyncio.run(_crawl())

        except ImportError:
            return "Crawl4AI_Error: crawl4ai not installed"
        except Exception as e:
            return f"Crawl4AI_Error: {e}"

    def _scrape_scraper_api(self, url: str) -> str:
        """Tier 2 — ScraperAPI (JS rendering, rotating proxies)."""
        if not self._is_safe_url(url):
            return "Error: URL failed SSRF safety check"
        try:
            params = {
                "api_key": self.scraper_api_key,
                "url": url,
                "render": "true",
                "country_code": "us",
            }
            response = requests.get(self.SCRAPER_API_BASE, params=params, timeout=60, stream=True)
            content = b""
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > 2 * 1024 * 1024:
                    break
            if response.status_code == 200:
                soup = BeautifulSoup(content.decode("utf-8", errors="ignore"), "html.parser")
                for el in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                    el.extract()
                return re.sub(r"\s+", " ", soup.get_text(separator=" ")).strip()
            return f"Error: ScraperAPI status {response.status_code}"
        except Exception as e:
            return f"ScraperAPI_Error: {e}"

    def _scrape_requests(self, url: str) -> str:
        """Tier 3 — Standard requests (plain HTML)."""
        if not self._is_safe_url(url):
            return "Error: URL failed SSRF safety check"
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            }
            response = requests.get(url, headers=headers, timeout=15, stream=True)
            content = b""
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > 2 * 1024 * 1024:
                    break
            if response.status_code != 200:
                return f"Error: status {response.status_code}"
            soup = BeautifulSoup(content.decode("utf-8", errors="ignore"), "html.parser")
            for el in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                el.extract()
            return re.sub(r"\s+", " ", soup.get_text(separator=" ")).strip()
        except Exception as e:
            return f"Requests_Error: {e}"

    def scrape_live_url(self, url: str) -> tuple:
        """
        3-Tier resilient scraping.
        Returns: (text, method_label)
        """
        _err = ("Error:", "Crawl4AI_Error:", "ScraperAPI_Error:", "Requests_Error:")

        # Tier 1 — Crawl4AI (always try first — free & unlimited)
        result = self._scrape_crawl4ai(url)
        if result and len(result) >= self.MIN_TEXT_LENGTH and not any(result.startswith(p) for p in _err):
            return result, "🟢 Crawl4AI (Free · Unlimited)"

        # Tier 2 — ScraperAPI (if key available)
        if self.scraper_enabled:
            result = self._scrape_scraper_api(url)
            if result and len(result) >= self.MIN_TEXT_LENGTH and not any(result.startswith(p) for p in _err):
                return result, "🔵 ScraperAPI (JS Rendering · Proxies)"

        # Tier 3 — Standard requests
        result = self._scrape_requests(url)
        return result, "⚪ Standard Requests (Plain HTML)"

    # ══════════════════════════════════════════════════════════════════════
    # RAG HELPERS
    # ══════════════════════════════════════════════════════════════════════

    def chunk_text(self, text: str, max_chars: int = 3000, overlap: int = 400) -> list:
        """
        Split text into overlapping chunks.
        FIX: tries to split at paragraph or sentence boundaries rather than
        cutting mid-word, which improves retrieval quality.
        """
        if len(text) <= max_chars:
            return [text]

        chunks, start = [], 0
        while start < len(text):
            end = min(start + max_chars, len(text))
            if end < len(text):
                # Prefer paragraph break, then sentence break, then word break
                for sep in ("\n\n", "\n", ". ", " "):
                    pos = text.rfind(sep, start + max_chars // 2, end)
                    if pos != -1:
                        end = pos + len(sep)
                        break
            chunks.append(text[start:end])
            if end >= len(text):
                break
            start = end - overlap
        return chunks

    def refresh_vector_index(self, collection_name: str, text_chunks: list) -> bool:
        """Wipe and rebuild a ChromaDB collection."""
        try:
            try:
                self.chroma_client.delete_collection(name=collection_name)
            except Exception:
                pass
            collection = self.chroma_client.get_or_create_collection(name=collection_name)
            batch_size = 100
            for i in range(0, len(text_chunks), batch_size):
                batch = text_chunks[i:i + batch_size]
                collection.add(
                    documents=batch,
                    ids=[f"chunk_{i + j}" for j in range(len(batch))],
                    metadatas=[{"index": i + j} for j in range(len(batch))],
                )
            return True
        except Exception as e:
            print(f"[KarikalanEngine] Vector index error: {e}")
            return False

    def query_vector_context(self, collection_name: str, query: str, n_results: int = 4) -> str:
        """Retrieve top-N relevant chunks from a collection."""
        try:
            collection = self.chroma_client.get_collection(name=collection_name)
            available = collection.count()
            if available == 0:
                return ""
            n = min(n_results, available)
            results = collection.query(query_texts=[query], n_results=n)
            docs = []
            if results and "documents" in results:
                for sublist in results["documents"]:
                    docs.extend(sublist)
            return "\n\n---\n\n".join(docs)
        except Exception as e:
            print(f"[KarikalanEngine] Vector query error: {e}")
            return ""

    # ══════════════════════════════════════════════════════════════════════
    # CONVERSATION MEMORY
    # ══════════════════════════════════════════════════════════════════════

    def add_to_memory(self, role: str, content: str):
        """Append a turn to conversation memory, trimming to max_memory_turns."""
        self.conversation_memory.append({"role": role, "content": content})
        max_msgs = self.max_memory_turns * 2
        if len(self.conversation_memory) > max_msgs:
            self.conversation_memory = self.conversation_memory[-max_msgs:]

    def get_memory_context(self, exclude_last_n: int = 0) -> str:
        """
        Format conversation history as a context string for the prompt.
        FIX: exclude_last_n lets callers exclude the most recent N messages
        (e.g. the current user query that was just appended) to avoid
        echoing it back in the memory prefix.
        """
        history = self.conversation_memory
        if exclude_last_n > 0:
            history = history[:-exclude_last_n]
        if not history:
            return ""
        lines = []
        for msg in history:
            role_label = "User" if msg["role"] == "user" else "Assistant"
            # Truncate at a sentence boundary for cleaner context
            content = msg["content"]
            if len(content) > 800:
                truncated = content[:800]
                last_period = truncated.rfind(". ")
                content = truncated[:last_period + 1] if last_period > 400 else truncated + "..."
            lines.append(f"{role_label}: {content}")
        return "\n".join(lines)

    def clear_memory(self):
        """Reset conversation history."""
        self.conversation_memory = []

    # ══════════════════════════════════════════════════════════════════════
    # 4-TIER LLM INFERENCE
    # ══════════════════════════════════════════════════════════════════════

    def _infer(self, system_instruction: str, prompt: str, use_memory: bool = False) -> tuple:
        """
        4-Tier LLM Fallback:
          Tier 1 — Gemini 2.5 Flash
          Tier 2 — Groq  llama-3.3-70b
          Tier 3 — AI/ML API gpt-4o-mini
          Tier 4 — Ollama (local, always-on)

        FIX: memory is now fully managed here.
          - The user message is appended to memory at the START of this call.
          - The assistant response is appended AFTER a successful response.
          - History passed to each provider excludes the current user message
            (it's already included explicitly as the final message).
          - If use_memory=False, nothing is written to memory.

        Returns: (response_text, model_label)
        """
        # Append the current user query to memory first
        if use_memory:
            self.add_to_memory("user", prompt)
        # History = everything except the message we just added
        history_for_provider = self.conversation_memory[:-1] if use_memory else []

        last_error = "No providers configured"

        # ── Tier 1 — Gemini ────────────────────────────────────────────
        if self.gemini_enabled and self.client:
            try:
                # FIX: exclude_last_n=1 so the current user query isn't echoed
                # back in the memory prefix — it's already in `prompt`.
                mem = self.get_memory_context(exclude_last_n=1) if use_memory else ""
                memory_prefix = (
                    f"=== CONVERSATION HISTORY ===\n{mem}\n\n=== CURRENT QUERY ===\n"
                    if mem else ""
                )
                full_prompt = memory_prefix + prompt
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=full_prompt,
                    config=genai_types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.2,
                    ),
                )
                text = response.text
                if use_memory:
                    self.add_to_memory("assistant", text)
                return text, "⚡ Gemini 2.5 Flash"
            except Exception as e:
                last_error = str(e)

        # ── Tier 2 — Groq ──────────────────────────────────────────────
        if self.groq_enabled:
            try:
                groq_messages = [{"role": "system", "content": system_instruction}]
                groq_messages.extend(history_for_provider)
                groq_messages.append({"role": "user", "content": prompt})
                resp = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.groq_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": groq_messages,
                        "temperature": 0.2,
                        "max_tokens": 4096,
                    },
                    timeout=45,
                )
                if resp.status_code == 200:
                    text = resp.json()["choices"][0]["message"]["content"]
                    if use_memory:
                        self.add_to_memory("assistant", text)
                    return text, "🟣 Groq (llama-3.3-70b)"
                last_error = f"Groq HTTP {resp.status_code}: {resp.text[:200]}"
            except Exception as e:
                last_error = str(e)

        # ── Tier 3 — AI/ML API ─────────────────────────────────────────
        if self.aiml_enabled:
            try:
                aiml_messages = [{"role": "system", "content": system_instruction}]
                aiml_messages.extend(history_for_provider)
                aiml_messages.append({"role": "user", "content": prompt})
                resp = requests.post(
                    "https://api.aimlapi.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.aiml_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "gpt-4o-mini",
                        "messages": aiml_messages,
                        "temperature": 0.2,
                        "max_tokens": 4096,
                    },
                    timeout=45,
                )
                if resp.status_code == 200:
                    text = resp.json()["choices"][0]["message"]["content"]
                    if use_memory:
                        self.add_to_memory("assistant", text)
                    return text, "🔶 AI/ML API (gpt-4o-mini)"
                last_error = f"AI/ML API HTTP {resp.status_code}: {resp.text[:200]}"
            except Exception as e:
                last_error = str(e)

        # ── Tier 4 — Ollama (local, always-on) ─────────────────────────
        if self.ollama_enabled:
            try:
                ollama_prompt = f"System: {system_instruction}\n\n"
                if use_memory and history_for_provider:
                    ollama_prompt += f"Conversation history:\n{self.get_memory_context(exclude_last_n=1)}\n\n"
                ollama_prompt += f"User: {prompt}\n\nAssistant:"

                resp = requests.post(
                    f"{self.ollama_base}/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": ollama_prompt,
                        "stream": False,
                        "options": {"temperature": 0.2, "num_predict": 4096},
                    },
                    timeout=120,
                )
                if resp.status_code == 200:
                    text = resp.json().get("response", "")
                    if use_memory:
                        self.add_to_memory("assistant", text)
                    return text, f"🖥️ Ollama ({self.ollama_model}) [Local]"
                last_error = f"Ollama HTTP {resp.status_code}"
            except Exception as e:
                last_error = str(e)

        # If use_memory=True but all tiers failed, remove the user message we added
        # so the history doesn't accumulate unanswered queries.
        if use_memory and self.conversation_memory and self.conversation_memory[-1]["role"] == "user":
            self.conversation_memory.pop()

        return f"❌ All LLM tiers failed. Last error: {last_error}", "❌ All Failed"

    # ══════════════════════════════════════════════════════════════════════
    # CAPABILITY 1 — MULTI-URL SCRAPING
    # ══════════════════════════════════════════════════════════════════════

    def scrape_multiple_urls(self, urls: list) -> tuple:
        """
        Scrape multiple URLs and merge into a unified RAG index.
        FIX: source labels are now prepended to each chunk individually so
        they're never split across chunk boundaries.
        Returns: (merged_chunks, scrape_summary)
        """
        merged_chunks = []
        summary = []
        collection_id = "zeravane_multi_url"
        _err = ("Error:", "Crawl4AI_Error:", "ScraperAPI_Error:", "Requests_Error:")

        for url in urls:
            url = url.strip()
            if not url:
                continue
            raw, method = self.scrape_live_url(url)
            ok = raw and len(raw) >= self.MIN_TEXT_LENGTH and not any(raw.startswith(p) for p in _err)
            if ok:
                # FIX: chunk first, then label each chunk — source tag never split
                raw_chunks = self.chunk_text(raw)
                for chunk in raw_chunks:
                    merged_chunks.append(f"[SOURCE: {url}]\n{chunk}")
                summary.append(f"✅ {url} — {method} ({len(raw_chunks)} chunks)")
            else:
                summary.append(f"❌ {url} — Failed: {raw[:80]}")

        if merged_chunks:
            self.refresh_vector_index(collection_name=collection_id, text_chunks=merged_chunks)
            self._cached_url = "__multi__"
            self._cached_collection = collection_id

        return merged_chunks, "\n".join(summary)

    # ══════════════════════════════════════════════════════════════════════
    # CAPABILITY 2 — GITHUB REPO ANALYZER
    # ══════════════════════════════════════════════════════════════════════

    def analyze_github_repo(self, github_url: str) -> tuple:
        """
        Analyze a public GitHub repository.
        Returns: (repo_content, metadata_dict)
        """
        try:
            match = re.search(r"github\.com/([^/]+)/([^/?\s#]+)", github_url)
            if not match:
                return "Invalid GitHub URL format.", {}

            owner, repo = match.group(1), match.group(2).rstrip("/")
            api_base = f"https://api.github.com/repos/{owner}/{repo}"
            headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "KarikalanAI/3.1"}
            if self.github_token:
                headers["Authorization"] = f"Bearer {self.github_token}"

            meta_resp = requests.get(api_base, headers=headers, timeout=15)
            metadata = {}
            if meta_resp.status_code == 200:
                meta = meta_resp.json()
                metadata = {
                    "name":           meta.get("full_name", ""),
                    "description":    meta.get("description", "No description"),
                    "language":       meta.get("language", "Unknown"),
                    "stars":          meta.get("stargazers_count", 0),
                    "forks":          meta.get("forks_count", 0),
                    "open_issues":    meta.get("open_issues_count", 0),
                    "topics":         meta.get("topics", []),
                    "default_branch": meta.get("default_branch", "main"),
                    "license":        (meta.get("license") or {}).get("name", "N/A"),
                    "updated_at":     meta.get("updated_at", "N/A"),
                }

            branch = metadata.get("default_branch", "main")

            # README
            readme_content = ""
            readme_resp = requests.get(
                f"{api_base}/readme",
                headers={**headers, "Accept": "application/vnd.github.v3.raw"},
                timeout=15,
            )
            if readme_resp.status_code == 200:
                readme_content = readme_resp.text[:10000]

            # File tree
            tree_content = ""
            tree_resp = requests.get(
                f"{api_base}/git/trees/{branch}?recursive=0",
                headers=headers,
                timeout=15,
            )
            if tree_resp.status_code == 200:
                tree_data = tree_resp.json().get("tree", [])
                files = [item["path"] for item in tree_data if item["type"] == "blob"][:60]
                tree_content = "\n".join(files)

            combined = (
                f"=== GITHUB REPO: {owner}/{repo} ===\n"
                f"Description: {metadata.get('description', 'N/A')}\n"
                f"Language: {metadata.get('language', 'N/A')}\n"
                f"Stars: {metadata.get('stars', 0):,} | Forks: {metadata.get('forks', 0):,}\n"
                f"Open Issues: {metadata.get('open_issues', 0)}\n"
                f"License: {metadata.get('license', 'N/A')}\n"
                f"Last Updated: {metadata.get('updated_at', 'N/A')}\n"
                f"Topics: {', '.join(metadata.get('topics', []))}\n\n"
                f"=== README ===\n{readme_content}\n\n"
                f"=== FILE TREE ===\n{tree_content}\n"
            )

            chunks = self.chunk_text(combined)
            self.refresh_vector_index(collection_name="zeravane_github", text_chunks=chunks)
            self._cached_url = github_url
            self._cached_collection = "zeravane_github"

            return combined, metadata

        except Exception as e:
            return f"GitHub_Error: {e}", {}

    # ══════════════════════════════════════════════════════════════════════
    # CAPABILITY 3 — TECH STACK DETECTION
    # ══════════════════════════════════════════════════════════════════════

    def detect_tech_stack(self, scraped_content: str, target_url: str = "") -> str:
        if not scraped_content or len(scraped_content) < 50:
            return "Insufficient content to detect tech stack."

        system_instruction = (
            "You are Karikalan AI (கரிகாலன் AI)'s tech stack detection engine. "
            "Analyze web content and identify the full technology stack with HIGH accuracy. "
            "Look for: meta tags, script imports, CSS conventions, API formats, "
            "framework-specific patterns, CDN URLs, build tool artifacts, error messages. "
            "Structure your response with these sections:\n"
            "🎨 Frontend | 🔧 Backend | 🗄️ Database | 🚀 Deployment | "
            "📦 Package Manager | 🎨 Styling | 🔗 APIs & Integrations | 🛠️ DevOps\n"
            "Rate each detection: [High/Medium/Low confidence]. "
            "Only list what you can infer from the content."
        )

        prompt = (
            f"Target URL: {target_url or 'Not provided'}\n\n"
            f"=== SCRAPED CONTENT (first 5000 chars) ===\n"
            f"{scraped_content[:5000]}\n\n"
            "Detect and report the complete technology stack."
        )

        result, _ = self._infer(system_instruction, prompt)
        return result

    # ══════════════════════════════════════════════════════════════════════
    # CAPABILITY 4 — CODE GENERATION FROM DOCS
    # ══════════════════════════════════════════════════════════════════════

    def generate_code_from_docs(self, docs_url: str, generation_request: str, language: str = "Python") -> tuple:
        """
        Scrape live documentation and generate production-ready code.
        Returns: (generated_code, scrape_method, model_used)
        """
        _err = ("Error:", "Crawl4AI_Error:", "ScraperAPI_Error:", "Requests_Error:")
        raw_docs, scrape_method = self.scrape_live_url(docs_url)
        scrape_ok = raw_docs and len(raw_docs) >= self.MIN_TEXT_LENGTH and not any(raw_docs.startswith(p) for p in _err)

        if scrape_ok:
            collection_id = "zeravane_codegen"
            chunks = self.chunk_text(raw_docs)
            self.refresh_vector_index(collection_name=collection_id, text_chunks=chunks)
            context = self.query_vector_context(collection_name=collection_id, query=generation_request, n_results=5)
        else:
            context = f"[Scraping failed: {raw_docs[:100]}]\nProceeding with training knowledge."

        system_instruction = (
            f"You are Karikalan AI (கரிகாலன் AI)'s code generation engine. "
            f"Generate production-ready {language} code from the provided documentation. "
            f"Requirements: proper error handling, type hints (where applicable), "
            f"clear docstrings, real-world patterns. "
            f"Base your code strictly on the documentation context when available. "
            f"Return ONLY clean, runnable code with inline comments. "
            f"End with a concise usage example."
        )

        prompt = (
            f"Documentation Source: {docs_url}\n"
            f"Target Language: {language}\n"
            f"Generation Request: {generation_request}\n\n"
            f"=== LIVE DOCUMENTATION CONTEXT ===\n{context}\n\n"
            f"Generate the {language} code now."
        )

        code, model_used = self._infer(system_instruction, prompt)
        return code, scrape_method, model_used

    # ══════════════════════════════════════════════════════════════════════
    # MAIN RAG PIPELINE
    # ══════════════════════════════════════════════════════════════════════

    def execute_live_agent_query(
        self,
        user_query: str,
        target_url: str = None,
        force_rescrape: bool = False,
        use_memory: bool = True,
    ) -> tuple:
        """
        Full RAG pipeline with 3-tier scraping + 4-tier LLM + conversation memory.

        FIX: memory management is now fully delegated to _infer().
        This method no longer calls add_to_memory() directly, which previously
        caused double user-message entries in conversation_memory.

        Returns: (response_text, context_payload, scrape_method, model_used)
        """
        context_payload = ""
        collection_id   = self._cached_collection
        scrape_method   = "N/A"
        _err = ("Error:", "Crawl4AI_Error:", "ScraperAPI_Error:", "Requests_Error:")

        # ── Scrape if URL provided ─────────────────────────────────────
        if target_url:
            url_changed = target_url != self._cached_url
            if url_changed or force_rescrape:
                raw_web_data, scrape_method = self.scrape_live_url(target_url)
                scrape_ok = (
                    raw_web_data
                    and len(raw_web_data) >= self.MIN_TEXT_LENGTH
                    and not any(raw_web_data.startswith(p) for p in _err)
                )
                if scrape_ok:
                    data_chunks = self.chunk_text(raw_web_data)
                    indexed = self.refresh_vector_index(collection_name=collection_id, text_chunks=data_chunks)
                    if indexed:
                        self._cached_url = target_url
                        context_payload  = self.query_vector_context(collection_name=collection_id, query=user_query)
                    else:
                        context_payload = "[Indexing Error]"
                else:
                    context_payload = f"[Scraping failed: {raw_web_data[:150]}]"
            else:
                scrape_method   = "✅ Cache Hit (URL unchanged)"
                context_payload = self.query_vector_context(collection_name=collection_id, query=user_query)

        web_context_available = (
            target_url
            and context_payload
            and not context_payload.startswith("[")
        )

        # ── Build system instruction ───────────────────────────────────
        if web_context_available:
            system_instruction = (
                "You are Karikalan AI (கரிகாலன் AI) v3.1, an advanced real-time web-aware developer agent. "
                "Analyse the live web documentation provided to answer the developer's query "
                "with precision. Prioritise live context over training knowledge. "
                "Provide clean, production-ready code solutions and detailed explanations. "
                "Cite documentation sources when drawing from the provided context. "
                "Remember the conversation history and maintain context across turns."
            )
        elif target_url:
            system_instruction = (
                f"You are Karikalan AI (கரிகாலன் AI) v3.1, an advanced developer agent. "
                f"The user provided URL: {target_url}. Scraping was attempted but failed. "
                f"Entering Offline Core Mode — answer using training knowledge about this "
                f"URL, domain, or framework. Be transparent about the data source. "
                f"Remember conversation history and maintain context across turns."
            )
        else:
            system_instruction = (
                "You are Karikalan AI (கரிகாலன் AI) v3.1, a premium full-stack programming assistant with "
                "expert-level knowledge across all major languages, frameworks, and architectures. "
                "Provide precise, production-ready solutions with best-practice patterns, "
                "thorough error handling, and clear explanations. "
                "Remember the conversation history and maintain context across turns."
            )

        fallback_context = (
            f"URL scraping unavailable for {target_url}. Using training knowledge."
            if target_url else "No web documentation retrieved — using base model knowledge."
        )

        prompt = (
            f"--- SYSTEM OVERVIEW ---\n"
            f"Karikalan AI Version: 3.1\n"
            f"Scrape Method: {scrape_method}\n"
            f"Target URL: {target_url or 'None'}\n"
            f"Context Available: {'Yes' if web_context_available else 'No'}\n"
            f"Memory Turns: {len(self.conversation_memory) // 2}\n\n"
            f"--- LIVE WEB DOCUMENTATION ---\n"
            f"{context_payload if context_payload else fallback_context}\n\n"
            f"--- DEVELOPER QUERY ---\n"
            f"{user_query}\n"
        )

        # NOTE: _infer() handles all memory writes (user + assistant)
        response_text, model_used = self._infer(system_instruction, prompt, use_memory=use_memory)
        return response_text, context_payload, scrape_method, model_used
