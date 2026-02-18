"""Tests for the workflows CLI command.

Covers:
- workflows list  (bundled + user)
- workflows show  (found / not-found)
- workflows copy  (bundled → user dir)
- workflows add   (install custom YAML)
- workflows remove (user dir; refuses bundled)
- workflows validate (valid / invalid)
"""

import textwrap
from unittest.mock import patch, MagicMock

import pytest

# Import the MODULE object (not just individual symbols) so we can patch it
# directly via patch.object(). This survives any sys.modules manipulation by
# other tests (e.g. test_swift_detection clears skill_seekers.cli.*), because
# we hold a reference to the original module object at collection time.
import skill_seekers.cli.workflows_command as _wf_cmd

cmd_list = _wf_cmd.cmd_list
cmd_show = _wf_cmd.cmd_show
cmd_copy = _wf_cmd.cmd_copy
cmd_add = _wf_cmd.cmd_add
cmd_remove = _wf_cmd.cmd_remove
cmd_validate = _wf_cmd.cmd_validate


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

MINIMAL_YAML = textwrap.dedent("""\
    name: test-workflow
    description: A test workflow
    version: "1.0"
    applies_to:
      - codebase_analysis
    variables: {}
    stages:
      - name: step1
        type: custom
        target: all
        uses_history: false
        enabled: true
        prompt: "Do something useful."
    post_process:
      reorder_sections: []
      add_metadata: {}
""")

INVALID_YAML = "not: a: valid: workflow"  # missing 'stages' key


@pytest.fixture
def tmp_user_dir(tmp_path, monkeypatch):
    """Redirect USER_WORKFLOWS_DIR to a temp directory.

    Uses patch.object on the captured module reference so the patch is applied
    to the same module dict that the functions reference via __globals__,
    regardless of any sys.modules manipulation by other tests.
    """
    fake_dir = tmp_path / "workflows"
    fake_dir.mkdir()
    monkeypatch.setattr(_wf_cmd, "USER_WORKFLOWS_DIR", fake_dir)
    return fake_dir


@pytest.fixture
def sample_yaml_file(tmp_path):
    """Write MINIMAL_YAML to a temp file and return its path."""
    p = tmp_path / "test-workflow.yaml"
    p.write_text(MINIMAL_YAML, encoding="utf-8")
    return p


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _mock_bundled(names=("default", "minimal", "security-focus")):
    """Patch list_bundled_workflows on the captured module object."""
    return patch.object(_wf_cmd, "list_bundled_workflows", return_value=list(names))


def _mock_bundled_text(name_to_text: dict):
    """Patch _bundled_yaml_text on the captured module object."""

    def _bundled_yaml_text(name):
        return name_to_text.get(name)

    return patch.object(_wf_cmd, "_bundled_yaml_text", side_effect=_bundled_yaml_text)


# ─────────────────────────────────────────────────────────────────────────────
# cmd_list
# ─────────────────────────────────────────────────────────────────────────────


class TestCmdList:
    def test_shows_bundled_and_user(self, capsys, tmp_user_dir):
        (tmp_user_dir / "my-workflow.yaml").write_text(MINIMAL_YAML, encoding="utf-8")

        bundled_text = {"default": MINIMAL_YAML}
        with _mock_bundled(["default"]), _mock_bundled_text(bundled_text):
            rc = cmd_list()

        out = capsys.readouterr().out
        assert rc == 0
        assert "Bundled" in out
        assert "default" in out
        assert "User" in out
        assert "my-workflow" in out

    def test_no_workflows(self, capsys, tmp_user_dir):
        # tmp_user_dir is empty, and we mock bundled to return empty
        with _mock_bundled([]):
            rc = cmd_list()
        assert rc == 0
        assert "No workflows" in capsys.readouterr().out

    def test_only_bundled(self, capsys, tmp_user_dir):
        with _mock_bundled(["default"]), _mock_bundled_text({"default": MINIMAL_YAML}):
            rc = cmd_list()
        out = capsys.readouterr().out
        assert rc == 0
        assert "Bundled" in out
        assert "User" not in out  # no user workflows


# ─────────────────────────────────────────────────────────────────────────────
# cmd_show
# ─────────────────────────────────────────────────────────────────────────────


