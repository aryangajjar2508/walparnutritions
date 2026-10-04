import json

with open('app/data/walpar_master_ingredients.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for ing in data['ingredients']:
    if ing['id'] in ['ing_464', 'ing_465', 'ing_357', 'ing_370', 'ing_448', 'ing_362', 'ing_380', 'ing_103', 'ing_267', 'ing_78', 'ing_79']:
        print(f"[{ing['id']}] Name: '{ing['name']}' | Raw: '{ing['raw_name']}' | Aliases: {ing['aliases']}")
