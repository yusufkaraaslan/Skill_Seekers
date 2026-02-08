"""
Vector Database Tools for MCP Server.

Provides MCP tools for exporting skills to 4 vector databases:
- Weaviate (hybrid search, 450K+ users)
- Chroma (local-first, 800K+ developers)
- FAISS (billion-scale, GPU-accelerated)
- Qdrant (native filtering, 100K+ users)

Each tool provides a direct interface to its respective vector database adaptor.
"""

import sys
from pathlib import Path

try:
    from mcp.types import TextContent
except ImportError:
    # Graceful degradation for testing
    class TextContent:
        """Fallback TextContent for when MCP is not installed"""

        def __init__(self, type: str, text: str):
            self.type = type
            self.text = text


# Path to CLI adaptors
CLI_DIR = Path(__file__).parent.parent.parent / "cli"
sys.path.insert(0, str(CLI_DIR))

try:
    from adaptors import get_adaptor
except ImportError:
    get_adaptor = None  # Will handle gracefully below


async def export_to_weaviate_impl(args: dict) -> list[TextContent]:
    """
    Export skill to Weaviate vector database format.

    Weaviate is a popular cloud-native vector database with hybrid search
    (combining vector similarity + BM25 keyword search). Ideal for
    production RAG applications with 450K+ users.

    Args:
        args: Dictionary with:
            - skill_dir (str): Path to skill directory (e.g., output/react/)
            - output_dir (str, optional): Output directory (default: same as skill_dir)

    Returns:
        List of TextContent with export results

    Example:
        {
            "skill_dir": "output/react",
            "output_dir": "output"
        }

    Output Format:
        JSON file with Weaviate schema:
        - class_name: Weaviate class name
        - schema: Property definitions
        - objects: Document objects with vectors and metadata
        - config: Distance metric configuration
    """
    if get_adaptor is None:
        return [
            TextContent(
                type="text",
                text="❌ Error: Could not import adaptors module. Please ensure skill-seekers is properly installed.",
            )
        ]

    skill_dir = Path(args["skill_dir"])
    output_dir = Path(args.get("output_dir", skill_dir.parent))

    if not skill_dir.exists():
        return [
            TextContent(
                type="text",
                text=f"❌ Error: Skill directory not found: {skill_dir}\n\nPlease scrape documentation first using scrape_docs.",
            )
        ]

    try:
        # Get Weaviate adaptor
        adaptor = get_adaptor("weaviate")

        # Package skill
        package_path = adaptor.package(skill_dir, output_dir)

        # Success message
        result_text = f"""✅ Weaviate Export Complete!

📦 Package: {package_path.name}
📁 Location: {package_path.parent}
📊 Size: {package_path.stat().st_size:,} bytes

🔧 Next Steps:
1. Upload to Weaviate:
   ```python
   import weaviate
   import json

   client = weaviate.Client("http://localhost:8080")
   data = json.load(open("{package_path}"))

   # Create schema
   client.schema.create_class(data["schema"])

   # Batch upload objects
   with client.batch as batch:
       for obj in data["objects"]:
           batch.add_data_object(obj["properties"], data["class_name"])
   ```

2. Query with hybrid search:
   ```python
   result = client.query.get(data["class_name"], ["content", "source"]) \\
       .with_hybrid("React hooks usage") \\
       .with_limit(5) \\
       .do()
   ```

📚 Resources:
- Weaviate Docs: https://weaviate.io/developers/weaviate
- Hybrid Search: https://weaviate.io/developers/weaviate/search/hybrid
"""

        return [TextContent(type="text", text=result_text)]

    except Exception as e:
        return [
            TextContent(
                type="text",
                text=f"❌ Error exporting to Weaviate: {str(e)}\n\nPlease check that the skill directory contains valid documentation.",
            )
        ]


