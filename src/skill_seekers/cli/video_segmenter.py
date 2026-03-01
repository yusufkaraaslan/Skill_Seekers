"""Video segmentation module.

Aligns transcript + metadata into VideoSegment objects using:
1. Chapter-based segmentation (primary — uses YouTube chapters)
2. Time-window segmentation (fallback — fixed-duration windows)
"""

import logging

from skill_seekers.cli.video_models import (
    SegmentContentType,
    TranscriptSegment,
    VideoInfo,
    VideoSegment,
    VideoSourceConfig,
)

logger = logging.getLogger(__name__)


def _classify_content_type(transcript: str) -> SegmentContentType:
    """Classify segment content type based on transcript text."""
    lower = transcript.lower()

    code_indicators = ["import ", "def ", "class ", "function ", "const ", "npm ", "pip ", "git "]
    intro_indicators = ["welcome", "hello", "today we", "in this video", "let's get started"]
    outro_indicators = ["thanks for watching", "subscribe", "see you next", "that's it for"]

    if any(kw in lower for kw in outro_indicators):
        return SegmentContentType.OUTRO
    if any(kw in lower for kw in intro_indicators):
        return SegmentContentType.INTRO
    if sum(1 for kw in code_indicators if kw in lower) >= 2:
        return SegmentContentType.LIVE_CODING

    return SegmentContentType.EXPLANATION


def _build_segment_content(
    transcript: str,
    chapter_title: str | None,
    start_time: float,
    end_time: float,
) -> str:
    """Build merged content string for a segment."""
    parts = []

    # Add chapter heading
    start_min, start_sec = divmod(int(start_time), 60)
    end_min, end_sec = divmod(int(end_time), 60)
    ts = f"{start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d}"

    if chapter_title:
        parts.append(f"### {chapter_title} ({ts})\n")
    else:
        parts.append(f"### Segment ({ts})\n")

    if transcript:
        parts.append(transcript)

    return "\n".join(parts)


def _get_transcript_in_range(
    transcript_segments: list[TranscriptSegment],
    start_time: float,
    end_time: float,
) -> tuple[str, float]:
    """Get concatenated transcript text and average confidence for a time range.

    Returns:
        Tuple of (text, avg_confidence).
    """
    texts = []
    confidences = []

    for seg in transcript_segments:
        # Check overlap: segment overlaps with time range
        if seg.end > start_time and seg.start < end_time:
            texts.append(seg.text)
            confidences.append(seg.confidence)

    text = " ".join(texts)
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    return text, avg_confidence


def segment_by_chapters(
    video_info: VideoInfo,
    transcript_segments: list[TranscriptSegment],
) -> list[VideoSegment]:
    """Segment video using YouTube chapter boundaries.

    Args:
        video_info: Video metadata with chapters.
        transcript_segments: Raw transcript segments.

    Returns:
        List of VideoSegment objects aligned to chapters.
    """
    segments = []

    for i, chapter in enumerate(video_info.chapters):
        transcript, confidence = _get_transcript_in_range(
            transcript_segments, chapter.start_time, chapter.end_time
        )

        content_type = _classify_content_type(transcript)
        content = _build_segment_content(
            transcript, chapter.title, chapter.start_time, chapter.end_time
        )

        segments.append(
            VideoSegment(
                index=i,
                start_time=chapter.start_time,
                end_time=chapter.end_time,
                duration=chapter.end_time - chapter.start_time,
                transcript=transcript,
                transcript_confidence=confidence,
                chapter_title=chapter.title,
                content=content,
                confidence=confidence,
                content_type=content_type,
            )
        )

    return segments


def segment_by_time_window(
    video_info: VideoInfo,
    transcript_segments: list[TranscriptSegment],
    window_seconds: float = 120.0,
    start_offset: float = 0.0,
    end_limit: float | None = None,
) -> list[VideoSegment]:
    """Segment video using fixed time windows.

    Args:
        video_info: Video metadata.
        transcript_segments: Raw transcript segments.
        window_seconds: Duration of each window in seconds.
        start_offset: Start segmentation at this time (seconds).
        end_limit: Stop segmentation at this time (seconds). None = full duration.

    Returns:
        List of VideoSegment objects.
    """
    segments = []
    duration = video_info.duration

    if duration <= 0 and transcript_segments:
        duration = max(seg.end for seg in transcript_segments)

    if end_limit is not None:
        duration = min(duration, end_limit)

    if duration <= 0:
        return segments

    current_time = start_offset
    index = 0

    while current_time < duration:
        end_time = min(current_time + window_seconds, duration)

        transcript, confidence = _get_transcript_in_range(
            transcript_segments, current_time, end_time
        )

        if transcript.strip():
            content_type = _classify_content_type(transcript)
            content = _build_segment_content(transcript, None, current_time, end_time)

            segments.append(
                VideoSegment(
                    index=index,
                    start_time=current_time,
                    end_time=end_time,
                    duration=end_time - current_time,
                    transcript=transcript,
                    transcript_confidence=confidence,
                    content=content,
                    confidence=confidence,
                    content_type=content_type,
                )
            )
            index += 1

        current_time = end_time

    return segments


def segment_video(
    video_info: VideoInfo,
    transcript_segments: list[TranscriptSegment],
    config: VideoSourceConfig,
) -> list[VideoSegment]:
    """Segment a video using the best available strategy.

    Priority:
    1. Chapter-based (if chapters available)
    2. Time-window fallback

    Args:
        video_info: Video metadata.
        transcript_segments: Raw transcript segments.
        config: Video source configuration.

    Returns:
        List of VideoSegment objects.
    """
    # Use chapters if available
    if video_info.chapters:
        logger.info(f"Using chapter-based segmentation ({len(video_info.chapters)} chapters)")
        segments = segment_by_chapters(video_info, transcript_segments)
        if segments:
            return segments

    # Fallback to time-window
    window = config.time_window_seconds
    logger.info(f"Using time-window segmentation ({window}s windows)")
    return segment_by_time_window(
        video_info,
        transcript_segments,
        window,
        start_offset=config.clip_start or 0.0,
        end_limit=config.clip_end,
    )
