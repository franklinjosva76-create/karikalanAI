# =============================================================================
# கரிகாலன் AI (Karikalan AI) — Streamlit Frontend v1.0
# Tamil Chola Heritage × Futuristic AI Platform
# =============================================================================
import os
import sys

os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.engine import KarikalanEngine

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="கரிகாலன் AI",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# DESIGN SYSTEM — CHOLA HERITAGE PALETTE
# Bronze gold   #C8922A  — molten Chola bronze, temple lamps
# Deep copper   #8B4513  — aged copper inscriptions
# Stone dark    #1A1208  — Brihadeeswarar granite darkness
# Warm black    #0D0A05  — night at Thanjavur
# Saffron glow  #FF9500  — sacred fire, vel spear
# Crimson royal #8B0000  — Chola war banners
# Ivory stone   #F5E6C8  — temple stone carvings
# Muted gold    #A07830  — aged gold accents
# =============================================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700;900&family=Inter:wght@300;400;500;600;700&display=swap');

:root {
    --bronze:       #C8922A;
    --bronze-dim:   #8B6320;
    --copper:       #8B4513;
    --saffron:      #FF9500;
    --saffron-dim:  #CC7700;
    --crimson:      #8B0000;
    --stone-dark:   #1A1208;
    --stone-mid:    #231A0A;
    --warm-black:   #0D0A05;
    --ivory:        #F5E6C8;
    --ivory-dim:    #C4B08A;
    --muted-gold:   #A07830;
    --text-body:    #E8D5A8;
    --text-muted:   #7A6540;
    --card-bg:      rgba(26,18,8,0.92);
    --border-gold:  rgba(200,146,42,0.35);
}

/* ── Global ── */
.stApp {
    background:
        radial-gradient(ellipse at 20% 10%, rgba(139,69,19,0.08) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 80%, rgba(200,146,42,0.06) 0%, transparent 50%),
        linear-gradient(160deg, #0D0A05 0%, #1A1208 40%, #0D0A05 100%);
    font-family: 'Inter', sans-serif;
}
.main { background: transparent; color: var(--text-body); }

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea  > div > div > textarea {
    border: 1.5px solid rgba(200,146,42,0.4) !important;
    background: rgba(13,10,5,0.95) !important;
    color: var(--ivory) !important;
    border-radius: 6px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    box-shadow: inset 0 1px 3px rgba(0,0,0,0.5), 0 0 8px rgba(200,146,42,0.1) !important;
    transition: all 0.25s ease !important;
}
.stTextInput > div > div > input:focus,
.stTextArea  > div > div > textarea:focus {
    border-color: var(--bronze) !important;
    box-shadow: inset 0 1px 3px rgba(0,0,0,0.5), 0 0 18px rgba(200,146,42,0.3) !important;
}
.stTextInput label, .stTextArea label {
    color: var(--ivory-dim) !important;
    font-size: 12px !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
}

/* ── Buttons ── */
.stButton > button {
    border: 1.5px solid var(--bronze) !important;
    background: linear-gradient(135deg, rgba(26,18,8,0.98) 0%, rgba(35,26,10,0.98) 100%) !important;
    color: var(--bronze) !important;
    border-radius: 4px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    font-size: 12px !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 0 10px rgba(200,146,42,0.15), inset 0 1px 0 rgba(200,146,42,0.1) !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, rgba(200,146,42,0.18) 0%, rgba(200,146,42,0.08) 100%) !important;
    box-shadow: 0 0 24px rgba(200,146,42,0.4), inset 0 1px 0 rgba(200,146,42,0.2) !important;
    color: var(--ivory) !important;
    transform: translateY(-1px) !important;
}

/* ── Selectbox ── */
.stSelectbox > div > div {
    background: rgba(13,10,5,0.95) !important;
    border: 1.5px solid rgba(200,146,42,0.35) !important;
    color: var(--ivory) !important;
    border-radius: 6px !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(13,10,5,0.8);
    border-radius: 6px;
    padding: 4px;
    gap: 3px;
    border: 1px solid rgba(200,146,42,0.2);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 4px !important;
    color: var(--text-muted) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    letter-spacing: 0.5px !important;
    transition: all 0.2s !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(200,146,42,0.2) 0%, rgba(200,146,42,0.08) 100%) !important;
    color: var(--bronze) !important;
    box-shadow: 0 0 12px rgba(200,146,42,0.2) !important;
    border: 1px solid rgba(200,146,42,0.3) !important;
}

/* ── Metrics ── */
[data-testid="metric-container"] {
    background: var(--card-bg) !important;
    border: 1px solid var(--border-gold) !important;
    border-radius: 6px !important;
    padding: 14px !important;
}
[data-testid="stMetricLabel"] { color: var(--text-muted) !important; }
[data-testid="stMetricValue"] { color: var(--bronze) !important; font-family: 'Cinzel', serif !important; }

