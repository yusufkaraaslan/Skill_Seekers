# Video Tutorial Extraction Guide

Convert video tutorials into structured AI skills with transcripts, on-screen code extraction, and AI enhancement.

Supports YouTube videos, YouTube playlists, local video files, and pre-extracted JSON data.

---

## Quick Start

```bash
# Install transcript-only dependencies (lightweight, ~15 MB)
pip install "skill-seekers[video]"

# Extract a YouTube tutorial (transcript only)
skill-seekers video --url https://www.youtube.com/watch?v=VIDEO_ID

# Install visual extraction dependencies (auto-detects your GPU)
skill-seekers video --setup

# Extract with on-screen code recognition
skill-seekers video --url https://www.youtube.com/watch?v=VIDEO_ID --visual

# Extract with AI enhancement (cleans OCR, synthesizes tutorial)
skill-seekers video --url https://www.youtube.com/watch?v=VIDEO_ID --visual --enhance-level 2
```

---

## Installation

### Transcript-Only (Lightweight)

This installs `yt-dlp` and `youtube-transcript-api` -- everything needed to pull metadata and transcripts from YouTube videos.

```bash
pip install "skill-seekers[video]"
```

Total download size is around 15 MB. No GPU or native libraries required.

### Full Visual Extraction

Visual extraction adds scene detection, keyframe classification, OCR (optical character recognition), and Whisper speech-to-text. Install the base visual dependencies first:

```bash
pip install "skill-seekers[video-full]"
```

This installs `faster-whisper`, `scenedetect`, `opencv-python-headless`, and `pytesseract`.

Then run the setup command to install GPU-aware dependencies (PyTorch and EasyOCR):

```bash
skill-seekers video --setup
```

### GPU Setup (`--setup`)

The `--setup` command auto-detects your GPU hardware and installs the correct PyTorch variant along with EasyOCR. These packages are installed at runtime rather than through pip extras because PyTorch requires different builds depending on your GPU.

**Detection order:**

| GPU Type | Detection Method | PyTorch Variant Installed |
|----------|-----------------|--------------------------|
| NVIDIA (CUDA) | `nvidia-smi` | `torch` with CUDA 11.8 / 12.1 / 12.4 (matched to your driver) |
| AMD (ROCm) | `rocminfo` | `torch` with ROCm 6.2 / 6.3 |
| AMD (no ROCm) | `lspci` | CPU-only (warns to install ROCm first) |
| Apple Silicon | macOS detection | `torch` with MPS support |
| CPU only | Fallback | `torch` CPU build |

**What gets installed:**

- **PyTorch** -- correct build for your GPU
- **EasyOCR** -- multi-engine OCR for on-screen text extraction
- **opencv-python-headless** -- frame extraction and image processing
- **scenedetect** -- scene change detection for keyframe selection
- **pytesseract** -- Tesseract OCR engine (requires the `tesseract` system binary)
- **faster-whisper** -- Whisper speech-to-text for audio fallback

**System dependency:** Tesseract must be installed separately through your system package manager:

```bash
# Ubuntu/Debian
sudo apt install tesseract-ocr

# macOS
brew install tesseract

# Arch/Manjaro
sudo pacman -S tesseract
```

---

## CLI Reference

