from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import re

import json
import asyncio
import config
import database
from services.pubchem import get_compound_details
from services.pubmed import search_pubmed_studies, get_latest_research_feed
from services.clinicaltrials import search_clinical_trials
from services.synthesizer import (
    synthesize_supplement_data,
    summarize_article_breakdown,
    ask_examine_ai,
    consult_symptoms_ai,
    validate_custom_formula_ai
)
from services.search_matcher import (
    resolve_ingredient_for_ask_ai,
    normalize_text_typos,
    find_targeted_supplements_for_symptoms
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("walpar-app")

app = FastAPI(title="Walpar - Evidence-Based Clinical Nutrition Platform")

@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static/") or request.url.path == "/":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize schema and seed data
database.init_db()

class ApiKeyPayload(BaseModel):
    api_key: str
    ncbi_key: str = ""

class AskAiPayload(BaseModel):
    question: str

class AnalyzePayload(BaseModel):
    name: str

class SymptomConsultPayload(BaseModel):
    symptoms: str

class FormulaIngredient(BaseModel):
    name: str
    dose: str
    form: Optional[str] = "Standard"

class ValidateFormulaPayload(BaseModel):
    name: str
    goal: str
    target_user: Optional[str] = "Adults"
    ingredients: List[FormulaIngredient]

class SaveFormulaPayload(BaseModel):
    name: str
    goal: str
    target_user: Optional[str] = "Adults"
    ingredients: List[Dict[str, Any]]
    synergy_score: int
    safety_rating: str
    evidence_grade: str
    analysis_report: Dict[str, Any]

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[-\s]+', '-', text)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    response = templates.TemplateResponse("index.html", {"request": request})
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/api/status")
async def get_status():
    gemini_key = config.get_gemini_api_key()
    ncbi_key = config.get_ncbi_api_key()
    return {
        "has_api_key": bool(gemini_key),
        "has_ncbi_key": bool(ncbi_key),
        "gemini_preview": f"{gemini_key[:6]}...{gemini_key[-4:]}" if len(gemini_key) > 10 else ("Set" if gemini_key else "Not Set"),
        "ncbi_preview": f"{ncbi_key[:4]}...{ncbi_key[-4:]}" if len(ncbi_key) > 8 else ("Set" if ncbi_key else "Not Set")
    }

@app.post("/api/settings/apikey")
async def save_api_key(payload: ApiKeyPayload):
    if payload.api_key:
        config.set_gemini_api_key(payload.api_key.strip())
    if payload.ncbi_key:
        config.set_ncbi_api_key(payload.ncbi_key.strip())
    return {"status": "success", "message": "API keys saved successfully!"}

# =======================================================================
# 1. Supplements Endpoints
# =======================================================================
def is_stub_supplement(supp: Optional[Dict[str, Any]]) -> bool:
    if not supp:
        return True
    summary = supp.get("summary", "")
    if "indexed in the clinical literature for its physiological" in summary:
        return True
    studies = supp.get("studies", [])
    if not studies or len(studies) == 0:
        return True
    matrix = supp.get("effect_matrix", [])
    if any(m.get("outcome") == "Biochemical & Physiological Markers" for m in matrix):
        return True
    dose = supp.get("dosage_guide", {})
    if "Consult clinical monograph" in str(dose):
        return True
    ttk = supp.get("things_to_know")
    if not ttk or not ttk.get("verdict"):
        return True
    faqs = supp.get("faqs")
    if not faqs or len(faqs) == 0:
        return True
    return False

def _sync_run_supplement_synthesis(
    name: str,
    slug: str,
    item_type: str = "supplements",
    letter_index: Optional[str] = None
) -> Dict[str, Any]:
    pubchem_info = get_compound_details(name)
    studies = search_pubmed_studies(name, max_results=12)
    clinical_trials = search_clinical_trials(name, max_results=5)

    synth = synthesize_supplement_data(name, pubchem_info, studies)
    official_name = synth.get("name", name.title())
    
    database.save_supplement_data(
        slug=slug,
        name=official_name,
        summary=synth.get("summary", ""),
        pubchem_data=pubchem_info,
        dosage_guide=synth.get("dosage_guide", {}),
        safety_data=synth.get("safety_data", {}),
        effect_matrix=synth.get("effect_matrix", []),
        studies=studies,
        clinical_trials=clinical_trials,
        item_type=item_type,
        letter_index=letter_index,
        faqs=synth.get("faqs", []),
        things_to_know=synth.get("things_to_know", {})
    )
    return database.get_supplement_by_slug(slug)

async def run_supplement_synthesis(
    name: str,
    slug: Optional[str] = None,
    item_type: str = "supplements",
    letter_index: Optional[str] = None
) -> Dict[str, Any]:
    if not slug:
        slug = slugify(name)
    return await asyncio.to_thread(_sync_run_supplement_synthesis, name, slug, item_type, letter_index)

@app.get("/api/supplements")
async def list_supplements(letter: Optional[str] = None, type: Optional[str] = None):
    return database.get_all_supplements(letter=letter, item_type=type)

@app.get("/api/supplement/{slug}")
async def get_supplement(slug: str):
    supp = database.get_supplement_by_slug(slug)
    if supp:
        return supp
    
    # If not in database, attempt live synthesis if API key is provided
    if config.get_gemini_api_key():
        return await trigger_analysis(AnalyzePayload(name=slug.replace("-", " ")))
    
    raise HTTPException(status_code=404, detail=f"Supplement '{slug}' not found.")

@app.post("/api/supplement/{slug}/resynthesize")
async def resynthesize_supplement(slug: str):
    supp = database.get_supplement_by_slug(slug)
    name = supp["name"] if supp else slug.replace("-", " ").title()
    return await run_supplement_synthesis(name, slug=slug)

@app.get("/api/clinicaltrials/{query}")
async def get_clinical_trials_endpoint(query: str):
    return search_clinical_trials(query, max_results=8)

@app.post("/api/supplement/analyze")
async def trigger_analysis(payload: AnalyzePayload):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Supplement name is required")

    slug = slugify(name)
    existing = database.get_supplement_by_slug(slug)
    if existing and not is_stub_supplement(existing):
        return existing

    if not config.get_gemini_api_key():
        raise HTTPException(status_code=400, detail="Gemini API Key is required to analyze new supplements.")

    logger.info(f"Synthesizing monograph for {name}...")
    try:
        return await run_supplement_synthesis(name, slug=slug)
    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to synthesize research: {str(e)}")

# =======================================================================
# 2. Conditions Endpoints
# =======================================================================
@app.get("/api/conditions")
async def get_conditions():
    return database.get_all_conditions()

@app.get("/api/condition/{slug}")
async def get_condition(slug: str):
    cond = database.get_condition_by_slug(slug)
    if not cond:
        raise HTTPException(status_code=404, detail=f"Condition '{slug}' not found.")
    return cond

# =======================================================================
# 3. Categories Endpoints
# =======================================================================
@app.get("/api/categories")
async def get_categories():
    return database.get_all_categories()

@app.get("/api/category/{category_name}")
async def get_category(category_name: str):
    return database.get_category_outcomes(category_name)

# =======================================================================
# 4. Guides Endpoints
# =======================================================================
@app.get("/api/guides")
async def get_guides():
    return database.get_all_guides()

@app.get("/api/guide/{slug}")
async def get_guide(slug: str):
    guide = database.get_guide_by_slug(slug)
    if not guide:
        raise HTTPException(status_code=404, detail=f"Guide '{slug}' not found.")
    return guide

# =======================================================================
# 5. Symptom-to-Supplement AI Consultant
# =======================================================================
@app.post("/api/consult/symptoms")
async def consult_symptoms(payload: SymptomConsultPayload):
    text = payload.symptoms.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Symptoms description is required.")

    all_conditions = database.get_all_conditions()
    corrected_text, targeted_supps, matched_conditions = find_targeted_supplements_for_symptoms(
        text,
        all_conditions,
        database.get_supplement_by_slug
    )

    try:
        report = consult_symptoms_ai(corrected_text, targeted_supps, matched_conditions)
        if corrected_text.lower() != text.lower():
            report["corrected_symptoms"] = corrected_text
        return report
    except Exception as e:
        logger.error(f"Symptom consult failed: {e}")
        from services.synthesizer import generate_symptom_fallback
        return generate_symptom_fallback(corrected_text, targeted_supps, matched_conditions)

# =======================================================================
# 6. Custom Supplement Formulator & Stack Builder
# =======================================================================
@app.post("/api/formulator/validate")
async def validate_formula(payload: ValidateFormulaPayload):
    if not payload.ingredients:
        raise HTTPException(status_code=400, detail="At least one ingredient is required.")
    
    if not config.get_gemini_api_key():
        raise HTTPException(status_code=400, detail="Gemini API key is required to validate custom formulas.")

    ing_dicts = [{"name": i.name, "dose": i.dose, "form": i.form} for i in payload.ingredients]
    try:
        eval_result = validate_custom_formula_ai(payload.name, payload.goal, ing_dicts)
        return eval_result
    except Exception as e:
        logger.error(f"Formulator validation error: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@app.post("/api/formulator/save")
async def save_formula(payload: SaveFormulaPayload):
    formula_id = database.save_custom_formula(payload.model_dump())
    return {"status": "success", "id": formula_id}

@app.get("/api/formulator/list")
async def list_formulas():
    return database.get_custom_formulas()

# =======================================================================
# 7. Live Research Feed & AI Chat
# =======================================================================
@app.get("/api/feed/latest")
async def get_latest_feed(topic: str = "all", refresh: bool = False):
    cached = database.get_recent_articles(topic, limit=12)
    if cached and not refresh:
        return cached

    raw_articles = get_latest_research_feed(topic, max_results=8)
    processed = []

    for i, art in enumerate(raw_articles):
        if i < 4 and config.get_gemini_api_key() and art.get("abstract"):
            try:
                summary_data = summarize_article_breakdown(art["title"], art["abstract"])
                art["takeaway"] = summary_data.get("takeaway", "")
                art["key_findings"] = summary_data.get("key_findings", "")
                art["significance"] = summary_data.get("significance", "")
            except Exception:
                art["takeaway"] = "Clinical trial published in PubMed."
        else:
            art["takeaway"] = art["abstract"][:200] + "..." if art.get("abstract") else "See study details on PubMed."
            art["key_findings"] = ""
            art["significance"] = ""
        processed.append(art)

    if processed:
        database.save_recent_articles(processed, topic=topic)

    return database.get_recent_articles(topic, limit=12)

@app.post("/api/ai/ask")
async def ask_assistant(payload: AskAiPayload):
    q = payload.question.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    all_supps = database.get_all_supplements()
    all_conditions = database.get_all_conditions()

    resolved = resolve_ingredient_for_ask_ai(q, all_supps)
    
    targeted_supps = []
    if resolved["type"] == "local_supplement":
        enriched = database.get_supplement_by_slug(resolved["supplement"]["slug"])
        if enriched:
            resolved["supplement"] = enriched
            targeted_supps = [enriched]
    elif resolved["type"] == "external_compound":
        comp_name = resolved.get("canonical_name", q.title())
        slug = slugify(comp_name)
        if not database.get_supplement_by_slug(slug):
            p = resolved.get("pubchem", {})
            pubmed = resolved.get("pubmed", [])
            desc = p.get("description") or f"Biochemical compound ({comp_name}) indexed in PubChem with molecular formula {p.get('formula', 'N/A')}."
            database.save_supplement_data(
                slug=slug,
                name=comp_name,
                summary=desc,
                pubchem_data=p,
                dosage_guide={"recommended_dose": "Refer to clinical trial monographs", "timing": "Daily with meals", "forms": "Standard standardized extract"},
                safety_data={"safety_rating": "Moderate / Consult Physician", "common_side_effects": [], "contraindications": "Consult healthcare practitioner prior to supplementation."},
                effect_matrix=[{"outcome": "Biochemical Modulation", "category": "General Health", "magnitude": "Under Clinical Investigation", "evidence_grade": "B", "study_count": len(pubmed), "clinical_notes": "Indexed in PubChem and PubMed clinical trial databases."}],
                studies=pubmed,
                item_type="supplements",
                things_to_know={"verdict": f"{comp_name} is an active biochemical compound with ongoing clinical and pharmacological investigations."},
                faqs=[{"question": f"What is {comp_name}?", "answer": desc[:250]}]
            )
            database._SUPPLEMENTS_CACHE = None
    else:
        # General question -> find relevant supplements from symptoms/conditions/outcomes
        _, targeted_supps, _ = find_targeted_supplements_for_symptoms(
            q,
            all_conditions,
            database.get_supplement_by_slug
        )

    try:
        answer = ask_examine_ai(q, targeted_supps, resolved_info=resolved)
        return {
            "answer": answer,
            "resolved": {
                "type": resolved["type"],
                "canonical_name": resolved.get("canonical_name"),
                "corrected_from": resolved.get("corrected_from")
            }
        }
    except Exception as e:
        logger.error(f"Ask AI failed: {e}")
        from services.synthesizer import generate_ask_ai_fallback
        fallback_ans = generate_ask_ai_fallback(q, targeted_supps, resolved)
        return {
            "answer": fallback_ans,
            "resolved": {
                "type": resolved["type"],
                "canonical_name": resolved.get("canonical_name"),
                "corrected_from": resolved.get("corrected_from")
            }
        }

@app.get("/api/search")
async def search(q: str = ""):
    if not q:
        return []
    return database.search_database(q)

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
