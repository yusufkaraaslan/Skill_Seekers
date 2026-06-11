#!/usr/bin/env python3
"""
Unified AI Enhancement System

Target single interface for the per-feature enhancer classes (the
consolidation itself is Phase 3 of docs/UNIFICATION_PLAN.md — today the
canonical implementations still live in their own modules):
- PatternEnhancer (C3.1, ai_enhancer.py)
- TestExampleEnhancer (C3.2, ai_enhancer.py)
- GuideEnhancer (C3.3, guide_enhancer.py)
- ConfigEnhancer (C3.4, config_enhancer.py)
- SkillEnhancer (SKILL.md, enhance_skill.py)

Benefits:
- Single source of truth
- No code duplication
- Consistent behavior
- Easy to maintain
- Supports custom prompts via workflow system
"""

import json
import logging
from dataclasses import dataclass
from typing import Literal

from skill_seekers.cli.parallel_batches import flatten_batch_results, run_batches_parallel

logger = logging.getLogger(__name__)

# Import config manager for settings
try:
    from skill_seekers.cli.config_manager import get_config_manager

    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False


@dataclass
class EnhancementConfig:
    """Configuration for enhancement."""

    mode: Literal["auto", "api", "local"] = "auto"
    batch_size: int = 20
    parallel_workers: int = 3
    enabled: bool = True
    api_key: str | None = None


