"""Tests for the `skill-seekers scan` command (issue #327).

The scan command orchestrates: signal collection → AI detection → config
resolution / AI generation → codebase config emission → optional publish.
This file groups tests by the layer being exercised. All AI and network
calls are stubbed.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch


from skill_seekers.cli.scan_command import (
    Detection,
    detect_with_ai,
    diff_against_existing,
    emit_codebase_config,
    generate_config_with_ai,
    maybe_publish,
    resolve_or_generate,
    run_scan,
    stamp_version,
)
from skill_seekers.cli.signal_collectors import Signal, SignalBundle


class TestStampVersion:
    def test_adds_top_level_detected_version(self, tmp_path: Path):
        cfg = tmp_path / "x.json"
        cfg.write_text(json.dumps({"name": "x", "description": "d"}))
        stamp_version(cfg, "1.2.3")
        data = json.loads(cfg.read_text())
        assert data["detected_version"] == "1.2.3"
        assert data["name"] == "x"
        assert data["description"] == "d"

    def test_overwrites_existing_detected_version(self, tmp_path: Path):
        cfg = tmp_path / "x.json"
        cfg.write_text(json.dumps({"name": "x", "detected_version": "1.0.0"}))
        stamp_version(cfg, "2.0.0")
        assert json.loads(cfg.read_text())["detected_version"] == "2.0.0"

    def test_none_version_clears_field(self, tmp_path: Path):
        cfg = tmp_path / "x.json"
        cfg.write_text(json.dumps({"name": "x", "detected_version": "1.0.0"}))
        stamp_version(cfg, None)
        data = json.loads(cfg.read_text())
        assert "detected_version" not in data

    def test_preserves_unrelated_keys(self, tmp_path: Path):
        cfg = tmp_path / "x.json"
        original = {
            "name": "x",
            "base_url": "https://x.io",
            "sources": [{"type": "documentation", "base_url": "https://x.io"}],
            "categories": {"a": ["foo"]},
        }
        cfg.write_text(json.dumps(original))
        stamp_version(cfg, "9.9.9")
        data = json.loads(cfg.read_text())
        assert data["base_url"] == "https://x.io"
        assert data["sources"] == original["sources"]
        assert data["categories"] == original["categories"]


class TestEmitCodebaseConfig:
    def test_emits_expected_shape(self, tmp_path: Path):
        proj = tmp_path / "myproj"
        proj.mkdir()
        out = tmp_path / "out"
        out.mkdir()

        cfg_path = emit_codebase_config(proj, out)

        assert cfg_path.name == "myproj-codebase.json"
        data = json.loads(cfg_path.read_text())
        assert data["name"] == "myproj-codebase"
        assert "sources" in data
        assert len(data["sources"]) == 1
        source = data["sources"][0]
        assert source["type"] == "local"
        assert source["path"] == str(proj.resolve())
        assert source.get("include_code") is True
        assert "file_patterns" in source
        assert "skip_patterns" in source

    def test_overwrites_existing(self, tmp_path: Path):
        proj = tmp_path / "p"
        proj.mkdir()
        out = tmp_path / "out"
        out.mkdir()

        first = emit_codebase_config(proj, out)
        first.write_text(json.dumps({"name": "stale"}))

        second = emit_codebase_config(proj, out)
        data = json.loads(second.read_text())
        assert data["name"] == "p-codebase"


class TestDiffAgainstExisting:
    def _write(self, out: Path, name: str, version: str | None) -> Path:
        path = out / f"{name}.json"
        payload = {"name": name}
        if version is not None:
            payload["detected_version"] = version
        path.write_text(json.dumps(payload))
        return path

    def test_all_added_when_out_empty(self, tmp_path: Path):
        out = tmp_path / "out"
        out.mkdir()
        detections = [
            Detection(
                name="react",
                ecosystem="npm",
                version="18.3.0",
                kind="framework",
                confidence=0.9,
                evidence="",
            ),
        ]
        diff = diff_against_existing(out, detections)
        assert diff.added == ["react"]
        assert diff.updated == []
        assert diff.removed == []

    def test_no_change_when_versions_match(self, tmp_path: Path):
        out = tmp_path / "out"
        out.mkdir()
        self._write(out, "react", "18.3.0")
        detections = [
            Detection(
                name="react",
                ecosystem="npm",
                version="18.3.0",
                kind="framework",
                confidence=0.9,
                evidence="",
            ),
        ]
        diff = diff_against_existing(out, detections)
        assert diff.added == []
        assert diff.updated == []
        assert diff.removed == []

    def test_updated_on_version_bump(self, tmp_path: Path):
        out = tmp_path / "out"
        out.mkdir()
        self._write(out, "react", "18.2.0")
        detections = [
            Detection(
                name="react",
                ecosystem="npm",
                version="18.3.1",
                kind="framework",
                confidence=0.9,
                evidence="",
            ),
        ]
        diff = diff_against_existing(out, detections)
        assert diff.added == []
        assert diff.updated == [("react", "18.2.0", "18.3.1")]
        assert diff.removed == []

    def test_removed_when_detection_gone(self, tmp_path: Path):
        out = tmp_path / "out"
        out.mkdir()
        self._write(out, "react", "18.2.0")
        self._write(out, "vue", "3.4.0")
        detections = [
            Detection(
                name="react",
                ecosystem="npm",
                version="18.2.0",
                kind="framework",
                confidence=0.9,
                evidence="",
            ),
        ]
        diff = diff_against_existing(out, detections)
        assert diff.added == []
        assert diff.updated == []
        assert diff.removed == ["vue"]

    def test_ignores_codebase_config(self, tmp_path: Path):
        """The <project>-codebase.json should never appear in diffs."""
        out = tmp_path / "out"
        out.mkdir()
        (out / "myproj-codebase.json").write_text(
            json.dumps({"name": "myproj-codebase", "sources": [{"type": "local"}]})
        )
        detections: list[Detection] = []
        diff = diff_against_existing(out, detections)
        assert diff.added == []
        assert diff.updated == []
        assert diff.removed == []

    def test_handles_config_without_detected_version(self, tmp_path: Path):
        """Configs without detected_version should diff as 'updated' when one arrives."""
        out = tmp_path / "out"
        out.mkdir()
        self._write(out, "react", None)  # no detected_version
        detections = [
            Detection(
                name="react",
                ecosystem="npm",
                version="18.3.0",
                kind="framework",
                confidence=0.9,
                evidence="",
            ),
        ]
        diff = diff_against_existing(out, detections)
        # name still present → not added, not removed
        assert diff.added == []
        assert diff.removed == []
        # missing → new version is an update from None → "18.3.0"
        assert diff.updated == [("react", None, "18.3.0")]


def _bundle(project_name: str = "myproj") -> SignalBundle:
    """Minimal SignalBundle for AI-layer tests."""
    return SignalBundle(
        signals=[
            Signal(
                kind="manifest",
                path=Path("package.json"),
                content='{"dependencies": {"react": "^18.3.0"}}',
            ),
        ],
        git_remote=None,
        project_name=project_name,
    )


class TestDetectWithAI:
    def test_parses_clean_json_array(self):
        client = MagicMock()
        client.call.return_value = json.dumps(
            [
                {
                    "name": "react",
                    "ecosystem": "npm",
                    "version": "18.3.0",
                    "kind": "framework",
                    "confidence": 0.95,
                    "evidence": "package.json",
                },
            ]
        )

        detections = detect_with_ai(_bundle(), client)
        assert len(detections) == 1
        d = detections[0]
        assert isinstance(d, Detection)
        assert d.name == "react"
        assert d.version == "18.3.0"
        assert d.kind == "framework"

    def test_extracts_json_from_markdown_fence(self):
        client = MagicMock()
        client.call.return_value = (
            "Here are the detections:\n\n"
            "```json\n"
            '[{"name": "fastapi", "ecosystem": "pypi", "version": "0.110.0", '
            '"kind": "framework", "confidence": 0.9, "evidence": "pyproject.toml"}]\n'
            "```\n\nLet me know if you want more."
        )

        detections = detect_with_ai(_bundle(), client)
        assert len(detections) == 1
        assert detections[0].name == "fastapi"

    def test_malformed_json_returns_empty_list(self):
        client = MagicMock()
        client.call.return_value = "totally not json"
        detections = detect_with_ai(_bundle(), client)
        assert detections == []

    def test_none_response_returns_empty_list(self):
        client = MagicMock()
        client.call.return_value = None
        detections = detect_with_ai(_bundle(), client)
        assert detections == []

    def test_filters_below_confidence_threshold(self):
        client = MagicMock()
        client.call.return_value = json.dumps(
            [
                {
                    "name": "react",
                    "ecosystem": "npm",
                    "version": "18.3.0",
                    "kind": "framework",
                    "confidence": 0.95,
                    "evidence": "x",
                },
                {
                    "name": "lodash",
                    "ecosystem": "npm",
                    "version": "4.17.0",
                    "kind": "library",
                    "confidence": 0.2,
                    "evidence": "transitive",
                },
            ]
        )

        detections = detect_with_ai(_bundle(), client, min_confidence=0.5)
        assert [d.name for d in detections] == ["react"]

    def test_drops_entries_missing_required_fields(self):
        client = MagicMock()
        client.call.return_value = json.dumps(
            [
                {
                    "name": "react",
                    "ecosystem": "npm",
                    "version": "18.3.0",
                    "kind": "framework",
                    "confidence": 0.9,
                    "evidence": "x",
                },
                {"ecosystem": "npm", "version": "1.0.0"},  # no name → invalid
            ]
        )

        detections = detect_with_ai(_bundle(), client)
        assert [d.name for d in detections] == ["react"]


class TestGenerateConfigWithAI:
    def _det(self, name="newlib", version="1.0.0"):
        return Detection(
            name=name,
            ecosystem="npm",
            version=version,
            kind="library",
            confidence=0.9,
            evidence="package.json",
        )

    def test_returns_valid_config_dict(self):
        client = MagicMock()
        client.call.return_value = json.dumps(
            {
                "name": "newlib",
                "description": "Some new library.",
                "sources": [{"type": "documentation", "base_url": "https://newlib.dev/"}],
            }
        )

        cfg = generate_config_with_ai(self._det(), client)
        assert cfg["name"] == "newlib"
        assert cfg["sources"][0]["type"] == "documentation"
        # detected_version stamped from the Detection
        assert cfg["detected_version"] == "1.0.0"

    def test_extracts_from_markdown_fence(self):
        client = MagicMock()
        client.call.return_value = (
            "```json\n"
            '{"name": "newlib", "description": "x", '
            '"sources": [{"type": "documentation", "base_url": "https://x.io"}]}\n'
            "```"
        )
        cfg = generate_config_with_ai(self._det(), client)
        assert cfg["name"] == "newlib"

    def test_retries_once_on_invalid_then_succeeds(self):
        client = MagicMock()
        client.call.side_effect = [
            "garbage not json",
            json.dumps(
                {
                    "name": "newlib",
                    "description": "ok",
                    "sources": [{"type": "documentation", "base_url": "https://x.io"}],
                }
            ),
        ]
        cfg = generate_config_with_ai(self._det(), client)
        assert cfg is not None
        assert cfg["name"] == "newlib"
        assert client.call.call_count == 2

    def test_returns_none_after_repeated_failures(self):
        client = MagicMock()
        client.call.return_value = "garbage"
        cfg = generate_config_with_ai(self._det(), client)
        assert cfg is None

    def test_returns_none_when_validator_rejects(self):
        """AI returns JSON but missing required fields → validator fails → None."""
        client = MagicMock()
        client.call.return_value = json.dumps({"name": "x"})  # no description, no sources
        cfg = generate_config_with_ai(self._det(), client)
        assert cfg is None


class TestResolveOrGenerate:
    def _det(self, name="react", version="18.3.0"):
        return Detection(
            name=name,
            ecosystem="npm",
            version=version,
            kind="framework",
            confidence=0.9,
            evidence="package.json",
        )

    def _existing_config(self, tmp_path: Path, name: str) -> Path:
        path = tmp_path / f"{name}.json"
        path.write_text(
            json.dumps(
                {
                    "name": name,
                    "description": f"{name} skill",
                    "sources": [{"type": "documentation", "base_url": f"https://{name}.io"}],
                }
            )
        )
        return path

    def test_local_hit_returns_stamped_copy(self, tmp_path: Path):
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        existing = self._existing_config(tmp_path, "react")

        with patch(
            "skill_seekers.cli.scan_command.resolve_config_path",
            return_value=existing,
        ):
            result_path = resolve_or_generate(
                self._det(),
                out_dir=out_dir,
                client=MagicMock(),
                allow_network=True,
                allow_generate=True,
            )

        assert result_path is not None
        assert result_path.parent == out_dir
        data = json.loads(result_path.read_text())
        assert data["detected_version"] == "18.3.0"
        assert data["name"] == "react"

    def test_no_fetch_passes_auto_fetch_false(self, tmp_path: Path):
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        with patch(
            "skill_seekers.cli.scan_command.resolve_config_path",
            return_value=None,
        ) as resolve_mock:
            resolve_or_generate(
                self._det(),
                out_dir=out_dir,
                client=MagicMock(),
                allow_network=False,
                allow_generate=False,
            )

        # resolve_config_path is called with auto_fetch=False when allow_network=False
        _, kwargs = resolve_mock.call_args
        assert kwargs.get("auto_fetch") is False

    def test_falls_back_to_ai_generation_on_miss(self, tmp_path: Path):
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        generated = {
            "name": "react",
            "description": "react",
            "sources": [{"type": "documentation", "base_url": "https://react.dev"}],
            "detected_version": "18.3.0",
        }

        with (
            patch(
                "skill_seekers.cli.scan_command.resolve_config_path",
                return_value=None,
            ),
            patch(
                "skill_seekers.cli.scan_command.generate_config_with_ai",
                return_value=generated,
            ) as gen_mock,
        ):
            result_path = resolve_or_generate(
                self._det(),
                out_dir=out_dir,
                client=MagicMock(),
                allow_network=True,
                allow_generate=True,
            )

        assert result_path is not None
        assert gen_mock.called
        data = json.loads(result_path.read_text())
        assert data["name"] == "react"

    def test_no_generate_returns_none_on_miss(self, tmp_path: Path):
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        with (
            patch(
                "skill_seekers.cli.scan_command.resolve_config_path",
                return_value=None,
            ),
            patch(
                "skill_seekers.cli.scan_command.generate_config_with_ai",
            ) as gen_mock,
        ):
            result_path = resolve_or_generate(
                self._det(),
                out_dir=out_dir,
                client=MagicMock(),
                allow_network=True,
                allow_generate=False,
            )

        assert result_path is None
        gen_mock.assert_not_called()

    def test_marks_generated_path_as_freshly_generated(self, tmp_path: Path):
        """Resolver returns a tuple (path, was_generated) so caller can prompt to publish."""
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        existing = self._existing_config(tmp_path, "react")

        with patch(
            "skill_seekers.cli.scan_command.resolve_config_path",
            return_value=existing,
        ):
            from skill_seekers.cli.scan_command import resolve_or_generate_with_status

            path, was_generated = resolve_or_generate_with_status(
                self._det(),
                out_dir=out_dir,
                client=MagicMock(),
                allow_network=True,
                allow_generate=True,
            )
        assert was_generated is False

        # Generated case
        with (
            patch(
                "skill_seekers.cli.scan_command.resolve_config_path",
                return_value=None,
            ),
            patch(
                "skill_seekers.cli.scan_command.generate_config_with_ai",
                return_value={
                    "name": "react",
                    "description": "x",
                    "sources": [{"type": "documentation", "base_url": "https://x"}],
                    "detected_version": "18.3.0",
                },
            ),
        ):
            path2, was_generated2 = resolve_or_generate_with_status(
                self._det(),
                out_dir=out_dir,
                client=MagicMock(),
                allow_network=True,
                allow_generate=True,
            )
        assert was_generated2 is True


class TestMaybePublish:
    def _write_cfg(self, tmp_path: Path, name: str) -> Path:
        path = tmp_path / f"{name}.json"
        path.write_text(
            json.dumps(
                {
                    "name": name,
                    "description": "x",
                    "sources": [{"type": "documentation", "base_url": "https://x.io"}],
                }
            )
        )
        return path

    def test_no_prompt_skips_entirely(self, tmp_path: Path, capsys):
        cfg = self._write_cfg(tmp_path, "newlib")
        submit = MagicMock()

        with patch("skill_seekers.cli.scan_command._submit_config_sync", submit):
            maybe_publish([cfg], skip_prompt=True)

        submit.assert_not_called()

    def test_no_generated_configs_no_prompt(self, tmp_path: Path):
        submit = MagicMock()
        with (
            patch("skill_seekers.cli.scan_command._submit_config_sync", submit),
            patch("builtins.input") as input_mock,
        ):
            maybe_publish([], skip_prompt=False)
        input_mock.assert_not_called()
        submit.assert_not_called()

    def test_yes_calls_submit_with_path(self, tmp_path: Path):
        cfg = self._write_cfg(tmp_path, "newlib")
        submit = MagicMock(return_value={"ok": True, "url": "https://github.com/x/y/issues/1"})

        with (
            patch("skill_seekers.cli.scan_command._submit_config_sync", submit),
            patch("builtins.input", return_value="y"),
        ):
            maybe_publish([cfg], skip_prompt=False)

        submit.assert_called_once()
        args, _ = submit.call_args
        assert args[0] == cfg

    def test_no_does_not_call_submit(self, tmp_path: Path):
        cfg = self._write_cfg(tmp_path, "newlib")
        submit = MagicMock()
        with (
            patch("skill_seekers.cli.scan_command._submit_config_sync", submit),
            patch("builtins.input", return_value="n"),
        ):
            maybe_publish([cfg], skip_prompt=False)
        submit.assert_not_called()

    def test_handles_submit_failure_gracefully(self, tmp_path: Path, capsys):
        cfg = self._write_cfg(tmp_path, "newlib")
        submit = MagicMock(side_effect=RuntimeError("boom"))
        with (
            patch("skill_seekers.cli.scan_command._submit_config_sync", submit),
            patch("builtins.input", return_value="y"),
        ):
            # Should not raise
            maybe_publish([cfg], skip_prompt=False)
        captured = capsys.readouterr()
        assert "failed" in captured.out.lower() or "error" in captured.out.lower()


class TestRunScan:
    """End-to-end scan against a fixture project. AI and network stubbed."""

    def _make_project(self, tmp_path: Path) -> Path:
        proj = tmp_path / "fakeproj"
        proj.mkdir()
        (proj / "package.json").write_text(
            json.dumps({"name": "fakeproj", "dependencies": {"react": "^18.3.0"}})
        )
        (proj / "README.md").write_text("# fakeproj\n\nUses React.")
        return proj

    def test_resolved_path_emits_config_and_codebase(self, tmp_path: Path):
        proj = self._make_project(tmp_path)
        out_dir = tmp_path / "out"

        # Stub AI client to return one react detection.
        client = MagicMock()
        client.call.return_value = json.dumps(
            [
                {
                    "name": "react",
                    "ecosystem": "npm",
                    "version": "18.3.0",
                    "kind": "framework",
                    "confidence": 0.95,
                    "evidence": "package.json",
                }
            ]
        )

        # Stub resolve_config_path so it returns a pre-existing react.json.
        canned = tmp_path / "react.json"
        canned.write_text(
            json.dumps(
                {
                    "name": "react",
                    "description": "react",
                    "sources": [{"type": "documentation", "base_url": "https://react.dev"}],
                }
            )
        )

        with patch("skill_seekers.cli.scan_command.resolve_config_path", return_value=canned):
            result = run_scan(
                proj,
                out_dir,
                agent_client=client,
                allow_network=True,
                allow_generate=True,
                skip_publish=True,
                min_confidence=0.4,
            )

        assert len(result.detections) == 1
        assert result.detections[0].name == "react"
        # 1 framework + codebase
        assert result.codebase_config is not None
        assert result.codebase_config.name == "fakeproj-codebase.json"
        assert len(result.emitted) == 1
        assert result.emitted[0].name == "react.json"
        # Resolved (not generated)
        assert result.generated == []
        # On first scan, react is "added"
        assert result.diff is not None
        assert "react" in result.diff.added

    def test_unmapped_path_triggers_ai_generation(self, tmp_path: Path):
        proj = self._make_project(tmp_path)
        out_dir = tmp_path / "out"

        client = MagicMock()
        # First call → detection. Second call → AI-generated config.
        client.call.side_effect = [
            json.dumps(
                [
                    {
                        "name": "supernovafw",
                        "ecosystem": "npm",
                        "version": "0.1.0",
                        "kind": "framework",
                        "confidence": 0.9,
                        "evidence": "package.json",
                    }
                ]
            ),
            json.dumps(
                {
                    "name": "supernovafw",
                    "description": "Made up framework.",
                    "sources": [{"type": "documentation", "base_url": "https://supernovafw.dev"}],
                }
            ),
        ]

        with patch("skill_seekers.cli.scan_command.resolve_config_path", return_value=None):
            result = run_scan(
                proj,
                out_dir,
                agent_client=client,
                allow_network=True,
                allow_generate=True,
                skip_publish=True,
                min_confidence=0.4,
            )

        assert len(result.generated) == 1
        assert result.generated[0].name == "supernovafw.json"
        data = json.loads(result.generated[0].read_text())
        assert data["detected_version"] == "0.1.0"

    def test_re_scan_reports_no_changes(self, tmp_path: Path):
        proj = self._make_project(tmp_path)
        out_dir = tmp_path / "out"

        client = MagicMock()
        client.call.return_value = json.dumps(
            [
                {
                    "name": "react",
                    "ecosystem": "npm",
                    "version": "18.3.0",
                    "kind": "framework",
                    "confidence": 0.95,
                    "evidence": "x",
                }
            ]
        )

        canned = tmp_path / "react.json"
        canned.write_text(
            json.dumps(
                {
                    "name": "react",
                    "description": "react",
                    "sources": [{"type": "documentation", "base_url": "https://react.dev"}],
                }
            )
        )

        with patch("skill_seekers.cli.scan_command.resolve_config_path", return_value=canned):
            run_scan(
                proj,
                out_dir,
                agent_client=client,
                allow_network=True,
                allow_generate=True,
                skip_publish=True,
                min_confidence=0.4,
            )
            # Second pass — same detection, same version → no diff.
            result2 = run_scan(
                proj,
                out_dir,
                agent_client=client,
                allow_network=True,
                allow_generate=True,
                skip_publish=True,
                min_confidence=0.4,
            )

        assert result2.diff is not None
        assert result2.diff.added == []
        assert result2.diff.updated == []
        assert result2.diff.removed == []

    def test_no_generate_skips_unmapped_silently(self, tmp_path: Path):
        proj = self._make_project(tmp_path)
        out_dir = tmp_path / "out"

        client = MagicMock()
        client.call.return_value = json.dumps(
            [
                {
                    "name": "obscurelib",
                    "ecosystem": "npm",
                    "version": "1.0.0",
                    "kind": "library",
                    "confidence": 0.9,
                    "evidence": "x",
                }
            ]
        )

        with patch("skill_seekers.cli.scan_command.resolve_config_path", return_value=None):
            result = run_scan(
                proj,
                out_dir,
                agent_client=client,
                allow_network=False,
                allow_generate=False,
                skip_publish=True,
                min_confidence=0.4,
            )

        # Detection happened but no config could be produced.
        assert len(result.detections) == 1
        assert result.emitted == []
        assert result.generated == []
        # Codebase config is still emitted.
        assert result.codebase_config is not None


class TestCliRegistration:
    def test_scan_is_registered_in_command_modules(self):
        from skill_seekers.cli.main import COMMAND_MODULES

        assert COMMAND_MODULES["scan"] == "skill_seekers.cli.scan_command"

    def test_scan_parser_registered(self):
        from skill_seekers.cli.parsers import get_parser_names

        assert "scan" in get_parser_names()

    def test_scan_parser_has_expected_arguments(self):
        import argparse
        from skill_seekers.cli.parsers.scan_parser import ScanParser

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        ScanParser().create_parser(subparsers)
        # Smoke parse: a minimal valid invocation
        args = parser.parse_args(["scan", ".", "--no-fetch", "--no-generate"])
        assert args.directory == "."
        assert args.no_fetch is True
        assert args.no_generate is True
