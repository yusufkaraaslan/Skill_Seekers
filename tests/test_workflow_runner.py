"""Tests for the shared workflow_runner utility.

Covers:
- run_workflows() with no workflow flags → (False, [])
- run_workflows() with a single named workflow
- WorkflowEngine loads bundled presets by name (integration)
- run_workflows() with multiple named workflows (chaining)
- run_workflows() with inline --enhance-stage flags
- run_workflows() with both named and inline workflows
- collect_workflow_vars() parsing
- Dry-run mode triggers sys.exit(0)
"""

import argparse
from unittest.mock import MagicMock, patch

import pytest

from skill_seekers.cli.workflow_runner import collect_workflow_vars, run_workflows


# ─────────────────────────── helpers ────────────────────────────────────────


def make_args(
    enhance_workflow=None,
    enhance_stage=None,
    var=None,
    workflow_dry_run=False,
):
    """Build a minimal argparse.Namespace for testing."""
    return argparse.Namespace(
        enhance_workflow=enhance_workflow,
        enhance_stage=enhance_stage,
        var=var,
        workflow_dry_run=workflow_dry_run,
    )


# ─────────────────────────── collect_workflow_vars ──────────────────────────


class TestCollectWorkflowVars:
    def test_no_vars(self):
        args = make_args()
        assert collect_workflow_vars(args) == {}

    def test_single_var(self):
        args = make_args(var=["key=value"])
        assert collect_workflow_vars(args) == {"key": "value"}

    def test_multiple_vars(self):
        args = make_args(var=["a=1", "b=2", "c=hello world"])
        result = collect_workflow_vars(args)
        assert result == {"a": "1", "b": "2", "c": "hello world"}

    def test_var_with_equals_in_value(self):
        args = make_args(var=["url=http://example.com/a=b"])
        result = collect_workflow_vars(args)
        assert result == {"url": "http://example.com/a=b"}

    def test_extra_context_merged(self):
        args = make_args(var=["user_key=abc"])
        result = collect_workflow_vars(args, extra={"extra_key": "xyz"})
        assert result == {"user_key": "abc", "extra_key": "xyz"}

    def test_extra_context_overridden_by_var(self):
        # --var takes precedence because extra is added first, then var overwrites
        args = make_args(var=["key=from_var"])
        result = collect_workflow_vars(args, extra={"key": "from_extra"})
        # var keys should win
        assert result["key"] == "from_var"

    def test_invalid_var_skipped(self):
        """Entries without '=' are silently skipped."""
        args = make_args(var=["no_equals_sign", "good=value"])
        result = collect_workflow_vars(args)
        assert result == {"good": "value"}


# ─────────────────────────── run_workflows ──────────────────────────────────


class TestRunWorkflowsNoFlags:
    def test_returns_false_empty_when_no_flags(self):
        args = make_args()
        executed, names = run_workflows(args)
        assert executed is False
        assert names == []

    def test_returns_false_when_empty_lists(self):
        args = make_args(enhance_workflow=[], enhance_stage=[])
        executed, names = run_workflows(args)
        assert executed is False
        assert names == []


class TestRunWorkflowsSingle:
    """Single --enhance-workflow flag."""

    def test_single_workflow_executes(self):
        args = make_args(enhance_workflow=["minimal"])

        mock_engine = MagicMock()
        mock_engine.workflow.name = "minimal"
        mock_engine.workflow.description = "A minimal workflow"
        mock_engine.workflow.stages = [MagicMock(), MagicMock()]

        with patch(
            "skill_seekers.cli.enhancement_workflow.WorkflowEngine",
            return_value=mock_engine,
        ):
            executed, names = run_workflows(args)

        assert executed is True
        assert names == ["minimal"]
        mock_engine.run.assert_called_once()

    def test_single_workflow_failed_load_skipped(self):
        args = make_args(enhance_workflow=["nonexistent-workflow"])

        with patch(
            "skill_seekers.cli.enhancement_workflow.WorkflowEngine",
            side_effect=FileNotFoundError("not found"),
        ):
            executed, names = run_workflows(args)

        assert executed is False
        assert names == []

    def test_single_workflow_run_failure_continues(self):
        args = make_args(enhance_workflow=["minimal"])

        mock_engine = MagicMock()
        mock_engine.workflow.name = "minimal"
        mock_engine.workflow.description = "desc"
        mock_engine.workflow.stages = []
        mock_engine.run.side_effect = RuntimeError("AI call failed")

        with patch(
            "skill_seekers.cli.enhancement_workflow.WorkflowEngine",
            return_value=mock_engine,
        ):
            executed, names = run_workflows(args)

        # Engine failed → not counted as executed
        assert executed is False
        assert names == []


