"""
Packaging tools for MCP server.

This module contains tools for packaging, uploading, and installing skills.
Extracted from server.py for better modularity.
"""

import json
import os
import re
import sys
from pathlib import Path

# Still used by enhance_skill_tool and install_skill_tool's enhancement phase,
# which deliberately stay subprocess-based (they spawn a LOCAL coding agent).
from skill_seekers.mcp.tools.subprocess_utils import run_subprocess_with_streaming

from skill_seekers.mcp.tools._common import (
    CLI_DIR,
    TextContent,
    run_cli_main,
    run_cli_tool,
    text_response,
)


# Path to CLI tools


async def package_skill_tool(args: dict) -> list[TextContent]:
    """
    Package skill for target LLM platform and optionally auto-upload.

    Args:
        args: Dictionary with:
            - skill_dir (str): Path to skill directory (e.g., output/react/)
            - auto_upload (bool): Try to upload automatically if API key is available (default: True)
            - target (str): Target platform (default: 'auto')
                           Options: 'auto', 'claude', 'gemini', 'openai', 'markdown'

    Returns:
        List of TextContent with packaging results

    Note:
        Runs package_skill.main() in-process (Phase 5d). The old subprocess
        timeout no longer applies — the "Maximum time" line in the output is
        advisory only. On a non-zero exit the output keeps the "❌ Error:"
        marker that install_skill_tool sniffs to abort before upload.
    """
    from skill_seekers.cli.adaptors import get_adaptor

    skill_dir = args["skill_dir"]
    auto_upload = args.get("auto_upload", True)
    target = args.get("target", "auto")
    if target == "auto":
        from skill_seekers.cli.agent_client import AgentClient

        target = AgentClient.detect_default_target()

    # Get platform adaptor
    try:
        adaptor = get_adaptor(target)
    except ValueError as e:
        return [
            TextContent(
                type="text",
                text=f"❌ Invalid platform: {str(e)}\n\nSupported platforms: claude, gemini, openai, markdown",
            )
        ]

    # Check if platform-specific API key exists - only upload if available
    env_var_name = adaptor.get_env_var_name()
    has_api_key = os.environ.get(env_var_name, "").strip() if env_var_name else False
    should_upload = auto_upload and has_api_key

    # Run package_skill.main() in-process with the same argv the subprocess got
    argv = [
        skill_dir,
        "--no-open",  # Don't open folder in MCP context
        "--skip-quality-check",  # Skip interactive quality checks in MCP context
        "--target",
        target,  # Add target platform
    ]

    # Add upload flag only if we have API key
    if should_upload:
        argv.append("--upload")

    # Advisory only (output text); the in-process call is unbounded
    timeout = 300

    progress_msg = f"📦 Packaging skill for {adaptor.PLATFORM_NAME}...\n"
    if should_upload:
        progress_msg += f"📤 Will auto-upload to {adaptor.PLATFORM_NAME} if successful\n"
    progress_msg += f"⏱️ Maximum time: {timeout // 60} minutes\n\n"

    from skill_seekers.cli import package_skill

    stdout, stderr, returncode = run_cli_main(package_skill.main, argv)

    output = progress_msg + stdout

    if returncode == 0:
        if should_upload:
            # Upload succeeded
            output += f"\n\n✅ Skill packaged and uploaded to {adaptor.PLATFORM_NAME}!"
            if target == "claude":
                output += "\n   Your skill is now available in Claude!"
                output += "\n   Go to https://claude.ai/skills to use it"
            elif target == "gemini":
                output += "\n   Your skill is now available in Gemini!"
                output += "\n   Go to https://aistudio.google.com/ to use it"
            elif target == "openai":
                output += "\n   Your assistant is now available in OpenAI!"
                output += "\n   Go to https://platform.openai.com/assistants/ to use it"
        elif auto_upload and not has_api_key:
            # User wanted upload but no API key
            output += f"\n\n📝 Skill packaged successfully for {adaptor.PLATFORM_NAME}!"
            output += "\n"
            output += "\n💡 To enable automatic upload:"
            if target == "claude":
                output += "\n   1. Get API key from https://console.anthropic.com/"
                output += "\n   2. Set: export ANTHROPIC_API_KEY=sk-ant-..."
                output += "\n\n📤 Manual upload:"
                output += "\n   1. Find the .zip file in your output/ folder"
                output += "\n   2. Go to https://claude.ai/skills"
                output += "\n   3. Click 'Upload Skill' and select the .zip file"
            elif target == "gemini":
                output += "\n   1. Get API key from https://aistudio.google.com/"
                output += "\n   2. Set: export GOOGLE_API_KEY=AIza..."
                output += "\n\n📤 Manual upload:"
                output += "\n   1. Go to https://aistudio.google.com/"
                output += "\n   2. Upload the .tar.gz file from your output/ folder"
            elif target == "openai":
                output += "\n   1. Get API key from https://platform.openai.com/"
                output += "\n   2. Set: export OPENAI_API_KEY=sk-proj-..."
                output += "\n\n📤 Manual upload:"
                output += "\n   1. Use OpenAI Assistants API"
                output += "\n   2. Upload the .zip file from your output/ folder"
            elif target == "markdown":
                output += "\n   (No API key needed - markdown is export only)"
                output += "\n   Package created for manual distribution"
        else:
            # auto_upload=False, just packaged
            output += f"\n\n✅ Skill packaged successfully for {adaptor.PLATFORM_NAME}!"
            if target == "claude":
                output += "\n   Upload manually to https://claude.ai/skills"
            elif target == "gemini":
                output += "\n   Upload manually to https://aistudio.google.com/"
            elif target == "openai":
                output += "\n   Upload manually via OpenAI Assistants API"
            elif target == "markdown":
                output += "\n   Package ready for manual distribution"

        return [TextContent(type="text", text=output)]
    else:
        return [TextContent(type="text", text=f"{output}\n\n❌ Error:\n{stderr}")]