### Video-Specific Flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--url URL` | string | -- | Video URL (YouTube, Vimeo) |
| `--video-file PATH` | string | -- | Local video file path |
| `--playlist URL` | string | -- | Playlist URL (processes all videos in the playlist) |
| `--visual` | flag | off | Enable visual extraction (requires video-full deps) |
| `--vision-ocr` | flag | off | Use Claude Vision API as fallback for low-confidence code frames (requires `ANTHROPIC_API_KEY`, ~$0.004/frame) |
| `--whisper-model MODEL` | string | `base` | Whisper model size for speech-to-text fallback |
| `--from-json FILE` | string | -- | Build skill from previously extracted JSON data |
| `--start-time TIME` | string | -- | Start time for extraction (single video only) |
| `--end-time TIME` | string | -- | End time for extraction (single video only) |
| `--setup` | flag | -- | Auto-detect GPU and install visual extraction dependencies, then exit |
| `--visual-interval SECS` | float | `0.7` | How often to sample frames during visual extraction (seconds) |
| `--visual-min-gap SECS` | float | `0.5` | Minimum gap between extracted frames (seconds) |
| `--visual-similarity THRESH` | float | `3.0` | Pixel-diff threshold for duplicate frame detection; lower values keep more frames |
| `--languages LANGS` | string | `en` | Transcript language preference (comma-separated, e.g., `en,es`) |

### Shared Flags

