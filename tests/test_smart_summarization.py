"""
Tests for smart summarization feature in enhance_skill_local.py

Tests the automatic content reduction for large skills to ensure
compatibility with Claude CLI's character limits.
"""

import pytest
from pathlib import Path
from skill_seekers.cli.enhance_skill_local import LocalSkillEnhancer


class TestSmartSummarization:
    """Test smart summarization feature for large skills"""

    def test_summarize_reference_basic(self, tmp_path):
        """Test basic summarization preserves structure"""
        enhancer = LocalSkillEnhancer(tmp_path)

        # Create a realistic reference content with more text to make summarization worthwhile
        sections = []
        for i in range(20):
            sections.append(f"""
## Section {i}

This is section {i} with detailed explanation that would benefit from summarization.
We add multiple paragraphs to make the content more realistic and substantial.
This content explains various aspects of the framework in detail.

Another paragraph with more information about this specific topic.
Technical details and explanations continue here with examples and use cases.

```python
# Example code for section {i}
def function_{i}():
    print("Section {i}")
    return {i}
```

Final paragraph wrapping up this section with concluding remarks.
""")

        content = "# Introduction\n\nThis is the framework introduction.\n" + "\n".join(sections)

        # Summarize to 30%
        summarized = enhancer.summarize_reference(content, target_ratio=0.3)

        # Verify key elements preserved
        assert "# Introduction" in summarized
        assert "```python" in summarized  # Code blocks preserved
        assert "[Content intelligently summarized" in summarized
        # For large content, summarization should reduce size
        assert len(summarized) < len(content)

    def test_summarize_preserves_code_blocks(self, tmp_path):
        """Test that code blocks are prioritized and preserved"""
        enhancer = LocalSkillEnhancer(tmp_path)

        content = """# Framework

Some text here.

```python
# Example 1
def hello():
    print("Hello")
```

More text between examples.

```python
# Example 2
def world():
    print("World")
```

Even more text.

```python
# Example 3
def important():
    return "key"
```

Final text section.
"""

        summarized = enhancer.summarize_reference(content, target_ratio=0.5)

        # Should preserve multiple code blocks
        assert summarized.count("```python") >= 2
        assert "Example 1" in summarized or "Example 2" in summarized or "Example 3" in summarized

    def test_summarize_large_content(self, tmp_path):
        """Test summarization with very large content"""
        enhancer = LocalSkillEnhancer(tmp_path)

        # Create large content (simulate 50K chars)
        sections = []
        for i in range(50):
            sections.append(f"""
## Section {i}

This is section {i} with lots of content that needs to be summarized.
We add multiple paragraphs to make it realistic.

```python
# Code example {i}
def function_{i}():
    return {i}
```

More explanatory text follows here.
Another paragraph of content.
""")

        content = "\n".join(sections)
        original_size = len(content)

        # Summarize to 30%
        summarized = enhancer.summarize_reference(content, target_ratio=0.3)
        summarized_size = len(summarized)

        # Should be significantly reduced
        assert summarized_size < original_size
        # Should be roughly 30% (allow 20-50% range due to structural constraints)
        ratio = summarized_size / original_size
        assert 0.2 <= ratio <= 0.5, f"Ratio {ratio:.2f} not in expected range"

    def test_create_prompt_without_summarization(self, tmp_path):
        """Test prompt creation with normal-sized content"""
        # Create test skill directory
        skill_dir = tmp_path / "small_skill"
        skill_dir.mkdir()

        # Create references directory with small content
        refs_dir = skill_dir / "references"
        refs_dir.mkdir()

        (refs_dir / "index.md").write_text("# Index\n\nSmall content here.")
        (refs_dir / "api.md").write_text("# API\n\n```python\ndef test(): pass\n```")

        enhancer = LocalSkillEnhancer(skill_dir)

        # Create prompt without summarization
        prompt = enhancer.create_enhancement_prompt(use_summarization=False)

        assert prompt is not None
        assert "YOUR TASK:" in prompt
        assert "REFERENCE DOCUMENTATION:" in prompt
        assert "[Content intelligently summarized" not in prompt

    def test_create_prompt_with_summarization(self, tmp_path):
        """Test prompt creation with summarization enabled"""
        # Create test skill directory
        skill_dir = tmp_path / "large_skill"
        skill_dir.mkdir()

        # Create SKILL.md
        (skill_dir / "SKILL.md").write_text("# Test Skill\n\nTest skill content.")

        # Create references directory with large content
        refs_dir = skill_dir / "references"
        refs_dir.mkdir()

        # Create large reference file (>12K chars to trigger per-file truncation)
        # Note: read_reference_files() skips index.md, so use api.md
        large_content = "\n".join([f"# Section {i}\n\nContent here with more text to make it substantial.\n\n```python\ndef func_{i}(): pass\n```\n" for i in range(200)])
        (refs_dir / "api.md").write_text(large_content)

        enhancer = LocalSkillEnhancer(skill_dir)

        # Create prompt with summarization
        prompt = enhancer.create_enhancement_prompt(use_summarization=True, summarization_ratio=0.3)

        assert prompt is not None
        assert "YOUR TASK:" in prompt
        assert "REFERENCE DOCUMENTATION:" in prompt
        # After summarization, content should include the marker
        assert "[Content intelligently summarized" in prompt or "[Content truncated for size...]" in prompt

    def test_run_detects_large_skill(self, tmp_path, monkeypatch, capsys):
        """Test that run() automatically detects large skills"""
        # Create test skill directory with large content
        skill_dir = tmp_path / "large_skill"
        skill_dir.mkdir()

        refs_dir = skill_dir / "references"
        refs_dir.mkdir()

        # Create SKILL.md (required for skill directory validation)
        (skill_dir / "SKILL.md").write_text("# Test Skill\n\nTest skill content.")

        # Create content that exceeds 30K threshold
        # Note: read_reference_files() skips index.md, so use different names
        large_content = "\n".join([f"# Section {i}\n\n" + "Content with detailed explanations " * 50 + "\n\n```python\ndef func_{i}(): pass\n```\n" for i in range(150)])
        (refs_dir / "api.md").write_text(large_content)
        # Add more reference files to ensure we exceed 30K
        (refs_dir / "guide.md").write_text(large_content)
        (refs_dir / "tutorial.md").write_text(large_content[:len(large_content)//2])  # Half size

        enhancer = LocalSkillEnhancer(skill_dir)

        # Mock the headless run to avoid actually calling Claude
        def mock_headless(prompt_file, timeout):
            return True

        monkeypatch.setattr(enhancer, '_run_headless', mock_headless)

        # Run enhancement
        result = enhancer.run(headless=True)

        # Capture output
        captured = capsys.readouterr()

        # Should detect large skill and show warning
        assert "LARGE SKILL DETECTED" in captured.out
        assert "smart summarization" in captured.out.lower()
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
