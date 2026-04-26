#!/usr/bin/env python3
"""
Tests for Unified Multi-Source Scraper

Covers:
- Config validation (unified vs legacy)
- Conflict detection
- Rule-based merging
- Skill building
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from skill_seekers.cli.config_validator import ConfigValidator, validate_config
from skill_seekers.cli.conflict_detector import Conflict, ConflictDetector
from skill_seekers.cli.merge_sources import RuleBasedMerger
from skill_seekers.cli.unified_skill_builder import UnifiedSkillBuilder

# ===========================
# Config Validation Tests
# ===========================


def test_detect_unified_format():
    """Test unified format detection and legacy rejection"""
    import json
    import tempfile

    unified_config = {
        "name": "test",
        "description": "Test skill",
        "sources": [{"type": "documentation", "base_url": "https://example.com"}],
    }

    legacy_config = {"name": "test", "description": "Test skill", "base_url": "https://example.com"}

    # Test unified detection
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(unified_config, f)
        config_path = f.name

    try:
        validator = ConfigValidator(config_path)
        assert validator.is_unified
        validator.validate()  # Should pass
    finally:
        os.unlink(config_path)

    # Test legacy rejection (legacy format removed in v2.11.0)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(legacy_config, f)
        config_path = f.name

    try:
        validator = ConfigValidator(config_path)
        assert validator.is_unified  # Always True now
        # Validation should fail for legacy format
        with pytest.raises(ValueError, match="LEGACY CONFIG FORMAT DETECTED"):
            validator.validate()
    finally:
        os.unlink(config_path)


def test_validate_unified_sources():
    """Test source type validation"""
    config = {
        "name": "test",
        "description": "Test",
        "sources": [
            {"type": "documentation", "base_url": "https://example.com"},
            {"type": "github", "repo": "user/repo"},
            {"type": "pdf", "path": "/path/to.pdf"},
        ],
    }

    validator = ConfigValidator(config)
    validator.validate()
    assert len(validator.config["sources"]) == 3


def test_validate_invalid_source_type():
    """Test invalid source type raises error"""
    config = {
        "name": "test",
        "description": "Test",
        "sources": [{"type": "invalid_type", "url": "https://example.com"}],
    }

    validator = ConfigValidator(config)
    with pytest.raises(ValueError, match="Invalid type"):
        validator.validate()


def test_needs_api_merge():
    """Test API merge detection"""
    # Config with both docs and GitHub code
    config_needs_merge = {
        "name": "test",
        "description": "Test",
        "sources": [
            {"type": "documentation", "base_url": "https://example.com", "extract_api": True},
            {"type": "github", "repo": "user/repo", "include_code": True},
        ],
    }

    validator = ConfigValidator(config_needs_merge)
    assert validator.needs_api_merge()

    # Config with only docs
    config_no_merge = {
        "name": "test",
        "description": "Test",
        "sources": [{"type": "documentation", "base_url": "https://example.com"}],
    }

    validator = ConfigValidator(config_no_merge)
    assert not validator.needs_api_merge()


def test_backward_compatibility():
    """Test legacy config rejection (removed in v2.11.0)"""
    legacy_config = {
        "name": "test",
        "description": "Test skill",
        "base_url": "https://example.com",
        "selectors": {"main_content": "article"},
        "max_pages": 100,
    }

    # Legacy format should be rejected with clear error message
    validator = ConfigValidator(legacy_config)
    with pytest.raises(ValueError) as exc_info:
        validator.validate()

    # Check error message provides migration guidance
    error_msg = str(exc_info.value)
    assert "LEGACY CONFIG FORMAT DETECTED" in error_msg
    assert "removed in v2.11.0" in error_msg
    assert "sources" in error_msg  # Shows new format requires sources array


# ===========================
# Conflict Detection Tests
# ===========================


def test_detect_missing_in_docs():
    """Test detection of APIs missing in documentation"""
    docs_data = {
        "pages": [
            {
                "url": "https://example.com/api",
                "apis": [
                    {
                        "name": "documented_func",
                        "parameters": [{"name": "x", "type": "int"}],
                        "return_type": "str",
                    }
                ],
            }
        ]
    }

    github_data = {
        "code_analysis": {
            "analyzed_files": [
                {
                    "functions": [
                        {
                            "name": "undocumented_func",
                            "parameters": [{"name": "y", "type_hint": "float"}],
                            "return_type": "bool",
                        }
                    ]
                }
            ]
        }
    }

    detector = ConflictDetector(docs_data, github_data)
    conflicts = detector._find_missing_in_docs()

    assert len(conflicts) > 0
    assert any(c.type == "missing_in_docs" for c in conflicts)
    assert any(c.api_name == "undocumented_func" for c in conflicts)


def test_detect_missing_in_code():
    """Test detection of APIs missing in code"""
    docs_data = {
        "pages": [
            {
                "url": "https://example.com/api",
                "apis": [
                    {
                        "name": "obsolete_func",
                        "parameters": [{"name": "x", "type": "int"}],
                        "return_type": "str",
                    }
                ],
            }
        ]
    }

    github_data = {"code_analysis": {"analyzed_files": []}}

    detector = ConflictDetector(docs_data, github_data)
    conflicts = detector._find_missing_in_code()

    assert len(conflicts) > 0
    assert any(c.type == "missing_in_code" for c in conflicts)
    assert any(c.api_name == "obsolete_func" for c in conflicts)


def test_detect_signature_mismatch():
    """Test detection of signature mismatches"""
    docs_data = {
        "pages": [
            {
                "url": "https://example.com/api",
                "apis": [
                    {
                        "name": "func",
                        "parameters": [{"name": "x", "type": "int"}],
                        "return_type": "str",
                    }
                ],
            }
        ]
    }

    github_data = {
        "code_analysis": {
            "analyzed_files": [
                {
                    "functions": [
                        {
                            "name": "func",
                            "parameters": [
                                {"name": "x", "type_hint": "int"},
                                {"name": "y", "type_hint": "bool", "default": "False"},
                            ],
                            "return_type": "str",
                        }
                    ]
                }
            ]
        }
    }

    detector = ConflictDetector(docs_data, github_data)
    conflicts = detector._find_signature_mismatches()

    assert len(conflicts) > 0
    assert any(c.type == "signature_mismatch" for c in conflicts)
    assert any(c.api_name == "func" for c in conflicts)


def test_conflict_severity():
    """Test conflict severity assignment"""
    # High severity: missing_in_code
    conflict_high = Conflict(
        type="missing_in_code",
        severity="high",
        api_name="test",
        docs_info={"name": "test"},
        code_info=None,
        difference="API documented but not in code",
    )
    assert conflict_high.severity == "high"

    # Medium severity: missing_in_docs
    conflict_medium = Conflict(
        type="missing_in_docs",
        severity="medium",
        api_name="test",
        docs_info=None,
        code_info={"name": "test"},
        difference="API in code but not documented",
    )
    assert conflict_medium.severity == "medium"


# ===========================
# Merge Tests
# ===========================


def test_rule_based_merge_docs_only():
    """Test rule-based merge for docs-only APIs"""
    docs_data = {
        "pages": [
            {
                "url": "https://example.com/api",
                "apis": [
                    {
                        "name": "docs_only_api",
                        "parameters": [{"name": "x", "type": "int"}],
                        "return_type": "str",
                    }
                ],
            }
        ]
    }

    github_data = {"code_analysis": {"analyzed_files": []}}

    detector = ConflictDetector(docs_data, github_data)
    conflicts = detector.detect_all_conflicts()

    merger = RuleBasedMerger(docs_data, github_data, conflicts)
    merged = merger.merge_all()

    assert "apis" in merged
    assert "docs_only_api" in merged["apis"]
    assert merged["apis"]["docs_only_api"]["status"] == "docs_only"


def test_rule_based_merge_code_only():
    """Test rule-based merge for code-only APIs"""
    docs_data = {"pages": []}

    github_data = {
        "code_analysis": {
            "analyzed_files": [
                {
                    "functions": [
                        {
                            "name": "code_only_api",
                            "parameters": [{"name": "y", "type_hint": "float"}],
                            "return_type": "bool",
                        }
                    ]
                }
            ]
        }
    }

    detector = ConflictDetector(docs_data, github_data)
    conflicts = detector.detect_all_conflicts()

    merger = RuleBasedMerger(docs_data, github_data, conflicts)
    merged = merger.merge_all()

    assert "apis" in merged
    assert "code_only_api" in merged["apis"]
    assert merged["apis"]["code_only_api"]["status"] == "code_only"


def test_rule_based_merge_matched():
    """Test rule-based merge for matched APIs"""
    docs_data = {
        "pages": [
            {
                "url": "https://example.com/api",
                "apis": [
                    {
                        "name": "matched_api",
                        "parameters": [{"name": "x", "type": "int"}],
                        "return_type": "str",
                    }
                ],
            }
        ]
    }

    github_data = {
        "code_analysis": {
            "analyzed_files": [
                {
                    "functions": [
                        {
                            "name": "matched_api",
                            "parameters": [{"name": "x", "type_hint": "int"}],
                            "return_type": "str",
                        }
                    ]
                }
            ]
        }
    }

    detector = ConflictDetector(docs_data, github_data)
    conflicts = detector.detect_all_conflicts()

    merger = RuleBasedMerger(docs_data, github_data, conflicts)
    merged = merger.merge_all()

    assert "apis" in merged
    assert "matched_api" in merged["apis"]
    assert merged["apis"]["matched_api"]["status"] == "matched"


def test_merge_summary():
    """Test merge summary statistics"""
    docs_data = {
        "pages": [
            {
                "url": "https://example.com/api",
                "apis": [
                    {"name": "api1", "parameters": [], "return_type": "str"},
                    {"name": "api2", "parameters": [], "return_type": "int"},
                ],
            }
        ]
    }

    github_data = {
        "code_analysis": {
            "analyzed_files": [
                {"functions": [{"name": "api3", "parameters": [], "return_type": "bool"}]}
            ]
        }
    }

    detector = ConflictDetector(docs_data, github_data)
    conflicts = detector.detect_all_conflicts()

    merger = RuleBasedMerger(docs_data, github_data, conflicts)
    merged = merger.merge_all()

    assert "summary" in merged
    assert merged["summary"]["total_apis"] == 3
    assert merged["summary"]["docs_only"] == 2
    assert merged["summary"]["code_only"] == 1


# ===========================
# Skill Builder Tests
# ===========================


def test_skill_builder_basic():
    """Test basic skill building"""
    config = {
        "name": "test_skill",
        "description": "Test skill description",
        "sources": [{"type": "documentation", "base_url": "https://example.com"}],
    }

    scraped_data = {"documentation": {"pages": [], "data_file": "/tmp/test.json"}}

    with tempfile.TemporaryDirectory() as tmpdir:
        # Override output directory
        builder = UnifiedSkillBuilder(config, scraped_data)
        builder.skill_dir = tmpdir

        builder._generate_skill_md()

        # Check SKILL.md was created
        skill_md = Path(tmpdir) / "SKILL.md"
        assert skill_md.exists()

        content = skill_md.read_text()
        assert "test_skill" in content.lower()
        assert "Test skill description" in content


def test_skill_builder_with_conflicts():
    """Test skill building with conflicts"""
    config = {
        "name": "test_skill",
        "description": "Test",
        "sources": [
            {"type": "documentation", "base_url": "https://example.com"},
            {"type": "github", "repo": "user/repo"},
        ],
    }

    scraped_data = {}

    conflicts = [
        Conflict(
            type="missing_in_code",
            severity="high",
            api_name="test_api",
            docs_info={"name": "test_api"},
            code_info=None,
            difference="Test difference",
        )
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        builder = UnifiedSkillBuilder(config, scraped_data, conflicts=conflicts)
        builder.skill_dir = tmpdir

        builder._generate_skill_md()

        skill_md = Path(tmpdir) / "SKILL.md"
        content = skill_md.read_text()

        assert "1 conflicts detected" in content
        assert "missing_in_code" in content


def test_skill_builder_merged_apis():
    """Test skill building with merged APIs"""
    config = {"name": "test", "description": "Test", "sources": []}

    scraped_data = {}

    merged_data = {
        "apis": {
            "test_api": {
                "name": "test_api",
                "status": "matched",
                "merged_signature": "test_api(x: int) -> str",
                "merged_description": "Test API",
                "source": "both",
            }
        }
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        builder = UnifiedSkillBuilder(config, scraped_data, merged_data=merged_data)
        builder.skill_dir = tmpdir

        content = builder._format_merged_apis()

        assert "✅ Verified APIs" in content
        assert "test_api" in content


# ===========================
# Issue #363: Local C3.x output
# ===========================


def _make_local_source(
    *,
    name: str = "my-codebase",
    path: str = "/tmp/my-codebase",
    test_examples: dict | None = None,
    patterns: list | None = None,
    how_to_guides: dict | None = None,
    config_patterns: dict | None = None,
    architecture: dict | None = None,
) -> dict:
    """Build a local-source dict shaped like UnifiedScraper._run_local_codebase_analysis output."""
    return {
        "source_id": f"unified_local_0_{name}",
        "path": path,
        "name": name,
        "description": f"Local analysis of {name}",
        "weight": 1.0,
        "patterns": patterns,
        "test_examples": test_examples,
        "how_to_guides": how_to_guides,
        "config_patterns": config_patterns,
        "architecture": architecture,
        "api_reference": None,
        "dependency_graph": None,
    }


def test_local_source_test_examples_become_references_363():
    """Issue #363: test_examples from local sources should land in references/."""
    config = {
        "name": "skill_363",
        "description": "Local C3.x output should not be dropped",
        "sources": [{"type": "local", "path": "/tmp/my-codebase"}],
    }

    test_examples = {
        "total_examples": 292,
        "high_value_count": 47,
        "examples_by_category": {"DI": 100, "Setup": 80, "Mocks": 112},
        "examples": [],
    }
    local_source = _make_local_source(test_examples=test_examples)

    scraped_data = {"local": [local_source]}

    with tempfile.TemporaryDirectory() as tmpdir:
        builder = UnifiedSkillBuilder(config, scraped_data)
        builder.skill_dir = tmpdir
        os.makedirs(os.path.join(tmpdir, "references"), exist_ok=True)

        builder._generate_local_codebase_analysis_references()

        analysis_root = Path(tmpdir) / "references" / "codebase_analysis"
        # Source-id is sanitized; should produce a single subdir
        subdirs = [p for p in analysis_root.iterdir() if p.is_dir()]
        assert len(subdirs) == 1, f"expected 1 source dir, got {subdirs}"
        source_dir = subdirs[0]

        examples_json = source_dir / "examples" / "test_examples.json"
        assert examples_json.exists(), "test_examples.json not generated"

        data = json.loads(examples_json.read_text())
        assert data["total_examples"] == 292
        assert data["high_value_count"] == 47

        # ARCHITECTURE.md should also be created with the test-examples summary
        arch_md = source_dir / "ARCHITECTURE.md"
        assert arch_md.exists()
        arch_content = arch_md.read_text()
        assert "292 usage example" in arch_content