/* ── Expanders ── */
.streamlit-expanderHeader {
    background: rgba(13,10,5,0.9) !important;
    border: 1px solid rgba(200,146,42,0.2) !important;
    border-radius: 6px !important;
    color: var(--ivory-dim) !important;
    font-size: 13px !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D0A05 0%, #1A1208 100%) !important;
    border-right: 1px solid rgba(200,146,42,0.2) !important;
}
[data-testid="stSidebar"] .stMarkdown { color: var(--text-body) !important; }

/* ── Toggle ── */
.stToggle { color: var(--ivory-dim) !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: rgba(13,10,5,0.5); }
::-webkit-scrollbar-thumb { background: rgba(200,146,42,0.3); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(200,146,42,0.5); }

/* ════════════════════════════════════════
   CUSTOM COMPONENTS
════════════════════════════════════════ */

/* ── Hero Header ── */
.karikalan-header {
    text-align: center;
    padding: 28px 0 18px;
    position: relative;
}
.karikalan-header::before {
    content: '';
    position: absolute;
    top: 0; left: 50%;
    transform: translateX(-50%);
    width: 340px; height: 1px;
    background: linear-gradient(90deg, transparent, var(--bronze), transparent);
}
.karikalan-header::after {
    content: '';
    position: absolute;
    bottom: 0; left: 50%;
    transform: translateX(-50%);
    width: 240px; height: 1px;
    background: linear-gradient(90deg, transparent, var(--bronze-dim), transparent);
}
.title-tamil {
    font-family: 'Cinzel', serif;
    font-size: 38px;
    font-weight: 900;
    letter-spacing: 6px;
    color: var(--bronze);
    text-shadow: 0 0 30px rgba(200,146,42,0.4), 0 0 60px rgba(200,146,42,0.15);
    margin: 0;
    line-height: 1.1;
}
.title-sub-tamil {
    font-size: 15px;
    color: var(--ivory-dim);
    letter-spacing: 3px;
    margin: 4px 0 0;
    opacity: 0.8;
}
.title-tagline {
    font-size: 11px;
    color: var(--text-muted);
    letter-spacing: 3px;
    text-transform: uppercase;
    margin: 10px 0 0;
}

/* ── Kolam Divider (decorative line with diamond) ── */
.kolam-divider {
    display: flex; align-items: center; gap: 12px;
    margin: 14px 0;
}
.kolam-line {
    flex: 1; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(200,146,42,0.4), transparent);
}
.kolam-diamond {
    width: 8px; height: 8px;
    background: var(--bronze);
    transform: rotate(45deg);
    box-shadow: 0 0 8px rgba(200,146,42,0.5);
    flex-shrink: 0;
}

/* ── Status Banner ── */
.mode-banner {
    background: linear-gradient(135deg, rgba(26,18,8,0.98) 0%, rgba(35,26,10,0.98) 100%);
    border: 1px solid rgba(200,146,42,0.25);
    border-left: 3px solid var(--bronze);
    border-radius: 4px;
    padding: 10px 16px;
    margin: 10px 0;
    font-size: 13px;
    color: var(--ivory-dim);
}
.mode-banner span.mode-label {
    color: var(--bronze);
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    font-size: 11px;
}

/* ── Chat Bubbles ── */
.chat-scroll { max-height: 520px; overflow-y: auto; padding-right: 6px; }
.msg-user {
    background: linear-gradient(135deg, rgba(26,18,8,0.95), rgba(35,26,12,0.95));
    border: 1px solid rgba(200,146,42,0.25);
    border-radius: 10px 10px 3px 10px;
    padding: 12px 16px; margin: 10px 0 4px;
    color: var(--ivory); font-size: 14px; line-height: 1.6;
}
.msg-ai {
    background: linear-gradient(135deg, rgba(13,10,5,0.98), rgba(26,18,8,0.98));
    border: 1px solid rgba(200,146,42,0.15);
    border-left: 3px solid var(--saffron);
    border-radius: 3px 10px 10px 10px;
    padding: 12px 16px; margin: 4px 0 10px;
    color: var(--text-body); font-size: 14px; line-height: 1.7;
}
.msg-sender {
    font-size: 10px; letter-spacing: 2px; text-transform: uppercase;
    font-weight: 600; margin-bottom: 5px;
}
.msg-sender-user { color: var(--bronze-dim); }
.msg-sender-ai   { color: var(--saffron-dim); }
.msg-meta { font-size: 10px; color: var(--text-muted); margin-top: 6px; letter-spacing: 0.5px; }

