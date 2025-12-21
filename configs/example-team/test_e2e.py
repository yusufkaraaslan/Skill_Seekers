#!/usr/bin/env python3
"""
E2E Test Script for Example Team Config Repository

Tests the complete workflow:
1. Register the example-team source
2. Fetch a config from it
3. Verify the config was loaded correctly
4. Clean up
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skill_seekers.mcp.source_manager import SourceManager
from skill_seekers.mcp.git_repo import GitConfigRepo


def test_example_team_repo():
    """Test the example-team repository end-to-end."""
    print("🧪 E2E Test: Example Team Config Repository\n")

    # Get absolute path to example-team directory
    example_team_path = Path(__file__).parent.absolute()
    git_url = f"file://{example_team_path}"

    print(f"📁 Repository: {git_url}\n")

    # Step 1: Add source
    print("1️⃣  Registering source...")
    sm = SourceManager()
    try:
        source = sm.add_source(
            name="example-team-test",
            git_url=git_url,
            source_type="custom",
            branch="master"  # Git init creates 'master' by default
        )
        print(f"   ✅ Source registered: {source['name']}")
    except Exception as e:
        print(f"   ❌ Failed to register source: {e}")
        return False

    # Step 2: Clone/pull repository
    print("\n2️⃣  Cloning repository...")
    gr = GitConfigRepo()
    try:
        repo_path = gr.clone_or_pull(
            source_name="example-team-test",
            git_url=git_url,
            branch="master"
        )
        print(f"   ✅ Repository cloned to: {repo_path}")
    except Exception as e:
        print(f"   ❌ Failed to clone repository: {e}")
        return False

    # Step 3: List available configs
    print("\n3️⃣  Discovering configs...")
    try:
        configs = gr.find_configs(repo_path)
        print(f"   ✅ Found {len(configs)} configs:")
        for config_file in configs:
            print(f"      - {config_file.name}")
    except Exception as e:
        print(f"   ❌ Failed to discover configs: {e}")
        return False

    # Step 4: Fetch a specific config
    print("\n4️⃣  Fetching 'react-custom' config...")
    try:
        config = gr.get_config(repo_path, "react-custom")
        print(f"   ✅ Config loaded successfully!")
        print(f"      Name: {config['name']}")
        print(f"      Description: {config['description']}")
        print(f"      Base URL: {config['base_url']}")
        print(f"      Max Pages: {config['max_pages']}")
        if 'metadata' in config:
            print(f"      Team: {config['metadata'].get('team', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Failed to fetch config: {e}")
        return False

    # Step 5: Verify config content
    print("\n5️⃣  Verifying config content...")
    try:
        assert config['name'] == 'react-custom', "Config name mismatch"
        assert 'selectors' in config, "Missing selectors"
        assert 'url_patterns' in config, "Missing url_patterns"
        assert 'categories' in config, "Missing categories"
        print("   ✅ Config structure validated")
    except AssertionError as e:
        print(f"   ❌ Validation failed: {e}")
        return False

    # Step 6: List all sources
    print("\n6️⃣  Listing all sources...")
    try:
        sources = sm.list_sources()
        print(f"   ✅ Total sources: {len(sources)}")
        for src in sources:
            print(f"      - {src['name']} ({src['type']})")
    except Exception as e:
        print(f"   ❌ Failed to list sources: {e}")
        return False

    # Step 7: Clean up
    print("\n7️⃣  Cleaning up...")
    try:
        removed = sm.remove_source("example-team-test")
        if removed:
            print("   ✅ Source removed successfully")
        else:
            print("   ⚠️  Source was not found (already removed?)")
    except Exception as e:
        print(f"   ❌ Failed to remove source: {e}")
        return False

    print("\n" + "="*60)
    print("✅ E2E TEST PASSED - All steps completed successfully!")
    print("="*60)
    return True


if __name__ == "__main__":
    success = test_example_team_repo()
    sys.exit(0 if success else 1)
