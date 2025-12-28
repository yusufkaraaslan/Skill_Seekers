#!/usr/bin/env python3
"""
Base Adaptor for Multi-LLM Support

Defines the abstract interface that all platform-specific adaptors must implement.
This enables Skill Seekers to generate skills for multiple LLM platforms (Claude, Gemini, ChatGPT).
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class SkillMetadata:
    """Universal skill metadata used across all platforms"""
    name: str
    description: str
    version: str = "1.0.0"
    author: Optional[str] = None
    tags: list[str] = field(default_factory=list)


class SkillAdaptor(ABC):
    """
    Abstract base class for platform-specific skill adaptors.

    Each platform (Claude, Gemini, OpenAI) implements this interface to handle:
    - Platform-specific SKILL.md formatting
    - Platform-specific package structure (ZIP, tar.gz, etc.)
    - Platform-specific upload endpoints and authentication
    - Optional AI enhancement capabilities
    """

    # Platform identifiers (override in subclasses)
    PLATFORM: str = "unknown"              # e.g., "claude", "gemini", "openai"
    PLATFORM_NAME: str = "Unknown"          # e.g., "Claude AI (Anthropic)"
    DEFAULT_API_ENDPOINT: Optional[str] = None

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize adaptor with optional configuration.

        Args:
            config: Platform-specific configuration options
        """
        self.config = config or {}

    @abstractmethod
    def format_skill_md(self, skill_dir: Path, metadata: SkillMetadata) -> str:
        """
        Format SKILL.md content with platform-specific frontmatter/structure.

        Different platforms require different formats:
        - Claude: YAML frontmatter + markdown
        - Gemini: Plain markdown (no frontmatter)
        - OpenAI: Assistant instructions format

        Args:
            skill_dir: Path to skill directory containing references/
            metadata: Skill metadata (name, description, version, etc.)

        Returns:
            Formatted SKILL.md content as string
        """
        pass

    @abstractmethod
    def package(self, skill_dir: Path, output_path: Path) -> Path:
        """
        Package skill for platform (ZIP, tar.gz, etc.).

        Different platforms require different package formats:
        - Claude: .zip with SKILL.md, references/, scripts/, assets/
        - Gemini: .tar.gz with system_instructions.md, references/
        - OpenAI: .zip with assistant_instructions.txt, vector_store_files/

        Args:
            skill_dir: Path to skill directory to package
            output_path: Path for output package (file or directory)

        Returns:
            Path to created package file
        """
        pass

    @abstractmethod
    def upload(self, package_path: Path, api_key: str, **kwargs) -> Dict[str, Any]:
        """
        Upload packaged skill to platform.

        Returns a standardized response dictionary for all platforms.

        Args:
            package_path: Path to packaged skill file
            api_key: Platform API key
            **kwargs: Additional platform-specific arguments

        Returns:
            Dictionary with keys:
            - success (bool): Whether upload succeeded
            - skill_id (str|None): Platform-specific skill/assistant ID
            - url (str|None): URL to view/manage skill
            - message (str): Success or error message
        """
        pass

    def validate_api_key(self, api_key: str) -> bool:
        """
        Validate API key format for this platform.

        Default implementation just checks if key is non-empty.
        Override for platform-specific validation.

        Args:
            api_key: API key to validate

        Returns:
            True if key format is valid
        """
        return bool(api_key and api_key.strip())

    def get_env_var_name(self) -> str:
        """
        Get expected environment variable name for API key.

        Returns:
            Environment variable name (e.g., "ANTHROPIC_API_KEY", "GOOGLE_API_KEY")
        """
        return f"{self.PLATFORM.upper()}_API_KEY"

    def supports_enhancement(self) -> bool:
        """
        Whether this platform supports AI-powered SKILL.md enhancement.

        Returns:
            True if platform can enhance skills
        """
        return False

    def enhance(self, skill_dir: Path, api_key: str) -> bool:
        """
        Optionally enhance SKILL.md using platform's AI.

        Only called if supports_enhancement() returns True.

        Args:
            skill_dir: Path to skill directory
            api_key: Platform API key

        Returns:
            True if enhancement succeeded
        """
        return False

    def _read_existing_content(self, skill_dir: Path) -> str:
        """
        Helper to read existing SKILL.md content (without frontmatter).

        Args:
            skill_dir: Path to skill directory

        Returns:
            SKILL.md content without YAML frontmatter
        """
        skill_md_path = skill_dir / "SKILL.md"
        if not skill_md_path.exists():
            return ""

        content = skill_md_path.read_text(encoding='utf-8')

        # Strip YAML frontmatter if present
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                return parts[2].strip()

        return content

    def _extract_quick_reference(self, skill_dir: Path) -> str:
        """
        Helper to extract quick reference section from references.

        Args:
            skill_dir: Path to skill directory

        Returns:
            Quick reference content as markdown string
        """
        index_path = skill_dir / "references" / "index.md"
        if not index_path.exists():
            return "See references/ directory for documentation."

        # Read index and extract relevant sections
        content = index_path.read_text(encoding='utf-8')
        return content[:500] + "..." if len(content) > 500 else content

    def _generate_toc(self, skill_dir: Path) -> str:
        """
        Helper to generate table of contents from references.

        Args:
            skill_dir: Path to skill directory

        Returns:
            Table of contents as markdown string
        """
        refs_dir = skill_dir / "references"
        if not refs_dir.exists():
            return ""

        toc_lines = []
        for ref_file in sorted(refs_dir.glob("*.md")):
            if ref_file.name == "index.md":
                continue
            title = ref_file.stem.replace('_', ' ').title()
            toc_lines.append(f"- [{title}](references/{ref_file.name})")

        return "\n".join(toc_lines)
