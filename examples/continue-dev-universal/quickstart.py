#!/usr/bin/env python3
"""
Quickstart script for Continue.dev + Skill Seekers integration.

Usage:
    python quickstart.py --framework vue
    python quickstart.py --framework django --skip-scrape
"""

import argparse
import json
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


def create_continue_config(framework: str, port: int = 8765) -> Path:
    """
    Create Continue.dev configuration.

    Args:
        framework: Framework name
        port: Context server port

    Returns:
        Path to created config file
    """
    config_dir = Path.home() / ".continue"
    config_dir.mkdir(exist_ok=True)

    config_path = config_dir / "config.json"

    # Load existing config or create new
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        config = {
            "models": [],
            "contextProviders": []
        }

    # Add context provider for this framework
    provider = {
        "name": "http",
        "params": {
            "url": f"http://localhost:{port}/docs/{framework}",
            "title": f"{framework}-docs",
            "displayTitle": f"{framework.title()} Documentation",
            "description": f"{framework} framework expert knowledge"
        }
    }

    # Check if already exists
    existing = [
        p for p in config.get("contextProviders", [])
        if p.get("params", {}).get("title") == provider["params"]["title"]
    ]

    if not existing:
        config.setdefault("contextProviders", []).append(provider)
        print(f"✅ Added {framework} context provider to Continue config")
    else:
        print(f"⏭️  {framework} context provider already exists in Continue config")

    # Save config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    return config_path


def main():
    parser = argparse.ArgumentParser(
        description="Quickstart script for Continue.dev + Skill Seekers"
    )
    parser.add_argument(
        "--framework",
        type=str,
        required=True,
        help="Framework to generate documentation for (vue, react, django, etc.)"
    )
    parser.add_argument(
        "--skip-scrape",
        action="store_true",
        help="Skip scraping step (use existing output)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Context server port (default: 8765)"
    )
    args = parser.parse_args()

    framework = args.framework.lower()
    output_dir = Path(f"output/{framework}")

    print("=" * 60)
    print("Continue.dev + Skill Seekers Quickstart")
    print("=" * 60)
    print(f"Framework: {framework}")
    print(f"Context server port: {args.port}")
    print("=" * 60)

    # Step 1: Scrape documentation (unless skipped)
    if not args.skip_scrape:
        if not run_command(
            [
                "skill-seekers",
                "scrape",
                "--config",
                f"configs/{framework}.json"
            ],
            f"Scraping {framework} documentation"
        ):
            return 1
    else:
        print(f"\n⏭️  SKIPPED: Using existing {output_dir}")

        if not output_dir.exists():
            print(f"❌ ERROR: {output_dir} does not exist!")
            print(f"Run without --skip-scrape to generate documentation first.")
            return 1

    # Step 2: Package documentation
    if not run_command(
        [
            "skill-seekers",
            "package",
            str(output_dir),
            "--target",
            "markdown"
        ],
        f"Packaging {framework} documentation"
    ):
        return 1

    # Step 3: Create Continue config
    print(f"\n{'='*60}")
    print(f"STEP: Configuring Continue.dev")
    print(f"{'='*60}")

    config_path = create_continue_config(framework, args.port)
    print(f"✅ Continue config updated: {config_path}")

    # Step 4: Instructions for starting server
    print(f"\n{'='*60}")
    print(f"✅ SUCCESS: Setup complete!")
    print(f"{'='*60}")
    print(f"\nNext steps:")
    print(f"\n1. Start context server:")
    print(f"   python context_server.py --port {args.port}")
    print(f"\n2. Open any IDE with Continue.dev:")
    print(f"   - VS Code: code my-project/")
    print(f"   - IntelliJ: idea my-project/")
    print(f"   - PyCharm: pycharm my-project/")
    print(f"\n3. Test in Continue panel (Cmd+L or Ctrl+L):")
    print(f"   @{framework}-docs Create a {framework} component")
    print(f"\n4. Verify Continue references documentation")
    print(f"\nContinue config location: {config_path}")
    print(f"Context provider: @{framework}-docs")

    return 0


if __name__ == "__main__":
    sys.exit(main())
