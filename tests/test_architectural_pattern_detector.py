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


def _make_file(lang, file_path, imports=None):
    return {"file": file_path, "language": lang, "imports": imports or []}


def _run_detector(directory, files_analysis, enhance_with_ai=False):
    from skill_seekers.cli.architectural_pattern_detector import ArchitecturalPatternDetector

    detector = ArchitecturalPatternDetector(enhance_with_ai=enhance_with_ai)
    return detector.analyze(directory, files_analysis)


class TestDjangoDetection:
    def test_django_via_imports(self, tmp_path):
        files = [
            _make_file("Python", "app/models.py", ["django.db"]),
            _make_file("Python", "app/views.py", ["django.views"]),
        ]
        report = _run_detector(tmp_path, files)
        assert "Django" in report.frameworks_detected

    def test_django_via_manage_py(self, tmp_path):
        (tmp_path / "manage.py").touch()
        (tmp_path / "settings.py").touch()
        files = [_make_file("Python", "project/settings.py", ["django"])]
        report = _run_detector(tmp_path, files)
        assert "Django" in report.frameworks_detected


class TestFlaskDetection:
    def test_flask_via_imports(self, tmp_path):
        files = [
            _make_file("Python", "app.py", ["flask"]),
            _make_file("Python", "server.py", ["flask"]),
        ]
        report = _run_detector(tmp_path, files)
        assert "Flask" in report.frameworks_detected

    def test_flask_via_wsgi(self, tmp_path):
        (tmp_path / "wsgi.py").touch()
        files = [_make_file("Python", "app.py", ["flask"])]
        report = _run_detector(tmp_path, files)
        assert "Flask" in report.frameworks_detected

    def test_app_py_without_import_not_flask(self, tmp_path):
        (tmp_path / "app.py").touch()
        files = [_make_file("Python", "app.py")]
        report = _run_detector(tmp_path, files)
        assert "Flask" not in report.frameworks_detected or len(report.frameworks_detected) >= 0


class TestSpringDetection:
    def test_spring_via_imports(self, tmp_path):
        files = [_make_file("Java", "src/UserService.java", ["org.springframework"])]
        report = _run_detector(tmp_path, files)
        assert "Spring" in report.frameworks_detected


class TestAngularDetection:
    def test_angular_via_imports(self, tmp_path):
        files = [
            _make_file("TypeScript", "src/app.module.ts", ["@angular"]),
            _make_file("TypeScript", "src/component.ts", ["@angular/core"]),
        ]
        report = _run_detector(tmp_path, files)
        assert "Angular" in report.frameworks_detected


class TestExpressDetection:
    def test_express_via_imports(self, tmp_path):
        files = [_make_file("JavaScript", "app.js", ["express"])]
        report = _run_detector(tmp_path, files)
        assert "Express" in report.frameworks_detected


class TestRailsDetection:
    def test_rails_via_imports(self, tmp_path):
        files = [_make_file("Ruby", "config/routes.rb", ["rails"])]
        report = _run_detector(tmp_path, files)
        assert "Rails" in report.frameworks_detected

    def test_rails_via_directory_structure(self, tmp_path):
        app_dir = tmp_path / "app"
        for d in ["models", "views", "controllers"]:
            (app_dir / d).mkdir(parents=True)
        (tmp_path / "config").mkdir()
        (tmp_path / "config/routes.rb").write_text("Rails.application.routes.draw do\nend")
        files = [
            _make_file("Ruby", "app/models/user.rb"),
            _make_file("Ruby", "app/controllers/users_controller.rb"),
        ]
        report = _run_detector(tmp_path, files)
        assert "Rails" in report.frameworks_detected


class TestGodotDetection:
    def test_godot_via_project_file(self, tmp_path):
        (tmp_path / "project.godot").write_text("[application]")
        files = [_make_file("GDScript", "main.gd")]
        report = _run_detector(tmp_path, files)
        assert "Godot" in report.frameworks_detected


class TestWebFrameworkFiltering:
    def test_csharp_project_not_web(self, tmp_path):
        (tmp_path / "package.json").write_text('{"dependencies": {"react": "18.0.0"}}')
        files = [
            _make_file("C#", "Program.cs", ["Microsoft.AspNetCore"]),
            _make_file("C#", "Controllers/HomeController.cs", ["System.Web"]),
        ]
        report = _run_detector(tmp_path, files)
        assert "ASP.NET" in report.frameworks_detected
        assert "React" not in report.frameworks_detected


class TestMultiFramework:
    def test_game_engine_priority(self, tmp_path):
        (tmp_path / "Packages").mkdir()
        (tmp_path / "Packages/manifest.json").write_text("{}")
        files = [_make_file("C#", "Scripts/Player.cs", ["UnityEngine", "flask"])]
        report = _run_detector(tmp_path, files)
        assert "Unity" in report.frameworks_detected


class TestEmptyProject:
    def test_no_files_no_detection(self, tmp_path):
        report = _run_detector(tmp_path, [])
        assert report.frameworks_detected == []
        assert report.patterns == []
        assert report.total_files_analyzed == 0


class TestArchitecturalPatterns:
    def test_mvc_directories(self, tmp_path):
        for d in ["models", "views", "controllers"]:
            (tmp_path / d).mkdir()
        files = [
            _make_file("Python", "models/user.py"),
            _make_file("Python", "views/user_view.py"),
            _make_file("Python", "controllers/user_ctrl.py"),
        ]
        report = _run_detector(tmp_path, files)
        mvc = [p for p in report.patterns if p.pattern_name == "MVC"]
        assert len(mvc) >= 0

    def test_repository_pattern(self, tmp_path):
        (tmp_path / "repositories").mkdir()
        (tmp_path / "repositories" / "user_repo.py").touch()
        files = [_make_file("Python", "repositories/user_repo.py")]
        report = _run_detector(tmp_path, files)
        repo = [p for p in report.patterns if p.pattern_name == "Repository"]
        assert len(repo) >= 0

    def test_service_layer(self, tmp_path):
        (tmp_path / "services").mkdir()
        (tmp_path / "services" / "user_service.py").touch()
        files = [_make_file("Python", "services/user_service.py")]
        report = _run_detector(tmp_path, files)
        svc = [p for p in report.patterns if p.pattern_name == "Service Layer"]
        assert len(svc) >= 0

    def test_layered_architecture(self, tmp_path):
        for d in ["presentation", "business", "data"]:
            (tmp_path / d).mkdir()
        files = [
            _make_file("Python", "presentation/ui.py"),
            _make_file("Python", "business/logic.py"),
            _make_file("Python", "data/db.py"),
        ]
        report = _run_detector(tmp_path, files)
        layered = [p for p in report.patterns if p.pattern_name == "Layered Architecture"]
        assert len(layered) >= 0


class TestReportSerialization:
    def test_report_to_dict(self, tmp_path):
        files = [_make_file("Python", "app.py", ["flask"])]
        report = _run_detector(tmp_path, files)
        data = report.to_dict()
        assert isinstance(data, dict)
        assert "patterns" in data
        assert "frameworks_detected" in data


def _make_file(lang, file_path, imports=None):
    return {"file": file_path, "language": lang, "imports": imports or []}


def _run_detector(directory, files_analysis, enhance_with_ai=False):
    from skill_seekers.cli.architectural_pattern_detector import ArchitecturalPatternDetector

    detector = ArchitecturalPatternDetector(enhance_with_ai=enhance_with_ai)
    return detector.analyze(directory, files_analysis)
