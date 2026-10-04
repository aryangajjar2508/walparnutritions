import os
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import re
import json
import hashlib
import cv2
import numpy as np
from typing import List, Dict, Any, Union, Tuple, Optional
from pathlib import Path
from PIL import Image

import pytesseract
import shutil

if os.name == 'nt':
    if os.path.exists(r"C:\Program Files\Tesseract-OCR\tesseract.exe"):
        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:
    tess_path = shutil.which("tesseract") or "/usr/bin/tesseract"
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except Exception:
    pass

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

try:
    from rapidocr_onnxruntime import RapidOCR
    RAPID_AVAILABLE = True
except ImportError:
    RAPID_AVAILABLE = False

try:
    import torch
    import paddle
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
except Exception:
    PADDLE_AVAILABLE = False

from app.config import GEMINI_API_KEY, GEMINI_MODEL, CACHE_DB_PATH

# ─────────────────────────────────────────────────────────────
#  Unicode safety: strip chars that crash Windows cp1252 charmap
#  (arrows →, degree °, micro µ, etc. can appear in OCR output)
# ─────────────────────────────────────────────────────────────
def _safe_text(text: str) -> str:
    """Replace/remove characters that cannot be encoded in cp1252 (Windows charmap)."""
    if not isinstance(text, str):
        return str(text)
    # Common OCR substitutions for nutraceutical labels
    _REPLACEMENTS = {
        '\u2192': '->',   # → right arrow
        '\u2190': '<-',   # ← left arrow
        '\u2022': '-',    # • bullet
        '\u00b0': ' ',    # ° degree
        '\u00b5': 'mcg',  # µ micro (often means mcg)
        '\u03bc': 'mcg',  # μ greek mu
        '\u2264': '<=',   # ≤
        '\u2265': '>=',   # ≥
        '\u00ae': '',     # ® registered
        '\u2122': '',     # ™ trademark
        '\u00a9': '',     # © copyright
        '\u2019': "'",    # ' right single quote
        '\u2018': "'",    # ' left single quote
        '\u201c': '"',    # " left double quote
        '\u201d': '"',    # " right double quote
        '\u2013': '-',    # – en dash
        '\u2014': '-',    # — em dash
        '\u00bd': '1/2',  # ½
        '\u00bc': '1/4',  # ¼
        '\u00be': '3/4',  # ¾
        '\u00b1': '+/-',  # ±
        '\u00d7': 'x',    # × multiplication
        '\u00f7': '/',    # ÷ division
    }
    for char, replacement in _REPLACEMENTS.items():
        text = text.replace(char, replacement)

    # Word-level common OCR corrections in nutraceutical text
    text = re.sub(r'\bcalclum\b', 'calcium', text, flags=re.IGNORECASE)
    text = re.sub(r'\blrom\b', 'from', text, flags=re.IGNORECASE)
    text = re.sub(r'\btrom\b', 'from', text, flags=re.IGNORECASE)
    text = re.sub(r'\bvitamind3\b', 'Vitamin D3', text, flags=re.IGNORECASE)
    text = re.sub(r'\bexciplent\b', 'excipient', text, flags=re.IGNORECASE)
    text = re.sub(r'\bintormation\b', 'information', text, flags=re.IGNORECASE)
    text = re.sub(r'\bnutritlonal\b', 'nutritional', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(?:ni009|nioo9|ni008|n1009)\b', '600 IU', text, flags=re.IGNORECASE)

    # Final safety: encode to cp1252 and back, replacing anything that still fails
    return text.encode('cp1252', errors='replace').decode('cp1252', errors='replace')


# ─────────────────────────────────────────────────────────────
#  Internal helper: run preprocessor safely
# ─────────────────────────────────────────────────────────────
def _preprocess_to_cv(image_input: Union[str, Path, np.ndarray]) -> np.ndarray:
    """Return preprocessed BGR ndarray for local OCR engines."""
    try:
        from app.image_preprocessor import preprocess_for_ocr
        return preprocess_for_ocr(image_input)
    except Exception as e:
        print(f"[Preprocessor] Skipped ({e}), using raw image")
        if isinstance(image_input, (str, Path)):
            img = cv2.imread(str(image_input))
            return img if img is not None else np.zeros((100, 100, 3), dtype=np.uint8)
        return image_input if isinstance(image_input, np.ndarray) else np.zeros((100, 100, 3), dtype=np.uint8)


def _preprocess_to_pil(image_input: Union[str, Path, np.ndarray]) -> Image.Image:
    """Return preprocessed PIL RGB image for vision APIs and Tesseract."""
    try:
        from app.image_preprocessor import preprocess_pil
        return preprocess_pil(image_input)
    except Exception as e:
        print(f"[Preprocessor] PIL fallback ({e})")
        if isinstance(image_input, (str, Path)):
            from PIL import ImageOps
            pil = Image.open(str(image_input))
            try:
                pil = ImageOps.exif_transpose(pil)
            except Exception:
                pass
            return pil.convert("RGB")
        cv_img = image_input if isinstance(image_input, np.ndarray) else np.zeros((100, 100, 3), dtype=np.uint8)
        return Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))


class OCRManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.rapid_engine = None
        self.paddle_engine = None
        self.gemini_model = None
        self.knowledge_cache = {}
        self._gemini_quota_exhausted_until = 0.0
        self._load_cache()
        self._init_gemini()
        self._init_rapid()

    def _load_cache(self):
        try:
            if CACHE_DB_PATH.exists():
                with open(CACHE_DB_PATH, "r", encoding="utf-8") as f:
                    self.knowledge_cache = json.load(f)
        except Exception as e:
            print(f"Error loading knowledge cache: {e}")

    def _save_cache(self, image_hash: str, parsed_items: list, raw_text: str):
        try:
            self.knowledge_cache[image_hash] = {
                "extracted_items": parsed_items,
                "raw_text": raw_text
            }
            with open(CACHE_DB_PATH, "w", encoding="utf-8") as f:
                json.dump(self.knowledge_cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving to knowledge cache: {e}")

    def _init_gemini(self):
        if GENAI_AVAILABLE and GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                self.gemini_model = genai.GenerativeModel(GEMINI_MODEL)
                print(f"Gemini API ({GEMINI_MODEL}) initialized successfully.")
            except Exception as e:
                print(f"Error configuring Gemini API: {e}")

    def _init_rapid(self):
        if RAPID_AVAILABLE and self.rapid_engine is None:
            try:
                self.rapid_engine = RapidOCR()
            except Exception as e:
                print(f"Error initializing RapidOCR: {e}")

    def _init_paddle(self):
        if PADDLE_AVAILABLE and self.paddle_engine is None:
            try:
                self.paddle_engine = PaddleOCR(
                    use_textline_orientation=True,
                    lang='en',
                    enable_mkldnn=False
                )
            except Exception as e:
                print(f"Error initializing PaddleOCR: {e}")

    def get_available_engines(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "gemini",
                "name": "Walpar Neural Vision Engine (AI Model - High Precision)",
                "description": "Proprietary deep learning vision model with contextual formula intelligence and auto-learning.",
                "is_default": True
            },
            {
                "id": "rapidocr",
                "name": "Walpar Fast Engine (Local ONNX)",
                "description": "High-accuracy local deep learning model. 100% offline execution.",
                "is_default": False
            },
            {
                "id": "easyocr",
                "name": "Walpar Mobile Lens Engine (Local PyTorch)",
                "description": "Optimized for mobile camera photos and rotated text.",
                "is_default": False
            },
            {
                "id": "paddleocr",
                "name": "Walpar Layout Engine (Local PP-OCR)",
                "description": "Comprehensive layout and line-orientation detection.",
                "is_default": False
            },
            {
                "id": "tesseract",
                "name": "Walpar Standard Engine (Local Tesseract 5.5)",
                "description": "Standard document layout recognizer.",
                "is_default": False
            },
            {
                "id": "ensemble",
                "name": "Walpar Multi-Engine Ensemble (Cross-Verification)",
                "description": "Cross-verifies formula text across multiple engines.",
                "is_default": False
            }
        ]

    def extract_text(self, image_input: Union[str, Path, np.ndarray], engine: str = "gemini") -> Tuple[List[Dict[str, Any]], Optional[List[Dict[str, Any]]]]:
        """
        Returns (ocr_lines, gemini_parsed_items_or_None)
        Preprocessing (auto-rotate, deskew, perspective, enhance) is applied
        inside EVERY engine path.
        """
        engine_id = (engine or "gemini").lower()

        if engine_id in ["gemini", "google", "ai"]:
            return self._extract_gemini_with_fallback(image_input)
        elif engine_id in ["rapidocr", "rapid"]:
            return self._extract_rapid(image_input), None
        elif engine_id in ["easyocr", "easy"]:
            return self._extract_easyocr(image_input), None
        elif engine_id in ["paddleocr", "paddle"]:
            return self._extract_paddle(image_input), None
        elif engine_id in ["tesseract", "tess"]:
            return self._extract_tesseract(image_input), None
        elif engine_id in ["ensemble", "multi"]:
            return self._extract_ensemble(image_input), None
        else:
            return self._extract_gemini_with_fallback(image_input)

    # ─────────────────────────────────────────────────────────
    #  Gemini Vision API
    # ─────────────────────────────────────────────────────────
    def _extract_gemini_with_fallback(self, image_input: Union[str, Path, np.ndarray]) -> Tuple[List[Dict[str, Any]], Optional[List[Dict[str, Any]]]]:
        """
        Runs Gemini 2.5 Flash Vision with angle-aware prompt.
        Preprocessing (rotate/deskew/perspective/enhance) applied before sending.
        Falls back to local RapidOCR (also preprocessed) on any error.
        """
        # ── Fast check: if quota cooldown is active, fall back immediately without waiting ──
        import time
        if time.time() < self._gemini_quota_exhausted_until:
            print("[OCRManager] Cloud quota cooldown active. Using local engine directly.")
            return self._extract_rapid(image_input), None

        # ── Preprocess first (rotate, deskew, perspective, enhance) ──
        pil_img = _preprocess_to_pil(image_input)

        try:
            if not self.gemini_model:
                self._init_gemini()

            if not self.gemini_model:
                raise RuntimeError("Vision model not initialized")

            # ── Angle-aware & Active-ingredient focused prompt ──
            prompt = """You are an expert pharmaceutical and nutraceutical chemist at Walpar.

The image may be a photo taken at any angle — rotated, tilted, upside-down or from the side.
First, mentally correct the orientation to read all text clearly.
Then carefully extract ONLY the ACTIVE ingredients from the formulation / supplement facts table that have a stated dosage and unit.

RULES:
- ORIENTATION: The photo might be taken in ANY direction: upright (0°), rotated 90° clockwise, upside-down (180°), rotated 270° counter-clockwise, tilted, or slanted. Mentally rotate the image as needed and read every ingredient and dosage accurately in whichever direction the text flows.
- ONLY extract active formulation ingredients with a clear strength/dosage and unit (e.g. mg, mcg, IU, g, %, Billion CFU, ml).
- Exact chemical fidelity: Extract the EXACT ingredient name as printed on the label (e.g. "L-Glutathione", "Alpha Lipoic Acid", "Vitamin C", "Grape Seed Extract", "L-Arginine").
- CRITICAL: NEVER confuse or substitute distinct compounds! Do NOT write "L-Glutamine" if the label says "L-Glutathione". Do NOT write "Thiamine" if the label says "Theanine". Do NOT write "L-Cystine" if the label says "L-Carnitine".
- Dosage must be a number only (e.g. 100, 50, 500, 1.5).
- Unit must be one of: mg, mcg, IU, g, %, Billion CFU, ml.
- Strictly DO NOT include: "Other Ingredients", excipients without dosages (e.g. starch, talc, magnesium stearate, PVPK, DCP, aerosil, colors), batch numbers, expiry dates, RDA disclaimers, or manufacturing text.

Return ONLY a valid JSON list, no markdown, no explanation:
[
  {"name": "L-Glutathione", "dosage": 100, "unit": "mg"},
  {"name": "Alpha Lipoic Acid", "dosage": 100, "unit": "mg"},
  {"name": "Vitamin C", "dosage": 50, "unit": "mg"}
]
"""
            try:
                response = self.gemini_model.generate_content([prompt, pil_img])
            except Exception as api_err:
                err_str = str(api_err).lower()
                if "quota" in err_str or "429" in err_str or "resource_exhausted" in err_str or "resourceexhausted" in err_str:
                    print("[OCRManager] Quota limit hit. Activating 10-minute local engine cooldown.")
                    self._gemini_quota_exhausted_until = time.time() + 600
                raise api_err

            resp_text = response.text.strip()

            # Clean possible markdown ticks ```json ... ```
            cleaned_json = re.sub(r'^```json\s*', '', resp_text, flags=re.IGNORECASE | re.MULTILINE)
            cleaned_json = re.sub(r'^```\s*', '', cleaned_json, flags=re.MULTILINE)
            cleaned_json = re.sub(r'```\s*$', '', cleaned_json).strip()

            # Handle case where Gemini wraps in a single object instead of list
            if cleaned_json.startswith('{'):
                cleaned_json = f"[{cleaned_json}]"

            parsed_items = json.loads(cleaned_json)

            # Validate: must be a list
            if not isinstance(parsed_items, list):
                raise ValueError(f"Expected JSON list, got: {type(parsed_items)}")

            # Convert into standard OCR line representations
            ocr_lines = []
            h, w = pil_img.size[1], pil_img.size[0]
            step_y = max(20, h // max(1, len(parsed_items) + 2))

            for idx, item in enumerate(parsed_items):
                name = _safe_text(str(item.get("name", "")).strip())
                dose = item.get("dosage", "")
                unit = _safe_text(str(item.get("unit", "")).strip())
                full_line = _safe_text(f"{name} {dose} {unit}".strip())
                y = (idx + 1) * step_y

                ocr_lines.append({
                    "text": full_line,
                    "confidence": 0.99,
                    "box": [[20, y], [w - 20, y], [w - 20, y + 25], [20, y + 25]],
                    "bbox": [20, y, w - 20, y + 25]
                })

            # Save to local knowledge cache for self-learning
            img_hash = hashlib.md5(pil_img.tobytes()[:2048]).hexdigest()
            self._save_cache(img_hash, parsed_items, resp_text)

            print(f"[OCRManager] Extracted {len(parsed_items)} ingredients successfully.")
            return ocr_lines, parsed_items

        except Exception as e:
            print(f"[OCRManager Fallback -> local engine]: {e}")
            preprocessed_cv = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            rapid_lines = self._extract_rapid(preprocessed_cv)
            return rapid_lines, None

    # ─────────────────────────────────────────────────────────
    #  RapidOCR (ONNX local with multi-angle auto-scan)
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def _score_rapid_results(results: list) -> float:
        if not results:
            return -100.0
        dosages = 0
        keywords = 0
        horiz_boxes = 0
        vert_boxes = 0
        total_conf = 0.0

        dose_pat = re.compile(r'\d+(?:\.\d+)?\s*(?:mg|mcg|iu|g|ml|cfu)\b', re.I)
        kw_pat = re.compile(r'\b(vitamin|calcium|magnesium|zinc|iron|acid|extract|each|tablet|tablets|capsule|capsules|contains|composition|serving|nutritional|information|energy|protein|fat|carbohydrate|daily|value)\b', re.I)

        for box, text, conf in results:
            text_str = str(text)
            total_conf += float(conf)
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            w = max(xs) - min(xs)
            h = max(ys) - min(ys)
            if w > 1.25 * h:
                horiz_boxes += 1
            elif h > 1.25 * w:
                vert_boxes += 1

            if dose_pat.search(text_str):
                dosages += 1
            if kw_pat.search(text_str):
                keywords += 1

        return (dosages * 30.0) + (keywords * 15.0) + (horiz_boxes * 2.5) - (vert_boxes * 8.0) + (total_conf * 0.1)

    def _extract_rapid(self, image_input: Union[str, Path, np.ndarray]) -> List[Dict[str, Any]]:
        if not self.rapid_engine:
            self._init_rapid()
        if not self.rapid_engine:
            return self._extract_tesseract(image_input)

        # Preprocess: rotate, deskew, perspective, enhance
        if isinstance(image_input, np.ndarray):
            img = image_input   # already preprocessed (from fallback path)
        else:
            img = _preprocess_to_cv(image_input)

        results, _ = self.rapid_engine(img)
        best_results = results or []
        best_score = self._score_rapid_results(best_results)

        # Multi-Angle Auto-Scan:
        # Check if text appears vertical (words taller than wide) or if 0° yielded no valid dosages
        vert_count = sum(1 for box, _, _ in (results or []) if (max(p[1] for p in box) - min(p[1] for p in box)) > 1.25 * (max(p[0] for p in box) - min(p[0] for p in box)))
        horiz_count = sum(1 for box, _, _ in (results or []) if (max(p[0] for p in box) - min(p[0] for p in box)) > 1.25 * (max(p[1] for p in box) - min(p[1] for p in box)))
        dose_count = sum(1 for _, text, _ in (results or []) if re.search(r'\d+(?:\.\d+)?\s*(?:mg|mcg|iu|g|ml|cfu)\b', str(text), re.I))

        if (results and vert_count > horiz_count) or dose_count < 2 or best_score < 100.0:
            for rot_code in [cv2.ROTATE_90_COUNTERCLOCKWISE, cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_180]:
                rot_img = cv2.rotate(img, rot_code)
                rot_res, _ = self.rapid_engine(rot_img)
                sc = self._score_rapid_results(rot_res or [])
                if sc > best_score:
                    best_score = sc
                    best_results = rot_res

        if not best_results:
            return []

        raw_elements = []
        for box, text, conf in best_results:
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            center_y = (min_y + max_y) / 2.0

            raw_elements.append({
                "text": str(text).strip(),
                "confidence": float(conf),
                "box": box,
                "bbox": [min_x, min_y, max_x, max_y],
                "min_x": min_x,
                "max_x": max_x,
                "min_y": min_y,
                "max_y": max_y,
                "center_y": center_y,
                "height": max_y - min_y
            })

        return self._merge_horizontal_rows(raw_elements)

    # ─────────────────────────────────────────────────────────
    #  EasyOCR (PyTorch)
    # ─────────────────────────────────────────────────────────
    def _extract_easyocr(self, image_input: Union[str, Path, np.ndarray]) -> List[Dict[str, Any]]:
        import easyocr
        # EasyOCR has its own angle correction, but our preprocessor makes it more reliable
        img = _preprocess_to_cv(image_input)

        reader = easyocr.Reader(
            ['en'],
            gpu=False,
            verbose=False
        )
        # Pass as ndarray so EasyOCR doesn't re-load from path (gets preprocessed array)
        results = reader.readtext(img)
        if not results:
            return []

        raw_elements = []
        for box, text, conf in results:
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            center_y = (min_y + max_y) / 2.0

            raw_elements.append({
                "text": str(text).strip(),
                "confidence": float(conf),
                "box": box,
                "bbox": [min_x, min_y, max_x, max_y],
                "min_x": min_x,
                "max_x": max_x,
                "min_y": min_y,
                "max_y": max_y,
                "center_y": center_y,
                "height": max_y - min_y
            })

        return self._merge_horizontal_rows(raw_elements)

    # ─────────────────────────────────────────────────────────
    #  PaddleOCR
    # ─────────────────────────────────────────────────────────
    def _extract_paddle(self, image_input: Union[str, Path, np.ndarray]) -> List[Dict[str, Any]]:
        if not self.paddle_engine:
            self._init_paddle()
        if not self.paddle_engine:
            return self._extract_rapid(image_input)

        # Preprocess: rotate, deskew, perspective, enhance
        if isinstance(image_input, np.ndarray):
            img = image_input
        else:
            img = _preprocess_to_cv(image_input)

        results = list(self.paddle_engine.predict(img))
        if not results:
            return []

        res = results[0]
        rec_texts = res.get("rec_texts", [])
        rec_scores = res.get("rec_scores", [])
        rec_polys = res.get("rec_polys", [])
        if not rec_polys and "dt_polys" in res:
            rec_polys = res.get("dt_polys", [])

        raw_elements = []
        for i in range(len(rec_texts)):
            text = str(rec_texts[i]).strip()
            score = float(rec_scores[i]) if i < len(rec_scores) else 0.9
            poly = rec_polys[i] if i < len(rec_polys) else None

            if poly is not None:
                poly_list = poly.tolist() if isinstance(poly, np.ndarray) else poly
                xs = [p[0] for p in poly_list]
                ys = [p[1] for p in poly_list]
                min_x, max_x = min(xs), max(xs)
                min_y, max_y = min(ys), max(ys)
                center_y = (min_y + max_y) / 2.0
            else:
                poly_list = []
                min_x, min_y, max_x, max_y = 0, 0, 0, 0
                center_y = i * 25.0

            raw_elements.append({
                "text": text,
                "confidence": score,
                "box": poly_list,
                "bbox": [min_x, min_y, max_x, max_y],
                "min_x": min_x,
                "max_x": max_x,
                "min_y": min_y,
                "max_y": max_y,
                "center_y": center_y,
                "height": max_y - min_y
            })

        return self._merge_horizontal_rows(raw_elements)

    # ─────────────────────────────────────────────────────────
    #  Tesseract
    # ─────────────────────────────────────────────────────────
    def _extract_tesseract(self, image_input: Union[str, Path, np.ndarray]) -> List[Dict[str, Any]]:
        # Preprocess: rotate, deskew, perspective, enhance
        if isinstance(image_input, np.ndarray):
            pil_img = Image.fromarray(cv2.cvtColor(image_input, cv2.COLOR_BGR2RGB))
        else:
            pil_img = _preprocess_to_pil(image_input)

        # PSM 6 = assume a single uniform block of text (best for ingredient tables)
        config = "--psm 6 --oem 3"
        data = pytesseract.image_to_data(pil_img, config=config, output_type=pytesseract.Output.DICT)
        n_boxes = len(data["text"])
        raw_elements = []

        for i in range(n_boxes):
            text = data["text"][i].strip()
            conf = float(data["conf"][i])
            if text and conf > 25:
                x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
                box = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]
                raw_elements.append({
                    "text": text,
                    "confidence": conf / 100.0,
                    "box": box,
                    "bbox": [x, y, x + w, y + h],
                    "min_x": x,
                    "max_x": x + w,
                    "min_y": y,
                    "max_y": y + h,
                    "center_y": y + (h / 2.0),
                    "height": h
                })

        return self._merge_horizontal_rows(raw_elements)

    # ─────────────────────────────────────────────────────────
    #  Ensemble (cross-verify multiple engines)
    # ─────────────────────────────────────────────────────────
    def _extract_ensemble(self, image_input: Union[str, Path, np.ndarray]) -> List[Dict[str, Any]]:
        """
        Run RapidOCR + Tesseract, merge results:
        - Lines confirmed by both engines get confidence boost
        - Lines from only one engine are still included
        """
        # Preprocess once, share the result to avoid doing it twice
        preprocessed_cv = _preprocess_to_cv(image_input)
        preprocessed_pil = Image.fromarray(cv2.cvtColor(preprocessed_cv, cv2.COLOR_BGR2RGB))

        rapid_lines = self._extract_rapid(preprocessed_cv)
        tesseract_lines = self._extract_tesseract(preprocessed_pil)

        if not rapid_lines and not tesseract_lines:
            return []

        # Merge: use rapid as base, boost conf if tesseract confirms same text
        merged = {line["text"].lower().strip(): line for line in rapid_lines}

        for t_line in tesseract_lines:
            t_text = t_line["text"].lower().strip()
            if t_text in merged:
                # Confirmed by both — boost confidence
                merged[t_text]["confidence"] = min(0.99, merged[t_text]["confidence"] + 0.1)
            else:
                # Only in tesseract — add it
                merged[t_text] = t_line

        # Re-sort by vertical position
        all_lines = sorted(merged.values(), key=lambda l: l["bbox"][1])
        return all_lines

    # ─────────────────────────────────────────────────────────
    #  Row merging helpers
    # ─────────────────────────────────────────────────────────
    def _merge_horizontal_rows(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not elements:
            return []

        # Sort elements primarily by vertical center
        elements.sort(key=lambda e: e["center_y"])
        rows = []
        for el in elements:
            placed = False
            el_w = el.get("width", el["max_x"] - el["min_x"])
            for r in rows:
                row_cy = sum(e["center_y"] for e in r) / len(r)
                row_h = sum(e["height"] for e in r) / len(r)
                # Must be vertically aligned with the row's center
                if abs(el["center_y"] - row_cy) < (row_h * 0.45):
                    # Must NOT have major horizontal overlap with any element already in this row
                    has_x_overlap = False
                    for existing in r:
                        ex_w = existing.get("width", existing["max_x"] - existing["min_x"])
                        overlap_x = max(0, min(el["max_x"], existing["max_x"]) - max(el["min_x"], existing["min_x"]))
                        min_w = min(el_w, ex_w)
                        if min_w > 0 and (overlap_x / min_w) > 0.25:
                            has_x_overlap = True
                            break
                    if not has_x_overlap:
                        r.append(el)
                        placed = True
                        break
            if not placed:
                rows.append([el])

        # Fuse elements in each row, then sort all rows top to bottom
        lines = []
        for r in rows:
            lines.append(self._fuse_row_elements(r))

        lines.sort(key=lambda l: l["bbox"][1])
        return lines

    def _fuse_row_elements(self, row_elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        row_elements.sort(key=lambda e: e["min_x"])
        # _safe_text applied here covers ALL local engines (RapidOCR, EasyOCR, Paddle, Tesseract)
        full_text = _safe_text(" ".join([e["text"] for e in row_elements]))
        avg_conf = sum([e["confidence"] for e in row_elements]) / len(row_elements)
        min_x = min([e["min_x"] for e in row_elements])
        min_y = min([e["min_y"] for e in row_elements])
        max_x = max([e["max_x"] for e in row_elements])
        max_y = max([e["max_y"] for e in row_elements])

        return {
            "text": full_text,
            "confidence": round(avg_conf, 3),
            "box": [[min_x, min_y], [max_x, min_y], [max_x, max_y], [min_x, max_y]],
            "bbox": [min_x, min_y, max_x, max_y]
        }
