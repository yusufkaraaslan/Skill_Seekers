"""ExecutionContext - Single source of truth for all configuration.

This module provides a singleton context object that holds all resolved
configuration from CLI args, config files, and environment variables.
All components read from this context instead of parsing their own argv.

Example:
    >>> from skill_seekers.cli.execution_context import ExecutionContext
    >>> ctx = ExecutionContext.initialize(args=parsed_args)
    >>> ctx = ExecutionContext.get()  # Get initialized instance
    >>> print(ctx.output.name)
    >>> print(ctx.enhancement.agent)
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import threading
from pathlib import Path
from typing import Any, ClassVar
from collections.abc import Generator

from pydantic import BaseModel, Field, PrivateAttr

logger = logging.getLogger(__name__)


class SourceInfoConfig(BaseModel):
    """Source detection results."""

    type: str = Field(..., description="Source type (web, github, pdf, etc.)")
    raw_source: str = Field(..., description="Original user input")
    parsed: dict[str, Any] = Field(default_factory=dict, description="Parsed source details")
    suggested_name: str = Field(default="", description="Auto-generated skill name")


class EnhancementSettings(BaseModel):
    """AI enhancement configuration."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "enabled": True,
                "level": 2,
                "mode": "auto",
                "agent": "kimi",
                "timeout": 2700,
            }
        }
    }

    enabled: bool = Field(default=True, description="Whether enhancement is enabled")
    level: int = Field(default=2, ge=0, le=3, description="Enhancement level (0-3)")
    mode: str = Field(default="auto", description="Mode: api, local, or auto")
    agent: str | None = Field(default=None, description="Local agent name (claude, kimi, etc.)")
    agent_cmd: str | None = Field(default=None, description="Custom agent command override")
    api_key: str | None = Field(default=None, description="API key for enhancement")
    timeout: int = Field(default=2700, description="Timeout in seconds (default: 45min)")
    workflows: list[str] = Field(default_factory=list, description="Enhancement workflow names")
    stages: list[str] = Field(default_factory=list, description="Inline enhancement stages")
    workflow_vars: dict[str, str] = Field(default_factory=dict, description="Workflow variables")


