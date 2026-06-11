"""Back-compat shim — module moved to ``skill_seekers.services.config_publisher``.

Deprecated: import from ``skill_seekers.services.config_publisher`` instead.
This shim re-exports the public API and will be removed in a future major release.
"""

from skill_seekers.services.config_publisher import (
    CATEGORY_KEYWORDS,
    ConfigPublisher,
    detect_category,
)

__all__ = ["CATEGORY_KEYWORDS", "ConfigPublisher", "detect_category"]
