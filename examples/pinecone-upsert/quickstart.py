#!/usr/bin/env python3
"""
Pinecone Upsert Quickstart

This example shows how to:
1. Load Skill Seekers documents (LangChain format)
2. Create embeddings with OpenAI
3. Upsert to Pinecone with metadata
4. Query with semantic search

Requirements:
    pip install pinecone-client openai

Environment:
    export PINECONE_API_KEY=your-pinecone-key
    export OPENAI_API_KEY=sk-...
"""

import json
import os
import time
from pathlib import Path
from typing import List, Dict

from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI


def create_index(pc: Pinecone, index_name: str, dimension: int = 1536) -> None:
    """
    Create Pinecone index if it doesn't exist.

    Args:
        pc: Pinecone client
        index_name: Name of the index
        dimension: Embedding dimension (1536 for OpenAI ada-002)
    """
    # Check if index exists
    if index_name not in pc.list_indexes().names():
        print(f"Creating index: {index_name}")
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
        # Wait for index to be ready
        while not pc.describe_index(index_name).status["ready"]:
            print("Waiting for index to be ready...")
            time.sleep(1)
        print(f"✅ Index created: {index_name}")
    else:
        print(f"ℹ️  Index already exists: {index_name}")


def load_documents(json_path: str) -> List[Dict]:
    """
    Load documents from Skill Seekers JSON output.

    Args:
        json_path: Path to skill-seekers generated JSON file

    Returns:
        List of document dictionaries
    """
    with open(json_path) as f:
        documents = json.load(f)

    print(f"✅ Loaded {len(documents)} documents")

    # Show category breakdown
    categories = {}
    for doc in documents:
        cat = doc["metadata"].get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1

    print(f"   Categories: {dict(sorted(categories.items()))}")

    return documents


def create_embeddings(openai_client: OpenAI, texts: List[str]) -> List[List[float]]:
    """
    Create embeddings for a list of texts.

    Args:
        openai_client: OpenAI client
        texts: List of texts to embed

    Returns:
        List of embedding vectors
    """
    response = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=texts
    )
    return [data.embedding for data in response.data]


def batch_upsert(
    index,
    openai_client: OpenAI,
    documents: List[Dict],
    batch_size: int = 100
) -> None:
    """
    Upsert documents to Pinecone in batches.

    Args:
        index: Pinecone index
        openai_client: OpenAI client
        documents: List of documents
        batch_size: Number of documents per batch
    """
    print(f"\nUpserting {len(documents)} documents...")
    print(f"Batch size: {batch_size}")

    vectors = []
    for i, doc in enumerate(documents):
        # Create embedding
        response = openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=doc["page_content"]
        )
        embedding = response.data[0].embedding

        # Prepare vector
        vectors.append({
            "id": f"doc_{i}",
            "values": embedding,
            "metadata": {
                "text": doc["page_content"][:1000],  # Store snippet
                "source": doc["metadata"]["source"],
                "category": doc["metadata"]["category"],
                "file": doc["metadata"]["file"],
                "type": doc["metadata"]["type"]
            }
        })

        # Batch upsert
        if len(vectors) >= batch_size:
            index.upsert(vectors=vectors)
            vectors = []
            print(f"  Upserted {i + 1}/{len(documents)} documents...")

    # Upsert remaining
    if vectors:
        index.upsert(vectors=vectors)

    print(f"✅ Upserted all documents to Pinecone")

    # Verify
    stats = index.describe_index_stats()
    print(f"   Total vectors in index: {stats['total_vector_count']}")


def semantic_search(
    index,
    openai_client: OpenAI,
    query: str,
    top_k: int = 5,
    category: str = None
) -> List[Dict]:
    """
    Perform semantic search.

    Args:
        index: Pinecone index
        openai_client: OpenAI client
        query: Search query
        top_k: Number of results
        category: Optional category filter

    Returns:
        List of matches
    """
    # Create query embedding
    response = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=query
    )
    query_embedding = response.data[0].embedding

    # Build filter
    filter_dict = None
    if category:
        filter_dict = {"category": {"$eq": category}}

    # Query
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
        filter=filter_dict
    )

    return results["matches"]


