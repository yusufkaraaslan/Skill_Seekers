# Skill Seekers Intelligence System - Technical Architecture

**Version:** 1.0 (Draft)
**Status:** 🔬 Research & Design
**Last Updated:** 2026-01-20
**For:** Study and iteration before implementation

---

## 🎯 System Overview

The **Skill Seekers Intelligence System** is a multi-layered architecture that automatically generates, updates, and intelligently loads codebase knowledge into Claude Code's context.

**Core Principles:**
1. **Git-Based Triggers:** Only update on branch merges (not constant watching)
2. **Modular Skills:** Separate libraries from codebase, split codebase into modules
3. **Smart Clustering:** Load only relevant skills based on context
4. **User Control:** Config-driven, user has final say

---

## 🏗️ Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACE                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ CLI Commands     Claude Code Plugin    Config Files  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                   ORCHESTRATION LAYER                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ • Project Manager                                    │   │
│  │ • Skill Registry                                     │   │
│  │ • Update Scheduler                                   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                  SKILL GENERATION LAYER                     │
│  ┌────────────────────┐  ┌────────────────────┐            │
│  │ Tech Stack         │  │ Modular Codebase   │            │
│  │ Detector           │  │ Analyzer           │            │
│  └────────────────────┘  └────────────────────┘            │
│  ┌────────────────────┐  ┌────────────────────┐            │
│  │ Library Skill      │  │ Git Change         │            │
│  │ Downloader         │  │ Detector           │            │
│  └────────────────────┘  └────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                  CLUSTERING LAYER                           │
│  ┌────────────────────┐  ┌────────────────────┐            │
│  │ Import-Based       │  │ Embedding-Based    │            │
│  │ Clustering         │  │ Clustering         │            │
│  │ (Phase 1)          │  │ (Phase 2)          │            │
│  └────────────────────┘  └────────────────────┘            │
│  ┌────────────────────┐                                     │
│  │ Hybrid Clustering  │                                     │
│  │ (Combines both)    │                                     │
│  └────────────────────┘                                     │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                     STORAGE LAYER                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ • Skill Files (.skill-seekers/skills/)               │   │
│  │ • Embeddings Cache (.skill-seekers/cache/)           │   │
│  │ • Metadata (.skill-seekers/registry.json)            │   │
│  │ • Git Hooks (.skill-seekers/hooks/)                  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📂 File System Structure

```
project-root/
├── .skill-seekers/                    # Intelligence system directory
│   ├── config.yml                     # User configuration
│   │
│   ├── skills/                        # Generated skills
│   │   ├── libraries/                 # External library skills
│   │   │   ├── fastapi.skill
│   │   │   ├── react.skill
│   │   │   └── postgresql.skill
│   │   │
│   │   └── codebase/                  # Project-specific skills
│   │       ├── backend/
│   │       │   ├── api.skill
│   │       │   ├── auth.skill
│   │       │   └── models.skill
│   │       │
│   │       └── frontend/
│   │           ├── components.skill
│   │           └── pages.skill
│   │
│   ├── cache/                         # Performance caches
│   │   ├── embeddings/                # Skill embeddings
│   │   │   ├── fastapi.npy
│   │   │   ├── api.npy
│   │   │   └── ...
│   │   │
│   │   └── metadata/                  # Cached metadata
│   │       └── skill-registry.json
│   │
│   ├── hooks/                         # Git hooks
│   │   ├── post-merge                 # Auto-regenerate on merge
│   │   ├── post-commit                # Optional
│   │   └── pre-push                   # Optional validation
│   │
│   ├── logs/                          # System logs
│   │   ├── regeneration.log
│   │   └── clustering.log
│   │
│   └── registry.json                  # Skill registry metadata
│
├── .git/                              # Git repository
└── ... (project files)
```

---

## ⚙️ Component Details

### 1. Project Manager

**Responsibility:** Initialize and manage project intelligence

