"""Web UI backend for Skill Seekers.

A FastAPI application that exposes the Skill Seekers toolchain (create, scan,
enhance, package, port, marketplace, config library) over a local HTTP API,
and serves the Seeker HUD single-page app from ``ui/dist`` when built.

State is stored under ``~/.skill-seekers/ui/`` (jobs, projects, activity,
skill metadata overrides) following the conventions of the existing
``services/`` managers (``~/.skill-seekers/marketplaces.json`` etc.).
"""

__all__ = ["app", "jobs", "registry", "clis", "runner"]
