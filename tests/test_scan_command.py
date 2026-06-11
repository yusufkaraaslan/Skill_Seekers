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
    ScanResult,
    _canonical_name_candidates,
    _exit_code_for,
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
    def test_writes_to_metadata_detected_version(self, tmp_path: Path):
        cfg = tmp_path / "x.json"
        cfg.write_text(json.dumps({"name": "x", "description": "d"}))
        stamp_version(cfg, "1.2.3")
        data = json.loads(cfg.read_text())
        assert data["metadata"]["detected_version"] == "1.2.3"
        # NOT at top level (WS2 — schema cleanup).
        assert "detected_version" not in data
        assert data["name"] == "x"
        assert data["description"] == "d"

    def test_overwrites_existing_detected_version(self, tmp_path: Path):
        cfg = tmp_path / "x.json"
        cfg.write_text(json.dumps({"name": "x", "metadata": {"detected_version": "1.0.0"}}))
        stamp_version(cfg, "2.0.0")
        assert json.loads(cfg.read_text())["metadata"]["detected_version"] == "2.0.0"

    def test_migrates_legacy_top_level_field_to_metadata(self, tmp_path: Path):
        """WS2 backwards-compat: a config previously stamped at top level should
        get migrated to metadata on the next stamp."""
        cfg = tmp_path / "x.json"
        cfg.write_text(json.dumps({"name": "x", "detected_version": "1.0.0"}))
        stamp_version(cfg, "2.0.0")
        data = json.loads(cfg.read_text())
        assert "detected_version" not in data  # top-level cleared
        assert data["metadata"]["detected_version"] == "2.0.0"

    def test_none_version_clears_field(self, tmp_path: Path):
        cfg = tmp_path / "x.json"
        cfg.write_text(json.dumps({"name": "x", "metadata": {"detected_version": "1.0.0"}}))
        stamp_version(cfg, None)
        data = json.loads(cfg.read_text())
        assert "detected_version" not in data
        assert "detected_version" not in data.get("metadata", {})

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

    def test_no_churn_when_internal_name_differs_from_detection(self, tmp_path: Path):
        """Regression: diff used to key existing off `data['name']` (canonical
        preset name) but current off `Detection.name` (AI display name). Even
        with the same package across scans, the keys mismatched and the diff
        spammed phantom 'added X / removed Y'. Now both sides key by filename
        slug.
        """
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        # Simulate the file that scan would have written: filename is the slug
        # of the AI's name ("Godot Engine" → "godot-engine.json"), but the
        # *resolved* canonical config inside has internal name = "godot".
        (out_dir / "godot-engine.json").write_text(
            json.dumps(
                {
                    "name": "godot",  # canonical from registry, NOT matching the slug
                    "detected_version": "4.7",
                }
            )
        )

        # Second-scan detection: AI returns same display name again.
        detections = [
            Detection(
                name="Godot Engine",
                ecosystem="other",
                version="4.7",
                kind="framework",
                confidence=1.0,
                evidence="",
            ),
        ]
        diff = diff_against_existing(out_dir, detections)
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

    def test_non_numeric_confidence_is_dropped_not_crash(self):
        """Regression for SCAN-02: a non-numeric confidence must drop that one
        entry, not crash the whole scan with ValueError/TypeError."""
        client = MagicMock()
        client.call.return_value = json.dumps(
            [
                {
                    "name": "react",
                    "ecosystem": "npm",
                    "version": "18.3.0",
                    "kind": "framework",
                    "confidence": "high",  # non-numeric — would crash float()
                    "evidence": "x",
                },
                {
                    "name": "vue",
                    "ecosystem": "npm",
                    "version": "3.4.0",
                    "kind": "framework",
                    "confidence": 0.9,
                    "evidence": "y",
                },
            ]
        )
        detections = detect_with_ai(_bundle(), client)
        assert [d.name for d in detections] == ["vue"]

    def test_handles_agentclient_exception_gracefully(self):
        """AgentClient auth/network errors must not crash the scan."""
        client = MagicMock()
        client.call.side_effect = RuntimeError("API key invalid")
        detections = detect_with_ai(_bundle(), client)
        assert detections == []

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
        # detected_version stamped from the Detection (WS2: now under metadata)
        assert cfg["metadata"]["detected_version"] == "1.0.0"

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

    def test_handles_agentclient_exception_gracefully(self):
        """Generator call raising → retries; if all retries raise → None, no crash."""
        client = MagicMock()
        client.call.side_effect = RuntimeError("connection refused")
        cfg = generate_config_with_ai(self._det(), client)
        assert cfg is None
        # Both attempts were made — exception didn't break the retry loop.
        assert client.call.call_count == 2

    def test_rejects_name_that_breaks_registry_submission(self):
        """submit_config_tool requires name ^[a-zA-Z0-9_-]+$. Reject up front
        so we don't write configs that silently fail to publish later."""
        client = MagicMock()
        bad = json.dumps(
            {
                "name": "@scope/pkg",  # / and @ both forbidden by the registry regex
                "description": "valid otherwise",
                "sources": [{"type": "documentation", "base_url": "https://x.io"}],
            }
        )
        good = json.dumps(
            {
                "name": "scope-pkg",  # acceptable
                "description": "valid otherwise",
                "sources": [{"type": "documentation", "base_url": "https://x.io"}],
            }
        )
        client.call.side_effect = [bad, good]
        cfg = generate_config_with_ai(self._det(), client)
        assert cfg is not None
        assert cfg["name"] == "scope-pkg"
        assert client.call.call_count == 2


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
        # WS2: detected_version now lives under metadata.
        assert data["metadata"]["detected_version"] == "18.3.0"
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

        # Generated case — fresh out_dir so the cache shortcut doesn't fire.
        out_dir2 = tmp_path / "out2"
        out_dir2.mkdir()
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
                out_dir=out_dir2,
                client=MagicMock(),
                allow_network=True,
                allow_generate=True,
            )
        assert was_generated2 is True


