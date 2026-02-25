from unittest.mock import MagicMock, patch

import pytest

from skill_seekers.cli.enhance_skill_local import (
    AGENT_PRESETS,
    LocalSkillEnhancer,
    detect_terminal_app,
)


def _make_skill_dir(tmp_path):
    skill_dir = tmp_path / "test_skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Test", encoding="utf-8")
    return skill_dir


def _allow_executable(monkeypatch, name="my-agent"):
    monkeypatch.setattr(
        "skill_seekers.cli.enhance_skill_local.shutil.which",
        lambda executable: f"/usr/bin/{executable}" if executable == name else None,
    )


class TestMultiAgentSupport:
    """Test multi-agent enhancement support."""

    def test_agent_presets_structure(self):
        """Verify AGENT_PRESETS has required fields."""
        for preset in AGENT_PRESETS.values():
            assert "display_name" in preset
            assert "command" in preset
            assert "supports_skip_permissions" in preset
            assert isinstance(preset["command"], list)
            assert len(preset["command"]) > 0

    def test_build_agent_command_claude(self, tmp_path):
        """Test Claude Code command building."""
        skill_dir = _make_skill_dir(tmp_path)
        enhancer = LocalSkillEnhancer(skill_dir, agent="claude")
        prompt_file = str(tmp_path / "prompt.txt")

        cmd_parts, uses_file = enhancer._build_agent_command(prompt_file, True)

        assert cmd_parts[0] == "claude"
        assert "--dangerously-skip-permissions" in cmd_parts
        assert prompt_file in cmd_parts
        assert uses_file is True

    def test_build_agent_command_codex(self, tmp_path):
        """Test Codex CLI command building."""
        skill_dir = _make_skill_dir(tmp_path)
        enhancer = LocalSkillEnhancer(skill_dir, agent="codex")
        prompt_file = str(tmp_path / "prompt.txt")

        cmd_parts, uses_file = enhancer._build_agent_command(prompt_file, False)

        assert cmd_parts[0] == "codex"
        assert "exec" in cmd_parts
        assert "--full-auto" in cmd_parts
        assert "--skip-git-repo-check" in cmd_parts
        assert uses_file is False

    def test_build_agent_command_custom_with_placeholder(self, tmp_path, monkeypatch):
        """Test custom command with {prompt_file} placeholder."""
        _allow_executable(monkeypatch, name="my-agent")
        skill_dir = _make_skill_dir(tmp_path)
        enhancer = LocalSkillEnhancer(
            skill_dir,
            agent="custom",
            agent_cmd="my-agent --input {prompt_file}",
        )
        prompt_file = str(tmp_path / "prompt.txt")

        cmd_parts, uses_file = enhancer._build_agent_command(prompt_file, False)

        assert cmd_parts[0] == "my-agent"
        assert "--input" in cmd_parts
        assert prompt_file in cmd_parts
        assert uses_file is True

    def test_custom_agent_requires_command(self, tmp_path):
        """Test custom agent fails without --agent-cmd."""
        skill_dir = _make_skill_dir(tmp_path)

        with pytest.raises(ValueError, match="Custom agent requires --agent-cmd"):
            LocalSkillEnhancer(skill_dir, agent="custom")

    def test_invalid_agent_name(self, tmp_path):
        """Test invalid agent name raises error."""
        skill_dir = _make_skill_dir(tmp_path)

        with pytest.raises(ValueError, match="Unknown agent"):
            LocalSkillEnhancer(skill_dir, agent="invalid-agent")

    def test_agent_normalization(self, tmp_path):
        """Test agent name normalization (aliases)."""
        skill_dir = _make_skill_dir(tmp_path)

        for alias in ["claude-code", "claude_code", "CLAUDE"]:
            enhancer = LocalSkillEnhancer(skill_dir, agent=alias)
            assert enhancer.agent == "claude"

    def test_environment_variable_agent(self, tmp_path, monkeypatch):
        """Test SKILL_SEEKER_AGENT environment variable."""
        skill_dir = _make_skill_dir(tmp_path)

        monkeypatch.setenv("SKILL_SEEKER_AGENT", "codex")
        enhancer = LocalSkillEnhancer(skill_dir)

        assert enhancer.agent == "codex"

    def test_environment_variable_custom_command(self, tmp_path, monkeypatch):
        """Test SKILL_SEEKER_AGENT_CMD environment variable."""
        _allow_executable(monkeypatch, name="my-agent")
        skill_dir = _make_skill_dir(tmp_path)

        monkeypatch.setenv("SKILL_SEEKER_AGENT", "custom")
        monkeypatch.setenv("SKILL_SEEKER_AGENT_CMD", "my-agent {prompt_file}")

        enhancer = LocalSkillEnhancer(skill_dir)
        assert enhancer.agent == "custom"
        assert enhancer.agent_cmd == "my-agent {prompt_file}"

    def test_rejects_command_with_semicolon(self, tmp_path):
        """Test rejection of commands with shell metacharacters."""
        skill_dir = _make_skill_dir(tmp_path)

        with pytest.raises(ValueError, match="dangerous shell characters"):
            LocalSkillEnhancer(
                skill_dir,
                agent="custom",
                agent_cmd="evil-cmd; rm -rf /",
            )

    def test_rejects_command_with_pipe(self, tmp_path):
        """Test rejection of commands with pipe."""
        skill_dir = _make_skill_dir(tmp_path)

        with pytest.raises(ValueError, match="dangerous shell characters"):
            LocalSkillEnhancer(
                skill_dir,
                agent="custom",
                agent_cmd="cmd | malicious",
            )

    def test_rejects_command_with_background_job(self, tmp_path):
        """Test rejection of commands with background job operator."""
        skill_dir = _make_skill_dir(tmp_path)

        with pytest.raises(ValueError, match="dangerous shell characters"):
            LocalSkillEnhancer(
                skill_dir,
                agent="custom",
                agent_cmd="cmd & malicious",
            )

    def test_rejects_missing_executable(self, tmp_path, monkeypatch):
        """Test rejection when executable is not found on PATH."""
        monkeypatch.setattr("skill_seekers.cli.enhance_skill_local.shutil.which", lambda _exe: None)
        skill_dir = _make_skill_dir(tmp_path)

        with pytest.raises(ValueError, match="not found in PATH"):
            LocalSkillEnhancer(
                skill_dir,
                agent="custom",
                agent_cmd="missing-agent {prompt_file}",
            )


