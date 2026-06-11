"""Back-compat shim — module moved to ``skill_seekers.services.marketplace_manager``.

Deprecated: import from ``skill_seekers.services.marketplace_manager`` instead.
This shim re-exports the public API and will be removed in a future major release.
"""

from skill_seekers.services.marketplace_manager import MarketplaceManager

__all__ = ["MarketplaceManager"]
