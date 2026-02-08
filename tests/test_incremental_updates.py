#!/usr/bin/env python3
"""
Tests for incremental update functionality.

Validates:
- Change detection (add/modify/delete)
- Version tracking
- Update package generation
- Diff report generation
- Update application
"""

import pytest
from pathlib import Path
import sys
import tempfile
import json
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from skill_seekers.cli.incremental_updater import IncrementalUpdater


@pytest.fixture
def temp_skill_dir():
    """Create temporary skill directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "test_skill"
        skill_dir.mkdir()

        # Create SKILL.md
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text("# Test Skill\n\nInitial content")

        # Create references
        refs_dir = skill_dir / "references"
        refs_dir.mkdir()

        ref1 = refs_dir / "getting_started.md"
        ref1.write_text("# Getting Started\n\nInitial guide")

        yield skill_dir


def test_initial_scan_all_added(temp_skill_dir):
    """Test first scan treats all files as added."""
    updater = IncrementalUpdater(temp_skill_dir)

    change_set = updater.detect_changes()

    # First scan - everything is "added"
    assert len(change_set.added) == 2  # SKILL.md + 1 ref
    assert len(change_set.modified) == 0
    assert len(change_set.deleted) == 0
    assert change_set.has_changes
    assert change_set.total_changes == 2


def test_no_changes_after_save(temp_skill_dir):
    """Test no changes detected after saving versions."""
    updater = IncrementalUpdater(temp_skill_dir)

    # First scan
    updater.detect_changes()
    updater.save_current_versions()

    # Second scan (no changes)
    updater2 = IncrementalUpdater(temp_skill_dir)
    change_set2 = updater2.detect_changes()

    assert len(change_set2.added) == 0
    assert len(change_set2.modified) == 0
    assert len(change_set2.deleted) == 0
    assert len(change_set2.unchanged) == 2
    assert not change_set2.has_changes


def test_detect_modified_file(temp_skill_dir):
    """Test detection of modified files."""
    updater = IncrementalUpdater(temp_skill_dir)

    # Initial scan and save
    updater.detect_changes()
    updater.save_current_versions()

    # Modify a file
    time.sleep(0.01)  # Ensure timestamp changes
    skill_md = temp_skill_dir / "SKILL.md"
    skill_md.write_text("# Test Skill\n\nModified content")

    # Detect changes
    updater2 = IncrementalUpdater(temp_skill_dir)
    change_set = updater2.detect_changes()

    assert len(change_set.modified) == 1
    assert len(change_set.added) == 0
    assert len(change_set.deleted) == 0
    assert change_set.modified[0].file_path == "SKILL.md"
    assert change_set.modified[0].version == 2  # Incremented


def test_detect_added_file(temp_skill_dir):
    """Test detection of new files."""
    updater = IncrementalUpdater(temp_skill_dir)

    # Initial scan and save
    updater.detect_changes()
    updater.save_current_versions()

    # Add new file
    refs_dir = temp_skill_dir / "references"
    new_ref = refs_dir / "api_reference.md"
    new_ref.write_text("# API Reference\n\nNew documentation")

    # Detect changes
    updater2 = IncrementalUpdater(temp_skill_dir)
    change_set = updater2.detect_changes()

    assert len(change_set.added) == 1
    assert len(change_set.modified) == 0
    assert len(change_set.deleted) == 0
    assert change_set.added[0].file_path == "references/api_reference.md"


def test_detect_deleted_file(temp_skill_dir):
    """Test detection of deleted files."""
    updater = IncrementalUpdater(temp_skill_dir)

    # Initial scan and save
    updater.detect_changes()
    updater.save_current_versions()

    # Delete a file
    ref_file = temp_skill_dir / "references" / "getting_started.md"
    ref_file.unlink()

    # Detect changes
    updater2 = IncrementalUpdater(temp_skill_dir)
    change_set = updater2.detect_changes()

    assert len(change_set.deleted) == 1
    assert len(change_set.added) == 0
    assert len(change_set.modified) == 0
    assert "references/getting_started.md" in change_set.deleted


def test_mixed_changes(temp_skill_dir):
    """Test detection of multiple types of changes."""
    updater = IncrementalUpdater(temp_skill_dir)

    # Initial scan and save
    updater.detect_changes()
    updater.save_current_versions()

    # Make mixed changes
    time.sleep(0.01)

    # Modify SKILL.md
    (temp_skill_dir / "SKILL.md").write_text("# Test Skill\n\nModified")

    # Add new file
    refs_dir = temp_skill_dir / "references"
    (refs_dir / "new_file.md").write_text("# New File")

    # Delete existing file
    (refs_dir / "getting_started.md").unlink()

    # Detect changes
    updater2 = IncrementalUpdater(temp_skill_dir)
    change_set = updater2.detect_changes()

    assert len(change_set.modified) == 1
    assert len(change_set.added) == 1
    assert len(change_set.deleted) == 1
    assert change_set.total_changes == 3


def test_generate_update_package(temp_skill_dir):
    """Test update package generation."""
    updater = IncrementalUpdater(temp_skill_dir)

    # Initial scan
    updater.detect_changes()
    updater.save_current_versions()

    # Make a change
    time.sleep(0.01)
    (temp_skill_dir / "SKILL.md").write_text("# Modified")

    # Detect and package
    updater2 = IncrementalUpdater(temp_skill_dir)
    change_set = updater2.detect_changes()

    with tempfile.TemporaryDirectory() as tmpdir:
        package_path = Path(tmpdir) / "update.json"
        result_path = updater2.generate_update_package(change_set, package_path)

        assert result_path.exists()

        # Validate package structure
        package_data = json.loads(result_path.read_text())

        assert "metadata" in package_data
        assert "changes" in package_data
        assert package_data["metadata"]["total_changes"] == 1
        assert "SKILL.md" in package_data["changes"]
        assert package_data["changes"]["SKILL.md"]["action"] == "modify"


def test_diff_report_generation(temp_skill_dir):
    """Test diff report generation."""
    updater = IncrementalUpdater(temp_skill_dir)

    # Initial scan and save
    updater.detect_changes()
    updater.save_current_versions()

    # Make changes
    time.sleep(0.01)
    (temp_skill_dir / "SKILL.md").write_text("# Modified content")

    # Generate report
    updater2 = IncrementalUpdater(temp_skill_dir)
    change_set = updater2.detect_changes()
    report = updater2.generate_diff_report(change_set)

    assert "INCREMENTAL UPDATE REPORT" in report
    assert "Modified: 1 files" in report
    assert "SKILL.md" in report


def test_version_increment(temp_skill_dir):
    """Test version numbers increment correctly."""
    updater = IncrementalUpdater(temp_skill_dir)

    # Initial scan
    change_set1 = updater.detect_changes()
    updater.save_current_versions()

    # All files should be version 1
    for doc in change_set1.added:
        assert doc.version == 1

    # Modify and check version increments
    time.sleep(0.01)
    (temp_skill_dir / "SKILL.md").write_text("Modified once")

    updater2 = IncrementalUpdater(temp_skill_dir)
    change_set2 = updater2.detect_changes()
    updater2.save_current_versions()

    assert change_set2.modified[0].version == 2

    # Modify again
    time.sleep(0.01)
    (temp_skill_dir / "SKILL.md").write_text("Modified twice")

    updater3 = IncrementalUpdater(temp_skill_dir)
    change_set3 = updater3.detect_changes()

    assert change_set3.modified[0].version == 3


def test_apply_update_package(temp_skill_dir):
    """Test applying an update package."""
    # Create initial state
    updater = IncrementalUpdater(temp_skill_dir)
    updater.detect_changes()
    updater.save_current_versions()

    # Create update package manually
    with tempfile.TemporaryDirectory() as tmpdir:
        package_path = Path(tmpdir) / "update.json"

        update_data = {
            "metadata": {
                "timestamp": "2026-02-05T12:00:00",
                "skill_name": "test_skill",
                "change_summary": {"modified": 1},
                "total_changes": 1,
            },
            "changes": {
                "SKILL.md": {
                    "action": "modify",
                    "version": 2,
                    "content": "# Updated Content\n\nApplied from package",
                }
            },
        }

        package_path.write_text(json.dumps(update_data))

        # Apply update
        success = updater.apply_update_package(package_path)

        assert success
        assert (
            temp_skill_dir / "SKILL.md"
        ).read_text() == "# Updated Content\n\nApplied from package"


def test_content_hash_consistency(temp_skill_dir):
    """Test content hash is consistent for same content."""
    updater = IncrementalUpdater(temp_skill_dir)

    # Get hash
    skill_md = temp_skill_dir / "SKILL.md"
    hash1 = updater._compute_file_hash(skill_md)

    # Read and rewrite same content
    content = skill_md.read_text()
    skill_md.write_text(content)

    hash2 = updater._compute_file_hash(skill_md)

    # Hashes should be identical
    assert hash1 == hash2


def test_empty_skill_directory():
    """Test handling empty skill directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        empty_dir = Path(tmpdir) / "empty"
        empty_dir.mkdir()

        updater = IncrementalUpdater(empty_dir)
        change_set = updater.detect_changes()

        assert len(change_set.added) == 0
        assert len(change_set.modified) == 0
        assert len(change_set.deleted) == 0
        assert not change_set.has_changes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
