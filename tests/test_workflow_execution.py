"""Exercise real workflow engines with offline model replies and actual skill files."""

import argparse
import json
from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml

from skill_seekers.cli.enhancement_workflow import (
    EnhancementWorkflow,
    WorkflowEngine,
    WorkflowStage,
    format_workflow_prompt,
)
from skill_seekers.cli.execution_context import ExecutionContext
from skill_seekers.cli.workflow_documents import load_workflow_documents
from skill_seekers.cli.workflow_runner import run_workflows

DEFAULT = Path(__file__).parents[1] / "src/skill_seekers/workflows/default.yaml"


@pytest.fixture(autouse=True)
def isolated_context():
    ExecutionContext.reset()
    yield
    ExecutionContext.reset()


@pytest.fixture
def skill(tmp_path):
    root = tmp_path / "skill"
    root.mkdir()
    (root / "references").mkdir()
    (root / "SKILL.md").write_text(
        "---\nname: example\ndescription: Original identity\n---\n\n# Original\nExisting knowledge."
    )
    (root / "references/guide.md").write_text("# Guide\nSOURCE_FACT: Set timeout to 30 seconds.")
    return root


def args(*workflows, inline=None, dry=False, var=None):
    return argparse.Namespace(
        enhance_workflow=list(workflows), enhance_stage=inline, workflow_dry_run=dry, var=var
    )


def install_model(monkeypatch, replies):
    model = Mock()
    model.call.side_effect = replies
    monkeypatch.setattr("skill_seekers.cli.ai_enhancer.AIEnhancer", lambda **_: model)
    return model


def write_workflow(tmp_path, stages, **extra):
    path = tmp_path / "custom.yaml"
    path.write_text(yaml.safe_dump({"name": "custom", "stages": stages, **extra}))
    return str(path)


@pytest.mark.parametrize(
    "template,expected",
    [
        ('JSON {"findings": []}; {name}', 'JSON {"findings": []}; Example'),
        ("{unknown}; {name}", "{unknown}; Example"),
        ("{{name}} and {name}", "{name} and Example"),
        ("{previous_results[summary]}", "Earlier finding"),
        ("{number:04d}; {name!r}", "0007; 'Example'"),
        ('{{"name": "{name}"}}', '{"name": "Example"}'),
        ("{missing[key]} {number:bad}", "{missing[key]} {number:bad}"),
        ("unclosed { and {name}", "unclosed { and Example"),
        ("{value}", "{name}"),
    ],
)
def test_prompt_substitution_preserves_json_and_format_syntax(template, expected):
    context = {
        "name": "Example",
        "number": 7,
        "previous_results": {"summary": "Earlier finding"},
        "value": "{name}",
    }
    assert format_workflow_prompt(template, context) == expected


def test_default_workflow_reads_sources_and_saves_replacement(skill, monkeypatch):
    original = (skill / "SKILL.md").read_text()
    model = install_model(
        monkeypatch,
        [
            '{"findings": [], "risk_level": "none"}',
            '{"architecture_style": "documented workflow"}',
            json.dumps(
                {"skill_md": "---\nname: changed\n---\n# Improved\nUse a 30-second timeout."}
            ),
        ],
    )
    assert run_workflows(
        args(str(DEFAULT)), context={"skill_dir": str(skill)}, use_context_fallback=False
    ) == (True, [str(DEFAULT)])
    assert model.call.call_count == 3
    for call in model.call.call_args_list:
        assert "SOURCE_FACT" in call.args[0]
        assert "Existing knowledge" in call.args[0]
    assert "documented workflow" in model.call.call_args.args[0]
    assert model.call.call_args.kwargs["max_tokens"] == 16384
    output = (skill / "SKILL.md").read_text()
    assert "# Improved" in output
    assert "name: example" in output
    assert "name: changed" not in output
    assert (skill / "SKILL.md.backup").read_text() == original
    report = json.loads((skill / "workflow_results.json").read_text())
    assert report[0]["results"]["architecture"]["architecture_style"] == "documented workflow"
    assert not (skill / "EVAL.md").exists()
    assert not (skill / "SHRINK_LOG.md").exists()


