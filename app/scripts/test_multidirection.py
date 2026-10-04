import sys
sys.path.insert(0, '.')
from PIL import Image
from pathlib import Path
from app.ocr_manager import OCRManager
from app.formula_parser import FormulaParser

ocr = OCRManager()
parser = FormulaParser()

img_dir = Path("C:/Users/aryan/.gemini/antigravity/brain/e086dc92-aef5-46f2-9d32-a023fca8ddd7/.user_uploaded")
products = [
    ("Multivitamin Syrup", img_dir / "media_1790247620630.jpg", 90),
    ("Probiotic UTI", img_dir / "media_1790247632363.jpg", 180),
    ("CoQ10 + Arginine", img_dir / "media_1790247643671.jpg", 270),
]

print("===================================================================")
print("TESTING OCR ACCURACY ON MULTI-DIRECTION ROTATED PRODUCTS")
print("===================================================================")

for label, p, angle in products:
    im = Image.open(p)
    rotated = im.rotate(angle, expand=True)
    temp_p = Path(f"temp_dir_test_{angle}.jpg")
    rotated.save(temp_p)
    print(f"\n>>> PRODUCT: {label} (ROTATED {angle}°)")
    
    lines, gemini_items = ocr.extract_text(str(temp_p), engine="gemini")
    if gemini_items:
        items = parser.parse_gemini_items(gemini_items)
        print(f"    Source: Gemini Vision | Extracted {len(items)} active ingredients:")
        for it in items[:6]:
            print(f"      - {it['name']}: {it['dosage']} {it['unit']} -> [{it['id']}] {it['match_score']}%")
    else:
        items = parser.parse_ocr_lines(lines)
        print(f"    Source: Fallback OCR | Extracted {len(items)} active ingredients:")
        for it in items[:6]:
            print(f"      - {it['name']}: {it['dosage']} {it['unit']}")

    if temp_p.exists():
        temp_p.unlink()

print("\n===================================================================")
print("MULTI-DIRECTION TEST COMPLETED")
print("===================================================================")
