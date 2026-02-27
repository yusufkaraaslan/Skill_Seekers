# Video Source — Processing Pipeline

**Date:** February 27, 2026
**Document:** 03 of 07
**Status:** Planning

---

## Table of Contents

1. [Pipeline Overview](#pipeline-overview)
2. [Phase 1: Source Resolution](#phase-1-source-resolution)
3. [Phase 2: Metadata Extraction](#phase-2-metadata-extraction)
4. [Phase 3: Transcript Extraction](#phase-3-transcript-extraction)
5. [Phase 4: Visual Extraction](#phase-4-visual-extraction)
6. [Phase 5: Segmentation & Alignment](#phase-5-segmentation--alignment)
7. [Phase 6: Output Generation](#phase-6-output-generation)
8. [Error Handling](#error-handling)
9. [Caching Strategy](#caching-strategy)
10. [Performance Optimization](#performance-optimization)

---

## Pipeline Overview

The video processing pipeline has **6 sequential phases**, with Phases 3 and 4 running in parallel where possible:

```
Phase 1: RESOLVE     What videos are we processing?
   │                 Input: URL/path/playlist → list of video URLs/paths
   ▼
Phase 2: METADATA    What do we know about each video?
   │                 yt-dlp extract_info() → VideoInfo (metadata only)
   ▼
   ├──────────────────────────────────┐
   │                                  │
Phase 3: TRANSCRIPT               Phase 4: VISUAL (optional)
   │  What was said?                  │  What was shown?
   │  YouTube API / Whisper           │  PySceneDetect + OpenCV + easyocr
   │  → list[TranscriptSegment]       │  → list[KeyFrame]
   │                                  │
   └──────────────────────────────────┘
   │
   ▼
Phase 5: SEGMENT & ALIGN    Merge streams into structured segments
   │                        → list[VideoSegment]
   ▼
Phase 6: OUTPUT              Generate reference files + SKILL.md section
                             → video_*.md + video_data/*.json
```

---

## Phase 1: Source Resolution

**Purpose:** Take user input and resolve it to a concrete list of videos to process.

### Input Types

| Input | Resolution Strategy |
|-------|-------------------|
| YouTube video URL | Direct — single video |
| YouTube short URL (youtu.be) | Expand to full URL — single video |
| YouTube playlist URL | yt-dlp `extract_flat=True` → list of video URLs |
| YouTube channel URL | yt-dlp channel extraction → list of video URLs |
| Vimeo video URL | Direct — single video |
| Local video file | Direct — single file |
| Local directory | Glob for video extensions → list of file paths |

### Algorithm

```
resolve_source(input, config) -> list[VideoTarget]:

    1. Determine source type:
       - YouTube video URL? → [VideoTarget(url=input)]
       - YouTube playlist?  → extract_playlist(input) → filter → [VideoTarget(url=...), ...]
       - YouTube channel?   → extract_channel_videos(input) → filter → [VideoTarget(url=...), ...]
       - Vimeo URL?         → [VideoTarget(url=input)]
       - Local file?        → [VideoTarget(path=input)]
       - Local directory?   → glob(directory, config.file_patterns) → [VideoTarget(path=...), ...]

    2. Apply filters from config:
       - max_videos: Limit total video count
       - title_include_patterns: Only include matching titles
       - title_exclude_patterns: Exclude matching titles
       - min_views: Filter by minimum view count (online only)
       - upload_after: Filter by upload date (online only)

    3. Sort by relevance:
       - Playlists: Keep playlist order
       - Channels: Sort by view count (most popular first)
       - Directories: Sort by filename

    4. Return filtered, sorted list of VideoTarget objects
```

### Playlist Resolution Detail

```python
def resolve_playlist(playlist_url: str, config: VideoSourceConfig) -> list[VideoTarget]:
    """Resolve a YouTube playlist to individual video targets.

    Uses yt-dlp's extract_flat mode for fast playlist metadata
    without downloading each video's full info.
    """
    opts = {
        'quiet': True,
        'extract_flat': True,      # Only get video IDs and titles
        'playlistend': config.max_videos,  # Limit early
    }
    with YoutubeDL(opts) as ydl:
        playlist_info = ydl.extract_info(playlist_url, download=False)

    targets = []
    for i, entry in enumerate(playlist_info.get('entries', [])):
        video_url = f"https://www.youtube.com/watch?v={entry['id']}"
        target = VideoTarget(
            url=video_url,
            video_id=entry['id'],
            title=entry.get('title', ''),
            playlist_title=playlist_info.get('title', ''),
            playlist_index=i,
            playlist_total=len(playlist_info.get('entries', [])),
        )

        # Apply title filters
        if config.title_include_patterns:
            if not any(p.lower() in target.title.lower()
                      for p in config.title_include_patterns):
                continue
        if config.title_exclude_patterns:
            if any(p.lower() in target.title.lower()
                  for p in config.title_exclude_patterns):
                continue

        targets.append(target)

    return targets[:config.max_videos]
```

### Local Directory Resolution

```python
def resolve_local_directory(
    directory: str,
    config: VideoSourceConfig
) -> list[VideoTarget]:
    """Resolve a local directory to video file targets.

    Also discovers associated subtitle files (.srt, .vtt) for each video.
    """
    VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.webm', '.avi', '.mov', '.flv', '.ts', '.wmv'}
    SUBTITLE_EXTENSIONS = {'.srt', '.vtt', '.ass', '.ssa'}

    patterns = config.file_patterns or [f'*{ext}' for ext in VIDEO_EXTENSIONS]
    subtitle_patterns = config.subtitle_patterns or [f'*{ext}' for ext in SUBTITLE_EXTENSIONS]

    video_files = []
    for pattern in patterns:
        if config.recursive:
            video_files.extend(Path(directory).rglob(pattern))
        else:
            video_files.extend(Path(directory).glob(pattern))

    # Build subtitle lookup (video_name -> subtitle_path)
    subtitle_lookup = {}
    for pattern in subtitle_patterns:
        for sub_file in Path(directory).rglob(pattern):
            stem = sub_file.stem
            subtitle_lookup[stem] = str(sub_file)

    targets = []
    for video_file in sorted(video_files):
        subtitle_path = subtitle_lookup.get(video_file.stem)
        target = VideoTarget(
            path=str(video_file),
            video_id=hashlib.sha256(str(video_file).encode()).hexdigest()[:16],
            title=video_file.stem,
            subtitle_path=subtitle_path,
        )
        targets.append(target)

    return targets[:config.max_videos]
```

---

## Phase 2: Metadata Extraction

**Purpose:** Extract full metadata for each video without downloading content.

### Algorithm

```
extract_metadata(target: VideoTarget) -> VideoInfo:

    IF target.url is set (online video):
        1. Call yt-dlp extract_info(url, download=False)
        2. Parse info_dict into VideoInfo fields:
           - Basic: title, description, duration, upload_date
           - Channel: channel_name, channel_url, subscriber_count
           - Engagement: view_count, like_count, comment_count
           - Discovery: tags, categories, language, thumbnail_url
           - Structure: chapters (list of Chapter objects)
           - Playlist: playlist_title, playlist_index (from target)
        3. Apply duration filter (skip if < min_duration or > max_duration)
        4. Apply view count filter (skip if < min_views)

    ELIF target.path is set (local file):
        1. Use ffprobe (via subprocess) or yt-dlp for local metadata:
           - Duration
           - Resolution
           - Codec info
        2. Check for sidecar metadata files:
           - {filename}.json (custom metadata)
           - {filename}.nfo (media info)
        3. Check for sidecar subtitle files:
           - {filename}.srt
           - {filename}.vtt
        4. Generate VideoInfo with available metadata:
           - Title from filename (cleaned)
           - Duration from ffprobe
           - Other fields set to None/empty

    Return VideoInfo (transcript and segments still empty)
```

### Metadata Fields from yt-dlp

```python
def parse_ytdlp_metadata(info: dict, target: VideoTarget) -> VideoInfo:
    """Convert yt-dlp info_dict to our VideoInfo model."""

    # Parse chapters
    chapters = []
    raw_chapters = info.get('chapters') or []
    for i, ch in enumerate(raw_chapters):
        end_time = ch.get('end_time')
        if end_time is None and i + 1 < len(raw_chapters):
            end_time = raw_chapters[i + 1]['start_time']
        elif end_time is None:
            end_time = info.get('duration', 0)
        chapters.append(Chapter(
            title=ch.get('title', f'Chapter {i + 1}'),
            start_time=ch.get('start_time', 0),
            end_time=end_time,
        ))

    # Determine source type
    if 'youtube' in info.get('extractor', '').lower():
        source_type = VideoSourceType.YOUTUBE
    elif 'vimeo' in info.get('extractor', '').lower():
        source_type = VideoSourceType.VIMEO
    else:
        source_type = VideoSourceType.LOCAL_FILE

    return VideoInfo(
        video_id=info.get('id', target.video_id),
        source_type=source_type,
        source_url=info.get('webpage_url', target.url),
        file_path=target.path,
        title=info.get('title', target.title or 'Untitled'),
        description=info.get('description', ''),
        duration=info.get('duration', 0.0),
        upload_date=_parse_date(info.get('upload_date')),
        language=info.get('language', 'unknown'),
        channel_name=info.get('uploader') or info.get('channel'),
        channel_url=info.get('uploader_url') or info.get('channel_url'),
        channel_subscriber_count=info.get('channel_follower_count'),
        view_count=info.get('view_count'),
        like_count=info.get('like_count'),
        comment_count=info.get('comment_count'),
        tags=info.get('tags') or [],
        categories=info.get('categories') or [],
        thumbnail_url=info.get('thumbnail'),
        chapters=chapters,
        playlist_title=target.playlist_title,
        playlist_index=target.playlist_index,
        playlist_total=target.playlist_total,
        raw_transcript=[],  # Populated in Phase 3
        segments=[],        # Populated in Phase 5
        transcript_source=TranscriptSource.NONE,  # Updated in Phase 3
        visual_extraction_enabled=False,  # Updated in Phase 4
        whisper_model=None,
        processing_time_seconds=0.0,
        extracted_at='',
        transcript_confidence=0.0,
        content_richness_score=0.0,
    )
```

---

## Phase 3: Transcript Extraction

**Purpose:** Extract the spoken content of the video as timestamped text.

### Decision Tree

```
get_transcript(video_info, config) -> list[TranscriptSegment]:

    IF video is YouTube:
        TRY youtube-transcript-api:
            1. List available transcripts
            2. Prefer manual captions in user's language
            3. Fall back to auto-generated captions
            4. Fall back to translated captions
            IF success:
                SET transcript_source = YOUTUBE_MANUAL or YOUTUBE_AUTO
                RETURN parsed transcript segments

        IF youtube-transcript-api fails:
            TRY yt-dlp subtitle download:
                1. Download subtitle in best available format (VTT preferred)
                2. Parse VTT/SRT into segments
                IF success:
                    SET transcript_source = SUBTITLE_FILE
                    RETURN parsed transcript segments

    IF video is local AND has sidecar subtitle file:
        1. Parse SRT/VTT file into segments
        SET transcript_source = SUBTITLE_FILE
        RETURN parsed transcript segments

    IF no transcript found AND Whisper is available:
        1. Extract audio from video (yt-dlp for online, ffmpeg for local)
        2. Run faster-whisper with word_timestamps=True
        3. Parse Whisper output into TranscriptSegment objects
        SET transcript_source = WHISPER
        RETURN parsed transcript segments

    IF no transcript and no Whisper:
        LOG warning: "No transcript available for {video_id}"
        SET transcript_source = NONE
        RETURN empty list
```

### YouTube Transcript Extraction (Detail)

```python
def extract_youtube_transcript(
    video_id: str,
    preferred_languages: list[str] | None = None,
    confidence_threshold: float = 0.3,
) -> tuple[list[TranscriptSegment], TranscriptSource]:
    """Extract transcript from YouTube captions.

    Priority:
    1. Manual captions in preferred language
    2. Manual captions in any language (with translation)
    3. Auto-generated captions in preferred language
    4. Auto-generated captions in any language (with translation)
    """
    preferred_languages = preferred_languages or ['en']

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    except Exception as e:
        raise TranscriptNotAvailable(f"No transcripts for {video_id}: {e}")

    # Strategy 1: Manual captions in preferred language
    transcript = None
    source = TranscriptSource.YOUTUBE_MANUAL
    try:
        transcript = transcript_list.find_manually_created_transcript(preferred_languages)
    except Exception:
        pass

    # Strategy 2: Auto-generated in preferred language
    if transcript is None:
        source = TranscriptSource.YOUTUBE_AUTO
        try:
            transcript = transcript_list.find_generated_transcript(preferred_languages)
        except Exception:
            pass

    # Strategy 3: Any manual caption, translated
    if transcript is None:
        source = TranscriptSource.YOUTUBE_MANUAL
        for t in transcript_list:
            if not t.is_generated:
                try:
                    transcript = t.translate(preferred_languages[0])
                    break
                except Exception:
                    continue

    # Strategy 4: Any auto-generated, translated
    if transcript is None:
        source = TranscriptSource.YOUTUBE_AUTO
        for t in transcript_list:
            if t.is_generated:
                try:
                    transcript = t.translate(preferred_languages[0])
                    break
                except Exception:
                    continue

    if transcript is None:
        raise TranscriptNotAvailable(f"No usable transcript for {video_id}")

    # Fetch and parse
    raw_data = transcript.fetch()
    segments = []
    for item in raw_data:
        confidence = 1.0 if source == TranscriptSource.YOUTUBE_MANUAL else 0.8
        segments.append(TranscriptSegment(
            text=item['text'],
            start=item['start'],
            end=item['start'] + item.get('duration', 0),
            confidence=confidence,
            words=None,  # YouTube API doesn't provide word-level
            source=source,
        ))

    return segments, source
```

### Whisper Transcription (Detail)

```python
def transcribe_with_whisper(
    video_info: VideoInfo,
    config: VideoSourceConfig,
    output_dir: str,
) -> tuple[list[TranscriptSegment], str]:
    """Transcribe video audio using faster-whisper.

    Steps:
    1. Extract audio from video (download if online)
    2. Load Whisper model
    3. Transcribe with word-level timestamps
    4. Convert to TranscriptSegment objects

    Returns:
        (segments, model_name) tuple
    """
    # Step 1: Get audio file
    if video_info.source_url and not video_info.file_path:
        # Download audio only (no video)
        audio_path = download_audio_only(
            video_info.source_url,
            output_dir=output_dir,
        )
    elif video_info.file_path:
        # Extract audio from local file
        audio_path = extract_audio_ffmpeg(
            video_info.file_path,
            output_dir=output_dir,
        )
    else:
        raise ValueError("No source URL or file path available")

    # Step 2: Load model
    model = WhisperModel(
        config.whisper_model,
        device=config.whisper_device,
        compute_type="auto",
    )

    # Step 3: Transcribe
    whisper_segments, info = model.transcribe(
        audio_path,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
        language=video_info.language if video_info.language != 'unknown' else None,
    )

    # Update video language if detected
    if video_info.language == 'unknown':
        video_info.language = info.language

    # Step 4: Convert to our format
    segments = []
    for seg in whisper_segments:
        words = []
        if seg.words:
            for w in seg.words:
                words.append(WordTimestamp(
                    word=w.word.strip(),
                    start=w.start,
                    end=w.end,
                    probability=w.probability,
                ))

        segments.append(TranscriptSegment(
            text=seg.text.strip(),
            start=seg.start,
            end=seg.end,
            confidence=_compute_segment_confidence(seg),
            words=words if words else None,
            source=TranscriptSource.WHISPER,
        ))

    # Cleanup audio file
    if os.path.exists(audio_path):
        os.remove(audio_path)

    return segments, config.whisper_model


def download_audio_only(url: str, output_dir: str) -> str:
    """Download only the audio stream using yt-dlp.

    Converts to WAV at 16kHz mono (Whisper's native format).
    This is 10-50x smaller than downloading full video.
    """
    opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }],
        'postprocessor_args': {
            'ffmpeg': ['-ar', '16000', '-ac', '1'],  # 16kHz mono
        },
        'outtmpl': f'{output_dir}/audio_%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return f"{output_dir}/audio_{info['id']}.wav"


def extract_audio_ffmpeg(video_path: str, output_dir: str) -> str:
    """Extract audio from local video file using FFmpeg.

    Converts to WAV at 16kHz mono for Whisper.
    """
    stem = Path(video_path).stem
    output_path = f"{output_dir}/audio_{stem}.wav"
    subprocess.run([
        'ffmpeg', '-i', video_path,
        '-vn',                  # No video
        '-ar', '16000',         # 16kHz sample rate
        '-ac', '1',             # Mono
        '-f', 'wav',            # WAV format
        output_path,
        '-y',                   # Overwrite
        '-loglevel', 'quiet',
    ], check=True)
    return output_path
```

### Subtitle File Parsing

```python
def parse_subtitle_file(subtitle_path: str) -> list[TranscriptSegment]:
    """Parse SRT or VTT subtitle file into transcript segments.

    Supports:
    - SRT (.srt): SubRip format
    - VTT (.vtt): WebVTT format
    """
    ext = Path(subtitle_path).suffix.lower()

    if ext == '.srt':
        return _parse_srt(subtitle_path)
    elif ext == '.vtt':
        return _parse_vtt(subtitle_path)
    else:
        raise ValueError(f"Unsupported subtitle format: {ext}")


def _parse_srt(path: str) -> list[TranscriptSegment]:
    """Parse SRT subtitle file.

    SRT format:
    1
    00:00:01,500 --> 00:00:04,000
    Welcome to the tutorial

    2
    00:00:04,500 --> 00:00:07,000
    Today we'll learn React
    """
    segments = []
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = content.strip().split('\n\n')
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue

        # Parse timestamp line
        time_line = lines[1]
        start_str, end_str = time_line.split(' --> ')
        start = _srt_time_to_seconds(start_str.strip())
        end = _srt_time_to_seconds(end_str.strip())

        # Join text lines
        text = ' '.join(lines[2:]).strip()
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        segments.append(TranscriptSegment(
            text=text,
            start=start,
            end=end,
            confidence=1.0,  # Subtitle files assumed accurate
            words=None,
            source=TranscriptSource.SUBTITLE_FILE,
        ))

    return segments
```

---

## Phase 4: Visual Extraction

**Purpose:** Extract and analyze visual content (code, slides, diagrams) from video frames.

**This phase is OPTIONAL** — only runs when `visual_extraction=True` in config or `--visual` CLI flag.

### Algorithm

```
extract_visual_content(video_info, config) -> list[KeyFrame]:

    1. GET VIDEO FILE:
       - If local file: use directly
       - If online: download video (lowest sufficient resolution)

    2. DETECT SCENE BOUNDARIES:
       - Run PySceneDetect ContentDetector on video
       - Get list of (start_time, end_time) for each scene
       - Filter by min_scene_change_score

    3. SELECT KEYFRAME TIMESTAMPS:
       For each segment (from chapters or scene boundaries):
         - Add frame at segment start
         - Add frames at scene change points within segment
         - Add frames at regular intervals (keyframe_interval seconds)
       Deduplicate timestamps within 1-second window

    4. EXTRACT FRAMES:
       For each selected timestamp:
         - Use OpenCV to extract frame at exact timestamp
         - Save as PNG to video_data/frames/{video_id}/

    5. CLASSIFY FRAMES:
       For each extracted frame:
         - Run frame classifier (heuristic-based):
           - Brightness analysis → dark bg = code/terminal
           - Edge density → high = diagram
           - Color distribution → uniform = slide
           - Face detection → webcam
         - Set frame_type

    6. OCR ON RELEVANT FRAMES:
       For each frame where frame_type in (code_editor, terminal, slide, diagram):
         - Run easyocr with appropriate languages
         - Parse OCR results into OCRRegion objects
         - Detect monospace text (code indicator)
         - Filter by confidence threshold
         - Combine regions into KeyFrame.ocr_text

    7. DETECT CODE BLOCKS:
       For frames classified as code_editor or terminal:
         - Group contiguous monospace OCR regions
         - Detect programming language (reuse detect_language from doc_scraper)
         - Create CodeBlock objects

    8. CLEANUP:
       - Remove downloaded video file (if downloaded)
       - Keep extracted frame images (for reference)

    RETURN list of KeyFrame objects with all analysis populated
```

### Scene Detection Detail

```python
def detect_keyframe_timestamps(
    video_path: str,
    chapters: list[Chapter],
    config: VideoSourceConfig,
) -> list[float]:
    """Determine which timestamps to extract frames at.

    Combines:
    1. Chapter boundaries
    2. Scene change detection
    3. Regular intervals

    Returns sorted, deduplicated list of timestamps in seconds.
    """
    timestamps = set()

    # Source 1: Chapter boundaries
    for chapter in chapters:
        timestamps.add(chapter.start_time)
        # Also add midpoint for long chapters
        if chapter.duration > 120:  # > 2 minutes
            timestamps.add(chapter.start_time + chapter.duration / 2)

    # Source 2: Scene change detection
    scene_list = detect(
        video_path,
        ContentDetector(threshold=27.0, min_scene_len=30),
    )
    for scene_start, scene_end in scene_list:
        ts = scene_start.get_seconds()
        timestamps.add(ts)

    # Source 3: Regular intervals (fill gaps)
    duration = get_video_duration(video_path)
    interval = config.keyframe_interval
    t = 0.0
    while t < duration:
        timestamps.add(t)
        t += interval

    # Sort and deduplicate (merge timestamps within 1 second)
    sorted_ts = sorted(timestamps)
    deduped = [sorted_ts[0]] if sorted_ts else []
    for ts in sorted_ts[1:]:
        if ts - deduped[-1] >= 1.0:
            deduped.append(ts)

    return deduped
```

### Frame Classification Detail

```python
def classify_frame(image_path: str) -> FrameType:
    """Classify a video frame based on visual characteristics.

    Uses heuristic analysis:
    - Background brightness (dark = code/terminal)
    - Text density and layout
    - Color distribution
    - Edge patterns

    This is a fast, deterministic classifier. More accurate
    classification could use a trained CNN, but heuristics
    are sufficient for our use case and run in <10ms per frame.
    """
    img = cv2.imread(image_path)
    if img is None:
        return FrameType.OTHER

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # === Metrics ===
    mean_brightness = float(np.mean(gray))
    brightness_std = float(np.std(gray))
    saturation_mean = float(np.mean(hsv[:, :, 1]))

    # Edge analysis
    edges = cv2.Canny(gray, 50, 150)
    edge_density = float(np.count_nonzero(edges)) / (h * w)

    # Top and bottom bar detection (common in slides)
    top_strip = gray[:int(h * 0.1), :]
    bottom_strip = gray[int(h * 0.9):, :]
    top_uniform = float(np.std(top_strip)) < 20
    bottom_uniform = float(np.std(bottom_strip)) < 20

    # === Classification Rules ===

    # Dark background with structured content → code or terminal
    if mean_brightness < 80:
        if edge_density > 0.05:
            # Has text/content on dark background
            if brightness_std > 50:
                return FrameType.CODE_EDITOR
            else:
                return FrameType.TERMINAL
        else:
            return FrameType.OTHER  # Just a dark frame

    # Light background, uniform, with text → slide
    if mean_brightness > 170 and brightness_std < 60 and saturation_mean < 50:
        if edge_density > 0.03:
            return FrameType.SLIDE
        else:
            return FrameType.OTHER  # Blank/near-blank frame

    # High edge density with moderate brightness → diagram
    if edge_density > 0.15 and 80 < mean_brightness < 200:
        return FrameType.DIAGRAM

    # Browser detection (address bar pattern)
    # Look for horizontal line near top of frame
    top_section = gray[:int(h * 0.15), :]
    horizontal_lines = cv2.HoughLinesP(
        cv2.Canny(top_section, 50, 150),
        1, np.pi / 180, threshold=100,
        minLineLength=int(w * 0.3), maxLineGap=10
    )
    if horizontal_lines is not None and len(horizontal_lines) > 0:
        return FrameType.BROWSER

    # Moderate brightness, some edges → general screencast
    if 80 < mean_brightness < 200 and edge_density > 0.02:
        return FrameType.SCREENCAST

    return FrameType.OTHER
```

---

## Phase 5: Segmentation & Alignment

**Purpose:** Combine the 3 streams (ASR + OCR + metadata) into structured `VideoSegment` objects aligned on the timeline.

### Segmentation Strategy

```
determine_segments(video_info, config) -> list[TimeWindow]:

    STRATEGY 1 - CHAPTERS (preferred):
        IF video has YouTube chapters:
            Use chapter boundaries directly
            Each chapter → one segment
            May split long chapters (> max_segment_duration)

    STRATEGY 2 - HYBRID (default):
        IF chapters available but sparse:
            Use chapters as primary boundaries
            Add scene change boundaries between chapters
            Merge very short scenes (< min_segment_duration)

    STRATEGY 3 - TIME WINDOW (fallback):
        IF no chapters and no good scene boundaries:
            Split into fixed-duration windows (config.time_window_seconds)
            Try to split at sentence boundaries in transcript
            Avoid splitting mid-sentence
```

### Alignment Algorithm

```
align_streams(
    time_windows: list[TimeWindow],
    transcript: list[TranscriptSegment],
    keyframes: list[KeyFrame],  # May be empty if visual extraction disabled
    chapters: list[Chapter],
) -> list[VideoSegment]:

    For each time_window:
        1. COLLECT TRANSCRIPT for this window:
           - Find all TranscriptSegments that overlap with [start, end]
           - For partial overlaps, include full segment if >50% overlaps
           - Concatenate text, collect words
           - Compute average confidence

        2. COLLECT KEYFRAMES for this window:
           - Find all KeyFrames where timestamp in [start, end]
           - Already classified and OCR'd in Phase 4

        3. COLLECT OCR TEXT:
           - Gather ocr_text from all keyframes in window
           - Deduplicate (same text in consecutive frames)
           - Identify code blocks

        4. MAP CHAPTER:
           - Find chapter that best overlaps this window
           - Set chapter_title

        5. DETERMINE CONTENT TYPE:
           - If has_code_on_screen and transcript mentions coding → LIVE_CODING
           - If has_slides → SLIDES
           - If mostly talking with no visual → EXPLANATION
           - etc.

        6. GENERATE MERGED CONTENT:
           - Start with transcript text
           - If code on screen not mentioned in transcript:
             Append: "\n\n**Code shown on screen:**\n```{language}\n{code}\n```"
           - If slide text adds info beyond transcript:
             Append: "\n\n**Slide content:**\n{slide_text}"
           - Prepend chapter title as heading if present

        7. DETECT CATEGORY:
           - Use smart_categorize logic from doc_scraper
           - Match chapter_title and transcript against category keywords
           - Set segment.category

        8. CREATE VideoSegment with all populated fields
```

### Content Merging Detail

```python
def merge_segment_content(
    transcript: str,
    keyframes: list[KeyFrame],
    code_blocks: list[CodeBlock],
    chapter_title: str | None,
    start_time: float,
    end_time: float,
) -> str:
    """Generate the final merged content for a segment.

    Merging rules:
    1. Chapter title becomes a heading with timestamp
    2. Transcript is the primary content
    3. Code blocks are inserted where contextually relevant
    4. Slide/diagram text supplements the transcript
    5. Duplicate information is not repeated
    """
    parts = []

    # Heading
    timestamp_str = _format_timestamp(start_time, end_time)
    if chapter_title:
        parts.append(f"### {chapter_title} ({timestamp_str})\n")
    else:
        parts.append(f"### Segment ({timestamp_str})\n")

    # Transcript (cleaned)
    cleaned_transcript = _clean_transcript(transcript)
    if cleaned_transcript:
        parts.append(cleaned_transcript)

    # Code blocks (if not already mentioned in transcript)
    for cb in code_blocks:
        # Check if code content appears in transcript already
        code_snippet = cb.code[:50]  # First 50 chars
        if code_snippet.lower() not in transcript.lower():
            lang = cb.language or ''
            context_label = {
                CodeContext.EDITOR: "Code shown in editor",
                CodeContext.TERMINAL: "Terminal command",
                CodeContext.SLIDE: "Code from slide",
                CodeContext.BROWSER: "Code from browser",
            }.get(cb.context, "Code shown on screen")

            parts.append(f"\n**{context_label}:**")
            parts.append(f"```{lang}\n{cb.code}\n```")

    # Slide text (supplementary)
    slide_frames = [kf for kf in keyframes if kf.frame_type == FrameType.SLIDE]
    for sf in slide_frames:
        if sf.ocr_text and sf.ocr_text.lower() not in transcript.lower():
            parts.append(f"\n**Slide:**\n{sf.ocr_text}")

    return '\n\n'.join(parts)
```

---

## Phase 6: Output Generation

**Purpose:** Convert processed VideoInfo and VideoSegments into reference files and SKILL.md integration.

See **[05_VIDEO_OUTPUT.md](./05_VIDEO_OUTPUT.md)** for full output format specification.

### Summary of Outputs

```
output/{skill_name}/
├── references/
│   ├── video_{sanitized_title}.md    # One per video, contains all segments
│   └── ...
├── video_data/
│   ├── metadata.json                 # All video metadata (VideoScraperResult)
│   ├── transcripts/
│   │   ├── {video_id}.json          # Raw transcript per video
│   │   └── ...
│   ├── segments/
│   │   ├── {video_id}_segments.json  # Aligned segments per video
│   │   └── ...
│   └── frames/                       # Only if visual extraction enabled
│       ├── {video_id}/
│       │   ├── frame_000.00.png
│       │   └── ...
│       └── ...
└── pages/
    └── video_{video_id}.json         # Page format for compatibility
```

---

## Error Handling

### Error Categories

| Error | Severity | Strategy |
|-------|----------|----------|
| Video not found (404) | Per-video | Skip, log warning, continue with others |
| Private/restricted video | Per-video | Skip, log warning |
| No transcript available | Per-video | Try Whisper fallback, then skip |
| Whisper model download fails | Fatal for Whisper | Fall back to no-transcript mode |
| FFmpeg not installed | Fatal for Whisper/visual | Clear error message with install instructions |
| Rate limited (YouTube) | Temporary | Exponential backoff, retry 3 times |
| Network timeout | Temporary | Retry 3 times with increasing timeout |
| Corrupt video file | Per-video | Skip, log error |
| OCR fails on frame | Per-frame | Skip frame, continue with others |
| Out of disk space | Fatal | Check space before download, clear error |
| GPU out of memory | Per-video | Fall back to CPU, log warning |

### Error Reporting

```python
@dataclass
class VideoError:
    """Error encountered during video processing."""
    video_id: str
    video_title: str
    phase: str          # 'resolve', 'metadata', 'transcript', 'visual', 'segment'
    error_type: str     # 'not_found', 'private', 'no_transcript', 'network', etc.
    message: str
    recoverable: bool
    timestamp: str      # ISO 8601

    def to_dict(self) -> dict:
        return {
            'video_id': self.video_id,
            'video_title': self.video_title,
            'phase': self.phase,
            'error_type': self.error_type,
            'message': self.message,
            'recoverable': self.recoverable,
        }
```

---

## Caching Strategy

### What Gets Cached

| Data | Cache Key | Location | TTL |
|------|-----------|----------|-----|
| yt-dlp metadata | `{video_id}_meta.json` | `video_data/cache/` | 7 days |
| YouTube transcript | `{video_id}_transcript.json` | `video_data/cache/` | 7 days |
| Whisper transcript | `{video_id}_whisper_{model}.json` | `video_data/cache/` | Permanent |
| Keyframes | `{video_id}/frame_*.png` | `video_data/frames/` | Permanent |
| OCR results | `{video_id}_ocr.json` | `video_data/cache/` | Permanent |
| Aligned segments | `{video_id}_segments.json` | `video_data/segments/` | Permanent |

### Cache Invalidation

- Metadata cache: Invalidated after 7 days (engagement numbers change)
- Transcript cache: Invalidated if video is re-uploaded or captions updated
- Whisper cache: Only invalidated if model changes
- Visual cache: Only invalidated if config changes (different threshold, interval)

### Resume Support

Video processing integrates with the existing `resume_command.py`:
- Progress saved after each video completes
- On resume: skip already-processed videos
- Resume point: per-video granularity

---

## Performance Optimization

### Parallel Processing

```
For a playlist of N videos:

Sequential bottleneck: Whisper transcription (GPU-bound)
Parallelizable: YouTube API calls, metadata extraction, OCR

Approach:
1. Phase 1-2 (resolve + metadata): Parallel HTTP requests (ThreadPool, max 5)
2. Phase 3 (transcript):
   - YouTube API calls: Parallel (ThreadPool, max 10)
   - Whisper: Sequential (GPU is the bottleneck)
3. Phase 4 (visual): Sequential per video (GPU-bound for OCR)
4. Phase 5-6 (segment + output): Parallel per video (CPU-bound, fast)
```

### Memory Management

- **Whisper model:** Load once, reuse across videos. Unload after all videos processed.
- **easyocr Reader:** Load once, reuse across frames. Unload after visual extraction.
- **OpenCV VideoCapture:** Open per video, close immediately after frame extraction.
- **Frames:** Save to disk immediately, don't hold in memory.

### Disk Space Management

| Content | Size per 30 min video | Notes |
|---------|----------------------|-------|
| Audio WAV (16kHz mono) | ~55 MB | Temporary, deleted after Whisper |
| Keyframes (50 frames) | ~15 MB | Permanent, compressed PNG |
| Transcript JSON | ~50 KB | Small |
| Segments JSON | ~100 KB | Small |
| Downloaded video (if needed) | ~200-500 MB | Temporary, deleted after visual extraction |

**Total permanent storage per video:** ~15-20 MB (with visual extraction), ~200 KB (transcript only).
