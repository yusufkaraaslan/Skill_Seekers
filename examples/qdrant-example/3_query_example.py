#!/usr/bin/env python3
"""Query Qdrant (demonstrates filtering without vectors)"""
import argparse

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    from rich.console import Console
    from rich.table import Table
except ImportError:
    print("❌ Run: pip install qdrant-client rich")
    exit(1)

console = Console()

parser = argparse.ArgumentParser()
parser.add_argument("--url", default="http://localhost:6333")
args = parser.parse_args()

console.print("[bold green]Qdrant Query Examples[/bold green]")
console.print(f"[dim]Connected to: {args.url}[/dim]\n")

# Connect
client = QdrantClient(url=args.url)
collection_name = "django"

# Example 1: Scroll (get all) with filter
console.print("[bold cyan]Example 1: Filter by Category[/bold cyan]\n")

result = client.scroll(
    collection_name=collection_name,
    scroll_filter=Filter(
        must=[
            FieldCondition(
                key="category",
                match=MatchValue(value="api")
            )
        ]
    ),
    limit=5
)

points = result[0]
table = Table(show_header=True, header_style="bold magenta")
table.add_column("ID")
table.add_column("Category")
table.add_column("File")
table.add_column("Content Preview")

for point in points:
    preview = point.payload["content"][:60] + "..."
    table.add_row(
        str(point.id)[:8] + "...",
        point.payload["category"],
        point.payload["file"],
        preview
    )

console.print(table)

# Example 2: Complex filter (AND condition)
console.print("\n[bold cyan]Example 2: Complex Filter (AND)[/bold cyan]\n")

result = client.scroll(
    collection_name=collection_name,
    scroll_filter=Filter(
        must=[
            FieldCondition(key="category", match=MatchValue(value="guides")),
            FieldCondition(key="type", match=MatchValue(value="reference"))
        ]
    ),
    limit=3
)

console.print(f"[green]Found {len(result[0])} points matching both conditions:[/green]\n")

for i, point in enumerate(result[0], 1):
    console.print(f"[bold]{i}. {point.payload['file']}[/bold]")
    console.print(f"   {point.payload['content'][:100]}...\n")

console.print("✅ Query examples completed!")
console.print("\n[yellow]💡 Note:[/yellow] For vector search, add embeddings to points!")
