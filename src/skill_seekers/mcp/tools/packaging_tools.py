"""
Packaging tools for MCP server.

This module contains tools for packaging, uploading, and installing skills.
Extracted from server.py for better modularity.
"""

import asyncio
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, List, Tuple

try:
    from mcp.types import TextContent
except ImportError:
    TextContent = None  # Graceful degradation


# Path to CLI tools
CLI_DIR = Path(__file__).parent.parent.parent / "cli"


def run_subprocess_with_streaming(cmd: List[str], timeout: int = None) -> Tuple[str, str, int]:
    """
    Run subprocess with real-time output streaming.

    This solves the blocking issue where long-running processes (like scraping)
    would cause MCP to appear frozen. Now we stream output as it comes.

    Args:
        cmd: Command to run as list of strings
        timeout: Maximum time to wait in seconds (None for no timeout)

    Returns:
        Tuple of (stdout, stderr, returncode)
    """
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


async def package_skill_tool(args: dict) -> List[TextContent]:
    """
    Package skill to .zip and optionally auto-upload.

    Args:
        args: Dictionary with:
            - skill_dir (str): Path to skill directory (e.g., output/react/)
            - auto_upload (bool): Try to upload automatically if API key is available (default: True)

    Returns:
        List of TextContent with packaging results
    """
    skill_dir = args["skill_dir"]
    auto_upload = args.get("auto_upload", True)

    # Check if API key exists - only upload if available
    has_api_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()
    should_upload = auto_upload and has_api_key

    # Run package_skill.py
    cmd = [
        sys.executable,
        str(CLI_DIR / "package_skill.py"),
        skill_dir,
        "--no-open",  # Don't open folder in MCP context
        "--skip-quality-check"  # Skip interactive quality checks in MCP context
    ]

    # Add upload flag only if we have API key
    if should_upload:
        cmd.append("--upload")

    # Timeout: 5 minutes for packaging + upload
    timeout = 300

    progress_msg = "📦 Packaging skill...\n"
    if should_upload:
        progress_msg += "📤 Will auto-upload if successful\n"
    progress_msg += f"⏱️ Maximum time: {timeout // 60} minutes\n\n"

    stdout, stderr, returncode = run_subprocess_with_streaming(cmd, timeout=timeout)

    output = progress_msg + stdout

    if returncode == 0:
        if should_upload:
            # Upload succeeded
            output += "\n\n✅ Skill packaged and uploaded automatically!"
            output += "\n   Your skill is now available in Claude!"
        elif auto_upload and not has_api_key:
            # User wanted upload but no API key
            output += "\n\n📝 Skill packaged successfully!"
            output += "\n"
            output += "\n💡 To enable automatic upload:"
            output += "\n   1. Get API key from https://console.anthropic.com/"
            output += "\n   2. Set: export ANTHROPIC_API_KEY=sk-ant-..."
            output += "\n"
            output += "\n📤 Manual upload:"
            output += "\n   1. Find the .zip file in your output/ folder"
            output += "\n   2. Go to https://claude.ai/skills"
            output += "\n   3. Click 'Upload Skill' and select the .zip file"
        else:
            # auto_upload=False, just packaged
            output += "\n\n✅ Skill packaged successfully!"
            output += "\n   Upload manually to https://claude.ai/skills"

        return [TextContent(type="text", text=output)]
    else:
        return [TextContent(type="text", text=f"{output}\n\n❌ Error:\n{stderr}")]


async def upload_skill_tool(args: dict) -> List[TextContent]:
    """
    Upload skill .zip to Claude.

    Args:
        args: Dictionary with:
            - skill_zip (str): Path to skill .zip file (e.g., output/react.zip)

    Returns:
        List of TextContent with upload results
    """
    skill_zip = args["skill_zip"]

    # Run upload_skill.py
    cmd = [
        sys.executable,
        str(CLI_DIR / "upload_skill.py"),
        skill_zip
    ]

    # Timeout: 5 minutes for upload
    timeout = 300

    progress_msg = "📤 Uploading skill to Claude...\n"
    progress_msg += f"⏱️ Maximum time: {timeout // 60} minutes\n\n"

    stdout, stderr, returncode = run_subprocess_with_streaming(cmd, timeout=timeout)

    output = progress_msg + stdout

    if returncode == 0:
        return [TextContent(type="text", text=output)]
    else:
        return [TextContent(type="text", text=f"{output}\n\n❌ Error:\n{stderr}")]