class OutputSettings(BaseModel):
    """Output configuration."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "react-docs",
                "doc_version": "18.2",
                "dry_run": False,
            }
        }
    }

    name: str | None = Field(default=None, description="Skill name")
    output_dir: str | None = Field(default=None, description="Output directory override")
    doc_version: str = Field(default="", description="Documentation version tag")
    dry_run: bool = Field(default=False, description="Preview mode without execution")


class ScrapingSettings(BaseModel):
    """Web scraping configuration."""

    max_pages: int | None = Field(default=None, description="Maximum pages to scrape")
    rate_limit: float | None = Field(default=None, description="Rate limit in seconds")
    browser: bool = Field(default=False, description="Use headless browser for JS sites")
    browser_wait_until: str = Field(
        default="domcontentloaded", description="Browser wait condition"
    )
    browser_extra_wait: int = Field(default=0, description="Extra wait time in ms after page load")
    workers: int = Field(default=1, description="Number of parallel workers")
    async_mode: bool = Field(default=False, description="Enable async mode")
    resume: bool = Field(default=False, description="Resume from checkpoint")
    fresh: bool = Field(default=False, description="Clear checkpoint and start fresh")
    skip_scrape: bool = Field(default=False, description="Skip scraping, use existing data")
    languages: list[str] = Field(default_factory=lambda: ["en"], description="Language preferences")


class AnalysisSettings(BaseModel):
    """Code analysis configuration."""

    depth: str = Field(default="surface", description="Analysis depth: surface, deep, full")
    skip_patterns: bool = Field(default=False, description="Skip design pattern detection")
    skip_test_examples: bool = Field(default=False, description="Skip test example extraction")
    skip_how_to_guides: bool = Field(default=False, description="Skip how-to guide generation")
    skip_config_patterns: bool = Field(default=False, description="Skip config pattern extraction")
    skip_api_reference: bool = Field(default=False, description="Skip API reference generation")
    skip_dependency_graph: bool = Field(default=False, description="Skip dependency graph")
    skip_docs: bool = Field(default=False, description="Skip documentation extraction")
    no_comments: bool = Field(default=False, description="Skip comment extraction")
    file_patterns: list[str] | None = Field(default=None, description="File patterns to analyze")


class RAGSettings(BaseModel):
    """RAG (Retrieval-Augmented Generation) configuration."""

    chunk_for_rag: bool = Field(default=False, description="Enable semantic chunking")
    chunk_tokens: int = Field(default=512, description="Chunk size in tokens")
    chunk_overlap_tokens: int = Field(default=50, description="Overlap between chunks")
    preserve_code_blocks: bool = Field(default=True, description="Don't split code blocks")
    preserve_paragraphs: bool = Field(default=True, description="Respect paragraph boundaries")


class ExecutionContext(BaseModel):
    """Single source of truth for all execution configuration.

    This is a singleton - use ExecutionContext.get() to access the instance.
    Initialize once at entry point with ExecutionContext.initialize().

    Example:
        >>> ctx = ExecutionContext.initialize(args=parsed_args)
        >>> ctx = ExecutionContext.get()  # Get initialized instance
        >>> print(ctx.output.name)
    """

    model_config = {
        "json_schema_extra": {
            "example": {
                "source": {"type": "web", "raw_source": "https://react.dev/"},
                "enhancement": {"level": 2, "agent": "kimi"},
                "output": {"name": "react-docs"},
            }
        }
    }

    # Configuration sections
    source: SourceInfoConfig | None = Field(default=None, description="Source information")
    enhancement: EnhancementSettings = Field(default_factory=EnhancementSettings)
    output: OutputSettings = Field(default_factory=OutputSettings)
    scraping: ScrapingSettings = Field(default_factory=ScrapingSettings)
    analysis: AnalysisSettings = Field(default_factory=AnalysisSettings)
    rag: RAGSettings = Field(default_factory=RAGSettings)

    # Private attributes
    _raw_args: dict[str, Any] = PrivateAttr(default_factory=dict)

    # Singleton storage (class-level)
    _instance: ClassVar[ExecutionContext | None] = None
    _lock: ClassVar[threading.Lock] = threading.Lock()
    _initialized: ClassVar[bool] = False

    @classmethod
    def get(cls) -> ExecutionContext:
        """Get the singleton instance.

        Raises:
            RuntimeError: If context hasn't been initialized
        """
        if cls._instance is None:
            raise RuntimeError(
                "ExecutionContext not initialized. Call ExecutionContext.initialize() first."
            )
        return cls._instance

    @classmethod
    def initialize(
        cls,
        args: Any | None = None,
        config_path: str | None = None,
        source_info: Any | None = None,
    ) -> ExecutionContext:
        """Initialize the singleton context.

        Priority (highest to lowest):
        1. CLI args (explicit user input)
        2. Config file (JSON config)
        3. Environment variables
        4. Defaults

        Args:
            args: Parsed argparse.Namespace
            config_path: Path to config JSON file
            source_info: SourceInfo from source_detector

        Returns:
            Initialized ExecutionContext instance
        """
        with cls._lock:
            if cls._initialized:
                logger.debug(
                    "ExecutionContext.initialize() called again — returning existing instance. "
                    "Use ExecutionContext.reset() first if re-initialization is intended."
                )
                return cls._instance

            context_data = cls._build_from_sources(args, config_path, source_info)
            cls._instance = cls.model_validate(context_data)
            if args:
                cls._instance._raw_args = vars(args)
            cls._initialized = True
            return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton (mainly for testing)."""
        with cls._lock:
            cls._instance = None
            cls._initialized = False

    @classmethod
    def _build_from_sources(
        cls,
        args: Any | None,
        config_path: str | None,
        source_info: Any | None,
    ) -> dict[str, Any]:
        """Build context dict from all configuration sources."""
        # Start with defaults
        data = cls._default_data()

        # Layer 1: Config file
        if config_path:
            file_config = cls._load_config_file(config_path)
            data = cls._deep_merge(data, file_config)

        # Layer 2: CLI args (override config file)
        if args:
            arg_config = cls._args_to_data(args)
            data = cls._deep_merge(data, arg_config)

        # Layer 3: Source info
        if source_info:
            data["source"] = {
                "type": source_info.type,
                "raw_source": source_info.raw_source,
                "parsed": source_info.parsed,
                "suggested_name": source_info.suggested_name,
            }

        return data

    @classmethod
    def _default_data(cls) -> dict[str, Any]:
        """Get default configuration."""
        from skill_seekers.cli.agent_client import get_default_timeout

        return {
            "enhancement": {
                "enabled": True,
                "level": 2,
                # Env-var-based mode detection (lowest priority — CLI and config override this)
                "mode": "api"
                if any(
                    os.environ.get(k)
                    for k in (
                        "ANTHROPIC_API_KEY",
                        "OPENAI_API_KEY",
                        "MOONSHOT_API_KEY",
                        "GOOGLE_API_KEY",
                    )
                )
                else "auto",
                "agent": os.environ.get("SKILL_SEEKER_AGENT"),
                "agent_cmd": None,
                "api_key": None,
                "timeout": get_default_timeout(),
                "workflows": [],
                "stages": [],
                "workflow_vars": {},
            },
            "output": {
                "name": None,
                "output_dir": None,
                "doc_version": "",
                "dry_run": False,
            },
            "scraping": {
                "max_pages": None,
                "rate_limit": None,
                "browser": False,
                "browser_wait_until": "domcontentloaded",
                "browser_extra_wait": 0,
                "workers": 1,
                "async_mode": False,
                "resume": False,
                "fresh": False,
                "skip_scrape": False,
                "languages": ["en"],
            },
            "analysis": {
                "depth": "surface",
                "skip_patterns": False,
                "skip_test_examples": False,
                "skip_how_to_guides": False,
                "skip_config_patterns": False,
                "skip_api_reference": False,
                "skip_dependency_graph": False,
                "skip_docs": False,
                "no_comments": False,
                "file_patterns": None,
            },
            "rag": {
                "chunk_for_rag": False,
                "chunk_tokens": 512,
                "chunk_overlap_tokens": 50,
                "preserve_code_blocks": True,
                "preserve_paragraphs": True,
            },
        }

    @classmethod
    def _load_config_file(cls, config_path: str) -> dict[str, Any]:
        """Load and normalize config file."""
        path = Path(config_path)
        try:
            with open(path, encoding="utf-8") as f:
                file_data = json.load(f)
        except FileNotFoundError:
            raise ValueError(f"Config file not found: {config_path}") from None
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file {config_path}: {e}") from None

        config: dict[str, Any] = {}

        # Unified config format (sources array)
        if "sources" in file_data:
            enhancement = file_data.get("enhancement", {})

            # Handle timeout field (can be "unlimited" or integer)
            timeout_val = enhancement.get("timeout", 2700)
            if isinstance(timeout_val, str) and timeout_val.lower() in ("unlimited", "none"):
                from skill_seekers.cli.agent_client import UNLIMITED_TIMEOUT

                timeout_val = UNLIMITED_TIMEOUT

            config["output"] = {
                "name": file_data.get("name"),
                "doc_version": file_data.get("version", ""),
            }
            config["enhancement"] = {
                "enabled": enhancement.get("enabled", True),
                "level": enhancement.get("level", 2),
                "mode": enhancement.get("mode", "auto").lower(),
                "agent": enhancement.get("agent"),
                "timeout": timeout_val,
                "workflows": file_data.get("workflows", []),
                "stages": file_data.get("workflow_stages", []),
                "workflow_vars": file_data.get("workflow_vars", {}),
            }

        # Simple web config format
        elif "base_url" in file_data:
            config["output"] = {
                "name": file_data.get("name"),
                "doc_version": file_data.get("version", ""),
            }
            config["scraping"] = {
                "max_pages": file_data.get("max_pages"),
                "rate_limit": file_data.get("rate_limit"),
                "browser": file_data.get("browser", False),
            }

        return config

    @classmethod
    def _args_to_data(cls, args: Any) -> dict[str, Any]:
        """Convert argparse.Namespace to config dict."""
        config: dict[str, Any] = {}

        # Output
        if hasattr(args, "name") and args.name is not None:
            config.setdefault("output", {})["name"] = args.name
        if hasattr(args, "output") and args.output is not None:
            config.setdefault("output", {})["output_dir"] = args.output
        if hasattr(args, "doc_version") and args.doc_version:
            config.setdefault("output", {})["doc_version"] = args.doc_version
        if getattr(args, "dry_run", False):
            config.setdefault("output", {})["dry_run"] = True

        # Enhancement
        if hasattr(args, "enhance_level") and args.enhance_level is not None:
            config.setdefault("enhancement", {})["level"] = args.enhance_level
        if getattr(args, "agent", None):
            config.setdefault("enhancement", {})["agent"] = args.agent
        if getattr(args, "agent_cmd", None):
            config.setdefault("enhancement", {})["agent_cmd"] = args.agent_cmd
        if getattr(args, "api_key", None):
            config.setdefault("enhancement", {})["api_key"] = args.api_key

        # Only set mode when user explicitly passed --api-key on CLI.
        # Env-var-based mode detection belongs in _default_data(), not here,
        # to preserve the priority: CLI args > Config file > Env vars > Defaults.
        if getattr(args, "api_key", None):
            config.setdefault("enhancement", {})["mode"] = "api"

        # Workflows
        if getattr(args, "enhance_workflow", None):
            config.setdefault("enhancement", {})["workflows"] = list(args.enhance_workflow)
        if getattr(args, "enhance_stage", None):
            config.setdefault("enhancement", {})["stages"] = list(args.enhance_stage)
        if getattr(args, "var", None):
            config.setdefault("enhancement", {})["workflow_vars"] = cls._parse_vars(args.var)

        # Scraping
        if hasattr(args, "max_pages") and args.max_pages is not None:
            config.setdefault("scraping", {})["max_pages"] = args.max_pages
        if hasattr(args, "rate_limit") and args.rate_limit is not None:
            config.setdefault("scraping", {})["rate_limit"] = args.rate_limit
        if getattr(args, "browser", False):
            config.setdefault("scraping", {})["browser"] = True
        if hasattr(args, "workers") and args.workers:
            config.setdefault("scraping", {})["workers"] = args.workers
        if getattr(args, "async_mode", False):
            config.setdefault("scraping", {})["async_mode"] = True
        if getattr(args, "resume", False):
            config.setdefault("scraping", {})["resume"] = True
        if getattr(args, "fresh", False):
            config.setdefault("scraping", {})["fresh"] = True
        if getattr(args, "skip_scrape", False):
            config.setdefault("scraping", {})["skip_scrape"] = True

        # Analysis
        if getattr(args, "depth", None):
            config.setdefault("analysis", {})["depth"] = args.depth
        if getattr(args, "skip_patterns", False):
            config.setdefault("analysis", {})["skip_patterns"] = True
        if getattr(args, "skip_test_examples", False):
            config.setdefault("analysis", {})["skip_test_examples"] = True
        if getattr(args, "skip_how_to_guides", False):
            config.setdefault("analysis", {})["skip_how_to_guides"] = True
        if getattr(args, "file_patterns", None):
            config.setdefault("analysis", {})["file_patterns"] = [
                p.strip() for p in args.file_patterns.split(",")
            ]

        # RAG
        if getattr(args, "chunk_for_rag", False):
            config.setdefault("rag", {})["chunk_for_rag"] = True
        if hasattr(args, "chunk_tokens") and args.chunk_tokens is not None:
            config.setdefault("rag", {})["chunk_tokens"] = args.chunk_tokens

        return config

    @staticmethod
    def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Deep merge override into base."""
        result = base.copy()
        for key, value in override.items():
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                result[key] = ExecutionContext._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    @staticmethod
    def _parse_vars(var_list: list[str]) -> dict[str, str]:
        """Parse --var key=value into dict."""
        result = {}
        for var in var_list:
            if "=" in var:
                key, value = var.split("=", 1)
                result[key] = value
        return result

    def get_raw(self, name: str, default: Any = None) -> Any:
        """Get raw argument value (backward compatibility)."""
        return self._raw_args.get(name, default)

    def get_agent_client(self) -> Any:
        """Get configured AgentClient from context."""
        from skill_seekers.cli.agent_client import AgentClient

        return AgentClient(mode=self.enhancement.mode, agent=self.enhancement.agent)

    @contextlib.contextmanager
    def override(self, **kwargs: Any) -> Generator[ExecutionContext, None, None]:
        """Temporarily override context values.

        Usage:
            with ctx.override(enhancement__level=3):
                run_workflow()  # Uses level 3
            # Original values restored
        """
        # Create new data with overrides
        current_data = self.model_dump(exclude={"_raw_args"})

        for key, value in kwargs.items():
            if "__" in key:
                parts = key.split("__")
                target = current_data
                for part in parts[:-1]:
                    target = target.setdefault(part, {})
                target[parts[-1]] = value
            else:
                current_data[key] = value

        # Create temporary instance and preserve _raw_args
        temp_ctx = self.__class__.model_validate(current_data)
        temp_ctx._raw_args = dict(self._raw_args)  # Copy raw args to temp context

        with self._lock:
            previous = self._instance
            self.__class__._instance = temp_ctx

        try:
            yield temp_ctx
        finally:
            with self._lock:
                self.__class__._instance = previous


def get_context() -> ExecutionContext:
    """Shortcut for ExecutionContext.get()."""
    return ExecutionContext.get()
