"""Video transcript extraction module.

Handles all transcript acquisition:
- YouTube captions via youtube-transcript-api (Tier 1)
- Subtitle file parsing: SRT and VTT (Tier 1)
- Whisper ASR stub (Tier 2 — raises ImportError with install instructions)
"""

import logging
import re
from pathlib import Path

from skill_seekers.cli.video_models import (
    TranscriptSegment,
    TranscriptSource,
    VideoInfo,
    VideoSourceConfig,
    VideoSourceType,
)

logger = logging.getLogger(__name__)

# Optional dependency: youtube-transcript-api
try:
    from youtube_transcript_api import YouTubeTranscriptApi

    HAS_YOUTUBE_TRANSCRIPT = True
except ImportError:
    HAS_YOUTUBE_TRANSCRIPT = False

# Optional dependency: faster-whisper (Tier 2)
try:
    from faster_whisper import WhisperModel  # noqa: F401

    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False


# =============================================================================
# YouTube Transcript Extraction (Tier 1)
# =============================================================================


def extract_youtube_transcript(
    video_id: str,
    languages: list[str] | None = None,
) -> tuple[list[TranscriptSegment], TranscriptSource]:
    """Fetch YouTube captions via youtube-transcript-api.

    Args:
        video_id: YouTube video ID (11 chars).
        languages: Language preference list (e.g., ['en', 'tr']).

    Returns:
        Tuple of (transcript segments, source type).

    Raises:
        RuntimeError: If youtube-transcript-api is not installed.
    """
    if not HAS_YOUTUBE_TRANSCRIPT:
        raise RuntimeError(
            "youtube-transcript-api is required for YouTube transcript extraction.\n"
            'Install with: pip install "skill-seekers[video]"\n'
            "Or: pip install youtube-transcript-api"
        )

    if languages is None:
        languages = ["en"]

    try:
        ytt_api = YouTubeTranscriptApi()

        # Use list_transcripts to detect whether the transcript is auto-generated
        source = TranscriptSource.YOUTUBE_MANUAL
        try:
            transcript_list = ytt_api.list(video_id)
            # Prefer manually created transcripts; fall back to auto-generated
            try:
                transcript_entry = transcript_list.find_manually_created_transcript(languages)
                source = TranscriptSource.YOUTUBE_MANUAL
            except Exception:
                try:
                    transcript_entry = transcript_list.find_generated_transcript(languages)
                    source = TranscriptSource.YOUTUBE_AUTO
                except Exception:
                    # Fall back to any available transcript
                    transcript_entry = transcript_list.find_transcript(languages)
                    source = (
                        TranscriptSource.YOUTUBE_AUTO
                        if transcript_entry.is_generated
                        else TranscriptSource.YOUTUBE_MANUAL
                    )
            transcript = transcript_entry.fetch()
        except Exception:
            # Fall back to direct fetch if list fails (older API versions)
            transcript = ytt_api.fetch(video_id, languages=languages)
            # Check is_generated on the FetchedTranscript if available
            if getattr(transcript, "is_generated", False):
                source = TranscriptSource.YOUTUBE_AUTO

        segments = []
        for snippet in transcript.snippets:
            text = snippet.text.strip()
            if not text:
                continue
            start = snippet.start
            duration = snippet.duration
            segments.append(
                TranscriptSegment(
                    text=text,
                    start=start,
                    end=start + duration,
                    confidence=1.0,
                    source=source,
                )
            )

        if not segments:
            return [], TranscriptSource.NONE

        return segments, source

    except Exception as e:
        logger.warning(f"Failed to fetch YouTube transcript for {video_id}: {e}")
        return [], TranscriptSource.NONE


# =============================================================================
# Subtitle File Parsing (Tier 1)
# =============================================================================


def _parse_timestamp_srt(ts: str) -> float:
    """Parse SRT timestamp (HH:MM:SS,mmm) to seconds."""
    ts = ts.strip().replace(",", ".")
    parts = ts.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    return 0.0


def _parse_timestamp_vtt(ts: str) -> float:
    """Parse VTT timestamp (HH:MM:SS.mmm or MM:SS.mmm) to seconds."""
    ts = ts.strip()
    parts = ts.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    return 0.0


def parse_srt(path: str) -> list[TranscriptSegment]:
    """Parse an SRT subtitle file into TranscriptSegments.

    Args:
        path: Path to .srt file.

    Returns:
        List of TranscriptSegment objects.
    """
    content = Path(path).read_text(encoding="utf-8", errors="replace")
    segments = []

    # SRT format: index\nstart --> end\ntext\n\n
    blocks = re.split(r"\n\s*\n", content.strip())
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 2:
            continue

        # Find the timestamp line (contains -->)
        ts_line = None
        text_lines = []
        for line in lines:
            if "-->" in line:
                ts_line = line
            elif ts_line is not None:
                text_lines.append(line)

        if ts_line is None:
            continue

        parts = ts_line.split("-->")
        if len(parts) != 2:
            continue

        start = _parse_timestamp_srt(parts[0])
        end = _parse_timestamp_srt(parts[1])
        text = " ".join(text_lines).strip()

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        if text:
            segments.append(
                TranscriptSegment(
                    text=text,
                    start=start,
                    end=end,
                    confidence=1.0,
                    source=TranscriptSource.SUBTITLE_FILE,
                )
            )

    return segments


