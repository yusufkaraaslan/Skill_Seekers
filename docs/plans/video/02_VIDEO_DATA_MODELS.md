# Video Source — Data Models & Type Definitions

**Date:** February 27, 2026
**Document:** 02 of 07
**Status:** Planning

---

## Table of Contents

1. [Design Principles](#design-principles)
2. [Core Data Classes](#core-data-classes)
3. [Supporting Data Classes](#supporting-data-classes)
4. [Enumerations](#enumerations)
5. [JSON Schema (Serialization)](#json-schema-serialization)
6. [Relationships Diagram](#relationships-diagram)
7. [Config Schema (Unified Config)](#config-schema-unified-config)

---

## Design Principles

1. **Immutable after creation** — Use `@dataclass(frozen=True)` for segments and frames. Once extracted, data doesn't change.
2. **Serializable** — Every data class must serialize to/from JSON for caching, output, and inter-process communication.
3. **Timeline-aligned** — Every piece of data has `start_time` and `end_time` fields. This is the alignment axis for merging streams.
4. **Confidence-scored** — Every extracted piece of content carries a confidence score for quality filtering.
5. **Source-aware** — Every piece of data traces back to its origin (which video, which stream, which tool).
6. **Compatible** — Output structures must be compatible with existing Skill Seekers page/reference format for seamless integration.

---

## Core Data Classes

### VideoInfo — The top-level container for a single video

```python
@dataclass
class VideoInfo:
    """Complete metadata and extracted content for a single video.

    This is the primary output of the video scraper for one video.
    It contains raw metadata from the platform, plus all extracted
    and aligned content (segments).

    Lifecycle:
        1. Created with metadata during resolve phase
        2. Transcript populated during ASR phase
        3. Visual data populated during OCR phase (if enabled)
        4. Segments populated during alignment phase
    """

    # === Identity ===
    video_id: str
    """Unique identifier.
    - YouTube: 11-char video ID (e.g., 'dQw4w9WgXcQ')
    - Vimeo: numeric ID (e.g., '123456789')
    - Local: SHA-256 hash of file path
    """

    source_type: VideoSourceType
    """Where this video came from (youtube, vimeo, local_file)."""

    source_url: str | None
    """Original URL for online videos. None for local files."""

    file_path: str | None
    """Local file path. Set for local files, or after download for
    online videos that needed audio extraction."""

    # === Basic Metadata ===
    title: str
    """Video title. For local files, derived from filename."""

    description: str
    """Full description text. Empty string for local files without metadata."""

    duration: float
    """Duration in seconds."""

    upload_date: str | None
    """Upload/creation date in ISO 8601 format (YYYY-MM-DD).
    None if unknown."""

    language: str
    """Primary language code (e.g., 'en', 'tr', 'ja').
    Detected from captions, Whisper, or metadata."""

    # === Channel / Author ===
    channel_name: str | None
    """Channel or uploader name."""

    channel_url: str | None
    """URL to the channel/uploader page."""

    channel_subscriber_count: int | None
    """Subscriber/follower count. Quality signal."""

    # === Engagement Metadata (quality signals) ===
    view_count: int | None
    """Total view count. Higher = more authoritative."""

    like_count: int | None
    """Like count."""

    comment_count: int | None
    """Comment count. Higher = more discussion."""

    # === Discovery Metadata ===
    tags: list[str]
    """Video tags from platform. Used for categorization."""

    categories: list[str]
    """Platform categories (e.g., ['Education', 'Science & Technology'])."""

    thumbnail_url: str | None
    """URL to the best quality thumbnail."""

    # === Structure ===
    chapters: list[Chapter]
    """YouTube chapter markers. Empty list if no chapters.
    This is the PRIMARY segmentation source."""

    # === Playlist Context ===
    playlist_title: str | None
    """Title of the playlist this video belongs to. None if standalone."""

    playlist_index: int | None
    """0-based index within the playlist. None if standalone."""

    playlist_total: int | None
    """Total number of videos in the playlist. None if standalone."""

    # === Extracted Content (populated during processing) ===
    raw_transcript: list[TranscriptSegment]
    """Raw transcript segments as received from YouTube API or Whisper.
    Before alignment and merging."""

    segments: list[VideoSegment]
    """Final aligned and merged segments. This is the PRIMARY output.
    Each segment combines ASR + OCR + metadata into a single unit."""

    # === Processing Metadata ===
    transcript_source: TranscriptSource
    """How the transcript was obtained."""

    visual_extraction_enabled: bool
    """Whether OCR/frame extraction was performed."""

    whisper_model: str | None
    """Whisper model used, if applicable (e.g., 'base', 'large-v3')."""

    processing_time_seconds: float
    """Total processing time for this video."""

    extracted_at: str
    """ISO 8601 timestamp of when extraction was performed."""

    # === Quality Scores (computed) ===
    transcript_confidence: float
    """Average confidence of transcript (0.0 - 1.0).
    Based on caption type or Whisper probability."""

    content_richness_score: float
    """How rich/useful the extracted content is (0.0 - 1.0).
    Based on: duration, chapters present, code detected, engagement."""

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dictionary."""
        ...

    @classmethod
    def from_dict(cls, data: dict) -> 'VideoInfo':
        """Deserialize from dictionary."""
        ...
```

### VideoSegment — The fundamental aligned content unit

```python
@dataclass
class VideoSegment:
    """A time-aligned segment combining all 3 extraction streams.

    This is the CORE data unit of the video pipeline. Every piece
    of video content is broken into segments that align:
    - ASR transcript (what was said)
    - OCR content (what was shown on screen)
    - Metadata (chapter title, topic)

    Segments are then used to generate reference markdown files
    and integrate into SKILL.md.

    Segmentation strategies (in priority order):
    1. Chapter boundaries (YouTube chapters)
    2. Semantic boundaries (topic shifts detected by NLP)
    3. Time windows (configurable interval, default 3-5 minutes)
    """

    # === Time Bounds ===
    index: int
    """0-based segment index within the video."""

    start_time: float
    """Start time in seconds."""

    end_time: float
    """End time in seconds."""

    duration: float
    """Segment duration in seconds (end_time - start_time)."""

    # === Stream 1: ASR (Audio) ===
    transcript: str
    """Full transcript text for this time window.
    Concatenated from word-level timestamps."""

    words: list[WordTimestamp]
    """Word-level timestamps within this segment.
    Allows precise text-to-time mapping."""

    transcript_confidence: float
    """Average confidence for this segment's transcript (0.0 - 1.0)."""

    # === Stream 2: OCR (Visual) ===
    keyframes: list[KeyFrame]
    """Extracted keyframes within this time window.
    Only populated if visual_extraction is enabled."""

    ocr_text: str
    """Combined OCR text from all keyframes in this segment.
    Deduplicated and cleaned."""

    detected_code_blocks: list[CodeBlock]
    """Code blocks detected on screen via OCR.
    Includes language detection and formatted code."""

    has_code_on_screen: bool
    """Whether code/terminal was detected on screen."""

    has_slides: bool
    """Whether presentation slides were detected."""

    has_diagram: bool
    """Whether diagrams/architecture drawings were detected."""

    # === Stream 3: Metadata ===
    chapter_title: str | None
    """YouTube chapter title if this segment maps to a chapter.
    None if video has no chapters or segment spans chapter boundary."""

    topic: str | None
    """Inferred topic for this segment.
    Derived from chapter title, transcript keywords, or AI classification."""

    category: str | None
    """Mapped category (e.g., 'getting_started', 'api', 'tutorial').
    Uses the same categorization system as other sources."""

    # === Merged Content ===
    content: str
    """Final merged text content for this segment.

    Merging strategy:
    1. Start with transcript text
    2. If code detected on screen but not mentioned in transcript,
       append code block with annotation
    3. If slide text detected, integrate as supplementary content
    4. Add chapter title as heading if present

    This is what gets written to reference markdown files.
    """

    summary: str | None
    """AI-generated summary of this segment (populated during enhancement).
    None until enhancement phase."""

    # === Quality Metadata ===
    confidence: float
    """Overall confidence for this segment (0.0 - 1.0).
    Weighted average of transcript + OCR confidences."""

    content_type: SegmentContentType
    """Primary content type of this segment."""

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dictionary."""
        ...

    @classmethod
    def from_dict(cls, data: dict) -> 'VideoSegment':
        """Deserialize from dictionary."""
        ...

    @property
    def timestamp_display(self) -> str:
        """Human-readable timestamp (e.g., '05:30 - 08:15')."""
        start_min, start_sec = divmod(int(self.start_time), 60)
        end_min, end_sec = divmod(int(self.end_time), 60)
        return f"{start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d}"

    @property
    def youtube_timestamp_url(self) -> str | None:
        """YouTube URL with timestamp parameter (e.g., '?t=330').
        Returns None if not a YouTube video."""
        ...
```

---

## Supporting Data Classes

### Chapter — YouTube chapter marker

```python
@dataclass(frozen=True)
class Chapter:
    """A chapter marker from a video (typically YouTube).

    Chapters provide natural content boundaries and are the
    preferred segmentation method.
    """
    title: str
    """Chapter title as shown in YouTube."""

    start_time: float
    """Start time in seconds."""

    end_time: float
    """End time in seconds."""

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    def to_dict(self) -> dict:
        return {
            'title': self.title,
            'start_time': self.start_time,
            'end_time': self.end_time,
        }
```

### TranscriptSegment — Raw transcript chunk from API/Whisper

```python
@dataclass(frozen=True)
class TranscriptSegment:
    """A raw transcript segment as received from the source.

    This is the unprocessed output from youtube-transcript-api or
    faster-whisper, before alignment and merging.

    youtube-transcript-api segments are typically 2-5 seconds each.
    faster-whisper segments are typically sentence-level (5-30 seconds).
    """
    text: str
    """Transcript text for this segment."""

    start: float
    """Start time in seconds."""

    end: float
    """End time in seconds. Computed as start + duration for YouTube API."""

    confidence: float
    """Confidence score (0.0 - 1.0).
    - YouTube manual captions: 1.0 (assumed perfect)
    - YouTube auto-generated: 0.8 (estimated)
    - Whisper: actual model probability
    """

    words: list[WordTimestamp] | None
    """Word-level timestamps, if available.
    Always available from faster-whisper.
    Not available from youtube-transcript-api.
    """

    source: TranscriptSource
    """Which tool produced this segment."""

    def to_dict(self) -> dict:
        return {
            'text': self.text,
            'start': self.start,
            'end': self.end,
            'confidence': self.confidence,
            'words': [w.to_dict() for w in self.words] if self.words else None,
            'source': self.source.value,
        }
```

### WordTimestamp — Individual word with timing

```python
@dataclass(frozen=True)
class WordTimestamp:
    """A single word with precise timing information.

    Enables precise text-to-time mapping within segments.
    Essential for aligning ASR with OCR content.
    """
    word: str
    """The word text."""

    start: float
    """Start time in seconds."""

    end: float
    """End time in seconds."""

    probability: float
    """Model confidence for this word (0.0 - 1.0).
    From faster-whisper's word_timestamps output."""

    def to_dict(self) -> dict:
        return {
            'word': self.word,
            'start': self.start,
            'end': self.end,
            'probability': self.probability,
        }
```

### KeyFrame — Extracted video frame with analysis

```python
@dataclass
class KeyFrame:
    """An extracted video frame with visual analysis results.

    Keyframes are extracted at:
    1. Scene change boundaries (PySceneDetect)
    2. Chapter boundaries
    3. Regular intervals within segments (configurable)

    Each frame is classified and optionally OCR'd.
    """
    timestamp: float
    """Exact timestamp in seconds where this frame was extracted."""

    image_path: str
    """Path to the saved frame image file (PNG).
    Relative to the video_data/frames/ directory."""

    frame_type: FrameType
    """Classification of what this frame shows."""

    scene_change_score: float
    """How different this frame is from the previous one (0.0 - 1.0).
    Higher = more significant visual change.
    From PySceneDetect's content detection."""

    # === OCR Results ===
    ocr_regions: list[OCRRegion]
    """All text regions detected in this frame.
    Empty list if OCR was not performed or no text detected."""

    ocr_text: str
    """Combined OCR text from all regions.
    Cleaned and deduplicated."""

    ocr_confidence: float
    """Average OCR confidence across all regions (0.0 - 1.0)."""

    # === Frame Properties ===
    width: int
    """Frame width in pixels."""

    height: int
    """Frame height in pixels."""

    mean_brightness: float
    """Average brightness (0-255). Used for classification."""

    def to_dict(self) -> dict:
        return {
            'timestamp': self.timestamp,
            'image_path': self.image_path,
            'frame_type': self.frame_type.value,
            'scene_change_score': self.scene_change_score,
            'ocr_regions': [r.to_dict() for r in self.ocr_regions],
            'ocr_text': self.ocr_text,
            'ocr_confidence': self.ocr_confidence,
            'width': self.width,
            'height': self.height,
        }
```

### OCRRegion — A detected text region in a frame

```python
@dataclass(frozen=True)
class OCRRegion:
    """A single text region detected by OCR within a frame.

    Includes bounding box coordinates for spatial analysis
    (e.g., detecting code editors vs. slide titles).
    """
    text: str
    """Detected text content."""

    confidence: float
    """OCR confidence (0.0 - 1.0)."""

    bbox: tuple[int, int, int, int]
    """Bounding box as (x1, y1, x2, y2) in pixels.
    Top-left to bottom-right."""

    is_monospace: bool
    """Whether the text appears to be in a monospace font.
    Indicates code/terminal content."""

    def to_dict(self) -> dict:
        return {
            'text': self.text,
            'confidence': self.confidence,
            'bbox': list(self.bbox),
            'is_monospace': self.is_monospace,
        }
```

### CodeBlock — Detected code on screen

```python
@dataclass
class CodeBlock:
    """A code block detected via OCR from video frames.

    Represents code that was visible on screen during a segment.
    May come from a code editor, terminal, or presentation slide.
    """
    code: str
    """The extracted code text. Cleaned and formatted."""

    language: str | None
    """Detected programming language (e.g., 'python', 'javascript').
    Uses the same detection heuristics as doc_scraper.detect_language().
    None if language cannot be determined."""

    source_frame: float
    """Timestamp of the frame where this code was extracted."""

    context: CodeContext
    """Where the code appeared (editor, terminal, slide)."""

    confidence: float
    """OCR confidence for this code block (0.0 - 1.0)."""

    def to_dict(self) -> dict:
        return {
            'code': self.code,
            'language': self.language,
            'source_frame': self.source_frame,
            'context': self.context.value,
            'confidence': self.confidence,
        }
```

### VideoPlaylist — Container for playlist processing

```python
@dataclass
class VideoPlaylist:
    """A playlist or channel containing multiple videos.

    Used to track multi-video processing state and ordering.
    """
    playlist_id: str
    """Platform playlist ID."""

    title: str
    """Playlist title."""

    description: str
    """Playlist description."""

    channel_name: str | None
    """Channel that owns the playlist."""

    video_count: int
    """Total number of videos in the playlist."""

    videos: list[VideoInfo]
    """Extracted video information for each video.
    Ordered by playlist index."""

    source_url: str
    """Original playlist URL."""

    def to_dict(self) -> dict:
        return {
            'playlist_id': self.playlist_id,
            'title': self.title,
            'description': self.description,
            'channel_name': self.channel_name,
            'video_count': self.video_count,
            'videos': [v.to_dict() for v in self.videos],
            'source_url': self.source_url,
        }
```

### VideoScraperResult — Top-level scraper output

```python
@dataclass
class VideoScraperResult:
    """Complete result from the video scraper.

    This is the top-level output that gets passed to the
    unified scraper and SKILL.md builder.
    """
    videos: list[VideoInfo]
    """All processed videos."""

    playlists: list[VideoPlaylist]
    """Playlist containers (if input was playlists)."""

    total_duration_seconds: float
    """Sum of all video durations."""

    total_segments: int
    """Sum of all segments across all videos."""

    total_code_blocks: int
    """Total code blocks detected across all videos."""

    categories: dict[str, list[VideoSegment]]
    """Segments grouped by detected category.
    Same category system as other sources."""

    config: VideoSourceConfig
    """Configuration used for this scrape."""

    processing_time_seconds: float
    """Total pipeline processing time."""

    warnings: list[str]
    """Any warnings generated during processing (e.g., missing captions)."""

    errors: list[VideoError]
    """Errors for individual videos that failed processing."""

    def to_dict(self) -> dict:
        ...
```

---

## Enumerations

```python
from enum import Enum

class VideoSourceType(Enum):
    """Where a video came from."""
    YOUTUBE = "youtube"
    VIMEO = "vimeo"
    LOCAL_FILE = "local_file"
    LOCAL_DIRECTORY = "local_directory"

class TranscriptSource(Enum):
    """How the transcript was obtained."""
    YOUTUBE_MANUAL = "youtube_manual"          # Human-created captions
    YOUTUBE_AUTO = "youtube_auto_generated"    # YouTube's ASR
    WHISPER = "whisper"                        # faster-whisper local ASR
    SUBTITLE_FILE = "subtitle_file"            # SRT/VTT file alongside video
    NONE = "none"                              # No transcript available

class FrameType(Enum):
    """Classification of a keyframe's visual content."""
    CODE_EDITOR = "code_editor"      # IDE or code editor visible
    TERMINAL = "terminal"            # Terminal/command line
    SLIDE = "slide"                  # Presentation slide
    DIAGRAM = "diagram"              # Architecture/flow diagram
    BROWSER = "browser"              # Web browser (documentation, output)
    WEBCAM = "webcam"                # Speaker face/webcam only
    SCREENCAST = "screencast"        # General screen recording
    OTHER = "other"                  # Unclassified

class CodeContext(Enum):
    """Where code was displayed in the video."""
    EDITOR = "editor"        # Code editor / IDE
    TERMINAL = "terminal"    # Terminal / command line output
    SLIDE = "slide"          # Code on a presentation slide
    BROWSER = "browser"      # Code in a browser (docs, playground)
    UNKNOWN = "unknown"

class SegmentContentType(Enum):
    """Primary content type of a video segment."""
    EXPLANATION = "explanation"    # Talking/explaining concepts
    LIVE_CODING = "live_coding"   # Writing code on screen
    DEMO = "demo"                 # Running/showing a demo
    SLIDES = "slides"             # Presentation slides
    Q_AND_A = "q_and_a"          # Q&A section
    INTRO = "intro"              # Introduction/overview
    OUTRO = "outro"              # Conclusion/wrap-up
    MIXED = "mixed"              # Combination of types

class SegmentationStrategy(Enum):
    """How segments are determined."""
    CHAPTERS = "chapters"                # YouTube chapter boundaries
    SEMANTIC = "semantic"                # Topic shift detection
    TIME_WINDOW = "time_window"          # Fixed time intervals
    SCENE_CHANGE = "scene_change"        # Visual scene changes
    HYBRID = "hybrid"                    # Combination of strategies
```

---

## JSON Schema (Serialization)

### VideoSegment JSON

```json
{
    "index": 0,
    "start_time": 45.0,
    "end_time": 180.0,
    "duration": 135.0,
    "transcript": "Let's start by setting up our React project. First, we'll use Create React App...",
    "words": [
        {"word": "Let's", "start": 45.0, "end": 45.3, "probability": 0.95},
        {"word": "start", "start": 45.3, "end": 45.6, "probability": 0.98}
    ],
    "transcript_confidence": 0.94,
    "keyframes": [
        {
            "timestamp": 52.3,
            "image_path": "frames/video_abc123/frame_52.30.png",
            "frame_type": "terminal",
            "scene_change_score": 0.72,
            "ocr_text": "npx create-react-app my-app",
            "ocr_confidence": 0.89,
            "ocr_regions": [
                {
                    "text": "npx create-react-app my-app",
                    "confidence": 0.89,
                    "bbox": [120, 340, 580, 370],
                    "is_monospace": true
                }
            ],
            "width": 1920,
            "height": 1080
        }
    ],
    "ocr_text": "npx create-react-app my-app\ncd my-app\nnpm start",
    "detected_code_blocks": [
        {
            "code": "npx create-react-app my-app\ncd my-app\nnpm start",
            "language": "bash",
            "source_frame": 52.3,
            "context": "terminal",
            "confidence": 0.89
        }
    ],
    "has_code_on_screen": true,
    "has_slides": false,
    "has_diagram": false,
    "chapter_title": "Project Setup",
    "topic": "react project setup",
    "category": "getting_started",
    "content": "## Project Setup (00:45 - 03:00)\n\nLet's start by setting up our React project...\n\n```bash\nnpx create-react-app my-app\ncd my-app\nnpm start\n```\n",
    "summary": null,
    "confidence": 0.92,
    "content_type": "live_coding"
}
```

### VideoInfo JSON (abbreviated)

```json
{
    "video_id": "abc123def45",
    "source_type": "youtube",
    "source_url": "https://www.youtube.com/watch?v=abc123def45",
    "file_path": null,
    "title": "React Hooks Tutorial for Beginners",
    "description": "Learn React Hooks from scratch...",
    "duration": 1832.0,
    "upload_date": "2026-01-15",
    "language": "en",
    "channel_name": "React Official",
    "channel_url": "https://www.youtube.com/@reactofficial",
    "channel_subscriber_count": 250000,
    "view_count": 1500000,
    "like_count": 45000,
    "comment_count": 2300,
    "tags": ["react", "hooks", "tutorial", "javascript"],
    "categories": ["Education"],
    "thumbnail_url": "https://i.ytimg.com/vi/abc123def45/maxresdefault.jpg",
    "chapters": [
        {"title": "Intro", "start_time": 0.0, "end_time": 45.0},
        {"title": "Project Setup", "start_time": 45.0, "end_time": 180.0},
        {"title": "useState Hook", "start_time": 180.0, "end_time": 540.0}
    ],
    "playlist_title": "React Complete Course",
    "playlist_index": 3,
    "playlist_total": 12,
    "segments": ["... (see VideoSegment JSON above)"],
    "transcript_source": "youtube_manual",
    "visual_extraction_enabled": true,
    "whisper_model": null,
    "processing_time_seconds": 45.2,
    "extracted_at": "2026-02-27T14:30:00Z",
    "transcript_confidence": 0.95,
    "content_richness_score": 0.88
}
```

---

## Relationships Diagram

```
VideoScraperResult
├── videos: list[VideoInfo]
│   ├── chapters: list[Chapter]
│   ├── raw_transcript: list[TranscriptSegment]
│   │   └── words: list[WordTimestamp] | None
│   └── segments: list[VideoSegment]            ← PRIMARY OUTPUT
│       ├── words: list[WordTimestamp]
│       ├── keyframes: list[KeyFrame]
│       │   └── ocr_regions: list[OCRRegion]
│       └── detected_code_blocks: list[CodeBlock]
├── playlists: list[VideoPlaylist]
│   └── videos: list[VideoInfo]                 ← same as above
├── categories: dict[str, list[VideoSegment]]
├── config: VideoSourceConfig
└── errors: list[VideoError]
```

---

## Config Schema (Unified Config)

### Video source in unified config JSON

```json
{
    "type": "video",

    "_comment_source": "One of: url, playlist, channel, path, directory",

    "url": "https://www.youtube.com/watch?v=abc123",
    "playlist": "https://www.youtube.com/playlist?list=PLxxx",
    "channel": "https://www.youtube.com/@channelname",
    "path": "./recordings/tutorial.mp4",
    "directory": "./recordings/",

    "name": "official_tutorials",
    "description": "Official React tutorial videos",
    "weight": 0.2,

    "_comment_filtering": "Control which videos to process",
    "max_videos": 20,
    "min_duration": 60,
    "max_duration": 7200,
    "languages": ["en"],
    "title_include_patterns": ["tutorial", "guide"],
    "title_exclude_patterns": ["shorts", "live stream"],
    "min_views": 1000,
    "upload_after": "2024-01-01",

    "_comment_extraction": "Control extraction depth",
    "visual_extraction": true,
    "whisper_model": "base",
    "whisper_device": "auto",
    "ocr_languages": ["en"],
    "keyframe_interval": 5.0,
    "min_scene_change_score": 0.3,
    "ocr_confidence_threshold": 0.5,
    "transcript_confidence_threshold": 0.3,

    "_comment_segmentation": "Control how content is segmented",
    "segmentation_strategy": "hybrid",
    "time_window_seconds": 300,
    "merge_short_segments": true,
    "min_segment_duration": 30,
    "max_segment_duration": 600,

    "_comment_categorization": "Map segments to categories",
    "categories": {
        "getting_started": ["intro", "quickstart", "setup", "install"],
        "hooks": ["useState", "useEffect", "useContext", "hooks"],
        "components": ["component", "props", "state", "render"],
        "advanced": ["performance", "suspense", "concurrent", "ssr"]
    },

    "_comment_local_files": "For local video sources",
    "file_patterns": ["*.mp4", "*.mkv", "*.webm"],
    "subtitle_patterns": ["*.srt", "*.vtt"],
    "recursive": true
}
```

### VideoSourceConfig dataclass (parsed from JSON)

```python
@dataclass
class VideoSourceConfig:
    """Configuration for video source processing.

    Parsed from the 'sources' entry in unified config JSON.
    Provides defaults for all optional fields.
    """
    # Source specification (exactly one must be set)
    url: str | None = None
    playlist: str | None = None
    channel: str | None = None
    path: str | None = None
    directory: str | None = None

    # Identity
    name: str = "video"
    description: str = ""
    weight: float = 0.2

    # Filtering
    max_videos: int = 50
    min_duration: float = 60.0          # 1 minute
    max_duration: float = 7200.0        # 2 hours
    languages: list[str] | None = None  # None = all languages
    title_include_patterns: list[str] | None = None
    title_exclude_patterns: list[str] | None = None
    min_views: int | None = None
    upload_after: str | None = None     # ISO date

    # Extraction
    visual_extraction: bool = False     # Off by default (heavy)
    whisper_model: str = "base"
    whisper_device: str = "auto"        # 'auto', 'cpu', 'cuda'
    ocr_languages: list[str] | None = None
    keyframe_interval: float = 5.0      # Extract frame every N seconds within segment
    min_scene_change_score: float = 0.3
    ocr_confidence_threshold: float = 0.5
    transcript_confidence_threshold: float = 0.3

    # Segmentation
    segmentation_strategy: str = "hybrid"
    time_window_seconds: float = 300.0  # 5 minutes
    merge_short_segments: bool = True
    min_segment_duration: float = 30.0
    max_segment_duration: float = 600.0

    # Categorization
    categories: dict[str, list[str]] | None = None

    # Local file options
    file_patterns: list[str] | None = None
    subtitle_patterns: list[str] | None = None
    recursive: bool = True

    @classmethod
    def from_dict(cls, data: dict) -> 'VideoSourceConfig':
        """Create config from unified config source entry."""
        ...

    def validate(self) -> list[str]:
        """Validate configuration. Returns list of errors."""
        errors = []
        sources_set = sum(1 for s in [self.url, self.playlist, self.channel,
                                       self.path, self.directory] if s is not None)
        if sources_set == 0:
            errors.append("Video source must specify one of: url, playlist, channel, path, directory")
        if sources_set > 1:
            errors.append("Video source must specify exactly one source type")
        if self.min_duration >= self.max_duration:
            errors.append("min_duration must be less than max_duration")
        if self.min_segment_duration >= self.max_segment_duration:
            errors.append("min_segment_duration must be less than max_segment_duration")
        return errors
```
