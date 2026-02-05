#!/usr/bin/env python3
"""
LlamaIndex Query Engine Quickstart

This example shows how to:
1. Load Skill Seekers nodes
2. Create a VectorStoreIndex
3. Build a query engine
4. Query the documentation with chat mode

Requirements:
    pip install llama-index llama-index-llms-openai llama-index-embeddings-openai

Environment:
    export OPENAI_API_KEY=sk-...
"""

import json
from pathlib import Path

from llama_index.core.schema import TextNode
from llama_index.core import VectorStoreIndex, StorageContext


def load_nodes(json_path: str) -> list[TextNode]:
    """
    Load TextNodes from Skill Seekers JSON output.

    Args:
        json_path: Path to skill-seekers generated JSON file

    Returns:
        List of LlamaIndex TextNode objects
    """
    with open(json_path) as f:
        nodes_data = json.load(f)

    nodes = [
        TextNode(
            text=node["text"],
            metadata=node["metadata"],
            id_=node["id_"]
        )
        for node in nodes_data
    ]

    print(f"✅ Loaded {len(nodes)} nodes")

    # Show category breakdown
    categories = {}
    for node in nodes:
        cat = node.metadata.get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1

    print(f"   Categories: {dict(sorted(categories.items()))}")

    return nodes


def create_index(nodes: list[TextNode], persist_dir: str = "./storage") -> VectorStoreIndex:
    """
    Create a VectorStoreIndex from nodes.

    Args:
        nodes: List of TextNode objects
        persist_dir: Directory to persist the index

    Returns:
        VectorStoreIndex instance
    """
    # Create index
    index = VectorStoreIndex(nodes)

    # Persist to disk
    index.storage_context.persist(persist_dir=persist_dir)

    print(f"✅ Index created and persisted to: {persist_dir}")
    print(f"   Nodes indexed: {len(nodes)}")

    return index


def query_examples(index: VectorStoreIndex) -> None:
    """
    Run example queries to demonstrate functionality.

    Args:
        index: VectorStoreIndex instance
    """
    print("\n" + "="*60)
    print("EXAMPLE QUERIES")
    print("="*60 + "\n")

    # Create query engine
    query_engine = index.as_query_engine(
        similarity_top_k=3,
        response_mode="compact"
    )

    example_queries = [
        "What is this documentation about?",
        "How do I get started?",
        "Show me some code examples",
    ]

    for query in example_queries:
        print(f"QUERY: {query}")
        print("-" * 60)

        response = query_engine.query(query)
        print(f"ANSWER:\n{response}\n")

        print("SOURCES:")
        for i, node in enumerate(response.source_nodes, 1):
            cat = node.metadata.get('category', 'unknown')
            file_name = node.metadata.get('file', 'unknown')
            score = node.score if hasattr(node, 'score') else 'N/A'
            print(f"  {i}. {cat} ({file_name}) - Score: {score}")
        print("\n")


def interactive_chat(index: VectorStoreIndex) -> None:
    """
    Start an interactive chat session.

    Args:
        index: VectorStoreIndex instance
    """
    print("="*60)
    print("INTERACTIVE CHAT MODE")
    print("="*60)
    print("Ask questions about the documentation (type 'quit' to exit)\n")

    # Create chat engine with memory
    chat_engine = index.as_chat_engine(
        chat_mode="condense_question",
        verbose=False
    )

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Goodbye!")
            break

        if not user_input:
            continue

        try:
            response = chat_engine.chat(user_input)
            print(f"\nAssistant: {response}\n")

            # Show sources
            if hasattr(response, 'source_nodes') and response.source_nodes:
                print("Sources:")
                for node in response.source_nodes[:3]:  # Show top 3
                    cat = node.metadata.get('category', 'unknown')
                    file_name = node.metadata.get('file', 'unknown')
                    print(f"  - {cat} ({file_name})")
                print()

        except Exception as e:
            print(f"\n❌ Error: {e}\n")


def main():
    """
    Main execution flow.
    """
    print("="*60)
    print("LLAMAINDEX QUERY ENGINE QUICKSTART")
    print("="*60)
    print()

    # Configuration
    DOCS_PATH = "../../output/django-llama-index.json"  # Adjust path as needed
    STORAGE_DIR = "./storage"

    # Check if documents exist
    if not Path(DOCS_PATH).exists():
        print(f"❌ Documents not found at: {DOCS_PATH}")
        print("\nGenerate documents first:")
        print("  1. skill-seekers scrape --config configs/django.json")
        print("  2. skill-seekers package output/django --target llama-index")
        print("\nOr adjust DOCS_PATH in the script to point to your documents.")
        return

    # Step 1: Load nodes
    print("Step 1: Loading nodes...")
    nodes = load_nodes(DOCS_PATH)
    print()

    # Step 2: Create index
    print("Step 2: Creating index...")
    index = create_index(nodes, STORAGE_DIR)
    print()

    # Step 3: Run example queries
    print("Step 3: Running example queries...")
    query_examples(index)

    # Step 4: Interactive chat
    interactive_chat(index)


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
        print("  1. Set OPENAI_API_KEY environment variable")
        print("  2. Installed required packages:")
        print("     pip install llama-index llama-index-llms-openai llama-index-embeddings-openai")
