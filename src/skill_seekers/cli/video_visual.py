"""Video visual extraction module (Tier 2).

Extracts keyframes from videos, classifies them, and performs OCR
to extract text content from slides, code, and terminal screens.

Dependencies (Tier 2):
- opencv-python-headless: Frame extraction and image analysis
- scenedetect: Scene boundary detection
- easyocr: Text recognition in frames
"""

from __future__ import annotations

import concurrent.futures
import difflib
import gc
import logging
import os
import re
import tempfile
from dataclasses import dataclass, field

from skill_seekers.cli.video_models import (
    CodeBlock,
    CodeContext,
    FrameSubSection,
    FrameType,
    KeyFrame,
    OCRRegion,
    TextGroup,
    TextGroupEdit,
    TextGroupTimeline,
)

logger = logging.getLogger(__name__)

# Set ROCm/MIOpen env vars BEFORE importing torch (via easyocr).
# Without MIOPEN_FIND_MODE=FAST, MIOpen tries to allocate huge workspace
# buffers (300MB+), gets 0 bytes, and silently falls back to CPU kernels.
if "MIOPEN_FIND_MODE" not in os.environ:
    os.environ["MIOPEN_FIND_MODE"] = "FAST"
if "MIOPEN_USER_DB_PATH" not in os.environ:
    _miopen_db = os.path.expanduser("~/.config/miopen")
    os.makedirs(_miopen_db, exist_ok=True)
    os.environ["MIOPEN_USER_DB_PATH"] = _miopen_db

# Tier 2 dependency flags
try:
    import cv2

    HAS_OPENCV = True
except ImportError:
    cv2 = None  # type: ignore[assignment]
    HAS_OPENCV = False

try:
    import scenedetect as sd

    HAS_SCENEDETECT = True
except ImportError:
    sd = None  # type: ignore[assignment]
    HAS_SCENEDETECT = False

try:
    import easyocr

    HAS_EASYOCR = True
except ImportError:
    easyocr = None  # type: ignore[assignment]
    HAS_EASYOCR = False

try:
    import pytesseract

    HAS_PYTESSERACT = True
except ImportError:
    pytesseract = None  # type: ignore[assignment]
    HAS_PYTESSERACT = False

# Circuit breaker: after first tesseract failure, disable it for the session.
# Prevents wasting time spawning subprocesses that always fail.
_tesseract_broken = False


_INSTALL_MSG = (
    "Visual extraction requires additional dependencies.\n"
    "Recommended: skill-seekers video --setup  (auto-detects GPU, installs correct PyTorch)\n"
    'Alternative:  pip install "skill-seekers[video-full]"  (may install wrong PyTorch variant)'
)

# Lazy-initialized EasyOCR reader (heavy, only load once)
_ocr_reader = None


def _detect_gpu() -> bool:
    """Check if a CUDA or ROCm GPU is available for EasyOCR/PyTorch."""
    try:
        import torch

        return torch.cuda.is_available() or (
            hasattr(torch.version, "hip") and torch.version.hip is not None
        )
    except ImportError:
        return False


def _get_ocr_reader():
    """Get or create the EasyOCR reader (lazy singleton)."""
    global _ocr_reader
    if _ocr_reader is None:
        use_gpu = _detect_gpu()
        logger.info(
            f"Initializing OCR engine ({'GPU' if use_gpu else 'CPU'} mode, "
            "first run may download models)..."
        )
        _ocr_reader = easyocr.Reader(["en"], gpu=use_gpu)
    return _ocr_reader


def _detect_theme(gray_img) -> str:
    """Detect 'dark' or 'light' theme from grayscale image.

    Uses median brightness: < 128 = dark theme, >= 128 = light theme.
    """
    import numpy as np

    median = float(np.median(gray_img))
    return "dark" if median < 128 else "light"


def _preprocess_frame_for_ocr(frame_path: str, frame_type: FrameType) -> str:
    """Apply frame-type-aware preprocessing before OCR.

    CODE_EDITOR/TERMINAL: COLOR inversion (preserves syntax highlighting) →
    grayscale → aggressive upscale → CLAHE contrast enhancement.  Produces
    a high-res, high-contrast grayscale suitable for EasyOCR.

    SLIDE: mild sharpening.
    Others: no preprocessing.

    Args:
        frame_path: Path to the original frame image.
        frame_type: Classification of the frame.

    Returns:
        Path to the preprocessed image (may be a temp file or the original).
    """
    if not HAS_OPENCV:
        return frame_path

    import numpy as np

    if frame_type in (FrameType.CODE_EDITOR, FrameType.TERMINAL):
        img = cv2.imread(frame_path)
        if img is None:
            return frame_path

        # 1. Theme detection on original grayscale
        gray_check = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        theme = _detect_theme(gray_check)

        # 2. COLOR inversion on BGR — preserves syntax highlighting distinctions.
        #    Grayscale-then-invert loses the difference between blue/green/red text.
        if theme == "dark":
            img = cv2.bitwise_not(img)

        # 3. Convert inverted color to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 4. Aggressive upscale BEFORE any processing — OCR needs ~12px+ char height.
        #    Must be done on grayscale (not binary) for clean INTER_CUBIC interpolation.
        h, w = gray.shape
        if w < 1920:
            scale = max(2, (1920 // w) + 1)
            gray = cv2.resize(gray, (w * scale, h * scale), interpolation=cv2.INTER_CUBIC)

        # 5. CLAHE contrast enhancement — brings out faint text
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

        with tempfile.NamedTemporaryFile(suffix=".png", prefix="ocr_pre_", delete=False) as tmp:
            tmp_path = tmp.name
        cv2.imwrite(tmp_path, gray)
        return tmp_path

    if frame_type == FrameType.SLIDE:
        img = cv2.imread(frame_path)
        if img is None:
            return frame_path
        kernel = np.array([[0, -0.5, 0], [-0.5, 3, -0.5], [0, -0.5, 0]])
        sharpened = cv2.filter2D(img, -1, kernel)
        with tempfile.NamedTemporaryFile(suffix=".png", prefix="ocr_pre_", delete=False) as tmp:
            tmp_path = tmp.name
        cv2.imwrite(tmp_path, sharpened)
        return tmp_path

    return frame_path


def _binarize_for_tesseract(grayscale_path: str) -> str:
    """Produce a clean binary image from a preprocessed grayscale, for Tesseract.

    Pipeline: Gaussian blur → Otsu's threshold → morphological close.
    Tesseract performs best on clean black-text-on-white binary images.

    Args:
        grayscale_path: Path to a preprocessed grayscale image.

    Returns:
        Path to the binary image (temp file).
    """
    import numpy as np

    gray = cv2.imread(grayscale_path, cv2.IMREAD_GRAYSCALE)
    if gray is None:
        return grayscale_path

    # Gaussian blur to smooth noise before thresholding
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)

    # Otsu's binarization — globally optimal for bimodal (text vs background)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Morphological close to fill small gaps in character strokes
    kernel = np.ones((2, 2), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)

    with tempfile.NamedTemporaryFile(suffix=".png", prefix="ocr_bin_", delete=False) as tmp:
        tmp_path = tmp.name
    cv2.imwrite(tmp_path, binary)
    return tmp_path


def _get_ocr_params(frame_type: FrameType) -> dict:
    """Return EasyOCR readtext kwargs tuned per frame type.

    CODE_EDITOR/TERMINAL: lower thresholds, beam search, higher mag.
    SLIDE/OTHER: defaults with greedy decoder.
    """
    if frame_type in (FrameType.CODE_EDITOR, FrameType.TERMINAL):
        return {
            "text_threshold": 0.4,
            "low_text": 0.3,
            "contrast_ths": 0.3,
            "mag_ratio": 1.0,  # Frame already upscaled in preprocessing
            "decoder": "beamsearch",
            "beamWidth": 10,
        }
    if frame_type == FrameType.SLIDE:
        return {
            "text_threshold": 0.6,
            "low_text": 0.4,
            "mag_ratio": 1.0,
            "decoder": "greedy",
            "beamWidth": 5,
        }
    return {
        "text_threshold": 0.6,
        "low_text": 0.4,
        "mag_ratio": 1.0,
        "decoder": "greedy",
        "beamWidth": 5,
    }


_CODE_TOKENS = frozenset(
    {
        "func",
        "var",
        "def",
        "class",
        "return",
        "if",
        "for",
        "while",
        "import",
        "from",
        "const",
        "let",
        "function",
        "extends",
        "self",
        "true",
        "false",
        "null",
        "none",
        "elif",
        "else",
        "try",
        "except",
        "async",
        "await",
        "yield",
        "print",
        "int",
        "str",
        "float",
        "bool",
        "=",
        "(",
        ")",
        "{",
        "}",
        "[",
        "]",
        ":",
        "->",
        "=>",
        "==",
        "!=",
    }
)


def _has_code_tokens(text: str) -> bool:
    """Check if text contains recognizable code tokens."""
    lower = text.lower()
    return any(token in lower for token in _CODE_TOKENS)


def _run_tesseract_ocr(preprocessed_path: str, frame_type: FrameType) -> list[tuple]:  # noqa: ARG001
    """Run pytesseract on a preprocessed frame.

    Creates a binarized version of the preprocessed grayscale (Tesseract
    performs best on clean binary images), then runs Tesseract with
    ``--psm 4`` (single column of variable-size text) and LSTM engine.

    Returns results in the same format as EasyOCR: list of (bbox, text, confidence).
    Groups words into lines by y-coordinate.

    Uses a circuit breaker: if tesseract fails once, it's disabled for the
    rest of the session to avoid wasting time on repeated subprocess failures.

    Args:
        preprocessed_path: Path to the preprocessed grayscale image.
        frame_type: Frame classification (reserved for future per-type tuning).
    """
    global _tesseract_broken
    if not HAS_PYTESSERACT or _tesseract_broken:
        return []

    # Produce clean binary for Tesseract
    binary_path = _binarize_for_tesseract(preprocessed_path)
    try:
        data = pytesseract.image_to_data(
            binary_path,
            config="--psm 4 --oem 1",
            output_type=pytesseract.Output.DICT,
        )
    except Exception:  # noqa: BLE001
        _tesseract_broken = True
        logger.warning(
            "pytesseract failed — disabling for this session. "
            "Install tesseract binary: skill-seekers video --setup"
        )
        return []
    finally:
        if binary_path != preprocessed_path and os.path.exists(binary_path):
            os.unlink(binary_path)

    # Collect words with valid confidence
    words = []
    for i in range(len(data["text"])):
        text = data["text"][i].strip()
        conf = float(data["conf"][i])
        if not text or conf < 30:
            continue
        x = data["left"][i]
        y = data["top"][i]
        w = data["width"][i]
        h = data["height"][i]
        bbox = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]
        words.append(
            {
                "bbox": bbox,
                "text": text,
                "conf": conf / 100.0,
                "y_center": y + h / 2,
                "line_num": data["line_num"][i],
                "block_num": data["block_num"][i],
            }
        )

    if not words:
        return []

    # Group by (block_num, line_num) to form lines
    line_groups: dict[tuple[int, int], list[dict]] = {}
    for w in words:
        key = (w["block_num"], w["line_num"])
        line_groups.setdefault(key, []).append(w)

    results = []
    for _key, line_words in sorted(line_groups.items()):
        line_words.sort(key=lambda w: w["bbox"][0][0])
        line_text = " ".join(w["text"] for w in line_words)
        avg_conf = sum(w["conf"] for w in line_words) / len(line_words)

        # Build bounding box for the whole line
        x_min = min(w["bbox"][0][0] for w in line_words)
        y_min = min(w["bbox"][0][1] for w in line_words)
        x_max = max(w["bbox"][1][0] for w in line_words)
        y_max = max(w["bbox"][2][1] for w in line_words)
        bbox = [[x_min, y_min], [x_max, y_min], [x_max, y_max], [x_min, y_max]]

        results.append((bbox, line_text, avg_conf))

    return results


