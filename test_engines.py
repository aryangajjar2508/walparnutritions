import urllib.request
import json

for engine in ["rapidocr", "tesseract", "ensemble"]:
    url = f"http://127.0.0.1:8000/api/sample/sample_immunity_booster.png?engine={engine}"
    req = urllib.request.Request(url, method="POST")
    res = urllib.request.urlopen(req)
    data = json.loads(res.read().decode("utf-8"))
    
    print(f"\n================ ENGINE: {engine.upper()} ================")
    print("Success:", data.get("success"))
    print("Ingredients count:", len(data.get("ingredients", [])))
    for ing in data.get("ingredients", []):
        print(f"  * {ing['name']} -> {ing['dosage']} {ing['unit']} (DB Match: {ing['is_matched']})")