These flags are available on all Skill Seekers commands:

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--name NAME` | string | `video_skill` | Skill name (used for output directory and filenames) |
| `--description TEXT` | string | -- | Skill description (used in SKILL.md) |
| `--output DIR` | string | `output/<name>` | Output directory |
| `--enhance-level LEVEL` | int (0-3) | `0` | AI enhancement level (see [AI Enhancement](#ai-enhancement) below). Default is 0 (disabled) for the video command. |
| `--enhance-workflow NAME` | string | -- | Enhancement workflow preset to apply (repeatable). Auto-set to `video-tutorial` when `--enhance-level` > 0. |
| `--api-key KEY` | string | -- | Anthropic API key (or set `ANTHROPIC_API_KEY` env var) |
| `--dry-run` | flag | off | Preview what will happen without executing |
| `--verbose` / `-v` | flag | off | Enable DEBUG level logging |
| `--quiet` / `-q` | flag | off | Suppress most output (WARNING level only) |

---

## Source Types

### YouTube Videos

Provide a YouTube URL with `--url`. The tool extracts metadata (title, channel, duration, chapters, tags, view count) via `yt-dlp` and fetches transcripts via the YouTube Transcript API.

```bash
skill-seekers video --url https://www.youtube.com/watch?v=dQw4w9WgXcQ --name my-tutorial
```

Shortened URLs also work:

```bash
skill-seekers video --url https://youtu.be/dQw4w9WgXcQ
```

### YouTube Playlists

Provide a playlist URL with `--playlist`. Every video in the playlist is processed sequentially and combined into a single skill.

```bash
skill-seekers video --playlist "https://www.youtube.com/playlist?list=PLxxxxxxx" --name course-name
```

Note: `--start-time` and `--end-time` cannot be used with playlists.

### Local Video Files

Provide a file path with `--video-file`. Metadata is extracted from the file itself. If a subtitle file (`.srt` or `.vtt`) exists alongside the video with the same base name, it is used automatically.

```bash
skill-seekers video --video-file recording.mp4 --name my-recording
```

For transcript extraction from local files without subtitles, the tool falls back to Whisper speech-to-text (requires `faster-whisper` from the `video-full` extras).

### Pre-Extracted JSON (`--from-json`)

If you have already run extraction and saved the JSON data, you can rebuild the skill without re-downloading or re-processing:

```bash
skill-seekers video --from-json output/my-tutorial_video_extracted.json --name my-tutorial
```

This skips all network requests and video processing -- it only runs the skill-building step.

---

## Visual Extraction Pipeline

When `--visual` is enabled, the tool runs a multi-stream pipeline on the video file:

### Stream 1: Metadata Extraction

Uses `yt-dlp` to fetch title, channel, duration, chapters, tags, thumbnails, view/like counts, and upload date.

### Stream 2: Transcript Extraction (3-Tier Fallback)

Transcripts are acquired in priority order:

1. **YouTube Transcript API** -- Fetches official captions. Prefers manually created transcripts over auto-generated ones. Confidence is reduced by 20% for auto-generated captions.
2. **Subtitle files** -- Parses `.srt` or `.vtt` files found alongside local video files.
3. **Whisper fallback** -- Runs `faster-whisper` speech-to-text on the audio track. Requires the `video-full` extras.

If none succeed, the video is processed without a transcript (visual data only).

### Stream 3: Visual Extraction

The visual pipeline has several stages:

1. **Scene detection** -- Samples frames at `--visual-interval` intervals (default: every 0.7 seconds). Filters duplicates using pixel-diff comparison controlled by `--visual-similarity`.

2. **Keyframe classification** -- Each extracted frame is classified into one of these types:
   - `CODE_EDITOR` -- IDE or text editor showing code
   - `TERMINAL` -- Command line / terminal window
   - `SLIDE` -- Presentation slide
   - `DIAGRAM` -- Diagrams, flowcharts, architecture drawings
   - `BROWSER` -- Web browser content
   - `WEBCAM` -- Speaker face / webcam feed
   - `SCREENCAST` -- General screen recording
   - `OTHER` -- Anything else

3. **Per-panel OCR** -- For `CODE_EDITOR` and `TERMINAL` frames, the image is split into panels (e.g., sidebar vs. editor pane) and OCR is run on each panel separately. This avoids mixing IDE UI text with actual code.

4. **OCR line cleaning** -- Removes line numbers captured by OCR, IDE decorations, button labels, and intra-line duplications from multi-engine results.

5. **Code filtering** -- The `_is_likely_code()` function checks whether OCR text contains actual programming tokens (e.g., `=`, `{}`, `def`, `import`) rather than UI junk. Only text that passes this filter is included in reference files as code blocks.

6. **Text block tracking** -- Groups OCR results across sequential frames into "text groups" that track the evolution of on-screen code over time. Detects additions, modifications, and deletions between frames.

7. **Language detection** -- Uses the `LanguageDetector` to identify the programming language of each text group based on code patterns and keywords.

8. **Audio-visual alignment** -- Pairs on-screen code with overlapping transcript segments to create annotated code examples (what was on screen + what the narrator was saying).

### Vision API Fallback (`--vision-ocr`)

When `--vision-ocr` is enabled and OCR confidence is low on a code frame, the tool sends the frame image to the Claude Vision API for higher-quality code extraction. This costs approximately $0.004 per frame and requires `ANTHROPIC_API_KEY` to be set.

### OCR Engines

The tool uses a multi-engine OCR ensemble:

- **EasyOCR** -- Neural network-based, good at recognizing code fonts
- **Tesseract** (via pytesseract) -- Traditional OCR engine, handles clean text well

Results from both engines are merged with deduplication to maximize accuracy.

---

## AI Enhancement

Enhancement is **disabled by default** for the video command (`--enhance-level` defaults to 0). Enable it by setting `--enhance-level` to 1, 2, or 3.

### Enhancement Levels

| Level | What It Does |
|-------|-------------|
| `0` | No AI enhancement. Raw extraction output only. |
| `1` | Enhances SKILL.md only (overview, structure, readability). |
| `2` | **Recommended.** Two-pass enhancement: first cleans reference files (Code Timeline reconstruction), then runs workflow stages and enhances SKILL.md. |
| `3` | Full enhancement. All level-2 work plus architecture, configuration, and comprehensive documentation analysis. |

Enhancement auto-detects the mode based on environment:

- If `ANTHROPIC_API_KEY` is set, uses **API mode** (direct Claude API calls).
- Otherwise, uses **LOCAL mode** (Claude Code CLI, free with Max plan).

### Two-Pass Enhancement (Level 2+)

At enhancement level 2 or higher, the tool runs two passes:

**Pass 1: Reference file cleanup.** Each reference file is sent to Claude with a focused prompt to reconstruct the Code Timeline section. The AI uses transcript context to fix OCR errors, remove UI decorations, set correct language tags, and reconstruct garbled code blocks.

**Pass 2: Workflow stages + SKILL.md rewrite.** The `video-tutorial` workflow runs four specialized stages, then the traditional SKILL.md enhancer rewrites the final output.

### The `video-tutorial` Workflow

When `--enhance-level` > 0 and no `--enhance-workflow` is explicitly specified, the `video-tutorial` workflow is automatically applied. It has four stages:

1. **`ocr_code_cleanup`** -- Reviews all code blocks for OCR noise. Removes captured line numbers, UI elements, and common OCR character confusions (l/1, O/0, rn/m). Outputs cleaned blocks with language detection and confidence scoring.

2. **`language_detection`** -- Determines the programming language for each code block using narrator mentions, code patterns, visible file extensions, framework context, and pre-filled `detected_language` hints from the extraction pipeline.

3. **`tutorial_synthesis`** -- Groups content by topic rather than timestamp. Identifies main concepts, builds a progressive learning path, and pairs code blocks with narrator explanations. Creates structured tutorial sections with prerequisites and key concepts.

4. **`skill_polish`** -- Produces the final SKILL.md with clear trigger conditions, a quick reference of 5-10 annotated code examples, a step-by-step guide, and key concept definitions. Ensures all code fences have correct language tags and no raw OCR artifacts remain.

---

## Output Structure

After extraction completes, the output directory contains:

```
output/<name>/
├── SKILL.md                          # Main skill file (enhanced if --enhance-level > 0)
├── references/
│   └── video_<sanitized-title>.md    # Full transcript + OCR + Code Timeline per video
├── frames/                           # Only present with --visual
│   └── frame_NNN_Ns.jpg             # Extracted keyframes (N = frame number, Ns = timestamp)
└── video_data/
    └── metadata.json                 # Full extraction metadata (VideoScraperResult)
