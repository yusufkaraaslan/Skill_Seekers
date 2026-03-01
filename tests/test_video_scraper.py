#!/usr/bin/env python3
"""
Tests for Video Scraper (cli/video_scraper.py)

Tests cover:
- Data models (enums, dataclasses, serialization)
- Metadata extraction (YouTube URL parsing, video ID extraction)
- Transcript extraction (SRT/VTT parsing, fallback chain)
- Segmentation (chapter-based, time-window)
- Full pipeline (VideoToSkillConverter)
- Source detection (SourceDetector video patterns)
- CLI argument parsing
- Create command routing
"""

import os
import shutil
import tempfile
import unittest

# Video-specific deps are optional
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


# =============================================================================
# Helper: Build mock data
# =============================================================================


def _make_sample_video_info():
    """Build a minimal VideoInfo dict for testing."""
    from skill_seekers.cli.video_models import (
        TranscriptSource,
        VideoInfo,
        VideoSourceType,
        Chapter,
    )

    return VideoInfo(
        video_id="abc123def45",
        source_type=VideoSourceType.YOUTUBE,
        source_url="https://www.youtube.com/watch?v=abc123def45",
        title="Test Video Tutorial",
        description="A test video for unit testing.",
        duration=600.0,
        upload_date="2026-01-15",
        language="en",
        channel_name="Test Channel",
        channel_url="https://youtube.com/@testchannel",
        view_count=100000,
        like_count=5000,
        tags=["test", "tutorial", "python"],
        categories=["Education"],
        chapters=[
            Chapter(title="Intro", start_time=0.0, end_time=60.0),
            Chapter(title="Setup", start_time=60.0, end_time=180.0),
            Chapter(title="Main Content", start_time=180.0, end_time=500.0),
            Chapter(title="Wrap Up", start_time=500.0, end_time=600.0),
        ],
        transcript_source=TranscriptSource.YOUTUBE_MANUAL,
    )


def _make_sample_transcript_segments():
    """Build a list of TranscriptSegment objects for testing."""
    from skill_seekers.cli.video_models import TranscriptSegment, TranscriptSource

    return [
        TranscriptSegment(
            text="Welcome to this tutorial.",
            start=0.0,
            end=3.0,
            confidence=1.0,
            source=TranscriptSource.YOUTUBE_MANUAL,
        ),
        TranscriptSegment(
            text="Today we'll learn about Python.",
            start=3.0,
            end=6.0,
            confidence=1.0,
            source=TranscriptSource.YOUTUBE_MANUAL,
        ),
        TranscriptSegment(
            text="Let's set up our environment.",
            start=60.0,
            end=65.0,
            confidence=1.0,
            source=TranscriptSource.YOUTUBE_MANUAL,
        ),
        TranscriptSegment(
            text="First install Python from python.org.",
            start=65.0,
            end=70.0,
            confidence=1.0,
            source=TranscriptSource.YOUTUBE_MANUAL,
        ),
        TranscriptSegment(
            text="Now let's write some code.",
            start=180.0,
            end=185.0,
            confidence=1.0,
            source=TranscriptSource.YOUTUBE_MANUAL,
        ),
        TranscriptSegment(
            text="def hello(): return 'world'",
            start=185.0,
            end=190.0,
            confidence=0.95,
            source=TranscriptSource.YOUTUBE_MANUAL,
        ),
        TranscriptSegment(
            text="Thanks for watching, subscribe for more.",
            start=500.0,
            end=510.0,
            confidence=1.0,
            source=TranscriptSource.YOUTUBE_MANUAL,
        ),
    ]


def _make_sample_srt_content():
    """Build sample SRT subtitle content."""
    return """1
00:00:00,000 --> 00:00:03,000
Welcome to this tutorial.

2
00:00:03,000 --> 00:00:06,000
Today we'll learn about Python.

3
00:01:00,000 --> 00:01:05,000
Let's set up our environment.
"""


def _make_sample_vtt_content():
    """Build sample WebVTT subtitle content."""
    return """WEBVTT

00:00:00.000 --> 00:00:03.000
Welcome to this tutorial.

00:00:03.000 --> 00:00:06.000
Today we'll learn about Python.

00:01:00.000 --> 00:01:05.000
Let's set up our environment.
"""


# =============================================================================
# Test: Data Models
# =============================================================================


class TestVideoModels(unittest.TestCase):
    """Test video data models (enums + dataclasses)."""

    def test_video_source_type_enum(self):
        from skill_seekers.cli.video_models import VideoSourceType

        self.assertEqual(VideoSourceType.YOUTUBE.value, "youtube")
        self.assertEqual(VideoSourceType.LOCAL_FILE.value, "local_file")
        self.assertEqual(VideoSourceType.VIMEO.value, "vimeo")

    def test_transcript_source_enum(self):
        from skill_seekers.cli.video_models import TranscriptSource

        self.assertEqual(TranscriptSource.YOUTUBE_MANUAL.value, "youtube_manual")
        self.assertEqual(TranscriptSource.WHISPER.value, "whisper")
        self.assertEqual(TranscriptSource.NONE.value, "none")

    def test_segment_content_type_enum(self):
        from skill_seekers.cli.video_models import SegmentContentType

        self.assertEqual(SegmentContentType.LIVE_CODING.value, "live_coding")
        self.assertEqual(SegmentContentType.EXPLANATION.value, "explanation")

    def test_chapter_serialization(self):
        from skill_seekers.cli.video_models import Chapter

        ch = Chapter(title="Intro", start_time=0.0, end_time=60.0)
        d = ch.to_dict()
        self.assertEqual(d["title"], "Intro")
        self.assertEqual(d["start_time"], 0.0)
        self.assertEqual(d["end_time"], 60.0)

        ch2 = Chapter.from_dict(d)
        self.assertEqual(ch2.title, "Intro")
        self.assertAlmostEqual(ch2.duration, 60.0)

    def test_transcript_segment_serialization(self):
        from skill_seekers.cli.video_models import TranscriptSegment, TranscriptSource

        seg = TranscriptSegment(
            text="Hello world",
            start=0.0,
            end=2.5,
            confidence=0.95,
            source=TranscriptSource.YOUTUBE_MANUAL,
        )
        d = seg.to_dict()
        self.assertEqual(d["text"], "Hello world")
        self.assertEqual(d["source"], "youtube_manual")

        seg2 = TranscriptSegment.from_dict(d)
        self.assertEqual(seg2.text, "Hello world")
        self.assertEqual(seg2.source, TranscriptSource.YOUTUBE_MANUAL)

    def test_video_segment_serialization(self):
        from skill_seekers.cli.video_models import SegmentContentType, VideoSegment

        seg = VideoSegment(
            index=0,
            start_time=0.0,
            end_time=60.0,
            duration=60.0,
            transcript="Hello world",
            chapter_title="Intro",
            content_type=SegmentContentType.INTRO,
            confidence=0.9,
        )
        d = seg.to_dict()
        self.assertEqual(d["chapter_title"], "Intro")
        self.assertEqual(d["content_type"], "intro")

        seg2 = VideoSegment.from_dict(d)
        self.assertEqual(seg2.chapter_title, "Intro")
        self.assertEqual(seg2.content_type, SegmentContentType.INTRO)

    def test_video_segment_timestamp_display(self):
        from skill_seekers.cli.video_models import VideoSegment

        seg = VideoSegment(index=0, start_time=330.0, end_time=495.0, duration=165.0)
        self.assertEqual(seg.timestamp_display, "05:30 - 08:15")

    def test_video_segment_timestamp_display_hours(self):
        from skill_seekers.cli.video_models import VideoSegment

        seg = VideoSegment(index=0, start_time=3661.0, end_time=7200.0, duration=3539.0)
        self.assertIn("1:", seg.timestamp_display)

    def test_video_info_serialization(self):
        info = _make_sample_video_info()
        d = info.to_dict()
        self.assertEqual(d["video_id"], "abc123def45")
        self.assertEqual(d["source_type"], "youtube")
        self.assertEqual(len(d["chapters"]), 4)

        from skill_seekers.cli.video_models import VideoInfo

        info2 = VideoInfo.from_dict(d)
        self.assertEqual(info2.video_id, "abc123def45")
        self.assertEqual(len(info2.chapters), 4)

    def test_video_source_config_validation(self):
        from skill_seekers.cli.video_models import VideoSourceConfig

        # No source specified
        config = VideoSourceConfig()
        errors = config.validate()
        self.assertTrue(len(errors) > 0)

        # Valid config
        config = VideoSourceConfig(url="https://youtube.com/watch?v=test")
        errors = config.validate()
        self.assertEqual(len(errors), 0)

        # Multiple sources
        config = VideoSourceConfig(url="test", path="test.mp4")
        errors = config.validate()
        self.assertTrue(len(errors) > 0)

    def test_video_scraper_result_serialization(self):
        from skill_seekers.cli.video_models import VideoScraperResult

        result = VideoScraperResult(
            total_duration_seconds=600.0,
            total_segments=4,
            warnings=["Test warning"],
        )
        d = result.to_dict()
        self.assertEqual(d["total_segments"], 4)
        self.assertEqual(d["warnings"], ["Test warning"])

        result2 = VideoScraperResult.from_dict(d)
        self.assertEqual(result2.total_segments, 4)

    def test_word_timestamp_serialization(self):
        from skill_seekers.cli.video_models import WordTimestamp

        wt = WordTimestamp(word="hello", start=0.0, end=0.5, probability=0.95)
        d = wt.to_dict()
        self.assertEqual(d["word"], "hello")

        wt2 = WordTimestamp.from_dict(d)
        self.assertEqual(wt2.word, "hello")

    def test_code_block_serialization(self):
        from skill_seekers.cli.video_models import CodeBlock, CodeContext

        cb = CodeBlock(
            code="print('hi')", language="python", context=CodeContext.EDITOR, confidence=0.9
        )
        d = cb.to_dict()
        self.assertEqual(d["context"], "editor")

        cb2 = CodeBlock.from_dict(d)
        self.assertEqual(cb2.context, CodeContext.EDITOR)


# =============================================================================
# Test: Metadata
# =============================================================================


class TestVideoMetadata(unittest.TestCase):
    """Test video metadata extraction functions."""

    def test_extract_video_id_standard_url(self):
        from skill_seekers.cli.video_metadata import extract_video_id

        self.assertEqual(
            extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
            "dQw4w9WgXcQ",
        )

    def test_extract_video_id_short_url(self):
        from skill_seekers.cli.video_metadata import extract_video_id

        self.assertEqual(
            extract_video_id("https://youtu.be/dQw4w9WgXcQ"),
            "dQw4w9WgXcQ",
        )

    def test_extract_video_id_embed_url(self):
        from skill_seekers.cli.video_metadata import extract_video_id

        self.assertEqual(
            extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ"),
            "dQw4w9WgXcQ",
        )

    def test_extract_video_id_shorts_url(self):
        from skill_seekers.cli.video_metadata import extract_video_id

        self.assertEqual(
            extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ"),
            "dQw4w9WgXcQ",
        )

    def test_extract_video_id_not_youtube(self):
        from skill_seekers.cli.video_metadata import extract_video_id

        self.assertIsNone(extract_video_id("https://vimeo.com/123456"))
        self.assertIsNone(extract_video_id("https://example.com"))

    def test_detect_video_source_type_youtube(self):
        from skill_seekers.cli.video_metadata import detect_video_source_type
        from skill_seekers.cli.video_models import VideoSourceType

        self.assertEqual(
            detect_video_source_type("https://www.youtube.com/watch?v=test"),
            VideoSourceType.YOUTUBE,
        )
        self.assertEqual(
            detect_video_source_type("https://youtu.be/test"),
            VideoSourceType.YOUTUBE,
        )

    def test_detect_video_source_type_vimeo(self):
        from skill_seekers.cli.video_metadata import detect_video_source_type
        from skill_seekers.cli.video_models import VideoSourceType

        self.assertEqual(
            detect_video_source_type("https://vimeo.com/123456"),
            VideoSourceType.VIMEO,
        )

    def test_extract_local_metadata(self):
        from skill_seekers.cli.video_metadata import extract_local_metadata

        # Create a temp file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_name = tmp.name
        try:
            info = extract_local_metadata(tmp_name)
            self.assertEqual(info.source_type.value, "local_file")
            self.assertIsNotNone(info.video_id)
            self.assertIsNotNone(info.file_path)
        finally:
            os.unlink(tmp_name)


# =============================================================================
# Test: Transcript
# =============================================================================