# ---------------------------------------------------------------------------
# Helpers shared by new test classes
# ---------------------------------------------------------------------------


def _make_skill_dir_with_refs(tmp_path, ref_content="# Ref\nSome reference content.\n"):
    """Create a skill dir with SKILL.md and one reference file."""
    skill_dir = tmp_path / "my_skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# My Skill\nInitial content.", encoding="utf-8")
    refs_dir = skill_dir / "references"
    refs_dir.mkdir()
    (refs_dir / "api.md").write_text(ref_content, encoding="utf-8")
    return skill_dir


# ---------------------------------------------------------------------------
# detect_terminal_app
# ---------------------------------------------------------------------------


class TestDetectTerminalApp:
    def test_skill_seeker_terminal_takes_priority(self, monkeypatch):
        monkeypatch.setenv("SKILL_SEEKER_TERMINAL", "Ghostty")
        monkeypatch.delenv("TERM_PROGRAM", raising=False)
        terminal, method = detect_terminal_app()
        assert terminal == "Ghostty"
        assert method == "SKILL_SEEKER_TERMINAL"

    def test_term_program_iterm_mapped(self, monkeypatch):
        monkeypatch.delenv("SKILL_SEEKER_TERMINAL", raising=False)
        monkeypatch.setenv("TERM_PROGRAM", "iTerm.app")
        terminal, method = detect_terminal_app()
        assert terminal == "iTerm"
        assert method == "TERM_PROGRAM"

    def test_term_program_apple_terminal_mapped(self, monkeypatch):
        monkeypatch.delenv("SKILL_SEEKER_TERMINAL", raising=False)
        monkeypatch.setenv("TERM_PROGRAM", "Apple_Terminal")
        terminal, method = detect_terminal_app()
        assert terminal == "Terminal"

    def test_term_program_ghostty_mapped(self, monkeypatch):
        monkeypatch.delenv("SKILL_SEEKER_TERMINAL", raising=False)
        monkeypatch.setenv("TERM_PROGRAM", "ghostty")
        terminal, method = detect_terminal_app()
        assert terminal == "Ghostty"

    def test_unknown_term_program_falls_back_to_terminal(self, monkeypatch):
        monkeypatch.delenv("SKILL_SEEKER_TERMINAL", raising=False)
        monkeypatch.setenv("TERM_PROGRAM", "some-unknown-terminal")
        terminal, method = detect_terminal_app()
        assert terminal == "Terminal"
        assert "unknown" in method

    def test_no_env_defaults_to_terminal(self, monkeypatch):
        monkeypatch.delenv("SKILL_SEEKER_TERMINAL", raising=False)
        monkeypatch.delenv("TERM_PROGRAM", raising=False)
        terminal, method = detect_terminal_app()
        assert terminal == "Terminal"
        assert method == "default"

    def test_skill_seeker_overrides_term_program(self, monkeypatch):
        monkeypatch.setenv("SKILL_SEEKER_TERMINAL", "WezTerm")
        monkeypatch.setenv("TERM_PROGRAM", "Apple_Terminal")
        terminal, method = detect_terminal_app()
        assert terminal == "WezTerm"
        assert method == "SKILL_SEEKER_TERMINAL"


