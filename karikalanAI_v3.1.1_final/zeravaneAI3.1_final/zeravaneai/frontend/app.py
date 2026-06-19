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
# LANGUAGE FRONTEND DICTIONARY MAPPING
# =============================================================================
UI_TRANSLATIONS = {
    "English": {
        "title": "KARIKALAN AI",
        "tagline": "Enterprise AI Coding Platform · 4-Tier LLM · Tamil Chola Heritage",
        "lbl_llm_tiers": "🧠 LLM TIERS",
        "lbl_scraping": "🕷️ SCRAPING TIERS",
        "lbl_memory": "💬 CONVERSATION MEMORY",
        "lbl_memory_toggle": "Conversation Memory",
        "lbl_active_turns": "Active turns",
        "btn_clear_mem": "🗑️ Clear Memory",
        "lbl_vectordb": "🗄️ VECTOR DB",
        "btn_clear_cache": "🗑️ Clear Cache",
        "exp_api_keys": "🔑 API Keys",
        "tab_titles": ["💬 AI Assistant", "🔗 Multi-URL RAG", "🐙 GitHub Analyzer", "🔍 Tech Stack Detector", "⚙️ Code Generator"],
        
        # Tab 1
        "t1_title": "💬 AI Chat Agent",
        "t1_sub": "Scrapes live docs and answers from real context",
        "t1_url_label": "Target URL (optional)",
        "t1_url_placeholder": "https://docs.fastapi.tiangolo.com  (leave blank for base knowledge)",
        "t1_force_scrape": "🔄 Force re-scrape",
        "t1_banner_core": "🧠 Core Mode — Base model knowledge · No scraping",
        "t1_banner_web": "🌐 Web Intelligence Mode — Live scraping active",
        "t1_history_lbl": "Conversation History",
        "t1_query_lbl": "Your Query",
        "t1_query_placeholder": "Ask anything about code, APIs, frameworks, architectures...",
        "t1_btn_execute": "🏛️ Execute Agent",
        "t1_btn_clear": "🗑️ Clear",
        "t1_err_query": "Please enter a query.",
        "t1_resp_lbl": "Response",
        "t1_context_lbl": "🔍 Retrieved Context",
        "t1_no_context": "[No context — running on base knowledge]",
        "t1_spinner_scrape": "🌐 Scraping live documentation...",
        "t1_spinner_think": "🧠 Karikalan AI is thinking...",

        # Tab 2
        "t2_title": "🔗 Multi-URL Knowledge Base",
        "t2_sub": "Scrape multiple URLs and query across all of them",
        "t2_banner": "📡 Multi-Source Intelligence — Each URL scraped via 3-tier fallback · Merged into one ChromaDB index",
        "t2_urls_lbl": "URLs (one per line)",
        "t2_urls_placeholder": "https://docs.fastapi.tiangolo.com\nhttps://docs.pydantic.dev",
        "t2_query_lbl": "Query",
        "t2_query_placeholder": "Compare authentication approaches across these frameworks...",
        "t2_btn_scrape": "🏛️ Scrape All + Query",
        "t2_err_url": "Enter at least one URL.",
        "t2_err_query": "Enter a query.",
        "t2_spinner_scrape": "🌐 Scraping URLs...",
        "t2_results_lbl": "SCRAPE RESULTS",
        "t2_spinner_query": "🧠 Querying merged knowledge base...",
        "t2_resp_lbl": "RESPONSE",
        "t2_err_no_scrape": "No URLs scraped successfully.",

        # Tab 3
        "t3_title": "🐙 GitHub Repository Analyzer",
        "t3_sub": "Deep-dive any public GitHub repo — README, file tree, metadata",
        "t3_url_lbl": "Repository URL",
        "t3_url_placeholder": "https://github.com/tiangolo/fastapi",
        "t3_query_lbl": "Ask about this repo",
        "t3_query_placeholder": "How do I get started? What's the architecture?",
        "t3_btn_analyze": "🏛️ Analyze Repository",
        "t3_err_url": "Enter a GitHub URL.",
        "t3_err_query": "Enter a question.",
        "t3_spinner_fetch": "🐙 Fetching repository via GitHub API...",
        "t3_m1": "⭐ Stars", "t3_m2": "🍴 Forks", "t3_m3": "🐛 Issues", "t3_m4": "💻 Language", "t3_m5": "📄 License",
        "t3_spinner_analyze": "🧠 Analyzing...",
        "t3_resp_lbl": "ANALYSIS",
        "t3_raw_lbl": "📁 Raw Repo Data",

        # Tab 4
        "t4_title": "🔍 Tech Stack Detector",
        "t4_sub": "Scrape any site and detect its full technology stack",
        "t4_url_lbl": "Website URL",
        "t4_url_placeholder": "https://vercel.com",
        "t4_btn_detect": "🔍 Detect Stack",
        "t4_err_url": "Enter a URL.",
        "t4_spinner": "🌐 Scraping and analyzing website...",
        "t4_results_lbl": "DETECTED STACK",
        "t4_raw_lbl": "🔍 Raw Scraped Content",

        # Tab 5
        "t5_title": "⚙️ Code Generator from Live Docs",
        "t5_sub": "Paste any docs URL, Karikalan AI scrapes and generates production-ready code",
        "t5_banner": "🤖 Live Docs → Production Code — Crawl4AI fetches docs · RAG indexes content · LLM generates boilerplate",
        "t5_url_lbl": "Documentation URL",
        "t5_url_placeholder": "https://docs.stripe.com/api",
        "t5_request_lbl": "What code should be generated?",
        "t5_request_placeholder": "Create a complete REST API with CRUD operations and JWT authentication...",
        "t5_lang_lbl": "Target Language",
        "t5_btn_gen": "⚙️ Generate Code",
        "t5_err_url": "Enter a documentation URL.",
        "t5_err_req": "Describe what code you want.",
        "t5_spinner": "🌐 Scraping docs & generating code...",
        "t5_results_lbl": "GENERATED CODE",
        
        "sys_instruction_suffix": "Respond strictly in clear, professional English."
    },
    "Tamil (தமிழ்)": {
        "title": "கரிகாலன் AI",
        "tagline": "நிறுவன அளவிலான செயற்கை நுண்ணறிவு குறியீட்டு தளம் · தமிழ் சோழர் பாரம்பரியம்",
        "lbl_llm_tiers": "🧠 LLM படிநிலைகள் · Tiers",
        "lbl_scraping": "🕷️ வலை சேகரிப்பு · Scraping",
        "lbl_memory": "💬 நினைவகம் · Memory",
        "lbl_memory_toggle": "உரையாடல் நினைவு · Conversation Memory",
        "lbl_active_turns": "நடப்பு திருப்பங்கள்",
        "btn_clear_mem": "🗑️ நினைவகம் அழி · Clear Memory",
        "lbl_vectordb": "🗄️ தரவுத்தளம் · Vector DB",
        "btn_clear_cache": "🗑️ தரவு அழி · Clear Cache",
        "exp_api_keys": "🔑 API விசைகள் · Keys",
        "tab_titles": ["💬 AI உதவியாளர்", "🔗 பல URL RAG", "🐙 GitHub பகுப்பாய்வு", "🔍 Tech Stack கண்டறிவு", "⚙️ குறியீடு உருவாக்கம்"],
        
        # Tab 1
        "t1_title": "💬 AI உரையாடல் · Intelligent Chat Agent",
        "t1_sub": "உங்கள் திட்டத்தின் ஆவணங்களை AI படித்து பதிலளிக்கும்",
        "t1_url_label": "இணையதள முகவரி · Target URL (விரும்பினால்)",
        "t1_url_placeholder": "https://docs.fastapi.tiangolo.com  (அடிப்படை அறிவுக்கு இதை காலியாக விடவும்)",
        "t1_force_scrape": "🔄 மீண்டும் சேகரி · Force re-scrape",
        "t1_banner_core": "🧠 அடிப்படை நிலை — Base model knowledge · No scraping",
        "t1_banner_web": "🌐 வலை நுண்ணறிவு நிலை — Live scraping active",
        "t1_history_lbl": "உரையாடல் வரலாறு",
        "t1_query_lbl": "உங்கள் கேள்வி · Your Query",
        "t1_query_placeholder": "குறியீடு, API, கட்டமைப்பு — எதையும் கேளுங்கள்...",
        "t1_btn_execute": "🏛️ AI-ஐ இயக்கு · Execute Agent",
        "t1_btn_clear": "🗑️ அழி · Clear",
        "t1_err_query": "கேள்வி உள்ளிடவும் · Please enter a query.",
        "t1_resp_lbl": "கரிகாலன் AI பதில்",
        "t1_context_lbl": "🔍 மூல சூழல் · Retrieved Context",
        "t1_no_context": "[சூழல் இல்லை · No context — running on base knowledge]",
        "t1_spinner_scrape": "🌐 வலை பக்கங்களை சேகரிக்கிறோம்...",
        "t1_spinner_think": "🧠 கரிகாலன் AI சிந்திக்கிறது...",

        # Tab 2
        "t2_title": "🔗 பல URL அறிவுத்தளம் · Multi-URL Knowledge Base",
        "t2_sub": "பல இணையதளங்களை சேகரித்து ஒரே கேள்வியில் பதிலளிக்கவும்",
        "t2_banner": "📡 பல மூல நுண்ணறிவு — ஒவ்வொரு URL-உம் 3-அடுக்கு மல்டி-ஃபால்பேக் மூலம் சேகரிக்கப்பட்டு, ஒரு ChromaDB குறியீட்டில் இணைக்கப்படுகிறது",
        "t2_urls_lbl": "இணையதள முகவரிகள் (ஒவ்வொரு வரியில்)",
        "t2_urls_placeholder": "https://docs.fastapi.tiangolo.com\nhttps://docs.pydantic.dev",
        "t2_query_lbl": "கேள்வி",
        "t2_query_placeholder": "இந்த கட்டமைப்புகளில் அங்கீகார அணுகுமுறைகளை ஒப்பிடுக...",
        "t2_btn_scrape": "🏛️ சேகரி மற்றும் கேள் · Scrape All + Query",
        "t2_err_url": "குறைந்தது ஒரு URL உள்ளிடவும்.",
        "t2_err_query": "கேள்வி உள்ளிடவும்.",
        "t2_spinner_scrape": "🌐 URL-களை சேகரிக்கிறோம்...",
        "t2_results_lbl": "சேகரிப்பு முடிவுகள்",
        "t2_spinner_query": "🧠 ஒருங்கிணைந்த அறிவுத்தளத்தை வினவுகிறோம்...",
        "t2_resp_lbl": "பதில்",
        "t2_err_no_scrape": "எந்த URL-உம் வெற்றிகரமாக சேகரிக்கப்படவில்லை.",

        # Tab 3
        "t3_title": "🐙 GitHub பகுப்பாய்வு · Repository Analyzer",
        "t3_sub": "எந்த GitHub திட்டத்தையும் ஆழமாக பகுப்பாய்வு செய்யவும் — README, கோப்பு மரம், மெட்டாடேட்டா",
        "t3_url_lbl": "GitHub திட்ட முகவரி",
        "t3_url_placeholder": "https://github.com/tiangolo/fastapi",
        "t3_query_lbl": "இந்த களஞ்சியத்தைப் பற்றிக் கேளுங்கள்",
        "t3_query_placeholder": "நான் எப்படி தொடங்குவது? இதன் கட்டமைப்பு என்ன?",
        "t3_btn_analyze": "🏛️ திட்டம் பகுப்பாய்வு · Analyze Repository",
        "t3_err_url": "GitHub முகவரி உள்ளிடவும்.",
        "t3_err_query": "கேள்வி உள்ளிடவும்.",
        "t3_spinner_fetch": "🐙 GitHub API மூலம் திட்டம் பெறுகிறோம்...",
        "t3_m1": "⭐ நட்சத்திரங்கள்", "t3_m2": "🍴 கிளைகள்", "t3_m3": "🐛 பிழைகள்", "t3_m4": "💻 மொழி", "t3_m5": "📄 உரிமம்",
        "t3_spinner_analyze": "🧠 பகுப்பாய்வு செய்கிறோம்...",
        "t3_resp_lbl": "பகுப்பாய்வு பதில்",
        "t3_raw_lbl": "📁 மூல திட்ட தரவு",

        # Tab 4
        "t4_title": "🔍 தொழில்நுட்ப அடுக்கு கண்டறிவு · Tech Stack Detector",
        "t4_sub": "எந்த இணையதளத்தின் தொழில்நுட்பங்களையும் AI மூலம் கண்டறியவும்",
        "t4_url_lbl": "இணையதள முகவரி",
        "t4_url_placeholder": "https://vercel.com",
        "t4_btn_detect": "🔍 தொழில்நுட்பங்கள் கண்டறி · Detect Stack",
        "t4_err_url": "URL உள்ளிடவும்.",
        "t4_spinner": "🌐 இணையதளத்தை சேகரிக்கிறோம் மற்றும் பகுப்பாய்கிறோம்...",
        "t4_results_lbl": "கண்டறிந்த தொழில்நுட்பங்கள்",
        "t4_raw_lbl": "🔍 சேகரிக்கப்பட்ட உள்ளடக்கம்",

        # Tab 5
        "t5_title": "⚙️ குறியீடு உருவாக்கம் · Code Generator from Live Docs",
        "t5_sub": "ஆவண URL கொடுங்கள் — AI நேரடியாக படித்து குறியீடு உருவாக்கும்",
        "t5_banner": "🤖 நேரடி ஆவணங்கள் → குறியீடு — Crawl4AI தரவை எடுக்கிறது · RAG உள்ளடக்கத்தை வரிசைப்படுத்துகிறது · LLM பொதுவான குறியீட்டை உருவாக்குகிறது",
        "t5_url_lbl": "ஆவண முகவரி",
        "t5_url_placeholder": "https://docs.stripe.com/api",
        "t5_request_lbl": "என்ன குறியீடு வேண்டும்?",
        "t5_request_placeholder": "CRUD செயல்பாடுகள் மற்றும் JWT அங்கீகாரத்துடன் முழுமையான REST API ஐ உருவாக்கவும்...",
        "t5_lang_lbl": "மொழி",
        "t5_btn_gen": "⚙️ குறியீடு உருவாக்கு · Generate Code",
        "t5_err_url": "ஆவண URL உள்ளிடவும்.",
        "t5_err_req": "என்ன குறியீடு வேண்டும் என்று சொல்லவும்.",
        "t5_spinner": "🌐 ஆவணங்கள் சேகரிக்கிறோம் & குறியீடு உருவாக்குகிறோம்...",
        "t5_results_lbl": "உருவாக்கப்பட்ட குறியீடு",

        "sys_instruction_suffix": "நீங்கள் ஒரு திறமையான கணினி மென்பொருள் முகவர். ஆங்கில வார்த்தைகளைத் தவிர்த்து, தூய தமிழில் மட்டுமே துல்லியமாக பதிலளிக்கவும்."
    },
    "Tanglish": {
        "title": "KARIKALAN AI",
        "tagline": "Enterprise AI Coding Platform · 4-Tier LLM · Tamil Chola Heritage",
        "lbl_llm_tiers": "🧠 LLM TIERS / படிநிலைகள்",
        "lbl_scraping": "🕷️ SCRAPING / வலை சேகரிப்பு",
        "lbl_memory": "💬 MEMORY / நினைவகம்",
        "lbl_memory_toggle": "Conversation Memory / உரையாடல் நினைவு",
        "lbl_active_turns": "Active turns / திருப்பங்கள்",
        "btn_clear_mem": "🗑️ Clear Memory / அழி",
        "lbl_vectordb": "🗄️ VECTOR DB / தரவுத்தளம்",
        "btn_clear_cache": "🗑️ Clear Cache / தற்காலிக சேமிப்பை அழி",
        "exp_api_keys": "🔑 API Keys / விசைகள்",
        "tab_titles": ["💬 AI Assistant", "🔗 Multi-URL RAG", "🐙 GitHub Analyzer", "🔍 Tech Stack Detector", "⚙️ Code Generator"],
        
        # Tab 1
        "t1_title": "💬 AI Chat Agent (Tanglish)",
        "t1_sub": "Scrapes live docs and answers with blended context",
        "t1_url_label": "Target URL / இணையதள முகவரி (optional)",
        "t1_url_placeholder": "https://docs.fastapi.tiangolo.com  (leave blank for base knowledge)",
        "t1_force_scrape": "🔄 Force re-scrape / மீண்டும் சேகரி",
        "t1_banner_core": "🧠 Core Mode — Base model knowledge · No scraping active",
        "t1_banner_web": "🌐 Web Intelligence Mode — Live scraping integration active",
        "t1_history_lbl": "Conversation History / உரையாடல் வரலாறு",
        "t1_query_lbl": "Your Query / உங்க கேள்வி",
        "t1_query_placeholder": "Code, APIs, frameworks, கட்டமைப்புகள் பத்தி எது வேணாலும் கேளுங்கள்...",
        "t1_btn_execute": "🏛️ Execute Agent / இயக்கு",
        "t1_btn_clear": "🗑️ Clear / அழி",
        "t1_err_query": "Please enter a query / கேள்வி உள்ளிடவும்.",
        "t1_resp_lbl": "Karikalan AI Response",
        "t1_context_lbl": "🔍 Retrieved Context / மூல சூழல்",
        "t1_no_context": "[No context — running on base knowledge]",
        "t1_spinner_scrape": "🌐 Scraping live documentation / வலைப்பக்கத்தை சேகரிக்கிறோம்...",
        "t1_spinner_think": "🧠 Karikalan AI is thinking / யோசிக்கிறது...",

        # Tab 2
        "t2_title": "🔗 Multi-URL Knowledge Base",
        "t2_sub": "Scrape multiple URLs and query across all of them",
        "t2_banner": "📡 Multi-Source Intelligence — Each URL scraped via 3-tier fallback · Merged into one ChromaDB index",
        "t2_urls_lbl": "URLs / இணையதள முகவரிகள் (one per line)",
        "t2_urls_placeholder": "https://docs.fastapi.tiangolo.com\nhttps://docs.pydantic.dev",
        "t2_query_lbl": "Query / கேள்வி",
        "t2_query_placeholder": "Compare authentication approaches across these frameworks...",
        "t2_btn_scrape": "🏛️ Scrape All + Query",
        "t2_err_url": "Enter at least one URL / ஒரு URL ஆவது கொடுங்க.",
        "t2_err_query": "Enter a query / கேள்வி உள்ளிடவும்.",
        "t2_spinner_scrape": "🌐 Scraping URLs / சேகரிக்கிறோம்...",
        "t2_results_lbl": "Scrape Results",
        "t2_spinner_query": "🧠 Querying merged knowledge base / தேடுகிறோம்...",
        "t2_resp_lbl": "RESPONSE / பதில்",
        "t2_err_no_scrape": "No URLs scraped successfully.",

        # Tab 3
        "t3_title": "🐙 GitHub Repository Analyzer",
        "t3_sub": "Deep-dive any public GitHub repo — README, file tree, metadata",
        "t3_url_lbl": "Repository URL",
        "t3_url_placeholder": "https://github.com/tiangolo/fastapi",
        "t3_query_lbl": "Ask about this repo",
        "t3_query_placeholder": "How do I get started? What's the architecture?",
        "t3_btn_analyze": "🏛️ Analyze Repository",
        "t3_err_url": "Enter a GitHub URL.",
        "t3_err_query": "Enter a question.",
        "t3_spinner_fetch": "🐙 Fetching repo details via GitHub API...",
        "t3_m1": "⭐ Stars", "t3_m2": "🍴 Forks", "t3_m3": "🐛 Issues", "t3_m4": "💻 Language", "t3_m5": "📄 License",
        "t3_spinner_analyze": "🧠 Analyzing / பகுப்பாய்வு செய்கிறோம்...",
        "t3_resp_lbl": "ANALYSIS / பதில்",
        "t3_raw_lbl": "📁 Raw Repo Data",

        # Tab 4
        "t4_title": "🔍 Tech Stack Detector",
        "t4_sub": "Scrape any site and detect its full technology stack",
        "t4_url_lbl": "Website URL",
        "t4_url_placeholder": "https://vercel.com",
        "t4_btn_detect": "🔍 Detect Stack",
        "t4_err_url": "Enter a URL.",
        "t4_spinner": "🌐 Scraping and analyzing website...",
        "t4_results_lbl": "Detected Stack",
        "t4_raw_lbl": "🔍 Raw Scraped Content",

        # Tab 5
        "t5_title": "⚙️ Code Generator from Live Docs",
        "t5_sub": "Paste any docs URL, Karikalan AI scrapes and generates production-ready code",
        "t5_banner": "🤖 Live Docs → Production Code — Crawl4AI fetches docs · RAG indexes content · LLM generates boilerplate",
        "t5_url_lbl": "Documentation URL",
        "t5_url_placeholder": "https://docs.stripe.com/api",
        "t5_request_lbl": "What code should be generated?",
        "t5_request_placeholder": "Create a complete REST API with CRUD operations and JWT authentication...",
        "t5_lang_lbl": "Target Language",
        "t5_btn_gen": "⚙️ Generate Code",
        "t5_err_url": "Enter a documentation URL.",
        "t5_err_req": "Describe what code you want.",
        "t5_spinner": "🌐 Scraping docs & generating code...",
        "t5_results_lbl": "Generated Code",

        "sys_instruction_suffix": "You are a coding assistant agent. Respond in informal, chat-style conversational Tamil combined with English words (Tanglish). However, explicitly keep all technical keywords (like 'database', 'function', 'loop', 'api', 'class', 'variable') completely in English so developer workflows remain clear."
    }
}

