# ZeravaneAI v3.0 — Complete Technical Documentation
### For Product Testers & Contributors

---

> **What is ZeravaneAI?**
> An enterprise-level AI-powered coding assistant and agentic development platform. It can scrape live documentation from any website, understand it, remember your conversation, and answer developer questions — all powered by a 4-tier LLM fallback system that never runs out of credits.

---

## TABLE OF CONTENTS

1. Project Overview
2. Folder & File Structure
3. How the Whole System Works (Big Picture)
4. `engine.py` — Complete Breakdown (line by line)
5. `api.py` — FastAPI REST API Breakdown
6. `frontend/app.py` — Streamlit UI Breakdown
7. `streamlit_app.py` — Entry Point
8. `requirements.txt` — Dependencies Explained
9. `.env.example` — All Config Variables
10. `Dockerfile` — Container Setup
11. All Data Flows Explained
12. Key Concepts Explained Simply
13. How to Set Up & Run
14. What Each Tab Does (Tester Guide)
15. Common Errors & How to Fix Them

---

---

# 1. PROJECT OVERVIEW

ZeravaneAI is built around one core idea: **a developer should never be blocked by a rate limit or a missing API key.**

Every major system has a fallback:

```
LLM Fallback:
  Gemini 2.5 Flash  →  Groq  →  AI/ML API  →  Ollama (local, unlimited)

Scraping Fallback:
  Crawl4AI (free)  →  ScraperAPI  →  Standard requests

Vector DB Fallback:
  Persistent ChromaDB  →  In-memory store
```

If every cloud API fails at the same time, ZeravaneAI uses a model running on your own GPU (RTX 3060) via Ollama. The system never fully dies.

### What it can do:
- Answer any coding question (like a ChatGPT for developers)
- Scrape any documentation page and answer questions from it in real-time
- Remember the whole conversation (multi-turn memory)
- Scrape multiple URLs and merge them into one knowledge base
- Analyze any GitHub repository (README, file tree, metadata)
- Detect the tech stack of any website
- Generate production-ready code from live documentation
- Expose all features as a REST API

---

---

# 2. FOLDER & FILE STRUCTURE

```
zeravaneAI3.0/
│
├── streamlit_app.py          ← Entry point (run this to start the UI)
├── requirements.txt          ← All Python packages needed
├── Dockerfile                ← Docker container config
├── .env.example              ← Template for API keys
├── .gitignore                ← Files Git should ignore
├── README.md                 ← Quick-start guide
│
└── zeravaneai/               ← Main Python package
    ├── __init__.py           ← Makes zeravaneai a Python package
    │
    ├── backend/              ← All logic lives here
    │   ├── __init__.py
    │   ├── engine.py         ← THE BRAIN — all AI, scraping, RAG logic
    │   └── api.py            ← FastAPI REST API (exposes engine as HTTP)
    │
    ├── frontend/             ← The visual interface
    │   ├── __init__.py
    │   └── app.py            ← Streamlit UI (all 5 tabs)
    │
    └── data/
        └── zeravane_db/      ← ChromaDB stores vector data here
            (auto-created)
```

### Why this structure?
- `backend/` and `frontend/` are separated so in the future, the UI can be replaced with React without touching the engine
- `engine.py` has no Streamlit dependency — it works standalone or through the API
- `data/` is outside the code folders so the database persists even if you update the code

---

---

# 3. HOW THE WHOLE SYSTEM WORKS (Big Picture)

Here is the complete journey of a single user query:

```
User types: "How do I authenticate with the Stripe API?"
+ URL: "https://docs.stripe.com/api"

Step 1 — Frontend (app.py)
   User input is captured from the Streamlit text area

Step 2 — Engine called (engine.py → execute_live_agent_query)
   The main pipeline function receives: query + URL + memory flag

Step 3 — Memory
   The user's message is added to conversation_memory list

Step 4 — URL Check
   Is this URL already cached? No → proceed to scrape

Step 5 — Scraping (3-tier)
   Try Crawl4AI → if fails → try ScraperAPI → if fails → try requests
   Result: raw text content from the Stripe docs page

Step 6 — Chunking
   Long text is split into overlapping 3000-character chunks
   e.g., a 50,000 char page becomes ~17 chunks

Step 7 — Vector Indexing (ChromaDB)
   Each chunk is stored in ChromaDB with an ID
   ChromaDB converts text to numbers (embeddings) for similarity search

Step 8 — Vector Retrieval
   The user's query is compared to all chunks
   Top 4 most relevant chunks are retrieved

Step 9 — Prompt Assembly
   System instruction + retrieved context + user query = full prompt
   Conversation history is prepended if memory is on

Step 10 — LLM Inference (4-tier)
   Try Gemini 2.5 Flash → if rate limited → try Groq
   → if exhausted → try AI/ML API → if all fail → Ollama local

Step 11 — Response
   LLM answer is returned to frontend
   Answer + model used + scrape method shown to user
   Answer stored in conversation memory
```

---

---

# 4. ENGINE.PY — COMPLETE LINE-BY-LINE BREAKDOWN

`engine.py` is the most important file. It is 865 lines and contains all intelligence.

---

## 4.1 Module Docstring (Lines 1–17)

```python
"""
ZeravaneAI — Core Engine v3.0
Upgrades over v2.0:
  • Persistent ChromaDB vector store
  • 4-Tier LLM fallback
  • Conversation memory
  • Crawl4AI scraper tier
  ...
"""
```

**What this is:** A docstring (documentation string) at the top of the file. It doesn't run as code — it exists so any developer reading the file immediately understands what changed from the previous version. It's like a changelog inside the code itself.

---

## 4.2 Standard Library Imports (Lines 19–26)

```python
import os           # Read environment variables and file paths
import re           # Regular expressions — used to clean scraped text
import json         # Parse JSON responses from APIs
import math         # Used in the similarity scoring formula
import ipaddress    # Check if an IP address is private/public (SSRF protection)
import requests     # Make HTTP calls to LLM APIs and scraping services
from urllib.parse import urlparse    # Break a URL into parts (scheme, host, path)
from bs4 import BeautifulSoup        # Parse HTML — extract clean text from web pages
```

**Why each one matters:**
- `ipaddress` + `urlparse` are the security layer — they block attackers from using ZeravaneAI to call internal servers
- `BeautifulSoup` strips all the HTML clutter (scripts, navbars, footers) and gives just the readable text
- `requests` is how the app calls every external service (Gemini, Groq, ScraperAPI, Ollama)

