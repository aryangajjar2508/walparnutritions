import sys
sys.path.insert(0, '.')
from pathlib import Path
from app.ocr_manager import OCRManager
from app.formula_parser import FormulaParser

ocr_mgr = OCRManager()
parser = FormulaParser()
img_dir = Path('C:/Users/aryan/.gemini/antigravity/brain/e086dc92-aef5-46f2-9d32-a023fca8ddd7/.user_uploaded')
for label, p in [('Multivitamin', img_dir / 'media_1790247620630.jpg'), ('Probiotic', img_dir / 'media_1790247632363.jpg'), ('CoQ10', img_dir / 'media_1790247643671.jpg')]:
    lines, _ = ocr_mgr.extract_text(str(p), engine='rapidocr')
    items = parser.parse_ocr_lines(lines)
    print(f"{label}: extracted {len(items)} items from RapidOCR")
    for it in items[:4]:
        print(f"   - {it['name']}: {it['dosage']} {it['unit']}")
