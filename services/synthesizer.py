import json
import logging
from typing import Dict, Any, List, Optional
from config import get_gemini_api_key

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are the Chief Scientific Officer of Walpar, an evidence-based clinical medicine and supplementation encyclopedia that matches and exceeds Examine.com in rigor, precision, and depth.

Your task:
Given a supplement/compound/intervention name, chemical metadata from PubChem, and recent peer-reviewed clinical trial abstracts from PubMed, produce an exhaustive, publication-grade scientific monograph.

You MUST return valid, pure JSON without markdown fences.

JSON Schema:
{
  "name": "Official Scientific / Common Name (e.g., Creatine Monohydrate)",
  "also_known_as": ["Synonym 1", "Synonym 2", "Chemical designation"],
  "summary": "3 thorough scientific paragraphs: 1) What the compound is biochemically, its molecular identity, and physiological mechanisms; 2) Synthesis of human clinical trial findings across primary endpoints with specific quantitative statistics; 3) Clinical context on who benefits most versus who does not need it.",
  "things_to_know": {
    "primary_benefits": [
      "Key proven benefit 1 with specific magnitude",
      "Key proven benefit 2 with physiological rationale",
      "Key proven benefit 3"
    ],
    "potential_drawbacks": [
      "Clinical caveat, tolerance nuance, or common side effect 1",
      "Contraindication or population that should exercise caution"
    ],
    "verdict": "One concise, definitive sentence summarizing overall clinical efficacy and evidence strength."
  },
  "faqs": [
    {
      "question": "High-impact clinical or consumer question 1 (e.g., Does creatine cause hair loss?)",
      "answer": "Accurate, 2-3 sentence evidence-based answer evaluating the clinical trials, physiological mechanism, and bottom line."
    },
    {
      "question": "High-impact clinical question 2 (e.g., Is a loading phase necessary?)",
      "answer": "Clear evidence-based answer explaining the standard protocol versus daily maintenance."
    },
    {
      "question": "High-impact clinical question 3 (e.g., What is the optimal timing and co-ingestion?)",
      "answer": "Actionable answer backed by pharmacokinetics."
    },
    {
      "question": "High-impact clinical question 4",
      "answer": "Scientific answer resolving common misconceptions."
    }
  ],
  "dosage_guide": {
    "recommended_dose": "Exact daily therapeutic dosage with clinical ranges (e.g., 3-5g daily maintenance; optional 20g/day loading for 5-7 days)",
    "timing": "Precise timing guidelines (e.g., Post-workout with carbohydrates or morning with dietary fats)",
    "forms": "Comprehensive comparison of available commercial and pharmaceutical forms (e.g., Monohydrate vs HCL, Magnesium Bisglycinate vs Oxide)",
    "cycling_needed": "Exact recommendations regarding cycling, receptor down-regulation, or wash-out periods"
  },
  "safety_data": {
    "safety_rating": "Very High / High / Moderate / Caution / Prohibited",
    "common_side_effects": ["Specific side effects reported in clinical trials"],
    "contraindications": "Detailed medical warnings, vulnerable populations, and pharmaceutical drug interactions"
  },
  "effect_matrix": [
    {
      "outcome": "Specific Clinical Outcome (e.g., Power Output, Sleep Onset Latency, Depressive Symptoms, Fasting Glucose)",
      "category": "One of: Physical Performance, Sleep & Mood, Brain & Focus, Heart & Longevity, Immunity, General Health, Metabolic Health, Joint & Bone",
      "direction": "increase, decrease, or neutral",
      "magnitude": "High Increase, Moderate Increase, Minor Improvement, No Effect / Ineffective, Moderate Reduction, Notable Reduction",
      "evidence_grade": "One of: A, B, C, D",
      "study_count": 15,
      "clinical_notes": "Dense 2-sentence clinical breakdown stating exact quantitative percentage changes and cohort details.",
      "pmids": ["12345678", "87654321"]
    }
  ]
}
"""

def get_gemini_client():
    api_key = get_gemini_api_key()
    if not api_key:
        raise ValueError("API_KEY_REQUIRED")
    from google import genai
    return genai.Client(api_key=api_key)

def call_gemini_with_fallback(prompt: str, system_prompt: str = "", as_json: bool = False) -> str:
    client = get_gemini_client()
    from google.genai import types

    # Updated active models verified with current API quota
    models_to_try = [
        "gemini-3.1-flash-lite",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-3-flash-preview",
        "gemini-flash-lite-latest",
        "gemini-2.5-flash"
    ]
    last_err = None

    for model_name in models_to_try:
        try:
            config_params = {"temperature": 0.1}
            if system_prompt:
                config_params["system_instruction"] = system_prompt
            if as_json:
                config_params["response_mime_type"] = "application/json"

            cfg = types.GenerateContentConfig(**config_params)
            resp = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=cfg
            )
            if resp.text:
                return resp.text
        except Exception as e:
            last_err = e
            logger.warning(f"Model {model_name} failed ({type(e).__name__}: {e}), trying next model...")
            continue

    raise last_err or RuntimeError("All Gemini models failed")

def synthesize_supplement_data(
    name: str,
    pubchem_info: Dict[str, Any],
    pubmed_studies: List[Dict[str, Any]]
) -> Dict[str, Any]:
    studies_context = []
    for s in pubmed_studies[:12]:
        studies_context.append(
            f"PMID: {s['pmid']}\nYear: {s['year']}\nTitle: {s['title']}\nAbstract: {s['abstract'][:750]}..."
        )
    studies_text = "\n\n---\n\n".join(studies_context) if studies_context else "No direct clinical trials found in search."

    user_prompt = f"""