---

## 4.3 Optional Imports with Try/Except (Lines 28–48)

```python
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
```

**What this does:** Tries to load environment variables from a `.env` file. If `python-dotenv` is not installed, it silently skips — the app still works, just reading from system environment variables instead.

```python
try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
```

**What this does:** Sets a flag. If `chromadb` is installed, `CHROMADB_AVAILABLE = True` and the app uses the real persistent database. If not, it falls back to the custom in-memory store built below. This is called a **graceful degradation** pattern — the app never crashes due to a missing package.

```python
try:
    from google import genai
    from google.genai import types as genai_types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
```

**Same pattern** for Gemini. If the `google-genai` package isn't installed, Gemini tier is skipped and the app falls to Groq.

---

## 4.4 The `_Collection` Class (Lines 56–95) — Fallback Vector Store

This class is a custom mini database that works like ChromaDB but with no external dependency.

```python
class _Collection:
    def __init__(self):
        self._docs = {}  # A dictionary: {"chunk_0": "text...", "chunk_1": "text..."}
```

**`_docs` is a Python dictionary** where:
- Key = chunk ID (e.g., `"chunk_0"`)
- Value = the actual text content of that chunk

```python
def add(self, documents, ids, metadatas=None):
    for doc, did in zip(documents, ids):
        self._docs[did] = doc
```

**`add()` method:** Takes a list of documents and a list of IDs, pairs them up using `zip()`, and stores them in `_docs`. The `metadatas` parameter is accepted but ignored (ChromaDB uses it, so we accept it to be compatible).

```python
def _score(self, query, doc):
    q_words = set(query.lower().split())    # Unique words in the query
    d_words = doc.lower().split()           # All words in the document
    if not q_words or not d_words:
        return 0.0
    d_freq = {}
    for w in d_words:
        d_freq[w] = d_freq.get(w, 0) + 1   # Count how many times each word appears
    overlap = sum(d_freq.get(w, 0) for w in q_words)  # How many query words are in doc
    return overlap / (math.sqrt(len(q_words)) * math.sqrt(len(d_words)) + 1e-9)
```

**`_score()` is the search algorithm.** This is a simplified TF-IDF cosine similarity:
- Convert both query and document to lowercase, split into words
- Count how many query words appear in the document
- Divide by a normalisation factor (square roots of both lengths) so longer documents don't automatically win
- The `1e-9` prevents division by zero
- Returns a float between 0.0 (no match) and a higher number (strong match)

**Example:** Query = "authentication token", Doc = "Use authentication tokens for API access"
- q_words = {"authentication", "token"}
- Both words found in doc → higher score

```python
def query(self, query_texts, n_results=3):
    query = query_texts[0] if query_texts else ""
    scored = sorted(
        self._docs.items(),
        key=lambda kv: self._score(query, kv[1]),
        reverse=True,
    )
    top = [doc for _, doc in scored[:n_results]]
    return {"documents": [top]}
```

**`query()` method:** Scores every single stored document against the query, sorts them highest-to-lowest, returns the top N. Returns data in the same format ChromaDB returns (`{"documents": [[...]]}`), so the rest of the code works the same regardless of which backend is used.

---

## 4.5 The `_InMemoryClient` Class (Lines 98–120) — Fallback DB Client

```python
class _InMemoryClient:
    def __init__(self):
        self._collections = {}   # {"collection_name": _Collection object}

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
        self._collections.pop(name, None)   # Remove if exists, do nothing if not
```

**What this is:** A fake version of the ChromaDB client that has all the same method names and return shapes. Every method in `ZeravaneEngine` calls `self.chroma_client.get_or_create_collection(...)` — it doesn't know or care whether it's talking to a real ChromaDB or this fake one. This is called the **adapter pattern**.

The `**kwargs` on every method means "accept any extra keyword arguments and ignore them" — ChromaDB methods accept extra params like `embedding_function=` that this simple version doesn't need.

---

## 4.6 `ZeravaneEngine` Class — Constants (Lines 154–156)

```python
class ZeravaneEngine:
    SCRAPER_API_BASE = "https://api.scraperapi.com"
    MIN_TEXT_LENGTH  = 100
    DB_PATH          = os.path.join(os.path.dirname(__file__), "..", "data", "zeravane_db")
```

**Class-level constants** (defined at class level, not inside `__init__`):
- `SCRAPER_API_BASE`: The URL all ScraperAPI requests go to
- `MIN_TEXT_LENGTH`: A scrape result shorter than 100 characters is considered a failure — it's probably an error message, not real content
- `DB_PATH`: Where ChromaDB stores its files. `os.path.dirname(__file__)` = folder of `engine.py`, then `..` goes up one level to `zeravaneai/`, then into `data/zeravane_db/`

---

## 4.7 `__init__` Method — Engine Startup (Lines 160–194)

```python
def __init__(self):
    # Load all API keys
    self.gemini_api_key  = self._get_secret("GEMINI_API_KEY") or self._get_secret("GOOGLE_API_KEY")
    self.groq_api_key    = self._get_secret("GROQ_API_KEY",    default="")
    self.aiml_api_key    = self._get_secret("AIML_API_KEY",    default="")
    self.scraper_api_key = self._get_secret("SCRAPER_API_KEY", default="")
    self.github_token    = self._get_secret("GITHUB_TOKEN",    default="")
    self.ollama_base     = self._get_secret("OLLAMA_BASE_URL", default="http://localhost:11434")
    self.ollama_model    = self._get_secret("OLLAMA_MODEL",    default="qwen2.5-coder:7b")
```

**Key loading:** `_get_secret` is called for each key. The `or` on the Gemini line means "try GEMINI_API_KEY first, if missing try GOOGLE_API_KEY" — so both naming conventions work.

```python
    # Feature flags — True/False booleans
    self.gemini_enabled  = bool(self.gemini_api_key) and GEMINI_AVAILABLE
    self.groq_enabled    = bool(self.groq_api_key)
    self.aiml_enabled    = bool(self.aiml_api_key)
    self.scraper_enabled = bool(self.scraper_api_key)
    self.ollama_enabled  = self._check_ollama()
```

`bool("")` = `False`, `bool("some_key")` = `True`. These flags control the entire fallback logic — if a tier's flag is False, it's completely skipped in `_infer()`.