# ---------------------------------------------------------------------------
# write_status / read_status
# ---------------------------------------------------------------------------


class TestStatusReadWrite:
    def test_write_and_read_status(self, tmp_path):
        skill_dir = _make_skill_dir_with_refs(tmp_path)
        enhancer = LocalSkillEnhancer(skill_dir)

        enhancer.write_status("running", message="In progress", progress=0.5)
        data = enhancer.read_status()

        assert data is not None
        assert data["status"] == "running"
        assert data["message"] == "In progress"
        assert data["progress"] == 0.5
        assert data["skill_dir"] == str(skill_dir)

    def test_write_status_creates_file(self, tmp_path):
        skill_dir = _make_skill_dir_with_refs(tmp_path)
        enhancer = LocalSkillEnhancer(skill_dir)

        enhancer.write_status("pending")
        assert enhancer.status_file.exists()

    def test_read_status_returns_none_if_no_file(self, tmp_path):
        skill_dir = _make_skill_dir_with_refs(tmp_path)
        enhancer = LocalSkillEnhancer(skill_dir)
        assert enhancer.read_status() is None

    def test_write_status_includes_timestamp(self, tmp_path):
        skill_dir = _make_skill_dir_with_refs(tmp_path)
        enhancer = LocalSkillEnhancer(skill_dir)

        enhancer.write_status("completed")
        data = enhancer.read_status()
        assert "timestamp" in data
        assert data["timestamp"]  # non-empty

    def test_write_status_error_field(self, tmp_path):
        skill_dir = _make_skill_dir_with_refs(tmp_path)
        enhancer = LocalSkillEnhancer(skill_dir)

        enhancer.write_status("failed", error="Something went wrong")
        data = enhancer.read_status()
        assert data["status"] == "failed"
        assert data["error"] == "Something went wrong"

    def test_read_status_returns_none_on_corrupt_file(self, tmp_path):
        skill_dir = _make_skill_dir_with_refs(tmp_path)
        enhancer = LocalSkillEnhancer(skill_dir)

        enhancer.status_file.write_text("{not valid json}", encoding="utf-8")
        assert enhancer.read_status() is None

    def test_multiple_writes_last_wins(self, tmp_path):
        skill_dir = _make_skill_dir_with_refs(tmp_path)
        enhancer = LocalSkillEnhancer(skill_dir)

        enhancer.write_status("pending")
        enhancer.write_status("running")
        enhancer.write_status("completed")

        data = enhancer.read_status()
        assert data["status"] == "completed"


# ---------------------------------------------------------------------------
# summarize_reference
# ---------------------------------------------------------------------------


