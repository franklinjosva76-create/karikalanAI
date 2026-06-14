"""
KarikalanAI — FastAPI REST API v3.1
─────────────────────────────────────────────────────────────────────────────
New in v3.0:
  • /memory endpoints (view, clear)
  • /multi-scrape endpoint
  • /github endpoint
  • /tech-stack endpoint
  • /codegen endpoint
  • use_memory flag on /query
  • Improved error responses

Run with:
    uvicorn zeravaneai.backend.api:app --reload --port 8000
"""

import os
import sys
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

if not os.environ.get("GEMINI_API_KEY") and os.environ.get("GOOGLE_API_KEY"):
    os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.engine import KarikalanEngine

# ── App ─────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Karikalan AI API",
    description=(
        "Karikalan AI v3.1 — Enterprise AI Coding Assistant.\n"
        "3-tier scraping · 4-tier LLM fallback · Persistent RAG · Conversation memory."
    ),
    version="3.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ────────────────────────────────────────────────────────────────────

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8501",
    "https://localhost:8501",
    "http://127.0.0.1:8501",
    "http://localhost:8000",
    # Add your production domain here:
    # "https://your-app.streamlit.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=True,
    max_age=3600,
)

# ── Singleton engine ─────────────────────────────────────────────────────────

_engine: KarikalanEngine = None


def get_engine() -> KarikalanEngine:
    global _engine
    if _engine is None:
        _engine = KarikalanEngine()
    return _engine


# ── Request / Response models ────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    target_url: Optional[str] = None
    force_rescrape: Optional[bool] = False
    use_memory: Optional[bool] = True


class QueryResponse(BaseModel):
    answer: str
    context_payload: str
    scrape_method: str
    model_used: str
    scraper_enabled: bool
    memory_turns: int


class ScrapeRequest(BaseModel):
    url: str


class ScrapeResponse(BaseModel):
    scrape_method: str
    context_preview: str
    chunks_indexed: int


class MultiScrapeRequest(BaseModel):
    urls: List[str]
    query: str


class MultiScrapeResponse(BaseModel):
    answer: str
    scrape_summary: str
    model_used: str
    chunks_indexed: int


class GithubRequest(BaseModel):
    github_url: str
    query: str


class GithubResponse(BaseModel):
    answer: str
    metadata: dict
    model_used: str


class TechStackRequest(BaseModel):
    url: str


class TechStackResponse(BaseModel):
    report: str
    scrape_method: str


class CodegenRequest(BaseModel):
    docs_url: str
    request: str
    language: Optional[str] = "Python"


class CodegenResponse(BaseModel):
    code: str
    scrape_method: str
    model_used: str


class HealthResponse(BaseModel):
    status: str
    version: str
    llm_tiers: dict
    scraping_tiers: dict
    vector_db: str
    cached_url: Optional[str]
    memory_turns: int