def interactive_search(index, openai_client: OpenAI) -> None:
    """
    Start an interactive search session.

    Args:
        index: Pinecone index
        openai_client: OpenAI client
    """
    print("\n" + "="*60)
    print("INTERACTIVE SEMANTIC SEARCH")
    print("="*60)
    print("Search the documentation (type 'quit' to exit)\n")

    while True:
        user_input = input("Query: ").strip()

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Goodbye!")
            break

        if not user_input:
            continue

        try:
            # Search
            start = time.time()
            matches = semantic_search(
                index=index,
                openai_client=openai_client,
                query=user_input,
                top_k=3
            )
            elapsed = time.time() - start

            # Display results
            print(f"\n🔍 Found {len(matches)} results ({elapsed*1000:.2f}ms)\n")

            for i, match in enumerate(matches, 1):
                print(f"Result {i}:")
                print(f"  Score: {match['score']:.3f}")
                print(f"  Category: {match['metadata']['category']}")
                print(f"  File: {match['metadata']['file']}")
                print(f"  Text: {match['metadata']['text'][:200]}...")
                print()

        except Exception as e:
            print(f"\n❌ Error: {e}\n")


def main():
    """
    Main execution flow.
    """
    print("="*60)
    print("PINECONE UPSERT QUICKSTART")
    print("="*60)
    print()

    # Configuration
    INDEX_NAME = "skill-seekers-demo"
    DOCS_PATH = "../../output/django-langchain.json"  # Adjust path as needed

    # Check API keys
    if not os.getenv("PINECONE_API_KEY"):
        print("❌ PINECONE_API_KEY not set")
        print("\nSet environment variable:")
        print("  export PINECONE_API_KEY=your-api-key")
        return

    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set")
        print("\nSet environment variable:")
        print("  export OPENAI_API_KEY=sk-...")
        return

    # Check if documents exist
    if not Path(DOCS_PATH).exists():
        print(f"❌ Documents not found at: {DOCS_PATH}")
        print("\nGenerate documents first:")
        print("  1. skill-seekers scrape --config configs/django.json")
        print("  2. skill-seekers package output/django --target langchain")
        print("\nOr adjust DOCS_PATH in the script to point to your documents.")
        return

    # Initialize clients
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    openai_client = OpenAI()

    # Step 1: Create index
    print("Step 1: Creating Pinecone index...")
    create_index(pc, INDEX_NAME)
    index = pc.Index(INDEX_NAME)
    print()

    # Step 2: Load documents
    print("Step 2: Loading documents...")
    documents = load_documents(DOCS_PATH)
    print()

    # Step 3: Upsert to Pinecone
    print("Step 3: Upserting to Pinecone...")
    batch_upsert(index, openai_client, documents, batch_size=100)
    print()

    # Step 4: Example queries
    print("Step 4: Running example queries...")
    print("="*60 + "\n")

    example_queries = [
        "How do I create a Django model?",
        "Explain Django views",
        "What is Django ORM?",
    ]

    for query in example_queries:
        print(f"QUERY: {query}")
        print("-" * 60)

        matches = semantic_search(
            index=index,
            openai_client=openai_client,
            query=query,
            top_k=3
        )

        for match in matches:
            print(f"  Score: {match['score']:.3f}")
            print(f"  Category: {match['metadata']['category']}")
            print(f"  Text: {match['metadata']['text'][:150]}...")
            print()

    # Step 5: Interactive search
    interactive_search(index, openai_client)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\nMake sure you have:")
        print("  1. Set PINECONE_API_KEY environment variable")
        print("  2. Set OPENAI_API_KEY environment variable")
        print("  3. Installed required packages:")
        print("     pip install pinecone-client openai")
