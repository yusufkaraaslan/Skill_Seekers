#!/usr/bin/env python3
"""Query FAISS index"""
import json, sys, os
import numpy as np

try:
    import faiss
    from openai import OpenAI
    from rich.console import Console
    from rich.table import Table
except ImportError:
    print("❌ Run: pip install -r requirements.txt")
    sys.exit(1)

console = Console()

# Load index and metadata
console.print("📥 Loading FAISS index...")
index = faiss.read_index("flask.index")

with open("flask_metadata.json") as f:
    data = json.load(f)

console.print(f"✅ Loaded {index.ntotal} vectors")

# Initialize OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def search(query_text: str, k: int = 5):
    """Search FAISS index"""
    console.print(f"\n[yellow]Query:[/yellow] {query_text}")

    # Generate query embedding
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=query_text
    )
    query_vector = np.array([response.data[0].embedding]).astype('float32')

    # Search
    distances, indices = index.search(query_vector, k)

    # Display results
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", width=3)
    table.add_column("Distance", width=10)
    table.add_column("Category", width=12)
    table.add_column("Content Preview")

    for i, (dist, idx) in enumerate(zip(distances[0], indices[0]), 1):
        doc = data["documents"][idx]
        meta = data["metadatas"][idx]
        preview = doc[:80] + "..." if len(doc) > 80 else doc

        table.add_row(
            str(i),
            f"{dist:.2f}",
            meta.get("category", "N/A"),
            preview
        )

    console.print(table)
    console.print("[dim]💡 Distance: Lower = more similar[/dim]")

# Example queries
console.print("[bold green]FAISS Query Examples[/bold green]\n")

search("How do I create a Flask route?", k=3)
search("database models and ORM", k=3)
search("authentication and security", k=3)

console.print("\n✅ All examples completed!")
