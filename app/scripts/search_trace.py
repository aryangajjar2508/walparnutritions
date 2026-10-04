import pandas as pd
df = pd.read_excel('rate avg.xlsx')
for idx, row in df.iterrows():
    name = str(row['Item']).lower()
    if 'mang' in name or 'moly' in name or 'seleni' in name or 'iodi' in name:
        print(f"Row {idx}: {row['Item']}")