```python
# src/skill_seekers/intelligence/project_manager.py

class ProjectManager:
    """Manages project intelligence system lifecycle"""

    def __init__(self, project_root: Path):
        self.root = project_root
        self.config_path = project_root / ".skill-seekers" / "config.yml"
        self.skills_dir = project_root / ".skill-seekers" / "skills"

    def initialize(self) -> bool:
        """
        Initialize project for intelligence system
        Creates directory structure, config, git hooks
        """
        # 1. Create directory structure
        self._create_directories()

        # 2. Generate default config
        config = self._generate_default_config()
        self._save_config(config)

        # 3. Install git hooks
        self._install_git_hooks()

        # 4. Initial skill generation
        self._initial_skill_generation()

        return True

    def _create_directories(self):
        """Create .skill-seekers directory structure"""
        dirs = [
            ".skill-seekers",
            ".skill-seekers/skills",
            ".skill-seekers/skills/libraries",
            ".skill-seekers/skills/codebase",
            ".skill-seekers/cache",
            ".skill-seekers/cache/embeddings",
            ".skill-seekers/cache/metadata",
            ".skill-seekers/hooks",
            ".skill-seekers/logs",
        ]

        for d in dirs:
            (self.root / d).mkdir(parents=True, exist_ok=True)

    def _generate_default_config(self) -> dict:
        """Generate sensible default configuration"""
        return {
            "version": "1.0",
            "project_name": self.root.name,
            "watch_branches": ["main", "development"],
            "tech_stack": {
                "auto_detect": True,
                "frameworks": []
            },
            "skill_generation": {
                "enabled": True,
                "output_dir": ".skill-seekers/skills/codebase"
            },
            "git_hooks": {
                "enabled": True,
                "trigger_on": ["post-merge"]
            },
            "clustering": {
                "enabled": False,  # Phase 4+
                "strategy": "import",  # import, embedding, hybrid
                "max_skills_in_context": 5
            }
        }

    def _install_git_hooks(self):
        """Install git hooks for auto-regeneration"""
        hook_template = """#!/bin/bash
# Auto-generated by skill-seekers
# DO NOT EDIT - regenerate with: skill-seekers init-project

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
CONFIG_FILE=".skill-seekers/config.yml"

if [ ! -f "$CONFIG_FILE" ]; then
    exit 0
fi

# Read watched branches from config
WATCH_BRANCHES=$(yq '.watch_branches[]' "$CONFIG_FILE" 2>/dev/null || echo "")

if echo "$WATCH_BRANCHES" | grep -q "^$CURRENT_BRANCH$"; then
    echo "🔄 Skill regeneration triggered on branch: $CURRENT_BRANCH"
    skill-seekers regenerate-skills --branch "$CURRENT_BRANCH" --silent
    echo "✅ Skills updated"
fi
"""

        hook_path = self.root / ".git" / "hooks" / "post-merge"
        hook_path.write_text(hook_template)
        hook_path.chmod(0o755)  # Make executable
```

---

### 2. Tech Stack Detector

**Responsibility:** Detect frameworks and libraries from project files

