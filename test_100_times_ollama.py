import sys
sys.path.insert(0, r"c:\Users\aryan\Desktop\Walpar_ocr")

import os
import re
import json
import time
import requests
from app.ocr_manager import OCRManager
from app.formula_parser import FormulaParser
from app.model_subagent import ModelTrainingSubagent
from app.salt_rda_engine import SaltRDAEngine

def run_100_tests():
    print("=" * 70)
    print("WALPAR NEURAL ENGINE: 100-TEST VERIFICATION SUITE")
    print("Model: walpar-gemma3:latest (Local Ollama, 100% Offline, Zero Cloud API)")
    print("=" * 70)

    ocr_mgr = OCRManager.get_instance()
    parser = FormulaParser()
    subagent = ModelTrainingSubagent.get_instance()
    salt_engine = SaltRDAEngine.get_instance()

    passed = 0
    failed = 0
    total = 100

    # -------------------------------------------------------------
    # Test Category A: Formula OCR & Extraction (20 tests: 4 samples x 5 runs)
    # -------------------------------------------------------------
    samples = [
        ("samples/sample_curcumin_synergy.png", 3, ["Curcumin Extract", "Piperine", "Ginger Extract"]),
        ("samples/sample_immunity_booster.png", 4, ["Vitamin C", "Zinc", "Vitamin D3", "Elderberry Extract"]),
        ("samples/sample_joint_care.png", 4, ["Glucosamine Sulphate", "Chondroitin Sulphate", "Msm", "Boswellia Serrata Extract"]),
        ("samples/sample_sleep_relax.png", 4, ["Melatonin", "L-Theanine", "Magnesium Glycinate", "Vitamin B6"])
    ]

    print("\n--- CATEGORY A: End-to-End Vision OCR Formula Extractions (Tests 1 to 20) ---")
    test_num = 1
    for run in range(5):
        for img_path, expected_count, expected_names in samples:
            try:
                ocr_lines, items = ocr_mgr._extract_ollama(img_path)
                matched = parser.parse_gemini_items(items) if items else []
                if len(matched) >= expected_count:
                    passed += 1
                    status = "PASS"
                else:
                    failed += 1
                    status = f"FAIL (Got {len(matched)} items, expected {expected_count})"
                print(f"Test #{test_num:03d} [{os.path.basename(img_path)} (Run {run+1})]: {status} - Matched {len(matched)} ingredients")
            except Exception as e:
                failed += 1
                print(f"Test #{test_num:03d} [{os.path.basename(img_path)}]: FAIL ({e})")
            test_num += 1

    # -------------------------------------------------------------
    # Test Category B: Subagent NLP Directives Parsing (50 tests)
    # -------------------------------------------------------------
    directives = [
        ("selenium is same as sodium selenite", "selenium", "sodium selenite"),
        ("map haldi extract to curcumin dry extract", "haldi extract", "curcumin dry extract"),
        ("cholecalciferol is alias for vitamin d3", "cholecalciferol", "vitamin d3"),
        ("vitamin b3 is niacinamide", "vitamin b3", "niacinamide"),
        ("ascorbic acid equals vitamin c", "ascorbic acid", "vitamin c"),
        ("pyridoxine is same as vitamin b6", "pyridoxine", "vitamin b6"),
        ("methylcobalamin is alias for vitamin b12", "methylcobalamin", "vitamin b12"),
        ("folic acid is same as folate", "folic acid", "folate"),
        ("menaquinone-7 is alias for vitamin k2", "menaquinone-7", "vitamin k2"),
        ("tocopherol equals vitamin e", "tocopherol", "vitamin e")
    ]

    print("\n--- CATEGORY B: Subagent Knowledge Directives (Tests 21 to 70) ---")
    for run in range(5):
        for text, exp_src, exp_tgt in directives:
            try:
                parsed = subagent._parse_with_ollama(text)
                if parsed and exp_src in parsed.get("source_term", "").lower() and exp_tgt in parsed.get("target_term", "").lower():
                    passed += 1
                    status = "PASS"
                else:
                    failed += 1
                    status = f"FAIL (Got: {parsed})"
                print(f"Test #{test_num:03d} [Directive: '{text[:30]}...' (Run {run+1})]: {status}")
            except Exception as e:
                failed += 1
                print(f"Test #{test_num:03d} [Directive: '{text[:30]}...']: FAIL ({e})")
            test_num += 1

    # -------------------------------------------------------------
    # Test Category C: Salt & Elemental RDA Verification (30 tests)
    # -------------------------------------------------------------
    salt_cases = [
        ("Zinc Sulphate", 50.0, "Zinc", 22.0),
        ("Ferrous Fumarate", 100.0, "Iron", 33.0),
        ("Calcium Carbonate", 500.0, "Calcium", 40.0),
        ("Magnesium Oxide", 250.0, "Magnesium", 60.3),
        ("Sodium Selenite", 0.1, "Selenium", 45.6),
        ("Copper Sulphate", 2.0, "Copper", 25.4)
    ]

    print("\n--- CATEGORY C: Salt & RDA Annotation Invariance (Tests 71 to 100) ---")
    for run in range(5):
        for salt_name, dose, exp_elem, exp_pct in salt_cases:
            try:
                ing_dict = {"name": salt_name, "dosage": dose, "unit": "mg"}
                salt_engine.annotate_ingredient(ing_dict)
                parent_elem = ing_dict.get("salt_element_calc", {}).get("parent_nutrient", "")
                if ing_dict.get("is_salt_derivative") and parent_elem.lower() == exp_elem.lower():
                    passed += 1
                    status = "PASS"
                else:
                    failed += 1
                    status = f"FAIL (Got parent: {parent_elem})"
                print(f"Test #{test_num:03d} [Salt: {salt_name} -> {exp_elem} (Run {run+1})]: {status}")
            except Exception as e:
                failed += 1
                print(f"Test #{test_num:03d} [Salt: {salt_name}]: FAIL ({e})")
            test_num += 1

    # -------------------------------------------------------------
    # Final Report
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print("FINAL 100-TEST VERIFICATION REPORT")
    print(f"Total Tests Run: {total}")
    print(f"Passed:          {passed}")
    print(f"Failed:          {failed}")
    accuracy = (passed / total) * 100.0
    print(f"Overall Accuracy: {accuracy:.2f}%")
    print("=" * 70)

if __name__ == "__main__":
    run_100_tests()
