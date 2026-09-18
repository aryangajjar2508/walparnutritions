import re
import difflib
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Common medical, symptom, and supplement misspelling dictionary
COMMON_TYPOS: Dict[str, str] = {
    # Supplements & Ingredients
    "creatne": "creatine",
    "cretine": "creatine",
    "creatine monohydrat": "creatine monohydrate",
    "ashwaganda": "ashwagandha",
    "ashwaghanda": "ashwagandha",
    "ashwagandah": "ashwagandha",
    "aswagandha": "ashwagandha",
    "berbrine": "berberine",
    "berberin": "berberine",
    "berbarine": "berberine",
    "meltonin": "melatonin",
    "melitonin": "melatonin",
    "melotinin": "melatonin",
    "magnezium": "magnesium",
    "magnisium": "magnesium",
    "magnecium": "magnesium",
    "curcumine": "curcumin",
    "turmaric": "turmeric",
    "turmric": "turmeric",
    "fadoga": "fadogia",
    "fadoga agrestis": "fadogia agrestis",
    "glutathion": "glutathione",
    "resveratol": "resveratrol",
    "resveretrol": "resveratrol",
    "theanene": "theanine",
    "l-theanene": "l-theanine",
    "vitamen": "vitamin",
    "vitamim": "vitamin",
    "coq 10": "coenzyme q10",
    "coq10": "coenzyme q10",
    "tongkat": "tongkat ali",
    "tongkatali": "tongkat ali",
    "tongkat alii": "tongkat ali",
    "shilajeet": "shilajit",
    "rhodiola rosea": "rhodiola rosea",
    "rhodiola": "rhodiola rosea",
    "rodiola": "rhodiola rosea",
    "lions mane": "lion's mane",
    "lion mane": "lion's mane",
    "apiginin": "apigenin",
    "citruline": "citrulline",
    "arginin": "arginine",
    "palmitoylethanolamid": "palmitoylethanolamide",
    "glucosamin": "glucosamine",
    "chondroitine": "chondroitin",
    
    # Symptoms & Conditions
    "fatique": "fatigue",
    "fatige": "fatigue",
    "exhausion": "exhaustion",
    "insomnea": "insomnia",
    "insomna": "insomnia",
    "hartburn": "heartburn",
    "heart burn": "heartburn",
    "pane": "pain",
    "stifness": "stiffness",
    "sweling": "swelling",
    "swolen": "swollen",
    "anxieti": "anxiety",
    "anxeity": "anxiety",
    "depresion": "depression",
    "diabetis": "diabetes",
    "blud presure": "blood pressure",
    "blod presure": "blood pressure",
    "stomache": "stomach",
    "stomache ache": "stomach ache",
    "stomache akes": "stomach aches",
    "bloting": "bloating",
    "digeston": "digestion",
    "headacke": "headache",
    "headach": "headache",
    "migranes": "migraines",
    "migrane": "migraine",
    "nusea": "nausea",
    "colestrol": "cholesterol",
    "artritis": "arthritis",
    "inflamation": "inflammation",
    "inflamatory": "inflammatory",
    "brainfog": "brain fog",
    "brain fogg": "brain fog",
    "cramps": "muscle cramps",
    "palpitation": "heart palpitations"
}

QUESTION_PREFIX_PATTERNS = [
    r"^what\s+(is|are)\s+(a\s+|an\s+|the\s+)?",
    r"^tell\s+me\s+about\s+(a\s+|an\s+|the\s+)?",
    r"^how\s+(to|do\s+i|should\s+i)\s+(take|use|consume)\s+",
    r"^details\s+(on|about)\s+",
    r"^information\s+(on|about)\s+",
    r"^can\s+you\s+explain\s+",
    r"^what\s+does\s+",
    r"^what\s+do\s+you\s+know\s+about\s+",
    r"^explain\s+",
    r"^review\s+of\s+",
    r"^dosage\s+(for|of)\s+",
    r"^side\s+effects\s+of\s+",
    r"^benefits\s+of\s+",
    r"^is\s+",
    r"^can\s+"
]

