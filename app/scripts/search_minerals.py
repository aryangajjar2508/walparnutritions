import pandas as pd

df = pd.read_excel('rate avg.xlsx')
print(f"Total rows: {len(df)}")
terms = [
    'coenzyme', 'co-enzyme', 'coq10', 'q10', 'ubiquin', 'selenium', 'selenate', 'manganese',
    'molybdenum', 'molybdate', 'iodine', 'potassium iodide', 'copper', 'cupric', 'chromium',
    'picolinate', 'probiotic', 'lactobacillus', 'bifidobacterium', 'cranberry', 'mannose',
    'lysine', 'glutathione', 'glutathion', 'arginine', 'carnitine', 'inositol', 'choline'
]

for idx, row in df.iterrows():
    raw_name = str(row['Item']).lower()
    for t in terms:
        if t in raw_name:
            print(f"Row {idx:3d} (ID ing_{idx+1}): '{row['Item']}' (Rate: {row.get('Rate ', 0)})")
            break