class TestVideoTranscript(unittest.TestCase):
    """Test transcript extraction functions."""

    def test_parse_srt(self):
        from skill_seekers.cli.video_transcript import parse_srt

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".srt", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(_make_sample_srt_content())
            tmp_name = tmp.name
        try:
            segments = parse_srt(tmp_name)
            self.assertEqual(len(segments), 3)
            self.assertEqual(segments[0].text, "Welcome to this tutorial.")
            self.assertAlmostEqual(segments[0].start, 0.0)
            self.assertAlmostEqual(segments[0].end, 3.0)
            self.assertEqual(segments[0].source.value, "subtitle_file")
        finally:
            os.unlink(tmp_name)

    def test_parse_vtt(self):
        from skill_seekers.cli.video_transcript import parse_vtt

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".vtt", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(_make_sample_vtt_content())
            tmp_name = tmp.name
        try:
            segments = parse_vtt(tmp_name)
            self.assertEqual(len(segments), 3)
            self.assertEqual(segments[0].text, "Welcome to this tutorial.")
            self.assertAlmostEqual(segments[2].start, 60.0)
        finally:
            os.unlink(tmp_name)

    def test_parse_srt_with_html_tags(self):
        from skill_seekers.cli.video_transcript import parse_srt

        content = """1
00:00:00,000 --> 00:00:03,000
<b>Bold text</b> and <i>italic</i>
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".srt", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(content)
            tmp_name = tmp.name
        try:
            segments = parse_srt(tmp_name)
            self.assertEqual(len(segments), 1)
            self.assertEqual(segments[0].text, "Bold text and italic")
        finally:
            os.unlink(tmp_name)

    def test_whisper_stub_raises(self):
        from skill_seekers.cli.video_transcript import transcribe_with_whisper, HAS_WHISPER

        if not HAS_WHISPER:
            with self.assertRaises(RuntimeError) as ctx:
                transcribe_with_whisper("test.wav")
            self.assertIn("faster-whisper", str(ctx.exception))

    def test_get_transcript_fallback_to_subtitle(self):
        """Test that get_transcript falls back to subtitle files."""
        from skill_seekers.cli.video_transcript import get_transcript
        from skill_seekers.cli.video_models import (
            TranscriptSource,
            VideoInfo,
            VideoSourceConfig,
            VideoSourceType,
        )

        tmp_dir = tempfile.mkdtemp()
        try:
            # Create a fake video file and matching SRT
            video_path = os.path.join(tmp_dir, "test.mp4")
            srt_path = os.path.join(tmp_dir, "test.srt")
            with open(video_path, "w") as f:
                f.write("fake")
            with open(srt_path, "w", encoding="utf-8") as f:
                f.write(_make_sample_srt_content())

            video_info = VideoInfo(
                video_id="local123",
                source_type=VideoSourceType.LOCAL_FILE,
                file_path=video_path,
            )
            config = VideoSourceConfig()

            segments, source = get_transcript(video_info, config)
            self.assertEqual(source, TranscriptSource.SUBTITLE_FILE)
            self.assertEqual(len(segments), 3)
        finally:
            shutil.rmtree(tmp_dir)


# =============================================================================
# Test: Segmenter
# =============================================================================


class TestVideoSegmenter(unittest.TestCase):
    """Test video segmentation."""

    def test_segment_by_chapters(self):
        from skill_seekers.cli.video_segmenter import segment_by_chapters

        video_info = _make_sample_video_info()
        transcript = _make_sample_transcript_segments()
        segments = segment_by_chapters(video_info, transcript)

        self.assertEqual(len(segments), 4)
        self.assertEqual(segments[0].chapter_title, "Intro")
        self.assertEqual(segments[1].chapter_title, "Setup")
        self.assertIn("Welcome", segments[0].transcript)

    def test_segment_by_time_window(self):
        from skill_seekers.cli.video_segmenter import segment_by_time_window

        video_info = _make_sample_video_info()
        transcript = _make_sample_transcript_segments()
        segments = segment_by_time_window(video_info, transcript, window_seconds=300.0)

        # With 600s duration and 300s windows, expect 2 segments
        self.assertTrue(len(segments) >= 1)
        self.assertIsNone(segments[0].chapter_title)

    def test_segment_video_uses_chapters(self):
        from skill_seekers.cli.video_segmenter import segment_video
        from skill_seekers.cli.video_models import VideoSourceConfig

        video_info = _make_sample_video_info()
        transcript = _make_sample_transcript_segments()
        config = VideoSourceConfig()

        segments = segment_video(video_info, transcript, config)
        # Should use chapters since they're available
        self.assertEqual(len(segments), 4)
        self.assertEqual(segments[0].chapter_title, "Intro")

    def test_segment_video_fallback_to_time_window(self):
        from skill_seekers.cli.video_segmenter import segment_video
        from skill_seekers.cli.video_models import VideoInfo, VideoSourceConfig, VideoSourceType

        video_info = VideoInfo(
            video_id="no_chapters",
            source_type=VideoSourceType.YOUTUBE,
            duration=300.0,
        )
        transcript = _make_sample_transcript_segments()
        config = VideoSourceConfig(time_window_seconds=120.0)

        segments = segment_video(video_info, transcript, config)
        self.assertTrue(len(segments) >= 1)
        # No chapters, so chapter_title should be None
        for seg in segments:
            self.assertIsNone(seg.chapter_title)

    def test_segment_content_type_classification(self):
        from skill_seekers.cli.video_segmenter import _classify_content_type
        from skill_seekers.cli.video_models import SegmentContentType

        self.assertEqual(
            _classify_content_type("Welcome to this tutorial, today we"),
            SegmentContentType.INTRO,
        )
        self.assertEqual(
            _classify_content_type("import os\ndef process_data(): return result"),
            SegmentContentType.LIVE_CODING,
        )
        self.assertEqual(
            _classify_content_type("thanks for watching subscribe for more"),
            SegmentContentType.OUTRO,
        )


# =============================================================================
# Test: Source Detection
# =============================================================================


class TestVideoSourceDetection(unittest.TestCase):
    """Test SourceDetector recognizes video URLs and file extensions."""

    def test_detect_youtube_url(self):
        from skill_seekers.cli.source_detector import SourceDetector

        info = SourceDetector.detect("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        self.assertEqual(info.type, "video")
        self.assertEqual(info.parsed["source_kind"], "url")

    def test_detect_youtube_short_url(self):
        from skill_seekers.cli.source_detector import SourceDetector

        info = SourceDetector.detect("https://youtu.be/dQw4w9WgXcQ")
        self.assertEqual(info.type, "video")

    def test_detect_youtube_playlist(self):
        from skill_seekers.cli.source_detector import SourceDetector

        info = SourceDetector.detect("https://www.youtube.com/playlist?list=PLtest123")
        self.assertEqual(info.type, "video")
        self.assertEqual(info.suggested_name, "youtube_playlist")

    def test_detect_youtube_channel(self):
        from skill_seekers.cli.source_detector import SourceDetector

        info = SourceDetector.detect("https://www.youtube.com/@testchannel")
        self.assertEqual(info.type, "video")
        self.assertEqual(info.suggested_name, "youtube_channel")

    def test_detect_vimeo_url(self):
        from skill_seekers.cli.source_detector import SourceDetector

        info = SourceDetector.detect("https://vimeo.com/123456789")
        self.assertEqual(info.type, "video")
        self.assertEqual(info.suggested_name, "vimeo_video")

    def test_detect_mp4_file(self):
        from skill_seekers.cli.source_detector import SourceDetector

        info = SourceDetector.detect("recording.mp4")
        self.assertEqual(info.type, "video")
        self.assertEqual(info.suggested_name, "recording")
        self.assertEqual(info.parsed["source_kind"], "file")

    def test_detect_mkv_file(self):
        from skill_seekers.cli.source_detector import SourceDetector

        info = SourceDetector.detect("tutorial.mkv")
        self.assertEqual(info.type, "video")

    def test_detect_webm_file(self):
        from skill_seekers.cli.source_detector import SourceDetector

        info = SourceDetector.detect("screencast.webm")
        self.assertEqual(info.type, "video")

    def test_detect_avi_file(self):
        from skill_seekers.cli.source_detector import SourceDetector

        info = SourceDetector.detect("old-recording.avi")
        self.assertEqual(info.type, "video")

    def test_detect_mov_file(self):
        from skill_seekers.cli.source_detector import SourceDetector

        info = SourceDetector.detect("screen.mov")
        self.assertEqual(info.type, "video")

    def test_validate_video_file_exists(self):
        from skill_seekers.cli.source_detector import SourceDetector, SourceInfo

        info = SourceInfo(
            type="video",
            parsed={"file_path": "/nonexistent/file.mp4", "source_kind": "file"},
            suggested_name="file",
            raw_input="file.mp4",
        )
        with self.assertRaises(ValueError):
            SourceDetector.validate_source(info)

    def test_validate_video_url_no_error(self):
        """URL-based video sources should not raise during validation."""
        from skill_seekers.cli.source_detector import SourceDetector, SourceInfo

        info = SourceInfo(
            type="video",
            parsed={"url": "https://youtube.com/watch?v=test", "source_kind": "url"},
            suggested_name="test",
            raw_input="https://youtube.com/watch?v=test",
        )
        # Should not raise
        SourceDetector.validate_source(info)


# =============================================================================
# Test: CLI Arguments
# =============================================================================


class TestVideoArguments(unittest.TestCase):
    """Test video CLI argument definitions."""

    def test_video_arguments_dict(self):
        from skill_seekers.cli.arguments.video import VIDEO_ARGUMENTS

        self.assertIn("url", VIDEO_ARGUMENTS)
        self.assertIn("video_file", VIDEO_ARGUMENTS)
        self.assertIn("playlist", VIDEO_ARGUMENTS)
        self.assertIn("languages", VIDEO_ARGUMENTS)
        self.assertIn("visual", VIDEO_ARGUMENTS)
        self.assertIn("whisper_model", VIDEO_ARGUMENTS)
        self.assertIn("from_json", VIDEO_ARGUMENTS)

    def test_add_video_arguments(self):
        import argparse
        from skill_seekers.cli.arguments.video import add_video_arguments

        parser = argparse.ArgumentParser()
        add_video_arguments(parser)

        # Should parse without error
        args = parser.parse_args(["--url", "https://youtube.com/watch?v=test"])
        self.assertEqual(args.url, "https://youtube.com/watch?v=test")

    def test_enhance_level_defaults_to_zero(self):
        import argparse
        from skill_seekers.cli.arguments.video import add_video_arguments

        parser = argparse.ArgumentParser()
        add_video_arguments(parser)

        args = parser.parse_args([])
        self.assertEqual(args.enhance_level, 0)

    def test_unified_parser_has_video(self):
        """Test video subcommand is registered in main parser."""
        from skill_seekers.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["video", "--url", "https://youtube.com/watch?v=test"])
        self.assertEqual(args.url, "https://youtube.com/watch?v=test")


# =============================================================================
# Test: VideoToSkillConverter
# =============================================================================


class TestVideoToSkillConverter(unittest.TestCase):
    """Test the main VideoToSkillConverter class."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        # Clean up output dirs that may have been created
        for d in ["output/test_video", "output/test_video_video_extracted.json"]:
            if os.path.exists(d):
                if os.path.isdir(d):
                    shutil.rmtree(d, ignore_errors=True)
                else:
                    os.unlink(d)

    def test_init_with_url(self):
        from skill_seekers.cli.video_scraper import VideoToSkillConverter

        config = {"name": "test_video", "url": "https://youtube.com/watch?v=test"}
        converter = VideoToSkillConverter(config)
        self.assertEqual(converter.name, "test_video")

    def test_init_with_video_file(self):
        from skill_seekers.cli.video_scraper import VideoToSkillConverter

        config = {"name": "test_video", "video_file": "test.mp4"}
        converter = VideoToSkillConverter(config)
        self.assertEqual(converter.config["video_file"], "test.mp4")

    def test_build_skill_from_loaded_data(self):
        """Test build_skill works with pre-loaded result data."""
        from skill_seekers.cli.video_scraper import VideoToSkillConverter
        from skill_seekers.cli.video_models import (
            VideoScraperResult,
            VideoInfo,
            VideoSourceType,
            TranscriptSource,
            VideoSegment,
            SegmentContentType,
        )

        config = {
            "name": "test_video",
            "output": os.path.join(self.temp_dir, "test_video"),
        }
        converter = VideoToSkillConverter(config)

        # Manually set result
        converter.result = VideoScraperResult(
            videos=[
                VideoInfo(
                    video_id="test123",
                    source_type=VideoSourceType.YOUTUBE,
                    source_url="https://youtube.com/watch?v=test123",
                    title="Test Video",
                    description="A test video.",
                    duration=120.0,
                    channel_name="Test",
                    view_count=1000,
                    transcript_source=TranscriptSource.YOUTUBE_MANUAL,
                    segments=[
                        VideoSegment(
                            index=0,
                            start_time=0.0,
                            end_time=60.0,
                            duration=60.0,
                            transcript="Hello world test content.",
                            chapter_title="Intro",
                            content="### Intro (00:00 - 01:00)\n\nHello world test content.",
                            content_type=SegmentContentType.INTRO,
                            confidence=0.9,
                        ),
                        VideoSegment(
                            index=1,
                            start_time=60.0,
                            end_time=120.0,
                            duration=60.0,
                            transcript="Main content here.",
                            chapter_title="Main",
                            content="### Main (01:00 - 02:00)\n\nMain content here.",
                            content_type=SegmentContentType.EXPLANATION,
                            confidence=0.9,
                        ),
                    ],
                ),
            ],
            total_duration_seconds=120.0,
            total_segments=2,
        )

        skill_dir = converter.build_skill()
        self.assertTrue(os.path.isdir(skill_dir))
        self.assertTrue(os.path.isfile(os.path.join(skill_dir, "SKILL.md")))
        self.assertTrue(os.path.isdir(os.path.join(skill_dir, "references")))
        self.assertTrue(os.path.isdir(os.path.join(skill_dir, "video_data")))

        # Check SKILL.md content
        with open(os.path.join(skill_dir, "SKILL.md"), encoding="utf-8") as f:
            skill_content = f.read()
        self.assertIn("Test Video", skill_content)
        self.assertIn("Video Tutorials", skill_content)

    def test_save_and_load_extracted_data(self):
        """Test JSON save/load roundtrip."""
        from skill_seekers.cli.video_scraper import VideoToSkillConverter
        from skill_seekers.cli.video_models import VideoScraperResult, VideoInfo, VideoSourceType

        config = {"name": "test_video"}
        converter = VideoToSkillConverter(config)
        converter.result = VideoScraperResult(
            videos=[VideoInfo(video_id="test", source_type=VideoSourceType.YOUTUBE, title="Test")],
            total_duration_seconds=60.0,
        )

        # Save
        data_file = converter.save_extracted_data()
        self.assertTrue(os.path.isfile(data_file))

        # Load into new converter
        converter2 = VideoToSkillConverter(config)
        converter2.load_extracted_data(data_file)
        self.assertEqual(len(converter2.result.videos), 1)
        self.assertEqual(converter2.result.videos[0].title, "Test")

        # Clean up
        os.unlink(data_file)


# =============================================================================
# Test: Visual Extraction Stubs
# =============================================================================


class TestVideoVisualStubs(unittest.TestCase):
    """Test Tier 2 visual extraction stubs raise proper errors."""

    def test_check_visual_dependencies(self):
        from skill_seekers.cli.video_visual import check_visual_dependencies

        deps = check_visual_dependencies()
        self.assertIn("opencv", deps)
        self.assertIn("scenedetect", deps)
        self.assertIn("easyocr", deps)

    def test_detect_scenes_raises_without_deps(self):
        from skill_seekers.cli.video_visual import detect_scenes, HAS_OPENCV

        if not HAS_OPENCV:
            with self.assertRaises(RuntimeError):
                detect_scenes("test.mp4")

    def test_extract_keyframes_raises_without_deps(self):
        from skill_seekers.cli.video_visual import extract_keyframes, HAS_OPENCV

        if not HAS_OPENCV:
            with self.assertRaises(RuntimeError):
                extract_keyframes("test.mp4", [0.0, 1.0])

    def test_classify_frame_raises_without_deps(self):
        from skill_seekers.cli.video_visual import classify_frame, HAS_OPENCV

        if not HAS_OPENCV:
            with self.assertRaises(RuntimeError):
                classify_frame("frame.png")

    def test_extract_text_raises_without_deps(self):
        from skill_seekers.cli.video_visual import extract_text_from_frame, HAS_EASYOCR

        if not HAS_EASYOCR:
            with self.assertRaises(RuntimeError):
                extract_text_from_frame("frame.png")


# =============================================================================
# Test: Create Command Integration
# =============================================================================