class TestRunWorkflowsMultiple:
    """Multiple --enhance-workflow flags (chaining)."""

    def test_two_workflows_both_execute(self):
        args = make_args(enhance_workflow=["security-focus", "minimal"])

        engines = []
        for wf_name in ["security-focus", "minimal"]:
            m = MagicMock()
            m.workflow.name = wf_name
            m.workflow.description = f"desc of {wf_name}"
            m.workflow.stages = [MagicMock()]
            engines.append(m)

        with patch(
            "skill_seekers.cli.enhancement_workflow.WorkflowEngine",
            side_effect=engines,
        ):
            executed, names = run_workflows(args)

        assert executed is True
        assert names == ["security-focus", "minimal"]
        for engine in engines:
            engine.run.assert_called_once()

    def test_three_workflows_in_order(self):
        workflow_names = ["security-focus", "minimal", "api-documentation"]
        args = make_args(enhance_workflow=workflow_names)

        run_order = []
        engines = []
        for wf_name in workflow_names:
            m = MagicMock()
            m.workflow.name = wf_name
            m.workflow.description = "desc"
            m.workflow.stages = []
            # Track call order
            m.run.side_effect = lambda *_a, _n=wf_name, **_kw: run_order.append(_n)
            engines.append(m)

        with patch(
            "skill_seekers.cli.enhancement_workflow.WorkflowEngine",
            side_effect=engines,
        ):
            executed, names = run_workflows(args)

        assert executed is True
        assert names == workflow_names
        assert run_order == workflow_names  # Preserves order

    def test_partial_failure_partial_success(self):
        """One workflow fails to load; the other should still run."""
        args = make_args(enhance_workflow=["bad-workflow", "minimal"])

        good_engine = MagicMock()
        good_engine.workflow.name = "minimal"
        good_engine.workflow.description = "desc"
        good_engine.workflow.stages = []

        def side_effect(name, **_kwargs):
            if name == "bad-workflow":
                raise FileNotFoundError("not found")
            return good_engine

        with patch(
            "skill_seekers.cli.enhancement_workflow.WorkflowEngine",
            side_effect=side_effect,
        ):
            executed, names = run_workflows(args)

        assert executed is True
        assert names == ["minimal"]  # Only successful one


class TestRunWorkflowsInlineStages:
    """--enhance-stage flags (combined into one inline workflow)."""

    def test_inline_stages_execute(self):
        args = make_args(enhance_stage=["security:Check security", "cleanup:Remove boilerplate"])

        mock_engine = MagicMock()
        mock_engine.workflow.name = "inline_workflow"
        mock_engine.workflow.stages = [MagicMock(), MagicMock()]

        with patch(
            "skill_seekers.cli.enhancement_workflow.WorkflowEngine",
            return_value=mock_engine,
        ) as MockEngine:
            executed, names = run_workflows(args)

        assert executed is True
        assert "inline_workflow" in names
        mock_engine.run.assert_called_once()

        # Verify inline workflow was built correctly
        call_kwargs = MockEngine.call_args[1]
        stages = call_kwargs["workflow_data"]["stages"]
        assert len(stages) == 2
        assert stages[0]["name"] == "security"
        assert stages[0]["prompt"] == "Check security"
        assert stages[1]["name"] == "cleanup"
        assert stages[1]["prompt"] == "Remove boilerplate"

    def test_inline_stage_without_colon(self):
        """Stage spec without ':' uses the whole string as both name and prompt."""
        args = make_args(enhance_stage=["analyze everything"])

        mock_engine = MagicMock()
        mock_engine.workflow.stages = []

        with patch(
            "skill_seekers.cli.enhancement_workflow.WorkflowEngine",
            return_value=mock_engine,
        ) as MockEngine:
            run_workflows(args)

        call_kwargs = MockEngine.call_args[1]
        stage = call_kwargs["workflow_data"]["stages"][0]
        assert stage["name"] == "stage_1"
        assert stage["prompt"] == "analyze everything"


class TestRunWorkflowsMixed:
    """Both --enhance-workflow and --enhance-stage provided."""

    def test_named_then_inline(self):
        args = make_args(
            enhance_workflow=["security-focus"],
            enhance_stage=["extra:Extra stage"],
        )

        named_engine = MagicMock()
        named_engine.workflow.name = "security-focus"
        named_engine.workflow.description = "desc"
        named_engine.workflow.stages = []

        inline_engine = MagicMock()
        inline_engine.workflow.stages = []

        with patch(
            "skill_seekers.cli.enhancement_workflow.WorkflowEngine",
            side_effect=[named_engine, inline_engine],
        ):
            executed, names = run_workflows(args)

        assert executed is True
        assert "security-focus" in names
        assert "inline_workflow" in names
        named_engine.run.assert_called_once()
        inline_engine.run.assert_called_once()