def clean_token(s: str) -> str:
    return re.sub(r'[^a-z0-9]', '', s.lower())

def normalize_text_typos(text: str) -> Tuple[str, List[Tuple[str, str]]]:
    """
    Normalizes known typos in text and returns (corrected_text, list_of_replacements).
    """
    corrected = text
    corrections_made = []
    
    # Check multi-word phrases first
    for wrong, right in sorted(COMMON_TYPOS.items(), key=lambda x: -len(x[0])):
        pattern = r'\b' + re.escape(wrong) + r'\b'
        if re.search(pattern, corrected, flags=re.IGNORECASE):
            corrected = re.sub(pattern, right, corrected, flags=re.IGNORECASE)
            corrections_made.append((wrong, right))
            
    return corrected, corrections_made

def extract_core_ingredient_query(raw_query: str) -> str:
    """
    Strips question boilerplate to isolate the core ingredient / topic being asked.
    e.g., 'What is creatne and how to take it?' -> 'creatne'
          'tell me about ashwaganda' -> 'ashwaganda'
          'fadogia agrestis' -> 'fadogia agrestis'
    """
    q = raw_query.strip().strip("?.,!").strip()
    
STOP_WORDS = {
    'what', 'is', 'are', 'the', 'how', 'to', 'take', 'and', 'for', 'of', 'in', 'with', 'on', 'tell', 'me',
    'about', 'does', 'can', 'help', 'good', 'bad', 'should', 'would', 'could', 'much', 'many', 'when',
    'why', 'which', 'who', 'safe', 'safety', 'side', 'effects', 'benefits', 'dosage', 'dose', 'best',
    'time', 'way', 'effective', 'work', 'works', 'use', 'using', 'used', 'i', 'my', 'have', 'has', 'had',
    'supplement', 'supplements', 'taking', 'ingredient', 'ingredients', 'please', 'explain', 'give', 'details',
    'information', 'info', 'review', 'reviews', 'do', 'it', 'there', 'any'
}

QUESTION_PREFIX_PATTERNS = [
    r"^what\s+(is|are)\s+(a\s+|an\s+|the\s+)?",
    r"^tell\s+me\s+about\s+(a\s+|an\s+|the\s+)?",
    r"^how\s+(to|do\s+i|should\s+i)\s+(take|use|consume)\s+",
    r"^details\s+(on|about)\s+",
    r"^information\s+(on|about)\s+",
    r"^can\s+you\s+explain\s+",
    r"^what\s+does\s+",
    r"^what\s+do\s+you\s+know\s+about\s+",
    r"^explain\s+",
    r"^review\s+of\s+",
    r"^dosage\s+(for|of)\s+",
    r"^side\s+effects\s+of\s+",
    r"^benefits\s+of\s+",
    r"^is\s+",
    r"^can\s+"
]

def clean_token(s: str) -> str:
    return re.sub(r'[^a-z0-9]', '', s.lower())

def normalize_text_typos(text: str) -> Tuple[str, List[Tuple[str, str]]]:
    """
    Normalizes known typos in text and returns (corrected_text, list_of_replacements).
    """
    corrected = text
    corrections_made = []
    
    # Check multi-word phrases first
    for wrong, right in sorted(COMMON_TYPOS.items(), key=lambda x: -len(x[0])):
        pattern = r'\b' + re.escape(wrong) + r'\b'
        if re.search(pattern, corrected, flags=re.IGNORECASE):
            corrected = re.sub(pattern, right, corrected, flags=re.IGNORECASE)
            corrections_made.append((wrong, right))
            
    return corrected, corrections_made

