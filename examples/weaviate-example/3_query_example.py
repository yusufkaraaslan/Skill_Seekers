#!/usr/bin/env python3
"""
Step 3: Query Weaviate

This script demonstrates various query patterns with Weaviate:
1. Hybrid search (keyword + vector)
2. Metadata filtering
3. Limit and pagination

Usage:
    # Local Docker
    python 3_query_example.py

    # Weaviate Cloud
    python 3_query_example.py --url https://your-cluster.weaviate.network --api-key YOUR_KEY
"""

import argparse
import sys

try:
    import weaviate
    from weaviate.auth import AuthApiKey
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
except ImportError:
    print("❌ Missing dependencies!")
    print("Install with: pip install weaviate-client rich")
    sys.exit(1)

console = Console()

def connect_to_weaviate(url: str, api_key: str = None):
    """Connect to Weaviate instance."""
    try:
        if api_key:
            auth_config = AuthApiKey(api_key)
            client = weaviate.Client(url=url, auth_client_secret=auth_config)
        else:
            client = weaviate.Client(url=url)

        if client.is_ready():
            return client
        else:
            console.print("[red]❌ Weaviate is not ready[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]❌ Connection failed: {e}[/red]")
        sys.exit(1)

def hybrid_search_example(client, class_name: str = "React"):
    """Example 1: Hybrid Search (keyword + vector)."""
    console.print("\n" + "=" * 60)
    console.print("[bold cyan]Example 1: Hybrid Search[/bold cyan]")
    console.print("=" * 60)

    query = "How do I use React hooks?"
    alpha = 0.5  # 50% keyword, 50% vector

    console.print(f"\n[yellow]Query:[/yellow] {query}")
    console.print(f"[yellow]Alpha:[/yellow] {alpha} (0=keyword only, 1=vector only)")

    try:
        result = (
            client.query.get(class_name, ["content", "source", "category", "file"])
            .with_hybrid(query=query, alpha=alpha)
            .with_limit(3)
            .do()
        )

        objects = result["data"]["Get"][class_name]

        if not objects:
            console.print("[red]No results found[/red]")
            return

        # Create results table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=3)
        table.add_column("Category", style="cyan")
        table.add_column("File", style="green")
        table.add_column("Content Preview", style="white")

        for i, obj in enumerate(objects, 1):
            content_preview = obj["content"][:100] + "..." if len(obj["content"]) > 100 else obj["content"]
            table.add_row(
                str(i),
                obj["category"],
                obj["file"],
                content_preview
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Query failed: {e}[/red]")

def keyword_only_search(client, class_name: str = "React"):
    """Example 2: Keyword-Only Search (alpha=0)."""
    console.print("\n" + "=" * 60)
    console.print("[bold cyan]Example 2: Keyword-Only Search[/bold cyan]")
    console.print("=" * 60)

    query = "useState Hook"
    alpha = 0  # Pure keyword search

    console.print(f"\n[yellow]Query:[/yellow] {query}")
    console.print(f"[yellow]Alpha:[/yellow] {alpha} (pure keyword/BM25)")

    try:
        result = (
            client.query.get(class_name, ["content", "category", "file"])
            .with_hybrid(query=query, alpha=alpha)
            .with_limit(3)
            .do()
        )

        objects = result["data"]["Get"][class_name]

        for i, obj in enumerate(objects, 1):
            panel = Panel(
                f"[cyan]Category:[/cyan] {obj['category']}\n"
                f"[cyan]File:[/cyan] {obj['file']}\n\n"
                f"[white]{obj['content'][:200]}...[/white]",
                title=f"Result {i}",
                border_style="green"
            )
            console.print(panel)

    except Exception as e:
        console.print(f"[red]Query failed: {e}[/red]")

def filtered_search(client, class_name: str = "React"):
    """Example 3: Search with Metadata Filter."""
    console.print("\n" + "=" * 60)
    console.print("[bold cyan]Example 3: Filtered Search[/bold cyan]")
    console.print("=" * 60)

    query = "component"
    category_filter = "api"

    console.print(f"\n[yellow]Query:[/yellow] {query}")
    console.print(f"[yellow]Filter:[/yellow] category = '{category_filter}'")

    try:
        result = (
            client.query.get(class_name, ["content", "category", "file"])
            .with_hybrid(query=query, alpha=0.5)
            .with_where({
                "path": ["category"],
                "operator": "Equal",
                "valueText": category_filter
            })
            .with_limit(5)
            .do()
        )

        objects = result["data"]["Get"][class_name]

        if not objects:
            console.print("[red]No results found[/red]")
            return

        console.print(f"\n[green]Found {len(objects)} results in '{category_filter}' category:[/green]\n")

        for i, obj in enumerate(objects, 1):
            console.print(f"[bold]{i}. {obj['file']}[/bold]")
            console.print(f"   {obj['content'][:150]}...\n")

    except Exception as e:
        console.print(f"[red]Query failed: {e}[/red]")

def semantic_search(client, class_name: str = "React"):
    """Example 4: Pure Semantic Search (alpha=1)."""
    console.print("\n" + "=" * 60)
    console.print("[bold cyan]Example 4: Semantic Search[/bold cyan]")
    console.print("=" * 60)

    query = "managing application state"  # Conceptual query
    alpha = 1  # Pure vector/semantic search

    console.print(f"\n[yellow]Query:[/yellow] {query}")
    console.print(f"[yellow]Alpha:[/yellow] {alpha} (pure semantic/vector)")

    try:
        result = (
            client.query.get(class_name, ["content", "category", "file"])
            .with_hybrid(query=query, alpha=alpha)
            .with_limit(3)
            .do()
        )

        objects = result["data"]["Get"][class_name]

        for i, obj in enumerate(objects, 1):
            console.print(f"\n[bold green]Result {i}:[/bold green]")
            console.print(f"[cyan]Category:[/cyan] {obj['category']}")
            console.print(f"[cyan]File:[/cyan] {obj['file']}")
            console.print(f"[white]{obj['content'][:200]}...[/white]")

    except Exception as e:
        console.print(f"[red]Query failed: {e}[/red]")

def get_statistics(client, class_name: str = "React"):
    """Show database statistics."""
    console.print("\n" + "=" * 60)
    console.print("[bold cyan]Database Statistics[/bold cyan]")
    console.print("=" * 60)

    try:
        # Total count
        result = client.query.aggregate(class_name).with_meta_count().do()
        total_count = result["data"]["Aggregate"][class_name][0]["meta"]["count"]

        console.print(f"\n[green]Total objects:[/green] {total_count}")

        # Count by category
        result = (
            client.query.aggregate(class_name)
            .with_group_by_filter(["category"])
            .with_meta_count()
            .do()
        )

        groups = result["data"]["Aggregate"][class_name]

        console.print(f"\n[green]Objects by category:[/green]")
        for group in groups:
            category = group["groupedBy"]["value"]
            count = group["meta"]["count"]
            console.print(f"  • {category}: {count}")

    except Exception as e:
        console.print(f"[red]Statistics failed: {e}[/red]")

def main():
    parser = argparse.ArgumentParser(description="Query Weaviate examples")
    parser.add_argument(
        "--url",
        default="http://localhost:8080",
        help="Weaviate URL (default: http://localhost:8080)"
    )
    parser.add_argument(
        "--api-key",
        help="Weaviate API key (for cloud instances)"
    )
    parser.add_argument(
        "--class",
        dest="class_name",
        default="React",
        help="Class name to query (default: React)"
    )

    args = parser.parse_args()

    console.print("[bold green]Weaviate Query Examples[/bold green]")
    console.print(f"[dim]Connected to: {args.url}[/dim]")

    # Connect
    client = connect_to_weaviate(args.url, args.api_key)

    # Get statistics
    get_statistics(client, args.class_name)

    # Run examples
    hybrid_search_example(client, args.class_name)
    keyword_only_search(client, args.class_name)
    filtered_search(client, args.class_name)
    semantic_search(client, args.class_name)

    console.print("\n[bold green]✅ All examples completed![/bold green]")
    console.print("\n[cyan]💡 Tips:[/cyan]")
    console.print("  • Adjust 'alpha' to balance keyword vs semantic search")
    console.print("  • Use filters to narrow results by metadata")
    console.print("  • Combine multiple filters with 'And'/'Or' operators")
    console.print("  • See README.md for more customization options")

if __name__ == "__main__":
    main()
