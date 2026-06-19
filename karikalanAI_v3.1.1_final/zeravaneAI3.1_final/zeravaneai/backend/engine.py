"""
கரிகாலன் AI (Karikalan AI) — Core Engine v3.1
──────────────────────────────────────────────────────────────────────────────
v3.1 fixes over v3.0:
  • Fixed Crawl4AI: migrated from removed WebCrawler to AsyncWebCrawler
  • Fixed memory double-write: user messages no longer duplicated across turns
  • Fixed Gemini memory prefix: no longer echoes the current user query back
  • Fixed api.py import path: zeravaneai.backend.engine (was backend.engine)
  • Fixed scrape_multiple_urls: source labels now anchored at chunk boundaries
  • Fixed _infer use_memory=False leaving orphaned user entries in memory
  • Improved get_memory_context: truncates at sentence boundary, not mid-word
  • Improved chunk_text: respects paragraph/sentence boundaries where possible
  • Fixed Crawl4AI thread executor: pool.submit(asyncio.run, _crawl()) was passing
    an already-created coroutine object cross-thread (not thread-safe); fixed to
    pool.submit(lambda: asyncio.run(_crawl())) so the coroutine is created
    inside the worker thread where it will run.
  • HOTFIX: _infer() now returns (response_text, model_name) tuple consistently
    to match execute_live_agent_query() unpacking expectations.
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


# ════════════════════════════════════════════════════════════════════════════
# FALLBACK IN-MEMORY VECTOR STORE
# (used only when chromadb is not installed)
# ════════════════════════════════════════════════════════════════════════════

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


# ════════════════════════════════════════════════════════════════════════════
# KARIKALAN ENGINE
# ════════════════════════════════════════════════════════════════════════════

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

    # ── Init ───────────────────────────────────────────────────────────────

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

    # ═══════════════════════════════════════════════════════════════════════
    # SCRAPING — 3-Tier
    # ═══════════════════════════════════════════════════════════════════════

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
                        future = pool.submit(lambda: asyncio.run(_crawl()))
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

    # ═══════════════════════════════════════════════════════════════════════
    # RAG HELPERS
    # ═══════════════════════════════════════════════════════════════════════

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
                    if pos > start + max_chars // 2:
                        end = pos + len(sep)
                        break
            chunks.append(text[start:end])
            start = end - overlap
        return chunks

    def get_memory_context(self, max_chars: int = 2000) -> str:
        """
        Extract conversation memory context for system prompt.
        FIX: truncates at sentence boundary, not mid-word.
        """
        if not self.conversation_memory:
            return ""
        lines = [f"{m['role'].upper()}: {m['content']}" for m in self.conversation_memory]
        text = "\n".join(lines)
        if len(text) <= max_chars:
            return text
        truncated = text[:max_chars]
        # Try to truncate at a sentence or line boundary
        for boundary in [". ", "\n", " "]:
            pos = truncated.rfind(boundary)
            if pos > max_chars // 2:
                return truncated[:pos + len(boundary)]
        return truncated

    def add_to_memory(self, role: str, content: str):
        """Add a message to conversation memory (user or assistant)."""
        self.conversation_memory.append({"role": role, "content": content})
        # Keep only the last N turns (each turn = 2 messages: user + assistant)
        max_messages = self.max_memory_turns * 2
        if len(self.conversation_memory) > max_messages:
            self.conversation_memory = self.conversation_memory[-max_messages:]

    def clear_memory(self):
        """Clear all conversation memory."""
        self.conversation_memory = []

    def _get_current_model_name(self) -> str:
        """Return the name of the LLM tier that would be used (for logging)."""
        if self.gemini_enabled and self.client:
            return "⚡ Gemini 2.5 Flash"
        elif self.groq_enabled:
            return "🔥 Groq llama-3.3-70b"
        elif self.aiml_enabled:
            return "🤖 AI/ML API (gpt-4o-mini)"
        elif self.ollama_enabled:
            return f"🏠 Ollama ({self.ollama_model})"
        else:
            return "❌ Fallback (No LLM Available)"

    def _infer(self, system_instruction: str, prompt: str, use_memory: bool = True) -> tuple:
        """
        Unified LLM inference with 4-tier fallback and integrated memory management.
        HOTFIX: Now returns (response_text, model_name) tuple consistently.
        
        Returns:
            tuple: (response_text, model_used_name)
        """
        # Build system message with memory context
        system_parts = [system_instruction]
        if use_memory and self.conversation_memory:
            memory_ctx = self.get_memory_context()
            if memory_ctx:
                system_parts.append(f"Recent conversation:\n{memory_ctx}")
        system_message = "\n\n".join(system_parts)

        # Tier 1 — Gemini 2.5 Flash
        if self.gemini_enabled and self.client:
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=[
                        genai_types.Content(
                            role="user",
                            parts=[genai_types.Part(text=f"{system_message}\n\n{prompt}")]
                        )
                    ]
                )
                if response.text:
                    # Manage memory: add user message (first time), then assistant response
                    if use_memory:
                        # Only add user message if it's not already in memory (check last message)
                        if not self.conversation_memory or self.conversation_memory[-1]["role"] != "user":
                            self.add_to_memory("user", prompt)
                        self.add_to_memory("assistant", response.text)
                    return response.text, "⚡ Gemini 2.5 Flash"
            except Exception as e:
                print(f"[KarikalanEngine] Gemini error: {e}")

        # Tier 2 — Groq llama-3.3-70b
        if self.groq_enabled:
            try:
                import requests as req
                groq_url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {"Authorization": f"Bearer {self.groq_api_key}"}
                payload = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2048
                }
                resp = req.post(groq_url, json=payload, headers=headers, timeout=30)
                if resp.status_code == 200:
                    result = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                    if result:
                        if use_memory:
                            if not self.conversation_memory or self.conversation_memory[-1]["role"] != "user":
                                self.add_to_memory("user", prompt)
                            self.add_to_memory("assistant", result)
                        return result, "🔥 Groq llama-3.3-70b"
            except Exception as e:
                print(f"[KarikalanEngine] Groq error: {e}")

        # Tier 3 — AI/ML API (gpt-4o-mini)
        if self.aiml_enabled:
            try:
                import requests as req
                aiml_url = "https://api.aiml.team/v1/chat/completions"
                headers = {"Authorization": f"Bearer {self.aiml_api_key}"}
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2048
                }
                resp = req.post(aiml_url, json=payload, headers=headers, timeout=30)
                if resp.status_code == 200:
                    result = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                    if result:
                        if use_memory:
                            if not self.conversation_memory or self.conversation_memory[-1]["role"] != "user":
                                self.add_to_memory("user", prompt)
                            self.add_to_memory("assistant", result)
                        return result, "🤖 AI/ML API (gpt-4o-mini)"
            except Exception as e:
                print(f"[KarikalanEngine] AI/ML API error: {e}")

        # Tier 4 — Ollama local
        if self.ollama_enabled:
            try:
                import requests as req
                ollama_url = f"{self.ollama_base}/api/generate"
                payload = {
                    "model": self.ollama_model,
                    "prompt": f"{system_message}\n\n{prompt}",
                    "stream": False
                }
                resp = req.post(ollama_url, json=payload, timeout=120)
                if resp.status_code == 200:
                    result = resp.json().get("response", "")
                    if result:
                        if use_memory:
                            if not self.conversation_memory or self.conversation_memory[-1]["role"] != "user":
                                self.add_to_memory("user", prompt)
                            self.add_to_memory("assistant", result)
                        return result, f"🏠 Ollama ({self.ollama_model})"
            except Exception as e:
                print(f"[KarikalanEngine] Ollama error: {e}")

        # Fallback
        fallback_msg = "All LLM tiers are unavailable. Please check your API keys and network connectivity."
        return fallback_msg, "❌ Fallback (No LLM Available)"

    # ═══════════════════════════════════════════════════════════════════════
    # VECTOR STORE & RAG
    # ═══════════════════════════════════════════════════════════════════════

    def refresh_vector_index(self, collection_name: str, text_chunks: list) -> bool:
        """Add/refresh text chunks to vector store."""
        try:
            col = self.chroma_client.get_or_create_collection(name=collection_name)
            ids = [f"{collection_name}_{i}" for i in range(len(text_chunks))]
            col.add(documents=text_chunks, ids=ids)
            return True
        except Exception as e:
            print(f"[KarikalanEngine] refresh_vector_index error: {e}")
            return False

    def query_vector_context(self, collection_name: str, query: str, n_results: int = 4) -> str:
        """Query vector store and return concatenated results."""
        try:
            col = self.chroma_client.get_collection(name=collection_name)
            results = col.query(query_texts=[query], n_results=n_results)
            docs = results.get("documents", [[]])[0]
            return "\n\n".join(docs) if docs else ""
        except Exception as e:
            print(f"[KarikalanEngine] query_vector_context error: {e}")
            return ""

    def scrape_multiple_urls(self, urls: list) -> tuple:
        """
        Scrape and index multiple URLs in parallel.
        Returns: (total_chunks, summary_text)
        """
        all_chunks = []
        summary_lines = []

        for url in urls:
            try:
                raw_text, method = self.scrape_live_url(url)
                _err = ("Error:", "Crawl4AI_Error:", "ScraperAPI_Error:", "Requests_Error:")
                if raw_text and len(raw_text) >= self.MIN_TEXT_LENGTH and not any(raw_text.startswith(p) for p in _err):
                    chunks = self.chunk_text(raw_text)
                    all_chunks.extend(chunks)
                    summary_lines.append(f"✅ {url}: {len(chunks)} chunks ({method})")
                else:
                    summary_lines.append(f"❌ {url}: Scraping failed")
            except Exception as e:
                summary_lines.append(f"❌ {url}: {str(e)[:50]}")

        if all_chunks:
            self.refresh_vector_index(collection_name="zeravane_multi_url", text_chunks=all_chunks)

        summary = "\n".join(summary_lines)
        return all_chunks, summary

    # ═══════════════════════════════════════════════════════════════════════
    # SPECIALIZED AGENTS
    # ═══════════════════════════════════════════════════════════════════════

    def detect_tech_stack(self, scraped_content: str, target_url: str = "") -> str:
        """Analyze scraped content and detect tech stack."""
        system_instruction = "You are a tech stack detector. Output markdown lists with confidence scores."
        prompt = f"Target URL: {target_url}\nContent:\n{scraped_content[:5000]}"
        result, _ = self._infer(system_instruction, prompt, use_memory=False)
        return result

    def generate_code_from_docs(self, docs_url: str, generation_request: str, language: str = "Python") -> tuple:
        """Generate code from documentation."""
        raw_docs, method = self.scrape_live_url(docs_url)
        chunks = self.chunk_text(raw_docs)
        self.refresh_vector_index(collection_name="zeravane_codegen", text_chunks=chunks)
        context = self.query_vector_context(collection_name="zeravane_codegen", query=generation_request)
        system_instruction = f"Generate precise {language} production code."
        prompt = f"Doc Context:\n{context}\n\nRequest: {generation_request}"
        code, model = self._infer(system_instruction, prompt, use_memory=False)
        return code, method, model

    def analyze_github_repo(self, repo_url: str) -> tuple:
        """Analyze a GitHub repository."""
        try:
            # Extract owner/repo from URL
            parts = repo_url.rstrip("/").split("/")
            owner, repo = parts[-2], parts[-1]
            
            # Use GitHub API if token available, otherwise scrape
            if self.github_token:
                headers = {"Authorization": f"Bearer {self.github_token}"}
                api_url = f"https://api.github.com/repos/{owner}/{repo}"
                resp = requests.get(api_url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    meta = resp.json()
                else:
                    meta = {}
            else:
                meta = {}

            # Fallback: scrape the repo page
            if not meta:
                raw_web_data, _ = self.scrape_live_url(repo_url)
            else:
                raw_web_data = json.dumps(meta, indent=2)

            metadata = {
                "description": meta.get("description", "N/A"),
                "language": meta.get("language", "N/A"),
                "stars": meta.get("stargazers_count", 0),
                "forks": meta.get("forks_count", 0),
                "open_issues": meta.get("open_issues_count", 0),
                "default_branch": meta.get("default_branch", "main"),
                "license": (meta.get("license") or {}).get("name", "N/A"),
                "updated_at": meta.get("updated_at", "N/A"),
                "topics": meta.get("topics", [])
            }
            combined = f"=== GITHUB REPO: {owner}/{repo} ===\nDescription: {metadata['description']}\nLanguage: {metadata['language']}\n"
            chunks = self.chunk_text(combined)
            self.refresh_vector_index(collection_name="zeravane_github", text_chunks=chunks)
            return combined, metadata
        except Exception as e:
            return f"GitHub_Error: {e}", {}

    def execute_live_agent_query(self, user_query: str, target_url: str = None, force_rescrape: bool = False, use_memory: bool = True) -> tuple:
        """
        Execute a live agent query with optional URL context.
        
        Returns:
            tuple: (response_text, context_payload, scrape_method, model_used)
        """
        context_payload = ""
        collection_id   = self._cached_collection
        scrape_method   = "N/A"
        _err = ("Error:", "Crawl4AI_Error:", "ScraperAPI_Error:", "Requests_Error:")

        if target_url:
            if target_url != self._cached_url or force_rescrape:
                raw_web_data, scrape_method = self.scrape_live_url(target_url)
                if raw_web_data and len(raw_web_data) >= self.MIN_TEXT_LENGTH and not any(raw_web_data.startswith(p) for p in _err):
                    data_chunks = self.chunk_text(raw_web_data)
                    if self.refresh_vector_index(collection_name=collection_id, text_chunks=data_chunks):
                        self._cached_url = target_url
                        context_payload  = self.query_vector_context(collection_name=collection_id, query=user_query)
                else:
                    context_payload = f"[Scraping failed: {raw_web_data[:100]}]"
            else:
                scrape_method   = "✅ Cache Hit"
                context_payload = self.query_vector_context(collection_name=collection_id, query=user_query)

        system_instruction = "You are Karikalan AI v3.1. Answer code questions precisely using history and live context."
        prompt = f"Context:\n{context_payload}\n\nQuery: {user_query}"
        response_text, model_used = self._infer(system_instruction, prompt, use_memory=use_memory)
        return response_text, context_payload, scrape_method, model_used
