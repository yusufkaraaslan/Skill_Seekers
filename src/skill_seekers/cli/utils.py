#!/usr/bin/env python3
"""
Utility functions for Skill Seeker CLI tools
"""

import os
import sys
import subprocess
import platform
import time
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Union, TypeVar, Callable

logger = logging.getLogger(__name__)

T = TypeVar('T')


def open_folder(folder_path: Union[str, Path]) -> bool:
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


def has_api_key() -> bool:
    """
    Check if ANTHROPIC_API_KEY is set in environment

    Returns:
        bool: True if API key is set, False otherwise
    """
    api_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()
    return len(api_key) > 0


def get_api_key() -> Optional[str]:
    """
    Get ANTHROPIC_API_KEY from environment

    Returns:
        str: API key or None if not set
    """
    api_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()
    return api_key if api_key else None


def get_upload_url() -> str:
    """
    Get the Claude skills upload URL

    Returns:
        str: Claude skills upload URL
    """
    return "https://claude.ai/skills"


def print_upload_instructions(zip_path: Union[str, Path]) -> None:
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


def format_file_size(size_bytes: int) -> str:
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


def validate_skill_directory(skill_dir: Union[str, Path]) -> Tuple[bool, Optional[str]]:
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


def validate_zip_file(zip_path: Union[str, Path]) -> Tuple[bool, Optional[str]]:
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


def read_reference_files(skill_dir: Union[str, Path], max_chars: int = 100000, preview_limit: int = 40000) -> Dict[str, str]:
    """Read reference files from a skill directory with size limits.

    This function reads markdown files from the references/ subdirectory
    of a skill, applying both per-file and total content limits.

    Args:
        skill_dir (str or Path): Path to skill directory
        max_chars (int): Maximum total characters to read (default: 100000)
        preview_limit (int): Maximum characters per file (default: 40000)

    Returns:
        dict: Dictionary mapping filename to content

    Example:
        >>> refs = read_reference_files('output/react/', max_chars=50000)
        >>> len(refs)
        5
    """
    from pathlib import Path

    skill_path = Path(skill_dir)
    references_dir = skill_path / "references"
    references: Dict[str, str] = {}

    if not references_dir.exists():
        print(f"⚠ No references directory found at {references_dir}")
        return references

    total_chars = 0
    # Search recursively for all .md files (including subdirectories like github/README.md)
    for ref_file in sorted(references_dir.rglob("*.md")):
        if ref_file.name == "index.md":
            continue

        content = ref_file.read_text(encoding='utf-8')

        # Limit size per file
        if len(content) > preview_limit:
            content = content[:preview_limit] + "\n\n[Content truncated...]"

        # Use relative path from references_dir as key for nested files
        relative_path = ref_file.relative_to(references_dir)
        references[str(relative_path)] = content
        total_chars += len(content)

        # Stop if we've read enough
        if total_chars > max_chars:
            print(f"  ℹ Limiting input to {max_chars:,} characters")
            break

    return references


def retry_with_backoff(
    operation: Callable[[], T],
    max_attempts: int = 3,
    base_delay: float = 1.0,
    operation_name: str = "operation"
) -> T:
    """Retry an operation with exponential backoff.

    Useful for network operations that may fail due to transient errors.
    Waits progressively longer between retries (exponential backoff).

    Args:
        operation: Function to retry (takes no arguments, returns result)
        max_attempts: Maximum number of attempts (default: 3)
        base_delay: Base delay in seconds, doubles each retry (default: 1.0)
        operation_name: Name for logging purposes (default: "operation")

    Returns:
        Result of successful operation

    Raises:
        Exception: Last exception if all retries fail

    Example:
        >>> def fetch_page():
        ...     response = requests.get(url, timeout=30)
        ...     response.raise_for_status()
        ...     return response.text
        >>> content = retry_with_backoff(fetch_page, max_attempts=3, operation_name=f"fetch {url}")
    """
    last_exception: Optional[Exception] = None

    for attempt in range(1, max_attempts + 1):
        try:
            return operation()
        except Exception as e:
            last_exception = e
            if attempt < max_attempts:
                delay = base_delay * (2 ** (attempt - 1))
                logger.warning(
                    "%s failed (attempt %d/%d), retrying in %.1fs: %s",
                    operation_name, attempt, max_attempts, delay, e
                )
                time.sleep(delay)
            else:
                logger.error(
                    "%s failed after %d attempts: %s",
                    operation_name, max_attempts, e
                )

    # This should always have a value, but mypy doesn't know that
    if last_exception is not None:
        raise last_exception
    raise RuntimeError(f"{operation_name} failed with no exception captured")


async def retry_with_backoff_async(
    operation: Callable[[], T],
    max_attempts: int = 3,
    base_delay: float = 1.0,
    operation_name: str = "operation"
) -> T:
    """Async version of retry_with_backoff for async operations.

    Args:
        operation: Async function to retry (takes no arguments, returns awaitable)
        max_attempts: Maximum number of attempts (default: 3)
        base_delay: Base delay in seconds, doubles each retry (default: 1.0)
        operation_name: Name for logging purposes (default: "operation")

    Returns:
        Result of successful operation

    Raises:
        Exception: Last exception if all retries fail

    Example:
        >>> async def fetch_page():
        ...     response = await client.get(url, timeout=30.0)
        ...     response.raise_for_status()
        ...     return response.text
        >>> content = await retry_with_backoff_async(fetch_page, operation_name=f"fetch {url}")
    """
    import asyncio

    last_exception: Optional[Exception] = None

    for attempt in range(1, max_attempts + 1):
        try:
            return await operation()
        except Exception as e:
            last_exception = e
            if attempt < max_attempts:
                delay = base_delay * (2 ** (attempt - 1))
                logger.warning(
                    "%s failed (attempt %d/%d), retrying in %.1fs: %s",
                    operation_name, attempt, max_attempts, delay, e
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    "%s failed after %d attempts: %s",
                    operation_name, max_attempts, e
                )

    if last_exception is not None:
        raise last_exception
    raise RuntimeError(f"{operation_name} failed with no exception captured")
