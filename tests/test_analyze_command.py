#!/usr/bin/env python3
"""Tests for analyze subcommand integration in main CLI."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from skill_seekers.cli.main import create_parser


class TestAnalyzeSubcommand(unittest.TestCase):
    """Test analyze subcommand registration and argument parsing."""

    def setUp(self):
        """Create parser for testing."""
        self.parser = create_parser()

    def test_analyze_subcommand_exists(self):
        """Test that analyze subcommand is registered."""
        args = self.parser.parse_args(["analyze", "--directory", "."])
        self.assertEqual(args.command, "analyze")
        self.assertEqual(args.directory, ".")

    def test_analyze_with_output_directory(self):
        """Test analyze with custom output directory."""
        args = self.parser.parse_args(["analyze", "--directory", ".", "--output", "custom/"])
        self.assertEqual(args.output, "custom/")

    def test_quick_preset_flag(self):
        """Test --quick preset flag parsing."""
        args = self.parser.parse_args(["analyze", "--directory", ".", "--quick"])
        self.assertTrue(args.quick)
        self.assertFalse(args.comprehensive)

    def test_comprehensive_preset_flag(self):
        """Test --comprehensive preset flag parsing."""
        args = self.parser.parse_args(["analyze", "--directory", ".", "--comprehensive"])
        self.assertTrue(args.comprehensive)
        self.assertFalse(args.quick)

    def test_quick_and_comprehensive_mutually_exclusive(self):
        """Test that both flags can be parsed (mutual exclusion enforced at runtime)."""
        # The parser allows both flags; runtime logic prevents simultaneous use
        args = self.parser.parse_args(["analyze", "--directory", ".", "--quick", "--comprehensive"])
        self.assertTrue(args.quick)
        self.assertTrue(args.comprehensive)
        # Note: Runtime will catch this and return error code 1

    def test_enhance_level_flag(self):
        """Test --enhance-level flag parsing."""
        args = self.parser.parse_args(["analyze", "--directory", ".", "--enhance-level", "2"])
        self.assertEqual(args.enhance_level, 2)

    def test_skip_flags_passed_through(self):
        """Test that skip flags are recognized."""
        args = self.parser.parse_args(
            ["analyze", "--directory", ".", "--skip-patterns", "--skip-test-examples"]
        )
        self.assertTrue(args.skip_patterns)
        self.assertTrue(args.skip_test_examples)

    def test_all_skip_flags(self):
        """Test all skip flags are properly parsed."""
        args = self.parser.parse_args(
            [
                "analyze",
                "--directory",
                ".",
                "--skip-api-reference",
                "--skip-dependency-graph",
                "--skip-patterns",
                "--skip-test-examples",
                "--skip-how-to-guides",
                "--skip-config-patterns",
                "--skip-docs",
            ]
        )
        self.assertTrue(args.skip_api_reference)
        self.assertTrue(args.skip_dependency_graph)
        self.assertTrue(args.skip_patterns)
        self.assertTrue(args.skip_test_examples)
        self.assertTrue(args.skip_how_to_guides)
        self.assertTrue(args.skip_config_patterns)
        self.assertTrue(args.skip_docs)

    def test_backward_compatible_depth_flag(self):
        """Test that deprecated --depth flag still works."""
        args = self.parser.parse_args(["analyze", "--directory", ".", "--depth", "full"])
        self.assertEqual(args.depth, "full")

    def test_depth_flag_choices(self):
        """Test that depth flag accepts correct values."""
        for depth in ["surface", "deep", "full"]:
            args = self.parser.parse_args(["analyze", "--directory", ".", "--depth", depth])
            self.assertEqual(args.depth, depth)

    def test_languages_flag(self):
        """Test languages flag parsing."""
        args = self.parser.parse_args(
            ["analyze", "--directory", ".", "--languages", "Python,JavaScript"]
        )
        self.assertEqual(args.languages, "Python,JavaScript")

    def test_file_patterns_flag(self):
        """Test file patterns flag parsing."""
        args = self.parser.parse_args(
            ["analyze", "--directory", ".", "--file-patterns", "*.py,src/**/*.js"]
        )
        self.assertEqual(args.file_patterns, "*.py,src/**/*.js")

    def test_no_comments_flag(self):
        """Test no-comments flag parsing."""
        args = self.parser.parse_args(["analyze", "--directory", ".", "--no-comments"])
        self.assertTrue(args.no_comments)

    def test_verbose_flag(self):
        """Test verbose flag parsing."""
        args = self.parser.parse_args(["analyze", "--directory", ".", "--verbose"])
        self.assertTrue(args.verbose)

    def test_complex_command_combination(self):
        """Test complex command with multiple flags."""
        args = self.parser.parse_args(
            [
                "analyze",
                "--directory",
                "./src",
                "--output",
                "analysis/",
                "--quick",
                "--languages",
                "Python",
                "--skip-patterns",
                "--verbose",
            ]
        )
        self.assertEqual(args.directory, "./src")
        self.assertEqual(args.output, "analysis/")
        self.assertTrue(args.quick)
        self.assertEqual(args.languages, "Python")
        self.assertTrue(args.skip_patterns)
        self.assertTrue(args.verbose)

    def test_directory_is_required(self):
        """Test that directory argument is required."""
        with self.assertRaises(SystemExit):
            self.parser.parse_args(["analyze"])

    def test_default_output_directory(self):
        """Test default output directory value."""
        args = self.parser.parse_args(["analyze", "--directory", "."])
        self.assertEqual(args.output, "output/codebase/")


class TestAnalyzePresetBehavior(unittest.TestCase):
    """Test preset flag behavior and argument transformation."""

    def setUp(self):
        """Create parser for testing."""
        self.parser = create_parser()

    def test_quick_preset_implies_surface_depth(self):
        """Test that --quick preset should trigger surface depth."""
        args = self.parser.parse_args(["analyze", "--directory", ".", "--quick"])
        self.assertTrue(args.quick)
        # Note: Depth transformation happens in dispatch handler

    def test_comprehensive_preset_implies_full_depth(self):
        """Test that --comprehensive preset should trigger full depth."""
        args = self.parser.parse_args(["analyze", "--directory", ".", "--comprehensive"])
        self.assertTrue(args.comprehensive)
        # Note: Depth transformation happens in dispatch handler

    def test_enhance_level_standalone(self):
        """Test --enhance-level can be used without presets."""
        args = self.parser.parse_args(["analyze", "--directory", ".", "--enhance-level", "3"])
        self.assertEqual(args.enhance_level, 3)
        self.assertFalse(args.quick)
        self.assertFalse(args.comprehensive)


class TestAnalyzeWorkflowFlags(unittest.TestCase):
    """Test workflow and parity flags added to the analyze subcommand."""

    def setUp(self):
        """Create parser for testing."""
        self.parser = create_parser()

    def test_enhance_workflow_accepted_as_list(self):
        """Test --enhance-workflow is accepted and stored as a list."""
        args = self.parser.parse_args(
            ["analyze", "--directory", ".", "--enhance-workflow", "security-focus"]
        )
        self.assertEqual(args.enhance_workflow, ["security-focus"])

    def test_enhance_workflow_chained_twice(self):
        """Test --enhance-workflow can be chained to produce a two-item list."""
        args = self.parser.parse_args(
            [
                "analyze",
                "--directory",
                ".",
                "--enhance-workflow",
                "security-focus",
                "--enhance-workflow",
                "minimal",
            ]
        )
        self.assertEqual(args.enhance_workflow, ["security-focus", "minimal"])

    def test_enhance_stage_accepted_as_list(self):
        """Test --enhance-stage is accepted with action=append."""
        args = self.parser.parse_args(
            ["analyze", "--directory", ".", "--enhance-stage", "sec:Analyze security"]
        )
        self.assertEqual(args.enhance_stage, ["sec:Analyze security"])

    def test_var_accepted_as_list(self):
        """Test --var is accepted with action=append (dest is 'var')."""
        args = self.parser.parse_args(["analyze", "--directory", ".", "--var", "focus=performance"])
        self.assertEqual(args.var, ["focus=performance"])

    def test_workflow_dry_run_flag(self):
        """Test --workflow-dry-run sets the flag."""
        args = self.parser.parse_args(["analyze", "--directory", ".", "--workflow-dry-run"])
        self.assertTrue(args.workflow_dry_run)

    def test_api_key_stored_correctly(self):
        """Test --api-key is stored in args."""
        args = self.parser.parse_args(["analyze", "--directory", ".", "--api-key", "sk-ant-test"])
        self.assertEqual(args.api_key, "sk-ant-test")

    def test_dry_run_stored_correctly(self):
        """Test --dry-run is stored in args."""
        args = self.parser.parse_args(["analyze", "--directory", ".", "--dry-run"])
        self.assertTrue(args.dry_run)

    def test_workflow_flags_combined(self):
        """Test workflow flags can be combined with other analyze flags."""
        args = self.parser.parse_args(
            [
                "analyze",
                "--directory",
                ".",
                "--enhance-workflow",
                "security-focus",
                "--api-key",
                "sk-ant-test",
                "--dry-run",
                "--enhance-level",
                "1",
            ]
        )
        self.assertEqual(args.enhance_workflow, ["security-focus"])
        self.assertEqual(args.api_key, "sk-ant-test")
        self.assertTrue(args.dry_run)
        self.assertEqual(args.enhance_level, 1)


if __name__ == "__main__":
    unittest.main()
