#!/usr/bin/env python3
"""
Architectural Pattern Detection (C3.7)

Detects high-level architectural patterns by analyzing multi-file relationships,
directory structures, and framework conventions.

Detected Patterns:
- MVC (Model-View-Controller)
- MVVM (Model-View-ViewModel)
- MVP (Model-View-Presenter)
- Repository Pattern
- Service Layer Pattern
- Layered Architecture (3-tier, N-tier)
- Clean Architecture
- Hexagonal/Ports & Adapters

Credits:
- Architectural pattern definitions from industry standards
- Framework detection based on official documentation
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ArchitecturalPattern:
    """Detected architectural pattern"""

    pattern_name: str  # e.g., "MVC", "MVVM", "Repository"
    confidence: float  # 0.0-1.0
    evidence: list[str]  # List of evidence supporting detection
    components: dict[str, list[str]]  # Component type -> file paths
    framework: str | None = None  # Detected framework (Django, Spring, etc.)
    description: str = ""  # Human-readable description


@dataclass
class ArchitecturalReport:
    """Complete architectural analysis report"""

    patterns: list[ArchitecturalPattern]
    directory_structure: dict[str, int]  # Directory name -> file count
    total_files_analyzed: int
    frameworks_detected: list[str]
    ai_analysis: dict | None = None  # AI enhancement (C3.6 integration)

    def to_dict(self) -> dict:
        """Export to dictionary"""
        return {
            "patterns": [
                {
                    "pattern_name": p.pattern_name,
                    "confidence": p.confidence,
                    "evidence": p.evidence,
                    "components": p.components,
                    "framework": p.framework,
                    "description": p.description,
                }
                for p in self.patterns
            ],
            "directory_structure": self.directory_structure,
            "total_files_analyzed": self.total_files_analyzed,
            "frameworks_detected": self.frameworks_detected,
            "ai_analysis": self.ai_analysis,
        }


class ArchitecturalPatternDetector:
    """
    Detect high-level architectural patterns.

    Analyzes entire codebase structure, not individual files.
    """

    # Common directory patterns for architectures
    MVC_DIRS = {"models", "views", "controllers", "model", "view", "controller"}
    MVVM_DIRS = {"models", "views", "viewmodels", "viewmodel"}
    LAYERED_DIRS = {"presentation", "business", "data", "dal", "bll", "ui"}
    CLEAN_ARCH_DIRS = {"domain", "application", "infrastructure", "presentation"}
    REPO_DIRS = {"repositories", "repository"}
    SERVICE_DIRS = {"services", "service"}

    # Framework detection patterns
    FRAMEWORK_MARKERS = {
        # Game Engines (checked first to avoid false positives)
        "Unity": [
            "Assembly-CSharp.csproj",
            "UnityEngine.dll",
            "ProjectSettings/ProjectVersion.txt",
            ".unity",
            "Library/",
        ],
        "Unreal": ["Source/", ".uproject", "Config/DefaultEngine.ini", "Binaries/", "Content/"],
        "Godot": ["project.godot", ".godot", ".tscn", ".tres", ".gd"],
        # Web Frameworks
        "Django": ["django", "manage.py", "settings.py", "urls.py"],
        "Flask": ["flask", "app.py", "wsgi.py"],
        "Spring": [
            "springframework",
            "org.springframework",
            "@Controller",
            "@Service",
            "@Repository",
        ],
        "ASP.NET": [
            "Microsoft.AspNetCore",
            "System.Web",
            "Controllers",
            "Models",
            "Views",
            ".cshtml",
            "Startup.cs",
        ],
        "Rails": [
            "rails",
            "action",
            "app/models",
            "app/views",
            "app/controllers",
            "config/routes.rb",
        ],
        "Angular": [
            "@angular",
            "angular",
            "app.module.ts",
            "@Component",
            "@Injectable",
            "angular.json",
        ],
        "React": ["react", "package.json", "components"],
        "Vue.js": ["vue", ".vue", "components"],
        "Express": ["express", "app.js", "routes"],
        "Laravel": ["laravel", "illuminate", "artisan", "app/Http/Controllers", "app/Models"],
    }

    def __init__(self, enhance_with_ai: bool = True):
        """
        Initialize detector.

        Args:
            enhance_with_ai: Enable AI enhancement for detected patterns (C3.6)
        """
        self.enhance_with_ai = enhance_with_ai
        self.ai_enhancer = None

        if self.enhance_with_ai:
            try:
                from skill_seekers.cli.ai_enhancer import AIEnhancer

                self.ai_enhancer = AIEnhancer()
            except Exception as e:
                logger.warning(f"⚠️  Failed to initialize AI enhancer: {e}")
                self.enhance_with_ai = False

    def analyze(self, directory: Path, files_analysis: list[dict]) -> ArchitecturalReport:
        """
        Analyze codebase for architectural patterns.

        Args:
            directory: Root directory of codebase
            files_analysis: List of analyzed files from CodeAnalyzer

        Returns:
            ArchitecturalReport with detected patterns
        """
        logger.info(f"🏗️  Analyzing architectural patterns in {directory}")

        # Build directory structure map
        dir_structure = self._analyze_directory_structure(directory)

        # Detect frameworks
        frameworks = self._detect_frameworks(directory, files_analysis)

        # Detect architectural patterns
        patterns = []

        patterns.extend(self._detect_mvc(dir_structure, files_analysis, frameworks))
        patterns.extend(self._detect_mvvm(dir_structure, files_analysis, frameworks))
        patterns.extend(self._detect_repository(dir_structure, files_analysis))
        patterns.extend(self._detect_service_layer(dir_structure, files_analysis))
        patterns.extend(self._detect_layered_architecture(dir_structure, files_analysis))
        patterns.extend(self._detect_clean_architecture(dir_structure, files_analysis))

        report = ArchitecturalReport(
            patterns=patterns,
            directory_structure=dir_structure,
            total_files_analyzed=len(files_analysis),
            frameworks_detected=frameworks,
        )

        # Enhance with AI if enabled (C3.6)
        if self.enhance_with_ai and self.ai_enhancer and patterns:
            report.ai_analysis = self._enhance_with_ai(report)

        logger.info(f"✅ Detected {len(patterns)} architectural patterns")
        return report

    def _analyze_directory_structure(self, directory: Path) -> dict[str, int]:
        """Analyze directory structure and count files"""
        structure = defaultdict(int)

        for path in directory.rglob("*"):
            if path.is_file():
                # Get relative directory path
                rel_dir = path.parent.relative_to(directory)
                dir_name = str(rel_dir).lower()

                # Extract top-level and leaf directory names
                parts = Path(dir_name).parts
                if parts:
                    structure[parts[0]] += 1  # Top-level dir
                    if len(parts) > 1:
                        structure[parts[-1]] += 1  # Leaf dir

        return dict(structure)

    def _detect_frameworks(self, directory: Path, files: list[dict]) -> list[str]:
        """Detect frameworks being used"""
        detected = []

        # Check file paths from analyzed files
        all_paths = [str(f.get("file", "")) for f in files]
        all_content = " ".join(all_paths)

        # Extract all imports from ALL languages (fixes #239 - extended to multi-language)
        all_imports = []
        for file_data in files:
            if file_data.get("imports"):
                all_imports.extend(file_data["imports"])

        # Create searchable import string
        import_content = " ".join(all_imports)
        logger.debug(
            f"Collected {len(all_imports)} imports from {len([f for f in files if f.get('imports')])} files for framework detection"
        )

        # Also check actual directory structure for game engine markers
        # (project.godot, .unity, .uproject are config files, not in analyzed files)
        dir_files = []
        try:
            # Get all files and directories in the root (non-recursive for performance)
            for item in directory.iterdir():
                dir_files.append(item.name)
        except Exception as e:
            logger.warning(f"Could not scan directory for framework markers: {e}")

        dir_content = " ".join(dir_files)

        # Check game engines FIRST (priority detection)
        for framework in ["Unity", "Unreal", "Godot"]:
            if framework in self.FRAMEWORK_MARKERS:
                markers = self.FRAMEWORK_MARKERS[framework]
                # Check both analyzed files AND directory structure
                file_matches = sum(1 for marker in markers if marker.lower() in all_content.lower())
                dir_matches = sum(1 for marker in markers if marker.lower() in dir_content.lower())
                total_matches = file_matches + dir_matches

                if total_matches >= 2:
                    detected.append(framework)
                    logger.info(f"  📦 Detected framework: {framework}")
                    # Return early to prevent web framework false positives
                    return detected

        # Check other frameworks (including imports - fixes #239)
        for framework, markers in self.FRAMEWORK_MARKERS.items():
            if framework in ["Unity", "Unreal", "Godot"]:
                continue  # Already checked

            # Check in file paths, directory structure, AND imports
            path_matches = sum(1 for marker in markers if marker.lower() in all_content.lower())
            dir_matches = sum(1 for marker in markers if marker.lower() in dir_content.lower())
            import_matches = sum(
                1 for marker in markers if marker.lower() in import_content.lower()
            )

            # Strategy: Prioritize import-based detection (more accurate)
            # If we have import matches, they're strong signals - use them alone
            # Otherwise, require 2+ matches from paths/dirs
            if import_matches >= 1:
                # Import-based detection (high confidence)
                detected.append(framework)
                logger.info(f"  📦 Detected framework: {framework} (imports:{import_matches})")
            elif (path_matches + dir_matches) >= 2:
                # Path/directory-based detection (requires 2+ matches)
                detected.append(framework)
                logger.info(
                    f"  📦 Detected framework: {framework} (path:{path_matches} dir:{dir_matches})"
                )

        return detected

    def _detect_mvc(
        self, dirs: dict[str, int], files: list[dict], frameworks: list[str]
    ) -> list[ArchitecturalPattern]:
        """Detect MVC pattern"""
        patterns = []

        # Check for MVC directory structure
        mvc_dir_matches = sum(1 for d in self.MVC_DIRS if d in dirs)
        has_mvc_structure = mvc_dir_matches >= 2

        if not has_mvc_structure:
            return patterns

        # Build evidence
        evidence = []
        components = defaultdict(list)

        # Find MVC files
        for file in files:
            file_path = str(file.get("file", "")).lower()

            if "model" in file_path and ("models/" in file_path or "/model/" in file_path):
                components["Models"].append(file.get("file", ""))
                if len(components["Models"]) == 1:
                    evidence.append("Models directory with model classes")

            if "view" in file_path and ("views/" in file_path or "/view/" in file_path):
                components["Views"].append(file.get("file", ""))
                if len(components["Views"]) == 1:
                    evidence.append("Views directory with view files")

            if "controller" in file_path and (
                "controllers/" in file_path or "/controller/" in file_path
            ):
                components["Controllers"].append(file.get("file", ""))
                if len(components["Controllers"]) == 1:
                    evidence.append("Controllers directory with controller classes")

        # Calculate confidence
        has_models = len(components["Models"]) > 0
        has_views = len(components["Views"]) > 0
        has_controllers = len(components["Controllers"]) > 0

        if sum([has_models, has_views, has_controllers]) >= 2:
            confidence = 0.6 + (sum([has_models, has_views, has_controllers]) * 0.15)

            # Boost confidence if framework detected
            framework = None
            for fw in ["Django", "Flask", "Spring", "ASP.NET", "Rails", "Laravel"]:
                if fw in frameworks:
                    confidence = min(0.95, confidence + 0.1)
                    framework = fw
                    evidence.append(f"{fw} framework detected (uses MVC)")
                    break

            patterns.append(
                ArchitecturalPattern(
                    pattern_name="MVC (Model-View-Controller)",
                    confidence=confidence,
                    evidence=evidence,
                    components=dict(components),
                    framework=framework,
                    description="Separates application into Models (data), Views (UI), and Controllers (logic)",
                )
            )

        return patterns

    def _detect_mvvm(
        self, dirs: dict[str, int], files: list[dict], frameworks: list[str]
    ) -> list[ArchitecturalPattern]:
        """Detect MVVM pattern"""
        patterns = []

        # Look for ViewModels directory or classes ending with ViewModel
        has_viewmodel_dir = "viewmodels" in dirs or "viewmodel" in dirs
        viewmodel_files = [f for f in files if "viewmodel" in str(f.get("file", "")).lower()]

        if not (has_viewmodel_dir or len(viewmodel_files) >= 2):
            return patterns

        evidence = []
        components = defaultdict(list)

        # Find MVVM files
        for file in files:
            file_path = str(file.get("file", "")).lower()
            classes = file.get("classes", [])

            if "model" in file_path and "viewmodel" not in file_path:
                components["Models"].append(file.get("file", ""))

            if "view" in file_path:
                components["Views"].append(file.get("file", ""))

            if "viewmodel" in file_path or any(
                "viewmodel" in c.get("name", "").lower() for c in classes
            ):
                components["ViewModels"].append(file.get("file", ""))

        if len(components["ViewModels"]) >= 2:
            evidence.append(
                f"ViewModels directory with {len(components['ViewModels'])} ViewModel classes"
            )

        if len(components["Views"]) >= 2:
            evidence.append(f"Views directory with {len(components['Views'])} view files")

        if len(components["Models"]) >= 1:
            evidence.append(f"Models directory with {len(components['Models'])} model files")

        # Calculate confidence
        has_models = len(components["Models"]) > 0
        has_views = len(components["Views"]) > 0
        has_viewmodels = len(components["ViewModels"]) >= 2

        if has_viewmodels and (has_models or has_views):
            confidence = 0.7 if (has_models and has_views and has_viewmodels) else 0.6

            framework = None
            for fw in ["ASP.NET", "Angular", "Vue.js"]:
                if fw in frameworks:
                    confidence = min(0.95, confidence + 0.1)
                    framework = fw
                    evidence.append(f"{fw} framework detected (supports MVVM)")
                    break

            patterns.append(
                ArchitecturalPattern(
                    pattern_name="MVVM (Model-View-ViewModel)",
                    confidence=confidence,
                    evidence=evidence,
                    components=dict(components),
                    framework=framework,
                    description="ViewModels provide data-binding between Views and Models",
                )
            )

        return patterns

    def _detect_repository(
        self, dirs: dict[str, int], files: list[dict]
    ) -> list[ArchitecturalPattern]:
        """Detect Repository pattern"""
        patterns = []

        # Look for repositories directory or classes ending with Repository
        has_repo_dir = any(d in dirs for d in self.REPO_DIRS)
        repo_files = [
            f
            for f in files
            if "repository" in str(f.get("file", "")).lower()
            or any("repository" in c.get("name", "").lower() for c in f.get("classes", []))
        ]

        if not (has_repo_dir or len(repo_files) >= 2):
            return patterns

        evidence = []
        components = defaultdict(list)

        for file in repo_files:
            components["Repositories"].append(file.get("file", ""))

        if len(components["Repositories"]) >= 2:
            evidence.append(
                f"Repository pattern: {len(components['Repositories'])} repository classes"
            )
            evidence.append("Repositories abstract data access logic")

            patterns.append(
                ArchitecturalPattern(
                    pattern_name="Repository Pattern",
                    confidence=0.75,
                    evidence=evidence,
                    components=dict(components),
                    description="Encapsulates data access logic in repository classes",
                )
            )

        return patterns

    def _detect_service_layer(
        self, dirs: dict[str, int], files: list[dict]
    ) -> list[ArchitecturalPattern]:
        """Detect Service Layer pattern"""
        patterns = []

        has_service_dir = any(d in dirs for d in self.SERVICE_DIRS)
        service_files = [
            f
            for f in files
            if "service" in str(f.get("file", "")).lower()
            or any("service" in c.get("name", "").lower() for c in f.get("classes", []))
        ]

        if not (has_service_dir or len(service_files) >= 3):
            return patterns

        evidence = []
        components = defaultdict(list)

        for file in service_files:
            components["Services"].append(file.get("file", ""))

        if len(components["Services"]) >= 3:
            evidence.append(f"Service layer: {len(components['Services'])} service classes")
            evidence.append("Services encapsulate business logic")

            patterns.append(
                ArchitecturalPattern(
                    pattern_name="Service Layer Pattern",
                    confidence=0.75,
                    evidence=evidence,
                    components=dict(components),
                    description="Encapsulates business logic in service classes",
                )
            )

        return patterns

    def _detect_layered_architecture(
        self, dirs: dict[str, int], _files: list[dict]
    ) -> list[ArchitecturalPattern]:
        """Detect Layered Architecture (3-tier, N-tier)"""
        patterns = []

        layered_matches = sum(1 for d in self.LAYERED_DIRS if d in dirs)

        if layered_matches < 2:
            return patterns

        evidence = []
        _components = defaultdict(list)
        layers_found = []

        if "presentation" in dirs or "ui" in dirs:
            layers_found.append("Presentation Layer")
            evidence.append("Presentation/UI layer detected")

        if "business" in dirs or "bll" in dirs:
            layers_found.append("Business Logic Layer")
            evidence.append("Business logic layer detected")

        if "data" in dirs or "dal" in dirs:
            layers_found.append("Data Access Layer")
            evidence.append("Data access layer detected")

        if len(layers_found) >= 2:
            confidence = 0.65 + (len(layers_found) * 0.1)

            patterns.append(
                ArchitecturalPattern(
                    pattern_name=f"Layered Architecture ({len(layers_found)}-tier)",
                    confidence=min(confidence, 0.9),
                    evidence=evidence,
                    components={"Layers": layers_found},
                    description=f"Separates concerns into {len(layers_found)} distinct layers",
                )
            )

        return patterns

    def _detect_clean_architecture(
        self, dirs: dict[str, int], _files: list[dict]
    ) -> list[ArchitecturalPattern]:
        """Detect Clean Architecture"""
        patterns = []

        clean_matches = sum(1 for d in self.CLEAN_ARCH_DIRS if d in dirs)

        if clean_matches < 3:
            return patterns

        evidence = []
        components = defaultdict(list)

        if "domain" in dirs:
            evidence.append("Domain layer (core business logic)")
            components["Domain"].append("domain/")

        if "application" in dirs:
            evidence.append("Application layer (use cases)")
            components["Application"].append("application/")

        if "infrastructure" in dirs:
            evidence.append("Infrastructure layer (external dependencies)")
            components["Infrastructure"].append("infrastructure/")

        if "presentation" in dirs:
            evidence.append("Presentation layer (UI/API)")
            components["Presentation"].append("presentation/")

        if len(components) >= 3:
            patterns.append(
                ArchitecturalPattern(
                    pattern_name="Clean Architecture",
                    confidence=0.85,
                    evidence=evidence,
                    components=dict(components),
                    description="Dependency inversion with domain at center, infrastructure at edges",
                )
            )

        return patterns

    def _enhance_with_ai(self, report: ArchitecturalReport) -> dict:
        """Enhance architectural analysis with AI insights"""
        if not self.ai_enhancer:
            return {}

        # Prepare summary for AI
        summary = f"""Detected {len(report.patterns)} architectural patterns:
{chr(10).join(f"- {p.pattern_name} (confidence: {p.confidence:.2f})" for p in report.patterns)}

Frameworks: {", ".join(report.frameworks_detected) if report.frameworks_detected else "None"}
Total files: {report.total_files_analyzed}

Provide brief architectural insights and recommendations."""

        try:
            response = self.ai_enhancer._call_claude(summary, max_tokens=500)
            return {"insights": response} if response else {}
        except Exception as e:
            logger.warning(f"⚠️  AI enhancement failed: {e}")
            return {}
