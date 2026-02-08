#!/usr/bin/env python3
"""
Simple Skill Packager
Packages a skill directory into a .zip file for Claude.

Usage:
    skill-seekers package output/steam-inventory/
    skill-seekers package output/react/
    skill-seekers package output/react/ --no-open  # Don't open folder
"""

import argparse
import os
import sys
from pathlib import Path

# Import utilities
try:
    from quality_checker import SkillQualityChecker, print_report
    from utils import (
        format_file_size,
        open_folder,
        print_upload_instructions,
        validate_skill_directory,
    )
except ImportError:
    # If running from different directory, add cli to path
    sys.path.insert(0, str(Path(__file__).parent))
    from quality_checker import SkillQualityChecker, print_report
    from utils import (
        format_file_size,
        open_folder,
        print_upload_instructions,
        validate_skill_directory,
    )


def package_skill(
    skill_dir,
    open_folder_after=True,
    skip_quality_check=False,
    target="claude",
    streaming=False,
    chunk_size=4000,
    chunk_overlap=200,
    batch_size=100,
    enable_chunking=False,
    chunk_max_tokens=512,
    preserve_code_blocks=True,
):
    """
    Package a skill directory into platform-specific format

    Args:
        skill_dir: Path to skill directory
        open_folder_after: Whether to open the output folder after packaging
        skip_quality_check: Skip quality checks before packaging
        target: Target LLM platform ('claude', 'gemini', 'openai', 'markdown')
        streaming: Use streaming ingestion for large docs
        chunk_size: Maximum characters per chunk (streaming mode)
        chunk_overlap: Overlap between chunks (streaming mode)
        batch_size: Number of chunks per batch (streaming mode)
        enable_chunking: Enable intelligent chunking for RAG platforms
        chunk_max_tokens: Maximum tokens per chunk (default: 512)
        preserve_code_blocks: Preserve code blocks during chunking

    Returns:
        tuple: (success, package_path) where success is bool and package_path is Path or None
    """
    skill_path = Path(skill_dir)

    # Validate skill directory
    is_valid, error_msg = validate_skill_directory(skill_path)
    if not is_valid:
        print(f"❌ Error: {error_msg}")
        return False, None

    # Run quality checks (unless skipped)
    if not skip_quality_check:
        print("\n" + "=" * 60)
        print("QUALITY CHECK")
        print("=" * 60)

        checker = SkillQualityChecker(skill_path)
        report = checker.check_all()

        # Print report
        print_report(report, verbose=False)

        # If there are errors or warnings, ask user to confirm
        if report.has_errors or report.has_warnings:
            print("=" * 60)
            response = input("\nContinue with packaging? (y/n): ").strip().lower()
            if response != "y":
                print("\n❌ Packaging cancelled by user")
                return False, None
            print()
        else:
            print("=" * 60)
            print()

    # Get platform-specific adaptor
    try:
        from skill_seekers.cli.adaptors import get_adaptor

        adaptor = get_adaptor(target)
    except (ImportError, ValueError) as e:
        print(f"❌ Error: {e}")
        return False, None

    # Create package using adaptor
    skill_name = skill_path.name
    output_dir = skill_path.parent

    # Auto-enable chunking for RAG platforms
    RAG_PLATFORMS = [
        "langchain",
        "llama-index",
        "haystack",
        "weaviate",
        "chroma",
        "faiss",
        "qdrant",
    ]

    if target in RAG_PLATFORMS and not enable_chunking:
        print(f"ℹ️  Auto-enabling chunking for {target} platform")
        enable_chunking = True

    print(f"📦 Packaging skill: {skill_name}")
    print(f"   Target: {adaptor.PLATFORM_NAME}")
    print(f"   Source: {skill_path}")

    if streaming:
        print(f"   Mode: Streaming (chunk_size={chunk_size}, overlap={chunk_overlap})")
    elif enable_chunking:
        print(
            f"   Chunking: Enabled (max_tokens={chunk_max_tokens}, preserve_code={preserve_code_blocks})"
        )

    try:
        # Use streaming if requested and supported
        if streaming and hasattr(adaptor, "package_streaming"):
            package_path = adaptor.package_streaming(
                skill_path,
                output_dir,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                batch_size=batch_size,
            )
        elif streaming:
            print("⚠️  Streaming not supported for this platform, using standard packaging")
            package_path = adaptor.package(
                skill_path,
                output_dir,
                enable_chunking=enable_chunking,
                chunk_max_tokens=chunk_max_tokens,
                preserve_code_blocks=preserve_code_blocks,
            )
        else:
            package_path = adaptor.package(
                skill_path,
                output_dir,
                enable_chunking=enable_chunking,
                chunk_max_tokens=chunk_max_tokens,
                preserve_code_blocks=preserve_code_blocks,
            )

        print(f"   Output: {package_path}")
    except Exception as e:
        print(f"❌ Error creating package: {e}")
        return False, None

    # Get package size
    package_size = package_path.stat().st_size
    print(f"\n✅ Package created: {package_path}")
    print(f"   Size: {package_size:,} bytes ({format_file_size(package_size)})")

    # Open folder in file browser
    if open_folder_after:
        print(f"\n📂 Opening folder: {package_path.parent}")
        open_folder(package_path.parent)

    # Print upload instructions
    print_upload_instructions(package_path)

    return True, package_path


