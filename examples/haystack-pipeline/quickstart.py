#!/usr/bin/env python3
"""
Haystack Pipeline Example

Demonstrates how to use Skill Seekers documentation with Haystack 2.x
for building RAG pipelines.
"""

import json
import sys
from pathlib import Path


def main():
    """Run Haystack pipeline example."""
    print("=" * 60)
    print("Haystack Pipeline Example")
    print("=" * 60)

    # Check if Haystack is installed
    try:
        from haystack import Document
        from haystack.document_stores.in_memory import InMemoryDocumentStore
        from haystack.components.retrievers.in_memory import InMemoryBM25Retriever
    except ImportError:
        print("❌ Error: Haystack not installed")
        print("   Install with: pip install haystack-ai")
        sys.exit(1)

    # Find the Haystack documents file
    docs_path = Path("../../output/react-haystack.json")

    if not docs_path.exists():
        print(f"❌ Error: Documents not found at {docs_path}")
        print("\n📝 Generate documents first:")
        print("   skill-seekers create --config configs/react.json --max-pages 100")
        print("   skill-seekers package output/react --target haystack")
        sys.exit(1)

    # Step 1: Load documents
    print("\n📚 Step 1: Loading documents...")
    with open(docs_path) as f:
        docs_data = json.load(f)

    documents = [
        Document(content=doc["content"], meta=doc["meta"]) for doc in docs_data
    ]

    print(f"✅ Loaded {len(documents)} documents")

    # Show document breakdown
    categories = {}
    for doc in documents:
        cat = doc.meta.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1

    print("\n📁 Categories:")
    for cat, count in sorted(categories.items()):
        print(f"   - {cat}: {count}")

    # Step 2: Create document store
    print("\n💾 Step 2: Creating document store...")
    document_store = InMemoryDocumentStore()
    document_store.write_documents(documents)

    indexed_count = document_store.count_documents()
    print(f"✅ Indexed {indexed_count} documents")

    # Step 3: Create retriever
    print("\n🔍 Step 3: Creating BM25 retriever...")
    retriever = InMemoryBM25Retriever(document_store=document_store)
    print("✅ Retriever ready")

    # Step 4: Query examples
    print("\n🎯 Step 4: Running queries...\n")

    queries = [
        "How do I use useState hook?",
        "What are React components?",
        "How to handle events in React?",
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n{'=' * 60}")
        print(f"Query {i}: {query}")
        print("=" * 60)

        # Run query
        results = retriever.run(query=query, top_k=3)

        if not results["documents"]:
            print("   No results found")
            continue

        # Display results
        for j, doc in enumerate(results["documents"], 1):
            print(f"\n📖 Result {j}:")
            print(f"   Source: {doc.meta.get('file', 'unknown')}")
            print(f"   Category: {doc.meta.get('category', 'unknown')}")

            # Show preview (first 200 chars)
            preview = doc.content[:200].replace("\n", " ")
            print(f"   Preview: {preview}...")

    # Summary
    print("\n" + "=" * 60)
    print("✅ Example complete!")
    print("=" * 60)
    print("\n📊 Summary:")
    print(f"   • Documents loaded: {len(documents)}")
    print(f"   • Documents indexed: {indexed_count}")
    print(f"   • Queries executed: {len(queries)}")
    print("\n💡 Next steps:")
    print("   • Try different queries")
    print("   • Experiment with top_k parameter")
    print("   • Build RAG pipeline with LLM generation")
    print("   • Use vector embeddings for semantic search")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
