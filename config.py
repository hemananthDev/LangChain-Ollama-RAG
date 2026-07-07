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
