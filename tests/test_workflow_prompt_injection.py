"""Tests for prompt injection check workflow (#324).

Validates that:
- prompt-injection-check.yaml is a valid bundled workflow
- default.yaml includes injection_scan as its first stage
- security-focus.yaml includes injection_scan as its first stage
- The workflow YAML is structurally correct
"""

from __future__ import annotations

import yaml


def _load_bundled_yaml(name: str) -> dict:
    """Load a bundled workflow YAML by name."""
    from importlib.resources import files as importlib_files

    for suffix in (".yaml", ".yml"):
        try:
            ref = importlib_files("skill_seekers.workflows").joinpath(name + suffix)
            return yaml.safe_load(ref.read_text(encoding="utf-8"))
        except (FileNotFoundError, TypeError, ModuleNotFoundError):
            continue
    raise FileNotFoundError(f"Bundled workflow '{name}' not found")


class TestPromptInjectionCheckWorkflow:
    """Validate the standalone prompt-injection-check workflow."""

    def test_workflow_loads(self):
        data = _load_bundled_yaml("prompt-injection-check")
        assert data["name"] == "prompt-injection-check"

    def test_has_stages(self):
        data = _load_bundled_yaml("prompt-injection-check")
        assert "stages" in data
        assert len(data["stages"]) >= 1

    def test_injection_scan_stage_present(self):
        data = _load_bundled_yaml("prompt-injection-check")
        stage_names = [s["name"] for s in data["stages"]]
        assert "injection_scan" in stage_names

    def test_injection_scan_has_prompt(self):
        data = _load_bundled_yaml("prompt-injection-check")
        scan_stage = next(s for s in data["stages"] if s["name"] == "injection_scan")
        assert scan_stage.get("prompt")
        assert "prompt injection" in scan_stage["prompt"].lower()

    def test_injection_scan_targets_all(self):
        data = _load_bundled_yaml("prompt-injection-check")
        scan_stage = next(s for s in data["stages"] if s["name"] == "injection_scan")
        assert scan_stage["target"] == "all"

    def test_applies_to_all_source_types(self):
        data = _load_bundled_yaml("prompt-injection-check")
        applies = data.get("applies_to", [])
        assert "doc_scraping" in applies
        assert "github_analysis" in applies
        assert "codebase_analysis" in applies

    def test_post_process_metadata(self):
        data = _load_bundled_yaml("prompt-injection-check")
        meta = data.get("post_process", {}).get("add_metadata", {})
        assert meta.get("security_scanned") is True


class TestDefaultWorkflowHasInjectionScan:
    """Validate that default.yaml runs injection_scan first."""

    def test_injection_scan_is_first_stage(self):
        data = _load_bundled_yaml("default")
        assert data["stages"][0]["name"] == "injection_scan"

    def test_injection_scan_has_prompt(self):
        data = _load_bundled_yaml("default")
        scan_stage = data["stages"][0]
        assert scan_stage.get("prompt")
        assert "injection" in scan_stage["prompt"].lower()


class TestSecurityFocusHasInjectionScan:
    """Validate that security-focus.yaml runs injection_scan first."""

    def test_injection_scan_is_first_stage(self):
        data = _load_bundled_yaml("security-focus")
        assert data["stages"][0]["name"] == "injection_scan"

    def test_injection_scan_has_prompt(self):
        data = _load_bundled_yaml("security-focus")
        scan_stage = data["stages"][0]
        assert scan_stage.get("prompt")
        assert "injection" in scan_stage["prompt"].lower()
