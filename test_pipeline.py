from app.ocr_engine import OCREngine
from app.formula_parser import FormulaParser
from app.evaluator import FormulaEvaluator
from app.pricing_engine import PricingEngine

ocr = OCREngine.get_instance()
parser = FormulaParser()
evaluator = FormulaEvaluator()
pricer = PricingEngine()

lines = ocr.extract_text('samples/sample_immunity_booster.png')
print(f"Extracted {len(lines)} lines from sample.")

ingredients = parser.parse_ocr_lines(lines)
print(f"Parsed {len(ingredients)} ingredients:")
for item in ingredients:
    print(f"  * {item['name']}: {item['dosage']} {item['unit']}")

evaluation = evaluator.evaluate_formula(ingredients, 'effervescent')
print(f"\nEvaluation Score: {evaluation['score']}/100 ({evaluation['status_label']})")
print("Synergies detected:")
for syn in evaluation['synergies']:
    print(f"  + {syn['title']}: {syn['description']}")

quote = pricer.calculate_quote(ingredients, 'effervescent', batch_quantity=10000)
print(f"\nInstant Pricing Quote (10,000 units):")
print(f"  * Unit Selling Price: Rs {quote['pricing']['unit_selling_price_inr']}")
print(f"  * Total Batch with 18% GST: Rs {quote['pricing']['total_batch_with_gst_inr']:,}")
