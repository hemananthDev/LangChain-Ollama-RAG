"""
Streamlit UI for the RAG system.
"""

import shutil
from pathlib import Path

import streamlit as st

from config import VECTOR_DB_ROOT
from ingestion import ingest_document
from main import create_retrieval_chain, load_vector_store


def list_knowledge_bases():
    VECTOR_DB_ROOT.mkdir(exist_ok=True)
    return sorted(f.name for f in VECTOR_DB_ROOT.iterdir() if f.is_dir())


THEMES = {
    "dark": {"bg": "#0e1117", "sidebar": "#1a1d23", "text": "#fafafa", "bubble": "#1e2128", "border": "#2e3138"},
    "light": {"bg": "#ffffff", "sidebar": "#f0f2f6", "text": "#0e1117", "bubble": "#f0f2f6", "border": "#d0d3da"},
}


def apply_theme():
    t = THEMES[st.session_state.get("theme", "dark")]
    st.markdown(f"""
    <style>
        .stApp {{ background-color: {t['bg']}; color: {t['text']}; }}
        section[data-testid="stSidebar"] {{ background-color: {t['sidebar']}; }}
        .stChatMessage {{ background-color: {t['bubble']}; border: 1px solid {t['border']}; border-radius: 8px; }}
    </style>
    """, unsafe_allow_html=True)


def get_chain(db_name):
    if st.session_state.get("loaded_kb") != db_name:
        vectorstore = load_vector_store(db_name)
        st.session_state.chain = create_retrieval_chain(vectorstore)
        st.session_state.loaded_kb = db_name
    return st.session_state.chain


# ── Sidebar ──────────────────────────────────────────────────────────────────

st.set_page_config(page_title="RAG Chat", layout="wide")

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

apply_theme()

with st.sidebar:
    st.title("Knowledge Bases")
    icon = "☀️" if st.session_state.theme == "dark" else "🌙"
    if st.button(f"{icon} {'Light' if st.session_state.theme == 'dark' else 'Dark'} Mode", use_container_width=True):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()
    st.divider()

    databases = list_knowledge_bases()

    for db in databases:
        cols = st.columns([3, 1, 1])
        if cols[0].button(db, key=f"kb_{db}", use_container_width=True):
            st.session_state.active_kb = db
            st.session_state.messages = []
            st.session_state.pop("chain", None)
            st.session_state.pop("loaded_kb", None)

        if cols[1].button("🗑️", key=f"del_chat_{db}", help="Clear chat"):
            if st.session_state.get("active_kb") == db:
                st.session_state.messages = []

        if cols[2].button("❌", key=f"del_kb_{db}", help="Delete KB"):
            shutil.rmtree(VECTOR_DB_ROOT / db, ignore_errors=True)
            if st.session_state.get("active_kb") == db:
                st.session_state.pop("active_kb", None)
                st.session_state.messages = []
                st.session_state.pop("chain", None)
                st.session_state.pop("loaded_kb", None)
            st.rerun()

    st.divider()
    st.subheader("Add Knowledge Base")
    uploaded = st.file_uploader("Upload document", type=["pdf", "txt", "docx"])

    if uploaded and st.button("Ingest"):
        tmp_path = Path(uploaded.name)
        tmp_path.write_bytes(uploaded.read())
        with st.spinner("Ingesting document…"):
            try:
                db_name = ingest_document(str(tmp_path))
                st.session_state.active_kb = db_name
                st.session_state.messages = []
                st.session_state.pop("chain", None)
                st.session_state.pop("loaded_kb", None)
                st.success(f"Created: {db_name}")
            except Exception as e:
                st.error(str(e))
            finally:
                tmp_path.unlink(missing_ok=True)
        st.rerun()


# ── Main chat area ────────────────────────────────────────────────────────────

active_kb = st.session_state.get("active_kb")

if not active_kb:
    st.info("Select or create a knowledge base from the sidebar to start chatting.")
    st.stop()

st.header(f"💬 {active_kb}")

col1, col2, col3 = st.columns([1, 1, 6])
if col1.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()
if col2.button("Delete KB + Chat"):
    shutil.rmtree(VECTOR_DB_ROOT / active_kb, ignore_errors=True)
    st.session_state.pop("active_kb", None)
    st.session_state.messages = []
    st.session_state.pop("chain", None)
    st.session_state.pop("loaded_kb", None)
    st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if question := st.chat_input("Ask a question…"):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                chain = get_chain(active_kb)
                answer = chain.invoke(question)
            except Exception as e:
                answer = f"Error: {e}"
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