class TestSummarizeReference:
    def _enhancer(self, tmp_path):
        skill_dir = _make_skill_dir_with_refs(tmp_path)
        return LocalSkillEnhancer(skill_dir)

    def test_short_content_unchanged_intro(self, tmp_path):
        """Very short content - intro lines == all lines."""
        enhancer = self._enhancer(tmp_path)
        content = "Line 1\nLine 2\nLine 3\n"
        result = enhancer.summarize_reference(content, target_ratio=0.3)
        # Should still produce something
        assert result
        assert "intelligently summarized" in result.lower()

    def test_extracts_code_blocks(self, tmp_path):
        enhancer = self._enhancer(tmp_path)
        content = "\n".join(["Intro line"] * 20) + "\n"
        content += "```python\nprint('hello')\n```\n"
        content += "\n".join(["Other line"] * 20)
        result = enhancer.summarize_reference(content)
        assert "```python" in result
        assert "print('hello')" in result

    def test_preserves_headings(self, tmp_path):
        enhancer = self._enhancer(tmp_path)
        content = "\n".join(["Intro line"] * 20) + "\n"
        content += "## My Heading\n\nFirst paragraph.\nSecond paragraph.\n"
        content += "\n".join(["Other line"] * 20)
        result = enhancer.summarize_reference(content)
        assert "## My Heading" in result

    def test_adds_truncation_notice(self, tmp_path):
        enhancer = self._enhancer(tmp_path)
        content = "Some content line\n" * 100
        result = enhancer.summarize_reference(content)
        assert "intelligently summarized" in result.lower()

    def test_target_ratio_applied(self, tmp_path):
        enhancer = self._enhancer(tmp_path)
        content = "A line of content.\n" * 500
        result = enhancer.summarize_reference(content, target_ratio=0.1)
        # Result should be significantly shorter than original
        assert len(result) < len(content)

    def test_code_blocks_not_arbitrarily_capped(self, tmp_path):
        """Code blocks should not be arbitrarily capped at 5 - should use token budget."""
        enhancer = self._enhancer(tmp_path)
        content = "\n".join(["Intro line"] * 10) + "\n"  # Shorter intro
        for i in range(10):
            content += f"```\ncode_block_{i}()\n```\n"  # Short code blocks
        # Use high ratio to ensure budget fits well beyond 5 blocks
        result = enhancer.summarize_reference(content, target_ratio=0.9)
        # Each block has opening + closing ```, so divide by 2 for actual block count
        code_block_count = result.count("```") // 2
        assert code_block_count > 5, f"Expected >5 code blocks, got {code_block_count}"


# ---------------------------------------------------------------------------
# create_enhancement_prompt
# ---------------------------------------------------------------------------


class TestCreateEnhancementPrompt:
    def test_returns_string_with_references(self, tmp_path):
        skill_dir = _make_skill_dir_with_refs(tmp_path)
        enhancer = LocalSkillEnhancer(skill_dir)
        prompt = enhancer.create_enhancement_prompt()
        assert prompt is not None
        assert isinstance(prompt, str)
        assert len(prompt) > 100

    def test_prompt_contains_skill_name(self, tmp_path):
        skill_dir = _make_skill_dir_with_refs(tmp_path)
        enhancer = LocalSkillEnhancer(skill_dir)
        prompt = enhancer.create_enhancement_prompt()
        assert skill_dir.name in prompt

    def test_prompt_contains_current_skill_md(self, tmp_path):
        skill_dir = _make_skill_dir_with_refs(tmp_path)
        (skill_dir / "SKILL.md").write_text("# ExistingContent MARKER", encoding="utf-8")
        enhancer = LocalSkillEnhancer(skill_dir)
        prompt = enhancer.create_enhancement_prompt()
        assert "ExistingContent MARKER" in prompt

    def test_prompt_contains_reference_content(self, tmp_path):
        skill_dir = _make_skill_dir_with_refs(tmp_path, ref_content="UNIQUE_REF_MARKER\n")
        enhancer = LocalSkillEnhancer(skill_dir)
        prompt = enhancer.create_enhancement_prompt()
        assert "UNIQUE_REF_MARKER" in prompt

    def test_returns_none_when_no_references(self, tmp_path):
        """If there are no reference files, create_enhancement_prompt returns None."""
        skill_dir = tmp_path / "empty_skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Empty", encoding="utf-8")
        # No references dir at all
        enhancer = LocalSkillEnhancer(skill_dir)
        result = enhancer.create_enhancement_prompt()
        assert result is None

    def test_summarization_applied_when_requested(self, tmp_path):
        """When use_summarization=True, result should be smaller (or contain marker)."""
        # Create very large reference content
        big_content = ("Reference line with lots of content.\n") * 1000
        skill_dir = _make_skill_dir_with_refs(tmp_path, ref_content=big_content)
        enhancer = LocalSkillEnhancer(skill_dir)
        prompt = enhancer.create_enhancement_prompt(use_summarization=True)
        assert prompt is not None
        # Summarization should have kicked in
        assert "intelligently summarized" in prompt.lower()

    def test_prompt_includes_task_instructions(self, tmp_path):
        skill_dir = _make_skill_dir_with_refs(tmp_path)
        enhancer = LocalSkillEnhancer(skill_dir)
        prompt = enhancer.create_enhancement_prompt()
        assert "SKILL.md" in prompt
        # Should have save instructions
        assert "SAVE" in prompt.upper() or "write" in prompt.lower()


