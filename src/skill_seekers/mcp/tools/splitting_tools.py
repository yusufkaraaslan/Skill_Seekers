"""
Splitting tools for Skill Seeker MCP Server.

This module provides tools for splitting large documentation configs into multiple
focused skills and generating router/hub skills for managing split documentation.
"""

import glob
import sys
from pathlib import Path
from typing import Any, List

try:
    from mcp.types import TextContent
except ImportError:
    TextContent = None

# Path to CLI tools
CLI_DIR = Path(__file__).parent.parent.parent / "cli"

# Import subprocess helper from parent module
# We'll use a local import to avoid circular dependencies
def run_subprocess_with_streaming(cmd, timeout=None):
    """
    Run subprocess with real-time output streaming.
    Returns (stdout, stderr, returncode).

    This solves the blocking issue where long-running processes (like scraping)
    would cause MCP to appear frozen. Now we stream output as it comes.
    """
    import subprocess
    import time

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True
        )

        stdout_lines = []
        stderr_lines = []
        start_time = time.time()

        # Read output line by line as it comes
        while True:
            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                process.kill()
                stderr_lines.append(f"\n⚠️ Process killed after {timeout}s timeout")
                break

            # Check if process finished
            if process.poll() is not None:
                break

            # Read available output (non-blocking)
            try:
                import select
                readable, _, _ = select.select([process.stdout, process.stderr], [], [], 0.1)

                if process.stdout in readable:
                    line = process.stdout.readline()
                    if line:
                        stdout_lines.append(line)

                if process.stderr in readable:
                    line = process.stderr.readline()
                    if line:
                        stderr_lines.append(line)
            except:
                # Fallback for Windows (no select)
                time.sleep(0.1)

        # Get any remaining output
        remaining_stdout, remaining_stderr = process.communicate()
        if remaining_stdout:
            stdout_lines.append(remaining_stdout)
        if remaining_stderr:
            stderr_lines.append(remaining_stderr)

        stdout = ''.join(stdout_lines)
        stderr = ''.join(stderr_lines)
        returncode = process.returncode

        return stdout, stderr, returncode

    except Exception as e:
        return "", f"Error running subprocess: {str(e)}", 1


async def split_config(args: dict) -> List[TextContent]:
    """
    Split large documentation config into multiple focused skills.

    For large documentation sites (10K+ pages), this tool splits the config into
    multiple smaller configs based on categories, size, or custom strategy. This
    improves performance and makes individual skills more focused.

    Args:
        args: Dictionary containing:
            - config_path (str): Path to config JSON file (e.g., configs/godot.json)
            - strategy (str, optional): Split strategy: auto, none, category, router, size (default: auto)
            - target_pages (int, optional): Target pages per skill (default: 5000)
            - dry_run (bool, optional): Preview without saving files (default: False)

    Returns:
        List[TextContent]: Split results showing created configs and recommendations,
                          or error message if split failed.
    """
    config_path = args["config_path"]
    strategy = args.get("strategy", "auto")
    target_pages = args.get("target_pages", 5000)
    dry_run = args.get("dry_run", False)

    # Run split_config.py
    cmd = [
        sys.executable,
        str(CLI_DIR / "split_config.py"),
        config_path,
        "--strategy", strategy,
        "--target-pages", str(target_pages)
    ]

    if dry_run:
        cmd.append("--dry-run")

    # Timeout: 5 minutes for config splitting
    timeout = 300

    progress_msg = "✂️ Splitting configuration...\n"
    progress_msg += f"⏱️ Maximum time: {timeout // 60} minutes\n\n"

    stdout, stderr, returncode = run_subprocess_with_streaming(cmd, timeout=timeout)

    output = progress_msg + stdout

    if returncode == 0:
        return [TextContent(type="text", text=output)]
    else:
        return [TextContent(type="text", text=f"{output}\n\n❌ Error:\n{stderr}")]


async def generate_router(args: dict) -> List[TextContent]:
    """
    Generate router/hub skill for split documentation.

    Creates an intelligent routing skill that helps users navigate between split
    sub-skills. The router skill analyzes user queries and directs them to the
    appropriate sub-skill based on content categories.

    Args:
        args: Dictionary containing:
            - config_pattern (str): Config pattern for sub-skills (e.g., 'configs/godot-*.json')
            - router_name (str, optional): Router skill name (optional, inferred from configs)

    Returns:
        List[TextContent]: Router skill creation results with usage instructions,
                          or error message if generation failed.
    """
    config_pattern = args["config_pattern"]
    router_name = args.get("router_name")

    # Expand glob pattern
    config_files = glob.glob(config_pattern)

    if not config_files:
        return [TextContent(type="text", text=f"❌ No config files match pattern: {config_pattern}")]

    # Run generate_router.py
    cmd = [
        sys.executable,
        str(CLI_DIR / "generate_router.py"),
    ] + config_files

    if router_name:
        cmd.extend(["--name", router_name])

    # Timeout: 5 minutes for router generation
    timeout = 300

    progress_msg = "🧭 Generating router skill...\n"
    progress_msg += f"⏱️ Maximum time: {timeout // 60} minutes\n\n"

    stdout, stderr, returncode = run_subprocess_with_streaming(cmd, timeout=timeout)

    output = progress_msg + stdout

    if returncode == 0:
        return [TextContent(type="text", text=output)]
    else:
        return [TextContent(type="text", text=f"{output}\n\n❌ Error:\n{stderr}")]