def test_chained_workflows_read_updated_skill(skill, monkeypatch, tmp_path):
    path = write_workflow(
        tmp_path,
        [
            {
                "name": "rewrite",
                "type": "custom",
                "target": "skill_md",
                "prompt": "Improve supplied document",
            }
        ],
    )
    model = install_model(
        monkeypatch,
        [
            json.dumps({"skill_md": "# First revision\nUseful detail."}),
            json.dumps({"skill_md": "# Second revision\nMore useful detail."}),
        ],
    )
    assert run_workflows(
        args(path, path), context={"skill_dir": str(skill)}, use_context_fallback=False
    )[0]
    assert "First revision" in model.call.call_args_list[1].args[0]
    assert "Second revision" in (skill / "SKILL.md").read_text()
    assert len(json.loads((skill / "workflow_results.json").read_text())) == 2


def test_inline_workflows_execute_and_preserve_analysis(skill, monkeypatch):
    original = (skill / "SKILL.md").read_text()
    model = install_model(
        monkeypatch, ['{"summary":"Earlier finding"}', '{"advice":"Keep examples"}']
    )
    assert run_workflows(
        args(inline=["inspect:Summarize", "review:Check {previous_results[summary]}"]),
        context={"skill_dir": str(skill)},
        use_context_fallback=False,
    ) == (True, ["inline_workflow"])
    assert "Check Earlier finding" in model.call.call_args_list[1].args[0]
    assert (skill / "SKILL.md").read_text() == original
    assert (
        json.loads((skill / "workflow_results.json").read_text())[0]["results"]["advice"]
        == "Keep examples"
    )


@pytest.mark.parametrize(
    "response",
    [None, "", "not json", "[]", '{"skill_md":""}', '{"skill_md":"Done"}', '{"skill_md":'],
)
def test_failed_or_invalid_replacement_preserves_skill(skill, monkeypatch, tmp_path, response):
    original = (skill / "SKILL.md").read_bytes()
    path = write_workflow(
        tmp_path, [{"name": "rewrite", "target": "skill_md", "prompt": "Improve"}]
    )
    install_model(monkeypatch, [response])
    assert run_workflows(
        args(path), context={"skill_dir": str(skill)}, use_context_fallback=False
    ) == (False, [])
    assert (skill / "SKILL.md").read_bytes() == original
    assert not (skill / "SKILL.md.backup").exists()
    assert not (skill / "workflow_results.json").exists()


@pytest.mark.parametrize("inline", [False, True])
def test_real_dry_run_has_no_model_calls_or_writes(skill, monkeypatch, inline):
    model = install_model(monkeypatch, [])
    before = {str(p): p.read_bytes() for p in skill.rglob("*") if p.is_file()}
    request = (
        args(inline=["inspect:Inspect source"], dry=True)
        if inline
        else args(str(DEFAULT), dry=True)
    )
    with pytest.raises(SystemExit) as exited:
        run_workflows(request, context={"skill_dir": str(skill)}, use_context_fallback=False)
    assert exited.value.code == 0
    model.call.assert_not_called()
    assert {str(p): p.read_bytes() for p in skill.rglob("*") if p.is_file()} == before


def test_missing_workflow_preview_is_failure(tmp_path):
    with pytest.raises(SystemExit) as exited:
        run_workflows(args(str(tmp_path / "missing.yaml"), dry=True), use_context_fallback=False)
    assert exited.value.code == 1


def test_context_is_bounded_and_excludes_external_symlinks(skill, tmp_path, monkeypatch):
    monkeypatch.setattr("skill_seekers.cli.workflow_documents.MAX_DOCUMENT_CHARS", 32)
    monkeypatch.setattr("skill_seekers.cli.workflow_documents.MAX_CONTEXT_CHARS", 50)
    outside = tmp_path / "outside.md"
    outside.write_text("PRIVATE_OUTSIDE_DOCUMENT")
    (skill / "references/external.md").symlink_to(outside)
    context = load_workflow_documents(skill)
    assert sum(len(doc["content"]) for doc in context["documents"]) <= 50
    assert context["documents_truncated"]
    assert context["skill_truncated"]
    assert "PRIVATE_OUTSIDE_DOCUMENT" not in json.dumps(context)


def test_truncated_skill_cannot_be_overwritten(skill, tmp_path, monkeypatch):
    monkeypatch.setattr("skill_seekers.cli.workflow_documents.MAX_DOCUMENT_CHARS", 32)
    original = (skill / "SKILL.md").read_bytes()
    path = write_workflow(
        tmp_path, [{"name": "rewrite", "target": "skill_md", "prompt": "Improve"}]
    )
    install_model(monkeypatch, [json.dumps({"skill_md": "# Replacement\nIncomplete rewrite"})])
    assert not run_workflows(
        args(path), context={"skill_dir": str(skill)}, use_context_fallback=False
    )[0]
    assert (skill / "SKILL.md").read_bytes() == original