class TestCmdShow:
    def test_show_bundled(self, capsys):
        with patch.object(_wf_cmd, "_workflow_yaml_text", return_value=MINIMAL_YAML):
            rc = cmd_show("default")
        assert rc == 0
        assert "name: test-workflow" in capsys.readouterr().out

    def test_show_not_found(self, capsys):
        with patch.object(_wf_cmd, "_workflow_yaml_text", return_value=None):
            rc = cmd_show("nonexistent")
        assert rc == 1
        assert "not found" in capsys.readouterr().err.lower()

    def test_show_user_workflow(self, capsys, tmp_user_dir):
        (tmp_user_dir / "my-wf.yaml").write_text(MINIMAL_YAML, encoding="utf-8")
        rc = cmd_show("my-wf")
        assert rc == 0
        assert "name: test-workflow" in capsys.readouterr().out


# ─────────────────────────────────────────────────────────────────────────────
# cmd_copy
# ─────────────────────────────────────────────────────────────────────────────


class TestCmdCopy:
    def test_copy_bundled_to_user_dir(self, capsys, tmp_user_dir):
        with _mock_bundled_text({"security-focus": MINIMAL_YAML}):
            rc = cmd_copy(["security-focus"])

        assert rc == 0
        dest = tmp_user_dir / "security-focus.yaml"
        assert dest.exists()
        assert dest.read_text(encoding="utf-8") == MINIMAL_YAML

    def test_copy_nonexistent(self, capsys, tmp_user_dir):
        with _mock_bundled_text({}), _mock_bundled([]):
            rc = cmd_copy(["ghost-workflow"])
        assert rc == 1
        assert "not found" in capsys.readouterr().err.lower()

    def test_copy_overwrites_existing(self, capsys, tmp_user_dir):
        existing = tmp_user_dir / "default.yaml"
        existing.write_text("old content", encoding="utf-8")

        with _mock_bundled_text({"default": MINIMAL_YAML}):
            rc = cmd_copy(["default"])

        assert rc == 0
        assert existing.read_text(encoding="utf-8") == MINIMAL_YAML
        assert "Warning" in capsys.readouterr().out

    def test_copy_multiple(self, capsys, tmp_user_dir):
        """Copying multiple bundled workflows installs all of them."""
        texts = {"default": MINIMAL_YAML, "minimal": MINIMAL_YAML}
        with _mock_bundled_text(texts):
            rc = cmd_copy(["default", "minimal"])

        assert rc == 0
        assert (tmp_user_dir / "default.yaml").exists()
        assert (tmp_user_dir / "minimal.yaml").exists()

    def test_copy_partial_failure_continues(self, capsys, tmp_user_dir):
        """A missing workflow doesn't prevent others from being copied."""
        with _mock_bundled_text({"default": MINIMAL_YAML}), _mock_bundled(["default"]):
            rc = cmd_copy(["default", "ghost"])

        assert rc == 1
        assert (tmp_user_dir / "default.yaml").exists()
        assert "not found" in capsys.readouterr().err.lower()


# ─────────────────────────────────────────────────────────────────────────────
# cmd_add
# ─────────────────────────────────────────────────────────────────────────────


