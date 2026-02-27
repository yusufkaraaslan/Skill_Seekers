# Video Source — Testing Strategy

**Date:** February 27, 2026
**Document:** 06 of 07
**Status:** Planning

---

## Table of Contents

1. [Testing Principles](#testing-principles)
2. [Test File Structure](#test-file-structure)
3. [Fixtures & Mock Data](#fixtures--mock-data)
4. [Unit Tests](#unit-tests)
5. [Integration Tests](#integration-tests)
6. [E2E Tests](#e2e-tests)
7. [CI Considerations](#ci-considerations)
8. [Performance Tests](#performance-tests)

---

## Testing Principles

1. **No network calls in unit tests** — All YouTube API, yt-dlp, and download operations must be mocked.
2. **No GPU required in CI** — All Whisper and easyocr tests must work on CPU, or be marked `@pytest.mark.slow`.
3. **No video files in repo** — Test fixtures use JSON transcripts and small synthetic images, not actual video files.
4. **100% pipeline coverage** — Every phase of the 6-phase pipeline must be tested.
5. **Edge case focus** — Test missing chapters, empty transcripts, corrupt frames, rate limits.
6. **Compatible with existing test infra** — Use existing conftest.py, markers, and patterns.

---

## Test File Structure

```
tests/
├── test_video_models.py          # Data model tests (serialization, validation)
├── test_video_scraper.py         # Main scraper orchestration tests
├── test_video_transcript.py      # Transcript extraction tests
├── test_video_visual.py          # Visual extraction tests
├── test_video_segmenter.py       # Segmentation and alignment tests
├── test_video_integration.py     # Integration with unified scraper, create command
├── test_video_output.py          # Output generation tests
├── test_video_source_detector.py # Source detection tests (or add to existing)
├── fixtures/
│   └── video/
│       ├── sample_metadata.json       # yt-dlp info_dict mock
│       ├── sample_transcript.json     # YouTube transcript mock
│       ├── sample_whisper_output.json # Whisper transcription mock
│       ├── sample_chapters.json       # Chapter data mock
│       ├── sample_playlist.json       # Playlist metadata mock
│       ├── sample_segments.json       # Pre-aligned segments
│       ├── sample_frame_code.png      # 100x100 synthetic dark frame
│       ├── sample_frame_slide.png     # 100x100 synthetic light frame
│       ├── sample_frame_diagram.png   # 100x100 synthetic edge-heavy frame
│       ├── sample_srt.srt             # SRT subtitle file
│       ├── sample_vtt.vtt             # WebVTT subtitle file
│       └── sample_config.json         # Video source config
```

---

## Fixtures & Mock Data

### yt-dlp Metadata Fixture

```python
# tests/fixtures/video/sample_metadata.json
SAMPLE_YTDLP_METADATA = {
    "id": "abc123def45",
    "title": "React Hooks Tutorial for Beginners",
    "description": "Learn React Hooks from scratch. Covers useState, useEffect, and custom hooks.",
    "duration": 1832,
    "upload_date": "20260115",
    "uploader": "React Official",
    "uploader_url": "https://www.youtube.com/@reactofficial",
    "channel_follower_count": 250000,
    "view_count": 1500000,
    "like_count": 45000,
    "comment_count": 2300,
    "tags": ["react", "hooks", "tutorial", "javascript"],
    "categories": ["Education"],
    "language": "en",
    "thumbnail": "https://i.ytimg.com/vi/abc123def45/maxresdefault.jpg",
    "webpage_url": "https://www.youtube.com/watch?v=abc123def45",
    "chapters": [
        {"title": "Intro", "start_time": 0, "end_time": 45},
        {"title": "Project Setup", "start_time": 45, "end_time": 180},
        {"title": "useState Hook", "start_time": 180, "end_time": 540},
        {"title": "useEffect Hook", "start_time": 540, "end_time": 900},
        {"title": "Custom Hooks", "start_time": 900, "end_time": 1320},
        {"title": "Best Practices", "start_time": 1320, "end_time": 1680},
        {"title": "Wrap Up", "start_time": 1680, "end_time": 1832},
    ],
    "subtitles": {
        "en": [{"ext": "vtt", "url": "https://..."}],
    },
    "automatic_captions": {
        "en": [{"ext": "vtt", "url": "https://..."}],
    },
    "extractor": "youtube",
}
```

### YouTube Transcript Fixture

```python
SAMPLE_YOUTUBE_TRANSCRIPT = [
    {"text": "Welcome to this React Hooks tutorial.", "start": 0.0, "duration": 2.5},
    {"text": "Today we'll learn about the most important hooks.", "start": 2.5, "duration": 3.0},
    {"text": "Let's start by setting up our project.", "start": 45.0, "duration": 2.8},
    {"text": "We'll use Create React App.", "start": 47.8, "duration": 2.0},
    {"text": "Run npx create-react-app hooks-demo.", "start": 49.8, "duration": 3.5},
    # ... more segments covering all chapters
]
```

### Whisper Output Fixture

```python
SAMPLE_WHISPER_OUTPUT = {
    "language": "en",
    "language_probability": 0.98,
    "duration": 1832.0,
    "segments": [
        {
            "start": 0.0,
            "end": 2.5,
            "text": "Welcome to this React Hooks tutorial.",
            "avg_logprob": -0.15,
            "no_speech_prob": 0.01,
            "words": [
                {"word": "Welcome", "start": 0.0, "end": 0.4, "probability": 0.97},
                {"word": "to", "start": 0.4, "end": 0.5, "probability": 0.99},
                {"word": "this", "start": 0.5, "end": 0.7, "probability": 0.98},
                {"word": "React", "start": 0.7, "end": 1.1, "probability": 0.95},
                {"word": "Hooks", "start": 1.1, "end": 1.5, "probability": 0.93},
                {"word": "tutorial.", "start": 1.5, "end": 2.3, "probability": 0.96},
            ],
        },
    ],
}
```

### Synthetic Frame Fixtures

```python
# Generate in conftest.py or fixture setup
import numpy as np
import cv2

def create_dark_frame(path: str):
    """Create a synthetic dark frame (simulates code editor)."""
    img = np.zeros((1080, 1920, 3), dtype=np.uint8)
    img[200:250, 100:800] = [200, 200, 200]  # Simulated text line
    img[270:320, 100:600] = [180, 180, 180]  # Another text line
    cv2.imwrite(path, img)

def create_light_frame(path: str):
    """Create a synthetic light frame (simulates slide)."""
    img = np.ones((1080, 1920, 3), dtype=np.uint8) * 240
    img[100:150, 200:1000] = [40, 40, 40]  # Title text
    img[300:330, 200:1200] = [60, 60, 60]  # Body text
    cv2.imwrite(path, img)
```

### conftest.py Additions

```python
# tests/conftest.py — add video fixtures

import pytest
import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "video"


@pytest.fixture
def sample_ytdlp_metadata():
    """Load sample yt-dlp metadata."""
    with open(FIXTURES_DIR / "sample_metadata.json") as f:
        return json.load(f)


@pytest.fixture
def sample_transcript():
    """Load sample YouTube transcript."""
    with open(FIXTURES_DIR / "sample_transcript.json") as f:
        return json.load(f)


@pytest.fixture
def sample_whisper_output():
    """Load sample Whisper transcription output."""
    with open(FIXTURES_DIR / "sample_whisper_output.json") as f:
        return json.load(f)


@pytest.fixture
def sample_chapters():
    """Load sample chapter data."""
    with open(FIXTURES_DIR / "sample_chapters.json") as f:
        return json.load(f)


@pytest.fixture
def sample_video_config():
    """Create a sample VideoSourceConfig."""
    from skill_seekers.cli.video_models import VideoSourceConfig
    return VideoSourceConfig(
        url="https://www.youtube.com/watch?v=abc123def45",
        name="test_video",
        visual_extraction=False,
        max_videos=5,
    )


@pytest.fixture
def video_output_dir(tmp_path):
    """Create a temporary output directory for video tests."""
    output = tmp_path / "output" / "test_video"
    output.mkdir(parents=True)
    (output / "video_data").mkdir()
    (output / "video_data" / "transcripts").mkdir()
    (output / "video_data" / "segments").mkdir()
    (output / "video_data" / "frames").mkdir()
    (output / "references").mkdir()
    (output / "pages").mkdir()
    return output
```

---

## Unit Tests

### test_video_models.py

```python
"""Tests for video data models and serialization."""

class TestVideoInfo:
    def test_create_from_ytdlp_metadata(self, sample_ytdlp_metadata):
        """VideoInfo correctly parses yt-dlp info_dict."""
        ...

    def test_serialization_round_trip(self):
        """VideoInfo serializes to dict and deserializes back identically."""
        ...

    def test_content_richness_score(self):
        """Content richness score computed correctly based on signals."""
        ...

    def test_empty_chapters(self):
        """VideoInfo handles video with no chapters."""
        ...


class TestVideoSegment:
    def test_timestamp_display(self):
        """Timestamp display formats correctly (MM:SS - MM:SS)."""
        ...

    def test_youtube_timestamp_url(self):
        """YouTube timestamp URL generated correctly."""
        ...

    def test_segment_with_code_blocks(self):
        """Segment correctly tracks detected code blocks."""
        ...

    def test_segment_without_visual(self):
        """Segment works when visual extraction is disabled."""
        ...


class TestChapter:
    def test_chapter_duration(self):
        """Chapter duration computed correctly."""
        ...

    def test_chapter_serialization(self):
        """Chapter serializes to/from dict."""
        ...


class TestTranscriptSegment:
    def test_from_youtube_api(self):
        """TranscriptSegment created from YouTube API format."""
        ...

    def test_from_whisper_output(self):
        """TranscriptSegment created from Whisper output."""
        ...

    def test_with_word_timestamps(self):
        """TranscriptSegment preserves word-level timestamps."""
        ...


class TestVideoSourceConfig:
    def test_validate_single_source(self):
        """Config requires exactly one source field."""
        ...

    def test_validate_duration_range(self):
        """Config validates min < max duration."""
        ...

    def test_defaults(self):
        """Config has sensible defaults."""
        ...

    def test_from_unified_config(self, sample_video_config):
        """Config created from unified config JSON entry."""
        ...


class TestEnums:
    def test_all_video_source_types(self):
        """All VideoSourceType values are valid."""
        ...

    def test_all_frame_types(self):
        """All FrameType values are valid."""
        ...

    def test_all_transcript_sources(self):
        """All TranscriptSource values are valid."""
        ...
```

### test_video_transcript.py

```python
"""Tests for transcript extraction (YouTube API + Whisper + subtitle parsing)."""

class TestYouTubeTranscript:
    @patch('skill_seekers.cli.video_transcript.YouTubeTranscriptApi')
    def test_extract_manual_captions(self, mock_api, sample_transcript):
        """Prefers manual captions over auto-generated."""
        ...

    @patch('skill_seekers.cli.video_transcript.YouTubeTranscriptApi')
    def test_fallback_to_auto_generated(self, mock_api):
        """Falls back to auto-generated when manual not available."""
        ...

    @patch('skill_seekers.cli.video_transcript.YouTubeTranscriptApi')
    def test_fallback_to_translation(self, mock_api):
        """Falls back to translated captions when preferred language unavailable."""
        ...

    @patch('skill_seekers.cli.video_transcript.YouTubeTranscriptApi')
    def test_no_transcript_available(self, mock_api):
        """Raises TranscriptNotAvailable when no captions exist."""
        ...

    @patch('skill_seekers.cli.video_transcript.YouTubeTranscriptApi')
    def test_confidence_scoring(self, mock_api, sample_transcript):
        """Manual captions get 1.0 confidence, auto-generated get 0.8."""
        ...


class TestWhisperTranscription:
    @pytest.mark.slow
    @patch('skill_seekers.cli.video_transcript.WhisperModel')
    def test_transcribe_with_word_timestamps(self, mock_model):
        """Whisper returns word-level timestamps."""
        ...

    @patch('skill_seekers.cli.video_transcript.WhisperModel')
    def test_language_detection(self, mock_model):
        """Whisper detects video language."""
        ...

    @patch('skill_seekers.cli.video_transcript.WhisperModel')
    def test_vad_filtering(self, mock_model):
        """VAD filter removes silence segments."""
        ...

    def test_download_audio_only(self):
        """Audio extraction downloads audio stream only (not video)."""
        # Mock yt-dlp download
        ...


class TestSubtitleParsing:
    def test_parse_srt(self, tmp_path):
        """Parse SRT subtitle file into segments."""
        srt_content = "1\n00:00:01,500 --> 00:00:04,000\nHello world\n\n2\n00:00:05,000 --> 00:00:08,000\nSecond line\n"
        srt_file = tmp_path / "test.srt"
        srt_file.write_text(srt_content)
        ...

    def test_parse_vtt(self, tmp_path):
        """Parse WebVTT subtitle file into segments."""
        vtt_content = "WEBVTT\n\n00:00:01.500 --> 00:00:04.000\nHello world\n\n00:00:05.000 --> 00:00:08.000\nSecond line\n"
        vtt_file = tmp_path / "test.vtt"
        vtt_file.write_text(vtt_content)
        ...

    def test_srt_html_tag_removal(self, tmp_path):
        """SRT parser removes inline HTML tags."""
        ...

    def test_empty_subtitle_file(self, tmp_path):
        """Handle empty subtitle file gracefully."""
        ...


class TestTranscriptFallbackChain:
    @patch('skill_seekers.cli.video_transcript.YouTubeTranscriptApi')
    @patch('skill_seekers.cli.video_transcript.WhisperModel')
    def test_youtube_then_whisper_fallback(self, mock_whisper, mock_yt_api):
        """Falls back to Whisper when YouTube captions fail."""
        ...

    def test_subtitle_file_discovery(self, tmp_path):
        """Discovers sidecar subtitle files for local videos."""
        ...
```

### test_video_visual.py

```python
"""Tests for visual extraction (scene detection, frame extraction, OCR)."""

class TestFrameClassification:
    def test_classify_dark_frame_as_code(self, tmp_path):
        """Dark frame with text patterns classified as code_editor."""
        ...

    def test_classify_light_frame_as_slide(self, tmp_path):
        """Light uniform frame classified as slide."""
        ...

    def test_classify_high_edge_as_diagram(self, tmp_path):
        """High edge density frame classified as diagram."""
        ...

    def test_classify_blank_frame_as_other(self, tmp_path):
        """Nearly blank frame classified as other."""
        ...


class TestKeyframeTimestamps:
    def test_chapter_boundaries_included(self, sample_chapters):
        """Keyframe timestamps include chapter start times."""
        ...

    def test_long_chapter_midpoint(self, sample_chapters):
        """Long chapters (>2 min) get midpoint keyframe."""
        ...

    def test_deduplication_within_1_second(self):
        """Timestamps within 1 second are deduplicated."""
        ...

    def test_regular_intervals_fill_gaps(self):
        """Regular interval timestamps fill gaps between scenes."""
        ...


class TestOCRExtraction:
    @pytest.mark.slow
    @patch('skill_seekers.cli.video_visual.easyocr.Reader')
    def test_extract_text_from_code_frame(self, mock_reader, tmp_path):
        """OCR extracts text from code editor frame."""
        ...

    @patch('skill_seekers.cli.video_visual.easyocr.Reader')
    def test_confidence_filtering(self, mock_reader):
        """Low-confidence OCR results are filtered out."""
        ...

    @patch('skill_seekers.cli.video_visual.easyocr.Reader')
    def test_monospace_detection(self, mock_reader):
        """Monospace text regions correctly detected."""
        ...


class TestCodeBlockDetection:
    def test_detect_python_code(self):
        """Detect Python code from OCR text."""
        ...

    def test_detect_terminal_commands(self):
        """Detect terminal commands from OCR text."""
        ...

    def test_language_detection_from_ocr(self):
        """Language detection works on OCR-extracted code."""
        ...
```

### test_video_segmenter.py

```python
"""Tests for segmentation and stream alignment."""

class TestChapterSegmentation:
    def test_chapters_create_segments(self, sample_chapters):
        """Chapters map directly to segments."""
        ...

    def test_long_chapter_splitting(self):
        """Chapters exceeding max_segment_duration are split."""
        ...

    def test_empty_chapters(self):
        """Falls back to time window when no chapters."""
        ...


class TestTimeWindowSegmentation:
    def test_fixed_windows(self):
        """Creates segments at fixed intervals."""
        ...

    def test_sentence_boundary_alignment(self):
        """Segments split at sentence boundaries, not mid-word."""
        ...

    def test_configurable_window_size(self):
        """Window size respects config.time_window_seconds."""
        ...


class TestStreamAlignment:
    def test_align_transcript_to_segments(self, sample_transcript, sample_chapters):
        """Transcript segments mapped to correct time windows."""
        ...

    def test_align_keyframes_to_segments(self):
        """Keyframes mapped to correct segments by timestamp."""
        ...

    def test_partial_overlap_handling(self):
        """Transcript segments partially overlapping window boundaries."""
        ...

    def test_empty_segment_handling(self):
        """Handle segments with no transcript (silence, music)."""
        ...


class TestContentMerging:
    def test_transcript_only_content(self):
        """Content is just transcript when no visual data."""
        ...

    def test_code_block_appended(self):
        """Code on screen is appended to transcript content."""
        ...

    def test_duplicate_code_not_repeated(self):
        """Code mentioned in transcript is not duplicated from OCR."""
        ...

    def test_chapter_title_as_heading(self):
        """Chapter title becomes markdown heading in content."""
        ...

    def test_slide_text_supplementary(self):
        """Slide text adds to content when not in transcript."""
        ...


class TestCategorization:
    def test_category_from_chapter_title(self):
        """Category inferred from chapter title keywords."""
        ...

    def test_category_from_transcript(self):
        """Category inferred from transcript content."""
        ...

    def test_custom_categories_from_config(self):
        """Custom category keywords from config used."""
        ...
```

---

## Integration Tests

### test_video_integration.py

```python
"""Integration tests for video pipeline end-to-end."""

class TestSourceDetectorVideo:
    def test_detect_youtube_video(self):
        info = SourceDetector.detect("https://youtube.com/watch?v=abc123def45")
        assert info.type == "video"
        assert info.parsed["video_source"] == "youtube_video"

    def test_detect_youtube_short_url(self):
        info = SourceDetector.detect("https://youtu.be/abc123def45")
        assert info.type == "video"

    def test_detect_youtube_playlist(self):
        info = SourceDetector.detect("https://youtube.com/playlist?list=PLxxx")
        assert info.type == "video"
        assert info.parsed["video_source"] == "youtube_playlist"

    def test_detect_youtube_channel(self):
        info = SourceDetector.detect("https://youtube.com/@reactofficial")
        assert info.type == "video"
        assert info.parsed["video_source"] == "youtube_channel"

    def test_detect_vimeo(self):
        info = SourceDetector.detect("https://vimeo.com/123456789")
        assert info.type == "video"
        assert info.parsed["video_source"] == "vimeo"

    def test_detect_mp4_file(self, tmp_path):
        f = tmp_path / "tutorial.mp4"
        f.touch()
        info = SourceDetector.detect(str(f))
        assert info.type == "video"
        assert info.parsed["video_source"] == "local_file"

    def test_detect_video_directory(self, tmp_path):
        d = tmp_path / "videos"
        d.mkdir()
        (d / "vid1.mp4").touch()
        (d / "vid2.mkv").touch()
        info = SourceDetector.detect(str(d))
        assert info.type == "video"

    def test_youtube_not_confused_with_web(self):
        """YouTube URLs detected as video, not web."""
        info = SourceDetector.detect("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert info.type == "video"
        assert info.type != "web"


class TestUnifiedConfigVideo:
    def test_video_source_in_config(self, tmp_path):
        """Video source parsed correctly from unified config."""
        ...

    def test_multiple_video_sources(self, tmp_path):
        """Multiple video sources in same config."""
        ...

    def test_video_alongside_docs(self, tmp_path):
        """Video source alongside documentation source."""
        ...


class TestFullPipeline:
    @patch('skill_seekers.cli.video_transcript.YouTubeTranscriptApi')
    @patch('skill_seekers.cli.video_scraper.YoutubeDL')
    def test_single_video_transcript_only(
        self, mock_ytdl, mock_transcript, sample_ytdlp_metadata,
        sample_transcript, video_output_dir
    ):
        """Full pipeline: single YouTube video, transcript only."""
        mock_ytdl.return_value.__enter__.return_value.extract_info.return_value = sample_ytdlp_metadata
        mock_transcript.list_transcripts.return_value = ...

        # Run pipeline
        # Assert output files exist and content is correct
        ...

    @pytest.mark.slow
    @patch('skill_seekers.cli.video_visual.easyocr.Reader')
    @patch('skill_seekers.cli.video_transcript.YouTubeTranscriptApi')
    @patch('skill_seekers.cli.video_scraper.YoutubeDL')
    def test_single_video_with_visual(
        self, mock_ytdl, mock_transcript, mock_ocr,
        sample_ytdlp_metadata, video_output_dir
    ):
        """Full pipeline: single video with visual extraction."""
        ...
```

---

## CI Considerations

### What Runs in CI (Default)

- All unit tests (mocked, no network, no GPU)
- Integration tests with mocked external services
- Source detection tests (pure logic)
- Data model tests (pure logic)

### What Doesn't Run in CI (Marked)

```python
@pytest.mark.slow       # Whisper model loading, actual OCR
@pytest.mark.integration  # Real YouTube API calls
@pytest.mark.e2e         # Full pipeline with real video download
```

### CI Test Matrix Compatibility

| Test | Ubuntu | macOS | Python 3.10 | Python 3.12 | GPU |
|------|--------|-------|-------------|-------------|-----|
| Unit tests | Yes | Yes | Yes | Yes | No |
| Integration (mocked) | Yes | Yes | Yes | Yes | No |
| Whisper tests (mocked) | Yes | Yes | Yes | Yes | No |
| OCR tests (mocked) | Yes | Yes | Yes | Yes | No |
| E2E (real download) | Skip | Skip | Skip | Skip | No |

### Dependency Handling in Tests

```python
# At top of visual test files:
pytest.importorskip("cv2", reason="opencv-python-headless required for visual tests")
pytest.importorskip("easyocr", reason="easyocr required for OCR tests")

# At top of whisper test files:
pytest.importorskip("faster_whisper", reason="faster-whisper required for transcription tests")
```

---

## Performance Tests

```python
@pytest.mark.benchmark
class TestVideoPerformance:
    def test_transcript_parsing_speed(self, sample_transcript):
        """Transcript parsing completes in < 10ms for 1000 segments."""
        ...

    def test_segment_alignment_speed(self):
        """Segment alignment completes in < 50ms for 100 segments."""
        ...

    def test_frame_classification_speed(self, tmp_path):
        """Frame classification completes in < 20ms per frame."""
        ...

    def test_content_merging_speed(self):
        """Content merging completes in < 5ms per segment."""
        ...

    def test_output_generation_speed(self, video_output_dir):
        """Output generation (5 videos, 50 segments) in < 1 second."""
        ...
```
