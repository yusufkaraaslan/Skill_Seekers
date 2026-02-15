"""Scrape command presets.

Defines preset configurations for the scrape command.

Presets:
    quick:          Fast scraping with minimal depth
    standard:       Balanced scraping (DEFAULT)
    deep:           Comprehensive scraping with all features
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
import argparse


@dataclass(frozen=True)
class ScrapePreset:
    """Definition of a scrape preset.
    
    Attributes:
        name: Human-readable preset name
        description: Brief description of what this preset does
        rate_limit: Rate limit in seconds between requests
        features: Dict of feature flags (feature_name -> enabled)
        async_mode: Whether to use async scraping
        workers: Number of parallel workers
        estimated_time: Human-readable time estimate
    """
    name: str
    description: str
    rate_limit: float
    features: Dict[str, bool] = field(default_factory=dict)
    async_mode: bool = False
    workers: int = 1
    estimated_time: str = ""


# Preset definitions
SCRAPE_PRESETS = {
    "quick": ScrapePreset(
        name="Quick",
        description="Fast scraping with minimal depth (good for testing)",
        rate_limit=0.1,
        features={
            "rag_chunking": False,
            "resume": False,
        },
        async_mode=True,
        workers=5,
        estimated_time="2-5 minutes"
    ),
    
    "standard": ScrapePreset(
        name="Standard",
        description="Balanced scraping with good coverage (recommended)",
        rate_limit=0.5,
        features={
            "rag_chunking": True,
            "resume": True,
        },
        async_mode=True,
        workers=3,
        estimated_time="10-30 minutes"
    ),
    
    "deep": ScrapePreset(
        name="Deep",
        description="Comprehensive scraping with all features",
        rate_limit=1.0,
        features={
            "rag_chunking": True,
            "resume": True,
        },
        async_mode=True,
        workers=2,
        estimated_time="1-3 hours"
    ),
}


def apply_scrape_preset(args: argparse.Namespace, preset_name: str) -> None:
    """Apply a scrape preset to the args namespace.
    
    Args:
        args: The argparse.Namespace to modify
        preset_name: Name of the preset to apply
        
    Raises:
        KeyError: If preset_name is not a valid preset
    """
    preset = SCRAPE_PRESETS[preset_name]
    
    # Apply rate limit (only if not set by user)
    if args.rate_limit is None:
        args.rate_limit = preset.rate_limit
    
    # Apply workers (only if not set by user)
    if args.workers is None:
        args.workers = preset.workers
    
    # Apply async mode
    args.async_mode = preset.async_mode
    
    # Apply feature flags
    for feature, enabled in preset.features.items():
        if feature == "rag_chunking":
            if not hasattr(args, 'chunk_for_rag') or not args.chunk_for_rag:
                args.chunk_for_rag = enabled


def show_scrape_preset_list() -> None:
    """Print the list of available scrape presets to stdout."""
    print("\nAvailable Scrape Presets")
    print("=" * 60)
    print()
    
    for name, preset in SCRAPE_PRESETS.items():
        marker = " (DEFAULT)" if name == "standard" else ""
        print(f"  {name}{marker}")
        print(f"    {preset.description}")
        print(f"    Estimated time: {preset.estimated_time}")
        print(f"    Workers: {preset.workers}")
        print(f"    Async: {preset.async_mode}, Rate limit: {preset.rate_limit}s")
        print()
    
    print("Usage: skill-seekers scrape <url> --preset <name>")
    print()
