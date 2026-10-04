import sqlite3
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

DB_PATH = Path(__file__).parent / "examine.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Supplements Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS supplements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            summary TEXT NOT NULL,
            pubchem_data TEXT,
            dosage_guide TEXT,
            safety_data TEXT,
            clinical_trials TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Migration: Ensure clinical_trials, item_type, letter_index, faqs, and things_to_know exist
        cursor.execute("PRAGMA table_info(supplements)")
        existing_cols = [c[1] for c in cursor.fetchall()]
        if "clinical_trials" not in existing_cols:
            cursor.execute("ALTER TABLE supplements ADD COLUMN clinical_trials TEXT")
        if "item_type" not in existing_cols:
            cursor.execute("ALTER TABLE supplements ADD COLUMN item_type TEXT DEFAULT 'supplements'")
        if "letter_index" not in existing_cols:
            cursor.execute("ALTER TABLE supplements ADD COLUMN letter_index TEXT")
        if "faqs" not in existing_cols:
            cursor.execute("ALTER TABLE supplements ADD COLUMN faqs TEXT")
        if "things_to_know" not in existing_cols:
            cursor.execute("ALTER TABLE supplements ADD COLUMN things_to_know TEXT")
        
        # 2. Effect Matrix Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS effect_matrix (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplement_slug TEXT NOT NULL,
            outcome TEXT NOT NULL,
            category TEXT NOT NULL,
            magnitude TEXT NOT NULL,
            evidence_grade TEXT NOT NULL,
            study_count INTEGER DEFAULT 1,
            clinical_notes TEXT,
            pmids TEXT,
            direction TEXT DEFAULT 'neutral',
            FOREIGN KEY (supplement_slug) REFERENCES supplements(slug) ON DELETE CASCADE
        );
        """)

        # Migration: Ensure direction column in effect_matrix
        cursor.execute("PRAGMA table_info(effect_matrix)")
        em_cols = [c[1] for c in cursor.fetchall()]
        if "direction" not in em_cols:
            cursor.execute("ALTER TABLE effect_matrix ADD COLUMN direction TEXT DEFAULT 'neutral'")

        # 3. Cited Studies Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS studies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplement_slug TEXT NOT NULL,
            pmid TEXT NOT NULL,
            title TEXT NOT NULL,
            abstract TEXT,
            journal TEXT,
            year TEXT,
            url TEXT,
            FOREIGN KEY (supplement_slug) REFERENCES supplements(slug) ON DELETE CASCADE
        );
        """)

        # 4. Live Research Feed Articles Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS recent_articles (
            pmid TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            journal TEXT,
            year TEXT,
            authors TEXT,
            study_type TEXT,
            abstract TEXT,
            takeaway TEXT,
            key_findings TEXT,
            significance TEXT,
            topic TEXT DEFAULT 'all',
            url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 5. Conditions Directory Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conditions (
            slug TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            overview TEXT NOT NULL,
            tier1_supplements TEXT, -- Grade A/B primary supplements
            tier2_supplements TEXT, -- Grade B/C supportive supplements
            ineffective_supplements TEXT, -- Ineffective / marketing hype
            lifestyle_factors TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 6. Categories Directory Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            slug TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            icon TEXT NOT NULL,
            description TEXT NOT NULL,
            primary_outcomes TEXT,
            key_supplements TEXT
        );
        """)

        # 7. Protocol Guides Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS guides (
            slug TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            subtitle TEXT NOT NULL,
            target_goal TEXT NOT NULL,
            reading_time TEXT NOT NULL,
            summary TEXT NOT NULL,
            protocol_phases TEXT,
            recommended_stacks TEXT,
            lifestyle_prerequisites TEXT
        );
        """)

        # 8. Custom Formulas Table (User-created supplements)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS custom_formulas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            goal TEXT NOT NULL,
            target_user TEXT,
            ingredients TEXT NOT NULL,
            synergy_score INTEGER DEFAULT 80,
            safety_rating TEXT,
            evidence_grade TEXT,
            analysis_report TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        conn.commit()

        # Seed baseline encyclopedias ONLY if database has not been initialized yet
        cursor.execute("SELECT COUNT(*) FROM supplements")
        if cursor.fetchone()[0] < 100:
            seed_all_data()

# =======================================================
# Condition & Guide & Category Helpers
# =======================================================