/* ── Model / Method Tags ── */
.tag {
    display: inline-block; padding: 2px 9px;
    border-radius: 3px; font-size: 10px;
    font-weight: 600; letter-spacing: 1px;
    text-transform: uppercase; margin-left: 6px;
}
.tag-model  { background: rgba(200,146,42,0.12); border: 1px solid rgba(200,146,42,0.35); color: var(--bronze); }
.tag-memory { background: rgba(255,149,0,0.1);   border: 1px solid rgba(255,149,0,0.3);   color: var(--saffron); }
.tag-cache  { background: rgba(139,69,19,0.15);   border: 1px solid rgba(139,69,19,0.4);   color: #C87050; }

/* ── Tier Status Dots ── */
.tier-row {
    display: flex; align-items: center; gap: 8px;
    padding: 5px 0; font-size: 12px; color: var(--text-muted);
}
.tier-dot {
    width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0;
}
.tier-dot.active   { background: var(--bronze); box-shadow: 0 0 6px rgba(200,146,42,0.6); }
.tier-dot.inactive { background: rgba(100,80,40,0.4); }
.tier-label { flex: 1; }
.tier-label.active { color: var(--ivory-dim); }

/* ── Info Cards (for GitHub metadata) ── */
.chola-card {
    background: rgba(13,10,5,0.95);
    border: 1px solid var(--border-gold);
    border-top: 2px solid var(--bronze);
    border-radius: 4px; padding: 14px;
    margin: 6px 0;
}

/* ── Topic badges ── */
.topic-badge {
    display: inline-block; padding: 3px 10px; margin: 3px 2px;
    background: rgba(200,146,42,0.08);
    border: 1px solid rgba(200,146,42,0.25);
    border-radius: 3px; color: var(--bronze);
    font-size: 11px; letter-spacing: 0.5px;
}

/* ── Sidebar brand mark ── */
.sidebar-emblem {
    text-align: center; padding: 16px 0 12px;
    border-bottom: 1px solid rgba(200,146,42,0.2);
    margin-bottom: 14px;
}
.sidebar-glyph {
    font-size: 32px; display: block; margin-bottom: 6px;
    filter: drop-shadow(0 0 8px rgba(200,146,42,0.5));
}
.sidebar-name {
    font-family: 'Cinzel', serif;
    font-size: 15px; font-weight: 700;
    color: var(--bronze); letter-spacing: 3px;
    display: block;
}
.sidebar-sub { font-size: 10px; color: var(--text-muted); letter-spacing: 2px; display: block; margin-top: 3px; }

/* ── Section headers inside tabs ── */
.tab-section-title {
    font-family: 'Cinzel', serif;
    font-size: 16px; font-weight: 600;
    color: var(--bronze); letter-spacing: 2px;
    margin: 0 0 4px;
}
.tab-section-sub { font-size: 12px; color: var(--text-muted); letter-spacing: 0.5px; margin-bottom: 14px; }

/* Keyframes */
@keyframes lamp-glow {
    0%, 100% { text-shadow: 0 0 20px rgba(200,146,42,0.4), 0 0 40px rgba(200,146,42,0.15); }
    50%       { text-shadow: 0 0 35px rgba(200,146,42,0.7), 0 0 70px rgba(200,146,42,0.25); }
}
.title-tamil { animation: lamp-glow 4s ease-in-out infinite; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# ENGINE + SESSION STATE
# =============================================================================

@st.cache_resource(show_spinner="🏛️ தமிழ் AI துவங்குகிறது · Initialising Karikalan AI...")
def load_engine():
    return KarikalanEngine()

engine = load_engine()

for key, val in {
    "chat_history": [],
    "last_url": "",
    "memory_enabled": True,
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# =============================================================================
# HEADER
# =============================================================================
st.markdown("""
<div class="karikalan-header">
    <div class="title-tamil">KARIKALAN AI</div>
    <div class="title-sub-tamil">கரிகாலன் AI · கரிகால சோழன்</div>
    <div class="title-tagline">
        Enterprise AI Coding Platform · 4-Tier LLM · Tamil Chola Heritage
    </div>
</div>
""", unsafe_allow_html=True)

# Kolam divider
st.markdown("""
<div class="kolam-divider">
    <div class="kolam-line"></div>
    <div class="kolam-diamond"></div>
    <div style="font-size:10px;letter-spacing:3px;color:#7A6540;white-space:nowrap;">
        கல்லணை கட்டிய கரிகாலன் · Builder of the Grand Anicut
    </div>
    <div class="kolam-diamond"></div>
    <div class="kolam-line"></div>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown("""
    <div class="sidebar-emblem">
        <span class="sidebar-glyph">🏛️</span>
        <span class="sidebar-name">KARIKALAN AI</span>
        <span class="sidebar-sub">கரிகாலன் · சோழ பேரரசு</span>
    </div>
    """, unsafe_allow_html=True)

    # LLM Tiers
    st.markdown(
        "<div style='font-size:10px;letter-spacing:2px;text-transform:uppercase;"
        "color:#7A6540;margin-bottom:8px;'>🧠 LLM படிநிலைகள் · Tiers</div>",
        unsafe_allow_html=True,
    )
    tiers = [
        ("Gemini 2.5 Flash",        engine.gemini_enabled),
        ("Groq · llama-3.3-70b",    engine.groq_enabled),
        ("AI/ML API · gpt-4o-mini", engine.aiml_enabled),
        (f"Ollama · {engine.ollama_model}", engine.ollama_enabled),
    ]
    for label, active in tiers:
        cls = "active" if active else "inactive"
        st.markdown(
            f"<div class='tier-row'>"
            f"<div class='tier-dot {cls}'></div>"
            f"<div class='tier-label {cls}'>{label}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div class='kolam-divider'><div class='kolam-line'></div><div class='kolam-diamond'></div><div class='kolam-line'></div></div>", unsafe_allow_html=True)

    # Scraping Tiers
    st.markdown(
        "<div style='font-size:10px;letter-spacing:2px;text-transform:uppercase;"
        "color:#7A6540;margin-bottom:8px;'>🕷️ வலை சேகரிப்பு · Scraping</div>",
        unsafe_allow_html=True,
    )
    scrape_tiers = [
        ("Crawl4AI · Free · Unlimited", True),
        ("ScraperAPI · JS Rendering",   engine.scraper_enabled),
        ("Standard Requests · Fallback", True),
    ]
    for label, active in scrape_tiers:
        cls = "active" if active else "inactive"
        st.markdown(
            f"<div class='tier-row'>"
            f"<div class='tier-dot {cls}'></div>"
            f"<div class='tier-label {cls}'>{label}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div class='kolam-divider'><div class='kolam-line'></div><div class='kolam-diamond'></div><div class='kolam-line'></div></div>", unsafe_allow_html=True)

    # Memory
    st.markdown(
        "<div style='font-size:10px;letter-spacing:2px;text-transform:uppercase;"
        "color:#7A6540;margin-bottom:8px;'>💬 நினைவகம் · Memory</div>",
        unsafe_allow_html=True,
    )
    st.session_state.memory_enabled = st.toggle(
        "உரையாடல் நினைவு · Conversation Memory",
        value=st.session_state.memory_enabled,
    )
    turns = len(engine.conversation_memory) // 2
    st.markdown(
        f"<div style='font-size:11px;color:#7A6540;margin-top:4px;'>"
        f"நடப்பு திருப்பங்கள் · Active turns: "
        f"<b style='color:#C8922A;'>{turns}</b></div>",
        unsafe_allow_html=True,
    )
    if st.button("🗑️ நினைவகம் அழி · Clear Memory", use_container_width=True):
        engine.clear_memory()
        st.session_state.chat_history = []
        st.rerun()

    st.markdown("<div class='kolam-divider'><div class='kolam-line'></div><div class='kolam-diamond'></div><div class='kolam-line'></div></div>", unsafe_allow_html=True)

    # Vector DB
    db_type = "Persistent ChromaDB" if hasattr(engine.chroma_client, "list_collections") else "In-Memory Store"
    st.markdown(
        f"<div style='font-size:10px;letter-spacing:2px;text-transform:uppercase;"
        f"color:#7A6540;margin-bottom:6px;'>🗄️ தரவுத்தளம் · Vector DB</div>"
        f"<div style='font-size:12px;color:#A07830;'>{db_type}</div>",
        unsafe_allow_html=True,
    )
    if engine._cached_url:
        short = engine._cached_url[:38] + "..." if len(engine._cached_url) > 38 else engine._cached_url
        st.markdown(
            f"<div style='font-size:10px;color:#6A5530;margin-top:4px;word-break:break-all;'>"
            f"✓ {short}</div>",
            unsafe_allow_html=True,
        )
    if st.button("🗑️ தரவு அழி · Clear Cache", use_container_width=True):
        try:
            engine.chroma_client.delete_collection(name=engine._cached_collection)
        except Exception:
            pass
        engine._cached_url = None
        st.session_state.last_url = ""
        st.rerun()

    st.markdown("<div class='kolam-divider'><div class='kolam-line'></div><div class='kolam-diamond'></div><div class='kolam-line'></div></div>", unsafe_allow_html=True)

    with st.expander("🔑 API விசைகள் · Keys"):
        keys = {
            "GEMINI": bool(engine.gemini_api_key),
            "GROQ":   bool(engine.groq_api_key),
            "AI/ML":  bool(engine.aiml_api_key),
            "SCRAPER":bool(engine.scraper_api_key),
            "GITHUB": bool(engine.github_token),
            "OLLAMA": engine.ollama_enabled,
        }
        for k, v in keys.items():
            icon  = "✓" if v else "✗"
            color = "#C8922A" if v else "#4A3520"
            st.markdown(
                f"<div style='font-size:11px;color:{color};padding:2px 0;'>{icon} {k}</div>",
                unsafe_allow_html=True,
            )

    st.markdown(
        "<div style='text-align:center;font-size:10px;color:#3A2810;"
        "padding-top:16px;letter-spacing:1px;'>"
        "கரிகால சோழன் கட்டிய கல்லணை போல்<br>"
        "<i>Built to last like the Grand Anicut</i></div>",
        unsafe_allow_html=True,
    )

# =============================================================================
# MAIN TABS
# =============================================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💬 AI உதவியாளர்",
    "🔗 பல URL RAG",
    "🐙 GitHub பகுப்பாய்வு",
    "🔍 Tech Stack கண்டறிவு",
    "⚙️ குறியீடு உருவாக்கம்",
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — AI CHAT AGENT
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("""
    <div class="tab-section-title">💬 AI உரையாடல் · Intelligent Chat Agent</div>
    <div class="tab-section-sub">
        உங்கள் திட்டத்தின் ஆவணங்களை AI படித்து பதிலளிக்கும் ·
        Scrapes live docs and answers from real context
    </div>
    """, unsafe_allow_html=True)

    col_url, col_opts = st.columns([3, 1])
    with col_url:
        target_url = st.text_input(
            "இணையதள முகவரி · Target URL (விரும்பினால் · optional)",
            placeholder="https://docs.fastapi.tiangolo.com  (leave blank for base knowledge)",
            value=st.session_state.last_url,
            key="tab1_url",
        )
    with col_opts:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        force_rescrape = st.checkbox("🔄 மீண்டும் சேகரி · Force re-scrape", value=False)

    # Mode banner
    if not target_url.strip():
        st.markdown("""
        <div class="mode-banner">
            <span class="mode-label">🧠 அடிப்படை நிலை · Core Mode</span>
            &nbsp;—&nbsp; Base model knowledge · No scraping
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="mode-banner">
            <span class="mode-label">🌐 வலை நுண்ணறிவு · Web Intelligence Mode</span>
            &nbsp;—&nbsp; Live scraping active · {('Crawl4AI + ScraperAPI' if engine.scraper_enabled else 'Crawl4AI + Requests')}
        </div>""", unsafe_allow_html=True)

    # Chat history
    if st.session_state.chat_history:
        st.markdown(
            f"<div style='font-size:10px;letter-spacing:2px;text-transform:uppercase;"
            f"color:#7A6540;margin:14px 0 8px;'>"
            f"உரையாடல் வரலாறு · Conversation ({len(st.session_state.chat_history)} turns)</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div class='chat-scroll'>", unsafe_allow_html=True)
        for entry in st.session_state.chat_history:
            st.markdown(
                f"<div class='msg-user'>"
                f"<div class='msg-sender msg-sender-user'>நீங்கள் · You</div>"
                f"{entry['query']}"
                f"</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='msg-ai'>"
                f"<div class='msg-sender msg-sender-ai'>கரிகாலன் AI · Karikalan AI</div>"
                f"{entry['response']}"
                f"<div class='msg-meta'>"
                f"<span class='tag tag-model'>{entry['model_used']}</span>"
                f"<span class='tag tag-cache'>{entry['scrape_method']}</span>"
                f"</div></div>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    # Input
    st.markdown("<div class='kolam-divider'><div class='kolam-line'></div><div class='kolam-diamond'></div><div class='kolam-line'></div></div>", unsafe_allow_html=True)

    user_query = st.text_area(
        "உங்கள் கேள்வி · Your Query",
        placeholder="Ask anything about code, APIs, frameworks, architectures...\nகுறியீடு, API, கட்டமைப்பு — எதையும் கேளுங்கள்...",
        height=100,
        key="tab1_query",
    )

    col_run, col_clear = st.columns([4, 1])
    with col_run:
        run_btn = st.button("🏛️ AI-ஐ இயக்கு · Execute Agent", use_container_width=True, key="tab1_run")
    with col_clear:
        if st.button("🗑️ அழி · Clear", use_container_width=True, key="tab1_clr"):
            st.session_state.chat_history = []
            engine.clear_memory()
            st.rerun()

    if run_btn:
        if not user_query.strip():
            st.error("கேள்வி உள்ளிடவும் · Please enter a query.")
        else:
            url_to_use = target_url.strip() or None
            spinner_msg = (
                "🌐 வலை பக்கங்களை சேகரிக்கிறோம் · Scraping live documentation..."
                if url_to_use else
                "🧠 கரிகாலன் AI சிந்திக்கிறது · Processing..."
            )
            with st.spinner(spinner_msg):
                response_text, context_payload, scrape_method, model_used = engine.execute_live_agent_query(
                    user_query=user_query,
                    target_url=url_to_use,
                    force_rescrape=force_rescrape,
                    use_memory=st.session_state.memory_enabled,
                )

            if url_to_use:
                st.session_state.last_url = url_to_use

            st.session_state.chat_history.append({
                "query":        user_query,
                "response":     response_text,
                "scrape_method": scrape_method,
                "model_used":   model_used,
                "url":          url_to_use,
            })

            # Response display
            st.markdown(
                "<div style='font-size:10px;letter-spacing:2px;text-transform:uppercase;"
                "color:#7A6540;margin:18px 0 10px;'>கரிகாலன் AI பதில் · Response</div>",
                unsafe_allow_html=True,
            )
            turns = len(engine.conversation_memory) // 2
            meta_html = (
                f"<span class='tag tag-model'>{model_used}</span>"
                f"<span class='tag tag-cache'>{scrape_method}</span>"
            )
            if st.session_state.memory_enabled:
                meta_html += f"<span class='tag tag-memory'>நினைவு · {turns} turns</span>"
            st.markdown(f"<div style='margin-bottom:10px;'>{meta_html}</div>", unsafe_allow_html=True)
            st.markdown(response_text)

            with st.expander("🔍 மூல சூழல் · Retrieved Context"):
                st.text_area(
                    "",
                    value=context_payload or "[சூழல் இல்லை · No context — running on base knowledge]",
                    disabled=True, height=160,
                )
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — MULTI-URL RAG
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("""
    <div class="tab-section-title">🔗 பல URL அறிவுத்தளம் · Multi-URL Knowledge Base</div>
    <div class="tab-section-sub">
        பல இணையதளங்களை சேகரித்து ஒரே கேள்வியில் பதிலளிக்கவும் ·
        Scrape multiple URLs and query across all of them
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="mode-banner">
        <span class="mode-label">📡 பல மூல நுண்ணறிவு · Multi-Source Intelligence</span>
        &nbsp;—&nbsp; Each URL scraped via 3-tier fallback · Merged into one ChromaDB index
    </div>""", unsafe_allow_html=True)

    multi_urls = st.text_area(
        "இணையதள முகவரிகள் · URLs (ஒவ்வொரு வரியில் · one per line)",
        placeholder="https://docs.fastapi.tiangolo.com\nhttps://docs.pydantic.dev\nhttps://www.uvicorn.org",
        height=120,
    )
    multi_query = st.text_area(
        "கேள்வி · Query",
        placeholder="Compare authentication approaches across these frameworks...",
        height=80,
    )

    if st.button("🏛️ சேகரி மற்றும் கேள் · Scrape All + Query", use_container_width=True):
        urls = [u.strip() for u in multi_urls.strip().splitlines() if u.strip()]
        if not urls:
            st.error("குறைந்தது ஒரு URL உள்ளிடவும் · Enter at least one URL.")
        elif not multi_query.strip():
            st.error("கேள்வி உள்ளிடவும் · Enter a query.")
        else:
            with st.spinner(f"🌐 {len(urls)} URL-களை சேகரிக்கிறோம்..."):
                chunks, summary = engine.scrape_multiple_urls(urls)

            st.markdown(
                "<div style='font-size:10px;letter-spacing:2px;color:#7A6540;margin:12px 0 6px;'>"
                "சேகரிப்பு முடிவுகள் · SCRAPE RESULTS</div>",
                unsafe_allow_html=True,
            )
            for line in summary.splitlines():
                if line.startswith("✅"):
                    st.success(line)
                elif line.startswith("❌"):
                    st.error(line)

            if chunks:
                with st.spinner("🧠 ஒருங்கிணைந்த அறிவுத்தளத்தை வினவுகிறோம்..."):
                    context_payload = engine.query_vector_context("zeravane_multi_url", multi_query, n_results=5)
                    sys_msg = (
                        "You are Karikalan AI (கரிகாலன் AI), a multi-source web intelligence agent. "
                        "Answer using merged content from all provided URLs. Cite source URLs when possible."
                    )
                    prompt = (
                        f"Sources: {', '.join(urls)}\n\n"
                        f"=== MERGED CONTENT ===\n{context_payload}\n\n"
                        f"=== QUESTION ===\n{multi_query}"
                    )
                    response_text, model_used = engine._infer(sys_msg, prompt)

                st.markdown(
                    "<div style='font-size:10px;letter-spacing:2px;color:#7A6540;margin:16px 0 10px;'>"
                    "பதில் · RESPONSE</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(f"<span class='tag tag-model'>{model_used}</span>", unsafe_allow_html=True)
                st.markdown(response_text)
            else:
                st.warning("எந்த URL-உம் வெற்றிகரமாக சேகரிக்கப்படவில்லை · No URLs scraped successfully.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — GITHUB ANALYZER
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("""
    <div class="tab-section-title">🐙 GitHub பகுப்பாய்வு · Repository Analyzer</div>
    <div class="tab-section-sub">
        எந்த GitHub திட்டத்தையும் ஆழமாக பகுப்பாய்வு செய்யவும் ·
        Deep-dive any public GitHub repo — README, file tree, metadata
    </div>
    """, unsafe_allow_html=True)

    github_url = st.text_input(
        "GitHub திட்ட முகவரி · Repository URL",
        placeholder="https://github.com/tiangolo/fastapi",
    )
    github_query = st.text_area(
        "கேள்வி · Ask about this repo",
        placeholder="How do I get started? What's the architecture? What does this project do?",
        height=80,
    )

    if st.button("🏛️ திட்டம் பகுப்பாய்வு · Analyze Repository", use_container_width=True):
        if not github_url.strip():
            st.error("GitHub முகவரி உள்ளிடவும் · Enter a GitHub URL.")
        elif not github_query.strip():
            st.error("கேள்வி உள்ளிடவும் · Enter a question.")
        else:
            with st.spinner("🐙 GitHub API மூலம் திட்டம் பெறுகிறோம்..."):
                repo_content, metadata = engine.analyze_github_repo(github_url.strip())

            if metadata:
                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric("⭐ நட்சத்திரங்கள்", f"{metadata.get('stars', 0):,}")
                m2.metric("🍴 கிளைகள்",       f"{metadata.get('forks', 0):,}")
                m3.metric("🐛 பிழைகள்",       f"{metadata.get('open_issues', 0):,}")
                m4.metric("💻 மொழி",          metadata.get("language", "N/A"))
                m5.metric("📄 உரிமம்",         metadata.get("license", "N/A"))

                if metadata.get("description"):
                    st.markdown(
                        f"<div class='mode-banner'>{metadata['description']}</div>",
                        unsafe_allow_html=True,
                    )
                if metadata.get("topics"):
                    badges = "".join(f"<span class='topic-badge'>{t}</span>" for t in metadata["topics"][:10])
                    st.markdown(badges, unsafe_allow_html=True)

            if not repo_content.startswith(("GitHub_Error", "Invalid")):
                with st.spinner("🧠 பகுப்பாய்வு செய்கிறோம்..."):
                    context = engine.query_vector_context("zeravane_github", github_query, n_results=4) or repo_content[:7000]
                    sys_msg = (
                        "You are Karikalan AI (கரிகாலன் AI), a GitHub repository analyst. "
                        "Answer from the repository data: README, file tree, metadata. "
                        "Be specific — cite file names and README sections."
                    )
                    prompt = (
                        f"Repository: {github_url.strip()}\n\n"
                        f"=== REPO DATA ===\n{context}\n\n"
                        f"=== QUESTION ===\n{github_query}"
                    )
                    response_text, model_used = engine._infer(sys_msg, prompt)

                st.markdown(
                    "<div style='font-size:10px;letter-spacing:2px;color:#7A6540;margin:16px 0 10px;'>"
                    "பகுப்பாய்வு பதில் · ANALYSIS</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(f"<span class='tag tag-model'>{model_used}</span>", unsafe_allow_html=True)
                st.markdown(response_text)

                with st.expander("📁 மூல திட்ட தரவு · Raw Repo Data"):
                    st.text_area("", value=repo_content[:4000], disabled=True, height=220)
            else:
                st.error(f"பிழை · Failed: {repo_content}")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — TECH STACK DETECTOR
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown("""
    <div class="tab-section-title">🔍 தொழில்நுட்ப அடுக்கு கண்டறிவு · Tech Stack Detector</div>
    <div class="tab-section-sub">
        எந்த இணையதளத்தின் தொழில்நுட்பங்களையும் AI மூலம் கண்டறியவும் ·
        Scrape any site and detect its full technology stack
    </div>
    """, unsafe_allow_html=True)

    stack_url = st.text_input(
        "இணையதள முகவரி · Website URL",
        placeholder="https://vercel.com  or  https://github.com/tiangolo/fastapi",
    )

    if st.button("🔍 தொழில்நுட்பங்கள் கண்டறி · Detect Stack", use_container_width=True):
        if not stack_url.strip():
            st.error("URL உள்ளிடவும் · Enter a URL.")
        else:
            with st.spinner("🌐 இணையதளத்தை சேகரிக்கிறோம் மற்றும் பகுப்பாய்கிறோம்..."):
                raw_content, scrape_method = engine.scrape_live_url(stack_url.strip())
                stack_report = engine.detect_tech_stack(raw_content, stack_url.strip())

            st.markdown(
                f"<div style='margin-bottom:12px;'>"
                f"<span class='tag tag-cache'>{scrape_method}</span></div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div style='font-size:10px;letter-spacing:2px;color:#7A6540;margin:0 0 10px;'>"
                "கண்டறிந்த தொழில்நுட்பங்கள் · DETECTED STACK</div>",
                unsafe_allow_html=True,
            )
            st.markdown(stack_report)

            with st.expander("🔍 சேகரிக்கப்பட்ட உள்ளடக்கம் · Raw Scraped Content"):
                st.text_area("", value=raw_content[:2500], disabled=True, height=150)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 5 — CODE GENERATOR
# ─────────────────────────────────────────────────────────────────────────────
with tab5:
    st.markdown("""
    <div class="tab-section-title">⚙️ குறியீடு உருவாக்கம் · Code Generator from Live Docs</div>
    <div class="tab-section-sub">
        ஆவண URL கொடுங்கள் — AI நேரடியாக படித்து குறியீடு உருவாக்கும் ·
        Paste any docs URL, Karikalan AI scrapes and generates production-ready code
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="mode-banner">
        <span class="mode-label">🤖 நேரடி ஆவணங்கள் → குறியீடு · Live Docs → Production Code</span>
        &nbsp;—&nbsp; Crawl4AI fetches docs · RAG indexes content · LLM generates boilerplate
    </div>""", unsafe_allow_html=True)

    codegen_url = st.text_input(
        "ஆவண முகவரி · Documentation URL",
        placeholder="https://docs.stripe.com/api  or  https://docs.fastapi.tiangolo.com",
    )
    codegen_request = st.text_area(
        "என்ன குறியீடு வேண்டும் · What code should be generated?",
        placeholder="Create a complete REST API with CRUD operations and JWT authentication...",
        height=80,
    )
    codegen_language = st.selectbox(
        "மொழி · Target Language",
        ["Python", "TypeScript", "JavaScript", "Go", "Rust", "Java", "C#", "PHP", "Ruby", "Kotlin"],
    )

    if st.button("⚙️ குறியீடு உருவாக்கு · Generate Code", use_container_width=True):
        if not codegen_url.strip():
            st.error("ஆவண URL உள்ளிடவும் · Enter a documentation URL.")
        elif not codegen_request.strip():
            st.error("என்ன குறியீடு வேண்டும் என்று சொல்லவும் · Describe what code you want.")
        else:
            with st.spinner(f"🌐 ஆவணங்கள் சேகரிக்கிறோம் · {codegen_language} குறியீடு உருவாக்குகிறோம்..."):
                generated_code, scrape_method, model_used = engine.generate_code_from_docs(
                    docs_url=codegen_url.strip(),
                    generation_request=codegen_request.strip(),
                    language=codegen_language,
                )

            st.markdown(
                f"<div style='margin-bottom:12px;'>"
                f"<span class='tag tag-model'>{model_used}</span>"
                f"<span class='tag tag-cache'>{scrape_method}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div style='font-size:10px;letter-spacing:2px;color:#7A6540;margin:0 0 10px;'>"
                f"உருவாக்கப்பட்ட {codegen_language} குறியீடு · GENERATED CODE</div>",
                unsafe_allow_html=True,
            )
            st.markdown(generated_code)

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("<div class='kolam-divider'><div class='kolam-line'></div><div class='kolam-diamond'></div><div style='font-size:9px;letter-spacing:2px;color:#3A2810;white-space:nowrap;'>சோழ பேரரசு · CHOLA EMPIRE</div><div class='kolam-diamond'></div><div class='kolam-line'></div></div>", unsafe_allow_html=True)
st.markdown("""
<p style='text-align:center;font-size:10px;color:#3A2810;letter-spacing:2px;padding:6px 0;'>
கரிகாலன் AI · கரிகால சோழன் நினைவில் ·
Built by Franklin Josva · Dindigul, Tamil Nadu
</p>
""", unsafe_allow_html=True)
