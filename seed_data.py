import json
import logging
from data.conditions_data import ALL_CONDITIONS
from data.supplements_data import ALL_SUPPLEMENTS

logger = logging.getLogger("seed-data")

def seed_categories_data(get_db):
    categories = [
        {
            "slug": "sleep-circadian",
            "name": "Sleep & Circadian Rhythm",
            "icon": "🌙",
            "description": "Evidence-based interventions to reduce sleep onset latency, optimize deep slow-wave sleep, and entrain circadian biology.",
            "primary_outcomes": ["Sleep Onset Latency", "Sleep Efficiency", "Slow-Wave Sleep", "Jet Lag Recovery", "REM Density"],
            "key_supplements": ["Melatonin", "Magnesium Glycinate", "L-Theanine", "Apigenin", "Glycine", "Tart Cherry"]
        },
        {
            "slug": "brain-focus",
            "name": "Brain Health & Cognition",
            "icon": "🧠",
            "description": "Nootropic compounds, neuroprotective botanicals, and substrates that enhance working memory, executive function, and mental endurance.",
            "primary_outcomes": ["Working Memory", "Executive Function", "Reaction Time", "Brain-Derived Neurotrophic Factor (BDNF)", "Attention Span"],
            "key_supplements": ["Alpha-GPC", "Lion's Mane", "Creatine Monohydrate", "L-Theanine", "Caffeine", "Bacopa Monnieri"]
        },
        {
            "slug": "performance-muscle",
            "name": "Physical Performance & Muscle",
            "icon": "⚡",
            "description": "Ergogenic aids and nutrients proven in randomized trials to enhance power output, hypertrophy, anaerobic threshold, and training volume.",
            "primary_outcomes": ["1RM Power Output", "Lean Muscle Mass", "Anaerobic Threshold", "Muscular Endurance", "Rate of Force Development"],
            "key_supplements": ["Creatine Monohydrate", "Beta-Alanine", "L-Citrulline Malate", "Whey Protein", "Caffeine", "Tart Cherry"]
        },
        {
            "slug": "stress-mood",
            "name": "Stress, Anxiety & Mood",
            "icon": "🧘",
            "description": "Adaptogens and anxiolytic nutrients that regulate the hypothalamic-pituitary-adrenal (HPA) axis and modulate GABAergic/serotonergic tone.",
            "primary_outcomes": ["Serum Cortisol", "HAM-A Anxiety Scores", "Subjective Stress (PSS)", "Depressive Symptoms", "Heart Rate Variability (HRV)"],
            "key_supplements": ["Ashwagandha (KSM-66)", "Rhodiola Rosea", "L-Theanine", "Magnesium Glycinate", "Saffron", "Holy Basil"]
        },
        {
            "slug": "metabolic-health",
            "name": "Metabolic Health & Glucose",
            "icon": "🩸",
            "description": "Nutrients that upregulate AMPK, improve cellular insulin sensitivity, and modulate postprandial glycemic excursions.",
            "primary_outcomes": ["HbA1c", "Fasting Blood Glucose", "HOMA-IR Insulin Sensitivity", "Triglycerides", "Postprandial Spikes"],
            "key_supplements": ["Berberine", "Alpha-Lipoic Acid", "Chromium Picolinate", "Cinnamon Extract", "Inositol", "Omega-3"]
        },
        {
            "slug": "longevity-cellular",
            "name": "Longevity & Cellular Health",
            "icon": "⏳",
            "description": "Compounds supporting mitochondrial respiration, cellular autophagy, NAD+ homeostasis, and mitigating oxidative stress.",
            "primary_outcomes": ["Mitochondrial Efficiency", "NAD+ Levels", "Endothelial Function", "Systemic hs-CRP", "Telomere Length"],
            "key_supplements": ["CoQ10 (Ubiquinol)", "N-Acetylcysteine (NAC)", "Resveratrol", "Quercetin", "Vitamin D3", "Omega-3"]
        },
        {
            "slug": "joint-bone",
            "name": "Joint, Cartilage & Bone",
            "icon": "🦴",
            "description": "Nutritional building blocks and anti-inflammatory compounds that preserve synovial fluid, cartilage thickness, and bone mineral density.",
            "primary_outcomes": ["WOMAC Osteoarthritis Pain", "Cartilage Degradation Biomarkers", "Joint Stiffness", "Bone Mineral Density"],
            "key_supplements": ["Curcumin (Phytosome)", "Collagen Peptides", "Glucosamine & Chondroitin", "Boswellia Serrata", "Vitamin D3 + K2"]
        },
        {
            "slug": "heart-cardiovascular",
            "name": "Cardiovascular & Heart Health",
            "icon": "❤️",
            "description": "Interventions lowering LDL particle count, supporting nitric oxide mediated flow dilation, and reducing systemic arterial stiffness.",
            "primary_outcomes": ["Systolic & Diastolic BP", "Triglycerides", "Flow-Mediated Dilation (FMD)", "LDL Oxidation", "hs-CRP"],
            "key_supplements": ["Omega-3 Fish Oil (EPA/DHA)", "CoQ10", "Garlic Extract (Aged)", "L-Citrulline", "Magnesium Taurate"]
        },
        {
            "slug": "immunity-defense",
            "name": "Immune Defense & Inflammation",
            "icon": "🛡️",
            "description": "Essential micronutrients and immunomodulating botanicals that bolster innate and adaptive immune cell signaling.",
            "primary_outcomes": ["Duration of Upper Respiratory Infections", "Natural Killer Cell Activity", "IL-6 / TNF-alpha Suppression"],
            "key_supplements": ["Vitamin D3", "Zinc Carnosine", "Vitamin C", "Elderberry", "Echinacea", "N-Acetylcysteine (NAC)"]
        },
        {
            "slug": "hormones-vitality",
            "name": "Hormones & Vitality",
            "icon": "🧬",
            "description": "Evidence-backed nutrients supporting endocrine equilibrium, free testosterone, luteinizing hormone, and thyroid function.",
            "primary_outcomes": ["Total & Free Testosterone", "LH & FSH Ratios", "Thyroid T3/T4 Balance", "Sex Hormone-Binding Globulin (SHBG)"],
            "key_supplements": ["Tongkat Ali (Eurycoma longifolia)", "Ashwagandha", "Zinc", "Boron", "Vitamin D3", "Fenugreek"]
        },
        {
            "slug": "gut-digestion",
            "name": "Gut Health & Digestion",
            "icon": "🌱",
            "description": "Targeted therapies to rebuild the mucosal intestinal barrier, promote microbial diversity, and alleviate dysbiosis.",
            "primary_outcomes": ["Zonulin Intestinal Permeability", "Bloating & Gas Reduction", "Stool Consistency (Bristol Scale)"],
            "key_supplements": ["L-Glutamine", "Zinc Carnosine", "Probiotics (Multi-strain)", "Psyllium Husk", "Deglycyrrhizinated Licorice (DGL)"]
        },
        {
            "slug": "liver-detox",
            "name": "Liver Health & Detoxification",
            "icon": "🧪",
            "description": "Hepatic antioxidants and methyl donors that reduce liver transaminases (ALT/AST) and mitigate hepatic steatosis.",
            "primary_outcomes": ["Serum ALT & AST Enzymes", "Hepatic Fat Accumulation", "Glutathione S-Transferase Induction"],
            "key_supplements": ["Milk Thistle (Silymarin)", "N-Acetylcysteine (NAC)", "Choline", "TUDCA", "Curcumin"]
        }
    ]

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories")
        for c in categories:
            cursor.execute("""
            INSERT INTO categories (slug, name, icon, description, primary_outcomes, key_supplements)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                c["slug"],
                c["name"],
                c["icon"],
                c["description"],
                json.dumps(c["primary_outcomes"]),
                json.dumps(c["key_supplements"])
            ))
        conn.commit()

def seed_conditions_data(get_db):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM conditions")
        for c in ALL_CONDITIONS:
            cursor.execute("""
            INSERT INTO conditions (slug, name, category, overview, tier1_supplements, tier2_supplements, ineffective_supplements, lifestyle_factors)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                c["slug"],
                c["name"],
                c["category"],
                c["overview"],
                json.dumps(c["tier1_supplements"]),
                json.dumps(c["tier2_supplements"]),
                json.dumps(c["ineffective_supplements"]),
                json.dumps(c["lifestyle_factors"])
            ))
        conn.commit()

