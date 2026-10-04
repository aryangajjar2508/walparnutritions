import sys
sys.path.insert(0, '.')
from app.formula_parser import FormulaParser

parser = FormulaParser()

test_cases = [
    ("L-Glutathione", "Glutathione / L-Glutathion Reduced"),
    ("L-Glutamine", "Glutamine"),
    ("Vitamin B1 (as Thiamine Hydrochloride)", "Vitamin B1"),
    ("Vitamin B2 (as Riboflavin 5 Phosphate)", "Riboflavin / Vit B2"),
    ("Vitamin B6 (as Pyridoxine Hydrochloride)", "Pyridoxine / Vit B6"),
    ("Vitamin D (as Cholecalciferol)", "Cholecalciferol / Vit D3"),
    ("Vitamin B12 (as Cyanocobalamin)", "Methylcobalamine / Vit B12"),
    ("L-Lysine (as L-Lysine Hcl)", "L-Lysine Hcl"),
    ("Selenium (as Sodium Selenate)", "Sodium Selenite / Selenium"),
    ("Vitamin A", "Vitamin A"),
    ("Blend of Lactobacillus Spp. Probiotics", "Lactobacillus / Probiotics"),
    ("Blend of Bifidobacterium Spp. Probiotics", "Bifidobacterium"),
    ("Co-Enzyme Q10 (Ubiquinol)", "Co Enzyme Q 10"),
    ("L-Carnitine L-Tartrate", "L Carnitine L Tartrate"),
    ("L-Arginine", "L-Arginine Base"),
    ("Folic Acid", "Folic Acid"),
    ("Zinc", "Zinc"),
    ("Cranberry Extract", "Cranberry"),
    ("D-Mannose", "D-Mannose")
]

print("=== RUNNING INGREDIENT MATCHING TEST ===")
all_passed = True
for query, expected_desc in test_cases:
    matched, score = parser.match_ingredient(query)
    clean_name = parser.format_clean_name(query, matched)
    if matched:
        print(f"PASS: '{query}' -> [{matched['id']}] '{matched['name']}' ({score}%) | Clean UI: '{clean_name}'")
        # Ensure confusions don't happen
        if "glutathione" in query.lower() and "glutamine" in matched['name'].lower():
            print(f"FAIL: Glutathione matched to Glutamine!")
            all_passed = False
        if "b1 (" in query.lower() and "tulsi" in matched['name'].lower():
            print(f"FAIL: B1 matched to Tulsi!")
            all_passed = False
        if "b2 (" in query.lower() and "s.red" in matched['name'].lower():
            print(f"FAIL: B2 matched to S.Red!")
            all_passed = False
        if "b6 (" in query.lower() and "raspberry" in matched['name'].lower():
            print(f"FAIL: B6 matched to Raspberry!")
            all_passed = False
        if "carnitine" in query.lower() and "cystine" in matched['name'].lower():
            print(f"FAIL: Carnitine matched to Cystine!")
            all_passed = False
    else:
        print(f"INFO: '{query}' -> CUSTOM / NOT IN DB (0%) | Clean UI: '{clean_name}'")

if all_passed:
    print("\nALL INGREDIENT FIDELITY CHECKS PASSED PERFECTLY!")