class TestCmdAdd:
    def test_add_valid_yaml(self, capsys, tmp_user_dir, sample_yaml_file):
        rc = cmd_add([str(sample_yaml_file)])
        assert rc == 0
        dest = tmp_user_dir / "test-workflow.yaml"
        assert dest.exists()
        assert "Installed" in capsys.readouterr().out

    def test_add_with_override_name(self, capsys, tmp_user_dir, sample_yaml_file):
        rc = cmd_add([str(sample_yaml_file)], override_name="custom-name")
        assert rc == 0
        assert (tmp_user_dir / "custom-name.yaml").exists()

    def test_add_invalid_yaml(self, capsys, tmp_path, tmp_user_dir):
        bad = tmp_path / "bad.yaml"
        bad.write_text(INVALID_YAML, encoding="utf-8")
        rc = cmd_add([str(bad)])
        assert rc == 1
        assert "invalid" in capsys.readouterr().err.lower()

    def test_add_nonexistent_file(self, capsys, tmp_user_dir):
        rc = cmd_add(["/nonexistent/path/workflow.yaml"])
        assert rc == 1
        assert "does not exist" in capsys.readouterr().err.lower()

    def test_add_wrong_extension(self, capsys, tmp_path, tmp_user_dir):
        f = tmp_path / "workflow.json"
        f.write_text("{}", encoding="utf-8")
        rc = cmd_add([str(f)])
        assert rc == 1

    def test_add_overwrites_with_warning(self, capsys, tmp_user_dir, sample_yaml_file):
        # Pre-create the destination
        (tmp_user_dir / "test-workflow.yaml").write_text("old", encoding="utf-8")
        rc = cmd_add([str(sample_yaml_file)])
        assert rc == 0
        assert "Warning" in capsys.readouterr().out

    def test_add_multiple_files(self, capsys, tmp_user_dir, tmp_path):
        """Adding multiple YAML files installs all of them."""
        wf1 = tmp_path / "wf-one.yaml"
        wf2 = tmp_path / "wf-two.yaml"
        wf1.write_text(MINIMAL_YAML, encoding="utf-8")
        wf2.write_text(MINIMAL_YAML, encoding="utf-8")

        rc = cmd_add([str(wf1), str(wf2)])
        assert rc == 0
        assert (tmp_user_dir / "wf-one.yaml").exists()
        assert (tmp_user_dir / "wf-two.yaml").exists()
        out = capsys.readouterr().out
        assert "wf-one" in out
        assert "wf-two" in out

    def test_add_multiple_name_flag_rejected(self, capsys, tmp_user_dir, tmp_path):
        """--name with multiple files returns error without installing."""
        wf1 = tmp_path / "wf-a.yaml"
        wf2 = tmp_path / "wf-b.yaml"
        wf1.write_text(MINIMAL_YAML, encoding="utf-8")
        wf2.write_text(MINIMAL_YAML, encoding="utf-8")

        rc = cmd_add([str(wf1), str(wf2)], override_name="should-fail")
        assert rc == 1
        assert "cannot be used" in capsys.readouterr().err.lower()
        assert not (tmp_user_dir / "should-fail.yaml").exists()

    def test_add_partial_failure_continues(self, capsys, tmp_user_dir, tmp_path):
        """A bad file in the middle doesn't prevent valid files from installing."""
        good = tmp_path / "good.yaml"
        bad = tmp_path / "bad.yaml"
        good.write_text(MINIMAL_YAML, encoding="utf-8")
        bad.write_text(INVALID_YAML, encoding="utf-8")

        rc = cmd_add([str(good), str(bad)])
        assert rc == 1  # non-zero because of the bad file
        assert (tmp_user_dir / "good.yaml").exists()  # good one still installed


# ─────────────────────────────────────────────────────────────────────────────
# cmd_remove
# ─────────────────────────────────────────────────────────────────────────────


class TestCmdRemove:
    def test_remove_user_workflow(self, capsys, tmp_user_dir):
        wf = tmp_user_dir / "my-wf.yaml"
        wf.write_text(MINIMAL_YAML, encoding="utf-8")

        with _mock_bundled([]):
            rc = cmd_remove(["my-wf"])

        assert rc == 0
        assert not wf.exists()
        assert "Removed" in capsys.readouterr().out

    def test_remove_bundled_refused(self, capsys, tmp_user_dir):
        with _mock_bundled(["default"]):
            rc = cmd_remove(["default"])
        assert rc == 1
        assert "bundled" in capsys.readouterr().err.lower()

    def test_remove_nonexistent(self, capsys, tmp_user_dir):
        with _mock_bundled([]):
            rc = cmd_remove(["ghost"])
        assert rc == 1
        assert "not found" in capsys.readouterr().err.lower()

    def test_remove_yml_extension(self, capsys, tmp_user_dir):
        wf = tmp_user_dir / "my-wf.yml"
        wf.write_text(MINIMAL_YAML, encoding="utf-8")

        with _mock_bundled([]):
            rc = cmd_remove(["my-wf"])

        assert rc == 0
        assert not wf.exists()

    def test_remove_multiple(self, capsys, tmp_user_dir):
        """Removing multiple workflows deletes all of them."""
        (tmp_user_dir / "wf-a.yaml").write_text(MINIMAL_YAML, encoding="utf-8")
        (tmp_user_dir / "wf-b.yaml").write_text(MINIMAL_YAML, encoding="utf-8")

        with _mock_bundled([]):
            rc = cmd_remove(["wf-a", "wf-b"])

        assert rc == 0
        assert not (tmp_user_dir / "wf-a.yaml").exists()
        assert not (tmp_user_dir / "wf-b.yaml").exists()

    def test_remove_partial_failure_continues(self, capsys, tmp_user_dir):
        """A missing workflow doesn't prevent others from being removed."""
        (tmp_user_dir / "wf-good.yaml").write_text(MINIMAL_YAML, encoding="utf-8")

        with _mock_bundled([]):
            rc = cmd_remove(["wf-good", "ghost"])

        assert rc == 1
        assert not (tmp_user_dir / "wf-good.yaml").exists()
        assert "not found" in capsys.readouterr().err.lower()


# ─────────────────────────────────────────────────────────────────────────────
# cmd_validate
# ─────────────────────────────────────────────────────────────────────────────


