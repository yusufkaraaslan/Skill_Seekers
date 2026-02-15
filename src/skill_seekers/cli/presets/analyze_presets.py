"""Analyze command presets.

Defines preset configurations for the analyze command (Issue #268).

Presets control analysis depth and feature selection ONLY.
AI Enhancement is controlled separately via --enhance or --enhance-level flags.

Examples:
    skill-seekers analyze --directory . --preset quick
    skill-seekers analyze --directory . --preset quick --enhance
    skill-seekers analyze --directory . --preset comprehensive --enhance-level 2
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
import argparse


@dataclass(frozen=True)
class AnalysisPreset:
    """Definition of an analysis preset.
    
    Presets control analysis depth and features ONLY.
    AI Enhancement is controlled separately via --enhance or --enhance-level.
    
    Attributes:
        name: Human-readable preset name
        description: Brief description of what this preset does
        depth: Analysis depth level (surface, deep, full)
        features: Dict of feature flags (feature_name -> enabled)
        estimated_time: Human-readable time estimate
    """
    name: str
    description: str
    depth: str
    features: Dict[str, bool] = field(default_factory=dict)
    estimated_time: str = ""


# Preset definitions
ANALYZE_PRESETS = {
    "quick": AnalysisPreset(
        name="Quick",
        description="Fast basic analysis with minimal features",
        depth="surface",
        features={
            "api_reference": True,
            "dependency_graph": False,
            "patterns": False,
            "test_examples": False,
            "how_to_guides": False,
            "config_patterns": False,
        },
        estimated_time="1-2 minutes"
    ),
    
    "standard": AnalysisPreset(
        name="Standard",
        description="Balanced analysis with core features (recommended)",
        depth="deep",
        features={
            "api_reference": True,
            "dependency_graph": True,
            "patterns": True,
            "test_examples": True,
            "how_to_guides": False,
            "config_patterns": True,
        },
        estimated_time="5-10 minutes"
    ),
    
    "comprehensive": AnalysisPreset(
        name="Comprehensive",
        description="Full analysis with all features",
        depth="full",
        features={
            "api_reference": True,
            "dependency_graph": True,
            "patterns": True,
            "test_examples": True,
            "how_to_guides": True,
            "config_patterns": True,
        },
        estimated_time="20-60 minutes"
    ),
}


def apply_analyze_preset(args: argparse.Namespace, preset_name: str) -> None:
    """Apply an analysis preset to the args namespace.
    
    This modifies the args object to set the preset's depth and feature flags.
    NOTE: This does NOT set enhance_level - that's controlled separately via
    --enhance or --enhance-level flags.
    
    Args:
        args: The argparse.Namespace to modify
        preset_name: Name of the preset to apply
        
    Raises:
        KeyError: If preset_name is not a valid preset
        
    Example:
        >>> args = parser.parse_args(['--directory', '.', '--preset', 'quick'])
        >>> apply_analyze_preset(args, args.preset)
        >>> # args now has preset depth and features applied
        >>> # enhance_level is still 0 (default) unless --enhance was specified
    """
    preset = ANALYZE_PRESETS[preset_name]
    
    # Set depth
    args.depth = preset.depth
    
    # Set feature flags (skip_* attributes)
    for feature, enabled in preset.features.items():
        skip_attr = f"skip_{feature}"
        setattr(args, skip_attr, not enabled)


def get_preset_help_text(preset_name: str) -> str:
    """Get formatted help text for a preset.
    
    Args:
        preset_name: Name of the preset
        
    Returns:
        Formatted help string
    """
    preset = ANALYZE_PRESETS[preset_name]
    return (
        f"{preset.name}: {preset.description}\n"
        f"  Time: {preset.estimated_time}\n"
        f"  Depth: {preset.depth}"
    )


def show_preset_list() -> None:
    """Print the list of available presets to stdout.
    
    This is used by the --preset-list flag.
    """
    print("\nAvailable Analysis Presets")
    print("=" * 60)
    print()
    
    for name, preset in ANALYZE_PRESETS.items():
        marker = " (DEFAULT)" if name == "standard" else ""
        print(f"  {name}{marker}")
        print(f"    {preset.description}")
        print(f"    Estimated time: {preset.estimated_time}")
        print(f"    Depth: {preset.depth}")
        
        # Show enabled features
        enabled = [f for f, v in preset.features.items() if v]
        if enabled:
            print(f"    Features: {', '.join(enabled)}")
        print()
    
    print("AI Enhancement (separate from presets):")
    print("  --enhance              Enable AI enhancement (default level 1)")
    print("  --enhance-level N      Set AI enhancement level (0-3)")
    print()
    print("Examples:")
    print("  skill-seekers analyze --directory <dir> --preset quick")
    print("  skill-seekers analyze --directory <dir> --preset quick --enhance")
    print("  skill-seekers analyze --directory <dir> --preset comprehensive --enhance-level 2")
    print()


def resolve_enhance_level(args: argparse.Namespace) -> int:
    """Determine the enhance level based on user arguments.
    
    This is separate from preset application. Enhance level is controlled by:
    - --enhance-level N (explicit)
    - --enhance (use default level 1)
    - Neither (default to 0)
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        The enhance level to use (0-3)
    """
    # Explicit enhance level takes priority
    if args.enhance_level is not None:
        return args.enhance_level
    
    # --enhance flag enables default level (1)
    if args.enhance:
        return 1
    
    # Default is no enhancement
    return 0


def apply_preset_with_warnings(args: argparse.Namespace) -> str:
    """Apply preset with deprecation warnings for legacy flags.
    
    This is the main entry point for applying presets. It:
    1. Determines which preset to use
    2. Prints deprecation warnings if legacy flags were used
    3. Applies the preset (depth and features only)
    4. Sets enhance_level separately based on --enhance/--enhance-level
    5. Returns the preset name
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        The preset name that was applied
    """
    preset_name = None
    
    # Check for explicit preset
    if args.preset:
        preset_name = args.preset
    
    # Check for legacy flags and print warnings
    elif args.quick:
        print_deprecation_warning("--quick", "--preset quick")
        preset_name = "quick"
    
    elif args.comprehensive:
        print_deprecation_warning("--comprehensive", "--preset comprehensive")
        preset_name = "comprehensive"
    
    elif args.depth:
        depth_to_preset = {
            "surface": "quick",
            "deep": "standard", 
            "full": "comprehensive",
        }
        if args.depth in depth_to_preset:
            new_flag = f"--preset {depth_to_preset[args.depth]}"
            print_deprecation_warning(f"--depth {args.depth}", new_flag)
            preset_name = depth_to_preset[args.depth]
    
    # Default to standard
    if preset_name is None:
        preset_name = "standard"
    
    # Apply the preset (depth and features only)
    apply_analyze_preset(args, preset_name)
    
    # Set enhance_level separately (not part of preset)
    args.enhance_level = resolve_enhance_level(args)
    
    return preset_name


def print_deprecation_warning(old_flag: str, new_flag: str) -> None:
    """Print a deprecation warning for legacy flags.
    
    Args:
        old_flag: The old/deprecated flag name
        new_flag: The new recommended flag/preset
    """
    print(f"\n⚠️  DEPRECATED: {old_flag} is deprecated and will be removed in v3.0.0")
    print(f"   Use: {new_flag}")
    print()
