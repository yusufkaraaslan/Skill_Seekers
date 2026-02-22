"""Tests for the smart enhancement dispatcher (enhance_command.py)."""

import argparse
import sys

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_args(**kwargs):
    """Build a fake Namespace with sensible defaults."""
    defaults = {
        "skill_directory": "output/react",
        "target": None,
        "api_key": None,
        "dry_run": False,
        "agent": None,
        "agent_cmd": None,
        "interactive_enhancement": False,
        "background": False,
        "daemon": False,
        "no_force": False,
        "timeout": 600,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_skill_dir(tmp_path):
    skill_dir = tmp_path / "test_skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Test", encoding="utf-8")
    return skill_dir


# ---------------------------------------------------------------------------
# _is_root
# ---------------------------------------------------------------------------


class TestIsRoot:
    def test_returns_bool(self):
        from skill_seekers.cli.enhance_command import _is_root

        assert isinstance(_is_root(), bool)

    def test_not_root_when_monkeypatched(self, monkeypatch):
        import os

        monkeypatch.setattr(os, "getuid", lambda: 1000)
        from skill_seekers.cli.enhance_command import _is_root

        assert _is_root() is False

    def test_root_when_uid_zero(self, monkeypatch):
        import os

        monkeypatch.setattr(os, "getuid", lambda: 0)
        from skill_seekers.cli.enhance_command import _is_root

        assert _is_root() is True

    def test_windows_no_getuid(self, monkeypatch):
        """On Windows (no os.getuid), _is_root should return False."""
        import os

        if hasattr(os, "getuid"):
            monkeypatch.delattr(os, "getuid")
        from skill_seekers.cli.enhance_command import _is_root

        assert _is_root() is False


# ---------------------------------------------------------------------------
# _pick_mode — explicit --target flag
# ---------------------------------------------------------------------------


