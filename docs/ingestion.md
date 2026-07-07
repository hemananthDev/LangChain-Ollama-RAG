# `ingestion.py` — Document Ingestion

## Purpose

`ingestion.py` owns the write path of the RAG system. It takes a raw document file, processes it into chunks, embeds those chunks, and persists them to a Chroma vector database on disk. It exposes a single public function: `ingest_document`.

---

## Full File

```python
"""
Ingest a document into a Chroma vector database.
"""

from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
)
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import CHUNK_OVERLAP, CHUNK_SIZE, EMBEDDING_MODEL, VECTOR_DB_ROOT


def load_documents(file_path):
    extension = Path(file_path).suffix.lower()

    if extension == ".txt":
        loader = TextLoader(file_path, encoding="utf-8")
    elif extension == ".pdf":
        loader = PyPDFLoader(file_path)
    elif extension == ".docx":
        loader = Docx2txtLoader(file_path)
    else:
        raise ValueError(
            f"Unsupported file type: {extension}\n"
            "Supported formats: .txt, .pdf, .docx"
        )

    return loader.load()


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    return splitter.split_documents(documents)


def create_vector_store(documents, persist_directory):
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=str(persist_directory),
    )


def ingest_document(file_path):
    file_path = Path(file_path).expanduser()

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    VECTOR_DB_ROOT.mkdir(exist_ok=True)

    db_name = f"{file_path.stem} Knowledge Base"
    vector_db_path = VECTOR_DB_ROOT / db_name

    documents = load_documents(str(file_path))
    chunks = split_documents(documents)
    create_vector_store(chunks, vector_db_path)

    return db_name
```

---

## Line-by-Line Breakdown

### Imports

```python
from pathlib import Path
```
Used to manipulate file paths in an OS-agnostic way — extracting extensions, stems, and constructing directory paths.

```python
from langchain_chroma import Chroma
```
The LangChain wrapper around ChromaDB. `Chroma.from_documents` is the class method used to create and persist a new vector store from a list of documents.

```python
from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
)
```
Three format-specific loaders from LangChain's community package:
- `TextLoader` — reads plain text files
- `PyPDFLoader` — extracts text from PDFs page by page using `pypdf`
- `Docx2txtLoader` — extracts text from `.docx` Word documents using `docx2txt`

```python
from langchain_ollama import OllamaEmbeddings
```
LangChain's integration with Ollama's embedding endpoint. Sends text to the locally running Ollama server and returns embedding vectors.

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter
```
The splitter that breaks documents into chunks. "Recursive" means it tries progressively finer separators until chunks fit within `CHUNK_SIZE`.

```python
from config import CHUNK_OVERLAP, CHUNK_SIZE, EMBEDDING_MODEL, VECTOR_DB_ROOT
```
All four constants this module needs, imported from the central config. No values are hardcoded here.

---

### `load_documents(file_path)`

```python
extension = Path(file_path).suffix.lower()
```
Extracts the file extension (e.g. `.pdf`) and lowercases it so `.PDF` and `.pdf` are treated identically.

```python
if extension == ".txt":
    loader = TextLoader(file_path, encoding="utf-8")
elif extension == ".pdf":
    loader = PyPDFLoader(file_path)
elif extension == ".docx":
    loader = Docx2txtLoader(file_path)
else:
    raise ValueError(...)
```
Selects the appropriate loader based on extension. If the extension is not supported, a `ValueError` is raised immediately with a helpful message listing the supported formats. This error propagates up to `app.py` where it is caught and displayed to the user.

```python
return loader.load()
```
Calls the loader's `load()` method, which reads the file and returns a list of `Document` objects. Each `Document` has `page_content` (the text) and `metadata` (source info like file path and page number).

---

### `split_documents(documents)`

```python
splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
)
```
Creates a splitter configured with the values from `config.py`. The splitter tries to split on `\n\n`, then `\n`, then `. `, then ` `, then individual characters — using the first separator that produces chunks within `CHUNK_SIZE`.

```python
return splitter.split_documents(documents)
```
Splits every `Document` in the list and returns a new, larger list of smaller `Document` objects. Each chunk inherits the metadata of its parent document.

---

### `create_vector_store(documents, persist_directory)`

```python
embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
```
Creates an embeddings instance that will call the locally running Ollama server to generate vectors. No embedding happens at this line — it just configures the client.

```python
Chroma.from_documents(
    documents=documents,
    embedding=embeddings,
    persist_directory=str(persist_directory),
)
```
This single call does three things:
1. Iterates over every chunk in `documents`
2. Calls `embeddings` to convert each chunk's `page_content` into a vector
3. Writes all vectors, text, and metadata to a Chroma database at `persist_directory`

`persist_directory` is converted to a string because Chroma expects a `str`, not a `Path` object.

---

### `ingest_document(file_path)` — Public API

```python
file_path = Path(file_path).expanduser()
```
Converts the input to a `Path` object and expands `~` to the user's home directory, so paths like `~/Documents/file.pdf` work correctly.

```python
if not file_path.exists():
    raise FileNotFoundError(f"File not found: {file_path}")
```
Validates the file exists before doing any work. Raises a clear error that propagates to the UI.

```python
VECTOR_DB_ROOT.mkdir(exist_ok=True)
```
Creates the `VectorDB/` root directory if it doesn't already exist. `exist_ok=True` means no error is raised if it already exists.

```python
db_name = f"{file_path.stem} Knowledge Base"
```
Derives the knowledge base name from the filename without its extension. For example, `report.pdf` becomes `"report Knowledge Base"`. This name is used as both the folder name on disk and the display name in the UI.

```python
vector_db_path = VECTOR_DB_ROOT / db_name
```
Constructs the full path where this knowledge base will be stored: `VectorDB/report Knowledge Base/`.

```python
documents = load_documents(str(file_path))
chunks = split_documents(documents)
create_vector_store(chunks, vector_db_path)
```
Orchestrates the three internal steps in sequence: load → split → embed and persist.

```python
return db_name
```
Returns the knowledge base name so the caller (`app.py`) can immediately set it as the active KB and display it in the UI.
