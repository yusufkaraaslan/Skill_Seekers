"""Video source data models and type definitions.

Defines all enumerations and dataclasses for the video extraction pipeline:
- Enums: VideoSourceType, TranscriptSource, FrameType, CodeContext, SegmentContentType
- Core: VideoInfo, VideoSegment, VideoScraperResult
- Supporting: Chapter, TranscriptSegment, WordTimestamp, KeyFrame, OCRRegion,
  FrameSubSection, CodeBlock
- Config: VideoSourceConfig
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# =============================================================================
# Enumerations
# =============================================================================


class VideoSourceType(Enum):
    """Where a video came from."""

    YOUTUBE = "youtube"
    VIMEO = "vimeo"
    LOCAL_FILE = "local_file"
    LOCAL_DIRECTORY = "local_directory"


class TranscriptSource(Enum):
    """How the transcript was obtained."""

    YOUTUBE_MANUAL = "youtube_manual"
    YOUTUBE_AUTO = "youtube_auto_generated"
    WHISPER = "whisper"
    SUBTITLE_FILE = "subtitle_file"
    NONE = "none"


class FrameType(Enum):
    """Classification of a keyframe's visual content."""

    CODE_EDITOR = "code_editor"
    TERMINAL = "terminal"
    SLIDE = "slide"
    DIAGRAM = "diagram"
    BROWSER = "browser"
    WEBCAM = "webcam"
    SCREENCAST = "screencast"
    OTHER = "other"


class CodeContext(Enum):
    """Where code was displayed in the video."""

    EDITOR = "editor"
    TERMINAL = "terminal"
    SLIDE = "slide"
    BROWSER = "browser"
    UNKNOWN = "unknown"


class SegmentContentType(Enum):
    """Primary content type of a video segment."""

    EXPLANATION = "explanation"
    LIVE_CODING = "live_coding"
    DEMO = "demo"
    SLIDES = "slides"
    Q_AND_A = "q_and_a"
    INTRO = "intro"
    OUTRO = "outro"
    MIXED = "mixed"


class SegmentationStrategy(Enum):
    """How segments are determined."""

    CHAPTERS = "chapters"
    TIME_WINDOW = "time_window"
    SCENE_CHANGE = "scene_change"
    HYBRID = "hybrid"


# =============================================================================
# Supporting Data Classes
# =============================================================================


@dataclass(frozen=True)
class Chapter:
    """A chapter marker from a video (typically YouTube)."""

    title: str
    start_time: float
    end_time: float

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "start_time": self.start_time,
            "end_time": self.end_time,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Chapter:
        return cls(
            title=data["title"],
            start_time=data["start_time"],
            end_time=data["end_time"],
        )


@dataclass(frozen=True)
class WordTimestamp:
    """A single word with precise timing information."""

    word: str
    start: float
    end: float
    probability: float = 1.0

    def to_dict(self) -> dict:
        return {
            "word": self.word,
            "start": self.start,
            "end": self.end,
            "probability": self.probability,
        }

    @classmethod
    def from_dict(cls, data: dict) -> WordTimestamp:
        return cls(
            word=data["word"],
            start=data["start"],
            end=data["end"],
            probability=data.get("probability", 1.0),
        )


@dataclass(frozen=True)
class TranscriptSegment:
    """A raw transcript segment from YouTube API or Whisper."""

    text: str
    start: float
    end: float
    confidence: float = 1.0
    words: list[WordTimestamp] | None = None
    source: TranscriptSource = TranscriptSource.NONE

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "start": self.start,
            "end": self.end,
            "confidence": self.confidence,
            "words": [w.to_dict() for w in self.words] if self.words else None,
            "source": self.source.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> TranscriptSegment:
        words = None
        if data.get("words"):
            words = [WordTimestamp.from_dict(w) for w in data["words"]]
        return cls(
            text=data["text"],
            start=data["start"],
            end=data["end"],
            confidence=data.get("confidence", 1.0),
            words=words,
            source=TranscriptSource(data.get("source", "none")),
        )


