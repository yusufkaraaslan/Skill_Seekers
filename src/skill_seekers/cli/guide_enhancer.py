"""
AI Enhancement for How-To Guides (C3.3)

This module provides comprehensive AI enhancement for how-to guides with dual-mode support:
- API mode: Uses Claude API (requires ANTHROPIC_API_KEY)
- LOCAL mode: Uses Claude Code CLI (no API key needed)

Provides 5 automatic enhancements:
1. Step Descriptions - Natural language explanations (not just syntax)
2. Troubleshooting Solutions - Diagnostic flows + solutions for common errors
3. Prerequisites Explanations - Why each prerequisite is needed + setup instructions
4. Next Steps Suggestions - Related guides, variations, learning paths
5. Use Case Examples - Real-world scenarios showing when to use guide
"""

import json
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING

# Avoid circular imports by using TYPE_CHECKING
if TYPE_CHECKING:
    from .how_to_guide_builder import PrerequisiteItem, TroubleshootingItem
else:
    # Import at runtime to avoid circular dependency issues
    try:
        from .how_to_guide_builder import PrerequisiteItem, TroubleshootingItem
    except ImportError:
        # Fallback definitions if import fails
        @dataclass
        class PrerequisiteItem:
            name: str
            why: str
            setup: str

        @dataclass
        class TroubleshootingItem:
            problem: str
            symptoms: List[str] = field(default_factory=list)
            solution: str = ""
            diagnostic_steps: List[str] = field(default_factory=list)

logger = logging.getLogger(__name__)

# Conditional import for Anthropic API
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.debug("Anthropic library not available - API mode will be unavailable")


@dataclass
class StepEnhancement:
    """Enhanced step information (internal use only)"""
    step_index: int
    explanation: str  # Natural language explanation
    variations: List[str] = field(default_factory=list)  # Alternative approaches