Gemini requires BOTH a key AND the package installed: `bool(key) AND GEMINI_AVAILABLE`.

Ollama doesn't need a key — it uses `_check_ollama()` which actually pings `localhost:11434` to see if Ollama is running.

```python
    self.client     = None
    self.model_name = "gemini-2.5-flash"
    if self.gemini_enabled:
        try:
            self.client = genai.Client(api_key=self.gemini_api_key)
        except Exception as e:
            print(f"[ZeravaneEngine] Gemini init error: {e}")
            self.gemini_enabled = False
```

Creates the Gemini SDK client object. If this fails (bad key format, etc.), sets `gemini_enabled = False` so Tier 1 is skipped without crashing.

```python
    self.chroma_client    = self._init_chroma()
    self._cached_url      = None
    self._cached_collection = "zeravane_cache"

    self.conversation_memory = []
    self.max_memory_turns    = 10
```

- `_cached_url`: The URL last scraped. If a new query uses the same URL, we skip re-scraping.
- `_cached_collection`: Which ChromaDB collection is currently active. Default is `"zeravane_cache"`.
- `conversation_memory`: A plain Python list. Each item is `{"role": "user", "content": "..."}` or `{"role": "assistant", "content": "..."}`.
- `max_memory_turns = 10`: Keep maximum 10 back-and-forth exchanges (20 messages total).

---

## 4.8 `_get_secret()` Method (Lines 198–205)

```python
def _get_secret(self, key: str, default=None):
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.environ.get(key) or default
```

**Two-source secret resolution:**
1. First checks Streamlit Secrets (the secrets management system in Streamlit Cloud — for production deployment)
2. Falls back to OS environment variables (for local development with `.env` file)
3. If neither has it, returns `default`

This means the same code works locally (`.env` file) and on Streamlit Cloud (Secrets UI) without any changes.

---

## 4.9 `_init_chroma()` — ChromaDB Setup (Lines 209–220)

```python
def _init_chroma(self):
    if CHROMADB_AVAILABLE:
        try:
            os.makedirs(self.DB_PATH, exist_ok=True)    # Create folder if it doesn't exist
            client = chromadb.PersistentClient(path=self.DB_PATH)
            print(f"[ZeravaneEngine] ✅ Persistent ChromaDB at {self.DB_PATH}")
            return client
        except Exception as e:
            print(f"[ZeravaneEngine] ChromaDB init failed, using in-memory fallback: {e}")
    else:
        print("[ZeravaneEngine] chromadb not installed — using in-memory vector store")
    return _InMemoryClient()
```

`chromadb.PersistentClient(path=...)` creates a real ChromaDB instance that saves data to disk. Even if you restart the server, the indexed documents are still there. `exist_ok=True` means "don't throw an error if the folder already exists."

If anything goes wrong, the method falls through to `return _InMemoryClient()` — the fallback. The rest of the code never knows which one it got.

---

## 4.10 `_check_ollama()` — Local LLM Health Check (Lines 224–229)

```python
def _check_ollama(self) -> bool:
    try:
        r = requests.get(f"{self.ollama_base}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False
```

Makes a quick HTTP request to Ollama's `/api/tags` endpoint. If Ollama is running, this returns 200 and a list of available models. If it's not running (or the port is blocked), the request fails and returns `False`. The `timeout=3` means "give up after 3 seconds" — startup should be fast.

---

## 4.11 `_is_safe_url()` — SSRF Protection (Lines 233–252)

SSRF = Server-Side Request Forgery. An attacker could type `http://localhost:8000/admin` into the URL field and make ZeravaneAI call internal services on the same server. This method blocks that.

```python
@staticmethod
def _is_safe_url(url: str) -> bool:
    try:
        parsed = urlparse(url)

        # Only allow http and https — block file://, ftp://, etc.
        if parsed.scheme not in ("http", "https"):
            return False

        hostname = parsed.hostname or parsed.netloc.split(":")[0]
        if not hostname:
            return False

        # Block obvious localhost variants
        if hostname in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
            return False

        # If it looks like a raw IP address, check if it's private
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False
        except ValueError:
            pass    # Not an IP address — it's a domain name like "google.com" — that's fine

        return True
    except Exception:
        return False
```

`@staticmethod` means this method doesn't need `self` — it's a utility function attached to the class. Every single scraping method calls this before making any request.

Private IP ranges blocked: `192.168.x.x`, `10.x.x.x`, `172.16–31.x.x`, `127.x.x.x`.

---

## 4.12 Scraping Tier 1 — `_scrape_crawl4ai()` (Lines 258–277)

```python
def _scrape_crawl4ai(self, url: str) -> str:
    if not self._is_safe_url(url):
        return "Error: URL failed SSRF safety check"
    try:
        from crawl4ai import WebCrawler
        crawler = WebCrawler()
        crawler.warmup()                                    # Load Playwright browser
        result = crawler.run(url=url, word_count_threshold=10)
        if result.success and result.markdown:
            return result.markdown[:500_000]               # Max 500KB of content
        return f"Crawl4AI_Error: {result.error_message}"
    except ImportError:
        return "Crawl4AI_Error: crawl4ai not installed"
    except Exception as e:
        return f"Crawl4AI_Error: {e}"
```

**Why Crawl4AI is Tier 1:**
- Completely free, no API key, no rate limits
- Uses a real headless browser (Playwright) so it handles JavaScript-rendered pages
- Returns clean **Markdown** instead of raw HTML — much better for LLMs to understand
- `word_count_threshold=10` skips any page section with fewer than 10 words (nav items, tooltips, etc.)
- `[:500_000]` caps output at 500KB to protect memory

The `from crawl4ai import WebCrawler` is inside the function (not at the top of the file) — this is called a **lazy import**. If crawl4ai isn't installed, this specific error is caught and returns a string starting with `"Crawl4AI_Error:"`. The calling function `scrape_live_url()` then moves on to the next tier.

---

## 4.13 Scraping Tier 2 — `_scrape_scraper_api()` (Lines 279–303)

```python
params = {
    "api_key": self.scraper_api_key,
    "url": url,
    "render": "true",       # Use a headless browser (handles JS)
    "country_code": "us",   # Appear to be coming from the US
}
response = requests.get(self.SCRAPER_API_BASE, params=params, timeout=60, stream=True)
content = b""
for chunk in response.iter_content(chunk_size=8192):    # Read 8KB at a time
    content += chunk
    if len(content) > 2 * 1024 * 1024:                 # Stop at 2MB
        break
```

