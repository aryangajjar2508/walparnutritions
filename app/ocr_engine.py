import os
import cv2
import numpy as np
from typing import List, Dict, Any, Union
from pathlib import Path

# Fix for Windows / paddle conflict: import torch before paddle
import torch
import paddle
from paddleocr import PaddleOCR

class OCREngine:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        # Initialize PaddleOCR with enable_mkldnn=False to prevent oneDNN PIR bug on Windows CPU
        print("Initializing PaddleOCR engine...")
        self.ocr = PaddleOCR(
            use_textline_orientation=True,
            lang='en',
            enable_mkldnn=False
        )
        print("PaddleOCR engine initialized successfully.")

    def preprocess_image(self, img: np.ndarray) -> np.ndarray:
        """
        Enhance image for better OCR accuracy (contrast normalization, mild sharpening)
        """
        if img is None:
            return img

        # If too small, upscale
        h, w = img.shape[:2]
        if max(h, w) < 800:
            scale = 800.0 / max(h, w)
            img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)

        return img

    def extract_text(self, image_input: Union[str, Path, np.ndarray]) -> List[Dict[str, Any]]:
        """
        Run OCR on an image file path or numpy array.
        Returns list of text elements grouped logically by line:
        [{'text': 'Vitamin C 500mg', 'box': [[x1,y1],...], 'confidence': 0.98}, ...]
        """
        if isinstance(image_input, (str, Path)):
            img = cv2.imread(str(image_input))
            if img is None:
                raise ValueError(f"Could not load image from {image_input}")
        else:
            img = image_input

        img = self.preprocess_image(img)

        # Run PaddleOCR predict
        results = list(self.ocr.predict(img))
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
            
            # Format poly / box
            poly = rec_polys[i] if i < len(rec_polys) else None
            if poly is not None:
                if isinstance(poly, np.ndarray):
                    poly_list = poly.tolist()
                else:
                    poly_list = poly
                
                # Calculate bounding box
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
                "min_y": min_y,
                "max_x": max_x,
                "max_y": max_y,
                "center_y": center_y,
                "height": max_y - min_y
            })

        # Group horizontally-aligned text into lines
        grouped_lines = self._group_into_lines(raw_elements)
        return grouped_lines

    def _group_into_lines(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge words that are on the same line horizontally.
        """
        if not elements:
            return []

        # Sort elements primarily by Y (top to bottom), secondarily by X (left to right)
        elements.sort(key=lambda e: (e["center_y"], e["min_x"]))

        lines = []
        current_line = [elements[0]]

        for el in elements[1:]:
            prev = current_line[-1]
            avg_height = max(12, (prev["height"] + el["height"]) / 2.0)
            
            # If vertical distance between centers is within threshold (half line height)
            if abs(el["center_y"] - prev["center_y"]) < (avg_height * 0.75):
                current_line.append(el)
            else:
                # Merge current line
                lines.append(self._merge_line_elements(current_line))
                current_line = [el]

        if current_line:
            lines.append(self._merge_line_elements(current_line))

        return lines

    def _merge_line_elements(self, line_elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Sort left to right
        line_elements.sort(key=lambda e: e["min_x"])
        full_text = " ".join([e["text"] for e in line_elements])
        avg_conf = sum([e["confidence"] for e in line_elements]) / len(line_elements)
        
        # Bounding box encompassing all elements in the line
        min_x = min([e["min_x"] for e in line_elements])
        min_y = min([e["min_y"] for e in line_elements])
        max_x = max([e["max_x"] for e in line_elements])
        max_y = max([e["max_y"] for e in line_elements])
        
        return {
            "text": full_text,
            "confidence": round(avg_conf, 3),
            "box": [[min_x, min_y], [max_x, min_y], [max_x, max_y], [min_x, max_y]],
            "bbox": [min_x, min_y, max_x, max_y]
        }