@dataclass(frozen=True)
class OCRRegion:
    """A detected text region in a video frame."""

    text: str
    confidence: float
    bbox: tuple[int, int, int, int]
    is_monospace: bool = False

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "confidence": self.confidence,
            "bbox": list(self.bbox),
            "is_monospace": self.is_monospace,
        }

    @classmethod
    def from_dict(cls, data: dict) -> OCRRegion:
        return cls(
            text=data["text"],
            confidence=data["confidence"],
            bbox=tuple(data["bbox"]),
            is_monospace=data.get("is_monospace", False),
        )


@dataclass
class FrameSubSection:
    """A single panel/region within a video frame, OCR'd independently.

    Each IDE panel (e.g. code editor, terminal, file tree) is detected
    as a separate sub-section so that side-by-side editors produce
    independent OCR results instead of being merged into one blob.
    """

    bbox: tuple[int, int, int, int]  # (x1, y1, x2, y2)
    frame_type: FrameType = FrameType.OTHER
    ocr_text: str = ""
    ocr_regions: list[OCRRegion] = field(default_factory=list)
    ocr_confidence: float = 0.0
    panel_id: str = ""  # e.g. "panel_0_0" (row_col)
    _vision_used: bool = False  # Whether Vision API was used for OCR

    def to_dict(self) -> dict:
        return {
            "bbox": list(self.bbox),
            "frame_type": self.frame_type.value,
            "ocr_text": self.ocr_text,
            "ocr_regions": [r.to_dict() for r in self.ocr_regions],
            "ocr_confidence": self.ocr_confidence,
            "panel_id": self.panel_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> FrameSubSection:
        return cls(
            bbox=tuple(data["bbox"]),
            frame_type=FrameType(data.get("frame_type", "other")),
            ocr_text=data.get("ocr_text", ""),
            ocr_regions=[OCRRegion.from_dict(r) for r in data.get("ocr_regions", [])],
            ocr_confidence=data.get("ocr_confidence", 0.0),
            panel_id=data.get("panel_id", ""),
        )


@dataclass
class KeyFrame:
    """An extracted video frame with visual analysis results."""

    timestamp: float
    image_path: str
    frame_type: FrameType = FrameType.OTHER
    scene_change_score: float = 0.0
    ocr_regions: list[OCRRegion] = field(default_factory=list)
    ocr_text: str = ""
    ocr_confidence: float = 0.0
    width: int = 0
    height: int = 0
    sub_sections: list[FrameSubSection] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "image_path": self.image_path,
            "frame_type": self.frame_type.value,
            "scene_change_score": self.scene_change_score,
            "ocr_regions": [r.to_dict() for r in self.ocr_regions],
            "ocr_text": self.ocr_text,
            "ocr_confidence": self.ocr_confidence,
            "width": self.width,
            "height": self.height,
            "sub_sections": [ss.to_dict() for ss in self.sub_sections],
        }

    @classmethod
    def from_dict(cls, data: dict) -> KeyFrame:
        return cls(
            timestamp=data["timestamp"],
            image_path=data["image_path"],
            frame_type=FrameType(data.get("frame_type", "other")),
            scene_change_score=data.get("scene_change_score", 0.0),
            ocr_regions=[OCRRegion.from_dict(r) for r in data.get("ocr_regions", [])],
            ocr_text=data.get("ocr_text", ""),
            ocr_confidence=data.get("ocr_confidence", 0.0),
            width=data.get("width", 0),
            height=data.get("height", 0),
            sub_sections=[FrameSubSection.from_dict(ss) for ss in data.get("sub_sections", [])],
        )


@dataclass
class CodeBlock:
    """A code block detected via OCR from video frames."""

    code: str
    language: str | None = None
    source_frame: float = 0.0
    context: CodeContext = CodeContext.UNKNOWN
    confidence: float = 0.0
    text_group_id: str = ""

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "language": self.language,
            "source_frame": self.source_frame,
            "context": self.context.value,
            "confidence": self.confidence,
            "text_group_id": self.text_group_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> CodeBlock:
        return cls(
            code=data["code"],
            language=data.get("language"),
            source_frame=data.get("source_frame", 0.0),
            context=CodeContext(data.get("context", "unknown")),
            confidence=data.get("confidence", 0.0),
            text_group_id=data.get("text_group_id", ""),
        )