# ---------------------------------------------------------------------------
# _run_headless — mocked subprocess
# ---------------------------------------------------------------------------


class TestRunHeadless:
    def _make_skill_with_md(self, tmp_path, md_content="# Original\nInitial."):
        skill_dir = _make_skill_dir_with_refs(tmp_path)
        (skill_dir / "SKILL.md").write_text(md_content, encoding="utf-8")
        return skill_dir

    def test_returns_false_when_agent_not_found(self, tmp_path):
        """FileNotFoundError → returns False."""
        skill_dir = self._make_skill_with_md(tmp_path)
        enhancer = LocalSkillEnhancer(skill_dir, agent="claude")

        with patch.object(
            enhancer, "_run_agent_command", return_value=(None, "Command not found: claude")
        ):
            result = enhancer._run_headless(str(tmp_path / "prompt.txt"), timeout=10)
        assert result is False

    def test_returns_false_on_nonzero_exit(self, tmp_path):
        skill_dir = self._make_skill_with_md(tmp_path)
        enhancer = LocalSkillEnhancer(skill_dir, agent="claude")

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "some error"
        mock_result.stdout = ""
        with patch.object(enhancer, "_run_agent_command", return_value=(mock_result, None)):
            result = enhancer._run_headless(str(tmp_path / "prompt.txt"), timeout=10)
        assert result is False

    def test_returns_false_when_skill_md_not_updated(self, tmp_path):
        """Agent exits 0 but SKILL.md mtime/size unchanged → returns False."""
        skill_dir = self._make_skill_with_md(tmp_path)
        enhancer = LocalSkillEnhancer(skill_dir, agent="claude")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        with patch.object(enhancer, "_run_agent_command", return_value=(mock_result, None)):
            # No change to SKILL.md → should return False
            result = enhancer._run_headless(str(tmp_path / "prompt.txt"), timeout=10)
        assert result is False

    def test_returns_true_when_skill_md_updated(self, tmp_path):
        """Agent exits 0 AND SKILL.md is larger → returns True."""
        skill_dir = self._make_skill_with_md(tmp_path, md_content="# Short")
        enhancer = LocalSkillEnhancer(skill_dir, agent="claude")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        def _fake_run(prompt_file, timeout, include_permissions_flag, quiet=False):  # noqa: ARG001
            # Simulate agent updating SKILL.md with more content
            import time

            time.sleep(0.01)
            (skill_dir / "SKILL.md").write_text("# Enhanced\n" + "A" * 500, encoding="utf-8")
            return mock_result, None

        with patch.object(enhancer, "_run_agent_command", side_effect=_fake_run):
            result = enhancer._run_headless(str(tmp_path / "prompt.txt"), timeout=10)
        assert result is True


# ---------------------------------------------------------------------------
# run() orchestration
# ---------------------------------------------------------------------------


