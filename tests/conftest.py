"""
Pytest configuration for tests.

Configures anyio to only use asyncio backend (not trio).
Checks that the skill_seekers package is installed before running tests.
"""

import sys

import pytest


def pytest_configure(config):  # noqa: ARG001
    """Check if package is installed before running tests."""
    try:
        import skill_seekers  # noqa: F401
    except ModuleNotFoundError:
        print("\n" + "=" * 70)
        print("ERROR: skill_seekers package not installed")
        print("=" * 70)
        print("\nPlease install the package in editable mode first:")
        print("  pip install -e .")
        print("\nOr activate your virtual environment if you already installed it.")
        print("=" * 70 + "\n")
        sys.exit(1)


@pytest.fixture(scope="session")
def anyio_backend():
    """Override anyio backend to only use asyncio (not trio)."""
    return "asyncio"


@pytest.fixture(autouse=True)
def _isolate_user_config(monkeypatch, tmp_path_factory):
    """Never let a developer's real ~/.config/skill-seekers/config.json leak into tests.

    ExecutionContext now reads the user's default enhancement level from it,
    so a machine with `default_enhance_level: 1` persisted would fail every
    "default is 2" assertion. Tests that need a user config point
    ConfigManager.CONFIG_FILE at their own file.
    """
    from skill_seekers.cli.config_manager import ConfigManager

    monkeypatch.setattr(
        ConfigManager, "CONFIG_FILE", tmp_path_factory.mktemp("user-config") / "config.json"
    )


@pytest.fixture(autouse=True)
def _reset_execution_context():
    """Reset the ExecutionContext singleton before and after every test.

    Without this, a test that calls ExecutionContext.initialize() poisons
    all subsequent tests in the same process.
    """
    from skill_seekers.cli.execution_context import ExecutionContext

    ExecutionContext.reset()
    yield
    ExecutionContext.reset()


@pytest.fixture(scope="session")
def bootstrap_artifact(tmp_path_factory):
    """Run the real bootstrap once against an isolated, representative project.

    Never sync dependencies or analyze the developer checkout during tests.
    The shared artifact is read-only; consumers put their own outputs in tmp_path.
    """
    import os
    from pathlib import Path
    from tests.subprocess_helpers import run_process_tree

    base = tmp_path_factory.mktemp("bootstrap")
    source = base / "sample"
    source.mkdir()
    (source / "README.md").write_text(
        "# Sample service\n\nA small service with reusable API methods.\n"
    )
    (source / "service.py").write_text(
        '"""Example service API."""\n'
        + "\n".join(
            f'def operation_{i}(value: str) -> str:\n    """Normalize a value for operation {i}."""\n    return value.strip()\n'
            for i in range(8)
        )
    )
    (source / "test_service.py").write_text(
        '"""Service usage examples."""\nfrom service import operation_0\n'
        'def test_normalize():\n    assert operation_0(" demo ") == "demo"\n'
    )
    output = base / "skill-seekers"
    repo = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo / "src") + os.pathsep + env.get("PYTHONPATH", "")
    result = run_process_tree(
        [
            "bash",
            str(repo / "scripts/bootstrap_skill.sh"),
            "--source",
            str(source),
            "--output",
            str(output),
            "--no-sync",
            "--enhance-level",
            "0",
            "--python",
            sys.executable,
        ],
        cwd=base,
        env=env,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result, output


@pytest.fixture(autouse=True)
def _reject_unmocked_agent_processes(monkeypatch):
    """Fail at the subprocess boundary instead of launching installed AI agents."""
    import os
    import shlex
    import subprocess
    from pathlib import Path

    original = subprocess.Popen
    agents = {"claude", "codex", "gemini", "opencode", "kimi", "qwen", "aider"}

    class TestPopen(original):
        def __init__(self, args, *positional, **kwargs):
            if isinstance(args, (str, bytes)):
                argv = shlex.split(os.fsdecode(args))
            elif isinstance(args, os.PathLike):
                argv = [args]
            else:
                argv = args
            if argv:
                executable = os.fsdecode(kwargs.get("executable") or argv[0])
                name = Path(executable).name.removesuffix(".exe")
                if name in agents or (name == "gh" and len(argv) > 1 and argv[1] == "copilot"):
                    pytest.fail(
                        f"Test attempted to launch real agent {name!r}; "
                        "mock the subprocess boundary or disable AI enhancement."
                    )
            super().__init__(args, *positional, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", TestPopen)
