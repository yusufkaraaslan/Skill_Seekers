"""Formal preset system for analyze command.

Provides predefined analysis configurations with clear trade-offs
between speed and comprehensiveness.
"""

from dataclasses import dataclass


@dataclass
class AnalysisPreset:
    """Analysis preset configuration.

    Defines a complete analysis configuration including depth,
    feature flags, and AI enhancement level.
    """

    name: str
    description: str
    depth: str  # surface, deep, full
    features: dict[str, bool]  # Feature flags (api_reference, patterns, etc.)
    enhance_level: int  # 0=none, 1=SKILL.md, 2=+Arch+Config, 3=full
    estimated_time: str
    icon: str


# Preset definitions
PRESETS = {
    "quick": AnalysisPreset(
        name="Quick",
        description="Fast basic analysis (1-2 min, essential features only)",
        depth="surface",
        features={
            "api_reference": True,  # ON - Essential for API docs
            "dependency_graph": False,  # OFF - Slow, not critical for quick
            "patterns": False,  # OFF - Slow pattern detection
            "test_examples": False,  # OFF - Time-consuming extraction
            "how_to_guides": False,  # OFF - Requires AI enhancement
            "config_patterns": False,  # OFF - Not critical for quick scan
            "docs": True,  # ON - README/docs are essential
        },
        enhance_level=0,  # No AI enhancement (fast)
        estimated_time="1-2 minutes",
        icon="⚡",
    ),
    "standard": AnalysisPreset(
        name="Standard",
        description="Balanced analysis (5-10 min, core features, DEFAULT)",
        depth="deep",
        features={
            "api_reference": True,  # ON - Core feature
            "dependency_graph": True,  # ON - Valuable insights
            "patterns": True,  # ON - Design pattern detection
            "test_examples": True,  # ON - Real usage examples
            "how_to_guides": False,  # OFF - Requires AI (slow)
            "config_patterns": True,  # ON - Configuration docs
            "docs": True,  # ON - Project documentation
        },
        enhance_level=1,  # SKILL.md enhancement only
        estimated_time="5-10 minutes",
        icon="🎯",
    ),
    "comprehensive": AnalysisPreset(
        name="Comprehensive",
        description="Full analysis (20-60 min, all features + AI)",
        depth="full",
        features={
            "api_reference": True,  # ON - Complete API docs
            "dependency_graph": True,  # ON - Full dependency analysis
            "patterns": True,  # ON - All design patterns
            "test_examples": True,  # ON - All test examples
            "how_to_guides": True,  # ON - AI-generated guides
            "config_patterns": True,  # ON - All configuration patterns
            "docs": True,  # ON - All project docs
        },
        enhance_level=3,  # Full AI enhancement (all features)
        estimated_time="20-60 minutes",
        icon="🚀",
    ),
}


class PresetManager:
    """Manages analysis presets and applies them to CLI arguments."""

    @staticmethod
    def get_preset(name: str) -> AnalysisPreset | None:
        """Get preset by name.

        Args:
            name: Preset name (case-insensitive)

        Returns:
            AnalysisPreset if found, None otherwise
        """
        return PRESETS.get(name.lower())

    @staticmethod
    def list_presets() -> list[str]:
        """List available preset names.

        Returns:
            List of preset names in definition order
        """
        return list(PRESETS.keys())

    @staticmethod
    def format_preset_help() -> str:
        """Format preset help text for CLI.

        Returns:
            Formatted help text with preset descriptions
        """
        lines = ["Available presets:"]
        lines.append("")
        for name, preset in PRESETS.items():
            lines.append(f"  {preset.icon} {name:15} - {preset.description}")
            lines.append(f"     Estimated time: {preset.estimated_time}")
            lines.append(f"     Depth: {preset.depth}, AI level: {preset.enhance_level}")
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def apply_preset(preset_name: str, args: dict) -> dict:
        """Apply preset to args, with CLI overrides.

        Preset defaults are applied first, then CLI arguments override
        specific values. This allows users to customize presets.

        Args:
            preset_name: Preset to apply
            args: Existing args from CLI (may contain overrides)

        Returns:
            Updated args with preset applied

        Raises:
            ValueError: If preset_name is unknown
        """
        preset = PresetManager.get_preset(preset_name)
        if not preset:
            raise ValueError(f"Unknown preset: {preset_name}")

        # Start with preset defaults
        updated_args = {"depth": preset.depth, "enhance_level": preset.enhance_level}

        # Convert feature flags to skip_* arguments
        # feature=False → skip_feature=True (disabled)
        # feature=True → skip_feature=False (enabled)
        for feature, enabled in preset.features.items():
            skip_key = f"skip_{feature.replace('-', '_')}"
            updated_args[skip_key] = not enabled

        # Apply CLI overrides (CLI takes precedence over preset)
        for key, value in args.items():
            if value is not None:  # Only override if explicitly set
                updated_args[key] = value

        return updated_args

    @staticmethod
    def get_default_preset() -> str:
        """Get the default preset name.

        Returns:
            Default preset name ("standard")
        """
        return "standard"


# Public API
__all__ = [
    "AnalysisPreset",
    "PRESETS",
    "PresetManager",
]