```python
# src/skill_seekers/intelligence/stack_detector.py

from pathlib import Path
from typing import Dict, List
import json
import yaml
import toml

class TechStackDetector:
    """
    Detect tech stack from project configuration files
    Supports: Python, JavaScript/TypeScript, Go, Rust, Java
    """

    def __init__(self, project_root: Path):
        self.root = project_root
        self.detectors = {
            "python": self._detect_python,
            "javascript": self._detect_javascript,
            "typescript": self._detect_typescript,
            "go": self._detect_go,
            "rust": self._detect_rust,
            "java": self._detect_java,
        }

    def detect(self) -> Dict[str, List[str]]:
        """
        Detect complete tech stack

        Returns:
            {
                "languages": ["Python", "JavaScript"],
                "frameworks": ["FastAPI", "React"],
                "databases": ["PostgreSQL"],
                "tools": ["Docker", "Redis"]
            }
        """
        stack = {
            "languages": [],
            "frameworks": [],
            "databases": [],
            "tools": []
        }

        # Detect languages
        for lang, detector in self.detectors.items():
            if detector():
                stack["languages"].append(lang.title())

        # Detect frameworks (per language)
        if "Python" in stack["languages"]:
            stack["frameworks"].extend(self._detect_python_frameworks())

        if "JavaScript" in stack["languages"] or "TypeScript" in stack["languages"]:
            stack["frameworks"].extend(self._detect_js_frameworks())

        # Detect databases
        stack["databases"].extend(self._detect_databases())

        # Detect tools
        stack["tools"].extend(self._detect_tools())

        return stack

    def _detect_python(self) -> bool:
        """Detect Python project"""
        markers = [
            "requirements.txt",
            "setup.py",
            "pyproject.toml",
            "Pipfile",
            "poetry.lock"
        ]
        return any((self.root / marker).exists() for marker in markers)

    def _detect_python_frameworks(self) -> List[str]:
        """Detect Python frameworks"""
        frameworks = []

        # Parse requirements.txt
        req_file = self.root / "requirements.txt"
        if req_file.exists():
            deps = req_file.read_text().lower()

            framework_map = {
                "fastapi": "FastAPI",
                "django": "Django",
                "flask": "Flask",
                "sqlalchemy": "SQLAlchemy",
                "pydantic": "Pydantic",
                "anthropic": "Anthropic",
                "openai": "OpenAI",
                "beautifulsoup4": "BeautifulSoup",
                "requests": "Requests",
                "httpx": "HTTPX",
                "aiohttp": "aiohttp",
            }

            for key, name in framework_map.items():
                if key in deps:
                    frameworks.append(name)

        # Parse pyproject.toml
        pyproject = self.root / "pyproject.toml"
        if pyproject.exists():
            try:
                data = toml.loads(pyproject.read_text())
                deps = data.get("project", {}).get("dependencies", [])
                deps_str = " ".join(deps).lower()

                for key, name in framework_map.items():
                    if key in deps_str and name not in frameworks:
                        frameworks.append(name)
            except:
                pass

        return frameworks

    def _detect_javascript(self) -> bool:
        """Detect JavaScript project"""
        return (self.root / "package.json").exists()

    def _detect_typescript(self) -> bool:
        """Detect TypeScript project"""
        markers = ["tsconfig.json", "package.json"]
        if not all((self.root / m).exists() for m in markers):
            return False

        # Check if typescript is in dependencies
        pkg = self.root / "package.json"
        try:
            data = json.loads(pkg.read_text())
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            return "typescript" in deps
        except:
            return False

    def _detect_js_frameworks(self) -> List[str]:
        """Detect JavaScript/TypeScript frameworks"""
        frameworks = []

        pkg = self.root / "package.json"
        if not pkg.exists():
            return frameworks

        try:
            data = json.loads(pkg.read_text())
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

            framework_map = {
                "react": "React",
                "vue": "Vue",
                "next": "Next.js",
                "nuxt": "Nuxt.js",
                "svelte": "Svelte",
                "angular": "Angular",
                "express": "Express",
                "fastify": "Fastify",
                "nestjs": "NestJS",
            }

            for key, name in framework_map.items():
                if key in deps:
                    frameworks.append(name)

        except:
            pass

        return frameworks

    def _detect_databases(self) -> List[str]:
        """Detect databases from environment and configs"""
        databases = []

        # Check .env file
        env_file = self.root / ".env"
        if env_file.exists():
            env_content = env_file.read_text().lower()

            db_markers = {
                "postgres": "PostgreSQL",
                "mysql": "MySQL",
                "mongodb": "MongoDB",
                "redis": "Redis",
                "sqlite": "SQLite",
            }

            for marker, name in db_markers.items():
                if marker in env_content:
                    databases.append(name)

        # Check docker-compose.yml
        compose = self.root / "docker-compose.yml"
        if compose.exists():
            try:
                data = yaml.safe_load(compose.read_text())
                services = data.get("services", {})

                for service_name, config in services.items():
                    image = config.get("image", "").lower()

                    db_images = {
                        "postgres": "PostgreSQL",
                        "mysql": "MySQL",
                        "mongo": "MongoDB",
                        "redis": "Redis",
                    }

                    for marker, name in db_images.items():
                        if marker in image and name not in databases:
                            databases.append(name)
            except:
                pass

        return databases

    def _detect_tools(self) -> List[str]:
        """Detect development tools"""
        tools = []

        tool_markers = {
            "Dockerfile": "Docker",
            "docker-compose.yml": "Docker Compose",
            ".github/workflows": "GitHub Actions",
            "Makefile": "Make",
            "nginx.conf": "Nginx",
        }

        for marker, name in tool_markers.items():
            if (self.root / marker).exists():
                tools.append(name)

        return tools

    def _detect_go(self) -> bool:
        return (self.root / "go.mod").exists()

    def _detect_rust(self) -> bool:
        return (self.root / "Cargo.toml").exists()

    def _detect_java(self) -> bool:
        markers = ["pom.xml", "build.gradle", "build.gradle.kts"]
        return any((self.root / m).exists() for m in markers)
```