```

Additionally, a standalone JSON file is saved outside the skill directory:

```
output/<name>_video_extracted.json    # Raw extraction data (can be re-used with --from-json)
```

### Reference File Contents

Each reference file (`references/video_<title>.md`) contains:

- **Metadata block** -- Source channel, duration, publish date, URL, view/like counts, tags
- **Table of contents** -- From YouTube chapters or auto-generated segments
- **Segments** -- Transcript text organized by time segment, with keyframe images and OCR text inline
- **Code Timeline** -- (visual mode) Tracked code groups showing text evolution over time, with edit diffs
- **Audio-Visual Alignment** -- (visual mode) Paired on-screen code with narrator explanations
- **Transcript source** -- Which tier provided the transcript (YouTube manual, YouTube auto, subtitle file, Whisper) and confidence score

---

## Time Clipping

Use `--start-time` and `--end-time` to extract only a portion of a video. This is useful for long videos where you only need a specific section.

**Accepted time formats:**

| Format | Example | Meaning |
|--------|---------|---------|
| Seconds | `90` or `330.5` | 90 seconds / 330.5 seconds |
| MM:SS | `1:30` | 1 minute 30 seconds |
| HH:MM:SS | `0:05:30` | 5 minutes 30 seconds |

Both transcript segments and chapters are filtered to the specified range. When visual extraction is enabled, frames outside the range are skipped.

```bash
# Extract only minutes 5 through 15
skill-seekers video --url https://youtu.be/VIDEO_ID --start-time 5:00 --end-time 15:00

# Extract from 2 minutes onward
skill-seekers video --url https://youtu.be/VIDEO_ID --start-time 120

# Extract the first 10 minutes
skill-seekers video --url https://youtu.be/VIDEO_ID --end-time 10:00
```

Restrictions:

- `--start-time` must be less than `--end-time` when both are specified.
- Time clipping cannot be used with `--playlist`.

---

## Examples

### Basic transcript extraction from a YouTube video

```bash
skill-seekers video --url https://www.youtube.com/watch?v=VIDEO_ID --name react-hooks-tutorial
```

### Visual extraction with on-screen code recognition

```bash
skill-seekers video --url https://youtu.be/VIDEO_ID --name godot-signals --visual
```

### Full pipeline with AI enhancement (recommended for production skills)

```bash
export ANTHROPIC_API_KEY=sk-ant-...
skill-seekers video --url https://youtu.be/VIDEO_ID --name django-rest-api \
    --visual --enhance-level 2
