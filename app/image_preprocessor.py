"""
Walpar Image Preprocessor
=========================
Automatically corrects:
  - EXIF orientation (phone camera metadata)
  - 90° / 180° / 270° rotation (portrait/landscape mix-up)
  - Slight deskew (tilted handheld photos)
  - Perspective/keystone distortion (angled shots)
  - Contrast, sharpness, and noise

Used BEFORE any OCR engine so results are always accurate
regardless of how the user photographed the label.
"""

import cv2
import numpy as np
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
from pathlib import Path
from typing import Union
import math


# ──────────────────────────────────────────────────────────────
#  Public API
# ──────────────────────────────────────────────────────────────

def preprocess_for_ocr(image_input: Union[str, Path, np.ndarray],
                       save_path: Union[str, Path, None] = None) -> np.ndarray:
    """
    Full preprocessing pipeline.
    Returns a cleaned, upright BGR numpy array ready for any OCR engine.
    If save_path is given, also saves the corrected image to disk (overwrites).
    """
    # Step 1 — Load as PIL (handles EXIF)
    pil_img = _load_and_fix_exif(image_input)

    # Step 2 — Convert to OpenCV BGR
    cv_img = _pil_to_cv(pil_img)

    # Step 3 — Auto-rotate to upright (0°/90°/180°/270°)
    cv_img = _auto_rotate(cv_img)

    # Step 4 — Deskew slight tilt (±30°)
    cv_img = _deskew(cv_img)

    # Step 5 — Perspective correction (if strong keystone)
    cv_img = _perspective_correct(cv_img)

    # Step 6 — Enhance contrast / sharpen
    cv_img = _enhance(cv_img)

    # Step 7 — Optionally save back
    if save_path is not None:
        cv2.imwrite(str(save_path), cv_img)

    return cv_img


def preprocess_pil(image_input: Union[str, Path, np.ndarray]) -> Image.Image:
    """Convenience wrapper that returns a PIL Image (for Gemini API)."""
    cv_img = preprocess_for_ocr(image_input)
    return Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))


def detect_document_corners(image_input: Union[str, Path, np.ndarray]) -> dict:
    """
    Intelligently detect the 4 corners of a document or formula label in an image
    using adaptive edge detection and convex quadrilateral contour approximation.
    Returns normalized coordinates [0.0 - 1.0] for:
    {'tl': [x, y], 'tr': [x, y], 'br': [x, y], 'bl': [x, y]}
    """
    try:
        pil_img = _load_and_fix_exif(image_input)
        cv_img = _pil_to_cv(pil_img)
        h, w = cv_img.shape[:2]

        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 40, 140)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilated = cv2.dilate(edges, kernel, iterations=1)

        contours, _ = cv2.findContours(dilated, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        img_area = float(h * w)
        best_quad = None
        best_area = 0.0

        for cnt in sorted(contours, key=cv2.contourArea, reverse=True)[:20]:
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.025 * peri, True)
            if len(approx) == 4 and cv2.isContourConvex(approx):
                area = float(cv2.contourArea(approx))
                if 0.08 * img_area < area < 0.98 * img_area and area > best_area:
                    best_area = area
                    best_quad = approx

        if best_quad is not None:
            pts = best_quad.reshape(4, 2).astype(np.float32)
            ordered = _order_points(pts)
            return {
                'tl': [float(round(max(0.0, min(1.0, ordered[0][0] / w)), 4)), float(round(max(0.0, min(1.0, ordered[0][1] / h)), 4))],
                'tr': [float(round(max(0.0, min(1.0, ordered[1][0] / w)), 4)), float(round(max(0.0, min(1.0, ordered[1][1] / h)), 4))],
                'br': [float(round(max(0.0, min(1.0, ordered[2][0] / w)), 4)), float(round(max(0.0, min(1.0, ordered[2][1] / h)), 4))],
                'bl': [float(round(max(0.0, min(1.0, ordered[3][0] / w)), 4)), float(round(max(0.0, min(1.0, ordered[3][1] / h)), 4))]
            }
    except Exception as e:
        print(f"[DocScanner] Corner auto-detection notice: {e}")

    # Default fallback: 6% inset quadrilateral
    return {
        'tl': [0.06, 0.06],
        'tr': [0.94, 0.06],
        'br': [0.94, 0.94],
        'bl': [0.06, 0.94]
    }