def main():
    parser = argparse.ArgumentParser(
        description="Package a skill directory into a .zip file for Claude",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Package skill with quality checks (recommended)
  skill-seekers package output/react/

  # Package skill without opening folder
  skill-seekers package output/react/ --no-open

  # Skip quality checks (faster, but not recommended)
  skill-seekers package output/react/ --skip-quality-check

  # Package and auto-upload to Claude
  skill-seekers package output/react/ --upload

  # Get help
  skill-seekers package --help
        """,
    )

    parser.add_argument("skill_dir", help="Path to skill directory (e.g., output/react/)")

    parser.add_argument(
        "--no-open", action="store_true", help="Do not open the output folder after packaging"
    )

    parser.add_argument(
        "--skip-quality-check", action="store_true", help="Skip quality checks before packaging"
    )

    parser.add_argument(
        "--target",
        choices=[
            "claude",
            "gemini",
            "openai",
            "markdown",
            "langchain",
            "llama-index",
            "haystack",
            "weaviate",
            "chroma",
            "faiss",
            "qdrant",
        ],
        default="claude",
        help="Target LLM platform (default: claude)",
    )

    parser.add_argument(
        "--upload",
        action="store_true",
        help="Automatically upload after packaging (requires platform API key)",
    )

    parser.add_argument(
        "--streaming",
        action="store_true",
        help="Use streaming ingestion for large docs (memory-efficient, with chunking)",
    )

    parser.add_argument(
        "--chunk-size",
        type=int,
        default=4000,
        help="Maximum characters per chunk (streaming mode, default: 4000)",
    )

    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="Overlap between chunks for context (streaming mode, default: 200)",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of chunks per batch (streaming mode, default: 100)",
    )

    # Chunking parameters (for RAG platforms)
    parser.add_argument(
        "--chunk",
        action="store_true",
        help="Enable intelligent chunking for RAG platforms (auto-enabled for RAG adaptors)",
    )

    parser.add_argument(
        "--chunk-tokens",
        type=int,
        default=512,
        help="Maximum tokens per chunk (default: 512, recommended for OpenAI embeddings)",
    )

    parser.add_argument(
        "--no-preserve-code",
        action="store_true",
        help="Allow code block splitting (default: false, code blocks preserved)",
    )

    args = parser.parse_args()

    success, package_path = package_skill(
        args.skill_dir,
        open_folder_after=not args.no_open,
        skip_quality_check=args.skip_quality_check,
        target=args.target,
        streaming=args.streaming,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        batch_size=args.batch_size,
        enable_chunking=args.chunk,
        chunk_max_tokens=args.chunk_tokens,
        preserve_code_blocks=not args.no_preserve_code,
    )

    if not success:
        sys.exit(1)

    # Auto-upload if requested
    if args.upload:
        try:
            from skill_seekers.cli.adaptors import get_adaptor

            # Get adaptor for target platform
            adaptor = get_adaptor(args.target)

            # Get API key from environment
            api_key = os.environ.get(adaptor.get_env_var_name(), "").strip()

            if not api_key:
                # No API key - show helpful message but DON'T fail
                print("\n" + "=" * 60)
                print("💡 Automatic Upload")
                print("=" * 60)
                print()
                print(f"To enable automatic upload to {adaptor.PLATFORM_NAME}:")
                print("  1. Get API key from the platform")
                print(f"  2. Set: export {adaptor.get_env_var_name()}=...")
                print("  3. Run package command with --upload flag")
                print()
                print("For now, use manual upload (instructions above) ☝️")
                print("=" * 60)
                # Exit successfully - packaging worked!
                sys.exit(0)

            # API key exists - try upload
            print("\n" + "=" * 60)
            print(f"📤 Uploading to {adaptor.PLATFORM_NAME}...")
            print("=" * 60)

            result = adaptor.upload(package_path, api_key)

            if result["success"]:
                print(f"\n✅ {result['message']}")
                if result["url"]:
                    print(f"   View at: {result['url']}")
                print("=" * 60)
                sys.exit(0)
            else:
                print(f"\n❌ Upload failed: {result['message']}")
                print()
                print("💡 Try manual upload instead (instructions above) ☝️")
                print("=" * 60)
                # Exit successfully - packaging worked even if upload failed
                sys.exit(0)

        except ImportError as e:
            print(f"\n❌ Error: {e}")
            print("Install required dependencies for this platform")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Upload error: {e}")
            sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