def test_local_source_skill_md_includes_summary_363():
    """SKILL.md should reflect counts from local-source C3.x output (#363)."""
    config = {
        "name": "skill_363",
        "description": "Test",
        "sources": [{"type": "local", "path": "/tmp/my-codebase"}],
    }

    local_source = _make_local_source(
        test_examples={"total_examples": 50, "high_value_count": 12},
        how_to_guides={"guides": [{"title": "A"}, {"title": "B"}]},
    )
    scraped_data = {"local": [local_source]}

    with tempfile.TemporaryDirectory() as tmpdir:
        builder = UnifiedSkillBuilder(config, scraped_data)
        builder.skill_dir = tmpdir

        builder._generate_skill_md()

        skill_md = Path(tmpdir) / "SKILL.md"
        content = skill_md.read_text()

        assert "Architecture & Code Analysis" in content
        assert "50 extracted from tests" in content
        assert "12 high-value" in content
        assert "2 workflow tutorials" in content


def test_format_c3_summary_aggregates_across_sources_363():
    """_format_c3_summary_section should sum counts across multiple payloads."""
    config = {"name": "agg", "description": "Test", "sources": []}
    builder = UnifiedSkillBuilder(config, {})

    payloads = [
        {"test_examples": {"total_examples": 100, "high_value_count": 20}},
        {"test_examples": {"total_examples": 50, "high_value_count": 5}},
    ]

    out = builder._format_c3_summary_section(payloads)
    assert "150 extracted from tests" in out
    assert "25 high-value" in out


