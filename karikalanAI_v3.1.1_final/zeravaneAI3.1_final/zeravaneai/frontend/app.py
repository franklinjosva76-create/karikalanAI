import os
import sys

# Force pure-Python protobuf implementation
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import streamlit as st

# Setup explicit path resolution to avoid path resolution deadlocks
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

Z_DIR = os.path.join(BASE_DIR, "zeravaneai")
if Z_DIR not in sys.path:
    sys.path.append(Z_DIR)

# Safe Engine Imports
try:
    from zeravaneai.backend.engine import KarikalanEngine
except ImportError:
    try:
        from backend.engine import KarikalanEngine
    except ImportError:
        st.error("Could not find backend engine pathway module. Check file structures.")
        st.stop()

# =============================================================================
# INITIALIZE WEB INTERFACE LAYOUT
# =============================================================================
st.set_page_config(
    page_title="கரிகாலன் AI",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom injection styles matching Chola design archetype
st.markdown("""
<style>
    .stApp { background-color: #0D0A05 !important; color: #F5E6C8 !important; }
    h1, h2, h3, h4, label, .stMarkdown p { color: #F5E6C8 !important; font-family: monospace; }
    .chola-title-container { text-align: center; padding: 15px; background: #1A1208; border-bottom: 2px solid #C8922A; margin-bottom: 20px; }
    .tag { padding: 4px 8px; font-size: 11px; font-weight: bold; border-radius: 3px; margin-right: 5px; }
    .tag-model { background-color: #8B0000; color: #F5E6C8; }
    .tag-cache { background-color: #3A2810; color: #F5E6C8; }
</style>
""", unsafe_allow_html=True)

if "engine" not in st.session_state:
    st.session_state.engine = KarikalanEngine()

st.markdown("<div class='chola-title-container'><h2 style='color:#C8922A; margin:0;'>கரிகாலன் AI Engine v3.1</h2></div>", unsafe_allow_html=True)

# Sidebar layout navigation
with st.sidebar:
    st.markdown("<h3 style='color:#C8922A;'>இராணுவக் கட்டுப்பாடு</h3>", unsafe_allow_html=True)
    app_mode = st.radio("Select Agent System Mode:", ["Live RAG Assistant", "Multi-URL Indexer", "Tech Stack Detector", "Doc-to-Code Generator", "GitHub Analyzer"])
    if st.button("Wipe Context History"):
        st.session_state.engine.clear_memory()
        st.success("Wiped memory context.")

# =============================================================================
# AGENT INTERFACE LAYER ROUTING
# =============================================================================
if app_mode == "Live RAG Assistant":
    st.markdown("### 🏛️ Real-Time Contextual Knowledge Agent")
    target_url = st.text_input("Target Reference URL (Optional):", placeholder="https://example.com/docs")
    force_rescrape = st.checkbox("Force Bypass Cache & Rescrape")
    user_query = st.text_area("Developer Prompt Query:")
    
    if st.button("Execute Pipeline Solution"):
        if not user_query.strip():
            st.warning("Please provide a prompt input query.")
        else:
            with st.spinner("Processing architectural 4-tier pipeline..."):
                resp, context, method, model = st.session_state.engine.execute_live_agent_query(
                    user_query=user_query.strip(),
                    target_url=target_url.strip() if target_url.strip() else None,
                    force_rescrape=force_rescrape
                )
                st.markdown(f"<div><span class='tag tag-model'>{model}</span><span class='tag tag-cache'>{method}</span></div>", unsafe_allow_html=True)
                st.markdown("#### Output Implementation Workspace:")
                st.write(resp)

elif app_mode == "Multi-URL Indexer":
    st.markdown("### 🗄️ Parallel Vector Space Indexer")
    urls_input = st.text_area("URLs List (One per line):")
    if st.button("Build Vector Space Context"):
        urls = [u.strip() for u in urls_input.split("\n") if u.strip()]
        if not urls:
            st.warning("Provide target URLs.")
        else:
            with st.spinner("Indexing vector slices..."):
                chunks, summary = st.session_state.engine.scrape_multiple_urls(urls)
                st.text(summary)

elif app_mode == "Tech Stack Detector":
    st.markdown("### 🔧 Technical Stack Archetype Detector")
    tech_url = st.text_input("Application Platform Target URL:")
    if st.button("Inspect Stack Footprints"):
        with st.spinner("Scanning framework footprints..."):
            raw, method = st.session_state.engine.scrape_live_url(tech_url.strip())
            res = st.session_state.engine.detect_tech_stack(raw, target_url=tech_url.strip())
            st.write(res)

elif app_mode == "Doc-to-Code Generator":
    st.markdown("### 📦 Live Doc-to-Code Generation Studio")
    codegen_url = st.text_input("Documentation Endpoint Link:")
    codegen_lang = st.selectbox("Target Output Language Language:", ["Python", "TypeScript", "Go"])
    codegen_req = st.text_area("Generation Directives & Logic Rules:")
    if st.button("Synthesize Solution"):
        with st.spinner("Compiling structural mappings..."):
            code, method, model = st.session_state.engine.generate_code_from_docs(codegen_url, codegen_req, codegen_lang)
            st.code(code)

elif app_mode == "GitHub Analyzer":
    st.markdown("### 🏛️ Public Repository Blueprint Analyzer")
    github_url = st.text_input("GitHub Public Repository URL Link:")
    if st.button("Map Blueprint"):
        with st.spinner("Extracting repository metadata trees..."):
            content, meta = st.session_state.engine.analyze_github_repo(github_url)
            st.json(meta)
            st.text_area("Extracted Tree Frame", content[:2000], height=200)