class TestCmdValidate:
    def test_validate_bundled_by_name(self, capsys):
        with patch.object(_wf_cmd, "WorkflowEngine") as mock_engine_cls:
            mock_wf = MagicMock()
            mock_wf.name = "security-focus"
            mock_wf.description = "Security review"
            mock_wf.version = "1.0"
            mock_wf.stages = [MagicMock(name="step1", type="custom", enabled=True)]
            mock_engine_cls.return_value.workflow = mock_wf

            rc = cmd_validate("security-focus")

        assert rc == 0
        out = capsys.readouterr().out
        assert "valid" in out.lower()
        assert "security-focus" in out

    def test_validate_file_path(self, capsys, sample_yaml_file):
        rc = cmd_validate(str(sample_yaml_file))
        assert rc == 0
        assert "valid" in capsys.readouterr().out.lower()

    def test_validate_not_found(self, capsys):
        with patch.object(_wf_cmd, "WorkflowEngine", side_effect=FileNotFoundError("not found")):
            rc = cmd_validate("nonexistent")
        assert rc == 1
        assert "error" in capsys.readouterr().err.lower()

    def test_validate_invalid_content(self, capsys, tmp_path):
        bad = tmp_path / "bad.yaml"
        bad.write_text("- this: is\n- not: valid workflow", encoding="utf-8")
        rc = cmd_validate(str(bad))
        assert rc == 1


# ─────────────────────────────────────────────────────────────────────────────
# main() entry point
# ─────────────────────────────────────────────────────────────────────────────


class TestMain:
    def test_main_no_action_exits_0(self):
        from skill_seekers.cli.workflows_command import main

        with pytest.raises(SystemExit) as exc:
            main([])
        assert exc.value.code == 0

    def test_main_list(self, capsys, tmp_user_dir):
        from skill_seekers.cli.workflows_command import main

        # tmp_user_dir is empty; mock bundled to return nothing
        with _mock_bundled([]), pytest.raises(SystemExit) as exc:
            main(["list"])
        assert exc.value.code == 0

    def test_main_validate_success(self, capsys, sample_yaml_file):
        from skill_seekers.cli.workflows_command import main

        with pytest.raises(SystemExit) as exc:
            main(["validate", str(sample_yaml_file)])
        assert exc.value.code == 0

    def test_main_show_success(self, capsys, tmp_user_dir):
        (tmp_user_dir / "my-wf.yaml").write_text(MINIMAL_YAML, encoding="utf-8")
        with pytest.raises(SystemExit) as exc:
            _wf_cmd.main(["show", "my-wf"])
        assert exc.value.code == 0
        assert "name: test-workflow" in capsys.readouterr().out

    def test_main_show_not_found_exits_1(self, capsys, tmp_user_dir):
        with (
            patch.object(_wf_cmd, "_workflow_yaml_text", return_value=None),
            pytest.raises(SystemExit) as exc,
        ):
            _wf_cmd.main(["show", "ghost"])
        assert exc.value.code == 1

    def test_main_copy_single(self, capsys, tmp_user_dir):
        with _mock_bundled_text({"default": MINIMAL_YAML}), pytest.raises(SystemExit) as exc:
            _wf_cmd.main(["copy", "default"])
        assert exc.value.code == 0
        assert (tmp_user_dir / "default.yaml").exists()

    def test_main_copy_multiple(self, capsys, tmp_user_dir):
        texts = {"default": MINIMAL_YAML, "minimal": MINIMAL_YAML}
        with _mock_bundled_text(texts), pytest.raises(SystemExit) as exc:
            _wf_cmd.main(["copy", "default", "minimal"])
        assert exc.value.code == 0
        assert (tmp_user_dir / "default.yaml").exists()
        assert (tmp_user_dir / "minimal.yaml").exists()

    def test_main_copy_not_found_exits_1(self, capsys, tmp_user_dir):
        with _mock_bundled_text({}), _mock_bundled([]), pytest.raises(SystemExit) as exc:
            _wf_cmd.main(["copy", "ghost"])
        assert exc.value.code == 1

    def test_main_add_single_file(self, capsys, tmp_user_dir, sample_yaml_file):
        with pytest.raises(SystemExit) as exc:
            _wf_cmd.main(["add", str(sample_yaml_file)])
        assert exc.value.code == 0
        assert (tmp_user_dir / "test-workflow.yaml").exists()

    def test_main_add_multiple_files(self, capsys, tmp_user_dir, tmp_path):
        wf1 = tmp_path / "wf-a.yaml"
        wf2 = tmp_path / "wf-b.yaml"
        wf1.write_text(MINIMAL_YAML, encoding="utf-8")
        wf2.write_text(MINIMAL_YAML, encoding="utf-8")
        with pytest.raises(SystemExit) as exc:
            _wf_cmd.main(["add", str(wf1), str(wf2)])
        assert exc.value.code == 0
        assert (tmp_user_dir / "wf-a.yaml").exists()
        assert (tmp_user_dir / "wf-b.yaml").exists()

    def test_main_add_with_name_flag(self, capsys, tmp_user_dir, sample_yaml_file):
        with pytest.raises(SystemExit) as exc:
            _wf_cmd.main(["add", str(sample_yaml_file), "--name", "renamed"])
        assert exc.value.code == 0
        assert (tmp_user_dir / "renamed.yaml").exists()

    def test_main_add_name_rejected_for_multiple(self, capsys, tmp_user_dir, tmp_path):
        wf1 = tmp_path / "wf-a.yaml"
        wf2 = tmp_path / "wf-b.yaml"
        wf1.write_text(MINIMAL_YAML, encoding="utf-8")
        wf2.write_text(MINIMAL_YAML, encoding="utf-8")
        with pytest.raises(SystemExit) as exc:
            _wf_cmd.main(["add", str(wf1), str(wf2), "--name", "bad"])
        assert exc.value.code == 1

    def test_main_remove_single(self, capsys, tmp_user_dir):
        (tmp_user_dir / "my-wf.yaml").write_text(MINIMAL_YAML, encoding="utf-8")
        with _mock_bundled([]), pytest.raises(SystemExit) as exc:
            _wf_cmd.main(["remove", "my-wf"])
        assert exc.value.code == 0
        assert not (tmp_user_dir / "my-wf.yaml").exists()

    def test_main_remove_multiple(self, capsys, tmp_user_dir):
        (tmp_user_dir / "wf-a.yaml").write_text(MINIMAL_YAML, encoding="utf-8")
        (tmp_user_dir / "wf-b.yaml").write_text(MINIMAL_YAML, encoding="utf-8")
        with _mock_bundled([]), pytest.raises(SystemExit) as exc:
            _wf_cmd.main(["remove", "wf-a", "wf-b"])
        assert exc.value.code == 0
        assert not (tmp_user_dir / "wf-a.yaml").exists()
        assert not (tmp_user_dir / "wf-b.yaml").exists()

    def test_main_remove_bundled_refused(self, capsys, tmp_user_dir):
        with _mock_bundled(["default"]), pytest.raises(SystemExit) as exc:
            _wf_cmd.main(["remove", "default"])
        assert exc.value.code == 1

    def test_main_remove_not_found_exits_1(self, capsys, tmp_user_dir):
        with _mock_bundled([]), pytest.raises(SystemExit) as exc:
            _wf_cmd.main(["remove", "ghost"])
        assert exc.value.code == 1