class TestMaybePublish:
    """WS11: maybe_publish is now async. Tests drive it with asyncio.run.
    Patches target the async helpers (_submit_config, _prompt_async,
    _find_existing_issue) rather than the old _submit_config_sync."""

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

    def _async_mock(self, return_value=None, side_effect=None):
        """MagicMock that returns an awaitable resolving to return_value."""

        mock = MagicMock()

        async def _coro(*args, **kwargs):
            if side_effect is not None:
                if isinstance(side_effect, BaseException) or (
                    isinstance(side_effect, type) and issubclass(side_effect, BaseException)
                ):
                    raise side_effect
                return side_effect(*args, **kwargs)
            return return_value

        mock.side_effect = lambda *a, **kw: _coro(*a, **kw)
        return mock

    def _run(self, coro):
        import asyncio

        return asyncio.run(coro)

    def test_no_prompt_skips_entirely(self, tmp_path: Path):
        cfg = self._write_cfg(tmp_path, "newlib")
        submit = self._async_mock()

        with patch("skill_seekers.cli.scan_command._submit_config", submit):
            self._run(maybe_publish([cfg], skip_prompt=True))

        assert submit.call_count == 0

    def test_no_generated_configs_no_prompt(self, tmp_path: Path):
        submit = self._async_mock()
        prompt = self._async_mock()
        with (
            patch("skill_seekers.cli.scan_command._submit_config", submit),
            patch("skill_seekers.cli.scan_command._prompt_async", prompt),
        ):
            self._run(maybe_publish([], skip_prompt=False))
        assert prompt.call_count == 0
        assert submit.call_count == 0

    def test_yes_calls_submit_with_path(self, tmp_path: Path):
        cfg = self._write_cfg(tmp_path, "newlib")
        submit = self._async_mock(
            return_value={"ok": True, "message": "https://github.com/x/y/issues/1"}
        )
        prompt = self._async_mock(return_value="y")
        find = self._async_mock(return_value=None)  # no existing issue

        with (
            patch.dict("os.environ", {"GITHUB_TOKEN": "fake"}),
            patch("skill_seekers.cli.scan_command._submit_config", submit),
            patch("skill_seekers.cli.scan_command._prompt_async", prompt),
            patch("skill_seekers.cli.scan_command._find_existing_issue", find),
        ):
            self._run(maybe_publish([cfg], skip_prompt=False))

        assert submit.call_count == 1
        # Path passed as first positional arg
        args, _ = submit.call_args
        assert args[0] == cfg

    def test_no_does_not_call_submit(self, tmp_path: Path):
        cfg = self._write_cfg(tmp_path, "newlib")
        submit = self._async_mock()
        prompt = self._async_mock(return_value="n")
        find = self._async_mock(return_value=None)
        with (
            patch.dict("os.environ", {"GITHUB_TOKEN": "fake"}),
            patch("skill_seekers.cli.scan_command._submit_config", submit),
            patch("skill_seekers.cli.scan_command._prompt_async", prompt),
            patch("skill_seekers.cli.scan_command._find_existing_issue", find),
        ):
            self._run(maybe_publish([cfg], skip_prompt=False))
        assert submit.call_count == 0

    def test_missing_github_token_skips_prompt(self, tmp_path: Path, capsys):
        """Without GITHUB_TOKEN, don't ask 5 questions and fail 5 times."""
        cfg = self._write_cfg(tmp_path, "newlib")
        submit = self._async_mock()
        prompt = self._async_mock()
        with (
            patch("skill_seekers.cli.scan_command._submit_config", submit),
            patch.dict("os.environ", {}, clear=True),
            patch("skill_seekers.cli.scan_command._prompt_async", prompt),
        ):
            self._run(maybe_publish([cfg], skip_prompt=False))
        assert prompt.call_count == 0
        assert submit.call_count == 0
        captured = capsys.readouterr()
        assert "GITHUB_TOKEN" in captured.out

    def test_handles_submit_failure_gracefully(self, tmp_path: Path, capsys):
        cfg = self._write_cfg(tmp_path, "newlib")
        submit = self._async_mock(side_effect=RuntimeError("boom"))
        prompt = self._async_mock(return_value="y")
        find = self._async_mock(return_value=None)
        with (
            patch.dict("os.environ", {"GITHUB_TOKEN": "fake"}),
            patch("skill_seekers.cli.scan_command._submit_config", submit),
            patch("skill_seekers.cli.scan_command._prompt_async", prompt),
            patch("skill_seekers.cli.scan_command._find_existing_issue", find),
        ):
            self._run(maybe_publish([cfg], skip_prompt=False))
        captured = capsys.readouterr()
        assert "boom" in captured.out

    def test_idempotency_existing_issue_skips_submission(self, tmp_path: Path, capsys):
        """WS11: if an issue already exists, skip the prompt + submission."""
        cfg = self._write_cfg(tmp_path, "newlib")
        submit = self._async_mock()
        prompt = self._async_mock()
        find = self._async_mock(return_value="https://github.com/y/z/issues/42")

        with (
            patch.dict("os.environ", {"GITHUB_TOKEN": "fake"}),
            patch("skill_seekers.cli.scan_command._submit_config", submit),
            patch("skill_seekers.cli.scan_command._prompt_async", prompt),
            patch("skill_seekers.cli.scan_command._find_existing_issue", find),
        ):
            self._run(maybe_publish([cfg], skip_prompt=False))

        assert submit.call_count == 0  # no duplicate submission
        assert prompt.call_count == 0  # no prompt either
        captured = capsys.readouterr()
        assert "issues/42" in captured.out


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
        # WS2: detected_version now lives under metadata.
        assert data["metadata"]["detected_version"] == "0.1.0"

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