def warp_perspective_quad(image_input: Union[str, Path, np.ndarray],
                          corners: dict,
                          rotation: int = 0,
                          save_path: Union[str, Path, None] = None) -> np.ndarray:
    """
    Doc-Scanner Perspective Warp:
    Straightens an arbitrary quadrilateral region defined by 4 corners into
    a flat, un-skewed rectangular image using projective homography.
    corners: {'tl': [x, y], 'tr': [x, y], 'br': [x, y], 'bl': [x, y]} in normalized (0.0 - 1.0) coords.
    rotation: optional rotation in degrees (0, 90, 180, 270) before cropping.
    """
    pil_img = _load_and_fix_exif(image_input)
    cv_img = _pil_to_cv(pil_img)

    # Apply pre-rotation if requested
    if rotation == 90:
        cv_img = cv2.rotate(cv_img, cv2.ROTATE_90_CLOCKWISE)
    elif rotation == 180:
        cv_img = cv2.rotate(cv_img, cv2.ROTATE_180)
    elif rotation == 270:
        cv_img = cv2.rotate(cv_img, cv2.ROTATE_90_COUNTERCLOCKWISE)

    h, w = cv_img.shape[:2]

    # Convert normalized corners to pixel coordinates
    tl = np.array([float(corners['tl'][0]) * w, float(corners['tl'][1]) * h], dtype=np.float32)
    tr = np.array([float(corners['tr'][0]) * w, float(corners['tr'][1]) * h], dtype=np.float32)
    br = np.array([float(corners['br'][0]) * w, float(corners['br'][1]) * h], dtype=np.float32)
    bl = np.array([float(corners['bl'][0]) * w, float(corners['bl'][1]) * h], dtype=np.float32)

    src = np.array([tl, tr, br, bl], dtype=np.float32)

    # Calculate optimal output width & height based on opposite edge lengths
    width_a = np.linalg.norm(br - bl)
    width_b = np.linalg.norm(tr - tl)
    max_w = int(max(width_a, width_b))

    height_a = np.linalg.norm(tr - br)
    height_b = np.linalg.norm(tl - bl)
    max_h = int(max(height_a, height_b))

    max_w = max(60, min(max_w, 1600))
    max_h = max(60, min(max_h, 1600))

    dst = np.array([
        [0, 0],
        [max_w - 1, 0],
        [max_w - 1, max_h - 1],
        [0, max_h - 1]
    ], dtype=np.float32)

    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(cv_img, M, (max_w, max_h),
                                 flags=cv2.INTER_CUBIC,
                                 borderMode=cv2.BORDER_REPLICATE)

    if save_path is not None:
        cv2.imwrite(str(save_path), warped)

    return warped


# ──────────────────────────────────────────────────────────────
#  Step 1 — Load + EXIF
# ──────────────────────────────────────────────────────────────

def render_text_document_image(lines: list, title: str = "FORMULATION SPECIFICATION") -> Image.Image:
    """Renders a structured, high-resolution document image from plain text lines."""
    w = 1200
    line_h = 36
    h = max(800, 160 + len(lines[:120]) * line_h)
    img = Image.new("RGB", (w, h), (255, 255, 255))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    
    # Elegant Walpar Blue Header
    draw.rectangle([(0, 0), (w, 80)], fill=(15, 76, 129))
    draw.text((40, 26), f"WALPAR NUTRACEUTICALS • {title[:50].upper()}", fill=(255, 255, 255))
    
    # Subtitle bar
    draw.rectangle([(0, 80), (w, 110)], fill=(241, 245, 249))
    draw.text((40, 88), "DIGITAL FORMULATION DOCUMENT • EXTRACTED SPECIFICATION", fill=(100, 116, 139))
    
    cur_y = 135
    for idx, l in enumerate(lines[:120]):
        bg_col = (248, 250, 252) if idx % 2 == 0 else (255, 255, 255)
        draw.rectangle([(25, cur_y - 4), (w - 25, cur_y + line_h - 6)], fill=bg_col, outline=(226, 232, 240))
        draw.text((45, cur_y + 2), str(l), fill=(30, 41, 59))
        cur_y += line_h
    return img


