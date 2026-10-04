import urllib.request
import json

url = "http://127.0.0.1:8000/api/sample/sample_immunity_booster.png?engine=gemini"
req = urllib.request.Request(url, method="POST")
res = urllib.request.urlopen(req)
data = json.loads(res.read().decode("utf-8"))

print("=== LIVE GEMINI VISION API TEST ===")
print("Success:", data.get("success"))
print("Engine Used:", data.get("engine_used"))
print("Ingredients Matched:", data.get("matched_count"), "of", data.get("total_count"))
for ing in data.get("ingredients", []):
    print(f"  * {ing['name']} | Dose: {ing['dosage']} {ing['unit']} | DB Match: {ing['db_raw_name']}")
