#!/usr/bin/env python3
"""
Tests for architectural_pattern_detector.py - Framework detection.

Regression tests for:
- Issue #365: Unity C# projects misidentified as Unreal
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from skill_seekers.cli.architectural_pattern_detector import ArchitecturalPatternDetector


@pytest.fixture
def detector():
    return ArchitecturalPatternDetector(enhance_with_ai=False)


def _unity_files(root: str) -> list[dict]:
    """Simulate files_analysis for a Unity C# project."""
    return [
        {
            "file": f"{root}/Assets/Scripts/Player.cs",
            "language": "C#",
            "imports": ["UnityEngine", "UnityEngine.UI", "System.Collections"],
        },
        {
            "file": f"{root}/Assets/Scripts/GameManager.cs",
            "language": "C#",
            "imports": ["UnityEngine", "Zenject"],
        },
        {
            "file": f"{root}/Assets/Scripts/Enemy.cs",
            "language": "C#",
            "imports": ["UnityEngine", "System.Collections.Generic"],
        },
    ]


def _make_unity_dir(tmp_path: Path) -> Path:
    """Create a minimal Unity project directory structure."""
    (tmp_path / "Assets").mkdir()
    (tmp_path / "Library").mkdir()
    (tmp_path / "Packages").mkdir()
    (tmp_path / "ProjectSettings").mkdir()
    (tmp_path / "Packages" / "manifest.json").write_text(
        '{"dependencies": {"com.unity.2d.sprite": "1.0.0"}}'
    )
    (tmp_path / "ProjectSettings" / "ProjectVersion.txt").write_text("m_EditorVersion: 2022.3.10f1")
    return tmp_path


class TestUnityFrameworkDetection:
    """Regression tests for Unity vs Unreal framework detection (Issue #365)."""

    def test_unity_detected_via_imports(self, detector, tmp_path):
        """Unity project is detected correctly when C# files import UnityEngine."""
        root = str(tmp_path)
        _make_unity_dir(tmp_path)
        files = _unity_files(root)

        frameworks = detector._detect_frameworks(tmp_path, files)

        assert "Unity" in frameworks, f"Expected Unity, got {frameworks}"
        assert "Unreal" not in frameworks, f"Unreal should not be detected: {frameworks}"

    def test_unity_not_misidentified_as_unreal_with_source_dir(self, detector, tmp_path):
        """Unity project with a 'Source' subfolder must NOT be identified as Unreal (Issue #365)."""
        root = str(tmp_path)
        _make_unity_dir(tmp_path)
        # Simulate the common pattern: Assets/Scripts/Source/... exists
        source_dir = tmp_path / "Assets" / "Scripts" / "Source"
        source_dir.mkdir(parents=True)

        files = _unity_files(root)
        # Add a file whose path contains 'Source/' (the false-positive trigger for Unreal)
        files.append(
            {
                "file": f"{root}/Assets/Scripts/Source/Utilities.cs",
                "language": "C#",
                "imports": ["UnityEngine", "System"],
            }
        )

        frameworks = detector._detect_frameworks(tmp_path, files)

        assert "Unity" in frameworks, f"Expected Unity, got {frameworks}"
        assert "Unreal" not in frameworks, f"Unreal falsely detected: {frameworks}"

    def test_unreal_project_still_detected(self, detector, tmp_path):
        """Genuine Unreal projects are still identified correctly."""
        (tmp_path / "Source").mkdir()
        (tmp_path / "Binaries").mkdir()
        (tmp_path / "Content").mkdir()
        (tmp_path / "Config").mkdir()
        (tmp_path / "MyGame.uproject").write_text('{"FileVersion": 3}')

        files = [
            {
                "file": f"{tmp_path}/Source/MyGame/MyGameCharacter.cpp",
                "language": "C++",
                "imports": [],
            },
            {
                "file": f"{tmp_path}/Source/MyGame/MyGameCharacter.h",
                "language": "C++",
                "imports": [],
            },
        ]

        frameworks = detector._detect_frameworks(tmp_path, files)

        assert "Unreal" in frameworks, f"Expected Unreal, got {frameworks}"
        assert "Unity" not in frameworks, f"Unity should not be detected: {frameworks}"

    def test_unity_detected_with_manifest_in_paths(self, detector, tmp_path):
        """Unity project is detected via Packages/manifest.json in file paths."""
        root = str(tmp_path)
        _make_unity_dir(tmp_path)

        files = [
            {
                "file": f"{root}/Packages/manifest.json",
                "language": "JSON",
                "imports": [],
            },
            {
                "file": f"{root}/Assets/Scripts/Player.cs",
                "language": "C#",
                "imports": ["UnityEngine"],
            },
        ]

        frameworks = detector._detect_frameworks(tmp_path, files)

        assert "Unity" in frameworks, f"Expected Unity, got {frameworks}"
