import os
import re
import json
import time
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, Any, List, Optional, Tuple
from rapidfuzz import fuzz, process

from app.config import DATA_DIR, GEMINI_API_KEY, GEMINI_MODEL
from app.formula_parser import FormulaParser
from app.learning_engine import SelfLearningEngine

SUBAGENT_MEMORY_PATH = DATA_DIR / "model_subagent_memory.json"

def get_ist_timestamp() -> str:
    return datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d/%m/%Y, %I:%M:%S %p IST")

class ModelTrainingSubagent:
    """
    Walpar Model Training Subagent:
    Autonomous knowledge assimilation engine.
    Allows specialized model trainer (Tanmay) to teach new ingredient mappings,
    aliases, elemental salt relations, and formula rules in natural language.
    Permanently stores rules and immediately updates live runtime memory.
    """
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.rules: List[Dict[str, Any]] = []
        self.stats = {
            "total_rules": 0,
            "last_trained_at": None,
            "trainer": "tanmay",
            "model_version": "subagent-v2.5"
        }
        self.formula_parser = FormulaParser()
        self.load_memory()
        self.sync_rules_to_parser()

    def load_memory(self):
        """Loads persistent model training rules from disk"""
        try:
            if SUBAGENT_MEMORY_PATH.exists():
                with open(SUBAGENT_MEMORY_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.rules = data.get("rules", [])
                    self.stats.update(data.get("stats", {}))
            else:
                self.rules = []
                self.save_memory()
        except Exception as e:
            print(f"[ModelSubagent] Error loading memory: {e}")
            self.rules = []

    def save_memory(self):
        """Persists trained rules to disk"""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            self.stats["total_rules"] = len(self.rules)
            payload = {
                "stats": self.stats,
                "rules": self.rules
            }
            with open(SUBAGENT_MEMORY_PATH, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ModelSubagent] Error saving memory: {e}")

    def sync_rules_to_parser(self):
        """Injects all active trained rules into runtime parser and learning engine memory"""
        applied_count = 0
        for rule in self.rules:
            if rule.get("status") == "active":
                source = rule.get("source_term", "").strip().lower()
                target_name = rule.get("target_term", "").strip()
                target_item = self._find_master_ingredient(target_name)
                if target_item and source:
                    self._inject_alias_into_parser(source, target_item)
                    applied_count += 1
        print(f"[ModelSubagent] Synced {applied_count} active rules into runtime formula parser memory.")

    def _inject_alias_into_parser(self, source_term: str, target_item: Dict[str, Any]):
        """Injects an alias into FormulaParser and SelfLearningEngine"""
        clean_src = source_term.strip().lower()
        no_space = clean_src.replace(" ", "")
        hyphen_to_space = clean_src.replace("-", " ")
        space_to_hyphen = clean_src.replace(" ", "-")

        self.formula_parser.alias_to_ingredient[clean_src] = target_item
        self.formula_parser.alias_to_ingredient[no_space] = target_item
        self.formula_parser.alias_to_ingredient[hyphen_to_space] = target_item
        self.formula_parser.alias_to_ingredient[space_to_hyphen] = target_item

        # Also add to SelfLearningEngine
        learning_engine = SelfLearningEngine.get_instance()
        learning_engine.learned_patterns[clean_src] = {
            "canonical_name": target_item.get("name"),
            "canonical_id": str(target_item.get("id", "custom")),
            "rate": target_item.get("rate", 0.0),
            "source": "model_subagent_trainer_tanmay",
            "confidence_weight": 2.5
        }

    def _find_master_ingredient(self, query: str) -> Optional[Dict[str, Any]]:
        """Searches master ingredients list for target ingredient with high precision"""
        q_clean = query.strip().lower()
        if not q_clean:
            return None

        # 1. Exact alias match
        if q_clean in self.formula_parser.alias_to_ingredient:
            return self.formula_parser.alias_to_ingredient[q_clean]

        # 2. Exact match in master list
        for item in self.formula_parser.ingredients_master:
            name_lower = str(item.get("name", "")).strip().lower()
            if name_lower == q_clean:
                return item

        # 3. Fuzzy search in master list (score >= 78)
        names = [str(item.get("name", "")) for item in self.formula_parser.ingredients_master]
        match = process.extractOne(query, names, scorer=fuzz.token_sort_ratio)
        if match and match[1] >= 78:
            matched_name = match[0]
            for item in self.formula_parser.ingredients_master:
                if str(item.get("name", "")).strip().lower() == matched_name.strip().lower():
                    return item

        return None

    def _parse_with_gemini(self, text: str) -> Optional[Dict[str, Any]]:
        """Uses Gemini API to extract source term, target term, and rule intent from natural language"""
        api_key = os.environ.get("GEMINI_API_KEY") or GEMINI_API_KEY
        if not api_key:
            return None

        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")

            system_prompt = """
You are an expert pharmaceutical & nutraceutical formulation AI subagent.
A model trainer provides an instruction like:
- "selenium is same as sodium selenite"
- "map haldi extract to curcumin 95%"
- "cholecalciferol is alias for vitamin d3"
- "zinc sulphate monohydrate should be considered zinc"

Extract the training directive and respond ONLY with a raw JSON object (no markdown, no backticks):
{
  "source_term": "selenium",
  "target_term": "sodium selenite",
  "rule_type": "synonym",
  "explanation": "Mapped selenium to sodium selenite"
}

Rule types can be: "synonym", "alias", "salt_form", "excipient".
If the instruction cannot be parsed into a source and target ingredient, return:
{
  "source_term": "",
  "target_term": "",
  "rule_type": "unknown",
  "explanation": "Could not extract source and target"
}
"""
            resp = model.generate_content([system_prompt, f"Instruction: {text}"])
            raw = resp.text.strip()
            # Clean potential markdown ticks
            raw = re.sub(r"^```(?:json)?", "", raw)
            raw = re.sub(r"```$", "", raw).strip()
            parsed = json.loads(raw)
            if parsed.get("source_term") and parsed.get("target_term"):
                return parsed
        except Exception as e:
            print(f"[ModelSubagent] Gemini parsing failed: {e}, falling back to local NLP regex")

        return None

    def _parse_with_local_nlp(self, text: str) -> Optional[Dict[str, Any]]:
        """Robust local rule-based NLP parser for natural language directives"""
        t = text.strip()

        patterns = [
            # X is same as Y / X is the same as Y
            r"(?i)^(.+?)\s+(?:is\s+(?:the\s+)?same\s+as|is\s+equal\s+to|equals?|=)\s+(.+)$",
            # X is alias for Y / X is alias of Y / X is an alias for Y
            r"(?i)^(.+?)\s+is\s+(?:an?\s+)?alias\s+(?:for|of|to)\s+(.+)$",
            # map X to Y / map X as Y
            r"(?i)^map\s+(.+?)\s+(?:to|as|into)\s+(.+)$",
            # consider X as Y / treat X as Y
            r"(?i)^(?:consider|treat|take)\s+(.+?)\s+as\s+(.+)$",
            # X means Y / X -> Y
            r"(?i)^(.+?)\s+(?:means|->|=>)\s+(.+)$",
            # add X as Y
            r"(?i)^add\s+(.+?)\s+as\s+(.+)$",
            # link X to Y / link X with Y
            r"(?i)^link\s+(.+?)\s+(?:to|with)\s+(.+)$"
        ]

        for pat in patterns:
            m = re.match(pat, t)
            if m:
                src = m.group(1).strip().strip("'\"`")
                tgt = m.group(2).strip().strip("'\"`")
                if src and tgt:
                    return {
                        "source_term": src,
                        "target_term": tgt,
                        "rule_type": "synonym",
                        "explanation": f"Mapped '{src}' to '{tgt}'"
                    }

        return None

    def train_from_text(self, directive_text: str, trainer_username: str = "tanmay") -> Dict[str, Any]:
        """
        Executes natural language training directive.
        Validates target in master database, updates persistent memory,
        and immediately activates the learned rule across the system.
        """
        raw_text = str(directive_text or "").strip()
        if not raw_text:
            return {
                "success": False,
                "message": "Can't be added: Training directive was empty. Please provide an instruction like 'selenium is same as sodium selenite'.",
                "directive": raw_text
            }

        # 1. Parse directive (Try Gemini API first, then local NLP)
        parsed = self._parse_with_gemini(raw_text)
        if not parsed:
            parsed = self._parse_with_local_nlp(raw_text)

        if not parsed or not parsed.get("source_term") or not parsed.get("target_term"):
            return {
                "success": False,
                "message": f"Can't be added: Could not understand the relation in: \"{raw_text}\". Please format your instruction like: 'X is same as Y' or 'map X to Y'.",
                "directive": raw_text
            }

        source_term = parsed["source_term"].strip()
        target_term = parsed["target_term"].strip()
        rule_type = parsed.get("rule_type", "synonym")

        # 2. Validate target ingredient in master database
        target_item = self._find_master_ingredient(target_term)

        # Also check in Salt RDA Engine if it's an elemental mineral/salt
        if not target_item:
            try:
                from app.salt_rda_engine import SaltRDAEngine
                salt_eng = SaltRDAEngine.get_instance()
                matched_salt = salt_eng.match_salt(target_term)
                if matched_salt:
                    # Treat matched salt as valid ground truth
                    target_item = {
                        "name": matched_salt.get("salt_name"),
                        "rate": 0.0,
                        "unit": "mg",
                        "is_salt_form": True,
                        "element": matched_salt.get("element"),
                        "elemental_percent": matched_salt.get("elemental_percent")
                    }
            except Exception:
                pass

        if not target_item:
            # Generate close suggestions to assist Tanmay
            all_names = [str(x.get("name", "")) for x in self.formula_parser.ingredients_master]
            matches = process.extract(target_term, all_names, limit=4, scorer=fuzz.token_sort_ratio)
            suggestions = [m[0] for m in matches if m[1] > 40]

            sugg_str = f" Did you mean one of: {', '.join(suggestions)}?" if suggestions else ""
            return {
                "success": False,
                "message": f"Can't be added: Target ingredient \"{target_term}\" was not found in Walpar master database (601 ingredients).{sugg_str}",
                "directive": raw_text,
                "parsed_source": source_term,
                "parsed_target": target_term,
                "suggestions": suggestions
            }

        canonical_target_name = target_item.get("name", target_term)
        target_rate = float(target_item.get("rate") or 0.0)

        # 3. Check for duplicate or existing rule
        clean_src = source_term.lower()
        existing_idx = None
        for idx, r in enumerate(self.rules):
            if r.get("source_term", "").lower() == clean_src:
                existing_idx = idx
                break

        rule_id = f"rule_{int(time.time())}_{abs(hash(clean_src)) % 10000}"
        timestamp = get_ist_timestamp()

        new_rule = {
            "id": rule_id,
            "raw_directive": raw_text,
            "source_term": source_term,
            "source_term_clean": clean_src,
            "target_term": canonical_target_name,
            "target_rate": target_rate,
            "rule_type": rule_type,
            "trainer": trainer_username,
            "created_at_ist": timestamp,
            "status": "active",
            "validation_note": f"Verified against master DB item '{canonical_target_name}'"
        }

        if existing_idx is not None:
            self.rules[existing_idx] = new_rule
        else:
            self.rules.insert(0, new_rule)

        # 4. Immediately activate in runtime memory
        self._inject_alias_into_parser(clean_src, target_item)

        # 5. Save memory
        self.stats["last_trained_at"] = timestamp
        self.stats["trainer"] = trainer_username
        self.save_memory()

        rate_msg = f" (Database Rate: ₹{target_rate:,.2f}/kg)" if target_rate > 0 else ""
        return {
            "success": True,
            "message": f"Successfully added to Model Memory! \"{source_term}\" is now recognized as \"{canonical_target_name}\"{rate_msg}. All OCR scans and batch formulations will use this rule.",
            "rule": new_rule,
            "total_rules": len(self.rules)
        }

    def test_resolution(self, query: str) -> Dict[str, Any]:
        """
        Tests how the model and formula parser resolve an ingredient query
        using both master database and active subagent-trained rules.
        """
        q = str(query or "").strip()
        if not q:
            return {"success": False, "error": "Query is empty"}

        # 1. Extract dosage and unit if present
        dose, unit, cleaned_name = self.formula_parser.extract_dose_and_unit(q)
        eval_query = cleaned_name if cleaned_name else q

        # 2. Match ingredient in parser
        matched_item, score = self.formula_parser.match_ingredient(eval_query)

        # 3. Check if matched via a trained subagent rule
        matched_rule = None
        for r in self.rules:
            if r.get("status") == "active":
                src = r.get("source_term", "").lower()
                if src in q.lower() or src == eval_query.lower():
                    matched_rule = r
                    break

        resolved_name = (matched_item.get("name") if matched_item else "Not Matched")
        resolved_rate = float(matched_item.get("rate") or 0.0) if matched_item else 0.0

        return {
            "success": True,
            "query": q,
            "cleaned_name": eval_query,
            "extracted_dosage": dose,
            "extracted_unit": unit,
            "is_matched": bool(matched_item and score >= 60),
            "match_score": round(score, 1),
            "resolved_name": resolved_name,
            "resolved_rate": resolved_rate,
            "matched_by_subagent_rule": matched_rule
        }

    def delete_rule(self, rule_id: str) -> Dict[str, Any]:
        """Deletes a learned rule from memory and updates parser"""
        found = False
        removed_rule = None
        for i, r in enumerate(self.rules):
            if r.get("id") == rule_id:
                removed_rule = self.rules.pop(i)
                found = True
                break

        if found:
            self.save_memory()
            # Reload parser aliases to ensure deleted alias is purged
            self.formula_parser = FormulaParser()
            self.sync_rules_to_parser()
            return {"success": True, "message": f"Rule '{rule_id}' deleted successfully", "deleted_rule": removed_rule}

        return {"success": False, "error": f"Rule with ID '{rule_id}' not found"}

    def get_all_rules(self) -> List[Dict[str, Any]]:
        """Returns all rules in memory"""
        return self.rules
