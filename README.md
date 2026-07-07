# LangChain-Ollama-RAG

A fully local RAG application that lets you chat with your own documents using Ollama LLMs and a ChromaDB vector store, served through an interactive Streamlit UI.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [Supported Document Formats](#supported-document-formats)

---

## Overview

LangChain-Ollama-RAG ingests documents into a persistent Chroma vector database, then answers questions about them by retrieving the most relevant chunks and passing them as context to a local LLM running via Ollama. Everything runs entirely on your machine — no external API calls, no data leaves your system.

---

## Features

- **Multi-KB sidebar** — switch between knowledge bases in one click; each session is isolated
- **Document ingestion** — upload PDF, TXT, or DOCX files directly from the UI
- **Session management** — clear chat history, delete a knowledge base, or delete both independently
- **Loading animation** — spinner shown while the LLM is generating a response
- **Dark / Light mode** — toggle between themes from the sidebar
- **Fully local** — powered by Ollama; no internet connection required after setup

---

## Project Structure

```
LangChain-Ollama-RAG/
├── run.py            # Entry point — launches the Streamlit app
├── app.py            # Streamlit UI (sidebar, chat, theme toggle)
├── main.py           # Vector store loading & RAG chain construction
├── ingestion.py      # Document loading, chunking, and embedding
├── config.py         # All tunable parameters in one place
├── requirements.txt  # Python dependencies
├── pyproject.toml    # Project metadata
├── .gitignore
└── VectorDB/         # Auto-created; stores persisted Chroma databases
```

---

## Prerequisites

- Python 3.11 or higher
- [Ollama](https://ollama.com) installed and running locally

Pull the required models before starting:

```bash
ollama pull llama3.2:latest
ollama pull nomic-embed-text:latest
```

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/hemananthDev/LangChain-Ollama-RAG
cd LangChain-Ollama-RAG
```

2. Create and activate a virtual environment:

```bash
# using uv
uv venv
# using pip
python -m venv .venv
```
```bash
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

3. Install dependencies:

```bash
# using uv
uv sync
# using pip
pip install -r requirements.txt
```

---

## Configuration

All tunable parameters live in `config.py`:

| Parameter | Default | Description |
|---|---|---|
| `VECTOR_DB_ROOT` | `VectorDB/` | Directory where Chroma databases are persisted |
| `EMBEDDING_MODEL` | `nomic-embed-text:latest` | Ollama embedding model used for ingestion and retrieval |
| `LLM_MODEL` | `llama3.2:latest` | Ollama LLM used to generate answers |
| `TOP_K` | `3` | Number of document chunks retrieved per query |
| `CHUNK_SIZE` | `1000` | Maximum characters per document chunk |
| `CHUNK_OVERLAP` | `100` | Overlapping characters between consecutive chunks |

To swap models or tune chunking, edit `config.py` only — no other file needs to change.

---

## Usage

Start the application:

```bash
python run.py
```

This launches the Streamlit UI in your browser automatically.

### Creating a Knowledge Base

1. In the sidebar, scroll to **Add Knowledge Base**
2. Upload a PDF, TXT, or DOCX file
3. Click **Ingest** — the document is chunked, embedded, and saved to `VectorDB/`
4. The new knowledge base is selected automatically

### Chatting

1. Click a knowledge base name in the sidebar to activate it
2. Type your question in the chat input at the bottom
3. The app retrieves the most relevant chunks and streams the LLM's answer

### Managing Sessions

| Action | How |
|---|---|
| Switch knowledge base | Click its name in the sidebar |
| Clear chat history only | Click 🗑️ next to the KB name in the sidebar |
| Delete knowledge base only | Click ❌ next to the KB name in the sidebar |
| Clear chat + delete KB | Click **Delete KB + Chat** in the main area |
| Clear chat (active KB) | Click **Clear Chat** in the main area |

### Theme

Click **☀️ Light Mode** or **🌙 Dark Mode** at the top of the sidebar to toggle themes.

---

## How It Works

```
Document
   │
   ▼
load_documents()        # Loads PDF / TXT / DOCX via LangChain loaders
   │
   ▼
split_documents()       # Splits into chunks (CHUNK_SIZE, CHUNK_OVERLAP)
   │
   ▼
OllamaEmbeddings        # Embeds each chunk using EMBEDDING_MODEL
   │
   ▼
ChromaDB                # Persists vectors to VectorDB/<kb_name>/
   │
   ▼  (at query time)
Retriever               # Fetches TOP_K most similar chunks
   │
   ▼
ChatPromptTemplate      # Injects chunks as context + user question
   │
   ▼
ChatOllama (LLM_MODEL)  # Generates the answer locally
   │
   ▼
StrOutputParser         # Returns plain text to the UI
```

---

## Supported Document Formats

| Format | Extension |
|---|---|
| Plain text | `.txt` |
| PDF | `.pdf` |
| Word document | `.docx` |