class UnifiedEnhancer:
    """
    Single unified AI enhancement system.

    Supports all enhancement types:
    - patterns: Design pattern analysis
    - examples: Test example context
    - guides: How-to guide enhancement
    - config: Configuration pattern analysis
    - skill: SKILL.md enhancement
    - custom: Custom prompts via workflow system
    """

    def __init__(
        self,
        mode: str = "auto",
        api_key: str | None = None,
        enabled: bool = True,
        config: EnhancementConfig | None = None,
    ):
        """
        Initialize unified enhancer.

        Args:
            mode: Enhancement mode - "auto", "api", or "local"
            api_key: Anthropic API key (uses env if None)
            enabled: Enable AI enhancement
            config: Optional EnhancementConfig object
        """
        if config:
            self.config = config
        else:
            self.config = EnhancementConfig(mode=mode, api_key=api_key, enabled=enabled)

        # Get settings from config manager
        if CONFIG_AVAILABLE:
            cfg = get_config_manager()
            self.config.batch_size = cfg.get_local_batch_size()
            self.config.parallel_workers = cfg.get_local_parallel_workers()

        # Initialize AgentClient for AI calls
        from skill_seekers.cli.agent_client import AgentClient

        self._agent = AgentClient(
            mode=self.config.mode,
            api_key=self.config.api_key,
        )

        # Sync resolved mode back to config
        self.config.mode = self._agent.mode

        if self.config.enabled:
            if self._agent.is_available():
                self._agent.log_mode()
            else:
                logger.warning("⚠️  AI agent not available. AI enhancement disabled.")
                self.config.enabled = False

    def enhance(
        self,
        items: list[dict],
        enhancement_type: str,
        custom_prompt: str | None = None,
    ) -> list[dict]:
        """
        Universal enhancement method.

        Args:
            items: List of items to enhance (patterns, examples, guides, etc.)
            enhancement_type: Type of enhancement ("pattern", "example", "guide", "config", "skill", "custom")
            custom_prompt: Optional custom prompt (overrides default)

        Returns:
            Enhanced items
        """
        if not self.config.enabled or not items:
            return items

        # Get appropriate prompt
        prompt_template = custom_prompt or self._get_default_prompt(enhancement_type)

        # Batch processing
        batch_size = (
            self.config.batch_size if self.config.mode == "local" else 5  # API uses smaller batches
        )
        parallel_workers = self.config.parallel_workers if self.config.mode == "local" else 1

        logger.info(
            f"🤖 Enhancing {len(items)} {enhancement_type}s with AI "
            f"({self.config.mode.upper()} mode: {batch_size} per batch, {parallel_workers} workers)..."
        )

        # Create batches
        batches = []
        for i in range(0, len(items), batch_size):
            batches.append(items[i : i + batch_size])

        # Process batches (parallel for LOCAL, sequential for API)
        if parallel_workers > 1 and len(batches) > 1:
            enhanced = self._enhance_parallel(batches, prompt_template)
        else:
            enhanced = []
            for batch in batches:
                batch_results = self._enhance_batch(batch, prompt_template)
                enhanced.extend(batch_results)

        logger.info(f"✅ Enhanced {len(enhanced)} {enhancement_type}s")
        return enhanced

    def _enhance_parallel(self, batches: list[list[dict]], prompt_template: str) -> list[dict]:
        """Process batches in parallel using ThreadPoolExecutor."""
        results = run_batches_parallel(
            batches,
            lambda batch: self._enhance_batch(batch, prompt_template),
            self.config.parallel_workers,
            log=logger.info,
            warn=logger.warning,
        )
        return flatten_batch_results(results)

    def _enhance_batch(self, items: list[dict], prompt_template: str) -> list[dict]:
        """Enhance a batch of items."""
        # Prepare prompt
        item_descriptions = []
        for idx, item in enumerate(items):
            desc = self._format_item_for_prompt(idx, item)
            item_descriptions.append(desc)

        prompt = prompt_template.format(items="\n".join(item_descriptions), count=len(items))

        # Call AI
        response = self._call_claude(prompt, max_tokens=3000)

        if not response:
            return items

        # Parse response and merge with items
        try:
            analyses = json.loads(response)

            for idx, item in enumerate(items):
                if idx < len(analyses):
                    analysis = analyses[idx]
                    item["ai_analysis"] = analysis

                    # Apply confidence boost if present
                    if "confidence_boost" in analysis and "confidence" in item:
                        boost = analysis["confidence_boost"]
                        if -0.2 <= boost <= 0.2:
                            item["confidence"] = min(1.0, max(0.0, item["confidence"] + boost))

            return items

        except json.JSONDecodeError:
            logger.warning("⚠️  Failed to parse AI response, returning items unchanged")
            return items
        except Exception as e:
            logger.warning(f"⚠️  Error processing AI analysis: {e}")
            return items

    def _call_claude(self, prompt: str, max_tokens: int = 1000) -> str | None:
        """Call AI agent (API or LOCAL mode) via AgentClient."""
        from skill_seekers.cli.agent_client import get_default_timeout

        timeout = get_default_timeout() if self._agent.mode == "local" else None
        return self._agent.call(prompt, max_tokens=max_tokens, timeout=timeout)

    def _get_default_prompt(self, enhancement_type: str) -> str:
        """Get default prompt for enhancement type."""
        prompts = {
            "pattern": """Analyze these {count} design patterns and provide insights:

{items}

For EACH pattern, provide (in JSON format):
1. "explanation": Brief why this pattern was detected (1-2 sentences)
2. "issues": List of potential issues or anti-patterns (if any)
3. "recommendations": Suggestions for improvement (if any)
4. "related_patterns": Other patterns that might be relevant
5. "confidence_boost": Confidence adjustment from -0.2 to +0.2

Format as JSON array matching input order. Be concise and actionable.""",
            "example": """Analyze these {count} test examples and provide context:

{items}

For EACH example, provide (in JSON format):
1. "context": What this example demonstrates (1-2 sentences)
2. "best_practices": What's done well
3. "common_use_cases": When to use this pattern
4. "related_examples": Similar examples
5. "confidence_boost": Confidence adjustment from -0.2 to +0.2

Format as JSON array matching input order.""",
            "guide": """Enhance these {count} how-to guides:

{items}

For EACH guide, add:
1. "prerequisites": What users need to know first
2. "troubleshooting": Common issues and solutions
3. "next_steps": What to learn after this
4. "use_cases": Real-world scenarios

Format as JSON array.""",
            "config": """Analyze these {count} configuration patterns:

{items}

For EACH pattern, provide:
1. "purpose": Why this configuration exists
2. "common_values": Typical values used
3. "security_implications": Any security concerns
4. "best_practices": Recommended configuration

Format as JSON array.""",
        }

        return prompts.get(enhancement_type, prompts["pattern"])

    def _format_item_for_prompt(self, idx: int, item: dict) -> str:
        """Format item for inclusion in prompt."""
        # Pattern formatting
        if "pattern_type" in item:
            return f"{idx + 1}. {item['pattern_type']} in {item.get('class_name', 'unknown')}\n   Evidence: {', '.join(item.get('evidence', []))}"

        # Example formatting
        elif "category" in item and "code" in item:
            return f"{idx + 1}. {item['category']}: {item['code'][:100]}"

        # Generic formatting
        else:
            desc = item.get("description", item.get("name", str(item)))
            return f"{idx + 1}. {desc}"


# NOTE: this module used to define "backward compatibility" subclasses named
# PatternEnhancer / TestExampleEnhancer / GuideEnhancer / ConfigEnhancer plus
# an `AIEnhancer = UnifiedEnhancer` alias. They had ZERO importers and
# collided with the real, in-use classes of the same names in ai_enhancer.py,
# guide_enhancer.py, and config_enhancer.py — so they were removed. The
# consolidation of those hierarchies into this module is Phase 3 of
# docs/UNIFICATION_PLAN.md; until then, the per-feature modules are canonical.

if __name__ == "__main__":
    # Quick test
    enhancer = UnifiedEnhancer(mode="local", enabled=False)
    print(f"✅ Mode: {enhancer.config.mode}")
    print(f"✅ Batch size: {enhancer.config.batch_size}")
    print(f"✅ Workers: {enhancer.config.parallel_workers}")
