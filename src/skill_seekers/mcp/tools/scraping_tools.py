"""
Scraping Tools Module for MCP Server

This module contains all scraping-related MCP tool implementations:
- estimate_pages_tool: Estimate page count before scraping
- scrape_docs_tool: Scrape documentation (legacy or unified)
- scrape_github_tool: Scrape GitHub repositories
- scrape_pdf_tool: Scrape PDF documentation
- scrape_codebase_tool: Analyze local codebase and extract code knowledge

Extracted from server.py for better modularity and organization.
"""

import json
import sys
from pathlib import Path
from typing import Any, List

# MCP types - with graceful fallback for testing
try:
    from mcp.types import TextContent
except ImportError:
    # Graceful degradation: Create a simple fallback class for testing
    class TextContent:
        """Fallback TextContent for when MCP is not installed"""
        def __init__(self, type: str, text: str):
            self.type = type
            self.text = text

# Path to CLI tools
CLI_DIR = Path(__file__).parent.parent.parent / "cli"


def run_subprocess_with_streaming(cmd: List[str], timeout: int = None) -> tuple:
    """
    Run subprocess with real-time output streaming.

    This solves the blocking issue where long-running processes (like scraping)
    would cause MCP to appear frozen. Now we stream output as it comes.

    Args:
        cmd: Command list to execute
        timeout: Optional timeout in seconds

    Returns:
        Tuple of (stdout, stderr, returncode)
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


async def estimate_pages_tool(args: dict) -> List[TextContent]:
    """
    Estimate page count from a config file.

    Performs fast preview without downloading content to estimate
    how many pages will be scraped.

    Args:
        args: Dictionary containing:
            - config_path (str): Path to config JSON file
            - max_discovery (int, optional): Maximum pages to discover (default: 1000)
            - unlimited (bool, optional): Remove discovery limit (default: False)

    Returns:
        List[TextContent]: Tool execution results
    """
    config_path = args["config_path"]
    max_discovery = args.get("max_discovery", 1000)
    unlimited = args.get("unlimited", False)

    # Handle unlimited mode
    if unlimited or max_discovery == -1:
        max_discovery = -1
        timeout = 1800  # 30 minutes for unlimited discovery
    else:
        # Estimate: 0.5s per page discovered
        timeout = max(300, max_discovery // 2)  # Minimum 5 minutes

    # Run estimate_pages.py
    cmd = [
        sys.executable,
        str(CLI_DIR / "estimate_pages.py"),
        config_path,
        "--max-discovery", str(max_discovery)
    ]

    progress_msg = f"🔄 Estimating page count...\n"
    progress_msg += f"⏱️ Maximum time: {timeout // 60} minutes\n\n"

    stdout, stderr, returncode = run_subprocess_with_streaming(cmd, timeout=timeout)

    output = progress_msg + stdout

    if returncode == 0:
        return [TextContent(type="text", text=output)]
    else:
        return [TextContent(type="text", text=f"{output}\n\n❌ Error:\n{stderr}")]


async def scrape_docs_tool(args: dict) -> List[TextContent]:
    """
    Scrape documentation and build skill.

    Auto-detects unified vs legacy format and routes to appropriate scraper.
    Supports both single-source (legacy) and unified multi-source configs.
    Creates SKILL.md and reference files.

    Args:
        args: Dictionary containing:
            - config_path (str): Path to config JSON file
            - unlimited (bool, optional): Remove page limit (default: False)
            - enhance_local (bool, optional): Open terminal for local enhancement (default: False)
            - skip_scrape (bool, optional): Skip scraping, use cached data (default: False)
            - dry_run (bool, optional): Preview without saving (default: False)
            - merge_mode (str, optional): Override merge mode for unified configs

    Returns:
        List[TextContent]: Tool execution results
    """
    config_path = args["config_path"]
    unlimited = args.get("unlimited", False)
    enhance_local = args.get("enhance_local", False)
    skip_scrape = args.get("skip_scrape", False)
    dry_run = args.get("dry_run", False)
    merge_mode = args.get("merge_mode")

    # Load config to detect format
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Detect if unified format (has 'sources' array)
    is_unified = 'sources' in config and isinstance(config['sources'], list)

    # Handle unlimited mode by modifying config temporarily
    if unlimited:
        # Set max_pages to None (unlimited)
        if is_unified:
            # For unified configs, set max_pages on documentation sources
            for source in config.get('sources', []):
                if source.get('type') == 'documentation':
                    source['max_pages'] = None
        else:
            # For legacy configs
            config['max_pages'] = None

        # Create temporary config file
        temp_config_path = config_path.replace('.json', '_unlimited_temp.json')
        with open(temp_config_path, 'w') as f:
            json.dump(config, f, indent=2)

        config_to_use = temp_config_path
    else:
        config_to_use = config_path

    # Choose scraper based on format
    if is_unified:
        scraper_script = "unified_scraper.py"
        progress_msg = f"🔄 Starting unified multi-source scraping...\n"
        progress_msg += f"📦 Config format: Unified (multiple sources)\n"
    else:
        scraper_script = "doc_scraper.py"
        progress_msg = f"🔄 Starting scraping process...\n"
        progress_msg += f"📦 Config format: Legacy (single source)\n"

    # Build command
    cmd = [
        sys.executable,
        str(CLI_DIR / scraper_script),
        "--config", config_to_use
    ]

    # Add merge mode for unified configs
    if is_unified and merge_mode:
        cmd.extend(["--merge-mode", merge_mode])

    # Add --fresh to avoid user input prompts when existing data found
    if not skip_scrape:
        cmd.append("--fresh")

    if enhance_local:
        cmd.append("--enhance-local")
    if skip_scrape:
        cmd.append("--skip-scrape")
    if dry_run:
        cmd.append("--dry-run")

    # Determine timeout based on operation type
    if dry_run:
        timeout = 300  # 5 minutes for dry run
    elif skip_scrape:
        timeout = 600  # 10 minutes for building from cache
    elif unlimited:
        timeout = None  # No timeout for unlimited mode (user explicitly requested)
    else:
        # Read config to estimate timeout
        try:
            if is_unified:
                # For unified configs, estimate based on all sources
                total_pages = 0
                for source in config.get('sources', []):
                    if source.get('type') == 'documentation':
                        total_pages += source.get('max_pages', 500)
                max_pages = total_pages or 500
            else:
                max_pages = config.get('max_pages', 500)

            # Estimate: 30s per page + buffer
            timeout = max(3600, max_pages * 35)  # Minimum 1 hour, or 35s per page
        except:
            timeout = 14400  # Default: 4 hours

    # Add progress message
    if timeout:
        progress_msg += f"⏱️ Maximum time allowed: {timeout // 60} minutes\n"
    else:
        progress_msg += f"⏱️ Unlimited mode - no timeout\n"
    progress_msg += f"📝 Progress will be shown below:\n\n"

    # Run scraper with streaming
    stdout, stderr, returncode = run_subprocess_with_streaming(cmd, timeout=timeout)

    # Clean up temporary config
    if unlimited and Path(config_to_use).exists():
        Path(config_to_use).unlink()

    output = progress_msg + stdout

    if returncode == 0:
        return [TextContent(type="text", text=output)]
    else:
        error_output = output + f"\n\n❌ Error:\n{stderr}"
        return [TextContent(type="text", text=error_output)]


async def scrape_pdf_tool(args: dict) -> List[TextContent]:
    """
    Scrape PDF documentation and build Claude skill.

    Extracts text, code, and images from PDF files and builds
    a skill package with organized references.

    Args:
        args: Dictionary containing:
            - config_path (str, optional): Path to PDF config JSON file
            - pdf_path (str, optional): Direct PDF path (alternative to config_path)
            - name (str, optional): Skill name (required with pdf_path)
            - description (str, optional): Skill description
            - from_json (str, optional): Build from extracted JSON file

    Returns:
        List[TextContent]: Tool execution results
    """
    config_path = args.get("config_path")
    pdf_path = args.get("pdf_path")
    name = args.get("name")
    description = args.get("description")
    from_json = args.get("from_json")

    # Build command
    cmd = [sys.executable, str(CLI_DIR / "pdf_scraper.py")]

    # Mode 1: Config file
    if config_path:
        cmd.extend(["--config", config_path])

    # Mode 2: Direct PDF
    elif pdf_path and name:
        cmd.extend(["--pdf", pdf_path, "--name", name])
        if description:
            cmd.extend(["--description", description])

    # Mode 3: From JSON
    elif from_json:
        cmd.extend(["--from-json", from_json])

    else:
        return [TextContent(type="text", text="❌ Error: Must specify --config, --pdf + --name, or --from-json")]

    # Run pdf_scraper.py with streaming (can take a while)
    timeout = 600  # 10 minutes for PDF extraction

    progress_msg = "📄 Scraping PDF documentation...\n"
    progress_msg += f"⏱️ Maximum time: {timeout // 60} minutes\n\n"

    stdout, stderr, returncode = run_subprocess_with_streaming(cmd, timeout=timeout)

    output = progress_msg + stdout

    if returncode == 0:
        return [TextContent(type="text", text=output)]
    else:
        return [TextContent(type="text", text=f"{output}\n\n❌ Error:\n{stderr}")]


async def scrape_github_tool(args: dict) -> List[TextContent]:
    """
    Scrape GitHub repository and build Claude skill.

    Extracts README, Issues, Changelog, Releases, and code structure
    from GitHub repositories to create comprehensive skills.

    Args:
        args: Dictionary containing:
            - repo (str, optional): GitHub repository (owner/repo)
            - config_path (str, optional): Path to GitHub config JSON file
            - name (str, optional): Skill name (default: repo name)
            - description (str, optional): Skill description
            - token (str, optional): GitHub personal access token
            - no_issues (bool, optional): Skip GitHub issues extraction (default: False)
            - no_changelog (bool, optional): Skip CHANGELOG extraction (default: False)
            - no_releases (bool, optional): Skip releases extraction (default: False)
            - max_issues (int, optional): Maximum issues to fetch (default: 100)
            - scrape_only (bool, optional): Only scrape, don't build skill (default: False)

    Returns:
        List[TextContent]: Tool execution results
    """
    repo = args.get("repo")
    config_path = args.get("config_path")
    name = args.get("name")
    description = args.get("description")
    token = args.get("token")
    no_issues = args.get("no_issues", False)
    no_changelog = args.get("no_changelog", False)
    no_releases = args.get("no_releases", False)
    max_issues = args.get("max_issues", 100)
    scrape_only = args.get("scrape_only", False)

    # Build command
    cmd = [sys.executable, str(CLI_DIR / "github_scraper.py")]

    # Mode 1: Config file
    if config_path:
        cmd.extend(["--config", config_path])

    # Mode 2: Direct repo
    elif repo:
        cmd.extend(["--repo", repo])
        if name:
            cmd.extend(["--name", name])
        if description:
            cmd.extend(["--description", description])
        if token:
            cmd.extend(["--token", token])
        if no_issues:
            cmd.append("--no-issues")
        if no_changelog:
            cmd.append("--no-changelog")
        if no_releases:
            cmd.append("--no-releases")
        if max_issues != 100:
            cmd.extend(["--max-issues", str(max_issues)])
        if scrape_only:
            cmd.append("--scrape-only")

    else:
        return [TextContent(type="text", text="❌ Error: Must specify --repo or --config")]

    # Run github_scraper.py with streaming (can take a while)
    timeout = 600  # 10 minutes for GitHub scraping

    progress_msg = "🐙 Scraping GitHub repository...\n"
    progress_msg += f"⏱️ Maximum time: {timeout // 60} minutes\n\n"

    stdout, stderr, returncode = run_subprocess_with_streaming(cmd, timeout=timeout)

    output = progress_msg + stdout

    if returncode == 0:
        return [TextContent(type="text", text=output)]
    else:
        return [TextContent(type="text", text=f"{output}\n\n❌ Error:\n{stderr}")]


async def scrape_codebase_tool(args: dict) -> List[TextContent]:
    """
    Analyze local codebase and extract code knowledge.

    Walks directory tree, analyzes code files, extracts signatures,
    docstrings, and optionally generates API reference documentation
    and dependency graphs.

    Args:
        args: Dictionary containing:
            - directory (str): Directory to analyze
            - output (str, optional): Output directory for results (default: output/codebase/)
            - depth (str, optional): Analysis depth - surface, deep, full (default: deep)
            - languages (str, optional): Comma-separated languages (e.g., "Python,JavaScript,C++")
            - file_patterns (str, optional): Comma-separated file patterns (e.g., "*.py,src/**/*.js")
            - build_api_reference (bool, optional): Generate API reference markdown (default: False)
            - build_dependency_graph (bool, optional): Generate dependency graph and detect circular dependencies (default: False)

    Returns:
        List[TextContent]: Tool execution results

    Example:
        scrape_codebase(
            directory="/path/to/repo",
            depth="deep",
            build_api_reference=True,
            build_dependency_graph=True
        )
    """
    directory = args.get("directory")
    if not directory:
        return [TextContent(type="text", text="❌ Error: directory parameter is required")]

    output = args.get("output", "output/codebase/")
    depth = args.get("depth", "deep")
    languages = args.get("languages", "")
    file_patterns = args.get("file_patterns", "")
    build_api_reference = args.get("build_api_reference", False)
    build_dependency_graph = args.get("build_dependency_graph", False)

    # Build command
    cmd = [sys.executable, "-m", "skill_seekers.cli.codebase_scraper"]
    cmd.extend(["--directory", directory])

    if output:
        cmd.extend(["--output", output])
    if depth:
        cmd.extend(["--depth", depth])
    if languages:
        cmd.extend(["--languages", languages])
    if file_patterns:
        cmd.extend(["--file-patterns", file_patterns])
    if build_api_reference:
        cmd.append("--build-api-reference")
    if build_dependency_graph:
        cmd.append("--build-dependency-graph")

    timeout = 600  # 10 minutes for codebase analysis

    progress_msg = "🔍 Analyzing local codebase...\n"
    progress_msg += f"📁 Directory: {directory}\n"
    progress_msg += f"⏱️ Maximum time: {timeout // 60} minutes\n\n"

    stdout, stderr, returncode = run_subprocess_with_streaming(cmd, timeout=timeout)

    output_text = progress_msg + stdout

    if returncode == 0:
        return [TextContent(type="text", text=output_text)]
    else:
        return [TextContent(type="text", text=f"{output_text}\n\n❌ Error:\n{stderr}")]


async def detect_patterns_tool(args: dict) -> List[TextContent]:
    """
    Detect design patterns in source code.

    Analyzes source files or directories to detect common design patterns
    (Singleton, Factory, Observer, Strategy, Decorator, Builder, Adapter,
    Command, Template Method, Chain of Responsibility).

    Supports 9 languages: Python, JavaScript, TypeScript, C++, C, C#,
    Go, Rust, Java, Ruby, PHP.

    Args:
        args: Dictionary containing:
            - file (str, optional): Single file to analyze
            - directory (str, optional): Directory to analyze (analyzes all source files)
            - output (str, optional): Output directory for JSON results
            - depth (str, optional): Detection depth - surface, deep, full (default: deep)
            - json (bool, optional): Output JSON format (default: False)

    Returns:
        List[TextContent]: Pattern detection results

    Example:
        detect_patterns(file="src/database.py", depth="deep")
        detect_patterns(directory="src/", output="patterns/", json=True)
    """
    file_path = args.get("file")
    directory = args.get("directory")

    if not file_path and not directory:
        return [TextContent(type="text", text="❌ Error: Must specify either 'file' or 'directory' parameter")]

    output = args.get("output", "")
    depth = args.get("depth", "deep")
    json_output = args.get("json", False)

    # Build command
    cmd = [sys.executable, "-m", "skill_seekers.cli.pattern_recognizer"]

    if file_path:
        cmd.extend(["--file", file_path])
    if directory:
        cmd.extend(["--directory", directory])
    if output:
        cmd.extend(["--output", output])
    if depth:
        cmd.extend(["--depth", depth])
    if json_output:
        cmd.append("--json")

    timeout = 300  # 5 minutes for pattern detection

    progress_msg = "🔍 Detecting design patterns...\n"
    if file_path:
        progress_msg += f"📄 File: {file_path}\n"
    if directory:
        progress_msg += f"📁 Directory: {directory}\n"
    progress_msg += f"🎯 Detection depth: {depth}\n"
    progress_msg += f"⏱️ Maximum time: {timeout // 60} minutes\n\n"

    stdout, stderr, returncode = run_subprocess_with_streaming(cmd, timeout=timeout)

    output_text = progress_msg + stdout

    if returncode == 0:
        return [TextContent(type="text", text=output_text)]
    else:
        return [TextContent(type="text", text=f"{output_text}\n\n❌ Error:\n{stderr}")]
