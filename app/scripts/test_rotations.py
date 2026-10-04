import sys
sys.path.insert(0, '.')
from PIL import Image
from pathlib import Path
from app.ocr_manager import OCRManager
from app.formula_parser import FormulaParser

ocr = OCRManager()
parser = FormulaParser()

img_path = Path('C:/Users/aryan/.gemini/antigravity/brain/e086dc92-aef5-46f2-9d32-a023fca8ddd7/.user_uploaded/media_1790247643671.jpg')
im = Image.open(img_path)

for angle in [0, 90, 180, 270]:
    rotated = im.rotate(angle, expand=True)
    temp_p = Path(f'temp_test_rot_{angle}.jpg')
    rotated.save(temp_p)
    print(f"\n=================== TESTING ANGLE {angle}° ===================")
    lines, gemini_items = ocr.extract_text(str(temp_p), engine='gemini')
    if gemini_items:
        items = parser.parse_gemini_items(gemini_items)
        print(f"Angle {angle}°: Extracted {len(items)} items via Gemini Vision:")
        for it in items:
            print(f"  - {it['name']}: {it['dosage']} {it['unit']} [{it['id']}]")
    else:
        items = parser.parse_ocr_lines(lines)
        print(f"Angle {angle}°: Extracted {len(items)} items via fallback:")
        for it in items:
            print(f"  - {it['name']}: {it['dosage']} {it['unit']}")
    if temp_p.exists():
        temp_p.unlink()
