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
- API mode: Uses Claude API (requires ANTHROPIC_API_KEY)
- LOCAL mode: Uses Claude Code CLI (no API key needed, uses your Claude Max plan)
- AUTO mode: Tries API first, falls back to LOCAL

Credits:
- Uses Claude AI (Anthropic) for analysis
- Graceful degradation if API unavailable
"""

import json
import logging
import os
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

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
    """Base class for AI enhancement"""

    def __init__(self, api_key: str | None = None, enabled: bool = True, mode: str = "auto"):
        """
        Initialize AI enhancer.

        Args:
            api_key: Anthropic API key (uses ANTHROPIC_API_KEY env if None)
            enabled: Enable AI enhancement (default: True)
            mode: Enhancement mode - "auto" (default), "api", or "local"
                  - "auto": Use API if key available, otherwise fall back to LOCAL
                  - "api": Force API mode (fails if no key)
                  - "local": Use Claude Code CLI (no API key needed)
        """
        self.enabled = enabled
        self.mode = mode
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.client = None

        # Get settings from config (with defaults)
        if CONFIG_AVAILABLE:
            config = get_config_manager()
            self.local_batch_size = config.get_local_batch_size()
            self.local_parallel_workers = config.get_local_parallel_workers()
        else:
            self.local_batch_size = 20  # Default
            self.local_parallel_workers = 3  # Default

        # Determine actual mode
        if mode == "auto":
            if self.api_key:
                self.mode = "api"
            else:
                # Fall back to LOCAL mode (Claude Code CLI)
                self.mode = "local"
                logger.info("ℹ️  No API key found, using LOCAL mode (Claude Code CLI)")

        if self.mode == "api" and self.enabled:
            try:
                import anthropic

                # Support custom base_url for GLM-4.7 and other Claude-compatible APIs
                client_kwargs = {"api_key": self.api_key}
                base_url = os.environ.get("ANTHROPIC_BASE_URL")
                if base_url:
                    client_kwargs["base_url"] = base_url
                    logger.info(f"✅ Using custom API base URL: {base_url}")
                self.client = anthropic.Anthropic(**client_kwargs)
                logger.info("✅ AI enhancement enabled (using Claude API)")
            except ImportError:
                logger.warning("⚠️  anthropic package not installed, falling back to LOCAL mode")
                self.mode = "local"
            except Exception as e:
                logger.warning(f"⚠️  Failed to initialize API client: {e}, falling back to LOCAL mode")
                self.mode = "local"

        if self.mode == "local" and self.enabled:
            # Verify Claude CLI is available
            if self._check_claude_cli():
                logger.info("✅ AI enhancement enabled (using LOCAL mode - Claude Code CLI)")
            else:
                logger.warning("⚠️  Claude Code CLI not found. AI enhancement disabled.")
                logger.warning("   Install with: npm install -g @anthropic-ai/claude-code")
                self.enabled = False

    def _check_claude_cli(self) -> bool:
        """Check if Claude Code CLI is available"""
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _call_claude(self, prompt: str, max_tokens: int = 1000) -> str | None:
        """Call Claude (API or LOCAL mode) with error handling"""
        if self.mode == "api":
            return self._call_claude_api(prompt, max_tokens)
        elif self.mode == "local":
            return self._call_claude_local(prompt)
        return None

    def _call_claude_api(self, prompt: str, max_tokens: int = 1000) -> str | None:
        """Call Claude API"""
        if not self.client:
            return None

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as e:
            logger.warning(f"⚠️  AI API call failed: {e}")
            return None

    def _call_claude_local(self, prompt: str) -> str | None:
        """Call Claude using LOCAL mode (Claude Code CLI)"""
        try:
            # Create a temporary directory for this enhancement
            with tempfile.TemporaryDirectory(prefix="ai_enhance_") as temp_dir:
                temp_path = Path(temp_dir)

                # Create prompt file
                prompt_file = temp_path / "prompt.md"
                output_file = temp_path / "response.json"

                # Write prompt with instructions to output JSON
                full_prompt = f"""# AI Analysis Task

IMPORTANT: You MUST write your response as valid JSON to this file:
{output_file}

## Task

{prompt}

## Instructions

1. Analyze the input carefully
2. Generate the JSON response as specified
3. Use the Write tool to save the JSON to: {output_file}
4. The JSON must be valid and parseable