def extract_core_ingredient_query(raw_query: str) -> str:
    """
    Strips question boilerplate to isolate the core ingredient / topic being asked.
    e.g., 'What is creatne and how to take it?' -> 'creatne'
          'tell me about ashwaganda' -> 'ashwaganda'
          'fadogia agrestis' -> 'fadogia agrestis'
    """
    q = raw_query.strip().strip("?.,!").strip()
    
    for pat in QUESTION_PREFIX_PATTERNS:
        match = re.search(pat, q, flags=re.IGNORECASE)
        if match:
            q = q[match.end():].strip()
            break

    # Strip trailing clauses
    trailing_patterns = [
        r"\s+(and\s+)?(what\s+does\s+it\s+do|how\s+to\s+take\s+it|how\s+to\s+use\s+it|how\s+does\s+it\s+work|dosage|dosing|benefits|side\s+effects|safety|works?|reviews?).*$",
        r"\s+for\s+(sleep|weight\s+loss|muscle|anxiety|energy|focus|fatigue|memory).*$"
    ]
    for tp in trailing_patterns:
        q = re.sub(tp, "", q, flags=re.IGNORECASE).strip()

    return q

def fuzzy_find_supplement_in_db(
    query_term: str,
    all_supplements: List[Dict[str, Any]],
    cutoff: float = 0.72
) -> Optional[Tuple[Dict[str, Any], float, bool]]:
    """
    Finds the best matching supplement from our database.
    Returns (supplement, score, is_typo).
    """
    normalized_term, typos = normalize_text_typos(query_term)
    is_spelling_mistake = len(typos) > 0
    
    q_clean = clean_token(normalized_term)
    if not q_clean or len(q_clean) < 3 or q_clean in STOP_WORDS:
        return None

    best_match = None
    best_score = 0.0

    for s in all_supplements:
        name = s["name"]
        slug = s["slug"]
        base_name = re.sub(r'\(.*?\)', '', name).strip()
        n_clean = clean_token(base_name)
        
        # 1. Exact match
        if q_clean == n_clean or q_clean == clean_token(slug):
            return (s, 1.0, is_spelling_mistake)

        # 2. Substring match (require substantial overlap)
        if len(q_clean) >= 4 and q_clean in n_clean:
            score = 0.90 + (len(q_clean) / max(len(n_clean), 1)) * 0.08
            if score > best_score:
                best_score = score
                best_match = s
            continue
        elif len(n_clean) >= 5 and n_clean in q_clean:
            score = 0.88
            if score > best_score:
                best_score = score
                best_match = s
            continue

        # 3. Parenthetical / botanical name match (e.g., Withania somnifera)
        alt_match = re.search(r'\((.*?)\)', name)
        if alt_match:
            alt_clean = clean_token(alt_match.group(1))
            if (len(q_clean) >= 4 and q_clean in alt_clean) or (len(alt_clean) >= 5 and alt_clean in q_clean):
                score = 0.92
                if score > best_score:
                    best_score = score
                    best_match = s
                continue

        # 4. SequenceMatcher against base name
        ratio = difflib.SequenceMatcher(None, q_clean, n_clean).ratio()
        if ratio > best_score and ratio >= 0.76:
            best_score = ratio
            best_match = s

        # 5. Token-level matcher with stop words filtered out
        s_tokens = [clean_token(w) for w in re.findall(r'[a-zA-Z0-9]+', base_name) if len(w) >= 4 and clean_token(w) not in STOP_WORDS]
        q_tokens = [clean_token(w) for w in re.findall(r'[a-zA-Z0-9]+', normalized_term) if len(w) >= 4 and clean_token(w) not in STOP_WORDS]
        for qt in q_tokens:
            for st in s_tokens:
                tok_ratio = difflib.SequenceMatcher(None, qt, st).ratio()
                if tok_ratio > 0.84 and tok_ratio * 0.88 > best_score:
                    best_score = tok_ratio * 0.88
                    best_match = s

    if best_match and best_score >= cutoff:
        if best_score < 0.98:
            is_spelling_mistake = True
        return (best_match, best_score, is_spelling_mistake)

    return None

