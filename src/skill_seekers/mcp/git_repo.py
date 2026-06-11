"""Back-compat shim — module moved to ``skill_seekers.services.git_repo``.

Deprecated: import from ``skill_seekers.services.git_repo`` instead.
This shim re-exports the public API and will be removed in a future major release.
"""

from skill_seekers.services.git_repo import GitConfigRepo

__all__ = ["GitConfigRepo"]
