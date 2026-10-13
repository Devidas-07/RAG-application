import streamlit as st
import requests
import json
import os

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

st.set_page_config(page_title="RAG Search", page_icon="🔍", layout="centered")

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 2rem; max-width: 750px; }
    .search-title { text-align: center; font-size: 3rem; font-weight: 700;
                    color: #4285F4; margin-bottom: 0.2rem; }
    .search-sub   { text-align: center; color: #888; margin-bottom: 2rem; font-size: 0.95rem; }
    .answer-box   { background: #f8f9fa; border-left: 4px solid #4285F4;
                    padding: 1.2rem 1.5rem; border-radius: 8px; margin-top: 1.5rem; }
    .answer-label { font-size: 0.8rem; color: #4285F4; font-weight: 600;
                    text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; }
    .source-chip  { display: inline-block; background: #e8f0fe; color: #1a73e8;
                    border-radius: 12px; padding: 2px 10px; font-size: 0.78rem;
                    margin: 2px; }
    div[data-testid="stStatusWidget"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="search-title">🔍 RAG Search</div>', unsafe_allow_html=True)
st.markdown('<div class="search-sub">Ask anything from your uploaded documents</div>', unsafe_allow_html=True)

# ── Search Bar ─────────────────────────────────────────────────────────────────
with st.form("search_form", clear_on_submit=False):
    col1, col2 = st.columns([5, 1])
    with col1:
        question = st.text_input("", placeholder="Ask a question...", label_visibility="collapsed")
    with col2:
        submitted = st.form_submit_button("Search", use_container_width=True)

# ── Search Result ──────────────────────────────────────────────────────────────
if submitted and question.strip():
    try:
        answer_placeholder = st.empty()
        context_data = []
        full_answer = ""

        with requests.post(
            f"{API_BASE}/ask/stream",
            json={"question": question.strip()},
            stream=True,
            timeout=300
        ) as res:
            res.raise_for_status()
            for raw_line in res.iter_lines():
                if not raw_line:
                    continue
                chunk = json.loads(raw_line)
                if chunk["type"] == "context":
                    context_data = chunk["context_used"]
                elif chunk["type"] == "token":
                    full_answer += chunk["token"]
                    answer_placeholder.markdown(f"""
                    <div class="answer-box">
                        <div class="answer-label">✨ AI Answer</div>
                        {full_answer}
                    </div>
                    """, unsafe_allow_html=True)

        sources = list({ctx.get("document", "") for ctx in context_data if ctx.get("document")})
        if sources:
            st.markdown("**Sources:**")
            chips = " ".join(f'<span class="source-chip">📄 {s}</span>' for s in sources)
            st.markdown(chips, unsafe_allow_html=True)

        with st.expander("📚 View context chunks"):
            for i, ctx in enumerate(context_data, 1):
                st.markdown(f"**Chunk {i}** — `{ctx.get('document', '')}` | Score: `{ctx.get('score', '')}`")
                st.caption(ctx.get("text", ""))
                st.divider()

    except Exception as e:
        st.error(f"Cannot reach API: {e}")

elif submitted:
    st.warning("Please enter a question.")

# ── Sidebar: Upload & Delete ───────────────────────────────────────────────────
with st.sidebar:
    st.header("📄 Upload Document")
    uploaded_file = st.file_uploader("PDF or TXT", type=["pdf", "txt"])
    if st.button("Ingest", disabled=uploaded_file is None):
        with st.spinner("Ingesting..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                res = requests.post(f"{API_BASE}/ingest", files=files, timeout=120)
                if res.status_code == 200:
                    data = res.json()
                    st.success(f"✅ {data.get('chunks_created')} chunks created")
                    st.code(data.get("document_id", ""), language=None)
                else:
                    st.error(res.json().get("detail", "Ingestion failed"))
            except Exception as e:
                st.error(f"Error: {e}")

    st.divider()
    st.header("🗑️ Delete Document")
    doc_id = st.text_input("Document ID")
    if st.button("Delete", disabled=not doc_id.strip()):
        try:
            res = requests.delete(f"{API_BASE}/documents/{doc_id.strip()}", timeout=10)
            if res.status_code == 200:
                st.success("Deleted successfully")
            else:
                st.error(res.json().get("detail", "Delete failed"))
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()
    if st.button("⚡ Health Check"):
        try:
            res = requests.get(f"{API_BASE}/health", timeout=5)
            d = res.json()
            st.success(d["status"])
            st.info(f"Ollama: {'✅' if d['ollama_connected'] else '❌'}")
        except Exception as e:
            st.error(f"API unreachable: {e}")
