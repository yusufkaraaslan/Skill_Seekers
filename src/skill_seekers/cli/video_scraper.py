#!/usr/bin/env python3
"""
Video to Claude Skill Converter

Extracts transcripts, metadata, and visual content from videos
and converts them into Claude AI skills.

Supports YouTube videos/playlists, Vimeo, and local video files.

Usage:
    python3 video_scraper.py --url https://www.youtube.com/watch?v=...
    python3 video_scraper.py --video-file recording.mp4
    python3 video_scraper.py --playlist https://www.youtube.com/playlist?list=...
    python3 video_scraper.py --from-json video_extracted.json
"""

import argparse
import json
import logging
import os
import re
import sys
import time

from skill_seekers.cli.video_models import (
    AudioVisualAlignment,
    TextGroupTimeline,
    TranscriptSource,
    VideoInfo,
    VideoScraperResult,
    VideoSourceConfig,
    VideoSourceType,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Dependency Guard
# =============================================================================

# Core video deps are optional
try:
    import yt_dlp  # noqa: F401

    HAS_YTDLP = True
except ImportError:
    HAS_YTDLP = False

try:
    from youtube_transcript_api import YouTubeTranscriptApi  # noqa: F401

    HAS_YOUTUBE_TRANSCRIPT = True
except ImportError:
    HAS_YOUTUBE_TRANSCRIPT = False


def check_video_dependencies(require_full: bool = False) -> None:
    """Check that required video dependencies are available.

    Args:
        require_full: If True, also check Tier 2 deps (Whisper, OpenCV, etc.)

    Raises:
        RuntimeError: If required dependencies are missing.
    """
    missing = []
    if not HAS_YTDLP:
        missing.append("yt-dlp")
    if not HAS_YOUTUBE_TRANSCRIPT:
        missing.append("youtube-transcript-api")

    if require_full:
        try:
            import cv2  # noqa: F401
        except ImportError:
            missing.append("opencv-python-headless")
        try:
            import faster_whisper  # noqa: F401
        except ImportError:
            missing.append("faster-whisper")

    if missing:
        deps = ", ".join(missing)
        extra = "[video-full]" if require_full else "[video]"
        setup_hint = (
            "\nFor visual deps (GPU-aware): skill-seekers video --setup" if require_full else ""
        )
        raise RuntimeError(
            f"Missing video dependencies: {deps}\n"
            f'Install with: pip install "skill-seekers{extra}"'
            f"{setup_hint}\n"
            f"Or: pip install {' '.join(missing)}"
        )


# =============================================================================
# Helper Functions
# =============================================================================


def _sanitize_filename(title: str, max_length: int = 60) -> str:
    """Sanitize a video title for use as a filename."""
    name = title.lower()
    name = re.sub(r"[^a-z0-9\s-]", "", name)
    name = re.sub(r"[\s]+", "-", name)
    name = re.sub(r"-+", "-", name)
    name = name.strip("-")
    return name[:max_length]


def parse_time_to_seconds(time_str: str) -> float:
    """Parse a time string into seconds.

    Accepted formats:
        - Plain seconds: ``"330"`` or ``"330.5"``
        - MM:SS: ``"5:30"``
        - HH:MM:SS: ``"00:05:30"``

    Args:
        time_str: Time string in one of the accepted formats.

    Returns:
        Time in seconds as a float.

    Raises:
        ValueError: If *time_str* cannot be parsed.
    """
    time_str = time_str.strip()
    if not time_str:
        raise ValueError("Empty time string")

    parts = time_str.split(":")
    try:
        if len(parts) == 1:
            return float(parts[0])
        if len(parts) == 2:
            minutes, seconds = float(parts[0]), float(parts[1])
            return minutes * 60 + seconds
        if len(parts) == 3:
            hours, minutes, seconds = float(parts[0]), float(parts[1]), float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
    except ValueError:
        pass
    raise ValueError(
        f"Invalid time format: '{time_str}'. "
        "Use seconds (330), MM:SS (5:30), or HH:MM:SS (00:05:30)"
    )


def _format_duration(seconds: float) -> str:
    """Format seconds as HH:MM:SS or MM:SS."""
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def _format_count(count: int | None) -> str:
    """Format a count with commas."""
    if count is None:
        return "N/A"
    return f"{count:,}"


def infer_description_from_video(video_info: VideoInfo, name: str = "") -> str:
    """Infer skill description from video metadata."""
    if video_info.description:
        desc = video_info.description[:150].strip()
        if len(video_info.description) > 150:
            desc += "..."
        return f"Use when {desc.lower()}"
    if video_info.title:
        return f"Use when working with {video_info.title.lower()}"
    return (
        f"Use when referencing {name} video content"
        if name
        else "Use when referencing this video content"
    )


# =============================================================================
# Audio-Visual Alignment
# =============================================================================


def _build_audio_visual_alignments(
    timeline: TextGroupTimeline,
    transcript_segments: list,
) -> list[AudioVisualAlignment]:
    """Build audio-visual alignments pairing on-screen code with transcript.

    For each text group appearance, finds overlapping transcript segments
    and pairs them into AudioVisualAlignment objects.

    Args:
        timeline: TextGroupTimeline with text groups and appearances.
        transcript_segments: List of TranscriptSegment objects.

    Returns:
        List of AudioVisualAlignment objects.
    """
    alignments: list[AudioVisualAlignment] = []

    for group in timeline.text_groups:
        for start, end in group.appearances:
            # Find overlapping transcript segments
            overlapping_text = []
            for seg in transcript_segments:
                seg_start = seg.start
                seg_end = seg.end
                # Check overlap
                if seg_end > start and seg_start < end:
                    overlapping_text.append(seg.text)

            transcript_during = " ".join(overlapping_text).strip()
            if not transcript_during:
                continue

            alignments.append(
                AudioVisualAlignment(
                    text_group_id=group.group_id,
                    start_time=start,
                    end_time=end,
                    on_screen_code=group.full_text,
                    transcript_during=transcript_during,
                    language=group.detected_language,
                )
            )

    return alignments


# =============================================================================
# OCR Quality Filters
# =============================================================================


_RE_CODE_TOKENS = re.compile(
    r"[=(){};]|(?:def|class|function|import|return|var|let|const|public|private|void|static|override|virtual|protected)\b"
)
_RE_UI_PATTERNS = re.compile(
    r"\b(?:Inspector|Hierarchy|Project|Console|Image Type|Sorting Layer|Button|Canvas|Scene|Game)\b",
    re.IGNORECASE,
)


def _is_likely_code(text: str) -> bool:
    """Return True if text likely contains programming code, not UI junk."""
    if not text or len(text.strip()) < 10:
        return False
    code_tokens = _RE_CODE_TOKENS.findall(text)
    ui_patterns = _RE_UI_PATTERNS.findall(text)
    return len(code_tokens) >= 2 and len(code_tokens) > len(ui_patterns)


# =============================================================================
# Two-Pass AI Reference Enhancement
# =============================================================================


def _ai_clean_reference(ref_path: str, content: str, api_key: str | None = None) -> None:
    """Use AI to clean Code Timeline section in a reference file.

    Sends the reference file content to Claude with a focused prompt
    to reconstruct the Code Timeline from noisy OCR + transcript context.
    """
    try:
        import anthropic
    except ImportError:
        return

    key = api_key or os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
    if not key:
        return

    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    client_kwargs: dict = {"api_key": key}
    if base_url:
        client_kwargs["base_url"] = base_url

    prompt = (
        "You are cleaning a video tutorial reference file. The Code Timeline section "
        "contains OCR-extracted code that is noisy (duplicated lines, garbled characters, "
        "UI decorations mixed in). The transcript sections above provide context about "
        "what the code SHOULD be.\n\n"
        "Tasks:\n"
        "1. Reconstruct each code block in the file using transcript context\n"
        "2. Fix OCR errors (l/1, O/0, rn/m confusions)\n"
        "3. Remove any UI text (Inspector, Hierarchy, button labels)\n"
        "4. Set correct language tags on code fences\n"
        "5. Keep the document structure but clean the code text\n\n"
        "Return the COMPLETE reference file with cleaned code blocks. "
        "Do NOT modify the transcript or metadata sections.\n\n"
        f"Reference file:\n{content}"
    )

    try:
        client = anthropic.Anthropic(**client_kwargs)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}],
        )
        result = response.content[0].text
        if result and len(result) > len(content) * 0.5:
            with open(ref_path, "w", encoding="utf-8") as f:
                f.write(result)
            logger.info(f"AI-cleaned reference: {os.path.basename(ref_path)}")
    except Exception as e:
        logger.debug(f"Reference enhancement failed: {e}")


