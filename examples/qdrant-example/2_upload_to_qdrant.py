#!/usr/bin/env python3
"""Upload to Qdrant"""
import json, sys, argparse
from pathlib import Path

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
except ImportError:
    print("❌ Run: pip install qdrant-client")
    sys.exit(1)

parser = argparse.ArgumentParser()
parser.add_argument("--url", default="http://localhost:6333")
args = parser.parse_args()

print("=" * 60)
print("Step 2: Upload to Qdrant")
print("=" * 60)

# Connect
print(f"\n🔗 Connecting to Qdrant at {args.url}...")
client = QdrantClient(url=args.url)
print("✅ Connected!")

# Load data
with open("output/django-qdrant.json") as f:
    data = json.load(f)

collection_name = data["collection_name"]
config = data["config"]

print(f"\n📦 Creating collection: {collection_name}")

# Recreate collection if exists
try:
    client.delete_collection(collection_name)
except:
    pass

client.create_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(
        size=config["vector_size"],
        distance=Distance.COSINE
    )
)
print("✅ Collection created!")

# Upload points (without vectors for demo)
print(f"\n📤 Uploading {len(data['points'])} points...")
print("⚠️  Note: Vectors are None - you'll need to add embeddings for real use")

points = []
for point in data["points"]:
    # In production, add real vectors here
    points.append(PointStruct(
        id=point["id"],
        vector=[0.0] * config["vector_size"],  # Placeholder
        payload=point["payload"]
    ))

client.upsert(collection_name=collection_name, points=points)

info = client.get_collection(collection_name)
print(f"✅ Uploaded! Collection has {info.points_count} points")
print("\nNext: Add embeddings, then python 3_query_example.py")