@dataclass
class TextGroupEdit:
    """Represents an edit detected between appearances of a text group."""

    timestamp: float
    added_lines: list[str] = field(default_factory=list)
    removed_lines: list[str] = field(default_factory=list)
    modified_lines: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "added_lines": self.added_lines,
            "removed_lines": self.removed_lines,
            "modified_lines": self.modified_lines,
        }

    @classmethod
    def from_dict(cls, data: dict) -> TextGroupEdit:
        return cls(
            timestamp=data["timestamp"],
            added_lines=data.get("added_lines", []),
            removed_lines=data.get("removed_lines", []),
            modified_lines=data.get("modified_lines", []),
        )


@dataclass
class TextGroup:
    """A group of related text blocks tracked across the video.

    Represents a single code file/snippet as it appears and evolves
    across multiple video frames.
    """

    group_id: str
    appearances: list[tuple[float, float]] = field(default_factory=list)
    consensus_lines: list[dict] = field(default_factory=list)
    edits: list[TextGroupEdit] = field(default_factory=list)
    detected_language: str | None = None
    frame_type: FrameType = FrameType.CODE_EDITOR
    panel_id: str = ""  # Tracks which panel this group originated from

    @property
    def full_text(self) -> str:
        return "\n".join(line["text"] for line in self.consensus_lines if line.get("text"))

    def to_dict(self) -> dict:
        return {
            "group_id": self.group_id,
            "appearances": [[s, e] for s, e in self.appearances],
            "consensus_lines": self.consensus_lines,
            "edits": [e.to_dict() for e in self.edits],
            "detected_language": self.detected_language,
            "frame_type": self.frame_type.value,
            "panel_id": self.panel_id,
            "full_text": self.full_text,
        }

    @classmethod
    def from_dict(cls, data: dict) -> TextGroup:
        return cls(
            group_id=data["group_id"],
            appearances=[tuple(a) for a in data.get("appearances", [])],
            consensus_lines=data.get("consensus_lines", []),
            edits=[TextGroupEdit.from_dict(e) for e in data.get("edits", [])],
            detected_language=data.get("detected_language"),
            frame_type=FrameType(data.get("frame_type", "code_editor")),
            panel_id=data.get("panel_id", ""),
        )


@dataclass
class TextGroupTimeline:
    """Timeline of all text groups and their lifecycle in the video."""

    text_groups: list[TextGroup] = field(default_factory=list)
    total_code_time: float = 0.0
    total_groups: int = 0
    total_edits: int = 0

    def get_groups_at_time(self, timestamp: float) -> list[TextGroup]:
        """Return all text groups visible at a given timestamp."""
        return [
            tg
            for tg in self.text_groups
            if any(start <= timestamp <= end for start, end in tg.appearances)
        ]

    def to_dict(self) -> dict:
        return {
            "text_groups": [tg.to_dict() for tg in self.text_groups],
            "total_code_time": self.total_code_time,
            "total_groups": self.total_groups,
            "total_edits": self.total_edits,
        }

    @classmethod
    def from_dict(cls, data: dict) -> TextGroupTimeline:
        return cls(
            text_groups=[TextGroup.from_dict(tg) for tg in data.get("text_groups", [])],
            total_code_time=data.get("total_code_time", 0.0),
            total_groups=data.get("total_groups", 0),
            total_edits=data.get("total_edits", 0),
        )


