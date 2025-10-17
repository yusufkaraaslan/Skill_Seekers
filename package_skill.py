#!/usr/bin/env python3
"""
Simple Skill Packager
Packages a skill directory into a .zip file for Claude.

Usage:
    python3 package_skill.py output/steam-inventory/
    python3 package_skill.py output/react/
"""

import os
import sys
import zipfile
from pathlib import Path


def package_skill(skill_dir):
    """Package a skill directory into a .zip file"""
    skill_path = Path(skill_dir)

    if not skill_path.exists():
        print(f"❌ Error: Directory not found: {skill_dir}")
        return False

    if not skill_path.is_dir():
        print(f"❌ Error: Not a directory: {skill_dir}")
        return False

    # Verify SKILL.md exists
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        print(f"❌ Error: SKILL.md not found in {skill_dir}")
        return False

    # Create zip filename
    skill_name = skill_path.name
    zip_path = skill_path.parent / f"{skill_name}.zip"

    print(f"📦 Packaging skill: {skill_name}")
    print(f"   Source: {skill_path}")
    print(f"   Output: {zip_path}")

    # Create zip file
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(skill_path):
            # Skip backup files
            files = [f for f in files if not f.endswith('.backup')]

            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(skill_path)
                zf.write(file_path, arcname)
                print(f"   + {arcname}")

    # Get zip size
    zip_size = zip_path.stat().st_size
    print(f"\n✅ Package created: {zip_path}")
    print(f"   Size: {zip_size:,} bytes ({zip_size / 1024:.1f} KB)")

    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 package_skill.py <skill_directory>")
        print()
        print("Examples:")
        print("  python3 package_skill.py output/steam-inventory/")
        print("  python3 package_skill.py output/react/")
        sys.exit(1)

    skill_dir = sys.argv[1]
    success = package_skill(skill_dir)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
