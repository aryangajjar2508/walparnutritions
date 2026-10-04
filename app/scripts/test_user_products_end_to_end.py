import sys
sys.path.insert(0, '.')
import os
from pathlib import Path
from app.ocr_manager import OCRManager
from app.formula_parser import FormulaParser

ocr_mgr = OCRManager()
parser = FormulaParser()

img_dir = Path("C:/Users/aryan/.gemini/antigravity/brain/e086dc92-aef5-46f2-9d32-a023fca8ddd7/.user_uploaded")
test_images = [
    ("Multivitamin Syrup", img_dir / "media_1790247620630.jpg"),
    ("Probiotic UTI Capsule", img_dir / "media_1790247632363.jpg"),
    ("CoQ10 + Arginine Sachet", img_dir / "media_1790247643671.jpg")
]

print("==========================================================")
print("TESTING FULL OCR & EXTRACTION PIPELINE ON USER PRODUCTS")
print("==========================================================")

for label, img_path in test_images:
    print(f"\n>>> PRODUCT: {label}")
    print(f"    Path: {img_path.name}")
    if not img_path.exists():
        print(f"    FILE NOT FOUND!")
        continue

    try:
        ocr_lines, gemini_items = ocr_mgr.extract_text(str(img_path), engine="gemini")
        if gemini_items:
            items = parser.parse_gemini_items(gemini_items)
            source = "Gemini Vision"
        else:
            items = parser.parse_ocr_lines(ocr_lines)
            source = "Local OCR Fallback"

        print(f"    Source: {source} | Total active ingredients extracted: {len(items)}")
        for it in items:
            db_id = it.get('id')
            db_name = it.get('db_raw_name', '')
            score = it.get('match_score', 0)
            status = f"MATCHED [ID: {db_id}] '{db_name}' ({score}%)" if it.get('is_matched') else f"CUSTOM / NOT IN DB [ID: {db_id}]"
            print(f"      - {it.get('name')}: {it.get('dosage')} {it.get('unit')} -> {status}")
        import time
        time.sleep(3)
    except Exception as e:
        print(f"    ERROR processing {label}: {e}")
        import traceback
        traceback.print_exc()

print("\n==========================================================")
print("COMPLETED USER PRODUCTS PIPELINE TEST")
print("==========================================================")
