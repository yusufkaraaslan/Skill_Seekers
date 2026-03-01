# Video Source — Output Structure & SKILL.md Integration

**Date:** February 27, 2026
**Document:** 05 of 07
**Status:** Planning

---

## Table of Contents

1. [Output Directory Structure](#output-directory-structure)
2. [Reference File Format](#reference-file-format)
3. [SKILL.md Section Format](#skillmd-section-format)
4. [Metadata JSON Format](#metadata-json-format)
5. [Page JSON Format (Compatibility)](#page-json-format-compatibility)
6. [RAG Chunking for Video](#rag-chunking-for-video)
7. [Examples](#examples)

---

## Output Directory Structure

```
output/{skill_name}/
├── SKILL.md                              # Main skill file (video section added)
├── references/
│   ├── getting_started.md                # From docs (existing)
│   ├── api.md                            # From docs (existing)
│   ├── video_react-hooks-tutorial.md     # ← Video reference file
│   ├── video_project-setup-guide.md      # ← Video reference file
│   └── video_advanced-patterns.md        # ← Video reference file
├── video_data/                           # ← NEW: Video-specific data
│   ├── metadata.json                     # VideoScraperResult (full metadata)
│   ├── transcripts/
│   │   ├── abc123def45.json              # Raw transcript per video
│   │   ├── xyz789ghi01.json
│   │   └── ...
│   ├── segments/
│   │   ├── abc123def45_segments.json     # Aligned segments per video
│   │   ├── xyz789ghi01_segments.json
│   │   └── ...
│   └── frames/                           # Only if --visual enabled
│       ├── abc123def45/
│       │   ├── frame_045.00_terminal.png
│       │   ├── frame_052.30_code.png
│       │   ├── frame_128.00_slide.png
│       │   └── ...
│       └── xyz789ghi01/
│           └── ...
├── pages/                                # Existing page format
│   ├── page_001.json                     # From docs (existing)
│   ├── video_abc123def45.json            # ← Video in page format
│   └── ...
└── {skill_name}_data/                    # Raw scrape data (existing)
```

---

## Reference File Format

Each video produces one reference markdown file in `references/`. The filename is derived from the video title, sanitized and prefixed with `video_`.

### Naming Convention

```
video_{sanitized_title}.md
```

Sanitization rules:
- Lowercase
- Replace spaces and special chars with hyphens
- Remove consecutive hyphens
- Truncate to 60 characters
- Example: "React Hooks Tutorial for Beginners" → `video_react-hooks-tutorial-for-beginners.md`

### File Structure

```markdown
# {Video Title}

> **Source:** [{channel_name}]({channel_url}) | **Duration:** {HH:MM:SS} | **Published:** {date}
> **URL:** [{url}]({url})
> **Views:** {view_count} | **Likes:** {like_count}
> **Tags:** {tag1}, {tag2}, {tag3}

{description_summary (first 200 chars)}

---

## Table of Contents

{auto-generated from chapter titles / segment headings}

---

{segments rendered as sections}

### {Chapter Title or "Segment N"} ({MM:SS} - {MM:SS})

{merged content: transcript + code blocks + slide text}

```{language}
{code shown on screen}
```

---

### {Next Chapter} ({MM:SS} - {MM:SS})

{content continues...}

---

## Key Takeaways

{AI-generated summary of main points — populated during enhancement}

## Code Examples

{Consolidated list of all code blocks from the video}
```

### Full Example

```markdown
# React Hooks Tutorial for Beginners

> **Source:** [React Official](https://youtube.com/@reactofficial) | **Duration:** 30:32 | **Published:** 2026-01-15
> **URL:** [https://youtube.com/watch?v=abc123def45](https://youtube.com/watch?v=abc123def45)
> **Views:** 1,500,000 | **Likes:** 45,000
> **Tags:** react, hooks, tutorial, javascript, web development

Learn React Hooks from scratch in this comprehensive tutorial. We'll cover useState, useEffect, useContext, and custom hooks with practical examples.

---

## Table of Contents

- [Intro](#intro-0000---0045)
- [Project Setup](#project-setup-0045---0300)
- [useState Hook](#usestate-hook-0300---0900)
- [useEffect Hook](#useeffect-hook-0900---1500)
- [Custom Hooks](#custom-hooks-1500---2200)
- [Best Practices](#best-practices-2200---2800)
- [Wrap Up](#wrap-up-2800---3032)

---

### Intro (00:00 - 00:45)

Welcome to this React Hooks tutorial. Today we'll learn about the most important hooks in React and how to use them effectively in your applications. By the end of this video, you'll understand useState, useEffect, useContext, and how to create your own custom hooks.

---

### Project Setup (00:45 - 03:00)

Let's start by setting up our React project. We'll use Create React App which gives us a great starting point with all the tooling configured.

**Terminal command:**
```bash
npx create-react-app hooks-demo
cd hooks-demo
npm start
```

Open the project in your code editor. You'll see the standard React project structure with src/App.js as our main component file. Let's clear out the boilerplate and start fresh.

**Code shown in editor:**
```jsx
import React from 'react';

function App() {
  return (
    <div className="App">
      <h1>Hooks Demo</h1>
    </div>
  );
}

export default App;
```

---

### useState Hook (03:00 - 09:00)

The useState hook is the most fundamental hook in React. It lets you add state to functional components. Before hooks, you needed class components for state management.

Let's create a simple counter to demonstrate useState. The hook returns an array with two elements: the current state value and a function to update it. We use array destructuring to name them.

**Code shown in editor:**
```jsx
import React, { useState } from 'react';

function Counter() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>
        Increment
      </button>
      <button onClick={() => setCount(count - 1)}>
        Decrement
      </button>
    </div>
  );
}
```

Important things to remember about useState: the initial value is only used on the first render. If you need to compute the initial value, pass a function instead of a value to avoid recomputing on every render.

---

## Key Takeaways

1. **useState** is for managing simple state values in functional components
2. **useEffect** handles side effects (data fetching, subscriptions, DOM updates)
3. Always include a dependency array in useEffect to control when it runs
4. Custom hooks let you extract reusable stateful logic
5. Follow the Rules of Hooks: only call hooks at the top level, only in React functions

## Code Examples

### Counter with useState
```jsx
const [count, setCount] = useState(0);
```

### Data Fetching with useEffect
```jsx
useEffect(() => {
  fetch('/api/data')
    .then(res => res.json())
    .then(setData);
}, []);
```

### Custom Hook: useLocalStorage
```jsx
function useLocalStorage(key, initialValue) {
  const [value, setValue] = useState(() => {
    const saved = localStorage.getItem(key);
    return saved ? JSON.parse(saved) : initialValue;
  });

  useEffect(() => {
    localStorage.setItem(key, JSON.stringify(value));
  }, [key, value]);

  return [value, setValue];
}
```
```

---

## SKILL.md Section Format

Video content is integrated into SKILL.md as a dedicated section, following the existing section patterns.

### Section Placement

```markdown
# {Skill Name}

## Overview
{existing overview section}

## Quick Reference
{existing quick reference}

## Getting Started
{from docs/github}

## Core Concepts
{from docs/github}

## API Reference
{from docs/github}

## Video Tutorials                    ← NEW SECTION
{from video sources}

## Code Examples
{consolidated from all sources}

## References
{file listing}
```

### Section Content

```markdown
## Video Tutorials

This skill includes knowledge extracted from {N} video tutorial(s) totaling {HH:MM:SS} of content.

### {Video Title 1}
**Source:** [{channel}]({url}) | {duration} | {view_count} views

{summary or first segment content, abbreviated}

**Topics covered:** {chapter titles or detected topics}

→ Full transcript: [references/video_{sanitized_title}.md](references/video_{sanitized_title}.md)

---

### {Video Title 2}
...

### Key Patterns from Videos

{AI-generated section highlighting patterns that appear across multiple videos}

### Code Examples from Videos

{Consolidated code blocks from all videos, organized by topic}

```{language}
// From: {video_title} at {timestamp}
{code}
```
```

### Playlist Grouping

When a video source is a playlist, the SKILL.md section groups videos under the playlist title:

```markdown
## Video Tutorials

### React Complete Course (12 videos, 6:30:00 total)

1. **Introduction to React** (15:00) — Components, JSX, virtual DOM
2. **React Hooks Deep Dive** (30:32) — useState, useEffect, custom hooks
3. **State Management** (28:15) — Context API, Redux patterns
...

→ Full transcripts in [references/](references/) (video_*.md files)
```

---

## Metadata JSON Format

### `video_data/metadata.json` — Full scraper result

```json
{
    "scraper_version": "3.2.0",
    "extracted_at": "2026-02-27T14:30:00Z",
    "processing_time_seconds": 125.4,
    "config": {
        "visual_extraction": true,
        "whisper_model": "base",
        "segmentation_strategy": "hybrid",
        "max_videos": 20
    },
    "summary": {
        "total_videos": 5,
        "total_duration_seconds": 5420.0,
        "total_segments": 42,
        "total_code_blocks": 18,
        "total_keyframes": 156,
        "languages": ["en"],
        "categories_found": ["getting_started", "hooks", "advanced"]
    },
    "videos": [
        {
            "video_id": "abc123def45",
            "title": "React Hooks Tutorial for Beginners",
            "duration": 1832.0,
            "segments_count": 7,
            "code_blocks_count": 5,
            "transcript_source": "youtube_manual",
            "transcript_confidence": 0.95,
            "content_richness_score": 0.88,
            "reference_file": "references/video_react-hooks-tutorial-for-beginners.md"
        }
    ],
    "warnings": [
        "Video xyz789: Auto-generated captions used (manual not available)"
    ],
    "errors": []
}
```

### `video_data/transcripts/{video_id}.json` — Raw transcript

```json
{
    "video_id": "abc123def45",
    "transcript_source": "youtube_manual",
    "language": "en",
    "segments": [
        {
            "text": "Welcome to this React Hooks tutorial.",
            "start": 0.0,
            "end": 2.5,
            "confidence": 1.0,
            "words": null
        },
        {
            "text": "Today we'll learn about the most important hooks.",
            "start": 2.5,
            "end": 5.8,
            "confidence": 1.0,
            "words": null
        }
    ]
}
```

### `video_data/segments/{video_id}_segments.json` — Aligned segments

```json
{
    "video_id": "abc123def45",
    "segmentation_strategy": "chapters",
    "segments": [
        {
            "index": 0,
            "start_time": 0.0,
            "end_time": 45.0,
            "duration": 45.0,
            "chapter_title": "Intro",
            "category": "getting_started",
            "content_type": "explanation",
            "transcript": "Welcome to this React Hooks tutorial...",
            "transcript_confidence": 0.95,
            "has_code_on_screen": false,
            "has_slides": false,
            "keyframes_count": 2,
            "code_blocks_count": 0,
            "confidence": 0.95
        }
    ]
}
```

---

## Page JSON Format (Compatibility)

For compatibility with the existing page-based pipeline (`pages/*.json`), each video also produces a page JSON file. This ensures video content flows through the same build pipeline as other sources.

### `pages/video_{video_id}.json`

```json
{
    "url": "https://www.youtube.com/watch?v=abc123def45",
    "title": "React Hooks Tutorial for Beginners",
    "content": "{full merged content from all segments}",
    "category": "tutorials",
    "source_type": "video",
    "metadata": {
        "video_id": "abc123def45",
        "duration": 1832.0,
        "channel": "React Official",
        "view_count": 1500000,
        "chapters": 7,
        "transcript_source": "youtube_manual",
        "has_visual_extraction": true
    },
    "code_blocks": [
        {
            "language": "jsx",
            "code": "const [count, setCount] = useState(0);",
            "source": "video_ocr",
            "timestamp": 195.0
        }
    ],
    "extracted_at": "2026-02-27T14:30:00Z"
}
```

This format is compatible with the existing `build_skill()` function in `doc_scraper.py`, which reads `pages/*.json` files to build the skill.

---

## RAG Chunking for Video

When `--chunk-for-rag` is enabled, video segments are chunked differently from text documents because they already have natural boundaries (chapters/segments).

### Chunking Strategy

```
For each VideoSegment:
    IF segment.duration <= chunk_duration_threshold (default: 300s / 5 min):
        → Output as single chunk

    ELIF segment has sub-sections (code blocks interleaved with explanation):
        → Split at code block boundaries
        → Each chunk = explanation + associated code block

    ELSE (long segment without clear sub-sections):
        → Split at sentence boundaries
        → Target chunk size: config.chunk_size tokens
        → Overlap: config.chunk_overlap tokens
```

### RAG Metadata per Chunk

```json
{
    "text": "chunk content...",
    "metadata": {
        "source": "video",
        "source_type": "youtube",
        "video_id": "abc123def45",
        "video_title": "React Hooks Tutorial",
        "channel": "React Official",
        "timestamp_start": 180.0,
        "timestamp_end": 300.0,
        "timestamp_url": "https://youtube.com/watch?v=abc123def45&t=180",
        "chapter": "useState Hook",
        "category": "hooks",
        "content_type": "live_coding",
        "has_code": true,
        "language": "en",
        "confidence": 0.94,
        "view_count": 1500000,
        "upload_date": "2026-01-15"
    }
}
```

The `timestamp_url` field is especially valuable — it lets RAG systems link directly to the relevant moment in the video.

---

## Examples

### Minimal Output (transcript only, single video)

```
output/react-hooks-video/
├── SKILL.md                          # Skill with video section
├── references/
│   └── video_react-hooks-tutorial.md  # Full transcript organized by chapters
├── video_data/
│   ├── metadata.json                 # Scraper metadata
│   ├── transcripts/
│   │   └── abc123def45.json          # Raw transcript
│   └── segments/
│       └── abc123def45_segments.json  # Aligned segments
└── pages/
    └── video_abc123def45.json         # Page-compatible format
```

### Full Output (visual extraction, playlist of 5 videos)

```
output/react-complete/
├── SKILL.md
├── references/
│   ├── video_intro-to-react.md
│   ├── video_react-hooks-deep-dive.md
│   ├── video_state-management.md
│   ├── video_react-router.md
│   └── video_testing-react-apps.md
├── video_data/
│   ├── metadata.json
│   ├── transcripts/
│   │   ├── abc123def45.json
│   │   ├── def456ghi78.json
│   │   ├── ghi789jkl01.json
│   │   ├── jkl012mno34.json
│   │   └── mno345pqr67.json
│   ├── segments/
│   │   ├── abc123def45_segments.json
│   │   ├── def456ghi78_segments.json
│   │   ├── ghi789jkl01_segments.json
│   │   ├── jkl012mno34_segments.json
│   │   └── mno345pqr67_segments.json
│   └── frames/
│       ├── abc123def45/
│       │   ├── frame_045.00_terminal.png
│       │   ├── frame_052.30_code.png
│       │   ├── frame_128.00_slide.png
│       │   └── ... (50+ frames)
│       ├── def456ghi78/
│       │   └── ...
│       └── ...
└── pages/
    ├── video_abc123def45.json
    ├── video_def456ghi78.json
    ├── video_ghi789jkl01.json
    ├── video_jkl012mno34.json
    └── video_mno345pqr67.json
```

### Mixed Source Output (docs + github + video)

```
output/react-unified/
├── SKILL.md                              # Unified skill with ALL sources
├── references/
│   ├── getting_started.md                # From docs
│   ├── hooks.md                          # From docs
│   ├── api_reference.md                  # From docs
│   ├── architecture.md                   # From GitHub analysis
│   ├── patterns.md                       # From GitHub analysis
│   ├── video_react-hooks-tutorial.md     # From video
│   ├── video_react-conf-keynote.md       # From video
│   └── video_advanced-patterns.md        # From video
├── video_data/
│   └── ... (video-specific data)
├── pages/
│   ├── page_001.json                     # From docs
│   ├── page_002.json
│   ├── video_abc123def45.json            # From video
│   └── video_def456ghi78.json
└── react_data/
    └── pages/                            # Raw scrape data
```
