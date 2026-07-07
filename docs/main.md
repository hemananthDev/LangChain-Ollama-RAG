# `main.py` — Vector Store & Retrieval Chain

## Purpose

`main.py` owns the read path of the RAG system. It loads an existing Chroma vector store from disk and constructs the LangChain LCEL retrieval chain that powers question answering. It exposes two public functions: `load_vector_store` and `create_retrieval_chain`.

---

## Full File

```python
"""
Perform Retrieval-Augmented Generation (RAG) using
a Chroma vector database and Ollama.
"""

from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import ChatOllama, OllamaEmbeddings

from config import EMBEDDING_MODEL, LLM_MODEL, TOP_K, VECTOR_DB_ROOT


def load_vector_store(db_name):
    db_path = VECTOR_DB_ROOT / db_name

    if not db_path.exists():
        raise FileNotFoundError(
            f"Knowledge base '{db_name}' does not exist."
        )

    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

    return Chroma(
        persist_directory=str(db_path),
        embedding_function=embeddings,
    )


def format_docs(documents):
    return "\n\n".join(doc.page_content for doc in documents)


def create_retrieval_chain(vectorstore):
    retriever = vectorstore.as_retriever(
        search_kwargs={"k": TOP_K}
    )

    llm = ChatOllama(model=LLM_MODEL)

    prompt = ChatPromptTemplate.from_template(
        """
Answer the question using only the provided context.

If the answer cannot be found in the context,
respond that the information is not available.

Context:
{context}

Question:
{question}

Provide a detailed answer.
"""
    )

    chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain
```

---

## Line-by-Line Breakdown

### Imports

```python
from langchain_chroma import Chroma
```
Used to load an existing Chroma vector store from a persist directory. Unlike in `ingestion.py` where `Chroma.from_documents` creates a new store, here the `Chroma(...)` constructor is used to open an existing one.

```python
from langchain_core.output_parsers import StrOutputParser
```
The final step in the chain. Converts the LLM's response object (an `AIMessage`) into a plain Python string.

```python
from langchain_core.prompts import ChatPromptTemplate
```
Creates a reusable prompt template with named placeholders (`{context}`, `{question}`) that are filled at runtime.

```python
from langchain_core.runnables import RunnablePassthrough
```
A no-op runnable that passes its input through unchanged. Used to route the user's question directly to the prompt without modification.

```python
from langchain_ollama import ChatOllama, OllamaEmbeddings
```
- `ChatOllama` — the LangChain chat model interface for Ollama. Sends the filled prompt to the local LLM and returns a response.
- `OllamaEmbeddings` — used here to configure the embedding function for the vector store so it can embed queries at retrieval time.

```python
from config import EMBEDDING_MODEL, LLM_MODEL, TOP_K, VECTOR_DB_ROOT
```
All four constants this module needs, imported from the central config.

---

### `load_vector_store(db_name)`

```python
db_path = VECTOR_DB_ROOT / db_name
```
Constructs the full path to the knowledge base directory, e.g. `VectorDB/report Knowledge Base/`.

```python
if not db_path.exists():
    raise FileNotFoundError(
        f"Knowledge base '{db_name}' does not exist."
    )
```
Guards against trying to load a database that was deleted or never created. The error propagates to `app.py` where it is caught and shown to the user.

```python
embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
```
Creates the embedding client. This is passed to Chroma so that when a query comes in, Chroma knows how to embed it before performing the similarity search. The same model used during ingestion must be used here.

```python
return Chroma(
    persist_directory=str(db_path),
    embedding_function=embeddings,
)
```
Opens the existing Chroma database from disk. No re-embedding happens here — the stored vectors are loaded into memory. `persist_directory` must be a `str`, hence the conversion from `Path`.

---

### `format_docs(documents)`

```python
return "\n\n".join(doc.page_content for doc in documents)
```
Takes the list of `Document` objects returned by the retriever and joins their text content into a single string, separated by double newlines. This formatted string becomes the `{context}` value in the prompt.

Double newlines are used as separators so the LLM can visually distinguish between different retrieved chunks.

---

### `create_retrieval_chain(vectorstore)`

```python
retriever = vectorstore.as_retriever(
    search_kwargs={"k": TOP_K}
)
```
Creates a retriever from the vector store. `search_kwargs={"k": TOP_K}` configures it to return the `TOP_K` most similar chunks for any given query. The retriever performs cosine similarity search under the hood.

```python
llm = ChatOllama(model=LLM_MODEL)
```
Instantiates the local LLM. `ChatOllama` communicates with the Ollama server running on `localhost:11434`. No network call happens at this line — it just configures the client.

```python
prompt = ChatPromptTemplate.from_template("""
Answer the question using only the provided context.
...
Context:
{context}

Question:
{question}
...
""")
```
Defines the prompt template. The two placeholders `{context}` and `{question}` are filled at chain invocation time. Key design choices:
- "using only the provided context" — prevents hallucination from training data
- "respond that the information is not available" — provides a graceful fallback
- "Provide a detailed answer" — encourages thorough responses

```python
chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough(),
    }
    | prompt
    | llm
    | StrOutputParser()
)
```
Builds the LCEL chain using the `|` pipe operator. When `chain.invoke(question)` is called:

1. The input `question` string is fed into the dict simultaneously to both branches
2. Left branch: `retriever` fetches TOP_K chunks → `format_docs` joins them into a string → assigned to `"context"`
3. Right branch: `RunnablePassthrough()` passes the question through unchanged → assigned to `"question"`
4. The dict `{"context": "...", "question": "..."}` is passed to `prompt`, which fills the template
5. The filled prompt messages are passed to `llm`, which calls Ollama and returns an `AIMessage`
6. `StrOutputParser()` extracts the `.content` string from the `AIMessage`

```python
return chain
```
Returns the fully constructed chain. The chain is stateless — it can be called multiple times with different questions.
