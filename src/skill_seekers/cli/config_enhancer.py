#!/usr/bin/env python3
"""
Configuration Enhancer - AI-powered enhancement for config extraction results.

Provides dual-mode AI enhancement (API + LOCAL) for configuration analysis:
- Explain what each setting does
- Suggest best practices and improvements
- Security analysis (hardcoded secrets, exposed credentials)
- Migration suggestions (consolidate configs)
- Context-aware documentation

Similar to GuideEnhancer (C3.3) but for configuration files.
"""

import json
import logging
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Optional anthropic import
ANTHROPIC_AVAILABLE = False
try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    pass


@dataclass
class ConfigEnhancement:
    """AI-generated enhancement for a configuration"""

    explanation: str = ""  # What this setting does
    best_practice: str = ""  # Suggested improvement
    security_concern: str = ""  # Security issue (if any)
    migration_suggestion: str = ""  # Consolidation opportunity
    context: str = ""  # Pattern context and usage


@dataclass
class EnhancedConfigFile:
    """Configuration file with AI enhancements"""

    file_path: str
    config_type: str
    purpose: str
    enhancement: ConfigEnhancement
    setting_enhancements: dict[str, ConfigEnhancement] = field(default_factory=dict)


class ConfigEnhancer:
    """
    AI enhancement for configuration extraction results.

    Supports dual-mode operation:
    - API mode: Uses Claude API (requires ANTHROPIC_API_KEY)
    - LOCAL mode: Uses Claude Code CLI (no API key needed)
    - AUTO mode: Automatically detects best available mode
    """

    def __init__(self, mode: str = "auto"):
        """
        Initialize ConfigEnhancer.

        Args:
            mode: Enhancement mode - "api", "local", or "auto" (default)
        """
        self.mode = self._detect_mode(mode)
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.client = None

        if self.mode == "api" and ANTHROPIC_AVAILABLE and self.api_key:
            # Support custom base_url for GLM-4.7 and other Claude-compatible APIs
            client_kwargs = {"api_key": self.api_key}
            base_url = os.environ.get("ANTHROPIC_BASE_URL")
            if base_url:
                client_kwargs["base_url"] = base_url
                logger.info(f"✅ Using custom API base URL: {base_url}")
            self.client = anthropic.Anthropic(**client_kwargs)

    def _detect_mode(self, requested_mode: str) -> str:
        """
        Detect best enhancement mode.

        Args:
            requested_mode: User-requested mode

        Returns:
            Actual mode to use
        """
        if requested_mode in ["api", "local"]:
            return requested_mode

        # Auto-detect
        if os.environ.get("ANTHROPIC_API_KEY") and ANTHROPIC_AVAILABLE:
            logger.info("🤖 AI enhancement: API mode (Claude API detected)")
            return "api"
        else:
            logger.info("🤖 AI enhancement: LOCAL mode (using Claude Code CLI)")
            return "local"

    def enhance_config_result(self, result: dict) -> dict:
        """
        Enhance entire configuration extraction result.

        Args:
            result: ConfigExtractionResult as dict

        Returns:
            Enhanced result with AI insights
        """
        logger.info(f"🔄 Enhancing {len(result.get('config_files', []))} config files...")

        if self.mode == "api":
            return self._enhance_via_api(result)
        else:
            return self._enhance_via_local(result)

    # =========================================================================
    # API MODE - Direct Claude API calls
    # =========================================================================

    def _enhance_via_api(self, result: dict) -> dict:
        """Enhance configs using Claude API"""
        if not self.client:
            logger.error("❌ API mode requested but no API key available")
            return result

        try:
            # Create enhancement prompt
            prompt = self._create_enhancement_prompt(result)

            # Call Claude API
            logger.info("📡 Calling Claude API for config analysis...")
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=8000,
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse response
            enhanced_result = self._parse_api_response(response.content[0].text, result)
            logger.info("✅ API enhancement complete")
            return enhanced_result

        except Exception as e:
            logger.error(f"❌ API enhancement failed: {e}")
            return result

    def _create_enhancement_prompt(self, result: dict) -> str:
        """Create prompt for Claude API"""
        config_files = result.get("config_files", [])

        # Summarize configs for prompt
        config_summary = []
        for cf in config_files[:10]:  # Limit to first 10 files
            settings_summary = []
            for setting in cf.get("settings", [])[:5]:  # First 5 settings per file
                # Support both "type" (from config_extractor) and "value_type" (legacy)
                value_type = setting.get("type", setting.get("value_type", "unknown"))
                settings_summary.append(f"  - {setting['key']}: {setting['value']} ({value_type})")

            # Support both "type" (from config_extractor) and "config_type" (legacy)
            config_type = cf.get("type", cf.get("config_type", "unknown"))
            config_summary.append(f"""
File: {cf["relative_path"]} ({config_type})
Purpose: {cf["purpose"]}
Settings:
{chr(10).join(settings_summary)}
Patterns: {", ".join(cf.get("patterns", []))}
""")

        prompt = f"""Analyze these configuration files and provide AI-enhanced insights.

CONFIGURATION FILES ({len(config_files)} total, showing first 10):
{chr(10).join(config_summary)}

YOUR TASK: Provide comprehensive analysis in JSON format with these 5 enhancements:

1. **EXPLANATIONS**: For each config file, explain its purpose and key settings
2. **BEST PRACTICES**: Suggest improvements (better structure, naming, organization)
3. **SECURITY ANALYSIS**: Identify hardcoded secrets, exposed credentials, security issues
4. **MIGRATION SUGGESTIONS**: Identify opportunities to consolidate or standardize configs
5. **CONTEXT**: Explain the detected patterns and when to use them

OUTPUT FORMAT (strict JSON):
{{
  "file_enhancements": [
    {{
      "file_path": "path/to/config.json",
      "explanation": "This file configures the database connection...",
      "best_practice": "Consider using environment variables for host/port",
      "security_concern": "⚠️ DATABASE_PASSWORD is hardcoded - move to .env",
      "migration_suggestion": "Consolidate with config.yml (overlapping settings)",
      "context": "Standard PostgreSQL configuration pattern"
    }}
  ],
  "overall_insights": {{
    "config_count": {len(config_files)},
    "security_issues_found": 3,
    "consolidation_opportunities": ["Merge .env and config.json database settings"],
    "recommended_actions": ["Move secrets to environment variables", "Standardize on YAML format"]
  }}
}}

Focus on actionable insights that help developers understand and improve their configuration.
"""
        return prompt

    def _parse_api_response(self, response_text: str, original_result: dict) -> dict:
        """Parse Claude API response and merge with original result"""
        try:
            # Extract JSON from response
            import re

            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if not json_match:
                logger.warning("⚠️  No JSON found in API response")
                return original_result

            enhancements = json.loads(json_match.group())

            # Merge enhancements into original result
            original_result["ai_enhancements"] = enhancements

            # Add enhancement flags to config files
            file_enhancements = {
                e["file_path"]: e for e in enhancements.get("file_enhancements", [])
            }
            for cf in original_result.get("config_files", []):
                file_path = cf.get("relative_path", cf.get("file_path"))
                if file_path in file_enhancements:
                    cf["ai_enhancement"] = file_enhancements[file_path]

            return original_result

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse API response as JSON: {e}")
            return original_result

    # =========================================================================
    # LOCAL MODE - Claude Code CLI
    # =========================================================================

    def _enhance_via_local(self, result: dict) -> dict:
        """Enhance configs using Claude Code CLI"""
        try:
            # Create a temporary directory for this enhancement session
            with tempfile.TemporaryDirectory(prefix="config_enhance_") as temp_dir:
                temp_path = Path(temp_dir)

                # Define output file path (absolute path that Claude will write to)
                output_file = temp_path / "config_enhancement.json"

                # Create prompt file with the output path embedded
                prompt_file = temp_path / "enhance_prompt.md"
                prompt_content = self._create_local_prompt(result, output_file)
                prompt_file.write_text(prompt_content)

                logger.info("🖥️  Launching Claude Code CLI for config analysis...")
                logger.info("⏱️  This will take 30-60 seconds...")

                # Run Claude Code CLI
                result_data = self._run_claude_cli(prompt_file, output_file, temp_path)

                if result_data:
                    # Merge LOCAL enhancements
                    result["ai_enhancements"] = result_data
                    logger.info("✅ LOCAL enhancement complete")
                    return result
                else:
                    logger.warning("⚠️  LOCAL enhancement produced no results")
                    return result

        except Exception as e:
            logger.error(f"❌ LOCAL enhancement failed: {e}")
            return result

    def _create_local_prompt(self, result: dict, output_file: Path) -> str:
        """Create prompt file for Claude Code CLI

        Args:
            result: Config extraction result dict
            output_file: Absolute path where Claude should write the JSON output

        Returns:
            Prompt content string
        """
        config_files = result.get("config_files", [])

        # Format config data for Claude (limit to 15 files for reasonable prompt size)
        config_data = []
        for cf in config_files[:15]:
            # Support both "type" (from config_extractor) and "config_type" (legacy)
            config_type = cf.get("type", cf.get("config_type", "unknown"))
            settings_preview = []
            for s in cf.get("settings", [])[:3]:  # Show first 3 settings
                settings_preview.append(
                    f"    - {s.get('key', 'unknown')}: {str(s.get('value', ''))[:50]}"
                )

            config_data.append(f"""
### {cf["relative_path"]} ({config_type})
- Purpose: {cf["purpose"]}
- Patterns: {", ".join(cf.get("patterns", [])) or "none detected"}
- Settings: {len(cf.get("settings", []))} total
{chr(10).join(settings_preview) if settings_preview else "  (no settings)"}
""")

        prompt = f"""# Configuration Analysis Task

IMPORTANT: You MUST write the output to this EXACT file path:
{output_file}

## Configuration Files ({len(config_files)} total, showing first 15)

{chr(10).join(config_data)}

## Your Task

Analyze these configuration files and write a JSON file to the path specified above.

The JSON must have this EXACT structure:

```json
{{
  "file_enhancements": [
    {{
      "file_path": "relative/path/to/config.json",
      "explanation": "Brief explanation of what this config file does",
      "best_practice": "Suggested improvement or 'None'",
      "security_concern": "Security issue if any, or 'None'",
      "migration_suggestion": "Consolidation opportunity or 'None'",
      "context": "What pattern or purpose this serves"
    }}
  ],
  "overall_insights": {{
    "config_count": {len(config_files)},
    "security_issues_found": 0,
    "consolidation_opportunities": ["List of suggestions"],
    "recommended_actions": ["List of actions"]
  }}
}}
```

## Instructions

1. Use the Write tool to create the JSON file at: {output_file}
2. Include an enhancement entry for each config file shown above
3. Focus on actionable insights:
   - Explain what each config does in 1-2 sentences
   - Identify any hardcoded secrets or security issues
   - Suggest consolidation if configs have overlapping settings
   - Note any missing best practices

DO NOT explain your work - just write the JSON file directly.
"""
        return prompt

    def _run_claude_cli(
        self, prompt_file: Path, output_file: Path, working_dir: Path
    ) -> dict | None:
        """Run Claude Code CLI and wait for completion

        Args:
            prompt_file: Path to the prompt markdown file
            output_file: Expected path where Claude will write the JSON output
            working_dir: Working directory to run Claude from

        Returns:
            Parsed JSON dict if successful, None otherwise
        """
        import time

        try:
            start_time = time.time()

            # Run claude command with --dangerously-skip-permissions to bypass all prompts
            # This allows Claude to write files without asking for confirmation
            logger.info(f"   Running: claude --dangerously-skip-permissions {prompt_file.name}")
            logger.info(f"   Output expected at: {output_file}")

            result = subprocess.run(
                ["claude", "--dangerously-skip-permissions", str(prompt_file)],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=str(working_dir),
            )

            elapsed = time.time() - start_time
            logger.info(f"   Claude finished in {elapsed:.1f} seconds")

            if result.returncode != 0:
                logger.error(f"❌ Claude CLI failed (exit code {result.returncode})")
                if result.stderr:
                    logger.error(f"   Error: {result.stderr[:200]}")
                return None

            # Check if the expected output file was created
            if output_file.exists():
                try:
                    with open(output_file) as f:
                        data = json.load(f)
                        if "file_enhancements" in data or "overall_insights" in data:
                            logger.info(f"✅ Found enhancement data in {output_file.name}")
                            return data
                        else:
                            logger.warning("⚠️  Output file exists but missing expected keys")
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Failed to parse output JSON: {e}")
                    return None

            # Fallback: Look for any JSON files created in the working directory
            logger.info("   Looking for JSON files in working directory...")
            current_time = time.time()
            potential_files = []

            for json_file in working_dir.glob("*.json"):
                # Check if created recently (within last 2 minutes)
                if current_time - json_file.stat().st_mtime < 120:
                    potential_files.append(json_file)

            # Try to load the most recent JSON file with expected structure
            for json_file in sorted(potential_files, key=lambda f: f.stat().st_mtime, reverse=True):
                try:
                    with open(json_file) as f:
                        data = json.load(f)
                        if "file_enhancements" in data or "overall_insights" in data:
                            logger.info(f"✅ Found enhancement data in {json_file.name}")
                            return data
                except Exception:
                    continue

            logger.warning("⚠️  Could not find enhancement output file")
            logger.info(f"   Expected file: {output_file}")
            logger.info(f"   Files in dir: {list(working_dir.glob('*'))}")
            return None

        except subprocess.TimeoutExpired:
            logger.error("❌ Claude CLI timeout (5 minutes)")
            return None
        except FileNotFoundError:
            logger.error("❌ 'claude' command not found. Is Claude Code CLI installed?")
            logger.error("   Install with: npm install -g @anthropic-ai/claude-code")
            return None
        except Exception as e:
            logger.error(f"❌ Error running Claude CLI: {e}")
            return None


def main():
    """Command-line interface for config enhancement"""
    import argparse

    parser = argparse.ArgumentParser(description="AI-enhance configuration extraction results")
    parser.add_argument("result_file", help="Path to config extraction JSON result file")
    parser.add_argument(
        "--mode",
        choices=["auto", "api", "local"],
        default="auto",
        help="Enhancement mode (default: auto)",
    )
    parser.add_argument(
        "--output", help="Output file for enhanced results (default: <input>_enhanced.json)"
    )

    args = parser.parse_args()

    # Load result file
    try:
        with open(args.result_file) as f:
            result = json.load(f)
    except Exception as e:
        logger.error(f"❌ Failed to load result file: {e}")
        return 1

    # Enhance
    enhancer = ConfigEnhancer(mode=args.mode)
    enhanced_result = enhancer.enhance_config_result(result)

    # Save
    output_file = args.output or args.result_file.replace(".json", "_enhanced.json")
    try:
        with open(output_file, "w") as f:
            json.dump(enhanced_result, f, indent=2)
        logger.info(f"✅ Enhanced results saved to: {output_file}")
    except Exception as e:
        logger.error(f"❌ Failed to save results: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
