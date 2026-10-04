import google.generativeai as genai
from PIL import Image
import json

import os
api_key = os.environ.get("GEMINI_API_KEY", "")
genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-2.5-flash")
img = Image.open("samples/sample_immunity_booster.png")

prompt = """
You are an expert pharmaceutical and nutraceutical chemist.
Analyze this formula image carefully.
Extract all active ingredients, their exact strength/dosage number, and unit.
Return ONLY a valid JSON list with this structure:
[
  {"name": "...", "dosage": 500, "unit": "mg"}
]
Do not include markdown ticks like ```json, just raw JSON.
"""

response = model.generate_content([prompt, img])
print("=== GEMINI OCR EXTRACTION ===")
print(response.text.strip())