```

### Process a local recording with subtitles

```bash
# Place recording.srt alongside recording.mp4
skill-seekers video --video-file ./recording.mp4 --name my-lecture
```

### Extract a specific section of a long video

```bash
skill-seekers video --url https://youtu.be/VIDEO_ID --name auth-chapter \
    --start-time 15:30 --end-time 42:00 --visual
```

### Process an entire YouTube playlist as one skill

```bash
skill-seekers video --playlist "https://www.youtube.com/playlist?list=PLxxxxxxx" \
    --name python-crash-course --languages en
```

### Rebuild a skill from previously extracted data

```bash
skill-seekers video --from-json output/my-tutorial_video_extracted.json \
    --name my-tutorial --enhance-level 2
```

### Use Vision API for higher-quality code extraction on difficult frames

```bash
export ANTHROPIC_API_KEY=sk-ant-...
skill-seekers video --url https://youtu.be/VIDEO_ID --name cpp-tutorial \
    --visual --vision-ocr --enhance-level 2
```

---

## Troubleshooting

### "Missing video dependencies: yt-dlp, youtube-transcript-api"

You need to install the video extras:

```bash
pip install "skill-seekers[video]"
```

### "Missing video dependencies" when using `--visual`

Visual extraction requires the full dependency set:

```bash
pip install "skill-seekers[video-full]"
skill-seekers video --setup
```

### GPU not detected by `--setup`

- **NVIDIA:** Ensure `nvidia-smi` is in your PATH and your GPU driver is installed.
- **AMD:** Ensure ROCm is installed and `rocminfo` is available. If only `lspci` detects the GPU, install ROCm first for GPU acceleration: https://rocm.docs.amd.com/
- **Fallback:** If no GPU is found, CPU-only PyTorch is installed. OCR and Whisper will still work, just slower.

### "tesseract is not installed or it's not in your PATH"

Install Tesseract via your system package manager:

```bash
sudo apt install tesseract-ocr          # Ubuntu/Debian
brew install tesseract                   # macOS
sudo pacman -S tesseract                 # Arch/Manjaro
```

### YouTube transcript returns empty

Some videos have no captions available. Check:

- The video may have captions disabled by the uploader.
- Try different languages with `--languages en,auto`.
- For local files, place a `.srt` or `.vtt` subtitle file alongside the video.
- Install `faster-whisper` (via `video-full`) for speech-to-text fallback.

### Rate limits from YouTube

`yt-dlp` can be rate-limited by YouTube. If you hit this:

- Wait a few minutes and retry.
- For playlists, the tool processes videos sequentially with natural delays.
- Consider downloading the video first with `yt-dlp` and using `--video-file`.

### OCR quality is poor

- Use `--vision-ocr` to enable the Claude Vision API fallback for low-confidence frames (~$0.004/frame).
- Lower `--visual-similarity` (e.g., `1.5`) to keep more frames, giving the tracker more data points.
- Decrease `--visual-interval` (e.g., `0.3`) to sample frames more frequently.
- Use `--enhance-level 2` to let AI reconstruct code blocks from transcript context.

### Enhancement fails or hangs

- Verify your API key: `echo $ANTHROPIC_API_KEY`
- Check that the key has sufficient quota.
- Try a lower enhancement level: `--enhance-level 1` only enhances SKILL.md.
- Without an API key, enhancement falls back to LOCAL mode (requires Claude Code CLI with a Max plan).

### "No videos were successfully processed"

Check the error output for specifics. Common causes:

- Invalid or private YouTube URL.
- Network connectivity issues.
- Video is age-restricted or geo-blocked.
- Local file path does not exist or is not a supported format.
