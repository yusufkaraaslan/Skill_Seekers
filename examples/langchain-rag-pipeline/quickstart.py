#!/usr/bin/env python3
"""
LangChain RAG Pipeline Quickstart

This example shows how to:
1. Load Skill Seekers documents
2. Create a Chroma vector store
3. Build a RAG query engine
4. Query the documentation

Requirements:
    pip install langchain langchain-community langchain-openai chromadb openai

Environment:
    export OPENAI_API_KEY=sk-...
"""

import json
from pathlib import Path

from langchain.schema import Document
from langchain.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA


def load_documents(json_path: str) -> list[Document]:
    """
    Load LangChain Documents from Skill Seekers JSON output.

    Args:
        json_path: Path to skill-seekers generated JSON file

    Returns:
        List of LangChain Document objects
    """
    with open(json_path) as f:
        docs_data = json.load(f)

    documents = [
        Document(
            page_content=doc["page_content"],
            metadata=doc["metadata"]
        )
        for doc in docs_data
    ]

    print(f"✅ Loaded {len(documents)} documents")
    print(f"   Categories: {set(doc.metadata['category'] for doc in documents)}")

    return documents


def create_vector_store(documents: list[Document], persist_dir: str = "./chroma_db") -> Chroma:
    """
    Create a persistent Chroma vector store.

    Args:
        documents: List of LangChain Documents
        persist_dir: Directory to persist the vector store

    Returns:
        Chroma vector store instance
    """
    embeddings = OpenAIEmbeddings()

    vectorstore = Chroma.from_documents(
        documents,
        embeddings,
        persist_directory=persist_dir
    )

    print(f"✅ Vector store created at: {persist_dir}")
    print(f"   Documents indexed: {len(documents)}")

    return vectorstore


def create_qa_chain(vectorstore: Chroma) -> RetrievalQA:
    """
    Create a RAG question-answering chain.

    Args:
        vectorstore: Chroma vector store

    Returns:
        RetrievalQA chain
    """
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3}  # Return top 3 most relevant docs
    )

    llm = ChatOpenAI(model_name="gpt-4", temperature=0)

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )

    print("✅ QA chain created")

    return qa_chain


def query_documentation(qa_chain: RetrievalQA, query: str) -> None:
    """
    Query the documentation and print results.

    Args:
        qa_chain: RetrievalQA chain
        query: Question to ask
    """
    print(f"\n{'='*60}")
    print(f"QUERY: {query}")
    print(f"{'='*60}\n")

    result = qa_chain({"query": query})

    print(f"ANSWER:\n{result['result']}\n")

    print("SOURCES:")
    for i, doc in enumerate(result['source_documents'], 1):
        category = doc.metadata.get('category', 'unknown')
        file_name = doc.metadata.get('file', 'unknown')
        print(f"  {i}. {category} ({file_name})")
        print(f"     Preview: {doc.page_content[:100]}...\n")


def main():
    """
    Main execution flow.
    """
    print("="*60)
    print("LANGCHAIN RAG PIPELINE QUICKSTART")
    print("="*60)
    print()

    # Configuration
    DOCS_PATH = "../../output/react-langchain.json"  # Adjust path as needed
    CHROMA_DIR = "./chroma_db"

    # Check if documents exist
    if not Path(DOCS_PATH).exists():
        print(f"❌ Documents not found at: {DOCS_PATH}")
        print("\nGenerate documents first:")
        print("  1. skill-seekers scrape --config configs/react.json")
        print("  2. skill-seekers package output/react --target langchain")
        return

    # Step 1: Load documents
    print("Step 1: Loading documents...")
    documents = load_documents(DOCS_PATH)
    print()

    # Step 2: Create vector store
    print("Step 2: Creating vector store...")
    vectorstore = create_vector_store(documents, CHROMA_DIR)
    print()

    # Step 3: Create QA chain
    print("Step 3: Creating QA chain...")
    qa_chain = create_qa_chain(vectorstore)
    print()

    # Step 4: Query examples
    print("Step 4: Running example queries...")

    example_queries = [
        "How do I use React hooks?",
        "What is the difference between useState and useEffect?",
        "How do I handle forms in React?",
    ]

    for query in example_queries:
        query_documentation(qa_chain, query)

    # Interactive mode
    print("\n" + "="*60)
    print("INTERACTIVE MODE")
    print("="*60)
    print("Enter your questions (type 'quit' to exit)\n")

    while True:
        user_query = input("You: ").strip()

        if user_query.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Goodbye!")
            break

        if not user_query:
            continue

        query_documentation(qa_chain, user_query)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have:")
        print("  1. Set OPENAI_API_KEY environment variable")
        print("  2. Installed required packages:")
        print("     pip install langchain langchain-community langchain-openai chromadb openai")
