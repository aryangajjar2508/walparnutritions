import pandas as pd
df = pd.read_excel('rate avg.xlsx')
print('Total rows in excel:', len(df))
keywords = ['thiamine', 'riboflavin', 'pyridoxine', 'cholecalciferol', 'cobalamin', 'cyanocobalamin', 'vitamin', 'ascorbic', 'glutathion', 'coenzyme', 'ubiquin', 'zinc', 'selenium', 'molybdenum', 'manganese', 'carnitine', 'arginine']
for i, r in df.iterrows():
    name = str(r['Item']).lower()
    for kw in keywords:
        if kw in name:
            print(f"Row {i}: {r['Item']}")
            break
