#!/usr/bin/env python3
"""
AI Enhancement Module for Pattern Detection and Test Examples

Enhances C3.1 (Pattern Detection) and C3.2 (Test Example Extraction) with AI analysis.

Features:
- Explains why patterns were detected
- Suggests improvements and identifies issues
- Recommends related patterns
- Adds context to test examples
- Groups related examples into tutorials
- Identifies best practices

Modes:
- API mode: Uses AI API (Anthropic, Moonshot/Kimi, Google, OpenAI)
- LOCAL mode: Uses AI coding agent CLI (Claude Code, Kimi, Codex, Copilot, OpenCode)
- AUTO mode: Tries API first, falls back to LOCAL

Uses AgentClient for all AI invocations — fully agent-agnostic.
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Import config manager for settings
try:
    from skill_seekers.cli.config_manager import get_config_manager

    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False


@dataclass
class AIAnalysis:
    """AI analysis result for patterns or examples"""

    explanation: str
    issues: list[str]
    recommendations: list[str]
    related_items: list[str]  # Related patterns or examples
    best_practices: list[str]
    confidence_boost: float  # -0.2 to +0.2 adjustment to confidence


class AIEnhancer:
    """Base class for AI enhancement — delegates to AgentClient for all AI calls."""

    def __init__(
        self,
        api_key: str | None = None,
        enabled: bool = True,
        mode: str = "auto",
        agent: str | None = None,
    ):
        """
        Initialize AI enhancer.

        Args:
            api_key: API key (auto-detected from env if None)
            enabled: Enable AI enhancement (default: True)
            mode: Enhancement mode - "auto" (default), "api", or "local"
            agent: Local CLI agent name (e.g., "kimi", "claude")
        """
        self.enabled = enabled

        # Get settings from config (with defaults)
        if CONFIG_AVAILABLE:
            config = get_config_manager()
            self.local_batch_size = config.get_local_batch_size()
            self.local_parallel_workers = config.get_local_parallel_workers()
        else:
            self.local_batch_size = 20
            self.local_parallel_workers = 3

        # Initialize AgentClient
        from skill_seekers.cli.agent_client import AgentClient

        self._agent = AgentClient(mode=mode, api_key=api_key, agent=agent)
        self.mode = self._agent.mode
        self.client = self._agent.client  # For backward compatibility

        if self.enabled:
            if self._agent.is_available():
                self._agent.log_mode()
            else:
                logger.warning(
                    f"⚠️  {self._agent.agent_display} not available. AI enhancement disabled."
                )
                self.enabled = False

    def _call_claude(self, prompt: str, max_tokens: int = 1000) -> str | None:
        """Call AI agent (API or LOCAL mode) with error handling.

        Named _call_claude for backward compatibility — delegates to AgentClient.
        """
        return self._agent.call(prompt, max_tokens=max_tokens)

    def call(self, prompt: str, max_tokens: int = 1000) -> str | None:
        """Call AI agent — preferred method name over _call_claude."""
        return self._agent.call(prompt, max_tokens=max_tokens)


class PatternEnhancer(AIEnhancer):
    """Enhance design pattern detection with AI analysis"""

    def enhance_patterns(self, patterns: list[dict]) -> list[dict]:
        """
        Enhance detected patterns with AI analysis.

        Args:
            patterns: List of detected pattern instances

        Returns:
            Enhanced patterns with AI analysis
        """
        if not self.enabled or not patterns:
            return patterns

        # Use larger batch size for LOCAL mode (configurable)
        if self.mode == "local":
            batch_size = self.local_batch_size
            parallel_workers = self.local_parallel_workers
            logger.info(
                f"🤖 Enhancing {len(patterns)} patterns with AI "
                f"(LOCAL mode: {batch_size} per batch, {parallel_workers} parallel workers)..."
            )
        else:
            batch_size = 5  # API mode uses smaller batches
            parallel_workers = 1  # API mode is sequential
            logger.info(f"🤖 Enhancing {len(patterns)} detected patterns with AI...")

        # Create batches
        batches = []
        for i in range(0, len(patterns), batch_size):
            batches.append(patterns[i : i + batch_size])

        # Process batches (parallel for LOCAL, sequential for API)
        if parallel_workers > 1 and len(batches) > 1:
            enhanced = self._enhance_patterns_parallel(batches, parallel_workers)
        else:
            enhanced = []
            for batch in batches:
                batch_results = self._enhance_pattern_batch(batch)
                enhanced.extend(batch_results)

        logger.info(f"✅ Enhanced {len(enhanced)} patterns")
        return enhanced

    def _enhance_patterns_parallel(self, batches: list[list[dict]], workers: int) -> list[dict]:
        """Process pattern batches in parallel using ThreadPoolExecutor."""
        results = [None] * len(batches)  # Preserve order

        with ThreadPoolExecutor(max_workers=workers) as executor:
            # Submit all batches
            future_to_idx = {
                executor.submit(self._enhance_pattern_batch, batch): idx
                for idx, batch in enumerate(batches)
            }

            # Collect results as they complete
            completed = 0
            total = len(batches)
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    results[idx] = future.result()
                    completed += 1
                    # Show progress: always for small jobs (<10), every 5 for larger jobs
                    if total < 10 or completed % 5 == 0 or completed == total:
                        logger.info(f"   Progress: {completed}/{total} batches completed")
                except Exception as e:
                    logger.warning(f"⚠️  Batch {idx} failed: {e}")
                    results[idx] = batches[idx]  # Return unenhanced on failure

        # Flatten results
        enhanced = []
        for batch_result in results:
            if batch_result:
                enhanced.extend(batch_result)
        return enhanced

    def _enhance_pattern_batch(self, patterns: list[dict]) -> list[dict]:
        """Enhance a batch of patterns"""
        # Prepare prompt
        pattern_descriptions = []
        for idx, p in enumerate(patterns):
            desc = f"{idx + 1}. {p['pattern_type']} in {p.get('class_name', 'unknown')}"
            desc += f"\n   Evidence: {', '.join(p.get('evidence', []))}"
            pattern_descriptions.append(desc)

        prompt = f"""Analyze these detected design patterns and provide insights:

