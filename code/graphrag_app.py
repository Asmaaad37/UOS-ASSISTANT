import streamlit as st
import asyncio
import os
import time
from dotenv import load_dotenv
import json
from datetime import datetime
from pathlib import Path

os.environ["USE_TF"] = "0"          # disable TensorFlow in transformers
os.environ["KERAS_BACKEND"] = "torch"  # use torch backend for Keras

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="UniQuery · GraphRAG",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Syne:wght@400;600;700;800&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    background-color: #0a0a0f;
    color: #e8e6e0;
    font-family: 'DM Mono', monospace;
}

[data-testid="stAppViewContainer"] {
    background: 
        radial-gradient(ellipse 80% 50% at 20% 0%, rgba(99, 76, 178, 0.12) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 100%, rgba(20, 148, 132, 0.08) 0%, transparent 60%),
        #0a0a0f;
}

/* ── Hide Streamlit Chrome ── */
#MainMenu, footer { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }
.block-container { padding: 2rem 2.5rem 4rem; max-width: 1400px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.02) !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
[data-testid="stSidebar"] > div { padding: 2rem 1.5rem; }

/* ── Typography ── */
h1, h2, h3 { font-family: 'Syne', sans-serif !important; }

.app-title {
    font-family: 'Syne', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, #e8e6e0 0%, #9b8fd4 50%, #14a88a 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 0.25rem 0;
    line-height: 1.1;
}

.app-subtitle {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    color: rgba(232, 230, 224, 0.35);
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 2rem;
}

.section-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: rgba(232, 230, 224, 0.3);
    margin-bottom: 0.75rem;
    margin-top: 1.75rem;
}

/* ── Input ── */
[data-testid="stTextArea"] textarea {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 10px !important;
    color: #e8e6e0 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.875rem !important;
    padding: 1rem !important;
    transition: border-color 0.2s ease !important;
    resize: none !important;
}
[data-testid="stTextArea"] textarea:focus {
    border-color: rgba(155, 143, 212, 0.5) !important;
    box-shadow: 0 0 0 3px rgba(155, 143, 212, 0.08) !important;
    outline: none !important;
}
[data-testid="stTextArea"] label { display: none !important; }

/* ── Buttons ── */
.stButton > button {
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    border-radius: 8px !important;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.2s ease !important;
    border: none !important;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #7c6bc9, #14a88a) !important;
    color: #fff !important;
    box-shadow: 0 4px 20px rgba(124, 107, 201, 0.3) !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 28px rgba(124, 107, 201, 0.45) !important;
}
.stButton > button[kind="secondary"] {
    background: rgba(255,255,255,0.04) !important;
    color: rgba(232,230,224,0.6) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
}
.stButton > button[kind="secondary"]:hover {
    background: rgba(255,255,255,0.07) !important;
    color: #e8e6e0 !important;
}

/* ── Radio / Mode selector ── */
[data-testid="stRadio"] label {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.8rem !important;
    color: rgba(232,230,224,0.7) !important;
}
[data-testid="stRadio"] > div {
    gap: 0.5rem !important;
    flex-direction: column !important;
}