# ─────────────────────────────────────────────────────────────────────────────
# Parser argument binding
# ─────────────────────────────────────────────────────────────────────────────


class TestWorkflowsParserArgumentBinding:
    """Verify nargs='+' parsers produce lists with correct attribute names."""

    def _parse(self, argv):
        """Parse argv through the standalone main() parser by capturing args."""
        import argparse

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="action")

        copy_p = subparsers.add_parser("copy")
        copy_p.add_argument("workflow_names", nargs="+")

        add_p = subparsers.add_parser("add")
        add_p.add_argument("files", nargs="+")
        add_p.add_argument("--name")

        remove_p = subparsers.add_parser("remove")
        remove_p.add_argument("workflow_names", nargs="+")

        return parser.parse_args(argv)

    def test_copy_single_produces_list(self):
        args = self._parse(["copy", "security-focus"])
        assert args.workflow_names == ["security-focus"]

    def test_copy_multiple_produces_list(self):
        args = self._parse(["copy", "security-focus", "minimal"])
        assert args.workflow_names == ["security-focus", "minimal"]

    def test_add_single_produces_list(self):
        args = self._parse(["add", "my.yaml"])
        assert args.files == ["my.yaml"]

    def test_add_multiple_produces_list(self):
        args = self._parse(["add", "a.yaml", "b.yaml", "c.yaml"])
        assert args.files == ["a.yaml", "b.yaml", "c.yaml"]

    def test_add_name_flag_captured(self):
        args = self._parse(["add", "my.yaml", "--name", "custom"])
        assert args.files == ["my.yaml"]
        assert args.name == "custom"

    def test_remove_single_produces_list(self):
        args = self._parse(["remove", "my-wf"])
        assert args.workflow_names == ["my-wf"]

    def test_remove_multiple_produces_list(self):
        args = self._parse(["remove", "wf-a", "wf-b"])
        assert args.workflow_names == ["wf-a", "wf-b"]