async def upload_skill_tool(args: dict) -> list[TextContent]:
    """
    Upload skill package to target LLM platform.

    Args:
        args: Dictionary with:
            - skill_zip (str): Path to skill package (.zip or .tar.gz)
            - target (str): Target platform (default: 'auto')
                           Options: 'auto', 'claude', 'gemini', 'openai'
                           Note: 'markdown' does not support upload
            - api_key (str, optional): API key (uses env var if not provided)

    Returns:
        List of TextContent with upload results

    Note:
        Runs upload_skill.main() in-process (Phase 5d) — the upload itself is
        a non-interactive API call (upload_skill_api), so no subprocess is
        needed. The old subprocess timeout no longer applies — the
        "Maximum time" line in the output is advisory only.
    """
    from skill_seekers.cli.adaptors import get_adaptor

    skill_zip = args["skill_zip"]
    target = args.get("target", "auto")
    if target == "auto":
        from skill_seekers.cli.agent_client import AgentClient

        target = AgentClient.detect_default_target()
    api_key = args.get("api_key")

    # Get platform adaptor
    try:
        adaptor = get_adaptor(target)
    except ValueError as e:
        return [
            TextContent(
                type="text",
                text=f"❌ Invalid platform: {str(e)}\n\nSupported platforms: claude, gemini, openai",
            )
        ]

    # Check if upload is supported
    if target == "markdown":
        return [
            TextContent(
                type="text",
                text="❌ Markdown export does not support upload. Use the packaged file manually.",
            )
        ]

    # Run upload_skill.main() in-process with the same argv the subprocess got
    argv = [skill_zip, "--target", target]

    # Add API key if provided
    if api_key:
        argv.extend(["--api-key", api_key])

    # Advisory only (output text); the in-process call is unbounded
    timeout = 300

    progress_msg = f"📤 Uploading skill to {adaptor.PLATFORM_NAME}...\n"
    progress_msg += f"⏱️ Maximum time: {timeout // 60} minutes\n\n"

    from skill_seekers.cli import upload_skill

    return run_cli_tool(upload_skill.main, argv, progress_msg)