**Streaming download:** Instead of downloading the whole page at once (which could crash on very large pages), it downloads 8KB chunks at a time. If total content exceeds 2MB, it stops. This prevents memory overflow on huge pages.

After downloading, BeautifulSoup parses the HTML and removes useless elements:
```python
soup = BeautifulSoup(content.decode("utf-8", errors="ignore"), "html.parser")
for el in soup(["script", "style", "nav", "footer", "header", "noscript"]):
    el.extract()                                          # Remove these tags completely
text = re.sub(r"\s+", " ", soup.get_text(separator=" ")).strip()
```

`re.sub(r"\s+", " ", ...)` replaces all sequences of whitespace (spaces, newlines, tabs) with a single space — gives clean, readable text.

---

## 4.14 Scraping Tier 3 — `_scrape_requests()` (Lines 305–330)

Same as Tier 2 but without ScraperAPI. The `User-Agent` header is set to look like a real Chrome browser — many websites block requests without one:

```python
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 ..."
    )
}
```

This is the simplest tier — no proxy, no JS rendering, no API key. Works for most basic documentation sites.

---

## 4.15 `scrape_live_url()` — The 3-Tier Orchestrator (Lines 332–352)

```python
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
```

**Logic:** Each tier is tried in order. A result is considered successful only if:
1. It's not empty
2. It's at least 100 characters long (`MIN_TEXT_LENGTH`)
3. It doesn't start with any known error prefix

If Tier 1 fails, try Tier 2. If Tier 2 fails or isn't enabled, Tier 3 always runs (no success check — it's the last resort, we return whatever we got).

Returns a **tuple**: `(text_content, label_string)`. The label string is shown in the UI so users know which method was used.

---

## 4.16 `chunk_text()` — Text Splitting (Lines 358–369)

```python
def chunk_text(self, text: str, max_chars: int = 3000, overlap: int = 400) -> list:
    if len(text) <= max_chars:
        return [text]                           # Short text — return as single chunk
    chunks, start = [], 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break                               # Reached the end
        start += max_chars - overlap            # Move forward by (3000 - 400) = 2600 chars
    return chunks
```

**Why overlap?** Imagine a concept is explained starting at character 2900 of a page. Without overlap, it would be split between chunk 1 (ending at 3000) and chunk 2 (starting at 3000). The explanation would be incomplete in both chunks. With 400-character overlap, the tail of chunk 1 is repeated at the start of chunk 2, so the full concept is always contained within at least one chunk.

**Example:** A 10,000 character document becomes:
- Chunk 0: chars 0–3000
- Chunk 1: chars 2600–5600
- Chunk 2: chars 5200–8200
- Chunk 3: chars 7800–10000

---

## 4.17 `refresh_vector_index()` — Building the Search Index (Lines 371–391)

```python
def refresh_vector_index(self, collection_name: str, text_chunks: list) -> bool:
    try:
        try:
            self.chroma_client.delete_collection(name=collection_name)
        except Exception:
            pass                    # If collection doesn't exist yet, that's fine
        collection = self.chroma_client.get_or_create_collection(name=collection_name)

        batch_size = 100            # Add 100 chunks at a time
        for i in range(0, len(text_chunks), batch_size):
            batch = text_chunks[i:i + batch_size]
            collection.add(
                documents=batch,
                ids=[f"chunk_{i + j}" for j in range(len(batch))],
                metadatas=[{"index": i + j} for j in range(len(batch))],
            )
        return True
    except Exception as e:
        print(f"[ZeravaneEngine] Vector index error: {e}")
        return False
```

**Why delete first?** If the user queries the same URL twice, we don't want old chunks mixed with new ones. We wipe the collection and rebuild it fresh.

**Batch adding:** ChromaDB has memory limits per single `add()` call. Adding 100 chunks at a time prevents memory errors on large pages.

Each chunk gets:
- `documents`: The actual text
- `ids`: Unique IDs like `"chunk_0"`, `"chunk_1"` — ChromaDB requires unique IDs
- `metadatas`: Extra info like `{"index": 0}` — can be used for filtering later

---

## 4.18 `query_vector_context()` — Semantic Search (Lines 393–409)

```python
def query_vector_context(self, collection_name: str, query: str, n_results: int = 4) -> str:
    try:
        collection = self.chroma_client.get_collection(name=collection_name)
        available = collection.count()
        if available == 0:
            return ""
        n = min(n_results, available)       # Can't request more results than exist
        results = collection.query(query_texts=[query], n_results=n)
        docs = []
        if results and "documents" in results:
            for sublist in results["documents"]:
                docs.extend(sublist)
        return "\n\n---\n\n".join(docs)     # Join with separator for readability
    except Exception as e:
        print(f"[ZeravaneEngine] Vector query error: {e}")
        return ""
```

ChromaDB's `.query(query_texts=[query])` converts the query to an embedding vector and finds the stored chunks with the most similar vectors. `n_results=4` means return the 4 best matches.

The results come back as `{"documents": [["chunk text 1", "chunk text 2", ...]]}` — nested lists, hence the `for sublist in results["documents"]: docs.extend(sublist)` to flatten it.

The chunks are joined with `"\n\n---\n\n"` as a visual separator so the LLM sees clear boundaries between different chunks.

---

## 4.19 Conversation Memory Methods (Lines 415–435)

```python
def add_to_memory(self, role: str, content: str):
    self.conversation_memory.append({"role": role, "content": content})
    max_msgs = self.max_memory_turns * 2    # 10 turns × 2 messages/turn = 20 messages
    if len(self.conversation_memory) > max_msgs:
        self.conversation_memory = self.conversation_memory[-max_msgs:]  # Keep the last 20
```

**Sliding window memory:** When memory exceeds 20 messages (10 turns), the oldest messages are dropped. `self.conversation_memory[-20:]` returns the last 20 elements of the list. This keeps the LLM's context from growing unboundedly.

```python
def get_memory_context(self) -> str:
    lines = []
    for msg in self.conversation_memory:
        role_label = "User" if msg["role"] == "user" else "Assistant"
        lines.append(f"{role_label}: {msg['content'][:600]}")
    return "\n".join(lines)
```