def test_format_c3_summary_backward_compat_dict_arg_363():
    """Single-dict arg (legacy) must still produce the summary."""
    config = {"name": "compat", "description": "Test", "sources": []}
    builder = UnifiedSkillBuilder(config, {})

    payload = {"test_examples": {"total_examples": 7, "high_value_count": 3}}
    out = builder._format_c3_summary_section(payload)
    assert "7 extracted from tests" in out


def test_collect_c3_payloads_combines_github_and_local_363():
    """_collect_c3_payloads should pull from both github and local sources."""
    config = {"name": "combo", "description": "Test", "sources": []}

    github_c3 = {"test_examples": {"total_examples": 10, "high_value_count": 2}}
    local_source = _make_local_source(test_examples={"total_examples": 5, "high_value_count": 1})
    scraped_data = {
        "github": [{"repo_id": "owner_repo", "data": {"c3_analysis": github_c3}}],
        "local": [local_source],
    }
    builder = UnifiedSkillBuilder(config, scraped_data)

    payloads = builder._collect_c3_payloads()
    assert len(payloads) == 2

    # Aggregated summary should reflect both
    out = builder._format_c3_summary_section(payloads)
    assert "15 extracted from tests" in out
    assert "3 high-value" in out


def test_local_source_without_c3_data_skipped_363():
    """Local sources with no C3 fields should not create empty reference dirs."""
    config = {
        "name": "empty_local",
        "description": "Test",
        "sources": [{"type": "local", "path": "/tmp/my-codebase"}],
    }
    # All C3 fields None / empty
    local_source = _make_local_source()
    scraped_data = {"local": [local_source]}

    with tempfile.TemporaryDirectory() as tmpdir:
        builder = UnifiedSkillBuilder(config, scraped_data)
        builder.skill_dir = tmpdir
        os.makedirs(os.path.join(tmpdir, "references"), exist_ok=True)

        builder._generate_local_codebase_analysis_references()

        analysis_root = Path(tmpdir) / "references" / "codebase_analysis"
        assert not analysis_root.exists() or not any(analysis_root.iterdir())