async def install_skill_tool(args: dict) -> List[TextContent]:
    """
    Complete skill installation workflow.

    Orchestrates the complete workflow:
        1. Fetch config (if config_name provided)
        2. Scrape documentation
        3. AI Enhancement (MANDATORY - no skip option)
        4. Package to .zip
        5. Upload to Claude (optional)

    Args:
        args: Dictionary with:
            - config_name (str, optional): Config to fetch from API (mutually exclusive with config_path)
            - config_path (str, optional): Path to existing config (mutually exclusive with config_name)
            - destination (str): Output directory (default: "output")
            - auto_upload (bool): Upload after packaging (default: True)
            - unlimited (bool): Remove page limits (default: False)
            - dry_run (bool): Preview only (default: False)

    Returns:
        List of TextContent with workflow progress and results
    """
    # Import these here to avoid circular imports
    from .scraping_tools import scrape_docs_tool
    from .config_tools import fetch_config_tool

    # Extract and validate inputs
    config_name = args.get("config_name")
    config_path = args.get("config_path")
    destination = args.get("destination", "output")
    auto_upload = args.get("auto_upload", True)
    unlimited = args.get("unlimited", False)
    dry_run = args.get("dry_run", False)

    # Validation: Must provide exactly one of config_name or config_path
    if not config_name and not config_path:
        return [TextContent(
            type="text",
            text="❌ Error: Must provide either config_name or config_path\n\nExamples:\n  install_skill(config_name='react')\n  install_skill(config_path='configs/custom.json')"
        )]

    if config_name and config_path:
        return [TextContent(
            type="text",
            text="❌ Error: Cannot provide both config_name and config_path\n\nChoose one:\n  - config_name: Fetch from API (e.g., 'react')\n  - config_path: Use existing file (e.g., 'configs/custom.json')"
        )]

    # Initialize output
    output_lines = []
    output_lines.append("🚀 SKILL INSTALLATION WORKFLOW")
    output_lines.append("=" * 70)
    output_lines.append("")

    if dry_run:
        output_lines.append("🔍 DRY RUN MODE - Preview only, no actions taken")
        output_lines.append("")

    # Track workflow state
    workflow_state = {
        'config_path': config_path,
        'skill_name': None,
        'skill_dir': None,
        'zip_path': None,
        'phases_completed': []
    }

    try:
        # ===== PHASE 1: Fetch Config (if needed) =====
        if config_name:
            output_lines.append("📥 PHASE 1/5: Fetch Config")
            output_lines.append("-" * 70)
            output_lines.append(f"Config: {config_name}")
            output_lines.append(f"Destination: {destination}/")
            output_lines.append("")

            if not dry_run:
                # Call fetch_config_tool directly
                fetch_result = await fetch_config_tool({
                    "config_name": config_name,
                    "destination": destination
                })

                # Parse result to extract config path
                fetch_output = fetch_result[0].text
                output_lines.append(fetch_output)
                output_lines.append("")

                # Extract config path from output
                # Expected format: "✅ Config saved to: configs/react.json"
                match = re.search(r"saved to:\s*(.+\.json)", fetch_output)
                if match:
                    workflow_state['config_path'] = match.group(1).strip()
                    output_lines.append(f"✅ Config fetched: {workflow_state['config_path']}")
                else:
                    return [TextContent(type="text", text="\n".join(output_lines) + "\n\n❌ Failed to fetch config")]

                workflow_state['phases_completed'].append('fetch_config')
            else:
                output_lines.append("  [DRY RUN] Would fetch config from API")
                workflow_state['config_path'] = f"{destination}/{config_name}.json"

            output_lines.append("")

        # ===== PHASE 2: Scrape Documentation =====
        phase_num = "2/5" if config_name else "1/4"
        output_lines.append(f"📄 PHASE {phase_num}: Scrape Documentation")
        output_lines.append("-" * 70)
        output_lines.append(f"Config: {workflow_state['config_path']}")
        output_lines.append(f"Unlimited mode: {unlimited}")
        output_lines.append("")

        if not dry_run:
            # Load config to get skill name
            try:
                with open(workflow_state['config_path'], 'r') as f:
                    config = json.load(f)
                    workflow_state['skill_name'] = config.get('name', 'unknown')
            except Exception as e:
                return [TextContent(type="text", text="\n".join(output_lines) + f"\n\n❌ Failed to read config: {str(e)}")]

            # Call scrape_docs_tool (does NOT include enhancement)
            output_lines.append("Scraping documentation (this may take 20-45 minutes)...")
            output_lines.append("")

            scrape_result = await scrape_docs_tool({
                "config_path": workflow_state['config_path'],
                "unlimited": unlimited,
                "enhance_local": False,  # Enhancement is separate phase
                "skip_scrape": False,
                "dry_run": False
            })

            scrape_output = scrape_result[0].text
            output_lines.append(scrape_output)
            output_lines.append("")

            # Check for success
            if "❌" in scrape_output:
                return [TextContent(type="text", text="\n".join(output_lines) + "\n\n❌ Scraping failed - see error above")]

            workflow_state['skill_dir'] = f"{destination}/{workflow_state['skill_name']}"
            workflow_state['phases_completed'].append('scrape_docs')
        else:
            output_lines.append("  [DRY RUN] Would scrape documentation")
            workflow_state['skill_name'] = "example"
            workflow_state['skill_dir'] = f"{destination}/example"

        output_lines.append("")

        # ===== PHASE 3: AI Enhancement (MANDATORY) =====
        phase_num = "3/5" if config_name else "2/4"
        output_lines.append(f"✨ PHASE {phase_num}: AI Enhancement (MANDATORY)")
        output_lines.append("-" * 70)
        output_lines.append("⚠️  Enhancement is REQUIRED for quality (3/10→9/10 boost)")
        output_lines.append(f"Skill directory: {workflow_state['skill_dir']}")
        output_lines.append("Mode: Headless (runs in background)")
        output_lines.append("Estimated time: 30-60 seconds")
        output_lines.append("")

        if not dry_run:
            # Run enhance_skill_local in headless mode
            # Build command directly
            cmd = [
                sys.executable,
                str(CLI_DIR / "enhance_skill_local.py"),
                workflow_state['skill_dir']
                # Headless is default, no flag needed
            ]

            timeout = 900  # 15 minutes max for enhancement

            output_lines.append("Running AI enhancement...")

            stdout, stderr, returncode = run_subprocess_with_streaming(cmd, timeout=timeout)

            if returncode != 0:
                output_lines.append(f"\n❌ Enhancement failed (exit code {returncode}):")
                output_lines.append(stderr if stderr else stdout)
                return [TextContent(type="text", text="\n".join(output_lines))]

            output_lines.append(stdout)
            workflow_state['phases_completed'].append('enhance_skill')
        else:
            output_lines.append("  [DRY RUN] Would enhance SKILL.md with Claude Code")

        output_lines.append("")

        # ===== PHASE 4: Package Skill =====
        phase_num = "4/5" if config_name else "3/4"
        output_lines.append(f"📦 PHASE {phase_num}: Package Skill")
        output_lines.append("-" * 70)
        output_lines.append(f"Skill directory: {workflow_state['skill_dir']}")
        output_lines.append("")

        if not dry_run:
            # Call package_skill_tool (auto_upload=False, we handle upload separately)
            package_result = await package_skill_tool({
                "skill_dir": workflow_state['skill_dir'],
                "auto_upload": False  # We handle upload in next phase
            })

            package_output = package_result[0].text
            output_lines.append(package_output)
            output_lines.append("")

            # Extract zip path from output
            # Expected format: "Saved to: output/react.zip"
            match = re.search(r"Saved to:\s*(.+\.zip)", package_output)
            if match:
                workflow_state['zip_path'] = match.group(1).strip()
            else:
                # Fallback: construct zip path
                workflow_state['zip_path'] = f"{destination}/{workflow_state['skill_name']}.zip"

            workflow_state['phases_completed'].append('package_skill')
        else:
            output_lines.append("  [DRY RUN] Would package to .zip file")
            workflow_state['zip_path'] = f"{destination}/{workflow_state['skill_name']}.zip"

        output_lines.append("")

        # ===== PHASE 5: Upload (Optional) =====
        if auto_upload:
            phase_num = "5/5" if config_name else "4/4"
            output_lines.append(f"📤 PHASE {phase_num}: Upload to Claude")
            output_lines.append("-" * 70)
            output_lines.append(f"Zip file: {workflow_state['zip_path']}")
            output_lines.append("")

            # Check for API key
            has_api_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()

            if not dry_run:
                if has_api_key:
                    # Call upload_skill_tool
                    upload_result = await upload_skill_tool({
                        "skill_zip": workflow_state['zip_path']
                    })

                    upload_output = upload_result[0].text
                    output_lines.append(upload_output)

                    workflow_state['phases_completed'].append('upload_skill')
                else:
                    output_lines.append("⚠️  ANTHROPIC_API_KEY not set - skipping upload")
                    output_lines.append("")
                    output_lines.append("To enable automatic upload:")
                    output_lines.append("  1. Get API key from https://console.anthropic.com/")
                    output_lines.append("  2. Set: export ANTHROPIC_API_KEY=sk-ant-...")
                    output_lines.append("")
                    output_lines.append("📤 Manual upload:")
                    output_lines.append("  1. Go to https://claude.ai/skills")
                    output_lines.append("  2. Click 'Upload Skill'")
                    output_lines.append(f"  3. Select: {workflow_state['zip_path']}")
            else:
                output_lines.append("  [DRY RUN] Would upload to Claude (if API key set)")

            output_lines.append("")

        # ===== WORKFLOW SUMMARY =====
        output_lines.append("=" * 70)
        output_lines.append("✅ WORKFLOW COMPLETE")
        output_lines.append("=" * 70)
        output_lines.append("")

        if not dry_run:
            output_lines.append("Phases completed:")
            for phase in workflow_state['phases_completed']:
                output_lines.append(f"  ✓ {phase}")
            output_lines.append("")

            output_lines.append("📁 Output:")
            output_lines.append(f"  Skill directory: {workflow_state['skill_dir']}")
            if workflow_state['zip_path']:
                output_lines.append(f"  Skill package: {workflow_state['zip_path']}")
            output_lines.append("")

            if auto_upload and has_api_key:
                output_lines.append("🎉 Your skill is now available in Claude!")
                output_lines.append("   Go to https://claude.ai/skills to use it")
            elif auto_upload:
                output_lines.append("📝 Manual upload required (see instructions above)")
            else:
                output_lines.append("📤 To upload:")
                output_lines.append("   skill-seekers upload " + workflow_state['zip_path'])
        else:
            output_lines.append("This was a dry run. No actions were taken.")
            output_lines.append("")
            output_lines.append("To execute for real, remove the --dry-run flag:")
            if config_name:
                output_lines.append(f"  install_skill(config_name='{config_name}')")
            else:
                output_lines.append(f"  install_skill(config_path='{config_path}')")

        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        output_lines.append("")
        output_lines.append(f"❌ Workflow failed: {str(e)}")
        output_lines.append("")
        output_lines.append("Phases completed before failure:")
        for phase in workflow_state['phases_completed']:
            output_lines.append(f"  ✓ {phase}")
        return [TextContent(type="text", text="\n".join(output_lines))]
