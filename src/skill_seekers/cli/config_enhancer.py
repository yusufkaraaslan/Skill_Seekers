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
import sys
from dataclasses import dataclass, field
from pathlib import Path

from skill_seekers.cli.agent_client import AgentClient

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


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
    - API mode: Uses Anthropic API (requires ANTHROPIC_API_KEY)
    - LOCAL mode: Uses a coding agent CLI (no API key needed)
    - AUTO mode: Automatically detects best available mode
    """

    def __init__(self, mode: str = "auto"):
        """
        Initialize ConfigEnhancer.

        Args:
            mode: Enhancement mode - "api", "local", or "auto" (default)
        """
        self._agent = AgentClient(mode=mode)
        self.mode = self._agent.mode
        self._agent.log_mode()

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
    # API MODE - Direct AI API calls
    # =========================================================================

    def _enhance_via_api(self, result: dict) -> dict:
        """Enhance configs using AI API"""
        if not self._agent.is_available():
            logger.error("❌ API mode requested but no API client available")
            return result

        try:
            # Create enhancement prompt
            prompt = self._create_enhancement_prompt(result)

            # Call AI agent for config analysis
            logger.info("📡 Calling AI agent for config analysis...")
            response_text = self._agent.call(prompt, max_tokens=8000)

            if not response_text:
                logger.error("❌ AI agent returned no response")
                return result

            # Parse response
            enhanced_result = self._parse_api_response(response_text, result)
            logger.info("✅ API enhancement complete")
            return enhanced_result

        except Exception as e:
            logger.error(f"❌ API enhancement failed: {e}")
            return result

    def _create_enhancement_prompt(self, result: dict) -> str:
        """Create prompt for AI API"""
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
        """Parse AI API response and merge with original result"""
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
    # LOCAL MODE - Coding Agent CLI
    # =========================================================================

    def _enhance_via_local(self, result: dict) -> dict:
        """Enhance configs using LOCAL CLI agent"""
        try:
            logger.info("🖥️  Launching LOCAL agent for config analysis...")
            logger.info("⏱️  This will take 30-60 seconds...")

            # Build the prompt (without output_file since AgentClient handles that)
            prompt_content = self._create_local_prompt(result, Path("config_enhancement.json"))

            # Call via AgentClient which handles temp dirs, file polling, etc.
            response_text = self._agent.call(prompt_content, timeout=300)

            if response_text:
                try:
                    import re

                    json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                    if json_match:
                        data = json.loads(json_match.group())
                        if "file_enhancements" in data or "overall_insights" in data:
                            result["ai_enhancements"] = data
                            logger.info("✅ LOCAL enhancement complete")
                            return result
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Failed to parse LOCAL response as JSON: {e}")

            logger.warning("⚠️  LOCAL enhancement produced no results")
            return result

        except Exception as e:
            logger.error(f"❌ LOCAL enhancement failed: {e}")
            return result

    def _create_local_prompt(self, result: dict, output_file: Path) -> str:
        """Create prompt file for coding agent CLI

        Args:
            result: Config extraction result dict
            output_file: Absolute path where the agent should write the JSON output

        Returns:
            Prompt content string
        """
        config_files = result.get("config_files", [])

        # Format config data for AI agent (limit to 15 files for reasonable prompt size)
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
