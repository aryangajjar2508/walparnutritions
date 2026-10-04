import os
import re
import json
import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from app.config import INGREDIENTS_DB_PATH, EXAMINE_DB_PATH

class FormulaEvaluator:
    def __init__(self, db_path: str = None, examine_db_path: str = None):
        self.db_path = Path(db_path or INGREDIENTS_DB_PATH)
        self.examine_db_path = Path(examine_db_path or EXAMINE_DB_PATH)
        
        self.ingredients_db = {}
        self.dosage_forms = {}
        self.examine_cache = {}
        self.load_data()

    def get_examine_conn(self):
        if self.examine_db_path.exists():
            conn = sqlite3.connect(str(self.examine_db_path))
            conn.row_factory = sqlite3.Row
            return conn
        return None

    def load_data(self):
        # 1. Load Walpar master ingredients JSON
        try:
            if self.db_path.exists():
                with open(self.db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("ingredients", []):
                        self.ingredients_db[item["id"]] = item
                        self.ingredients_db[item["name"].lower().strip()] = item
                        for alias in item.get("aliases", []):
                            self.ingredients_db[alias.lower().strip()] = item
                    for form in data.get("dosage_forms", []):
                        self.dosage_forms[form["id"]] = form
        except Exception as e:
            print(f"[Evaluator] Error loading ingredients DB: {e}")

        # 2. Pre-index Examine DB supplements
        try:
            conn = self.get_examine_conn()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT slug, name FROM supplements")
                for r in cursor.fetchall():
                    s_slug = r["slug"].lower().strip()
                    s_name = r["name"].lower().strip()
                    self.examine_cache[s_slug] = s_slug
                    self.examine_cache[s_name] = s_slug
                conn.close()
                print(f"[Evaluator] Indexed {len(self.examine_cache)} Examine supplement keys from {self.examine_db_path}")
        except Exception as e:
            print(f"[Evaluator] Error indexing examine.db: {e}")

    def lookup_examine_monograph(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Looks up a supplement in examine.db by name, slug, or keyword variant.
        Returns complete monograph including effect_matrix and dosage_guide.
        """
        conn = self.get_examine_conn()
        if not conn:
            return None

        raw = str(query).strip()
        if not raw or len(raw) < 2:
            conn.close()
            return None

        # Extract terms: outside parens, inside parens, without filler words
        out_paren = re.sub(r'\(.*?\)', ' ', raw).strip()
        in_paren = re.findall(r'\((.*?)\)', raw)

        candidates_terms = [raw, out_paren] + in_paren
        clean_terms = []

        salt_pattern = r'\b(gluconate|citrate|picolinate|carbonate|bisglycinate|glycinate|sulfate|sulphate|oxide|ascorbate|fumarate|succinate|malate|chelate|monomethionine|hcl|hydrochloride|monohydrate|dihydrate|extract|plain|powder|95%|std|standardized|vial|tablets?|capsules?|mg|mcg|iu|as|from|with)\b'
        nutrient_synonyms = {
            'ascorbic acid': 'vitamin c',
            'ascorbate': 'vitamin c',
            'cholecalciferol': 'vitamin d',
            'ergocalciferol': 'vitamin d',
            'menaquinone': 'vitamin k',
            'phylloquinone': 'vitamin k',
            'methylcobalamin': 'vitamin b12',
            'cyanocobalamin': 'vitamin b12',
            'pyridoxine': 'vitamin b6',
            'thiamine': 'vitamin b1',
            'riboflavin': 'vitamin b2',
            'niacin': 'vitamin b3',
            'niacinamide': 'vitamin b3',
            'biotin': 'vitamin b7',
            'folic acid': 'folic acid',
            'folate': 'folic acid',
            'tocopherol': 'vitamin e',
            'coq10': 'coenzyme q10',
            'ubiquinone': 'coenzyme q10',
            'ubiquinol': 'coenzyme q10',
            'ferrous': 'iron',
            'black pepper': 'piperine',
            'bioperine': 'piperine',
            'curcuma longa': 'curcumin',
            'turmeric': 'curcumin',
            'sambucus': 'elderberry',
            'withania somnifera': 'ashwagandha',
            'boswellia serrata': 'boswellia',
        }

        for term in candidates_terms:
            ct = re.sub(r'[^a-zA-Z0-9\s\-]', ' ', term).strip().lower()
            ct_clean = re.sub(salt_pattern, '', ct).strip()
            ct_clean = re.sub(r'\s+', ' ', ct_clean)

            # Check synonyms
            for syn_k, syn_v in nutrient_synonyms.items():
                if syn_k in ct or syn_k in ct_clean:
                    if syn_v not in clean_terms:
                        clean_terms.append(syn_v)

            if ct_clean and len(ct_clean) >= 3 and ct_clean not in clean_terms:
                clean_terms.append(ct_clean)
            if ct and len(ct) >= 3 and ct not in clean_terms:
                clean_terms.append(ct)

        row = None
        cursor = conn.cursor()

        # 1. Exact match on slug, name, or parenthesized title
        for t in clean_terms:
            slug_variant = t.replace(' ', '-')
            cursor.execute("""
                SELECT * FROM supplements 
                WHERE lower(name) = ? OR lower(slug) = ? OR lower(name) LIKE ?
                ORDER BY length(name) ASC LIMIT 1
            """, (t, slug_variant, f"{t} (%)%"))
            row = cursor.fetchone()
            if row:
                break

        # 2. Match exact word boundaries
        if not row:
            for t in clean_terms:
                if len(t) >= 4:
                    cursor.execute("""
                        SELECT * FROM supplements 
                        WHERE lower(name) LIKE ? OR lower(slug) LIKE ?
                        ORDER BY 
                            CASE WHEN lower(name) LIKE ? THEN 1 ELSE 2 END,
                            length(name) ASC 
                        LIMIT 1
                    """, (f"%{t}%", f"%{t}%", f"{t}%"))
                    row = cursor.fetchone()
                    if row:
                        break

        if not row:
            conn.close()
            return None

        d = dict(row)
        slug = d["slug"]

        # Parse JSON fields safely
        try:
            d["dosage_guide"] = json.loads(d["dosage_guide"]) if d.get("dosage_guide") else {}
        except Exception:
            d["dosage_guide"] = {}

        try:
            d["safety_data"] = json.loads(d["safety_data"]) if d.get("safety_data") else {}
        except Exception:
            d["safety_data"] = {}

        try:
            d["things_to_know"] = json.loads(d["things_to_know"]) if d.get("things_to_know") else {}
        except Exception:
            d["things_to_know"] = {}

        # Fetch top effect matrix outcomes (Grade A/B clinical trials)
        cursor.execute("""
            SELECT outcome, category, magnitude, evidence_grade, clinical_notes, study_count, direction
            FROM effect_matrix 
            WHERE supplement_slug = ? 
            ORDER BY 
                CASE evidence_grade 
                    WHEN 'A' THEN 1 
                    WHEN 'B' THEN 2 
                    WHEN 'C' THEN 3 
                    ELSE 4 END,
                study_count DESC
            LIMIT 5
        """, (slug,))
        d["effect_matrix"] = [dict(mr) for mr in cursor.fetchall()]

        conn.close()
        return d

    def normalize_to_mg(self, dosage: float, unit: str, name: str = "") -> float:
        """
        Convert dosage to mg for total weight calculation
        """
        u = str(unit or "mg").lower().strip()
        n = str(name or "").lower().strip()
        d = float(dosage or 0.0)
        if u in ['g', 'gm', 'gram', 'grams']:
            return d * 1000.0
        elif u in ['mcg', 'ug', 'microgram', 'micrograms']:
            return d / 1000.0
        elif u == 'iu':
            if any(k in n for k in ['vitamin a', 'vit a', 'retinol', 'retinyl', 'carotene']):
                return d * 0.0003
            elif any(k in n for k in ['vitamin e', 'vit e', 'tocopher', 'tocopheryl']):
                return d * 0.67
            else:
                # Vitamin D family (D3 Cholecalciferol, D2 Ergocalciferol): 1 IU = 0.025 mcg = 0.000025 mg
                return d * 0.000025
        return float(d)

    def evaluate_formula(self, ingredients: List[Dict[str, Any]], dosage_form_id: str = "tablets") -> Dict[str, Any]:
        """
        Clinical evidence-based formulation evaluation powered by Examine database:
        - Human Effect Matrix (HEM) with Grade A/B RCT outcomes
        - Clinical Dosage & Safety Audit against Examine therapeutic standards
        - Synergies & Potentiation detection
        - Actionable AI Suggestions with 1-Click Apply
        - Formulation Quality Rating (0 - 100)
        (STRICTLY ZERO PRICES)
        """
        item_evaluations = []
        total_active_mg = 0.0
        synergies_detected = []
        conflicts_detected = []
        suggestions = []
        human_effect_matrix = []
        score = 80  # Base starting score

        names_present = [item.get("name", "").lower() for item in ingredients]

        # 1. Evaluate each individual ingredient using Examine monographs
        for item in ingredients:
            raw_name = str(item.get("name", "")).strip()
            dosage = float(item.get("dosage", 0))
            unit = str(item.get("unit", "mg")).strip()

            active_mg = self.normalize_to_mg(dosage, unit, raw_name)
            total_active_mg += active_mg

            # Lookup Examine Monograph
            monograph = self.lookup_examine_monograph(raw_name)

            status = "optimal"
            note = "Dosage within standard parameters."
            clinical_dose = "Standard therapeutic dose"
            safety_ul = "Standard dietary tolerance"
            highest_grade = "B"
            top_outcomes = []
            monograph_name = raw_name

            if monograph:
                monograph_name = monograph.get("name", raw_name)
                d_guide = monograph.get("dosage_guide", {})
                clinical_dose = d_guide.get("standard_dose") or d_guide.get("recommended_dose") or "Refer to clinical monograph"
                s_data = monograph.get("safety_data", {})
                safety_ul = s_data.get("upper_limit") or "No acute toxicity reported within clinical range"
                contraindications = s_data.get("contraindications", "")

                # Extract effect matrix outcomes
                mat_rows = monograph.get("effect_matrix", [])
                if mat_rows:
                    highest_grade = mat_rows[0].get("evidence_grade", "B")
                    for m in mat_rows:
                        top_outcomes.append({
                            "outcome": m.get("outcome"),
                            "category": m.get("category", "General Health"),
                            "grade": m.get("evidence_grade", "B"),
                            "magnitude": m.get("magnitude", "Clinical Improvement"),
                            "notes": m.get("clinical_notes", ""),
                            "ingredient": monograph_name
                        })
                        # Add to formula-wide effect matrix
                        human_effect_matrix.append({
                            "ingredient": monograph_name,
                            "outcome": m.get("outcome"),
                            "category": m.get("category", "General Health"),
                            "grade": m.get("evidence_grade", "B"),
                            "magnitude": m.get("magnitude", "Clinical Improvement"),
                            "notes": m.get("clinical_notes", "")
                        })

                # Grade A boost
                if highest_grade == "A":
                    score += 5
                    status = "optimal"
                    note = f"Backed by Grade A Human Clinical Trials. {monograph.get('things_to_know', {}).get('verdict', '')}"
                else:
                    note = f"Clinical Evidence Grade {highest_grade}. Standard clinical dose: {clinical_dose}."

                if contraindications and "precaution" not in note.lower():
                    item["contraindications"] = contraindications
            else:
                # Fallback to internal DB if not in examine.db
                db_item = self.ingredients_db.get(item.get("id")) or self.ingredients_db.get(raw_name.lower())
                if db_item:
                    ul = db_item.get("upper_limit", 0)
                    std_dose = db_item.get("standard_dose", 0)
                    std_unit = db_item.get("standard_unit", "mg")
                    clinical_dose = f"{std_dose} {std_unit}"
                    if ul > 0:
                        safety_ul = f"{ul} {std_unit}"
                        if dosage > ul:
                            status = "alert_toxic"
                            note = f"Exceeds regulatory Upper Limit ({ul} {std_unit})!"
                            score -= 15

            item_evaluations.append({
                "name": raw_name,
                "dosage": dosage,
                "unit": unit,
                "active_mg": round(active_mg, 2),
                "examine_matched": monograph is not None,
                "examine_name": monograph_name,
                "evidence_grade": highest_grade,
                "clinical_standard_dose": clinical_dose,
                "safety_upper_limit": safety_ul,
                "status": status,
                "note": note,
                "top_outcomes": top_outcomes[:2]
            })

        # 2. Evaluate Synergies & Potentiation Pairs (from Examine & Clinical trials)
        has_curcumin = any("curcumin" in n or "turmeric" in n for n in names_present)
        has_piperine = any("piperine" in n or "black pepper" in n for n in names_present)
        if has_curcumin and has_piperine:
            synergies_detected.append({
                "title": "Curcumin + Piperine Bioavailability Booster",
                "badge": "2000% Absorption",
                "evidence_grade": "A",
                "description": "Piperine (Black Pepper Extract) inhibits hepatic glucuronidation, increasing Curcumin bioavailability by up to 2,000%."
            })
            score += 10
        elif has_curcumin and not has_piperine:
            suggestions.append({
                "type": "synergy_missing",
                "title": "Add Piperine to Curcumin",
                "description": "Examine trials prove Curcumin has very low standalone absorption (<1%). Adding 5mg Piperine 95% multiplies absorption 20x.",
                "suggested_ingredient": "Piperine (Black Pepper Extract 95%)",
                "suggested_dose": 5,
                "suggested_unit": "mg"
            })

        has_d3 = any("vitamin d" in n or "cholecalciferol" in n for n in names_present)
        has_calcium = any("calcium" in n for n in names_present)
        has_k2 = any("vitamin k" in n or "k2" in n or "menaquinone" in n for n in names_present)

        if has_d3 and has_calcium and has_k2:
            synergies_detected.append({
                "title": "Bone Matrix Triad (D3 + K2-7 + Calcium)",
                "badge": "Vascular Safe",
                "evidence_grade": "A",
                "description": "D3 enhances calcium intestinal uptake, while K2-7 activates osteocalcin to route calcium straight into bone matrix and away from arteries."
            })
            score += 12
        elif has_d3 and has_calcium and not has_k2:
            suggestions.append({
                "type": "synergy_missing",
                "title": "Add Vitamin K2-7 to Calcium + D3",
                "description": "Examine safety monographs indicate calcium supplementation with D3 requires Vitamin K2-7 to ensure safe bone deposition and prevent arterial calcification.",
                "suggested_ingredient": "Vitamin K2-7 (Menaquinone-7)",
                "suggested_dose": 55,
                "suggested_unit": "mcg"
            })

        has_iron = any("iron" in n or "ferrous" in n for n in names_present)
        has_vit_c = any("vitamin c" in n or "ascorbic" in n for n in names_present)
        if has_iron and has_vit_c:
            synergies_detected.append({
                "title": "Iron + Vitamin C Synergistic Uptake",
                "badge": "Enhanced RBC Synthesis",
                "evidence_grade": "A",
                "description": "Ascorbic acid reduces ferric iron to ferrous state, drastically improving duodenal absorption and reducing gastric upset."
            })
            score += 8
        elif has_iron and not has_vit_c:
            suggestions.append({
                "type": "synergy_missing",
                "title": "Add Vitamin C to Iron",
                "description": "Adding 50-100mg Vitamin C with Iron doubles non-heme iron absorption.",
                "suggested_ingredient": "Vitamin C (Ascorbic Acid)",
                "suggested_dose": 50,
                "suggested_unit": "mg"
            })

        has_zinc = any("zinc" in n for n in names_present)
        if has_vit_c and has_zinc and has_d3:
            synergies_detected.append({
                "title": "Immunity Triad (Vitamin C + Zinc + Vitamin D3)",
                "badge": "Triple Cellular Defense",
                "evidence_grade": "A",
                "description": "Synergistic cellular defense: Vitamin C reinforces epithelial tissue, Zinc activates T-cells, and Vitamin D3 stimulates antimicrobial peptide expression."
            })
            score += 15
        elif has_vit_c and has_zinc:
            synergies_detected.append({
                "title": "Vitamin C + Zinc Cellular Protection",
                "badge": "Immune Defense",
                "evidence_grade": "A",
                "description": "Ascorbic acid and elemental zinc work synergistically to reduce oxidative stress and viral replication."
            })
            score += 8

        has_melatonin = any("melatonin" in n for n in names_present)
        has_theanine = any("theanine" in n for n in names_present)
        has_magnesium = any("magnesium" in n for n in names_present)
        if has_melatonin and (has_theanine or has_magnesium):
            synergies_detected.append({
                "title": "Sleep & Circadian Rhythm Synergy",
                "badge": "Restorative REM",
                "evidence_grade": "A",
                "description": "Melatonin induces onset of sleep, while Magnesium and L-Theanine calm NMDA receptors to facilitate deep restorative sleep."
            })
            score += 10

        has_glucosamine = any("glucosamine" in n for n in names_present)
        has_chondroitin = any("chondroitin" in n for n in names_present)
        has_msm = any("msm" in n or "methylsulfonylmethane" in n for n in names_present)
        if has_glucosamine and (has_chondroitin or has_msm):
            synergies_detected.append({
                "title": "Joint Cartilage Regenerative Complex",
                "badge": "Triple Action",
                "evidence_grade": "A",
                "description": "Glucosamine repairs cartilage matrix, Chondroitin inhibits destructive enzymes, and MSM lubricates synovial tissues."
            })
            score += 10

        # 3. Check Conflicts & Safety Alerts
        if has_calcium and has_iron:
            conflicts_detected.append({
                "title": "Calcium vs Iron Absorption Competition",
                "severity": "medium",
                "description": "Calcium inhibits non-heme iron absorption if taken in high amounts simultaneously. Consider using micro-encapsulated Ferrous Bisglycinate."
            })
            score -= 10

        zinc_item = next((item for item in ingredients if "zinc" in item.get("name", "").lower()), None)
        has_copper = any("copper" in n for n in names_present)
        if zinc_item and float(zinc_item.get("dosage", 0)) >= 30 and not has_copper:
            conflicts_detected.append({
                "title": "Zinc-Induced Copper Depletion Risk",
                "severity": "medium",
                "description": "Chronic zinc dosages >= 30mg can block intestinal copper absorption. Consider adding 1-2mg Copper Gluconate to maintain balance."
            })
            suggestions.append({
                "type": "safety_balance",
                "title": "Add 1mg Copper with High Zinc",
                "description": "Adding 1mg Copper Gluconate prevents zinc-induced copper depletion.",
                "suggested_ingredient": "Copper Gluconate",
                "suggested_dose": 1,
                "suggested_unit": "mg"
            })
            score -= 8

        # 4. Delivery Form Feasibility
        form_name = "Film-Coated Tablet"
        recommended_form = "Film-Coated Tablet"
        if total_active_mg > 2000:
            recommended_form = "Effervescent / Powder Sachet"
            form_status = "exceeds_single_unit"
            form_message = f"Total active weight ({round(total_active_mg, 1)} mg) is large; best suited for an Effervescent Tablet or Sachet."
        elif total_active_mg <= 750:
            recommended_form = "Tablet or 2-Piece Capsule"
            form_status = "feasible"
            form_message = f"Total active weight ({round(total_active_mg, 1)} mg) fits comfortably into a standard single tablet or capsule."
        else:
            recommended_form = "Caplet or Chewable Tablet"
            form_status = "feasible"
            form_message = f"Total active weight ({round(total_active_mg, 1)} mg) is suitable for a standard caplet or chewable."

        final_score = max(35, min(99, score))

        # Deduplicate Human Effect Matrix
        seen_outcomes = set()
        dedup_matrix = []
        for em in human_effect_matrix:
            key = (em["outcome"].lower(), em["grade"])
            if key not in seen_outcomes:
                seen_outcomes.add(key)
                dedup_matrix.append(em)

        return {
            "score": final_score,
            "status_label": "Grade A Evidence (Excellent)" if final_score >= 88 else ("High Clinical Grade" if final_score >= 75 else "Needs Optimization"),
            "total_active_mg": round(total_active_mg, 1),
            "item_evaluations": item_evaluations,
            "human_effect_matrix": dedup_matrix[:6],  # Top 6 clinical outcomes
            "synergies": synergies_detected,
            "conflicts": conflicts_detected,
            "suggestions": suggestions,
            "form_feasibility": {
                "chosen_form_name": form_name,
                "status": form_status,
                "message": form_message,
                "recommended_form_name": recommended_form
            }
        }