DO NOT include any explanation - just write the JSON file.
"""
                prompt_file.write_text(full_prompt)

                # Run Claude CLI
                result = subprocess.run(
                    ["claude", "--dangerously-skip-permissions", str(prompt_file)],
                    capture_output=True,
                    text=True,
                    timeout=120,  # 2 minute timeout per call
                    cwd=str(temp_path),
                )

                if result.returncode != 0:
                    logger.warning(f"⚠️  Claude CLI returned error: {result.returncode}")
                    return None

                # Read output file
                if output_file.exists():
                    response_text = output_file.read_text()
                    # Try to extract JSON from response
                    try:
                        # Validate it's valid JSON
                        json.loads(response_text)
                        return response_text
                    except json.JSONDecodeError:
                        # Try to find JSON in the response
                        import re
                        json_match = re.search(r'\[[\s\S]*\]|\{[\s\S]*\}', response_text)
                        if json_match:
                            return json_match.group()
                        logger.warning("⚠️  Could not parse JSON from LOCAL response")
                        return None
                else:
                    # Look for any JSON file created
                    for json_file in temp_path.glob("*.json"):
                        if json_file.name != "prompt.json":
                            return json_file.read_text()
                    logger.warning("⚠️  No output file from LOCAL mode")
                    return None

        except subprocess.TimeoutExpired:
            logger.warning("⚠️  Claude CLI timeout (2 minutes)")
            return None
        except Exception as e:
            logger.warning(f"⚠️  LOCAL mode error: {e}")
            return None


class PatternEnhancer(AIEnhancer):
    """Enhance design pattern detection with AI analysis"""

    # Maximum samples per pattern type to analyze (avoids analyzing 1000s of similar patterns)
    MAX_SAMPLES_PER_TYPE = 5

    def enhance_patterns(self, patterns: list[dict]) -> list[dict]:
        """
        Enhance detected patterns with AI analysis.

        Groups similar patterns by type and analyzes representative samples,
        then applies the analysis to all patterns of that type.

        Args:
            patterns: List of detected pattern instances

        Returns:
            Enhanced patterns with AI analysis
        """
        if not self.enabled or not patterns:
            return patterns

        total_patterns = len(patterns)

        # Group patterns by type to avoid redundant analysis
        grouped = self._group_patterns_by_type(patterns)
        unique_types = len(grouped)

        logger.info(
            f"🤖 Grouped {total_patterns} patterns into {unique_types} types "
            f"(analyzing {self.MAX_SAMPLES_PER_TYPE} samples per type max)"
        )

        # Enhance each pattern type with representative samples
        enhanced_patterns = []
        for idx, (pattern_type, type_patterns) in enumerate(grouped.items()):
            # Select diverse samples (up to MAX_SAMPLES_PER_TYPE)
            samples = self._select_diverse_samples(type_patterns, self.MAX_SAMPLES_PER_TYPE)

            logger.info(
                f"   [{idx + 1}/{unique_types}] Enhancing {pattern_type} "
                f"({len(samples)} samples from {len(type_patterns)} instances)"
            )

            # Get AI analysis for samples
            sample_analysis = self._enhance_pattern_type(pattern_type, samples)

            # Apply analysis to ALL patterns of this type
            for pattern in type_patterns:
                pattern["ai_analysis"] = sample_analysis
                enhanced_patterns.append(pattern)

        logger.info(f"✅ Enhanced {unique_types} pattern types ({total_patterns} total instances)")
        return enhanced_patterns

    def _group_patterns_by_type(self, patterns: list[dict]) -> dict[str, list[dict]]:
        """Group patterns by their type (Factory, Observer, etc.)"""
        grouped: dict[str, list[dict]] = {}
        for pattern in patterns:
            pattern_type = pattern.get("pattern_type", "Unknown")
            if pattern_type not in grouped:
                grouped[pattern_type] = []
            grouped[pattern_type].append(pattern)
        return grouped

    def _select_diverse_samples(self, patterns: list[dict], max_samples: int) -> list[dict]:
        """Select diverse samples from patterns (different files, classes)"""
        if len(patterns) <= max_samples:
            return patterns

        # Try to get samples from different files/classes for diversity
        seen_files = set()
        samples = []

        for pattern in patterns:
            file_path = pattern.get("file_path", "")
            if file_path not in seen_files:
                samples.append(pattern)
                seen_files.add(file_path)
                if len(samples) >= max_samples:
                    break

        # If not enough diverse samples, just take first N
        if len(samples) < max_samples:
            for pattern in patterns:
                if pattern not in samples:
                    samples.append(pattern)
                    if len(samples) >= max_samples:
                        break

        return samples

    def _enhance_pattern_type(self, pattern_type: str, samples: list[dict]) -> dict:
        """Enhance a pattern type with AI analysis based on samples"""
        # Prepare sample descriptions
        sample_descriptions = []
        for idx, p in enumerate(samples):
            desc = f"{idx + 1}. {p.get('class_name', 'unknown')} in {p.get('file_path', 'unknown')}"
            desc += f"\n   Evidence: {', '.join(p.get('evidence', []))}"
            sample_descriptions.append(desc)

        prompt = f"""Analyze this {pattern_type} design pattern usage based on these representative samples:

