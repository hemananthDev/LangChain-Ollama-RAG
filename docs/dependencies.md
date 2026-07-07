# Dependencies

All dependencies are declared in both `pyproject.toml` (for `uv`) and `requirements.txt` (for `pip`).

---

## Runtime Dependencies

### `streamlit>=1.35.0`

The web UI framework. Streamlit turns a Python script into an interactive browser application with no frontend code required. It handles routing, state management via `st.session_state`, and re-rendering the page on every user interaction.

Used in: `app.py`

---

### `langchain>=1.3.11`

The core LangChain package. Provides the foundational abstractions used throughout the project:
- `ChatPromptTemplate` — structured prompt templates with named placeholders
- `RunnablePassthrough` — a no-op runnable for routing values through a chain
- `StrOutputParser` — extracts plain text from LLM response objects
- The `|` pipe operator for composing LCEL chains

Used in: `main.py`

---

### `langchain-ollama>=1.1.0`

LangChain's integration package for Ollama. Provides:
- `ChatOllama` — a chat model interface that sends prompts to a locally running Ollama LLM and returns responses
- `OllamaEmbeddings` — an embeddings interface that sends text to Ollama's embedding endpoint and returns vectors

Both classes communicate with the Ollama server at `localhost:11434`.

Used in: `main.py`, `ingestion.py`

---

### `langchain-chroma>=1.1.0`

LangChain's integration package for ChromaDB. Provides the `Chroma` class which wraps the ChromaDB client with LangChain's vector store interface:
- `Chroma.from_documents` — creates and persists a new vector store from a list of documents
- `Chroma(persist_directory=...)` — loads an existing vector store from disk
- `.as_retriever()` — converts the vector store into a LangChain retriever

Used in: `ingestion.py`, `main.py`

---

### `langchain-community>=0.4.2`

LangChain's community-contributed integrations package. Provides the document loaders used in this project:
- `TextLoader` — loads `.txt` files as plain UTF-8 text
- `PyPDFLoader` — extracts text from `.pdf` files page by page
- `Docx2txtLoader` — extracts text from `.docx` Word documents

Used in: `ingestion.py`

---

### `langchain-text-splitters>=1.1.2`

LangChain's text splitting package. Provides `RecursiveCharacterTextSplitter`, which splits documents into chunks by trying progressively finer separators (`\n\n`, `\n`, `. `, ` `, characters) until chunks fit within `CHUNK_SIZE`.

Used in: `ingestion.py`

---

### `pypdf>=6.14.2`

The underlying PDF parsing library used by `PyPDFLoader`. Extracts text content from PDF files without requiring any external tools or system dependencies.

Used indirectly via: `langchain-community`

---

### `docx2txt>=0.8`

The underlying Word document parsing library used by `Docx2txtLoader`. Extracts plain text from `.docx` files by reading the XML structure inside the file.

Used indirectly via: `langchain-community`

---

### `chardet>=7.4.3`

Character encoding detection library. Used by `TextLoader` to detect the encoding of text files when `encoding="utf-8"` is not explicitly specified. Included as a safety dependency for edge cases with non-UTF-8 encoded files.

---

## Development Dependencies

### `black>=26.5.1`

An opinionated Python code formatter. Enforces a consistent code style across all files automatically. Run with:

```bash
black .
```

---

### `isort>=8.0.1`

A Python import sorter. Automatically organises import statements into sections (standard library, third-party, local) and sorts them alphabetically within each section. Run with:

```bash
isort .
```

---

### `dotenv>=0.9.9`

Loads environment variables from a `.env` file into `os.environ`. Included for future use if API keys or environment-specific configuration need to be managed without hardcoding them in source files.

---

## Dependency Graph

```
app.py
├── streamlit
├── langchain-chroma       → chromadb (transitive)
├── langchain-ollama       → ollama (transitive)
└── langchain              → langchain-core (transitive)

ingestion.py
├── langchain-chroma
├── langchain-community    → pypdf, docx2txt (transitive)
├── langchain-ollama
├── langchain-text-splitters
└── chardet

main.py
├── langchain-chroma
├── langchain-ollama
└── langchain
```
