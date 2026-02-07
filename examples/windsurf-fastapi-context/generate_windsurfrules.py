#!/usr/bin/env python3
"""
Automation script to generate Windsurf rules from FastAPI documentation.

Usage:
    python generate_windsurfrules.py --project /path/to/project
    python generate_windsurfrules.py --project . --max-chars 5000
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a shell command and return success status."""
    print(f"\n{'='*60}")
    print(f"STEP: {description}")
    print(f"{'='*60}")
    print(f"Running: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        print(f"❌ ERROR: {description} failed with code {result.returncode}")
        return False

    print(f"✅ SUCCESS: {description}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Generate Windsurf rules from FastAPI documentation"
    )
    parser.add_argument(
        "--project",
        type=str,
        default=".",
        help="Path to your project directory (default: current directory)",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=5500,
        help="Maximum characters per rule file (default: 5500, max: 6000)",
    )
    parser.add_argument(
        "--skip-scrape",
        action="store_true",
        help="Skip scraping step (use existing output/fastapi)",
    )
    args = parser.parse_args()

    project_path = Path(args.project).resolve()
    output_dir = Path("output/fastapi")
    rules_dir = project_path / ".windsurf" / "rules"

    print("=" * 60)
    print("Windsurf Rules Generator for FastAPI")
    print("=" * 60)
    print(f"Project: {project_path}")
    print(f"Rules directory: {rules_dir}")
    print(f"Max characters per file: {args.max_chars}")
    print("=" * 60)

    # Step 1: Scrape FastAPI documentation (unless skipped)
    if not args.skip_scrape:
        if not run_command(
            [
                "skill-seekers",
                "scrape",
                "--config",
                "configs/fastapi.json",
            ],
            "Scraping FastAPI documentation",
        ):
            return 1
    else:
        print(f"\n⏭️  SKIPPED: Using existing {output_dir}")

        if not output_dir.exists():
            print(f"❌ ERROR: {output_dir} does not exist!")
            print(f"Run without --skip-scrape to generate documentation first.")
            return 1

    # Step 2: Package with split rules
    if not run_command(
        [
            "skill-seekers",
            "package",
            str(output_dir),
            "--target",
            "markdown",
            "--split-rules",
            "--max-chars",
            str(args.max_chars),
        ],
        "Packaging for Windsurf with split rules",
    ):
        return 1

    # Step 3: Copy rules to project
    print(f"\n{'='*60}")
    print(f"STEP: Copying rules to project")
    print(f"{'='*60}")

    markdown_output = output_dir.parent / "fastapi-markdown"
    source_rules = markdown_output / "rules"

    if not source_rules.exists():
        # Single file (no splitting needed)
        source_skill = markdown_output / "SKILL.md"
        if not source_skill.exists():
            print(f"❌ ERROR: {source_skill} does not exist!")
            return 1

        # Create rules directory
        rules_dir.mkdir(parents=True, exist_ok=True)

        # Copy as single rule file
        dest_file = rules_dir / "fastapi.md"
        shutil.copy(source_skill, dest_file)
        print(f"✅ Copied: {dest_file}")
    else:
        # Multiple rule files
        rules_dir.mkdir(parents=True, exist_ok=True)

        for rule_file in source_rules.glob("*.md"):
            dest_file = rules_dir / rule_file.name
            shutil.copy(rule_file, dest_file)
            print(f"✅ Copied: {dest_file}")

    print(f"\n{'='*60}")
    print(f"✅ SUCCESS: Rules generated and copied!")
    print(f"{'='*60}")
    print(f"\nRules location: {rules_dir}")
    print(f"\nNext steps:")
    print(f"1. Open project in Windsurf: windsurf {project_path}")
    print(f"2. Reload window: Cmd+Shift+P → 'Reload Window'")
    print(f"3. Start Cascade: Cmd+L (or Ctrl+L)")
    print(f"4. Test: 'Create a FastAPI endpoint with async database'")
    print(f"\nRule files:")
    for rule_file in sorted(rules_dir.glob("*.md")):
        size = rule_file.stat().st_size
        print(f"  - {rule_file.name} ({size:,} bytes)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