class TestArchiveRemovedConfigs:
    """WS10: stale configs move to .archived/<timestamp>/, not deleted."""

    def _setup_project(self, tmp_path: Path):
        proj = tmp_path / "p"
        proj.mkdir()
        (proj / "package.json").write_text('{"name": "p"}')
        out = tmp_path / "out"
        out.mkdir()
        return proj, out

    def _client_returning(self, names):
        client = MagicMock()
        client.call.return_value = json.dumps(
            [
                {
                    "name": n,
                    "ecosystem": "npm",
                    "version": "1.0.0",
                    "kind": "library",
                    "confidence": 0.9,
                    "evidence": "x",
                }
                for n in names
            ]
        )
        return client

    def test_removed_config_is_archived_not_deleted(self, tmp_path: Path):
        proj, out = self._setup_project(tmp_path)
        # Simulate a prior scan that emitted moment.json + react.json
        stale = out / "moment.json"
        stale.write_text(json.dumps({"name": "moment", "metadata": {"detected_version": "2.0.0"}}))
        keep = out / "react.json"
        keep.write_text(json.dumps({"name": "react", "metadata": {"detected_version": "18.0.0"}}))

        # New scan detects only react → moment should be archived.
        client = self._client_returning(["react"])
        with patch(
            "skill_seekers.cli.scan_command.resolve_config_path",
            return_value=keep,
        ):
            result = run_scan(
                proj,
                out,
                agent_client=client,
                allow_network=True,
                allow_generate=False,
                skip_publish=True,
                min_confidence=0.4,
            )

        # moment.json no longer in out/, but exists in .archived/<ts>/
        assert not stale.exists()
        archived_root = out / ".archived"
        assert archived_root.is_dir()
        # Exactly one timestamped subdir, containing moment.json
        ts_dirs = list(archived_root.iterdir())
        assert len(ts_dirs) == 1
        archived_files = list(ts_dirs[0].iterdir())
        assert any(f.name == "moment.json" for f in archived_files)
        # ScanResult.archived reflects the move
        assert len(result.archived) == 1
        assert result.archived[0].name == "moment.json"

    def test_no_removed_means_no_archive_dir(self, tmp_path: Path):
        proj, out = self._setup_project(tmp_path)
        keep = out / "react.json"
        keep.write_text(json.dumps({"name": "react", "metadata": {"detected_version": "18.0.0"}}))

        client = self._client_returning(["react"])
        with patch("skill_seekers.cli.scan_command.resolve_config_path", return_value=keep):
            result = run_scan(
                proj,
                out,
                agent_client=client,
                allow_network=True,
                allow_generate=False,
                skip_publish=True,
                min_confidence=0.4,
            )

        assert result.archived == []
        assert not (out / ".archived").exists()

    def test_dry_run_does_not_archive(self, tmp_path: Path):
        proj, out = self._setup_project(tmp_path)
        stale = out / "moment.json"
        stale.write_text(json.dumps({"name": "moment", "metadata": {"detected_version": "2.0.0"}}))

        client = self._client_returning(["react"])
        with patch("skill_seekers.cli.scan_command.resolve_config_path", return_value=None):
            run_scan(
                proj,
                out,
                agent_client=client,
                allow_network=True,
                allow_generate=False,
                skip_publish=True,
                min_confidence=0.4,
                dry_run=True,
            )

        # Stale file still in place; nothing was actually moved.
        assert stale.exists()
        assert not (out / ".archived").exists()


