# 🏛️ கரிகாலன் AI (Karikalan AI)

> **Enterprise AI Coding Platform** — Tamil Chola Heritage × Futuristic AI
> 4-Tier LLM · 3-Tier Scraping · Persistent RAG · Conversation Memory

---

## கரிகால சோழன் · About the Name

**Karikalan (கரிகாலன்)** was the greatest Chola emperor — the king who engineered the **Kallanai Dam** (Grand Anicut) on the Kaveri river, the **oldest water regulation structure in the world still in use today**, built 2,000 years ago.

> *Named after the king who engineered the impossible — we're doing the same with AI.*

The platform carries this legacy: built to last, built to serve, built by a Tamil developer from Dindigul.

---

## 🚀 Quick Start

```bash
# Install
pip install -r requirements.txt
crawl4ai-setup

# Configure
cp .env.example .env
# Add your GEMINI_API_KEY at minimum

# (Optional) Local AI fallback via Ollama
ollama pull qwen2.5-coder:7b

# Run
streamlit run streamlit_app.py
# → http://localhost:8501

# API (optional)
uvicorn zeravaneai.backend.api:app --reload --port 8000
# → http://localhost:8000/docs
```

---

## 🧠 4-Tier LLM Architecture

```
Request
  ↓
⚡ Gemini 2.5 Flash     (Google AI Studio — 1M tokens/day free)
  ↓ rate limited?
🟣 Groq llama-3.3-70b   (ultra-fast — free tier)
  ↓ exhausted?
🔶 AI/ML API gpt-4o-mini (free tier)
  ↓ all cloud APIs down?
🖥️ Ollama local          (qwen2.5-coder:7b — unlimited, offline)
  ↓
✅ Always responds — never blocked
```

## 🕷️ 3-Tier Scraping

```
URL
  ↓
🟢 Crawl4AI      (free · unlimited · LLM-optimised markdown)
  ↓ fails?
🔵 ScraperAPI    (JS rendering · rotating proxies)
  ↓ fails?
⚪ Requests      (plain HTML — always works)
```

---

## 🌟 Features

| Feature | Description |
|---------|-------------|
| 💬 AI Chat Agent | Multi-turn conversation with memory + optional URL context |
| 🔗 Multi-URL RAG | Scrape multiple URLs → merged knowledge base → query |
| 🐙 GitHub Analyzer | README + file tree + metadata analysis |
| 🔍 Tech Stack Detector | Scrape any site → detect full tech stack with confidence |
| ⚙️ Code Generator | Live docs URL → production-ready code in any language |
| 🌐 REST API | 9 endpoints via FastAPI |
| 🗄️ Persistent DB | ChromaDB survives restarts |
| 🧠 Memory | 10-turn conversation window |

---

## 📁 Structure

```
karikalanAI/
├── streamlit_app.py          ← Run this
├── requirements.txt
├── Dockerfile
├── .env.example
└── zeravaneai/
    ├── backend/
    │   ├── engine.py         ← KarikalanEngine (all AI logic)
    │   └── api.py            ← FastAPI REST API
    ├── frontend/
    │   └── app.py            ← Streamlit UI (Tamil + English)
    └── data/
        └── zeravane_db/      ← Persistent ChromaDB
```

---

## 🔑 API Keys

| Key | Required | Free at |
|-----|----------|---------|
| `GEMINI_API_KEY` | ✅ Yes | aistudio.google.com |
| `GROQ_API_KEY` | Optional | console.groq.com |
| `AIML_API_KEY` | Optional | aimlapi.com |
| `SCRAPER_API_KEY` | Optional | scraperapi.com |
| `GITHUB_TOKEN` | Optional | github.com/settings/tokens |

---

கரிகால சோழன் கட்டிய கல்லணை போல் — Built to last like the Grand Anicut.

*Built by **Franklin Josva** · Dindigul, Tamil Nadu · 2025*