class TestRunWorkflowsVariables:
    def test_variables_passed_to_run(self):
        args = make_args(
            enhance_workflow=["minimal"],
            var=["framework=django", "depth=comprehensive"],
        )

        mock_engine = MagicMock()
        mock_engine.workflow.name = "minimal"
        mock_engine.workflow.description = "desc"
        mock_engine.workflow.stages = []

        with patch(
            "skill_seekers.cli.enhancement_workflow.WorkflowEngine",
            return_value=mock_engine,
        ):
            run_workflows(args, context={"extra": "ctx"})

        call_kwargs = mock_engine.run.call_args[1]
        ctx = call_kwargs["context"]
        assert ctx["framework"] == "django"
        assert ctx["depth"] == "comprehensive"
        assert ctx["extra"] == "ctx"


class TestRunWorkflowsDryRun:
    def test_dry_run_calls_preview_not_run(self):
        args = make_args(
            enhance_workflow=["minimal"],
            workflow_dry_run=True,
        )

        mock_engine = MagicMock()
        mock_engine.workflow.name = "minimal"
        mock_engine.workflow.description = "desc"
        mock_engine.workflow.stages = []

        with (
            patch(
                "skill_seekers.cli.enhancement_workflow.WorkflowEngine",
                return_value=mock_engine,
            ),
            pytest.raises(SystemExit) as exc,
        ):
            run_workflows(args)

        assert exc.value.code == 0
        mock_engine.preview.assert_called_once()
        mock_engine.run.assert_not_called()

    def test_dry_run_multiple_workflows_all_previewed(self):
        args = make_args(
            enhance_workflow=["security-focus", "minimal"],
            workflow_dry_run=True,
        )

        engines = []
        for name in ["security-focus", "minimal"]:
            m = MagicMock()
            m.workflow.name = name
            m.workflow.description = "desc"
            m.workflow.stages = []
            engines.append(m)

        with (
            patch(
                "skill_seekers.cli.enhancement_workflow.WorkflowEngine",
                side_effect=engines,
            ),
            pytest.raises(SystemExit),
        ):
            run_workflows(args)

        for engine in engines:
            engine.preview.assert_called_once()
            engine.run.assert_not_called()


# ────────────────── bundled preset loading (integration) ─────────────────────


class TestBundledPresetsLoad:
    """Verify WorkflowEngine can load each bundled preset by name.

    These are real integration tests – they actually read the YAML files
    shipped inside the package via importlib.resources.
    """

    BUNDLED_NAMES = [
        "default",
        "minimal",
        "security-focus",
        "architecture-comprehensive",
        "api-documentation",
    ]

    @pytest.mark.parametrize("preset_name", BUNDLED_NAMES)
    def test_bundled_preset_loads(self, preset_name):
        from skill_seekers.cli.enhancement_workflow import WorkflowEngine

        engine = WorkflowEngine(preset_name)
        wf = engine.workflow
        assert wf.name, f"Workflow '{preset_name}' has no name"
        assert isinstance(wf.stages, list), "stages must be a list"
        assert len(wf.stages) > 0, f"Workflow '{preset_name}' has no stages"

    @pytest.mark.parametrize("preset_name", BUNDLED_NAMES)
    def test_bundled_preset_stages_have_required_fields(self, preset_name):
        from skill_seekers.cli.enhancement_workflow import WorkflowEngine

        engine = WorkflowEngine(preset_name)
        for stage in engine.workflow.stages:
            assert stage.name, f"Stage in '{preset_name}' has no name"
            assert stage.type in ("builtin", "custom"), (
                f"Stage '{stage.name}' in '{preset_name}' has unknown type '{stage.type}'"
            )

    def test_unknown_preset_raises_file_not_found(self):
        from skill_seekers.cli.enhancement_workflow import WorkflowEngine

        with pytest.raises(FileNotFoundError):
            WorkflowEngine("completely-nonexistent-preset-xyz")

    def test_list_bundled_workflows_returns_all(self):
        from skill_seekers.cli.enhancement_workflow import list_bundled_workflows

        names = list_bundled_workflows()
        for expected in self.BUNDLED_NAMES:
            assert expected in names, f"'{expected}' not in bundled workflows: {names}"

    def test_list_user_workflows_empty_when_no_user_dir(self, tmp_path, monkeypatch):
        """list_user_workflows returns [] when ~/.config/skill-seekers/workflows/ does not exist."""
        from skill_seekers.cli import enhancement_workflow as ew_mod
        import pathlib

        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        monkeypatch.setenv("HOME", str(fake_home))
        # Also patch Path.home() used inside the module
        monkeypatch.setattr(pathlib.Path, "home", staticmethod(lambda: fake_home))

        names = ew_mod.list_user_workflows()
        assert names == []
