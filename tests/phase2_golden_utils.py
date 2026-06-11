"""Golden-output harness for the Phase 2 DocumentSkillBuilder refactor.

Protocol: BEFORE porting a scraper to DocumentSkillBuilder, its golden tree is
captured from the pre-refactor code (`UPDATE_GOLDENS=1 pytest <test>`), and
committed under tests/golden/phase2/<name>/. AFTER the port, the same test
runs in compare mode and fails on ANY byte difference — proving the port is
output-identical.

Run with UPDATE_GOLDENS=1 only on purpose (it rewrites the committed goldens).
"""

import os
import shutil
from pathlib import Path

GOLDEN_ROOT = Path(__file__).parent / "golden" / "phase2"


def build_snapshot(converter, build=None):
    """Run the converter's build and return {relpath: bytes} of skill_dir."""
    (build or converter.build_skill)()
    skill_dir = Path(converter.skill_dir)
    snapshot = {}
    for path in sorted(skill_dir.rglob("*")):
        if path.is_file():
            snapshot[str(path.relative_to(skill_dir))] = path.read_bytes()
    return snapshot


def assert_matches_golden(snapshot: dict, name: str):
    """Compare a snapshot against tests/golden/phase2/<name>/ (or update it)."""
    golden_dir = GOLDEN_ROOT / name

    if os.environ.get("UPDATE_GOLDENS") == "1":
        if golden_dir.exists():
            shutil.rmtree(golden_dir)
        for rel, data in snapshot.items():
            target = golden_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        return

    assert golden_dir.exists(), (
        f"No golden tree for '{name}'. Capture it from the PRE-refactor code "
        f"with: UPDATE_GOLDENS=1 pytest <this test>"
    )
    golden = {
        str(p.relative_to(golden_dir)): p.read_bytes()
        for p in sorted(golden_dir.rglob("*"))
        if p.is_file()
    }
    assert set(snapshot) == set(golden), (
        f"File set differs for '{name}'.\n"
        f"  missing: {sorted(set(golden) - set(snapshot))}\n"
        f"  extra:   {sorted(set(snapshot) - set(golden))}"
    )
    for rel in sorted(golden):
        if snapshot[rel] != golden[rel]:
            new = snapshot[rel].decode("utf-8", errors="replace").splitlines()
            old = golden[rel].decode("utf-8", errors="replace").splitlines()
            import difflib

            diff = "\n".join(difflib.unified_diff(old, new, f"golden/{rel}", f"built/{rel}"))
            raise AssertionError(f"Output changed for '{name}' at {rel}:\n{diff}")