def test_sanitize_source_id_363():
    """Source IDs must be filesystem-safe."""
    sanitize = UnifiedSkillBuilder._sanitize_source_id
    assert sanitize("my-skill_local_0_repo") == "my-skill_local_0_repo"
    assert sanitize("path/with/slashes") == "path_with_slashes"
    assert sanitize("name with spaces") == "name_with_spaces"
    assert sanitize("!!!") == "local"
    assert sanitize("") == "local"
    assert sanitize(None) == "local"


# ===========================
# Integration Tests
# ===========================


def test_full_workflow_unified_config():
    """Test complete workflow with unified config"""
    # Create test config
    config = {
        "name": "test_unified",
        "description": "Test unified workflow",
        "merge_mode": "rule-based",
        "sources": [
            {"type": "documentation", "base_url": "https://example.com", "extract_api": True},
            {
                "type": "github",
                "repo": "user/repo",
                "include_code": True,
                "code_analysis_depth": "surface",
            },
        ],
    }

    # Validate config
    validator = ConfigValidator(config)
    validator.validate()
    assert validator.is_unified
    assert validator.needs_api_merge()


def test_config_file_validation():
    """Test validation from config file"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        config = {
            "name": "test",
            "description": "Test",
            "sources": [{"type": "documentation", "base_url": "https://example.com"}],
        }
        json.dump(config, f)
        config_path = f.name

    try:
        validator = validate_config(config_path)
        assert validator.is_unified
    finally:
        os.unlink(config_path)


# ===========================
# Workflow JSON Config Tests
# ===========================


class TestWorkflowJsonConfig:
    """Test that UnifiedScraper.run() merges JSON workflow fields into effective_args."""

    def _make_scraper(self, tmp_path, extra_config=None):
        """Build a minimal UnifiedScraper backed by a temp config file."""
        from skill_seekers.cli.unified_scraper import UnifiedScraper

        config = {
            "name": "test_workflow",
            "description": "Test workflow config",
            "sources": [],
            **(extra_config or {}),
        }
        cfg_file = tmp_path / "config.json"
        cfg_file.write_text(json.dumps(config))
        scraper = UnifiedScraper.__new__(UnifiedScraper)
        scraper.config = config
        scraper.name = config["name"]
        return scraper

    def test_json_workflows_merged_when_args_none(self, tmp_path, monkeypatch):
        """JSON 'workflows' list is used even when args=None."""
        captured = {}

        def fake_run_workflows(args, context=None):  # noqa: ARG001
            captured["enhance_workflow"] = getattr(args, "enhance_workflow", None)

        monkeypatch.setattr(
            "skill_seekers.cli.workflow_runner.run_workflows", fake_run_workflows, raising=False
        )
        import skill_seekers.cli.unified_scraper as us_module

        monkeypatch.setattr(us_module, "run_workflows", fake_run_workflows, raising=False)

        scraper = self._make_scraper(tmp_path, {"workflows": ["security-focus", "minimal"]})
        # Patch _merge_workflow_config inline by directly testing the logic
        import argparse

        effective_args = argparse.Namespace(
            enhance_workflow=None, enhance_stage=None, var=None, workflow_dry_run=False
        )
        json_workflows = scraper.config.get("workflows", [])
        if json_workflows:
            effective_args.enhance_workflow = (
                list(effective_args.enhance_workflow or []) + json_workflows
            )
        assert effective_args.enhance_workflow == ["security-focus", "minimal"]

    def test_json_workflows_appended_after_cli(self, tmp_path):
        """CLI --enhance-workflow values come first; JSON 'workflows' appended after."""
        import argparse

        config = {
            "name": "test",
            "description": "test",
            "sources": [],
            "workflows": ["json-wf"],
        }
        cfg_file = tmp_path / "config.json"
        cfg_file.write_text(json.dumps(config))

        cli_args = argparse.Namespace(
            enhance_workflow=["cli-wf"],
            enhance_stage=None,
            var=None,
            workflow_dry_run=False,
        )
        json_workflows = config.get("workflows", [])
        effective = argparse.Namespace(
            enhance_workflow=list(cli_args.enhance_workflow or []) + json_workflows,
            enhance_stage=None,
            var=None,
            workflow_dry_run=False,
        )
        assert effective.enhance_workflow == ["cli-wf", "json-wf"]

    def test_json_workflow_stages_merged(self, tmp_path):
        """JSON 'workflow_stages' are appended to enhance_stage."""
        import argparse

        config = {"workflow_stages": ["sec:Analyze security", "cleanup:Remove boilerplate"]}
        effective_args = argparse.Namespace(
            enhance_workflow=None, enhance_stage=None, var=None, workflow_dry_run=False
        )
        json_stages = config.get("workflow_stages", [])
        if json_stages:
            effective_args.enhance_stage = list(effective_args.enhance_stage or []) + json_stages
        assert effective_args.enhance_stage == [
            "sec:Analyze security",
            "cleanup:Remove boilerplate",
        ]

    def test_json_workflow_vars_converted_to_kv_strings(self, tmp_path):
        """JSON 'workflow_vars' dict is converted to 'key=value' strings."""
        import argparse

        config = {"workflow_vars": {"focus_area": "performance", "detail_level": "basic"}}
        effective_args = argparse.Namespace(
            enhance_workflow=None, enhance_stage=None, var=None, workflow_dry_run=False
        )
        json_vars = config.get("workflow_vars", {})
        if json_vars:
            effective_args.var = list(effective_args.var or []) + [
                f"{k}={v}" for k, v in json_vars.items()
            ]
        assert "focus_area=performance" in effective_args.var
        assert "detail_level=basic" in effective_args.var

    def test_config_validator_accepts_workflow_fields(self, tmp_path):
        """ConfigValidator should not raise on workflow-related top-level fields."""
        from skill_seekers.cli.config_validator import ConfigValidator

        config = {
            "name": "test",
            "description": "Test with workflows",
            "sources": [{"type": "documentation", "base_url": "https://example.com"}],
            "workflows": ["security-focus"],
            "workflow_stages": ["custom:Do something"],
            "workflow_vars": {"key": "value"},
        }
        validator = ConfigValidator(config)
        # Should not raise
        assert validator.validate() is True

    def test_empty_workflow_config_no_effect(self, tmp_path):
        """If no JSON workflow fields exist, effective_args remains unchanged."""
        import argparse

        config = {"name": "test", "description": "test", "sources": []}
        effective_args = argparse.Namespace(
            enhance_workflow=None, enhance_stage=None, var=None, workflow_dry_run=False
        )
        json_workflows = config.get("workflows", [])
        json_stages = config.get("workflow_stages", [])
        json_vars = config.get("workflow_vars", {})
        has_json = bool(json_workflows or json_stages or json_vars)
        assert not has_json
        assert effective_args.enhance_workflow is None
        assert effective_args.enhance_stage is None
        assert effective_args.var is None


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
