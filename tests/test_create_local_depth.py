#!/usr/bin/env python3
"""A bare `create ./path` should produce a real analysis by default.

Regression: local create defaulted to ``surface`` depth, which skips per-file
AST analysis. The result was an empty ``code_analysis.json`` and a misleading
"Found N source files / Successfully analyzed 0 files" log, while a skill built
from a scan-emitted config (which defaults to deep) had a full API reference.
Local create now defaults to ``deep`` and still honors an explicit ``--depth``.
"""

import argparse

import pytest

from skill_seekers.cli.arguments.create import get_create_defaults
from skill_seekers.cli.create_command import CreateCommand
from skill_seekers.cli.execution_context import ExecutionContext
from skill_seekers.cli.source_detector import SourceInfo


def _local_command(directory, **overrides):
    defaults = get_create_defaults()
    defaults.update({"name": "mylib"})
    defaults.update(overrides)
    args = argparse.Namespace(**defaults)
    cmd = CreateCommand(args)
    cmd.source_info = SourceInfo(
        type="local",
        parsed={"directory": str(directory)},
        suggested_name="mylib",
        raw_input=str(directory),
    )
    ExecutionContext.reset()
    ExecutionContext.initialize(args=args, config_path=None, source_info=cmd.source_info)
    return cmd


@pytest.fixture(autouse=True)
def _reset_context():
    yield
    ExecutionContext.reset()


def test_local_create_defaults_to_deep(tmp_path):
    cmd = _local_command(tmp_path, depth=None)
    config = cmd._build_config("local", ExecutionContext.get())
    assert config["depth"] == "deep"


def test_local_create_respects_explicit_surface(tmp_path):
    cmd = _local_command(tmp_path, depth="surface")
    config = cmd._build_config("local", ExecutionContext.get())
    assert config["depth"] == "surface"
