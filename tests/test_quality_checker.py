#!/usr/bin/env python3
"""
Tests for cli/quality_checker.py functionality
"""

import tempfile
import unittest
from pathlib import Path

from skill_seekers.cli.quality_checker import QualityReport, SkillQualityChecker


class TestQualityChecker(unittest.TestCase):
    """Test quality checker functionality"""

    def create_test_skill(self, tmpdir, skill_md_content, create_references=True):
        """Helper to create a test skill directory"""
        skill_dir = Path(tmpdir) / "test-skill"
        skill_dir.mkdir()

        # Create SKILL.md
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(skill_md_content, encoding="utf-8")

        # Create references directory
        if create_references:
            refs_dir = skill_dir / "references"
            refs_dir.mkdir()
            (refs_dir / "index.md").write_text("# Index\n\nTest reference.", encoding="utf-8")
            (refs_dir / "getting_started.md").write_text(
                "# Getting Started\n\nHow to start.", encoding="utf-8"
            )

        return skill_dir

    def test_checker_detects_missing_skill_md(self):
        """Test that checker detects missing SKILL.md"""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "test-skill"
            skill_dir.mkdir()

            checker = SkillQualityChecker(skill_dir)
            report = checker.check_all()

            # Should have error about missing SKILL.md
            self.assertTrue(report.has_errors)
            self.assertTrue(any("SKILL.md" in issue.message for issue in report.errors))

    def test_checker_detects_missing_references(self):
        """Test that checker warns about missing references"""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_md = """---
name: test
---

# Test Skill

This is a test.
"""
            skill_dir = self.create_test_skill(tmpdir, skill_md, create_references=False)

            checker = SkillQualityChecker(skill_dir)
            report = checker.check_all()

            # Should have warning about missing references
            self.assertTrue(report.has_warnings)
            self.assertTrue(any("references" in issue.message.lower() for issue in report.warnings))

    def test_checker_detects_invalid_frontmatter(self):
        """Test that checker detects invalid YAML frontmatter"""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_md = """# Test Skill

No frontmatter here!
"""
            skill_dir = self.create_test_skill(tmpdir, skill_md)

            checker = SkillQualityChecker(skill_dir)
            report = checker.check_all()

            # Should have error about missing frontmatter
            self.assertTrue(report.has_errors)
            self.assertTrue(any("frontmatter" in issue.message.lower() for issue in report.errors))

    def test_checker_detects_missing_name_field(self):
        """Test that checker detects missing name field in frontmatter"""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_md = """---
description: test
---

# Test Skill
"""
            skill_dir = self.create_test_skill(tmpdir, skill_md)

            checker = SkillQualityChecker(skill_dir)
            report = checker.check_all()

            # Should have error about missing name field
            self.assertTrue(report.has_errors)
            self.assertTrue(any("name" in issue.message.lower() for issue in report.errors))

    def test_checker_detects_code_without_language(self):
        """Test that checker warns about code blocks without language tags"""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_md = """---
name: test
---

# Test Skill

Here's some code:

```
print("hello")
```
"""
            skill_dir = self.create_test_skill(tmpdir, skill_md)

            checker = SkillQualityChecker(skill_dir)
            report = checker.check_all()

            # Should have warning about code without language
            self.assertTrue(report.has_warnings)
            self.assertTrue(any("language" in issue.message.lower() for issue in report.warnings))

    def test_checker_approves_good_skill(self):
        """Test that checker gives high score to well-formed skill"""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_md = """---
name: test
description: A test skill
---

# Test Skill

## When to Use This Skill

Use this when you need to test.

## Quick Reference

Here are some examples:

```python
def hello():
    print("hello")
```

```javascript
console.log("hello");
```

## Example: Basic Usage

This shows how to use it.

## Reference Files

See the references directory for more:
- [Getting Started](references/getting_started.md)
- [Index](references/index.md)
"""
            skill_dir = self.create_test_skill(tmpdir, skill_md)

            checker = SkillQualityChecker(skill_dir)
            report = checker.check_all()

            # Should have no errors
            self.assertFalse(report.has_errors)

            # Quality score should be high
            self.assertGreaterEqual(report.quality_score, 80.0)

    def test_checker_detects_broken_links(self):
        """Test that checker detects broken internal links"""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_md = """---
name: test
---

# Test Skill

See [this file](nonexistent.md) for more info.
"""
            skill_dir = self.create_test_skill(tmpdir, skill_md)

            checker = SkillQualityChecker(skill_dir)
            report = checker.check_all()

            # Should have warning about broken link
            self.assertTrue(report.has_warnings)
            self.assertTrue(
                any("broken link" in issue.message.lower() for issue in report.warnings)
            )

    def test_quality_score_calculation(self):
        """Test that quality score is calculated correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            report = QualityReport("test", Path(tmpdir))

            # Perfect score to start
            self.assertEqual(report.quality_score, 100.0)

            # Add an error (should deduct 15 points)
            report.add_error("test", "Test error")
            self.assertEqual(report.quality_score, 85.0)

            # Add a warning (should deduct 5 points)
            report.add_warning("test", "Test warning")
            self.assertEqual(report.quality_score, 80.0)

            # Add more errors
            report.add_error("test", "Another error")
            report.add_error("test", "Yet another error")
            self.assertEqual(report.quality_score, 50.0)

    def test_quality_grade_calculation(self):
        """Test that quality grades are assigned correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            report = QualityReport("test", Path(tmpdir))

            # Grade A (90-100)
            self.assertEqual(report.quality_grade, "A")

            # Grade B (80-89)
            report.add_error("test", "Error 1")
            self.assertEqual(report.quality_grade, "B")

            # Grade C (70-79)
            report.add_warning("test", "Warning 1")
            report.add_warning("test", "Warning 2")
            self.assertEqual(report.quality_grade, "C")

            # Grade D (60-69)
            report.add_warning("test", "Warning 3")
            report.add_warning("test", "Warning 4")
            self.assertEqual(report.quality_grade, "D")

            # Grade F (below 60)
            report.add_error("test", "Error 2")
            report.add_error("test", "Error 3")
            self.assertEqual(report.quality_grade, "F")

    def test_is_excellent_property(self):
        """Test is_excellent property"""
        with tempfile.TemporaryDirectory() as tmpdir:
            report = QualityReport("test", Path(tmpdir))

            # Should be excellent with no issues
            self.assertTrue(report.is_excellent)

            # Adding an error should make it not excellent
            report.add_error("test", "Test error")
            self.assertFalse(report.is_excellent)

            # Clean report
            report2 = QualityReport("test", Path(tmpdir))
            # Adding a warning should also make it not excellent
            report2.add_warning("test", "Test warning")
            self.assertFalse(report2.is_excellent)


