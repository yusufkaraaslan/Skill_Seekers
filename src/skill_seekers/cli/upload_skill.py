#!/usr/bin/env python3
"""
Automatic Skill Uploader
Uploads a skill package to LLM platforms (Claude, Gemini, OpenAI, etc.)

Usage:
    # Anthropic (default)
    export ANTHROPIC_API_KEY=sk-ant-...
    skill-seekers upload output/react.zip

    # Gemini
    export GOOGLE_API_KEY=AIzaSy...
    skill-seekers upload output/react-gemini.tar.gz --target gemini

    # OpenAI
    export OPENAI_API_KEY=sk-proj-...
    skill-seekers upload output/react-openai.zip --target openai
"""

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


def main(args=None):
    from skill_seekers.cli.exit_codes import EXIT_ERROR, EXIT_SUCCESS

    if args is None:
        # Single source of flags: the central UploadParser (which itself
        # delegates to arguments.upload.add_upload_arguments).
        from skill_seekers.cli.parsers.upload_parser import UploadParser

        parser = UploadParser().build_standalone()
        args = parser.parse_args()

    # Auto-detect target platform if not specified
    if args.target is None:
        from skill_seekers.cli.agent_client import AgentClient

        args.target = AgentClient.detect_default_target()

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
        sys.exit(EXIT_SUCCESS)
    else:
        print(f"\n❌ Upload failed: {message}")
        print()
        print("📝 Manual upload instructions:")
        print_upload_instructions(args.package_file)
        sys.exit(EXIT_ERROR)


if __name__ == "__main__":
    main()