async def enhance_skill_tool(args: dict) -> list[TextContent]:
    """
    Enhance SKILL.md with AI using target platform's model.

    Args:
        args: Dictionary with:
            - skill_dir (str): Path to skill directory
            - target (str): Target platform (default: 'auto')
                           Options: 'auto', 'claude', 'gemini', 'openai'
                           Note: 'markdown' does not support enhancement
            - mode (str): Enhancement mode (default: 'local')
                         'local': Uses AI coding agent (no API key)
                         'api': Uses platform API (requires API key)
            - api_key (str, optional): API key for 'api' mode

    Returns:
        List of TextContent with enhancement results

    Note:
        Phase 5d deliberately did NOT migrate the 'local' mode to in-process:
        enhance_skill_local spawns a LOCAL coding agent (long-running,
        fork-bomb-guard semantics — the agent must be a real child process so
        recursion guards and timeouts apply). It stays on
        run_subprocess_with_streaming.
    """
    from skill_seekers.cli.adaptors import get_adaptor

    skill_dir = Path(args.get("skill_dir"))
    target = args.get("target", "auto")
    if target == "auto":
        from skill_seekers.cli.agent_client import AgentClient

        target = AgentClient.detect_default_target()
    mode = args.get("mode", "local")
    api_key = args.get("api_key")

    # Validate skill directory
    if not skill_dir.exists():
        return [TextContent(type="text", text=f"❌ Skill directory not found: {skill_dir}")]

    if not (skill_dir / "SKILL.md").exists():
        return [TextContent(type="text", text=f"❌ SKILL.md not found in {skill_dir}")]

    # Get platform adaptor
    try:
        adaptor = get_adaptor(target)
    except ValueError as e:
        return [
            TextContent(
                type="text",
                text=f"❌ Invalid platform: {str(e)}\n\nSupported platforms: claude, gemini, openai",
            )
        ]

    # Check if enhancement is supported
    if not adaptor.supports_enhancement():
        return [
            TextContent(
                type="text", text=f"❌ {adaptor.PLATFORM_NAME} does not support AI enhancement"
            )
        ]

    output_lines = []
    output_lines.append(f"🚀 Enhancing skill with {adaptor.PLATFORM_NAME}")
    output_lines.append("-" * 70)
    output_lines.append(f"Skill directory: {skill_dir}")
    output_lines.append(f"Mode: {mode}")
    output_lines.append("")

    if mode == "local":
        # Use local enhancement (AI coding agent)
        output_lines.append("Using AI coding agent (local, no API key required)")
        output_lines.append("Running enhancement in headless mode...")
        output_lines.append("")

        cmd = [sys.executable, str(CLI_DIR / "enhance_skill_local.py"), str(skill_dir)]

        try:
            stdout, stderr, returncode = run_subprocess_with_streaming(cmd, timeout=900)

            if returncode == 0:
                output_lines.append(stdout)
                output_lines.append("")
                output_lines.append("✅ Enhancement complete!")
                output_lines.append(f"Enhanced SKILL.md: {skill_dir / 'SKILL.md'}")
                output_lines.append(f"Backup: {skill_dir / 'SKILL.md.backup'}")
            else:
                output_lines.append(f"❌ Enhancement failed (exit code {returncode})")
                output_lines.append(stderr if stderr else stdout)

        except Exception as e:
            output_lines.append(f"❌ Error: {str(e)}")

    elif mode == "api":
        # Use API enhancement
        output_lines.append(f"Using {adaptor.PLATFORM_NAME} API")

        # Get API key
        if not api_key:
            env_var = adaptor.get_env_var_name()
            api_key = os.environ.get(env_var)

            if not api_key:
                return [
                    TextContent(
                        type="text",
                        text=f"❌ {env_var} not set. Set API key or pass via api_key parameter.",
                    )
                ]

        # Validate API key
        if not adaptor.validate_api_key(api_key):
            return [
                TextContent(
                    type="text", text=f"❌ Invalid API key format for {adaptor.PLATFORM_NAME}"
                )
            ]

        output_lines.append("Calling API for enhancement...")
        output_lines.append("")

        try:
            success = adaptor.enhance(skill_dir, api_key)

            if success:
                output_lines.append("✅ Enhancement complete!")
                output_lines.append(f"Enhanced SKILL.md: {skill_dir / 'SKILL.md'}")
                output_lines.append(f"Backup: {skill_dir / 'SKILL.md.backup'}")
            else:
                output_lines.append("❌ Enhancement failed")

        except Exception as e:
            output_lines.append(f"❌ Error: {str(e)}")

    else:
        return [TextContent(type="text", text=f"❌ Invalid mode: {mode}. Use 'local' or 'api'")]

    return [TextContent(type="text", text="\n".join(output_lines))]


