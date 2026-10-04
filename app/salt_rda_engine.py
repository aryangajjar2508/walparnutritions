import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

DB_FILE = Path(__file__).parent / "data" / "salt_rda_database.json"

class SaltRDAEngine:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.minerals = {}
        self.vitamins = {}
        self.miscellaneous = {}
        self._load_data()
        self._enrich_pdf_data()
        self._build_lookup_index()

    def _load_data(self):
        if DB_FILE.exists():
            try:
                with open(DB_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.minerals = data.get("mineralData", {})
                    self.vitamins = data.get("vitaminData", {})
            except Exception as e:
                print(f"[SaltRDAEngine] Error loading JSON DB: {e}")

    def _enrich_pdf_data(self):
        """
        Ensure 100% of salts and percentages from 'Element Salt Calculation %.pdf'
        and 'index (1).html' are present and complete.
        """
        # Lysine
        self.miscellaneous["lysine"] = {
            "name": "Lysine",
            "rdaUnit": "mg",
            "rdaGroups": [
                {"name": "Adults (19+y)", "rda": 2100}
            ],
            "saltForms": [
                {"id": "lysine-hcl", "name": "L-Lysine HCL", "percentage": 0.80},
                {"id": "lysine-monohydrate", "name": "L-Lysine Monohydrate", "percentage": 0.8903}
            ]
        }

        # Histidine
        self.miscellaneous["histidine"] = {
            "name": "Histidine",
            "rdaUnit": "mg",
            "rdaGroups": [
                {"name": "Adults (19+y)", "rda": 700}
            ],
            "saltForms": [
                {"id": "histidine-monohydrochloride", "name": "L-Histidine Monohydrochloride", "percentage": 0.74},
                {"id": "histidine-hydrochloride", "name": "L-Histidine Hydrochloride", "percentage": 0.8097}
            ]
        }

        # Choline
        self.miscellaneous["choline"] = {
            "name": "Choline",
            "rdaUnit": "mg",
            "rdaGroups": [
                {"name": "Men (19+y)", "rda": 550},
                {"name": "Women (19+y)", "rda": 425},
                {"name": "Pregnancy", "rda": 450},
                {"name": "Lactation", "rda": 550}
            ],
            "saltForms": [
                {"id": "choline-chloride", "name": "Choline Chloride", "percentage": 0.7460, "secondary": {"name": "Chloride", "percentage": 0.2539}},
                {"id": "tricholine-citrate", "name": "Tricholine Citrate", "percentage": 0.2076},
                {"id": "choline-bitartrate", "name": "Choline Bitartrate", "percentage": 0.4113}
            ]
        }

        # Amino Acids & Co-factors from PDF
        self.miscellaneous["cysteine"] = {
            "name": "Cysteine",
            "rdaUnit": "mg",
            "rdaGroups": [{"name": "Adults (19+y)", "rda": 500}],
            "saltForms": [
                {"id": "cysteine-hcl", "name": "L-Cysteine Hydrochloride", "percentage": 0.7686},
                {"id": "nac", "name": "N-Acetyl Cysteine", "percentage": 0.7424}
            ]
        }

        self.miscellaneous["creatine"] = {
            "name": "Creatine",
            "rdaUnit": "mg",
            "rdaGroups": [{"name": "Adults (19+y)", "rda": 3000}],
            "saltForms": [
                {"id": "creatine-monohydrate", "name": "Creatine Monohydrate", "percentage": 0.8791}
            ]
        }

        # Extra selenium salts from PDF
        if "selenium" in self.minerals:
            existing_ids = [s.get("id") for s in self.minerals["selenium"].get("saltForms", [])]
            if "selenomethionine" not in existing_ids:
                self.minerals["selenium"]["saltForms"].append({
                    "id": "selenomethionine", "name": "L-Selenomethionine", "percentage": 0.4026
                })
            if "selenium-dioxide" not in existing_ids:
                self.minerals["selenium"]["saltForms"].append({
                    "id": "selenium-dioxide", "name": "Selenium Dioxide Monohydrate", "percentage": 0.7116
                })

        # Extra folate salts from PDF
        if "b9" in self.vitamins:
            v_forms = self.vitamins["b9"].get("forms", [])
            existing_f_ids = [f.get("id") for f in v_forms]
            if "quatrefolic" not in existing_f_ids:
                v_forms.append({
                    "id": "quatrefolic", "name": "Quatrefolic (5-Methyltetrahydrofolate)", "percentage": 0.96
                })
            if "l-5-mthf-ca" not in existing_f_ids:
                v_forms.append({
                    "id": "l-5-mthf-ca", "name": "L-5-Methyltetrahydrofolate Calcium", "percentage": 0.8872,
                    "secondary": {"name": "Calcium", "percentage": 0.0803}
                })

    def _build_lookup_index(self):
        """
        Build an index mapping normalized names and aliases to salt form details
        """
        self.lookup = []

        def clean(s):
            return re.sub(r'[^a-z0-9]', '', s.lower())

        # 1. Minerals
        for m_key, m_info in self.minerals.items():
            parent_name = m_info.get("name", m_key.title())
            rda_unit = "mg"
            rda_groups = m_info.get("rdaGroups", [])
            for sf in m_info.get("saltForms", []):
                salt_name = sf.get("name", "")
                self.lookup.append({
                    "type": "mineral",
                    "parent_key": m_key,
                    "parent_name": parent_name,
                    "salt_name": salt_name,
                    "clean_name": clean(salt_name),
                    "percentage": sf.get("percentage", 1.0),
                    "secondary": sf.get("secondary"),
                    "rda_unit": rda_unit,
                    "rda_groups": rda_groups
                })

        # 2. Vitamins
        for v_key, v_info in self.vitamins.items():
            parent_name = v_info.get("name", v_key.title())
            rda_unit = v_info.get("rdaUnit", "mg")
            rda_groups = v_info.get("rdaGroups", [])
            for vf in v_info.get("forms", []):
                form_name = vf.get("name", "")
                aliases = [clean(form_name)]
                if v_key == "d":
                    aliases.extend(["vitamind3", "vitd3", "vitamind", "vitd", "d3", "cholecalciferol"])
                elif v_key == "a":
                    aliases.extend(["vitamina", "vita", "retinol", "retinylacetate", "retinylpalmitate"])
                elif v_key == "e":
                    aliases.extend(["vitamine", "vite", "alphatocopherol", "tocopherol", "tocopheryl"])
                elif v_key == "b6":
                    aliases.extend(["vitaminb6", "vitb6", "pyridoxine", "pyridoxinehcl"])
                elif v_key == "b12":
                    aliases.extend(["vitaminb12", "vitb12", "cyanocobalamin", "methylcobalamin"])
                elif v_key == "c":
                    aliases.extend(["vitaminc", "vitc", "ascorbicacid"])
                self.lookup.append({
                    "type": "vitamin",
                    "parent_key": v_key,
                    "parent_name": parent_name,
                    "salt_name": form_name,
                    "clean_name": clean(form_name),
                    "aliases": aliases,
                    "percentage": vf.get("percentage", 1.0),
                    "conversion": vf.get("conversion"),
                    "secondary": vf.get("secondary"),
                    "rda_unit": rda_unit,
                    "rda_groups": rda_groups
                })

        # 3. Miscellaneous
        for misc_key, misc_info in self.miscellaneous.items():
            parent_name = misc_info.get("name", misc_key.title())
            rda_unit = misc_info.get("rdaUnit", "mg")
            rda_groups = misc_info.get("rdaGroups", [])
            for sf in misc_info.get("saltForms", []):
                salt_name = sf.get("name", "")
                self.lookup.append({
                    "type": "misc",
                    "parent_key": misc_key,
                    "parent_name": parent_name,
                    "salt_name": salt_name,
                    "clean_name": clean(salt_name),
                    "percentage": sf.get("percentage", 1.0),
                    "secondary": sf.get("secondary"),
                    "rda_unit": rda_unit,
                    "rda_groups": rda_groups
                })

    def match_element(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Identifies whether a text refers to a mineral/vitamin/nutrient element
        and returns its metadata along with all associated salt forms.
        """
        if not text:
            return None
        t_low = text.lower().strip()
        cleaned_elem = re.sub(r'\b(elemental|pure|active|equivalent\s+to|eqv?\.?\s+to|\(elemental\)|\(as\b|as\b|\bfrom\b)\b', ' ', t_low)
        cleaned_elem = re.sub(r'[^a-z0-9]', '', cleaned_elem)

        mineral_map = {
            "calcium": ["calcium", "ca", "elementalcalcium"],
            "zinc": ["zinc", "zn", "elementalzinc"],
            "iron": ["iron", "ferrous", "ferric", "fe", "elementaliron"],
            "magnesium": ["magnesium", "mg", "elementalmagnesium"],
            "copper": ["copper", "cu", "elementalcopper"],
            "selenium": ["selenium", "se", "elementalselenium"],
            "manganese": ["manganese", "mn", "elementalmanganese"],
            "chromium": ["chromium", "cr", "elementalchromium"],
            "molybdenum": ["molybdenum", "mo", "elementalmolybdenum"],
            "potassium": ["potassium", "k", "elementalpotassium"],
            "sodium": ["sodium", "na", "elementalsodium"],
            "iodine": ["iodine", "iodide", "elementaliodine"]
        }
        for m_key, aliases in mineral_map.items():
            if m_key in self.minerals:
                if cleaned_elem in aliases or any(al == cleaned_elem or al in t_low.split() or f"elemental {al}" in t_low for al in aliases):
                    m_info = self.minerals[m_key]
                    return {
                        "element_key": m_key,
                        "element_name": m_info.get("name", m_key.title()),
                        "type": "mineral",
                        "rda_unit": "mg",
                        "rda_groups": m_info.get("rdaGroups", []),
                        "salt_forms": m_info.get("saltForms", [])
                    }

        vitamin_map = {
            "c": ["vitaminc", "vitc", "ascorbicacid", "ascorbate"],
            "d": ["vitamind", "vitd", "vitamind3", "vitd3", "cholecalciferol", "ergocalciferol", "d3"],
            "b12": ["vitaminb12", "vitb12", "cyanocobalamin", "methylcobalamin", "cobalamin", "b12"],
            "b6": ["vitaminb6", "vitb6", "pyridoxine", "pyridoxalphosphate", "b6"],
            "b9": ["vitaminb9", "vitb9", "folate", "folicacid", "methylfolate", "quatrefolic", "b9"],
            "a": ["vitamina", "vita", "retinol", "retinyl", "betacarotene"],
            "e": ["vitamine", "vite", "tocopherol", "alphatocopherol"],
            "b1": ["vitaminb1", "vitb1", "thiamine", "thiamin", "b1"],
            "b2": ["vitaminb2", "vitb2", "riboflavin", "b2"],
            "b3": ["vitaminb3", "vitb3", "niacin", "niacinamide", "nicotinamide", "nicotinicacid", "b3"],
            "b5": ["vitaminb5", "vitb5", "pantothenicacid", "pantothenate", "panthenol", "b5"],
            "b7": ["vitaminb7", "vitb7", "biotin", "b7"],
            "k": ["vitamink", "vitk", "vitamink2", "vitk2", "menaquinone", "phytomenadione", "k2"]
        }
        for v_key, aliases in vitamin_map.items():
            if v_key in self.vitamins:
                if cleaned_elem in aliases or any(al == cleaned_elem or al in t_low.split() or f"vitamin {al}" in t_low for al in aliases):
                    v_info = self.vitamins[v_key]
                    return {
                        "element_key": v_key,
                        "element_name": v_info.get("name", f"Vitamin {v_key.upper()}"),
                        "type": "vitamin",
                        "rda_unit": v_info.get("rdaUnit", "mg"),
                        "rda_groups": v_info.get("rdaGroups", []),
                        "salt_forms": v_info.get("forms", [])
                    }

        misc_map = {
            "choline": ["choline", "tricholine", "cholinechloride", "cholinebitartrate"],
            "lysine": ["lysine", "llysine"],
            "histidine": ["histidine", "lhistidine"],
            "cysteine": ["cysteine", "lcysteine", "nac", "nacetylcysteine"],
            "creatine": ["creatine", "creatinemonohydrate"]
        }
        for misc_key, aliases in misc_map.items():
            if misc_key in self.miscellaneous:
                if cleaned_elem in aliases or any(al == cleaned_elem or al in t_low.split() for al in aliases):
                    misc_info = self.miscellaneous[misc_key]
                    return {
                        "element_key": misc_key,
                        "element_name": misc_info.get("name", misc_key.title()),
                        "type": "misc",
                        "rda_unit": misc_info.get("rdaUnit", "mg"),
                        "rda_groups": misc_info.get("rdaGroups", []),
                        "salt_forms": misc_info.get("saltForms", [])
                    }

        return None

    def get_element_options(
        self,
        text_or_key: str,
        dose: float = 100.0,
        is_target_elemental: bool = True,
        unit: str = "mg"
    ) -> Dict[str, Any]:
        """
        Returns all salt form options for an element with calculated required doses,
        elemental yields, secondary nutrients, and demographic RDA coverage.
        """
        elem = self.match_element(text_or_key)
        if not elem:
            k = str(text_or_key).lower().strip()
            if k in self.minerals:
                m_info = self.minerals[k]
                elem = {
                    "element_key": k,
                    "element_name": m_info.get("name", k.title()),
                    "type": "mineral",
                    "rda_unit": "mg",
                    "rda_groups": m_info.get("rdaGroups", []),
                    "salt_forms": m_info.get("saltForms", [])
                }
            elif k in self.vitamins:
                v_info = self.vitamins[k]
                elem = {
                    "element_key": k,
                    "element_name": v_info.get("name", f"Vitamin {k.upper()}"),
                    "type": "vitamin",
                    "rda_unit": v_info.get("rdaUnit", "mg"),
                    "rda_groups": v_info.get("rdaGroups", []),
                    "salt_forms": v_info.get("forms", [])
                }
            elif k in self.miscellaneous:
                misc_info = self.miscellaneous[k]
                elem = {
                    "element_key": k,
                    "element_name": misc_info.get("name", k.title()),
                    "type": "misc",
                    "rda_unit": misc_info.get("rdaUnit", "mg"),
                    "rda_groups": misc_info.get("rdaGroups", []),
                    "salt_forms": misc_info.get("saltForms", [])
                }

        if not elem:
            return {"success": False, "error": f"Element '{text_or_key}' not found in database"}

        dose_in_mg = float(dose)
        u_clean = str(unit or "mg").lower().strip()
        if u_clean == "mcg":
            dose_in_mg = dose / 1000.0
        elif u_clean == "g":
            dose_in_mg = dose * 1000.0
        elif u_clean == "iu":
            conv = elem.get("conversion") or {}
            factor = conv.get("IUToMg", 0.000025)
            dose_in_mg = dose * factor

        rda_groups = elem.get("rda_groups", [])
        rda_unit = elem.get("rda_unit", "mg")
        options = []

        for sf in elem.get("salt_forms", []):
            pct = float(sf.get("percentage") if sf.get("percentage") is not None else 1.0)
            salt_name = sf.get("name", "")
            sec = sf.get("secondary")

            if is_target_elemental:
                req_salt_mg = (dose_in_mg / pct) if pct > 0 else dose_in_mg
                elemental_yield_mg = dose_in_mg
                sec_mg = (req_salt_mg * sec.get("percentage", 0.0)) if sec else 0.0
            else:
                req_salt_mg = dose_in_mg
                elemental_yield_mg = dose_in_mg * pct
                sec_mg = (dose_in_mg * sec.get("percentage", 0.0)) if sec else 0.0

            adult_rda_pct = 0.0
            rda_results = []
            for grp in rda_groups:
                r_val = grp.get("rda", 0.0)
                if r_val > 0:
                    r_unit = str(rda_unit or "mg").lower()
                    r_in_mg = r_val / 1000.0 if r_unit == "mcg" else (r_val * 1000.0 if r_unit == "g" else r_val)
                    p = (elemental_yield_mg / r_in_mg) * 100.0
                    rda_results.append({
                        "group": grp.get("name"),
                        "rda_value": r_val,
                        "rda_unit": rda_unit,
                        "percentage": round(p, 1)
                    })
                    g_low = grp.get("name", "").lower()
                    if "19-70" in g_low or "19-50" in g_low or "men (19" in g_low:
                        adult_rda_pct = round(p, 1)
                    elif not adult_rda_pct and ("adult" in g_low or "men" in g_low):
                        adult_rda_pct = round(p, 1)

            if not adult_rda_pct and rda_results:
                adult_rda_pct = rda_results[0]["percentage"]

            options.append({
                "salt_name": salt_name,
                "salt_id": sf.get("id"),
                "percentage": pct,
                "elemental_percent": round(pct * 100, 2),
                "required_salt_mg": round(req_salt_mg, 2),
                "elemental_yield_mg": round(elemental_yield_mg, 4),
                "secondary": {
                    "name": sec.get("name"),
                    "percentage": round(sec.get("percentage", 0) * 100, 2),
                    "amount_mg": round(sec_mg, 2)
                } if sec else None,
                "adult_rda_percent": adult_rda_pct,
                "rda_breakdown": rda_results
            })

        options.sort(key=lambda x: x["required_salt_mg"])

        return {
            "success": True,
            "element_name": elem["element_name"],
            "element_key": elem["element_key"],
            "type": elem["type"],
            "input_dose": dose,
            "input_unit": unit,
            "is_target_elemental": is_target_elemental,
            "options_count": len(options),
            "options": options
        }

    def match_salt(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Fuzzy / prefix / exact matching against all known salts from PDF & index (1).html
        """
        if not text:
            return None
        clean_text = re.sub(r'[^a-z0-9]', '', text.lower())
        if not clean_text:
            return None

        norm_text = clean_text.replace("bisglycinate", "biglycinate").replace("lthreonate", "ltheonate").replace("threonate", "theonate")

        # 1. Exact clean match or alias match
        for item in self.lookup:
            cn = item["clean_name"]
            aliases = item.get("aliases", [])
            if cn in [clean_text, norm_text] or clean_text in aliases or norm_text in aliases:
                return item

        # 1b. Check without "elemental" prefix
        stripped_text = re.sub(r'^(elemental|pure|active)', '', clean_text)
        if stripped_text != clean_text and stripped_text:
            for item in self.lookup:
                cn = item["clean_name"]
                aliases = item.get("aliases", [])
                if cn == stripped_text or stripped_text in aliases:
                    return item

        # 2. Contains match:
        best_match = None
        best_len = 0
        for item in self.lookup:
            cn = item["clean_name"]
            if len(cn) > 4:
                if cn in clean_text or cn in norm_text:
                    if len(cn) > best_len:
                        best_len = len(cn)
                        best_match = item
                elif clean_text.startswith(cn) or (cn.startswith(clean_text) and len(clean_text) >= 5):
                    if len(clean_text) > best_len:
                        best_len = len(clean_text)
                        best_match = item
            for al in item.get("aliases", []):
                if len(al) > 4:
                    if al in clean_text or al in norm_text:
                        if len(al) > best_len:
                            best_len = len(al)
                            best_match = item

        if best_match:
            return best_match

        # 3. Check if an Element was specified (e.g. "Elemental Zinc", "Zinc", "Elemental Calcium")
        elem = self.match_element(text)
        if elem and elem.get("salt_forms"):
            primary_sf = elem["salt_forms"][0]
            for item in self.lookup:
                if item["salt_name"] == primary_sf.get("name") and item.get("parent_key") == elem.get("element_key"):
                    res = dict(item)
                    res["is_element_specification"] = True
                    return res

        return None

    def calculate_elemental(
        self,
        salt_entry: Dict[str, Any],
        dose: float,
        unit: str = "mg"
    ) -> Dict[str, Any]:
        """
        Computes elemental yield and % RDA
        """
        if not salt_entry or not isinstance(salt_entry, dict):
            return {}

        # Convert dose to mg
        dose_in_mg = float(dose)
        u_clean = unit.lower().strip()
        if u_clean == "mcg":
            dose_in_mg = dose / 1000.0
        elif u_clean == "g":
            dose_in_mg = dose * 1000.0
        elif u_clean == "iu":
            conv = salt_entry.get("conversion", {})
            factor = conv.get("IUToMg", 0.000025)
            dose_in_mg = dose * factor

        percentage = salt_entry.get("percentage", 1.0)
        elemental_mg = dose_in_mg * percentage

        # Secondary element (e.g. Calcium Phosphate -> Phosphorous, Potassium Iodide -> Iodine)
        secondary_res = None
        sec = salt_entry.get("secondary")
        if sec:
            sec_pct = sec.get("percentage", 0.0)
            sec_mg = dose_in_mg * sec_pct
            secondary_res = {
                "name": sec.get("name"),
                "percentage": round(sec_pct * 100, 2),
                "amount_mg": round(sec_mg, 4)
            }

        # Calculate RDA Breakdown
        rda_groups = salt_entry.get("rda_groups", [])
        rda_unit = salt_entry.get("rda_unit", "mg")
        rda_results = []
        standard_adult_rda_pct = 0.0

        for grp in rda_groups:
            rda_val = grp.get("rda", 0.0)
            if rda_val <= 0:
                continue

            # Convert rda_val to mg for comparison
            rda_unit_clean = str(rda_unit or "mg").lower().strip()
            if rda_unit_clean == "mcg":
                rda_in_mg = rda_val / 1000.0
            elif rda_unit_clean == "iu":
                factor = (salt_entry.get("conversion") or {}).get("IUToMg", 0.000025)
                rda_in_mg = rda_val * factor
            elif rda_unit_clean == "g":
                rda_in_mg = rda_val * 1000.0
            else:
                rda_in_mg = rda_val

            pct = (elemental_mg / rda_in_mg) * 100.0 if rda_in_mg > 0 else 0.0
            rda_results.append({
                "group": grp.get("name"),
                "rda_value": rda_val,
                "rda_unit": rda_unit,
                "percentage": round(pct, 1)
            })

            grp_name = grp.get("name", "").lower()
            if "19-70" in grp_name or "19-50" in grp_name or "men (19" in grp_name:
                standard_adult_rda_pct = round(pct, 1)
            elif not standard_adult_rda_pct and ("adult" in grp_name or "men" in grp_name):
                standard_adult_rda_pct = round(pct, 1)

        if not standard_adult_rda_pct and rda_results:
            standard_adult_rda_pct = rda_results[0]["percentage"]

        return {
            "parent_nutrient": salt_entry["parent_name"],
            "salt_name": salt_entry["salt_name"],
            "salt_percentage": round(percentage * 100, 2),
            "input_dose": dose,
            "input_unit": unit,
            "elemental_amount_mg": round(elemental_mg, 4),
            "elemental_unit": "mg",
            "secondary": secondary_res,
            "standard_adult_rda_pct": standard_adult_rda_pct,
            "rda_breakdown": rda_results
        }

    def annotate_ingredient(self, ing: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes an OCR ingredient and attaches elemental calculation, RDA,
        and all available salt form options if matched.
        """
        name = ing.get("name", "")
        dosage = float(ing.get("dosage", 0) or 0)
        unit = ing.get("unit", "mg")

        matched = self.match_salt(name)
        elem_matched = self.match_element(name)

        if matched and dosage > 0:
            calc = self.calculate_elemental(matched, dosage, unit)
            parent_key = matched.get("parent_key") or (elem_matched.get("element_key") if elem_matched else None)
            is_elem_spec = matched.get("is_element_specification", False) or "elemental" in name.lower()

            if parent_key:
                target_dose = dosage if is_elem_spec else calc.get("elemental_amount_mg", dosage)
                options_info = self.get_element_options(parent_key, target_dose, is_target_elemental=True, unit=unit)
                calc["element_options"] = options_info.get("options", [])
                calc["element_options_count"] = len(calc["element_options"])
                calc["is_elemental_specification"] = is_elem_spec
            else:
                calc["element_options"] = []
                calc["element_options_count"] = 0

            ing["is_salt_derivative"] = True
            ing["salt_element_calc"] = calc
        elif elem_matched and dosage > 0:
            options_info = self.get_element_options(elem_matched["element_key"], dosage, is_target_elemental=True, unit=unit)
            calc = {
                "parent_nutrient": elem_matched["element_name"],
                "salt_name": f"{elem_matched['element_name']} (Elemental)",
                "salt_percentage": 100.0,
                "input_dose": dosage,
                "input_unit": unit,
                "elemental_amount_mg": dosage,
                "elemental_unit": unit,
                "secondary": None,
                "standard_adult_rda_pct": options_info.get("options", [{}])[0].get("adult_rda_percent", 0.0) if options_info.get("options") else 0.0,
                "is_elemental_specification": True,
                "element_options": options_info.get("options", []),
                "element_options_count": len(options_info.get("options", []))
            }
            ing["is_salt_derivative"] = True
            ing["salt_element_calc"] = calc
        else:
            ing["is_salt_derivative"] = False
            ing["salt_element_calc"] = None
        return ing

    def get_full_catalog(self) -> Dict[str, Any]:
        """
        Returns full structured catalog for interactive calculator UI
        """
        return {
            "minerals": self.minerals,
            "vitamins": self.vitamins,
            "miscellaneous": self.miscellaneous
        }