def _load_and_fix_exif(image_input: Union[str, Path, np.ndarray]) -> Image.Image:
    """Load image and apply EXIF orientation correction. Supports PDF, DOCX, XLSX, CSV, TXT, HEIC, TIFF, PNG, JPG."""
    if isinstance(image_input, (str, Path)):
        p_str = str(image_input).lower()
        if p_str.endswith(".pdf"):
            try:
                import fitz
                doc = fitz.open(str(image_input))
                if len(doc) > 0:
                    pix = doc[0].get_pixmap(dpi=300)
                    pil_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                else:
                    pil_img = Image.new("RGB", (600, 800), (255, 255, 255))
                doc.close()
                return pil_img
            except Exception as e:
                print(f"[Preprocessor] PDF load fallback: {e}")
                pil_img = Image.new("RGB", (600, 800), (255, 255, 255))
        elif p_str.endswith((".docx", ".doc")):
            try:
                import docx
                d = docx.Document(str(image_input))
                lines = [p.text.strip() for p in d.paragraphs if p.text.strip()]
                for t in d.tables:
                    for r in t.rows:
                        row_t = " ".join(c.text.strip() for c in r.cells if c.text.strip())
                        if row_t: lines.append(row_t)
                return render_text_document_image(lines, title="WORD FORMULATION SHEET")
            except Exception as e:
                print(f"[Preprocessor] DOCX load fallback: {e}")
                return Image.new("RGB", (600, 800), (255, 255, 255))
        elif p_str.endswith((".xlsx", ".xls", ".csv")):
            try:
                lines = []
                if p_str.endswith(".csv"):
                    import csv
                    with open(str(image_input), "r", encoding="utf-8", errors="ignore") as f:
                        for r in csv.reader(f):
                            if any(r): lines.append(" ".join(c.strip() for c in r if c.strip()))
                else:
                    import openpyxl
                    wb = openpyxl.load_workbook(str(image_input), data_only=True)
                    for s in wb.sheetnames:
                        ws = wb[s]
                        for r in ws.iter_rows(values_only=True):
                            c = [str(x).strip() for x in r if x is not None and str(x).strip()]
                            if c: lines.append(" ".join(c))
                return render_text_document_image(lines, title="EXCEL FORMULATION SHEET")
            except Exception as e:
                print(f"[Preprocessor] XLSX load fallback: {e}")
                return Image.new("RGB", (600, 800), (255, 255, 255))
        elif p_str.endswith(".txt"):
            try:
                with open(str(image_input), "r", encoding="utf-8", errors="ignore") as f:
                    lines = [l.strip() for l in f if l.strip()]
                return render_text_document_image(lines, title="TEXT FORMULATION SHEET")
            except Exception as e:
                print(f"[Preprocessor] TXT load fallback: {e}")
                return Image.new("RGB", (600, 800), (255, 255, 255))
        else:
            try:
                import pillow_heif
                pillow_heif.register_heif_opener()
            except Exception:
                pass
            pil_img = Image.open(str(image_input))
    elif isinstance(image_input, np.ndarray):
        # Already a numpy array (BGR) — convert
        pil_img = Image.fromarray(cv2.cvtColor(image_input, cv2.COLOR_BGR2RGB))
    else:
        pil_img = image_input

    # Fix EXIF rotation (phone cameras store orientation in metadata)
    try:
        pil_img = ImageOps.exif_transpose(pil_img)
    except Exception:
        pass

    # Ensure RGB
    if pil_img.mode not in ("RGB", "L"):
        pil_img = pil_img.convert("RGB")

    # Downscale exceptionally large images (e.g. 12MP-48MP) to 2400px using LANCZOS to preserve maximum sharp edge fidelity
    max_dim = 2400
    w, h = pil_img.size
    if max(w, h) > max_dim:
        scale = max_dim / float(max(w, h))
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    return pil_img


