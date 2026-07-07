# `app.py` — Streamlit UI

## Purpose

`app.py` is the entire user interface layer. It renders the sidebar, manages session state, handles document ingestion from the browser, and drives the chat interaction. It imports logic from `ingestion.py` and `main.py` but contains no RAG or embedding logic itself.

---

## Full File

```python
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
    "dark":  {"bg": "#0e1117", "sidebar": "#1a1d23", "text": "#fafafa", "bubble": "#1e2128", "border": "#2e3138"},
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
```

---

## Line-by-Line Breakdown

### Imports

```python
import shutil
```
Used to recursively delete knowledge base directories (`shutil.rmtree`) when the user clicks the delete button.

```python
from pathlib import Path
```
Used to construct the temporary file path when saving an uploaded document to disk before ingestion.

```python
import streamlit as st
```
The entire UI framework. Streamlit reruns the full script from top to bottom on every user interaction. State that must persist across reruns is stored in `st.session_state`.

```python
from config import VECTOR_DB_ROOT
from ingestion import ingest_document
from main import create_retrieval_chain, load_vector_store
```
Imports the only external dependencies this file needs. `app.py` never directly touches ChromaDB or Ollama — it delegates entirely to these modules.

---

### `list_knowledge_bases()`

```python
VECTOR_DB_ROOT.mkdir(exist_ok=True)
return sorted(f.name for f in VECTOR_DB_ROOT.iterdir() if f.is_dir())
```
Ensures `VectorDB/` exists, then returns a sorted list of all subdirectory names inside it. Each subdirectory is a knowledge base. Called on every rerun to keep the sidebar list up to date.

---

### `THEMES`

```python
THEMES = {
    "dark":  {"bg": "#0e1117", "sidebar": "#1a1d23", ...},
    "light": {"bg": "#ffffff", "sidebar": "#f0f2f6", ...},
}
```
A dict of colour palettes keyed by theme name. Each palette defines five CSS colour values:
- `bg` — main app background
- `sidebar` — sidebar background
- `text` — primary text colour
- `bubble` — chat message bubble background
- `border` — chat message bubble border

---

### `apply_theme()`

```python
t = THEMES[st.session_state.get("theme", "dark")]
```
Reads the current theme from session state, defaulting to `"dark"` if not yet set.

```python
st.markdown(f"""
<style>
    .stApp {{ background-color: {t['bg']}; color: {t['text']}; }}
    section[data-testid="stSidebar"] {{ background-color: {t['sidebar']}; }}
    .stChatMessage {{ background-color: {t['bubble']}; border: 1px solid {t['border']}; border-radius: 8px; }}
</style>
""", unsafe_allow_html=True)
```
Injects a `<style>` block into the page targeting Streamlit's internal CSS class names. `unsafe_allow_html=True` is required to inject raw HTML. The double braces `{{` and `}}` are Python f-string escapes for literal `{` and `}` characters in the CSS.

This function is called on every rerun, so the theme is always applied before anything is rendered.

---

### `get_chain(db_name)`

```python
if st.session_state.get("loaded_kb") != db_name:
    vectorstore = load_vector_store(db_name)
    st.session_state.chain = create_retrieval_chain(vectorstore)
    st.session_state.loaded_kb = db_name
return st.session_state.chain
```
A simple cache for the retrieval chain. Loading a vector store from disk and building a chain is expensive, so it is only done when the active KB changes. If `loaded_kb` already matches `db_name`, the cached chain is returned immediately without any disk I/O.

---

### Page Config & Theme Initialisation

```python
st.set_page_config(page_title="RAG Chat", layout="wide")
```
Must be the first Streamlit call in the script. Sets the browser tab title and uses the full browser width for the layout.

```python
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
```
Initialises the theme to dark on the very first run. On subsequent reruns, the existing value is preserved.

```python
apply_theme()
```
Injects the CSS for the current theme before any UI elements are rendered.

---

### Sidebar — Theme Toggle

```python
icon = "☀️" if st.session_state.theme == "dark" else "🌙"
if st.button(f"{icon} {'Light' if st.session_state.theme == 'dark' else 'Dark'} Mode", use_container_width=True):
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
    st.rerun()
```
Renders a button whose label reflects the opposite of the current theme (so clicking it switches to that theme). On click, the theme is toggled in session state and `st.rerun()` triggers a full script rerun, which calls `apply_theme()` again with the new value.

---

### Sidebar — Knowledge Base List