def resolve_ingredient_for_ask_ai(
    raw_question: str,
    all_supplements: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Intelligently analyzes Ask AI question:
    1. Extracts candidate ingredient / compound.
    2. Corrects any spelling mistakes.
    3. Finds match in local database (876 items).
    4. If not found locally, queries PubChem & PubMed dynamically for unknown compounds.
    """
    from services.pubchem import get_compound_details
    from services.pubmed import search_pubmed_studies

    # Step 1: Normalize typos
    norm_question, typos_found = normalize_text_typos(raw_question)
    
    # Step 2: Extract candidate core term
    core_term = extract_core_ingredient_query(norm_question)
    if not core_term:
        core_term = norm_question

    clean_core = clean_token(core_term)

    # Step 3: If core_term is a stop word or trivial question, treat as general question
    if clean_core in STOP_WORDS or len(clean_core) < 2:
        return {
            "type": "general_question",
            "query": norm_question,
            "corrected_from": raw_question if typos_found else None
        }

    # Step 4: Try local DB match
    db_result = fuzzy_find_supplement_in_db(core_term, all_supplements)
    
    if db_result:
        supp, score, is_typo = db_result
        return {
            "type": "local_supplement",
            "supplement": supp,
            "canonical_name": supp["name"],
            "corrected_from": raw_question if (is_typo or typos_found) else None,
            "score": score
        }

    # Step 5: NOT in database -> Live PubChem & PubMed Lookup for this ingredient!
    logger.info(f"Ingredient '{core_term}' not found in local DB. Fetching PubChem/PubMed...")
    pubchem_info = get_compound_details(core_term)
    has_chemical_data = bool(pubchem_info.get("cid") or pubchem_info.get("description") or pubchem_info.get("formula"))
    
    pubmed_studies = search_pubmed_studies(core_term, max_results=4) if has_chemical_data else []

    if has_chemical_data or pubmed_studies:
        return {
            "type": "external_compound",
            "canonical_name": pubchem_info.get("name", core_term.title()),
            "pubchem": pubchem_info,
            "pubmed": pubmed_studies,
            "corrected_from": raw_question if typos_found else None
        }

    # Step 6: General question or symptom query
    return {
        "type": "general_question",
        "query": norm_question,
        "corrected_from": raw_question if typos_found else None
    }

def find_targeted_supplements_for_symptoms(
    symptoms_text: str,
    all_conditions: List[Dict[str, Any]],
    get_supp_by_slug_fn
) -> Tuple[str, List[Dict[str, Any]], List[str]]:
    """
    Identifies relevant conditions and target supplements for user's symptoms,
    handling misspellings and mapping root drivers.
    Returns: (corrected_text, targeted_supplements, identified_conditions)
    """
    corrected_text, _ = normalize_text_typos(symptoms_text)
    clean_symptoms = clean_token(corrected_text)
    
    target_slugs = set()
    matched_conditions = []

    # 1. Match against Conditions table
    for cond in all_conditions:
        c_name = cond["name"]
        c_clean = clean_token(c_name)
        
        # Check if condition name or key tokens appear in symptoms
        tokens = [clean_token(w) for w in re.findall(r'[a-zA-Z0-9]+', c_name) if len(w) > 3]
        is_matched = (c_clean in clean_symptoms) or any(t in clean_symptoms for t in tokens)
        
        if not is_matched:
            overview = cond.get("overview", "")
            tokens_in_symptoms = [clean_token(w) for w in re.findall(r'[a-zA-Z0-9]+', corrected_text) if len(w) > 3]
            overlap = [t for t in tokens_in_symptoms if t in overview.lower()]
            if len(overlap) >= 2:
                is_matched = True

        if is_matched:
            matched_conditions.append(c_name)
            t1 = cond.get("tier1_supplements", [])
            t2 = cond.get("tier2_supplements", [])
            for s in t1 + t2:
                if isinstance(s, dict) and s.get("slug"):
                    target_slugs.add(s["slug"])
                elif isinstance(s, str):
                    slug_str = re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
                    target_slugs.add(slug_str)

    # Core staples fallback if no specific condition matched
    if not target_slugs:
        target_slugs.update(["magnesium", "ashwagandha", "creatine-monohydrate", "vitamin-d", "omega-3-fatty-acids", "curcumin-curcuma-longa", "l-theanine", "coenzyme-q10"])

    targeted_supps = []
    for slug in list(target_slugs)[:8]:
        supp = get_supp_by_slug_fn(slug)
        if supp:
            targeted_supps.append(supp)

    return (corrected_text, targeted_supps, matched_conditions)
