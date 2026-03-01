# Video Source Support — Master Plan

**Date:** February 27, 2026
**Feature ID:** V1.0
**Status:** Planning
**Priority:** High
**Estimated Complexity:** Large (multi-sprint feature)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Motivation & Goals](#motivation--goals)
3. [Scope](#scope)
4. [Plan Documents Index](#plan-documents-index)
5. [High-Level Architecture](#high-level-architecture)
6. [Implementation Phases](#implementation-phases)
7. [Dependencies](#dependencies)
8. [Risk Assessment](#risk-assessment)
9. [Success Criteria](#success-criteria)

---

## Executive Summary

Add **video** as a first-class source type in Skill Seekers, alongside web documentation, GitHub repositories, PDF files, and Word documents. Videos contain a massive amount of knowledge — conference talks, official tutorials, live coding sessions, architecture walkthroughs — that is currently inaccessible to our pipeline.

The video source will use a **3-stream parallel extraction** model:

| Stream | What | Tool |
|--------|------|------|
| **ASR** (Audio Speech Recognition) | Spoken words → timestamped text | youtube-transcript-api + faster-whisper |
| **OCR** (Optical Character Recognition) | On-screen code/slides/diagrams → text | PySceneDetect + OpenCV + easyocr |
| **Metadata** | Title, chapters, tags, description | yt-dlp Python API |

These three streams are **aligned on a shared timeline** and merged into structured `VideoSegment` objects — the fundamental output unit. Segments are then categorized, converted to reference markdown files, and integrated into SKILL.md just like any other source.

---

## Motivation & Goals

### Why Video?

1. **Knowledge density** — A 30-minute conference talk can contain the equivalent of a 5,000-word blog post, plus live code demos that never appear in written docs.
2. **Official tutorials** — Many frameworks (React, Flutter, Unity, Godot) have official video tutorials that are the canonical learning resource.
3. **Code walkthroughs** — Screen-recorded coding sessions show real patterns, debugging workflows, and architecture decisions that written docs miss.
4. **Conference talks** — JSConf, PyCon, GopherCon, etc. contain deep technical insights from framework authors.
5. **Completeness** — Skill Seekers aims to be the **universal** documentation preprocessor. Video is the last major content type we don't support.

### Goals

- **G1:** Extract structured, time-aligned knowledge from YouTube videos, playlists, channels, and local video files.
- **G2:** Integrate video as a first-class source in the unified config system (multiple video sources per skill, alongside docs/github/pdf).
- **G3:** Auto-detect video sources in the `create` command (YouTube URLs, video file extensions).
- **G4:** Support two tiers: lightweight (transcript + metadata only) and full (+ visual extraction with OCR).
- **G5:** Produce output that is indistinguishable in quality from other source types — properly categorized reference files integrated into SKILL.md.
- **G6:** Make visual extraction (Whisper, OCR) available as optional add-on dependencies, keeping core install lightweight.

### Non-Goals (explicitly out of scope for V1.0)

- Real-time / live stream processing
- Video generation or editing
- Speaker diarization (identifying who said what) — future enhancement
- Automatic video discovery (e.g., "find all React tutorials on YouTube") — future enhancement
- DRM-protected or paywalled video content (Udemy, Coursera, etc.)
- Audio-only podcasts (similar pipeline but separate feature)

---

## Scope

### Supported Video Sources

| Source | Input Format | Example |
|--------|-------------|---------|
| YouTube single video | URL | `https://youtube.com/watch?v=abc123` |
| YouTube short URL | URL | `https://youtu.be/abc123` |
| YouTube playlist | URL | `https://youtube.com/playlist?list=PLxxx` |
| YouTube channel | URL | `https://youtube.com/@channelname` |
| Vimeo video | URL | `https://vimeo.com/123456` |
| Local video file | Path | `./tutorials/intro.mp4` |
| Local video directory | Path | `./recordings/` (batch) |

### Supported Video Formats (local files)

| Format | Extension | Notes |
|--------|-----------|-------|
| MP4 | `.mp4` | Most common, universal |
| Matroska | `.mkv` | Common for screen recordings |
| WebM | `.webm` | Web-native, YouTube's format |
| AVI | `.avi` | Legacy but still used |
| QuickTime | `.mov` | macOS screen recordings |
| Flash Video | `.flv` | Legacy, rare |
| MPEG Transport | `.ts` | Streaming recordings |
| Windows Media | `.wmv` | Windows screen recordings |

### Supported Languages (transcript)

All languages supported by:
- YouTube's caption system (100+ languages)
- faster-whisper / OpenAI Whisper (99 languages)

---

## Plan Documents Index

| Document | Content |
|----------|---------|
| [`01_VIDEO_RESEARCH.md`](./01_VIDEO_RESEARCH.md) | Library research, benchmarks, industry standards |
| [`02_VIDEO_DATA_MODELS.md`](./02_VIDEO_DATA_MODELS.md) | All data classes, type definitions, JSON schemas |
| [`03_VIDEO_PIPELINE.md`](./03_VIDEO_PIPELINE.md) | Processing pipeline (6 phases), algorithms, edge cases |
| [`04_VIDEO_INTEGRATION.md`](./04_VIDEO_INTEGRATION.md) | CLI, config, source detection, unified scraper integration |
| [`05_VIDEO_OUTPUT.md`](./05_VIDEO_OUTPUT.md) | Output structure, SKILL.md integration, reference file format |
| [`06_VIDEO_TESTING.md`](./06_VIDEO_TESTING.md) | Test strategy, mocking, fixtures, CI considerations |
| [`07_VIDEO_DEPENDENCIES.md`](./07_VIDEO_DEPENDENCIES.md) | Dependency tiers, optional installs, system requirements — **IMPLEMENTED** (`video_setup.py`, GPU auto-detection, `--setup`) |

---

## High-Level Architecture

```
                              ┌──────────────────────┐
                              │    User Input         │
                              │                       │
                              │  YouTube URL          │
                              │  Playlist URL         │
                              │  Local .mp4 file      │
                              │  Unified config JSON  │
                              └──────────┬───────────┘
                                         │
                              ┌──────────▼───────────┐
                              │  Source Detector      │
                              │  (source_detector.py) │
                              │  type="video"         │
                              └──────────┬───────────┘
                                         │
                              ┌──────────▼───────────┐
                              │  Video Scraper        │
                              │  (video_scraper.py)   │
                              │  Main orchestrator    │
                              └──────────┬───────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
         ┌──────────▼──────┐  ┌──────────▼──────┐  ┌──────────▼──────┐
         │  Stream 1: ASR  │  │  Stream 2: OCR  │  │  Stream 3: Meta │
         │                 │  │  (optional)      │  │                 │
         │ youtube-trans-  │  │ PySceneDetect    │  │ yt-dlp          │
         │ cript-api       │  │ OpenCV           │  │ extract_info()  │
         │ faster-whisper  │  │ easyocr          │  │                 │
         └────────┬────────┘  └────────┬────────┘  └────────┬────────┘
                  │                    │                    │
                  │    Timestamped     │   Keyframes +     │  Chapters,
                  │    transcript      │   OCR text         │  tags, desc
                  │                    │                    │
                  └────────────────────┼────────────────────┘
                                       │
                            ┌──────────▼───────────┐
                            │  Segmenter &         │
                            │  Aligner             │
                            │  (video_segmenter.py)│
                            │                      │
                            │  Align 3 streams     │
                            │  on shared timeline  │
                            └──────────┬───────────┘
                                       │
                              list[VideoSegment]
                                       │
                            ┌──────────▼───────────┐
                            │  Output Generator    │
                            │                      │
                            │  ├ references/*.md   │
                            │  ├ video_data/*.json │
                            │  └ SKILL.md section  │
                            └──────────────────────┘
```

---

## Implementation Phases

### Phase 1: Foundation (Core Pipeline)
- `video_models.py` — All data classes
- `video_scraper.py` — Main orchestrator
- `video_transcript.py` — YouTube captions + Whisper fallback
- Source detector update — YouTube URL patterns, video file extensions
- Basic metadata extraction via yt-dlp
- Output: timestamped transcript as reference markdown

### Phase 2: Segmentation & Structure
- `video_segmenter.py` — Chapter-aware segmentation
- Semantic segmentation fallback (when no chapters)
- Time-window fallback (configurable interval)
- Segment categorization (reuse smart_categorize patterns)

### Phase 3: Visual Extraction
- `video_visual.py` — Frame extraction + scene detection
- Frame classification (code/slide/terminal/diagram/other)
- OCR on classified frames (easyocr)
- Timeline alignment with ASR transcript

### Phase 4: Integration
- Unified config support (`"type": "video"`)
- `create` command routing
- CLI parser + arguments
- Unified scraper integration (video alongside docs/github/pdf)
- SKILL.md section generation

### Phase 5: Quality & Polish
- AI enhancement for video content (summarization, topic extraction)
- RAG-optimized chunking for video segments
- MCP tools (scrape_video, export_video)
- Comprehensive test suite

---

## Dependencies

### Core (always required for video)
```
yt-dlp>=2024.12.0
youtube-transcript-api>=1.2.0
```

### Full (for visual extraction + local file transcription)
```
faster-whisper>=1.0.0
scenedetect[opencv]>=0.6.4
easyocr>=1.7.0
opencv-python-headless>=4.9.0
```

### System Requirements (for full mode)
- FFmpeg (required by faster-whisper and yt-dlp for audio extraction)
- GPU (optional but recommended for Whisper and easyocr)

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| YouTube API changes break scraping | Medium | High | yt-dlp actively maintained, abstract behind our API |
| Whisper models are large (~1.5GB) | Certain | Medium | Optional dependency, offer multiple model sizes |
| OCR accuracy on code is low | Medium | Medium | Combine OCR with transcript context, use confidence scoring |
| Video download is slow | High | Medium | Stream audio only, don't download full video for transcript |
| Auto-generated captions are noisy | High | Medium | Confidence filtering, AI cleanup in enhancement phase |
| Copyright / ToS concerns | Low | High | Document that user is responsible for content rights |
| CI tests can't download videos | Certain | Medium | Mock all network calls, use fixture transcripts |

---

## Success Criteria

1. **Functional:** `skill-seekers create https://youtube.com/watch?v=xxx` produces a skill with video content integrated into SKILL.md.
2. **Multi-source:** Video sources work alongside docs/github/pdf in unified configs.
3. **Quality:** Video-derived reference files are categorized and structured (not raw transcript dumps).
4. **Performance:** Transcript-only mode processes a 30-minute video in < 30 seconds.
5. **Tests:** Full test suite with mocked network calls, 100% of video pipeline covered.
6. **Tiered deps:** `pip install skill-seekers[video]` works without pulling Whisper/OpenCV.
