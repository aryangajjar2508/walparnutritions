import sys
sys.path.insert(0, '.')
import json
from app.scripts.load_excel_db import extract_aliases, clean_text
import pandas as pd

with open('app/data/walpar_master_ingredients.json', 'r', encoding='utf-8') as f:
    current_db = json.load(f)['ingredients']

df = pd.read_excel('rate avg.xlsx')

print(f"Current DB items: {len(current_db)}, Excel items: {len(df)}")
for idx, row in df.iterrows():
    raw_item = str(row['Item']).strip()
    clean_n = clean_text(raw_item)
    curr = current_db[idx] if idx < len(current_db) else None
    if curr:
        # Check if aliases in curr contain something totally unrelated
        curr_aliases = curr.get('aliases', [])
        for a in curr_aliases:
            if a in ['thiamine', 'pyridoxine', 'riboflavin', 'cyanocobalamin', 'cholecalciferol', 'vitamin b1', 'vitamin b2', 'vitamin b6', 'vitamin b12', 'vitamin d3']:
                if not any(k in clean_n.lower() for k in ['thimine', 'thiamine', 'pyridoxine', 'riboflavin', 'cobalamin', 'cholecalciferol', 'd3', 'b1', 'b2', 'b6', 'b12', 'vitamin']):
                    print(f"CORRUPTED: Row {idx} '{clean_n}' has alias '{a}'")
