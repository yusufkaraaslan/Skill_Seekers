# Video Source — Dependencies & System Requirements

**Date:** February 27, 2026
**Document:** 07 of 07
**Status:** Planning

> **Status: IMPLEMENTED** — `skill-seekers video --setup` (see `video_setup.py`, 835 lines, 60 tests)
> - GPU auto-detection: NVIDIA (nvidia-smi/CUDA), AMD (rocminfo/ROCm), CPU fallback
> - Correct PyTorch index URL selection per GPU vendor
> - EasyOCR removed from pip extras, installed at runtime via --setup
> - ROCm configuration (MIOPEN_FIND_MODE, HSA_OVERRIDE_GFX_VERSION)
> - Virtual environment detection with --force override
> - System dependency checks (tesseract, ffmpeg)
> - Non-interactive mode for MCP/CI usage

---

## Table of Contents

1. [Dependency Tiers](#dependency-tiers)
2. [pyproject.toml Changes](#pyprojecttoml-changes)
3. [System Requirements](#system-requirements)
4. [Import Guards](#import-guards)
5. [Dependency Check Command](#dependency-check-command)
6. [Model Management](#model-management)
7. [Docker Considerations](#docker-considerations)

---

## Dependency Tiers

Video processing has two tiers to keep the base install lightweight:

### Tier 1: `[video]` — Lightweight (YouTube transcripts + metadata)

**Use case:** YouTube videos with existing captions. No download, no GPU needed.

| Package | Version | Size | Purpose |
|---------|---------|------|---------|
| `yt-dlp` | `>=2024.12.0` | ~15MB | Metadata extraction, audio download |
| `youtube-transcript-api` | `>=1.2.0` | ~50KB | YouTube caption extraction |

**Capabilities:**
- YouTube metadata (title, chapters, tags, description, engagement)
- YouTube captions (manual and auto-generated)
- Vimeo metadata
- Playlist and channel resolution
- Subtitle file parsing (SRT, VTT)
- Segmentation and alignment
- Full output generation

**NOT included:**
- Speech-to-text (Whisper)
- Visual extraction (frame + OCR)
- Local video file transcription (without subtitles)

### Tier 2: `[video-full]` — Full (adds Whisper + visual extraction)

**Use case:** Local videos without subtitles, or when you want code/slide extraction from screen.

| Package | Version | Size | Purpose |
|---------|---------|------|---------|
| `yt-dlp` | `>=2024.12.0` | ~15MB | Metadata + audio download |
| `youtube-transcript-api` | `>=1.2.0` | ~50KB | YouTube captions |
| `faster-whisper` | `>=1.0.0` | ~5MB (+ models: 75MB-3GB) | Speech-to-text |
| `scenedetect[opencv]` | `>=0.6.4` | ~50MB (includes OpenCV) | Scene boundary detection |
| `easyocr` | `>=1.7.0` | ~150MB (+ models: ~200MB) | Text recognition from frames |
| `opencv-python-headless` | `>=4.9.0` | ~50MB | Frame extraction, image processing |

**Additional capabilities over Tier 1:**
- Whisper speech-to-text (99 languages, word-level timestamps)
- Scene detection (find visual transitions)
- Keyframe extraction (save important frames)
- Frame classification (code/slide/terminal/diagram)
- OCR on frames (extract code and text from screen)
- Code block detection from video

**Total install size:**
- Tier 1: ~15MB
- Tier 2: ~270MB + models (~300MB-3.2GB depending on Whisper model)

---

## pyproject.toml Changes

```toml
[project.optional-dependencies]
# Existing dependencies...
gemini = ["google-generativeai>=0.8.0"]
openai = ["openai>=1.0.0"]
all-llms = ["google-generativeai>=0.8.0", "openai>=1.0.0"]

# NEW: Video processing
video = [
    "yt-dlp>=2024.12.0",
    "youtube-transcript-api>=1.2.0",
]
video-full = [
    "yt-dlp>=2024.12.0",
    "youtube-transcript-api>=1.2.0",
    "faster-whisper>=1.0.0",
    "scenedetect[opencv]>=0.6.4",
    "easyocr>=1.7.0",
    "opencv-python-headless>=4.9.0",
]

# Update 'all' to include video
all = [
    # ... existing all dependencies ...
    "yt-dlp>=2024.12.0",
    "youtube-transcript-api>=1.2.0",
    "faster-whisper>=1.0.0",
    "scenedetect[opencv]>=0.6.4",
    "easyocr>=1.7.0",
    "opencv-python-headless>=4.9.0",
]

[project.scripts]
# ... existing entry points ...
skill-seekers-video = "skill_seekers.cli.video_scraper:main"      # NEW
```

### Installation Commands

```bash
# Lightweight video (YouTube transcripts + metadata)
pip install skill-seekers[video]

# Full video (+ Whisper + visual extraction)
pip install skill-seekers[video-full]

# Everything
pip install skill-seekers[all]

# Development (editable)
pip install -e ".[video]"
pip install -e ".[video-full]"
```

---

## System Requirements

### Tier 1 (Lightweight)

| Requirement | Needed For | How to Check |
|-------------|-----------|-------------|
| Python 3.10+ | All | `python --version` |
| Internet connection | YouTube API calls | N/A |

No additional system dependencies. Pure Python.

### Tier 2 (Full)

| Requirement | Needed For | How to Check | Install |
|-------------|-----------|-------------|---------|
| Python 3.10+ | All | `python --version` | — |
| FFmpeg | Audio extraction, video processing | `ffmpeg -version` | See below |
| GPU (optional) | Whisper + easyocr acceleration | `nvidia-smi` (NVIDIA) | CUDA toolkit |

### FFmpeg Installation

FFmpeg is required for:
- Extracting audio from video files (Whisper input)
- Downloading audio-only streams (yt-dlp post-processing)
- Converting between audio formats

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows (winget)
winget install ffmpeg

# Windows (choco)
choco install ffmpeg

# Verify
ffmpeg -version
```

### GPU Support (Optional)

GPU accelerates Whisper (~4x) and easyocr (~5x) but is not required.

**NVIDIA GPU (CUDA):**
```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# faster-whisper uses CTranslate2 which auto-detects CUDA
# easyocr uses PyTorch which auto-detects CUDA
# No additional setup needed if PyTorch CUDA is working
```

**Apple Silicon (MPS):**
```bash
# faster-whisper does not support MPS directly
# Falls back to CPU on Apple Silicon
# easyocr has partial MPS support
```

**CPU-only (no GPU):**
```bash
# Everything works on CPU, just slower
# Whisper base model: ~4x slower on CPU vs GPU
# easyocr: ~5x slower on CPU vs GPU
# For short videos (<10 min), CPU is fine
```

---

## Import Guards

All video dependencies use try/except import guards to provide clear error messages:

### video_scraper.py

```python
"""Video scraper - main orchestrator."""

# Core dependencies (always available)
import json
import logging
import os
from pathlib import Path

# Tier 1: Video basics
try:
    from yt_dlp import YoutubeDL
    HAS_YTDLP = True
except ImportError:
    HAS_YTDLP = False

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    HAS_YT_TRANSCRIPT = True
except ImportError:
    HAS_YT_TRANSCRIPT = False

# Feature availability check
def check_video_dependencies(require_full: bool = False) -> None:
    """Check that video dependencies are installed.

    Args:
        require_full: If True, check for full dependencies (Whisper, OCR)

    Raises:
        ImportError: With installation instructions
    """
    missing = []

    if not HAS_YTDLP:
        missing.append("yt-dlp")
    if not HAS_YT_TRANSCRIPT:
        missing.append("youtube-transcript-api")

    if missing:
        raise ImportError(
            f"Video processing requires: {', '.join(missing)}\n"
            f"Install with: pip install skill-seekers[video]"
        )

    if require_full:
        full_missing = []
        try:
            import faster_whisper
        except ImportError:
            full_missing.append("faster-whisper")
        try:
            import cv2
        except ImportError:
            full_missing.append("opencv-python-headless")
        try:
            import scenedetect
        except ImportError:
            full_missing.append("scenedetect[opencv]")
        try:
            import easyocr
        except ImportError:
            full_missing.append("easyocr")

        if full_missing:
            raise ImportError(
                f"Visual extraction requires: {', '.join(full_missing)}\n"
                f"Install with: pip install skill-seekers[video-full]"
            )
```

### video_transcript.py

```python
"""Transcript extraction module."""

# YouTube transcript (Tier 1)
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    HAS_YT_TRANSCRIPT = True
except ImportError:
    HAS_YT_TRANSCRIPT = False

# Whisper (Tier 2)
try:
    from faster_whisper import WhisperModel
    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False


def get_transcript(video_info, config):
    """Get transcript using best available method."""

    # Try YouTube captions first (Tier 1)
    if HAS_YT_TRANSCRIPT and video_info.source_type == VideoSourceType.YOUTUBE:
        try:
            return extract_youtube_transcript(video_info.video_id, config.languages)
        except TranscriptNotAvailable:
            pass

    # Try Whisper fallback (Tier 2)
    if HAS_WHISPER:
        return transcribe_with_whisper(video_info, config)

    # No transcript possible
    if not HAS_WHISPER:
        logger.warning(
            f"No transcript for {video_info.video_id}. "
            "Install faster-whisper for speech-to-text: "
            "pip install skill-seekers[video-full]"
        )
    return [], TranscriptSource.NONE
```

### video_visual.py

```python
"""Visual extraction module."""

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

try:
    from scenedetect import detect, ContentDetector
    HAS_SCENEDETECT = True
except ImportError:
    HAS_SCENEDETECT = False

try:
    import easyocr
    HAS_EASYOCR = True
except ImportError:
    HAS_EASYOCR = False


def check_visual_dependencies() -> None:
    """Check visual extraction dependencies."""
    missing = []
    if not HAS_OPENCV:
        missing.append("opencv-python-headless")
    if not HAS_SCENEDETECT:
        missing.append("scenedetect[opencv]")
    if not HAS_EASYOCR:
        missing.append("easyocr")

    if missing:
        raise ImportError(
            f"Visual extraction requires: {', '.join(missing)}\n"
            f"Install with: pip install skill-seekers[video-full]"
        )


def check_ffmpeg() -> bool:
    """Check if FFmpeg is available."""
    import shutil
    return shutil.which('ffmpeg') is not None
```

---

## Dependency Check Command

Add a dependency check to the `config` command:

```bash
# Check all video dependencies
skill-seekers config --check-video

# Output:
# Video Dependencies:
#   yt-dlp              ✅ 2025.01.15
#   youtube-transcript-api ✅ 1.2.3
#   faster-whisper      ❌ Not installed (pip install skill-seekers[video-full])
#   opencv-python-headless ❌ Not installed
#   scenedetect         ❌ Not installed
#   easyocr             ❌ Not installed
#
# System Dependencies:
#   FFmpeg              ✅ 6.1.1
#   GPU (CUDA)          ❌ Not available (CPU mode will be used)
#
# Available modes:
#   Transcript only     ✅ YouTube captions available
#   Whisper fallback    ❌ Install faster-whisper
#   Visual extraction   ❌ Install video-full dependencies
```

---

## Model Management

### Whisper Models

Whisper models are downloaded on first use and cached in the user's home directory.

| Model | Download Size | Disk Size | First-Use Download Time |
|-------|-------------|-----------|------------------------|
| tiny | 75 MB | 75 MB | ~15s |
| base | 142 MB | 142 MB | ~25s |
| small | 466 MB | 466 MB | ~60s |
| medium | 1.5 GB | 1.5 GB | ~3 min |
| large-v3 | 3.1 GB | 3.1 GB | ~5 min |
| large-v3-turbo | 1.6 GB | 1.6 GB | ~3 min |

**Cache location:** `~/.cache/huggingface/hub/` (CTranslate2 models)

**Pre-download command:**
```bash
# Pre-download a model before using it
python -c "from faster_whisper import WhisperModel; WhisperModel('base')"
```

### easyocr Models

easyocr models are also downloaded on first use.

| Language Pack | Download Size | Disk Size |
|-------------|-------------|-----------|
| English | ~100 MB | ~100 MB |
| + Additional language | ~50-100 MB each | ~50-100 MB each |

**Cache location:** `~/.EasyOCR/model/`

**Pre-download command:**
```bash
# Pre-download English OCR model
python -c "import easyocr; easyocr.Reader(['en'])"
```

---

## Docker Considerations

### Dockerfile additions for video support

```dockerfile
# Tier 1 (lightweight)
RUN pip install skill-seekers[video]

# Tier 2 (full)
RUN apt-get update && apt-get install -y ffmpeg
RUN pip install skill-seekers[video-full]

# Pre-download Whisper model (avoids first-run download)
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('base')"

# Pre-download easyocr model
RUN python -c "import easyocr; easyocr.Reader(['en'])"
```

### Docker image sizes

| Tier | Base Image Size | Additional Size | Total |
|------|----------------|----------------|-------|
| Tier 1 (video) | ~300 MB | ~20 MB | ~320 MB |
| Tier 2 (video-full, CPU) | ~300 MB | ~800 MB | ~1.1 GB |
| Tier 2 (video-full, GPU) | ~5 GB (CUDA base) | ~800 MB | ~5.8 GB |

### Kubernetes resource recommendations

```yaml
# Tier 1 (transcript only)
resources:
  requests:
    memory: "256Mi"
    cpu: "500m"
  limits:
    memory: "512Mi"
    cpu: "1000m"

# Tier 2 (full, CPU)
resources:
  requests:
    memory: "2Gi"
    cpu: "2000m"
  limits:
    memory: "4Gi"
    cpu: "4000m"

# Tier 2 (full, GPU)
resources:
  requests:
    memory: "4Gi"
    cpu: "2000m"
    nvidia.com/gpu: 1
  limits:
    memory: "8Gi"
    cpu: "4000m"
    nvidia.com/gpu: 1
```
