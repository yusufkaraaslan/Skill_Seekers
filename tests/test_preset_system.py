#!/usr/bin/env python3
"""
Tests for Preset System

Tests the formal preset system for analyze command.
"""

import pytest
from skill_seekers.cli.presets import PresetManager, PRESETS, AnalysisPreset


class TestPresetDefinitions:
    """Test preset definitions are complete and valid."""

    def test_all_presets_defined(self):
        """Test that all expected presets are defined."""
        assert "quick" in PRESETS
        assert "standard" in PRESETS
        assert "comprehensive" in PRESETS
        assert len(PRESETS) == 3

    def test_preset_structure(self):
        """Test that presets have correct structure."""
        for name, preset in PRESETS.items():
            assert isinstance(preset, AnalysisPreset)
            assert preset.name
            assert preset.description
            assert preset.depth in ["surface", "deep", "full"]
            assert isinstance(preset.features, dict)
            assert 0 <= preset.enhance_level <= 3
            assert preset.estimated_time
            assert preset.icon

    def test_quick_preset(self):
        """Test quick preset configuration."""
        quick = PRESETS["quick"]
        assert quick.name == "Quick"
        assert quick.depth == "surface"
        assert quick.enhance_level == 0
        assert quick.estimated_time == "1-2 minutes"
        assert quick.icon == "⚡"
        # Quick should disable slow features
        assert quick.features["api_reference"]  # Essential
        assert not quick.features["dependency_graph"]  # Slow
        assert not quick.features["patterns"]  # Slow
        assert not quick.features["test_examples"]  # Slow
        assert not quick.features["how_to_guides"]  # Requires AI
        assert quick.features["docs"]  # Essential

    def test_standard_preset(self):
        """Test standard preset configuration."""
        standard = PRESETS["standard"]
        assert standard.name == "Standard"
        assert standard.depth == "deep"
        assert standard.enhance_level == 1
        assert standard.estimated_time == "5-10 minutes"
        assert standard.icon == "🎯"
        # Standard should enable core features
        assert standard.features["api_reference"]
        assert standard.features["dependency_graph"]
        assert standard.features["patterns"]
        assert standard.features["test_examples"]
        assert not standard.features["how_to_guides"]  # Slow
        assert standard.features["config_patterns"]
        assert standard.features["docs"]

    def test_comprehensive_preset(self):
        """Test comprehensive preset configuration."""
        comprehensive = PRESETS["comprehensive"]
        assert comprehensive.name == "Comprehensive"
        assert comprehensive.depth == "full"
        assert comprehensive.enhance_level == 3
        assert comprehensive.estimated_time == "20-60 minutes"
        assert comprehensive.icon == "🚀"
        # Comprehensive should enable ALL features
        assert all(comprehensive.features.values())


class TestPresetManager:
    """Test PresetManager functionality."""

    def test_get_preset(self):
        """Test PresetManager.get_preset()."""
        quick = PresetManager.get_preset("quick")
        assert quick is not None
        assert quick.name == "Quick"
        assert quick.depth == "surface"

        # Case insensitive
        standard = PresetManager.get_preset("STANDARD")
        assert standard is not None
        assert standard.name == "Standard"

    def test_get_preset_invalid(self):
        """Test PresetManager.get_preset() with invalid name."""
        invalid = PresetManager.get_preset("nonexistent")
        assert invalid is None

    def test_list_presets(self):
        """Test PresetManager.list_presets()."""
        presets = PresetManager.list_presets()
        assert len(presets) == 3
        assert "quick" in presets
        assert "standard" in presets
        assert "comprehensive" in presets

    def test_format_preset_help(self):
        """Test PresetManager.format_preset_help()."""
        help_text = PresetManager.format_preset_help()
        assert "Available presets:" in help_text
        assert "⚡ quick" in help_text
        assert "🎯 standard" in help_text
        assert "🚀 comprehensive" in help_text
        assert "1-2 minutes" in help_text
        assert "5-10 minutes" in help_text
        assert "20-60 minutes" in help_text

    def test_get_default_preset(self):
        """Test PresetManager.get_default_preset()."""
        default = PresetManager.get_default_preset()
        assert default == "standard"


