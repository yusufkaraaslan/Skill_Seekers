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

Credits:
- Uses Claude AI (Anthropic) for analysis
- Graceful degradation if API unavailable
"""

import os
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AIAnalysis:
    """AI analysis result for patterns or examples"""
    explanation: str
    issues: List[str]
    recommendations: List[str]
    related_items: List[str]  # Related patterns or examples
    best_practices: List[str]
    confidence_boost: float  # -0.2 to +0.2 adjustment to confidence


class AIEnhancer:
    """Base class for AI enhancement"""

    def __init__(self, api_key: Optional[str] = None, enabled: bool = True, mode: str = "auto"):
        """
        Initialize AI enhancer.

        Args:
            api_key: Anthropic API key (uses ANTHROPIC_API_KEY env if None)
            enabled: Enable AI enhancement (default: True)
            mode: Enhancement mode - "auto" (default), "api", or "local"
                  - "auto": Use API if key available, otherwise disable
                  - "api": Force API mode (fails if no key)
                  - "local": Use Claude Code local mode (opens terminal)
        """
        self.enabled = enabled
        self.mode = mode
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        self.client = None

        # Determine actual mode
        if mode == "auto":
            if self.api_key:
                self.mode = "api"
            else:
                # For now, disable if no API key
                # LOCAL mode for batch processing is complex
                self.mode = "disabled"
                self.enabled = False
                logger.info("ℹ️  AI enhancement disabled (no API key found)")
                logger.info("   Set ANTHROPIC_API_KEY to enable, or use 'skill-seekers enhance' for SKILL.md")
                return

        if self.mode == "api" and self.enabled:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("✅ AI enhancement enabled (using Claude API)")
            except ImportError:
                logger.warning("⚠️  anthropic package not installed. AI enhancement disabled.")
                logger.warning("   Install with: pip install anthropic")
                self.enabled = False
            except Exception as e:
                logger.warning(f"⚠️  Failed to initialize AI client: {e}")
                self.enabled = False
        elif self.mode == "local":
            # LOCAL mode requires Claude Code to be available
            # For patterns/examples, this is less practical than API mode
            logger.info("ℹ️  LOCAL mode not yet supported for pattern/example enhancement")
            logger.info("   Use API mode (set ANTHROPIC_API_KEY) or 'skill-seekers enhance' for SKILL.md")
            self.enabled = False

    def _call_claude(self, prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """Call Claude API with error handling"""
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
            logger.warning(f"⚠️  AI API call failed: {e}")
            return None


class PatternEnhancer(AIEnhancer):
    """Enhance design pattern detection with AI analysis"""

    def enhance_patterns(self, patterns: List[Dict]) -> List[Dict]:
        """
        Enhance detected patterns with AI analysis.

        Args:
            patterns: List of detected pattern instances

        Returns:
            Enhanced patterns with AI analysis
        """
        if not self.enabled or not patterns:
            return patterns

        logger.info(f"🤖 Enhancing {len(patterns)} detected patterns with AI...")

        # Batch patterns to minimize API calls (max 5 per batch)
        batch_size = 5
        enhanced = []

        for i in range(0, len(patterns), batch_size):
            batch = patterns[i:i+batch_size]
            batch_results = self._enhance_pattern_batch(batch)
            enhanced.extend(batch_results)

        logger.info(f"✅ Enhanced {len(enhanced)} patterns")
        return enhanced

    def _enhance_pattern_batch(self, patterns: List[Dict]) -> List[Dict]:
        """Enhance a batch of patterns"""
        # Prepare prompt
        pattern_descriptions = []
        for idx, p in enumerate(patterns):
            desc = f"{idx+1}. {p['pattern_type']} in {p.get('class_name', 'unknown')}"
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
            import json
            analyses = json.loads(response)

            # Merge AI analysis into patterns
            for idx, pattern in enumerate(patterns):
                if idx < len(analyses):
                    analysis = analyses[idx]
                    pattern['ai_analysis'] = {
                        'explanation': analysis.get('explanation', ''),
                        'issues': analysis.get('issues', []),
                        'recommendations': analysis.get('recommendations', []),
                        'related_patterns': analysis.get('related_patterns', []),
                        'confidence_boost': analysis.get('confidence_boost', 0.0)
                    }

                    # Adjust confidence
                    boost = analysis.get('confidence_boost', 0.0)
                    if -0.2 <= boost <= 0.2:
                        pattern['confidence'] = min(1.0, max(0.0, pattern['confidence'] + boost))

            return patterns

        except json.JSONDecodeError:
            logger.warning("⚠️  Failed to parse AI response, returning patterns unchanged")
            return patterns
        except Exception as e:
            logger.warning(f"⚠️  Error processing AI analysis: {e}")
            return patterns


class TestExampleEnhancer(AIEnhancer):
    """Enhance test examples with AI analysis"""

    def enhance_examples(self, examples: List[Dict]) -> List[Dict]:
        """
        Enhance test examples with AI context and explanations.

        Args:
            examples: List of extracted test examples

        Returns:
            Enhanced examples with AI analysis
        """
        if not self.enabled or not examples:
            return examples

        logger.info(f"🤖 Enhancing {len(examples)} test examples with AI...")

        # Batch examples to minimize API calls
        batch_size = 5
        enhanced = []

        for i in range(0, len(examples), batch_size):
            batch = examples[i:i+batch_size]
            batch_results = self._enhance_example_batch(batch)
            enhanced.extend(batch_results)

        logger.info(f"✅ Enhanced {len(enhanced)} examples")
        return enhanced

    def _enhance_example_batch(self, examples: List[Dict]) -> List[Dict]:
        """Enhance a batch of examples"""
        # Prepare prompt
        example_descriptions = []
        for idx, ex in enumerate(examples):
            desc = f"{idx+1}. {ex.get('category', 'unknown')} - {ex.get('test_name', 'unknown')}"
            desc += f"\n   Code: {ex.get('code', '')[:100]}..."
            if ex.get('expected_behavior'):
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
            import json
            analyses = json.loads(response)

            # Merge AI analysis into examples
            for idx, example in enumerate(examples):
                if idx < len(analyses):
                    analysis = analyses[idx]
                    example['ai_analysis'] = {
                        'explanation': analysis.get('explanation', ''),
                        'best_practices': analysis.get('best_practices', []),
                        'common_mistakes': analysis.get('common_mistakes', []),
                        'related_examples': analysis.get('related_examples', []),
                        'tutorial_group': analysis.get('tutorial_group', '')
                    }

            return examples

        except json.JSONDecodeError:
            logger.warning("⚠️  Failed to parse AI response, returning examples unchanged")
            return examples
        except Exception as e:
            logger.warning(f"⚠️  Error processing AI analysis: {e}")
            return examples

    def generate_tutorials(self, examples: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group enhanced examples into tutorial sections.

        Args:
            examples: Enhanced examples with AI analysis

        Returns:
            Dictionary mapping tutorial groups to examples
        """
        tutorials = {}

        for example in examples:
            ai_analysis = example.get('ai_analysis', {})
            group = ai_analysis.get('tutorial_group', 'Miscellaneous')

            if group not in tutorials:
                tutorials[group] = []
            tutorials[group].append(example)

        return tutorials