/* ── Answer Cards ── */
.answer-card {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 1.5rem 1.75rem;
    height: 100%;
    min-height: 220px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.3s ease;
}
.answer-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 14px 14px 0 0;
}
.answer-card.vector::before {
    background: linear-gradient(90deg, #7c6bc9, transparent);
}
.answer-card.graph::before {
    background: linear-gradient(90deg, #14a88a, transparent);
}
.answer-card:hover {
    border-color: rgba(255,255,255,0.12);
}

.card-header {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 1.25rem;
}
.card-badge {
    font-family: 'DM Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    padding: 0.25rem 0.6rem;
    border-radius: 20px;
    font-weight: 500;
}
.badge-vector {
    background: rgba(124, 107, 201, 0.15);
    color: #9b8fd4;
    border: 1px solid rgba(124, 107, 201, 0.25);
}
.badge-graph {
    background: rgba(20, 168, 138, 0.12);
    color: #14a88a;
    border: 1px solid rgba(20, 168, 138, 0.25);
}
.card-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.95rem;
    font-weight: 700;
    color: rgba(232,230,224,0.9);
}
.card-body {
    font-family: 'DM Mono', monospace;
    font-size: 0.82rem;
    line-height: 1.75;
    color: rgba(232,230,224,0.72);
    white-space: pre-wrap;
}
.card-empty {
    font-family: 'DM Mono', monospace;
    font-size: 0.78rem;
    color: rgba(232,230,224,0.2);
    font-style: italic;
    padding: 2rem 0;
    text-align: center;
}
.timing-tag {
    font-family: 'DM Mono', monospace;
    font-size: 0.62rem;
    color: rgba(232,230,224,0.25);
    margin-top: 1.25rem;
    letter-spacing: 0.05em;
}

/* ── History items ── */
.history-item {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 8px;
    padding: 0.65rem 0.9rem;
    margin-bottom: 0.5rem;
    font-size: 0.75rem;
    color: rgba(232,230,224,0.5);
    cursor: pointer;
    transition: all 0.15s ease;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.history-item:hover {
    background: rgba(255,255,255,0.05);
    color: rgba(232,230,224,0.8);
    border-color: rgba(255,255,255,0.1);
}

/* ── Status / Spinner ── */
.status-bar {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    background: rgba(124, 107, 201, 0.08);
    border: 1px solid rgba(124, 107, 201, 0.18);
    border-radius: 8px;
    font-size: 0.78rem;
    color: rgba(155, 143, 212, 0.85);
    margin-bottom: 1.25rem;
    font-family: 'DM Mono', monospace;
}

/* ── Divider ── */
hr { border-color: rgba(255,255,255,0.05) !important; }

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
    color: #e8e6e0 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.8rem !important;
}

/* ── Slider ── */
[data-testid="stSlider"] {
    padding: 0.5rem 0;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
</style>
""", unsafe_allow_html=True)


# ── Load env & initialize ─────────────────────────────────────────────────────
load_dotenv()

@st.cache_resource(show_spinner=False)
def init_graphrag():
    """Initialize all GraphRAG components once and cache them."""
    import neo4j
    from neo4j_graphrag.llm import OllamaLLM
    from neo4j_graphrag.embeddings import SentenceTransformerEmbeddings
    from neo4j_graphrag.retrievers import VectorRetriever, VectorCypherRetriever
    from neo4j_graphrag.generation import GraphRAG, RagTemplate
    from neo4j_graphrag.embeddings import OllamaEmbeddings

    NEO4J_URI      = os.getenv("NEO4J_URI")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

    driver = neo4j.GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    driver.verify_connectivity()

    # embedder = SentenceTransformerEmbeddings(model="all-MiniLM-L6-v2")
    embedder = OllamaEmbeddings(
    model="nomic-embed-text"         # upgrade from all-MiniLM-L6-v2
)

    rag_llm = OllamaLLM(
        model_name="qwen2.5:3b",
        model_params={"options": {"temperature": 0}}
    )

    vector_retriever = VectorRetriever(
        driver,
        index_name="text_embeddings",
        embedder=embedder,
        return_properties=["text"],
    )

    graph_retriever = VectorCypherRetriever(
        driver,
        index_name="text_embeddings",
        embedder=embedder,
        retrieval_query="""
WITH node AS chunk
MATCH (chunk)<-[:FROM_CHUNK]-(p:Program)
OPTIONAL MATCH (p)<-[:OFFERS]-(d:Department)
OPTIONAL MATCH (p)-[:HAS_DURATION]->(dur:Duration)
OPTIONAL MATCH (p)-[:HAS_ELIGIBILITY]->(e:Eligibility)
OPTIONAL MATCH (p)-[:HAS_FEE_STRUCTURE]->(fs:FeeStructure)
OPTIONAL MATCH (fs)-[:INCLUDES_FEE]->(fc:FeeComponent)
OPTIONAL MATCH (fc)-[:OF_TYPE]->(ft:FeeType)
OPTIONAL MATCH (fc)-[:APPLIES_TO]->(sm:StudyMode)
WITH chunk, p, d, dur, e, fc, ft, sm
RETURN
'Program: '       + coalesce(p.name,'')   + '\n' +
'Department: '    + coalesce(d.name,'')   + '\n' +
'Duration: '      + coalesce(dur.name,'') + '\n' +
'Eligibility: '   + coalesce(e.name,'')   + '\n' +
'Fee Component: ' + coalesce(fc.name,'')  + '\n' +
'Fee Type: '      + coalesce(ft.name,'')  + '\n' +
'Study Mode: '    + coalesce(sm.name,'')  + '\n' +
'Context: '       + coalesce(chunk.text,'') AS info
"""
    )

    rag_template = RagTemplate(
    template='''
You are a university academic assistant. Answer ONLY what is asked.
Be concise and direct. Do NOT mention course codes unless asked.
All fee amounts are in Pakistani Rupees (PKR). Never use $ or USD symbols.
If data is missing, say "Not found in context."

Question: {query_text}

Context:
{context}

Answer:''',
    expected_inputs=['query_text', 'context']
)

    v_rag = GraphRAG(llm=rag_llm, retriever=vector_retriever, prompt_template=rag_template)
    g_rag = GraphRAG(llm=rag_llm, retriever=graph_retriever, prompt_template=rag_template)

    return v_rag, g_rag


def run_rag(rag_instance, query: str, top_k: int) -> tuple[str, float]:
    t0 = time.time()
    result = rag_instance.search(query, retriever_config={"top_k": top_k})
    return result.answer, round(time.time() - t0, 2)


def save_response(query: str, answer: str, source: str):
    """Save RAG response to JSON file for TTS ingestion."""
    try:
        output_path = Path("rag_responses.json")
        
        # Load existing responses if file exists
        if output_path.exists():
            with open(output_path, "r", encoding="utf-8") as f:
                responses = json.load(f)
        else:
            responses = []
        
        # Build new entry
        entry = {
            "response_text": answer,
            "source": "KnowledgeGraph",
            "rag_type": source,          # "VectorRAG" or "GraphRAG"
            "query": query,
            "timestamp": datetime.now().isoformat()
        }
        
        responses.append(entry)
        
        # Save back
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(responses, f, indent=2, ensure_ascii=False)
        
        return entry
    except Exception as e:
        # Log error but don't crash the app
        print(f"Error saving response: {e}")
        return None




# ── Session State ─────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "last_query" not in st.session_state:
    st.session_state.last_query = ""


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="app-title">◈ UniQuery</p>', unsafe_allow_html=True)
    st.markdown('<p class="app-subtitle">GraphRAG · Knowledge Engine</p>', unsafe_allow_html=True)

    st.markdown('<p class="section-label">Retrieval Mode</p>', unsafe_allow_html=True)
    mode = st.radio(
        "mode",
        ["◈ Both Side by Side", "◭ Vector RAG Only", "⬡ Graph RAG Only"],
        label_visibility="collapsed"
    )

    st.markdown('<p class="section-label">Settings</p>', unsafe_allow_html=True)
    top_k = st.slider("Top-K Results", min_value=3, max_value=15, value=5, step=1)

    st.markdown('<p class="section-label">Connection</p>', unsafe_allow_html=True)
    if st.button("Test Neo4j Connection", use_container_width=True, type="secondary"):
        try:
            init_graphrag()
            st.success("Connected ✓")
        except Exception as e:
            st.error(f"Failed: {e}")

    # Query History
    if st.session_state.history:
        st.markdown('<p class="section-label">Recent Queries</p>', unsafe_allow_html=True)
        for q in reversed(st.session_state.history[-6:]):
            st.markdown(f'<div class="history-item">↩ {q[:48]}{"…" if len(q)>48 else ""}</div>',
                       unsafe_allow_html=True)
        if st.button("Clear History", use_container_width=True, type="secondary"):
            st.session_state.history = []
            st.rerun()

    # Download responses for TTS
    response_file = Path("rag_responses.json")
    if response_file.exists():
        st.markdown('<p class="section-label">TTS Export</p>', unsafe_allow_html=True)
        
        with open(response_file, "r", encoding="utf-8") as f:
            responses = json.load(f)
        
        # Latest response only (for direct TTS ingestion)
        if responses:
            latest = responses[-1]
            st.markdown(f"""
            <div style="background:rgba(20,168,138,0.08); border:1px solid rgba(20,168,138,0.2);
            border-radius:8px; padding:0.75rem; font-size:0.7rem; 
            color:rgba(232,230,224,0.6); font-family: DM Mono, monospace;
            margin-bottom:0.75rem; line-height:1.6;">
            <span style="color:#14a88a">Latest →</span><br>
            {latest['response_text'][:120]}{'…' if len(latest['response_text'])>120 else ''}
            </div>
            """, unsafe_allow_html=True)
        
        # Download full file
        st.download_button(
            label="⬇ Download Responses JSON",
            data=open(response_file, "r", encoding="utf-8").read(),
            file_name="rag_responses.json",
            mime="application/json",
            use_container_width=True,
            type="secondary"
        )
        
        # Clear responses
        if st.button("✕ Clear Responses", use_container_width=True, type="secondary"):
            response_file.unlink()
            st.success("Cleared.")
            st.rerun()


# ── Main Area ─────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom: 0.25rem;">
    <span style="font-family: Syne, sans-serif; font-size: 1.5rem; font-weight: 800;
    background: linear-gradient(135deg, #e8e6e0, #9b8fd4 60%, #14a88a);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
    Ask the Knowledge Graph
    </span>
</div>
<p style="font-size:0.72rem; color:rgba(232,230,224,0.3); letter-spacing:0.1em;
font-family: DM Mono, monospace; margin-bottom: 1.75rem;">
University admissions · Programs · Fee structures · Courses
</p>
""", unsafe_allow_html=True)

# Query input
query = st.text_area(
    "query",
    placeholder="e.g. What is the fee structure for BS Computer Science?",
    height=90,
    label_visibility="collapsed",
    value=st.session_state.last_query
)

col_btn1, col_btn2, col_spacer = st.columns([1.2, 1, 5])
with col_btn1:
    run_btn = st.button("◈ Run Query", type="primary", use_container_width=True)
with col_btn2:
    if st.button("✕ Clear", type="secondary", use_container_width=True):
        st.session_state.last_query = ""
        st.rerun()

st.markdown("<hr style='margin: 1.5rem 0'>", unsafe_allow_html=True)

# ── Run Query ─────────────────────────────────────────────────────────────────
if run_btn and query.strip():
    st.session_state.last_query = query

    # Add to history
    if query not in st.session_state.history:
        st.session_state.history.append(query)

    # Load components
    with st.spinner(""):
        st.markdown('<div class="status-bar">⟳ &nbsp; Initializing retrieval components...</div>',
                   unsafe_allow_html=True)
        try:
            v_rag, g_rag = init_graphrag()
        except Exception as e:
            st.error(f"Connection error: {e}")
            st.stop()

    run_vector = mode in ["◈ Both Side by Side", "◭ Vector RAG Only"]
    run_graph  = mode in ["◈ Both Side by Side", "⬡ Graph RAG Only"]

    v_answer, v_time = "", 0.0
    g_answer, g_time = "", 0.0

    # Run selected RAG(s)
    with st.spinner("Querying knowledge graph..."):
        if run_vector:
            try:
                v_answer, v_time = run_rag(v_rag, query, top_k)
                if v_answer:
                    save_response(query, v_answer, "VectorRAG")  # ← add this
            except Exception as e:
                v_answer = f"Error: {e}"

        if run_graph:
            try:
                g_answer, g_time = run_rag(g_rag, query, top_k)
                if g_answer:
                    save_response(query, g_answer, "GraphRAG")   # ← add this
            except Exception as e:
                g_answer = f"Error: {e}"

    # ── Display Results ────────────────────────────────────────────────────────
    if mode == "◈ Both Side by Side":
        col_v, col_g = st.columns(2, gap="medium")

        with col_v:
            st.markdown(f"""
            <div class="answer-card vector">
                <div class="card-header">
                    <span class="card-badge badge-vector">Vector RAG</span>
                    <span class="card-title">Semantic Search</span>
                </div>
                <div class="card-body">{v_answer or '<span class="card-empty">No answer returned.</span>'}</div>
                <div class="timing-tag">⏱ {v_time}s · top-{top_k} chunks</div>
            </div>
            """, unsafe_allow_html=True)

        with col_g:
            st.markdown(f"""
            <div class="answer-card graph">
                <div class="card-header">
                    <span class="card-badge badge-graph">Graph RAG</span>
                    <span class="card-title">Graph Traversal</span>
                </div>
                <div class="card-body">{g_answer or '<span class="card-empty">No answer returned.</span>'}</div>
                <div class="timing-tag">⏱ {g_time}s · top-{top_k} nodes</div>
            </div>
            """, unsafe_allow_html=True)

    elif mode == "◭ Vector RAG Only":
        st.markdown(f"""
        <div class="answer-card vector">
            <div class="card-header">
                <span class="card-badge badge-vector">Vector RAG</span>
                <span class="card-title">Semantic Search Answer</span>
            </div>
            <div class="card-body">{v_answer or '<span class="card-empty">No answer returned.</span>'}</div>
            <div class="timing-tag">⏱ {v_time}s · top-{top_k} chunks</div>
        </div>
        """, unsafe_allow_html=True)

    elif mode == "⬡ Graph RAG Only":
        st.markdown(f"""
        <div class="answer-card graph">
            <div class="card-header">
                <span class="card-badge badge-graph">Graph RAG</span>
                <span class="card-title">Graph Traversal Answer</span>
            </div>
            <div class="card-body">{g_answer or '<span class="card-empty">No answer returned.</span>'}</div>
            <div class="timing-tag">⏱ {g_time}s · top-{top_k} nodes</div>
        </div>
        """, unsafe_allow_html=True)

elif run_btn and not query.strip():
    st.warning("Please enter a question first.")

else:
    # Empty state
    if mode == "◈ Both Side by Side":
        col_v, col_g = st.columns(2, gap="medium")
        with col_v:
            st.markdown("""
            <div class="answer-card vector">
                <div class="card-header">
                    <span class="card-badge badge-vector">Vector RAG</span>
                    <span class="card-title">Semantic Search</span>
                </div>
                <div class="card-empty">Your answer will appear here.</div>
            </div>
            """, unsafe_allow_html=True)
        with col_g:
            st.markdown("""
            <div class="answer-card graph">
                <div class="card-header">
                    <span class="card-badge badge-graph">Graph RAG</span>
                    <span class="card-title">Graph Traversal</span>
                </div>
                <div class="card-empty">Your answer will appear here.</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        is_vector = mode == "◭ Vector RAG Only"
        st.markdown(f"""
        <div class="answer-card {'vector' if is_vector else 'graph'}">
            <div class="card-header">
                <span class="card-badge {'badge-vector' if is_vector else 'badge-graph'}">
                    {'Vector RAG' if is_vector else 'Graph RAG'}
                </span>
                <span class="card-title">
                    {'Semantic Search' if is_vector else 'Graph Traversal'}
                </span>
            </div>
            <div class="card-empty">Your answer will appear here.</div>
        </div>
        """, unsafe_allow_html=True)