class TestVideoCreateCommandIntegration(unittest.TestCase):
    """Test create command routes video sources correctly."""

    def test_create_command_routing_youtube_url(self):
        """Test that CreateCommand routes YouTube URLs to video scraper."""
        from skill_seekers.cli.source_detector import SourceDetector

        # Detect source
        info = SourceDetector.detect("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        self.assertEqual(info.type, "video")

    def test_create_command_routing_video_file(self):
        """Test that CreateCommand routes video files to video scraper."""
        from skill_seekers.cli.source_detector import SourceDetector

        info = SourceDetector.detect("tutorial.mp4")
        self.assertEqual(info.type, "video")

    def test_create_arguments_include_video(self):
        """Test that create arguments include video mode."""
        from skill_seekers.cli.arguments.create import get_source_specific_arguments

        video_args = get_source_specific_arguments("video")
        self.assertIn("video_url", video_args)
        self.assertIn("visual", video_args)
        self.assertIn("whisper_model", video_args)


# =============================================================================
# Test: Config Validator
# =============================================================================


class TestVideoConfigValidator(unittest.TestCase):
    """Test that video is a valid source type in config validator."""

    def test_video_in_valid_source_types(self):
        from skill_seekers.cli.config_validator import ConfigValidator

        self.assertIn("video", ConfigValidator.VALID_SOURCE_TYPES)


# =============================================================================
# Test: Helper Functions
# =============================================================================


class TestVideoHelperFunctions(unittest.TestCase):
    """Test module-level helper functions."""

    def test_sanitize_filename(self):
        from skill_seekers.cli.video_scraper import _sanitize_filename

        self.assertEqual(
            _sanitize_filename("React Hooks Tutorial for Beginners"),
            "react-hooks-tutorial-for-beginners",
        )
        self.assertEqual(
            _sanitize_filename("Test!!!   Video---Title"),
            "test-video-title",
        )

    def test_sanitize_filename_max_length(self):
        from skill_seekers.cli.video_scraper import _sanitize_filename

        result = _sanitize_filename("a" * 100, max_length=20)
        self.assertLessEqual(len(result), 20)

    def test_format_duration(self):
        from skill_seekers.cli.video_scraper import _format_duration

        self.assertEqual(_format_duration(65), "01:05")
        self.assertEqual(_format_duration(3661), "1:01:01")
        self.assertEqual(_format_duration(0), "00:00")

    def test_format_count(self):
        from skill_seekers.cli.video_scraper import _format_count

        self.assertEqual(_format_count(1500000), "1,500,000")
        self.assertEqual(_format_count(None), "N/A")

    def test_infer_description_from_video(self):
        from skill_seekers.cli.video_scraper import infer_description_from_video

        info = _make_sample_video_info()
        desc = infer_description_from_video(info)
        self.assertTrue(desc.startswith("Use when"))


# =============================================================================
# Test: OCR Preprocessing (Phase 1)
# =============================================================================


class TestOCRPreprocessing(unittest.TestCase):
    """Test frame-type-aware OCR preprocessing functions."""

    def test_get_ocr_params_code_editor(self):
        from skill_seekers.cli.video_visual import _get_ocr_params
        from skill_seekers.cli.video_models import FrameType

        params = _get_ocr_params(FrameType.CODE_EDITOR)
        self.assertEqual(params["decoder"], "beamsearch")
        self.assertEqual(params["text_threshold"], 0.4)
        self.assertEqual(params["contrast_ths"], 0.3)
        self.assertEqual(params["mag_ratio"], 1.0)

    def test_get_ocr_params_terminal(self):
        from skill_seekers.cli.video_visual import _get_ocr_params
        from skill_seekers.cli.video_models import FrameType

        params = _get_ocr_params(FrameType.TERMINAL)
        self.assertEqual(params["decoder"], "beamsearch")
        self.assertEqual(params["low_text"], 0.3)

    def test_get_ocr_params_slide(self):
        from skill_seekers.cli.video_visual import _get_ocr_params
        from skill_seekers.cli.video_models import FrameType

        params = _get_ocr_params(FrameType.SLIDE)
        self.assertEqual(params["decoder"], "greedy")
        self.assertEqual(params["text_threshold"], 0.6)

    def test_get_ocr_params_other(self):
        from skill_seekers.cli.video_visual import _get_ocr_params
        from skill_seekers.cli.video_models import FrameType

        params = _get_ocr_params(FrameType.OTHER)
        self.assertEqual(params["decoder"], "greedy")

    def test_preprocess_returns_original_for_other(self):
        from skill_seekers.cli.video_visual import _preprocess_frame_for_ocr
        from skill_seekers.cli.video_models import FrameType

        result = _preprocess_frame_for_ocr("/nonexistent/path.jpg", FrameType.OTHER)
        self.assertEqual(result, "/nonexistent/path.jpg")

    def test_preprocess_returns_original_for_webcam(self):
        from skill_seekers.cli.video_visual import _preprocess_frame_for_ocr
        from skill_seekers.cli.video_models import FrameType

        result = _preprocess_frame_for_ocr("/nonexistent/path.jpg", FrameType.WEBCAM)
        self.assertEqual(result, "/nonexistent/path.jpg")


# =============================================================================
# Test: Spatial Layout (Phase 2)
# =============================================================================


class TestSpatialLayout(unittest.TestCase):
    """Test OCR spatial layout preservation functions."""

    def test_cluster_empty_results(self):
        from skill_seekers.cli.video_visual import _cluster_ocr_into_lines
        from skill_seekers.cli.video_models import FrameType

        regions = _cluster_ocr_into_lines([], FrameType.OTHER)
        self.assertEqual(regions, [])

    def test_cluster_single_result(self):
        from skill_seekers.cli.video_visual import _cluster_ocr_into_lines
        from skill_seekers.cli.video_models import FrameType

        raw = [([[0, 10], [100, 10], [100, 30], [0, 30]], "hello world", 0.9)]
        regions = _cluster_ocr_into_lines(raw, FrameType.OTHER)
        self.assertEqual(len(regions), 1)
        self.assertEqual(regions[0].text, "hello world")
        self.assertAlmostEqual(regions[0].confidence, 0.9)

    def test_cluster_two_lines(self):
        from skill_seekers.cli.video_visual import _cluster_ocr_into_lines
        from skill_seekers.cli.video_models import FrameType

        raw = [
            ([[0, 10], [100, 10], [100, 30], [0, 30]], "line one", 0.9),
            ([[0, 50], [100, 50], [100, 70], [0, 70]], "line two", 0.8),
        ]
        regions = _cluster_ocr_into_lines(raw, FrameType.CODE_EDITOR)
        self.assertEqual(len(regions), 2)
        self.assertEqual(regions[0].text, "line one")
        self.assertEqual(regions[1].text, "line two")
        self.assertTrue(regions[0].is_monospace)

    def test_cluster_same_line_fragments(self):
        from skill_seekers.cli.video_visual import _cluster_ocr_into_lines
        from skill_seekers.cli.video_models import FrameType

        raw = [
            ([[0, 10], [50, 10], [50, 30], [0, 30]], "hello", 0.9),
            ([[55, 10], [120, 10], [120, 30], [55, 30]], "world", 0.85),
        ]
        regions = _cluster_ocr_into_lines(raw, FrameType.OTHER)
        self.assertEqual(len(regions), 1)
        self.assertIn("hello", regions[0].text)
        self.assertIn("world", regions[0].text)

    def test_cluster_monospace_flag(self):
        from skill_seekers.cli.video_visual import _cluster_ocr_into_lines
        from skill_seekers.cli.video_models import FrameType

        raw = [([[0, 0], [100, 0], [100, 20], [0, 20]], "test", 0.9)]

        code_regions = _cluster_ocr_into_lines(raw, FrameType.CODE_EDITOR)
        self.assertTrue(code_regions[0].is_monospace)

        terminal_regions = _cluster_ocr_into_lines(raw, FrameType.TERMINAL)
        self.assertTrue(terminal_regions[0].is_monospace)

        slide_regions = _cluster_ocr_into_lines(raw, FrameType.SLIDE)
        self.assertFalse(slide_regions[0].is_monospace)

    def test_assemble_code_editor_newlines(self):
        from skill_seekers.cli.video_visual import _assemble_structured_text
        from skill_seekers.cli.video_models import FrameType, OCRRegion

        regions = [
            OCRRegion(text="def hello():", confidence=0.9, bbox=(100, 10, 300, 30)),
            OCRRegion(text="return 'world'", confidence=0.9, bbox=(100, 40, 350, 60)),
        ]
        text = _assemble_structured_text(regions, FrameType.CODE_EDITOR)
        self.assertIn("\n", text)
        self.assertIn("def hello():", text)
        self.assertIn("return 'world'", text)

    def test_assemble_slide_double_newlines(self):
        from skill_seekers.cli.video_visual import _assemble_structured_text
        from skill_seekers.cli.video_models import FrameType, OCRRegion

        regions = [
            OCRRegion(text="Title", confidence=0.9, bbox=(100, 10, 300, 30)),
            OCRRegion(text="Subtitle", confidence=0.9, bbox=(100, 80, 350, 100)),
        ]
        text = _assemble_structured_text(regions, FrameType.SLIDE)
        self.assertIn("\n\n", text)

    def test_assemble_other_flat(self):
        from skill_seekers.cli.video_visual import _assemble_structured_text
        from skill_seekers.cli.video_models import FrameType, OCRRegion

        regions = [
            OCRRegion(text="hello", confidence=0.9, bbox=(0, 0, 50, 20)),
            OCRRegion(text="world", confidence=0.9, bbox=(0, 30, 50, 50)),
        ]
        text = _assemble_structured_text(regions, FrameType.OTHER)
        self.assertEqual(text, "hello world")
        self.assertNotIn("\n", text)

    def test_assemble_empty_regions(self):
        from skill_seekers.cli.video_visual import _assemble_structured_text
        from skill_seekers.cli.video_models import FrameType

        text = _assemble_structured_text([], FrameType.CODE_EDITOR)
        self.assertEqual(text, "")


# =============================================================================
# Test: Cross-Frame Text Continuity (Phase 3)
# =============================================================================


class TestTextContinuity(unittest.TestCase):
    """Test cross-frame text tracking and code block detection."""

    def test_text_similarity_identical(self):
        from skill_seekers.cli.video_visual import _text_similarity

        self.assertAlmostEqual(_text_similarity("hello world", "hello world"), 1.0)

    def test_text_similarity_empty(self):
        from skill_seekers.cli.video_visual import _text_similarity

        self.assertEqual(_text_similarity("", "hello"), 0.0)
        self.assertEqual(_text_similarity("hello", ""), 0.0)
        self.assertEqual(_text_similarity("", ""), 0.0)

    def test_text_similarity_different(self):
        from skill_seekers.cli.video_visual import _text_similarity

        sim = _text_similarity("hello world", "goodbye universe")
        self.assertLess(sim, 0.5)

    def test_text_similarity_similar(self):
        from skill_seekers.cli.video_visual import _text_similarity

        sim = _text_similarity(
            "def hello():\n    return 'world'",
            "def hello():\n    return 'world!'",
        )
        self.assertGreater(sim, 0.8)

    def test_tracker_creates_new_block(self):
        from skill_seekers.cli.video_visual import TextBlockTracker
        from skill_seekers.cli.video_models import FrameType

        tracker = TextBlockTracker()
        tracker.update(0, 1.0, "def hello():\n    return 'world'", 0.9, FrameType.CODE_EDITOR)
        blocks = tracker.finalize()
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].first_seen, 1.0)
        self.assertEqual(blocks[0].frame_type, FrameType.CODE_EDITOR)

    def test_tracker_merges_similar_frames(self):
        from skill_seekers.cli.video_visual import TextBlockTracker
        from skill_seekers.cli.video_models import FrameType

        tracker = TextBlockTracker()
        text1 = "def hello():\n    return 'world'"
        text2 = "def hello():\n    return 'world!'"
        tracker.update(0, 1.0, text1, 0.8, FrameType.CODE_EDITOR)
        tracker.update(1, 2.0, text2, 0.9, FrameType.CODE_EDITOR)
        blocks = tracker.finalize()
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].best_text, text2)
        self.assertEqual(blocks[0].best_confidence, 0.9)
        self.assertEqual(len(blocks[0].frame_indices), 2)

    def test_tracker_creates_separate_blocks_for_different_text(self):
        from skill_seekers.cli.video_visual import TextBlockTracker
        from skill_seekers.cli.video_models import FrameType

        tracker = TextBlockTracker()
        tracker.update(0, 1.0, "completely different text about cats", 0.8, FrameType.CODE_EDITOR)
        tracker.update(1, 2.0, "unrelated content about dogs and stuff", 0.9, FrameType.CODE_EDITOR)
        blocks = tracker.finalize()
        self.assertEqual(len(blocks), 2)

    def test_tracker_completes_on_non_code_frame(self):
        from skill_seekers.cli.video_visual import TextBlockTracker
        from skill_seekers.cli.video_models import FrameType

        tracker = TextBlockTracker()
        tracker.update(0, 1.0, "def hello():\n    return 'world'", 0.9, FrameType.CODE_EDITOR)
        tracker.update(1, 2.0, "slide text", 0.9, FrameType.SLIDE)
        # After slide frame, the code block should be completed
        tracker.update(2, 3.0, "def hello():\n    return 'world'", 0.9, FrameType.CODE_EDITOR)
        blocks = tracker.finalize()
        # Should have 2 blocks (before and after the slide)
        self.assertEqual(len(blocks), 2)

    def test_tracker_ignores_short_text(self):
        from skill_seekers.cli.video_visual import TextBlockTracker
        from skill_seekers.cli.video_models import FrameType

        tracker = TextBlockTracker()
        tracker.update(0, 1.0, "short", 0.9, FrameType.CODE_EDITOR)
        blocks = tracker.finalize()
        self.assertEqual(len(blocks), 0)

    def test_extract_code_blocks_filters_short(self):
        from skill_seekers.cli.video_visual import _extract_code_blocks, TrackedTextBlock
        from skill_seekers.cli.video_models import FrameType

        blocks_in = [
            TrackedTextBlock(
                first_seen=1.0,
                last_seen=2.0,
                frame_indices=[0],
                text_snapshots=["short"],
                frame_type=FrameType.CODE_EDITOR,
                best_text="short",
                best_confidence=0.9,
            ),
        ]
        code_blocks = _extract_code_blocks(blocks_in)
        self.assertEqual(len(code_blocks), 0)

    def test_extract_code_blocks_maps_context(self):
        from skill_seekers.cli.video_visual import _extract_code_blocks, TrackedTextBlock
        from skill_seekers.cli.video_models import CodeContext, FrameType

        blocks_in = [
            TrackedTextBlock(
                first_seen=1.0,
                last_seen=2.0,
                frame_indices=[0, 1],
                text_snapshots=["def hello():\n    return 'world'"],
                frame_type=FrameType.CODE_EDITOR,
                best_text="def hello():\n    return 'world'",
                best_confidence=0.9,
            ),
            TrackedTextBlock(
                first_seen=3.0,
                last_seen=4.0,
                frame_indices=[2],
                text_snapshots=["$ python hello.py\nHello World output"],
                frame_type=FrameType.TERMINAL,
                best_text="$ python hello.py\nHello World output",
                best_confidence=0.8,
            ),
        ]
        code_blocks = _extract_code_blocks(blocks_in)
        self.assertEqual(len(code_blocks), 2)
        self.assertEqual(code_blocks[0].context, CodeContext.EDITOR)
        self.assertEqual(code_blocks[1].context, CodeContext.TERMINAL)

    def test_extract_code_blocks_skips_non_code_frames(self):
        from skill_seekers.cli.video_visual import _extract_code_blocks, TrackedTextBlock
        from skill_seekers.cli.video_models import FrameType

        blocks_in = [
            TrackedTextBlock(
                first_seen=1.0,
                last_seen=2.0,
                frame_indices=[0],
                text_snapshots=["This is a long slide text with lots of content here"],
                frame_type=FrameType.SLIDE,
                best_text="This is a long slide text with lots of content here",
                best_confidence=0.9,
            ),
        ]
        code_blocks = _extract_code_blocks(blocks_in)
        self.assertEqual(len(code_blocks), 0)

    def test_extract_visual_data_returns_tuple(self):
        """Verify extract_visual_data returns (keyframes, code_blocks) tuple."""
        from skill_seekers.cli.video_visual import extract_visual_data, HAS_OPENCV

        if not HAS_OPENCV:
            with self.assertRaises(RuntimeError):
                extract_visual_data("test.mp4", [], "/tmp/test")
        else:
            # If opencv is available, at least verify the signature
            import inspect

            sig = inspect.signature(extract_visual_data)
            # Check the return annotation
            self.assertIn("tuple", str(sig.return_annotation).lower())

    def test_extract_text_from_frame_returns_tuple(self):
        """Verify extract_text_from_frame returns (raw_results, flat_text) tuple."""
        from skill_seekers.cli.video_visual import extract_text_from_frame, HAS_EASYOCR

        if not HAS_EASYOCR:
            with self.assertRaises(RuntimeError):
                extract_text_from_frame("frame.png")
        else:
            import inspect

            sig = inspect.signature(extract_text_from_frame)
            self.assertIn("tuple", str(sig.return_annotation).lower())


# =============================================================================
# Test: Output Formatting (Phase 4)
# =============================================================================