class TestPickModeExplicitTarget:
    def test_target_gemini_forces_api(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        from skill_seekers.cli.enhance_command import _pick_mode

        args = _make_args(target="gemini")
        mode, target = _pick_mode(args)
        assert mode == "api"
        assert target == "gemini"

    def test_target_openai_forces_api(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        from skill_seekers.cli.enhance_command import _pick_mode

        args = _make_args(target="openai")
        mode, target = _pick_mode(args)
        assert mode == "api"
        assert target == "openai"

    def test_target_claude_forces_api(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        from skill_seekers.cli.enhance_command import _pick_mode

        args = _make_args(target="claude")
        mode, target = _pick_mode(args)
        assert mode == "api"
        assert target == "claude"


# ---------------------------------------------------------------------------
# _pick_mode — auto-detection from env vars
# ---------------------------------------------------------------------------


class TestPickModeAutoDetect:
    def test_anthropic_key_selects_claude(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        from skill_seekers.cli.enhance_command import _pick_mode

        mode, target = _pick_mode(_make_args())
        assert mode == "api"
        assert target == "claude"

    def test_google_key_selects_gemini(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
        monkeypatch.setenv("GOOGLE_API_KEY", "AIza-test")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        from skill_seekers.cli.enhance_command import _pick_mode

        mode, target = _pick_mode(_make_args())
        assert mode == "api"
        assert target == "gemini"

    def test_openai_key_selects_openai(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-proj-test")

        from skill_seekers.cli.enhance_command import _pick_mode

        mode, target = _pick_mode(_make_args())
        assert mode == "api"
        assert target == "openai"

    def test_no_keys_falls_back_to_local(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        from skill_seekers.cli.enhance_command import _pick_mode

        mode, target = _pick_mode(_make_args())
        assert mode == "local"
        assert target is None

    def test_anthropic_takes_priority_over_google(self, monkeypatch):
        """ANTHROPIC_API_KEY should win when both are set."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        monkeypatch.setenv("GOOGLE_API_KEY", "AIza-test")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        from skill_seekers.cli.enhance_command import _pick_mode

        mode, target = _pick_mode(_make_args())
        assert mode == "api"
        assert target == "claude"


# ---------------------------------------------------------------------------
# _pick_mode — config default_agent
# ---------------------------------------------------------------------------


class TestPickModeConfigAgent:
    def _patch_config(self, monkeypatch, agent: str | None):
        """Patch get_config_manager to return a stub with get_default_agent()."""
        monkeypatch.setattr(
            "skill_seekers.cli.enhance_command._get_config_default_agent",
            lambda: agent,
        )

    def test_config_gemini_with_key_uses_gemini(self, monkeypatch):
        self._patch_config(monkeypatch, "gemini")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
        monkeypatch.setenv("GOOGLE_API_KEY", "AIza-test")

        from skill_seekers.cli.enhance_command import _pick_mode

        mode, target = _pick_mode(_make_args())
        assert mode == "api"
        assert target == "gemini"

    def test_config_gemini_without_key_falls_to_autodetect(self, monkeypatch):
        """Config says gemini but no GOOGLE_API_KEY → auto-detect."""
        self._patch_config(monkeypatch, "gemini")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        from skill_seekers.cli.enhance_command import _pick_mode

        mode, target = _pick_mode(_make_args())
        assert mode == "local"

    def test_config_agent_overridden_by_explicit_target(self, monkeypatch):
        """--target flag takes priority over config."""
        self._patch_config(monkeypatch, "gemini")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        from skill_seekers.cli.enhance_command import _pick_mode

        args = _make_args(target="openai")
        mode, target = _pick_mode(args)
        assert mode == "api"
        assert target == "openai"


# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------


class TestEnhanceArgumentParsing:
    """Test that the enhance parser exposes all expected arguments."""

    def _parse(self, argv, tmp_path):
        import argparse as _ap
        from skill_seekers.cli.arguments.enhance import add_enhance_arguments

        parser = _ap.ArgumentParser()
        add_enhance_arguments(parser)
        return parser.parse_args(argv)

    def test_target_gemini(self, tmp_path):
        args = self._parse(["output/react", "--target", "gemini"], tmp_path)
        assert args.target == "gemini"

    def test_target_openai(self, tmp_path):
        args = self._parse(["output/react", "--target", "openai"], tmp_path)
        assert args.target == "openai"

    def test_api_key_stored(self, tmp_path):
        args = self._parse(["output/react", "--api-key", "test-key-123"], tmp_path)
        assert args.api_key == "test-key-123"

    def test_dry_run(self, tmp_path):
        args = self._parse(["output/react", "--dry-run"], tmp_path)
        assert args.dry_run is True

    def test_no_target_defaults_none(self, tmp_path):
        args = self._parse(["output/react"], tmp_path)
        assert args.target is None

    def test_invalid_target_rejected(self, tmp_path):
        import argparse as _ap
        from skill_seekers.cli.arguments.enhance import add_enhance_arguments

        parser = _ap.ArgumentParser()
        add_enhance_arguments(parser)
        with pytest.raises(SystemExit):
            parser.parse_args(["output/react", "--target", "notaplatform"])


# ---------------------------------------------------------------------------
# main() CLI integration — dry-run + root detection
# ---------------------------------------------------------------------------


class TestEnhanceCommandMain:
    def test_dry_run_no_ai_call(self, tmp_path):
        skill_dir = _make_skill_dir(tmp_path)
        sys_argv_backup = sys.argv.copy()
        sys.argv = ["enhance_command.py", str(skill_dir), "--dry-run"]
        try:
            from skill_seekers.cli.enhance_command import main

            rc = main()
            assert rc == 0
        finally:
            sys.argv = sys_argv_backup

    def test_missing_dir_returns_error(self, tmp_path):
        sys_argv_backup = sys.argv.copy()
        sys.argv = ["enhance_command.py", str(tmp_path / "nonexistent")]
        try:
            from skill_seekers.cli.enhance_command import main

            rc = main()
            assert rc == 1
        finally:
            sys.argv = sys_argv_backup

    def test_root_local_mode_blocked(self, monkeypatch, tmp_path):
        import os

        skill_dir = _make_skill_dir(tmp_path)
        monkeypatch.setattr(os, "getuid", lambda: 0)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        sys_argv_backup = sys.argv.copy()
        sys.argv = ["enhance_command.py", str(skill_dir)]
        try:
            from skill_seekers.cli.enhance_command import main

            rc = main()
            assert rc == 1
        finally:
            sys.argv = sys_argv_backup

    def test_root_api_mode_allowed(self, monkeypatch, tmp_path):
        """Even as root, API mode should be selected (not blocked)."""
        import os

        skill_dir = _make_skill_dir(tmp_path)
        monkeypatch.setattr(os, "getuid", lambda: 0)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")

        # Patch _run_api_mode to avoid real API call
        monkeypatch.setattr(
            "skill_seekers.cli.enhance_command._run_api_mode",
            lambda *_: 0,
        )

        sys_argv_backup = sys.argv.copy()
        sys.argv = ["enhance_command.py", str(skill_dir)]
        try:
            from skill_seekers.cli.enhance_command import main

            rc = main()
            assert rc == 0
        finally:
            sys.argv = sys_argv_backup


# ---------------------------------------------------------------------------
# Config manager — get_default_agent
# ---------------------------------------------------------------------------


class TestConfigManagerDefaultAgent:
    def test_get_default_agent_none_by_default(self, tmp_path, monkeypatch):
        from skill_seekers.cli.config_manager import ConfigManager

        monkeypatch.setattr(ConfigManager, "CONFIG_DIR", tmp_path / "cfg")
        monkeypatch.setattr(ConfigManager, "CONFIG_FILE", tmp_path / "cfg" / "config.json")
        monkeypatch.setattr(ConfigManager, "PROGRESS_DIR", tmp_path / "prog")

        mgr = ConfigManager()
        assert mgr.get_default_agent() is None

    def test_set_and_get_default_agent(self, tmp_path, monkeypatch):
        from skill_seekers.cli.config_manager import ConfigManager

        monkeypatch.setattr(ConfigManager, "CONFIG_DIR", tmp_path / "cfg")
        monkeypatch.setattr(ConfigManager, "CONFIG_FILE", tmp_path / "cfg" / "config.json")
        monkeypatch.setattr(ConfigManager, "PROGRESS_DIR", tmp_path / "prog")

        mgr = ConfigManager()
        mgr.set_default_agent("gemini")
        assert mgr.get_default_agent() == "gemini"

    def test_set_default_agent_persisted(self, tmp_path, monkeypatch):
        from skill_seekers.cli.config_manager import ConfigManager

        monkeypatch.setattr(ConfigManager, "CONFIG_DIR", tmp_path / "cfg")
        config_file = tmp_path / "cfg" / "config.json"
        monkeypatch.setattr(ConfigManager, "CONFIG_FILE", config_file)
        monkeypatch.setattr(ConfigManager, "PROGRESS_DIR", tmp_path / "prog")

        mgr = ConfigManager()
        mgr.set_default_agent("openai")

        # Re-instantiate to verify persistence
        mgr2 = ConfigManager()
        assert mgr2.get_default_agent() == "openai"