---

### 3. Modular Skill Generator

**Responsibility:** Split codebase into modular skills based on config

```python
# src/skill_seekers/intelligence/modular_generator.py

from pathlib import Path
from typing import List, Dict
import glob

class ModularSkillGenerator:
    """
    Generate modular skills from codebase
    Splits based on: namespace, directory, feature, or custom
    """

    def __init__(self, project_root: Path, config: dict):
        self.root = project_root
        self.config = config
        self.modules = config.get("modules", {})

    def generate_all(self) -> List[Path]:
        """Generate all modular skills"""
        generated_skills = []

        for module_name, module_config in self.modules.items():
            skills = self.generate_module(module_name, module_config)
            generated_skills.extend(skills)

        return generated_skills

    def generate_module(self, module_name: str, module_config: dict) -> List[Path]:
        """
        Generate skills for a single module

        module_config = {
            "path": "src/api/",
            "split_by": "namespace",  # or directory, feature, custom
            "skills": [
                {
                    "name": "api",
                    "description": "API endpoints",
                    "include": ["*/routes/*.py"],
                    "exclude": ["*_test.py"]
                }
            ]
        }
        """
        skills = []

        for skill_config in module_config.get("skills", []):
            skill_path = self._generate_skill(module_name, skill_config)
            skills.append(skill_path)

        return skills

    def _generate_skill(self, module_name: str, skill_config: dict) -> Path:
        """Generate a single skill file"""
        skill_name = skill_config["name"]
        include_patterns = skill_config.get("include", [])
        exclude_patterns = skill_config.get("exclude", [])

        # 1. Find files matching patterns
        files = self._find_files(include_patterns, exclude_patterns)

        # 2. Run codebase analysis on these files
        # (Reuse existing C3.x codebase_scraper.py)
        from skill_seekers.cli.codebase_scraper import analyze_codebase

        analysis_result = analyze_codebase(
            files=files,
            project_root=self.root,
            depth="deep",
            ai_mode="none"
        )

        # 3. Generate SKILL.md
        skill_content = self._format_skill(
            name=skill_name,
            description=skill_config.get("description", ""),
            analysis=analysis_result
        )

        # 4. Save skill file
        output_dir = self.root / ".skill-seekers" / "skills" / "codebase" / module_name
        output_dir.mkdir(parents=True, exist_ok=True)

        skill_path = output_dir / f"{skill_name}.skill"
        skill_path.write_text(skill_content)

        return skill_path

    def _find_files(self, include: List[str], exclude: List[str]) -> List[Path]:
        """Find files matching include/exclude patterns"""
        files = set()

        # Include patterns
        for pattern in include:
            matched = glob.glob(str(self.root / pattern), recursive=True)
            files.update(Path(f) for f in matched)

        # Exclude patterns
        for pattern in exclude:
            matched = glob.glob(str(self.root / pattern), recursive=True)
            files.difference_update(Path(f) for f in matched)

        return sorted(files)

    def _format_skill(self, name: str, description: str, analysis: dict) -> str:
        """Format analysis results into SKILL.md"""
        return f"""---
name: {name}
description: {description}
module: codebase
---

# {name.title()}

## Description

{description}

## API Reference

{analysis.get('api_reference', '')}

## Design Patterns

{analysis.get('patterns', '')}

## Examples

{analysis.get('examples', '')}

## Related Skills

{self._generate_cross_references(name)}
"""

    def _generate_cross_references(self, skill_name: str) -> str:
        """Generate cross-references to related skills"""
        # Analyze imports to find dependencies
        # Link to other skills that this skill imports from
        return "- Related skill 1\n- Related skill 2"
```

