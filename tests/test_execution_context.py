"""Tests for ExecutionContext singleton.

This module tests the ExecutionContext class which provides a single source
of truth for all configuration in Skill Seekers.
"""

import argparse
import json
import os
import tempfile

import pytest

from skill_seekers.cli.execution_context import (
    ExecutionContext,
    get_context,
)


class TestExecutionContextBasics:
    """Basic functionality tests."""

    def setup_method(self):
        """Reset singleton before each test."""
        ExecutionContext.reset()

    def teardown_method(self):
        """Clean up after each test."""
        ExecutionContext.reset()

    def test_get_returns_defaults_when_not_initialized(self):
        """Should return default context when not explicitly initialized."""
        ctx = ExecutionContext.get()
        assert ctx is not None
        assert ctx.enhancement.level == 2  # default
        assert ctx.output.name is None  # default

    def test_get_context_shortcut(self):
        """get_context() should be equivalent to ExecutionContext.get()."""
        args = argparse.Namespace(name="test-skill")
        ExecutionContext.initialize(args=args)

        ctx = get_context()
        assert ctx.output.name == "test-skill"

    def test_initialize_returns_instance(self):
        """initialize() should return the context instance."""
        args = argparse.Namespace(name="test")
        ctx = ExecutionContext.initialize(args=args)

        assert isinstance(ctx, ExecutionContext)
        assert ctx.output.name == "test"

    def test_singleton_behavior(self):
        """Multiple calls should return same instance."""
        args = argparse.Namespace(name="first")
        ctx1 = ExecutionContext.initialize(args=args)
        ctx2 = ExecutionContext.get()

        assert ctx1 is ctx2

    def test_reset_clears_instance(self):
        """reset() should clear the initialized instance, get() returns fresh defaults."""
        args = argparse.Namespace(name="test-skill")
        ExecutionContext.initialize(args=args)
        assert ExecutionContext.get().output.name == "test-skill"

        ExecutionContext.reset()

        # After reset, get() returns default context (not the old one)
        ctx = ExecutionContext.get()
        assert ctx.output.name is None  # default, not "test-skill"


class TestExecutionContextFromArgs:
    """Tests for building context from CLI args."""

    def setup_method(self):
        ExecutionContext.reset()

    def teardown_method(self):
        ExecutionContext.reset()

    def test_basic_args(self):
        """Should extract basic args correctly."""
        args = argparse.Namespace(
            name="react-docs",
            output="custom/output",
            doc_version="18.2",
            dry_run=True,
            enhance_level=3,
            agent="kimi",
        )

        ctx = ExecutionContext.initialize(args=args)

        assert ctx.output.name == "react-docs"
        assert ctx.output.output_dir == "custom/output"
        assert ctx.output.doc_version == "18.2"
        assert ctx.output.dry_run is True
        assert ctx.enhancement.level == 3
        assert ctx.enhancement.agent == "kimi"

    def test_scraping_args(self):
        """Should extract scraping args correctly."""
        args = argparse.Namespace(
            name="test",
            max_pages=100,
            rate_limit=1.5,
            browser=True,
            workers=4,
            async_mode=True,
            resume=True,
            fresh=False,
            skip_scrape=True,
        )

        ctx = ExecutionContext.initialize(args=args)

        assert ctx.scraping.max_pages == 100
        assert ctx.scraping.rate_limit == 1.5
        assert ctx.scraping.browser is True
        assert ctx.scraping.workers == 4
        assert ctx.scraping.async_mode is True
        assert ctx.scraping.resume is True
        assert ctx.scraping.skip_scrape is True

    def test_analysis_args(self):
        """Should extract analysis args correctly."""
        args = argparse.Namespace(
            name="test",
            depth="full",
            skip_patterns=True,
            skip_test_examples=True,
            skip_how_to_guides=True,
            file_patterns="*.py,*.js",
        )

        ctx = ExecutionContext.initialize(args=args)

        assert ctx.analysis.depth == "full"
        assert ctx.analysis.skip_patterns is True
        assert ctx.analysis.skip_test_examples is True
        assert ctx.analysis.skip_how_to_guides is True
        assert ctx.analysis.file_patterns == ["*.py", "*.js"]

    def test_workflow_args(self):
        """Should extract workflow args correctly."""
        args = argparse.Namespace(
            name="test",
            enhance_workflow=["security-focus", "api-docs"],
            enhance_stage=["stage1:prompt1"],
            var=["key1=value1", "key2=value2"],
        )

        ctx = ExecutionContext.initialize(args=args)

        assert ctx.enhancement.workflows == ["security-focus", "api-docs"]
        assert ctx.enhancement.stages == ["stage1:prompt1"]
        assert ctx.enhancement.workflow_vars == {"key1": "value1", "key2": "value2"}

    def test_rag_args(self):
        """Should extract RAG args correctly."""
        args = argparse.Namespace(
            name="test",
            chunk_for_rag=True,
            chunk_tokens=1024,
        )

        ctx = ExecutionContext.initialize(args=args)

        assert ctx.rag.chunk_for_rag is True
        assert ctx.rag.chunk_tokens == 1024

    def test_api_mode_detection(self):
        """Should detect API mode from api_key."""
        args = argparse.Namespace(
            name="test",
            api_key="test-key",
        )

        ctx = ExecutionContext.initialize(args=args)

        assert ctx.enhancement.mode == "api"

    def test_local_mode_detection(self):
        """Should default to local/auto mode without API key."""
        # Clean API key env vars to ensure test isolation
        api_keys = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "MOONSHOT_API_KEY", "GOOGLE_API_KEY"]
        saved = {k: os.environ.pop(k, None) for k in api_keys}
        try:
            args = argparse.Namespace(name="test")
            ctx = ExecutionContext.initialize(args=args)
            assert ctx.enhancement.mode in ("local", "auto")
        finally:
            for k, v in saved.items():
                if v is not None:
                    os.environ[k] = v

    def test_raw_args_access(self):
        """Should provide access to raw args for backward compatibility."""
        args = argparse.Namespace(
            name="test",
            custom_field="custom_value",
        )

        ctx = ExecutionContext.initialize(args=args)

        assert ctx.get_raw("name") == "test"
        assert ctx.get_raw("custom_field") == "custom_value"
        assert ctx.get_raw("nonexistent", "default") == "default"


