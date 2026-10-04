import json
from rapidfuzz import fuzz, process

with open('app/data/walpar_master_ingredients.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

ingredients = data['ingredients']
alias_map = {}
for item in ingredients:
    alias_map[item['name'].lower()] = item
    for a in item.get('aliases', []):
        alias_map[a.lower()] = item

test_queries = [
    'Vitamin C (Ascorbic Acid)',
    'Zinc Sulphate Monohydrate',
    'Zinc (as Zinc Sulphate)',
    'Vitamin D3 (Cholecalciferol)',
    'Curcumin 95%',
    'Piperine (Black Pepper Extract)',
    'Ashwagandha Dry Extract',
    'KSM-66',
    'Melatonin',
    'Glucosamine Sulphate',
    'L-Carnitine L-Tartrate',
    'Opitac Glutathione',
    'Marine Collagen'
]

print(f"Total aliases indexed: {len(alias_map)}")
for q in test_queries:
    ql = q.lower()
    matched = None
    if ql in alias_map:
        matched = alias_map[ql]
    else:
        candidates = list(alias_map.keys())
        res = process.extractOne(ql, candidates, scorer=fuzz.token_set_ratio)
        if res and res[1] >= 75:
            matched = alias_map[res[0]]
            
    if matched:
        print(f"Query: '{q}' -> MATCHED: '{matched['name']}' (Source: '{matched['raw_name']}')")
    else:
        print(f"Query: '{q}' -> NO MATCH")