---

### 4. Import-Based Clustering Engine

**Responsibility:** Find relevant skills based on import analysis

```python
# src/skill_seekers/intelligence/import_clustering.py

from pathlib import Path
from typing import List, Set
import ast

class ImportBasedClusteringEngine:
    """
    Find relevant skills by analyzing imports in current file
    Fast and deterministic - no AI needed
    """

    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self.skill_registry = self._build_registry()

    def _build_registry(self) -> dict:
        """
        Build registry mapping imports to skills

        Returns:
            {
                "fastapi": ["libraries/fastapi.skill"],
                "anthropic": ["libraries/anthropic.skill"],
                "src.api": ["codebase/backend/api.skill"],
                "src.auth": ["codebase/backend/auth.skill"],
            }
        """
        registry = {}

        # Scan all skills and extract what they provide
        for skill_path in self.skills_dir.rglob("*.skill"):
            # Parse skill metadata (YAML frontmatter)
            provides = self._extract_provides(skill_path)

            for module in provides:
                if module not in registry:
                    registry[module] = []
                registry[module].append(skill_path)

        return registry

    def find_relevant_skills(
        self,
        current_file: Path,
        max_skills: int = 5
    ) -> List[Path]:
        """
        Find most relevant skills for current file

        Algorithm:
        1. Parse imports from current file
        2. Map imports to skills via registry
        3. Add current file's skill (if exists)
        4. Rank and return top N
        """
        # 1. Parse imports
        imports = self._parse_imports(current_file)

        # 2. Map to skills
        relevant_skills = set()

        for imp in imports:
            # External library?
            if self._is_external(imp):
                lib_skill = self._find_library_skill(imp)
                if lib_skill:
                    relevant_skills.add(lib_skill)

            # Internal module?
            else:
                module_skill = self._find_module_skill(imp)
                if module_skill:
                    relevant_skills.add(module_skill)

        # 3. Add current file's skill (highest priority)
        current_skill = self._find_skill_for_file(current_file)
        if current_skill:
            # Insert at beginning
            relevant_skills = [current_skill] + list(relevant_skills)

        # 4. Rank and return
        return self._rank_skills(relevant_skills)[:max_skills]

    def _parse_imports(self, file_path: Path) -> Set[str]:
        """
        Parse imports from Python file using AST

        Returns: {"fastapi", "anthropic", "src.api", "src.auth"}
        """
        imports = set()

        try:
            tree = ast.parse(file_path.read_text())

            for node in ast.walk(tree):
                # import X
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)

                # from X import Y
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)

        except Exception as e:
            print(f"Warning: Could not parse {file_path}: {e}")

        return imports

    def _is_external(self, import_name: str) -> bool:
        """Check if import is external library or internal module"""
        # External if:
        # - Not starts with project name
        # - Not starts with "src"
        # - Is known library (fastapi, django, etc.)

        internal_prefixes = ["src", "tests", self._get_project_name()]

        return not any(import_name.startswith(prefix) for prefix in internal_prefixes)

    def _find_library_skill(self, import_name: str) -> Path | None:
        """Find library skill for external import"""
        # Try exact match first
        skill_path = self.skills_dir / "libraries" / f"{import_name}.skill"
        if skill_path.exists():
            return skill_path

        # Try partial match (e.g., "fastapi.routing" -> "fastapi")
        base_module = import_name.split(".")[0]
        skill_path = self.skills_dir / "libraries" / f"{base_module}.skill"
        if skill_path.exists():
            return skill_path

        return None

    def _find_module_skill(self, import_name: str) -> Path | None:
        """Find codebase skill for internal import"""
        # Use registry to map import to skill
        return self.skill_registry.get(import_name)

    def _find_skill_for_file(self, file_path: Path) -> Path | None:
        """Find which skill contains this file"""
        # Match file path against skill file patterns
        # This requires reading all skill configs
        # For now, simple heuristic: src/api/ -> api.skill

        rel_path = file_path.relative_to(self.project_root)

        if "api" in str(rel_path):
            return self.skills_dir / "codebase" / "backend" / "api.skill"
        elif "auth" in str(rel_path):
            return self.skills_dir / "codebase" / "backend" / "auth.skill"
        # ... etc

        return None

    def _rank_skills(self, skills: List[Path]) -> List[Path]:
        """Rank skills by relevance (for now, just deduplicate)"""
        return list(dict.fromkeys(skills))  # Preserve order, remove dupes
```