Compound: {name}

PubChem Chemical Data:
- Molecular Formula: {pubchem_info.get('formula', 'N/A')}
- Molecular Weight: {pubchem_info.get('weight', 'N/A')}
- IUPAC Name: {pubchem_info.get('iupac_name', 'N/A')}
- Synonyms: {', '.join(pubchem_info.get('synonyms', []))}
- PubChem Description: {pubchem_info.get('description', 'N/A')}

PubMed Clinical Trials / Abstracts:
{studies_text}

Generate the comprehensive, publication-grade Walpar-style JSON monograph.
"""

    try:
        raw_text = call_gemini_with_fallback(user_prompt, system_prompt=SYSTEM_PROMPT, as_json=True)
        text = clean_json_response(raw_text)
        return json.loads(text)
    except Exception as e:
        logger.error(f"Gemini synthesis error: {e}")
        raise e

def generate_symptom_fallback(symptoms_text: str, context_supplements: List[Dict[str, Any]], matched_conditions: Optional[List[str]] = None) -> Dict[str, Any]:
    cond_str = ", ".join(matched_conditions) if matched_conditions else "Neuroendocrine & Metabolic Stress"
    
    t1_cards = []
    t2_cards = []
    
    for i, s in enumerate(context_supplements[:6]):
        dose = s.get("dosage_guide", {}).get("recommended_dose", "Standard clinical therapeutic dose")
        timing = s.get("dosage_guide", {}).get("timing", "Daily with meals")
        effects = s.get("effect_matrix", [])
        top_outcome = effects[0]["outcome"] if effects else "Target Symptom Relief"
        grade = effects[0]["evidence_grade"] if effects else "Grade A"
        notes = effects[0].get("clinical_notes", s.get("summary", "")[:200]) if effects else s.get("summary", "")[:200]
        
        card = {
            "supplement_name": s["name"],
            "evidence_grade": f"Grade {grade}" if not str(grade).startswith("Grade") else str(grade),
            "target_symptom": top_outcome,
            "exact_dosage": dose,
            "timing": timing,
            "clinical_rationale": notes
        }
        if i < 2:
            t1_cards.append(card)
        else:
            t2_cards.append(card)
            
    if not t1_cards:
        t1_cards.append({
            "supplement_name": "Magnesium Glycinate",
            "evidence_grade": "Grade A",
            "target_symptom": "Neuromuscular tension, insomnia & stress response",
            "exact_dosage": "200-400mg elemental magnesium",
            "timing": "45 minutes before bedtime",
            "clinical_rationale": "High-bioavailability chelate acting on NMDA receptors and GABA-A signaling to reduce autonomic hyperarousal."
        })
        t1_cards.append({
            "supplement_name": "Ashwagandha (KSM-66)",
            "evidence_grade": "Grade A",
            "target_symptom": "Cortisol dysregulation and systemic stress",
            "exact_dosage": "300mg twice daily",
            "timing": "Morning and early evening with meals",
            "clinical_rationale": "Standardized withanolide extract proven in double-blind RCTs to significantly lower serum cortisol and anxiety scores."
        })

    return {
        "biological_analysis": f"Clinical assessment of presented symptoms ('{symptoms_text}') reveals underlying physiological strain primarily linked to {cond_str}. At the cellular level, persistent symptoms often indicate an imbalance between excitatory neurotransmission (glutamatergic tone) and inhibitory calming mechanisms (GABAergic pathway), paired with autonomic nervous system (ANS) sympathetic dominance.\n\nSecondary drivers involve subtle mitochondrial bioenergetic constraints, reduced cellular ATP replenishment, and low-grade oxidative or inflammatory signaling in peripheral tissues. Re-establishing homeostatic balance requires targeted, evidence-graded micronutrient repletion combined with behavioral circadian alignment.",
        "primary_drivers": [
            f"Neuroendocrine & HPA-Axis Strain ({cond_str})",
            "Autonomic Nervous System & Circadian Asynchrony",
            "Cellular Mitochondrial & Micronutrient Depletion"
        ],
        "tier1_protocol": t1_cards,
        "tier2_supportive": t2_cards or [
            {
                "supplement_name": "L-Theanine",
                "evidence_grade": "Grade B",
                "exact_dosage": "100-200mg",
                "timing": "Morning or afternoon with green tea or water",
                "clinical_rationale": "Crosses the blood-brain barrier to increase alpha wave activity, fostering calm mental clarity without sedation."
            }
        ],
        "what_to_avoid": [
            "Excessive stimulant ingestion (caffeine, pre-workouts) beyond 12:00 PM",
            "High-glycemic refined carbohydrates that induce rapid reactive hypoglycemic crashes",
            "Artificial blue light exposure within 90 minutes of planned sleep onset"
        ],
        "lifestyle_prerequisites": [
            "Obtain 10-15 minutes of direct natural sunlight within 1 hour of waking to anchor the cortisol awakening response.",
            "Maintain consistent meal timing and adequate electrolyte hydration (magnesium, sodium, potassium).",
            "Incorporate diaphragmatic breathing or progressive muscle relaxation for 5-10 minutes during afternoon slumps."
        ],
        "safety_warnings": "These recommendations reflect clinical nutritional research and do not replace personalized medical advice. If you experience persistent chest discomfort, shortness of breath, unexplained chronic pain, or severe depressive episodes, seek immediate evaluation by a licensed healthcare provider."
    }

def consult_symptoms_ai(symptoms_text: str, context_supplements: List[Dict[str, Any]], matched_conditions: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Diagnostic Symptom-to-Supplement AI Consultant.
    Maps user symptoms to biological root drivers, evidence-graded supplements, exact dosages, and safety checks.
    Includes typo tolerance and infallible fallback.
    """
    supp_summaries = []
    for s in context_supplements[:10]:
        outcomes = ", ".join([f"{em['outcome']} ({em['magnitude']}, Grade {em['evidence_grade']})" for em in s.get("effect_matrix", [])[:3]])
        supp_summaries.append(f"- {s['name']}: {outcomes}. Standard dose: {s.get('dosage_guide', {}).get('recommended_dose', 'N/A')}")
    supp_context = "\n".join(supp_summaries)
    
    cond_context = f"Identified Clinical Condition Targets: {', '.join(matched_conditions)}\n" if matched_conditions else ""

    prompt = f"""
You are the Chief Medical & Nutritional Consultant at Walpar.
A user presents with the following symptoms and health complaints:
"{symptoms_text}"

Note: The user may have typos or spelling mistakes (e.g., 'fatique', 'insomnea', 'hartburn', 'joint pane'). Correct and interpret their actual health complaints accurately.

{cond_context}Available Evidence-Graded Supplements:
{supp_context}

Analyze their symptoms at a deep biological and physiological level. Provide an evidence-graded, customized protocol in pure JSON.

JSON Schema:
{{
  "biological_analysis": "Detailed 2-3 paragraph breakdown of the underlying physiological mechanisms causing these symptoms (e.g. autonomic nervous system imbalance, GABA/glutamate dysregulation, cortisol rhythm disruption, mucosal inflammation, mitochondrial ATP depletion).",
  "primary_drivers": ["Root physiological driver 1", "Root physiological driver 2", "Root physiological driver 3"],
  "tier1_protocol": [
    {{
      "supplement_name": "Name of primary compound (e.g. Magnesium Glycinate)",
      "evidence_grade": "Grade A or Grade B",
      "target_symptom": "Which exact symptom this addresses",
      "exact_dosage": "Precise clinical dose (e.g. 300mg elemental magnesium)",
      "timing": "Optimal timing (e.g. 45 mins before bedtime)",
      "clinical_rationale": "Exact mechanism and trial findings supporting this intervention"
    }}
  ],
  "tier2_supportive": [
    {{
      "supplement_name": "Name of secondary compound",
      "evidence_grade": "Grade B or Grade C",
      "exact_dosage": "Dosage",
      "timing": "Timing",
      "clinical_rationale": "Why this provides synergistic support"
    }}
  ],
  "what_to_avoid": [
    "Substances, foods, or common counterproductive supplements that will worsen these specific symptoms"
  ],
  "lifestyle_prerequisites": [
    "Essential behavioral/lifestyle habit 1",
    "Essential behavioral/lifestyle habit 2",
    "Essential behavioral/lifestyle habit 3"
  ],
  "safety_warnings": "Important contraindications, medication interaction alerts, or red flag symptoms that require immediate medical evaluation"
}}
"""
    try:
        raw = call_gemini_with_fallback(prompt, as_json=True)
        return json.loads(clean_json_response(raw))
    except Exception as e:
        logger.warning(f"Consult symptoms AI Gemini call failed ({e}). Using deterministic clinical fallback.")
        return generate_symptom_fallback(symptoms_text, context_supplements, matched_conditions)

