"""
Ingest a document into a Chroma vector database.

This module is responsible only for:
1. Loading a document.
2. Splitting it into chunks.
3. Creating embeddings.
4. Persisting a Chroma vector database.

The application entry point should be run.py.
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


# =========================
# Document Loading
# =========================

def load_documents(file_path):
    """
    Load a document based on its file extension.
    """

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


# =========================
# Chunking
# =========================

def split_documents(documents):
    """
    Split documents into smaller chunks.
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    return splitter.split_documents(documents)


# =========================
# Vector Store
# =========================

def create_vector_store(documents, persist_directory):
    """
    Create and persist a Chroma vector database.
    """

    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

    Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=str(persist_directory),
    )


# =========================
# Public API
# =========================

def ingest_document(file_path):
    """
    Ingest a document into a Chroma vector database.

    Parameters
    ----------
    file_path : str
        Path to the source document.

    Returns
    -------
    str
        Name of the created knowledge base.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.

    ValueError
        If the file type is unsupported.
    """

    file_path = Path(file_path).expanduser()

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    VECTOR_DB_ROOT.mkdir(exist_ok=True)

    db_name = f"{file_path.stem} Knowledge Base"
    vector_db_path = VECTOR_DB_ROOT / db_name

    documents = load_documents(str(file_path))
    chunks = split_documents(documents)

    create_vector_store(
        chunks,
        vector_db_path,
    )

    return db_name