---

### 5. Embedding-Based Clustering Engine

**Responsibility:** Find relevant skills using semantic similarity

```python
# src/skill_seekers/intelligence/embedding_clustering.py

from pathlib import Path
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

class EmbeddingBasedClusteringEngine:
    """
    Find relevant skills using embeddings and cosine similarity
    More flexible than import-based, but slower
    """

    def __init__(self, skills_dir: Path, cache_dir: Path):
        self.skills_dir = skills_dir
        self.cache_dir = cache_dir
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # 80MB, fast

        # Load or generate skill embeddings
        self.skill_embeddings = self._load_skill_embeddings()

    def _load_skill_embeddings(self) -> dict:
        """Load pre-computed skill embeddings from cache"""
        embeddings = {}

        for skill_path in self.skills_dir.rglob("*.skill"):
            cache_path = self.cache_dir / "embeddings" / f"{skill_path.stem}.npy"

            if cache_path.exists():
                # Load from cache
                embeddings[skill_path] = np.load(cache_path)
            else:
                # Generate and cache
                embedding = self._embed_skill(skill_path)
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                np.save(cache_path, embedding)
                embeddings[skill_path] = embedding

        return embeddings

    def _embed_skill(self, skill_path: Path) -> np.ndarray:
        """Generate embedding for a skill"""
        content = skill_path.read_text()

        # Extract key sections (API Reference + Examples)
        api_section = self._extract_section(content, "## API Reference")
        examples_section = self._extract_section(content, "## Examples")

        # Combine and embed
        text = f"{api_section}\n{examples_section}"
        embedding = self.model.encode(text[:5000])  # Limit to 5K chars

        return embedding

    def _embed_file(self, file_path: Path) -> np.ndarray:
        """Generate embedding for current file"""
        content = file_path.read_text()

        # Embed full content (or first N chars for performance)
        embedding = self.model.encode(content[:5000])

        return embedding

    def find_relevant_skills(
        self,
        current_file: Path,
        max_skills: int = 5
    ) -> List[Path]:
        """
        Find most relevant skills using cosine similarity

        Algorithm:
        1. Embed current file
        2. Compute cosine similarity with all skill embeddings
        3. Rank by similarity
        4. Return top N
        """
        # 1. Embed current file
        file_embedding = self._embed_file(current_file)

        # 2. Compute similarities
        similarities = {}

        for skill_path, skill_embedding in self.skill_embeddings.items():
            similarity = self._cosine_similarity(file_embedding, skill_embedding)
            similarities[skill_path] = similarity

        # 3. Rank by similarity
        ranked = sorted(similarities.items(), key=lambda x: x[1], reverse=True)

        # 4. Return top N
        return [skill_path for skill_path, _ in ranked[:max_skills]]

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors"""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def _extract_section(self, content: str, header: str) -> str:
        """Extract section from markdown content"""
        lines = content.split("\n")
        section_lines = []
        in_section = False

        for line in lines:
            if line.startswith(header):
                in_section = True
                continue

            if in_section:
                if line.startswith("##"):  # Next section
                    break
                section_lines.append(line)

        return "\n".join(section_lines)
```