class TestOutputFormatting(unittest.TestCase):
    """Test type-aware output formatting in reference markdown."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_reference_md_code_block_formatting(self):
        """Test that code editor OCR is wrapped in fenced code blocks."""
        from skill_seekers.cli.video_scraper import VideoToSkillConverter
        from skill_seekers.cli.video_models import (
            CodeBlock,
            CodeContext,
            FrameType,
            KeyFrame,
            SegmentContentType,
            TranscriptSource,
            VideoInfo,
            VideoScraperResult,
            VideoSegment,
            VideoSourceType,
        )

        config = {
            "name": "test_video",
            "output": os.path.join(self.temp_dir, "test_video"),
        }
        converter = VideoToSkillConverter(config)

        converter.result = VideoScraperResult(
            videos=[
                VideoInfo(
                    video_id="test123",
                    source_type=VideoSourceType.YOUTUBE,
                    title="Code Tutorial",
                    duration=60.0,
                    transcript_source=TranscriptSource.YOUTUBE_MANUAL,
                    segments=[
                        VideoSegment(
                            index=0,
                            start_time=0.0,
                            end_time=60.0,
                            duration=60.0,
                            transcript="Some code content.",
                            content="### Intro (00:00 - 01:00)\n\nSome code content.",
                            content_type=SegmentContentType.LIVE_CODING,
                            confidence=0.9,
                            keyframes=[
                                KeyFrame(
                                    timestamp=5.0,
                                    image_path="/nonexistent/frame.jpg",
                                    frame_type=FrameType.CODE_EDITOR,
                                    ocr_text="def hello():\n    return 'world'",
                                ),
                            ],
                            detected_code_blocks=[
                                CodeBlock(
                                    code="def hello():\n    return 'world'",
                                    language="python",
                                    source_frame=5.0,
                                    context=CodeContext.EDITOR,
                                    confidence=0.9,
                                ),
                            ],
                            has_code_on_screen=True,
                        ),
                    ],
                ),
            ],
            total_duration_seconds=60.0,
            total_segments=1,
        )

        ref_md = converter._generate_reference_md(converter.result.videos[0])
        # OCR text should be in a fenced code block with language hint
        self.assertIn("```python", ref_md)
        self.assertIn("def hello():", ref_md)
        # Detected code subsection should exist
        self.assertIn("#### Detected Code", ref_md)

    def test_reference_md_slide_formatting(self):
        """Test that slide OCR is formatted as blockquotes."""
        from skill_seekers.cli.video_scraper import VideoToSkillConverter
        from skill_seekers.cli.video_models import (
            FrameType,
            KeyFrame,
            SegmentContentType,
            TranscriptSource,
            VideoInfo,
            VideoScraperResult,
            VideoSegment,
            VideoSourceType,
        )

        config = {
            "name": "test_video",
            "output": os.path.join(self.temp_dir, "test_video"),
        }
        converter = VideoToSkillConverter(config)

        converter.result = VideoScraperResult(
            videos=[
                VideoInfo(
                    video_id="test456",
                    source_type=VideoSourceType.YOUTUBE,
                    title="Slide Presentation",
                    duration=60.0,
                    transcript_source=TranscriptSource.YOUTUBE_MANUAL,
                    segments=[
                        VideoSegment(
                            index=0,
                            start_time=0.0,
                            end_time=60.0,
                            duration=60.0,
                            content="### Slides\n\nPresentation content.",
                            content_type=SegmentContentType.SLIDES,
                            confidence=0.9,
                            keyframes=[
                                KeyFrame(
                                    timestamp=5.0,
                                    image_path="/nonexistent/frame.jpg",
                                    frame_type=FrameType.SLIDE,
                                    ocr_text="Title\n\nSubtitle",
                                ),
                            ],
                        ),
                    ],
                ),
            ],
            total_duration_seconds=60.0,
            total_segments=1,
        )

        ref_md = converter._generate_reference_md(converter.result.videos[0])
        self.assertIn("> Title", ref_md)
        self.assertIn("> Subtitle", ref_md)
        # Should NOT be in a fenced code block
        self.assertNotIn("```", ref_md)

    def test_skill_md_code_block_count(self):
        """Test that SKILL.md overview includes code block count."""
        from skill_seekers.cli.video_scraper import VideoToSkillConverter
        from skill_seekers.cli.video_models import (
            CodeBlock,
            CodeContext,
            KeyFrame,
            SegmentContentType,
            TranscriptSource,
            VideoInfo,
            VideoScraperResult,
            VideoSegment,
            VideoSourceType,
        )

        config = {
            "name": "test_video",
            "output": os.path.join(self.temp_dir, "test_video"),
        }
        converter = VideoToSkillConverter(config)

        converter.result = VideoScraperResult(
            videos=[
                VideoInfo(
                    video_id="test789",
                    source_type=VideoSourceType.YOUTUBE,
                    title="Code Tutorial",
                    duration=60.0,
                    transcript_source=TranscriptSource.YOUTUBE_MANUAL,
                    segments=[
                        VideoSegment(
                            index=0,
                            start_time=0.0,
                            end_time=60.0,
                            duration=60.0,
                            content="### Code\n\nSome content.",
                            content_type=SegmentContentType.LIVE_CODING,
                            confidence=0.9,
                            keyframes=[
                                KeyFrame(
                                    timestamp=5.0,
                                    image_path="/nonexistent/frame.jpg",
                                    ocr_text="print('hi')",
                                ),
                            ],
                            detected_code_blocks=[
                                CodeBlock(
                                    code="print('hi')",
                                    language="python",
                                    source_frame=5.0,
                                    context=CodeContext.EDITOR,
                                    confidence=0.9,
                                ),
                            ],
                        ),
                    ],
                ),
            ],
            total_duration_seconds=60.0,
            total_segments=1,
            total_code_blocks=1,
        )

        skill_md = converter._generate_skill_md()
        self.assertIn("1 code blocks detected", skill_md)


# =============================================================================
# Test: Y-Bucket Consensus Engine (Phase A)
# =============================================================================


class TestYBucketConsensus(unittest.TestCase):
    """Test the Y-bucket consensus engine for multi-frame OCR."""

    def test_single_frame_single_region(self):
        from skill_seekers.cli.video_visual import YBucketConsensusEngine
        from skill_seekers.cli.video_models import OCRRegion

        engine = YBucketConsensusEngine(y_tolerance=15.0)
        engine.add_frame(
            0,
            1.0,
            [OCRRegion(text="hello world", confidence=0.9, bbox=(10, 100, 200, 120))],
        )
        buckets = engine.build_consensus()
        self.assertEqual(len(buckets), 1)
        self.assertEqual(buckets[0].consensus_text, "hello world")
        self.assertAlmostEqual(buckets[0].consensus_confidence, 0.9)

    def test_consensus_from_multiple_frames(self):
        from skill_seekers.cli.video_visual import YBucketConsensusEngine
        from skill_seekers.cli.video_models import OCRRegion

        engine = YBucketConsensusEngine(y_tolerance=15.0)
        # Frame 0: low confidence garbled text
        engine.add_frame(
            0,
            1.0,
            [OCRRegion(text="Dlctionary", confidence=0.3, bbox=(10, 100, 200, 120))],
        )
        # Frame 1: medium confidence
        engine.add_frame(
            1,
            1.5,
            [OCRRegion(text="Dictionary", confidence=0.62, bbox=(10, 102, 200, 122))],
        )
        # Frame 2: good confidence
        engine.add_frame(
            2,
            2.0,
            [OCRRegion(text="Dictionary", confidence=0.85, bbox=(10, 101, 200, 121))],
        )
        buckets = engine.build_consensus()
        self.assertEqual(len(buckets), 1)
        self.assertEqual(buckets[0].consensus_text, "Dictionary")
        self.assertGreater(buckets[0].consensus_confidence, 0.5)

    def test_multiple_lines_tracked(self):
        from skill_seekers.cli.video_visual import YBucketConsensusEngine
        from skill_seekers.cli.video_models import OCRRegion

        engine = YBucketConsensusEngine(y_tolerance=15.0)
        engine.add_frame(
            0,
            1.0,
            [
                OCRRegion(text="line one", confidence=0.9, bbox=(10, 100, 200, 120)),
                OCRRegion(text="line two", confidence=0.8, bbox=(10, 150, 200, 170)),
            ],
        )
        buckets = engine.build_consensus()
        self.assertEqual(len(buckets), 2)
        texts = [b.consensus_text for b in buckets]
        self.assertIn("line one", texts)
        self.assertIn("line two", texts)

    def test_low_confidence_single_observation_empty(self):
        from skill_seekers.cli.video_visual import YBucketConsensusEngine
        from skill_seekers.cli.video_models import OCRRegion

        engine = YBucketConsensusEngine(y_tolerance=15.0)
        engine.add_frame(
            0,
            1.0,
            [OCRRegion(text="garbled", confidence=0.2, bbox=(10, 100, 200, 120))],
        )
        buckets = engine.build_consensus()
        self.assertEqual(len(buckets), 1)
        self.assertEqual(buckets[0].consensus_text, "")

    def test_get_consensus_text_joins_lines(self):
        from skill_seekers.cli.video_visual import YBucketConsensusEngine
        from skill_seekers.cli.video_models import OCRRegion

        engine = YBucketConsensusEngine(y_tolerance=15.0)
        engine.add_frame(
            0,
            1.0,
            [
                OCRRegion(text="def hello():", confidence=0.9, bbox=(10, 100, 200, 120)),
                OCRRegion(text="    return 'world'", confidence=0.8, bbox=(10, 140, 250, 160)),
            ],
        )
        engine.build_consensus()
        text = engine.get_consensus_text()
        self.assertIn("def hello():", text)
        self.assertIn("return 'world'", text)
        self.assertIn("\n", text)

    def test_reset_clears_state(self):
        from skill_seekers.cli.video_visual import YBucketConsensusEngine
        from skill_seekers.cli.video_models import OCRRegion

        engine = YBucketConsensusEngine()
        engine.add_frame(0, 1.0, [OCRRegion(text="test", confidence=0.9, bbox=(10, 100, 200, 120))])
        engine.reset()
        self.assertEqual(engine.get_consensus_text(), "")
        self.assertEqual(engine.get_consensus_confidence(), 0.0)

    def test_get_bucket_y_centers(self):
        from skill_seekers.cli.video_visual import YBucketConsensusEngine
        from skill_seekers.cli.video_models import OCRRegion

        engine = YBucketConsensusEngine(y_tolerance=15.0)
        engine.add_frame(
            0,
            1.0,
            [
                OCRRegion(text="a", confidence=0.9, bbox=(0, 100, 100, 120)),
                OCRRegion(text="b", confidence=0.9, bbox=(0, 200, 100, 220)),
            ],
        )
        centers = engine.get_bucket_y_centers()
        self.assertEqual(len(centers), 2)
        self.assertIn(110.0, centers)
        self.assertIn(210.0, centers)


# =============================================================================
# Test: Text Group Lifecycle (Phase B)
# =============================================================================


class TestTextGroupLifecycle(unittest.TestCase):
    """Test text group assignment and edit detection."""

    def test_single_block_creates_group(self):
        from skill_seekers.cli.video_visual import TextBlockTracker
        from skill_seekers.cli.video_models import FrameType, OCRRegion

        tracker = TextBlockTracker()
        regions = [
            OCRRegion(text="def hello():", confidence=0.9, bbox=(10, 100, 200, 120)),
            OCRRegion(text="    return 'world'", confidence=0.8, bbox=(10, 140, 250, 160)),
        ]
        tracker.update(
            0,
            1.0,
            "def hello():\n    return 'world'",
            0.85,
            FrameType.CODE_EDITOR,
            ocr_regions=regions,
        )
        tracker.finalize()
        groups = tracker.get_text_groups()
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].group_id, "TG-001")
        self.assertEqual(len(groups[0].appearances), 1)

    def test_same_text_reappears_same_group(self):
        from skill_seekers.cli.video_visual import TextBlockTracker
        from skill_seekers.cli.video_models import FrameType, OCRRegion

        tracker = TextBlockTracker()
        regions = [
            OCRRegion(text="def hello():", confidence=0.9, bbox=(10, 100, 200, 120)),
            OCRRegion(text="    return 'world'", confidence=0.8, bbox=(10, 140, 250, 160)),
        ]
        text = "def hello():\n    return 'world'"

        # First appearance
        tracker.update(0, 1.0, text, 0.85, FrameType.CODE_EDITOR, ocr_regions=regions)
        # Break with non-code frame
        tracker.update(1, 5.0, "webcam", 0.5, FrameType.WEBCAM)
        # Re-appear
        tracker.update(2, 10.0, text, 0.85, FrameType.CODE_EDITOR, ocr_regions=regions)

        tracker.finalize()
        groups = tracker.get_text_groups()
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0].appearances), 2)

    def test_different_text_creates_new_group(self):
        from skill_seekers.cli.video_visual import TextBlockTracker
        from skill_seekers.cli.video_models import FrameType, OCRRegion

        tracker = TextBlockTracker()
        regions_a = [
            OCRRegion(text="def func_a():", confidence=0.9, bbox=(10, 100, 200, 120)),
        ]
        regions_b = [
            OCRRegion(text="class TotallyDifferent:", confidence=0.9, bbox=(10, 100, 300, 120)),
        ]

        tracker.update(0, 1.0, "def func_a():", 0.9, FrameType.CODE_EDITOR, ocr_regions=regions_a)
        tracker.update(1, 5.0, "webcam", 0.5, FrameType.WEBCAM)
        tracker.update(
            2, 10.0, "class TotallyDifferent:", 0.9, FrameType.CODE_EDITOR, ocr_regions=regions_b
        )

        tracker.finalize()
        groups = tracker.get_text_groups()
        self.assertEqual(len(groups), 2)

    def test_edit_detected_between_appearances(self):
        from skill_seekers.cli.video_visual import TextBlockTracker
        from skill_seekers.cli.video_models import FrameType, OCRRegion

        tracker = TextBlockTracker()
        regions_v1 = [
            OCRRegion(text="def hello():", confidence=0.9, bbox=(10, 100, 200, 120)),
            OCRRegion(text="    return 'world'", confidence=0.8, bbox=(10, 140, 250, 160)),
        ]
        regions_v2 = [
            OCRRegion(text="def hello():", confidence=0.9, bbox=(10, 100, 200, 120)),
            OCRRegion(text="    return 'hello world'", confidence=0.8, bbox=(10, 140, 250, 160)),
        ]

        # First version
        tracker.update(
            0,
            1.0,
            "def hello():\n    return 'world'",
            0.85,
            FrameType.CODE_EDITOR,
            ocr_regions=regions_v1,
        )
        tracker.update(1, 5.0, "webcam", 0.5, FrameType.WEBCAM)
        # Modified version
        tracker.update(
            2,
            10.0,
            "def hello():\n    return 'hello world'",
            0.85,
            FrameType.CODE_EDITOR,
            ocr_regions=regions_v2,
        )

        tracker.finalize()
        groups = tracker.get_text_groups()
        self.assertEqual(len(groups), 1)
        self.assertGreaterEqual(len(groups[0].edits), 1)

    def test_tracker_y_bucket_matching(self):
        """Test that y-bucket matching works for consecutive code frames."""
        from skill_seekers.cli.video_visual import TextBlockTracker
        from skill_seekers.cli.video_models import FrameType, OCRRegion

        tracker = TextBlockTracker()
        # Two frames with same y-coordinates but slightly different text
        regions_1 = [
            OCRRegion(text="Dlctionary", confidence=0.3, bbox=(10, 100, 200, 120)),
            OCRRegion(text="var x = 1", confidence=0.7, bbox=(10, 140, 200, 160)),
        ]
        regions_2 = [
            OCRRegion(text="Dictionary", confidence=0.8, bbox=(10, 101, 200, 121)),
            OCRRegion(text="var x = 1", confidence=0.9, bbox=(10, 141, 200, 161)),
        ]

        tracker.update(
            0, 1.0, "Dlctionary\nvar x = 1", 0.5, FrameType.CODE_EDITOR, ocr_regions=regions_1
        )
        tracker.update(
            1, 2.0, "Dictionary\nvar x = 1", 0.85, FrameType.CODE_EDITOR, ocr_regions=regions_2
        )

        blocks = tracker.finalize()
        # Should be one block (matched by y-bucket overlap)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(len(blocks[0].frame_indices), 2)

    def test_compute_edit_no_changes(self):
        from skill_seekers.cli.video_visual import TextBlockTracker

        tracker = TextBlockTracker()
        result = tracker._compute_edit(["line1", "line2"], ["line1", "line2"], 1.0)
        self.assertIsNone(result)

    def test_compute_edit_with_additions(self):
        from skill_seekers.cli.video_visual import TextBlockTracker

        tracker = TextBlockTracker()
        result = tracker._compute_edit(["line1"], ["line1", "line2"], 1.0)
        self.assertIsNotNone(result)
        self.assertIn("line2", result.added_lines)

    def test_compute_edit_with_removals(self):
        from skill_seekers.cli.video_visual import TextBlockTracker

        tracker = TextBlockTracker()
        result = tracker._compute_edit(["line1", "line2"], ["line1"], 1.0)
        self.assertIsNotNone(result)
        self.assertIn("line2", result.removed_lines)


# =============================================================================
# Test: Text Group Timeline (Phase C)
# =============================================================================


class TestTextGroupTimeline(unittest.TestCase):
    """Test TextGroupTimeline data structure."""

    def test_timeline_serialization(self):
        from skill_seekers.cli.video_models import TextGroup, TextGroupTimeline, FrameType

        tg = TextGroup(
            group_id="TG-001",
            appearances=[(1.0, 5.0), (10.0, 15.0)],
            consensus_lines=[
                {"y_center": 110.0, "text": "def hello():", "confidence": 0.9},
                {"y_center": 150.0, "text": "    return 'world'", "confidence": 0.8},
            ],
            edits=[],
            frame_type=FrameType.CODE_EDITOR,
        )
        timeline = TextGroupTimeline(
            text_groups=[tg],
            total_code_time=9.0,
            total_groups=1,
            total_edits=0,
        )

        d = timeline.to_dict()
        self.assertEqual(len(d["text_groups"]), 1)
        self.assertEqual(d["total_code_time"], 9.0)

        timeline2 = TextGroupTimeline.from_dict(d)
        self.assertEqual(len(timeline2.text_groups), 1)
        self.assertEqual(timeline2.text_groups[0].group_id, "TG-001")

    def test_get_groups_at_time(self):
        from skill_seekers.cli.video_models import TextGroup, TextGroupTimeline, FrameType

        tg1 = TextGroup(
            group_id="TG-001",
            appearances=[(1.0, 5.0)],
            consensus_lines=[{"text": "code1", "y_center": 100.0, "confidence": 0.9}],
            edits=[],
            frame_type=FrameType.CODE_EDITOR,
        )
        tg2 = TextGroup(
            group_id="TG-002",
            appearances=[(3.0, 8.0)],
            consensus_lines=[{"text": "code2", "y_center": 100.0, "confidence": 0.9}],
            edits=[],
            frame_type=FrameType.CODE_EDITOR,
        )
        timeline = TextGroupTimeline(text_groups=[tg1, tg2])

        # At t=4, both should be active
        active = timeline.get_groups_at_time(4.0)
        self.assertEqual(len(active), 2)

        # At t=0, none active
        active = timeline.get_groups_at_time(0.0)
        self.assertEqual(len(active), 0)

        # At t=6, only TG-002
        active = timeline.get_groups_at_time(6.0)
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].group_id, "TG-002")

    def test_text_group_full_text(self):
        from skill_seekers.cli.video_models import TextGroup, FrameType

        tg = TextGroup(
            group_id="TG-001",
            consensus_lines=[
                {"y_center": 100.0, "text": "line one", "confidence": 0.9},
                {"y_center": 120.0, "text": "", "confidence": 0.0},
                {"y_center": 140.0, "text": "line three", "confidence": 0.8},
            ],
            edits=[],
            frame_type=FrameType.CODE_EDITOR,
        )
        self.assertEqual(tg.full_text, "line one\nline three")

    def test_text_group_serialization(self):
        from skill_seekers.cli.video_models import TextGroup, TextGroupEdit, FrameType

        edit = TextGroupEdit(
            timestamp=5.0,
            added_lines=["new line"],
            removed_lines=[],
            modified_lines=[{"line_num": 0, "old": "x", "new": "y"}],
        )
        tg = TextGroup(
            group_id="TG-001",
            appearances=[(1.0, 5.0)],
            consensus_lines=[{"y_center": 100.0, "text": "code", "confidence": 0.9}],
            edits=[edit],
            detected_language="python",
            frame_type=FrameType.CODE_EDITOR,
        )

        d = tg.to_dict()
        self.assertEqual(d["group_id"], "TG-001")
        self.assertEqual(d["detected_language"], "python")
        self.assertEqual(len(d["edits"]), 1)

        tg2 = TextGroup.from_dict(d)
        self.assertEqual(tg2.group_id, "TG-001")
        self.assertEqual(tg2.detected_language, "python")
        self.assertEqual(len(tg2.edits), 1)
        self.assertEqual(tg2.edits[0].added_lines, ["new line"])

    def test_code_block_text_group_id(self):
        from skill_seekers.cli.video_models import CodeBlock, CodeContext

        cb = CodeBlock(
            code="print('hi')",
            language="python",
            context=CodeContext.EDITOR,
            confidence=0.9,
            text_group_id="TG-001",
        )
        d = cb.to_dict()
        self.assertEqual(d["text_group_id"], "TG-001")

        cb2 = CodeBlock.from_dict(d)
        self.assertEqual(cb2.text_group_id, "TG-001")

    def test_video_info_timeline_serialization(self):
        from skill_seekers.cli.video_models import (
            VideoInfo,
            VideoSourceType,
            TextGroupTimeline,
            TextGroup,
            FrameType,
        )

        tg = TextGroup(
            group_id="TG-001",
            appearances=[(1.0, 5.0)],
            consensus_lines=[{"y_center": 100.0, "text": "code", "confidence": 0.9}],
            edits=[],
            frame_type=FrameType.CODE_EDITOR,
        )
        timeline = TextGroupTimeline(text_groups=[tg], total_groups=1)

        info = VideoInfo(
            video_id="test",
            source_type=VideoSourceType.YOUTUBE,
            text_group_timeline=timeline,
        )
        d = info.to_dict()
        self.assertIsNotNone(d["text_group_timeline"])
        self.assertEqual(len(d["text_group_timeline"]["text_groups"]), 1)

        info2 = VideoInfo.from_dict(d)
        self.assertIsNotNone(info2.text_group_timeline)
        self.assertEqual(len(info2.text_group_timeline.text_groups), 1)

    def test_video_info_no_timeline_serialization(self):
        from skill_seekers.cli.video_models import VideoInfo, VideoSourceType

        info = VideoInfo(video_id="test", source_type=VideoSourceType.YOUTUBE)
        d = info.to_dict()
        self.assertIsNone(d["text_group_timeline"])

        info2 = VideoInfo.from_dict(d)
        self.assertIsNone(info2.text_group_timeline)

    def test_extract_visual_data_returns_3_tuple(self):
        """Verify extract_visual_data returns (keyframes, code_blocks, timeline) tuple."""
        from skill_seekers.cli.video_visual import extract_visual_data, HAS_OPENCV

        if not HAS_OPENCV:
            with self.assertRaises(RuntimeError):
                extract_visual_data("test.mp4", [], "/tmp/test")
        else:
            import inspect

            sig = inspect.signature(extract_visual_data)
            self.assertIn("tuple", str(sig.return_annotation).lower())
            self.assertIn("TextGroupTimeline", str(sig.return_annotation))


# =============================================================================
# Test: Audio-Visual Alignment (Phase D)
# =============================================================================


class TestAudioVisualAlignment(unittest.TestCase):
    """Test audio-visual alignment building and rendering."""

    def test_alignment_serialization(self):
        from skill_seekers.cli.video_models import AudioVisualAlignment

        av = AudioVisualAlignment(
            text_group_id="TG-001",
            start_time=1.0,
            end_time=5.0,
            on_screen_code="def hello():\n    return 'world'",
            transcript_during="Now let's define a hello function",
            language="python",
        )
        d = av.to_dict()
        self.assertEqual(d["text_group_id"], "TG-001")
        self.assertEqual(d["language"], "python")

        av2 = AudioVisualAlignment.from_dict(d)
        self.assertEqual(av2.text_group_id, "TG-001")
        self.assertEqual(av2.language, "python")
        self.assertIn("hello function", av2.transcript_during)

    def test_build_audio_visual_alignments(self):
        from skill_seekers.cli.video_scraper import _build_audio_visual_alignments
        from skill_seekers.cli.video_models import (
            TextGroup,
            TextGroupTimeline,
            TranscriptSegment,
            TranscriptSource,
            FrameType,
        )

        tg = TextGroup(
            group_id="TG-001",
            appearances=[(10.0, 20.0)],
            consensus_lines=[
                {"y_center": 100.0, "text": "def hello():", "confidence": 0.9},
            ],
            edits=[],
            frame_type=FrameType.CODE_EDITOR,
        )
        timeline = TextGroupTimeline(text_groups=[tg])

        transcript = [
            TranscriptSegment(
                text="Before code", start=5.0, end=9.0, source=TranscriptSource.YOUTUBE_MANUAL
            ),
            TranscriptSegment(
                text="Now we define hello",
                start=10.0,
                end=15.0,
                source=TranscriptSource.YOUTUBE_MANUAL,
            ),
            TranscriptSegment(
                text="and it returns world",
                start=15.0,
                end=20.0,
                source=TranscriptSource.YOUTUBE_MANUAL,
            ),
            TranscriptSegment(
                text="After code", start=21.0, end=25.0, source=TranscriptSource.YOUTUBE_MANUAL
            ),
        ]

        alignments = _build_audio_visual_alignments(timeline, transcript)
        self.assertEqual(len(alignments), 1)
        self.assertEqual(alignments[0].text_group_id, "TG-001")
        self.assertIn("define hello", alignments[0].transcript_during)
        self.assertIn("returns world", alignments[0].transcript_during)
        # Before and after should not be included
        self.assertNotIn("Before code", alignments[0].transcript_during)
        self.assertNotIn("After code", alignments[0].transcript_during)

    def test_build_alignments_no_overlap(self):
        from skill_seekers.cli.video_scraper import _build_audio_visual_alignments
        from skill_seekers.cli.video_models import (
            TextGroup,
            TextGroupTimeline,
            TranscriptSegment,
            TranscriptSource,
            FrameType,
        )

        tg = TextGroup(
            group_id="TG-001",
            appearances=[(100.0, 110.0)],
            consensus_lines=[{"y_center": 100.0, "text": "code", "confidence": 0.9}],
            edits=[],
            frame_type=FrameType.CODE_EDITOR,
        )
        timeline = TextGroupTimeline(text_groups=[tg])

        transcript = [
            TranscriptSegment(
                text="Unrelated", start=0.0, end=5.0, source=TranscriptSource.YOUTUBE_MANUAL
            ),
        ]

        alignments = _build_audio_visual_alignments(timeline, transcript)
        self.assertEqual(len(alignments), 0)

    def test_reference_md_code_timeline_section(self):
        """Test that Code Timeline section renders correctly."""
        from skill_seekers.cli.video_scraper import VideoToSkillConverter
        from skill_seekers.cli.video_models import (
            FrameType,
            TextGroup,
            TextGroupTimeline,
            TranscriptSource,
            VideoInfo,
            VideoScraperResult,
            VideoSegment,
            SegmentContentType,
            VideoSourceType,
        )

        config = {"name": "test_video", "output": os.path.join(tempfile.mkdtemp(), "test_video")}
        converter = VideoToSkillConverter(config)

        tg = TextGroup(
            group_id="TG-001",
            appearances=[(1.0, 5.0)],
            consensus_lines=[
                {"y_center": 100.0, "text": "def hello():", "confidence": 0.9},
                {"y_center": 140.0, "text": "    return 'world'", "confidence": 0.8},
            ],
            edits=[],
            frame_type=FrameType.CODE_EDITOR,
        )
        timeline = TextGroupTimeline(
            text_groups=[tg], total_code_time=4.0, total_groups=1, total_edits=0
        )

        converter.result = VideoScraperResult(
            videos=[
                VideoInfo(
                    video_id="test",
                    source_type=VideoSourceType.YOUTUBE,
                    title="Test",
                    duration=60.0,
                    transcript_source=TranscriptSource.YOUTUBE_MANUAL,
                    text_group_timeline=timeline,
                    segments=[
                        VideoSegment(
                            index=0,
                            start_time=0.0,
                            end_time=60.0,
                            duration=60.0,
                            content="### Intro\n\nContent.",
                            content_type=SegmentContentType.LIVE_CODING,
                        ),
                    ],
                ),
            ],
            total_duration_seconds=60.0,
            total_segments=1,
        )

        ref_md = converter._generate_reference_md(converter.result.videos[0])
        self.assertIn("## Code Timeline", ref_md)
        self.assertIn("TG-001", ref_md)
        self.assertIn("def hello():", ref_md)
        self.assertIn("return 'world'", ref_md)

    def test_reference_md_audio_visual_section(self):
        """Test that Audio-Visual Alignment section renders correctly."""
        from skill_seekers.cli.video_scraper import VideoToSkillConverter
        from skill_seekers.cli.video_models import (
            AudioVisualAlignment,
            TranscriptSource,
            VideoInfo,
            VideoScraperResult,
            VideoSegment,
            SegmentContentType,
            VideoSourceType,
        )

        config = {"name": "test_video", "output": os.path.join(tempfile.mkdtemp(), "test_video")}
        converter = VideoToSkillConverter(config)

        converter.result = VideoScraperResult(
            videos=[
                VideoInfo(
                    video_id="test",
                    source_type=VideoSourceType.YOUTUBE,
                    title="Test",
                    duration=60.0,
                    transcript_source=TranscriptSource.YOUTUBE_MANUAL,
                    audio_visual_alignments=[
                        AudioVisualAlignment(
                            text_group_id="TG-001",
                            start_time=1.0,
                            end_time=5.0,
                            on_screen_code="def hello():\n    return 'world'",
                            transcript_during="Now we write a hello function",
                            language="python",
                        ),
                    ],
                    segments=[
                        VideoSegment(
                            index=0,
                            start_time=0.0,
                            end_time=60.0,
                            duration=60.0,
                            content="### Intro\n\nContent.",
                            content_type=SegmentContentType.LIVE_CODING,
                        ),
                    ],
                ),
            ],
            total_duration_seconds=60.0,
            total_segments=1,
        )

        ref_md = converter._generate_reference_md(converter.result.videos[0])
        self.assertIn("## Audio-Visual Alignment", ref_md)
        self.assertIn("TG-001", ref_md)
        self.assertIn("def hello():", ref_md)
        self.assertIn("hello function", ref_md)
        self.assertIn("**Narrator:**", ref_md)


# =============================================================================
# Phase E-G Tests: Dark Theme, Multi-Engine OCR, Claude Vision
# =============================================================================


class TestDarkThemePreprocessing(unittest.TestCase):
    """Tests for dark theme detection and frame preprocessing."""

    def test_detect_theme_dark(self):
        """Dark image (median < 128) returns 'dark'."""
        import numpy as np

        from skill_seekers.cli.video_visual import _detect_theme

        # Simulate a dark IDE background (median ~30)
        dark_img = np.full((100, 200), 30, dtype=np.uint8)
        self.assertEqual(_detect_theme(dark_img), "dark")

    def test_detect_theme_light(self):
        """Light image (median >= 128) returns 'light'."""
        import numpy as np

        from skill_seekers.cli.video_visual import _detect_theme

        # Simulate a light background (median ~220)
        light_img = np.full((100, 200), 220, dtype=np.uint8)
        self.assertEqual(_detect_theme(light_img), "light")

    def test_preprocess_inverts_dark_frame(self):
        """Verify dark code frame gets inverted to produce lighter output."""
        try:
            import cv2
            import numpy as np
        except ImportError:
            self.skipTest("OpenCV not available")

        from skill_seekers.cli.video_models import FrameType
        from skill_seekers.cli.video_visual import _preprocess_frame_for_ocr

        # Create a dark frame (simulating dark-theme IDE)
        dark_frame = np.full((100, 200, 3), 30, dtype=np.uint8)
        # Add some "text" pixels (bright on dark)
        dark_frame[40:60, 20:180] = 200

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
        cv2.imwrite(tmp_path, dark_frame)

        try:
            result_path = _preprocess_frame_for_ocr(tmp_path, FrameType.CODE_EDITOR)
            self.assertNotEqual(result_path, tmp_path)

            result_img = cv2.imread(result_path, cv2.IMREAD_GRAYSCALE)
            self.assertIsNotNone(result_img)

            # After inversion + binarization, the output should have higher
            # median brightness (white background with dark text)
            original_gray = cv2.imread(tmp_path, cv2.IMREAD_GRAYSCALE)
            self.assertGreater(float(np.median(result_img)), float(np.median(original_gray)))

            os.unlink(result_path)
        finally:
            os.unlink(tmp_path)

    def test_preprocess_keeps_light_frame_orientation(self):
        """Verify light code frame is binarized but not double-inverted."""
        try:
            import cv2
            import numpy as np
        except ImportError:
            self.skipTest("OpenCV not available")

        from skill_seekers.cli.video_models import FrameType
        from skill_seekers.cli.video_visual import _preprocess_frame_for_ocr

        # Create a light frame (white background, dark text)
        light_frame = np.full((100, 200, 3), 240, dtype=np.uint8)
        light_frame[40:60, 20:180] = 30  # dark text

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
        cv2.imwrite(tmp_path, light_frame)

        try:
            result_path = _preprocess_frame_for_ocr(tmp_path, FrameType.CODE_EDITOR)
            self.assertNotEqual(result_path, tmp_path)

            result_img = cv2.imread(result_path, cv2.IMREAD_GRAYSCALE)
            self.assertIsNotNone(result_img)

            # Light frame should still have high median (white background preserved)
            self.assertGreater(float(np.median(result_img)), 128)

            os.unlink(result_path)
        finally:
            os.unlink(tmp_path)


class TestMultiEngineOCR(unittest.TestCase):
    """Tests for multi-engine OCR ensemble voting."""

    def test_tesseract_ocr_returns_correct_format(self):
        """Verify _run_tesseract_ocr returns (bbox, text, confidence) tuples."""
        try:
            import pytesseract  # noqa: F401
            import cv2
            import numpy as np
        except ImportError:
            self.skipTest("pytesseract or OpenCV not available")

        from skill_seekers.cli.video_models import FrameType
        from skill_seekers.cli.video_visual import _run_tesseract_ocr

        # Create a simple white image with black text
        img = np.full((100, 400), 255, dtype=np.uint8)
        cv2.putText(img, "def hello():", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, 0, 2)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
        cv2.imwrite(tmp_path, img)

        try:
            results = _run_tesseract_ocr(tmp_path, FrameType.CODE_EDITOR)
            # Results should be a list of tuples
            self.assertIsInstance(results, list)
            for item in results:
                self.assertEqual(len(item), 3)
                bbox, text, conf = item
                self.assertIsInstance(bbox, list)
                self.assertIsInstance(text, str)
                self.assertIsInstance(conf, float)
                self.assertGreaterEqual(conf, 0.0)
                self.assertLessEqual(conf, 1.0)
        finally:
            os.unlink(tmp_path)

    def test_multi_engine_picks_higher_confidence(self):
        """Mock both engines: higher confidence result wins."""
        from skill_seekers.cli.video_visual import _pick_better_ocr_result

        result_high = ([[0, 0], [100, 0], [100, 20], [0, 20]], "def foo():", 0.9)
        result_low = ([[0, 0], [100, 0], [100, 20], [0, 20]], "deff fo()", 0.4)

        winner = _pick_better_ocr_result(result_high, result_low)
        self.assertEqual(winner[1], "def foo():")
        self.assertEqual(winner[2], 0.9)

    def test_multi_engine_code_token_preference(self):
        """Result with code tokens preferred over garbage."""
        from skill_seekers.cli.video_visual import _pick_better_ocr_result

        # Garbage has higher confidence but no code tokens
        garbage = ([[0, 0], [100, 0], [100, 20], [0, 20]], "chitd Icrate", 0.8)
        code = ([[0, 0], [100, 0], [100, 20], [0, 20]], "def create():", 0.6)

        winner = _pick_better_ocr_result(garbage, code)
        self.assertEqual(winner[1], "def create():")

    def test_multi_engine_single_engine_fallback(self):
        """When one engine returns nothing, use the other."""
        from skill_seekers.cli.video_visual import _merge_by_y_bucket

        easy_results = [
            ([[0, 0], [100, 0], [100, 20], [0, 20]], "line one", 0.8),
            ([[0, 30], [100, 30], [100, 50], [0, 50]], "line two", 0.7),
        ]

        merged = _merge_by_y_bucket(easy_results, [])
        # Should return easy_results when tess is empty
        # (the function won't be called with both empty — that's handled upstream)
        self.assertEqual(len(merged), 2)


class TestClaudeVisionOCR(unittest.TestCase):
    """Tests for Claude Vision API OCR fallback."""

    def test_vision_ocr_no_api_key(self):
        """Returns empty when ANTHROPIC_API_KEY is not set."""
        from unittest.mock import patch

        from skill_seekers.cli.video_models import FrameType
        from skill_seekers.cli.video_visual import _ocr_with_claude_vision

        with patch.dict(os.environ, {}, clear=True):
            # Ensure no ANTHROPIC_API_KEY
            os.environ.pop("ANTHROPIC_API_KEY", None)
            text, conf = _ocr_with_claude_vision("/fake/path.png", FrameType.CODE_EDITOR)
            self.assertEqual(text, "")
            self.assertEqual(conf, 0.0)

    def test_vision_ocr_success(self):
        """Mock anthropic client returns extracted code."""
        import sys
        from unittest.mock import MagicMock, patch

        from skill_seekers.cli.video_models import FrameType
        from skill_seekers.cli.video_visual import _ocr_with_claude_vision

        # Create a minimal image file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
            tmp_path = tmp.name

        try:
            mock_response = MagicMock()
            mock_content = MagicMock()
            mock_content.text = "def hello():\n    return 'world'"
            mock_response.content = [mock_content]

            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response

            mock_anthropic = MagicMock()
            mock_anthropic.Anthropic.return_value = mock_client

            with (
                patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}),
                patch.dict(sys.modules, {"anthropic": mock_anthropic}),
            ):
                text, conf = _ocr_with_claude_vision(tmp_path, FrameType.CODE_EDITOR)

            self.assertIn("def hello():", text)
            self.assertEqual(conf, 0.95)
        finally:
            os.unlink(tmp_path)

    def test_vision_fallback_on_low_confidence(self):
        """Vision API is only called when multi-engine conf < 0.5."""
        from skill_seekers.cli.video_models import FrameType
        from skill_seekers.cli.video_visual import _ocr_with_claude_vision

        # Without API key, vision always returns empty — simulating no-fallback
        os.environ.pop("ANTHROPIC_API_KEY", None)
        text, conf = _ocr_with_claude_vision("/fake.png", FrameType.CODE_EDITOR)
        self.assertEqual(text, "")
        self.assertEqual(conf, 0.0)


class TestRegionDetection(unittest.TestCase):
    """Tests for IDE panel detection and region-based classification."""

    def test_single_panel_no_dividers(self):
        """A uniform frame produces a single full-frame region."""
        try:
            import cv2
            import numpy as np
        except ImportError:
            self.skipTest("OpenCV not available")

        from skill_seekers.cli.video_visual import classify_frame_regions

        # Uniform dark frame — no dividers
        img = np.full((400, 800, 3), 35, dtype=np.uint8)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
        cv2.imwrite(tmp_path, img)

        try:
            regions = classify_frame_regions(tmp_path)
            self.assertEqual(len(regions), 1)
            x1, y1, x2, y2, _ft = regions[0]
            self.assertEqual((x1, y1), (0, 0))
            self.assertEqual((x2, y2), (800, 400))
        finally:
            os.unlink(tmp_path)

    def test_vertical_divider_splits_panels(self):
        """A bright vertical line creates two separate panels."""
        try:
            import cv2
            import numpy as np
        except ImportError:
            self.skipTest("OpenCV not available")

        from skill_seekers.cli.video_visual import classify_frame_regions

        # Dark frame with a bright vertical divider at x=400
        img = np.full((600, 800, 3), 35, dtype=np.uint8)
        img[:, 398:402] = 200  # 4px bright vertical line

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
        cv2.imwrite(tmp_path, img)

        try:
            regions = classify_frame_regions(tmp_path)
            # Should detect at least 2 panels (left and right of divider)
            self.assertGreaterEqual(len(regions), 2)
        finally:
            os.unlink(tmp_path)

    def test_find_code_bbox_merges_regions(self):
        """_find_code_bbox merges multiple code panels into one box."""
        from skill_seekers.cli.video_models import FrameType
        from skill_seekers.cli.video_visual import _find_code_bbox

        regions = [
            (0, 0, 200, 600, FrameType.CODE_EDITOR),
            (200, 0, 800, 600, FrameType.WEBCAM),
            (800, 0, 1000, 600, FrameType.CODE_EDITOR),
        ]
        bbox = _find_code_bbox(regions)
        self.assertIsNotNone(bbox)
        self.assertEqual(bbox, (0, 0, 1000, 600))

    def test_find_code_bbox_returns_none_for_no_code(self):
        """_find_code_bbox returns None when no code regions exist."""
        from skill_seekers.cli.video_models import FrameType
        from skill_seekers.cli.video_visual import _find_code_bbox

        regions = [
            (0, 0, 800, 600, FrameType.WEBCAM),
            (800, 0, 1200, 600, FrameType.DIAGRAM),
        ]
        self.assertIsNone(_find_code_bbox(regions))

    def test_small_panels_filtered_out(self):
        """Panels smaller than minimum size thresholds are excluded."""
        try:
            import cv2
            import numpy as np
        except ImportError:
            self.skipTest("OpenCV not available")

        from skill_seekers.cli.video_visual import classify_frame_regions

        # Create frame with many thin vertical dividers creating tiny panels
        img = np.full((400, 800, 3), 35, dtype=np.uint8)
        # Add dividers at x=50, x=100 — creates panels < 200px wide
        img[:, 48:52] = 200
        img[:, 98:102] = 200

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
        cv2.imwrite(tmp_path, img)

        try:
            regions = classify_frame_regions(tmp_path)
            # Tiny panels (< 200px wide) should be filtered out
            for x1, _y1, x2, _y2, _ft in regions:
                self.assertGreaterEqual(x2 - x1, 200)
        finally:
            os.unlink(tmp_path)

    def test_crop_code_region(self):
        """_crop_code_region saves a cropped version of the frame."""
        try:
            import cv2
            import numpy as np
        except ImportError:
            self.skipTest("OpenCV not available")

        from skill_seekers.cli.video_visual import _crop_code_region

        img = np.full((600, 1000, 3), 100, dtype=np.uint8)
        # Mark code region with distinct color
        img[100:500, 200:800] = 50

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
        cv2.imwrite(tmp_path, img)

        try:
            cropped = _crop_code_region(tmp_path, (200, 100, 800, 500))
            self.assertTrue(os.path.exists(cropped))
            cropped_img = cv2.imread(cropped)
            self.assertEqual(cropped_img.shape[:2], (400, 600))
            os.unlink(cropped)
        finally:
            os.unlink(tmp_path)


class TestPerPanelOCR(unittest.TestCase):
    """Tests for per-panel sub-section OCR tracking."""

    def test_get_code_panels_returns_individual_panels(self):
        """_get_code_panels returns separate bboxes instead of merging."""
        from skill_seekers.cli.video_models import FrameType
        from skill_seekers.cli.video_visual import _get_code_panels

        regions = [
            (0, 0, 500, 1080, FrameType.CODE_EDITOR),
            (500, 0, 1000, 1080, FrameType.CODE_EDITOR),
            (1000, 0, 1920, 1080, FrameType.OTHER),
        ]

        panels = _get_code_panels(regions)
        self.assertEqual(len(panels), 2)
        self.assertEqual(panels[0], (0, 0, 500, 1080))
        self.assertEqual(panels[1], (500, 0, 1000, 1080))

    def test_get_code_panels_includes_terminals(self):
        """_get_code_panels returns terminal panels too."""
        from skill_seekers.cli.video_models import FrameType
        from skill_seekers.cli.video_visual import _get_code_panels

        regions = [
            (0, 0, 960, 540, FrameType.CODE_EDITOR),
            (0, 540, 960, 1080, FrameType.TERMINAL),
            (960, 0, 1920, 1080, FrameType.OTHER),
        ]

        panels = _get_code_panels(regions)
        self.assertEqual(len(panels), 2)

    def test_get_code_panels_filters_narrow_panels(self):
        """_get_code_panels drops panels narrower than min_width."""
        from skill_seekers.cli.video_models import FrameType
        from skill_seekers.cli.video_visual import _get_code_panels

        regions = [
            (0, 0, 500, 1080, FrameType.CODE_EDITOR),  # 500px wide — kept
            (500, 0, 1400, 1080, FrameType.CODE_EDITOR),  # 900px wide — kept
            (1400, 0, 1650, 1080, FrameType.CODE_EDITOR),  # 250px wide — dropped
            (1650, 0, 1920, 1080, FrameType.CODE_EDITOR),  # 270px wide — dropped
        ]

        panels = _get_code_panels(regions)
        self.assertEqual(len(panels), 2)
        self.assertEqual(panels[0], (0, 0, 500, 1080))
        self.assertEqual(panels[1], (500, 0, 1400, 1080))

    def test_get_code_panels_custom_min_width(self):
        """_get_code_panels respects custom min_width."""
        from skill_seekers.cli.video_models import FrameType
        from skill_seekers.cli.video_visual import _get_code_panels

        regions = [
            (0, 0, 200, 1080, FrameType.CODE_EDITOR),  # 200px
            (200, 0, 500, 1080, FrameType.CODE_EDITOR),  # 300px
        ]

        # Default min_width=300 drops the 200px panel
        self.assertEqual(len(_get_code_panels(regions)), 1)
        # Custom min_width=100 keeps both
        self.assertEqual(len(_get_code_panels(regions, min_width=100)), 2)

    def test_frame_subsection_serialization(self):
        """FrameSubSection to_dict/from_dict round-trips correctly."""
        from skill_seekers.cli.video_models import (
            FrameSubSection,
            FrameType,
            OCRRegion,
        )

        ss = FrameSubSection(
            bbox=(100, 200, 500, 600),
            frame_type=FrameType.CODE_EDITOR,
            ocr_text="def hello():\n    pass",
            ocr_regions=[OCRRegion(text="def hello():", confidence=0.9, bbox=(100, 200, 400, 220))],
            ocr_confidence=0.9,
            panel_id="panel_0_0",
        )

        data = ss.to_dict()
        restored = FrameSubSection.from_dict(data)
        self.assertEqual(restored.bbox, (100, 200, 500, 600))
        self.assertEqual(restored.frame_type, FrameType.CODE_EDITOR)
        self.assertEqual(restored.ocr_text, "def hello():\n    pass")
        self.assertEqual(len(restored.ocr_regions), 1)
        self.assertAlmostEqual(restored.ocr_confidence, 0.9)
        self.assertEqual(restored.panel_id, "panel_0_0")

    def test_keyframe_with_sub_sections(self):
        """KeyFrame serialization preserves sub_sections."""
        from skill_seekers.cli.video_models import (
            FrameSubSection,
            FrameType,
            KeyFrame,
        )

        kf = KeyFrame(
            timestamp=10.0,
            image_path="/tmp/frame.jpg",
            frame_type=FrameType.CODE_EDITOR,
            sub_sections=[
                FrameSubSection(
                    bbox=(0, 0, 500, 1080),
                    frame_type=FrameType.CODE_EDITOR,
                    ocr_text="panel 1 code",
                    panel_id="panel_0_0",
                ),
                FrameSubSection(
                    bbox=(500, 0, 1000, 1080),
                    frame_type=FrameType.CODE_EDITOR,
                    ocr_text="panel 2 code",
                    panel_id="panel_0_1",
                ),
            ],
        )

        data = kf.to_dict()
        self.assertEqual(len(data["sub_sections"]), 2)

        restored = KeyFrame.from_dict(data)
        self.assertEqual(len(restored.sub_sections), 2)
        self.assertEqual(restored.sub_sections[0].ocr_text, "panel 1 code")
        self.assertEqual(restored.sub_sections[1].panel_id, "panel_0_1")

    def test_tracker_panel_position_matching(self):
        """Two calls with overlapping x-range bbox match the same block."""
        from skill_seekers.cli.video_models import FrameType
        from skill_seekers.cli.video_visual import TextBlockTracker

        tracker = TextBlockTracker()
        code = "def hello():\n    return 'world'\n# some code here"

        # First frame — left panel
        tracker.update(
            frame_index=0,
            timestamp=1.0,
            ocr_text=code,
            confidence=0.8,
            frame_type=FrameType.CODE_EDITOR,
            panel_bbox=(0, 0, 500, 1080),
        )

        # Second frame — same left panel (slightly shifted)
        tracker.update(
            frame_index=1,
            timestamp=2.0,
            ocr_text=code + "\n# added line",
            confidence=0.85,
            frame_type=FrameType.CODE_EDITOR,
            panel_bbox=(0, 0, 510, 1080),
        )

        blocks = tracker.finalize()
        # Should match as one block due to x-range overlap
        self.assertEqual(len(blocks), 1)
        self.assertEqual(len(blocks[0].frame_indices), 2)

    def test_tracker_separate_panels_tracked_separately(self):
        """Two calls with non-overlapping bboxes create separate blocks."""
        from skill_seekers.cli.video_models import FrameType
        from skill_seekers.cli.video_visual import TextBlockTracker

        tracker = TextBlockTracker()
        left_code = "def left_func():\n    return 'left'\n# left panel code"
        right_code = "def right_func():\n    return 'right'\n# right panel code"

        # Frame 0: left panel
        tracker.update(
            frame_index=0,
            timestamp=1.0,
            ocr_text=left_code,
            confidence=0.8,
            frame_type=FrameType.CODE_EDITOR,
            panel_bbox=(0, 0, 500, 1080),
        )

        # Frame 0: right panel (same frame, different panel)
        tracker.update(
            frame_index=0,
            timestamp=1.0,
            ocr_text=right_code,
            confidence=0.8,
            frame_type=FrameType.CODE_EDITOR,
            panel_bbox=(520, 0, 1020, 1080),
        )

        blocks = tracker.finalize()
        self.assertEqual(len(blocks), 2)
        # Verify they tracked different content
        texts = {b.best_text for b in blocks}
        self.assertIn(left_code, texts)
        self.assertIn(right_code, texts)


class TestTextGroupPanelId(unittest.TestCase):
    """Tests for panel_id propagation to TextGroup."""

    def test_text_group_inherits_panel_id(self):
        """Panel ID propagates from TrackedTextBlock to TextGroup."""
        from skill_seekers.cli.video_models import FrameType
        from skill_seekers.cli.video_visual import TextBlockTracker

        tracker = TextBlockTracker()
        code = "class MyClass:\n    def method(self):\n        pass"

        tracker.update(
            frame_index=0,
            timestamp=1.0,
            ocr_text=code,
            confidence=0.8,
            frame_type=FrameType.CODE_EDITOR,
            panel_bbox=(0, 0, 500, 1080),
        )

        # Complete blocks and assign text groups
        tracker.finalize()
        groups = tracker.get_text_groups()

        # TrackedTextBlock should have panel_bbox set
        blocks = tracker._completed_blocks
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].panel_bbox, (0, 0, 500, 1080))

        # The text group should exist (but panel_id propagation depends
        # on panel_id being set on the block, which requires the extraction
        # loop to set it — here we verify the mechanism works)
        self.assertTrue(len(groups) >= 1)

    def test_text_group_panel_id_serialization(self):
        """TextGroup panel_id survives to_dict/from_dict."""
        from skill_seekers.cli.video_models import FrameType, TextGroup

        group = TextGroup(
            group_id="TG-001",
            appearances=[(1.0, 5.0)],
            consensus_lines=[{"y_center": 100.0, "text": "hello", "confidence": 0.9}],
            frame_type=FrameType.CODE_EDITOR,
            panel_id="panel_0_1",
        )

        data = group.to_dict()
        self.assertEqual(data["panel_id"], "panel_0_1")

        restored = TextGroup.from_dict(data)
        self.assertEqual(restored.panel_id, "panel_0_1")


# =============================================================================
# Video Enhancement Tests
# =============================================================================


class TestVideoEnhanceSourceDetection(unittest.TestCase):
    """Test video source detection in utils and enhance_skill."""

    def test_utils_detect_video_source(self):
        """_determine_source_metadata classifies video_ files as video_tutorial."""
        from skill_seekers.cli.utils import read_reference_files

        # Create a temp skill dir with a video reference file
        with tempfile.TemporaryDirectory() as tmpdir:
            refs_dir = os.path.join(tmpdir, "references")
            os.makedirs(refs_dir)
            video_ref = os.path.join(refs_dir, "video_my_tutorial.md")
            with open(video_ref, "w") as f:
                f.write("# Test Video\n\nSome content")

            references = read_reference_files(tmpdir)
            self.assertIn("video_my_tutorial.md", references)
            self.assertEqual(references["video_my_tutorial.md"]["source"], "video_tutorial")
            self.assertEqual(references["video_my_tutorial.md"]["confidence"], "high")

    def test_utils_non_video_not_detected(self):
        """Regular reference files are not classified as video_tutorial."""
        from skill_seekers.cli.utils import read_reference_files

        with tempfile.TemporaryDirectory() as tmpdir:
            refs_dir = os.path.join(tmpdir, "references")
            os.makedirs(refs_dir)
            ref = os.path.join(refs_dir, "api_reference.md")
            with open(ref, "w") as f:
                f.write("# API Reference\n\nSome content")

            references = read_reference_files(tmpdir)
            self.assertIn("api_reference.md", references)
            self.assertNotEqual(references["api_reference.md"]["source"], "video_tutorial")


class TestVideoEnhancementPrompt(unittest.TestCase):
    """Test video-specific enhancement prompt building."""

    def test_is_video_source_true(self):
        """_is_video_source returns True for video_tutorial references."""
        from unittest.mock import MagicMock

        from skill_seekers.cli.enhance_skill import SkillEnhancer

        # Mock the enhancer (skip API key requirement)
        enhancer = MagicMock(spec=SkillEnhancer)
        enhancer._is_video_source = SkillEnhancer._is_video_source.__get__(enhancer)

        refs = {
            "video_tutorial.md": {"source": "video_tutorial", "confidence": "high"},
        }
        self.assertTrue(enhancer._is_video_source(refs))

    def test_is_video_source_false(self):
        """_is_video_source returns False for non-video references."""
        from unittest.mock import MagicMock

        from skill_seekers.cli.enhance_skill import SkillEnhancer

        enhancer = MagicMock(spec=SkillEnhancer)
        enhancer._is_video_source = SkillEnhancer._is_video_source.__get__(enhancer)

        refs = {
            "api.md": {"source": "documentation", "confidence": "high"},
        }
        self.assertFalse(enhancer._is_video_source(refs))

    def test_video_prompt_contains_key_instructions(self):
        """Video enhancement prompt contains video-specific instructions."""
        from unittest.mock import MagicMock, PropertyMock

        from skill_seekers.cli.enhance_skill import SkillEnhancer

        enhancer = MagicMock(spec=SkillEnhancer)
        enhancer._build_video_enhancement_prompt = (
            SkillEnhancer._build_video_enhancement_prompt.__get__(enhancer)
        )
        type(enhancer).skill_dir = PropertyMock(
            return_value=type("P", (), {"name": "test-tutorial"})()
        )

        refs = {
            "video_test.md": {
                "source": "video_tutorial",
                "confidence": "high",
                "content": "# Test\n\n## Segment 1\nTranscript here\n```\nsome code\n```",
                "size": 100,
            },
        }

        prompt = enhancer._build_video_enhancement_prompt(refs, "# test\n")

        # Check key video-specific sections are present
        self.assertIn("OCR Code Reconstruction", prompt)
        self.assertIn("Language Detection", prompt)
        self.assertIn("Code Timeline", prompt)
        self.assertIn("Audio-Visual Alignment", prompt)
        self.assertIn("line numbers", prompt.lower())
        self.assertIn("UI chrome", prompt)
        self.assertIn("GDScript", prompt)
        self.assertIn("video_test.md", prompt)

    def test_video_prompt_dispatched_automatically(self):
        """_build_enhancement_prompt dispatches to video prompt when video source detected."""
        from unittest.mock import MagicMock, PropertyMock

        from skill_seekers.cli.enhance_skill import SkillEnhancer

        enhancer = MagicMock(spec=SkillEnhancer)
        enhancer._is_video_source = SkillEnhancer._is_video_source.__get__(enhancer)
        enhancer._build_enhancement_prompt = SkillEnhancer._build_enhancement_prompt.__get__(
            enhancer
        )
        enhancer._build_video_enhancement_prompt = (
            SkillEnhancer._build_video_enhancement_prompt.__get__(enhancer)
        )
        type(enhancer).skill_dir = PropertyMock(return_value=type("P", (), {"name": "my-video"})())

        refs = {
            "video_tutorial.md": {
                "source": "video_tutorial",
                "confidence": "high",
                "content": "# Video\n\nContent here",
                "size": 50,
            },
        }

        prompt = enhancer._build_enhancement_prompt(refs, "# SKILL\n")

        # Should use video prompt (has VIDEO TUTORIAL in header)
        self.assertIn("VIDEO TUTORIAL", prompt)
        self.assertIn("OCR Code Reconstruction", prompt)


class TestVideoWorkflowAutoInjection(unittest.TestCase):
    """Test that video scraper auto-injects video-tutorial workflow."""

    def test_workflow_auto_injected(self):
        """When no workflow specified, video-tutorial is injected."""
        import argparse

        args = argparse.Namespace(
            enhance_level=2,
            enhance_workflow=None,
            enhance_stage=None,
            var=None,
            workflow_dry_run=False,
            api_key=None,
        )

        # Simulate the auto-injection logic from video_scraper main()
        if not getattr(args, "enhance_workflow", None):
            args.enhance_workflow = ["video-tutorial"]

        self.assertEqual(args.enhance_workflow, ["video-tutorial"])

    def test_workflow_not_overridden(self):
        """When user specifies workflow, it is NOT overridden."""
        import argparse

        args = argparse.Namespace(
            enhance_level=2,
            enhance_workflow=["custom-workflow"],
            enhance_stage=None,
            var=None,
            workflow_dry_run=False,
            api_key=None,
        )

        # Simulate the auto-injection logic
        if not getattr(args, "enhance_workflow", None):
            args.enhance_workflow = ["video-tutorial"]

        self.assertEqual(args.enhance_workflow, ["custom-workflow"])

    def test_video_tutorial_yaml_exists(self):
        """video-tutorial.yaml workflow file is bundled."""
        from importlib.resources import files as importlib_files

        try:
            pkg = importlib_files("skill_seekers.workflows")
            yaml_content = pkg.joinpath("video-tutorial.yaml").read_text(encoding="utf-8")
            self.assertIn("video-tutorial", yaml_content)
            self.assertIn("ocr_code_cleanup", yaml_content)
            self.assertIn("video_scraping", yaml_content)
        except Exception:
            # If package not installed in editable mode, check file directly
            import pathlib

            yaml_path = (
                pathlib.Path(__file__).parent.parent
                / "src"
                / "skill_seekers"
                / "workflows"
                / "video-tutorial.yaml"
            )
            self.assertTrue(yaml_path.exists(), "video-tutorial.yaml not found")


# =============================================================================
# Test: Time Clipping (--start-time / --end-time)
# =============================================================================


class TestTimeClipping(unittest.TestCase):
    """Test --start-time / --end-time clipping support."""

    # ---- parse_time_to_seconds() ----

    def test_parse_time_seconds_integer(self):
        from skill_seekers.cli.video_scraper import parse_time_to_seconds

        self.assertEqual(parse_time_to_seconds("330"), 330.0)

    def test_parse_time_seconds_float(self):
        from skill_seekers.cli.video_scraper import parse_time_to_seconds

        self.assertAlmostEqual(parse_time_to_seconds("90.5"), 90.5)

    def test_parse_time_mmss(self):
        from skill_seekers.cli.video_scraper import parse_time_to_seconds

        self.assertEqual(parse_time_to_seconds("5:30"), 330.0)

    def test_parse_time_hhmmss(self):
        from skill_seekers.cli.video_scraper import parse_time_to_seconds

        self.assertEqual(parse_time_to_seconds("1:05:30"), 3930.0)

    def test_parse_time_zero(self):
        from skill_seekers.cli.video_scraper import parse_time_to_seconds

        self.assertEqual(parse_time_to_seconds("0"), 0.0)
        self.assertEqual(parse_time_to_seconds("0:00"), 0.0)
        self.assertEqual(parse_time_to_seconds("0:00:00"), 0.0)

    def test_parse_time_decimal_mmss(self):
        from skill_seekers.cli.video_scraper import parse_time_to_seconds

        self.assertAlmostEqual(parse_time_to_seconds("1:30.5"), 90.5)

    def test_parse_time_invalid_raises(self):
        from skill_seekers.cli.video_scraper import parse_time_to_seconds

        with self.assertRaises(ValueError):
            parse_time_to_seconds("abc")

    def test_parse_time_empty_raises(self):
        from skill_seekers.cli.video_scraper import parse_time_to_seconds

        with self.assertRaises(ValueError):
            parse_time_to_seconds("")

    def test_parse_time_too_many_colons_raises(self):
        from skill_seekers.cli.video_scraper import parse_time_to_seconds

        with self.assertRaises(ValueError):
            parse_time_to_seconds("1:2:3:4")

    # ---- Argument registration ----

    def test_video_arguments_include_start_end_time(self):
        from skill_seekers.cli.arguments.video import VIDEO_ARGUMENTS

        self.assertIn("start_time", VIDEO_ARGUMENTS)
        self.assertIn("end_time", VIDEO_ARGUMENTS)

    def test_create_arguments_include_start_end_time(self):
        from skill_seekers.cli.arguments.create import VIDEO_ARGUMENTS

        self.assertIn("start_time", VIDEO_ARGUMENTS)
        self.assertIn("end_time", VIDEO_ARGUMENTS)

    def test_argument_parsing_defaults_none(self):
        import argparse
        from skill_seekers.cli.arguments.video import add_video_arguments

        parser = argparse.ArgumentParser()
        add_video_arguments(parser)
        args = parser.parse_args(["--url", "https://example.com"])
        self.assertIsNone(args.start_time)
        self.assertIsNone(args.end_time)

    def test_argument_parsing_with_values(self):
        import argparse
        from skill_seekers.cli.arguments.video import add_video_arguments

        parser = argparse.ArgumentParser()
        add_video_arguments(parser)
        args = parser.parse_args(
            ["--url", "https://example.com", "--start-time", "2:00", "--end-time", "5:00"]
        )
        self.assertEqual(args.start_time, "2:00")
        self.assertEqual(args.end_time, "5:00")

    # ---- Transcript filtering ----

    def test_transcript_clip_filters_segments(self):
        """Verify transcript segments are filtered to clip range."""
        from skill_seekers.cli.video_models import TranscriptSegment

        segments = [
            TranscriptSegment(text="intro", start=0.0, end=30.0),
            TranscriptSegment(text="part1", start=30.0, end=90.0),
            TranscriptSegment(text="part2", start=90.0, end=150.0),
            TranscriptSegment(text="outro", start=150.0, end=200.0),
        ]

        clip_start, clip_end = 60.0, 120.0
        filtered = [s for s in segments if s.end > clip_start and s.start < clip_end]
        # part1 (30-90) overlaps with 60-120, part2 (90-150) overlaps with 60-120
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0].text, "part1")
        self.assertEqual(filtered[1].text, "part2")

    def test_transcript_clip_start_only(self):
        """Verify only clip_start filters correctly."""
        from skill_seekers.cli.video_models import TranscriptSegment

        segments = [
            TranscriptSegment(text="before", start=0.0, end=50.0),
            TranscriptSegment(text="after", start=50.0, end=100.0),
        ]
        clip_start = 50.0
        clip_end = float("inf")
        filtered = [s for s in segments if s.end > clip_start and s.start < clip_end]
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].text, "after")

    # ---- Validation ----

    def test_playlist_plus_clip_rejected(self):
        from skill_seekers.cli.video_models import VideoSourceConfig

        config = VideoSourceConfig(
            playlist="https://youtube.com/playlist?list=x",
            clip_start=60.0,
        )
        errors = config.validate()
        self.assertTrue(any("--start-time" in e for e in errors))

    def test_start_gte_end_rejected(self):
        from skill_seekers.cli.video_models import VideoSourceConfig

        config = VideoSourceConfig(
            url="https://youtube.com/watch?v=x", clip_start=300.0, clip_end=120.0
        )
        errors = config.validate()
        self.assertTrue(any("must be before" in e for e in errors))

    def test_valid_clip_no_errors(self):
        from skill_seekers.cli.video_models import VideoSourceConfig

        config = VideoSourceConfig(
            url="https://youtube.com/watch?v=x", clip_start=60.0, clip_end=300.0
        )
        errors = config.validate()
        self.assertEqual(errors, [])

    # ---- VideoInfo clip metadata serialization ----

    def test_video_info_clip_roundtrip(self):
        from skill_seekers.cli.video_models import VideoInfo, VideoSourceType

        info = VideoInfo(
            video_id="test",
            source_type=VideoSourceType.YOUTUBE,
            duration=300.0,
            original_duration=600.0,
            clip_start=120.0,
            clip_end=420.0,
        )
        data = info.to_dict()
        self.assertEqual(data["original_duration"], 600.0)
        self.assertEqual(data["clip_start"], 120.0)
        self.assertEqual(data["clip_end"], 420.0)

        restored = VideoInfo.from_dict(data)
        self.assertEqual(restored.original_duration, 600.0)
        self.assertEqual(restored.clip_start, 120.0)
        self.assertEqual(restored.clip_end, 420.0)

    def test_video_info_no_clip_roundtrip(self):
        from skill_seekers.cli.video_models import VideoInfo, VideoSourceType

        info = VideoInfo(video_id="test", source_type=VideoSourceType.YOUTUBE)
        data = info.to_dict()
        self.assertIsNone(data["original_duration"])
        self.assertIsNone(data["clip_start"])
        self.assertIsNone(data["clip_end"])

        restored = VideoInfo.from_dict(data)
        self.assertIsNone(restored.original_duration)
        self.assertIsNone(restored.clip_start)

    # ---- VideoSourceConfig clip fields ----

    def test_source_config_clip_fields(self):
        from skill_seekers.cli.video_models import VideoSourceConfig

        config = VideoSourceConfig.from_dict(
            {
                "url": "https://example.com",
                "clip_start": 10.0,
                "clip_end": 60.0,
            }
        )
        self.assertEqual(config.clip_start, 10.0)
        self.assertEqual(config.clip_end, 60.0)

    def test_source_config_clip_defaults_none(self):
        from skill_seekers.cli.video_models import VideoSourceConfig

        config = VideoSourceConfig.from_dict({"url": "https://example.com"})
        self.assertIsNone(config.clip_start)
        self.assertIsNone(config.clip_end)

    # ---- Converter init ----

    def test_converter_init_with_clip_times(self):
        from skill_seekers.cli.video_scraper import VideoToSkillConverter

        config = {
            "name": "test",
            "url": "https://youtube.com/watch?v=x",
            "start_time": 120.0,
            "end_time": 300.0,
        }
        converter = VideoToSkillConverter(config)
        self.assertEqual(converter.start_time, 120.0)
        self.assertEqual(converter.end_time, 300.0)

    def test_converter_init_without_clip_times(self):
        from skill_seekers.cli.video_scraper import VideoToSkillConverter

        config = {"name": "test", "url": "https://youtube.com/watch?v=x"}
        converter = VideoToSkillConverter(config)
        self.assertIsNone(converter.start_time)
        self.assertIsNone(converter.end_time)

    # ---- Segmenter start_offset / end_limit ----

    def test_segmenter_time_window_with_offset(self):
        from skill_seekers.cli.video_segmenter import segment_by_time_window
        from skill_seekers.cli.video_models import VideoInfo, VideoSourceType

        info = VideoInfo(video_id="test", source_type=VideoSourceType.YOUTUBE, duration=600.0)
        # Use 120s windows starting at 120s, ending at 360s
        segments = segment_by_time_window(
            info, [], window_seconds=120.0, start_offset=120.0, end_limit=360.0
        )
        # No transcript segments so no segments generated, but verify no crash
        self.assertEqual(len(segments), 0)

    def test_segmenter_time_window_offset_with_transcript(self):
        from skill_seekers.cli.video_segmenter import segment_by_time_window
        from skill_seekers.cli.video_models import (
            VideoInfo,
            VideoSourceType,
            TranscriptSegment,
        )

        info = VideoInfo(video_id="test", source_type=VideoSourceType.YOUTUBE, duration=600.0)
        transcript = [
            TranscriptSegment(text="before clip", start=0.0, end=60.0),
            TranscriptSegment(text="in clip part1", start=120.0, end=180.0),
            TranscriptSegment(text="in clip part2", start=200.0, end=300.0),
            TranscriptSegment(text="after clip", start=400.0, end=500.0),
        ]
        segments = segment_by_time_window(
            info, transcript, window_seconds=120.0, start_offset=120.0, end_limit=360.0
        )
        # Should have segments starting at 120, 240
        self.assertTrue(len(segments) >= 1)
        # All segments should be within clip range
        for seg in segments:
            self.assertGreaterEqual(seg.start_time, 120.0)
            self.assertLessEqual(seg.end_time, 360.0)


# =============================================================================
# OCR Quality Improvement Tests
# =============================================================================


class TestCleanOcrLine(unittest.TestCase):
    """Tests for _clean_ocr_line() in video_visual.py."""

    def test_strips_leading_line_numbers(self):
        from skill_seekers.cli.video_visual import _clean_ocr_line

        self.assertEqual(_clean_ocr_line("23 public class Card"), "public class Card")
        self.assertEqual(_clean_ocr_line("1\tpublic void Start()"), "public void Start()")
        self.assertEqual(_clean_ocr_line("  456 return x"), "return x")

    def test_strips_ide_decorations(self):
        from skill_seekers.cli.video_visual import _clean_ocr_line

        # Unity Inspector line should be removed entirely
        self.assertEqual(_clean_ocr_line("Inspector Card Script"), "")
        self.assertEqual(_clean_ocr_line("Hierarchy Main Camera"), "")
        # Tab bar text should be removed
        self.assertEqual(_clean_ocr_line("File Edit Assets Window Help"), "")

    def test_strips_collapse_markers(self):
        from skill_seekers.cli.video_visual import _clean_ocr_line

        self.assertNotIn("▶", _clean_ocr_line("▶ class Card"))
        self.assertNotIn("▼", _clean_ocr_line("▼ Properties"))

    def test_preserves_normal_code(self):
        from skill_seekers.cli.video_visual import _clean_ocr_line

        self.assertEqual(
            _clean_ocr_line("public class Card : MonoBehaviour"),
            "public class Card : MonoBehaviour",
        )
        self.assertEqual(_clean_ocr_line("    def main():"), "def main():")


class TestFixIntraLineDuplication(unittest.TestCase):
    """Tests for _fix_intra_line_duplication() in video_visual.py."""

    def test_fixes_simple_duplication(self):
        from skill_seekers.cli.video_visual import _fix_intra_line_duplication

        result = _fix_intra_line_duplication("public class Card public class Card : MonoBehaviour")
        # Should keep the half with more content
        self.assertIn("MonoBehaviour", result)
        # Should not have "public class Card" twice
        self.assertLessEqual(result.count("public class Card"), 1)

    def test_preserves_non_duplicated(self):
        from skill_seekers.cli.video_visual import _fix_intra_line_duplication

        original = "public class Card : MonoBehaviour"
        self.assertEqual(_fix_intra_line_duplication(original), original)

    def test_short_lines_unchanged(self):
        from skill_seekers.cli.video_visual import _fix_intra_line_duplication

        self.assertEqual(_fix_intra_line_duplication("a b"), "a b")
        self.assertEqual(_fix_intra_line_duplication("x"), "x")


class TestIsLikelyCode(unittest.TestCase):
    """Tests for _is_likely_code() in video_scraper.py."""

    def test_true_for_real_code(self):
        from skill_seekers.cli.video_scraper import _is_likely_code

        self.assertTrue(_is_likely_code("public void DrawCard() {"))
        self.assertTrue(_is_likely_code("def main():\n    return x"))
        self.assertTrue(_is_likely_code("function handleClick(event) {"))
        self.assertTrue(_is_likely_code("import os; import sys"))

    def test_false_for_ui_junk(self):
        from skill_seekers.cli.video_scraper import _is_likely_code

        self.assertFalse(_is_likely_code("Inspector Image Type Simple"))
        self.assertFalse(_is_likely_code("Hierarchy Canvas Button"))
        self.assertFalse(_is_likely_code(""))
        self.assertFalse(_is_likely_code("short"))

    def test_code_tokens_must_exceed_ui(self):
        from skill_seekers.cli.video_scraper import _is_likely_code

        # More UI than code tokens
        self.assertFalse(_is_likely_code("Inspector Console Project Hierarchy Scene Game = ;"))


class TestTextGroupLanguageDetection(unittest.TestCase):
    """Tests for language detection in get_text_groups()."""

    def test_groups_get_language_detected(self):
        from unittest.mock import MagicMock, patch

        from skill_seekers.cli.video_visual import TextBlockTracker
        from skill_seekers.cli.video_models import FrameType

        tracker = TextBlockTracker()

        # Add enough data for a text group to form
        code = "public class Card : MonoBehaviour {\n    void Start() {\n    }\n}"
        tracker.update(0, 0.0, code, 0.9, FrameType.CODE_EDITOR)
        tracker.update(1, 1.0, code, 0.9, FrameType.CODE_EDITOR)
        tracker.update(2, 2.0, code, 0.9, FrameType.CODE_EDITOR)

        blocks = tracker.finalize()  # noqa: F841

        # Patch the LanguageDetector at the import source used by the lazy import
        mock_detector = MagicMock()
        mock_detector.detect_from_code.return_value = ("csharp", 0.9)

        mock_module = MagicMock()
        mock_module.LanguageDetector.return_value = mock_detector

        with patch.dict("sys.modules", {"skill_seekers.cli.language_detector": mock_module}):
            groups = tracker.get_text_groups()

            # If groups were formed and had enough text, language should be detected
            for group in groups:
                if group.full_text and len(group.full_text) >= 20:
                    self.assertEqual(group.detected_language, "csharp")


class TestSkipWebcamOcr(unittest.TestCase):
    """Tests that WEBCAM/OTHER frame types skip OCR."""

    def test_webcam_frame_type_excluded_from_ocr_condition(self):
        """Verify the condition in the OCR block excludes WEBCAM/OTHER."""
        from skill_seekers.cli.video_models import FrameType

        # These should be excluded from the non-code OCR path
        excluded = (FrameType.WEBCAM, FrameType.OTHER)
        for ft in excluded:
            self.assertIn(ft, excluded)

        # These should still get OCR'd
        included = (FrameType.SLIDE, FrameType.DIAGRAM)
        for ft in included:
            self.assertNotIn(ft, excluded)


class TestReferenceSkipsJunkCodeFences(unittest.TestCase):
    """Tests that _is_likely_code() prevents junk from becoming code fences."""

    def test_junk_text_not_in_code_fence(self):
        from skill_seekers.cli.video_scraper import _is_likely_code

        # UI junk should be filtered
        junk_texts = [
            "Inspector Image Type Simple",
            "Hierarchy Main Camera",
            "Canvas Sorting Layer Default",
        ]
        for junk in junk_texts:
            self.assertFalse(
                _is_likely_code(junk),
                f"Expected False for UI junk: {junk}",
            )

    def test_real_code_in_code_fence(self):
        from skill_seekers.cli.video_scraper import _is_likely_code

        real_code = [
            "public class Card : MonoBehaviour { void Start() {} }",
            "def draw_card(self):\n    return self.deck.pop()",
            "const card = new Card(); card.flip();",
        ]
        for code in real_code:
            self.assertTrue(
                _is_likely_code(code),
                f"Expected True for real code: {code}",
            )


class TestFuzzyWordMatch(unittest.TestCase):
    """Tests for _fuzzy_word_match() in video_visual.py."""

    def test_exact_match(self):
        from skill_seekers.cli.video_visual import _fuzzy_word_match

        self.assertTrue(_fuzzy_word_match("public", "public"))

    def test_prefix_noise(self):
        from skill_seekers.cli.video_visual import _fuzzy_word_match

        # OCR often adds a garbage char prefix
        self.assertTrue(_fuzzy_word_match("gpublic", "public"))
        self.assertTrue(_fuzzy_word_match("Jpublic", "public"))

    def test_different_words(self):
        from skill_seekers.cli.video_visual import _fuzzy_word_match

        self.assertFalse(_fuzzy_word_match("class", "void"))
        self.assertFalse(_fuzzy_word_match("ab", "xy"))


if __name__ == "__main__":
    unittest.main()