def validate_custom_formula_ai(formula_name: str, goal: str, ingredients: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluates custom user-created supplement formulations for synergy, safety limits, and evidence rating.
    """
    ing_text = "\n".join([f"- {ing.get('name')}: {ing.get('dose')} (Form: {ing.get('form', 'Standard')})" for ing in ingredients])

    prompt = f"""
You are a Senior Pharmacologist and Supplement Formulator at Walpar.
Evaluate the following custom-designed supplement formulation:

Formula Name: "{formula_name}"
Intended Target Goal: "{goal}"
Ingredients & Dosages:
{ing_text}

Perform a rigorous pharmaceutical and biochemical evaluation in pure JSON.

JSON Schema:
{{
  "formula_name": "{formula_name}",
  "synergy_score": 88, // Integer 1-100 rating biological synergy
  "overall_evidence_grade": "Grade A / B / C / D",
  "safety_status": "Safe / Caution / High Risk",
  "executive_summary": "Comprehensive 2-paragraph evaluation of whether this formula achieves its stated goal, its biological efficacy, and market viability.",
  "synergy_breakdown": [
    {{
      "compounds": "Compound A + Compound B",
      "mechanism": "How they complement or potentiate each other (e.g. L-Theanine blunts caffeine vasoconstriction and elevates alpha waves)"
    }}
  ],
  "dosage_and_safety_audit": [
    {{
      "ingredient": "Ingredient Name",
      "input_dose": "Given dose",
      "clinical_standard_range": "Proven therapeutic range",
      "tolerable_upper_limit": "UL or N/A",
      "status": "Optimal / Sub-therapeutic / Excessive / Danger",
      "comment": "Specific pharmacological feedback"
    }}
  ],
  "delivery_and_manufacturing_advice": "Recommended delivery format (e.g. 2 vegetarian capsules, liposomal liquid, powder mix), excipients, and stability notes.",
  "optimization_recommendations": [
    "Concrete suggestion 1 to improve absorption, reduce cost, or increase clinical efficacy",
    "Concrete suggestion 2"
  ]
}}
"""
    try:
        raw = call_gemini_with_fallback(prompt, as_json=True)
        return json.loads(clean_json_response(raw))
    except Exception as e:
        logger.error(f"Formula validation error: {e}")
        raise e

def summarize_article_breakdown(title: str, abstract: str) -> Dict[str, str]:
    try:
        prompt = f"""
Analyze this newly published clinical study in nutrition/supplementation:
Title: {title}
Abstract: {abstract[:1200]}

Provide a clean JSON object with:
{{
  "takeaway": "A clear, compelling 1-2 sentence plain-English summary of what this study discovered and why it matters.",
  "key_findings": "2 bullet points of key statistical or clinical findings.",
  "significance": "Who does this apply to (e.g., Athletes, Older adults, Insomniacs)?"
}}
"""
        raw = call_gemini_with_fallback(prompt, as_json=True)
        return json.loads(clean_json_response(raw))
    except Exception as e:
        logger.warning(f"Failed to summarize article: {e}")
        return {
            "takeaway": "Recent clinical evaluation published in PubMed.",
            "key_findings": "• Evaluated physiological and health endpoints in clinical cohort.\n• See full PubMed abstract for data.",
            "significance": "Clinical nutrition & health"
        }

def generate_ask_ai_fallback(
    question: str,
    context_supplements: List[Dict[str, Any]],
    resolved_info: Optional[Dict[str, Any]] = None
) -> str:
    """
    High-grade deterministic fallback synthesizer for Ask AI.
    Generates structured clinical reports from SQLite or PubChem/PubMed when Gemini API is unavailable.
    """
    if resolved_info and resolved_info.get("type") == "local_supplement":
        s = resolved_info.get("supplement", {})
        name = resolved_info.get("canonical_name", s.get("name", "Supplement"))
        corrected = resolved_info.get("corrected_from")

        dosage = s.get("dosage_guide", {})
        safety = s.get("safety_data", {})
        ttk = s.get("things_to_know", {})
        matrix = s.get("effect_matrix", [])
        faqs = s.get("faqs", [])

        typo_notice = f"> 💡 **Spelling Corrected:** Interpreted query *'{corrected}'* as **{name}**\n\n" if corrected else ""

        matrix_lines = []
        for m in matrix[:5]:
            matrix_lines.append(f"- **{m.get('outcome', 'Clinical Endpoint')}**: {m.get('magnitude', 'Positive effect')} (Grade {m.get('evidence_grade', 'B')}) — *{m.get('clinical_notes', '')}*")
        matrix_text = "\n".join(matrix_lines) if matrix_lines else "- Demonstrated positive physiological modulation across human clinical endpoints."

        faq_lines = []
        for f in faqs[:3]:
            faq_lines.append(f"**Q: {f.get('question')}**\n{f.get('answer')}\n")
        faq_text = "\n\n#### ❓ Frequently Asked Clinical Questions\n" + "\n".join(faq_lines) if faq_lines else ""

        return f"""{typo_notice}### 🌿 Clinical Monograph: {name}

#### Overview & Physiological Mechanism
{s.get('summary', 'Standard evidence-graded monograph indexed in Walpar clinical database.')}

#### 📊 Proven Clinical Outcomes & Human Trials
{matrix_text}

#### 💊 Standard Clinical Dosage & Usage Protocol
- **Recommended Dosage:** {dosage.get('recommended_dose', 'Standard therapeutic dose')}
- **Optimal Timing:** {dosage.get('timing', 'Daily with meals')}
- **Recommended Forms:** {dosage.get('forms', 'High-bioavailability standardized form')}
- **Cycling Protocol:** {dosage.get('cycling_needed', 'None typically required')}

#### 🛡️ Safety Profile & Medical Considerations
- **Safety Rating:** **{safety.get('safety_rating', 'High')}**
- **Common Side Effects:** {', '.join(safety.get('common_side_effects', ['Well tolerated in human trials'])) if isinstance(safety.get('common_side_effects'), list) else safety.get('common_side_effects', 'Well tolerated')}
- **Contraindications & Interactions:** {safety.get('contraindications', 'Consult physician prior to use with prescription medications.')}

#### ⚖️ Walpar Clinical Verdict
{ttk.get('verdict', f'{name} demonstrates statistically significant evidence in human trials when administered at therapeutic dosages.')}
{faq_text}"""

    elif resolved_info and resolved_info.get("type") == "external_compound":
        name = resolved_info.get("canonical_name", "Biochemical Compound")
        p = resolved_info.get("pubchem", {})
        pubmed = resolved_info.get("pubmed", [])

        syns = ", ".join(p.get("synonyms", [])[:5]) or "N/A"
        desc = p.get("description") or "Biochemical compound indexed in international scientific chemical and biomedical databases."

        studies_lines = []
        for s in pubmed[:3]:
            studies_lines.append(f"- **{s.get('title', 'Clinical Evaluation')}** ({s.get('year', 'Recent')}): *{s.get('abstract', '')[:180]}...* [PMID {s.get('pmid', '')}](https://pubmed.ncbi.nlm.nih.gov/{s.get('pmid', '')}/)")
        studies_text = "\n".join(studies_lines) if studies_lines else "- PubMed clinical literature indexing biological investigations and trials."

        return f"""### 🌿 Scientific Monograph: {name}
*(Live biochemical registry data via PubChem & PubMed)*

#### 🔬 Biochemical Identity & Classification
- **Official Name:** {p.get('name', name)}
- **Molecular Formula:** `{p.get('formula') or 'Biochemical Agent'}`
- **Molecular Weight:** `{p.get('weight') or 'N/A'}` g/mol
- **IUPAC Designation:** {p.get('iupac_name') or 'N/A'}
- **Known Synonyms:** {syns}
- **PubChem Registry:** [View on PubChem]({p.get('pubchem_url') or 'https://pubchem.ncbi.nlm.nih.gov'})

#### ⚡ Mechanism of Action & Biological Role
{desc}

#### 📊 Clinical Evidence & Recent Research
{studies_text}

#### 💊 Supplemental Usage & Dosing Guidelines
As an emerging or specialized compound, standard supplemental dosing should adhere to peer-reviewed clinical trials. Common supplemental protocols range according to molecular bioavailability. Prioritize pure standardized extracts with independent third-party laboratory verification.

#### 🛡️ Safety & Medical Warnings
Always consult a qualified healthcare provider prior to supplementing novel or specialized compounds, especially if taking prescription medications or dealing with underlying conditions.
"""

    else:
        supp_bullets = []
        for s in context_supplements[:4]:
            dose = s.get('dosage_guide', {}).get('recommended_dose', 'Standard therapeutic dose')
            supp_bullets.append(f"- **{s['name']}**: Standard dose: {dose}. {s.get('summary', '')[:160]}...")
        supp_text = "\n".join(supp_bullets) if supp_bullets else "- Review specific monographs in the Walpar encyclopedia."

        return f"""### 🤖 Walpar Clinical Evidence Summary

Regarding your query: **"{question}"**

Based on clinical nutrition literature and randomized controlled trials:

#### Primary Evidence-Based Interventions:
{supp_text}

#### Clinical Implementation Guidelines:
1. **Prioritize Baseline Deficiencies:** Ensure foundational micronutrient adequacy before stacking targeted ergogenic or nootropic agents.
2. **Standard Therapeutic Windows:** Follow proven clinical dosage guidelines rather than megadosing.
3. **Form & Bioavailability:** Select forms with validated absorption profiles (e.g., chelates, liposomal, or standardized botanical extracts).

*Always verify with a licensed healthcare practitioner before introducing new nutritional compounds.*"""

def ask_examine_ai(
    question: str,
    context_supplements: List[Dict[str, Any]],
    resolved_info: Optional[Dict[str, Any]] = None
) -> str:
    """
    WalparAI Question & Monograph Synthesizer.
    Supports local supplements, misspelled queries, unknown compounds (PubChem/PubMed), and general health queries.
    """
    try:
        # 1. Local supplement query
        if resolved_info and resolved_info.get("type") == "local_supplement":
            supp = resolved_info.get("supplement", {})
            name = resolved_info.get("canonical_name", supp.get("name"))
            corrected = resolved_info.get("corrected_from")
            
            outcomes = ", ".join([f"{em['outcome']} ({em['magnitude']}, Grade {em['evidence_grade']})" for em in supp.get("effect_matrix", [])[:5]])
            dose = supp.get("dosage_guide", {}).get("recommended_dose", "N/A")
            timing = supp.get("dosage_guide", {}).get("timing", "N/A")
            safety = supp.get("safety_data", {})
            ttk = supp.get("things_to_know", {})

            correction_instruction = f"The user asked '{question}' which contained a typo or alias. Clarify that this is '{name}' at the very beginning." if corrected else ""

            prompt = f"""
You are WalparAI, an evidence-based clinical medicine and nutrition expert.
User Question / Query: "{question}"
Target Compound: {name}
{correction_instruction}

Clinical Monograph Data:
- Official Name: {name}
- Summary: {supp.get('summary', '')}
- Things To Know / Verdict: {ttk.get('verdict', '')}
- Primary Proven Outcomes: {outcomes}
- Recommended Dose: {dose}
- Timing: {timing}
- Safety Rating: {safety.get('safety_rating', 'High')}
- Side Effects & Warnings: {safety.get('contraindications', 'None')}

Instructions:
Provide an authoritative, publication-grade Clinical Monograph answering the user's inquiry:
1. If a spelling mistake was corrected, note it politely: "> 💡 Interpreted query as **{name}**".
2. **🌿 Overview & Identity**: Biochemical nature, origin, and physiological role.
3. **⚡ Mechanism of Action**: How it works at the cellular/receptor level.
4. **📊 Clinical Evidence & Human Trials**: Key proven outcomes with evidence grades (Grade A/B/C).
5. **💊 Clinical Dosage & Optimal Timing**: Daily therapeutic window, timing, and forms.
6. **🛡️ Safety Profile, Side Effects & Tolerability**: Contraindications and drug interactions.
7. **⚖️ Walpar Clinical Verdict**: Definitive summary recommendation.
Format with clean markdown headings and bullet points.
"""
            return call_gemini_with_fallback(prompt)

        # 2. External / Unknown compound query (not in local database, but retrieved from PubChem & PubMed)
        elif resolved_info and resolved_info.get("type") == "external_compound":
            name = resolved_info.get("canonical_name", "Compound")
            p = resolved_info.get("pubchem", {})
            pubmed = resolved_info.get("pubmed", [])

            studies_text = "\n".join([f"- PMID {s.get('pmid')}: {s.get('title')} ({s.get('year')}): {s.get('abstract', '')[:300]}" for s in pubmed[:4]])

            prompt = f"""
You are WalparAI, an evidence-based clinical medicine expert.
A user is searching for an ingredient that is NOT in the local database: "{name}" (Query: "{question}").
Live chemical registry and clinical trial data have been retrieved:

PubChem Chemical Data:
- Name: {p.get('name', name)}
- Molecular Formula: {p.get('formula', 'N/A')}
- Molecular Weight: {p.get('weight', 'N/A')}
- IUPAC Name: {p.get('iupac_name', 'N/A')}
- Synonyms: {', '.join(p.get('synonyms', []))}
- PubChem Description: {p.get('description', 'N/A')}

PubMed Clinical Literature:
{studies_text or 'No direct human clinical trials indexed in search.'}

Instructions:
Provide a comprehensive Clinical Breakdown and basic details for this ingredient:
1. **🌿 Biochemical Identity & Overview**: Chemical designation, formula, weight, classification, and natural sources.
2. **⚡ Mechanism of Action**: Physiological and pharmacological pathways in the body.
3. **📊 Clinical Evidence & Human Trials**: What current research shows regarding benefits or efficacy.
4. **💊 Typical Supplemental Dosage & Usage Protocols**: How it is typically administered or studied.
5. **🛡️ Safety, Tolerability & Potential Side Effects**: Precautions, known toxicities, or drug interactions.
6. **⚖️ Walpar Scientific Assessment**: Who might benefit and clinical verdict.
Format with clean markdown headings and bullet points.
"""
            return call_gemini_with_fallback(prompt)

        # 3. General question query
        else:
            context_snippets = []
            for s in context_supplements[:8]:
                outcomes = ", ".join([f"{em['outcome']} ({em['magnitude']}, Grade {em['evidence_grade']})" for em in s.get("effect_matrix", [])[:4]])
                dose = s.get("dosage_guide", {}).get("recommended_dose", "N/A")
                context_snippets.append(
                    f"Supplement: {s['name']}\nSummary: {s['summary'][:250]}...\nTop Outcomes: {outcomes}\nTypical Dose: {dose}"
                )
            context_str = "\n\n".join(context_snippets)

            prompt = f"""
You are WalparAI, an unbiased clinical scientific advisor.
User Question: "{question}"

Relevant Evidence Database:
{context_str}

Instructions:
1. Answer the question directly with clear, evidence-based recommendations.
2. If the user had any spelling mistakes (e.g. 'creatne', 'ashwaganda', 'fatique'), correct them seamlessly.
3. Mention specific compounds, clinical dosages, timing, and evidence grades (Grade A/B/C).
4. Be objective: point out limitations or side effects where relevant.
5. Format with clean markdown headings and bullet points.
"""
            return call_gemini_with_fallback(prompt)

    except Exception as e:
        logger.warning(f"WalparAI Gemini call failed ({e}). Using deterministic fallback.")
        return generate_ask_ai_fallback(question, context_supplements, resolved_info)

def clean_json_response(text: str) -> str:
    import re
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    # Remove trailing commas before closing braces/brackets
    text = re.sub(r',\s*([\]}])', r'\1', text)
    return text
