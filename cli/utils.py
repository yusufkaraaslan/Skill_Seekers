#!/usr/bin/env python3
"""
Utility functions for Skill Seeker CLI tools
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def open_folder(folder_path):
    """
    Open a folder in the system file browser

    Args:
        folder_path: Path to folder to open

    Returns:
        bool: True if successful, False otherwise
    """
    folder_path = Path(folder_path).resolve()

    if not folder_path.exists():
        print(f"⚠️  Folder not found: {folder_path}")
        return False

    system = platform.system()

    try:
        if system == "Linux":
            # Try xdg-open first (standard)
            subprocess.run(["xdg-open", str(folder_path)], check=True)
        elif system == "Darwin":  # macOS
            subprocess.run(["open", str(folder_path)], check=True)
        elif system == "Windows":
            subprocess.run(["explorer", str(folder_path)], check=True)
        else:
            print(f"⚠️  Unknown operating system: {system}")
            return False

        return True

    except subprocess.CalledProcessError:
        print(f"⚠️  Could not open folder automatically")
        return False
    except FileNotFoundError:
        print(f"⚠️  File browser not found on system")
        return False


def has_api_key():
    """
    Check if ANTHROPIC_API_KEY is set in environment

    Returns:
        bool: True if API key is set, False otherwise
    """
    api_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()
    return len(api_key) > 0


def get_api_key():
    """
    Get ANTHROPIC_API_KEY from environment

    Returns:
        str: API key or None if not set
    """
    api_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()
    return api_key if api_key else None


def get_upload_url():
    """
    Get the Claude skills upload URL

    Returns:
        str: Claude skills upload URL
    """
    return "https://claude.ai/skills"


def print_upload_instructions(zip_path):
    """
    Print clear upload instructions for manual upload

    Args:
        zip_path: Path to the .zip file to upload
    """
    zip_path = Path(zip_path)

    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║                     NEXT STEP                            ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    print(f"📤 Upload to Claude: {get_upload_url()}")
    print()
    print(f"1. Go to {get_upload_url()}")
    print("2. Click \"Upload Skill\"")
    print(f"3. Select: {zip_path}")
    print("4. Done! ✅")
    print()


def format_file_size(size_bytes):
    """
    Format file size in human-readable format

    Args:
        size_bytes: Size in bytes

    Returns:
        str: Formatted size (e.g., "45.3 KB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def validate_skill_directory(skill_dir):
    """
    Validate that a directory is a valid skill directory

    Args:
        skill_dir: Path to skill directory

    Returns:
        tuple: (is_valid, error_message)
    """
    skill_path = Path(skill_dir)

    if not skill_path.exists():
        return False, f"Directory not found: {skill_dir}"

    if not skill_path.is_dir():
        return False, f"Not a directory: {skill_dir}"

    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return False, f"SKILL.md not found in {skill_dir}"

    return True, None


def validate_zip_file(zip_path):
    """
    Validate that a file is a valid skill .zip file

    Args:
        zip_path: Path to .zip file

    Returns:
        tuple: (is_valid, error_message)
    """
    zip_path = Path(zip_path)

    if not zip_path.exists():
        return False, f"File not found: {zip_path}"

    if not zip_path.is_file():
        return False, f"Not a file: {zip_path}"

    if not zip_path.suffix == '.zip':
        return False, f"Not a .zip file: {zip_path}"

    return True, None