class TestRunOrchestration:
    def test_run_returns_false_for_missing_skill_dir(self, tmp_path):
        nonexistent = tmp_path / "does_not_exist"
        enhancer = LocalSkillEnhancer(nonexistent, agent="claude")
        result = enhancer.run(headless=True, timeout=5)
        assert result is False

    def test_run_returns_false_when_no_references(self, tmp_path):
        skill_dir = tmp_path / "empty_skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Empty", encoding="utf-8")
        # No references dir
        enhancer = LocalSkillEnhancer(skill_dir, agent="claude")
        result = enhancer.run(headless=True, timeout=5)
        assert result is False

    def test_run_delegates_to_background(self, tmp_path):
        """run(background=True) should delegate to _run_background."""
        skill_dir = _make_skill_dir_with_refs(tmp_path)
        enhancer = LocalSkillEnhancer(skill_dir, agent="claude")

        with patch.object(enhancer, "_run_background", return_value=True) as mock_bg:
            result = enhancer.run(background=True, timeout=5)
        mock_bg.assert_called_once()
        assert result is True

    def test_run_delegates_to_daemon(self, tmp_path):
        """run(daemon=True) should delegate to _run_daemon."""
        skill_dir = _make_skill_dir_with_refs(tmp_path)
        enhancer = LocalSkillEnhancer(skill_dir, agent="claude")

        with patch.object(enhancer, "_run_daemon", return_value=True) as mock_dm:
            result = enhancer.run(daemon=True, timeout=5)
        mock_dm.assert_called_once()
        assert result is True

    def test_run_calls_run_headless_in_headless_mode(self, tmp_path):
        """run(headless=True) should ultimately call _run_headless."""
        skill_dir = _make_skill_dir_with_refs(tmp_path)
        enhancer = LocalSkillEnhancer(skill_dir, agent="claude")

        with patch.object(enhancer, "_run_headless", return_value=True) as mock_hl:
            result = enhancer.run(headless=True, timeout=5)
        mock_hl.assert_called_once()
        assert result is True


# ---------------------------------------------------------------------------
# _run_background status transitions
# ---------------------------------------------------------------------------


class TestRunBackground:
    def test_background_writes_pending_status(self, tmp_path):
        """_run_background writes 'pending' status before spawning thread."""
        skill_dir = _make_skill_dir_with_refs(tmp_path)
        enhancer = LocalSkillEnhancer(skill_dir, agent="claude")

        # Patch _run_headless so the thread finishes quickly without real subprocess
        with patch.object(enhancer, "_run_headless", return_value=True):
            enhancer._run_background(headless=True, timeout=5)

        # Give background thread a moment
        import time

        time.sleep(0.1)

        # Status file should exist (written by the worker)
        data = enhancer.read_status()
        assert data is not None

    def test_background_returns_true_immediately(self, tmp_path):
        """_run_background should return True after starting thread, not after completion."""
        skill_dir = _make_skill_dir_with_refs(tmp_path)
        enhancer = LocalSkillEnhancer(skill_dir, agent="claude")

        # Delay the headless run to confirm we don't block
        import time

        def _slow_run(*_args, **_kwargs):
            time.sleep(0.5)
            return True

        with patch.object(enhancer, "_run_headless", side_effect=_slow_run):
            start = time.time()
            result = enhancer._run_background(headless=True, timeout=10)
            elapsed = time.time() - start

        # Should have returned quickly (not waited for the slow thread)
        assert result is True
        assert elapsed < 0.4, f"_run_background took {elapsed:.2f}s - should return immediately"