Formats memory as a readable string. Each message is truncated to 600 characters to prevent the context from becoming too large. The format is simple:
```
User: How do I set up FastAPI?
Assistant: FastAPI is installed via pip...
User: How do I add authentication?
```

```python
def clear_memory(self):
    self.conversation_memory = []
```

Simply empties the list. Called when user clicks "Clear Memory" in the sidebar.

---

## 4.20 `_infer()` — 4-Tier LLM Inference (Lines 441–571)

This is the most critical method. Every AI response in the entire application goes through here.

```python
def _infer(self, system_instruction: str, prompt: str, use_memory: bool = False) -> tuple:
```

Takes:
- `system_instruction`: How the LLM should behave ("You are ZeravaneAI...")
- `prompt`: The actual content to respond to (scraped docs + user query)
- `use_memory`: Whether to include conversation history

Returns: `(response_text, model_label)`

**Tier 1 — Gemini:**
```python
if self.gemini_enabled and self.client:
    try:
        memory_prefix = ""
        if use_memory:
            mem = self.get_memory_context()
            if mem:
                memory_prefix = f"=== CONVERSATION HISTORY ===\n{mem}\n\n=== CURRENT QUERY ===\n"
        full_prompt = memory_prefix + prompt

        response = self.client.models.generate_content(
            model=self.model_name,         # "gemini-2.5-flash"
            contents=full_prompt,
            config=genai_types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,           # Low = more focused, less creative/random
            ),
        )
        text = response.text
        if use_memory:
            self.add_to_memory("assistant", text[:800])   # Store first 800 chars of response
        return text, "⚡ Gemini 2.5 Flash"
    except Exception as e:
        last_error = str(e)
        # Falls through to Tier 2
```

`temperature=0.2`: On a scale of 0–2, lower temperature = more deterministic answers. For code and technical answers, we want precision, not creativity. 0.2 gives focused, accurate responses.

Gemini uses a single-string prompt format, so memory is prepended as text.

**Tier 2 — Groq:**
```python
groq_messages = [{"role": "system", "content": system_instruction}]
if use_memory:
    groq_messages.extend(self.conversation_memory[:-1])  # All history except latest user msg
groq_messages.append({"role": "user", "content": prompt})
```

Groq uses the OpenAI chat format — a list of messages with roles. This is more sophisticated than Gemini's string format because the LLM can see exactly who said what rather than reading it from a formatted block of text.

`[:-1]` slices to exclude the last item (the current user message, which is added separately at the end).

**Tier 3 — AI/ML API:**
Identical structure to Groq — same OpenAI-compatible format, different base URL and model name.

**Tier 4 — Ollama:**
```python
ollama_prompt = f"System: {system_instruction}\n\n"
if use_memory and self.conversation_memory:
    ollama_prompt += f"Conversation history:\n{self.get_memory_context()}\n\n"
ollama_prompt += f"User: {prompt}\n\nAssistant:"
```

Ollama's local models use a simple text-completion format (not chat format). The `"Assistant:"` at the end is a completion cue — it tells the model to continue from that point, which is how instruction-tuned models are prompted.

```python
resp = requests.post(
    f"{self.ollama_base}/api/generate",
    json={
        "model": self.ollama_model,
        "prompt": ollama_prompt,
        "stream": False,                     # Get the whole response at once, not streamed
        "options": {"temperature": 0.2, "num_predict": 4096},
    },
    timeout=120,    # 2 minutes — local models can be slow
)
```

`stream: False` gets the complete response in one HTTP response. `num_predict: 4096` is the maximum number of tokens Ollama will generate. `timeout=120` because a 7B model on an RTX 3060 can take 30–60 seconds for a complex response.

---

## 4.21 `scrape_multiple_urls()` — Multi-Source RAG (Lines 577–608)

```python
def scrape_multiple_urls(self, urls: list) -> tuple:
    merged_chunks = []
    summary = []
    collection_id = "zeravane_multi_url"   # Separate collection just for multi-URL

    for url in urls:
        url = url.strip()
        if not url:
            continue
        raw, method = self.scrape_live_url(url)
        ok = raw and len(raw) >= self.MIN_TEXT_LENGTH and not any(raw.startswith(p) for p in _err)
        if ok:
            labeled = f"[SOURCE: {url}]\n{raw}"   # Prefix each chunk with its source URL
            chunks = self.chunk_text(labeled)
            merged_chunks.extend(chunks)
            summary.append(f"✅ {url} — {method}")
        else:
            summary.append(f"❌ {url} — Failed: {raw[:80]}")

    if merged_chunks:
        self.refresh_vector_index(collection_name=collection_id, text_chunks=merged_chunks)
```

**Key idea:** Each chunk is prefixed with `[SOURCE: url]`. When the LLM receives context from this collection, it can see which URL each piece of information came from — enabling source citation in answers.

All chunks from all URLs are merged into one collection (`"zeravane_multi_url"`), so a single query can retrieve the most relevant content from any of the scraped sources.

---

## 4.22 `analyze_github_repo()` — GitHub Intelligence (Lines 612–690)

```python
match = re.search(r"github\.com/([^/]+)/([^/?\s#]+)", github_url)
owner, repo = match.group(1), match.group(2).rstrip("/")
```

**Regex breakdown:**
- `github\.com/` — matches literal "github.com/"
- `([^/]+)` — captures one or more characters that aren't "/" = the owner name
- `/([^/?\s#]+)` — captures the repo name (stops at `/`, `?`, whitespace, `#`)
- `.group(1)` = owner, `.group(2)` = repo

Makes 3 GitHub API calls:
1. `GET /repos/{owner}/{repo}` — metadata (stars, forks, language, topics, license)
2. `GET /repos/{owner}/{repo}/readme` with raw accept header — README content
3. `GET /repos/{owner}/{repo}/git/trees/{branch}?recursive=0` — file tree (top-level only)

The README is capped at 10,000 characters, file tree at 60 files — keeps the context manageable.

---

## 4.23 `execute_live_agent_query()` — The Main Pipeline (Lines 768–864)

This is the master function that orchestrates everything.

```python
def execute_live_agent_query(
    self,
    user_query: str,
    target_url: str = None,
    force_rescrape: bool = False,
    use_memory: bool = True,
) -> tuple:
```

**Step by step:**

1. **Memory capture:** `self.add_to_memory("user", user_query)`