# =============================================================================
# Main Converter Class
# =============================================================================


class VideoToSkillConverter:
    """Convert video content to Claude skill."""

    def __init__(self, config: dict):
        """Initialize converter.

        Args:
            config: Configuration dict with keys:
                - name: Skill name
                - url/video_file/playlist: Video source
                - description: Optional description
                - languages: Optional language preferences
                - visual: Whether to enable visual extraction
                - whisper_model: Whisper model size
        """
        self.config = config
        self.name = config["name"]
        self.description = config.get("description", "")
        self.languages = (config.get("languages") or "en").split(",")
        self.visual = config.get("visual", False)
        self.whisper_model = config.get("whisper_model", "base")
        self.visual_interval = config.get("visual_interval", 0.7)
        self.visual_min_gap = config.get("visual_min_gap", 0.5)
        self.visual_similarity = config.get("visual_similarity", 3.0)
        self.vision_ocr = config.get("vision_ocr", False)

        # Time-clipping (seconds, None = full video)
        self.start_time: float | None = config.get("start_time")
        self.end_time: float | None = config.get("end_time")

        # Paths
        self.skill_dir = config.get("output") or f"output/{self.name}"
        self.data_file = f"output/{self.name}_video_extracted.json"

        # Results
        self.result: VideoScraperResult | None = None

    def process(self) -> VideoScraperResult:
        """Run the full video processing pipeline.

        Returns:
            VideoScraperResult with all extracted data.
        """
        from skill_seekers.cli.video_metadata import (
            detect_video_source_type,
            extract_local_metadata,
            extract_youtube_metadata,
            resolve_playlist,
        )
        from skill_seekers.cli.video_segmenter import segment_video
        from skill_seekers.cli.video_transcript import get_transcript

        start_time = time.time()

        # Validate visual deps upfront so we fail fast
        if self.visual:
            check_video_dependencies(require_full=True)
            from skill_seekers.cli.video_visual import check_visual_dependencies

            deps = check_visual_dependencies()
            missing = [name for name, available in deps.items() if not available]
            if missing:
                raise RuntimeError(
                    f"Visual extraction requires: {', '.join(missing)}\n"
                    'Install with: pip install "skill-seekers[video-full]"\n'
                    "Or: pip install opencv-python-headless scenedetect easyocr"
                )

        source_config = VideoSourceConfig(
            name=self.name,
            description=self.description,
            languages=self.languages,
            visual_extraction=self.visual,
            whisper_model=self.whisper_model,
            clip_start=self.start_time,
            clip_end=self.end_time,
        )

        videos: list[VideoInfo] = []
        warnings: list[str] = []
        errors: list[dict] = []

        # Determine source URLs
        urls_or_paths = []
        if self.config.get("playlist"):
            logger.info("Resolving playlist...")
            try:
                check_video_dependencies()
                urls_or_paths = resolve_playlist(self.config["playlist"])
                logger.info(f"Found {len(urls_or_paths)} videos in playlist")
            except Exception as e:
                errors.append({"source": self.config["playlist"], "error": str(e)})
                logger.error(f"Failed to resolve playlist: {e}")
        elif self.config.get("url"):
            urls_or_paths = [self.config["url"]]
        elif self.config.get("video_file"):
            urls_or_paths = [self.config["video_file"]]

        # Process each video
        for i, source in enumerate(urls_or_paths):
            logger.info(f"[{i + 1}/{len(urls_or_paths)}] Processing: {source}")
            try:
                source_type = detect_video_source_type(source)

                # Extract metadata
                if source_type == VideoSourceType.YOUTUBE:
                    check_video_dependencies()
                    video_info = extract_youtube_metadata(source)
                else:
                    video_info = extract_local_metadata(source)

                # Extract transcript
                transcript_segments, transcript_source = get_transcript(video_info, source_config)
                video_info.raw_transcript = transcript_segments
                video_info.transcript_source = transcript_source

                if not transcript_segments:
                    warnings.append(f"No transcript available for '{video_info.title}'")

                # Compute transcript confidence
                if transcript_segments:
                    video_info.transcript_confidence = sum(
                        s.confidence for s in transcript_segments
                    ) / len(transcript_segments)

                    if transcript_source == TranscriptSource.YOUTUBE_AUTO:
                        video_info.transcript_confidence *= 0.8

                # Apply time clipping to transcript and chapters
                clip_start = self.start_time
                clip_end = self.end_time
                if clip_start is not None or clip_end is not None:
                    cs = clip_start or 0.0
                    ce = clip_end or float("inf")

                    # Store original duration before clipping
                    video_info.original_duration = video_info.duration
                    video_info.clip_start = cs
                    video_info.clip_end = clip_end  # keep None if not set

                    # Filter transcript segments to clip range
                    original_count = len(transcript_segments)
                    transcript_segments = [
                        seg for seg in transcript_segments if seg.end > cs and seg.start < ce
                    ]
                    video_info.raw_transcript = transcript_segments
                    logger.info(
                        f"  Clipped transcript: {len(transcript_segments)}/{original_count} "
                        f"segments in range {_format_duration(cs)}-{_format_duration(ce) if clip_end else 'end'}"
                    )

                    # Filter chapters to clip range
                    if video_info.chapters:
                        video_info.chapters = [
                            ch
                            for ch in video_info.chapters
                            if ch.end_time > cs and ch.start_time < ce
                        ]

                # Segment video
                segments = segment_video(video_info, transcript_segments, source_config)
                video_info.segments = segments

                # Visual extraction (Tier 2)
                if self.visual:
                    from skill_seekers.cli.video_visual import (
                        download_video,
                        extract_visual_data,
                    )

                    video_path = video_info.file_path
                    temp_video_dir = None

                    # Download if remote (YouTube/Vimeo)
                    if not video_path or not os.path.exists(video_path):
                        import tempfile as _tmpmod

                        temp_video_dir = _tmpmod.mkdtemp(prefix="ss_video_")
                        video_path = download_video(
                            source,
                            temp_video_dir,
                            clip_start=self.start_time,
                            clip_end=self.end_time,
                        )

                    if video_path and os.path.exists(video_path):
                        keyframes, code_blocks, timeline = extract_visual_data(
                            video_path,
                            segments,
                            self.skill_dir,
                            sample_interval=self.visual_interval,
                            min_gap=self.visual_min_gap,
                            similarity_threshold=self.visual_similarity,
                            use_vision_api=self.vision_ocr,
                            clip_start=self.start_time,
                            clip_end=self.end_time,
                        )
                        # Attach keyframes to segments
                        for kf in keyframes:
                            for seg in segments:
                                if seg.start_time <= kf.timestamp < seg.end_time:
                                    seg.keyframes.append(kf)
                                    break
                        # Assign code blocks to segments by timestamp
                        for cb in code_blocks:
                            for seg in segments:
                                if seg.start_time <= cb.source_frame < seg.end_time:
                                    seg.detected_code_blocks.append(cb)
                                    seg.has_code_on_screen = True
                                    break
                        # Set timeline and build audio-visual alignments
                        video_info.text_group_timeline = timeline
                        if timeline:
                            video_info.audio_visual_alignments = _build_audio_visual_alignments(
                                timeline, video_info.raw_transcript
                            )
                        logger.info(
                            f"  Visual: {len(keyframes)} keyframes extracted, "
                            f"{sum(1 for kf in keyframes if kf.ocr_text)} with OCR text, "
                            f"{len(code_blocks)} code blocks detected"
                        )
                    else:
                        warnings.append(f"Could not download video for visual extraction: {source}")

                    # Clean up temp download
                    if temp_video_dir:
                        import shutil

                        shutil.rmtree(temp_video_dir, ignore_errors=True)

                # Set processing metadata
                video_info.extracted_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                video_info.visual_extraction_enabled = self.visual
                video_info.processing_time_seconds = time.time() - start_time

                videos.append(video_info)
                visual_msg = ""
                if self.visual:
                    total_kf = sum(len(s.keyframes) for s in segments)
                    total_ocr = sum(1 for s in segments for kf in s.keyframes if kf.ocr_text)
                    visual_msg = f", {total_kf} keyframes, {total_ocr} with OCR"
                logger.info(
                    f"  => {len(segments)} segments, "
                    f"{len(transcript_segments)} transcript chunks, "
                    f"source: {transcript_source.value}{visual_msg}"
                )

            except Exception as e:
                errors.append({"source": source, "error": str(e)})
                logger.error(f"Failed to process {source}: {e}")
                logger.debug("Traceback:", exc_info=True)

        # Build result
        total_duration = sum(v.duration for v in videos)
        total_segments = sum(len(v.segments) for v in videos)
        total_code_blocks = sum(
            sum(len(s.detected_code_blocks) for s in v.segments) for v in videos
        )

        self.result = VideoScraperResult(
            videos=videos,
            total_duration_seconds=total_duration,
            total_segments=total_segments,
            total_code_blocks=total_code_blocks,
            config=source_config,
            processing_time_seconds=time.time() - start_time,
            warnings=warnings,
            errors=errors,
        )

        return self.result

    def save_extracted_data(self) -> str:
        """Save extracted data to JSON file.

        Returns:
            Path to saved JSON file.
        """
        if self.result is None:
            raise RuntimeError("No data to save. Run process() first.")

        os.makedirs(os.path.dirname(self.data_file) or ".", exist_ok=True)
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self.result.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info(f"Saved extracted data to {self.data_file}")
        return self.data_file

    def load_extracted_data(self, json_path: str) -> None:
        """Load previously extracted data from JSON.

        Args:
            json_path: Path to extracted JSON file.
        """
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        self.result = VideoScraperResult.from_dict(data)
        logger.info(f"Loaded {len(self.result.videos)} videos from {json_path}")

    def build_skill(self) -> str:
        """Build skill directory with SKILL.md and reference files.

        Returns:
            Path to skill directory.
        """
        if self.result is None:
            raise RuntimeError(
                "No data to build from. Run process() or load_extracted_data() first."
            )

        # Create directories
        refs_dir = os.path.join(self.skill_dir, "references")
        video_data_dir = os.path.join(self.skill_dir, "video_data")
        os.makedirs(refs_dir, exist_ok=True)
        os.makedirs(video_data_dir, exist_ok=True)

        # Generate reference files for each video
        for video in self.result.videos:
            sanitized = (
                _sanitize_filename(video.title)
                or video.video_id
                or f"video_{hash(video.title) % 10000:04d}"
            )
            ref_filename = f"video_{sanitized}.md"
            ref_path = os.path.join(refs_dir, ref_filename)
            ref_content = self._generate_reference_md(video)
            with open(ref_path, "w", encoding="utf-8") as f:
                f.write(ref_content)

        # Save metadata JSON
        metadata_path = os.path.join(video_data_dir, "metadata.json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.result.to_dict(), f, indent=2, ensure_ascii=False)

        # Generate SKILL.md
        skill_md = self._generate_skill_md()
        skill_path = os.path.join(self.skill_dir, "SKILL.md")
        with open(skill_path, "w", encoding="utf-8") as f:
            f.write(skill_md)

        logger.info(f"Built skill at {self.skill_dir}")
        logger.info(f"  {len(self.result.videos)} videos, {self.result.total_segments} segments")
        return self.skill_dir

    def _generate_reference_md(self, video: VideoInfo) -> str:
        """Generate reference markdown file for a single video."""
        lines = []

        # Title
        lines.append(f"# {video.title}\n")

        # Metadata block
        meta_parts = []
        if video.channel_name:
            if video.channel_url:
                meta_parts.append(f"**Source:** [{video.channel_name}]({video.channel_url})")
            else:
                meta_parts.append(f"**Source:** {video.channel_name}")
        if video.duration > 0:
            dur_str = _format_duration(video.duration)
            if video.clip_start is not None or video.clip_end is not None:
                orig = _format_duration(video.original_duration) if video.original_duration else "?"
                cs = _format_duration(video.clip_start) if video.clip_start is not None else "0:00"
                ce = _format_duration(video.clip_end) if video.clip_end is not None else orig
                dur_str = f"{cs} - {ce} (of {orig})"
            meta_parts.append(f"**Duration:** {dur_str}")
        if video.upload_date:
            meta_parts.append(f"**Published:** {video.upload_date}")

        if meta_parts:
            lines.append("> " + " | ".join(meta_parts))

        if video.source_url:
            lines.append(f"> **URL:** [{video.source_url}]({video.source_url})")

        engagement_parts = []
        if video.view_count is not None:
            engagement_parts.append(f"**Views:** {_format_count(video.view_count)}")
        if video.like_count is not None:
            engagement_parts.append(f"**Likes:** {_format_count(video.like_count)}")
        if engagement_parts:
            lines.append("> " + " | ".join(engagement_parts))

        if video.tags:
            lines.append(f"> **Tags:** {', '.join(video.tags[:10])}")

        lines.append("")

        # Description summary
        if video.description:
            desc = video.description[:300]
            if len(video.description) > 300:
                desc += "..."
            lines.append(desc)
            lines.append("")

        lines.append("---\n")

        # Table of contents (from chapters or segments)
        if video.segments:
            lines.append("## Table of Contents\n")
            for seg in video.segments:
                label = seg.chapter_title or f"Segment {seg.index + 1}"
                lines.append(
                    f"- [{label}](#{_sanitize_filename(label)}-{seg.timestamp_display.replace(' ', '')})"
                )
            lines.append("\n---\n")

        # Segments as sections
        for seg in video.segments:
            lines.append(seg.content)

            # Visual data (keyframes + OCR)
            if seg.keyframes:
                for kf in seg.keyframes:
                    if kf.image_path and os.path.exists(kf.image_path):
                        rel_path = os.path.relpath(
                            kf.image_path,
                            os.path.dirname(os.path.join(self.skill_dir, "references", "x.md")),
                        )
                        lines.append(
                            f"\n> **Frame** ({kf.frame_type.value} at {_format_duration(kf.timestamp)}):"
                        )
                        lines.append(f"> ![keyframe]({rel_path})")
                    if kf.sub_sections:
                        from skill_seekers.cli.video_models import FrameType

                        lang_hint = ""
                        if seg.detected_code_blocks:
                            for cb in seg.detected_code_blocks:
                                if cb.language:
                                    lang_hint = cb.language
                                    break
                        for ss in kf.sub_sections:
                            if (
                                ss.frame_type in (FrameType.CODE_EDITOR, FrameType.TERMINAL)
                                and ss.ocr_text
                                and _is_likely_code(ss.ocr_text)
                            ):
                                lines.append(f"\n```{lang_hint}")
                                lines.append(ss.ocr_text)
                                lines.append("```")
                    elif kf.ocr_text:
                        from skill_seekers.cli.video_models import FrameType

                        if kf.frame_type in (FrameType.CODE_EDITOR, FrameType.TERMINAL):
                            if _is_likely_code(kf.ocr_text):
                                lang_hint = ""
                                if seg.detected_code_blocks:
                                    for cb in seg.detected_code_blocks:
                                        if cb.language:
                                            lang_hint = cb.language
                                            break
                                lines.append(f"\n```{lang_hint}")
                                lines.append(kf.ocr_text)
                                lines.append("```")
                        elif kf.frame_type == FrameType.SLIDE:
                            for text_line in kf.ocr_text.split("\n"):
                                if text_line.strip():
                                    lines.append(f"> {text_line}")
                        else:
                            lines.append(f"> **On-screen text:** {kf.ocr_text}")

            # Detected code blocks subsection
            if seg.detected_code_blocks:
                lines.append("\n#### Detected Code\n")
                for cb in seg.detected_code_blocks:
                    lang_label = cb.language or "unknown"
                    context_label = cb.context.value if cb.context else "unknown"
                    lines.append(
                        f"**{lang_label}** ({context_label} at "
                        f"{_format_duration(cb.source_frame)}):\n"
                    )
                    lines.append(f"```{cb.language or ''}")
                    lines.append(cb.code)
                    lines.append("```\n")

            lines.append("\n---\n")

        # Code Timeline section (from text groups)
        if video.text_group_timeline and video.text_group_timeline.text_groups:
            tl = video.text_group_timeline
            lines.append("\n## Code Timeline\n")
            lines.append(
                f"> {tl.total_groups} code groups tracked, "
                f"{tl.total_edits} edits detected, "
                f"{tl.total_code_time:.0f}s of on-screen code\n"
            )

            for group in tl.text_groups:
                lang_hint = group.detected_language or ""
                lines.append(f"### {group.group_id}")
                appearance_strs = []
                for start, end in group.appearances:
                    appearance_strs.append(f"{_format_duration(start)} - {_format_duration(end)}")
                lines.append(f"**Appearances:** {', '.join(appearance_strs)}\n")

                lines.append(f"```{lang_hint}")
                lines.append(group.full_text)
                lines.append("```\n")

                if group.edits:
                    lines.append("**Edits:**\n")
                    for edit in group.edits:
                        lines.append(f"- At {_format_duration(edit.timestamp)}:")
                        for line in edit.added_lines:
                            lines.append(f"  + `{line}`")
                        for line in edit.removed_lines:
                            lines.append(f"  - `{line}`")
                        for mod in edit.modified_lines:
                            lines.append(
                                f"  ~ L{mod.get('line_num', '?')}: "
                                f"`{mod.get('old', '')}` → `{mod.get('new', '')}`"
                            )
                    lines.append("")

            lines.append("---\n")

        # Audio-Visual Alignment section
        if video.audio_visual_alignments:
            lines.append("\n## Audio-Visual Alignment\n")
            lines.append(f"> {len(video.audio_visual_alignments)} code-narration pairs\n")

            for av in video.audio_visual_alignments:
                lang_hint = av.language or ""
                lines.append(
                    f"**{av.text_group_id}** "
                    f"({_format_duration(av.start_time)} - {_format_duration(av.end_time)})\n"
                )
                lines.append(f"```{lang_hint}")
                lines.append(av.on_screen_code)
                lines.append("```\n")
                lines.append(f"> **Narrator:** {av.transcript_during}\n")

            lines.append("---\n")

        # Transcript source info
        lines.append(f"\n*Transcript source: {video.transcript_source.value}*")
        if video.transcript_confidence > 0:
            lines.append(f"*Confidence: {video.transcript_confidence:.0%}*")

        return "\n".join(lines)

    def _enhance_reference_files(self, enhance_level: int, args) -> None:
        """First-pass: AI-clean reference files before SKILL.md enhancement.

        When enhance_level >= 2 and an API key is available, sends each
        reference file to Claude to reconstruct noisy Code Timeline
        sections using transcript context.
        """
        has_api_key = bool(
            os.environ.get("ANTHROPIC_API_KEY")
            or os.environ.get("ANTHROPIC_AUTH_TOKEN")
            or getattr(args, "api_key", None)
        )
        if not has_api_key or enhance_level < 2:
            return

        refs_dir = os.path.join(self.skill_dir, "references")
        if not os.path.isdir(refs_dir):
            return

        logger.info("\n📝 Pass 1: AI-cleaning reference files (Code Timeline reconstruction)...")
        api_key = getattr(args, "api_key", None)

        for ref_file in sorted(os.listdir(refs_dir)):
            if not ref_file.endswith(".md"):
                continue
            ref_path = os.path.join(refs_dir, ref_file)
            try:
                with open(ref_path, encoding="utf-8") as f:
                    content = f.read()
            except OSError:
                continue

            # Only enhance if there are code fences to clean
            if "```" not in content:
                continue

            _ai_clean_reference(ref_path, content, api_key)

    def _generate_skill_md(self) -> str:
        """Generate the main SKILL.md file."""
        lines = []
        desc = self.description or infer_description_from_video(
            self.result.videos[0]
            if self.result.videos
            else VideoInfo(video_id="none", source_type=VideoSourceType.YOUTUBE),
            self.name,
        )

        lines.append(f"# {self.name}\n")
        lines.append(f"{desc}\n")

        # Overview
        total_dur = _format_duration(self.result.total_duration_seconds)
        lines.append("## Overview\n")
        overview = (
            f"This skill includes knowledge extracted from "
            f"{len(self.result.videos)} video(s) totaling {total_dur} of content."
        )
        # Visual extraction summary
        total_kf = sum(
            len(kf) for v in self.result.videos for s in v.segments for kf in [s.keyframes]
        )
        total_ocr = sum(
            1 for v in self.result.videos for s in v.segments for kf in s.keyframes if kf.ocr_text
        )
        total_code = sum(
            len(s.detected_code_blocks) for v in self.result.videos for s in v.segments
        )
        if total_kf > 0:
            overview += (
                f"\nVisual extraction: {total_kf} keyframes, {total_ocr} with on-screen text"
            )
            if total_code > 0:
                overview += f", {total_code} code blocks detected"
            overview += "."
        lines.append(f"{overview}\n")

        # Video tutorials section
        lines.append("## Video Tutorials\n")

        for video in self.result.videos:
            lines.append(f"### {video.title}")
            meta = []
            if video.channel_name:
                if video.source_url:
                    meta.append(f"[{video.channel_name}]({video.source_url})")
                else:
                    meta.append(video.channel_name)
            if video.duration > 0:
                dur_str = _format_duration(video.duration)
                if video.clip_start is not None or video.clip_end is not None:
                    orig = (
                        _format_duration(video.original_duration)
                        if video.original_duration
                        else "?"
                    )
                    cs = (
                        _format_duration(video.clip_start)
                        if video.clip_start is not None
                        else "0:00"
                    )
                    ce = _format_duration(video.clip_end) if video.clip_end is not None else orig
                    dur_str = f"Clip {cs}-{ce} (of {orig})"
                meta.append(dur_str)
            if video.view_count is not None:
                meta.append(f"{_format_count(video.view_count)} views")
            if meta:
                lines.append(f"**Source:** {' | '.join(meta)}\n")

            # Topics covered
            topics = [s.chapter_title for s in video.segments if s.chapter_title]
            if topics:
                lines.append(f"**Topics covered:** {', '.join(topics)}\n")

            # First segment preview
            if video.segments and video.segments[0].transcript:
                preview = video.segments[0].transcript[:200]
                if len(video.segments[0].transcript) > 200:
                    preview += "..."
                lines.append(f"{preview}\n")

            sanitized = (
                _sanitize_filename(video.title)
                or video.video_id
                or f"video_{hash(video.title) % 10000:04d}"
            )
            ref_filename = f"video_{sanitized}.md"
            lines.append(
                f"> Full transcript: [references/{ref_filename}](references/{ref_filename})\n"
            )
            lines.append("---\n")

        # Warnings
        if self.result.warnings:
            lines.append("## Notes\n")
            for warning in self.result.warnings:
                lines.append(f"- {warning}")
            lines.append("")

        # References
        lines.append("## References\n")
        for video in self.result.videos:
            sanitized = (
                _sanitize_filename(video.title)
                or video.video_id
                or f"video_{hash(video.title) % 10000:04d}"
            )
            ref_filename = f"video_{sanitized}.md"
            lines.append(f"- [{video.title}](references/{ref_filename})")

        return "\n".join(lines)


# =============================================================================
# CLI Entry Point
# =============================================================================


def main() -> int:
    """Entry point for video scraper CLI.

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    from skill_seekers.cli.arguments.video import add_video_arguments

    parser = argparse.ArgumentParser(
        prog="skill-seekers-video",
        description="Extract transcripts and metadata from videos and generate skill",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  skill-seekers video --url https://www.youtube.com/watch?v=...
  skill-seekers video --video-file recording.mp4
  skill-seekers video --playlist https://www.youtube.com/playlist?list=...
  skill-seekers video --from-json video_extracted.json
  skill-seekers video --url https://youtu.be/... --languages en,es
""",
    )

    add_video_arguments(parser)
    args = parser.parse_args()

    # --setup: run GPU detection + dependency installation, then exit
    if getattr(args, "setup", False):
        from skill_seekers.cli.video_setup import run_setup

        return run_setup(interactive=True)

    # Setup logging
    log_level = logging.DEBUG if args.verbose else (logging.WARNING if args.quiet else logging.INFO)
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    # Validate inputs
    has_source = any(
        [
            getattr(args, "url", None),
            getattr(args, "video_file", None),
            getattr(args, "playlist", None),
        ]
    )
    has_json = getattr(args, "from_json", None)

    if not has_source and not has_json:
        parser.error("Must specify --url, --video-file, --playlist, or --from-json")

    # Parse and validate time clipping
    raw_start = getattr(args, "start_time", None)
    raw_end = getattr(args, "end_time", None)
    clip_start: float | None = None
    clip_end: float | None = None

    if raw_start is not None:
        try:
            clip_start = parse_time_to_seconds(raw_start)
        except ValueError as exc:
            parser.error(f"--start-time: {exc}")
    if raw_end is not None:
        try:
            clip_end = parse_time_to_seconds(raw_end)
        except ValueError as exc:
            parser.error(f"--end-time: {exc}")

    if clip_start is not None or clip_end is not None:
        if getattr(args, "playlist", None):
            parser.error("--start-time/--end-time cannot be used with --playlist")
        if clip_start is not None and clip_end is not None and clip_start >= clip_end:
            parser.error(f"--start-time ({clip_start}s) must be before --end-time ({clip_end}s)")

    # Build config
    config = {
        "name": args.name or "video_skill",
        "description": getattr(args, "description", None) or "",
        "output": getattr(args, "output", None),
        "url": getattr(args, "url", None),
        "video_file": getattr(args, "video_file", None),
        "playlist": getattr(args, "playlist", None),
        "languages": getattr(args, "languages", "en"),
        "visual": getattr(args, "visual", False),
        "whisper_model": getattr(args, "whisper_model", "base"),
        "visual_interval": getattr(args, "visual_interval", 0.7),
        "visual_min_gap": getattr(args, "visual_min_gap", 0.5),
        "visual_similarity": getattr(args, "visual_similarity", 3.0),
        "vision_ocr": getattr(args, "vision_ocr", False),
        "start_time": clip_start,
        "end_time": clip_end,
    }

    converter = VideoToSkillConverter(config)

    # Dry run
    if args.dry_run:
        logger.info("DRY RUN — would process:")
        for key in ["url", "video_file", "playlist"]:
            if config.get(key):
                logger.info(f"  {key}: {config[key]}")
        logger.info(f"  name: {config['name']}")
        logger.info(f"  languages: {config['languages']}")
        logger.info(f"  visual: {config['visual']}")
        if clip_start is not None or clip_end is not None:
            start_str = _format_duration(clip_start) if clip_start is not None else "start"
            end_str = _format_duration(clip_end) if clip_end is not None else "end"
            logger.info(f"  clip range: {start_str} - {end_str}")
        return 0

    # Workflow 1: Build from JSON
    if has_json:
        logger.info(f"Loading extracted data from {args.from_json}")
        converter.load_extracted_data(args.from_json)
        converter.build_skill()
        logger.info(f"Skill built at {converter.skill_dir}")
        return 0

    # Workflow 2: Full extraction + build
    try:
        result = converter.process()
        if not result.videos:
            logger.error("No videos were successfully processed")
            if result.errors:
                for err in result.errors:
                    logger.error(f"  {err['source']}: {err['error']}")
            return 1

        converter.save_extracted_data()
        converter.build_skill()

        logger.info(f"\nSkill built successfully at {converter.skill_dir}")
        logger.info(f"  Videos: {len(result.videos)}")
        logger.info(f"  Segments: {result.total_segments}")
        logger.info(f"  Duration: {_format_duration(result.total_duration_seconds)}")
        logger.info(f"  Processing time: {result.processing_time_seconds:.1f}s")

        if result.warnings:
            for w in result.warnings:
                logger.warning(f"  {w}")

    except RuntimeError as e:
        logger.error(str(e))
        return 1

    # Enhancement
    enhance_level = getattr(args, "enhance_level", 0)
    if enhance_level > 0:
        # Pass 1: Clean reference files (Code Timeline reconstruction)
        converter._enhance_reference_files(enhance_level, args)

        # Auto-inject video-tutorial workflow if no workflow specified
        if not getattr(args, "enhance_workflow", None):
            args.enhance_workflow = ["video-tutorial"]

        # Pass 2: Run workflow stages (specialized video analysis)
        try:
            from skill_seekers.cli.workflow_runner import run_workflows

            video_context = {
                "skill_name": converter.name,
                "skill_dir": converter.skill_dir,
                "source_type": "video_tutorial",
            }
            run_workflows(args, context=video_context)
        except ImportError:
            logger.debug("Workflow runner not available, skipping workflow stages")

        # Run traditional SKILL.md enhancement (reads references + rewrites)
        _run_video_enhancement(converter.skill_dir, enhance_level, args)

    return 0


