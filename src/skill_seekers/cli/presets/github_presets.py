"""GitHub command presets.

Defines preset configurations for the github command.

Presets:
    quick:          Fast scraping with minimal data
    standard:       Balanced scraping (DEFAULT)
    comprehensive:  Comprehensive scraping with all data
"""

from dataclasses import dataclass, field
from typing import Dict
import argparse


@dataclass(frozen=True)
class GitHubPreset:
    """Definition of a GitHub preset.
    
    Attributes:
        name: Human-readable preset name
        description: Brief description of what this preset does
        max_issues: Maximum issues to fetch
        features: Dict of feature flags (feature_name -> enabled)
        estimated_time: Human-readable time estimate
    """
    name: str
    description: str
    max_issues: int
    features: Dict[str, bool] = field(default_factory=dict)
    estimated_time: str = ""


# Preset definitions
GITHUB_PRESETS = {
    "quick": GitHubPreset(
        name="Quick",
        description="Fast scraping with minimal data (README + code)",
        max_issues=10,
        features={
            "include_issues": False,
            "include_changelog": True,
            "include_releases": False,
        },
        estimated_time="1-3 minutes"
    ),
    
    "standard": GitHubPreset(
        name="Standard",
        description="Balanced scraping with issues and releases (recommended)",
        max_issues=100,
        features={
            "include_issues": True,
            "include_changelog": True,
            "include_releases": True,
        },
        estimated_time="5-15 minutes"
    ),
    
    "comprehensive": GitHubPreset(
        name="Comprehensive",
        description="Comprehensive scraping with all available data",
        max_issues=500,
        features={
            "include_issues": True,
            "include_changelog": True,
            "include_releases": True,
        },
        estimated_time="20-60 minutes"
    ),
}


def apply_github_preset(args: argparse.Namespace, preset_name: str) -> None:
    """Apply a GitHub preset to the args namespace.
    
    Args:
        args: The argparse.Namespace to modify
        preset_name: Name of the preset to apply
        
    Raises:
        KeyError: If preset_name is not a valid preset
    """
    preset = GITHUB_PRESETS[preset_name]
    
    # Apply max_issues only if not set by user
    if args.max_issues is None or args.max_issues == 100:  # 100 is default
        args.max_issues = preset.max_issues
    
    # Apply feature flags (only if not explicitly disabled by user)
    for feature, enabled in preset.features.items():
        skip_attr = f"no_{feature}"
        if not hasattr(args, skip_attr) or not getattr(args, skip_attr):
            setattr(args, skip_attr, not enabled)


def show_github_preset_list() -> None:
    """Print the list of available GitHub presets to stdout."""
    print("\nAvailable GitHub Presets")
    print("=" * 60)
    print()
    
    for name, preset in GITHUB_PRESETS.items():
        marker = " (DEFAULT)" if name == "standard" else ""
        print(f"  {name}{marker}")
        print(f"    {preset.description}")
        print(f"    Estimated time: {preset.estimated_time}")
        print(f"    Max issues: {preset.max_issues}")
        
        # Show enabled features
        enabled = [f.replace("include_", "") for f, v in preset.features.items() if v]
        if enabled:
            print(f"    Features: {', '.join(enabled)}")
        print()
    
    print("Usage: skill-seekers github --repo <owner/repo> --preset <name>")
    print()