2. **URL cache check:**
```python
url_changed = target_url != self._cached_url
if url_changed or force_rescrape:
    # Full scrape → chunk → index
else:
    scrape_method = "✅ Cache Hit (URL unchanged)"
    # Just query the existing index
```
Cache hit means: "this URL was already scraped, just search it." This makes follow-up questions on the same page instant.

3. **Context availability check:**
```python
web_context_available = (
    target_url
    and context_payload
    and not context_payload.startswith("[")
)
```
Context is only "available" if it's not empty and not an error string (which always starts with `[`).

4. **System instruction selection:** Three different personas:
   - URL + context available → "I have live documentation data"
   - URL + no context → "Scraping failed, using training knowledge"
   - No URL → "General coding assistant mode"

5. **Prompt assembly:**
```python
prompt = (
    f"--- SYSTEM OVERVIEW ---\n"
    f"ZeravaneAI Version: 3.0\n"
    f"Scrape Method: {scrape_method}\n"
    f"Target URL: {target_url or 'None'}\n"
    f"Context Available: {'Yes' if web_context_available else 'No'}\n"
    f"Memory Turns: {len(self.conversation_memory) // 2}\n\n"
    f"--- LIVE WEB DOCUMENTATION ---\n"
    f"{context_payload if context_payload else fallback_context}\n\n"
    f"--- DEVELOPER QUERY ---\n"
    f"{user_query}\n"
)
```

The LLM receives a structured prompt with clear sections. This format helps it understand exactly what information is available and where it came from.

6. **`_infer()` call** with `use_memory=True` → LLM responds → response stored in memory → returned to frontend.

---

---

# 5. API.PY — FASTAPI REST API BREAKDOWN

`api.py` wraps the engine in an HTTP API so other apps can use ZeravaneAI programmatically.

## 5.1 App Setup

```python
app = FastAPI(
    title="ZeravaneAI API",
    version="3.0.0",
    docs_url="/docs",      # Swagger UI at localhost:8000/docs
    redoc_url="/redoc",    # ReDoc UI at localhost:8000/redoc
)
```

FastAPI auto-generates interactive API documentation at `/docs`. Go to `http://localhost:8000/docs` to test every endpoint in a browser.

## 5.2 CORS Middleware

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,    # Only these domains can call the API
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=True,
    max_age=3600,    # Browser can cache CORS check for 1 hour
)
```

CORS (Cross-Origin Resource Sharing) controls which websites can call the API from a browser. Without this, a malicious website could make API calls on behalf of a logged-in user.

## 5.3 Singleton Engine Pattern

```python
_engine: ZeravaneEngine = None

def get_engine() -> ZeravaneEngine:
    global _engine
    if _engine is None:
        _engine = ZeravaneEngine()
    return _engine
```

**Singleton pattern:** Only one `ZeravaneEngine` instance is created for the entire life of the API server. Every request reuses the same instance — which means the same ChromaDB connection, the same conversation memory, the same cached URL. If a new instance were created per request, memory and cache would be lost between calls.

## 5.4 Pydantic Request/Response Models

```python
class QueryRequest(BaseModel):
    query: str
    target_url: Optional[str] = None
    force_rescrape: Optional[bool] = False
    use_memory: Optional[bool] = True
```

Pydantic models do three things automatically:
1. **Validation** — If `query` is missing from the request body, FastAPI returns a 422 error before your code runs
2. **Type coercion** — `"true"` string is converted to `True` boolean automatically
3. **Documentation** — FastAPI reads these models and generates the Swagger UI schema

## 5.5 All 9 Endpoints

| Endpoint | Method | What it does |
|----------|--------|--------------|
| `/` | GET | Returns app name, version, status |
| `/health` | GET | Returns status of all LLM tiers, scraping tiers, DB type, memory count |
| `/scrape` | POST | Scrapes a URL and indexes it — pre-warms cache |
| `/query` | POST | Full RAG pipeline — scrape + retrieve + LLM |
| `/multi-scrape` | POST | Multiple URLs → merged RAG → query |
| `/github` | POST | GitHub repo analysis + query |
| `/tech-stack` | POST | Scrape URL → detect tech stack |
| `/codegen` | POST | Scrape docs URL → generate code |
| `/memory` | GET | View full conversation history |
| `/memory` | DELETE | Clear conversation history |

---

---

# 6. FRONTEND/APP.PY — STREAMLIT UI BREAKDOWN

## 6.1 Engine Caching

```python
@st.cache_resource(show_spinner="⚡ Initialising ZeravaneAI engine...")
def load_engine():
    return ZeravaneEngine()

engine = load_engine()
```

`@st.cache_resource` tells Streamlit: "run this function once, cache the result, return the same object on every page reload." Without this, `ZeravaneEngine()` would be called every time the user does anything in the UI — reinitialising all connections, losing memory, losing cached URLs.

## 6.2 Session State

```python
for key, val in {
    "chat_history": [],
    "last_url": "",
    "memory_enabled": True,
}.items():
    if key not in st.session_state:
        st.session_state[key] = val
```

`st.session_state` is Streamlit's way of persisting data across UI interactions. In Streamlit, every button click re-runs the entire script from top to bottom. Without session state, `chat_history` would reset to `[]` every time. The `if key not in` check prevents resetting existing values on re-runs.

## 6.3 The 5 Tabs

**Tab 1 — Chat Agent:** Main interface. Combines URL input + free-text query + memory toggle. Shows chat bubbles for conversation history. Calls `execute_live_agent_query()`.

**Tab 2 — Multi-URL RAG:** Text area for multiple URLs (one per line). Calls `scrape_multiple_urls()` then queries the merged index.

**Tab 3 — GitHub Analyzer:** Accepts GitHub repo URL. Displays metadata as metrics (stars/forks/language). Calls `analyze_github_repo()`.

**Tab 4 — Tech Stack Detector:** Accepts any URL. Calls `scrape_live_url()` then `detect_tech_stack()`.

**Tab 5 — Code Generator:** Accepts docs URL + language selection + generation request. Calls `generate_code_from_docs()`.

## 6.4 CSS Architecture

The UI uses CSS custom properties (variables):
```css
:root {
    --neon-cyan:    #00D9FF;
    --neon-green:   #00FF41;
    --neon-purple:  #A855F7;
    --text-primary: #E0E6FF;
}
```

Badge animations use `@keyframes` to create pulsing glow effects — a visual indicator of which LLM/scraping tier is active. The dark background (`#060B1A`) and neon colors give the sci-fi/terminal aesthetic.