def seed_guides_data(get_db):
    guides = [
        {
            "slug": "deep-sleep-protocol",
            "title": "The Deep Sleep Architecture Protocol",
            "subtitle": "An evidence-based blueprint for increasing slow-wave sleep and eliminating midnight awakenings.",
            "target_goal": "Sleep Optimization & Circadian Health",
            "reading_time": "7 min read",
            "summary": "Sleep is not merely the absence of wakefulness—it is an active, metabolically demanding state of neurological repair and memory consolidation. This protocol synthesizes clinical trials on GABAergic modulation, core body cooling, and circadian melatonin pulses.",
            "protocol_phases": [
                {
                    "phase_title": "Phase 1: Circadian Anchoring (Morning)",
                    "action": "Expose eyes to 10,000+ lux sunlight within 30 minutes of waking for 15 minutes. Ingest 500ml water with a pinch of Celtic sea salt.",
                    "rationale": "Suppresses residual melatonin, synchronizes cortisol awakening response, and sets the internal circadian timer for nocturnal melatonin release 16 hours later."
                },
                {
                    "phase_title": "Phase 2: Adenosine Protection (Afternoon)",
                    "action": "Cut off all caffeine, pre-workouts, and stimulants by 12:00 PM.",
                    "rationale": "Caffeine has a 5-7 hour half-life and 12-hour quarter-life. Even if you can fall asleep, residual caffeine blocks adenosine A1 receptors and slashes deep slow-wave sleep by up to 30%."
                },
                {
                    "phase_title": "Phase 3: The Neurological Downshift Stack (45m Pre-Bed)",
                    "action": "Take: Magnesium Glycinate (300mg elemental) + L-Theanine (200mg) + Apigenin (50mg). Optional: Micro-dose Melatonin (0.3mg) if jet-lagged.",
                    "rationale": "Magnesium potentiates GABA-A receptor conductance, L-Theanine enhances alpha brain-wave generation, and Apigenin produces tranquil hypnotic signaling."
                }
            ],
            "recommended_stacks": [
                {"name": "Core Sleep Foundation", "items": ["Magnesium Glycinate: 300mg", "L-Theanine: 200mg", "Apigenin: 50mg"]},
                {"name": "Circadian Realignment (Jet Lag)", "items": ["Micro-dose Melatonin: 0.3mg (at target bedtime)", "Glycine: 3g"]}
            ],
            "lifestyle_prerequisites": [
                "Zero alcohol within 3 hours of bed (alcohol is a sedative that obliterates REM and deep sleep architecture).",
                "Keep bedroom temperature strictly at or below 66°F (19°C)."
            ]
        },
        {
            "slug": "joint-mobility-cartilage-guide",
            "title": "Joint Cartilage Restoration & Mobility Protocol",
            "subtitle": "Clinical strategies to extinguish chronic synovial inflammation and regenerate extracellular joint matrix.",
            "target_goal": "Joint Health, Tendon Elasticity & Cartilage Longevity",
            "reading_time": "8 min read",
            "summary": "Joint pain is driven by two distinct mechanisms: mechanical load wear-and-tear, and biochemical chronic low-grade synovial inflammation. This protocol targets both pathways using bioavailable curcuminoids, boswellic acids, and specialized collagen peptide fragments.",
            "protocol_phases": [
                {
                    "phase_title": "Phase 1: Extinguishing Synovial Inflammation",
                    "action": "Administer Curcumin Phytosome (500mg 2x daily with meals) + Boswellia Serrata (100mg ApresFlex).",
                    "rationale": "Dual-inhibition of COX-2 (cyclooxygenase) and 5-LOX (lipoxygenase) enzymes suppresses inflammatory prostaglandin E2 and leukotriene B4 without gastric mucosal toxicity."
                },
                {
                    "phase_title": "Phase 2: Cartilage Matrix Rebuilding",
                    "action": "Consume 10g - 15g of Hydrolyzed Type I/II Collagen Peptides paired with 50mg Vitamin C 45 minutes prior to joint movement.",
                    "rationale": "Vitamin C is an essential cofactor for prolyl hydroxylase in collagen triple-helix cross-linking. Ingestion before loading directs blood flow and amino acid delivery directly into avascular cartilage."
                }
            ],
            "recommended_stacks": [
                {"name": "Daily Joint Defense", "items": ["Curcumin Phytosome: 500mg", "Boswellia (AKBA): 100mg", "Collagen Peptides: 10g"]}
            ],
            "lifestyle_prerequisites": [
                "Perform full-range unloaded joint circles (CARs) every morning to circulate synovial fluid.",
                "Ensure adequate dietary omega-3 index (>8%) to keep baseline systemic inflammation low."
            ]
        },
        {
            "slug": "executive-focus-nootropic-protocol",
            "title": "Executive Focus & Neuro-Endurance Protocol",
            "subtitle": "Optimize acetylcholine synthesis, dopamine receptor density, and cognitive stamina.",
            "target_goal": "Cognition, Memory & Deep Work",
            "reading_time": "6 min read",
            "summary": "Deep focus requires two synchronized neurochemical states: sufficient cholinergic tone for working memory, and sustained dopaminergic signaling for task motivation without excessive sympathetic anxiety.",
            "protocol_phases": [
                {
                    "phase_title": "Phase 1: Acetylcholine & Neuro-Energy Foundation",
                    "action": "Creatine Monohydrate (5g daily) + Alpha-GPC (300mg in the morning).",
                    "rationale": "Creatine buffers neuronal phosphocreatine reserves, preventing brain ATP depletion during intense cognitive demand. Alpha-GPC delivers bioavailable choline directly across the blood-brain barrier."
                },
                {
                    "phase_title": "Phase 2: Smooth Sustained Deep Work",
                    "action": "Caffeine (100mg) paired with L-Theanine (200mg in a 1:2 ratio).",
                    "rationale": "L-Theanine antagonizes glutamate receptors and stimulates alpha brain waves, transforming the jagged edge of caffeine into calm, hyper-focused attention."
                }
            ],
            "recommended_stacks": [
                {"name": "Deep Work Stack", "items": ["Alpha-GPC: 300mg", "Creatine Monohydrate: 5g", "L-Theanine: 200mg", "Caffeine: 100mg"]}
            ],
            "lifestyle_prerequisites": [
                "Work in 90-minute ultradian rhythm blocks followed by 10 minutes of complete mental decompression.",
                "Hydrate with 500ml water containing sodium and potassium every 2 hours."
            ]
        }
    ]

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM guides")
        for g in guides:
            cursor.execute("""
            INSERT INTO guides (slug, title, subtitle, target_goal, reading_time, summary, protocol_phases, recommended_stacks, lifestyle_prerequisites)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                g["slug"],
                g["title"],
                g["subtitle"],
                g["target_goal"],
                g["reading_time"],
                g["summary"],
                json.dumps(g["protocol_phases"]),
                json.dumps(g["recommended_stacks"]),
                json.dumps(g["lifestyle_prerequisites"])
            ))
        conn.commit()

def seed_supplements_data(save_supplement_fn):
    import os
    catalog_path = os.path.join(os.path.dirname(__file__), "data", "full_catalog_data.json")
    items_by_slug = {}
    if os.path.exists(catalog_path):
        try:
            with open(catalog_path, "r", encoding="utf-8") as f:
                catalog_items = json.load(f)
                for item in catalog_items:
                    items_by_slug[item["slug"]] = item
            logger.info(f"Loaded master catalog with {len(items_by_slug)} entries from {catalog_path}")
        except Exception as e:
            logger.warning(f"Could not load full catalog json ({e})")

    # Overlay ALL_SUPPLEMENTS on top
    for gold in ALL_SUPPLEMENTS:
        items_by_slug[gold["slug"]] = {**items_by_slug.get(gold["slug"], {}), **gold}

    # Overlay GOLD_STANDARD_SUPPLEMENTS on top
    try:
        from data.gold_standard_catalog import GOLD_STANDARD_SUPPLEMENTS
        for extra in GOLD_STANDARD_SUPPLEMENTS:
            items_by_slug[extra["slug"]] = {**items_by_slug.get(extra["slug"], {}), **extra}
        logger.info(f"Integrated {len(GOLD_STANDARD_SUPPLEMENTS)} additional gold-standard monographs.")
    except Exception as e:
        logger.warning(f"Could not import GOLD_STANDARD_SUPPLEMENTS: {e}")

    items_to_seed = list(items_by_slug.values())
    logger.info(f"Seeding {len(items_to_seed)} clinical compounds, foods, and protocols into database...")
    for s in items_to_seed:
        save_supplement_fn(
            slug=s["slug"],
            name=s["name"],
            summary=s.get("summary", ""),
            pubchem_data=s.get("pubchem_data", {}),
            dosage_guide=s.get("dosage_guide", {}),
            safety_data=s.get("safety_data", {}),
            effect_matrix=s.get("effect_matrix", []),
            studies=s.get("studies", []),
            clinical_trials=s.get("clinical_trials", []),
            item_type=s.get("item_type", "supplements"),
            letter_index=s.get("letter_index", None),
            faqs=s.get("faqs", []),
            things_to_know=s.get("things_to_know", {})
        )

def seed_all_data():
    from database import get_db, save_supplement_data
    logger.info("Starting Walpar database seed initialization...")
    seed_categories_data(get_db)
    seed_conditions_data(get_db)
    seed_guides_data(get_db)
    seed_supplements_data(save_supplement_data)
    logger.info("Seeding completed successfully for all encyclopedic items.")

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    seed_all_data()