async def export_to_chroma_impl(args: dict) -> list[TextContent]:
    """
    Export skill to Chroma vector database format.

    Chroma is a popular open-source embedding database designed for
    local-first development. Perfect for RAG prototyping with 800K+ developers.

    Args:
        args: Dictionary with:
            - skill_dir (str): Path to skill directory (e.g., output/react/)
            - output_dir (str, optional): Output directory (default: same as skill_dir)

    Returns:
        List of TextContent with export results

    Example:
        {
            "skill_dir": "output/react",
            "output_dir": "output"
        }

    Output Format:
        JSON file with Chroma collection data:
        - collection_name: Collection identifier
        - documents: List of document texts
        - metadatas: List of metadata dicts
        - ids: List of unique IDs
    """
    if get_adaptor is None:
        return [
            TextContent(
                type="text",
                text="❌ Error: Could not import adaptors module.",
            )
        ]

    skill_dir = Path(args["skill_dir"])
    output_dir = Path(args.get("output_dir", skill_dir.parent))

    if not skill_dir.exists():
        return [
            TextContent(
                type="text",
                text=f"❌ Error: Skill directory not found: {skill_dir}",
            )
        ]

    try:
        adaptor = get_adaptor("chroma")
        package_path = adaptor.package(skill_dir, output_dir)

        result_text = f"""✅ Chroma Export Complete!

📦 Package: {package_path.name}
📁 Location: {package_path.parent}
📊 Size: {package_path.stat().st_size:,} bytes

🔧 Next Steps:
1. Load into Chroma:
   ```python
   import chromadb
   import json

   client = chromadb.Client()
   data = json.load(open("{package_path}"))

   # Create collection
   collection = client.create_collection(
       name=data["collection_name"],
       metadata={{"source": "skill-seekers"}}
   )

   # Add documents
   collection.add(
       documents=data["documents"],
       metadatas=data["metadatas"],
       ids=data["ids"]
   )
   ```

2. Query the collection:
   ```python
   results = collection.query(
       query_texts=["How to use React hooks?"],
       n_results=5
   )
   ```

📚 Resources:
- Chroma Docs: https://docs.trychroma.com/
- Getting Started: https://docs.trychroma.com/getting-started
"""

        return [TextContent(type="text", text=result_text)]

    except Exception as e:
        return [
            TextContent(
                type="text",
                text=f"❌ Error exporting to Chroma: {str(e)}",
            )
        ]


async def export_to_faiss_impl(args: dict) -> list[TextContent]:
    """
    Export skill to FAISS vector index format.

    FAISS (Facebook AI Similarity Search) is a library for efficient similarity
    search at billion-scale. Supports GPU acceleration for ultra-fast search.

    Args:
        args: Dictionary with:
            - skill_dir (str): Path to skill directory (e.g., output/react/)
            - output_dir (str, optional): Output directory (default: same as skill_dir)
            - index_type (str, optional): FAISS index type (default: 'Flat')
                                        Options: 'Flat', 'IVF', 'HNSW'

    Returns:
        List of TextContent with export results

    Example:
        {
            "skill_dir": "output/react",
            "output_dir": "output",
            "index_type": "HNSW"
        }

    Output Format:
        JSON file with FAISS data:
        - embeddings: List of embedding vectors
        - metadata: List of document metadata
        - index_config: FAISS index configuration
    """
    if get_adaptor is None:
        return [
            TextContent(
                type="text",
                text="❌ Error: Could not import adaptors module.",
            )
        ]

    skill_dir = Path(args["skill_dir"])
    output_dir = Path(args.get("output_dir", skill_dir.parent))

    if not skill_dir.exists():
        return [
            TextContent(
                type="text",
                text=f"❌ Error: Skill directory not found: {skill_dir}",
            )
        ]

    try:
        adaptor = get_adaptor("faiss")
        package_path = adaptor.package(skill_dir, output_dir)

        result_text = f"""✅ FAISS Export Complete!

📦 Package: {package_path.name}
📁 Location: {package_path.parent}
📊 Size: {package_path.stat().st_size:,} bytes

🔧 Next Steps:
1. Build FAISS index:
   ```python
   import faiss
   import json
   import numpy as np

   data = json.load(open("{package_path}"))
   embeddings = np.array(data["embeddings"], dtype="float32")

   # Create index (choose based on scale)
   dimension = embeddings.shape[1]

   # Option 1: Flat (exact search, small datasets)
   index = faiss.IndexFlatL2(dimension)

   # Option 2: IVF (fast approximation, medium datasets)
   # quantizer = faiss.IndexFlatL2(dimension)
   # index = faiss.IndexIVFFlat(quantizer, dimension, 100)
   # index.train(embeddings)

   # Option 3: HNSW (best quality approximation, large datasets)
   # index = faiss.IndexHNSWFlat(dimension, 32)

   # Add vectors
   index.add(embeddings)
   ```

2. Search:
   ```python
   # Search for similar docs
   query = np.array([your_query_embedding], dtype="float32")
   distances, indices = index.search(query, k=5)

   # Get metadata for results
   for i in indices[0]:
       print(data["metadata"][i])
   ```

3. Save index:
   ```python
   faiss.write_index(index, "react_docs.index")
   ```

📚 Resources:
- FAISS Wiki: https://github.com/facebookresearch/faiss/wiki
- GPU Support: https://github.com/facebookresearch/faiss/wiki/Faiss-on-the-GPU
"""

        return [TextContent(type="text", text=result_text)]

    except Exception as e:
        return [
            TextContent(
                type="text",
                text=f"❌ Error exporting to FAISS: {str(e)}",
            )
        ]