class TestPresetApplication:
    """Test preset application logic."""

    def test_apply_preset_quick(self):
        """Test applying quick preset."""
        args = {"directory": "/tmp/test"}
        updated = PresetManager.apply_preset("quick", args)

        assert updated["depth"] == "surface"
        assert updated["enhance_level"] == 0
        assert updated["skip_patterns"]  # Quick disables patterns
        assert updated["skip_dependency_graph"]  # Quick disables dep graph
        assert updated["skip_test_examples"]  # Quick disables tests
        assert updated["skip_how_to_guides"]  # Quick disables guides
        assert not updated["skip_api_reference"]  # Quick enables API ref
        assert not updated["skip_docs"]  # Quick enables docs

    def test_apply_preset_standard(self):
        """Test applying standard preset."""
        args = {"directory": "/tmp/test"}
        updated = PresetManager.apply_preset("standard", args)

        assert updated["depth"] == "deep"
        assert updated["enhance_level"] == 1
        assert not updated["skip_patterns"]  # Standard enables patterns
        assert not updated["skip_dependency_graph"]  # Standard enables dep graph
        assert not updated["skip_test_examples"]  # Standard enables tests
        assert updated["skip_how_to_guides"]  # Standard disables guides (slow)
        assert not updated["skip_api_reference"]  # Standard enables API ref
        assert not updated["skip_docs"]  # Standard enables docs

    def test_apply_preset_comprehensive(self):
        """Test applying comprehensive preset."""
        args = {"directory": "/tmp/test"}
        updated = PresetManager.apply_preset("comprehensive", args)

        assert updated["depth"] == "full"
        assert updated["enhance_level"] == 3
        # Comprehensive enables ALL features
        assert not updated["skip_patterns"]
        assert not updated["skip_dependency_graph"]
        assert not updated["skip_test_examples"]
        assert not updated["skip_how_to_guides"]
        assert not updated["skip_api_reference"]
        assert not updated["skip_config_patterns"]
        assert not updated["skip_docs"]

    def test_cli_overrides_preset(self):
        """Test that CLI args override preset defaults."""
        args = {
            "directory": "/tmp/test",
            "enhance_level": 2,  # Override preset default
            "skip_patterns": False,  # Override preset default
        }

        updated = PresetManager.apply_preset("quick", args)

        # Preset says enhance_level=0, but CLI said 2
        assert updated["enhance_level"] == 2  # CLI wins

        # Preset says skip_patterns=True (disabled), but CLI said False (enabled)
        assert not updated["skip_patterns"]  # CLI wins

    def test_apply_preset_preserves_args(self):
        """Test that apply_preset preserves existing args."""
        args = {
            "directory": "/tmp/test",
            "output": "custom_output/",
            "languages": "Python,JavaScript",
        }

        updated = PresetManager.apply_preset("standard", args)

        # Existing args should be preserved
        assert updated["directory"] == "/tmp/test"
        assert updated["output"] == "custom_output/"
        assert updated["languages"] == "Python,JavaScript"

    def test_apply_preset_invalid(self):
        """Test applying invalid preset raises error."""
        args = {"directory": "/tmp/test"}

        with pytest.raises(ValueError, match="Unknown preset: nonexistent"):
            PresetManager.apply_preset("nonexistent", args)


