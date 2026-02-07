#!/usr/bin/env python3
"""
Step 3: Query ChromaDB

This script demonstrates various query patterns with ChromaDB:
1. Semantic search
2. Metadata filtering
3. Distance scoring
4. Top-K results

Usage:
    # In-memory (if you used in-memory upload)
    python 3_query_example.py

    # Persistent (if you used --persist for upload)
    python 3_query_example.py --persist ./chroma_db
"""

import argparse
import sys

try:
    import chromadb
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
except ImportError:
    print("❌ Missing dependencies!")
    print("Install with: pip install chromadb rich")
    sys.exit(1)

console = Console()

def create_client(persist_directory: str = None):
    """Create ChromaDB client."""
    try:
        if persist_directory:
            return chromadb.PersistentClient(path=persist_directory)
        else:
            return chromadb.Client()
    except Exception as e:
        console.print(f"[red]❌ Client creation failed: {e}[/red]")
        sys.exit(1)

def get_collection(client, collection_name: str = "vue"):
    """Get collection from ChromaDB."""
    try:
        return client.get_collection(collection_name)
    except Exception as e:
        console.print(f"[red]❌ Collection not found: {e}[/red]")
        console.print("\n[yellow]Did you run 2_upload_to_chroma.py first?[/yellow]")
        sys.exit(1)

def semantic_search_example(collection):
    """Example 1: Basic Semantic Search."""
    console.print("\n" + "=" * 60)
    console.print("[bold cyan]Example 1: Semantic Search[/bold cyan]")
    console.print("=" * 60)

    query = "How do I create a Vue component?"

    console.print(f"\n[yellow]Query:[/yellow] {query}")

    try:
        results = collection.query(
            query_texts=[query],
            n_results=3
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        if not documents:
            console.print("[red]No results found[/red]")
            return

        # Create results table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=3)
        table.add_column("Distance", style="cyan", width=10)
        table.add_column("Category", style="green")
        table.add_column("File", style="yellow")
        table.add_column("Preview", style="white")

        for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances), 1):
            preview = doc[:80] + "..." if len(doc) > 80 else doc
            table.add_row(
                str(i),
                f"{dist:.3f}",
                meta.get("category", "N/A"),
                meta.get("file", "N/A"),
                preview
            )

        console.print(table)

        # Explain distance scores
        console.print("\n[dim]💡 Distance: Lower = more similar (< 0.5 = very relevant)[/dim]")

    except Exception as e:
        console.print(f"[red]Query failed: {e}[/red]")

def filtered_search_example(collection):
    """Example 2: Search with Metadata Filter."""
    console.print("\n" + "=" * 60)
    console.print("[bold cyan]Example 2: Filtered Search[/bold cyan]")
    console.print("=" * 60)

    query = "reactivity"
    category_filter = "api"

    console.print(f"\n[yellow]Query:[/yellow] {query}")
    console.print(f"[yellow]Filter:[/yellow] category = '{category_filter}'")

    try:
        results = collection.query(
            query_texts=[query],
            n_results=5,
            where={"category": category_filter}
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        if not documents:
            console.print("[red]No results found[/red]")
            return

        console.print(f"\n[green]Found {len(documents)} results in '{category_filter}' category:[/green]\n")

        for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances), 1):
            panel = Panel(
                f"[cyan]File:[/cyan] {meta.get('file', 'N/A')}\n"
                f"[cyan]Distance:[/cyan] {dist:.3f}\n\n"
                f"[white]{doc[:200]}...[/white]",
                title=f"Result {i}",
                border_style="green"
            )
            console.print(panel)

    except Exception as e:
        console.print(f"[red]Query failed: {e}[/red]")

