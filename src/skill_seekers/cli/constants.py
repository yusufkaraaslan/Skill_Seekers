"""Configuration constants for Skill Seekers CLI.

All values are loaded from ``defaults.json`` via :mod:`defaults`.
This module re-exports them as module-level names so that existing
``from skill_seekers.cli.constants import DEFAULT_RATE_LIMIT`` imports
keep working without changes.
"""

from skill_seekers.cli.defaults import DEFAULTS

# ===== SCRAPING CONFIGURATION =====

# Default scraping limits
DEFAULT_RATE_LIMIT: float = DEFAULTS["scraping"]["rate_limit"]
DEFAULT_MAX_PAGES: int = DEFAULTS["scraping"]["max_pages"]
DEFAULT_CHECKPOINT_INTERVAL: int = DEFAULTS["scraping"]["checkpoint_interval"]
DEFAULT_ASYNC_MODE: bool = DEFAULTS["scraping"]["async_mode"]

# Content analysis limits
CONTENT_PREVIEW_LENGTH: int = DEFAULTS["limits"]["content_preview_length"]
MAX_PAGES_WARNING_THRESHOLD: int = DEFAULTS["limits"]["max_pages_warning_threshold"]

# Quality thresholds
MIN_CATEGORIZATION_SCORE: int = DEFAULTS["categorization"]["min_score"]
URL_MATCH_POINTS: int = DEFAULTS["categorization"]["url_match_points"]
TITLE_MATCH_POINTS: int = DEFAULTS["categorization"]["title_match_points"]
CONTENT_MATCH_POINTS: int = DEFAULTS["categorization"]["content_match_points"]

# ===== ENHANCEMENT CONFIGURATION =====

# API-based enhancement limits (uses Anthropic API)
API_CONTENT_LIMIT: int = DEFAULTS["limits"]["api_content_limit"]
API_PREVIEW_LIMIT: int = DEFAULTS["limits"]["api_preview_limit"]

# Local enhancement limits (uses coding agent CLI)
LOCAL_CONTENT_LIMIT: int = DEFAULTS["limits"]["local_content_limit"]
LOCAL_PREVIEW_LIMIT: int = DEFAULTS["limits"]["local_preview_limit"]

# ===== PAGE ESTIMATION =====

# Estimation and discovery settings
DEFAULT_MAX_DISCOVERY: int = DEFAULTS["limits"]["default_max_discovery"]
DISCOVERY_THRESHOLD: int = DEFAULTS["limits"]["discovery_threshold"]

# ===== FILE LIMITS =====

# Output and processing limits
MAX_REFERENCE_FILES: int = DEFAULTS["limits"]["max_reference_files"]
MAX_CODE_BLOCKS_PER_PAGE: int = DEFAULTS["limits"]["max_code_blocks_per_page"]

# ===== EXPORT CONSTANTS =====

__all__ = [
    # Scraping
    "DEFAULT_RATE_LIMIT",
    "DEFAULT_MAX_PAGES",
    "DEFAULT_CHECKPOINT_INTERVAL",
    "DEFAULT_ASYNC_MODE",
    "CONTENT_PREVIEW_LENGTH",
    "MAX_PAGES_WARNING_THRESHOLD",
    "MIN_CATEGORIZATION_SCORE",
    "URL_MATCH_POINTS",
    "TITLE_MATCH_POINTS",
    "CONTENT_MATCH_POINTS",
    # Enhancement
    "API_CONTENT_LIMIT",
    "API_PREVIEW_LIMIT",
    "LOCAL_CONTENT_LIMIT",
    "LOCAL_PREVIEW_LIMIT",
    # Estimation
    "DEFAULT_MAX_DISCOVERY",
    "DISCOVERY_THRESHOLD",
    # Limits
    "MAX_REFERENCE_FILES",
    "MAX_CODE_BLOCKS_PER_PAGE",
]
