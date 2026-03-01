"""Video metadata extraction module.

Uses yt-dlp for metadata extraction without downloading video content.
Supports YouTube, Vimeo, and local video files.
"""

import hashlib
import logging
import os
import re

from skill_seekers.cli.video_models import (
    Chapter,
    VideoInfo,
    VideoSourceType,
)

logger = logging.getLogger(__name__)

# Optional dependency: yt-dlp
try:
    import yt_dlp

    HAS_YTDLP = True
except ImportError:
    HAS_YTDLP = False


# =============================================================================
# Video ID Extraction
# =============================================================================


# YouTube URL patterns
YOUTUBE_PATTERNS = [
    re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})"),
    re.compile(r"(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})"),
    re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})"),
    re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]{11})"),
    re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})"),
]

YOUTUBE_PLAYLIST_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?youtube\.com/playlist\?list=([a-zA-Z0-9_-]+)"
)

YOUTUBE_CHANNEL_PATTERNS = [
    re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/@([a-zA-Z0-9_-]+)"),
    re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/channel/([a-zA-Z0-9_-]+)"),
    re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/c/([a-zA-Z0-9_-]+)"),
]

VIMEO_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?vimeo\.com/(\d+)")


def extract_video_id(url: str) -> str | None:
    """Extract YouTube video ID from various URL formats.

    Args:
        url: YouTube URL in any supported format.

    Returns:
        11-character video ID, or None if not a YouTube URL.
    """
    for pattern in YOUTUBE_PATTERNS:
        match = pattern.search(url)
        if match:
            return match.group(1)
    return None


def detect_video_source_type(url_or_path: str) -> VideoSourceType:
    """Detect the source type of a video URL or file path.

    Args:
        url_or_path: URL or local file path.

    Returns:
        VideoSourceType enum value.
    """
    if os.path.isfile(url_or_path):
        return VideoSourceType.LOCAL_FILE
    if os.path.isdir(url_or_path):
        return VideoSourceType.LOCAL_DIRECTORY

    url_lower = url_or_path.lower()
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return VideoSourceType.YOUTUBE
    if "vimeo.com" in url_lower:
        return VideoSourceType.VIMEO

    return VideoSourceType.LOCAL_FILE


# =============================================================================
# YouTube Metadata via yt-dlp
# =============================================================================


def _check_ytdlp():
    """Raise RuntimeError if yt-dlp is not installed."""
    if not HAS_YTDLP:
        raise RuntimeError(
            "yt-dlp is required for video metadata extraction.\n"
            'Install with: pip install "skill-seekers[video]"\n'
            "Or: pip install yt-dlp"
        )


def extract_youtube_metadata(url: str) -> VideoInfo:
    """Extract metadata from a YouTube video URL without downloading.

    Args:
        url: YouTube video URL.

    Returns:
        VideoInfo with metadata populated.

    Raises:
        RuntimeError: If yt-dlp is not installed.
    """
    _check_ytdlp()

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "skip_download": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    video_id = info.get("id", extract_video_id(url) or "unknown")

    # Parse chapters
    chapters = []
    raw_chapters = info.get("chapters") or []
    for i, ch in enumerate(raw_chapters):
        end_time = ch.get("end_time", 0)
        if i + 1 < len(raw_chapters):
            end_time = raw_chapters[i + 1].get("start_time", end_time)
        chapters.append(
            Chapter(
                title=ch.get("title", f"Chapter {i + 1}"),
                start_time=ch.get("start_time", 0),
                end_time=end_time,
            )
        )

    return VideoInfo(
        video_id=video_id,
        source_type=VideoSourceType.YOUTUBE,
        source_url=url,
        title=info.get("title", ""),
        description=info.get("description", ""),
        duration=float(info.get("duration", 0)),
        upload_date=info.get("upload_date"),
        language=info.get("language") or "en",
        channel_name=info.get("channel") or info.get("uploader"),
        channel_url=info.get("channel_url") or info.get("uploader_url"),
        view_count=info.get("view_count"),
        like_count=info.get("like_count"),
        comment_count=info.get("comment_count"),
        tags=info.get("tags") or [],
        categories=info.get("categories") or [],
        thumbnail_url=info.get("thumbnail"),
        chapters=chapters,
    )


def extract_local_metadata(file_path: str) -> VideoInfo:
    """Extract basic metadata from a local video file.

    Args:
        file_path: Path to video file.

    Returns:
        VideoInfo with basic metadata from filename/file properties.
    """
    path = os.path.abspath(file_path)
    name = os.path.splitext(os.path.basename(path))[0]
    video_id = hashlib.sha256(path.encode()).hexdigest()[:16]

    return VideoInfo(
        video_id=video_id,
        source_type=VideoSourceType.LOCAL_FILE,
        file_path=path,
        title=name.replace("-", " ").replace("_", " ").title(),
        duration=0.0,  # Would need ffprobe for accurate duration
    )


# =============================================================================
# Playlist / Channel Resolution
# =============================================================================


def resolve_playlist(url: str) -> list[str]:
    """Resolve a YouTube playlist URL to a list of video URLs.

    Args:
        url: YouTube playlist URL.

    Returns:
        List of video URLs in playlist order.

    Raises:
        RuntimeError: If yt-dlp is not installed.
    """
    _check_ytdlp()

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    entries = info.get("entries") or []
    video_urls = []
    for entry in entries:
        vid_url = entry.get("url") or entry.get("webpage_url")
        if vid_url:
            video_urls.append(vid_url)
        elif entry.get("id"):
            video_urls.append(f"https://www.youtube.com/watch?v={entry['id']}")

    return video_urls


def resolve_channel(url: str, max_videos: int = 50) -> list[str]:
    """Resolve a YouTube channel URL to a list of recent video URLs.

    Args:
        url: YouTube channel URL.
        max_videos: Maximum number of videos to resolve.

    Returns:
        List of video URLs (most recent first).

    Raises:
        RuntimeError: If yt-dlp is not installed.
    """
    _check_ytdlp()

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
        "playlistend": max_videos,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    entries = info.get("entries") or []
    video_urls = []
    for entry in entries:
        vid_url = entry.get("url") or entry.get("webpage_url")
        if vid_url:
            video_urls.append(vid_url)
        elif entry.get("id"):
            video_urls.append(f"https://www.youtube.com/watch?v={entry['id']}")

    return video_urls[:max_videos]