def get_all_conditions() -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM conditions ORDER BY name ASC")
        rows = []
        for r in cursor.fetchall():
            d = dict(r)
            d["tier1_supplements"] = json.loads(d["tier1_supplements"]) if d["tier1_supplements"] else []
            d["tier2_supplements"] = json.loads(d["tier2_supplements"]) if d["tier2_supplements"] else []
            d["ineffective_supplements"] = json.loads(d["ineffective_supplements"]) if d["ineffective_supplements"] else []
            d["lifestyle_factors"] = json.loads(d["lifestyle_factors"]) if d["lifestyle_factors"] else []
            rows.append(d)
        return rows

def get_condition_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM conditions WHERE slug = ?", (slug.lower().strip(),))
        r = cursor.fetchone()
        if not r:
            return None
        d = dict(r)
        d["tier1_supplements"] = json.loads(d["tier1_supplements"]) if d["tier1_supplements"] else []
        d["tier2_supplements"] = json.loads(d["tier2_supplements"]) if d["tier2_supplements"] else []
        d["ineffective_supplements"] = json.loads(d["ineffective_supplements"]) if d["ineffective_supplements"] else []
        d["lifestyle_factors"] = json.loads(d["lifestyle_factors"]) if d["lifestyle_factors"] else []
        return d

def get_all_categories() -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories ORDER BY name ASC")
        rows = []
        for r in cursor.fetchall():
            d = dict(r)
            d["primary_outcomes"] = json.loads(d["primary_outcomes"]) if d["primary_outcomes"] else []
            d["key_supplements"] = json.loads(d["key_supplements"]) if d["key_supplements"] else []
            rows.append(d)
        return rows

def get_all_guides() -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT slug, title, subtitle, target_goal, reading_time, summary FROM guides ORDER BY title ASC")
        return [dict(r) for r in cursor.fetchall()]

def get_guide_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM guides WHERE slug = ?", (slug.lower().strip(),))
        r = cursor.fetchone()
        if not r:
            return None
        d = dict(r)
        d["protocol_phases"] = json.loads(d["protocol_phases"]) if d["protocol_phases"] else []
        d["recommended_stacks"] = json.loads(d["recommended_stacks"]) if d["recommended_stacks"] else []
        d["lifestyle_prerequisites"] = json.loads(d["lifestyle_prerequisites"]) if d["lifestyle_prerequisites"] else []
        return d

def save_custom_formula(data: Dict[str, Any]) -> int:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO custom_formulas 
        (name, goal, target_user, ingredients, synergy_score, safety_rating, evidence_grade, analysis_report)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("name", "Custom Blend"),
            data.get("goal", "Health Optimization"),
            data.get("target_user", "Adults"),
            json.dumps(data.get("ingredients", [])),
            data.get("synergy_score", 85),
            data.get("safety_rating", "High"),
            data.get("evidence_grade", "A"),
            json.dumps(data.get("analysis_report", {}))
        ))
        conn.commit()
        return cursor.lastrowid

def get_custom_formulas() -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM custom_formulas ORDER BY created_at DESC")
        rows = []
        for r in cursor.fetchall():
            d = dict(r)
            d["ingredients"] = json.loads(d["ingredients"]) if d["ingredients"] else []
            d["analysis_report"] = json.loads(d["analysis_report"]) if d["analysis_report"] else {}
            rows.append(d)
        return rows

# =======================================================
# Supplement & Matrix Helpers
# =======================================================

def save_recent_articles(articles: List[Dict[str, Any]], topic: str = "all"):
    with get_db() as conn:
        cursor = conn.cursor()
        for a in articles:
            takeaway = a.get("takeaway", "")
            if isinstance(takeaway, (list, dict)):
                takeaway = json.dumps(takeaway)
            
            key_findings = a.get("key_findings", "")
            if isinstance(key_findings, list):
                key_findings = "\n".join([f"• {item}" for item in key_findings])
            elif isinstance(key_findings, dict):
                key_findings = json.dumps(key_findings)

            significance = a.get("significance", "")
            if isinstance(significance, (list, dict)):
                significance = json.dumps(significance)

            cursor.execute("""
            INSERT INTO recent_articles 
            (pmid, title, journal, year, authors, study_type, abstract, takeaway, key_findings, significance, topic, url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(pmid) DO UPDATE SET
                takeaway=COALESCE(excluded.takeaway, recent_articles.takeaway),
                key_findings=COALESCE(excluded.key_findings, recent_articles.key_findings),
                significance=COALESCE(excluded.significance, recent_articles.significance),
                topic=excluded.topic
            """, (
                str(a.get("pmid", "")),
                str(a.get("title", "")),
                str(a.get("journal", "")),
                str(a.get("year", "")),
                str(a.get("authors", "")),
                str(a.get("study_type", "")),
                str(a.get("abstract", "")),
                str(takeaway),
                str(key_findings),
                str(significance),
                topic,
                str(a.get("url", ""))
            ))
        conn.commit()

