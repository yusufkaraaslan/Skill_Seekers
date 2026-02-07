#!/usr/bin/env python3
"""
Automate Cursor rules generation for React.

This script demonstrates the complete workflow:
1. Scrape React documentation
2. Package for Cursor
3. Extract and copy rules to project
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list, description: str) -> bool:
    """Run a shell command and return success status."""
    print(f"\n{'='*60}")
    print(f"STEP: {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        return False

    print(f"✅ Success!")
    if result.stdout:
        # Print first 500 chars to avoid clutter
        output = result.stdout[:500]
        if len(result.stdout) > 500:
            output += "... (truncated)"
        print(output)

    return True


def main():
    """Run the automation workflow."""
    print("=" * 60)
    print("Cursor Rules Generator - React Example")
    print("=" * 60)
    print("\nThis script will:")
    print("  1. Scrape React documentation (100 pages)")
    print("  2. Package for Cursor IDE")
    print("  3. Extract and copy to example-project/")
    print("\n⏱️  Estimated time: 2-3 minutes\n")

    # Step 1: Scrape React docs
    print("Starting workflow...")
    if not run_command(
        [
            "skill-seekers",
            "scrape",
            "--config",
            "../../configs/react.json",
            "--max-pages",
            "100",
        ],
        "Scraping React documentation",
    ):
        print("\n❌ Failed to scrape React documentation")
        print("   Make sure skill-seekers is installed: pip install skill-seekers")
        sys.exit(1)

    # Step 2: Package for Cursor
    if not run_command(
        ["skill-seekers", "package", "../../output/react", "--target", "claude"],
        "Packaging for Cursor",
    ):
        print("\n❌ Failed to package for Cursor")
        sys.exit(1)

    # Step 3: Extract ZIP
    if not run_command(
        [
            "unzip",
            "-o",
            "../../output/react-claude.zip",
            "-d",
            "../../output/react-cursor",
        ],
        "Extracting packaged skill",
    ):
        print("\n❌ Failed to extract package")
        print("   Make sure unzip is installed")
        sys.exit(1)

    # Step 4: Copy to example project
    source = Path("../../output/react-cursor/SKILL.md")
    target = Path("example-project/.cursorrules")

    if not source.exists():
        print(f"\n❌ Error: {source} not found")
        sys.exit(1)

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source.read_text())

    print(f"\n{'='*60}")
    print(f"STEP: Copying rules to project")
    print(f"{'='*60}")
    print(f"✅ Copied {source} → {target}")

    # Success summary
    print("\n" + "=" * 60)
    print("✅ Cursor rules generated successfully!")
    print("=" * 60)
    print(f"\n📁 Rules file: {target.absolute()}")
    print(f"📏 Size: {len(target.read_text())} characters")

    # Preview first 300 characters
    content = target.read_text()
    preview = content[:300]
    if len(content) > 300:
        preview += "..."

    print(f"\n📖 Preview:\n{preview}")

    print("\n🚀 Next steps:")
    print("   1. Open example-project/ in Cursor:")
    print("      cursor example-project/")
    print("\n   2. Try these prompts:")
    print("      - 'Create a useState hook for managing user data'")
    print("      - 'Add useEffect to fetch data on mount'")
    print("      - 'Implement a custom hook for form validation'")
    print("\n   3. Compare AI suggestions with and without .cursorrules")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
