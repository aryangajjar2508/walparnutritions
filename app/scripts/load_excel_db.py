import os
import re
import json
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
EXCEL_PATH = BASE_DIR / "rate avg.xlsx"
OUTPUT_JSON_PATH = BASE_DIR / "app" / "data" / "walpar_master_ingredients.json"

def clean_text(text: str) -> str:
    # Remove quotes, weird spaces, non-breaking spaces
    t = text.replace('\xa0', ' ').replace('"', ' ').replace("'", ' ').replace('`', ' ')
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def extract_aliases(raw_name: str, clean_name: str) -> list:
    aliases = set()
    raw_lower = raw_name.lower().strip()
    clean_lower = clean_name.lower().strip()
    
    aliases.add(clean_lower)
    aliases.add(raw_lower)
    
    # Text inside parentheses
    parens = re.findall(r'\((.*?)\)', clean_name)
    for p in parens:
        p_clean = clean_text(p).lower()
        if len(p_clean) >= 2:
            aliases.add(p_clean)
            
    # Text without parentheses
    no_paren = re.sub(r'\(.*?\)', '', clean_name).strip()
    no_paren_clean = clean_text(no_paren).lower()
    if no_paren_clean and len(no_paren_clean) >= 2:
        aliases.add(no_paren_clean)

    # Word-boundary or normalized key matching for nutraceutical synonyms
    norm = re.sub(r'[^a-z0-9]', '', clean_lower)

    # Specific targeted synonym mappings
    if 'ascorbic' in clean_lower or 'vitaminc' in norm:
        aliases.update(['vitamin c', 'vit c', 'l-ascorbic acid', 'ascorbic acid', 'sodium ascorbate'])
    
    if 'cholecalciferol' in clean_lower or 'vitd3' in norm or 'vitamind3' in norm:
        aliases.update(['vitamin d3', 'vit d3', 'vitamin d', 'cholecalciferol', 'cholecalciferol (vit d3)'])

    if 'methylcobalamin' in clean_lower or 'methylcobalamine' in clean_lower or 'cyanocobalamin' in clean_lower:
        aliases.update(['vitamin b12', 'vit b12', 'cyanocobalamin', 'methylcobalamin', 'methylcobalamine'])

    if 'pyridoxine' in clean_lower or 'vitaminb6' in norm or 'vitb6' in norm:
        aliases.update(['vitamin b6', 'vit b6', 'pyridoxine', 'pyridoxine hcl', 'pyridoxine hydrochloride'])

    if 'riboflavin' in clean_lower or 'vitaminb2' in norm or 'vitb2' in norm:
        aliases.update(['vitamin b2', 'vit b2', 'riboflavin', 'riboflavin 5 phosphate', 'riboflavin sodium phosphate'])

    if 'thimine' in clean_lower or 'thiamine' in clean_lower or 'vitaminb1' in norm or 'vitb1' in norm:
        aliases.update(['vitamin b1', 'vit b1', 'thiamine', 'thiamine hcl', 'thiamine hydrochloride', 'thiamine mononitrate'])

    if 'niacinamide' in clean_lower or 'nicotinamide' in clean_lower or 'vitaminb3' in norm:
        aliases.update(['vitamin b3', 'vit b3', 'niacinamide', 'nicotinamide', 'niacin'])

    if 'pantothenic' in clean_lower or 'vitaminb5' in norm:
        aliases.update(['vitamin b5', 'vit b5', 'pantothenic acid', 'd-calcium pantothenate', 'calcium pantothenate'])

    if 'biotin' in clean_lower:
        aliases.update(['vitamin b7', 'vitamin h', 'biotin', 'd-biotin'])

    if 'folic' in clean_lower:
        aliases.update(['vitamin b9', 'folate', 'folic acid', 'l-methylfolate'])

    if 'vitamina' in norm or ('vitamin a' in clean_lower):
        aliases.update(['vitamin a', 'vit a', 'vitamin a palmitate', 'vitamin a acetate', 'retinyl palmitate'])

    if 'vitamine' in norm or ('vitamin e' in clean_lower):
        aliases.update(['vitamin e', 'vit e', 'tocopherol', 'tocopheryl acetate', 'd-alpha tocopherol'])

    if 'vitamink' in norm or 'k-27' in clean_lower or 'k2' in clean_lower:
        aliases.update(['vitamin k2', 'vit k2', 'vitamin k2-7', 'vitamin k', 'menaquinone', 'menaquinone-7', 'mk-7'])

    if 'glutathion' in clean_lower or 'glutathione' in clean_lower:
        aliases.update(['l-glutathione', 'glutathione', 'reduced glutathione', 'l-glutathione reduced', 'gsh', 'opitac glutathione'])

    if 'coenzyme' in norm or 'coenzymeq10' in norm or ('co' in clean_lower and 'q 10' in clean_lower) or ('co' in clean_lower and 'q10' in clean_lower):
        aliases.update(['coenzyme q10', 'co-enzyme q10', 'coq10', 'ubiquinone', 'ubiquinol', 'co enzyme q10', 'co enzyme q 10'])

    if 'carnitine' in clean_lower:
        if 'acetyl' in clean_lower:
            aliases.update(['n-acetyl-l-carnitine', 'acetyl-l-carnitine', 'alc'])
        else:
            aliases.update(['l-carnitine', 'l-carnitine l-tartrate', 'carnitine', 'lclt'])

    if 'arginine' in clean_lower:
        aliases.update(['l-arginine', 'l arginine', 'arginine', 'l-arginine base'])

    if 'lysine' in clean_lower:
        aliases.update(['l-lysine', 'l lysine', 'lysine', 'l-lysine hcl', 'l-lysine hydrochloride'])

    if 'zinc' in clean_lower:
        aliases.update(['zinc', 'zinc element'])
        if 'sulphate' in clean_lower or 'sulfate' in clean_lower:
            aliases.update(['zinc sulphate', 'zinc sulfate', 'zinc sulphate monohydrate'])
        elif 'gluconate' in clean_lower:
            aliases.update(['zinc gluconate'])
        elif 'glycinate' in clean_lower:
            aliases.update(['zinc bisglycinate', 'zinc bis glycinate'])
        elif 'picolinate' in clean_lower:
            aliases.update(['zinc picolinate'])
        elif 'oxide' in clean_lower:
            aliases.update(['zinc oxide'])

    if 'selenite' in clean_lower or 'selenate' in clean_lower or 'selenium' in clean_lower:
        aliases.update(['selenium', 'sodium selenite', 'sodium selenate'])

    if 'cranberry' in clean_lower:
        aliases.update(['cranberry', 'cranberry extract', 'cranberry dry extract'])

    if 'mannose' in clean_lower:
        aliases.update(['d-mannose', 'mannose'])

    if 'lactobacillus' in clean_lower:
        aliases.update(['lactobacillus', 'lactobacillus spp', 'lactobacillus probiotic'])
        if 'plantarum' in clean_lower:
            aliases.update(['lactobacillus plantarum', 'l. plantarum'])
        if 'reuteri' in clean_lower:
            aliases.update(['lactobacillus reuteri', 'l. reuteri'])

    if 'bifidobacterium' in clean_lower:
        aliases.update(['bifidobacterium', 'bifidobacterium spp', 'bifidobacterium probiotic'])
        if 'animals' in clean_lower or 'animalis' in clean_lower:
            aliases.update(['bifidobacterium animalis', 'bifidobacterium animals', 'b. animalis'])

    if 'probiotic' in clean_lower:
        aliases.update(['probiotics', 'probiotic blend', 'probiotic blends'])

    if 'curcumin' in clean_lower or 'turmeric' in clean_lower:
        aliases.update(['curcumin', 'turmeric', 'curcuma longa', 'turmeric extract'])

    if 'ashwagandha' in clean_lower or 'withania' in clean_lower:
        aliases.update(['ashwagandha', 'withania somnifera', 'indian ginseng'])

    if 'piperine' in clean_lower or 'black pepper' in clean_lower:
        aliases.update(['piperine', 'black pepper', 'black pepper extract', 'bioperine'])

    if 'glucosamine' in clean_lower:
        aliases.update(['glucosamine', 'glucosamine sulphate', 'glucosamine hcl'])

    if 'chondroitin' in clean_lower:
        aliases.update(['chondroitin', 'chondroitin sulphate'])

    if 'collagen' in clean_lower:
        aliases.update(['collagen', 'marine collagen', 'collagen peptide', 'hydrolyzed collagen'])

    # Format all aliases cleanly
    cleaned_aliases = set()
    for a in aliases:
        ca = clean_text(a).lower().strip()
        if ca and len(ca) >= 2:
            cleaned_aliases.add(ca)

    return sorted(list(cleaned_aliases))