---

### 6. Hybrid Clustering Engine

**Responsibility:** Combine import-based and embedding-based clustering

```python
# src/skill_seekers/intelligence/hybrid_clustering.py

class HybridClusteringEngine:
    """
    Combine import-based (precise) and embedding-based (flexible)
    for best-of-both-worlds clustering
    """

    def __init__(
        self,
        import_engine: ImportBasedClusteringEngine,
        embedding_engine: EmbeddingBasedClusteringEngine,
        import_weight: float = 0.7,
        embedding_weight: float = 0.3
    ):
        self.import_engine = import_engine
        self.embedding_engine = embedding_engine
        self.import_weight = import_weight
        self.embedding_weight = embedding_weight

    def find_relevant_skills(
        self,
        current_file: Path,
        max_skills: int = 5
    ) -> List[Path]:
        """
        Find relevant skills using hybrid approach

        Algorithm:
        1. Get skills from both engines
        2. Combine with weighted ranking
        3. Return top N
        """
        # 1. Get results from both engines
        import_skills = self.import_engine.find_relevant_skills(
            current_file, max_skills=10
        )

        embedding_skills = self.embedding_engine.find_relevant_skills(
            current_file, max_skills=10
        )

        # 2. Weighted ranking
        skill_scores = {}

        # Import-based scores (higher rank = higher score)
        for i, skill in enumerate(import_skills):
            score = (len(import_skills) - i) * self.import_weight
            skill_scores[skill] = skill_scores.get(skill, 0) + score

        # Embedding-based scores
        for i, skill in enumerate(embedding_skills):
            score = (len(embedding_skills) - i) * self.embedding_weight
            skill_scores[skill] = skill_scores.get(skill, 0) + score

        # 3. Sort by combined score
        ranked = sorted(skill_scores.items(), key=lambda x: x[1], reverse=True)

        # 4. Return top N
        return [skill for skill, _ in ranked[:max_skills]]
```

---

## 🔌 Claude Code Plugin Integration

```python
# claude_plugins/skill-seekers-intelligence/agent.py

class SkillSeekersIntelligenceAgent:
    """
    Claude Code plugin for skill intelligence
    Handles file open events, loads relevant skills
    """

    def __init__(self):
        self.project_root = self._detect_project_root()
        self.config = self._load_config()
        self.clustering_engine = self._init_clustering_engine()
        self.loaded_skills = []

    def _init_clustering_engine(self):
        """Initialize clustering engine based on config"""
        strategy = self.config.get("clustering", {}).get("strategy", "import")

        if strategy == "import":
            return ImportBasedClusteringEngine(self.skills_dir)
        elif strategy == "embedding":
            return EmbeddingBasedClusteringEngine(self.skills_dir, self.cache_dir)
        elif strategy == "hybrid":
            import_engine = ImportBasedClusteringEngine(self.skills_dir)
            embedding_engine = EmbeddingBasedClusteringEngine(
                self.skills_dir, self.cache_dir
            )
            return HybridClusteringEngine(import_engine, embedding_engine)

    async def on_file_open(self, file_path: str):
        """Hook: User opens a file"""
        file_path = Path(file_path)

        # Find relevant skills
        relevant_skills = self.clustering_engine.find_relevant_skills(
            file_path,
            max_skills=self.config.get("clustering", {}).get("max_skills_in_context", 5)
        )

        # Load skills into Claude context
        await self.load_skills(relevant_skills)

        # Notify user
        self.notify_user(f"📚 Loaded {len(relevant_skills)} skills", relevant_skills)

    async def on_branch_merge(self, branch: str):
        """Hook: Branch merged"""
        if branch in self.config.get("watch_branches", []):
            await self.regenerate_skills(branch)

    async def load_skills(self, skill_paths: List[Path]):
        """Load skills into Claude's context"""
        self.loaded_skills = skill_paths

        # Read skill contents
        skill_contents = []
        for path in skill_paths:
            content = path.read_text()
            skill_contents.append({
                "name": path.stem,
                "content": content
            })

        # Tell Claude which skills are loaded
        # (Exact API depends on Claude Code plugin system)
        await self.claude_api.load_skills(skill_contents)

    async def regenerate_skills(self, branch: str):
        """Regenerate skills after branch merge"""
        # Run: skill-seekers regenerate-skills --branch {branch}
        import subprocess

        result = subprocess.run(
            ["skill-seekers", "regenerate-skills", "--branch", branch, "--silent"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            self.notify_user(f"✅ Skills updated for branch: {branch}")
        else:
            self.notify_user(f"❌ Skill regeneration failed: {result.stderr}")
```

