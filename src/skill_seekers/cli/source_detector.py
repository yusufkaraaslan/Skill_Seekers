"""Source type detection for unified create command.

Auto-detects source type from user input — supports web URLs, GitHub repos,
local directories, and 14+ file types (PDF, DOCX, EPUB, IPYNB, HTML, YAML/OpenAPI,
AsciiDoc, PPTX, RSS/Atom, man pages, video files, and config JSON).

Note: Confluence, Notion, and Slack/Discord chat sources are API/export-based
and cannot be auto-detected from a single argument. Use their dedicated
subcommands (``skill-seekers confluence``, ``notion``, ``chat``) instead.
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

        if source.endswith(".epub"):
            return cls._detect_epub(source)

        if source.endswith(".ipynb"):
            return cls._detect_jupyter(source)

        if source.lower().endswith((".html", ".htm")):
            return cls._detect_html(source)

        if source.endswith(".pptx"):
            return cls._detect_pptx(source)

        if source.lower().endswith((".adoc", ".asciidoc")):
            return cls._detect_asciidoc(source)

        # Man page file extensions (.1 through .8, .man)
        # Only match if the basename looks like a man page (e.g., "git.1", not "log.1")
        # Require basename without the extension to be a plausible command name
        if source.lower().endswith(".man"):
            return cls._detect_manpage(source)
        MAN_SECTION_EXTENSIONS = (".1", ".2", ".3", ".4", ".5", ".6", ".7", ".8")
        if source.lower().endswith(MAN_SECTION_EXTENSIONS):
            # Heuristic: man pages have a simple basename (no dots before extension)
            # e.g., "git.1" is a man page, "access.log.1" is not
            basename_no_ext = os.path.splitext(os.path.basename(source))[0]
            if "." not in basename_no_ext:
                return cls._detect_manpage(source)

        # Video file extensions
        VIDEO_EXTENSIONS = (".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv")
        if source.lower().endswith(VIDEO_EXTENSIONS):
            return cls._detect_video_file(source)

        # RSS/Atom feed file extensions (only .rss and .atom — .xml is too generic)
        if source.lower().endswith((".rss", ".atom")):
            return cls._detect_rss(source)

        # OpenAPI/Swagger spec detection (YAML files with OpenAPI content)
        # Sniff file content for 'openapi:' or 'swagger:' keys before committing
        if (
            source.lower().endswith((".yaml", ".yml"))
            and os.path.isfile(source)
            and cls._looks_like_openapi(source)
        ):
            return cls._detect_openapi(source)

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
            "  Web:        skill-seekers create https://docs.react.dev/\n"
            "  GitHub:     skill-seekers create facebook/react\n"
            "  Local:      skill-seekers create ./my-project\n"
            "  PDF:        skill-seekers create tutorial.pdf\n"
            "  DOCX:       skill-seekers create document.docx\n"
            "  EPUB:       skill-seekers create ebook.epub\n"
            "  Jupyter:    skill-seekers create notebook.ipynb\n"
            "  HTML:       skill-seekers create page.html\n"
            "  OpenAPI:    skill-seekers create openapi.yaml\n"
            "  AsciiDoc:   skill-seekers create document.adoc\n"
            "  PowerPoint: skill-seekers create presentation.pptx\n"
            "  RSS:        skill-seekers create feed.rss\n"
            "  Man page:   skill-seekers create command.1\n"
            "  Video:      skill-seekers create https://youtube.com/watch?v=...\n"
            "  Video:      skill-seekers create recording.mp4\n"
            "  Config:     skill-seekers create configs/react.json"
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
    def _detect_epub(cls, source: str) -> SourceInfo:
        """Detect EPUB file source."""
        name = os.path.splitext(os.path.basename(source))[0]
        return SourceInfo(
            type="epub", parsed={"file_path": source}, suggested_name=name, raw_input=source
        )

    @classmethod
    def _detect_jupyter(cls, source: str) -> SourceInfo:
        """Detect Jupyter Notebook file source."""
        name = os.path.splitext(os.path.basename(source))[0]
        return SourceInfo(
            type="jupyter", parsed={"file_path": source}, suggested_name=name, raw_input=source
        )

    @classmethod
    def _detect_html(cls, source: str) -> SourceInfo:
        """Detect HTML source — URL or local file.
        
        Tries to fetch from internet first, then falls back to local file.
        If source is a URL (http:// or https://), route to web scraper.
        If source is a local file path, route to html_scraper.
        """
        # Check if source is a URL
        if source.startswith("http://") or source.startswith("https://"):
            # Route to web scraper for URL-based HTML
            return cls._detect_web(source)
        
        # Otherwise treat as local file
        name = os.path.splitext(os.path.basename(source))[0]
        return SourceInfo(
            type="html", parsed={"file_path": source}, suggested_name=name, raw_input=source
        )

    @classmethod
    def _detect_pptx(cls, source: str) -> SourceInfo:
        """Detect PowerPoint file source."""
        name = os.path.splitext(os.path.basename(source))[0]
        return SourceInfo(
            type="pptx", parsed={"file_path": source}, suggested_name=name, raw_input=source
        )

    @classmethod
    def _detect_asciidoc(cls, source: str) -> SourceInfo:
        """Detect AsciiDoc file source."""
        name = os.path.splitext(os.path.basename(source))[0]
        return SourceInfo(
            type="asciidoc", parsed={"file_path": source}, suggested_name=name, raw_input=source
        )

    @classmethod
    def _detect_manpage(cls, source: str) -> SourceInfo:
        """Detect man page file source."""
        name = os.path.splitext(os.path.basename(source))[0]
        return SourceInfo(
            type="manpage", parsed={"file_path": source}, suggested_name=name, raw_input=source
        )

    @classmethod
    def _detect_rss(cls, source: str) -> SourceInfo:
        """Detect RSS/Atom feed file source."""
        name = os.path.splitext(os.path.basename(source))[0]
        return SourceInfo(
            type="rss", parsed={"file_path": source}, suggested_name=name, raw_input=source
        )

    @classmethod
    def _looks_like_openapi(cls, source: str) -> bool:
        """Check if a YAML/JSON file looks like an OpenAPI or Swagger spec.

        Reads the first few lines to look for 'openapi:' or 'swagger:' keys.

        Args:
            source: Path to the file

        Returns:
            True if the file appears to be an OpenAPI/Swagger spec
        """
        try:
            with open(source, encoding="utf-8", errors="replace") as f:
                # Read first 20 lines — the openapi/swagger key is always near the top
                for _ in range(20):
                    line = f.readline()
                    if not line:
                        break
                    stripped = line.strip().lower()
                    if stripped.startswith("openapi:") or stripped.startswith("swagger:"):
                        return True
                    if stripped.startswith('"openapi"') or stripped.startswith('"swagger"'):
                        return True
        except OSError:
            pass
        return False

    @classmethod
    def _detect_openapi(cls, source: str) -> SourceInfo:
        """Detect OpenAPI/Swagger spec file source."""
        name = os.path.splitext(os.path.basename(source))[0]
        return SourceInfo(
            type="openapi", parsed={"file_path": source}, suggested_name=name, raw_input=source
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

        elif source_info.type == "epub":
            file_path = source_info.parsed["file_path"]
            if not os.path.exists(file_path):
                raise ValueError(f"EPUB file does not exist: {file_path}")
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

        elif source_info.type in ("jupyter", "html", "pptx", "asciidoc", "manpage", "openapi"):
            file_path = source_info.parsed.get("file_path", "")
            if file_path:
                type_label = source_info.type.upper()
                if not os.path.exists(file_path):
                    raise ValueError(f"{type_label} file does not exist: {file_path}")
                if not os.path.isfile(file_path) and not os.path.isdir(file_path):
                    raise ValueError(f"Path is not a file or directory: {file_path}")

        elif source_info.type == "rss":
            file_path = source_info.parsed.get("file_path", "")
            if file_path and not os.path.exists(file_path):
                raise ValueError(f"RSS/Atom file does not exist: {file_path}")

        # For web, github, confluence, notion, chat, rss (URL), validation happens
        # during scraping (URL accessibility, API auth, etc.)