def parse_vtt(path: str) -> list[TranscriptSegment]:
    """Parse a WebVTT subtitle file into TranscriptSegments.

    Args:
        path: Path to .vtt file.

    Returns:
        List of TranscriptSegment objects.
    """
    content = Path(path).read_text(encoding="utf-8", errors="replace")
    segments = []

    # Skip VTT header
    lines = content.strip().split("\n")
    i = 0
    # Skip WEBVTT header and any metadata
    while i < len(lines) and not re.match(r"\d{2}:\d{2}", lines[i]):
        i += 1

    current_text_lines = []
    current_start = 0.0
    current_end = 0.0
    in_cue = False

    while i < len(lines):
        line = lines[i].strip()
        i += 1

        if "-->" in line:
            # Save previous cue
            if in_cue and current_text_lines:
                text = " ".join(current_text_lines).strip()
                text = re.sub(r"<[^>]+>", "", text)
                if text:
                    segments.append(
                        TranscriptSegment(
                            text=text,
                            start=current_start,
                            end=current_end,
                            confidence=1.0,
                            source=TranscriptSource.SUBTITLE_FILE,
                        )
                    )

            parts = line.split("-->")
            current_start = _parse_timestamp_vtt(parts[0])
            current_end = _parse_timestamp_vtt(parts[1].split()[0])
            current_text_lines = []
            in_cue = True

        elif line == "":
            if in_cue and current_text_lines:
                text = " ".join(current_text_lines).strip()
                text = re.sub(r"<[^>]+>", "", text)
                if text:
                    segments.append(
                        TranscriptSegment(
                            text=text,
                            start=current_start,
                            end=current_end,
                            confidence=1.0,
                            source=TranscriptSource.SUBTITLE_FILE,
                        )
                    )
                current_text_lines = []
                in_cue = False

        elif in_cue:
            # Skip cue identifiers (numeric lines before timestamps)
            if not line.isdigit():
                current_text_lines.append(line)

    # Handle last cue
    if in_cue and current_text_lines:
        text = " ".join(current_text_lines).strip()
        text = re.sub(r"<[^>]+>", "", text)
        if text:
            segments.append(
                TranscriptSegment(
                    text=text,
                    start=current_start,
                    end=current_end,
                    confidence=1.0,
                    source=TranscriptSource.SUBTITLE_FILE,
                )
            )

    return segments


# =============================================================================
# Whisper Stub (Tier 2)
# =============================================================================


def transcribe_with_whisper(
    audio_path: str,  # noqa: ARG001
    model: str = "base",  # noqa: ARG001
    language: str | None = None,  # noqa: ARG001
) -> list[TranscriptSegment]:
    """Transcribe audio using faster-whisper (Tier 2).

    Raises:
        RuntimeError: Always, unless faster-whisper is installed.
    """
    if not HAS_WHISPER:
        raise RuntimeError(
            "faster-whisper is required for Whisper transcription.\n"
            'Install with: pip install "skill-seekers[video-full]"\n'
            "Or: pip install faster-whisper"
        )

    # Tier 2 implementation placeholder
    raise NotImplementedError("Whisper transcription will be implemented in Tier 2")


# =============================================================================
# Main Entry Point
# =============================================================================


def get_transcript(
    video_info: VideoInfo,
    config: VideoSourceConfig,
) -> tuple[list[TranscriptSegment], TranscriptSource]:
    """Get transcript for a video, trying available methods in priority order.

    Priority:
    1. YouTube API (for YouTube videos)
    2. Subtitle files (SRT/VTT alongside local files)
    3. Whisper fallback (Tier 2)
    4. NONE (no transcript available)

    Args:
        video_info: Video metadata.
        config: Video source configuration.

    Returns:
        Tuple of (transcript segments, source type).
    """
    languages = config.languages or ["en"]

    # 1. Try YouTube API for YouTube videos
    if video_info.source_type == VideoSourceType.YOUTUBE and HAS_YOUTUBE_TRANSCRIPT:
        try:
            segments, source = extract_youtube_transcript(video_info.video_id, languages)
            if segments:
                logger.info(
                    f"Got {len(segments)} transcript segments via YouTube API "
                    f"({source.value}) for '{video_info.title}'"
                )
                return segments, source
        except Exception as e:
            logger.warning(f"YouTube transcript failed: {e}")

    # 2. Try subtitle files for local videos
    if video_info.file_path:
        base = Path(video_info.file_path).stem
        parent = Path(video_info.file_path).parent

        for ext in [".srt", ".vtt"]:
            sub_path = parent / f"{base}{ext}"
            if sub_path.exists():
                logger.info(f"Found subtitle file: {sub_path}")
                segments = parse_srt(str(sub_path)) if ext == ".srt" else parse_vtt(str(sub_path))
                if segments:
                    return segments, TranscriptSource.SUBTITLE_FILE

    # 3. Whisper fallback (Tier 2 — only if installed)
    if HAS_WHISPER and video_info.file_path:
        try:
            segments = transcribe_with_whisper(
                video_info.file_path,
                model=config.whisper_model,
                language=languages[0] if languages else None,
            )
            if segments:
                return segments, TranscriptSource.WHISPER
        except (RuntimeError, NotImplementedError):
            pass

    # 4. No transcript available
    logger.warning(f"No transcript available for '{video_info.title}'")
    return [], TranscriptSource.NONE