class TestCompletenessChecks(unittest.TestCase):
    """Test completeness check functionality"""

    def create_test_skill(self, tmpdir, skill_md_content):
        """Helper to create a test skill directory"""
        skill_dir = Path(tmpdir) / "test-skill"
        skill_dir.mkdir()

        # Create SKILL.md
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(skill_md_content, encoding="utf-8")

        # Create references directory
        refs_dir = skill_dir / "references"
        refs_dir.mkdir()
        (refs_dir / "index.md").write_text("# Index\n", encoding="utf-8")

        return skill_dir

    def test_checker_detects_prerequisites_section(self):
        """Test that checker detects prerequisites section"""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_md = """---
name: test
---

# Test Skill

## Prerequisites

Make sure you have:
- Python 3.10+
- pip installed

## Usage

Run the command.
"""
            skill_dir = self.create_test_skill(tmpdir, skill_md)

            checker = SkillQualityChecker(skill_dir)
            report = checker.check_all()

            # Should have info about found prerequisites
            completeness_infos = [i for i in report.info if i.category == "completeness"]
            self.assertTrue(
                any(
                    "prerequisites" in i.message.lower() or "verification" in i.message.lower()
                    for i in completeness_infos
                )
            )

    def test_checker_detects_troubleshooting_section(self):
        """Test that checker detects troubleshooting section"""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_md = """---
name: test
---

# Test Skill

## Usage

Run the command.

## Troubleshooting

### Common Issues

If the command fails, check your permissions.
"""
            skill_dir = self.create_test_skill(tmpdir, skill_md)

            checker = SkillQualityChecker(skill_dir)
            report = checker.check_all()

            # Should have info about found troubleshooting
            completeness_infos = [i for i in report.info if i.category == "completeness"]
            self.assertTrue(
                any(
                    "troubleshoot" in i.message.lower() or "error handling" in i.message.lower()
                    for i in completeness_infos
                )
            )

    def test_checker_detects_workflow_steps(self):
        """Test that checker detects workflow steps"""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_md = """---
name: test
---

# Test Skill

## Getting Started

First, install the dependencies.

Then, configure your environment.

Next, run the setup script.

Finally, verify the installation.
"""
            skill_dir = self.create_test_skill(tmpdir, skill_md)

            checker = SkillQualityChecker(skill_dir)
            report = checker.check_all()

            # Should have info about found workflow steps
            completeness_infos = [i for i in report.info if i.category == "completeness"]
            self.assertTrue(
                any(
                    "workflow" in i.message.lower() or "step" in i.message.lower()
                    for i in completeness_infos
                )
            )

    def test_ignores_workflow_steps_inside_code_blocks(self):
        """Step comments in a code example must NOT count as workflow guidance (#229)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_md = """# Test Skill

