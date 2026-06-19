# =============================================================================
# கரிகாலன் AI (Karikalan AI) — Streamlit Frontend v1.0
# Tamil Chola Heritage × Futuristic AI Platform
# =============================================================================
import os
import sys

# Force pure-Python implementation to bypass protobuf descriptor issues on Streamlit Cloud
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import streamlit as st

# ── DYNAMIC PATH RESOLUTION FIX FOR STREAMLIT DEPLOYMENT ─────────────────────
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(CURRENT_DIR)
sys.path.append(os.path.dirname(CURRENT_DIR))

try:
    from zeravaneai.backend.engine import KarikalanEngine
except ImportError:
    try:
        from backend.engine import KarikalanEngine
    except ImportError:
        sys.path.append(os.path.join(CURRENT_DIR, ".."))
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
# DESIGN SYSTEM — CHOLA HERITAGE PALETTE & INJECTED STYLES
# =============================================================================
st.markdown("""
<style>
    /* Dark Slate Theme Overrides */
    .stApp {
        background-color: #0D0A05 !important;
        color: #F5E6C8 !important;
    }
    
    /* Global Headings */
    h1, h2, h3, h4, h5, h6, label, .stMarkdown p {
        color: #F5E6C8 !important;
        font-family: 'Courier New', Courier, monospace;
    }

    /* Custom Header Branding */
    .chola-title-container {
        text-align: center;
        padding: 20px 0;
        background: linear-gradient(135deg, #1A1208 0%, #0D0A05 100%);
        border-bottom: 2px solid #C8922A;
        border-radius: 4px;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    .chola-title-main {
        font-size: 32px;
        font-weight: 800;
        letter-spacing: 4px;
        color: #C8922A !important;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
    }
    .chola-title-sub {
        font-size: 11px;
        letter-spacing: 3px;
        color: #A07830 !important;
        margin-top: 5px;
        text-transform: uppercase;
    }

    /* Kolam Custom Dividers */
    .kolam-divider {
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 20px 0;
    }
    .kolam-line {
        height: 1px;
        background: linear-gradient(90deg, transparent, #C8922A, transparent);
        flex-grow: 1;
        margin: 0 15px;
    }
    .kolam-diamond {
        width: 6px;
        height: 6px;
        background-color: #C8922A;
        transform: rotate(45deg);
        margin: 0 4px;
    }

    /* Sidebar Modifiers */
    section[data-testid="stSidebar"] {
        background-color: #1A1208 !important;
        border-right: 1px solid #C8922A;
    }

    /* Status Tags Layout */
    .tag {
        display: inline-block;
        padding: 4px 10px;
        font-size: 10px;
        font-weight: bold;
        letter-spacing: 1px;
        border-radius: 3px;
        margin-right: 8px;
        text-transform: uppercase;
    }
    .tag-model { background-color: #8B0000; color: #F5E6C8; border: 1px solid #C8922A; }
    .tag-cache { background-color: #3A2810; color: #F5E6C8; border: 1px solid #A07830; }

    /* Text inputs and Textareas custom styles */
    .stTextArea textarea, .stTextInput input {
        background-color: #1A1208 !important;
        color: #F5E6C8 !important;
        border: 1px solid #A07830 !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #C8922A !important;
        box-shadow: 0 0 5px rgba(200,146,42,0.5) !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session Engine
if "engine" not in st.session_state:
    st.session_state.engine = KarikalanEngine()

# =============================================================================
# HEADER BRANDING
# =============================================================================
st.markdown("""
<div class='chola-title-container'>
    <div class='chola-title-main'>கரிகாலன் AI</div>
    <div class='chola-title-sub'>Karikalan AI Engine • Core Production Architecture v3.1</div>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# SIDEBAR CONTROL CONSOLE
# =============================================================================
with st.sidebar:
    st.markdown("<div style='font-size:12px;letter-spacing:2px;color:#C8922A;margin-bottom:15px;font-weight:bold;'>இராணுவக் கட்டுப்பாடு · CONTROLS</div>", unsafe_allow_html=True)
    
    app_mode = st.radio(
        "Select Agent Mode:",
        ["Live RAG Assistant", "Multi-URL Indexer", "Tech Stack Detector", "Doc-to-Code Generator", "GitHub Repository Analyzer"],
        index=0
    )
    
    st.markdown("<div class='kolam-divider'><div class='kolam-line'></div></div>", unsafe_allow_html=True)
    
    # System Operational Flags
    st.markdown("<div style='font-size:10px;letter-spacing:1px;color:#A07830;margin-bottom:5px;'>BACKEND GATEWAY LOGS</div>", unsafe_allow_html=True)
    st.write(f"Gemini LLM (Tier 1): {'🟢 Active' if st.session_state.engine.gemini_enabled else '🔴 Disabled'}")
    st.write(f"Groq LLM (Tier 2): {'🟢 Configured' if st.session_state.engine.groq_enabled else '⚪ Offline'}")
    st.write(f"Ollama Local (Tier 4): {'🟢 Connected' if st.session_state.engine.ollama_enabled else '⚪ Unavailable'}")
    st.write(f"Vector Index (Chroma): {'🟢 Persistent Client' if hasattr(st.session_state.engine.chroma_client, 'list_collections') else '🟡 Volatile Fallback'}")
    
    if st.button("Clear Conversation Memory"):
        st.session_state.engine.clear_memory()
        st.success("Conversation history wiped.")

# =============================================================================
# MODE 1: LIVE RAG ASSISTANT
# =============================================================================
if app_mode == "Live RAG Assistant":
    st.markdown("### 🏛️ Real-Time Contextual Knowledge Agent")
    st.markdown("Query the engine using custom target URLs for ground-truth reference extraction, or chat natively with standard architectural memory.")
    
    target_url = st.text_input("Target Reference URL (Optional):", placeholder="https://docs.example.com/api-reference")
    force_rescrape = st.checkbox("Force Bypass Cache & Rescrape URL", value=False)
    
    user_query = st.text_area("Developer Query:", height=120, placeholder="Ask technical queries or framework implementations here...")
    
    if st.button("Execute Pipeline Solution"):
        if not user_query.strip():
            st.warning("Please enter a valid developer query.")
        else:
            with st.spinner("Executing 4-Tier Inference pipeline & extraction layers..."):
                resp, context, method, model = st.session_state.engine.execute_live_agent_query(
                    user_query=user_query.strip(),
                    target_url=target_url.strip() if target_url.strip() else None,
                    force_rescrape=force_rescrape,
                    use_memory=True
                )
                
                st.markdown(
                    f"<div style='margin-bottom:12px;'>"
                    f"<span class='tag tag-model'>{model}</span>"
                    f"<span class='tag tag-cache'>{method}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
                
                st.markdown("#### Response Engine Output:")
                st.markdown(resp)
                
                if context and not context.startswith("["):
                    with st.expander("Inspected Vector Space Context Fragments"):
                        st.text(context)

# =============================================================================
# MODE 2: MULTI-URL INDEXER
# =============================================================================
elif app_mode == "Multi-URL Indexer":
    st.markdown("### 🗄️ Parallel Vector Space Indexer")
    st.markdown("Provide multiple documentation endpoints line-by-line to parse, segment, label, and commit text chunks directly into standard vector embeddings.")
    
    urls_input = st.text_area("Target URL List (One per line):", height=150, placeholder="https://example1.com/docs\nhttps://example2.com/spec")
    
    if st.button("Build Vector Space Context"):
        url_list = [u.strip() for u in urls_input.split("\n") if u.strip()]
        if not url_list:
            st.warning("Please provide at least one valid endpoint URL.")
        else:
            with st.spinner("Processing asynchronous crawler operations..."):
                chunks, summary = st.session_state.engine.scrape_multiple_urls(url_list)
                st.info("Execution Summary Results:")
                st.text(summary)
                st.success(f"Committed {len(chunks)} contextual chunks safely into local Chroma index structures.")

# =============================================================================
# MODE 3: TECH STACK DETECTOR
# =============================================================================
elif app_mode == "Tech Stack Detector":
    st.markdown("### 🔧 Technical Stack Archetype Detector")
    st.markdown("Scrapes an application surface layer to identify client frameworks, server infrastructure conventions, CDNs, and orchestration platforms with confidence metrics.")
    
    tech_url = st.text_input("Application Platform URL:", placeholder="https://target-app-instance.com")
    
    if st.button("Inspect Stack Footprints"):
        if not tech_url.strip():
            st.warning("Please provide a valid platform URL endpoint.")
        else:
            with st.spinner("Extracting external headers and source marks..."):
                raw, method = st.session_state.engine.scrape_live_url(tech_url.strip())
                if "Error" in raw or len(raw) < 100:
                    st.error(f"Failed to access layout information: {raw}")
                else:
                    result = st.session_state.engine.detect_tech_stack(raw, target_url=tech_url.strip())
                    st.markdown(f"**Scraped Via:** {method}")
                    st.markdown(result)

# =============================================================================
# MODE 4: DOC-TO-CODE GENERATOR
# =============================================================================
elif app_mode == "Doc-to-Code Generator":
    st.markdown("### 📦 Live Doc-to-Code Generation Studio")
    st.markdown("Extract live structural API definitions directly and synthesize syntactically valid code blocks backed by verified handling protocols.")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        codegen_url = st.text_input("Live Documentation Reference Link:", placeholder="https://docs.stripe.com/api")
    with col2:
        codegen_language = st.selectbox("Target Output Language:", ["Python", "JavaScript", "TypeScript", "Go", "Rust", "Java"])
        
    codegen_request = st.text_area("Generation Directives & Logic Rules:", height=100, placeholder="Write a clean client implementation handling paginated listings...")
    
    if st.button("Synthesize Production Code Solution"):
        if not codegen_url.strip() or not codegen_request.strip():
            st.warning("Both documentation endpoints and generation rules are strictly required parameters.")
        else:
            with st.spinner("Compiling contextual layout parameters..."):
                generated_code, method, model_used = st.session_state.engine.generate_code_from_docs(
                    docs_url=codegen_url.strip(),
                    generation_request=codegen_request.strip(),
                    language=codegen_language
                )
                
            st.markdown(
                f"<div style='margin-bottom:12px;'>"
                f"<span class='tag tag-model'>{model_used}</span>"
                f"<span class='tag tag-cache'>{method}</span>"
                f"</div>",
                unsafe_allow_html=True
            )
            st.markdown(generated_code)

# =============================================================================
# MODE 5: GITHUB REPOSITORY ANALYZER
# =============================================================================
elif app_mode == "GitHub Repository Analyzer":
    st.markdown("### 🏛️ Public Repository Blueprint Analyzer")
    st.markdown("Processes file configurations, repository trees, parameters, licensing, and code paths across open public GitHub targets.")
    
    github_url = st.text_input("GitHub Public Repository URL:", placeholder="https://github.com/owner/repository")
    
    if st.button("Map Architecture Blueprint"):
        if not github_url.strip():
            st.warning("Please provide a valid GitHub URL endpoint.")
        else:
            with st.spinner("Extracting parameters via upstream GitHub REST APIs..."):
                combined_content, metadata = st.session_state.engine.analyze_github_repo(github_url.strip())
                
                if not metadata:
                    st.error(combined_content)
                else:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Stars count", f"{metadata.get('stars', 0):,}")
                        st.metric("Primary Architecture Language", metadata.get("language", "N/A"))
                    with col2:
                        st.metric("Forks count", f"{metadata.get('forks', 0):,}")
                        st.metric("License Variant", metadata.get("license", "N/A"))
                    with col3:
                        st.metric("Open Issues", f"{metadata.get('open_issues', 0):,}")
                        st.metric("Default Branch Root", metadata.get("default_branch", "main"))
                    
                    st.markdown("#### Inferred Repository Profile Summary Blueprint:")
                    st.text_area("Extracted Metadata Tree (First 3,000 Chars)", combined_content[:3000], height=250)

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("<div class='kolam-divider'><div class='kolam-line'></div><div class='kolam-diamond'></div><div style='font-size:9px;letter-spacing:2px;color:#3A2810;white-space:nowrap;'>சோழ பேரரசு · CHOLA EMPIRE</div><div class='kolam-diamond'></div><div class='kolam-line'></div></div>", unsafe_allow_html=True)
st.markdown("""
<p style='text-align:center;font-size:10px;color:#3A2810;letter-spacing:2px;padding:5px 0 25px;'>
    வடிவமைப்பு மற்றும் உருவாக்கம் · POWERED BY ZERAVANE AI
</p>
""", unsafe_allow_html=True)