---

---

# 7. STREAMLIT_APP.PY — ENTRY POINT

```python
import os
import sys
import runpy

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "zeravaneai"))
sys.path.insert(0, os.getcwd())

runpy.run_path("frontend/app.py", run_name="__main__")
```

**Why this exists:** When Streamlit runs `streamlit run streamlit_app.py`, it sets the working directory to wherever that file is. But `frontend/app.py` uses relative imports like `from backend.engine import ZeravaneEngine`. For that import to work, the current directory must be `zeravaneai/`. This file changes the directory before running the frontend. `runpy.run_path()` is safer than `exec()` — it handles module-level variables correctly.

---

---

# 8. REQUIREMENTS.TXT — DEPENDENCIES EXPLAINED

```
streamlit>=1.35.0          # The entire UI framework
python-dotenv>=1.0.0       # Loads .env file into environment variables
google-genai>=0.3.0        # Google's official Gemini SDK
fastapi>=0.111.0           # The REST API framework
uvicorn[standard]>=0.30.0  # ASGI server that runs FastAPI
python-multipart>=0.0.9    # Required for FastAPI file uploads
requests>=2.32.0           # HTTP library for calling external APIs
beautifulsoup4>=4.12.0     # HTML parsing for scrapers
urllib3>=2.0.0             # HTTP connection pooling (used by requests internally)
crawl4ai>=0.3.0            # Free, unlimited web scraper (Tier 1)
chromadb>=0.5.0            # Persistent vector database
pydantic>=2.0.0            # Data validation (used by FastAPI models)
```

Note: `crawl4ai` and `chromadb` are marked optional in the engine — the app works without them, just with reduced functionality.

---

---

# 9. .ENV.EXAMPLE — ALL CONFIG VARIABLES

| Variable | Required | Where to get it | Default |
|----------|----------|----------------|---------|
| `GEMINI_API_KEY` | YES | aistudio.google.com (free) | None |
| `GROQ_API_KEY` | Optional | console.groq.com (free) | None |
| `AIML_API_KEY` | Optional | aimlapi.com (free tier) | None |
| `SCRAPER_API_KEY` | Optional | scraperapi.com (paid) | None |
| `GITHUB_TOKEN` | Optional | github.com/settings/tokens | None |
| `OLLAMA_BASE_URL` | Optional | N/A | `http://localhost:11434` |
| `OLLAMA_MODEL` | Optional | Any pulled Ollama model | `qwen2.5-coder:7b` |

With just `GEMINI_API_KEY`, ZeravaneAI runs fully. Every additional key unlocks more fallback resilience.

---

---

# 10. DOCKERFILE — CONTAINER SETUP

```dockerfile
FROM python:3.11-slim           # Small base image with Python 3.11

WORKDIR /app                    # All commands run from /app

# System deps for Playwright (Crawl4AI) and C++ code (ChromaDB)
RUN apt-get install -y build-essential curl git wget

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download the Chromium browser Crawl4AI uses
RUN playwright install chromium --with-deps || true

COPY . .

RUN mkdir -p zeravaneai/data/zeravane_db

EXPOSE 8501 8000               # Streamlit port + FastAPI port

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

`--server.address=0.0.0.0` makes Streamlit accessible from outside the container (not just localhost). `|| true` after playwright install means "if this fails, don't stop the build" — in some environments Playwright install fails but the app still works with fallback scrapers.

---

---

# 11. ALL DATA FLOWS EXPLAINED

## Flow A: Simple Coding Question (No URL)

```
User: "How do I write a FastAPI middleware?"
      ↓
frontend/app.py — captures input
      ↓
engine.execute_live_agent_query(query="...", target_url=None)
      ↓
add_to_memory("user", query)
      ↓
No URL → skip scraping → context_payload = ""
      ↓
system_instruction = "You are a premium coding assistant..."
      ↓
_infer(system_instruction, prompt, use_memory=True)
      ↓
Try Gemini → succeeds
      ↓
add_to_memory("assistant", response[:800])
return (response, "", "N/A", "⚡ Gemini 2.5 Flash")
      ↓
frontend renders response in chat bubble
```

## Flow B: URL-Based RAG Query

```
User: "How does authentication work?"
URL:  "https://docs.fastapi.tiangolo.com/tutorial/security/"
      ↓
engine.execute_live_agent_query(query, url, force_rescrape=False)
      ↓
url != cached_url (new URL) → proceed to scrape
      ↓
scrape_live_url("https://docs.fastapi.tiangolo.com/...")
      ├─ _scrape_crawl4ai() → SUCCESS → returns markdown
      └─ returns (markdown_text, "🟢 Crawl4AI")
      ↓
chunk_text(markdown_text) → ~12 chunks of 3000 chars each
      ↓
refresh_vector_index("zeravane_cache", chunks) → stored in ChromaDB
      ↓
_cached_url = "https://docs.fastapi.tiangolo.com/..."
      ↓
query_vector_context("zeravane_cache", "How does authentication work?", n=4)
→ returns 4 most relevant chunks
      ↓
Build prompt with chunks + query
      ↓
_infer() → Gemini responds using the documentation context
      ↓
Response to user
```

## Flow C: Cache Hit (Second Question on Same URL)

```
User: "What about OAuth2 specifically?"
URL:  "https://docs.fastapi.tiangolo.com/tutorial/security/"  (same as before)
      ↓
url == cached_url AND force_rescrape=False
      ↓
scrape_method = "✅ Cache Hit (URL unchanged)"
      ↓
query_vector_context("zeravane_cache", "OAuth2") → instant retrieval from ChromaDB
      ↓
_infer() → response in <5 seconds (no scraping needed)
```

## Flow D: All Cloud APIs Fail

```
_infer() called
      ↓
Tier 1 Gemini → 429 Rate Limited → exception caught → last_error = "429"
      ↓
Tier 2 Groq   → 429 Rate Limited → exception caught → last_error = "429"
      ↓
Tier 3 AI/ML  → timeout          → exception caught → last_error = "timeout"
      ↓
Tier 4 Ollama → requests.post("http://localhost:11434/api/generate")
              → RTX 3060 processes query locally
              → returns response after ~30 seconds
              → "🖥️ Ollama (qwen2.5-coder:7b) [Local]"
      ↓