async def export_to_qdrant_impl(args: dict) -> list[TextContent]:
    """
    Export skill to Qdrant vector database format.

    Qdrant is a modern vector database with native payload filtering and
    high-performance search. Ideal for production RAG with 100K+ users.

    Args:
        args: Dictionary with:
            - skill_dir (str): Path to skill directory (e.g., output/react/)
            - output_dir (str, optional): Output directory (default: same as skill_dir)

    Returns:
        List of TextContent with export results

    Example:
        {
            "skill_dir": "output/react",
            "output_dir": "output"
        }

    Output Format:
        JSON file with Qdrant collection data:
        - collection_name: Collection identifier
        - points: List of points with id, vector, payload
        - config: Vector configuration
    """
    if get_adaptor is None:
        return [
            TextContent(
                type="text",
                text="❌ Error: Could not import adaptors module.",
            )
        ]

    skill_dir = Path(args["skill_dir"])
    output_dir = Path(args.get("output_dir", skill_dir.parent))

    if not skill_dir.exists():
        return [
            TextContent(
                type="text",
                text=f"❌ Error: Skill directory not found: {skill_dir}",
            )
        ]

    try:
        adaptor = get_adaptor("qdrant")
        package_path = adaptor.package(skill_dir, output_dir)

        result_text = f"""✅ Qdrant Export Complete!

📦 Package: {package_path.name}
📁 Location: {package_path.parent}
📊 Size: {package_path.stat().st_size:,} bytes

🔧 Next Steps:
1. Upload to Qdrant:
   ```python
   from qdrant_client import QdrantClient
   from qdrant_client.models import Distance, VectorParams
   import json

   client = QdrantClient("localhost", port=6333)
   data = json.load(open("{package_path}"))

   # Create collection
   client.create_collection(
       collection_name=data["collection_name"],
       vectors_config=VectorParams(
           size=data["config"]["vector_size"],
           distance=Distance.COSINE
       )
   )

   # Upload points
   client.upsert(
       collection_name=data["collection_name"],
       points=data["points"]
   )
   ```

2. Search with filters:
   ```python
   from qdrant_client.models import Filter, FieldCondition, MatchValue

   results = client.search(
       collection_name=data["collection_name"],
       query_vector=your_query_vector,
       query_filter=Filter(
           must=[
               FieldCondition(
                   key="category",
                   match=MatchValue(value="getting_started")
               )
           ]
       ),
       limit=5
   )
   ```

📚 Resources:
- Qdrant Docs: https://qdrant.tech/documentation/
- Filtering: https://qdrant.tech/documentation/concepts/filtering/
"""

        return [TextContent(type="text", text=result_text)]

    except Exception as e:
        return [
            TextContent(
                type="text",
                text=f"❌ Error exporting to Qdrant: {str(e)}",
            )
        ]


# Export all implementations
__all__ = [
    "export_to_weaviate_impl",
    "export_to_chroma_impl",
    "export_to_faiss_impl",
    "export_to_qdrant_impl",
]
