# Video Source — System Integration

**Date:** February 27, 2026
**Document:** 04 of 07
**Status:** Planning

---

## Table of Contents

1. [CLI Integration](#cli-integration)
2. [Source Detection](#source-detection)
3. [Unified Config Integration](#unified-config-integration)
4. [Unified Scraper Integration](#unified-scraper-integration)
5. [Create Command Integration](#create-command-integration)
6. [Parser & Arguments](#parser--arguments)
7. [MCP Tool Integration](#mcp-tool-integration)
8. [Enhancement Integration](#enhancement-integration)
9. [File Map (New & Modified)](#file-map-new--modified-files)

---

## CLI Integration

### New Subcommand: `video`

```bash
# Dedicated video scraping command
skill-seekers video --url https://youtube.com/watch?v=abc123
skill-seekers video --playlist https://youtube.com/playlist?list=PLxxx
skill-seekers video --channel https://youtube.com/@channelname
skill-seekers video --path ./recording.mp4
skill-seekers video --directory ./recordings/

# With options
skill-seekers video --url <URL> \
    --output output/react-videos/ \
    --visual \
    --whisper-model large-v3 \
    --max-videos 20 \
    --languages en \
    --categories '{"hooks": ["useState", "useEffect"]}' \
    --enhance-level 2
```

### Auto-Detection via `create` Command

```bash
# These all auto-detect as video sources
skill-seekers create https://youtube.com/watch?v=abc123
skill-seekers create https://youtu.be/abc123
skill-seekers create https://youtube.com/playlist?list=PLxxx
skill-seekers create https://youtube.com/@channelname
skill-seekers create https://vimeo.com/123456789
skill-seekers create ./tutorial.mp4
skill-seekers create ./recordings/                # Directory of videos

# With universal flags
skill-seekers create https://youtube.com/watch?v=abc123 --visual -p comprehensive
skill-seekers create ./tutorial.mp4 --enhance-level 2 --dry-run
```

### Registration in main.py

```python
# In src/skill_seekers/cli/main.py - COMMAND_MODULES dict

COMMAND_MODULES = {
    # ... existing commands ...
    'video': 'skill_seekers.cli.video_scraper',
    # ... rest of commands ...
}
```

---

## Source Detection

### Changes to `source_detector.py`

```python
# New patterns to add:

class SourceDetector:
    # Existing patterns...

    # NEW: Video URL patterns
    YOUTUBE_VIDEO_PATTERN = re.compile(
        r'(?:https?://)?(?:www\.)?'
        r'(?:youtube\.com/watch\?v=|youtu\.be/)'
        r'([a-zA-Z0-9_-]{11})'
    )
    YOUTUBE_PLAYLIST_PATTERN = re.compile(
        r'(?:https?://)?(?:www\.)?'
        r'youtube\.com/playlist\?list=([a-zA-Z0-9_-]+)'
    )
    YOUTUBE_CHANNEL_PATTERN = re.compile(
        r'(?:https?://)?(?:www\.)?'
        r'youtube\.com/(?:@|c/|channel/|user/)([a-zA-Z0-9_.-]+)'
    )
    VIMEO_PATTERN = re.compile(
        r'(?:https?://)?(?:www\.)?vimeo\.com/(\d+)'
    )

    # Video file extensions
    VIDEO_EXTENSIONS = {
        '.mp4', '.mkv', '.webm', '.avi', '.mov',
        '.flv', '.ts', '.wmv', '.m4v', '.ogv',
    }

    @classmethod
    def detect(cls, source: str) -> SourceInfo:
        """Updated detection order:
        1. .json (config)
        2. .pdf
        3. .docx
        4. Video file extensions (.mp4, .mkv, .webm, etc.)  ← NEW
        5. Directory (may contain videos)
        6. YouTube/Vimeo URL patterns  ← NEW
        7. GitHub patterns
        8. Web URL
        9. Domain inference
        """
        # 1. Config file
        if source.endswith('.json'):
            return cls._detect_config(source)

        # 2. PDF file
        if source.endswith('.pdf'):
            return cls._detect_pdf(source)

        # 3. Word document
        if source.endswith('.docx'):
            return cls._detect_word(source)

        # 4. NEW: Video file
        ext = os.path.splitext(source)[1].lower()
        if ext in cls.VIDEO_EXTENSIONS:
            return cls._detect_video_file(source)

        # 5. Directory
        if os.path.isdir(source):
            # Check if directory contains mostly video files
            if cls._is_video_directory(source):
                return cls._detect_video_directory(source)
            return cls._detect_local(source)

        # 6. NEW: Video URL patterns (before general web URL)
        video_info = cls._detect_video_url(source)
        if video_info:
            return video_info

        # 7. GitHub patterns
        github_info = cls._detect_github(source)
        if github_info:
            return github_info

        # 8. Web URL
        if source.startswith('http://') or source.startswith('https://'):
            return cls._detect_web(source)

        # 9. Domain inference
        if '.' in source and not source.startswith('/'):
            return cls._detect_web(f'https://{source}')

        raise ValueError(
            f"Cannot determine source type for: {source}\n\n"
            "Examples:\n"
            "  Web:      skill-seekers create https://docs.react.dev/\n"
            "  GitHub:   skill-seekers create facebook/react\n"
            "  Local:    skill-seekers create ./my-project\n"
            "  PDF:      skill-seekers create tutorial.pdf\n"
            "  DOCX:     skill-seekers create document.docx\n"
            "  Video:    skill-seekers create https://youtube.com/watch?v=xxx\n"  # NEW
            "  Playlist: skill-seekers create https://youtube.com/playlist?list=xxx\n"  # NEW
            "  Config:   skill-seekers create configs/react.json"
        )

    @classmethod
    def _detect_video_url(cls, source: str) -> SourceInfo | None:
        """Detect YouTube or Vimeo video URL."""

        # YouTube video
        match = cls.YOUTUBE_VIDEO_PATTERN.search(source)
        if match:
            video_id = match.group(1)
            return SourceInfo(
                type='video',
                parsed={
                    'video_source': 'youtube_video',
                    'video_id': video_id,
                    'url': f'https://www.youtube.com/watch?v={video_id}',
                },
                suggested_name=f'video-{video_id}',
                raw_input=source,
            )

        # YouTube playlist
        match = cls.YOUTUBE_PLAYLIST_PATTERN.search(source)
        if match:
            playlist_id = match.group(1)
            return SourceInfo(
                type='video',
                parsed={
                    'video_source': 'youtube_playlist',
                    'playlist_id': playlist_id,
                    'url': f'https://www.youtube.com/playlist?list={playlist_id}',
                },
                suggested_name=f'playlist-{playlist_id[:12]}',
                raw_input=source,
            )

        # YouTube channel
        match = cls.YOUTUBE_CHANNEL_PATTERN.search(source)
        if match:
            channel_name = match.group(1)
            return SourceInfo(
                type='video',
                parsed={
                    'video_source': 'youtube_channel',
                    'channel': channel_name,
                    'url': source if source.startswith('http') else f'https://www.youtube.com/@{channel_name}',
                },
                suggested_name=channel_name.lstrip('@'),
                raw_input=source,
            )

        # Vimeo
        match = cls.VIMEO_PATTERN.search(source)
        if match:
            video_id = match.group(1)
            return SourceInfo(
                type='video',
                parsed={
                    'video_source': 'vimeo',
                    'video_id': video_id,
                    'url': f'https://vimeo.com/{video_id}',
                },
                suggested_name=f'vimeo-{video_id}',
                raw_input=source,
            )

        return None

    @classmethod
    def _detect_video_file(cls, source: str) -> SourceInfo:
        """Detect local video file."""
        name = os.path.splitext(os.path.basename(source))[0]
        return SourceInfo(
            type='video',
            parsed={
                'video_source': 'local_file',
                'file_path': os.path.abspath(source),
            },
            suggested_name=name,
            raw_input=source,
        )

    @classmethod
    def _detect_video_directory(cls, source: str) -> SourceInfo:
        """Detect directory containing video files."""
        directory = os.path.abspath(source)
        name = os.path.basename(directory)
        return SourceInfo(
            type='video',
            parsed={
                'video_source': 'local_directory',
                'directory': directory,
            },
            suggested_name=name,
            raw_input=source,
        )

    @classmethod
    def _is_video_directory(cls, path: str) -> bool:
        """Check if a directory contains mostly video files.

        Returns True if >50% of files are video files.
        Used to distinguish video directories from code directories.
        """
        total = 0
        video = 0
        for f in os.listdir(path):
            if os.path.isfile(os.path.join(path, f)):
                total += 1
                ext = os.path.splitext(f)[1].lower()
                if ext in cls.VIDEO_EXTENSIONS:
                    video += 1
        return total > 0 and (video / total) > 0.5

    @classmethod
    def validate_source(cls, source_info: SourceInfo) -> None:
        """Updated to include video validation."""
        # ... existing validation ...

        if source_info.type == 'video':
            video_source = source_info.parsed.get('video_source')
            if video_source == 'local_file':
                file_path = source_info.parsed['file_path']
                if not os.path.exists(file_path):
                    raise ValueError(f"Video file does not exist: {file_path}")
            elif video_source == 'local_directory':
                directory = source_info.parsed['directory']
                if not os.path.exists(directory):
                    raise ValueError(f"Video directory does not exist: {directory}")
            # For online sources, validation happens during scraping
```

---

## Unified Config Integration

### Updated `scraped_data` dict in `unified_scraper.py`

```python
# In UnifiedScraper.__init__():
self.scraped_data = {
    "documentation": [],
    "github": [],
    "pdf": [],
    "word": [],
    "local": [],
    "video": [],      # ← NEW
}
```

### Video Source Processing in Unified Scraper

```python
def _scrape_video_source(self, source: dict, source_index: int) -> dict:
    """Process a video source from unified config.

    Args:
        source: Video source config dict from unified JSON
        source_index: Index for unique naming

    Returns:
        Dict with scraping results and metadata
    """
    from skill_seekers.cli.video_scraper import VideoScraper
    from skill_seekers.cli.video_models import VideoSourceConfig

    config = VideoSourceConfig.from_dict(source)
    scraper = VideoScraper(config=config, output_dir=self.output_dir)

    result = scraper.scrape()

    return {
        'source_type': 'video',
        'source_name': source.get('name', f'video_{source_index}'),
        'weight': source.get('weight', 0.2),
        'result': result,
        'video_count': len(result.videos),
        'segment_count': result.total_segments,
        'categories': result.categories,
    }
```

### Example Unified Config with Video

```json
{
    "name": "react-complete",
    "description": "React 19 - Documentation + Code + Video Tutorials",
    "output_dir": "output/react-complete/",

    "sources": [
        {
            "type": "documentation",
            "url": "https://react.dev/",
            "name": "official_docs",
            "weight": 0.4,
            "selectors": {
                "main_content": "article",
                "code_blocks": "pre code"
            },
            "categories": {
                "getting_started": ["learn", "quick-start"],
                "hooks": ["hooks", "use-state", "use-effect"],
                "api": ["reference", "api"]
            }
        },
        {
            "type": "github",
            "repo": "facebook/react",
            "name": "source_code",
            "weight": 0.3,
            "analysis_depth": "deep"
        },
        {
            "type": "video",
            "playlist": "https://www.youtube.com/playlist?list=PLreactplaylist",
            "name": "official_tutorials",
            "weight": 0.2,
            "max_videos": 15,
            "visual_extraction": true,
            "languages": ["en"],
            "categories": {
                "getting_started": ["intro", "quickstart", "setup"],
                "hooks": ["useState", "useEffect", "hooks"],
                "advanced": ["suspense", "concurrent", "server"]
            }
        },
        {
            "type": "video",
            "url": "https://www.youtube.com/watch?v=abc123def45",
            "name": "react_conf_keynote",
            "weight": 0.1,
            "visual_extraction": false
        }
    ],

    "merge_strategy": "unified",
    "conflict_resolution": "docs_first",

    "enhancement": {
        "enabled": true,
        "level": 2
    }
}
```

---

## Create Command Integration

### Changes to Create Command Routing

```python
# In src/skill_seekers/cli/create_command.py (or equivalent in main.py)

def route_source(source_info: SourceInfo, args: argparse.Namespace):
    """Route detected source to appropriate scraper."""

    if source_info.type == 'web':
        return _route_web(source_info, args)
    elif source_info.type == 'github':
        return _route_github(source_info, args)
    elif source_info.type == 'local':
        return _route_local(source_info, args)
    elif source_info.type == 'pdf':
        return _route_pdf(source_info, args)
    elif source_info.type == 'word':
        return _route_word(source_info, args)
    elif source_info.type == 'video':          # ← NEW
        return _route_video(source_info, args)
    elif source_info.type == 'config':
        return _route_config(source_info, args)


def _route_video(source_info: SourceInfo, args: argparse.Namespace):
    """Route video source to video scraper."""
    from skill_seekers.cli.video_scraper import VideoScraper
    from skill_seekers.cli.video_models import VideoSourceConfig

    parsed = source_info.parsed

    # Build config from CLI args + parsed source info
    config_dict = {
        'name': getattr(args, 'name', None) or source_info.suggested_name,
        'visual_extraction': getattr(args, 'visual', False),
        'whisper_model': getattr(args, 'whisper_model', 'base'),
        'max_videos': getattr(args, 'max_videos', 50),
        'languages': getattr(args, 'languages', None),
    }

    # Set the appropriate source field
    video_source = parsed['video_source']
    if video_source in ('youtube_video', 'vimeo'):
        config_dict['url'] = parsed['url']
    elif video_source == 'youtube_playlist':
        config_dict['playlist'] = parsed['url']
    elif video_source == 'youtube_channel':
        config_dict['channel'] = parsed['url']
    elif video_source == 'local_file':
        config_dict['path'] = parsed['file_path']
    elif video_source == 'local_directory':
        config_dict['directory'] = parsed['directory']

    config = VideoSourceConfig.from_dict(config_dict)
    output_dir = getattr(args, 'output', None) or f'output/{config_dict["name"]}/'

    scraper = VideoScraper(config=config, output_dir=output_dir)

    if getattr(args, 'dry_run', False):
        scraper.dry_run()
        return

    result = scraper.scrape()
    scraper.generate_output(result)
```

---

## Parser & Arguments

### New Parser: `video_parser.py`

```python
# src/skill_seekers/cli/parsers/video_parser.py

from skill_seekers.cli.parsers.base import SubcommandParser


class VideoParser(SubcommandParser):
    """Parser for the video scraping command."""

    name = 'video'
    help = 'Extract knowledge from YouTube videos, playlists, channels, or local video files'
    description = (
        'Process video content into structured skill documentation.\n\n'
        'Supports YouTube (single video, playlist, channel), Vimeo, and local video files.\n'
        'Extracts transcripts, metadata, chapters, and optionally visual content (code, slides).'
    )

    def add_arguments(self, parser):
        # Source (mutually exclusive group)
        source = parser.add_mutually_exclusive_group(required=True)
        source.add_argument('--url', help='YouTube or Vimeo video URL')
        source.add_argument('--playlist', help='YouTube playlist URL')
        source.add_argument('--channel', help='YouTube channel URL')
        source.add_argument('--path', help='Local video file path')
        source.add_argument('--directory', help='Directory containing video files')

        # Add shared arguments (output, dry-run, verbose, etc.)
        from skill_seekers.cli.arguments.common import add_all_standard_arguments
        add_all_standard_arguments(parser)

        # Add video-specific arguments
        from skill_seekers.cli.arguments.video import add_video_arguments
        add_video_arguments(parser)
```

### New Arguments: `video.py`

```python
# src/skill_seekers/cli/arguments/video.py

VIDEO_ARGUMENTS = {
    # === Filtering ===
    "max_videos": {
        "flags": ("--max-videos",),
        "kwargs": {
            "type": int,
            "default": 50,
            "help": "Maximum number of videos to process (default: 50)",
        },
    },
    "min_duration": {
        "flags": ("--min-duration",),
        "kwargs": {
            "type": float,
            "default": 60.0,
            "help": "Minimum video duration in seconds (default: 60)",
        },
    },
    "max_duration": {
        "flags": ("--max-duration",),
        "kwargs": {
            "type": float,
            "default": 7200.0,
            "help": "Maximum video duration in seconds (default: 7200 = 2 hours)",
        },
    },
    "languages": {
        "flags": ("--languages",),
        "kwargs": {
            "nargs": "+",
            "default": None,
            "help": "Preferred transcript languages (default: all). Example: --languages en es",
        },
    },
    "min_views": {
        "flags": ("--min-views",),
        "kwargs": {
            "type": int,
            "default": None,
            "help": "Minimum view count filter (online videos only)",
        },
    },

    # === Extraction ===
    "visual": {
        "flags": ("--visual",),
        "kwargs": {
            "action": "store_true",
            "help": "Enable visual extraction (OCR on keyframes). Requires video-full dependencies.",
        },
    },
    "whisper_model": {
        "flags": ("--whisper-model",),
        "kwargs": {
            "default": "base",
            "choices": ["tiny", "base", "small", "medium", "large-v3", "large-v3-turbo"],
            "help": "Whisper model size for speech-to-text (default: base)",
        },
    },
    "whisper_device": {
        "flags": ("--whisper-device",),
        "kwargs": {
            "default": "auto",
            "choices": ["auto", "cpu", "cuda"],
            "help": "Device for Whisper inference (default: auto)",
        },
    },
    "ocr_languages": {
        "flags": ("--ocr-languages",),
        "kwargs": {
            "nargs": "+",
            "default": None,
            "help": "OCR languages for visual extraction (default: same as --languages)",
        },
    },

    # === Segmentation ===
    "segment_strategy": {
        "flags": ("--segment-strategy",),
        "kwargs": {
            "default": "hybrid",
            "choices": ["chapters", "semantic", "time_window", "scene_change", "hybrid"],
            "help": "How to segment video content (default: hybrid)",
        },
    },
    "segment_duration": {
        "flags": ("--segment-duration",),
        "kwargs": {
            "type": float,
            "default": 300.0,
            "help": "Target segment duration in seconds for time_window strategy (default: 300)",
        },
    },

    # === Local file options ===
    "file_patterns": {
        "flags": ("--file-patterns",),
        "kwargs": {
            "nargs": "+",
            "default": None,
            "help": "File patterns for directory scanning (default: *.mp4 *.mkv *.webm)",
        },
    },
    "recursive": {
        "flags": ("--recursive",),
        "kwargs": {
            "action": "store_true",
            "default": True,
            "help": "Recursively scan directories (default: True)",
        },
    },
    "no_recursive": {
        "flags": ("--no-recursive",),
        "kwargs": {
            "action": "store_true",
            "help": "Disable recursive directory scanning",
        },
    },
}


def add_video_arguments(parser):
    """Add all video-specific arguments to a parser."""
    for arg_name, arg_def in VIDEO_ARGUMENTS.items():
        parser.add_argument(*arg_def["flags"], **arg_def["kwargs"])
```

### Progressive Help for Create Command

```python
# In arguments/create.py - add video to help modes

# New help flag
"help_video": {
    "flags": ("--help-video",),
    "kwargs": {
        "action": "store_true",
        "help": "Show video-specific options",
    },
}

# VIDEO_ARGUMENTS added to create command's video help mode
# skill-seekers create --help-video
```

---

## MCP Tool Integration

### New MCP Tool: `scrape_video`

```python
# In src/skill_seekers/mcp/tools/scraping_tools.py

@mcp.tool()
def scrape_video(
    url: str | None = None,
    playlist: str | None = None,
    path: str | None = None,
    output_dir: str = "output/",
    visual: bool = False,
    max_videos: int = 20,
    whisper_model: str = "base",
) -> str:
    """Scrape and extract knowledge from video content.

    Supports YouTube videos, playlists, channels, and local video files.
    Extracts transcripts, metadata, chapters, and optionally visual content.

    Args:
        url: YouTube or Vimeo video URL
        playlist: YouTube playlist URL
        path: Local video file or directory path
        output_dir: Output directory for results
        visual: Enable visual extraction (OCR on keyframes)
        max_videos: Maximum videos to process (for playlists)
        whisper_model: Whisper model size for transcription

    Returns:
        JSON string with scraping results summary
    """
    ...
```

### Updated Tool Count

Total MCP tools: **27** (was 26, add `scrape_video`)

---

## Enhancement Integration

### Video Content Enhancement

Video segments can be enhanced using the same AI enhancement pipeline:

```python
# In enhance_skill_local.py or enhance_command.py

def enhance_video_content(segments: list[VideoSegment], level: int) -> list[VideoSegment]:
    """AI-enhance video segments.

    Enhancement levels:
    0 - No enhancement
    1 - Summary generation per segment
    2 - + Topic extraction, category refinement, code annotation
    3 - + Cross-segment connections, tutorial flow analysis, key takeaways

    Uses the same enhancement infrastructure as other sources.
    """
    if level == 0:
        return segments

    for segment in segments:
        if level >= 1:
            segment.summary = ai_summarize(segment.content)

        if level >= 2:
            segment.topic = ai_extract_topic(segment.content)
            segment.category = ai_refine_category(
                segment.content, segment.category
            )
            # Annotate code blocks with explanations
            for cb in segment.detected_code_blocks:
                cb.explanation = ai_explain_code(cb.code, segment.transcript)

        if level >= 3:
            # Cross-segment analysis (needs all segments)
            pass  # Handled at video level, not segment level

    return segments
```

---

## File Map (New & Modified Files)

### New Files

| File | Purpose | Estimated Size |
|------|---------|---------------|
| `src/skill_seekers/cli/video_scraper.py` | Main video scraper orchestrator | ~800-1000 lines |
| `src/skill_seekers/cli/video_models.py` | All data classes and enums | ~500-600 lines |
| `src/skill_seekers/cli/video_transcript.py` | Transcript extraction (YouTube API + Whisper) | ~400-500 lines |
| `src/skill_seekers/cli/video_visual.py` | Visual extraction (scene detection + OCR) | ~500-600 lines |
| `src/skill_seekers/cli/video_segmenter.py` | Segmentation and stream alignment | ~400-500 lines |
| `src/skill_seekers/cli/parsers/video_parser.py` | CLI argument parser | ~80-100 lines |
| `src/skill_seekers/cli/arguments/video.py` | Video-specific argument definitions | ~120-150 lines |
| `tests/test_video_scraper.py` | Video scraper tests | ~600-800 lines |
| `tests/test_video_transcript.py` | Transcript extraction tests | ~400-500 lines |
| `tests/test_video_visual.py` | Visual extraction tests | ~400-500 lines |
| `tests/test_video_segmenter.py` | Segmentation tests | ~300-400 lines |
| `tests/test_video_models.py` | Data model tests | ~200-300 lines |
| `tests/test_video_integration.py` | Integration tests | ~300-400 lines |
| `tests/fixtures/video/` | Test fixtures (mock transcripts, metadata) | Various |

### Modified Files

| File | Changes |
|------|---------|
| `src/skill_seekers/cli/source_detector.py` | Add video URL patterns, video file detection, video directory detection |
| `src/skill_seekers/cli/main.py` | Register `video` subcommand in COMMAND_MODULES |
| `src/skill_seekers/cli/unified_scraper.py` | Add `"video": []` to scraped_data, add `_scrape_video_source()` |
| `src/skill_seekers/cli/arguments/create.py` | Add video args to create command, add `--help-video` |
| `src/skill_seekers/cli/parsers/__init__.py` | Register VideoParser |
| `src/skill_seekers/cli/config_validator.py` | Validate video source entries in unified config |
| `src/skill_seekers/mcp/tools/scraping_tools.py` | Add `scrape_video` tool |
| `pyproject.toml` | Add `[video]` and `[video-full]` optional dependencies, add `skill-seekers-video` entry point |
| `tests/test_source_detector.py` | Add video detection tests |
| `tests/test_unified.py` | Add video source integration tests |