def build_database():
    print(f"Reading excel from: {EXCEL_PATH}")
    df = pd.read_excel(EXCEL_PATH)
    
    ingredients = []
    seen_names = set()

    for idx, row in df.iterrows():
        raw_item = str(row['Item']).strip()
        if not raw_item or raw_item.lower() == 'nan':
            continue

        clean_n = clean_text(raw_item)
        if not clean_n or clean_n.lower() in seen_names:
            continue
        seen_names.add(clean_n.lower())

        # Determine reasonable standard unit and dosage for testing if known
        unit = "mg"
        std_dose = 100
        lower_name = clean_n.lower()
        if "mcg" in lower_name or "b12" in lower_name or "biotin" in lower_name or "folic" in lower_name or "k2" in lower_name or "chromium" in lower_name or "selenium" in lower_name:
            unit = "mcg"
            std_dose = 50
        elif "d3" in lower_name:
            unit = "IU"
            std_dose = 600
        elif "cfu" in lower_name or "lactobacillus" in lower_name or "bifidobacterium" in lower_name or "probiotic" in lower_name:
            unit = "Billion CFU"
            std_dose = 5
        elif "gm" in lower_name or ("powder" in lower_name and "collagen" in lower_name):
            unit = "g"
            std_dose = 5

        aliases = extract_aliases(raw_item, clean_n)

        # Store internal rate if needed, but rate will NOT be shown anywhere in UI
        rate_val = 0.0
        if 'Rate ' in df.columns and pd.notnull(row['Rate ']):
            try:
                rate_val = float(row['Rate '])
            except:
                rate_val = 0.0

        ingredients.append({
            "id": f"ing_{len(ingredients)+1}",
            "name": clean_n.title(),
            "raw_name": raw_item,
            "aliases": aliases,
            "default_unit": unit,
            "default_dose": std_dose,
            "_rate": rate_val
        })

    print(f"Total processed ingredients: {len(ingredients)}")
    
    OUTPUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump({"ingredients": ingredients}, f, indent=2, ensure_ascii=False)

    print(f"Successfully saved database to {OUTPUT_JSON_PATH}")

if __name__ == "__main__":
    build_database()