# ──────────────────────────────────────────────────────────────
#  Step 2 — PIL → CV2
# ──────────────────────────────────────────────────────────────

def _pil_to_cv(pil_img: Image.Image) -> np.ndarray:
    rgb = np.array(pil_img.convert("RGB"))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


# ──────────────────────────────────────────────────────────────
#  Step 3 — Auto-rotate (0 / 90 / 180 / 270)
# ──────────────────────────────────────────────────────────────

def _text_score(gray: np.ndarray) -> float:
    """
    Simple text-region density score.
    High score = image likely upright (horizontal text lines dominate).
    Uses horizontal Sobel edges as proxy for horizontal text lines.
    """
    h, w = gray.shape
    if h == 0 or w == 0:
        return 0.0
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    # Horizontal edge strength
    sobel_h = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=3)
    # Vertical edge strength
    sobel_v = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3)
    h_strength = np.sum(np.abs(sobel_h))
    v_strength = np.sum(np.abs(sobel_v))
    total = h_strength + v_strength
    if total == 0:
        return 0.5
    return float(h_strength / total)


def _auto_rotate(cv_img: np.ndarray) -> np.ndarray:
    """
    Intelligently check if image is sideways (90° or 270°) and correct it.
    Does not falsely rotate upright images based on edge noise.
    """
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    base_score = _text_score(gray)

    # If baseline horizontal edge density is already solid (>= 0.46), keep original 0° orientation
    if base_score >= 0.46:
        return cv_img

    candidates = [
        (cv2.rotate(cv_img, cv2.ROTATE_90_CLOCKWISE),         90),
        (cv2.rotate(cv_img, cv2.ROTATE_90_COUNTERCLOCKWISE),  270),
        (cv2.rotate(cv_img, cv2.ROTATE_180),                  180),
    ]

    best_img, best_score, best_angle = cv_img, base_score, 0
    for img, angle in candidates:
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        score = _text_score(g)
        # Only switch orientation if significantly higher (at least 20% improvement)
        if score > best_score * 1.20 and score > 0.55:
            best_score, best_img, best_angle = score, img, angle

    if best_angle != 0:
        print(f"[Preprocessor] Auto-rotated {best_angle}° (score={best_score:.3f} vs base={base_score:.3f})")

    return best_img


# ──────────────────────────────────────────────────────────────
#  Step 4 — Deskew slight tilt
# ──────────────────────────────────────────────────────────────

def _get_skew_angle(gray: np.ndarray) -> float:
    """
    Detect skew angle of text using Hough line transform.
    Returns angle in degrees in range [-45, 45].
    """
    # Threshold to binary
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Dilate to connect nearby text blobs into lines
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 1))
    dilated = cv2.dilate(thresh, kernel, iterations=2)

    # Detect lines
    coords = np.column_stack(np.where(dilated > 0))
    if len(coords) < 50:
        return 0.0

    # minAreaRect gives angle of the enclosing bounding box
    angle = cv2.minAreaRect(coords)[-1]

    # Normalize angle to [-45, 45]
    if angle < -45:
        angle = 90 + angle
    elif angle > 45:
        angle = angle - 90

    return float(angle)


def _rotate_image(img: np.ndarray, angle: float) -> np.ndarray:
    """Rotate image by given angle (degrees) around center, keeping full image."""
    h, w = img.shape[:2]
    cx, cy = w // 2, h // 2
    M = cv2.getRotationMatrix2D((cx, cy), angle, 1.0)

    # Compute new bounding size
    cos_a = abs(M[0, 0])
    sin_a = abs(M[0, 1])
    new_w = int(h * sin_a + w * cos_a)
    new_h = int(h * cos_a + w * sin_a)
    M[0, 2] += (new_w / 2) - cx
    M[1, 2] += (new_h / 2) - cy

    rotated = cv2.warpAffine(img, M, (new_w, new_h),
                              flags=cv2.INTER_CUBIC,
                              borderMode=cv2.BORDER_REPLICATE)
    return rotated