class TestProbeUrls:
    """WS9: URL reachability probe for AI-generated configs."""

    def _det(self, name="newlib"):
        return Detection(
            name=name,
            ecosystem="npm",
            version="1.0.0",
            kind="library",
            confidence=0.9,
            evidence="x",
        )

    def _good_response(self):
        return json.dumps(
            {
                "name": "newlib",
                "description": "x",
                "base_url": "https://newlib.dev",
                "sources": [
                    {"type": "documentation", "base_url": "https://newlib.dev"},
                    {"type": "github", "repo": "owner/newlib"},
                ],
            }
        )

    def test_no_probe_skips_url_check(self):
        client = MagicMock()
        client.call.return_value = self._good_response()
        # No probe call expected — would normally fire httpx.
        with patch("httpx.Client") as httpx_mock:
            cfg = generate_config_with_ai(self._det(), client, probe_urls=False)
        assert cfg is not None
        httpx_mock.assert_not_called()

    def test_probe_passes_when_all_urls_ok(self):
        client = MagicMock()
        client.call.return_value = self._good_response()

        # Stub httpx so all HEADs return 200.
        good_resp = MagicMock()
        good_resp.status_code = 200
        with patch("httpx.Client") as httpx_cls:
            httpx_cls.return_value.__enter__.return_value.head.return_value = good_resp
            cfg = generate_config_with_ai(self._det(), client, probe_urls=True)
        assert cfg is not None
        # Should NOT have _url_unverified stamp when all URLs are good.
        assert "_url_unverified" not in cfg.get("metadata", {})

    def test_probe_falls_back_to_get_on_405(self):
        """Regression: some servers return 405 Method Not Allowed on HEAD even
        for valid URLs (older PyPI mirrors, Cloudflare-fronted sites). Probe
        must fall back to GET so real URLs aren't flagged as unreachable."""
        client = MagicMock()
        client.call.return_value = self._good_response()

        head_405 = MagicMock()
        head_405.status_code = 405
        get_200 = MagicMock()
        get_200.status_code = 200

        with patch("httpx.Client") as httpx_cls:
            instance = httpx_cls.return_value.__enter__.return_value
            instance.head.return_value = head_405
            instance.get.return_value = get_200
            cfg = generate_config_with_ai(self._det(), client, probe_urls=True)

        assert cfg is not None
        # Server returned 405 on HEAD, 200 on GET → URL is valid → no unverified stamp.
        assert "_url_unverified" not in cfg.get("metadata", {})
        # And GET WAS called (fallback fired).
        assert instance.get.called

    def test_probe_retries_on_bad_urls_then_succeeds(self):
        client = MagicMock()
        # First call returns config with bad URL, second returns config with good URL
        bad_response = json.dumps(
            {
                "name": "newlib",
                "description": "x",
                "base_url": "https://badurl.invalid",
                "sources": [{"type": "documentation", "base_url": "https://badurl.invalid"}],
            }
        )
        good_response = json.dumps(
            {
                "name": "newlib",
                "description": "x",
                "base_url": "https://newlib.dev",
                "sources": [{"type": "documentation", "base_url": "https://newlib.dev"}],
            }
        )
        client.call.side_effect = [bad_response, good_response]

        good_resp = MagicMock()
        good_resp.status_code = 200
        bad_resp = MagicMock()
        bad_resp.status_code = 404

        # First probe: 404. Second probe: 200.
        with patch("httpx.Client") as httpx_cls:
            instance = httpx_cls.return_value.__enter__.return_value
            instance.head.side_effect = [bad_resp, good_resp]
            cfg = generate_config_with_ai(self._det(), client, probe_urls=True)

        assert cfg is not None
        assert cfg["base_url"] == "https://newlib.dev"
        assert "_url_unverified" not in cfg.get("metadata", {})
        # Both attempts were made.
        assert client.call.call_count == 2

    def test_probe_stamps_unverified_when_retries_exhausted(self):
        client = MagicMock()
        # Both attempts return configs with bad URLs.
        bad_response = json.dumps(
            {
                "name": "newlib",
                "description": "x",
                "base_url": "https://badurl.invalid",
                "sources": [{"type": "documentation", "base_url": "https://badurl.invalid"}],
            }
        )
        client.call.side_effect = [bad_response, bad_response]

        bad_resp = MagicMock()
        bad_resp.status_code = 404
        with patch("httpx.Client") as httpx_cls:
            instance = httpx_cls.return_value.__enter__.return_value
            instance.head.return_value = bad_resp
            cfg = generate_config_with_ai(self._det(), client, probe_urls=True)

        # Returns config with _url_unverified stamped so user sees what to fix.
        assert cfg is not None
        assert "_url_unverified" in cfg["metadata"]
        assert "https://badurl.invalid" in cfg["metadata"]["_url_unverified"]


