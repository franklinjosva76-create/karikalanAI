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
  • Fixed Crawl4AI thread executor: pool.submit(asyncio.run, _crawl()) was passing
    an already-created coroutine object cross-thread (not thread-safe); fixed to
    pool.submit(lambda: asyncio.run(_crawl())) so the coroutine is created
    inside the worker thread where it will run.
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


# ═══════════════════════════════════════════════════════════════════════
# FALLBACK IN-MEMORY VECTOR STORE
# (used only when chromadb is not installed)
# ═══════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════
# KARIKALAN ENGINE
# ═══════════════════════════════════════════════════════════════════════

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
                    pos = text.rfind(sep, start + max_chars // 2, end