def _run_video_enhancement(skill_dir: str, enhance_level: int, args) -> None:
    """Run traditional SKILL.md enhancement with video-aware prompt.

    This calls the same SkillEnhancer used by other scrapers, but the prompt
    auto-detects video_tutorial source type and uses a video-specific prompt.
    """
    import os
    import subprocess

    has_api_key = bool(
        os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("ANTHROPIC_AUTH_TOKEN")
        or getattr(args, "api_key", None)
    )

    if not has_api_key:
        logger.info("\n💡 Enhance your video skill with AI:")
        logger.info(f"  export ANTHROPIC_API_KEY=sk-ant-...")
        logger.info(f"  skill-seekers enhance {skill_dir} --enhance-level {enhance_level}")
        return

    logger.info(f"\n🤖 Running video-aware SKILL.md enhancement (level {enhance_level})...")

    try:
        enhance_cmd = ["skill-seekers-enhance", skill_dir]
        enhance_cmd.extend(["--enhance-level", str(enhance_level)])
        api_key = getattr(args, "api_key", None)
        if api_key:
            enhance_cmd.extend(["--api-key", api_key])

        logger.info(
            "Starting video skill enhancement (this may take 10+ minutes "
            "for large videos with AI enhancement)..."
        )
        subprocess.run(enhance_cmd, check=True, timeout=1800)
        logger.info("Video skill enhancement complete!")
    except subprocess.TimeoutExpired:
        logger.warning(
            "⚠ Enhancement timed out after 30 minutes. "
            "The skill was still built without enhancement. "
            "You can retry manually with:\n"
            f"  skill-seekers enhance {skill_dir} --enhance-level {enhance_level}"
        )
    except subprocess.CalledProcessError as exc:
        logger.warning(
            f"⚠ Enhancement failed (exit code {exc.returncode}), "
            "but skill was still built. You can retry manually with:\n"
            f"  skill-seekers enhance {skill_dir} --enhance-level {enhance_level}"
        )
    except FileNotFoundError:
        logger.warning("⚠ skill-seekers-enhance not found. Run manually:")
        logger.info(f"  skill-seekers enhance {skill_dir} --enhance-level {enhance_level}")


if __name__ == "__main__":
    sys.exit(main())
