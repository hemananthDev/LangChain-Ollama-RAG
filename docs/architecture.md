# Architecture

## Overview

LangChain-Ollama-RAG is structured around a clean separation of concerns. Each file has a single responsibility, and all configuration is centralised so no tunable value is ever hardcoded in logic files.

```
┌─────────────┐
│   run.py    │  ← single entry point
└──────┬──────┘
       │ subprocess
       ▼
┌─────────────┐
│   app.py    │  ← Streamlit UI layer
└──────┬──────┘
       │ imports
       ├──────────────────────┐
       ▼                      ▼
┌─────────────┐       ┌──────────────┐
│   main.py   │       │ ingestion.py │
└──────┬──────┘       └──────┬───────┘
       │                     │
       └──────────┬──────────┘
                  ▼
          ┌─────────────┐
          │  config.py  │  ← all parameters
          └─────────────┘
```

---

## Layers

### Entry Point — `run.py`

The sole purpose of `run.py` is to launch the Streamlit process. It uses `subprocess` to invoke `streamlit run app.py` via the same Python interpreter that called `run.py`. This means `python run.py` is the only command a user ever needs.

### UI Layer — `app.py`

`app.py` owns everything the user sees and interacts with:

- Sidebar: knowledge base list, theme toggle, document uploader
- Main area: chat header, session action buttons, chat history, chat input
- Theme: CSS injection via `st.markdown` based on session state
- State management: all Streamlit session state keys (`active_kb`, `messages`, `chain`, `loaded_kb`, `theme`) are managed here

`app.py` never directly touches the filesystem for vector data — it delegates to `ingestion.py` and `main.py`.

### RAG Logic — `main.py`

`main.py` is responsible for two things:

1. Loading an existing Chroma vector store from disk
2. Building the LangChain LCEL retrieval chain

It has no UI code and no ingestion code. It exposes `load_vector_store` and `create_retrieval_chain` as its public API.

### Ingestion — `ingestion.py`

`ingestion.py` handles the write path: taking a raw document file and producing a persisted Chroma vector database. It exposes a single public function `ingest_document` which orchestrates loading, chunking, embedding, and persisting.

### Configuration — `config.py`

All tunable parameters live here. Every other module imports from `config.py` and never defines its own constants. This means changing a model, chunk size, or database path requires editing exactly one file.

---

## Data Flow

### Ingestion Path (write)

```
User uploads file (app.py)
        │
        ▼
ingest_document(file_path)          [ingestion.py]
        │
        ├── load_documents()        # reads file via LangChain loader
        │         │
        │         └── returns list of Document objects
        │
        ├── split_documents()       # RecursiveCharacterTextSplitter
        │         │
        │         └── returns list of smaller Document chunks
        │
        └── create_vector_store()   # OllamaEmbeddings + Chroma.from_documents
                  │
                  └── persists to VectorDB/<kb_name>/
```

### Query Path (read)

```
User types question (app.py)
        │
        ▼
get_chain(db_name)                  [app.py]
        │
        ├── load_vector_store()     [main.py]
        │         │
        │         └── Chroma(persist_directory=...) — loads from disk
        │
        └── create_retrieval_chain() [main.py]
                  │
                  └── returns LCEL chain
                            │
                            ▼
                  chain.invoke(question)
                            │
                  ┌─────────┴──────────┐
                  │                    │
                  ▼                    ▼
           retriever               RunnablePassthrough
           (TOP_K chunks)          (question passed through)
                  │                    │
                  └─────────┬──────────┘
                            ▼
                    ChatPromptTemplate
                    (context + question)
                            │
                            ▼
                      ChatOllama
                      (LLM_MODEL)
                            │
                            ▼
                     StrOutputParser
                     (plain text answer)
                            │
                            ▼
                    displayed in UI (app.py)
```

---

## State Management

Streamlit reruns the entire script on every user interaction. State is preserved across reruns using `st.session_state`. The keys used in this project are:

| Key | Type | Purpose |
|---|---|---|
| `theme` | `str` | Current theme: `"dark"` or `"light"` |
| `active_kb` | `str` | Name of the currently selected knowledge base |
| `messages` | `list` | Chat history for the active KB as `{"role", "content"}` dicts |
| `chain` | LangChain chain | Cached retrieval chain for the active KB |
| `loaded_kb` | `str` | Name of the KB the cached chain was built for |

The `chain` and `loaded_kb` keys work together as a simple cache: if `loaded_kb` matches `active_kb`, the chain is reused; otherwise it is rebuilt from disk.

---

## File Responsibilities Summary

| File | Reads disk | Writes disk | UI | LLM | Config |
|---|---|---|---|---|---|
| `run.py` | — | — | — | — | — |
| `app.py` | — | — | ✓ | — | ✓ |
| `main.py` | ✓ (Chroma) | — | — | ✓ | ✓ |
| `ingestion.py` | ✓ (document) | ✓ (Chroma) | — | — | ✓ |
| `config.py` | — | — | — | — | ✓ |
