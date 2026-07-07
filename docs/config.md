# `config.py` — Central Configuration

## Purpose

`config.py` is the single source of truth for every tunable parameter in the project. No other file defines constants — they all import from here. This means changing a model name, chunk size, or database path requires editing exactly one file.

---

## Full File

```python
"""
Central configuration for the RAG system.
All tunable parameters live here.
"""

from pathlib import Path

# Paths
VECTOR_DB_ROOT = Path("VectorDB")

# Models
EMBEDDING_MODEL = "nomic-embed-text:latest"
LLM_MODEL = "llama3.2:latest"

# Retrieval
TOP_K = 3

# Chunking
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
```

---

## Line-by-Line Breakdown

### Import

```python
from pathlib import Path
```

`Path` is used to represent filesystem paths in an OS-agnostic way. `Path("VectorDB")` works correctly on both Windows and Unix without needing to hardcode separators.

---

### `VECTOR_DB_ROOT`

```python
VECTOR_DB_ROOT = Path("VectorDB")
```

The root directory where all Chroma vector databases are persisted. Each knowledge base gets its own subdirectory inside this folder: `VectorDB/<kb_name>/`.

This is a relative path, so it resolves relative to wherever the application is launched from. Since `run.py` is always launched from the project root, this consistently points to `RAGv2/VectorDB/`.

Used by: `ingestion.py`, `main.py`, `app.py`

---

### `EMBEDDING_MODEL`

```python
EMBEDDING_MODEL = "nomic-embed-text:latest"
```

The Ollama model used to convert text into vector embeddings. `nomic-embed-text` is a lightweight, high-quality embedding model well-suited for semantic search tasks.

This model is used in two places:
- `ingestion.py` — to embed document chunks before storing them
- `main.py` — to embed the user's query before searching

Both uses must reference the same model, which is guaranteed by this single constant.

To use a different embedding model, change this value and re-ingest all documents (existing databases were embedded with the old model and are incompatible).

---

### `LLM_MODEL`

```python
LLM_MODEL = "llama3.2:latest"
```

The Ollama model used to generate answers. `llama3.2` is Meta's instruction-tuned model, capable of following the prompt's instructions to answer only from the provided context.

Used only in `main.py` when constructing the `ChatOllama` instance.

To swap to a different LLM (e.g. `mistral:latest`, `gemma2:latest`), change this value — no other file needs to change.

---

### `TOP_K`

```python
TOP_K = 3
```

The number of document chunks retrieved from the vector store for each query. The retriever fetches the `TOP_K` most semantically similar chunks and passes them as context to the LLM.

- Increasing `TOP_K` gives the LLM more context, which can improve answer quality for complex questions, but increases prompt size and response latency.
- Decreasing `TOP_K` speeds up responses but may miss relevant information.

Used only in `main.py`.

---

### `CHUNK_SIZE`

```python
CHUNK_SIZE = 1000
```

The maximum number of characters in a single document chunk after splitting. The splitter will try to break at natural boundaries (paragraphs, sentences) but will hard-cut at this limit.

- Smaller chunks produce more precise retrieval but may lack enough context for the LLM to form a complete answer.
- Larger chunks provide more context per retrieved piece but reduce retrieval precision.

Used only in `ingestion.py`.

---

### `CHUNK_OVERLAP`

```python
CHUNK_OVERLAP = 100
```

The number of characters shared between the end of one chunk and the start of the next. This prevents information at chunk boundaries from being lost.

For example, if a sentence spans the boundary between chunk 1 and chunk 2, the overlap ensures that sentence appears fully in at least one of the chunks.

Must be less than `CHUNK_SIZE`. Used only in `ingestion.py`.

---

## Who Imports What

| Constant | `ingestion.py` | `main.py` | `app.py` |
|---|---|---|---|
| `VECTOR_DB_ROOT` | ✓ | ✓ | ✓ |
| `EMBEDDING_MODEL` | ✓ | ✓ | — |
| `LLM_MODEL` | — | ✓ | — |
| `TOP_K` | — | ✓ | — |
| `CHUNK_SIZE` | ✓ | — | — |
| `CHUNK_OVERLAP` | ✓ | — | — |