{chr(10).join(pattern_descriptions)}

For EACH pattern, provide (in JSON format):
1. "explanation": Brief why this pattern was detected (1-2 sentences)
2. "issues": List of potential issues or anti-patterns (if any)
3. "recommendations": Suggestions for improvement (if any)
4. "related_patterns": Other patterns that might be relevant
5. "confidence_boost": Confidence adjustment from -0.2 to +0.2 based on evidence quality

Format as JSON array matching input order. Be concise and actionable.
"""

        response = self._call_claude(prompt, max_tokens=2000)

        if not response:
            # Return patterns unchanged if API fails
            return patterns

        try:
            analyses = json.loads(response)

            # Merge AI analysis into patterns
            for idx, pattern in enumerate(patterns):
                if idx < len(analyses):
                    analysis = analyses[idx]
                    pattern["ai_analysis"] = {
                        "explanation": analysis.get("explanation", ""),
                        "issues": analysis.get("issues", []),
                        "recommendations": analysis.get("recommendations", []),
                        "related_patterns": analysis.get("related_patterns", []),
                        "confidence_boost": analysis.get("confidence_boost", 0.0),
                    }

                    # Adjust confidence
                    boost = analysis.get("confidence_boost", 0.0)
                    if -0.2 <= boost <= 0.2:
                        pattern["confidence"] = min(1.0, max(0.0, pattern["confidence"] + boost))

            return patterns

        except json.JSONDecodeError:
            logger.warning("⚠️  Failed to parse AI response, returning patterns unchanged")
            return patterns
        except Exception as e:
            logger.warning(f"⚠️  Error processing AI analysis: {e}")
            return patterns


class TestExampleEnhancer(AIEnhancer):
    """Enhance test examples with AI analysis"""

    def enhance_examples(self, examples: list[dict]) -> list[dict]:
        """
        Enhance test examples with AI context and explanations.

        Args:
            examples: List of extracted test examples

        Returns:
            Enhanced examples with AI analysis
        """
        if not self.enabled or not examples:
            return examples

        # Use larger batch size for LOCAL mode (configurable)
        if self.mode == "local":
            batch_size = self.local_batch_size
            parallel_workers = self.local_parallel_workers
            logger.info(
                f"🤖 Enhancing {len(examples)} test examples with AI "
                f"(LOCAL mode: {batch_size} per batch, {parallel_workers} parallel workers)..."
            )
        else:
            batch_size = 5  # API mode uses smaller batches
            parallel_workers = 1  # API mode is sequential
            logger.info(f"🤖 Enhancing {len(examples)} test examples with AI...")

        # Create batches
        batches = []
        for i in range(0, len(examples), batch_size):
            batches.append(examples[i : i + batch_size])

        # Process batches (parallel for LOCAL, sequential for API)
        if parallel_workers > 1 and len(batches) > 1:
            enhanced = self._enhance_examples_parallel(batches, parallel_workers)
        else:
            enhanced = []
            for batch in batches:
                batch_results = self._enhance_example_batch(batch)
                enhanced.extend(batch_results)

        logger.info(f"✅ Enhanced {len(enhanced)} examples")
        return enhanced

    def _enhance_examples_parallel(self, batches: list[list[dict]], workers: int) -> list[dict]:
        """Process example batches in parallel using ThreadPoolExecutor."""
        results = [None] * len(batches)  # Preserve order

        with ThreadPoolExecutor(max_workers=workers) as executor:
            # Submit all batches
            future_to_idx = {
                executor.submit(self._enhance_example_batch, batch): idx
                for idx, batch in enumerate(batches)
            }

            # Collect results as they complete
            completed = 0
            total = len(batches)
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    results[idx] = future.result()
                    completed += 1
                    # Show progress: always for small jobs (<10), every 5 for larger jobs
                    if total < 10 or completed % 5 == 0 or completed == total:
                        logger.info(f"   Progress: {completed}/{total} batches completed")
                except Exception as e:
                    logger.warning(f"⚠️  Batch {idx} failed: {e}")
                    results[idx] = batches[idx]  # Return unenhanced on failure

        # Flatten results
        enhanced = []
        for batch_result in results:
            if batch_result:
                enhanced.extend(batch_result)
        return enhanced

    def _enhance_example_batch(self, examples: list[dict]) -> list[dict]:
        """Enhance a batch of examples"""
        # Prepare prompt
        example_descriptions = []
        for idx, ex in enumerate(examples):
            desc = f"{idx + 1}. {ex.get('category', 'unknown')} - {ex.get('test_name', 'unknown')}"
            desc += f"\n   Code: {ex.get('code', '')[:100]}..."
            if ex.get("expected_behavior"):
                desc += f"\n   Expected: {ex['expected_behavior']}"
            example_descriptions.append(desc)

        prompt = f"""Analyze these test examples and provide educational context:

