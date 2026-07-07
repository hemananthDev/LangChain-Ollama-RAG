"""
Perform Retrieval-Augmented Generation (RAG) using
a Chroma vector database and Ollama.

This module is responsible only for:
1. Loading an existing Chroma vector database.
2. Creating the retrieval chain.
3. Running an interactive question-answer session.

The application entry point should be run.py.
"""

from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import ChatOllama, OllamaEmbeddings

from config import EMBEDDING_MODEL, LLM_MODEL, TOP_K, VECTOR_DB_ROOT


# =========================
# Vector Store
# =========================

def load_vector_store(db_name):
    """
    Load an existing Chroma vector database.

    Parameters
    ----------
    db_name : str
        Name of the vector database folder.

    Returns
    -------
    Chroma
        Loaded Chroma vector store.
    """

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


# =========================
# Retrieval Chain
# =========================

def format_docs(documents):
    """
    Combine retrieved documents into a single context string.
    """

    return "\n\n".join(doc.page_content for doc in documents)


def create_retrieval_chain(vectorstore):
    """
    Create the RAG retrieval chain.
    """

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


# =========================
# Interactive Q&A
# =========================

def ask_questions(db_name):
    """
    Start an interactive question-answer session.

    Parameters
    ----------
    db_name : str
        Name of the knowledge base.

    Commands
    --------
    back
        Return to the main menu.

    exit
        Exit the application.
    """

    vectorstore = load_vector_store(db_name)

    chain = create_retrieval_chain(vectorstore)

    print("\n===================================")
    print(f"Loaded Knowledge Base: {db_name}")
    print("===================================")

    while True:

        question = input(
            "\nQuestion ('back' to menu, 'exit' to quit): "
        ).strip()

        if not question:
            continue

        command = question.lower()

        if command == "back":
            break

        if command == "exit":
            raise SystemExit

        try:
            answer = chain.invoke(question)

            print("\nAnswer:\n")
            print(answer)

        except Exception as e:
            print(f"\nError: {e}")