User gets answer — zero interruption
```

---

---

# 12. KEY CONCEPTS EXPLAINED SIMPLY

## What is RAG?
RAG = Retrieval-Augmented Generation. Instead of just asking an LLM a question from its training data, you first retrieve relevant documents and include them in the question. Like giving an exam student the textbook chapter before the test.

## What is a Vector Database?
Normal databases search by exact text match. Vector databases convert text into numbers (vectors) and find text that is *semantically similar* — meaning it has the same meaning even if different words are used. Asking "authentication" finds chunks about "login", "JWT", "OAuth" without those words being in the query.

## What is a Chunk?
LLMs have a limit on how much text they can read at once (context window). A 100-page documentation site can't fit. Chunking splits it into small pieces (~3000 chars). Only the most relevant pieces are sent to the LLM — not the whole site.

## What is an Embedding?
An embedding is a list of numbers (like [0.23, -0.41, 0.87, ...]) that represents the meaning of text. ChromaDB converts text chunks and user queries to embeddings, then finds chunks whose embedding numbers are closest to the query's embedding — those are the most relevant.

## What is Temperature?
Temperature (0–2) controls how random an LLM's outputs are. Temperature 0 = always the most likely next word (robotic, repetitive). Temperature 2 = very random (creative but inaccurate). ZeravaneAI uses 0.2 — slightly off zero for natural language, but close to deterministic for code accuracy.

---

---

# 13. HOW TO SET UP & RUN

## Local Setup

```bash
# 1. Unzip and enter folder
unzip zeravaneAI3.0.zip
cd zeravaneAI3.0

# 2. (Recommended) Create virtual environment
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up Crawl4AI (one-time)
crawl4ai-setup    # Downloads Playwright browsers

# 5. Copy and fill API keys
cp .env.example .env
# Edit .env — at minimum add: GEMINI_API_KEY=your_key_here

# 6. (Optional) Set up Ollama for local fallback
# Download from: https://ollama.com/download
ollama pull qwen2.5-coder:7b

# 7. Run
streamlit run streamlit_app.py
# Open: http://localhost:8501

# 8. (Optional) Run API separately
uvicorn zeravaneai.backend.api:app --reload --port 8000
# Open: http://localhost:8000/docs
```

## Docker Setup

```bash
docker build -t zeravaneai .
docker run -p 8501:8501 \
  -e GEMINI_API_KEY=your_key \
  -e GROQ_API_KEY=your_key \
  zeravaneai
```

---

---

# 14. WHAT EACH TAB DOES (TESTER GUIDE)

## Tab 1 — 💬 Chat Agent

**What to test:**
- Type a coding question with no URL → should answer from base knowledge
- Add a URL (e.g., `https://docs.fastapi.tiangolo.com`) → should scrape and answer from docs
- Ask 2–3 follow-up questions on the same URL → should NOT re-scrape (cache hit in sidebar)
- Toggle memory off → follow-up questions should not reference previous answers
- Toggle memory on → follow-up questions should maintain context
- Check which LLM was used (shown in model tag below response)
- Check the "Inspect Vector Context" expander → should show actual doc text

**What the sidebar shows:**
- Green dots = API keys found and working
- Ollama status = whether your local model is running
- Cache status = which URL is currently indexed

## Tab 2 — 🔗 Multi-URL RAG

**What to test:**
- Paste 2–3 documentation URLs, one per line
- Ask a comparison question like "How does error handling differ across these frameworks?"
- Check scrape results — each URL shows ✅ or ❌
- The answer should cite content from multiple sources

## Tab 3 — 🐙 GitHub Analyzer

**What to test:**
- Enter `https://github.com/tiangolo/fastapi`
- Ask "What does this project do?" — should use README content
- Ask "What files are in the project?" — should reference the file tree
- Check the metrics (stars, forks, language, license) display correctly
- Use the "Raw Repository Data" expander to verify content was fetched

## Tab 4 — 🔍 Tech Stack Detector

**What to test:**
- Enter `https://vercel.com` — should detect Next.js, React, etc.
- Enter `https://github.com` — should detect Ruby on Rails, React, etc.
- Check confidence ratings in the output (High/Medium/Low)
- Check "Raw Scraped Content" expander — verify actual page text was retrieved

## Tab 5 — ⚙️ Code Generator

**What to test:**
- URL: `https://docs.fastapi.tiangolo.com`
- Request: "Create a REST API with user authentication using JWT tokens"
- Language: Python
- Should generate runnable FastAPI code with JWT auth
- Change language to TypeScript — same docs, different output language
- Check that the model tag shows which LLM generated the code

---

---

# 15. COMMON ERRORS & HOW TO FIX THEM

| Error | Cause | Fix |
|-------|-------|-----|
| `❌ GEMINI_API_KEY not found` | Missing key | Add to `.env` or Streamlit Secrets |
| `Crawl4AI_Error: crawl4ai not installed` | Package missing | `pip install crawl4ai && crawl4ai-setup` |
| `ChromaDB init failed` | Permissions or package | `pip install chromadb` or check folder permissions |
| Ollama shows INACTIVE | Ollama not running | Start Ollama: `ollama serve` |
| `❌ All LLM tiers failed` | All keys exhausted | Add Ollama as local fallback |
| Slow responses on Tab 5 | Crawl4AI initialising | Normal on first call — Playwright browser warmup |
| GitHub: `Invalid GitHub URL` | Wrong URL format | Must be `https://github.com/owner/repo` |
| Port already in use | Another process on 8501 | `streamlit run ... --server.port 8502` |

---

---

# APPENDIX: CHROMADB COLLECTIONS REFERENCE

ZeravaneAI creates these ChromaDB collections:

| Collection Name | Created By | Content |
|-----------------|-----------|---------|
| `zeravane_cache` | `execute_live_agent_query()` | Currently cached URL content |
| `zeravane_multi_url` | `scrape_multiple_urls()` | Merged multi-URL content |
| `zeravane_github` | `analyze_github_repo()` | GitHub repo content |
| `zeravane_codegen` | `generate_code_from_docs()` | Documentation for code generation |

Each collection is wiped and rebuilt when new content is indexed. The persistent ChromaDB stores all collections in `zeravaneai/data/zeravane_db/`.

---

*ZeravaneAI v3.0 · Built by Franklin Josva*
*Documentation covers all 865 lines of engine.py, 200+ lines of api.py, and 400+ lines of frontend/app.py*
