"""
கரிகாலன் AI (Karikalan AI) — Core Engine v3.1
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


class _Collection:
    def __init__(self):
        self._docs = {}

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
        scored = sorted(self._docs.items(), key=lambda kv: self._score(query, kv[1]), reverse=True)
        top = [doc for _, doc in scored[:n_results]]
        return {"documents": [top]}

    def delete(self):
        self._docs = {}

    def peek(self, limit=1):
        items = list(self._docs.values())[:limit]
        return {"documents": [items]}


class _InMemoryClient:
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


class KarikalanEngine:
    SCRAPER_API_BASE = "https://api.scraperapi.com"
    MIN_TEXT_LENGTH  = 100
    DB_PATH          = os.path.join(os.path.dirname(__file__), "..", "data", "zeravane_db")

    def __init__(self):
        self.gemini_api_key  = self._get_secret("GEMINI_API_KEY") or self._get_secret("GOOGLE_API_KEY")
        self.groq_api_key    = self._get_secret("GROQ_API_KEY",    default="")
        self.aiml_api_key    = self._get_secret("AIML_API_KEY",    default="")
        self.scraper_api_key = self._get_secret("SCRAPER_API_KEY", default="")
        self.github_token    = self._get_secret("GITHUB_TOKEN",    default="")
        self.ollama_base     = self._get_secret("OLLAMA_BASE_URL", default="http://localhost:11434")
        self.ollama_model    = self._get_secret("OLLAMA_MODEL",    default="qwen2.5-coder:7b")

        self.gemini_enabled  = bool(self.gemini_api_key) and GEMINI_AVAILABLE
        self.groq_enabled    = bool(self.groq_api_key)
        self.aiml_enabled    = bool(self.aiml_api_key)
        self.scraper_enabled = bool(self.scraper_api_key)
        self.ollama_enabled  = self._check_ollama()

        self.client     = None
        self.model_name = "gemini-2.5-flash"
        if self.gemini_enabled:
            try:
                self.client = genai.Client(api_key=self.gemini_api_key)
            except Exception as e:
                print(f"[KarikalanEngine] Gemini init error: {e}")
                self.gemini_enabled = False

        self.chroma_client      = self._init_chroma()
        self._cached_url        = None
        self._cached_collection = "zeravane_cache"
        self.conversation_memory = []
        self.max_memory_turns    = 10

    def _get_secret(self, key: str, default=None):
        try:
            import streamlit as st
            if hasattr(st, "secrets") and key in st.secrets:
                return st.secrets[key]
        except Exception:
            pass
        return os.environ.get(key) or default

    def _init_chroma(self):
        if CHROMADB_AVAILABLE:
            try:
                os.makedirs(self.DB_PATH, exist_ok=True)
                client = chromadb.PersistentClient(path=self.DB_PATH)
                print(f"[KarikalanEngine] ✅ Persistent ChromaDB at {self.DB_PATH}")
                return client
            except Exception as e:
                print(f"[KarikalanEngine] ChromaDB init failed: {e}")
        return _InMemoryClient()

    def _check_ollama(self) -> bool:
        try:
            r = requests.get(f"{self.ollama_base}/api/tags", timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    @staticmethod
    def _is_safe_url(url: str) -> bool:
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return False
            hostname = parsed.hostname or parsed.netloc.split(":")[0]
            if not hostname or hostname in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
                return False
            try:
                ip = ipaddress.ip_address(hostname)
                if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                    return False
            except ValueError:
                pass
            return True
        except Exception:
            return False

    def _scrape_crawl4ai(self, url: str) -> str:
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
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
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
        if not self._is_safe_url(url):
            return "Error: URL failed SSRF safety check"
        try:
            params = {"api_key": self.scraper_api_key, "url": url, "render": "true", "country_code": "us"}
            response = requests.get(self.SCRAPER_API_BASE, params=params, timeout=60, stream=True)
            content = b""
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > 2 * 1024 * 1024: break
            if response.status_code == 200:
                soup = BeautifulSoup(content.decode("utf-8", errors="ignore"), "html.parser")
                for el in soup(["script", "style", "nav", "footer", "header", "noscript"]): el.extract()
                return re.sub(r"\s+", " ", soup.get_text(separator=" ")).strip()
            return f"Error: ScraperAPI status {response.status_code}"
        except Exception as e:
            return f"ScraperAPI_Error: {e}"

    def _scrape_requests(self, url: str) -> str:
        if not self._is_safe_url(url):
            return "Error: URL failed SSRF safety check"
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = requests.get(url, headers=headers, timeout=15, stream=True)
            content = b""
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > 2 * 1024 * 1024: break
            if response.status_code != 200:
                return f"Error: status {response.status_code}"
            soup = BeautifulSoup(content.decode("utf-8", errors="ignore"), "html.parser")
            for el in soup(["script", "style", "nav", "footer", "header", "noscript"]): el.extract()
            return re.sub(r"\s+", " ", soup.get_text(separator=" ")).strip()
        except Exception as e:
            return f"Requests_Error: {e}"

    def scrape_live_url(self, url: str) -> tuple:
        _err = ("Error:", "Crawl4AI_Error:", "ScraperAPI_Error:", "Requests_Error:")
        result = self._scrape_crawl4ai(url)
        if result and len(result) >= self.MIN_TEXT_LENGTH and not any(result.startswith(p) for p in _err):
            return result, "🟢 Crawl4AI (Free · Unlimited)"
        if self.scraper_enabled:
            result = self._scrape_scraper_api(url)
            if result and len(result) >= self.MIN_TEXT_LENGTH and not any(result.startswith(p) for p in _err):
                return result, "🔵 ScraperAPI (JS Rendering · Proxies)"
        result = self._scrape_requests(url)
        return result, "⚪ Standard Requests (Plain HTML)"

    def chunk_text(self, text: str, max_chars: int = 3000, overlap: int = 400) -> list:
        if len(text) <= max_chars:
            return [text]
        chunks, start = [], 0
        while start < len(text):
            end = min(start + max_chars, len(text))
            if end < len(text):
                for sep in ("\n\n", "\n", ". ", " "):
                    pos = text.rfind(sep, start + max_chars // 2, end)
                    if pos != -1:
                        end = pos + len(sep)
                        break
            chunks.append(text[start:end])
            if end >= len(text): break
            start = end - overlap
        return chunks

    def refresh_vector_index(self, collection_name: str, text_chunks: list) -> bool:
        try:
            try: self.chroma_client.delete_collection(name=collection_name)
            except Exception: pass
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
        try:
            collection = self.chroma_client.get_collection(name=collection_name)
            available = collection.count()
            if available == 0: return ""
            n = min(n_results, available)
            results = collection.query(query_texts=[query], n_results=n)
            docs = []
            if results and "documents" in results:
                for sublist in results["documents"]: docs.extend(sublist)
            return "\n\n---\n\n".join(docs)
        except Exception as e:
            print(f"[KarikalanEngine] Vector query error: {e}")
            return ""

    def add_to_memory(self, role: str, content: str):
        self.conversation_memory.append({"role": role, "content": content})
        max_msgs = self.max_memory_turns * 2
        if len(self.conversation_memory) > max_msgs:
            self.conversation_memory = self.conversation_memory[-max_msgs:]

    def get_memory_context(self, exclude_last_n: int = 0) -> str:
        history = self.conversation_memory
        if exclude_last_n > 0: history = history[:-exclude_last_n]
        if not history: return ""
        lines = []
        for msg in history:
            role_label = "User" if msg["role"] == "user" else "Assistant"
            content = msg["content"]
            if len(content) > 800:
                truncated = content[:800]
                last_period = truncated.rfind(". ")
                content = truncated[:last_period + 1] if last_period > 400 else truncated + "..."
            lines.append(f"{role_label}: {content}")
        return "\n".join(lines)

    def clear_memory(self):
        self.conversation_memory = []

    def _infer(self, system_instruction: str, prompt: str, use_memory: bool = False) -> tuple:
        if use_memory:
            self.add_to_memory("user", prompt)
        history_for_provider = self.conversation_memory[:-1] if use_memory else []
        last_error = "No providers configured"

        if self.gemini_enabled and self.client:
            try:
                mem = self.get_memory_context(exclude_last_n=1) if use_memory else ""
                memory_prefix = f"=== CONVERSATION HISTORY ===\n{mem}\n\n=== CURRENT QUERY ===\n" if mem else ""
                full_prompt = memory_prefix + prompt
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=full_prompt,
                    config=genai_types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.2),
                )
                text = response.text
                if use_memory: self.add_to_memory("assistant", text)
                return text, "⚡ Gemini 2.5 Flash"
            except Exception as e:
                last_error = str(e)

        if self.groq_enabled:
            try:
                groq_messages = [{"role": "system", "content": system_instruction}]
                groq_messages.extend(history_for_provider)
                groq_messages.append({"role": "user", "content": prompt})
                resp = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.groq_api_key}", "Content-Type": "application/json"},
                    json={"model": "llama-3.3-70b-versatile", "messages": groq_messages, "temperature": 0.2, "max_tokens": 4096},
                    timeout=45,
                )
                if resp.status_code == 200:
                    text = resp.json()["choices"][0]["message"]["content"]
                    if use_memory: self.add_to_memory("assistant", text)
                    return text, "🟣 Groq (llama-3.3-70b)"
                last_error = f"Groq HTTP {resp.status_code}"
            except Exception as e:
                last_error = str(e)

        if self.ollama_enabled:
            try:
                ollama_prompt = f"System: {system_instruction}\n\n"
                if use_memory and history_for_provider:
                    ollama_prompt += f"Conversation history:\n{self.get_memory_context(exclude_last_n=1)}\n\n"
                ollama_prompt += f"User: {prompt}\n\nAssistant:"
                resp = requests.post(
                    f"{self.ollama_base}/api/generate",
                    json={"model": self.ollama_model, "prompt": ollama_prompt, "stream": False, "options": {"temperature": 0.2}},
                    timeout=120,
                )
                if resp.status_code == 200:
                    text = resp.json().get("response", "")
                    if use_memory: self.add_to_memory("assistant", text)
                    return text, f"🖥️ Ollama ({self.ollama_model})"
            except Exception as e:
                last_error = str(e)

        if use_memory and self.conversation_memory and self.conversation_memory[-1]["role"] == "user":
            self.conversation_memory.pop()
        return f"❌ Pipeline Failed: {last_error}", "❌ Failure"

    def scrape_multiple_urls(self, urls: list) -> tuple:
        merged_chunks = []
        summary = []
        collection_id = "zeravane_multi_url"
        _err = ("Error:", "Crawl4AI_Error:", "ScraperAPI_Error:", "Requests_Error:")

        for url in urls:
            url = url.strip()
            if not url: continue
            raw, method = self.scrape_live_url(url)
            if raw and len(raw) >= self.MIN_TEXT_LENGTH and not any(raw.startswith(p) for p in _err):
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

    def analyze_github_repo(self, github_url: str) -> tuple:
        try:
            match = re.search(r"github\.com/([^/]+)/([^/?\s#]+)", github_url)
            if not match: return "Invalid GitHub URL format.", {}
            owner, repo = match.group(1), match.group(2).rstrip("/")
            api_base = f"https://api.github.com/repos/{owner}/{repo}"
            headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "KarikalanAI/3.1"}
            if self.github_token: headers["Authorization"] = f"Bearer {self.github_token}"

            meta_resp = requests.get(api_base, headers=headers, timeout=15)
            if meta_resp.status_code != 200: return f"GitHub API Error {meta_resp.status_code}", {}
            meta = meta_resp.json()
            metadata = {
                "name": meta.get("full_name", ""), "description": meta.get("description", ""),
                "language": meta.get("language", "Unknown"), "stars": meta.get("stargazers_count", 0),
                "forks": meta.get("forks_count", 0), "open_issues": meta.get("open_issues_count", 0),
                "default_branch": meta.get("default_branch", "main"), "license": (meta.get("license") or {}).get("name", "N/A"),
                "updated_at": meta.get("updated_at", "N/A"), "topics": meta.get("topics", [])
            }
            combined = f"=== GITHUB REPO: {owner}/{repo} ===\nDescription: {metadata['description']}\nLanguage: {metadata['language']}\n"
            chunks = self.chunk_text(combined)
            self.refresh_vector_index(collection_name="zeravane_github", text_chunks=chunks)
            return combined, metadata
        except Exception as e:
            return f"GitHub_Error: {e}", {}

    def detect_tech_stack(self, scraped_content: str, target_url: str = "") -> str:
        system_instruction = "You are a tech stack detector. Output markdown lists with confidence scores."
        prompt = f"Target URL: {target_url}\nContent:\n{scraped_content[:5000]}"
        result, _ = self._infer(system_instruction, prompt)
        return result

    def generate_code_from_docs(self, docs_url: str, generation_request: str, language: str = "Python") -> tuple:
        raw_docs, method = self.scrape_live_url(docs_url)
        chunks = self.chunk_text(raw_docs)
        self.refresh_vector_index(collection_name="zeravane_codegen", text_chunks=chunks)
        context = self.query_vector_context(collection_name="zeravane_codegen", query=generation_request)
        system_instruction = f"Generate precise {language} production code."
        prompt = f"Doc Context:\n{context}\n\nRequest: {generation_request}"
        code, model = self._infer(system_instruction, prompt)
        return code, method, model

    def execute_live_agent_query(self, user_query: str, target_url: str = None, force_rescrape: bool = False, use_memory: bool = True) -> tuple:
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