Widgets library.

## Code Example

```python
# Step 1: Initialize the client
# Step 2: Configure options
# Step 3: Run the query
client = APIClient()
```
"""
            skill_dir = self.create_test_skill(tmpdir, skill_md)
            report = SkillQualityChecker(skill_dir).check_all()

            completeness_infos = [i for i in report.info if i.category == "completeness"]
            # No POSITIVE workflow finding (✓ / "markers"); only the suggestion is allowed.
            self.assertFalse(
                any(
                    "✓" in i.message and "workflow" in i.message.lower() for i in completeness_infos
                )
            )
            self.assertFalse(any("markers)" in i.message for i in completeness_infos))

    def test_ignores_grounding_and_error_hints_inside_code_blocks(self):
        """`verify that` / `if it fails` in code comments must not satisfy the
        grounding/error-handling checks (#229)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_md = """# Test Skill

## Example

```python
# prerequisites: none, but verify that the token is set
# if the request fails, retry with backoff
do_thing()
```
"""
            skill_dir = self.create_test_skill(tmpdir, skill_md)
            report = SkillQualityChecker(skill_dir).check_all()

            completeness_infos = [i for i in report.info if i.category == "completeness"]
            # Both should be reported as MISSING (suggestion), not found.
            self.assertTrue(
                any("Consider adding prerequisites" in i.message for i in completeness_infos)
            )
            self.assertTrue(
                any("Consider adding troubleshooting" in i.message for i in completeness_infos)
            )

    def test_ignores_inline_code_markers(self):
        """Workflow markers that appear only inside inline code are ignored (#229).

        The surrounding prose deliberately contains no step markers, so any
        detection would come solely from the inline `step N` spans.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_md = "# Test Skill\n\nInvoke `step 1` and `step 2` on the `first, item`.\n"
            skill_dir = self.create_test_skill(tmpdir, skill_md)
            report = SkillQualityChecker(skill_dir).check_all()

            completeness_infos = [i for i in report.info if i.category == "completeness"]
            self.assertFalse(any("markers)" in i.message for i in completeness_infos))

    def test_strip_code_removes_fenced_and_inline(self):
        from skill_seekers.cli.quality_checker import _strip_code

        text = (
            "before `inline` mid\n```python\nhidden step 1\n```\nafter\n~~~\nalso hidden\n~~~\nend"
        )
        stripped = _strip_code(text)
        self.assertNotIn("hidden", stripped)
        self.assertNotIn("inline", stripped)
        self.assertIn("before", stripped)
        self.assertIn("after", stripped)
        self.assertIn("end", stripped)

    def test_checker_suggests_adding_prerequisites(self):
        """Test that checker suggests adding prerequisites when missing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_md = """---
name: test
---

# Test Skill

## Usage

Just run the command.
"""
            skill_dir = self.create_test_skill(tmpdir, skill_md)

            checker = SkillQualityChecker(skill_dir)
            report = checker.check_all()

            # Should have info suggesting prerequisites
            completeness_infos = [i for i in report.info if i.category == "completeness"]
            self.assertTrue(
                any(
                    "consider" in i.message.lower() and "prerequisites" in i.message.lower()
                    for i in completeness_infos
                )
            )


class TestReadabilityChecks(unittest.TestCase):
    """Test provisional readability checks."""

    def create_test_skill(self, tmpdir, skill_md_content):
        """Create a minimal skill for readability tests."""
        skill_dir = Path(tmpdir) / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(skill_md_content, encoding="utf-8")
        (skill_dir / "references").mkdir()
        return skill_dir

    def readability_info(self, report):
        """Return readability info issues from a report."""
        return [issue for issue in report.info if issue.category == "readability"]

    def test_known_english_prose_reports_readability_information(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = self.create_test_skill(
                tmpdir,
                """---
name: test
---

# Test Skill

This guide explains how to configure the client. Follow the example carefully.

The reference section describes common setup choices and safe verification steps.
""",
            )

            report = SkillQualityChecker(skill_dir).check_all()
            infos = self.readability_info(report)

            self.assertEqual(len(infos), 1)
            self.assertIn("Flesch Reading Ease", infos[0].message)
            self.assertIn("Flesch-Kincaid Grade Level", infos[0].message)
            self.assertIn("average sentence length", infos[0].message)
            self.assertIn("average paragraph length", infos[0].message)
            self.assertIn("English-language formulas", infos[0].message)
            self.assertIn("may be inaccurate for non-English content", infos[0].message)

    def test_sentence_average_and_exact_boundary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            thirty_words = " ".join(f"word{i}" for i in range(30))
            skill_dir = self.create_test_skill(tmpdir, f"---\nname: test\n---\n\n{thirty_words}.")

            report = SkillQualityChecker(skill_dir).check_all()
            warnings = self.readability_info(report)

            self.assertTrue(self.readability_info(report))
            self.assertFalse(any("sentence(s) exceed" in issue.message for issue in warnings))

    def test_31_word_sentence_triggers_one_aggregated_warning(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            thirty_one_words = " ".join(f"word{i}" for i in range(31))
            skill_dir = self.create_test_skill(
                tmpdir, f"---\nname: test\n---\n\n{thirty_one_words}."
            )

            warnings = self.readability_info(SkillQualityChecker(skill_dir).check_all())

            sentence_notes = [issue for issue in warnings if "sentence(s) exceed" in issue.message]
            self.assertEqual(len(sentence_notes), 1)
            self.assertIn("1 sentence(s)", sentence_notes[0].message)

    def test_paragraph_average_and_exact_boundary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            two_hundred_words = " ".join(f"word{i}" for i in range(200))
            skill_dir = self.create_test_skill(
                tmpdir, f"---\nname: test\n---\n\n{two_hundred_words}."
            )

            report = SkillQualityChecker(skill_dir).check_all()
            warnings = self.readability_info(report)

            self.assertTrue(
                any(
                    "average paragraph length 1.0 sentences" in issue.message
                    for issue in self.readability_info(report)
                )
            )
            self.assertFalse(any("paragraph(s) exceed" in issue.message for issue in warnings))

    def test_201_word_paragraph_triggers_one_aggregated_warning(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            two_hundred_one_words = " ".join(f"word{i}" for i in range(201))
            skill_dir = self.create_test_skill(
                tmpdir, f"---\nname: test\n---\n\n{two_hundred_one_words}."
            )

            warnings = self.readability_info(SkillQualityChecker(skill_dir).check_all())

            paragraph_notes = [
                issue for issue in warnings if "paragraph(s) exceed" in issue.message
            ]
            self.assertEqual(len(paragraph_notes), 1)
            self.assertIn("1 paragraph(s)", paragraph_notes[0].message)

    def test_readability_never_affects_the_quality_score(self):
        """Readability is advisory: it must not deduct from quality_score.

        quality_score subtracts 5 points per warning and `quality --threshold`
        exits non-zero in CI, so emitting readability as warnings would fail
        existing quality gates on skills that had not changed.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            long_paragraph = " ".join(f"word{i}" for i in range(201)) + "."
            skill_dir = self.create_test_skill(
                tmpdir,
                f"---\nname: test\n---\n\n{long_paragraph}\n\n{long_paragraph}",
            )

            report = SkillQualityChecker(skill_dir).check_all()

            # Readability findings are present...
            self.assertTrue(self.readability_info(report))
            # ...but contribute nothing to warnings, and so nothing to the score.
            self.assertEqual(
                [issue for issue in report.warnings if issue.category == "readability"], []
            )

    def test_multiple_offences_are_aggregated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            long_paragraph = " ".join(f"word{i}" for i in range(201)) + "."
            skill_dir = self.create_test_skill(
                tmpdir,
                f"---\nname: test\n---\n\n{long_paragraph}\n\n{long_paragraph}",
            )

            notes = self.readability_info(SkillQualityChecker(skill_dir).check_all())
            # Aggregated notes only; readability_info also carries the metrics summary.
            aggregated = [issue for issue in notes if "exceed" in issue.message]

            self.assertEqual(len(aggregated), 2)
            self.assertTrue(any("2 sentence(s) exceed" in issue.message for issue in aggregated))
            self.assertTrue(any("2 paragraph(s) exceed" in issue.message for issue in aggregated))

    def test_frontmatter_is_excluded(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            frontmatter_words = " ".join(f"word{i}" for i in range(201))
            skill_dir = self.create_test_skill(
                tmpdir,
                f"---\nname: test\ndescription: {frontmatter_words}\n---\n\nShort prose.",
            )

            warnings = self.readability_info(SkillQualityChecker(skill_dir).check_all())

            self.assertFalse(any("paragraph(s) exceed" in issue.message for issue in warnings))

    def test_fenced_code_is_excluded(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            code_words = " ".join(f"word{i}" for i in range(201))
            skill_dir = self.create_test_skill(
                tmpdir,
                f"---\nname: test\n---\n\nShort prose.\n\n```text\n{code_words}\n```",
            )

            warnings = self.readability_info(SkillQualityChecker(skill_dir).check_all())

            self.assertFalse(any("paragraph(s) exceed" in issue.message for issue in warnings))

    def test_inline_code_is_excluded(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            code_words = " ".join(f"word{i}" for i in range(201))
            skill_dir = self.create_test_skill(
                tmpdir,
                f"---\nname: test\n---\n\nShort prose with `{code_words}` included.",
            )

            warnings = self.readability_info(SkillQualityChecker(skill_dir).check_all())

            self.assertFalse(any("paragraph(s) exceed" in issue.message for issue in warnings))

    def test_crlf_fenced_code_is_excluded(self):
        from skill_seekers.cli.quality_checker import _strip_code

        code_words = " ".join(f"word{i}" for i in range(201))
        stripped = _strip_code(f"Prose.\r\n```text\r\n{code_words}\r\n```\r\n")

        self.assertNotIn("word200", stripped)

    def test_empty_and_code_only_skills_do_not_crash(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_skill = self.create_test_skill(tmpdir, "---\nname: empty\n---\n")
            code_skill = Path(tmpdir) / "code-only"
            code_skill.mkdir()
            (code_skill / "SKILL.md").write_text(
                "---\nname: code-only\n---\n\n```python\nprint('hello')\n```\n",
                encoding="utf-8",
            )
            (code_skill / "references").mkdir()

            empty_report = SkillQualityChecker(empty_skill).check_all()
            code_report = SkillQualityChecker(code_skill).check_all()

            self.assertFalse(self.readability_info(empty_report))
            self.assertFalse(self.readability_info(code_report))
            self.assertFalse(self.readability_info(empty_report))
            self.assertFalse(self.readability_info(code_report))


class TestQualityCheckerCLI(unittest.TestCase):
    """Test quality checker CLI"""

    def test_cli_help_output(self):
        """Test that CLI help works"""
        import subprocess

        try:
            result = subprocess.run(
                ["python3", "-m", "skill_seekers.cli.quality_checker", "--help"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            # Should include usage info
            output = result.stdout + result.stderr
            self.assertTrue("usage:" in output.lower() or "quality" in output.lower())
        except FileNotFoundError:
            self.skipTest("Module not installed")

    def test_cli_with_nonexistent_directory(self):
        """Test CLI behavior with nonexistent directory"""
        import subprocess

        result = subprocess.run(
            ["python3", "-m", "skill_seekers.cli.quality_checker", "/nonexistent/path"],
            capture_output=True,
            text=True,
        )

        # Should fail
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