def _run_multi_engine_ocr(
    frame_path: str,
    frame_type: FrameType,
) -> tuple[list[tuple], str]:
    """Run multiple OCR engines and ensemble the results.

    Strategy:
    1. Preprocess the frame (inversion + binarization for code frames).
    2. Run EasyOCR on the preprocessed image.
    3. Run pytesseract on the preprocessed image.
    4. For each y-bucket line, pick the engine result with higher confidence.
    5. Prefer results that contain recognizable code tokens.

    Returns:
        Tuple of (raw_results, flat_text).
    """
    preprocessed_path = _preprocess_frame_for_ocr(frame_path, frame_type)
    try:
        return _ensemble_ocr_results(preprocessed_path, frame_type)
    finally:
        if preprocessed_path != frame_path and os.path.exists(preprocessed_path):
            os.unlink(preprocessed_path)


def _ensemble_ocr_results(
    preprocessed_path: str,
    frame_type: FrameType,
) -> tuple[list[tuple], str]:
    """Run EasyOCR + pytesseract and merge results by y-bucket."""
    # Run EasyOCR
    easy_results: list[tuple] = []
    if HAS_EASYOCR:
        try:
            reader = _get_ocr_reader()
            ocr_params = _get_ocr_params(frame_type)
            raw = reader.readtext(preprocessed_path, detail=1, paragraph=False, **ocr_params)
            easy_results = [
                (bbox, text.strip(), conf)
                for bbox, text, conf in raw
                if conf >= 0.3 and text.strip()
            ]
        except Exception:  # noqa: BLE001
            logger.debug("EasyOCR failed in multi-engine pipeline")

    # Run pytesseract
    tess_results = _run_tesseract_ocr(preprocessed_path, frame_type)

    if not easy_results and not tess_results:
        return [], ""
    if not easy_results:
        flat = " ".join(text for _, text, _ in tess_results)
        return tess_results, flat
    if not tess_results:
        flat = " ".join(text for _, text, _ in easy_results)
        return easy_results, flat

    # Merge by y-bucket: for each line, pick the better engine result
    merged = _merge_by_y_bucket(easy_results, tess_results)
    flat = " ".join(text for _, text, _ in merged)
    return merged, flat


def _merge_by_y_bucket(
    easy_results: list[tuple],
    tess_results: list[tuple],
    y_tolerance: float = 20.0,
) -> list[tuple]:
    """Merge two sets of OCR results by matching y-coordinate lines.

    For each y-bucket, picks the result with higher confidence,
    with a preference for results containing code tokens.
    """

    def _y_center(bbox) -> float:
        return (min(pt[1] for pt in bbox) + max(pt[1] for pt in bbox)) / 2

    # Build y-indexed lines for each engine
    easy_lines = [(r, _y_center(r[0])) for r in easy_results]
    tess_lines = [(r, _y_center(r[0])) for r in tess_results]

    # Sort by y
    easy_lines.sort(key=lambda x: x[1])
    tess_lines.sort(key=lambda x: x[1])

    merged: list[tuple] = []
    used_tess = set()

    for easy_r, easy_y in easy_lines:
        # Find matching tess line
        best_tess_idx = None
        best_dist = float("inf")
        for i, (tess_r, tess_y) in enumerate(tess_lines):
            if i in used_tess:
                continue
            dist = abs(easy_y - tess_y)
            if dist <= y_tolerance and dist < best_dist:
                best_dist = dist
                best_tess_idx = i

        if best_tess_idx is not None:
            used_tess.add(best_tess_idx)
            tess_r = tess_lines[best_tess_idx][0]
            # Pick better result
            winner = _pick_better_ocr_result(easy_r, tess_r)
            merged.append(winner)
        else:
            merged.append(easy_r)

    # Add unmatched tess lines
    for i, (tess_r, _) in enumerate(tess_lines):
        if i not in used_tess:
            merged.append(tess_r)

    # Sort final results by y position
    merged.sort(key=lambda r: _y_center(r[0]))
    return merged


def _pick_better_ocr_result(result_a: tuple, result_b: tuple) -> tuple:
    """Pick the better of two OCR results for the same line.

    Prefers code-token-containing results; ties broken by confidence.
    """
    _, text_a, conf_a = result_a
    _, text_b, conf_b = result_b

    has_code_a = _has_code_tokens(text_a)
    has_code_b = _has_code_tokens(text_b)

    # If one has code tokens and the other doesn't, prefer code tokens
    if has_code_a and not has_code_b:
        return result_a
    if has_code_b and not has_code_a:
        return result_b

    # Both have or both lack code tokens — pick higher confidence
    return result_a if conf_a >= conf_b else result_b


def _ocr_with_claude_vision(frame_path: str, frame_type: FrameType) -> tuple[str, float]:
    """Use Claude Vision API to extract code from a frame.

    Sends the frame image to Claude Haiku and asks it to extract all
    visible code/text exactly as shown.

    Returns:
        (extracted_text, confidence).  Confidence is 0.95 when successful.
        Returns ("", 0.0) if API key is not set or the call fails.
    """
    import base64

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return "", 0.0

    try:
        import anthropic

        # Read image as base64
        with open(frame_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")

        # Determine media type
        ext = os.path.splitext(frame_path)[1].lower()
        media_type_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        media_type = media_type_map.get(ext, "image/png")

        context = "IDE screenshot" if frame_type == FrameType.CODE_EDITOR else "terminal screenshot"
        prompt = (
            f"Extract all visible code/text from this {context} exactly as shown. "
            "Preserve indentation, line breaks, and all characters. "
            "Return only the raw code text, no explanations."
        )

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt,
                        },
                    ],
                }
            ],
        )

        text = response.content[0].text.strip() if response.content else ""
        if text:
            return text, 0.95
        return "", 0.0

    except Exception:  # noqa: BLE001
        logger.debug("Claude Vision API call failed, falling back to OCR results")
        return "", 0.0


def check_visual_dependencies() -> dict[str, bool]:
    """Check which visual extraction dependencies are available.

    Returns:
        Dict mapping dependency name to availability.
    """
    return {
        "opencv": HAS_OPENCV,
        "scenedetect": HAS_SCENEDETECT,
        "easyocr": HAS_EASYOCR,
    }


def detect_scenes(video_path: str) -> list[tuple[float, float]]:
    """Detect scene boundaries in a video using scenedetect.

    Args:
        video_path: Path to video file.

    Returns:
        List of (start_time, end_time) tuples for each scene in seconds.

    Raises:
        RuntimeError: If required dependencies are not installed.
    """
    if not HAS_OPENCV or not HAS_SCENEDETECT:
        raise RuntimeError(_INSTALL_MSG)

    logger.info(f"Detecting scenes in {video_path}...")

    video = sd.open_video(video_path)
    scene_manager = sd.SceneManager()
    scene_manager.add_detector(sd.ContentDetector(threshold=27.0))
    scene_manager.detect_scenes(video)
    scene_list = scene_manager.get_scene_list()

    scenes = []
    for scene_start, scene_end in scene_list:
        scenes.append((scene_start.get_seconds(), scene_end.get_seconds()))

    logger.info(f"Detected {len(scenes)} scenes")
    return scenes