{chr(10).join(example_descriptions)}

For EACH example, provide (in JSON format):
1. "explanation": What this example demonstrates (1-2 sentences, beginner-friendly)
2. "best_practices": List of best practices shown in this example
3. "common_mistakes": Common mistakes this example helps avoid
4. "related_examples": Related test scenarios or patterns
5. "tutorial_group": Suggested tutorial category (e.g., "User Authentication", "Database Operations")

Format as JSON array matching input order. Focus on educational value.
"""

        response = self._call_claude(prompt, max_tokens=2000)

        if not response:
            return examples

        try:
            analyses = json.loads(response)

            # Merge AI analysis into examples
            for idx, example in enumerate(examples):
                if idx < len(analyses):
                    analysis = analyses[idx]
                    example["ai_analysis"] = {
                        "explanation": analysis.get("explanation", ""),
                        "best_practices": analysis.get("best_practices", []),
                        "common_mistakes": analysis.get("common_mistakes", []),
                        "related_examples": analysis.get("related_examples", []),
                        "tutorial_group": analysis.get("tutorial_group", ""),
                    }

            return examples

        except json.JSONDecodeError:
            logger.warning("⚠️  Failed to parse AI response, returning examples unchanged")
            return examples
        except Exception as e:
            logger.warning(f"⚠️  Error processing AI analysis: {e}")
            return examples

    def generate_tutorials(self, examples: list[dict]) -> dict[str, list[dict]]:
        """
        Group enhanced examples into tutorial sections.

        Args:
            examples: Enhanced examples with AI analysis

        Returns:
            Dictionary mapping tutorial groups to examples
        """
        tutorials = {}

        for example in examples:
            ai_analysis = example.get("ai_analysis", {})
            group = ai_analysis.get("tutorial_group", "Miscellaneous")

            if group not in tutorials:
                tutorials[group] = []
            tutorials[group].append(example)

        return tutorials