{chr(10).join(sample_descriptions)}

Provide a SINGLE analysis that applies to all {pattern_type} patterns in this codebase:

1. "explanation": Why this pattern is commonly used here (1-2 sentences)
2. "common_issues": List of potential issues to watch for with this pattern
3. "best_practices": Recommendations for using this pattern well
4. "related_patterns": Other patterns often used alongside this one
5. "overall_quality": Assessment of how well this pattern is used (good/fair/needs_review)

Format as a single JSON object. Be concise and actionable.
"""

        response = self._call_claude(prompt, max_tokens=1000)

        if not response:
            return {"explanation": f"{pattern_type} pattern detected", "enhanced": False}

        try:
            analysis = json.loads(response)
            analysis["enhanced"] = True
            analysis["samples_analyzed"] = len(samples)
            return analysis
        except json.JSONDecodeError:
            logger.warning(f"⚠️  Failed to parse AI response for {pattern_type}")
            return {"explanation": f"{pattern_type} pattern detected", "enhanced": False}


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

        total_examples = len(examples)

        # Use larger batch size for LOCAL mode (configurable)
        if self.mode == "local":
            batch_size = self.local_batch_size
            parallel_workers = self.local_parallel_workers
        else:
            batch_size = 5  # API mode uses smaller batches
            parallel_workers = 1  # API mode is sequential

        # Create batches
        batches = []
        for i in range(0, len(examples), batch_size):
            batches.append(examples[i : i + batch_size])

        total_batches = len(batches)

        # Log initial progress info
        logger.info(
            f"🤖 Enhancing {total_examples} test examples with AI "
            f"({self.mode.upper()} mode, {total_batches} batches of ~{batch_size})"
        )
        logger.info(f"   [0/{total_examples}] 0% - Starting enhancement...")

        # Process batches (parallel for LOCAL, sequential for API)
        if parallel_workers > 1 and len(batches) > 1:
            enhanced = self._enhance_examples_parallel(
                batches, parallel_workers, total_examples
            )
        else:
            enhanced = []
            processed = 0
            for batch_idx, batch in enumerate(batches):
                batch_results = self._enhance_example_batch(batch)
                enhanced.extend(batch_results)
                processed += len(batch)
                percent = int((processed / total_examples) * 100)
                logger.info(
                    f"   [{processed}/{total_examples}] {percent}% - "
                    f"Batch {batch_idx + 1}/{total_batches} complete"
                )

        logger.info(f"✅ Enhanced {len(enhanced)}/{total_examples} test examples (100%)")
        return enhanced

    def _enhance_examples_parallel(
        self, batches: list[list[dict]], workers: int, total_items: int
    ) -> list[dict]:
        """Process example batches in parallel using ThreadPoolExecutor."""
        results = [None] * len(batches)  # Preserve order
        batch_sizes = [len(b) for b in batches]  # Track size of each batch

        with ThreadPoolExecutor(max_workers=workers) as executor:
            # Submit all batches
            future_to_idx = {
                executor.submit(self._enhance_example_batch, batch): idx
                for idx, batch in enumerate(batches)
            }

            # Collect results as they complete
            completed_batches = 0
            completed_items = 0
            total_batches = len(batches)

            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    results[idx] = future.result()
                    completed_batches += 1
                    completed_items += batch_sizes[idx]
                    percent = int((completed_items / total_items) * 100)
                    logger.info(
                        f"   [{completed_items}/{total_items}] {percent}% - "
                        f"Batch {completed_batches}/{total_batches} complete"
                    )
                except Exception as e:
                    logger.warning(f"⚠️  Batch {idx} failed: {e}")
                    results[idx] = batches[idx]  # Return unenhanced on failure
                    completed_batches += 1
                    completed_items += batch_sizes[idx]

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