class TestExecutionContextFromConfigFile:
    """Tests for building context from config files."""

    def setup_method(self):
        ExecutionContext.reset()

    def teardown_method(self):
        ExecutionContext.reset()

    def test_unified_config_format(self):
        """Should load unified config with sources array."""
        config = {
            "name": "unity-docs",
            "version": "2022.3",
            "enhancement": {
                "enabled": True,
                "level": 2,
                "mode": "local",
                "agent": "kimi",
                "timeout": "unlimited",
            },
            "workflows": ["unity-game-dev"],
            "workflow_stages": ["custom:stage"],
            "workflow_vars": {"var1": "value1"},
            "sources": [{"type": "documentation", "base_url": "https://docs.unity3d.com/"}],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config, f)
            config_path = f.name

        try:
            ctx = ExecutionContext.initialize(config_path=config_path)

            assert ctx.output.name == "unity-docs"
            assert ctx.output.doc_version == "2022.3"
            assert ctx.enhancement.enabled is True
            assert ctx.enhancement.level == 2
            assert ctx.enhancement.mode == "local"
            assert ctx.enhancement.agent == "kimi"
            assert ctx.enhancement.workflows == ["unity-game-dev"]
            assert ctx.enhancement.stages == ["custom:stage"]
            assert ctx.enhancement.workflow_vars == {"var1": "value1"}
        finally:
            os.unlink(config_path)

    def test_simple_web_config_format(self):
        """Should load simple web config format."""
        config = {
            "name": "react-docs",
            "version": "18.2",
            "base_url": "https://react.dev/",
            "max_pages": 500,
            "rate_limit": 0.5,
            "browser": True,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config, f)
            config_path = f.name

        try:
            ctx = ExecutionContext.initialize(config_path=config_path)

            assert ctx.output.name == "react-docs"
            assert ctx.output.doc_version == "18.2"
            assert ctx.scraping.max_pages == 500
            assert ctx.scraping.rate_limit == 0.5
            assert ctx.scraping.browser is True
        finally:
            os.unlink(config_path)

    def test_timeout_integer(self):
        """Should handle integer timeout in config."""
        config = {
            "name": "test",
            "enhancement": {"timeout": 3600},
            "sources": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config, f)
            config_path = f.name

        try:
            ctx = ExecutionContext.initialize(config_path=config_path)
            assert ctx.enhancement.timeout == 3600
        finally:
            os.unlink(config_path)