class TestDeprecationWarnings:
    """Test deprecation warning functionality."""

    def test_check_deprecated_flags_quick(self, capsys):
        """Test deprecation warning for --quick flag."""
        from skill_seekers.cli.codebase_scraper import _check_deprecated_flags
        import argparse

        args = argparse.Namespace(quick=True, comprehensive=False, depth=None, ai_mode="auto")

        _check_deprecated_flags(args)

        captured = capsys.readouterr()
        assert "DEPRECATED" in captured.out
        assert "--quick" in captured.out
        assert "--preset quick" in captured.out
        assert "v3.0.0" in captured.out

    def test_check_deprecated_flags_comprehensive(self, capsys):
        """Test deprecation warning for --comprehensive flag."""
        from skill_seekers.cli.codebase_scraper import _check_deprecated_flags
        import argparse

        args = argparse.Namespace(quick=False, comprehensive=True, depth=None, ai_mode="auto")

        _check_deprecated_flags(args)

        captured = capsys.readouterr()
        assert "DEPRECATED" in captured.out
        assert "--comprehensive" in captured.out
        assert "--preset comprehensive" in captured.out
        assert "v3.0.0" in captured.out

    def test_check_deprecated_flags_depth(self, capsys):
        """Test deprecation warning for --depth flag."""
        from skill_seekers.cli.codebase_scraper import _check_deprecated_flags
        import argparse

        args = argparse.Namespace(quick=False, comprehensive=False, depth="full", ai_mode="auto")

        _check_deprecated_flags(args)

        captured = capsys.readouterr()
        assert "DEPRECATED" in captured.out
        assert "--depth full" in captured.out
        assert "--preset comprehensive" in captured.out
        assert "v3.0.0" in captured.out

    def test_check_deprecated_flags_ai_mode(self, capsys):
        """Test deprecation warning for --ai-mode flag."""
        from skill_seekers.cli.codebase_scraper import _check_deprecated_flags
        import argparse

        args = argparse.Namespace(quick=False, comprehensive=False, depth=None, ai_mode="api")

        _check_deprecated_flags(args)

        captured = capsys.readouterr()
        assert "DEPRECATED" in captured.out
        assert "--ai-mode api" in captured.out
        assert "--enhance-level" in captured.out
        assert "v3.0.0" in captured.out

    def test_check_deprecated_flags_multiple(self, capsys):
        """Test deprecation warnings for multiple flags."""
        from skill_seekers.cli.codebase_scraper import _check_deprecated_flags
        import argparse

        args = argparse.Namespace(quick=True, comprehensive=False, depth="surface", ai_mode="local")

        _check_deprecated_flags(args)

        captured = capsys.readouterr()
        assert "DEPRECATED" in captured.out
        assert "--depth surface" in captured.out
        assert "--ai-mode local" in captured.out
        assert "--quick" in captured.out
        assert "MIGRATION TIP" in captured.out
        assert "v3.0.0" in captured.out

    def test_check_deprecated_flags_none(self, capsys):
        """Test no warnings when no deprecated flags used."""
        from skill_seekers.cli.codebase_scraper import _check_deprecated_flags
        import argparse

        args = argparse.Namespace(quick=False, comprehensive=False, depth=None, ai_mode="auto")

        _check_deprecated_flags(args)

        captured = capsys.readouterr()
        assert "DEPRECATED" not in captured.out
        assert "v3.0.0" not in captured.out


class TestBackwardCompatibility:
    """Test backward compatibility with old flags."""

    def test_old_flags_still_work(self):
        """Test that old flags still work (with warnings)."""
        # --quick flag
        args = {"quick": True}
        updated = PresetManager.apply_preset("quick", args)
        assert updated["depth"] == "surface"

        # --comprehensive flag
        args = {"comprehensive": True}
        updated = PresetManager.apply_preset("comprehensive", args)
        assert updated["depth"] == "full"

    def test_preset_flag_preferred(self):
        """Test that --preset flag is the recommended way."""
        # Using --preset quick
        args = {"preset": "quick"}
        updated = PresetManager.apply_preset("quick", args)
        assert updated["depth"] == "surface"

        # Using --preset standard
        args = {"preset": "standard"}
        updated = PresetManager.apply_preset("standard", args)
        assert updated["depth"] == "deep"

        # Using --preset comprehensive
        args = {"preset": "comprehensive"}
        updated = PresetManager.apply_preset("comprehensive", args)
        assert updated["depth"] == "full"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