async def install_skill_tool(args: dict) -> list[TextContent]:
    """
    Complete skill installation workflow.

    Orchestrates the complete workflow:
        1. Fetch config (if config_name provided)
        2. Scrape documentation
        3. AI Enhancement (MANDATORY - no skip option)
        4. Package for target platform (ZIP or tar.gz)
        5. Upload to target platform (optional)

    Args:
        args: Dictionary with:
            - config_name (str, optional): Config to fetch from API (mutually exclusive with config_path)
            - config_path (str, optional): Path to existing config (mutually exclusive with config_name)
            - destination (str): Output directory (default: "output")
            - auto_upload (bool): Upload after packaging (default: True)
            - unlimited (bool): Remove page limits (default: False)
            - dry_run (bool): Preview only (default: False)
            - target (str): Target LLM platform (default: "auto")

    Returns:
        List of TextContent with workflow progress and results
    """
    # Import these here to avoid circular imports
    from skill_seekers.cli.adaptors import get_adaptor

    from .scraping_tools import scrape_docs_tool
    from .source_tools import fetch_config_tool

    # Extract and validate inputs
    config_name = args.get("config_name")
    config_path = args.get("config_path")
    destination = args.get("destination", "output")
    auto_upload = args.get("auto_upload", True)
    unlimited = args.get("unlimited", False)
    dry_run = args.get("dry_run", False)
    target = args.get("target", "auto")
    marketplace_arg = args.get("marketplace")
    marketplace_category = args.get("marketplace_category", "development")
    create_branch = args.get("create_branch", False)
    if target == "auto":
        from skill_seekers.cli.agent_client import AgentClient

        target = AgentClient.detect_default_target()

    # Get platform adaptor
    try:
        adaptor = get_adaptor(target)
    except ValueError as e:
        return [
            TextContent(
                type="text",
                text=f"❌ Error: {str(e)}\n\nSupported platforms: claude, gemini, openai, markdown",
            )
        ]

    # Validation: Must provide exactly one of config_name or config_path
    if not config_name and not config_path:
        return [
            TextContent(
                type="text",
                text="❌ Error: Must provide either config_name or config_path\n\nExamples:\n  install_skill(config_name='react')\n  install_skill(config_path='configs/custom.json')",
            )
        ]

    if config_name and config_path:
        return [
            TextContent(
                type="text",
                text="❌ Error: Cannot provide both config_name and config_path\n\nChoose one:\n  - config_name: Fetch from API (e.g., 'react')\n  - config_path: Use existing file (e.g., 'configs/custom.json')",
            )
        ]

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
        "config_path": config_path,
        "skill_name": None,
        "skill_dir": None,
        "zip_path": None,
        "phases_completed": [],
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
                fetch_result = await fetch_config_tool(
                    {"config_name": config_name, "destination": destination}
                )

                # Parse result to extract config path
                fetch_output = fetch_result[0].text
                output_lines.append(fetch_output)
                output_lines.append("")

                # Extract config path from output
                # Expected format: "📂 Saved to: configs/react.json"
                match = re.search(r"(?i)saved to:\s*(.+\.json)", fetch_output)
                if match:
                    workflow_state["config_path"] = match.group(1).strip()
                    output_lines.append(f"✅ Config fetched: {workflow_state['config_path']}")
                else:
                    return [
                        TextContent(
                            type="text",
                            text="\n".join(output_lines) + "\n\n❌ Failed to fetch config",
                        )
                    ]

                workflow_state["phases_completed"].append("fetch_config")
            else:
                output_lines.append("  [DRY RUN] Would fetch config from API")
                workflow_state["config_path"] = f"{destination}/{config_name}.json"

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
                with open(workflow_state["config_path"]) as f:
                    config = json.load(f)
                    workflow_state["skill_name"] = config.get("name", "unknown")
                    workflow_state["config_data"] = config
            except Exception as e:
                return [
                    TextContent(
                        type="text",
                        text="\n".join(output_lines) + f"\n\n❌ Failed to read config: {str(e)}",
                    )
                ]

            # Call scrape_docs_tool (does NOT include enhancement)
            output_lines.append("Scraping documentation (this may take 20-45 minutes)...")
            output_lines.append("")

            scrape_result = await scrape_docs_tool(
                {
                    "config_path": workflow_state["config_path"],
                    "unlimited": unlimited,
                    "enhance_local": False,  # Enhancement is separate phase
                    "skip_scrape": False,
                    "dry_run": False,
                }
            )

            scrape_output = scrape_result[0].text
            output_lines.append(scrape_output)
            output_lines.append("")

            # Check for success using the SPECIFIC failure markers _run_converter
            # emits — not any "❌", which can appear in benign page content/logs
            # and would abort the workflow on a non-fatal warning.
            if (
                "❌ Converter returned non-zero exit code" in scrape_output
                or "❌ Converter raised an exception" in scrape_output
            ):
                return [
                    TextContent(
                        type="text",
                        text="\n".join(output_lines) + "\n\n❌ Scraping failed - see error above",
                    )
                ]

            workflow_state["skill_dir"] = f"{destination}/{workflow_state['skill_name']}"
            workflow_state["phases_completed"].append("scrape_docs")
        else:
            output_lines.append("  [DRY RUN] Would scrape documentation")
            workflow_state["skill_name"] = "example"
            workflow_state["skill_dir"] = f"{destination}/example"

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
            # Run enhance_skill_local in headless mode.
            # Phase 5d: deliberately KEPT as a subprocess — it spawns a LOCAL
            # coding agent (long-running, fork-bomb-guard semantics), which
            # must be a real child process.
            cmd = [
                sys.executable,
                str(CLI_DIR / "enhance_skill_local.py"),
                workflow_state["skill_dir"],
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
            workflow_state["phases_completed"].append("enhance_skill")
        else:
            output_lines.append("  [DRY RUN] Would enhance SKILL.md with AI agent")

        output_lines.append("")

        # ===== PHASE 4: Package Skill =====
        phase_num = "4/5" if config_name else "3/4"
        output_lines.append(f"📦 PHASE {phase_num}: Package Skill for {adaptor.PLATFORM_NAME}")
        output_lines.append("-" * 70)
        output_lines.append(f"Skill directory: {workflow_state['skill_dir']}")
        output_lines.append(f"Target platform: {adaptor.PLATFORM_NAME}")
        output_lines.append("")

        if not dry_run:
            # Call package_skill_tool with target
            package_result = await package_skill_tool(
                {
                    "skill_dir": workflow_state["skill_dir"],
                    "auto_upload": False,  # We handle upload in next phase
                    "target": target,
                }
            )

            package_output = package_result[0].text
            output_lines.append(package_output)
            output_lines.append("")

            # Abort if packaging failed — package_skill_tool emits "❌ Error:" on
            # a non-zero exit. Without this, a failed package still fabricated a
            # zip_path below and the workflow marched on to upload a missing file.
            if "❌ Error:" in package_output:
                output_lines.append("❌ Packaging failed; aborting before upload.")
                return text_response("\n".join(output_lines))

            # Extract package path from output (supports .zip and .tar.gz).
            # package_skill.py prints "   Output: <path>" and
            # "✅ Package created: <path>" — NOT "Saved to:", so match those.
            match = re.search(
                r"(?i)(?:output|package created|saved to):\s*(.+\.(?:zip|tar\.gz))",
                package_output,
            )
            if match:
                workflow_state["zip_path"] = match.group(1).strip()
            else:
                # Fallback: construct package path based on platform
                if target == "gemini":
                    workflow_state["zip_path"] = (
                        f"{destination}/{workflow_state['skill_name']}-gemini.tar.gz"
                    )
                elif target == "openai":
                    workflow_state["zip_path"] = (
                        f"{destination}/{workflow_state['skill_name']}-openai.zip"
                    )
                else:
                    workflow_state["zip_path"] = f"{destination}/{workflow_state['skill_name']}.zip"

            workflow_state["phases_completed"].append("package_skill")
        else:
            # Dry run - show expected package format
            if target == "gemini":
                pkg_ext = "tar.gz"
                pkg_file = f"{destination}/{workflow_state['skill_name']}-gemini.tar.gz"
            elif target == "openai":
                pkg_ext = "zip"
                pkg_file = f"{destination}/{workflow_state['skill_name']}-openai.zip"
            else:
                pkg_ext = "zip"
                pkg_file = f"{destination}/{workflow_state['skill_name']}.zip"

            output_lines.append(
                f"  [DRY RUN] Would package to {pkg_ext} file for {adaptor.PLATFORM_NAME}"
            )
            workflow_state["zip_path"] = pkg_file

        output_lines.append("")

        # ===== PHASE 5: Upload (Optional) =====
        has_api_key = False  # Initialize before conditional block
        if auto_upload:
            phase_num = "5/5" if config_name else "4/4"
            output_lines.append(f"📤 PHASE {phase_num}: Upload to {adaptor.PLATFORM_NAME}")
            output_lines.append("-" * 70)
            output_lines.append(f"Package file: {workflow_state['zip_path']}")
            output_lines.append("")

            # Check for platform-specific API key
            env_var_name = adaptor.get_env_var_name()
            has_api_key = os.environ.get(env_var_name, "").strip()

            if not dry_run:
                if has_api_key:
                    # Upload not supported for markdown platform
                    if target == "markdown":
                        output_lines.append("⚠️  Markdown export does not support upload")
                        output_lines.append("    Package has been created - use manually")
                    else:
                        # Call upload_skill_tool with target
                        upload_result = await upload_skill_tool(
                            {"skill_zip": workflow_state["zip_path"], "target": target}
                        )

                        upload_output = upload_result[0].text
                        output_lines.append(upload_output)

                        workflow_state["phases_completed"].append("upload_skill")
                else:
                    # Platform-specific instructions for missing API key
                    output_lines.append(f"⚠️  {env_var_name} not set - skipping upload")
                    output_lines.append("")
                    output_lines.append("To enable automatic upload:")

                    if target == "claude":
                        output_lines.append("  1. Get API key from https://console.anthropic.com/")
                        output_lines.append("  2. Set: export ANTHROPIC_API_KEY=sk-ant-...")
                        output_lines.append("")
                        output_lines.append("📤 Manual upload:")
                        output_lines.append("  1. Go to https://claude.ai/skills")
                        output_lines.append("  2. Click 'Upload Skill'")
                        output_lines.append(f"  3. Select: {workflow_state['zip_path']}")
                    elif target == "gemini":
                        output_lines.append("  1. Get API key from https://aistudio.google.com/")
                        output_lines.append("  2. Set: export GOOGLE_API_KEY=AIza...")
                        output_lines.append("")
                        output_lines.append("📤 Manual upload:")
                        output_lines.append("  1. Go to https://aistudio.google.com/")
                        output_lines.append(f"  2. Upload package: {workflow_state['zip_path']}")
                    elif target == "openai":
                        output_lines.append("  1. Get API key from https://platform.openai.com/")
                        output_lines.append("  2. Set: export OPENAI_API_KEY=sk-proj-...")
                        output_lines.append("")
                        output_lines.append("📤 Manual upload:")
                        output_lines.append("  1. Use OpenAI Assistants API")
                        output_lines.append(f"  2. Upload package: {workflow_state['zip_path']}")
                    elif target == "markdown":
                        output_lines.append("  (No API key needed - markdown is export only)")
                        output_lines.append(f"  Package created: {workflow_state['zip_path']}")
            else:
                output_lines.append(
                    f"  [DRY RUN] Would upload to {adaptor.PLATFORM_NAME} (if API key set)"
                )

            output_lines.append("")

        # ===== PHASE 6: Publish to Marketplace (Optional) =====
        marketplace_targets = []
        if marketplace_arg:
            marketplace_targets.append(
                {"marketplace": marketplace_arg, "category": marketplace_category}
            )
        else:
            cd = workflow_state.get("config_data", {})
            if isinstance(cd, dict):
                marketplace_targets = cd.get("marketplace_targets", [])

        if marketplace_targets:
            phase_num = len(workflow_state["phases_completed"]) + 1
            output_lines.append(f"{'=' * 70}")
            output_lines.append(
                f"PHASE {phase_num}: Publish to Marketplace"
                f" ({len(marketplace_targets)} target{'s' if len(marketplace_targets) > 1 else ''})"
            )
            output_lines.append(f"{'=' * 70}")
            output_lines.append("")

            if not dry_run:
                from .marketplace_tools import publish_to_marketplace_tool

                for mp_target in marketplace_targets:
                    mp_name = mp_target.get("marketplace", "")
                    mp_cat = mp_target.get("category", "development")
                    output_lines.append(f"Publishing to marketplace '{mp_name}'...")

                    try:
                        pub_result = await publish_to_marketplace_tool(
                            {
                                "skill_dir": workflow_state["skill_dir"],
                                "marketplace": mp_name,
                                "category": mp_cat,
                                "create_branch": create_branch,
                                "force": True,
                            }
                        )
                        pub_output = pub_result[0].text if pub_result else "No output"
                        output_lines.append(pub_output)
                        workflow_state["phases_completed"].append(
                            f"publish_to_marketplace({mp_name})"
                        )
                    except Exception as e:
                        output_lines.append(f"Failed to publish to '{mp_name}': {str(e)}")
                    output_lines.append("")
            else:
                for mp_target in marketplace_targets:
                    mp_name = mp_target.get("marketplace", "")
                    mp_cat = mp_target.get("category", "development")
                    output_lines.append(
                        f"  [DRY RUN] Would publish to marketplace '{mp_name}' (category: {mp_cat})"
                    )
                output_lines.append("")

        # ===== WORKFLOW SUMMARY =====
        output_lines.append("=" * 70)
        output_lines.append("✅ WORKFLOW COMPLETE")
        output_lines.append("=" * 70)
        output_lines.append("")

        if not dry_run:
            output_lines.append("Phases completed:")
            for phase in workflow_state["phases_completed"]:
                output_lines.append(f"  ✓ {phase}")
            output_lines.append("")

            output_lines.append("📁 Output:")
            output_lines.append(f"  Skill directory: {workflow_state['skill_dir']}")
            if workflow_state["zip_path"]:
                output_lines.append(f"  Skill package: {workflow_state['zip_path']}")
            output_lines.append("")

            if auto_upload and has_api_key and target != "markdown":
                # Platform-specific success message
                if target == "claude":
                    output_lines.append("🎉 Your skill is now available in Claude!")
                    output_lines.append("   Go to https://claude.ai/skills to use it")
                elif target == "gemini":
                    output_lines.append("🎉 Your skill is now available in Gemini!")
                    output_lines.append("   Go to https://aistudio.google.com/ to use it")
                elif target == "openai":
                    output_lines.append("🎉 Your assistant is now available in OpenAI!")
                    output_lines.append(
                        "   Go to https://platform.openai.com/assistants/ to use it"
                    )
            elif auto_upload:
                output_lines.append("📝 Manual upload required (see instructions above)")
            else:
                output_lines.append("📤 To upload:")
                output_lines.append(
                    f"   skill-seekers upload {workflow_state['zip_path']} --target {target}"
                )
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
        for phase in workflow_state["phases_completed"]:
            output_lines.append(f"  ✓ {phase}")
        return [TextContent(type="text", text="\n".join(output_lines))]