class TestExecutionContextPriority:
    """Tests for configuration priority (CLI > Config > Env > Defaults)."""

    def setup_method(self):
        ExecutionContext.reset()
        self._original_env = {}

    def teardown_method(self):
        ExecutionContext.reset()
        # Restore env vars
        for key, value in self._original_env.items():
            if value is not None:
                os.environ[key] = value
            else:
                os.environ.pop(key, None)

    def test_cli_overrides_config(self):
        """CLI args should override config file values."""
        config = {"name": "config-name", "sources": []}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config, f)
            config_path = f.name

        try:
            args = argparse.Namespace(name="cli-name")
            ctx = ExecutionContext.initialize(args=args, config_path=config_path)

            # CLI should win
            assert ctx.output.name == "cli-name"
        finally:
            os.unlink(config_path)

    def test_config_overrides_defaults(self):
        """Config file should override default values."""
        config = {
            "name": "config-name",
            "enhancement": {"level": 3},
            "sources": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config, f)
            config_path = f.name

        try:
            ctx = ExecutionContext.initialize(config_path=config_path)

            # Config should override default (level=2)
            assert ctx.enhancement.level == 3
        finally:
            os.unlink(config_path)

    def test_env_overrides_defaults(self):
        """Environment variables should override defaults."""
        self._original_env["SKILL_SEEKER_AGENT"] = os.environ.get("SKILL_SEEKER_AGENT")
        os.environ["SKILL_SEEKER_AGENT"] = "claude"

        ctx = ExecutionContext.initialize()

        # Env var should override default (None)
        assert ctx.enhancement.agent == "claude"


class TestExecutionContextSourceInfo:
    """Tests for source info integration."""

    def setup_method(self):
        ExecutionContext.reset()

    def teardown_method(self):
        ExecutionContext.reset()

    def test_source_info_integration(self):
        """Should integrate source info from source_detector."""

        class MockSourceInfo:
            type = "web"
            raw_source = "https://react.dev/"
            parsed = {"url": "https://react.dev/"}
            suggested_name = "react"

        ctx = ExecutionContext.initialize(source_info=MockSourceInfo())

        assert ctx.source is not None
        assert ctx.source.type == "web"
        assert ctx.source.raw_source == "https://react.dev/"
        assert ctx.source.suggested_name == "react"


class TestExecutionContextOverride:
    """Tests for the override context manager."""

    def setup_method(self):
        ExecutionContext.reset()

    def teardown_method(self):
        ExecutionContext.reset()

    def test_override_temporarily_changes_values(self):
        """override() should temporarily change values."""
        args = argparse.Namespace(name="original", enhance_level=2)
        ctx = ExecutionContext.initialize(args=args)

        assert ctx.enhancement.level == 2

        with ctx.override(enhancement__level=3):
            ctx_from_get = ExecutionContext.get()
            assert ctx_from_get.enhancement.level == 3

        # After exit, original value restored
        assert ExecutionContext.get().enhancement.level == 2

    def test_override_restores_on_exception(self):
        """override() should restore values even on exception."""
        args = argparse.Namespace(name="original", enhance_level=2)
        ctx = ExecutionContext.initialize(args=args)

        try:
            with ctx.override(enhancement__level=3):
                assert ExecutionContext.get().enhancement.level == 3
                raise ValueError("Test error")
        except ValueError:
            pass

        # Should still be restored
        assert ExecutionContext.get().enhancement.level == 2


class TestExecutionContextValidation:
    """Tests for Pydantic validation."""

    def setup_method(self):
        ExecutionContext.reset()

    def teardown_method(self):
        ExecutionContext.reset()

    def test_enhancement_level_bounds(self):
        """Enhancement level should be 0-3."""
        args = argparse.Namespace(name="test", enhance_level=5)

        with pytest.raises(ValueError) as exc_info:
            ExecutionContext.initialize(args=args)

        assert "level" in str(exc_info.value)

    def test_analysis_depth_choices(self):
        """Analysis depth should reject invalid values."""
        import pydantic

        args = argparse.Namespace(name="test", depth="invalid")
        with pytest.raises(pydantic.ValidationError):
            ExecutionContext.initialize(args=args)

    def test_analysis_depth_valid_choices(self):
        """Analysis depth should accept surface, deep, full."""
        for depth in ("surface", "deep", "full"):
            ExecutionContext.reset()
            args = argparse.Namespace(name="test", depth=depth)
            ctx = ExecutionContext.initialize(args=args)
            assert ctx.analysis.depth == depth


class TestExecutionContextDefaults:
    """Tests for default values."""

    def setup_method(self):
        ExecutionContext.reset()

    def teardown_method(self):
        ExecutionContext.reset()

    def test_default_values(self):
        """Should have sensible defaults."""
        ctx = ExecutionContext.initialize()

        # Enhancement defaults
        assert ctx.enhancement.enabled is True
        assert ctx.enhancement.level == 2
        assert ctx.enhancement.mode == "auto"  # Default is auto, resolved at runtime
        assert ctx.enhancement.timeout == 2700  # 45 minutes

        # Output defaults
        assert ctx.output.name is None
        assert ctx.output.dry_run is False

        # Scraping defaults
        assert ctx.scraping.browser is False
        assert ctx.scraping.workers == 1
        assert ctx.scraping.languages == ["en"]

        # Analysis defaults
        assert ctx.analysis.depth == "surface"
        assert ctx.analysis.skip_patterns is False

        # RAG defaults
        assert ctx.rag.chunk_for_rag is False
        assert ctx.rag.chunk_tokens == 512
