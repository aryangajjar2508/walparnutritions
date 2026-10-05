import re
import json
from typing import List, Dict, Any, Optional, Tuple
from rapidfuzz import fuzz, process
from app.config import INGREDIENTS_DB_PATH

class FormulaParser:
    _instances = []

    def __init__(self, db_path: str = None):
        self.db_path = db_path or INGREDIENTS_DB_PATH
        self.ingredients_master = []
        self.alias_to_ingredient = {}
        self.canonical_names = []
        self.load_database()
        self.load_subagent_rules()
        if self not in FormulaParser._instances:
            FormulaParser._instances.append(self)

    @classmethod
    def reload_all_subagent_rules(cls):
        """Reloads all subagent rules across all active parser instances"""
        for inst in list(cls._instances):
            try:
                inst.load_database()
                inst.load_subagent_rules()
            except Exception as e:
                print(f"[FormulaParser] Error reloading subagent rules: {e}")

    def load_subagent_rules(self):
        """Loads all active trained rules from SQLite DB and JSON memory"""
        try:
            from app.auth import db_get_all_training_rules
            db_rules = db_get_all_training_rules()
            for r in db_rules:
                if r.get("status") == "active":
                    source = str(r.get("source_term", "")).strip().lower()
                    target_name = str(r.get("target_term", "")).strip().lower()
                    target_item = self.alias_to_ingredient.get(target_name)
                    if not target_item:
                        for item in self.ingredients_master:
                            if item["name"].strip().lower() == target_name:
                                target_item = item
                                break
                    if target_item and source:
                        self.alias_to_ingredient[source] = target_item
                        self.alias_to_ingredient[source.replace(" ", "")] = target_item
                        self.alias_to_ingredient[source.replace("-", " ")] = target_item
                        self.alias_to_ingredient[re.sub(r'\b([ld])\s+', r'\1-', source)] = target_item
        except Exception:
            pass

    def load_database(self):
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.ingredients_master = data.get("ingredients", [])
                for item in self.ingredients_master:
                    canonical = item["name"].lower().strip()
                    self.alias_to_ingredient[canonical] = item
                    self.alias_to_ingredient[canonical.replace(" ", "")] = item
                    self.canonical_names.append(canonical)
                    for alias in item.get("aliases", []):
                        a_clean = alias.lower().strip()
                        if a_clean:
                            self.alias_to_ingredient[a_clean] = item
                            # Also index without spaces for OCR joined-words (e.g. "vitaminc")
                            self.alias_to_ingredient[a_clean.replace(" ", "")] = item
                            # Also index with/without hyphens (e.g. "l glutathione" vs "l-glutathione")
                            self.alias_to_ingredient[a_clean.replace("-", " ")] = item
                            self.alias_to_ingredient[re.sub(r'\b([ld])\s+', r'\1-', a_clean)] = item

                # Specific nutraceutical & elemental compound aliases
                calcium_target = self.alias_to_ingredient.get("calcium carbonate ( oystercell )") or self.alias_to_ingredient.get("calcium carbonate")
                if calcium_target:
                    for cal_alias in [
                        "calcium", "elemental calcium", "calcium carbonate (from coral grains)",
                        "calcium carbonate (coral grains)", "coral grains", "calcium from coral grains",
                        "calcium carbonate from coral grains", "equivalent to elemental calcium",
                        "calclum carbonate (lrom coral grains)", "calclum carbonate"
                    ]:
                        self.alias_to_ingredient[cal_alias] = calcium_target
                        self.alias_to_ingredient[cal_alias.replace(" ", "")] = calcium_target

                vit_d3_target = self.alias_to_ingredient.get("vitamin d3 veg source") or self.alias_to_ingredient.get("vitamin d3")
                if vit_d3_target:
                    for d3_alias in ["vitamin d3", "vitamind3", "vit d3", "vitd3", "cholecalciferol"]:
                        self.alias_to_ingredient[d3_alias] = vit_d3_target
                        self.alias_to_ingredient[d3_alias.replace(" ", "")] = vit_d3_target

                # Magnesium compound aliases
                mg_taurate = self.alias_to_ingredient.get("magnesium taurine")
                if mg_taurate:
                    for alias in ["magnesium acetyl taurate", "magnesium acetyltaurate", "magnesium ata", "acetyl taurate", "magnesium taurate"]:
                        self.alias_to_ingredient[alias] = mg_taurate
                        self.alias_to_ingredient[alias.replace(" ", "")] = mg_taurate

                mg_bisglycinate = self.alias_to_ingredient.get("magnesium bis glycinate")
                if mg_bisglycinate:
                    for alias in ["magnesium bisglycinate", "magnesium bis-glycinate", "magnesium bis glycinate"]:
                        self.alias_to_ingredient[alias] = mg_bisglycinate
                        self.alias_to_ingredient[alias.replace(" ", "")] = mg_bisglycinate

                mg_threonate = self.alias_to_ingredient.get("magnesium l threonate")
                if mg_threonate:
                    for alias in ["magnesium l threonate", "magnesium l-threonate", "magnesium lthreonate", "magnesium threonate"]:
                        self.alias_to_ingredient[alias] = mg_threonate
                        self.alias_to_ingredient[alias.replace(" ", "")] = mg_threonate

            print(f"FormulaParser: Loaded {len(self.ingredients_master)} ingredients and {len(self.alias_to_ingredient)} aliases from database.")
        except Exception as e:
            print(f"Error loading ingredients database: {e}")

    @staticmethod
    def normalize_unit(unit_str: Optional[str]) -> str:
        """
        Normalize extracted unit to standard supported units:
        'mg', 'mcg', 'IU', 'g', '%', 'Billion CFU', 'ml'
        """
        if not unit_str:
            return "mg"
        u = str(unit_str).strip().lower()
        if "cfu" in u:
            return "Billion CFU"
        elif u in ["mcg", "ug", "μg", "microgram", "micrograms"]:
            return "mcg"
        elif u in ["iu", "iul", "iu.", "i.u.", "i.u", "international unit", "international units"]:
            return "IU"
        elif u in ["g", "gm", "gram", "grams"]:
            return "g"
        elif u in ["%", "%dv", "% rda", "percent"]:
            return "%"
        elif u in ["ml", "m.l.", "milliliter", "millilitre"]:
            return "ml"
        else:
            return "mg"

    @staticmethod
    def _is_confusable(name1: str, name2: str) -> bool:
        """
        Guard against dangerous misclassification of distinct chemical/nutritional compounds:
        e.g. Glutathione != Glutamine, Theanine != Thiamine, etc.
        """
        n1 = name1.lower()
        n2 = name2.lower()

        # Glutathione vs Glutamine
        if ("glutath" in n1 and "glutamin" in n2) or ("glutamin" in n1 and "glutath" in n2):
            return True

        # Theanine vs Thiamine
        if ("theanin" in n1 and "thiamin" in n2) or ("thiamin" in n1 and "theanin" in n2):
            return True

        # Tyrosine vs Threonine
        if ("tyrosin" in n1 and "threonin" in n2) or ("threonin" in n1 and "tyrosin" in n2):
            return True

        # Riboflavin vs Rutin
        if ("riboflavin" in n1 and "rutin" in n2) or ("rutin" in n1 and "riboflavin" in n2):
            return True

        # Folic acid vs Folinic acid
        if ("folic" in n1 and "folinic" in n2) or ("folinic" in n1 and "folic" in n2):
            return True

        # Glucosamine vs Glutamine
        if ("glucosamin" in n1 and "glutamin" in n2) or ("glutamin" in n1 and "glucosamin" in n2):
            return True

        # Carnitine vs Citrulline or Cystine
        if ("carnitin" in n1 and ("citrullin" in n2 or "cystin" in n2)) or (("citrullin" in n1 or "cystin" in n1) and "carnitin" in n2):
            return True

        # Biotin vs Boron
        if ("biotin" in n1 and "boron" in n2) or ("boron" in n1 and "biotin" in n2):
            return True

        # Arginine vs Alanine
        if ("arginin" in n1 and "alanin" in n2) or ("alanin" in n1 and "arginin" in n2):
            return True

        return False

    def extract_dose_and_unit(self, text: str) -> Tuple[Optional[float], Optional[str], str]:
        """
        Extract numeric strength/dose and unit (mg, mcg, IU, g, %, CFU, ml)
        Examples:
          'L-Glutathione 100 mg' -> (100.0, 'mg', 'L-Glutathione')
          'Vitamin C 50 mg' -> (50.0, 'mg', 'Vitamin C')
          'Probiotics 5 Billion CFU' -> (5.0, 'Billion CFU', 'Probiotics')
          'Vitamin D3 600 IU' -> (600.0, 'IU', 'Vitamin D3')
          '62.5% 50mg VitaminC' -> (50.0, 'mg', 'VitaminC')
        """
        # Specific pattern for Billion CFU / Million CFU / CFU
        cfu_pattern = r'(\d+(?:\.\d+)?)\s*(billion\s*cfu|million\s*cfu|cfu)\b'
        cfu_match = re.search(cfu_pattern, text, re.IGNORECASE)
        if cfu_match:
            val = float(cfu_match.group(1))
            unit = "Billion CFU"
            cleaned_text = re.sub(cfu_pattern, '', text, flags=re.IGNORECASE).strip()
            return val, unit, cleaned_text

        # Pattern for standard dosage units: mg, mcg, ug, gm, g, iu (including iul OCR misread), %, ml
        pattern = r'(\d+(?:\.\d+)?)\s*(mg|mcg|ug|μg|gm|g|iu[l]?|i\.u\.?|%|ml)\b'
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        if matches:
            # Pick the most specific unit (prefer mg, mcg, iu, g over % if multiple)
            chosen_match = matches[0]
            for m in matches:
                u_str = m.group(2).lower()
                if u_str in ['mg', 'mcg', 'ug', 'μg', 'iu', 'iul', 'g', 'gm'] or 'i.u' in u_str:
                    chosen_match = m
                    break

            val_str, unit_str = chosen_match.groups()
            val = float(val_str)
            unit_norm = self.normalize_unit(unit_str)

            # Strip the matched dosage token
            cleaned_text = text[:chosen_match.start()] + ' ' + text[chosen_match.end():]
            # Strip RDA percentages (e.g. 41.66%, 100%, 50 %) and %RDA markers from cleaned_text
            cleaned_text = re.sub(r'(?:%\s*rda|\b\d+(?:\.\d+)?\s*%\s*)', '', cleaned_text, flags=re.IGNORECASE)
            # Strip packaging/manufacturing artifacts (e.g. "Batch No.", "Mfg. Date", "Exp. Date", etc.)
            cleaned_text = re.sub(
                r'\b(?:batch\s*(?:no\.?|number)?|mfg\.?\s*date|exp\.?\s*date|m\.?r\.?p\.?|lic\.?\s*no\.?|'
                r'unit\s*sale\s*price|per\s*\d+\s*(?:tab|cap|tablets?|capsules?)|'
                r'for\s*\d+\s*(?:tab|cap|tablets?|capsules?)|inclusive\s*of\s*all\s*taxes)\b.*',
                '', cleaned_text, flags=re.IGNORECASE
            )
            cleaned_text = re.sub(r'[\.\:\–\—\=\|\?\(\)\[\]\{\}\*\#]+', ' ', cleaned_text)
            cleaned_text = re.sub(r'^\s*[\.\:\–\—\=\|\s]+', '', cleaned_text)
            cleaned_text = re.sub(r'[\.\:\–\—\=\|\s]+$', '', cleaned_text)
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
            return val, unit_norm, cleaned_text

        # Number at end of line (e.g. "Vitamin C : 500")
        num_at_end = re.search(r'[:\-–—\s]\s*(\d+(?:\.\d+)?)\s*$', text)
        if num_at_end:
            val = float(num_at_end.group(1))
            cleaned_text = text[:num_at_end.start()].strip()
            return val, 'mg', cleaned_text

        return None, None, text

    def _match_single_term(self, cleaned: str) -> Tuple[Optional[Dict[str, Any]], float]:
        if not cleaned or len(cleaned) < 2:
            return None, 0.0

        # 1. Direct exact match
        if cleaned in self.alias_to_ingredient:
            return self.alias_to_ingredient[cleaned], 100.0

        # Direct exact match without spaces (e.g. "vitaminc", "grapeseedextract")
        no_space = cleaned.replace(" ", "")
        if no_space in self.alias_to_ingredient:
            return self.alias_to_ingredient[no_space], 100.0

        # Direct match with space instead of hyphen (e.g. "l glutathione")
        no_hyphen = cleaned.replace("-", " ")
        if no_hyphen in self.alias_to_ingredient:
            return self.alias_to_ingredient[no_hyphen], 100.0

        # Direct match with hyphen (e.g. "l-glutathione")
        with_hyphen = re.sub(r'\b([ld])\s+', r'\1-', cleaned)
        if with_hyphen in self.alias_to_ingredient:
            return self.alias_to_ingredient[with_hyphen], 100.0

        # Without leading l- or d- (e.g. "glutathione" matching "l-glutathione")
        no_prefix = re.sub(r'^[ld][\-\s]+', '', cleaned).strip()
        if no_prefix and no_prefix in self.alias_to_ingredient:
            return self.alias_to_ingredient[no_prefix], 98.0

        # 2. Whole word boundary matching (for multi-word or compound aliases)
        for alias, item in self.alias_to_ingredient.items():
            if len(alias) >= 4 and not self._is_confusable(cleaned, alias):
                if re.search(r'\b' + re.escape(alias) + r'\b', cleaned):
                    return item, 96.0

        # 3. Guarded Fuzzy matching using token_sort_ratio
        candidates = [c for c in self.alias_to_ingredient.keys() if len(c) >= 3 and not self._is_confusable(cleaned, c)]
        match = process.extractOne(cleaned, candidates, scorer=fuzz.token_sort_ratio)
        if match and match[1] >= 85:
            matched_alias = match[0]
            score = float(match[1])
            return self.alias_to_ingredient[matched_alias], score

        return None, 0.0

    def match_ingredient(self, query: str) -> Tuple[Optional[Dict[str, Any]], float]:
        """
        Match ingredient name against database using exact, alias, and guarded fuzzy matching.
        Supports parenthetical expressions: "Vitamin B1 (as Thiamine Hydrochloride)",
        "Zinc (as Zinc Sulphate Monohydrate)", "Co-Enzyme Q10 (Ubiquinol)".
        Returns (matched_item, confidence_pct)
        """
        raw_str = str(query).strip()
        if not raw_str or len(raw_str) < 2:
            return None, 0.0

        cleaned = re.sub(r'[^a-zA-Z0-9\s\-\(\)\%]', ' ', raw_str).strip().lower()
        cleaned = re.sub(r'\s+', ' ', cleaned)

        # Check if query contains parenthetical details
        parens = re.findall(r'\((.*?)\)', cleaned)
        candidates_to_try = []

        if parens:
            outside = re.sub(r'\(.*?\)', '', cleaned).strip()
            inside = parens[0].strip()
            inside_clean = re.sub(r'^(as|from)\s+', '', inside).strip()

            if outside and len(outside) >= 2:
                candidates_to_try.append(outside)
            if inside_clean and len(inside_clean) >= 2:
                candidates_to_try.append(inside_clean)
            if inside and len(inside) >= 2:
                candidates_to_try.append(inside)

        candidates_to_try.append(cleaned)

        for cand in candidates_to_try:
            item, score = self._match_single_term(cand)
            if item and score >= 85.0:
                return item, score

        return None, 0.0

    def format_clean_name(self, raw_name: str, matched_item: Optional[Dict[str, Any]] = None) -> str:
        """
        Formats a clean, professional, user-facing ingredient name that stays faithful
        to what is on the bottle label (e.g. 'L-Glutathione', 'Vitamin C', 'Alpha Lipoic Acid',
        'Grape Seed Extract', 'L-Arginine').
        """
        clean = raw_name.strip()
        # Clean leading numbers, bullets, stars, RDA percentages
        clean = re.sub(r'^[\d\.\-\*\•\–\—\s\:\#\%]+', '', clean).strip()

        # Specific known clean title mappings for exact fidelity
        title_map = {
            'l-glutathione': 'L-Glutathione',
            'glutathione': 'L-Glutathione',
            'l glutathione': 'L-Glutathione',
            'alpha lipoic acid': 'Alpha Lipoic Acid',
            'alphalipoicacid': 'Alpha Lipoic Acid',
            'vitamin c': 'Vitamin C',
            'vitaminc': 'Vitamin C',
            'ascorbic acid': 'Vitamin C (Ascorbic Acid)',
            'grape seed extract': 'Grape Seed Extract',
            'grapeseedextract': 'Grape Seed Extract',
            'grape seed dry extract': 'Grape Seed Extract',
            'l-arginine': 'L-Arginine',
            'l arginine': 'L-Arginine',
            'arginine': 'L-Arginine',
            'coq10': 'Coenzyme Q10',
            'co-q10': 'Coenzyme Q10',
            'vitamin d3': 'Vitamin D3',
            'vitamind3': 'Vitamin D3',
            'vitamin d': 'Vitamin D3',
            'cholecalciferol': 'Vitamin D3 (Cholecalciferol)',
            'calcium carbonate': 'Calcium Carbonate',
            'calcium carbonate (from coral grains)': 'Calcium Carbonate (from Coral Grains)',
            'calcium carbonate (coral grains)': 'Calcium Carbonate (from Coral Grains)',
            'calcium carbonate from coral grains': 'Calcium Carbonate (from Coral Grains)',
            'coral grains': 'Calcium Carbonate (from Coral Grains)',
            'calcium': 'Calcium',
            'elemental calcium': 'Calcium (Elemental)',
            'vitamin b12': 'Vitamin B12',
            'methylcobalamin': 'Vitamin B12 (Methylcobalamin)',
            'vitamin b6': 'Vitamin B6',
            'pyridoxine': 'Vitamin B6 (Pyridoxine)',
            'vitamin b1': 'Vitamin B1',
            'thiamine': 'Vitamin B1 (Thiamine)',
            'vitamin b2': 'Vitamin B2',
            'riboflavin': 'Vitamin B2 (Riboflavin)',
            'vitamin b3': 'Vitamin B3',
            'niacinamide': 'Vitamin B3 (Niacinamide)',
            'vitamin b7': 'Biotin',
            'biotin': 'Biotin',
            'vitamin b9': 'Folic Acid',
            'folic acid': 'Folic Acid',
            'zinc': 'Zinc',
            'zinc sulphate': 'Zinc Sulphate',
            'magnesium': 'Magnesium',
            'ashwagandha': 'Ashwagandha Extract',
            'curcumin': 'Curcumin 95%',
            'melatonin': 'Melatonin',
            'l-theanine': 'L-Theanine',
            'l-carnitine': 'L-Carnitine',
            'l-glutamine': 'L-Glutamine'
        }

        low = clean.lower()
        if low in title_map:
            return title_map[low]

        # Fix L- / D- prefixes
        clean = re.sub(r'^[lL][\-\s]+', 'L-', clean)
        clean = re.sub(r'^[dD][\-\s]+', 'D-', clean)

        def cap_word(w: str) -> str:
            if not w:
                return w
            prefix = ""
            suffix = ""
            if w.startswith('('):
                prefix = '('
                w = w[1:]
            if w.endswith(')'):
                suffix = ')'
                w = w[:-1]

            if w.startswith('L-') or w.startswith('D-'):
                res = w[:2] + w[2:].capitalize()
            elif w.lower() in ['c', 'd', 'd3', 'b1', 'b2', 'b3', 'b5', 'b6', 'b7', 'b9', 'b12', 'e', 'k', 'k2', 'iu', 'gsh', 'cfu', 'hcl', 'q10']:
                res = w.upper()
            elif w.lower() in ['as', 'from', 'of', 'and', 'spp.']:
                res = w.lower() if w.lower() != 'spp.' else 'Spp.'
            elif '-' in w:
                parts = w.split('-')
                res = '-'.join('Co' if p.lower() == 'co' else (p.upper() if p.lower() in ['q10', 'hcl'] else p.capitalize()) for p in parts)
            else:
                res = w.capitalize()

            return f"{prefix}{res}{suffix}"

        parts = clean.split()
        capitalized = [cap_word(p) for p in parts]
        return ' '.join(capitalized)

    def parse_ocr_lines(self, lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Takes raw OCR lines: [{'text': '...', 'box': [...], 'confidence': 0.98}, ...]
        Returns high-accuracy active ingredients with dosages (mg, mcg, IU, g, %, CFU, ml).
        Strictly skips filler text, excipients without dosages, regulatory notes, etc.
        """
        parsed_items = []
        skip_phrases = [
            "specification", "target product", "confidential", "contract manufacturing",
            "strength / unit", "active ingredient", "r&d note", "table", "composition",
            "batch no", "mfg date", "exp date", "walpar nutraceuticals", "supplement facts",
            "serving size", "direction for use", "storage", "keep out of reach",
            "nutritional information", "approximate values", "each film coated tablet contains",
            "each tablet contains", "each capsule contains", "each serving contains",
            "appropriate overages", "loss of potency", "approved colour", "other ingredients",
            "excipients", "no rda established", "icmr guidelines", "m.r.p", "unit sale price",
            "fssai", "lic no", "mfg by", "marketed by", "best before", "store in a cool"
        ]

        # Step 1: Pre-process lines to pair compound names with following "Equivalent to elemental..." lines,
        # and split multi-ingredient single lines
        normalized_lines = []
        # Standardize input lines to list of dicts
        standardized_lines = []
        for l in lines:
            if isinstance(l, str):
                standardized_lines.append({"text": l.strip(), "confidence": 0.95, "box": []})
            elif isinstance(l, dict):
                standardized_lines.append(l)
            else:
                standardized_lines.append({"text": str(l).strip(), "confidence": 0.95, "box": []})
        lines = standardized_lines

        i = 0
        while i < len(lines):
            line_obj = lines[i]
            text = line_obj.get("text", "").strip()
            if not text:
                i += 1
                continue

            # Check if this line is excipient only (e.g. "excipient q.s.", "excipients")
            if re.match(r'^(?:excipients?|excipient)\b', text, re.IGNORECASE) and not re.search(r'\b\d+\s*(?:mg|mcg|iu|g)\b', text, re.IGNORECASE):
                i += 1
                continue

            # Check multi-line: current line has no dosage, next line is "Equivalent to elemental ... <dose>"
            if i + 1 < len(lines):
                next_obj = lines[i + 1]
                next_text = next_obj.get("text", "").strip()
                val_curr, _, _ = self.extract_dose_and_unit(text)
                val_next, unit_next, _ = self.extract_dose_and_unit(next_text)

                if val_curr is None and val_next is not None and re.search(r'\b(equivalent\s+to|eqv?\.?\s+to|elemental)\b', next_text, re.IGNORECASE):
                    # Combine compound line with dosage
                    combined_text = f"{text} {val_next} {unit_next}"
                    normalized_lines.append({
                        "text": combined_text,
                        "confidence": min(line_obj.get("confidence", 0.95), next_obj.get("confidence", 0.95)),
                        "box": line_obj.get("box", [])
                    })
                    i += 2
                    continue

            # Check if single line contains multiple dosage tokens (e.g. "... 250 mg ... Vitamin D3 400 IU")
            dose_matches = list(re.finditer(r'(\d+(?:\.\d+)?)\s*(mg|mcg|ug|μg|gm|g|iu[l]?|i\.u\.?)\b', text, re.IGNORECASE))
            if len(dose_matches) > 1:
                prev_idx = 0
                for dm in dose_matches:
                    seg_end = dm.end()
                    rda_m = re.match(r'[\.\s]*\d+(?:\.\d+)?\s*%', text[seg_end:], re.IGNORECASE)
                    if rda_m:
                        seg_end += rda_m.end()
                    seg_text = text[prev_idx:seg_end].strip()
                    if seg_text:
                        normalized_lines.append({
                            "text": seg_text,
                            "confidence": line_obj.get("confidence", 0.95),
                            "box": line_obj.get("box", [])
                        })
                    prev_idx = seg_end
                i += 1
                continue

            normalized_lines.append(line_obj)
            i += 1

        for idx, line_obj in enumerate(normalized_lines):
            raw_text = line_obj.get("text", "").strip()
            if not raw_text or len(raw_text) < 2:
                continue

            val, unit, cleaned_name = self.extract_dose_and_unit(raw_text)

            # ACTIVE INGREDIENT FILTER:
            # Active ingredients MUST have a valid numeric dosage and unit (mg, mcg, IU, g, %, CFU, ml)
            # If no dosage was found, or if it's filler/regulatory text, skip it!
            if val is None or unit is None:
                continue

            clean_lower = cleaned_name.lower()
            if any(phrase == clean_lower or clean_lower.startswith(phrase) for phrase in skip_phrases):
                continue

            # Clean leading serial numbers, bullets, stars, %RDA
            cleaned_name = re.sub(r'^[\d\.\-\*\•\–\—\s\:\#\%]+', '', cleaned_name)
            cleaned_name = re.sub(r'[\:\–\—\=\|]+', ' ', cleaned_name).strip()
            cleaned_name = re.sub(r'\s+', ' ', cleaned_name)

            if not cleaned_name or len(cleaned_name) < 2:
                continue

            matched_item, match_score = self.match_ingredient(cleaned_name)

            final_unit = self.normalize_unit(unit)
            resolved_name = self.format_clean_name(cleaned_name, matched_item)

            if matched_item:
                db_raw = matched_item.get("raw_name", "")
                db_id = matched_item["id"]
                is_matched = True
            else:
                db_raw = ""
                db_id = f"custom_{idx+1}"
                is_matched = False
                match_score = 0.0

            parsed_items.append({
                "id": db_id,
                "name": resolved_name,
                "db_raw_name": db_raw,
                "dosage": val,
                "unit": final_unit,
                "is_matched": is_matched,
                "match_score": round(match_score, 1),
                "raw_text": raw_text,
                "confidence": round(line_obj.get("confidence", 0.95), 3),
                "box": line_obj.get("box", [])
            })

        # Deduplicate
        unique_items = []
        seen = set()
        for item in parsed_items:
            key = item["name"].lower()
            if key not in seen:
                seen.add(key)
                unique_items.append(item)

        return unique_items

    def parse_gemini_items(self, gemini_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Takes structured items directly from Gemini Vision:
        [ {"name": "L-Glutathione", "dosage": 100, "unit": "mg"}, ... ]
        and matches each against the 518 Walpar database ingredients while strictly
        preserving the exact chemical name as written on the bottle label.
        """
        matched_items = []
        for idx, item in enumerate(gemini_items):
            raw_name = str(item.get("name", "")).strip()
            dose = item.get("dosage", 100)
            raw_unit = item.get("unit", "mg")

            try:
                dose_val = float(dose)
            except (ValueError, TypeError):
                dose_val = 100.0

            # Normalize unit strictly to one of: mg, mcg, IU, g, %, Billion CFU, ml
            final_unit = self.normalize_unit(raw_unit)

            matched_item, score = self.match_ingredient(raw_name)

            # Keep clean user-facing name faithful to label
            resolved_name = self.format_clean_name(raw_name, matched_item)

            if matched_item:
                db_raw = matched_item.get("raw_name", "")
                db_id = matched_item["id"]
                is_matched = True
            else:
                db_raw = ""
                db_id = f"custom_{idx+1}"
                is_matched = False
                score = 0.0

            matched_items.append({
                "id": db_id,
                "name": resolved_name,
                "db_raw_name": db_raw,
                "dosage": dose_val,
                "unit": final_unit,
                "is_matched": is_matched,
                "match_score": round(score, 1),
                "raw_text": f"{resolved_name} {dose_val} {final_unit}",
                "confidence": 0.99,
                "box": []
            })
        return matched_items
