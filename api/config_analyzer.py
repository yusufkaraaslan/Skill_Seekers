#!/usr/bin/env python3
"""
Config Analyzer - Extract metadata from Skill Seekers config files
"""

import json
import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class ConfigAnalyzer:
    """Analyzes Skill Seekers config files and extracts metadata"""

    # Category mapping based on config content
    CATEGORY_MAPPING = {
        "web-frameworks": [
            "react", "vue", "django", "fastapi", "laravel", "astro", "hono"
        ],
        "game-engines": [
            "godot", "unity", "unreal"
        ],
        "devops": [
            "kubernetes", "ansible", "docker", "terraform"
        ],
        "css-frameworks": [
            "tailwind", "bootstrap", "bulma"
        ],
        "development-tools": [
            "claude-code", "vscode", "git"
        ],
        "gaming": [
            "steam"
        ],
        "testing": [
            "pytest", "jest", "test"
        ]
    }

    # Tag extraction keywords
    TAG_KEYWORDS = {
        "javascript": ["react", "vue", "astro", "hono", "javascript", "js", "node"],
        "python": ["django", "fastapi", "ansible", "python", "flask"],
        "php": ["laravel", "php"],
        "frontend": ["react", "vue", "astro", "tailwind", "frontend", "ui"],
        "backend": ["django", "fastapi", "laravel", "backend", "server", "api"],
        "css": ["tailwind", "css", "styling"],
        "game-development": ["godot", "unity", "unreal", "game"],
        "devops": ["kubernetes", "ansible", "docker", "k8s", "devops"],
        "documentation": ["docs", "documentation"],
        "testing": ["test", "testing", "pytest", "jest"]
    }

    def __init__(self, config_dir: Path, base_url: str = "https://api.skillseekersweb.com"):
        """
        Initialize config analyzer

        Args:
            config_dir: Path to configs directory
            base_url: Base URL for download links
        """
        self.config_dir = Path(config_dir)
        self.base_url = base_url

        if not self.config_dir.exists():
            raise ValueError(f"Config directory not found: {self.config_dir}")

    def analyze_all_configs(self) -> List[Dict[str, Any]]:
        """
        Analyze all config files and extract metadata

        Returns:
            List of config metadata dicts
        """
        configs = []

        # Find all JSON files recursively in configs directory and subdirectories
        for config_file in sorted(self.config_dir.rglob("*.json")):
            try:
                metadata = self.analyze_config(config_file)
                if metadata:  # Skip invalid configs
                    configs.append(metadata)
            except Exception as e:
                print(f"Warning: Failed to analyze {config_file.name}: {e}")
                continue

        return configs

    def analyze_config(self, config_path: Path) -> Optional[Dict[str, Any]]:
        """
        Analyze a single config file and extract metadata

        Args:
            config_path: Path to config JSON file

        Returns:
            Config metadata dict or None if invalid
        """
        try:
            # Read config file
            with open(config_path, 'r') as f:
                config_data = json.load(f)

            # Skip if no name field
            if "name" not in config_data:
                return None

            name = config_data["name"]
            description = config_data.get("description", "")

            # Determine config type
            config_type = self._determine_type(config_data)

            # Get primary source (base_url or repo)
            primary_source = self._get_primary_source(config_data, config_type)

            # Auto-categorize
            category = self._categorize_config(name, description, config_data)

            # Extract tags
            tags = self._extract_tags(name, description, config_data)

            # Get file metadata
            file_size = config_path.stat().st_size
            last_updated = self._get_last_updated(config_path)

            # Generate download URL
            download_url = f"{self.base_url}/api/download/{config_path.name}"

            # Get max_pages (for estimation)
            max_pages = self._get_max_pages(config_data)

            return {
                "name": name,
                "description": description,
                "type": config_type,
                "category": category,
                "tags": tags,
                "primary_source": primary_source,
                "max_pages": max_pages,
                "file_size": file_size,
                "last_updated": last_updated,
                "download_url": download_url,
                "config_file": config_path.name
            }

        except json.JSONDecodeError as e:
            print(f"Invalid JSON in {config_path.name}: {e}")
            return None
        except Exception as e:
            print(f"Error analyzing {config_path.name}: {e}")
            return None

    def get_config_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get config metadata by name

        Args:
            name: Config name (e.g., "react", "django")

        Returns:
            Config metadata or None if not found
        """
        configs = self.analyze_all_configs()
        for config in configs:
            if config["name"] == name:
                return config
        return None

    def _determine_type(self, config_data: Dict[str, Any]) -> str:
        """
        Determine if config is single-source or unified

        Args:
            config_data: Config JSON data

        Returns:
            "single-source" or "unified"
        """
        # Unified configs have "sources" array
        if "sources" in config_data:
            return "unified"

        # Check for merge_mode (another indicator of unified configs)
        if "merge_mode" in config_data:
            return "unified"

        return "single-source"

    def _get_primary_source(self, config_data: Dict[str, Any], config_type: str) -> str:
        """
        Get primary source URL/repo

        Args:
            config_data: Config JSON data
            config_type: "single-source" or "unified"

        Returns:
            Primary source URL or repo name
        """
        if config_type == "unified":
            # Get first source
            sources = config_data.get("sources", [])
            if sources:
                first_source = sources[0]
                if first_source.get("type") == "documentation":
                    return first_source.get("base_url", "")
                elif first_source.get("type") == "github":
                    return f"github.com/{first_source.get('repo', '')}"
                elif first_source.get("type") == "pdf":
                    return first_source.get("pdf_url", "PDF file")
            return "Multiple sources"

        # Single-source configs
        if "base_url" in config_data:
            return config_data["base_url"]
        elif "repo" in config_data:
            return f"github.com/{config_data['repo']}"
        elif "pdf_url" in config_data or "pdf" in config_data:
            return "PDF file"

        return "Unknown"

    def _categorize_config(self, name: str, description: str, config_data: Dict[str, Any]) -> str:
        """
        Auto-categorize config based on name and content

        Args:
            name: Config name
            description: Config description
            config_data: Full config data

        Returns:
            Category name
        """
        name_lower = name.lower()

        # Check against category mapping
        for category, keywords in self.CATEGORY_MAPPING.items():
            if any(keyword in name_lower for keyword in keywords):
                return category

        # Check description for hints
        desc_lower = description.lower()
        if "framework" in desc_lower or "library" in desc_lower:
            if any(word in desc_lower for word in ["web", "frontend", "backend", "api"]):
                return "web-frameworks"

        if "game" in desc_lower or "engine" in desc_lower:
            return "game-engines"

        if "devops" in desc_lower or "deployment" in desc_lower or "infrastructure" in desc_lower:
            return "devops"

        # Default to uncategorized
        return "uncategorized"

    def _extract_tags(self, name: str, description: str, config_data: Dict[str, Any]) -> List[str]:
        """
        Extract relevant tags from config

        Args:
            name: Config name
            description: Config description
            config_data: Full config data

        Returns:
            List of tags
        """
        tags = set()
        name_lower = name.lower()
        desc_lower = description.lower()

        # Check against tag keywords
        for tag, keywords in self.TAG_KEYWORDS.items():
            if any(keyword in name_lower or keyword in desc_lower for keyword in keywords):
                tags.add(tag)

        # Add config type as tag
        config_type = self._determine_type(config_data)
        if config_type == "unified":
            tags.add("multi-source")

        # Add source type tags
        if "base_url" in config_data or (config_type == "unified" and any(s.get("type") == "documentation" for s in config_data.get("sources", []))):
            tags.add("documentation")

        if "repo" in config_data or (config_type == "unified" and any(s.get("type") == "github" for s in config_data.get("sources", []))):
            tags.add("github")

        if "pdf" in config_data or "pdf_url" in config_data or (config_type == "unified" and any(s.get("type") == "pdf" for s in config_data.get("sources", []))):
            tags.add("pdf")

        return sorted(list(tags))

    def _get_max_pages(self, config_data: Dict[str, Any]) -> Optional[int]:
        """
        Get max_pages value from config

        Args:
            config_data: Config JSON data

        Returns:
            max_pages value or None
        """
        # Single-source configs
        if "max_pages" in config_data:
            return config_data["max_pages"]

        # Unified configs - get from first documentation source
        if "sources" in config_data:
            for source in config_data["sources"]:
                if source.get("type") == "documentation" and "max_pages" in source:
                    return source["max_pages"]

        return None

    def _get_last_updated(self, config_path: Path) -> str:
        """
        Get last updated date from git history

        Args:
            config_path: Path to config file

        Returns:
            ISO format date string
        """
        try:
            # Try to get last commit date for this file
            result = subprocess.run(
                ["git", "log", "-1", "--format=%cI", str(config_path)],
                cwd=config_path.parent.parent,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()

        except Exception:
            pass

        # Fallback to file modification time
        mtime = config_path.stat().st_mtime
        return datetime.fromtimestamp(mtime).isoformat()
