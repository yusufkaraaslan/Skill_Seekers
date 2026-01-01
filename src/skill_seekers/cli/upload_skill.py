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

import os
import sys
import json
import argparse
from pathlib import Path

# Import utilities
try:
    from utils import (
        print_upload_instructions,
        validate_zip_file
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from utils import (
        print_upload_instructions,
        validate_zip_file
    )


def upload_skill_api(package_path, target='claude', api_key=None):
    """
    Upload skill package to LLM platform

    Args:
        package_path: Path to skill package file
        target: Target platform ('claude', 'gemini', 'openai')
        api_key: Optional API key (otherwise read from environment)

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
        api_key = os.environ.get(adaptor.get_env_var_name(), '').strip()

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
        result = adaptor.upload(package_path, api_key)

        if result['success']:
            print()
            print(f"✅ {result['message']}")
            print()
            if result['url']:
                print("Your skill is now available at:")
                print(f"   {result['url']}")
            if result['skill_id']:
                print(f"   Skill ID: {result['skill_id']}")
            print()
            return True, "Upload successful"
        else:
            return False, result['message']

    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def main():
    parser = argparse.ArgumentParser(
        description="Upload a skill package to LLM platforms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Setup:
  Claude:
    export ANTHROPIC_API_KEY=sk-ant-...

  Gemini:
    export GOOGLE_API_KEY=AIzaSy...

  OpenAI:
    export OPENAI_API_KEY=sk-proj-...

Examples:
  # Upload to Claude (default)
  skill-seekers upload output/react.zip

  # Upload to Gemini
  skill-seekers upload output/react-gemini.tar.gz --target gemini

  # Upload to OpenAI
  skill-seekers upload output/react-openai.zip --target openai

  # Upload with explicit API key
  skill-seekers upload output/react.zip --api-key sk-ant-...
        """
    )

    parser.add_argument(
        'package_file',
        help='Path to skill package file (e.g., output/react.zip)'
    )

    parser.add_argument(
        '--target',
        choices=['claude', 'gemini', 'openai'],
        default='claude',
        help='Target LLM platform (default: claude)'
    )

    parser.add_argument(
        '--api-key',
        help='Platform API key (or set environment variable)'
    )

    args = parser.parse_args()

    # Upload skill
    success, message = upload_skill_api(args.package_file, args.target, args.api_key)

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