class TestMaxAiGenerationsCap:
    """WS8: cap unbounded AI generation so monorepos can't surprise-bill users."""

    def _make_project(self, tmp_path: Path) -> Path:
        proj = tmp_path / "p"
        proj.mkdir()
        (proj / "package.json").write_text('{"name": "p"}')
        return proj

    def test_cap_stops_ai_generation_after_n_calls(self, tmp_path: Path):
        """5 unmapped detections, cap=2 → only 2 generated, 3 listed as failed."""
        proj = self._make_project(tmp_path)
        out_dir = tmp_path / "out"

        # AI returns 5 detections, all with low canonical match → 5 unmapped.
        detections_json = json.dumps(
            [
                {
                    "name": f"unmapped{i}",
                    "ecosystem": "npm",
                    "version": "1.0.0",
                    "kind": "library",
                    "confidence": 0.9,
                    "evidence": "x",
                }
                for i in range(5)
            ]
        )

        gen_responses = [
            json.dumps(
                {
                    "name": f"unmapped{i}",
                    "description": "x",
                    "sources": [{"type": "documentation", "base_url": f"https://u{i}.dev"}],
                }
            )
            for i in range(5)
        ]

        client = MagicMock()
        client.call.side_effect = [detections_json] + gen_responses

        with patch("skill_seekers.cli.scan_command.resolve_config_path", return_value=None):
            result = run_scan(
                proj,
                out_dir,
                agent_client=client,
                allow_network=True,
                allow_generate=True,
                skip_publish=True,
                min_confidence=0.4,
                max_ai_generations=2,
            )

        assert len(result.generated) == 2
        assert len(result.failed) == 3

    def test_cap_zero_acts_as_no_generate(self, tmp_path: Path):
        proj = self._make_project(tmp_path)
        out_dir = tmp_path / "out"

        client = MagicMock()
        client.call.return_value = json.dumps(
            [
                {
                    "name": "x",
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
                allow_network=True,
                allow_generate=True,
                skip_publish=True,
                min_confidence=0.4,
                max_ai_generations=0,
            )

        assert len(result.generated) == 0
        assert result.failed == ["x"]


class TestDryRun:
    """WS8: dry-run previews scan output without writing or invoking AI generation."""

    def _make_project(self, tmp_path: Path) -> Path:
        proj = tmp_path / "p"
        proj.mkdir()
        (proj / "package.json").write_text('{"name": "p"}')
        return proj

    def test_dry_run_writes_nothing(self, tmp_path: Path):
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

        with patch("skill_seekers.cli.scan_command.resolve_config_path", return_value=None):
            result = run_scan(
                proj,
                out_dir,
                agent_client=client,
                allow_network=True,
                allow_generate=True,
                skip_publish=True,
                min_confidence=0.4,
                dry_run=True,
            )

        # Nothing on disk
        assert not out_dir.exists() or list(out_dir.iterdir()) == []
        # But preview paths populated for the report
        assert result.codebase_config is not None
        assert result.codebase_config.name == "p-codebase.json"
        # The 1 detection went into either generated or failed (preview)
        assert len(result.generated) + len(result.failed) == 1

    def test_dry_run_does_not_call_ai_generator(self, tmp_path: Path):
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

        gen_mock = MagicMock()
        with (
            patch("skill_seekers.cli.scan_command.resolve_config_path", return_value=None),
            patch("skill_seekers.cli.scan_command.generate_config_with_ai", gen_mock),
        ):
            run_scan(
                proj,
                out_dir,
                agent_client=client,
                allow_network=True,
                allow_generate=True,
                skip_publish=True,
                min_confidence=0.4,
                dry_run=True,
            )

        gen_mock.assert_not_called()


class TestExitCodeFor:
    """Non-zero exit code on complete failure — for CI shell pipelines."""

    def test_zero_when_codebase_emitted(self, tmp_path: Path):
        r = ScanResult(codebase_config=tmp_path / "x-codebase.json")
        assert _exit_code_for(r) == 0

    def test_zero_when_any_framework_emitted(self, tmp_path: Path):
        r = ScanResult(emitted=[tmp_path / "react.json"])
        assert _exit_code_for(r) == 0

    def test_one_when_nothing_emitted(self):
        r = ScanResult()
        assert _exit_code_for(r) == 1

    def test_one_when_only_failures(self):
        r = ScanResult(
            detections=[Detection("x", "npm", None, "library", 0.9, "")],
            failed=["x"],
        )
        assert _exit_code_for(r) == 1


class TestCliRegistration:
    def test_scan_is_registered_in_command_classes(self):
        """Scan uses the class-dispatch table (WS1) — no _reconstruct_argv hack."""
        from skill_seekers.cli.main import COMMAND_CLASSES

        assert COMMAND_CLASSES["scan"] == (
            "skill_seekers.cli.scan_command",
            "ScanCommand",
        )

    def test_scan_not_in_legacy_command_modules(self):
        """Scan should NOT appear in COMMAND_MODULES — that's the legacy table."""
        from skill_seekers.cli.main import COMMAND_MODULES

        assert "scan" not in COMMAND_MODULES

    def test_scan_command_class_consumes_args_namespace(self):
        """ScanCommand(args).execute() — no internal argparse re-parsing."""
        import argparse

        from skill_seekers.cli.scan_command import ScanCommand

        # Build a minimal namespace as the dispatcher would
        args = argparse.Namespace(
            directory="/does/not/exist",
            out="/tmp/whatever",
            no_fetch=True,
            no_generate=True,
            no_publish_prompt=True,
            agent=None,
            min_confidence=0.4,
            verbose=False,
        )
        cmd = ScanCommand(args)
        # Bad directory → returns 1 without raising
        assert cmd.execute() == 1

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


class TestCanonicalNameCandidates:
    """Real-world hit-rate: AI returns 'Godot Engine', preset is 'godot'."""

    def test_includes_original(self):
        cands = _canonical_name_candidates("Godot Engine")
        assert "Godot Engine" in cands

    def test_includes_lowercase(self):
        cands = _canonical_name_candidates("React")
        assert "react" in cands

    def test_includes_hyphenated_lowercase(self):
        cands = _canonical_name_candidates("Spring Boot")
        assert "spring-boot" in cands

    def test_strips_common_suffixes(self):
        # "Godot Engine" should produce "godot" as a fallback candidate.
        cands = _canonical_name_candidates("Godot Engine")
        assert "godot" in cands

        cands = _canonical_name_candidates("Tailwind CSS")
        assert "tailwind" in cands

        cands = _canonical_name_candidates("Vue.js")
        assert "vue" in cands

    def test_strips_chinese_suffixes(self):
        """WS7: half the user base is CJK; suffixes must work there too."""
        # Godot in Chinese — should still resolve to "godot" after stripping.
        cands = _canonical_name_candidates("Godot 引擎")
        assert "godot" in cands

        cands = _canonical_name_candidates("React 框架")
        assert "react" in cands

        # Traditional Chinese variant
        cands = _canonical_name_candidates("Vue 函式庫")
        assert "vue" in cands

    def test_strips_korean_suffixes(self):
        cands = _canonical_name_candidates("Godot 엔진")
        assert "godot" in cands

        cands = _canonical_name_candidates("React 프레임워크")
        assert "react" in cands

    def test_strips_japanese_suffixes(self):
        cands = _canonical_name_candidates("Godot エンジン")
        assert "godot" in cands

        cands = _canonical_name_candidates("React フレームワーク")
        assert "react" in cands

        cands = _canonical_name_candidates("Lodash ライブラリ")
        assert "lodash" in cands

    def test_strips_european_language_suffixes(self):
        """Spanish/French/Portuguese/German — common in EU/LATAM user base."""
        # Spanish "motor" (engine)
        cands = _canonical_name_candidates("Godot motor")
        assert "godot" in cands

        # French "cadre" (framework)
        cands = _canonical_name_candidates("React cadre")
        assert "react" in cands

        # German "bibliothek" (library) — lowercased before matching
        cands = _canonical_name_candidates("Lodash Bibliothek")
        assert "lodash" in cands

    def test_npm_scoped_package_unscoped_form(self):
        cands = _canonical_name_candidates("@anthropic-ai/sdk")
        # Both the full scoped name and a slugified unscoped form should appear.
        assert "@anthropic-ai/sdk" in cands
        # The slash gets normalized to a hyphen for filename-safe lookups.
        assert any("anthropic-ai-sdk" in c or "anthropic-sdk" in c for c in cands)

    def test_ordered_so_exact_match_wins(self):
        """Original input must come first so an existing exact-match preset
        beats any normalized fallback."""
        cands = _canonical_name_candidates("ReactQuery")
        assert cands[0] == "ReactQuery"

    def test_no_duplicates(self):
        cands = _canonical_name_candidates("react")
        assert len(cands) == len(set(cands))

    def test_whitespace_input_returns_unchanged_singleton(self):
        """Pure-whitespace input is returned as a one-element list (no crash,
        no candidate generation since there's nothing to canonicalize)."""
        assert _canonical_name_candidates("   ") == ["   "]

    def test_empty_string_returns_empty_list(self):
        """An empty string has no candidates — returns []."""
        assert _canonical_name_candidates("") == []


class TestResolverUsesCanonicalCandidates:
    """The resolver should try each canonical candidate against resolve_config_path."""

    def _det(self, name: str):
        return Detection(
            name=name,
            ecosystem="other",
            version="4.7",
            kind="framework",
            confidence=1.0,
            evidence="",
        )

    def test_resolver_tries_canonical_form_when_exact_misses(self, tmp_path: Path):
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        canonical_match = tmp_path / "godot.json"
        canonical_match.write_text(
            json.dumps(
                {
                    "name": "godot",
                    "description": "godot",
                    "sources": [
                        {"type": "documentation", "base_url": "https://docs.godotengine.org"}
                    ],
                }
            )
        )

        # First call (exact "Godot Engine.json") returns None; eventually the
        # canonical candidate "godot.json" hits. Resolver appends .json to
        # every candidate so local repo / user dir lookups actually find files.
        def fake_resolve(name, auto_fetch=True, fetch_destination="configs"):  # noqa: ARG001 — mirrors real signature
            return canonical_match if name == "godot.json" else None

        with patch("skill_seekers.cli.scan_command.resolve_config_path", side_effect=fake_resolve):
            from skill_seekers.cli.scan_command import resolve_or_generate_with_status

            path, was_generated = resolve_or_generate_with_status(
                self._det("Godot Engine"),
                out_dir=out_dir,
                client=MagicMock(),
                allow_network=True,
                allow_generate=False,
            )

        assert path is not None
        assert was_generated is False
        # Emitted config name should reflect the *detection* name (slugified for
        # filesystem), not the canonical name — so it stays stable on re-scan.
        # The content includes the resolved canonical config plus detected_version
        # (WS2: nested under metadata).
        data = json.loads(path.read_text())
        assert data["metadata"]["detected_version"] == "4.7"

    def test_resolver_appends_json_suffix_for_local_lookup(self, tmp_path: Path):
        """Regression: resolve_config_path checks for files literally — without
        '.json' appended, local repo configs/ and user-dir configs/ are missed.
        """
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        seen: list[str] = []

        def fake_resolve(name, auto_fetch=True, fetch_destination="configs"):  # noqa: ARG001 — mirrors real signature
            seen.append(name)
            return None

        with patch("skill_seekers.cli.scan_command.resolve_config_path", side_effect=fake_resolve):
            from skill_seekers.cli.scan_command import resolve_or_generate_with_status

            resolve_or_generate_with_status(
                self._det("react"),
                out_dir=out_dir,
                client=MagicMock(),
                allow_network=True,
                allow_generate=False,
            )

        assert seen, "resolve_config_path was never called"
        assert all(name.endswith(".json") for name in seen), (
            f"Resolver should append .json to every lookup; got {seen}"
        )

    def test_resolver_reuses_existing_out_dir_config(self, tmp_path: Path):
        """Re-scan should re-use the prior-emitted config (just re-stamp version),
        not waste an AI/API call and not blow away user edits."""
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        existing = out_dir / "react.json"
        existing.write_text(
            json.dumps(
                {
                    "name": "react",
                    "description": "User-edited description",
                    "sources": [{"type": "documentation", "base_url": "https://react.dev"}],
                    "detected_version": "18.2.0",
                    "_user_notes": "Don't overwrite me",  # simulates a manual edit
                }
            )
        )

        resolve_mock = MagicMock(return_value=None)
        gen_mock = MagicMock(return_value={})
        with (
            patch("skill_seekers.cli.scan_command.resolve_config_path", resolve_mock),
            patch("skill_seekers.cli.scan_command.generate_config_with_ai", gen_mock),
        ):
            from skill_seekers.cli.scan_command import resolve_or_generate_with_status

            path, was_generated = resolve_or_generate_with_status(
                self._det("react"),  # version="4.7" — different from existing 18.2.0
                out_dir=out_dir,
                client=MagicMock(),
                allow_network=True,
                allow_generate=True,
            )

        assert path == existing
        assert was_generated is False
        # Resolver and generator should NOT have been called when cache hit.
        resolve_mock.assert_not_called()
        gen_mock.assert_not_called()
        # User edits preserved; version re-stamped (WS2: under metadata).
        data = json.loads(existing.read_text())
        assert data["_user_notes"] == "Don't overwrite me"
        assert data["description"] == "User-edited description"
        assert data["metadata"]["detected_version"] == "4.7"

    def test_resolver_returns_none_when_no_candidate_hits(self, tmp_path: Path):
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        with patch("skill_seekers.cli.scan_command.resolve_config_path", return_value=None):
            from skill_seekers.cli.scan_command import resolve_or_generate_with_status

            path, _ = resolve_or_generate_with_status(
                self._det("SomeNonsenseLib"),
                out_dir=out_dir,
                client=MagicMock(),
                allow_network=True,
                allow_generate=False,
            )
        assert path is None

    def test_resolver_preserves_preexisting_user_config_in_out_dir(self, tmp_path: Path):
        """Regression: with out_dir == ./configs, resolve_config_path's
        CWD-relative 'configs/' lookup can return a user-managed file that
        already lives inside out_dir under a different slug (configs/godot.json
        for the godot-engine.json target). The intermediate cleanup must not
        delete a file this run did not create — copy, never move."""
        out_dir = tmp_path / "configs"
        out_dir.mkdir()
        user_config = out_dir / "godot.json"
        user_config.write_text(
            json.dumps(
                {
                    "name": "godot",
                    "description": "Hand-maintained by the user",
                    "sources": [
                        {"type": "documentation", "base_url": "https://docs.godotengine.org"}
                    ],
                }
            )
        )

        def fake_resolve(name, auto_fetch=True, fetch_destination="configs"):  # noqa: ARG001 — mirrors real signature
            # Simulates step 2 of resolve_config_path: the CWD-relative
            # configs/ lookup returns the user's pre-existing file (no fetch).
            return user_config.resolve() if name == "godot.json" else None

        with patch("skill_seekers.cli.scan_command.resolve_config_path", side_effect=fake_resolve):
            from skill_seekers.cli.scan_command import resolve_or_generate_with_status

            path, was_generated = resolve_or_generate_with_status(
                self._det("Godot Engine"),
                out_dir=out_dir,
                client=MagicMock(),
                allow_network=True,
                allow_generate=False,
            )

        assert path == out_dir / "godot-engine.json"
        assert was_generated is False
        # The user's hand-maintained file must survive untouched.
        assert user_config.exists(), "pre-existing user config was deleted by the scan"
        data = json.loads(user_config.read_text())
        assert data["description"] == "Hand-maintained by the user"

    def test_resolver_still_removes_fetched_intermediate_in_out_dir(self, tmp_path: Path):
        """The intermediate cleanup still applies to canonical-named files the
        resolve step itself fetched into out_dir during this run — otherwise
        they show up as phantom 'removed' configs on the next scan."""
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        def fake_resolve(name, auto_fetch=True, fetch_destination="configs"):  # noqa: ARG001 — mirrors real signature
            if name != "godot.json":
                return None
            # Simulates the API fetch landing godot.json inside out_dir.
            fetched = Path(fetch_destination) / "godot.json"
            fetched.write_text(
                json.dumps(
                    {
                        "name": "godot",
                        "description": "fetched",
                        "sources": [
                            {"type": "documentation", "base_url": "https://docs.godotengine.org"}
                        ],
                    }
                )
            )
            return fetched.resolve()

        with patch("skill_seekers.cli.scan_command.resolve_config_path", side_effect=fake_resolve):
            from skill_seekers.cli.scan_command import resolve_or_generate_with_status

            path, _ = resolve_or_generate_with_status(
                self._det("Godot Engine"),
                out_dir=out_dir,
                client=MagicMock(),
                allow_network=True,
                allow_generate=False,
            )

        assert path == out_dir / "godot-engine.json"
        assert path.exists()
        assert not (out_dir / "godot.json").exists(), (
            "fetched intermediate should be removed to avoid phantom-removed churn"
        )


class TestGenerateSchemaHintDepth:
    """Regression for SCAN-01: the AI schema hint's ``code_analysis_depth`` must
    be a value the validator accepts. Otherwise every github config the AI
    faithfully generates from the hint is rejected by UniSkillConfigValidator
    and the scan never produces an AI-generated config."""

    def test_schema_hint_depth_is_a_valid_level(self):
        import re

        from skill_seekers.cli.config_validator import UniSkillConfigValidator
        from skill_seekers.cli.scan_command import _GENERATE_SCHEMA_HINT

        match = re.search(r'"code_analysis_depth":\s*"([^"]+)"', _GENERATE_SCHEMA_HINT)
        assert match, "schema hint no longer advertises code_analysis_depth"
        assert match.group(1) in UniSkillConfigValidator.VALID_DEPTH_LEVELS