def extract_keyframes(video_path: str, timestamps: list[float]) -> list[KeyFrame]:
    """Extract keyframes at specified timestamps using OpenCV.

    Args:
        video_path: Path to video file.
        timestamps: List of timestamps (in seconds) to extract frames at.

    Returns:
        List of KeyFrame objects with saved frame paths.

    Raises:
        RuntimeError: If required dependencies are not installed.
    """
    if not HAS_OPENCV:
        raise RuntimeError(_INSTALL_MSG)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Cannot open video: {video_path}")
        return []

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    keyframes = []

    for ts in sorted(timestamps):
        frame_num = int(ts * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        if not ret:
            logger.warning(f"Could not read frame at {ts:.1f}s")
            continue

        # Save frame to temp file
        with tempfile.NamedTemporaryFile(
            suffix=".jpg", prefix=f"frame_{ts:.0f}s_", delete=False
        ) as tmp:
            tmp_path = tmp.name
        cv2.imwrite(tmp_path, frame)

        frame_type = classify_frame(tmp_path)
        kf = KeyFrame(
            timestamp=ts,
            image_path=tmp_path,
            frame_type=frame_type,
        )
        keyframes.append(kf)

    cap.release()
    logger.info(f"Extracted {len(keyframes)} keyframes")
    return keyframes


# Minimum panel dimensions for region-based classification.
# IDE panels smaller than these are toolbar/tab/scrollbar noise.
_MIN_PANEL_WIDTH = 200
_MIN_PANEL_HEIGHT = 150
_MIN_PANEL_AREA_PCT = 5.0  # percent of total frame area


def _classify_region(gray, edges, hsv) -> FrameType:
    """Classify a single rectangular region from pre-computed arrays."""
    import numpy as np

    h, w = gray.shape
    mean_brightness = float(gray.mean())
    edge_density = float(edges.mean()) / 255.0
    saturation_mean = float(hsv[:, :, 1].mean())

    # Horizontal line detection for code editors
    horizontal_lines = 0
    if mean_brightness < 80 and edge_density > 0.008:
        lines = cv2.HoughLinesP(
            edges, 1, np.pi / 180, threshold=80, minLineLength=w // 8, maxLineGap=10
        )
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
                if angle < 5 or angle > 175:
                    horizontal_lines += 1

    if mean_brightness < 80 and (
        edge_density > 0.05 or (edge_density > 0.01 and horizontal_lines >= 3)
    ):
        if saturation_mean < 30:
            return FrameType.TERMINAL
        return FrameType.CODE_EDITOR
    elif mean_brightness > 180 and edge_density > 0.03:
        return FrameType.SLIDE
    elif mean_brightness > 160 and edge_density < 0.02:
        return FrameType.DIAGRAM
    elif saturation_mean > 60 and mean_brightness > 80:
        return FrameType.WEBCAM

    return FrameType.OTHER


def _detect_panel_dividers(gray) -> tuple[list[int], list[int]]:
    """Detect IDE panel divider positions using brightness gradients.

    Panel dividers are thin lines where many rows (or columns) have a
    sharp brightness change.  Returns lists of x and y positions.
    """
    import numpy as np

    h, w = gray.shape

    # Vertical dividers: column-wise horizontal gradient
    dx = np.abs(np.diff(gray.astype(np.float32), axis=1))
    v_sig = (dx > 25).sum(axis=0)
    v_cols = np.where(v_sig > h * 0.3)[0]

    v_dividers: list[int] = []
    if len(v_cols) > 0:
        group = [v_cols[0]]
        for x in v_cols[1:]:
            if x - group[-1] <= 15:
                group.append(x)
            else:
                v_dividers.append(int(np.mean(group)))
                group = [x]
        v_dividers.append(int(np.mean(group)))
    v_dividers = [d for d in v_dividers if w * 0.03 < d < w * 0.97]

    # Horizontal dividers: row-wise vertical gradient
    dy = np.abs(np.diff(gray.astype(np.float32), axis=0))
    h_sig = (dy > 25).sum(axis=1)
    h_rows = np.where(h_sig > w * 0.3)[0]

    h_dividers: list[int] = []
    if len(h_rows) > 0:
        group = [h_rows[0]]
        for y in h_rows[1:]:
            if y - group[-1] <= 15:
                group.append(y)
            else:
                h_dividers.append(int(np.mean(group)))
                group = [y]
        h_dividers.append(int(np.mean(group)))
    h_dividers = [d for d in h_dividers if h * 0.03 < d < h * 0.97]

    return v_dividers, h_dividers


def classify_frame_regions(
    frame_path: str,
) -> list[tuple[int, int, int, int, FrameType]]:
    """Classify a frame by detecting IDE panels as rectangles.

    Finds panel divider lines (vertical and horizontal brightness edges),
    builds a grid of rectangular panels, filters by minimum size, and
    classifies each panel independently.

    This handles split-screen IDE layouts where half the screen shows code
    and the other half shows a game viewport or inspector.

    Args:
        frame_path: Path to frame image file.

    Returns:
        List of ``(x1, y1, x2, y2, FrameType)`` for each detected panel
        that meets the minimum size threshold.
    """
    if not HAS_OPENCV:
        raise RuntimeError(_INSTALL_MSG)

    img = cv2.imread(frame_path)
    if img is None:
        return [(0, 0, 0, 0, FrameType.OTHER)]

    h, w = img.shape[:2]
    gray_full = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges_full = cv2.Canny(gray_full, 50, 150)
    hsv_full = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    v_dividers, h_dividers = _detect_panel_dividers(gray_full)

    xs = [0] + v_dividers + [w]
    ys = [0] + h_dividers + [h]
    total_area = w * h

    panels: list[tuple[int, int, int, int, FrameType]] = []
    for i in range(len(ys) - 1):
        for j in range(len(xs) - 1):
            x1, x2 = xs[j], xs[j + 1]
            y1, y2 = ys[i], ys[i + 1]
            pw, ph = x2 - x1, y2 - y1
            area_pct = (pw * ph) / total_area * 100

            if pw < _MIN_PANEL_WIDTH or ph < _MIN_PANEL_HEIGHT:
                continue
            if area_pct < _MIN_PANEL_AREA_PCT:
                continue

            ft = _classify_region(
                gray_full[y1:y2, x1:x2],
                edges_full[y1:y2, x1:x2],
                hsv_full[y1:y2, x1:x2],
            )
            panels.append((x1, y1, x2, y2, ft))

    # Fallback: if no panels survived the size filter, classify whole frame
    if not panels:
        ft = _classify_region(gray_full, edges_full, hsv_full)
        panels.append((0, 0, w, h, ft))

    return panels


def _find_code_bbox(
    regions: list[tuple[int, int, int, int, FrameType]],
) -> tuple[int, int, int, int] | None:
    """Merge all code/terminal panels into one bounding box.

    Returns ``(x1, y1, x2, y2)`` covering all code regions, or None.
    """
    code = [r for r in regions if r[4] in (FrameType.CODE_EDITOR, FrameType.TERMINAL)]
    if not code:
        return None
    return (
        min(r[0] for r in code),
        min(r[1] for r in code),
        max(r[2] for r in code),
        max(r[3] for r in code),
    )


# Panels narrower than this produce mostly OCR noise (inspector sidebars,
# narrow file-tree strips, thin toolbars).  300 px is roughly the width
# needed for a single readable code line at typical IDE font sizes.
_MIN_PANEL_OCR_WIDTH = 300


def _get_code_panels(
    regions: list[tuple[int, int, int, int, FrameType]],
    min_width: int = _MIN_PANEL_OCR_WIDTH,
) -> list[tuple[int, int, int, int]]:
    """Return bounding boxes for individual code/terminal panels.

    Unlike ``_find_code_bbox`` which merges all code regions into one,
    this returns each code panel separately so they can be OCR'd
    independently.  Panels narrower than *min_width* pixels are
    discarded — they typically contain inspector sidebars or toolbars
    that produce garbage OCR.
    """
    return [
        (r[0], r[1], r[2], r[3])
        for r in regions
        if r[4] in (FrameType.CODE_EDITOR, FrameType.TERMINAL) and (r[2] - r[0]) >= min_width
    ]


def _crop_code_region(frame_path: str, bbox: tuple[int, int, int, int], suffix: str = "") -> str:
    """Crop the code region from a frame and save as a temp file.

    Args:
        frame_path: Path to the source frame image.
        bbox: ``(x1, y1, x2, y2)`` crop rectangle.
        suffix: Optional suffix to disambiguate when cropping multiple
            panels from the same frame (e.g. ``"_p0"``, ``"_p1"``).
    """
    img = cv2.imread(frame_path)
    x1, y1, x2, y2 = bbox
    cropped = img[y1:y2, x1:x2]
    base, ext = os.path.splitext(frame_path)
    cropped_path = f"{base}_code_crop{suffix}{ext}"
    cv2.imwrite(cropped_path, cropped)
    return cropped_path


def _frame_type_from_regions(
    regions: list[tuple[int, int, int, int, FrameType]],
) -> FrameType:
    """Derive the dominant frame type from pre-computed regions.

    Same logic as ``classify_frame`` but avoids re-loading the image.
    """
    for _x1, _y1, _x2, _y2, ft in regions:
        if ft == FrameType.TERMINAL:
            return FrameType.TERMINAL
        if ft == FrameType.CODE_EDITOR:
            return FrameType.CODE_EDITOR

    from collections import Counter

    type_counts = Counter(ft for _, _, _, _, ft in regions)
    return type_counts.most_common(1)[0][0] if type_counts else FrameType.OTHER


def classify_frame(frame_path: str) -> FrameType:
    """Classify a video frame by its visual content.

    Uses region-based panel detection: finds IDE panel boundaries,
    classifies each rectangular panel, returns CODE_EDITOR/TERMINAL
    if *any* panel contains code.  This handles split-screen layouts.

    Args:
        frame_path: Path to frame image file.

    Returns:
        FrameType classification (CODE_EDITOR if any panel has code).
    """
    regions = classify_frame_regions(frame_path)

    # If any panel is code, the frame "has code"
    for _x1, _y1, _x2, _y2, ft in regions:
        if ft == FrameType.TERMINAL:
            return FrameType.TERMINAL
        if ft == FrameType.CODE_EDITOR:
            return FrameType.CODE_EDITOR

    # No code — return the most common type
    from collections import Counter

    type_counts = Counter(ft for _, _, _, _, ft in regions)
    return type_counts.most_common(1)[0][0]


def extract_text_from_frame(
    frame_path: str,
    frame_type: FrameType = FrameType.OTHER,
) -> tuple[list[tuple], str]:
    """Extract text from a video frame using EasyOCR.

    Applies frame-type-aware preprocessing and OCR parameters for
    better accuracy on code, terminal, and slide frames.

    Args:
        frame_path: Path to frame image file.
        frame_type: Classification of the frame content.

    Returns:
        Tuple of (raw_easyocr_results, flat_text_string).
        Each raw result is (bbox, text, confidence).

    Raises:
        RuntimeError: If required dependencies are not installed.
    """
    if not HAS_EASYOCR:
        raise RuntimeError(_INSTALL_MSG)

    preprocessed_path = _preprocess_frame_for_ocr(frame_path, frame_type)
    try:
        reader = _get_ocr_reader()
        ocr_params = _get_ocr_params(frame_type)
        results = reader.readtext(preprocessed_path, detail=1, paragraph=False, **ocr_params)
    finally:
        if preprocessed_path != frame_path and os.path.exists(preprocessed_path):
            os.unlink(preprocessed_path)

    # Filter by confidence
    filtered = []
    texts = []
    for bbox, text, conf in results:
        if conf >= 0.3 and text.strip():
            filtered.append((bbox, text.strip(), conf))
            texts.append(text.strip())

    return filtered, " ".join(texts)


def _cluster_ocr_into_lines(
    raw_results: list[tuple],
    frame_type: FrameType = FrameType.OTHER,
) -> list[OCRRegion]:
    """Cluster EasyOCR results into line-based OCRRegions.

    Groups text fragments that share similar y-coordinates into
    lines, sorts within each line by x-coordinate, and builds
    one OCRRegion per line.

    Args:
        raw_results: List of (bbox, text, confidence) from EasyOCR.
        frame_type: Frame classification for monospace detection.

    Returns:
        List of OCRRegion objects, one per detected text line.
    """
    if not raw_results:
        return []

    # Compute y_center for each result and estimate line height
    items = []
    for bbox, text, conf in raw_results:
        y_top = min(pt[1] for pt in bbox)
        y_bottom = max(pt[1] for pt in bbox)
        x_left = min(pt[0] for pt in bbox)
        x_right = max(pt[0] for pt in bbox)
        y_center = (y_top + y_bottom) / 2
        line_height = y_bottom - y_top
        items.append(
            {
                "text": text,
                "conf": conf,
                "y_center": y_center,
                "y_top": y_top,
                "y_bottom": y_bottom,
                "x_left": x_left,
                "x_right": x_right,
                "line_height": max(line_height, 1),
            }
        )

    # Sort by y_center
    items.sort(key=lambda it: it["y_center"])

    # Cluster into lines
    lines: list[list[dict]] = [[items[0]]]
    for item in items[1:]:
        current_line = lines[-1]
        avg_height = sum(it["line_height"] for it in current_line) / len(current_line)
        if abs(item["y_center"] - current_line[-1]["y_center"]) <= avg_height * 0.5:
            current_line.append(item)
        else:
            lines.append([item])

    # Estimate average character width for tab detection
    total_chars = sum(len(it["text"]) for it in items)
    total_width = sum(it["x_right"] - it["x_left"] for it in items)
    avg_char_width = total_width / max(total_chars, 1)

    is_mono = frame_type in (FrameType.CODE_EDITOR, FrameType.TERMINAL)

    regions = []
    for line in lines:
        # Sort fragments within line by x-coordinate
        line.sort(key=lambda it: it["x_left"])

        # Join fragments with appropriate spacing
        parts = []
        for i, frag in enumerate(line):
            if i > 0:
                gap = frag["x_left"] - line[i - 1]["x_right"]
                if gap > avg_char_width * 2:
                    parts.append("\t")
                else:
                    parts.append(" ")
            parts.append(frag["text"])

        text = "".join(parts)
        avg_conf = sum(f["conf"] for f in line) / len(line)
        bbox = (
            int(min(f["x_left"] for f in line)),
            int(min(f["y_top"] for f in line)),
            int(max(f["x_right"] for f in line)),
            int(max(f["y_bottom"] for f in line)),
        )

        regions.append(
            OCRRegion(
                text=text,
                confidence=avg_conf,
                bbox=bbox,
                is_monospace=is_mono,
            )
        )

    return regions


# ── OCR line cleaning ────────────────────────────────────────────────


def _fuzzy_word_match(a: str, b: str) -> bool:
    """Check if two words are likely the same despite OCR noise.

    Allows single-char prefix/suffix noise (e.g. 'gpublic' vs 'public')
    and common OCR confusions (l/1, O/0, rn/m).
    """
    if a == b:
        return True
    # Strip single-char OCR prefix noise (e.g. 'Jpublic' → 'public')
    a_stripped = a.lstrip("gGjJlLiI|") if len(a) > 2 else a
    b_stripped = b.lstrip("gGjJlLiI|") if len(b) > 2 else b
    if a_stripped == b_stripped:
        return True
    # Allow edit distance ≤ 1 for short words
    if abs(len(a) - len(b)) <= 1 and len(a) >= 3:
        diffs = sum(1 for x, y in zip(a, b, strict=False) if x != y)
        diffs += abs(len(a) - len(b))
        return diffs <= 1
    return False


def _fix_intra_line_duplication(line: str) -> str:
    """Fix lines where OCR duplicated content.

    Detects when the same token sequence appears twice adjacent,
    e.g. 'public class Card public class Card : MonoBehaviour'
    → 'public class Card : MonoBehaviour'.
    """
    words = line.split()
    if len(words) < 4:
        return line
    half = len(words) // 2
    for split_point in range(max(2, half - 2), min(len(words) - 1, half + 3)):
        prefix = words[:split_point]
        suffix = words[split_point:]
        # Check if suffix starts with same sequence as prefix
        match_len = 0
        for i, w in enumerate(prefix):
            if i < len(suffix) and _fuzzy_word_match(w, suffix[i]):
                match_len += 1
            else:
                break
        if match_len >= len(prefix) * 0.7 and match_len >= 2:
            # Keep the longer/cleaner half (suffix usually has trailing content)
            return (
                " ".join(suffix)
                if len(" ".join(suffix)) >= len(" ".join(prefix))
                else " ".join(prefix)
            )
    return line


# Compiled patterns for _clean_ocr_line
_RE_LEADING_LINE_NUMBER = re.compile(r"^\s*\d{1,4}(?:\s+|\t)")
_RE_COLLAPSE_MARKERS = re.compile(r"[▶▼►◄…⋯⋮]")
_RE_IDE_TAB_BAR = re.compile(
    r"^\s*(?:File|Edit|Assets|Window|Help|View|Tools|Debug|Run|Terminal)\s+",
    re.IGNORECASE,
)
_RE_UNITY_INSPECTOR = re.compile(
    r"^\s*(?:Inspector|Hierarchy|Project|Console|Scene|Game)\b.*$",
    re.IGNORECASE,
)


def _clean_ocr_line(line: str) -> str:
    """Remove IDE decorations and OCR artifacts from a single line."""
    if not line:
        return line
    # Remove full-line UI chrome
    if _RE_UNITY_INSPECTOR.match(line):
        return ""
    if _RE_IDE_TAB_BAR.match(line):
        return ""
    # Strip leading line numbers (e.g. '23  public class Card')
    line = _RE_LEADING_LINE_NUMBER.sub("", line)
    # Remove collapse markers / VS Code decorations
    line = _RE_COLLAPSE_MARKERS.sub("", line)
    # Fix intra-line duplication from multi-engine overlap
    line = _fix_intra_line_duplication(line)
    return line.strip()


def _assemble_structured_text(regions: list[OCRRegion], frame_type: FrameType) -> str:
    """Join OCR line regions into structured text.

    CODE_EDITOR/TERMINAL: newline-separated with indentation from x-offset.
    SLIDE: double-newline paragraph spacing.
    Others: space-separated flat text.

    Args:
        regions: List of OCRRegion objects (one per line).
        frame_type: Frame classification.

    Returns:
        Formatted text string.
    """
    if not regions:
        return ""

    if frame_type in (FrameType.CODE_EDITOR, FrameType.TERMINAL):
        if not regions:
            return ""
        # Estimate indentation from x-offset relative to leftmost region
        min_x = min(r.bbox[0] for r in regions)
        raw_lines = []
        for r in regions:
            indent_px = r.bbox[0] - min_x
            # Estimate character width from the region
            region_width = r.bbox[2] - r.bbox[0]
            char_count = len(r.text.replace("\t", "    "))
            char_width = region_width / max(char_count, 1)
            indent_chars = int(indent_px / max(char_width, 1))
            # Round to nearest 4-space indent
            indent_level = round(indent_chars / 4)
            raw_lines.append("    " * indent_level + r.text)
        # Clean IDE decorations and OCR artifacts from each line
        cleaned = []
        for line in raw_lines:
            c = _clean_ocr_line(line)
            if c:
                cleaned.append(c)
        return "\n".join(cleaned)

    if frame_type == FrameType.SLIDE:
        cleaned = [_clean_ocr_line(r.text) for r in regions]
        return "\n\n".join(c for c in cleaned if c)

    cleaned = [_clean_ocr_line(r.text) for r in regions]
    return " ".join(c for c in cleaned if c)


def _compute_frame_timestamps(
    video_path: str,
    duration: float,
    sample_interval: float = 0.7,
    min_gap: float = 0.5,
    start_offset: float = 0.0,
    end_limit: float | None = None,
) -> list[float]:
    """Build a deduplicated list of timestamps to extract frames at.

    Combines scene-change detection (catches visual transitions) with
    regular interval sampling (catches gradual changes).  Nearby
    timestamps closer than *min_gap* seconds are merged.

    Args:
        video_path: Path to the video file.
        duration: Total video duration in seconds.
        sample_interval: Seconds between interval samples.
        min_gap: Minimum gap between kept timestamps.
        start_offset: Start sampling at this time (seconds).
        end_limit: Stop sampling at this time (seconds). None = full duration.

    Returns:
        Sorted, deduplicated list of timestamps (seconds).
    """
    effective_end = end_limit if end_limit is not None else duration
    timestamps: set[float] = set()

    # 1. Scene detection — catches cuts, slide transitions, editor switches
    if HAS_SCENEDETECT:
        try:
            scenes = detect_scenes(video_path)
            for start, _end in scenes:
                # Take frame 0.5s after the scene starts (avoids transition blur)
                ts = round(start + 0.5, 1)
                if ts >= start_offset and ts < effective_end:
                    timestamps.add(ts)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Scene detection failed, falling back to interval: {exc}")

    # 2. Regular interval sampling — fills gaps between scene cuts
    t = max(0.5, start_offset)
    while t < effective_end:
        timestamps.add(round(t, 1))
        t += sample_interval

    # Always include near the end
    if effective_end > 2.0:
        timestamps.add(round(effective_end - 1.0, 1))

    # 3. Sort and deduplicate (merge timestamps closer than min_gap)
    sorted_ts = sorted(timestamps)
    if not sorted_ts:
        return []

    deduped = [sorted_ts[0]]
    for ts in sorted_ts[1:]:
        if ts - deduped[-1] >= min_gap:
            deduped.append(ts)
    return deduped


def _frames_are_similar(frame_a, frame_b, threshold: float = 3.0) -> bool:
    """Check if two OpenCV frames are visually similar.

    Uses mean absolute pixel difference on downscaled grayscale.
    This catches text changes on dark backgrounds that histogram
    correlation would miss.

    Args:
        frame_a: First BGR frame (numpy array).
        frame_b: Second BGR frame (numpy array).
        threshold: Mean pixel difference below this = "duplicate".
            Typical values: 1-2 for identical, 3-5 for minor text
            changes, 10+ for scene changes.

    Returns:
        True if the frames are similar enough to skip one.
    """
    import numpy as np

    gray_a = cv2.cvtColor(frame_a, cv2.COLOR_BGR2GRAY)
    gray_b = cv2.cvtColor(frame_b, cv2.COLOR_BGR2GRAY)

    # Resize to same small size for speed
    small = (320, 180)
    gray_a = cv2.resize(gray_a, small)
    gray_b = cv2.resize(gray_b, small)

    # Mean absolute pixel difference (0-255 scale)
    diff = np.abs(gray_a.astype(np.float32) - gray_b.astype(np.float32))
    mean_diff = diff.mean()

    return mean_diff < threshold


def _text_similarity(text_a: str, text_b: str) -> float:
    """Compute text similarity ratio using SequenceMatcher.

    Args:
        text_a: First text string.
        text_b: Second text string.

    Returns:
        Similarity ratio between 0.0 and 1.0.
    """
    if not text_a or not text_b:
        return 0.0
    return difflib.SequenceMatcher(None, text_a, text_b).ratio()


@dataclass
class YBucketLine:
    """A line tracked by y-coordinate across multiple frames."""

    y_center: float
    y_tolerance: float = 15.0
    observations: list[dict] = field(default_factory=list)
    consensus_text: str = ""
    consensus_confidence: float = 0.0


class YBucketConsensusEngine:
    """Build consensus text from OCR observations across multiple frames.

    Groups OCR regions by y-coordinate into buckets, then for each bucket
    selects the best text by clustering similar observations and picking
    the highest-confidence cluster winner.
    """

    def __init__(self, y_tolerance: float = 15.0):
        self._y_tolerance = y_tolerance
        self._buckets: list[YBucketLine] = []
        self._frame_count = 0

    def add_frame(
        self,
        frame_index: int,
        timestamp: float,
        ocr_regions: list[OCRRegion],
    ) -> None:
        """Feed one frame's OCR regions into the engine."""
        self._frame_count += 1
        for region in ocr_regions:
            y_center = (region.bbox[1] + region.bbox[3]) / 2.0
            obs = {
                "text": region.text,
                "confidence": region.confidence,
                "frame_index": frame_index,
                "timestamp": timestamp,
                "x_left": region.bbox[0],
                "x_right": region.bbox[2],
            }

            # Find matching bucket
            matched = False
            for bucket in self._buckets:
                if abs(bucket.y_center - y_center) <= bucket.y_tolerance:
                    bucket.observations.append(obs)
                    matched = True
                    break

            if not matched:
                self._buckets.append(
                    YBucketLine(
                        y_center=y_center,
                        y_tolerance=self._y_tolerance,
                        observations=[obs],
                    )
                )

    def build_consensus(self) -> list[YBucketLine]:
        """Build consensus text for each y-bucket.

        Algorithm:
        1. Sort observations by confidence (descending).
        2. Cluster observations by text similarity (ratio >= 0.6).
        3. Score clusters by sum of confidence weights.
        4. Winning cluster's highest-confidence observation = consensus_text.
        5. Single observations with confidence < 0.4 → empty (unreliable).
        """
        for bucket in self._buckets:
            if not bucket.observations:
                continue

            # Sort by confidence descending
            sorted_obs = sorted(bucket.observations, key=lambda o: o["confidence"], reverse=True)

            # Single observation with low confidence → skip
            if len(sorted_obs) == 1 and sorted_obs[0]["confidence"] < 0.4:
                bucket.consensus_text = ""
                bucket.consensus_confidence = 0.0
                continue

            # Cluster by text similarity
            clusters: list[list[dict]] = []
            for obs in sorted_obs:
                placed = False
                for cluster in clusters:
                    rep_text = cluster[0]["text"]
                    sim = _text_similarity(rep_text, obs["text"])
                    if sim >= 0.6:
                        cluster.append(obs)
                        placed = True
                        break
                if not placed:
                    clusters.append([obs])

            # Score clusters by sum of confidence
            best_cluster = max(clusters, key=lambda c: sum(o["confidence"] for o in c))

            # Winner = highest confidence in best cluster
            winner = best_cluster[0]  # already sorted by confidence
            bucket.consensus_text = winner["text"]
            bucket.consensus_confidence = sum(o["confidence"] for o in best_cluster) / len(
                best_cluster
            )

        # Sort buckets by y_center (top to bottom)
        self._buckets.sort(key=lambda b: b.y_center)
        return self._buckets

    def get_consensus_text(self) -> str:
        """Return assembled consensus text (newline-joined lines)."""
        return "\n".join(b.consensus_text for b in self._buckets if b.consensus_text)

    def get_consensus_confidence(self) -> float:
        """Return mean consensus confidence across non-empty buckets."""
        non_empty = [b for b in self._buckets if b.consensus_text]
        if not non_empty:
            return 0.0
        return sum(b.consensus_confidence for b in non_empty) / len(non_empty)

    def get_bucket_y_centers(self) -> set[float]:
        """Return the set of y-center values for all buckets."""
        return {b.y_center for b in self._buckets}

    def reset(self) -> None:
        """Clear all state."""
        self._buckets.clear()
        self._frame_count = 0


@dataclass
class TrackedTextBlock:
    """A text block tracked across multiple video frames."""

    first_seen: float
    last_seen: float
    frame_indices: list[int] = field(default_factory=list)
    text_snapshots: list[str] = field(default_factory=list)
    frame_type: FrameType = FrameType.OTHER
    best_text: str = ""
    best_confidence: float = 0.0
    # Consensus fields (Phase A)
    consensus_lines: list[dict] = field(default_factory=list)
    text_group_id: str = ""
    ocr_regions_per_frame: list[list[OCRRegion]] = field(default_factory=list)
    panel_bbox: tuple[int, int, int, int] | None = None
    panel_id: str = ""


class TextBlockTracker:
    """Track text blocks across video frames for continuity detection.

    Uses y-bucket overlap matching when OCR regions are available,
    falling back to text similarity matching otherwise.
    """

    def __init__(self, similarity_threshold: float = 0.6, y_tolerance: float = 15.0):
        self._active_blocks: list[TrackedTextBlock] = []
        self._completed_blocks: list[TrackedTextBlock] = []
        self._similarity_threshold = similarity_threshold
        self._y_tolerance = y_tolerance
        # Y-bucket consensus engines keyed by active block index
        self._engines: dict[int, YBucketConsensusEngine] = {}
        # Text group tracking
        self._text_groups: list[TextGroup] = []
        self._next_group_id = 1

    def update(
        self,
        frame_index: int,
        timestamp: float,
        ocr_text: str,
        confidence: float,
        frame_type: FrameType,
        ocr_regions: list[OCRRegion] | None = None,
        panel_bbox: tuple[int, int, int, int] | None = None,
    ) -> None:
        """Process a new frame's OCR results.

        For code/terminal frames: match against active blocks using panel
        position (when ``panel_bbox`` is provided), y-bucket overlap (when
        ``ocr_regions`` are provided), or text similarity as final fallback.
        For other frames: complete all active blocks.
        """
        is_code_frame = frame_type in (FrameType.CODE_EDITOR, FrameType.TERMINAL)

        if not is_code_frame:
            self._complete_all_active()
            return

        if not ocr_text or len(ocr_text.strip()) < 10:
            return

        best_match: TrackedTextBlock | None = None
        best_match_idx = -1

        # 1. Try panel position matching first (for per-panel OCR)
        if panel_bbox is not None:
            best_match, best_match_idx = self._match_by_panel_position(panel_bbox, ocr_text)

        # 2. Try y-bucket matching when regions are available
        if best_match is None and ocr_regions:
            best_match, best_match_idx = self._match_by_y_buckets(ocr_regions)

        # 3. Fallback to text similarity (skip when panel_bbox is provided —
        #    spatial position is the authoritative signal for panel identity)
        if best_match is None and panel_bbox is None:
            best_sim = 0.0
            for i, block in enumerate(self._active_blocks):
                sim = _text_similarity(block.best_text, ocr_text)
                if sim >= self._similarity_threshold and sim > best_sim:
                    best_match = block
                    best_match_idx = i
                    best_sim = sim

        if best_match is not None:
            best_match.last_seen = timestamp
            best_match.frame_indices.append(frame_index)
            best_match.text_snapshots.append(ocr_text)
            if ocr_regions:
                best_match.ocr_regions_per_frame.append(list(ocr_regions))
            if confidence > best_match.best_confidence:
                best_match.best_text = ocr_text
                best_match.best_confidence = confidence
            # Update panel_bbox if not set yet
            if panel_bbox is not None and best_match.panel_bbox is None:
                best_match.panel_bbox = panel_bbox
            # Feed into consensus engine
            if ocr_regions and best_match_idx in self._engines:
                self._engines[best_match_idx].add_frame(frame_index, timestamp, ocr_regions)
        else:
            new_idx = len(self._active_blocks)
            new_block = TrackedTextBlock(
                first_seen=timestamp,
                last_seen=timestamp,
                frame_indices=[frame_index],
                text_snapshots=[ocr_text],
                frame_type=frame_type,
                best_text=ocr_text,
                best_confidence=confidence,
                ocr_regions_per_frame=[list(ocr_regions)] if ocr_regions else [],
                panel_bbox=panel_bbox,
            )
            self._active_blocks.append(new_block)
            # Create consensus engine for new block
            engine = YBucketConsensusEngine(y_tolerance=self._y_tolerance)
            if ocr_regions:
                engine.add_frame(frame_index, timestamp, ocr_regions)
            self._engines[new_idx] = engine

    def _match_by_y_buckets(
        self, new_regions: list[OCRRegion]
    ) -> tuple[TrackedTextBlock | None, int]:
        """Match new frame regions against active blocks by y-bucket overlap.

        Returns (matched_block, block_index) or (None, -1) if no match.
        A match requires >= 40% of the new frame's region y-centers to
        fall within existing bucket y-centers (within tolerance).
        """
        if not self._active_blocks:
            return None, -1

        new_y_centers = []
        for r in new_regions:
            y_center = (r.bbox[1] + r.bbox[3]) / 2.0
            new_y_centers.append(y_center)

        if not new_y_centers:
            return None, -1

        best_block = None
        best_idx = -1
        best_overlap = 0.0

        for i, _block in enumerate(self._active_blocks):
            engine = self._engines.get(i)
            if engine is None:
                continue

            existing_y_centers = engine.get_bucket_y_centers()
            if not existing_y_centers:
                continue

            # Count how many new y-centers match existing buckets
            matched = 0
            for ny in new_y_centers:
                for ey in existing_y_centers:
                    if abs(ny - ey) <= self._y_tolerance:
                        matched += 1
                        break

            overlap = matched / len(new_y_centers)
            if overlap >= 0.4 and overlap > best_overlap:
                best_overlap = overlap
                best_block = self._active_blocks[i]
                best_idx = i

        return best_block, best_idx

    def _match_by_panel_position(
        self,
        panel_bbox: tuple[int, int, int, int],
        ocr_text: str,
    ) -> tuple[TrackedTextBlock | None, int]:
        """Match by panel x-range overlap (horizontal position).

        Two panels match if their x-ranges overlap by >= 50%.
        Also requires text similarity >= 0.3 to avoid matching
        completely different content that happens to be in the same position.
        """
        if not self._active_blocks:
            return None, -1

        px1, _py1, px2, _py2 = panel_bbox
        p_width = px2 - px1
        if p_width <= 0:
            return None, -1

        best_block: TrackedTextBlock | None = None
        best_idx = -1
        best_overlap = 0.0

        for i, block in enumerate(self._active_blocks):
            if block.panel_bbox is None:
                continue

            bx1, _by1, bx2, _by2 = block.panel_bbox
            b_width = bx2 - bx1
            if b_width <= 0:
                continue

            # Compute x-range overlap
            overlap_start = max(px1, bx1)
            overlap_end = min(px2, bx2)
            overlap_width = max(0, overlap_end - overlap_start)

            # Overlap as fraction of the smaller panel width
            min_width = min(p_width, b_width)
            x_overlap = overlap_width / min_width

            if x_overlap >= 0.5 and x_overlap > best_overlap:
                # Require minimal text similarity to avoid cross-matching
                sim = _text_similarity(block.best_text, ocr_text)
                if sim >= 0.3:
                    best_overlap = x_overlap
                    best_block = block
                    best_idx = i

        return best_block, best_idx

    def _complete_all_active(self) -> None:
        """Move all active blocks to completed, building consensus first."""
        for i, block in enumerate(self._active_blocks):
            engine = self._engines.get(i)
            if engine is not None:
                buckets = engine.build_consensus()
                block.consensus_lines = [
                    {
                        "y_center": b.y_center,
                        "text": b.consensus_text,
                        "confidence": b.consensus_confidence,
                    }
                    for b in buckets
                    if b.consensus_text
                ]
                consensus_text = engine.get_consensus_text()
                consensus_conf = engine.get_consensus_confidence()
                if consensus_text and consensus_conf > block.best_confidence:
                    block.best_text = consensus_text
                    block.best_confidence = consensus_conf

            self._completed_blocks.append(block)

        self._active_blocks.clear()
        self._engines.clear()

    def _assign_text_group(self, block: TrackedTextBlock) -> None:
        """Assign a text group ID to a completed block.

        Compares consensus_lines against existing TextGroups:
        - Overlap >= 60% → same group (possibly edited)
        - Overlap < 60% → new group
        """
        block_lines = [cl["text"] for cl in block.consensus_lines if cl.get("text")]
        if not block_lines:
            # Fallback: use best_text lines
            block_lines = [line for line in block.best_text.split("\n") if line.strip()]
        if not block_lines:
            return

        best_group = None
        best_overlap = 0.0

        for group in self._text_groups:
            group_lines = [cl["text"] for cl in group.consensus_lines if cl.get("text")]
            if not group_lines:
                continue

            # Compute overlap
            shorter_len = min(len(block_lines), len(group_lines))
            if shorter_len == 0:
                continue

            matched = 0
            for bl in block_lines:
                for gl in group_lines:
                    if _text_similarity(bl, gl) >= 0.6:
                        matched += 1
                        break

            overlap = matched / shorter_len
            if overlap >= 0.6 and overlap > best_overlap:
                best_overlap = overlap
                best_group = group

        if best_group is not None:
            # Same group — compute edit
            old_lines = [cl["text"] for cl in best_group.consensus_lines if cl.get("text")]
            edit = self._compute_edit(old_lines, block_lines, block.first_seen)
            if edit is not None:
                best_group.edits.append(edit)

            # Update group's consensus lines to new version
            best_group.consensus_lines = (
                list(block.consensus_lines)
                if block.consensus_lines
                else [
                    {"y_center": 0.0, "text": line, "confidence": block.best_confidence}
                    for line in block_lines
                ]
            )
            best_group.appearances.append((block.first_seen, block.last_seen))
            block.text_group_id = best_group.group_id
            # Propagate panel_id if not already set
            if block.panel_id and not best_group.panel_id:
                best_group.panel_id = block.panel_id
        else:
            # New group
            group_id = f"TG-{self._next_group_id:03d}"
            self._next_group_id += 1
            new_group = TextGroup(
                group_id=group_id,
                appearances=[(block.first_seen, block.last_seen)],
                consensus_lines=list(block.consensus_lines)
                if block.consensus_lines
                else [
                    {"y_center": 0.0, "text": line, "confidence": block.best_confidence}
                    for line in block_lines
                ],
                edits=[],
                frame_type=block.frame_type,
                panel_id=block.panel_id,
            )
            self._text_groups.append(new_group)
            block.text_group_id = group_id

    def _compute_edit(
        self, old_lines: list[str], new_lines: list[str], timestamp: float
    ) -> TextGroupEdit | None:
        """Compute a TextGroupEdit between old and new line lists."""
        if old_lines == new_lines:
            return None

        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
        added: list[str] = []
        removed: list[str] = []
        modified: list[dict] = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue
            elif tag == "insert":
                added.extend(new_lines[j1:j2])
            elif tag == "delete":
                removed.extend(old_lines[i1:i2])
            elif tag == "replace":
                for k, old_line in enumerate(old_lines[i1:i2]):
                    if k < (j2 - j1):
                        modified.append(
                            {
                                "line_num": i1 + k,
                                "old": old_line,
                                "new": new_lines[j1 + k],
                            }
                        )
                    else:
                        removed.append(old_line)
                if (j2 - j1) > (i2 - i1):
                    added.extend(new_lines[j1 + (i2 - i1) : j2])

        if not added and not removed and not modified:
            return None

        return TextGroupEdit(
            timestamp=timestamp,
            added_lines=added,
            removed_lines=removed,
            modified_lines=modified,
        )

    def finalize(self) -> list[TrackedTextBlock]:
        """Complete tracking, assign text groups, and return all blocks."""
        self._complete_all_active()
        for block in self._completed_blocks:
            self._assign_text_group(block)
        return list(self._completed_blocks)

    def get_text_groups(self) -> list[TextGroup]:
        """Return all text groups after finalize().

        Also runs language detection on groups that don't already have
        a detected_language set.
        """
        # Run language detection on each group
        try:
            from skill_seekers.cli.language_detector import LanguageDetector

            detector = LanguageDetector()
        except ImportError:
            detector = None

        if detector is not None:
            for group in self._text_groups:
                if group.detected_language:
                    continue  # Already detected
                text = group.full_text
                if text and len(text) >= 20:
                    try:
                        lang, _conf = detector.detect_from_code(text)
                        if lang:
                            group.detected_language = lang
                    except Exception:
                        pass

        return list(self._text_groups)


def _extract_code_blocks(
    tracked_blocks: list[TrackedTextBlock],
    text_groups: list[TextGroup] | None = None,
) -> list[CodeBlock]:
    """Convert tracked text blocks into CodeBlock objects.

    Filters for code/terminal frames with sufficient text length
    and attempts language detection. When text_groups are provided
    and a block has a text_group_id, uses the group's consensus text
    for better quality.

    Args:
        tracked_blocks: Tracked text blocks from TextBlockTracker.
        text_groups: Optional list of TextGroup objects for consensus text.

    Returns:
        List of CodeBlock objects with detected language.
    """
    code_blocks = []

    # Build lookup for text groups
    group_map: dict[str, TextGroup] = {}
    if text_groups:
        for tg in text_groups:
            group_map[tg.group_id] = tg

    # Lazy import language detector
    try:
        from skill_seekers.cli.language_detector import LanguageDetector

        detector = LanguageDetector()
    except ImportError:
        detector = None

    for block in tracked_blocks:
        if block.frame_type not in (FrameType.CODE_EDITOR, FrameType.TERMINAL):
            continue
        if len(block.best_text) < 20:
            continue

        # Use consensus text from text group when available
        code_text = block.best_text
        if block.text_group_id and block.text_group_id in group_map:
            group = group_map[block.text_group_id]
            group_text = group.full_text
            if group_text and len(group_text) >= 20:
                code_text = group_text

        # Detect language
        language = None
        if detector is not None:
            try:
                lang, _conf = detector.detect_from_code(code_text)
                if lang:
                    language = lang
            except Exception:  # noqa: BLE001
                pass

        # Map FrameType to CodeContext
        if block.frame_type == FrameType.CODE_EDITOR:
            context = CodeContext.EDITOR
        elif block.frame_type == FrameType.TERMINAL:
            context = CodeContext.TERMINAL
        else:
            context = CodeContext.UNKNOWN

        code_blocks.append(
            CodeBlock(
                code=code_text,
                language=language,
                source_frame=block.first_seen,
                context=context,
                confidence=block.best_confidence,
                text_group_id=block.text_group_id,
            )
        )

    return code_blocks


def _ocr_single_panel(
    frame_path: str,
    panel_bbox: tuple[int, int, int, int],
    panel_idx: int,
    frame_type: FrameType,
    full_area: int,
    regions: list[tuple[int, int, int, int, FrameType]],
    use_vision_api: bool,
) -> FrameSubSection | None:
    """OCR a single panel and return a FrameSubSection (or None).

    Designed to be called in parallel via ThreadPoolExecutor — each
    invocation is independent (unique crop path, no shared mutable state).
    """
    x1, y1, x2, y2 = panel_bbox
    panel_area = (x2 - x1) * (y2 - y1)

    # Crop panel if it's a subset of the frame
    cropped_path: str | None = None
    if panel_area < full_area * 0.9:
        cropped_path = _crop_code_region(frame_path, panel_bbox, suffix=f"_p{panel_idx}")
        ocr_target = cropped_path
    else:
        ocr_target = frame_path

    try:
        raw_results, _ = _run_multi_engine_ocr(ocr_target, frame_type)
        p_regions = _cluster_ocr_into_lines(raw_results, frame_type) if raw_results else []
        p_text = _assemble_structured_text(p_regions, frame_type) if p_regions else ""
        p_conf = sum(r.confidence for r in p_regions) / len(p_regions) if p_regions else 0.0

        # Vision API fallback for low-confidence panels
        vision_used = False
        if use_vision_api and p_conf < 0.5:
            v_text, v_conf = _ocr_with_claude_vision(ocr_target, frame_type)
            if v_text and v_conf > p_conf:
                p_text, p_conf, p_regions = v_text, v_conf, []
                vision_used = True
    finally:
        if cropped_path and os.path.exists(cropped_path):
            os.unlink(cropped_path)

    if not p_text.strip():
        return None

    row = sum(1 for r in regions if r[1] < y1)
    col = sum(1 for r in regions if r[0] < x1 and abs(r[1] - y1) < 50)

    ss = FrameSubSection(
        bbox=panel_bbox,
        frame_type=frame_type,
        ocr_text=p_text,
        ocr_regions=p_regions,
        ocr_confidence=p_conf,
        panel_id=f"panel_{row}_{col}",
    )
    # Stash vision_used flag for the caller to count
    ss._vision_used = vision_used
    return ss


def extract_visual_data(
    video_path: str,
    segments: list,
    output_dir: str,
    sample_interval: float = 0.7,
    min_gap: float = 0.5,
    similarity_threshold: float = 3.0,
    use_vision_api: bool = False,
    clip_start: float | None = None,
    clip_end: float | None = None,
) -> tuple[list[KeyFrame], list[CodeBlock], TextGroupTimeline | None]:
    """Run continuous visual extraction on a video.

    Instead of extracting one frame per segment, this scans the entire
    video using scene-change detection + interval sampling, deduplicates
    near-identical frames, classifies each frame, runs OCR with
    frame-type-aware preprocessing, preserves spatial layout, tracks
    text across frames with y-bucket consensus, and builds a text group
    timeline for code lifecycle tracking.

    For code/terminal frames, uses multi-engine OCR (EasyOCR + pytesseract)
    with ensemble voting.  When ``use_vision_api`` is True and multi-engine
    confidence is below 0.5, falls back to Claude Vision API.

    Args:
        video_path: Path to downloaded video file.
        segments: List of VideoSegment objects (used for duration hint).
        output_dir: Directory to save extracted frames.
        sample_interval: Seconds between interval samples (default 0.7s).
        min_gap: Minimum gap between kept timestamps (default 0.5s).
        similarity_threshold: Pixel-diff threshold for duplicate detection (default 3.0).
        use_vision_api: If True, use Claude Vision API as fallback for low-confidence
            code frames (requires ANTHROPIC_API_KEY).
        clip_start: Start of clip range in seconds (None = beginning).
        clip_end: End of clip range in seconds (None = full duration).

    Returns:
        Tuple of (keyframes, code_blocks, text_group_timeline).
        text_group_timeline is None when no code frames are found.
    """
    if not HAS_OPENCV:
        raise RuntimeError(_INSTALL_MSG)

    frames_dir = os.path.join(output_dir, "frames")
    # Clean stale frames from previous runs
    if os.path.exists(frames_dir):
        for old in os.listdir(frames_dir):
            if old.endswith(".jpg"):
                os.remove(os.path.join(frames_dir, old))
    os.makedirs(frames_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Cannot open video: {video_path}")
        return [], [], None

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = total_frames / fps if fps > 0 else 0.0

    # If segments give a better duration hint, use it
    if segments:
        seg_end = max(s.end_time for s in segments)
        if seg_end > duration:
            duration = seg_end

    logger.info(
        f"Continuous visual scan: {duration:.0f}s video, "
        f"interval={sample_interval}s, scene detection={'ON' if HAS_SCENEDETECT else 'OFF'}"
    )

    # Build candidate timestamps
    timestamps = _compute_frame_timestamps(
        video_path,
        duration,
        sample_interval=sample_interval,
        min_gap=min_gap,
        start_offset=clip_start or 0.0,
        end_limit=clip_end,
    )
    logger.info(f"  {len(timestamps)} candidate timestamps after dedup")

    keyframes = []
    prev_frame = None
    skipped_similar = 0
    vision_api_frames = 0
    tracker = TextBlockTracker()

    for ts in timestamps:
        frame_num = int(ts * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        if not ret:
            continue

        # Skip near-duplicate frames
        if prev_frame is not None and _frames_are_similar(
            prev_frame, frame, threshold=similarity_threshold
        ):
            skipped_similar += 1
            continue
        prev_frame = frame.copy()
        frame_h, frame_w = frame.shape[:2]

        # Save frame
        idx = len(keyframes)
        frame_filename = f"frame_{idx:03d}_{ts:.0f}s.jpg"
        frame_path = os.path.join(frames_dir, frame_filename)
        cv2.imwrite(frame_path, frame)
        del frame  # Free the numpy array early — saved to disk

        # Classify using region-based panel detection
        regions = classify_frame_regions(frame_path)
        code_panels = _get_code_panels(regions)
        # Derive frame_type from already-computed regions (avoids loading
        # the image a second time — classify_frame() would repeat the work).
        frame_type = _frame_type_from_regions(regions)
        is_code_frame = frame_type in (FrameType.CODE_EDITOR, FrameType.TERMINAL)

        # Per-panel OCR: each code/terminal panel is OCR'd independently
        # so side-by-side editors produce separate code blocks.
        sub_sections: list[FrameSubSection] = []
        ocr_text = ""
        ocr_regions: list[OCRRegion] = []
        ocr_confidence = 0.0

        if is_code_frame and code_panels and (HAS_EASYOCR or HAS_PYTESSERACT):
            full_area = frame_h * frame_w

            if len(code_panels) > 1:
                # Parallel OCR — each panel is independent
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=min(2, len(code_panels))
                ) as pool:
                    futures = {
                        pool.submit(
                            _ocr_single_panel,
                            frame_path,
                            pb,
                            pi,
                            frame_type,
                            full_area,
                            regions,
                            use_vision_api,
                        ): pi
                        for pi, pb in enumerate(code_panels)
                    }
                    for fut in concurrent.futures.as_completed(futures):
                        ss = fut.result()
                        if ss is not None:
                            if ss._vision_used:
                                vision_api_frames += 1
                            sub_sections.append(ss)
            else:
                # Single panel — avoid thread overhead
                ss = _ocr_single_panel(
                    frame_path,
                    code_panels[0],
                    0,
                    frame_type,
                    full_area,
                    regions,
                    use_vision_api,
                )
                if ss is not None:
                    if ss._vision_used:
                        vision_api_frames += 1
                    sub_sections.append(ss)

            # Track each sub-section independently
            for ss in sub_sections:
                tracker.update(
                    idx,
                    ts,
                    ss.ocr_text,
                    ss.ocr_confidence,
                    ss.frame_type,
                    ocr_regions=ss.ocr_regions,
                    panel_bbox=ss.bbox,
                )

            # Set frame-level OCR to best sub-section for backward compat
            if sub_sections:
                best_ss = max(sub_sections, key=lambda s: s.ocr_confidence)
                ocr_text = best_ss.ocr_text
                ocr_regions = best_ss.ocr_regions
                ocr_confidence = best_ss.ocr_confidence

        elif is_code_frame and (HAS_EASYOCR or HAS_PYTESSERACT):
            # No code panels detected but frame is code — OCR whole frame
            raw_ocr_results, _flat_text = _run_multi_engine_ocr(frame_path, frame_type)
            if raw_ocr_results:
                ocr_regions = _cluster_ocr_into_lines(raw_ocr_results, frame_type)
                ocr_text = _assemble_structured_text(ocr_regions, frame_type)
                ocr_confidence = (
                    sum(r.confidence for r in ocr_regions) / len(ocr_regions)
                    if ocr_regions
                    else 0.0
                )

            if use_vision_api and ocr_confidence < 0.5:
                vision_text, vision_conf = _ocr_with_claude_vision(frame_path, frame_type)
                if vision_text and vision_conf > ocr_confidence:
                    ocr_text = vision_text
                    ocr_confidence = vision_conf
                    ocr_regions = []
                    vision_api_frames += 1

            tracker.update(idx, ts, ocr_text, ocr_confidence, frame_type, ocr_regions=ocr_regions)

        elif HAS_EASYOCR and frame_type not in (FrameType.WEBCAM, FrameType.OTHER):
            # Standard EasyOCR for slide/diagram frames (skip webcam/other)
            raw_ocr_results, _flat_text = extract_text_from_frame(frame_path, frame_type)
            if raw_ocr_results:
                ocr_regions = _cluster_ocr_into_lines(raw_ocr_results, frame_type)
                ocr_text = _assemble_structured_text(ocr_regions, frame_type)
                ocr_confidence = (
                    sum(r.confidence for r in ocr_regions) / len(ocr_regions)
                    if ocr_regions
                    else 0.0
                )

            tracker.update(idx, ts, ocr_text, ocr_confidence, frame_type, ocr_regions=ocr_regions)

        kf = KeyFrame(
            timestamp=ts,
            image_path=frame_path,
            frame_type=frame_type,
            ocr_text=ocr_text,
            ocr_regions=ocr_regions,
            ocr_confidence=ocr_confidence,
            width=frame_w,
            height=frame_h,
            sub_sections=sub_sections,
        )
        keyframes.append(kf)

        logger.debug(
            f"  Frame {idx}: {frame_type.value} at {ts:.1f}s"
            + (
                f" | OCR: {ocr_text[:60]}..."
                if len(ocr_text) > 60
                else f" | OCR: {ocr_text}"
                if ocr_text
                else ""
            )
        )

        # Periodically collect to free PyTorch/numpy memory
        if idx % 10 == 9:
            gc.collect()

    cap.release()

    # Finalize text tracking and extract code blocks
    tracked_blocks = tracker.finalize()
    text_groups = tracker.get_text_groups()
    code_blocks = _extract_code_blocks(tracked_blocks, text_groups=text_groups)

    # Build timeline
    timeline: TextGroupTimeline | None = None
    if text_groups:
        total_code_time = sum(end - start for tg in text_groups for start, end in tg.appearances)
        total_edits = sum(len(tg.edits) for tg in text_groups)
        timeline = TextGroupTimeline(
            text_groups=text_groups,
            total_code_time=total_code_time,
            total_groups=len(text_groups),
            total_edits=total_edits,
        )

    vision_msg = f", {vision_api_frames} via Vision API" if vision_api_frames > 0 else ""
    logger.info(
        f"Extracted {len(keyframes)} unique keyframes "
        f"({skipped_similar} duplicates skipped), "
        f"{sum(1 for kf in keyframes if kf.ocr_text)} with OCR text, "
        f"{len(code_blocks)} code blocks detected, "
        f"{len(text_groups)} text groups{vision_msg}"
    )
    return keyframes, code_blocks, timeline


def download_video(
    url: str,
    output_dir: str,
    clip_start: float | None = None,
    clip_end: float | None = None,
) -> str | None:
    """Download a video using yt-dlp for visual processing.

    Downloads the best quality up to 1080p. Uses separate video+audio streams
    and merges them (via ffmpeg) since YouTube only offers combined streams at
    360p/720p — higher resolutions require downloading video-only + audio-only
    and muxing.

    Args:
        url: Video URL.
        output_dir: Directory to save the downloaded file.
        clip_start: Download from this time (seconds). None = beginning.
        clip_end: Download until this time (seconds). None = full video.

    Returns:
        Path to downloaded video file, or None on failure.
    """
    try:
        import yt_dlp
    except ImportError:
        logger.error("yt-dlp is required for video download")
        return None

    os.makedirs(output_dir, exist_ok=True)
    output_template = os.path.join(output_dir, "video.%(ext)s")

    opts = {
        "format": (
            "bestvideo[height<=1080][vcodec^=avc1]+bestaudio/best[height<=1080][vcodec^=avc1]/"
            "bestvideo[height<=1080][vcodec^=h264]+bestaudio/best[height<=1080][vcodec^=h264]/"
            "bestvideo[height<=1080]+bestaudio/best[height<=1080]"
        ),
        "merge_output_format": "mp4",
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
    }

    # Apply download_ranges for clip support (yt-dlp 2023.01.02+)
    if clip_start is not None or clip_end is not None:
        try:
            from yt_dlp.utils import download_range_func

            ranges = [(clip_start or 0, clip_end or float("inf"))]
            opts["download_ranges"] = download_range_func(None, ranges)
        except (ImportError, TypeError):
            logger.warning(
                "yt-dlp version does not support download_ranges; "
                "downloading full video and relying on frame timestamp filtering"
            )

    logger.info(f"Downloading video for visual extraction...")
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if os.path.exists(filename):
                logger.info(f"Downloaded: {filename}")
                return filename
            # Try common extensions
            for ext in ["mp4", "webm", "mkv"]:
                candidate = os.path.join(output_dir, f"video.{ext}")
                if os.path.exists(candidate):
                    return candidate
    except Exception as e:
        logger.error(f"Failed to download video: {e}")

    return None