```python
databases = list_knowledge_bases()

for db in databases:
    cols = st.columns([3, 1, 1])
```
Fetches the current list of KBs and renders each one as a row of three columns in ratio 3:1:1.

```python
    if cols[0].button(db, key=f"kb_{db}", use_container_width=True):
        st.session_state.active_kb = db
        st.session_state.messages = []
        st.session_state.pop("chain", None)
        st.session_state.pop("loaded_kb", None)
```
The wide left column shows the KB name as a button. Clicking it sets this KB as active, clears the chat history, and invalidates the chain cache so a fresh chain is built for the new KB on the next question.

```python
    if cols[1].button("🗑️", key=f"del_chat_{db}", help="Clear chat"):
        if st.session_state.get("active_kb") == db:
            st.session_state.messages = []
```
The middle column is a trash icon button. It only clears messages if this KB is currently active — clearing chat for an inactive KB would have no visible effect.

```python
    if cols[2].button("❌", key=f"del_kb_{db}", help="Delete KB"):
        shutil.rmtree(VECTOR_DB_ROOT / db, ignore_errors=True)
        if st.session_state.get("active_kb") == db:
            st.session_state.pop("active_kb", None)
            st.session_state.messages = []
            st.session_state.pop("chain", None)
            st.session_state.pop("loaded_kb", None)
        st.rerun()
```
The right column deletes the KB folder from disk. `ignore_errors=True` prevents crashes if the folder was already deleted. If the deleted KB was active, all related session state is cleared. `st.rerun()` refreshes the sidebar list.

---

### Sidebar — Document Uploader

```python
uploaded = st.file_uploader("Upload document", type=["pdf", "txt", "docx"])
```
Renders a file upload widget restricted to the three supported formats.

```python
if uploaded and st.button("Ingest"):
    tmp_path = Path(uploaded.name)
    tmp_path.write_bytes(uploaded.read())
```
When both a file is uploaded and the Ingest button is clicked, the uploaded file (which exists only in memory as a `BytesIO` object) is written to a temporary file on disk. This is necessary because the LangChain loaders require a real file path.

```python
    with st.spinner("Ingesting document…"):
        try:
            db_name = ingest_document(str(tmp_path))
            ...
            st.success(f"Created: {db_name}")
        except Exception as e:
            st.error(str(e))
        finally:
            tmp_path.unlink(missing_ok=True)
```
`st.spinner` shows a loading animation during ingestion (which can take several seconds for large documents). The `finally` block ensures the temporary file is always deleted, even if ingestion fails.

---

### Main Area — Guard & Header

```python
active_kb = st.session_state.get("active_kb")

if not active_kb:
    st.info("Select or create a knowledge base from the sidebar to start chatting.")
    st.stop()
```
If no KB is selected, shows an info message and halts script execution. `st.stop()` prevents the rest of the page from rendering.

```python
st.header(f"💬 {active_kb}")
```
Displays the active KB name as the page header.

---

### Main Area — Action Buttons

```python
col1, col2, col3 = st.columns([1, 1, 6])
if col1.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()
```
Clears only the chat history for the active KB, leaving the KB and its chain intact.

```python
if col2.button("Delete KB + Chat"):
    shutil.rmtree(VECTOR_DB_ROOT / active_kb, ignore_errors=True)
    st.session_state.pop("active_kb", None)
    st.session_state.messages = []
    st.session_state.pop("chain", None)
    st.session_state.pop("loaded_kb", None)
    st.rerun()
```
Deletes the KB folder from disk and clears all related session state in one action.

---

### Chat History Rendering

```python
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
```
Initialises the message list if it doesn't exist, then renders every message in the history. `st.chat_message` renders a bubble with the appropriate avatar for `"user"` or `"assistant"`.

---

### Chat Input & Response

```python
if question := st.chat_input("Ask a question…"):
```
The walrus operator (`:=`) both checks if the user submitted a question and assigns it to `question` in one expression. `st.chat_input` renders a fixed input bar at the bottom of the page.

```python
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
```
Appends the user's message to history and immediately renders it in the chat.

```python
    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                chain = get_chain(active_kb)
                answer = chain.invoke(question)
            except Exception as e:
                answer = f"Error: {e}"
        st.markdown(answer)
```
Opens an assistant chat bubble, shows a spinner while the chain runs, then renders the answer inside the same bubble. The spinner disappears as soon as `chain.invoke` returns. Any exception is caught and displayed as the answer rather than crashing the app.

```python
    st.session_state.messages.append({"role": "assistant", "content": answer})
```
Appends the assistant's answer to history so it persists across reruns.