class MemoryResponse(BaseModel):
    turns: int
    history: list


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {
        "app": "ZeravaneAI",
        "version": "3.1.0",
        "status": "running",
        "description": "Enterprise AI Coding Assistant — 4-Tier LLM · 3-Tier Scraping · Persistent RAG",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health():
    engine = get_engine()
    return HealthResponse(
        status="healthy",
        version="3.1.0",
        llm_tiers={
            "tier1_gemini":  "active" if engine.gemini_enabled else "inactive",
            "tier2_groq":    "active" if engine.groq_enabled   else "inactive",
            "tier3_aiml":    "active" if engine.aiml_enabled   else "inactive",
            "tier4_ollama":  "active" if engine.ollama_enabled else "inactive",
        },
        scraping_tiers={
            "tier1_crawl4ai":    "available",
            "tier2_scraperapi":  "active" if engine.scraper_enabled else "inactive",
            "tier3_requests":    "available",
        },
        vector_db="chromadb_persistent" if hasattr(engine.chroma_client, "list_collections") else "in_memory",
        cached_url=engine._cached_url,
        memory_turns=len(engine.conversation_memory) // 2,
    )


@app.post("/scrape", response_model=ScrapeResponse, tags=["Scraping"])
def scrape_endpoint(request: ScrapeRequest):
    if not request.url.strip():
        raise HTTPException(status_code=400, detail="URL cannot be empty")
    engine = get_engine()
    raw_text, scrape_method = engine.scrape_live_url(request.url)
    _err = ("Error:", "Crawl4AI_Error:", "ScraperAPI_Error:", "Requests_Error:")
    scrape_ok = raw_text and len(raw_text) >= engine.MIN_TEXT_LENGTH and not any(raw_text.startswith(p) for p in _err)
    if not scrape_ok:
        raise HTTPException(status_code=502, detail=f"Scraping failed: {raw_text[:300]}")
    chunks = engine.chunk_text(raw_text)
    indexed = engine.refresh_vector_index(collection_name=engine._cached_collection, text_chunks=chunks)
    if not indexed:
        raise HTTPException(status_code=500, detail="Failed to build vector index")
    engine._cached_url = request.url
    context_preview = engine.query_vector_context(collection_name=engine._cached_collection, query="summary", n_results=1)
    return ScrapeResponse(scrape_method=scrape_method, context_preview=context_preview[:500], chunks_indexed=len(chunks))


@app.post("/query", response_model=QueryResponse, tags=["Query"])
def query_endpoint(request: QueryRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    engine = get_engine()
    response_text, context_payload, scrape_method, model_used = engine.execute_live_agent_query(
        user_query=request.query,
        target_url=request.target_url,
        force_rescrape=request.force_rescrape or False,
        use_memory=request.use_memory if request.use_memory is not None else True,
    )
    return QueryResponse(
        answer=response_text,
        context_payload=context_payload,
        scrape_method=scrape_method,
        model_used=model_used,
        scraper_enabled=engine.scraper_enabled,
        memory_turns=len(engine.conversation_memory) // 2,
    )


@app.post("/multi-scrape", response_model=MultiScrapeResponse, tags=["Scraping"])
def multi_scrape_endpoint(request: MultiScrapeRequest):
    if not request.urls:
        raise HTTPException(status_code=400, detail="URLs list cannot be empty")
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    engine = get_engine()
    chunks, summary = engine.scrape_multiple_urls(request.urls)
    if not chunks:
        raise HTTPException(status_code=502, detail=f"All URLs failed to scrape.\n{summary}")
    context = engine.query_vector_context(collection_name="zeravane_multi_url", query=request.query, n_results=5)
    system = (
        "You are ZeravaneAI, a web-aware developer agent with content from multiple URLs. "
        "Answer using the provided merged context. Cite source URLs where possible."
    )
    prompt = f"Sources: {', '.join(request.urls)}\n\n=== MERGED CONTENT ===\n{context}\n\n=== QUESTION ===\n{request.query}"
    answer, model_used = engine._infer(system, prompt)
    return MultiScrapeResponse(answer=answer, scrape_summary=summary, model_used=model_used, chunks_indexed=len(chunks))


@app.post("/github", response_model=GithubResponse, tags=["Analysis"])
def github_endpoint(request: GithubRequest):
    if not request.github_url.strip():
        raise HTTPException(status_code=400, detail="GitHub URL cannot be empty")
    engine = get_engine()
    repo_content, metadata = engine.analyze_github_repo(request.github_url.strip())
    if repo_content.startswith("GitHub_Error") or repo_content.startswith("Invalid"):
        raise HTTPException(status_code=502, detail=repo_content)
    context = engine.query_vector_context(collection_name="zeravane_github", query=request.query, n_results=4) or repo_content[:6000]
    system = (
        "You are ZeravaneAI, a GitHub repository analyst. "
        "Answer using the repository data: README, file tree, metadata. "
        "Be specific, cite file names or README sections where relevant."
    )
    prompt = f"Repository: {request.github_url}\n\n=== REPO DATA ===\n{context}\n\n=== QUESTION ===\n{request.query}"
    answer, model_used = engine._infer(system, prompt)
    return GithubResponse(answer=answer, metadata=metadata, model_used=model_used)


@app.post("/tech-stack", response_model=TechStackResponse, tags=["Analysis"])
def tech_stack_endpoint(request: TechStackRequest):
    if not request.url.strip():
        raise HTTPException(status_code=400, detail="URL cannot be empty")
    engine = get_engine()
    raw_content, scrape_method = engine.scrape_live_url(request.url.strip())
    report = engine.detect_tech_stack(raw_content, request.url.strip())
    return TechStackResponse(report=report, scrape_method=scrape_method)


@app.post("/codegen", response_model=CodegenResponse, tags=["Code Generation"])
def codegen_endpoint(request: CodegenRequest):
    if not request.docs_url.strip():
        raise HTTPException(status_code=400, detail="Docs URL cannot be empty")
    if not request.request.strip():
        raise HTTPException(status_code=400, detail="Generation request cannot be empty")
    engine = get_engine()
    code, scrape_method, model_used = engine.generate_code_from_docs(
        docs_url=request.docs_url.strip(),
        generation_request=request.request.strip(),
        language=request.language or "Python",
    )
    return CodegenResponse(code=code, scrape_method=scrape_method, model_used=model_used)


@app.get("/memory", response_model=MemoryResponse, tags=["Memory"])
def get_memory():
    engine = get_engine()
    return MemoryResponse(
        turns=len(engine.conversation_memory) // 2,
        history=engine.conversation_memory,
    )


@app.delete("/memory", tags=["Memory"])
def clear_memory():
    engine = get_engine()
    engine.clear_memory()
    return {"status": "cleared", "message": "Conversation memory reset successfully"}