def _deskew(cv_img: np.ndarray) -> np.ndarray:
    """Correct slight tilt in handheld photos (±30° range)."""
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    angle = _get_skew_angle(gray)

    # Only correct if tilt is meaningful (>0.5°) and not extreme (rotations handled above)
    if abs(angle) < 0.5 or abs(angle) > 30:
        return cv_img

    print(f"[Preprocessor] Deskewing {angle:.2f}°")
    return _rotate_image(cv_img, angle)


# ──────────────────────────────────────────────────────────────
#  Step 5 — Perspective correction (angled shots)
# ──────────────────────────────────────────────────────────────

def _perspective_correct(cv_img: np.ndarray) -> np.ndarray:
    """
    Detect if the largest rectangular region (e.g. a label/package) is
    significantly keystoned and correct it. Skips if correction would distort.
    """
    try:
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)

        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return cv_img

        # Find the largest 4-point contour (likely the label)
        img_area = h * w
        best_quad = None
        best_area = 0

        for cnt in sorted(contours, key=cv2.contourArea, reverse=True)[:10]:
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)

            if len(approx) == 4:
                area = cv2.contourArea(approx)
                # Must be at least 20% of image and at most 98%
                if 0.20 * img_area < area < 0.98 * img_area and area > best_area:
                    best_area = area
                    best_quad = approx

        if best_quad is None:
            return cv_img

        pts = best_quad.reshape(4, 2).astype(np.float32)

        # Order points: top-left, top-right, bottom-right, bottom-left
        rect = _order_points(pts)
        tl, tr, br, bl = rect

        # Compute output width/height
        width_a = np.linalg.norm(br - bl)
        width_b = np.linalg.norm(tr - tl)
        max_w = int(max(width_a, width_b))

        height_a = np.linalg.norm(tr - br)
        height_b = np.linalg.norm(tl - bl)
        max_h = int(max(height_a, height_b))

        if max_w < 100 or max_h < 100:
            return cv_img

        # Check keystone severity — only correct if skew ratio > 5%
        skew_ratio_w = abs(width_a - width_b) / max(width_a, width_b)
        skew_ratio_h = abs(height_a - height_b) / max(height_a, height_b)

        if skew_ratio_w < 0.05 and skew_ratio_h < 0.05:
            return cv_img  # Already straight enough

        dst = np.array([
            [0,         0        ],
            [max_w - 1, 0        ],
            [max_w - 1, max_h - 1],
            [0,         max_h - 1]
        ], dtype=np.float32)

        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(cv_img, M, (max_w, max_h),
                                     flags=cv2.INTER_CUBIC,
                                     borderMode=cv2.BORDER_REPLICATE)

        print(f"[Preprocessor] Perspective corrected (skew_w={skew_ratio_w:.2f}, skew_h={skew_ratio_h:.2f})")
        return warped

    except Exception as e:
        print(f"[Preprocessor] Perspective correction skipped: {e}")
        return cv_img


def _order_points(pts: np.ndarray) -> np.ndarray:
    """Order 4 points as [top-left, top-right, bottom-right, bottom-left]."""
    rect = np.zeros((4, 2), dtype=np.float32)
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]   # top-left: smallest sum
    rect[2] = pts[np.argmax(s)]   # bottom-right: largest sum
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # top-right: smallest diff
    rect[3] = pts[np.argmax(diff)]  # bottom-left: largest diff
    return rect


# ──────────────────────────────────────────────────────────────
#  Step 6 — Enhance contrast / sharpness
# ──────────────────────────────────────────────────────────────

def _enhance(cv_img: np.ndarray) -> np.ndarray:
    """
    Adaptive contrast enhancement + mild sharpening.
    Makes faded/low-light photos much more legible.
    """
    # Convert to PIL for easier enhancement
    pil = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))

    # Auto-contrast (clips histogram to improve range)
    pil = ImageOps.autocontrast(pil, cutoff=1)

    # Sharpness boost
    pil = ImageEnhance.Sharpness(pil).enhance(1.5)

    # Back to OpenCV
    enhanced = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

    # CLAHE (Contrast Limited Adaptive Histogram Equalization) per channel
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    lab = cv2.cvtColor(enhanced, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = clahe.apply(l)
    enhanced = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)

    return enhanced
