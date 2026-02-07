#!/usr/bin/env python3
"""
Step 2: Upload to Weaviate

This script:
1. Connects to Weaviate instance (local or cloud)
2. Creates the schema (class + properties)
3. Batch uploads all objects
4. Verifies the upload

Usage:
    # Local Docker
    python 2_upload_to_weaviate.py

    # Weaviate Cloud
    python 2_upload_to_weaviate.py --url https://your-cluster.weaviate.network --api-key YOUR_KEY

    # Reset existing data
    python 2_upload_to_weaviate.py --reset
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import weaviate
    from weaviate.auth import AuthApiKey
except ImportError:
    print("❌ weaviate-client not installed!")
    print("Install it with: pip install weaviate-client")
    sys.exit(1)

def connect_to_weaviate(url: str, api_key: str = None):
    """Connect to Weaviate instance."""
    print(f"\n🔗 Connecting to Weaviate at {url}...")

    try:
        if api_key:
            # Weaviate Cloud with authentication
            auth_config = AuthApiKey(api_key)
            client = weaviate.Client(
                url=url,
                auth_client_secret=auth_config
            )
        else:
            # Local Docker without authentication
            client = weaviate.Client(url=url)

        # Check if ready
        if client.is_ready():
            print("✅ Weaviate is ready!\n")
            return client
        else:
            print("❌ Weaviate is not ready")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 Tips:")
        print("  - For local: Ensure Docker is running (docker ps | grep weaviate)")
        print("  - For cloud: Check your URL and API key")
        sys.exit(1)

def load_skill_data(filepath: str = "output/react-weaviate.json"):
    """Load the Weaviate-format skill JSON."""
    path = Path(filepath)

    if not path.exists():
        print(f"❌ Skill file not found: {filepath}")
        print("Run '1_generate_skill.py' first!")
        sys.exit(1)

    with open(path) as f:
        return json.load(f)

def create_schema(client, schema: dict):
    """Create Weaviate schema (class + properties)."""
    class_name = schema["class"]

    print(f"📊 Creating schema: {class_name}")

    # Check if class already exists
    existing_schema = client.schema.get()
    class_exists = any(c["class"] == class_name for c in existing_schema.get("classes", []))

    if class_exists:
        print(f"⚠️  Class '{class_name}' already exists")
        response = input("Delete and recreate? [y/N]: ")
        if response.lower() == "y":
            client.schema.delete_class(class_name)
            print(f"🗑️  Deleted existing class")
        else:
            print("Skipping schema creation")
            return

    # Create the class
    client.schema.create_class(schema)
    print("✅ Schema created successfully!\n")

def upload_objects(client, class_name: str, objects: list):
    """Batch upload objects to Weaviate."""
    total = len(objects)
    batch_size = 100

    print(f"📤 Uploading {total} objects in batches...")

    with client.batch as batch:
        batch.batch_size = batch_size

        for i, obj in enumerate(objects):
            # Add object to batch
            batch.add_data_object(
                data_object=obj["properties"],
                class_name=class_name,
                uuid=obj["id"]
            )

            # Print progress
            if (i + 1) % batch_size == 0:
                batch_num = (i + 1) // batch_size
                print(f"✅ Batch {batch_num} uploaded ({i + 1}/{total} objects)")

    # Final batch
    final_count = total % batch_size
    if final_count > 0:
        batch_num = (total // batch_size) + 1
        print(f"✅ Batch {batch_num} uploaded ({final_count} objects)")

    print(f"\n✅ Successfully uploaded {total} documents to Weaviate")

def verify_upload(client, class_name: str):
    """Verify objects were uploaded correctly."""
    result = client.query.aggregate(class_name).with_meta_count().do()
    count = result["data"]["Aggregate"][class_name][0]["meta"]["count"]
    print(f"🔍 Class '{class_name}' now contains {count} objects")

def main():
    parser = argparse.ArgumentParser(description="Upload skill to Weaviate")
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
        "--file",
        default="output/react-weaviate.json",
        help="Path to Weaviate JSON file"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing class before uploading"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Step 2: Upload to Weaviate")
    print("=" * 60)

    # Connect to Weaviate
    client = connect_to_weaviate(args.url, args.api_key)

    # Load skill data
    data = load_skill_data(args.file)

    # Create schema
    create_schema(client, data["schema"])

    # Upload objects
    upload_objects(client, data["class_name"], data["objects"])

    # Verify
    verify_upload(client, data["class_name"])

    print("\n✅ Upload complete! Next step: python 3_query_example.py")

if __name__ == "__main__":
    main()
