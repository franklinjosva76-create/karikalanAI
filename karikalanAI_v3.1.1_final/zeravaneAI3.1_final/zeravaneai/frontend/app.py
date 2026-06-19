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
        "lbl_llm_tiers": "🧠 LLM படிநிலைகள்",
        "lbl_scraping": "🕷️ வலை சேகரிப்பு படிநிலைகள்",
        "lbl_memory": "💬 உரையாடல் நினைவகம்",
        "lbl_memory_toggle": "உரையாடல் நினைவு",
        "lbl_active_turns": "நடப்பு திருப்பங்கள்",
        "btn_clear_mem": "🗑️ நினைவகம் அழி",
        "lbl_vectordb": "🗄️ திசையன் தரவுத்தளம்",
        "btn_clear_cache": "🗑️ தற்காலிக சேமிப்பு அழி",
        "exp_api_keys": "🔑 API விசைகள்",
        "tab_titles": ["💬 AI உதவியாளர்", "🔗 பல URL RAG", "🐙 GitHub பகுப்பாய்வு", "🔍 Tech Stack கண்டறிவு", "⚙️ குறியீடு உருவாக்கம்"],
        
        # Tab 1
        "t1_title": "💬 AI உரையாடல் முகவர்",
        "t1_sub": "நேரடி ஆவணங்களை சேகரித்து உண்மையான சூழலில் இருந்து பதிலளிக்கும்",
        "t1_url_label": "இலக்கு இணையதள முகவரி (விருப்பமிருந்தால்)",
        "t1_url_placeholder": "https://docs.fastapi.tiangolo.com  (அடிப்படை அறிவுக்கு இதை காலியாக விடவும்)",
        "t1_force_scrape": "🔄 மீண்டும் சேகரி",
        "t1_banner_core": "🧠 அடிப்படை நிலை — பேஸ் மாடல் அறிவு மட்டுமே · வலை சேகரிப்பு இல்லை",
        "t1_banner_web": "🌐 வலை நுண்ணறிவு நிலை — நேரடி வலை சேகரிப்பு செயலில் உள்ளது",
        "t1_history_lbl": "உரையாடல் வரலாறு",
        "t1_query_lbl": "உங்கள் கேள்வி",
        "t1_query_placeholder": "மென்பொருள் குறியீடு, APIகள், கட்டமைப்புகள், ஆர்கிடெக்சர் பற்றி எதுவாக இருந்தாலும் கேளுங்கள்...",
        "t1_btn_execute": "🏛️ முகவரை இயக்கு",
        "t1_btn_clear": "🗑️ துடை",
        "t1_err_query": "தயவுசெய்து ஒரு கேள்வியை உள்ளிடவும்.",
        "t1_resp_lbl": "பதில்",
        "t1_context_lbl": "🔍 மீட்டெடுக்கப்பட்ட சூழல்",
        "t1_no_context": "[சூழல் இல்லை — அடிப்படை அறிவில் இயங்குகிறது]",
        "t1_spinner_scrape": "🌐 நேரடி ஆவணங்களைச் சேகரிக்கிறது...",
        "t1_spinner_think": "🧠 கரிகாலன் AI சிந்திக்கிறது...",

        # Tab 2
        "t2_title": "🔗 பல URL அறிவுத் தளம்",
        "t2_sub": "ஒன்றுக்கும் மேற்பட்ட URLகளைச் சேகரித்து அவை அனைத்திலும் தேடவும்",
        "t2_banner": "📡 பன்முக மூல நுண்ணறிவு — ஒவ்வொரு URL-உம் 3-அடுக்கு ஃபால்பேக் மூலம் சேகரிக்கப்பட்டு, ஒரு ChromaDB குறியீட்டில் இணைக்கப்படுகிறது",
        "t2_urls_lbl": "URLகள் (வரியிற்கு ஒன்று)",
        "t2_urls_placeholder": "https://docs.fastapi.tiangolo.com\nhttps://docs.pydantic.dev",
        "t2_query_lbl": "கேள்வி",
        "t2_query_placeholder": "இந்த கட்டமைப்புகளில் அங்கீகார அணுகுமுறைகளை ஒப்பிடுக...",
        "t2_btn_scrape": "🏛️ அனைத்தையும் சேகரித்து வினவு",
        "t2_err_url": "குறைந்தது ஒரு URL ஐ உள்ளிடவும்.",
        "t2_err_query": "ஒரு கேள்வியை உள்ளிடவும்.",
        "t2_spinner_scrape": "🌐 URLகளைச் சேகரிக்கிறது...",
        "t2_results_lbl": "சேகரிப்பு முடிவுகள்",
        "t2_spinner_query": "🧠 ஒருங்கிணைந்த அறிவுத் தளத்தை வினவுகிறது...",
        "t2_resp_lbl": "பதில்",
        "t2_err_no_scrape": "எந்த URLகளும் வெற்றிகரமாகச் சேகரிக்கப்படவில்லை.",

        # Tab 3
        "t3_title": "🐙 GitHub களஞ்சிய பகுப்பாய்வி",
        "t3_sub": "எந்தவொரு பொது GitHub களஞ்சியத்தையும் ஆழமாக பகுப்பாய்வு செய்யுங்கள் — README, கோப்பு மரம், மெட்டாடேட்டா",
        "t3_url_lbl": "களஞ்சிய URL",
        "t3_url_placeholder": "https://github.com/tiangolo/fastapi",
        "t3_query_lbl": "இந்த களஞ்சியத்தைப் பற்றிக் கேளுங்கள்",
        "t3_query_placeholder": "நான் எப்படி தொடங்குவது? இதன் கட்டமைப்பு என்ன?",
        "t3_btn_analyze": "🏛️ களஞ்சியத்தை பகுப்பாய்வு செய்",
        "t3_err_url": "ஒரு GitHub URL ஐ உள்ளிடவும்.",
        "t3_err_query": "ஒரு கேள்வியை உள்ளிடவும்.",
        "t3_spinner_fetch": "🐙 GitHub API மூலம் களஞ்சியத்தைப் பெறுகிறது...",
        "t3_m1": "⭐ நட்சத்திரங்கள்", "t3_m2": "🍴 கிளைகள்", "t3_m3": "🐛 பிழைகள்", "t3_m4": "💻 முதன்மை மொழி", "t3_m5": "📄 உரிமம்",
        "t3_spinner_analyze": "🧠 பகுப்பாய்வு செய்கிறது...",
        "t3_resp_lbl": "பகுப்பாய்வு",
        "t3_raw_lbl": "📁 மூல களஞ்சிய தரவு",

        # Tab 4
        "t4_title": "🔍 தொழில்நுட்ப அடுக்கு கண்டறிவி",
        "t4_sub": "எந்தவொரு தளத்தையும் சேகரித்து அதன் முழுமையான தொழில்நுட்ப அடுக்கைக் கண்டறியவும்",
        "t4_url_lbl": "இணையதள URL",
        "t4_url_placeholder": "https://vercel.com",
        "t4_btn_detect": "🔍 அடுக்கைக் கண்டறி",
        "t4_err_url": "ஒரு URL ஐ உள்ளிடவும்.",
        "t4_spinner": "🌐 இணையதளத்தைச் சேகரித்து பகுப்பாய்வு செய்கிறது...",
        "t4_results_lbl": "கண்டறியப்பட்ட அடுக்கு",
        "t4_raw_lbl": "🔍 சேகரிக்கப்பட்ட மூல உள்ளடக்கம்",

        # Tab 5
        "t5_title": "⚙️ நேரடி ஆவணங்களிலிருந்து குறியீடு உருவாக்கி",
        "t5_sub": "ஆவணங்கள் URL ஐ உள்ளிடவும், கரிகாலன் AI அதைச் சேகரித்து உற்பத்திக்குத் தயாரான குறியீட்டை உருவாக்கும்",
        "t5_banner": "🤖 நேரடி ஆவணங்கள் → உற்பத்தி குறியீடு — Crawl4AI ஆவணங்களைப் பெறுகிறது · RAG உள்ளடக்கத்தை வரிசைப்படுத்துகிறது · LLM கொதிகலன் குறியீட்டை உருவாக்குகிறது",
        "t5_url_lbl": "ஆவணப்படுத்தல் URL",
        "t5_url_placeholder": "https://docs.stripe.com/api",
        "t5_request_lbl": "என்ன குறியீடு உருவாக்கப்பட வேண்டும்?",
        "t5_request_placeholder": "CRUD செயல்பாடுகள் மற்றும் JWT அங்கீகாரத்துடன் முழுமையான REST API ஐ உருவாக்கவும்...",
        "t5_lang_lbl": "இலக்கு மொழி",
        "t5_btn_gen": "⚙️ குறியீட்டை உருவாக்கு",
        "t5_err_url": "ஒரு ஆவணப்படுத்தல் URL ஐ உள்ளிடவும்.",
        "t5_err_req": "உங்களுக்கு என்ன குறியீடு வேண்டும் என்பதை விவரிக்கவும்.",
        "t5_spinner": "🌐 ஆவணங்களைச் சேகரித்து குறியீட்டை உருவாக்குகிறது...",
        "t5_results_lbl": "உருவாக்கப்பட்ட குறியீடு",

        "sys_instruction_suffix": "Respond strictly and entirely in pure, formal Tamil text. Avoid transliterating English words where high-quality Tamil engineering terms exist."
    },
    "Tanglish": {
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
        "t1_sub": "Live docs-அை Scrape பண்ணி real context-ல இருந்து பதில் சொல்லும்",
        "t1_url_label": "Target URL (optional)",
        "t1_url_placeholder": "https://docs.fastapi.tiangolo.com  (base knowledge-க்கு blank-ஆ விடுங்க)",
        "t1_force_scrape": "🔄 Force re-scrape பண்ணு",
        "t1_banner_core": "🧠 Core Mode — Base model knowledge · Scraping active-ஆ இல்ல",
        "t1_banner_web": "🌐 Web Intelligence Mode — Live scraping active-ஆ இருக்கு",
        "t1_history_lbl": "Conversation History",
        "t1_query_lbl": "உங்க Query",
        "t1_query_placeholder": "Code, APIs, frameworks, architectures பத்தி எது வேணாலும் கேளுங்க...",
        "t1_btn_execute": "🏛️ Execute Agent",
        "t1_btn_clear": "🗑️ Clear பண்ணு",
        "t1_err_query": "தயவுசெஞ்சு ஒரு query-ஐ என்டர் பண்ணுங்க.",
        "t1_resp_lbl": "Response",
        "t1_context_lbl": "🔍 Retrieved Context",
        "t1_no_context": "[No context — base knowledge-ல ரன் ஆகுது]",
        "t1_spinner_scrape": "🌐 Live documentation-ஐ scrape பண்ணிட்டு இருக்கு...",
        "t1_spinner_think": "🧠 Karikalan AI யோசிச்சிட்டு இருக்கு...",

        # Tab 2
        "t2_title": "🔗 Multi-URL Knowledge Base",
        "t2_sub": "Multiple URL-களை scrape பண்ணி ஒரே நேரத்துல query பண்ணுங்க",
        "t2_banner": "📡 Multi-Source Intelligence — ஒவ்வொரு URL-உம் 3-tier fallback வழியா scrape செய்யப்பட்டு, ஒரே ChromaDB index-ல merge பண்ணப்படும்",
        "t2_urls_lbl": "URLs (ஒரு வரிக்கு ஒன்று)",
        "t2_urls_placeholder": "https://docs.fastapi.tiangolo.com\nhttps://docs.pydantic.dev",
        "t2_query_lbl": "Query",
        "t2_query_placeholder": "இந்த frameworks-க்கு நடுவுல இருக்குற authentication approaches-ஐ compare பண்ணு...",
        "t2_btn_scrape": "🏛️ Scrape All + Query",
        "t2_err_url": "At least ஒரு URL ஆவது குடுங்க.",
        "t2_err_query": "ஒரு query-ஐ என்டர் பண்ணுங்க.",
        "t2_spinner_scrape": "🌐 URL-களை scrape பண்ணிட்டு இருக்கு...",
        "t2_results_lbl": "SCRAPE RESULTS",
        "t2_spinner_query": "🧠 Merged knowledge base-ஐ வினவுகிறது...",
        "t2_resp_lbl": "RESPONSE",
        "t2_err_no_scrape": "எந்த URL-உம் வெற்றிகரமா scrape ஆகல.",

        # Tab 3
        "t3_title": "🐙 GitHub Repository Analyzer",
        "t3_sub": "எந்தவொரு public GitHub repo-வையும் deep-dive பண்ணுங்க — README, file tree, metadata",
        "t3_url_lbl": "Repository URL",
        "t3_url_placeholder": "https://github.com/tiangolo/fastapi",
        "t3_query_lbl": "இந்த repo பத்தி கேளுங்க",
        "t3_query_placeholder": "நான் எப்படி start பண்றது? இதோட architecture என்ன?",
        "t3_btn_analyze": "🏛️ Analyze Repository",
        "t3_err_url": "ஒரு GitHub URL-ஐ என்டர் பண்ணுங்க.",
        "t3_err_query": "ஒரு கேள்வியை என்டர் பண்ணுங்க.",
        "t3_spinner_fetch": "🐙 GitHub API வழியா repository-ஐ fetch பண்ணிட்டு இருக்கு...",
        "t3_m1": "⭐ Stars", "t3_m2": "🍴 Forks", "t3_m3": "🐛 Issues", "t3_m4": "💻 Language", "t3_m5": "📄 License",
        "t3_spinner_analyze": "🧠 Analyze பண்ணிட்டு இருக்கு...",
        "t3_resp_lbl": "ANALYSIS",
        "t3_raw_lbl": "📁 Raw Repo Data",

        # Tab 4
        "t4_title": "🔍 Tech Stack Detector",
        "t4_sub": "எந்த site-ஐயும் scrape பண்ணி அதோட முழு tech stack-ஐயும் கண்டுபிடிங்க",
        "t4_url_lbl": "Website URL",
        "t4_url_placeholder": "https://vercel.com",
        "t4_btn_detect": "🔍 Detect Stack",
        "t4_err_url": "ஒரு URL-ஐ என்டர் பண்ணுங்க.",
        "t4_spinner": "🌐 Website-ஐ scrape பண்ணி analyze பண்ணிட்டு இருக்கு...",
        "t4_results_lbl": "DETECTED STACK",
        "t4_raw_lbl": "🔍 Raw Scraped Content",

        # Tab 5
        "t5_title": "⚙️ Code Generator from Live Docs",
        "t5_sub": "Docs URL-ஐ குடுத்தா, Karikalan AI அதை scrape பண்ணி production-ready code-ஐ generate பண்ணிடும்",
        "t5_banner": "🤖 Live Docs → Production Code — Crawl4AI docs-ஐ எடுக்கும் · RAG content-ஐ index பண்ணும் · LLM boilerplate-ஐ generate பண்ணும்",
        "t5_url_lbl": "Documentation URL",
        "t5_url_placeholder": "https://docs.stripe.com/api",
        "t5_request_lbl": "என்ன code generate பண்ணனும்?",
        "t5_request_placeholder": "CRUD operations மற்றும் JWT authentication உடன் ஒரு முழுமையான REST API-ஐ உருவாக்கு...",
        "t5_lang_lbl": "Target Language",
        "t5_btn_gen": "⚙️ Generate Code",
        "t5_err_url": "ஒரு documentation URL-ஐ குடுங்க.",
        "t5_err_req": "உங்களுக்கு என்ன code வேணும்னு describe பண்ணுங்க.",
        "t5_spinner": "🌐 Docs-ஐ scrape பண்ணி code generate பண்ணிட்டு இருக்கு...",
        "t5_results_lbl": "GENERATED CODE",

        "sys_instruction_suffix": "Respond in a fluid conversational mix of casual Tamil language and clear English technical terms (Tanglish). Use absolute English terms for coding concepts like 'database', 'function', 'class', 'loop', 'variable', 'route', and 'API' so developers can directly read your architecture advice into structural code."
    }
}

# =============================================================================
# DESIGN SYSTEM — CHOLA HERITAGE PALETTE
# =============================================================================
st.markdown(""
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
    background: linear-gradient(135deg, rgba(200,146,42,0.18)