def test_workflow_variables_are_defaults_not_overrides(monkeypatch):
    model = install_model(monkeypatch, ["{}"])
    workflow = EnhancementWorkflow(
        name="variables",
        description="",
        variables={"name": "default"},
        stages=[WorkflowStage("inspect", "custom", "all", prompt="Name {name}")],
    )
    context = {"name": "explicit"}
    WorkflowEngine(workflow).run({}, context)
    assert "Name explicit" in model.call.call_args.args[0]
    assert context == {"name": "explicit"}


def test_template_variables_cannot_redirect_output(skill, tmp_path, monkeypatch):
    other = tmp_path / "other"
    other.mkdir()
    install_model(monkeypatch, ['{"note":"analysis"}'])
    run_workflows(
        args(inline=["analyze:Inspect"], var=[f"skill_dir={other}"]),
        context={"skill_dir": str(skill)},
        use_context_fallback=False,
    )
    assert (skill / "workflow_results.json").exists()
    assert not (other / "workflow_results.json").exists()


def test_failed_stage_does_not_report_success_or_save_partial_results(skill, tmp_path, monkeypatch):
    path = write_workflow(
        tmp_path,
        [
            {"name": "failed", "prompt": "Inspect"},
            {"name": "succeeded", "prompt": "Inspect again"},
        ],
    )
    install_model(monkeypatch, [None, '{"summary":"Partial result"}'])
    assert run_workflows(
        args(path), context={"skill_dir": str(skill)}, use_context_fallback=False
    ) == (False, [])
    assert not (skill / "workflow_results.json").exists()


def test_structured_skill_advice_is_saved_without_replacing_skill(skill, tmp_path, monkeypatch):
    original = (skill / "SKILL.md").read_text()
    path = write_workflow(
        tmp_path, [{"name": "advice", "target": "skill_md", "prompt": "Suggest improvements"}]
    )
    install_model(monkeypatch, ['{"improved_overview":"Suggested overview"}'])
    assert run_workflows(args(path), context={"skill_dir": str(skill)}, use_context_fallback=False)[
        0
    ]
    assert (skill / "SKILL.md").read_text() == original
    assert "Suggested overview" in (skill / "workflow_results.json").read_text()


def test_atomic_save_failure_leaves_original_in_place(skill, tmp_path, monkeypatch):
    original = (skill / "SKILL.md").read_bytes()
    path = write_workflow(
        tmp_path, [{"name": "rewrite", "target": "skill_md", "prompt": "Improve"}]
    )
    install_model(monkeypatch, ['{"skill_md":"# Replacement"}'])
    monkeypatch.setattr(
        "skill_seekers.cli.adaptors.base.os.replace", Mock(side_effect=OSError("disk error"))
    )
    assert not run_workflows(
        args(path), context={"skill_dir": str(skill)}, use_context_fallback=False
    )[0]
    assert (skill / "SKILL.md").read_bytes() == original
    assert not (skill / "SKILL.md.tmp").exists()
    assert not (skill / "workflow_results.json.tmp").exists()


@pytest.mark.parametrize("dry", [False, True])
def test_create_workflow_uses_output_directory_and_previews_before_scraping(
    skill, monkeypatch, dry
):
    from skill_seekers.cli.create_command import CreateCommand

    request = argparse.Namespace(
        source="https://docs.example.com",
        config=None,
        name="example",
        output=str(skill),
        description=None,
        dry_run=False,
        skip_scrape=False,
        enhance_workflow=[str(DEFAULT)],
        enhance_stage=None,
        var=None,
        workflow_dry_run=dry,
    )
    command = CreateCommand(request)
    scrape = Mock(return_value=0)
    enhance = Mock()
    monkeypatch.setattr(command, "_route_to_scraper", scrape)
    monkeypatch.setattr(command, "_run_enhancement", enhance)
    model = install_model(monkeypatch, ["{}", "{}", '{"skill_md":"# Created through workflow"}'])
    if dry:
        with pytest.raises(SystemExit) as exited:
            command.execute()
        assert exited.value.code == 0
        scrape.assert_not_called()
        enhance.assert_not_called()
        model.call.assert_not_called()
        assert not (skill / "workflow_results.json").exists()
    else:
        assert command.execute() == 0
        assert "SOURCE_FACT" in model.call.call_args.args[0]
        assert "# Created through workflow" in (skill / "SKILL.md").read_text()
