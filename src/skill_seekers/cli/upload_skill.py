#!/usr/bin/env python3
"""
Automatic Skill Uploader
Uploads a skill package to LLM platforms (Claude, Gemini, OpenAI, etc.)

Usage:
    # Claude (default)
    export ANTHROPIC_API_KEY=sk-ant-...
    skill-seekers upload output/react.zip

    # Gemini
    export GOOGLE_API_KEY=AIzaSy...
    skill-seekers upload output/react-gemini.tar.gz --target gemini

    # OpenAI
    export OPENAI_API_KEY=sk-proj-...
    skill-seekers upload output/react-openai.zip --target openai
"""

import argparse
import os
import sys
from pathlib import Path

# Import utilities
try:
    from utils import print_upload_instructions
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from utils import print_upload_instructions


def upload_skill_api(package_path, target="claude", api_key=None, **kwargs):
    """
    Upload skill package to LLM platform

    Args:
        package_path: Path to skill package file
        target: Target platform ('claude', 'gemini', 'openai', 'chroma', 'weaviate')
        api_key: Optional API key (otherwise read from environment)
        **kwargs: Platform-specific upload options

    Returns:
        tuple: (success, message)
    """
    try:
        from skill_seekers.cli.adaptors import get_adaptor
    except ImportError:
        return False, "Adaptor system not available. Reinstall skill-seekers."

    # Get platform-specific adaptor
    try:
        adaptor = get_adaptor(target)
    except ValueError as e:
        return False, str(e)

    # Get API key
    if not api_key:
        api_key = os.environ.get(adaptor.get_env_var_name(), "").strip()

    # API key validation only for platforms that require it
    if target in ["claude", "gemini", "openai"]:
        if not api_key:
            return False, f"{adaptor.get_env_var_name()} not set. Export your API key first."

        # Validate API key format
        if not adaptor.validate_api_key(api_key):
            return False, f"Invalid API key format for {adaptor.PLATFORM_NAME}"

    package_path = Path(package_path)

    # Basic file validation
    if not package_path.exists():
        return False, f"File not found: {package_path}"

    skill_name = package_path.stem

    print(f"📤 Uploading skill: {skill_name}")
    print(f"   Target: {adaptor.PLATFORM_NAME}")
    print(f"   Source: {package_path}")
    print(f"   Size: {package_path.stat().st_size:,} bytes")
    print()

    # Upload using adaptor
    print(f"⏳ Uploading to {adaptor.PLATFORM_NAME}...")

    try:
        result = adaptor.upload(package_path, api_key, **kwargs)

        if result["success"]:
            print()
            print(f"✅ {result['message']}")
            print()
            if result.get("url"):
                print("Your skill is now available at:")
                print(f"   {result['url']}")
            if result.get("skill_id"):
                print(f"   Skill ID: {result['skill_id']}")
            if result.get("collection"):
                print(f"   Collection: {result['collection']}")
            if result.get("class_name"):
                print(f"   Class: {result['class_name']}")
            if result.get("count"):
                print(f"   Documents uploaded: {result['count']}")
            print()
            return True, "Upload successful"
        else:
            return False, result["message"]

    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def main():
    parser = argparse.ArgumentParser(
        description="Upload a skill package to LLM platforms and vector databases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Setup:
  Claude:
    export ANTHROPIC_API_KEY=sk-ant-...

  Gemini:
    export GOOGLE_API_KEY=AIzaSy...

  OpenAI:
    export OPENAI_API_KEY=sk-proj-...

  ChromaDB (local):
    # No API key needed for local instance
    chroma run  # Start server

  Weaviate (local):
    # No API key needed for local instance
    docker run -p 8080:8080 semitechnologies/weaviate:latest

Examples:
  # Upload to Claude (default)
  skill-seekers upload output/react.zip

  # Upload to Gemini
  skill-seekers upload output/react-gemini.tar.gz --target gemini

  # Upload to OpenAI
  skill-seekers upload output/react-openai.zip --target openai

  # Upload to ChromaDB (local)
  skill-seekers upload output/react-chroma.json --target chroma

  # Upload to ChromaDB with OpenAI embeddings
  skill-seekers upload output/react-chroma.json --target chroma --embedding-function openai

  # Upload to Weaviate (local)
  skill-seekers upload output/react-weaviate.json --target weaviate

  # Upload to Weaviate Cloud
  skill-seekers upload output/react-weaviate.json --target weaviate --use-cloud --cluster-url https://xxx.weaviate.network --api-key YOUR_KEY
        """,
    )

    parser.add_argument("package_file", help="Path to skill package file (e.g., output/react.zip)")

    parser.add_argument(
        "--target",
        choices=["claude", "gemini", "openai", "chroma", "weaviate"],
        default="claude",
        help="Target platform (default: claude)",
    )

    parser.add_argument("--api-key", help="Platform API key (or set environment variable)")

    # ChromaDB upload options
    parser.add_argument(
        "--chroma-url",
        help="ChromaDB URL (default: http://localhost:8000 for HTTP, or use --persist-directory for local)",
    )

    parser.add_argument(
        "--persist-directory",
        help="Local directory for persistent ChromaDB storage (default: ./chroma_db)",
    )

    parser.add_argument(
        "--embedding-function",
        choices=["openai", "sentence-transformers", "none"],
        help="Embedding function for ChromaDB/Weaviate (default: platform default)",
    )

    parser.add_argument(
        "--openai-api-key", help="OpenAI API key for embeddings (or set OPENAI_API_KEY env var)"
    )

    # Weaviate upload options
    parser.add_argument(
        "--weaviate-url",
        default="http://localhost:8080",
        help="Weaviate URL (default: http://localhost:8080)",
    )

    parser.add_argument(
        "--use-cloud",
        action="store_true",
        help="Use Weaviate Cloud (requires --api-key and --cluster-url)",
    )

    parser.add_argument(
        "--cluster-url", help="Weaviate Cloud cluster URL (e.g., https://xxx.weaviate.network)"
    )

    args = parser.parse_args()

    # Build kwargs for vector DB upload
    upload_kwargs = {}

    if args.target == "chroma":
        if args.chroma_url:
            upload_kwargs["chroma_url"] = args.chroma_url
        if args.persist_directory:
            upload_kwargs["persist_directory"] = args.persist_directory
        if args.embedding_function:
            upload_kwargs["embedding_function"] = args.embedding_function
        if args.openai_api_key:
            upload_kwargs["openai_api_key"] = args.openai_api_key

    elif args.target == "weaviate":
        upload_kwargs["weaviate_url"] = args.weaviate_url
        upload_kwargs["use_cloud"] = args.use_cloud
        if args.cluster_url:
            upload_kwargs["cluster_url"] = args.cluster_url
        if args.embedding_function:
            upload_kwargs["embedding_function"] = args.embedding_function
        if args.openai_api_key:
            upload_kwargs["openai_api_key"] = args.openai_api_key

    # Upload skill
    success, message = upload_skill_api(
        args.package_file, args.target, args.api_key, **upload_kwargs
    )

    if success:
        sys.exit(0)
    else:
        print(f"\n❌ Upload failed: {message}")
        print()
        print("📝 Manual upload instructions:")
        print_upload_instructions(args.package_file)
        sys.exit(1)


if __name__ == "__main__":
    main()
