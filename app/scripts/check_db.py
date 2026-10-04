import json

with open('app/data/walpar_master_ingredients.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total ingredients: {len(data['ingredients'])}")
for ing in data['ingredients']:
    aliases = ing.get('aliases', [])
    for a in aliases:
        if any(v in a for v in ['vitamin', 'thiamine', 'pyridoxine', 'riboflavin', 'cobalamin', 'cyanocobalamin', 'cholecalciferol', 'glutathione', 'glutamine', 'ascorbic']):
            # Print if the ingredient name doesn't seem to match the alias
            name_lower = ing['name'].lower()
            if not any(v in name_lower for v in ['vitamin', 'thiamine', 'pyridoxine', 'riboflavin', 'cobalamin', 'cholecalciferol', 'glutathione', 'glutamine', 'ascorbic', 'vit']):
                print(f"SUSPICIOUS: ID {ing['id']} - Name: '{ing['name']}' has alias: '{a}'")