---

## 📊 Performance Considerations

### Import Analysis
- **Speed:** <100ms per file (AST parsing is fast)
- **Accuracy:** 85-90% (misses dynamic imports)
- **Memory:** Negligible (registry is small)

### Embedding Generation
- **Speed:** ~50ms per embedding (with all-MiniLM-L6-v2)
- **Accuracy:** 80-85% (better than imports for semantics)
- **Memory:** ~5KB per embedding
- **Storage:** ~500KB for 100 skills

### Skill Loading
- **Context Size:** 5 skills × 200 lines = 1000 lines (~4K tokens)
- **Loading Time:** <50ms (file I/O)
- **Claude Context:** Leaves plenty of room for code

### Git Hooks
- **Trigger Time:** <1 second (git hook overhead)
- **Regeneration:** 3-5 minutes (depends on codebase size)
- **Background:** Can run in background (async)

---

## 🔒 Security Considerations

1. **Git Hooks:** Installed with user permission, can be disabled
2. **File System:** Limited to project directory
3. **Network:** Library skills downloaded over HTTPS
4. **Embeddings:** Generated locally, no data sent externally
5. **Cache:** Stored locally in `.skill-seekers/cache/`

---

## 🎯 Design Trade-offs

### 1. Git-Based vs Watch Mode
- **Chosen:** Git-based (update on merge)
- **Why:** Better performance, no constant CPU usage
- **Trade-off:** Less real-time, requires commit

### 2. Import vs Embedding
- **Chosen:** Both (hybrid)
- **Why:** Import is fast/precise, embedding is flexible
- **Trade-off:** More complex, harder to debug

### 3. Config-Driven vs Auto
- **Chosen:** Config-driven with auto-detect
- **Why:** User control + convenience
- **Trade-off:** Requires manual config for complex cases

### 4. Local vs Cloud
- **Chosen:** Local (embeddings generated locally)
- **Why:** Privacy, speed, no API costs
- **Trade-off:** Requires model download (80MB)

---

## 🚧 Open Questions

1. **Claude Code Plugin API:** How exactly do we load skills into context?
2. **Context Management:** How to handle context overflow with large skills?
3. **Multi-File Context:** What if user has 3 files open? Load skills for all?
4. **Skill Updates:** How to invalidate cache when code changes?
5. **Cross-Project:** Can skills be shared across projects?

---

## 📚 References

- **Existing Code:** `src/skill_seekers/cli/codebase_scraper.py` (C3.x features)
- **Similar Tools:** GitHub Copilot, Cursor, Tabnine
- **Research:** RAG systems, semantic code search
- **Libraries:** sentence-transformers, numpy, ast

---

**Version:** 1.0 (Draft)
**Status:** For study and iteration
**Next:** Review, iterate, then implement Phase 1
