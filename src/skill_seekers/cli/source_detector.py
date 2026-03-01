"""Source type detection for unified create command.

Auto-detects whether a source is a web URL, GitHub repository,
local directory, PDF file, or config file based on patterns.
"""

import os
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


@dataclass
class SourceInfo:
    """Information about a detected source.

    Attributes:
        type: Source type ('web', 'github', 'local', 'pdf', 'config')
        parsed: Parsed source information (e.g., {'url': '...'}, {'repo': '...'})
        suggested_name: Auto-suggested name for the skill
        raw_input: Original user input
    """

    type: str
    parsed: dict[str, Any]
    suggested_name: str
    raw_input: str


class SourceDetector:
    """Detects source type from user input and extracts relevant information."""

    # GitHub repo patterns
    GITHUB_REPO_PATTERN = re.compile(r"^([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)$")
    GITHUB_URL_PATTERN = re.compile(
        r"(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)(?:\.git)?"
    )

    @classmethod
    def detect(cls, source: str) -> SourceInfo:
        """Detect source type and extract information.

        Args:
            source: User input (URL, path, repo, etc.)

        Returns:
            SourceInfo object with detected type and parsed data

        Raises:
            ValueError: If source type cannot be determined
        """
        # 1. File extension detection
        if source.endswith(".json"):
            return cls._detect_config(source)

        if source.endswith(".pdf"):
            return cls._detect_pdf(source)

        if source.endswith(".docx"):
            return cls._detect_word(source)

        # Video file extensions
        VIDEO_EXTENSIONS = (".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv")
        if source.lower().endswith(VIDEO_EXTENSIONS):
            return cls._detect_video_file(source)

        # 2. Video URL detection (before directory check)
        video_url_info = cls._detect_video_url(source)
        if video_url_info:
            return video_url_info

        # 3. Directory detection
        if os.path.isdir(source):
            return cls._detect_local(source)

        # 4. GitHub patterns
        github_info = cls._detect_github(source)
        if github_info:
            return github_info

        # 5. URL detection
        if source.startswith("http://") or source.startswith("https://"):
            return cls._detect_web(source)

        # 6. Domain inference (add https://)
        if "." in source and not source.startswith("/"):
            return cls._detect_web(f"https://{source}")

        # 7. Error - cannot determine
        raise ValueError(
            f"Cannot determine source type for: {source}\n\n"
            "Examples:\n"
            "  Web:    skill-seekers create https://docs.react.dev/\n"
            "  GitHub: skill-seekers create facebook/react\n"
            "  Local:  skill-seekers create ./my-project\n"
            "  PDF:    skill-seekers create tutorial.pdf\n"
            "  DOCX:   skill-seekers create document.docx\n"
            "  Video:  skill-seekers create https://youtube.com/watch?v=...\n"
            "  Video:  skill-seekers create recording.mp4\n"
            "  Config: skill-seekers create configs/react.json"
        )

    @classmethod
    def _detect_config(cls, source: str) -> SourceInfo:
        """Detect config file source."""
        name = os.path.splitext(os.path.basename(source))[0]
        return SourceInfo(
            type="config", parsed={"config_path": source}, suggested_name=name, raw_input=source
        )

    @classmethod
    def _detect_pdf(cls, source: str) -> SourceInfo:
        """Detect PDF file source."""
        name = os.path.splitext(os.path.basename(source))[0]
        return SourceInfo(
            type="pdf", parsed={"file_path": source}, suggested_name=name, raw_input=source
        )

    @classmethod
    def _detect_word(cls, source: str) -> SourceInfo:
        """Detect Word document (.docx) source."""
        name = os.path.splitext(os.path.basename(source))[0]
        return SourceInfo(
            type="word", parsed={"file_path": source}, suggested_name=name, raw_input=source
        )

    @classmethod
    def _detect_video_file(cls, source: str) -> SourceInfo:
        """Detect local video file source."""
        name = os.path.splitext(os.path.basename(source))[0]
        return SourceInfo(
            type="video",
            parsed={"file_path": source, "source_kind": "file"},
            suggested_name=name,
            raw_input=source,
        )

    @classmethod
    def _detect_video_url(cls, source: str) -> SourceInfo | None:
        """Detect video platform URL (YouTube, Vimeo).

        Returns SourceInfo if the source is a video URL, None otherwise.
        """
        lower = source.lower()

        # YouTube patterns
        youtube_keywords = [
            "youtube.com/watch",
            "youtu.be/",
            "youtube.com/playlist",
            "youtube.com/@",
            "youtube.com/channel/",
            "youtube.com/c/",
            "youtube.com/shorts/",
            "youtube.com/embed/",
        ]
        if any(kw in lower for kw in youtube_keywords):
            # Determine suggested name
            if "playlist" in lower:
                name = "youtube_playlist"
            elif "/@" in lower or "/channel/" in lower or "/c/" in lower:
                name = "youtube_channel"
            else:
                name = "youtube_video"
            return SourceInfo(
                type="video",
                parsed={"url": source, "source_kind": "url"},
                suggested_name=name,
                raw_input=source,
            )

        # Vimeo patterns
        if "vimeo.com/" in lower:
            return SourceInfo(
                type="video",
                parsed={"url": source, "source_kind": "url"},
                suggested_name="vimeo_video",
                raw_input=source,
            )

        return None

    @classmethod
    def _detect_local(cls, source: str) -> SourceInfo:
        """Detect local directory source."""
        # Clean up path
        directory = os.path.abspath(source)
        name = os.path.basename(directory)

        return SourceInfo(
            type="local", parsed={"directory": directory}, suggested_name=name, raw_input=source
        )

    @classmethod
    def _detect_github(cls, source: str) -> SourceInfo | None:
        """Detect GitHub repository source.

        Supports patterns:
        - owner/repo
        - github.com/owner/repo
        - https://github.com/owner/repo
        """
        # Try simple owner/repo pattern first
        match = cls.GITHUB_REPO_PATTERN.match(source)
        if match:
            owner, repo = match.groups()
            return SourceInfo(
                type="github",
                parsed={"repo": f"{owner}/{repo}"},
                suggested_name=repo,
                raw_input=source,
            )

        # Try GitHub URL pattern
        match = cls.GITHUB_URL_PATTERN.search(source)
        if match:
            owner, repo = match.groups()
            # Clean up repo name (remove .git suffix if present)
            if repo.endswith(".git"):
                repo = repo[:-4]
            return SourceInfo(
                type="github",
                parsed={"repo": f"{owner}/{repo}"},
                suggested_name=repo,
                raw_input=source,
            )

        return None

    @classmethod
    def _detect_web(cls, source: str) -> SourceInfo:
        """Detect web documentation source."""
        # Parse URL to extract domain for suggested name
        parsed_url = urlparse(source)
        domain = parsed_url.netloc or parsed_url.path

        # Clean up domain for name suggestion
        # docs.react.dev -> react
        # reactjs.org -> react
        name = domain.replace("www.", "").replace("docs.", "")
        name = name.split(".")[0]  # Take first part before TLD

        return SourceInfo(type="web", parsed={"url": source}, suggested_name=name, raw_input=source)

    @classmethod
    def validate_source(cls, source_info: SourceInfo) -> None:
        """Validate that source is accessible.

        Args:
            source_info: Detected source information

        Raises:
            ValueError: If source is not accessible
        """
        if source_info.type == "local":
            directory = source_info.parsed["directory"]
            if not os.path.exists(directory):
                raise ValueError(f"Directory does not exist: {directory}")
            if not os.path.isdir(directory):
                raise ValueError(f"Path is not a directory: {directory}")

        elif source_info.type == "pdf":
            file_path = source_info.parsed["file_path"]
            if not os.path.exists(file_path):
                raise ValueError(f"PDF file does not exist: {file_path}")
            if not os.path.isfile(file_path):
                raise ValueError(f"Path is not a file: {file_path}")

        elif source_info.type == "word":
            file_path = source_info.parsed["file_path"]
            if not os.path.exists(file_path):
                raise ValueError(f"Word document does not exist: {file_path}")
            if not os.path.isfile(file_path):
                raise ValueError(f"Path is not a file: {file_path}")

        elif source_info.type == "video":
            if source_info.parsed.get("source_kind") == "file":
                file_path = source_info.parsed["file_path"]
                if not os.path.exists(file_path):
                    raise ValueError(f"Video file does not exist: {file_path}")
                if not os.path.isfile(file_path):
                    raise ValueError(f"Path is not a file: {file_path}")
            # URL-based video sources are validated during processing

        elif source_info.type == "config":
            config_path = source_info.parsed["config_path"]
            if not os.path.exists(config_path):
                raise ValueError(f"Config file does not exist: {config_path}")
            if not os.path.isfile(config_path):
                raise ValueError(f"Path is not a file: {config_path}")

        # For web and github, validation happens during scraping
        # (URL accessibility, repo existence)