class TestEnhanceDispatcher:
    """Test auto-detection of API vs LOCAL mode in enhance main()."""

    def test_detect_api_target_anthropic(self, monkeypatch):
        """ANTHROPIC_API_KEY detected as claude target."""
        from skill_seekers.cli.enhance_skill_local import _detect_api_target

        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        result = _detect_api_target()
        assert result == ("claude", "sk-ant-test")

    def test_detect_api_target_google(self, monkeypatch):
        """GOOGLE_API_KEY detected as gemini target when no Anthropic key."""
        from skill_seekers.cli.enhance_skill_local import _detect_api_target

        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
        monkeypatch.setenv("GOOGLE_API_KEY", "AIza-test")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        result = _detect_api_target()
        assert result == ("gemini", "AIza-test")

    def test_detect_api_target_openai(self, monkeypatch):
        """OPENAI_API_KEY detected as openai target when no higher-priority key."""
        from skill_seekers.cli.enhance_skill_local import _detect_api_target

        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-test")
        result = _detect_api_target()
        assert result == ("openai", "sk-openai-test")

    def test_detect_api_target_none(self, monkeypatch):
        """Returns None when no API keys are set."""
        from skill_seekers.cli.enhance_skill_local import _detect_api_target

        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        result = _detect_api_target()
        assert result is None

    def test_detect_api_target_anthropic_priority(self, monkeypatch):
        """ANTHROPIC_API_KEY takes priority over GOOGLE_API_KEY."""
        from skill_seekers.cli.enhance_skill_local import _detect_api_target

        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        monkeypatch.setenv("GOOGLE_API_KEY", "AIza-test")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-test")
        result = _detect_api_target()
        assert result == ("claude", "sk-ant-test")

    def test_detect_api_target_auth_token_fallback(self, monkeypatch):
        """ANTHROPIC_AUTH_TOKEN is used when ANTHROPIC_API_KEY is absent."""
        from skill_seekers.cli.enhance_skill_local import _detect_api_target

        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "sk-auth-test")
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        result = _detect_api_target()
        assert result == ("claude", "sk-auth-test")

    def test_main_delegates_to_api_when_key_set(self, monkeypatch, tmp_path):
        """main() calls _run_api_enhance when an API key is detected."""
        import sys
        from skill_seekers.cli.enhance_skill_local import main

        skill_dir = _make_skill_dir(tmp_path)
        monkeypatch.setenv("GOOGLE_API_KEY", "AIza-test")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setattr(sys, "argv", ["enhance", str(skill_dir)])

        called_with = {}

        def fake_run_api(target, api_key):
            called_with["target"] = target
            called_with["api_key"] = api_key

        monkeypatch.setattr("skill_seekers.cli.enhance_skill_local._run_api_enhance", fake_run_api)
        main()
        assert called_with == {"target": "gemini", "api_key": "AIza-test"}

    def test_main_uses_local_when_mode_local(self, monkeypatch, tmp_path):
        """main() stays in LOCAL mode when --mode LOCAL is passed."""
        import sys
        from skill_seekers.cli.enhance_skill_local import main

        skill_dir = _make_skill_dir(tmp_path)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        monkeypatch.setattr(sys, "argv", ["enhance", str(skill_dir), "--mode", "LOCAL"])

        api_called = []
        monkeypatch.setattr(
            "skill_seekers.cli.enhance_skill_local._run_api_enhance",
            lambda *a: api_called.append(a),
        )

        # LocalSkillEnhancer.run will fail without a real agent, just verify
        # _run_api_enhance was NOT called
        with patch("skill_seekers.cli.enhance_skill_local.LocalSkillEnhancer") as mock_enhancer:
            mock_instance = MagicMock()
            mock_instance.run.return_value = True
            mock_enhancer.return_value = mock_instance
            with pytest.raises(SystemExit):
                main()

        assert api_called == [], "_run_api_enhance should not be called in LOCAL mode"

    def test_main_uses_local_when_no_api_keys(self, monkeypatch, tmp_path):
        """main() uses LOCAL mode when no API keys are present."""
        import sys
        from skill_seekers.cli.enhance_skill_local import main

        skill_dir = _make_skill_dir(tmp_path)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setattr(sys, "argv", ["enhance", str(skill_dir)])

        api_called = []
        monkeypatch.setattr(
            "skill_seekers.cli.enhance_skill_local._run_api_enhance",
            lambda *a: api_called.append(a),
        )

        with patch("skill_seekers.cli.enhance_skill_local.LocalSkillEnhancer") as mock_enhancer:
            mock_instance = MagicMock()
            mock_instance.run.return_value = True
            mock_enhancer.return_value = mock_instance
            with pytest.raises(SystemExit):
                main()

        assert api_called == [], "_run_api_enhance should not be called without API keys"
