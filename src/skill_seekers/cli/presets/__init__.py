"""Preset system for Skill Seekers CLI commands.

Presets provide predefined configurations for commands, simplifying the user
experience by replacing complex flag combinations with simple preset names.

Usage:
    skill-seekers scrape https://docs.example.com --preset quick
    skill-seekers github --repo owner/repo --preset standard
    skill-seekers analyze --directory . --preset comprehensive

Available presets vary by command. Use --preset-list to see available presets.
"""

# Preset Manager (from manager.py - formerly presets.py)
from .manager import (
    PresetManager,
    PRESETS,
    AnalysisPreset,  # This is the main AnalysisPreset (with enhance_level)
)

# Analyze presets
from .analyze_presets import (
    AnalysisPreset as AnalyzeAnalysisPreset,  # Alternative version (without enhance_level)
    ANALYZE_PRESETS,
    apply_analyze_preset,
    get_preset_help_text,
    show_preset_list,
    apply_preset_with_warnings,
)

# Scrape presets
from .scrape_presets import (
    ScrapePreset,
    SCRAPE_PRESETS,
    apply_scrape_preset,
    show_scrape_preset_list,
)

# GitHub presets
from .github_presets import (
    GitHubPreset,
    GITHUB_PRESETS,
    apply_github_preset,
    show_github_preset_list,
)

__all__ = [
    # Preset Manager
    "PresetManager",
    "PRESETS",
    # Analyze
    "AnalysisPreset",
    "ANALYZE_PRESETS",
    "apply_analyze_preset",
    "get_preset_help_text",
    "show_preset_list",
    "apply_preset_with_warnings",
    # Scrape
    "ScrapePreset",
    "SCRAPE_PRESETS",
    "apply_scrape_preset",
    "show_scrape_preset_list",
    # GitHub
    "GitHubPreset",
    "GITHUB_PRESETS",
    "apply_github_preset",
    "show_github_preset_list",
]