def top_k_results_example(collection):
    """Example 3: Get More Results (Top-K)."""
    console.print("\n" + "=" * 60)
    console.print("[bold cyan]Example 3: Top-K Results[/bold cyan]")
    console.print("=" * 60)

    query = "state management"

    console.print(f"\n[yellow]Query:[/yellow] {query}")
    console.print(f"[yellow]K:[/yellow] 10 (top 10 results)")

    try:
        results = collection.query(
            query_texts=[query],
            n_results=10
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        console.print(f"\n[green]Top 10 most relevant documents:[/green]\n")

        for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances), 1):
            category = meta.get("category", "N/A")
            file = meta.get("file", "N/A")
            console.print(f"[bold]{i:2d}.[/bold] [{dist:.3f}] {category:10s} | {file}")

    except Exception as e:
        console.print(f"[red]Query failed: {e}[/red]")

def complex_filter_example(collection):
    """Example 4: Complex Metadata Filtering."""
    console.print("\n" + "=" * 60)
    console.print("[bold cyan]Example 4: Complex Filter (AND condition)[/bold cyan]")
    console.print("=" * 60)

    query = "guide"

    console.print(f"\n[yellow]Query:[/yellow] {query}")
    console.print(f"[yellow]Filter:[/yellow] category = 'guides' AND type = 'reference'")

    try:
        results = collection.query(
            query_texts=[query],
            n_results=5,
            where={
                "$and": [
                    {"category": "guides"},
                    {"type": "reference"}
                ]
            }
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]

        if not documents:
            console.print("[red]No results match both conditions[/red]")
            return

        console.print(f"\n[green]Found {len(documents)} documents matching both conditions:[/green]\n")

        for i, (doc, meta) in enumerate(zip(documents, metadatas), 1):
            console.print(f"[bold]{i}. {meta.get('file', 'N/A')}[/bold]")
            console.print(f"   Category: {meta.get('category')} | Type: {meta.get('type')}")
            console.print(f"   {doc[:100]}...\n")

    except Exception as e:
        console.print(f"[red]Query failed: {e}[/red]")

def get_statistics(collection):
    """Show collection statistics."""
    console.print("\n" + "=" * 60)
    console.print("[bold cyan]Collection Statistics[/bold cyan]")
    console.print("=" * 60)

    try:
        # Total count
        count = collection.count()
        console.print(f"\n[green]Total documents:[/green] {count}")

        # Sample metadata to show categories
        sample = collection.get(limit=count)
        metadatas = sample["metadatas"]

        # Count by category
        categories = {}
        for meta in metadatas:
            cat = meta.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1

        console.print(f"\n[green]Documents by category:[/green]")
        for cat, cnt in sorted(categories.items()):
            console.print(f"  • {cat}: {cnt}")

    except Exception as e:
        console.print(f"[red]Statistics failed: {e}[/red]")

def main():
    parser = argparse.ArgumentParser(description="Query ChromaDB examples")
    parser.add_argument(
        "--persist",
        help="Persistent storage directory (if you used --persist for upload)"
    )
    parser.add_argument(
        "--collection",
        default="vue",
        help="Collection name to query (default: vue)"
    )

    args = parser.parse_args()

    console.print("[bold green]ChromaDB Query Examples[/bold green]")

    if args.persist:
        console.print(f"[dim]Using persistent storage: {args.persist}[/dim]")
    else:
        console.print("[dim]Using in-memory storage[/dim]")

    # Create client
    client = create_client(args.persist)

    # Get collection
    collection = get_collection(client, args.collection)

    # Get statistics
    get_statistics(collection)

    # Run examples
    semantic_search_example(collection)
    filtered_search_example(collection)
    top_k_results_example(collection)
    complex_filter_example(collection)

    console.print("\n[bold green]✅ All examples completed![/bold green]")
    console.print("\n[cyan]💡 Tips:[/cyan]")
    console.print("  • Lower distance = more similar (< 0.5 is very relevant)")
    console.print("  • Use 'where' filters to narrow results before search")
    console.print("  • Combine filters with $and, $or, $not operators")
    console.print("  • Adjust n_results to get more/fewer results")
    console.print("  • See README.md for custom embedding functions")

if __name__ == "__main__":
    main()