class GuideEnhancer:
    """
    AI enhancement for how-to guides with dual-mode support.

    Modes:
    - api: Uses Claude API (requires ANTHROPIC_API_KEY)
    - local: Uses Claude Code CLI (no API key needed)
    - auto: Automatically detect best mode
    """

    def __init__(self, mode: str = "auto"):
        """
        Initialize GuideEnhancer.

        Args:
            mode: Enhancement mode - "api", "local", or "auto"
        """
        self.mode = self._detect_mode(mode)
        self.api_key = os.environ.get('ANTHROPIC_API_KEY')
        self.client = None

        if self.mode == "api":
            if ANTHROPIC_AVAILABLE and self.api_key:
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("✨ GuideEnhancer initialized in API mode")
            else:
                logger.warning("⚠️  API mode requested but anthropic library not available or no API key")
                self.mode = "none"
        elif self.mode == "local":
            # Check if claude CLI is available
            if not self._check_claude_cli():
                logger.warning("⚠️  Claude CLI not found - falling back to API mode")
                self.mode = "api"
                if ANTHROPIC_AVAILABLE and self.api_key:
                    self.client = anthropic.Anthropic(api_key=self.api_key)
                else:
                    logger.warning("⚠️  API fallback also unavailable")
                    self.mode = "none"
            else:
                logger.info("✨ GuideEnhancer initialized in LOCAL mode")
        else:
            logger.warning("⚠️  No AI enhancement available (no API key or Claude CLI)")
            self.mode = "none"

    def _detect_mode(self, requested_mode: str) -> str:
        """
        Detect the best enhancement mode.

        Args:
            requested_mode: User-requested mode

        Returns:
            Detected mode: "api", "local", or "none"
        """
        if requested_mode == "auto":
            # Prefer API if key available, else LOCAL
            if os.environ.get('ANTHROPIC_API_KEY') and ANTHROPIC_AVAILABLE:
                return "api"
            elif self._check_claude_cli():
                return "local"
            else:
                return "none"
        return requested_mode

    def _check_claude_cli(self) -> bool:
        """Check if Claude Code CLI is available."""
        try:
            result = subprocess.run(
                ['claude', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def enhance_guide(self, guide_data: Dict) -> Dict:
        """
        Apply all 5 enhancements to a guide.

        Args:
            guide_data: Guide data dictionary with title, steps, etc.

        Returns:
            Enhanced guide data with all 5 enhancements
        """
        if self.mode == "none":
            logger.warning("⚠️  AI enhancement unavailable - returning original guide")
            return guide_data

        try:
            if self.mode == "api":
                return self._enhance_via_api(guide_data)
            else:
                return self._enhance_via_local(guide_data)
        except Exception as e:
            logger.error(f"❌ AI enhancement failed: {e}")
            logger.info("📝 Returning original guide without enhancement")
            return guide_data

    def enhance_step_descriptions(self, steps: List[Dict]) -> List[StepEnhancement]:
        """
        Enhancement 1: Add natural language explanations to steps.

        Args:
            steps: List of workflow steps

        Returns:
            List of step enhancements with explanations
        """
        if not steps or self.mode == "none":
            return []

        prompt = self._create_step_description_prompt(steps)
        response = self._call_ai(prompt)

        if not response:
            return []

        try:
            data = json.loads(response)
            return [
                StepEnhancement(
                    step_index=item.get('step_index', i),
                    explanation=item.get('explanation', ''),
                    variations=item.get('variations', [])
                )
                for i, item in enumerate(data.get('step_descriptions', []))
            ]
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"⚠️  Failed to parse step descriptions: {e}")
            return []

    def enhance_troubleshooting(self, guide_data: Dict) -> List[TroubleshootingItem]:
        """
        Enhancement 2: Generate diagnostic flows + solutions.

        Args:
            guide_data: Guide data with title, steps, language

        Returns:
            List of troubleshooting items with solutions
        """
        if self.mode == "none":
            return []

        prompt = self._create_troubleshooting_prompt(guide_data)
        response = self._call_ai(prompt)

        if not response:
            return []

        try:
            data = json.loads(response)
            return [
                TroubleshootingItem(
                    problem=item.get('problem', ''),
                    symptoms=item.get('symptoms', []),
                    diagnostic_steps=item.get('diagnostic_steps', []),
                    solution=item.get('solution', '')
                )
                for item in data.get('troubleshooting', [])
            ]
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"⚠️  Failed to parse troubleshooting items: {e}")
            return []

    def enhance_prerequisites(self, prereqs: List[str]) -> List[PrerequisiteItem]:
        """
        Enhancement 3: Explain why prerequisites are needed.

        Args:
            prereqs: List of prerequisite names

        Returns:
            List of enhanced prerequisites with explanations
        """
        if not prereqs or self.mode == "none":
            return []

        prompt = self._create_prerequisites_prompt(prereqs)
        response = self._call_ai(prompt)

        if not response:
            return []

        try:
            data = json.loads(response)
            return [
                PrerequisiteItem(
                    name=item.get('name', ''),
                    why=item.get('why', ''),
                    setup=item.get('setup', '')
                )
                for item in data.get('prerequisites_detailed', [])
            ]
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"⚠️  Failed to parse prerequisites: {e}")
            return []

    def enhance_next_steps(self, guide_data: Dict) -> List[str]:
        """
        Enhancement 4: Suggest related guides and variations.

        Args:
            guide_data: Guide data with title, topic

        Returns:
            List of next step suggestions
        """
        if self.mode == "none":
            return []

        prompt = self._create_next_steps_prompt(guide_data)
        response = self._call_ai(prompt)

        if not response:
            return []

        try:
            data = json.loads(response)
            return data.get('next_steps', [])
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"⚠️  Failed to parse next steps: {e}")
            return []

    def enhance_use_cases(self, guide_data: Dict) -> List[str]:
        """
        Enhancement 5: Generate real-world scenario examples.

        Args:
            guide_data: Guide data with title, description

        Returns:
            List of use case examples
        """
        if self.mode == "none":
            return []

        prompt = self._create_use_cases_prompt(guide_data)
        response = self._call_ai(prompt)

        if not response:
            return []

        try:
            data = json.loads(response)
            return data.get('use_cases', [])
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"⚠️  Failed to parse use cases: {e}")
            return []

    # === AI Call Methods ===

    def _call_ai(self, prompt: str, max_tokens: int = 4000) -> Optional[str]:
        """
        Call AI with the given prompt.

        Args:
            prompt: Prompt text
            max_tokens: Maximum tokens in response

        Returns:
            AI response text or None if failed
        """
        if self.mode == "api":
            return self._call_claude_api(prompt, max_tokens)
        elif self.mode == "local":
            return self._call_claude_local(prompt)
        return None

    def _call_claude_api(self, prompt: str, max_tokens: int = 4000) -> Optional[str]:
        """
        Call Claude API.

        Args:
            prompt: Prompt text
            max_tokens: Maximum tokens in response

        Returns:
            API response text or None if failed
        """
        if not self.client:
            return None

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.warning(f"⚠️  Claude API call failed: {e}")
            return None

    def _call_claude_local(self, prompt: str) -> Optional[str]:
        """
        Call Claude Code CLI.

        Args:
            prompt: Prompt text

        Returns:
            CLI response text or None if failed
        """
        try:
            # Create temporary prompt file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                f.write(prompt)
                prompt_file = f.name

            # Run claude CLI
            result = subprocess.run(
                ['claude', prompt_file],
                capture_output=True,
                text=True,
                timeout=300  # 5 min timeout
            )

            # Clean up prompt file
            Path(prompt_file).unlink(missing_ok=True)

            if result.returncode == 0:
                return result.stdout
            else:
                logger.warning(f"⚠️  Claude CLI failed: {result.stderr}")
                return None

        except (subprocess.TimeoutExpired, Exception) as e:
            logger.warning(f"⚠️  Claude CLI execution failed: {e}")
            return None

    # === Prompt Creation Methods ===

    def _enhance_via_api(self, guide_data: Dict) -> Dict:
        """
        Enhance guide via API mode.

        Args:
            guide_data: Guide data dictionary

        Returns:
            Enhanced guide data
        """
        prompt = self._create_enhancement_prompt(guide_data)
        response = self._call_claude_api(prompt)

        if not response:
            return guide_data

        return self._parse_enhancement_response(response, guide_data)

    def _enhance_via_local(self, guide_data: Dict) -> Dict:
        """
        Enhance guide via LOCAL mode.

        Args:
            guide_data: Guide data dictionary

        Returns:
            Enhanced guide data
        """
        prompt = self._create_enhancement_prompt(guide_data)
        response = self._call_claude_local(prompt)

        if not response:
            return guide_data

        return self._parse_enhancement_response(response, guide_data)

    def _create_enhancement_prompt(self, guide_data: Dict) -> str:
        """
        Create comprehensive enhancement prompt for all 5 enhancements.

        Args:
            guide_data: Guide data dictionary

        Returns:
            Complete prompt text
        """
        title = guide_data.get('title', 'Unknown Guide')
        steps = guide_data.get('steps', [])
        language = guide_data.get('language', 'python')
        prerequisites = guide_data.get('prerequisites', [])

        steps_text = self._format_steps_for_prompt(steps)
        prereqs_text = ', '.join(prerequisites) if prerequisites else 'None specified'

        prompt = f"""I need you to enhance this how-to guide with 5 improvements:

CURRENT GUIDE:
Title: {title}
Steps: {len(steps)} steps
Code Language: {language}
Prerequisites: {prereqs_text}

STEP CODE:
{steps_text}

YOUR TASK - Provide JSON output with these 5 enhancements:

1. STEP_DESCRIPTIONS: For each step, write natural language explanation (not just syntax)
   - Explain what the code does
   - Explain why it's needed
   - Provide context and best practices

2. TROUBLESHOOTING: Generate 3-5 common errors with diagnostic flows + solutions
   - Identify likely errors for this type of workflow
   - Provide symptoms to recognize the error
   - Give diagnostic steps to confirm the issue
   - Provide clear solution steps

3. PREREQUISITES: Explain WHY each prerequisite is needed + setup instructions
   - For each prerequisite, explain its purpose
   - Provide installation/setup commands
   - Explain when it's used in the workflow

4. NEXT_STEPS: Suggest 3-5 related guides, variations, learning paths
   - Related guides that build on this one
   - Variations (e.g., async version, different approaches)
   - Next logical learning steps

5. USE_CASES: Provide 2-3 real-world scenarios when to use this guide
   - Specific situations where this workflow applies
   - Problems it solves
   - When NOT to use this approach

OUTPUT FORMAT (strict JSON):
{{
  "step_descriptions": [
    {{"step_index": 0, "explanation": "...", "variations": ["..."]}},
    {{"step_index": 1, "explanation": "...", "variations": ["..."]}},
    ...
  ],
  "troubleshooting": [
    {{
      "problem": "ImportError: No module named 'requests'",
      "symptoms": ["Import fails", "Module not found error"],
      "diagnostic_steps": ["Check pip list", "Verify virtual env"],
      "solution": "Run: pip install requests"
    }},
    ...
  ],
  "prerequisites_detailed": [
    {{"name": "requests", "why": "HTTP client for making web requests", "setup": "pip install requests"}},
    ...
  ],
  "next_steps": [
    "How to handle async workflows",
    "How to add error handling",
    ...
  ],
  "use_cases": [
    "Use when you need to automate web scraping tasks",
    "Ideal for building documentation archives",
    ...
  ]
}}

IMPORTANT: Return ONLY valid JSON, no markdown code blocks or extra text.
"""
        return prompt

    def _create_step_description_prompt(self, steps: List[Dict]) -> str:
        """Create prompt for step descriptions only."""
        steps_text = self._format_steps_for_prompt(steps)
        return f"""Generate natural language explanations for these code steps:

{steps_text}

Return JSON:
{{
  "step_descriptions": [
    {{"step_index": 0, "explanation": "...", "variations": [""]}},
    ...
  ]
}}

IMPORTANT: Return ONLY valid JSON.
"""

    def _create_troubleshooting_prompt(self, guide_data: Dict) -> str:
        """Create prompt for troubleshooting items."""
        title = guide_data.get('title', 'Unknown')
        language = guide_data.get('language', 'python')
        steps = guide_data.get('steps', [])
        steps_text = self._format_steps_for_prompt(steps)

        return f"""Generate troubleshooting guidance for this {language} workflow:

Title: {title}
Steps:
{steps_text}

Return JSON with 3-5 common errors:
{{
  "troubleshooting": [
    {{
      "problem": "...",
      "symptoms": ["...", "..."],
      "diagnostic_steps": ["...", "..."],
      "solution": "..."
    }},
    ...
  ]
}}

IMPORTANT: Return ONLY valid JSON.
"""

    def _create_prerequisites_prompt(self, prereqs: List[str]) -> str:
        """Create prompt for prerequisites enhancement."""
        prereqs_text = ', '.join(prereqs)
        return f"""Explain why these prerequisites are needed and how to install them:

Prerequisites: {prereqs_text}

Return JSON:
{{
  "prerequisites_detailed": [
    {{"name": "...", "why": "...", "setup": "..."}},
    ...
  ]
}}

IMPORTANT: Return ONLY valid JSON.
"""

    def _create_next_steps_prompt(self, guide_data: Dict) -> str:
        """Create prompt for next steps suggestions."""
        title = guide_data.get('title', 'Unknown')
        return f"""Suggest 3-5 related guides and learning paths after completing: {title}

Return JSON:
{{
  "next_steps": [
    "How to ...",
    "How to ...",
    ...
  ]
}}

IMPORTANT: Return ONLY valid JSON.
"""

    def _create_use_cases_prompt(self, guide_data: Dict) -> str:
        """Create prompt for use case examples."""
        title = guide_data.get('title', 'Unknown')
        description = guide_data.get('description', '')

        return f"""Generate 2-3 real-world use cases for this guide:

Title: {title}
Description: {description}

Return JSON:
{{
  "use_cases": [
    "Use when you need to ...",
    "Ideal for ...",
    ...
  ]
}}

IMPORTANT: Return ONLY valid JSON.
"""

    def _format_steps_for_prompt(self, steps: List[Dict]) -> str:
        """Format steps for inclusion in prompts."""
        if not steps:
            return "No steps provided"

        formatted = []
        for i, step in enumerate(steps):
            desc = step.get('description', '')
            code = step.get('code', '')
            if code:
                formatted.append(f"Step {i+1}: {desc}\n```\n{code}\n```")
            else:
                formatted.append(f"Step {i+1}: {desc}")

        return "\n\n".join(formatted)

    def _parse_enhancement_response(self, response: str, guide_data: Dict) -> Dict:
        """
        Parse AI enhancement response.

        Args:
            response: AI response text (should be JSON)
            guide_data: Original guide data

        Returns:
            Enhanced guide data
        """
        try:
            # Try to extract JSON from response (in case there's extra text)
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_text = response[json_start:json_end]
                data = json.loads(json_text)
            else:
                data = json.loads(response)

            # Merge enhancements into guide_data
            enhanced = guide_data.copy()

            # Step descriptions
            if 'step_descriptions' in data:
                enhanced['step_enhancements'] = [
                    StepEnhancement(
                        step_index=item.get('step_index', i),
                        explanation=item.get('explanation', ''),
                        variations=item.get('variations', [])
                    )
                    for i, item in enumerate(data['step_descriptions'])
                ]

            # Troubleshooting
            if 'troubleshooting' in data:
                enhanced['troubleshooting_detailed'] = [
                    TroubleshootingItem(
                        problem=item.get('problem', ''),
                        symptoms=item.get('symptoms', []),
                        diagnostic_steps=item.get('diagnostic_steps', []),
                        solution=item.get('solution', '')
                    )
                    for item in data['troubleshooting']
                ]

            # Prerequisites
            if 'prerequisites_detailed' in data:
                enhanced['prerequisites_detailed'] = [
                    PrerequisiteItem(
                        name=item.get('name', ''),
                        why=item.get('why', ''),
                        setup=item.get('setup', '')
                    )
                    for item in data['prerequisites_detailed']
                ]

            # Next steps
            if 'next_steps' in data:
                enhanced['next_steps_detailed'] = data['next_steps']

            # Use cases
            if 'use_cases' in data:
                enhanced['use_cases'] = data['use_cases']

            logger.info("✅ Successfully enhanced guide with all 5 improvements")
            return enhanced

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"⚠️  Failed to parse AI response: {e}")
            logger.debug(f"Response was: {response[:500]}...")
            return guide_data
