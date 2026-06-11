"""Skill Seekers shared services layer.

Domain logic shared by the CLI and the MCP server. Modules here must be
importable WITHOUT the optional ``mcp`` extras — no imports from
``skill_seekers.mcp`` are allowed in this package (the MCP layer is a thin
adapter over these services, not the other way around).

Modules:
    - marketplace_manager: Marketplace registry CRUD (MarketplaceManager)
    - marketplace_publisher: Publish skills to plugin marketplaces
      (MarketplacePublisher)
    - config_publisher: Push configs to config source repos (ConfigPublisher,
      detect_category, CATEGORY_KEYWORDS)
    - source_manager: Config source registry CRUD (SourceManager)
    - git_repo: Git clone/pull + config discovery for config repos
      (GitConfigRepo)
"""
