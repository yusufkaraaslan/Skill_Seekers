# Video Source — Library Research & Industry Standards

**Date:** February 27, 2026
**Document:** 01 of 07
**Status:** Complete

---

## Table of Contents

1. [Industry Standards & Approaches](#industry-standards--approaches)
2. [Library Comparison Matrix](#library-comparison-matrix)
3. [Detailed Library Analysis](#detailed-library-analysis)
4. [Architecture Patterns from Industry](#architecture-patterns-from-industry)
5. [Benchmarks & Performance Data](#benchmarks--performance-data)
6. [Recommendations](#recommendations)

---

## Industry Standards & Approaches

### How the Industry Processes Video for AI/RAG

Based on research from NVIDIA, LlamaIndex, Ragie, and open-source projects, the industry has converged on a **3-stream parallel extraction** model:

#### The 3-Stream Model

```
Video Input
    │
    ├──→ Stream 1: ASR (Audio Speech Recognition)
    │    Extract spoken words with timestamps
    │    Tools: Whisper, YouTube captions API
    │    Output: [{text, start, end, confidence}, ...]
    │
    ├──→ Stream 2: OCR (Optical Character Recognition)
    │    Extract visual text (code, slides, diagrams)
    │    Tools: OpenCV + scene detection + OCR engine
    │    Output: [{text, timestamp, frame_type, bbox}, ...]
    │
    └──→ Stream 3: Metadata
         Extract structural info (chapters, tags, description)
         Tools: yt-dlp, platform APIs
         Output: {title, chapters, tags, description, ...}
```

**Key insight (from NVIDIA's multimodal RAG blog):** Ground everything to text first. Align all streams on a shared timeline, then merge into unified text segments. This makes the output compatible with any text-based RAG pipeline without requiring multimodal embeddings.

#### Reference Implementations

| Project | Approach | Strengths | Weaknesses |
|---------|----------|-----------|------------|
| [video-analyzer](https://github.com/byjlw/video-analyzer) | Whisper + OpenCV + LLM analysis | Full pipeline, LLM summaries | No chapter support, no YouTube integration |
| [LlamaIndex MultiModal RAG](https://www.llamaindex.ai/blog/multimodal-rag-for-advanced-video-processing-with-llamaindex-lancedb-33be4804822e) | Frame extraction + CLIP + LanceDB | Vector search over frames | Heavy (requires GPU), no ASR |
| [VideoRAG](https://video-rag.github.io/) | Graph-based reasoning + multimodal retrieval | Multi-hour video support | Research project, not production-ready |
| [Ragie Multimodal RAG](https://www.ragie.ai/blog/how-we-built-multimodal-rag-for-audio-and-video) | faster-whisper large-v3-turbo + OCR + object detection | Production-grade, 3-stream | Proprietary, not open-source |

#### Industry Best Practices

1. **Audio-only download** — Never download full video when you only need audio. Extract audio stream with FFmpeg (`-vn` flag). This is 10-50x smaller.
2. **Prefer existing captions** — YouTube manual captions are higher quality than any ASR model. Only fall back to Whisper when captions unavailable.
3. **Chapter-based segmentation** — YouTube chapters provide natural content boundaries. Use them as primary segmentation, fall back to time-window or semantic splitting.
4. **Confidence filtering** — Auto-generated captions and OCR output include confidence scores. Filter low-confidence content rather than including everything.
5. **Parallel extraction** — Run ASR and OCR in parallel (they're independent). Merge after both complete.
6. **Tiered processing** — Offer fast/light mode (transcript only) and deep mode (+ visual). Let users choose based on their compute budget.

---

## Library Comparison Matrix

### Metadata & Download

| Library | Purpose | Install Size | Actively Maintained | Python API | License |
|---------|---------|-------------|-------------------|------------|---------|
| **yt-dlp** | Metadata + subtitles + download | ~15MB | Yes (weekly releases) | Yes (`YoutubeDL` class) | Unlicense |
| pytube | YouTube download | ~1MB | Inconsistent | Yes | MIT |
| youtube-dl | Download (original) | ~10MB | Stale | Yes | Unlicense |
| pafy | YouTube metadata | ~50KB | Dead (2021) | Yes | LGPL |

**Winner: yt-dlp** — De-facto standard, actively maintained, comprehensive Python API, supports 1000+ sites (not just YouTube).

### Transcript Extraction (YouTube)

| Library | Purpose | Requires Download | Speed | Accuracy | License |
|---------|---------|-------------------|-------|----------|---------|
| **youtube-transcript-api** | YouTube captions | No | Very fast (<1s) | Depends on caption source | MIT |
| yt-dlp subtitles | Download subtitle files | Yes (subtitle only) | Fast (~2s) | Same as above | Unlicense |

**Winner: youtube-transcript-api** — Fastest, no download needed, returns structured JSON with timestamps directly. Falls back to yt-dlp for non-YouTube platforms.

### Speech-to-Text (ASR)

| Library | Speed (30 min audio) | Word Timestamps | Model Sizes | GPU Required | Language Support | License |
|---------|---------------------|----------------|-------------|-------------|-----------------|---------|
| **faster-whisper** | ~2-4 min (GPU), ~8-15 min (CPU) | Yes (`word_timestamps=True`) | tiny (39M) → large-v3 (1.5B) | No (but recommended) | 99 languages | MIT |
| openai-whisper | ~5-10 min (GPU), ~20-40 min (CPU) | Yes | Same models | Recommended | 99 languages | MIT |
| whisper-timestamped | Same as openai-whisper | Yes (more accurate) | Same models | Recommended | 99 languages | MIT |
| whisperx | ~2-3 min (GPU) | Yes (best accuracy via wav2vec2) | Same + wav2vec2 | Yes (required) | 99 languages | BSD |
| stable-ts | Same as openai-whisper | Yes (stabilized) | Same models | Recommended | 99 languages | MIT |
| Google Speech-to-Text | Real-time | Yes | Cloud | No | 125+ languages | Proprietary |
| AssemblyAI | Real-time | Yes | Cloud | No | 100+ languages | Proprietary |

**Winner: faster-whisper** — 4x faster than OpenAI Whisper via CTranslate2 optimization, MIT license, word-level timestamps, works without GPU (just slower), actively maintained. We may consider whisperx as a future upgrade for speaker diarization.

### Scene Detection & Frame Extraction

| Library | Purpose | Algorithm | Speed | License |
|---------|---------|-----------|-------|---------|
| **PySceneDetect** | Scene boundary detection | ContentDetector, ThresholdDetector, AdaptiveDetector | Fast | BSD |
| opencv-python-headless | Frame extraction, image processing | Manual (absdiff, histogram) | Fast | Apache 2.0 |
| Filmstrip | Keyframe extraction | Scene detection + selection | Medium | MIT |
| video-keyframe-detector | Keyframe extraction | Peak estimation from frame diff | Fast | MIT |
| decord | GPU-accelerated frame extraction | Direct frame access | Very fast | Apache 2.0 |

**Winner: PySceneDetect + opencv-python-headless** — PySceneDetect handles intelligent boundary detection, OpenCV handles frame extraction and image processing. Both are well-maintained and BSD/Apache licensed.

### OCR (Optical Character Recognition)

| Library | Languages | GPU Support | Accuracy on Code | Speed | Install Size | License |
|---------|-----------|------------|-------------------|-------|-------------|---------|
| **easyocr** | 80+ | Yes (PyTorch) | Good | Medium | ~150MB + models | Apache 2.0 |
| pytesseract | 100+ | No | Medium | Fast | ~30MB + Tesseract | Apache 2.0 |
| PaddleOCR | 80+ | Yes (PaddlePaddle) | Very Good | Fast | ~200MB + models | Apache 2.0 |
| TrOCR (HuggingFace) | Multilingual | Yes | Good | Slow | ~500MB | MIT |
| docTR | 10+ | Yes (TF/PyTorch) | Good | Medium | ~100MB | Apache 2.0 |

**Winner: easyocr** — Best balance of accuracy (especially on code/terminal text), GPU support, language coverage, and ease of use. PaddleOCR is a close second but has heavier dependencies (PaddlePaddle framework).

---

## Detailed Library Analysis

### 1. yt-dlp (Metadata & Download Engine)

**What it provides:**
- Video metadata (title, description, duration, upload date, channel, tags, categories)
- Chapter information (title, start_time, end_time for each chapter)
- Subtitle/caption download (all available languages, all formats)
- Thumbnail URLs
- View/like counts
- Playlist information (title, entries, ordering)
- Audio-only extraction (no full video download needed)
- Supports 1000+ video sites (YouTube, Vimeo, Dailymotion, etc.)

**Python API usage:**

```python
from yt_dlp import YoutubeDL

def extract_video_metadata(url: str) -> dict:
    """Extract metadata without downloading."""
    opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,  # Full extraction
    }
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info
```

**Key fields in `info_dict`:**

```python
{
    'id': 'dQw4w9WgXcQ',              # Video ID
    'title': 'Video Title',            # Full title
    'description': '...',              # Full description text
    'duration': 1832,                  # Duration in seconds
    'upload_date': '20260115',         # YYYYMMDD format
    'uploader': 'Channel Name',        # Channel/uploader name
    'uploader_id': '@channelname',     # Channel ID
    'uploader_url': 'https://...',     # Channel URL
    'channel_follower_count': 150000,  # Subscriber count
    'view_count': 5000000,             # View count
    'like_count': 120000,              # Like count
    'comment_count': 8500,             # Comment count
    'tags': ['react', 'hooks', ...],   # Video tags
    'categories': ['Education'],        # YouTube categories
    'language': 'en',                  # Primary language
    'subtitles': {                     # Manual captions
        'en': [{'ext': 'vtt', 'url': '...'}],
    },
    'automatic_captions': {            # Auto-generated captions
        'en': [{'ext': 'vtt', 'url': '...'}],
    },
    'chapters': [                      # Chapter markers
        {'title': 'Intro', 'start_time': 0, 'end_time': 45},
        {'title': 'Setup', 'start_time': 45, 'end_time': 180},
        {'title': 'First Component', 'start_time': 180, 'end_time': 420},
    ],
    'thumbnail': 'https://...',        # Best thumbnail URL
    'thumbnails': [...],               # All thumbnail variants
    'webpage_url': 'https://...',      # Canonical URL
    'formats': [...],                  # Available formats
    'requested_formats': [...],        # Selected format info
}
```

**Playlist extraction:**

```python
def extract_playlist(url: str) -> list[dict]:
    """Extract all videos from a playlist."""
    opts = {
        'quiet': True,
        'extract_flat': True,  # Don't extract each video yet
    }
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        # info['entries'] contains all video entries
        return info.get('entries', [])
```

**Audio-only download (for Whisper):**

```python
def download_audio(url: str, output_dir: str) -> str:
    """Download audio stream only (no video)."""
    opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '16',  # 16kHz (Whisper's native rate)
        }],
        'outtmpl': f'{output_dir}/%(id)s.%(ext)s',
        'quiet': True,
    }
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return f"{output_dir}/{info['id']}.wav"
```

### 2. youtube-transcript-api (Caption Extraction)

**What it provides:**
- Direct access to YouTube captions without downloading
- Manual and auto-generated caption support
- Translation support (translate captions to any language)
- Structured output with timestamps

**Python API usage:**

```python
from youtube_transcript_api import YouTubeTranscriptApi

def get_youtube_transcript(video_id: str, languages: list[str] = None) -> list[dict]:
    """Get transcript with timestamps."""
    languages = languages or ['en']

    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

    # Prefer manual captions over auto-generated
    try:
        transcript = transcript_list.find_manually_created_transcript(languages)
    except Exception:
        transcript = transcript_list.find_generated_transcript(languages)

    # Fetch the actual transcript data
    data = transcript.fetch()
    return data
    # Returns: [{'text': 'Hello', 'start': 0.0, 'duration': 1.5}, ...]
```

**Output format:**

```python
[
    {
        'text': "Welcome to this React tutorial",
        'start': 0.0,        # Start time in seconds
        'duration': 2.5       # Duration in seconds
    },
    {
        'text': "Today we'll learn about hooks",
        'start': 2.5,
        'duration': 3.0
    },
    # ... continues for entire video
]
```

**Key features:**
- Segments are typically 2-5 seconds each
- Manual captions have punctuation and proper casing
- Auto-generated captions may lack punctuation and have lower accuracy
- Can detect available languages and caption types

### 3. faster-whisper (Speech-to-Text)

**What it provides:**
- OpenAI Whisper models with 4x speedup via CTranslate2
- Word-level timestamps with confidence scores
- Language detection
- VAD (Voice Activity Detection) filtering
- Multiple model sizes from tiny (39M) to large-v3 (1.5B)

**Python API usage:**

```python
from faster_whisper import WhisperModel

def transcribe_with_whisper(audio_path: str, model_size: str = "base") -> dict:
    """Transcribe audio file with word-level timestamps."""
    model = WhisperModel(
        model_size,
        device="auto",          # auto-detect GPU/CPU
        compute_type="auto",    # auto-select precision
    )

    segments, info = model.transcribe(
        audio_path,
        word_timestamps=True,
        vad_filter=True,         # Filter silence
        vad_parameters={
            "min_silence_duration_ms": 500,
        },
    )

    result = {
        'language': info.language,
        'language_probability': info.language_probability,
        'duration': info.duration,
        'segments': [],
    }

    for segment in segments:
        seg_data = {
            'start': segment.start,
            'end': segment.end,
            'text': segment.text.strip(),
            'avg_logprob': segment.avg_logprob,
            'no_speech_prob': segment.no_speech_prob,
            'words': [],
        }
        if segment.words:
            for word in segment.words:
                seg_data['words'].append({
                    'word': word.word,
                    'start': word.start,
                    'end': word.end,
                    'probability': word.probability,
                })
        result['segments'].append(seg_data)

    return result
```

**Model size guide:**

| Model | Parameters | English WER | Multilingual WER | VRAM (FP16) | Speed (30 min, GPU) |
|-------|-----------|-------------|------------------|-------------|---------------------|
| tiny | 39M | 14.8% | 23.2% | ~1GB | ~30s |
| base | 74M | 11.5% | 18.7% | ~1GB | ~45s |
| small | 244M | 9.5% | 14.6% | ~2GB | ~90s |
| medium | 769M | 8.0% | 12.4% | ~5GB | ~180s |
| large-v3 | 1.5B | 5.7% | 10.1% | ~10GB | ~240s |
| large-v3-turbo | 809M | 6.2% | 10.8% | ~6GB | ~120s |

**Recommendation:** Default to `base` (good balance), offer `large-v3-turbo` for best accuracy, `tiny` for speed.

### 4. PySceneDetect (Scene Boundary Detection)

**What it provides:**
- Automatic scene/cut detection in video files
- Multiple detection algorithms (content-based, threshold, adaptive)
- Frame-accurate boundaries
- Integration with OpenCV

**Python API usage:**

```python
from scenedetect import detect, ContentDetector, AdaptiveDetector

def detect_scene_changes(video_path: str) -> list[tuple[float, float]]:
    """Detect scene boundaries in video.

    Returns list of (start_time, end_time) tuples.
    """
    scene_list = detect(
        video_path,
        ContentDetector(
            threshold=27.0,      # Sensitivity (lower = more scenes)
            min_scene_len=15,    # Minimum 15 frames per scene
        ),
    )

    boundaries = []
    for scene in scene_list:
        start = scene[0].get_seconds()
        end = scene[1].get_seconds()
        boundaries.append((start, end))

    return boundaries
```

**Detection algorithms:**

| Algorithm | Best For | Speed | Sensitivity |
|-----------|----------|-------|-------------|
| ContentDetector | General content changes | Fast | Medium |
| AdaptiveDetector | Gradual transitions | Medium | High |
| ThresholdDetector | Hard cuts (black frames) | Very fast | Low |

### 5. easyocr (Text Recognition)

**What it provides:**
- Text detection and recognition from images
- 80+ language support
- GPU acceleration
- Bounding box coordinates for each text region
- Confidence scores

**Python API usage:**

```python
import easyocr

def extract_text_from_frame(image_path: str, languages: list[str] = None) -> list[dict]:
    """Extract text from a video frame image."""
    languages = languages or ['en']
    reader = easyocr.Reader(languages, gpu=True)

    results = reader.readtext(image_path)
    # results: [([x1,y1],[x2,y2],[x3,y3],[x4,y4]), text, confidence]

    extracted = []
    for bbox, text, confidence in results:
        extracted.append({
            'text': text,
            'confidence': confidence,
            'bbox': bbox,  # Corner coordinates
        })

    return extracted
```

**Tips for code/terminal OCR:**
- Pre-process images: increase contrast, convert to grayscale
- Use higher DPI/resolution frames
- Filter by confidence threshold (>0.5 for code)
- Detect monospace regions first, then OCR only those regions

### 6. OpenCV (Frame Extraction)

**What it provides:**
- Video file reading and frame extraction
- Image processing (resize, crop, color conversion)
- Template matching (detect code editors, terminals)
- Histogram analysis (detect slide vs code vs webcam)

**Python API usage:**

```python
import cv2
import numpy as np

def extract_frames_at_timestamps(
    video_path: str,
    timestamps: list[float],
    output_dir: str
) -> list[str]:
    """Extract frames at specific timestamps."""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_paths = []

    for ts in timestamps:
        frame_number = int(ts * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        if ret:
            path = f"{output_dir}/frame_{ts:.2f}.png"
            cv2.imwrite(path, frame)
            frame_paths.append(path)

    cap.release()
    return frame_paths


def classify_frame(image_path: str) -> str:
    """Classify frame as code/slide/terminal/webcam/other.

    Uses heuristics:
    - Dark background + monospace text regions = code/terminal
    - Light background + large text blocks = slide
    - Face detection = webcam
    - High color variance = diagram
    """
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # Check brightness distribution
    mean_brightness = np.mean(gray)
    brightness_std = np.std(gray)

    # Dark background with structured content = code/terminal
    if mean_brightness < 80 and brightness_std > 40:
        return 'code'  # or 'terminal'

    # Light background with text blocks = slide
    if mean_brightness > 180 and brightness_std < 60:
        return 'slide'

    # High edge density = diagram
    edges = cv2.Canny(gray, 50, 150)
    edge_density = np.count_nonzero(edges) / (h * w)
    if edge_density > 0.15:
        return 'diagram'

    return 'other'
```

---

## Benchmarks & Performance Data

### Transcript Extraction Speed

| Method | 10 min video | 30 min video | 60 min video | Requires Download |
|--------|-------------|-------------|-------------|-------------------|
| youtube-transcript-api | ~0.5s | ~0.5s | ~0.5s | No |
| yt-dlp subtitles | ~2s | ~2s | ~2s | Subtitle file only |
| faster-whisper (tiny, GPU) | ~10s | ~30s | ~60s | Audio only |
| faster-whisper (base, GPU) | ~15s | ~45s | ~90s | Audio only |
| faster-whisper (large-v3, GPU) | ~80s | ~240s | ~480s | Audio only |
| faster-whisper (base, CPU) | ~60s | ~180s | ~360s | Audio only |

### Visual Extraction Speed

| Operation | Per Frame | Per 10 min video (50 keyframes) |
|-----------|----------|-------------------------------|
| Frame extraction (OpenCV) | ~5ms | ~0.25s |
| Scene detection (PySceneDetect) | N/A | ~15s for full video |
| Frame classification (heuristic) | ~10ms | ~0.5s |
| OCR per frame (easyocr, GPU) | ~200ms | ~10s |
| OCR per frame (easyocr, CPU) | ~1-2s | ~50-100s |

### Total Pipeline Time (estimated)

| Mode | 10 min video | 30 min video | 1 hour video |
|------|-------------|-------------|-------------|
| Transcript only (YouTube captions) | ~2s | ~2s | ~2s |
| Transcript only (Whisper base, GPU) | ~20s | ~50s | ~100s |
| Full (transcript + visual, GPU) | ~35s | ~80s | ~170s |
| Full (transcript + visual, CPU) | ~120s | ~350s | ~700s |

---

## Recommendations

### Primary Stack (Chosen)

| Component | Library | Why |
|-----------|---------|-----|
| Metadata + download | **yt-dlp** | De-facto standard, 1000+ sites, comprehensive Python API |
| YouTube transcripts | **youtube-transcript-api** | Fastest, no download, structured output |
| Speech-to-text | **faster-whisper** | 4x faster than Whisper, MIT, word timestamps |
| Scene detection | **PySceneDetect** | Best algorithm options, OpenCV-based |
| Frame extraction | **opencv-python-headless** | Standard, headless (no GUI deps) |
| OCR | **easyocr** | Best code/terminal accuracy, 80+ languages, GPU support |

### Future Considerations

| Component | Library | When to Add |
|-----------|---------|-------------|
| Speaker diarization | **whisperx** or **pyannote** | V2.0 — identify who said what |
| Object detection | **YOLO** | V2.0 — detect UI elements, diagrams |
| Multimodal embeddings | **CLIP** | V2.0 — embed frames for visual search |
| Slide detection | **python-pptx** + heuristics | V1.5 — detect and extract slide content |

### Sources

- [youtube-transcript-api (PyPI)](https://pypi.org/project/youtube-transcript-api/)
- [yt-dlp GitHub](https://github.com/yt-dlp/yt-dlp)
- [yt-dlp Information Extraction Pipeline (DeepWiki)](https://deepwiki.com/yt-dlp/yt-dlp/2.2-information-extraction-pipeline)
- [faster-whisper GitHub](https://github.com/SYSTRAN/faster-whisper)
- [faster-whisper (PyPI)](https://pypi.org/project/faster-whisper/)
- [whisper-timestamped GitHub](https://github.com/linto-ai/whisper-timestamped)
- [stable-ts (PyPI)](https://pypi.org/project/stable-ts/)
- [PySceneDetect GitHub](https://github.com/Breakthrough/PySceneDetect)
- [easyocr GitHub (implied from PyPI)](https://pypi.org/project/easyocr/)
- [NVIDIA Multimodal RAG for Video and Audio](https://developer.nvidia.com/blog/an-easy-introduction-to-multimodal-retrieval-augmented-generation-for-video-and-audio/)
- [LlamaIndex MultiModal RAG for Video](https://www.llamaindex.ai/blog/multimodal-rag-for-advanced-video-processing-with-llamaindex-lancedb-33be4804822e)
- [Ragie: How We Built Multimodal RAG](https://www.ragie.ai/blog/how-we-built-multimodal-rag-for-audio-and-video)
- [video-analyzer GitHub](https://github.com/byjlw/video-analyzer)
- [VideoRAG Project](https://video-rag.github.io/)
- [video-keyframe-detector GitHub](https://github.com/joelibaceta/video-keyframe-detector)
- [Filmstrip GitHub](https://github.com/tafsiri/filmstrip)