@dataclass
class AudioVisualAlignment:
    """Links on-screen code with concurrent transcript narration."""

    text_group_id: str
    start_time: float
    end_time: float
    on_screen_code: str
    transcript_during: str
    language: str | None = None

    def to_dict(self) -> dict:
        return {
            "text_group_id": self.text_group_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "on_screen_code": self.on_screen_code,
            "transcript_during": self.transcript_during,
            "language": self.language,
        }

    @classmethod
    def from_dict(cls, data: dict) -> AudioVisualAlignment:
        return cls(
            text_group_id=data["text_group_id"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            on_screen_code=data["on_screen_code"],
            transcript_during=data.get("transcript_during", ""),
            language=data.get("language"),
        )


# =============================================================================
# Core Data Classes
# =============================================================================


@dataclass
class VideoSegment:
    """A time-aligned segment combining transcript + visual + metadata."""

    index: int
    start_time: float
    end_time: float
    duration: float

    # Stream 1: ASR (Audio)
    transcript: str = ""
    words: list[WordTimestamp] = field(default_factory=list)
    transcript_confidence: float = 0.0

    # Stream 2: OCR (Visual)
    keyframes: list[KeyFrame] = field(default_factory=list)
    ocr_text: str = ""
    detected_code_blocks: list[CodeBlock] = field(default_factory=list)
    has_code_on_screen: bool = False
    has_slides: bool = False
    has_diagram: bool = False

    # Stream 3: Metadata
    chapter_title: str | None = None
    topic: str | None = None
    category: str | None = None

    # Merged content
    content: str = ""
    summary: str | None = None

    # Quality metadata
    confidence: float = 0.0
    content_type: SegmentContentType = SegmentContentType.MIXED

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "transcript": self.transcript,
            "words": [w.to_dict() for w in self.words],
            "transcript_confidence": self.transcript_confidence,
            "keyframes": [k.to_dict() for k in self.keyframes],
            "ocr_text": self.ocr_text,
            "detected_code_blocks": [c.to_dict() for c in self.detected_code_blocks],
            "has_code_on_screen": self.has_code_on_screen,
            "has_slides": self.has_slides,
            "has_diagram": self.has_diagram,
            "chapter_title": self.chapter_title,
            "topic": self.topic,
            "category": self.category,
            "content": self.content,
            "summary": self.summary,
            "confidence": self.confidence,
            "content_type": self.content_type.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> VideoSegment:
        return cls(
            index=data["index"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            duration=data["duration"],
            transcript=data.get("transcript", ""),
            words=[WordTimestamp.from_dict(w) for w in data.get("words", [])],
            transcript_confidence=data.get("transcript_confidence", 0.0),
            keyframes=[KeyFrame.from_dict(k) for k in data.get("keyframes", [])],
            ocr_text=data.get("ocr_text", ""),
            detected_code_blocks=[
                CodeBlock.from_dict(c) for c in data.get("detected_code_blocks", [])
            ],
            has_code_on_screen=data.get("has_code_on_screen", False),
            has_slides=data.get("has_slides", False),
            has_diagram=data.get("has_diagram", False),
            chapter_title=data.get("chapter_title"),
            topic=data.get("topic"),
            category=data.get("category"),
            content=data.get("content", ""),
            summary=data.get("summary"),
            confidence=data.get("confidence", 0.0),
            content_type=SegmentContentType(data.get("content_type", "mixed")),
        )

    @property
    def timestamp_display(self) -> str:
        """Human-readable timestamp (e.g., '05:30 - 08:15')."""
        start_min, start_sec = divmod(int(self.start_time), 60)
        end_min, end_sec = divmod(int(self.end_time), 60)
        if self.start_time >= 3600 or self.end_time >= 3600:
            start_hr, start_min = divmod(start_min, 60)
            end_hr, end_min = divmod(end_min, 60)
            return f"{start_hr:d}:{start_min:02d}:{start_sec:02d} - {end_hr:d}:{end_min:02d}:{end_sec:02d}"
        return f"{start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d}"


@dataclass
class VideoInfo:
    """Complete metadata and extracted content for a single video."""

    # Identity
    video_id: str
    source_type: VideoSourceType
    source_url: str | None = None
    file_path: str | None = None

    # Basic metadata
    title: str = ""
    description: str = ""
    duration: float = 0.0
    upload_date: str | None = None
    language: str = "en"

    # Channel / Author
    channel_name: str | None = None
    channel_url: str | None = None

    # Engagement metadata
    view_count: int | None = None
    like_count: int | None = None
    comment_count: int | None = None

    # Discovery metadata
    tags: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    thumbnail_url: str | None = None

    # Structure
    chapters: list[Chapter] = field(default_factory=list)

    # Playlist context
    playlist_title: str | None = None
    playlist_index: int | None = None
    playlist_total: int | None = None

    # Extracted content
    raw_transcript: list[TranscriptSegment] = field(default_factory=list)
    segments: list[VideoSegment] = field(default_factory=list)

    # Processing metadata
    transcript_source: TranscriptSource = TranscriptSource.NONE
    visual_extraction_enabled: bool = False
    whisper_model: str | None = None
    processing_time_seconds: float = 0.0
    extracted_at: str = ""

    # Quality scores
    transcript_confidence: float = 0.0
    content_richness_score: float = 0.0

    # Time-clipping metadata (None when full video is used)
    original_duration: float | None = None
    clip_start: float | None = None
    clip_end: float | None = None

    # Consensus-based text tracking (Phase A-D)
    text_group_timeline: TextGroupTimeline | None = None
    audio_visual_alignments: list[AudioVisualAlignment] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "video_id": self.video_id,
            "source_type": self.source_type.value,
            "source_url": self.source_url,
            "file_path": self.file_path,
            "title": self.title,
            "description": self.description,
            "duration": self.duration,
            "upload_date": self.upload_date,
            "language": self.language,
            "channel_name": self.channel_name,
            "channel_url": self.channel_url,
            "view_count": self.view_count,
            "like_count": self.like_count,
            "comment_count": self.comment_count,
            "tags": self.tags,
            "categories": self.categories,
            "thumbnail_url": self.thumbnail_url,
            "chapters": [c.to_dict() for c in self.chapters],
            "playlist_title": self.playlist_title,
            "playlist_index": self.playlist_index,
            "playlist_total": self.playlist_total,
            "raw_transcript": [t.to_dict() for t in self.raw_transcript],
            "segments": [s.to_dict() for s in self.segments],
            "transcript_source": self.transcript_source.value,
            "visual_extraction_enabled": self.visual_extraction_enabled,
            "whisper_model": self.whisper_model,
            "processing_time_seconds": self.processing_time_seconds,
            "extracted_at": self.extracted_at,
            "transcript_confidence": self.transcript_confidence,
            "content_richness_score": self.content_richness_score,
            "original_duration": self.original_duration,
            "clip_start": self.clip_start,
            "clip_end": self.clip_end,
            "text_group_timeline": self.text_group_timeline.to_dict()
            if self.text_group_timeline
            else None,
            "audio_visual_alignments": [a.to_dict() for a in self.audio_visual_alignments],
        }

    @classmethod
    def from_dict(cls, data: dict) -> VideoInfo:
        timeline_data = data.get("text_group_timeline")
        timeline = TextGroupTimeline.from_dict(timeline_data) if timeline_data else None
        return cls(
            video_id=data["video_id"],
            source_type=VideoSourceType(data["source_type"]),
            source_url=data.get("source_url"),
            file_path=data.get("file_path"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            duration=data.get("duration", 0.0),
            upload_date=data.get("upload_date"),
            language=data.get("language", "en"),
            channel_name=data.get("channel_name"),
            channel_url=data.get("channel_url"),
            view_count=data.get("view_count"),
            like_count=data.get("like_count"),
            comment_count=data.get("comment_count"),
            tags=data.get("tags", []),
            categories=data.get("categories", []),
            thumbnail_url=data.get("thumbnail_url"),
            chapters=[Chapter.from_dict(c) for c in data.get("chapters", [])],
            playlist_title=data.get("playlist_title"),
            playlist_index=data.get("playlist_index"),
            playlist_total=data.get("playlist_total"),
            raw_transcript=[TranscriptSegment.from_dict(t) for t in data.get("raw_transcript", [])],
            segments=[VideoSegment.from_dict(s) for s in data.get("segments", [])],
            transcript_source=TranscriptSource(data.get("transcript_source", "none")),
            visual_extraction_enabled=data.get("visual_extraction_enabled", False),
            whisper_model=data.get("whisper_model"),
            processing_time_seconds=data.get("processing_time_seconds", 0.0),
            extracted_at=data.get("extracted_at", ""),
            transcript_confidence=data.get("transcript_confidence", 0.0),
            content_richness_score=data.get("content_richness_score", 0.0),
            original_duration=data.get("original_duration"),
            clip_start=data.get("clip_start"),
            clip_end=data.get("clip_end"),
            text_group_timeline=timeline,
            audio_visual_alignments=[
                AudioVisualAlignment.from_dict(a) for a in data.get("audio_visual_alignments", [])
            ],
        )


@dataclass
class VideoSourceConfig:
    """Configuration for video source processing."""

    # Source specification (exactly one should be set)
    url: str | None = None
    playlist: str | None = None
    channel: str | None = None
    path: str | None = None
    directory: str | None = None

    # Identity
    name: str = "video"
    description: str = ""

    # Filtering
    max_videos: int = 50
    languages: list[str] | None = None

    # Extraction
    visual_extraction: bool = False
    whisper_model: str = "base"

    # Segmentation
    time_window_seconds: float = 120.0
    min_segment_duration: float = 10.0
    max_segment_duration: float = 600.0

    # Categorization
    categories: dict[str, list[str]] | None = None

    # Subtitle files
    subtitle_patterns: list[str] | None = None

    # Time-clipping (single video only)
    clip_start: float | None = None
    clip_end: float | None = None

    @classmethod
    def from_dict(cls, data: dict) -> VideoSourceConfig:
        return cls(
            url=data.get("url"),
            playlist=data.get("playlist"),
            channel=data.get("channel"),
            path=data.get("path"),
            directory=data.get("directory"),
            name=data.get("name", "video"),
            description=data.get("description", ""),
            max_videos=data.get("max_videos", 50),
            languages=data.get("languages"),
            visual_extraction=data.get("visual_extraction", False),
            whisper_model=data.get("whisper_model", "base"),
            time_window_seconds=data.get("time_window_seconds", 120.0),
            min_segment_duration=data.get("min_segment_duration", 10.0),
            max_segment_duration=data.get("max_segment_duration", 600.0),
            categories=data.get("categories"),
            subtitle_patterns=data.get("subtitle_patterns"),
            clip_start=data.get("clip_start"),
            clip_end=data.get("clip_end"),
        )

    def validate(self) -> list[str]:
        """Validate configuration. Returns list of errors."""
        errors = []
        sources_set = sum(
            1
            for s in [self.url, self.playlist, self.channel, self.path, self.directory]
            if s is not None
        )
        if sources_set == 0:
            errors.append(
                "Video source must specify one of: url, playlist, channel, path, directory"
            )
        if sources_set > 1:
            errors.append("Video source must specify exactly one source type")

        # Clip range validation
        has_clip = self.clip_start is not None or self.clip_end is not None
        if has_clip and self.playlist is not None:
            errors.append(
                "--start-time/--end-time cannot be used with --playlist. "
                "Clip range is for single videos only."
            )
        if (
            self.clip_start is not None
            and self.clip_end is not None
            and self.clip_start >= self.clip_end
        ):
            errors.append(
                f"--start-time ({self.clip_start}s) must be before --end-time ({self.clip_end}s)"
            )

        return errors


@dataclass
class VideoScraperResult:
    """Complete result from the video scraper."""

    videos: list[VideoInfo] = field(default_factory=list)
    total_duration_seconds: float = 0.0
    total_segments: int = 0
    total_code_blocks: int = 0
    config: VideoSourceConfig | None = None
    processing_time_seconds: float = 0.0
    warnings: list[str] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "videos": [v.to_dict() for v in self.videos],
            "total_duration_seconds": self.total_duration_seconds,
            "total_segments": self.total_segments,
            "total_code_blocks": self.total_code_blocks,
            "processing_time_seconds": self.processing_time_seconds,
            "warnings": self.warnings,
            "errors": self.errors,
        }

    @classmethod
    def from_dict(cls, data: dict) -> VideoScraperResult:
        return cls(
            videos=[VideoInfo.from_dict(v) for v in data.get("videos", [])],
            total_duration_seconds=data.get("total_duration_seconds", 0.0),
            total_segments=data.get("total_segments", 0),
            total_code_blocks=data.get("total_code_blocks", 0),
            processing_time_seconds=data.get("processing_time_seconds", 0.0),
            warnings=data.get("warnings", []),
            errors=data.get("errors", []),
        )
