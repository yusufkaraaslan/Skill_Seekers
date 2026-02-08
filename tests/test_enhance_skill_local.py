import pytest

from skill_seekers.cli.enhance_skill_local import AGENT_PRESETS, LocalSkillEnhancer


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
