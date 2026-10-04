import urllib.request
import json

req = urllib.request.Request('http://127.0.0.1:8000/api/sample/sample_immunity_booster.png', method='POST')
res = urllib.request.urlopen(req)
data = json.loads(res.read().decode('utf-8'))

print("API Success:", data.get('success'))
print("Extracted Ingredients:")
for ing in data.get('ingredients', []):
    print(f"  * {ing['name']} | Dose: {ing['dosage']} {ing['unit']} | Matched: {ing['is_matched']} | DB: {ing['db_raw_name']}")

raw_str = json.dumps(data)
print("Contains 'price':", 'price' in raw_str.lower())
print("Contains 'rate':", '"rate"' in raw_str.lower())
print("Contains 'cost':", 'cost' in raw_str.lower())