def get_recent_articles(topic: str = "all", limit: int = 15) -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        if topic == "all":
            cursor.execute("SELECT * FROM recent_articles ORDER BY year DESC, created_at DESC LIMIT ?", (limit,))
        else:
            cursor.execute("SELECT * FROM recent_articles WHERE topic = ? ORDER BY year DESC, created_at DESC LIMIT ?", (topic, limit))
        return [dict(r) for r in cursor.fetchall()]

def save_supplement_data(
    slug: str,
    name: str,
    summary: str,
    pubchem_data: Dict[str, Any],
    dosage_guide: Dict[str, Any],
    safety_data: Dict[str, Any],
    effect_matrix: List[Dict[str, Any]],
    studies: List[Dict[str, Any]],
    clinical_trials: Optional[List[Dict[str, Any]]] = None,
    item_type: str = "supplements",
    letter_index: Optional[str] = None,
    faqs: Optional[List[Dict[str, Any]]] = None,
    things_to_know: Optional[Dict[str, Any]] = None
):
    if not letter_index:
        first = name.strip()[0].upper()
        letter_index = "0-9" if first.isdigit() else first

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO supplements (slug, name, summary, pubchem_data, dosage_guide, safety_data, clinical_trials, item_type, letter_index, faqs, things_to_know, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(slug) DO UPDATE SET
            name=excluded.name,
            summary=excluded.summary,
            pubchem_data=excluded.pubchem_data,
            dosage_guide=excluded.dosage_guide,
            safety_data=excluded.safety_data,
            clinical_trials=COALESCE(excluded.clinical_trials, supplements.clinical_trials),
            item_type=COALESCE(excluded.item_type, supplements.item_type),
            letter_index=COALESCE(excluded.letter_index, supplements.letter_index),
            faqs=COALESCE(excluded.faqs, supplements.faqs),
            things_to_know=COALESCE(excluded.things_to_know, supplements.things_to_know),
            updated_at=CURRENT_TIMESTAMP
        """, (
            slug,
            name,
            summary,
            json.dumps(pubchem_data),
            json.dumps(dosage_guide),
            json.dumps(safety_data),
            json.dumps(clinical_trials) if clinical_trials else "[]",
            item_type,
            letter_index,
            json.dumps(faqs) if faqs else "[]",
            json.dumps(things_to_know) if things_to_know else "{}"
        ))

        cursor.execute("DELETE FROM effect_matrix WHERE supplement_slug = ?", (slug,))
        cursor.execute("DELETE FROM studies WHERE supplement_slug = ?", (slug,))

        for row in effect_matrix:
            mag = row.get("magnitude", "Moderate Increase")
            direction = row.get("direction")
            if not direction:
                if any(w in mag.lower() for w in ["increase", "improve", "enhance", "boost", "elevate"]):
                    direction = "increase"
                elif any(w in mag.lower() for w in ["decrease", "reduc", "lower", "drop"]):
                    direction = "decrease"
                else:
                    direction = "neutral"

            cursor.execute("""
            INSERT INTO effect_matrix 
            (supplement_slug, outcome, category, magnitude, evidence_grade, study_count, clinical_notes, pmids, direction)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                slug,
                row.get("outcome", ""),
                row.get("category", "General Health"),
                mag,
                row.get("evidence_grade", "B"),
                int(row.get("study_count", 1)),
                row.get("clinical_notes", ""),
                json.dumps(row.get("pmids", [])),
                direction
            ))

        for s in studies:
            cursor.execute("""
            INSERT INTO studies (supplement_slug, pmid, title, abstract, journal, year, url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                slug,
                s.get("pmid", ""),
                s.get("title", ""),
                s.get("abstract", ""),
                s.get("journal", ""),
                s.get("year", ""),
                s.get("url", "")
            ))
        conn.commit()

def get_supplement_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM supplements WHERE slug = ?", (slug.lower().strip(),))
        row = cursor.fetchone()
        if not row:
            return None

        supp = dict(row)
        supp["pubchem_data"] = json.loads(supp["pubchem_data"]) if supp.get("pubchem_data") else {}
        supp["dosage_guide"] = json.loads(supp["dosage_guide"]) if supp.get("dosage_guide") else {}
        supp["safety_data"] = json.loads(supp["safety_data"]) if supp.get("safety_data") else {}
        supp["clinical_trials"] = json.loads(supp["clinical_trials"]) if supp.get("clinical_trials") else []
        supp["faqs"] = json.loads(supp["faqs"]) if supp.get("faqs") else []
        supp["things_to_know"] = json.loads(supp["things_to_know"]) if supp.get("things_to_know") else {}

        cursor.execute("SELECT * FROM effect_matrix WHERE supplement_slug = ? ORDER BY evidence_grade ASC", (slug,))
        matrix_rows = cursor.fetchall()
        supp["effect_matrix"] = []
        for mr in matrix_rows:
            m_dict = dict(mr)
            m_dict["pmids"] = json.loads(m_dict["pmids"]) if m_dict["pmids"] else []
            supp["effect_matrix"].append(m_dict)

        cursor.execute("SELECT * FROM studies WHERE supplement_slug = ? ORDER BY year DESC", (slug,))
        supp["studies"] = [dict(sr) for sr in cursor.fetchall()]

        return supp

_SUPPLEMENTS_CACHE: Optional[List[Dict[str, Any]]] = None

def get_all_supplements(letter: Optional[str] = None, item_type: Optional[str] = None) -> List[Dict[str, Any]]:
    global _SUPPLEMENTS_CACHE
    if (not letter or letter.lower() == "all") and (not item_type or item_type.lower() == "all"):
        if _SUPPLEMENTS_CACHE is not None:
            return _SUPPLEMENTS_CACHE

    with get_db() as conn:
        cursor = conn.cursor()
        query = "SELECT slug, name, summary, dosage_guide, item_type, letter_index, updated_at FROM supplements WHERE 1=1"
        params = []
        if letter and letter.lower() != "all":
            if letter == "0-9":
                query += " AND letter_index = '0-9'"
            else:
                query += " AND UPPER(letter_index) = ?"
                params.append(letter.upper())
        if item_type and item_type.lower() != "all":
            query += " AND item_type = ?"
            params.append(item_type)
        query += " ORDER BY name ASC"
        cursor.execute(query, params)
        results = []
        for r in cursor.fetchall():
            d = dict(r)
            d["dosage_guide"] = json.loads(d["dosage_guide"]) if d.get("dosage_guide") else {}
            results.append(d)
        
        if (not letter or letter.lower() == "all") and (not item_type or item_type.lower() == "all"):
            _SUPPLEMENTS_CACHE = results
        return results

def search_database(query: str) -> List[Dict[str, Any]]:
    from services.search_matcher import normalize_text_typos
    
    raw = query.lower().strip()
    if not raw:
        return []

    q_norm, _ = normalize_text_typos(raw)
    
    # Generate search variants (raw, normalized, hyphenated, space-separated, no-space)
    terms = list(dict.fromkeys([
        raw, 
        q_norm, 
        raw.replace(" ", "-"), 
        raw.replace("-", " "), 
        raw.replace(" ", "")
    ]))

    results = []
    seen = set()

    with get_db() as conn:
        cursor = conn.cursor()

        # 1. Exact or prefix matches on Supplements (Highest priority)
        for t in terms:
            cursor.execute("""
            SELECT slug, name, summary, 'supplement' as type, 1 as priority
            FROM supplements
            WHERE lower(name) = ? OR lower(slug) = ? OR lower(name) LIKE ?
            LIMIT 8
            """, (t, t, f"{t}%"))
            for r in cursor.fetchall():
                key = (r["type"], r["slug"])
                if key not in seen:
                    seen.add(key)
                    results.append(dict(r))

        # 2. Conditions match
        for t in terms:
            cursor.execute("""
            SELECT slug, name, overview as summary, 'condition' as type, 2 as priority
            FROM conditions
            WHERE lower(name) LIKE ? OR lower(overview) LIKE ?
            LIMIT 5
            """, (f"%{t}%", f"%{t}%"))
            for r in cursor.fetchall():
                key = (r["type"], r["slug"])
                if key not in seen:
                    seen.add(key)
                    results.append(dict(r))

        # 3. Categories match
        for t in terms:
            cursor.execute("""
            SELECT slug, name, description as summary, 'category' as type, 2 as priority
            FROM categories
            WHERE lower(name) LIKE ? OR lower(description) LIKE ? OR lower(primary_outcomes) LIKE ?
            LIMIT 3
            """, (f"%{t}%", f"%{t}%", f"%{t}%"))
            for r in cursor.fetchall():
                key = (r["type"], r["slug"])
                if key not in seen:
                    seen.add(key)
                    results.append(dict(r))

        # 4. Guides match
        for t in terms:
            cursor.execute("""
            SELECT slug, title as name, summary, 'guide' as type, 2 as priority
            FROM guides
            WHERE lower(title) LIKE ? OR lower(target_goal) LIKE ? OR lower(summary) LIKE ?
            LIMIT 3
            """, (f"%{t}%", f"%{t}%", f"%{t}%"))
            for r in cursor.fetchall():
                key = (r["type"], r["slug"])
                if key not in seen:
                    seen.add(key)
                    results.append(dict(r))

        # 5. Supplements substring / effect matrix match (broader search)
        for t in terms:
            cursor.execute("""
            SELECT DISTINCT s.slug, s.name, s.summary, 'supplement' as type, 3 as priority
            FROM supplements s
            LEFT JOIN effect_matrix em ON s.slug = em.supplement_slug
            WHERE lower(s.name) LIKE ? 
               OR lower(s.summary) LIKE ? 
               OR lower(em.outcome) LIKE ? 
               OR lower(em.category) LIKE ?
            LIMIT 8
            """, (f"%{t}%", f"%{t}%", f"%{t}%", f"%{t}%"))
            for r in cursor.fetchall():
                key = (r["type"], r["slug"])
                if key not in seen:
                    seen.add(key)
                    results.append(dict(r))

    results.sort(key=lambda x: x.get("priority", 3))
    return results[:15]

def get_category_outcomes(category: str) -> List[Dict[str, Any]]:
    c = category.lower().strip()
    kw = [c]
    
    if 'performance' in c or 'muscle' in c:
        kw = ['performance', 'muscle', 'strength', 'power', 'endurance', 'hypertrophy', 'exercise', '1rm']
    elif 'sleep' in c or 'mood' in c or 'anxiety' in c:
        kw = ['sleep', 'circadian', 'mood', 'stress', 'anxiety', 'insomnia', 'relaxation', 'cortisol']
    elif 'brain' in c or 'focus' in c or 'cognit' in c:
        kw = ['brain', 'focus', 'cognit', 'memory', 'nootropic', 'executive', 'attention', 'bdnf']
    elif 'immun' in c:
        kw = ['immun', 'defense', 'infection', 'viral', 'respiratory', 'cold', 'inflammatory']
    elif 'metabol' in c or 'glucose' in c:
        kw = ['metabol', 'glucose', 'insulin', 'glycem', 'blood sugar', 'hba1c', 'lipid', 'cholesterol']
    elif 'cardio' in c or 'heart' in c:
        kw = ['cardio', 'heart', 'vascular', 'blood pressure', 'arterial', 'endothelial', 'nitric oxide']
    elif 'joint' in c or 'bone' in c:
        kw = ['joint', 'bone', 'cartilage', 'osteo', 'arthritis', 'womac', 'stiffness']
    elif 'gut' in c or 'digest' in c:
        kw = ['gut', 'digest', 'microbiome', 'bloating', 'zonulin', 'bowel', 'probiotic']
    elif 'hormone' in c or 'vitality' in c:
        kw = ['hormone', 'testosterone', 'thyroid', 'endocrine', 'lh', 'fsh', 'shbg']
    elif 'longevity' in c or 'aging' in c or 'cellular' in c or 'lifespan' in c:
        kw = ['longevity', 'cellular', 'lifespan', 'aging', 'nad', 'sod', 'glutathione', 'atp', 'autophagy', 'mitochondri']
    elif 'liver' in c or 'detox' in c or 'hepatic' in c:
        kw = ['liver', 'detox', 'alt', 'ast', 'hepatic', 'fibrosis', 'silymarin', 'glutathione', 'bilirubin']

    where_clauses = ' OR '.join(['lower(em.category) LIKE ? OR lower(em.outcome) LIKE ?' for _ in kw])
    params = []
    for k in kw:
        params.extend([f'%{k}%', f'%{k}%'])

    sql = f"""
    SELECT DISTINCT em.id, em.supplement_slug, em.outcome, em.category, em.magnitude, em.evidence_grade, em.study_count, em.clinical_notes, em.direction, em.pmids, s.name as supplement_name
    FROM effect_matrix em
    JOIN supplements s ON em.supplement_slug = s.slug
    WHERE {where_clauses}
    ORDER BY em.evidence_grade ASC, em.study_count DESC
    LIMIT 60
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        results = []
        for r in cursor.fetchall():
            d = dict(r)
            d["pmids"] = json.loads(d["pmids"]) if d["pmids"] else []
            results.append(d)
        return results

# =======================================================
# Comprehensive Encyclopedic Seed Data
# =======================================================
def seed_all_data():
    from seed_data import (
        seed_categories_data,
        seed_conditions_data,
        seed_guides_data,
        seed_supplements_data
    )
    seed_categories_data(get_db)
    seed_conditions_data(get_db)
    seed_guides_data(get_db)
    seed_supplements_data(save_supplement_data)