# =============================================================================
# DESIGN SYSTEM — CHOLA HERITAGE PALETTE
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

/* ── Kolam Divider ── */
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

/* ── Info Cards ── */
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
# SIDEBAR (Rendered First to capture the selected layout state)
# =============================================================================
with st.sidebar:
    st.markdown("""
    <div class="sidebar-emblem">
        <span class="sidebar-glyph">🏛️</span>
        <span class="sidebar-name">KARIKALAN AI</span>
        <span class="sidebar-sub">கரிகாலன் · சோழ பேரரசு</span>
    </div>
    """, unsafe_allow_html=True)

    # LANGUAGE SELECTION WIDGET
    st.markdown(
        "<div style='font-size:10px;letter-spacing:2px;text-transform:uppercase;"
        "color:#7A6540;margin-bottom:8px;'>🌐 LANGUAGE / மொழி முறை</div>",
        unsafe_allow_html=True,
    )
    selected_lang = st.selectbox(
        "Language Selector",
        options=["English", "Tamil (தமிழ்)", "Tanglish"],
        index=0,
        label_visibility="collapsed"
    )
    
    # Map the translations context data frame globally
    tx = UI_TRANSLATIONS[selected_lang]

    st.markdown("<div class='kolam-divider'><div class='kolam-line'></div><div class='kolam-diamond'></div><div class='kolam-line'></div></div>", unsafe_allow_html=True)

    # LLM Tiers
    st.markdown(
        f"<div style='font-size:10px;letter-spacing:2px;text-transform:uppercase;"
        f"color:#7A6540;margin-bottom:8px;'>{tx['lbl_llm_tiers']}</div>",
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
        f"<div style='font-size:10px;letter-spacing:2px;text-transform:uppercase;"
        f"color:#7A6540;margin-bottom:8px;'>{tx['lbl_scraping']}</div>",
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
        f"<div style='font-size:10px;letter-spacing:2px;text-transform:uppercase;"
        f"color:#7A6540;margin-bottom:8px;'>{tx['lbl_memory']}</div>",
        unsafe_allow_html=True,
    )
    st.session_state.memory_enabled = st.toggle(
        tx['lbl_memory_toggle'],
        value=st.session_state.memory_enabled,
    )
    turns = len(engine.conversation_memory) // 2
    st.markdown(
        f"<div style='font-size:11px;color:#7A6540;margin-top:4px;'>"
        f"{tx['lbl_active_turns']}: "
        f"<b style='color:#C8922A;'>{turns}</b></div>",
        unsafe_allow_html=True,
    )
    if st.button(tx['btn_clear_mem'], use_container_width=True):
        engine.clear_memory()
        st.session_state.chat_history = []
        st.rerun()

    st.markdown("<div class='kolam-divider'><div class='kolam-line'></div><div class='kolam-diamond'></div><div class='kolam-line'></div></div>", unsafe_allow_html=True)

    # Vector DB
    db_type = "Persistent ChromaDB" if hasattr(engine.chroma_client, "list_collections") else "In-Memory Store"
    st.markdown(
        f"<div style='font-size:10px;letter-spacing:2px;text-transform:uppercase;"
        f"color:#7A6540;margin-bottom:6px;'>{tx['lbl_vectordb']}</div>"
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
    if st.button(tx['btn_clear_cache'], use_container_width=True):
        try:
            engine.chroma_client.delete_collection(name=engine._cached_collection)
        except Exception:
            pass
        engine._cached_url = None
        st.session_state.last_url = ""
        st.rerun()

    st.markdown("<div class='kolam-divider'><div class='kolam-line'></div><div class='kolam-diamond'></div><div class='kolam-line'></div></div>", unsafe_allow_html=True)

    with st.expander(tx['exp_api_keys']):
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
# HEADER
# =============================================================================
st.markdown(f"""
<div class="karikalan-header">
    <div class="title-tamil">{tx['title']}</div>
    <div class="title-sub-tamil">கரிகாலன் AI · கரிகால சோழன்</div>
    <div class="title-tagline">
        {tx['tagline']}
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
# MAIN TABS
# =============================================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs(tx["tab_titles"])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — AI CHAT AGENT
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown(f"""
    <div class="tab-section-title">{tx['t1_title']}</div>
    <div class="tab-section-sub">{tx['t1_sub']}</div>
    """, unsafe_allow_html=True)

    col_url, col_opts = st.columns([3, 1])
    with col_url:
        target_url = st.text_input(
            tx['t1_url_label'],
            placeholder=tx['t1_url_placeholder'],
            value=st.session_state.last_url,
            key="tab1_url",
        )
    with col_opts:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        force_rescrape = st.checkbox(tx['t1_force_scrape'], value=False)

    # Mode banner
    if not target_url.strip():
        st.markdown(f"""
        <div class="mode-banner">
            {tx['t1_banner_core']}
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="mode-banner">
            {tx['t1_banner_web']} &nbsp;—&nbsp; {('Crawl4AI + ScraperAPI' if engine.scraper_enabled else 'Crawl4AI + Requests')}
        </div>""", unsafe_allow_html=True)

    # Chat history
    if st.session_state.chat_history:
        st.markdown(
            f"<div style='font-size:10px;letter-spacing:2px;text-transform:uppercase;"
            f"color:#7A6540;margin:14px 0 8px;'>"
            f"{tx['t1_history_lbl']} ({len(st.session_state.chat_history)} turns)</div>",
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
        tx['t1_query_lbl'],
        placeholder=tx['t1_query_placeholder'],
        height=100,
        key="tab1_query",
    )

    col_run, col_clear = st.columns([4, 1])
    with col_run:
        run_btn = st.button(tx['t1_btn_execute'], use_container_width=True, key="tab1_run")
    with col_clear:
        if st.button(tx['t1_btn_clear'], use_container_width=True, key="tab1_clr"):
            st.session_state.chat_history = []
            engine.clear_memory()
            st.rerun()

    if run_btn:
        if not user_query.strip():
            st.error(tx['t1_err_query'])
        else:
            url_to_use = target_url.strip() or None
            spinner_msg = tx['t1_spinner_scrape'] if url_to_use else tx['t1_spinner_think']
            with st.spinner(spinner_msg):
                response_text, context_payload, scrape_method, model_used = engine.execute_live_agent_query(
                    user_query=user_query,
                    target_url=url_to_use,
                    force_rescrape=force_rescrape,
                    use_memory=st.session_state.memory_enabled,
                    language_suffix=tx['sys_instruction_suffix']
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
                f"<div style='font-size:10px;letter-spacing:2px;text-transform:uppercase;"
                f"color:#7A6540;margin:18px 0 10px;'>{tx['t1_resp_lbl']}</div>",
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

            with st.expander(tx['t1_context_lbl']):
                st.text_area(
                    "",
                    value=context_payload or tx['t1_no_context'],
                    disabled=True, height=160,
                )
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — MULTI-URL RAG
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown(f"""
    <div class="tab-section-title">{tx['t2_title']}</div>
    <div class="tab-section-sub">{tx['t2_sub']}</div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="mode-banner">
        {tx['t2_banner']}
    </div>""", unsafe_allow_html=True)

    multi_urls = st.text_area(
        tx['t2_urls_lbl'],
        placeholder=tx['t2_urls_placeholder'],
        height=120,
    )
    multi_query = st.text_area(
        tx['t2_query_lbl'],
        placeholder=tx['t2_query_placeholder'],
        height=80,
    )

    if st.button(tx['t2_btn_scrape'], use_container_width=True):
        urls = [u.strip() for u in multi_urls.strip().splitlines() if u.strip()]
        if not urls:
            st.error(tx['t2_err_url'])
        elif not multi_query.strip():
            st.error(tx['t2_err_query'])
        else:
            with st.spinner(tx['t2_spinner_scrape']):
                chunks, summary = engine.scrape_multiple_urls(urls)

            st.markdown(
                f"<div style='font-size:10px;letter-spacing:2px;color:#7A6540;margin:12px 0 6px;'>"
                f"{tx['t2_results_lbl']}</div>",
                unsafe_allow_html=True,
            )
            for line in summary.splitlines():
                if line.startswith("✅"):
                    st.success(line)
                elif line.startswith("❌"):
                    st.error(line)

            if chunks:
                with st.spinner(tx['t2_spinner_query']):
                    context_payload = engine.query_vector_context("zeravane_multi_url", multi_query, n_results=5)
                    sys_msg = (
                        "You are Karikalan AI (கரிகாலன் AI), a multi-source web intelligence agent. "
                        "Answer using merged content from all provided URLs. Cite source URLs when possible. "
                        f"{tx['sys_instruction_suffix']}"
                    )
                    prompt = (
                        f"Sources: {', '.join(urls)}\n\n"
                        f"=== MERGED CONTENT ===\n{context_payload}\n\n"
                        f"=== QUESTION ===\n{multi_query}"
                    )
                    response_text, model_used = engine._infer(sys_msg, prompt)

                st.markdown(
                    f"<div style='font-size:10px;letter-spacing:2px;color:#7A6540;margin:16px 0 10px;'>"
                    f"{tx['t2_resp_lbl']}</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(f"<span class='tag tag-model'>{model_used}</span>", unsafe_allow_html=True)
                st.markdown(response_text)
            else:
                st.warning(tx['t2_err_no_scrape'])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — GITHUB ANALYZER
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown(f"""
    <div class="tab-section-title">{tx['t3_title']}</div>
    <div class="tab-section-sub">{tx['t3_sub']}</div>
    """, unsafe_allow_html=True)

    github_url = st.text_input(
        tx['t3_url_lbl'],
        placeholder=tx['t3_url_placeholder'],
    )
    github_query = st.text_area(
        tx['t3_query_lbl'],
        placeholder=tx['t3_query_placeholder'],
        height=80,
    )

    if st.button(tx['t3_btn_analyze'], use_container_width=True):
        if not github_url.strip():
            st.error(tx['t3_err_url'])
        elif not github_query.strip():
            st.error(tx['t3_err_query'])
        else:
            with st.spinner(tx['t3_spinner_fetch']):
                repo_content, metadata = engine.analyze_github_repo(github_url.strip())

            if metadata:
                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric(tx['t3_m1'], f"{metadata.get('stars', 0):,}")
                m2.metric(tx['t3_m2'], f"{metadata.get('forks', 0):,}")
                m3.metric(tx['t3_m3'], f"{metadata.get('open_issues', 0):,}")
                m4.metric(tx['t3_m4'], metadata.get("language", "N/A"))
                m5.metric(tx['t3_m5'], metadata.get("license", "N/A"))

                if metadata.get("description"):
                    st.markdown(
                        f"<div class='mode-banner'>{metadata['description']}</div>",
                        unsafe_allow_html=True,
                    )
                if metadata.get("topics"):
                    badges = "".join(f"<span class='topic-badge'>{t}</span>" for t in metadata["topics"][:10])
                    st.markdown(badges, unsafe_allow_html=True)

            if not repo_content.startswith(("GitHub_Error", "Invalid")):
                with st.spinner(tx['t3_spinner_analyze']):
                    context = engine.query_vector_context("zeravane_github", github_query, n_results=4) or repo_content[:7000]
                    sys_msg = (
                        "You are Karikalan AI (கரிகாலன் AI), a GitHub repository analyst. "
                        "Answer from the repository data: README, file tree, metadata. "
                        f"Be specific — cite file names and README sections. {tx['sys_instruction_suffix']}"
                    )
                    prompt = (
                        f"Repository: {github_url.strip()}\n\n"
                        f"=== REPO DATA ===\n{context}\n\n"
                        f"=== QUESTION ===\n{github_query}"
                    )
                    response_text, model_used = engine._infer(sys_msg, prompt)

                st.markdown(
                    f"<div style='font-size:10px;letter-spacing:2px;color:#7A6540;margin:16px 0 10px;'>"
                    f"{tx['t3_resp_lbl']}</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(f"<span class='tag tag-model'>{model_used}</span>", unsafe_allow_html=True)
                st.markdown(response_text)

                with st.expander(tx['t3_raw_lbl']):
                    st.text_area("", value=repo_content[:4000], disabled=True, height=220)
            else:
                st.error(f"Failed: {repo_content}")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — TECH STACK DETECTOR
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown(f"""
    <div class="tab-section-title">{tx['t4_title']}</div>
    <div class="tab-section-sub">{tx['t4_sub']}</div>
    """, unsafe_allow_html=True)

    stack_url = st.text_input(
        tx['t4_url_lbl'],
        placeholder=tx['t4_url_placeholder'],
    )

    if st.button(tx['t4_btn_detect'], use_container_width=True):
        if not stack_url.strip():
            st.error(tx['t4_err_url'])
        else:
            with st.spinner(tx['t4_spinner']):
                raw_content, scrape_method = engine.scrape_live_url(stack_url.strip())
                stack_report = engine.detect_tech_stack(raw_content, stack_url.strip(), language_suffix=tx['sys_instruction_suffix'])

            st.markdown(
                f"<div style='margin-bottom:12px;'>"
                f"<span class='tag tag-cache'>{scrape_method}</span></div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div style='font-size:10px;letter-spacing:2px;color:#7A6540;margin:0 0 10px;'>"
                f"{tx['t4_results_lbl']}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(stack_report)

            with st.expander(tx['t4_raw_lbl']):
                st.text_area("", value=raw_content[:2500], disabled=True, height=150)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 5 — CODE GENERATOR
# ─────────────────────────────────────────────────────────────────────────────
with tab5:
    st.markdown(f"""
    <div class="tab-section-title">{tx['t5_title']}</div>
    <div class="tab-section-sub">{tx['t5_sub']}</div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="mode-banner">
        {tx['t5_banner']}
    </div>""", unsafe_allow_html=True)

    codegen_url = st.text_input(
        tx['t5_url_lbl'],
        placeholder=tx['t5_url_placeholder'],
    )
    codegen_request = st.text_area(
        tx['t5_request_lbl'],
        placeholder=tx['t5_request_placeholder'],
        height=80,
    )
    codegen_language = st.selectbox(
        tx['t5_lang_lbl'],
        ["Python", "TypeScript", "JavaScript", "Go", "Rust", "Java", "C#", "PHP", "Ruby", "Kotlin"],
    )

    if st.button(tx['t5_btn_gen'], use_container_width=True):
        if not codegen_url.strip():
            st.error(tx['t5_err_url'])
        elif not codegen_request.strip():
            st.error(tx['t5_err_req'])
        else:
            with st.spinner(tx['t5_spinner']):
                generated_code, scrape_method, model_used = engine.generate_code_from_docs(
                    docs_url=codegen_url.strip(),
                    generation_request=codegen_request.strip(),
                    language=codegen_language,
                    language_suffix=tx['sys_instruction_suffix']
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
                f"{tx['t5_results_lbl']} ({codegen_language})</div>",
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
