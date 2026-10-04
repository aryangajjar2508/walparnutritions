# Walpar Clinical Conditions Directory (26 Comprehensive Conditions)

ALL_CONDITIONS = [
    {
        "slug": "insomnia",
        "name": "Insomnia & Sleep Disturbance",
        "category": "Sleep & Circadian",
        "overview": "Chronic difficulty with sleep onset, nocturnal awakenings, or unrefreshing sleep resulting in daytime impairment. Controlled trials show targeted natural compounds can modulate GABAergic transmission and circadian signaling without the tolerance or dependency of prescription hypnotics.",
        "tier1_supplements": [
            {"name": "Melatonin", "evidence": "Grade A", "magnitude": "High", "dose": "0.3mg - 2mg (30-60m before bed)", "notes": "Reduces sleep latency by 7-12 minutes; highly effective for circadian misalignment and delayed sleep phase."},
            {"name": "Magnesium Glycinate", "evidence": "Grade A", "magnitude": "Moderate", "dose": "200mg - 400mg elemental", "notes": "Agonizes GABA-A receptors and relaxes skeletal musculature; reduces nocturnal awakenings."}
        ],
        "tier2_supplements": [
            {"name": "L-Theanine", "evidence": "Grade B", "magnitude": "Moderate", "dose": "100mg - 200mg", "notes": "Stimulates alpha brain waves, facilitating relaxed mental transition to sleep without morning grogginess."},
            {"name": "Apigenin", "evidence": "Grade B", "magnitude": "Moderate", "dose": "50mg", "notes": "Chamomile flavonoid with mild benzodiazepine receptor binding affinity."},
            {"name": "Glycine", "evidence": "Grade B", "magnitude": "Minor", "dose": "3g", "notes": "Cools core body temperature to induce slow-wave deep sleep architecture."}
        ],
        "ineffective_supplements": [
            {"name": "Massive Dose Melatonin (>10mg)", "evidence": "Grade D", "notes": "Causes receptor desensitization, vivid nightmares, and marked daytime grogginess with no additional efficacy over 0.5-1mg."}
        ],
        "lifestyle_factors": [
            "Morning sunlight viewing (10-15 mins) within 30 minutes of waking to anchor the master circadian pacemaker (SCN).",
            "Dim artificial blue lighting 2 hours prior to desired bedtime.",
            "Maintain bedroom temperature around 65°F (18°C) to facilitate physiological nocturnal core cooling."
        ]
    },
    {
        "slug": "generalized-anxiety",
        "name": "Generalized Anxiety & Chronic Stress",
        "category": "Stress & Mood",
        "overview": "Sustained psychological tension, worry, and autonomic hyperactivity driven by chronic HPA axis activation and elevated serum cortisol. Clinical trials validate adaptogens and neuro-calming amino acids.",
        "tier1_supplements": [
            {"name": "Ashwagandha (KSM-66)", "evidence": "Grade A", "magnitude": "High", "dose": "300mg - 600mg daily", "notes": "Proven in over 20 double-blind RCTs to lower cortisol by 15-30% and reduce Hamilton Anxiety Rating Scale scores."},
            {"name": "L-Theanine", "evidence": "Grade A", "magnitude": "Moderate", "dose": "200mg as needed", "notes": "Blunts acute physiological stress spikes (heart rate, sympathetic tone) during mental pressure."}
        ],
        "tier2_supplements": [
            {"name": "Rhodiola Rosea", "evidence": "Grade B", "magnitude": "Moderate", "dose": "200mg - 400mg (3% rosavins)", "notes": "Particularly effective for anxiety accompanied by burnout, fatigue, and cognitive exhaustion."},
            {"name": "Magnesium Glycinate / L-Threonate", "evidence": "Grade B", "magnitude": "Moderate", "dose": "200mg elemental", "notes": "Buffers central nervous system excitotoxicity by antagonizing NMDA receptors."}
        ],
        "ineffective_supplements": [
            {"name": "Kava in unregulated crude forms", "evidence": "Grade D", "notes": "Significant hepatotoxicity risks with low-grade solvent extracts."}
        ],
        "lifestyle_factors": [
            "Physiological sigh breathing (two deep nasal inhales followed by one long extended mouth exhale).",
            "Eliminate caffeine intake past 12:00 PM."
        ]
    },
    {
        "slug": "major-depression-mood",
        "name": "Depressive Symptoms & Low Mood",
        "category": "Stress & Mood",
        "overview": "Persistent depressive mood, anhedonia, and monoaminergic or neuroinflammatory dysfunction. Evidence shows anti-inflammatory nutraceuticals and methyl donors provide measurable adjunct relief.",
        "tier1_supplements": [
            {"name": "Omega-3 Fatty Acids (High EPA)", "evidence": "Grade A", "magnitude": "High", "dose": "1000mg - 2000mg pure EPA daily", "notes": "Formulations with at least a 2:1 EPA:DHA ratio demonstrate statistically significant antidepressant efficacy in meta-analyses."},
            {"name": "S-Adenosylmethionine (SAMe)", "evidence": "Grade A", "magnitude": "Moderate", "dose": "400mg - 800mg daily", "notes": "Primary methyl donor for monoamine neurotransmitter synthesis; comparable to tricyclic antidepressants."}
        ],
        "tier2_supplements": [
            {"name": "Saffron Extract (Affron)", "evidence": "Grade B", "magnitude": "Moderate", "dose": "30mg daily", "notes": "Inhibits serotonin reuptake; multiple RCTs show efficacy equal to fluoxetine in mild-to-moderate depression."},
            {"name": "Vitamin D3", "evidence": "Grade B", "magnitude": "Moderate", "dose": "2000IU - 5000IU daily", "notes": "Essential cofactor for tryptophan hydroxylase; corrects depressive symptoms linked to hypovitaminosis D."}
        ],
        "ineffective_supplements": [
            {"name": "High-Dose St. John's Wort with SSRIs", "evidence": "Grade D", "notes": "Dangerous risk of Serotonin Syndrome due to potent CYP3A4 and P-glycoprotein induction."}
        ],
        "lifestyle_factors": [
            "Daily aerobic exercise (30 mins at moderate intensity) which elevates hippocampal BDNF.",
            "Bright light therapy (10,000 lux box) for 30 minutes each morning."
        ]
    },
    {
        "slug": "cognitive-fatigue-brain-fog",
        "name": "Cognitive Fatigue & Brain Fog",
        "category": "Brain & Focus",
        "overview": "Subjective mental slowness, poor working memory, and difficulty concentrating often triggered by neuroinflammation, poor cerebral perfusion, or mitochondrial ATP depletion.",
        "tier1_supplements": [
            {"name": "Alpha-GPC", "evidence": "Grade A", "magnitude": "High", "dose": "300mg - 600mg daily", "notes": "Readily crosses blood-brain barrier; boosts acetylcholine synthesis for acute mental clarity and focus."},
            {"name": "Creatine Monohydrate", "evidence": "Grade A", "magnitude": "Moderate", "dose": "5g daily", "notes": "Restores neuronal phosphocreatine reserves; significantly alleviates cognitive fatigue under sleep deprivation."}
        ],
        "tier2_supplements": [
            {"name": "Citicoline (CDP-Choline)", "evidence": "Grade B", "magnitude": "Moderate", "dose": "250mg - 500mg", "notes": "Supports neuronal membrane synthesis and upregulates dopamine receptor density."},
            {"name": "Lion's Mane Mushroom", "evidence": "Grade B", "magnitude": "Moderate", "dose": "1000mg standardized extract", "notes": "Stimulates Nerve Growth Factor (NGF) synthesis and neuroplasticity."}
        ],
        "ineffective_supplements": [
            {"name": "Excessive Caffeine (>400mg)", "evidence": "Grade D", "notes": "Triggers adenosine rebound, tremors, and paradoxical worsening of mental fatigue."}
        ],
        "lifestyle_factors": [
            "Zone 2 cardio to stimulate cerebral blood flow and nitric oxide production.",
            "Hydration with balanced electrolytes (sodium, potassium, magnesium) upon waking."
        ]
    },
    {
        "slug": "adhd-attention-deficit",
        "name": "ADHD & Executive Dysfunction",
        "category": "Brain & Focus",
        "overview": "Neurodevelopmental condition characterized by inattention, impulsivity, and executive dysfunction linked to prefrontal catecholaminergic signaling deficits.",
        "tier1_supplements": [
            {"name": "Omega-3 Fatty Acids (EPA/DHA)", "evidence": "Grade A", "magnitude": "Moderate", "dose": "1000mg EPA + 500mg DHA daily", "notes": "Meta-analyses demonstrate modest but significant improvements in clinical attention and behavioral scores."},
            {"name": "Zinc Bisglycinate", "evidence": "Grade B", "magnitude": "Moderate", "dose": "15mg - 30mg daily", "notes": "Regulates dopamine transporter; RCTs show reduced stimulant dosage requirements when co-administered."}
        ],
        "tier2_supplements": [
            {"name": "L-Tyrosine", "evidence": "Grade B", "magnitude": "Moderate", "dose": "500mg - 1500mg", "notes": "Direct precursor to dopamine and norepinephrine; buffers cognitive depletion during acute executive demand."},
            {"name": "Phosphatidylserine (PS)", "evidence": "Grade B", "magnitude": "Moderate", "dose": "200mg - 300mg", "notes": "Improves attention and auditory memory in pediatric and adult ADHD cohorts."}
        ],
        "ineffective_supplements": [
            {"name": "Artificial food coloring / Mega-dose multivitamins", "evidence": "Grade D", "notes": "Lacks consistent randomized evidence for symptom reduction."}
        ],
        "lifestyle_factors": [
            "High-protein breakfast to provide steady tyrosine and amino acid neurotransmitter precursors.",
            "Pomodoro interval structuring and physical activity breaks every 45 minutes."
        ]
    },
    {
        "slug": "type-2-diabetes-glucose",
        "name": "Type 2 Diabetes & Insulin Resistance",
        "category": "Metabolic Health",
        "overview": "Impaired cellular glucose uptake, peripheral insulin resistance, and chronic hyperglycemia leading to micro- and macro-vascular complications. Natural AMPK activators demonstrate potent glycemic control.",
        "tier1_supplements": [
            {"name": "Berberine HCl", "evidence": "Grade A", "magnitude": "High", "dose": "500mg (2-3x daily before meals)", "notes": "Directly activates AMPK; demonstrated reductions in HbA1c (-0.7% to -1.0%) and fasting glucose comparable to metformin."},
            {"name": "Alpha-Lipoic Acid (R-ALA)", "evidence": "Grade A", "magnitude": "Moderate", "dose": "300mg - 600mg daily", "notes": "Reduces oxidative stress and significantly alleviates diabetic peripheral neuropathy and improves insulin sensitivity."}
        ],
        "tier2_supplements": [
            {"name": "Chromium Picolinate", "evidence": "Grade B", "magnitude": "Minor", "dose": "200mcg - 1000mcg", "notes": "Potentiates insulin receptor phosphorylation; most effective in individuals with baseline chromium insufficiency."},
            {"name": "Cinnamon Extract (Ceylon)", "evidence": "Grade B", "magnitude": "Minor", "dose": "1g - 3g daily", "notes": "Mimics insulin signaling; modestly reduces fasting blood glucose."}
        ],
        "ineffective_supplements": [
            {"name": "Cassia Cinnamon in massive doses", "evidence": "Grade D", "notes": "Contains toxic levels of coumarin which causes hepatotoxicity."}
        ],
        "lifestyle_factors": [
            "Post-prandial walking: 10-15 minute walk immediately following carb-containing meals to activate GLUT4 non-insulinergic glucose uptake.",
            "Resistance training 3x/week to expand skeletal muscle glycogen storage capacity."
        ]
    },
    {
        "slug": "osteoarthritis-joint-pain",
        "name": "Osteoarthritis & Cartilage Degeneration",
        "category": "Joint & Bone",
        "overview": "Progressive degradation of articular cartilage and synovial inflammation resulting in stiffness, crepitus, and chronic joint pain. Meta-analyses demonstrate powerful joint-preserving natural compounds that inhibit COX-2 and 5-LOX inflammatory cascades.",
        "tier1_supplements": [
            {"name": "Curcumin Phytosome (Meriva / BCM-95)", "evidence": "Grade A", "magnitude": "High", "dose": "500mg - 1000mg daily", "notes": "Matched pharmaceutical NSAIDs (Ibuprofen 400mg) in WOMAC pain reduction across multiple 8-week trials with zero GI ulcers."},
            {"name": "Boswellia Serrata (AKBA)", "evidence": "Grade A", "magnitude": "Moderate", "dose": "100mg - 250mg (ApresFlex)", "notes": "Potent 5-lipoxygenase (5-LOX) inhibitor; reduces joint pain and improves knee flexion within 7 days."}
        ],
        "tier2_supplements": [
            {"name": "Hydrolyzed Collagen Peptides", "evidence": "Grade B", "magnitude": "Moderate", "dose": "10g - 15g daily", "notes": "Stimulates chondrocyte biosynthesis of extracellular matrix and Type II collagen."},
            {"name": "Glucosamine Sulfate + Chondroitin", "evidence": "Grade B", "magnitude": "Minor", "dose": "1500mg / 1200mg", "notes": "Provides structural glycosaminoglycan building blocks; modest benefits for moderate-to-severe joint narrowing."}
        ],
        "ineffective_supplements": [
            {"name": "Glucosamine Hydrochloride (HCl)", "evidence": "Grade D", "notes": "Consistently fails to show statistical efficacy compared to the Sulfate formulation."}
        ],
        "lifestyle_factors": [
            "Low-impact resistance training through full range of motion to stimulate synovial fluid exchange.",
            "Maintain healthy body weight (every 1 lb of fat loss relieves 4 lbs of knee joint pressure)."
        ]
    },
    {
        "slug": "sarcopenia-muscle-loss",
        "name": "Sarcopenia & Age-Related Muscle Loss",
        "category": "Performance & Muscle",
        "overview": "Involuntary loss of skeletal muscle mass, strength, and contractile function occurring with advancing age. Clinical nutrition protocols emphasize satellite cell activation and mTOR stimulation.",
        "tier1_supplements": [
            {"name": "Creatine Monohydrate", "evidence": "Grade A", "magnitude": "High", "dose": "5g daily", "notes": "The single most proven compound to prevent muscle wasting; increases lean mass, isometric strength, and functional mobility in older adults."},
            {"name": "Whey Protein Isolate / Essential Amino Acids", "evidence": "Grade A", "magnitude": "High", "dose": "25g - 40g (with >3g leucine per bolus)", "notes": "Overcomes age-related anabolic resistance by triggering muscle protein synthesis (MPS)."}
        ],
        "tier2_supplements": [
            {"name": "Vitamin D3", "evidence": "Grade B", "magnitude": "Moderate", "dose": "2000IU - 4000IU daily", "notes": "Maintains type II fast-twitch muscle fiber morphology and decreases fall risk in seniors."},
            {"name": "Omega-3 Fatty Acids", "evidence": "Grade B", "magnitude": "Moderate", "dose": "2g - 3g daily", "notes": "Sensitizes muscle tissue to hyperaminoacidemia and reduces chronic low-grade anabolic blunting."}
        ],
        "ineffective_supplements": [
            {"name": "Glutamine alone for muscle building", "evidence": "Grade D", "notes": "Splanchnic bed extracts >85% of oral glutamine before reaching systemic circulation."}
        ],
        "lifestyle_factors": [
            "Progressive resistance training targeting compound movements at 65-80% 1RM 2-3 days per week.",
            "Distribute protein intake evenly across 3-4 meals daily (0.4g/kg per meal)."
        ]
    },
    {
        "slug": "hypertension-blood-pressure",
        "name": "Hypertension & Elevated Blood Pressure",
        "category": "Cardiovascular",
        "overview": "Persistent elevation of systemic arterial pressure exceeding 130/80 mmHg. Clinical trials validate nutraceuticals that upregulate endothelial nitric oxide synthase (eNOS) and reduce arterial stiffness.",
        "tier1_supplements": [
            {"name": "Potassium Citrate", "evidence": "Grade A", "magnitude": "High", "dose": "1500mg - 3000mg from diet/supplement", "notes": "Promotes natriuresis and arterial vasodilation; reduces systolic BP by an average of 4-7 mmHg in meta-analyses."},
            {"name": "Garlic Extract (Aged Garlic / Kyolic)", "evidence": "Grade A", "magnitude": "Moderate", "dose": "600mg - 1200mg daily", "notes": "Stimulates endothelial nitric oxide and H2S production; lowers SBP by ~8 mmHg and DBP by ~5 mmHg."}
        ],
        "tier2_supplements": [
            {"name": "Magnesium (Taurate / Glycinate)", "evidence": "Grade B", "magnitude": "Moderate", "dose": "300mg - 400mg elemental", "notes": "Natural calcium channel blocker in vascular smooth muscle; provides mild, steady hypotensive support."},
            {"name": "L-Citrulline", "evidence": "Grade B", "magnitude": "Moderate", "dose": "3g - 6g daily", "notes": "Superior to L-Arginine for elevating systemic plasma arginine and vascular nitric oxide."}
        ],
        "ineffective_supplements": [
            {"name": "High-Dose Sodium Bicarbonate", "evidence": "Grade D", "notes": "Excessive sodium load directly exacerbates volume-dependent hypertension."}
        ],
        "lifestyle_factors": [
            "DASH dietary pattern: high potassium, magnesium, calcium, low refined sodium.",
            "Isometric handgrip training: 4 x 2-minute squeezes at 30% MVC, 3 times per week (drops SBP by 8-10 mmHg)."
        ]
    },
    {
        "slug": "hyperlipidemia-cholesterol",
        "name": "Hyperlipidemia & Elevated LDL/ApoB",
        "category": "Cardiovascular",
        "overview": "Elevated circulating concentrations of atherogenic lipoproteins (ApoB, LDL-C, small dense LDL) and triglycerides driving endothelial plaque formation.",
        "tier1_supplements": [
            {"name": "Berberine HCl", "evidence": "Grade A", "magnitude": "High", "dose": "500mg (2-3x daily)", "notes": "Upregulates hepatic LDLR expression by stabilizing LDLR mRNA via PCSK9 inhibition; lowers LDL-C by 15-25% and triglycerides by 20-35%."},
            {"name": "Soluble Viscous Fiber (Psyllium Husk / Beta-Glucan)", "evidence": "Grade A", "magnitude": "Moderate", "dose": "7g - 10g daily before meals", "notes": "Binds bile acids in gut lumen, forcing liver to deplete circulating cholesterol pools for bile resynthesis."}
        ],
        "tier2_supplements": [
            {"name": "Plant Phytosterols", "evidence": "Grade B", "magnitude": "Moderate", "dose": "1.5g - 2g daily", "notes": "Displaces dietary and biliary cholesterol from mixed micelles, lowering LDL-C by 8-10%."},
            {"name": "Omega-3 Ethyl Esters / EPA", "evidence": "Grade B", "magnitude": "High (Triglycerides)", "dose": "2g - 4g daily", "notes": "Dramatically reduces serum triglycerides by 25-40% via suppression of hepatic VLDL synthesis."}
        ],
        "ineffective_supplements": [
            {"name": "Flaxseed Oil for EPA conversion", "evidence": "Grade D", "notes": "Human conversion of ALA to EPA is <5% and to DHA <0.5%."}
        ],
        "lifestyle_factors": [
            "Replace saturated dietary fats (butter, palm, fatty meats) with monounsaturated fats (extra virgin olive oil, avocados).",
            "Eliminate all industrial trans-fats and ultra-processed carbohydrates."
        ]
    },
    {
        "slug": "nafld-fatty-liver",
        "name": "Non-Alcoholic Fatty Liver Disease (NAFLD)",
        "category": "Liver & Detox",
        "overview": "Hepatic steatosis (>5% fat accumulation) in hepatocytes without significant alcohol intake, driven by insulin resistance, lipotoxicity, and mitochondrial oxidative stress.",
        "tier1_supplements": [
            {"name": "Omega-3 Fatty Acids (EPA/DHA)", "evidence": "Grade A", "magnitude": "High", "dose": "2g - 3g daily", "notes": "Inhibits SREBP-1c and upregulates PPAR-alpha; proven in ultrasound and MRI trials to decrease hepatic intrahepatic lipid content."},
            {"name": "Vitamin E (d-alpha-tocopherol)", "evidence": "Grade A", "magnitude": "Moderate", "dose": "800 IU daily (in non-diabetic NASH)", "notes": "Validated in the PIVENS trial; significantly reduces histological hepatic steatosis and ballooning degeneration."}
        ],
        "tier2_supplements": [
            {"name": "Milk Thistle (Standardized Silymarin)", "evidence": "Grade B", "magnitude": "Moderate", "dose": "140mg - 420mg daily", "notes": "Membrane stabilizer and antioxidant; consistently lowers elevated ALT and AST transaminases."},
            {"name": "Choline (Phosphatidylcholine)", "evidence": "Grade B", "magnitude": "Moderate", "dose": "500mg daily", "notes": "Essential for VLDL assembly; deficiency causes rapid fat accumulation in hepatocytes."}
        ],
        "ineffective_supplements": [
            {"name": "Detox cleanse teas / juice cleanses", "evidence": "Grade D", "notes": "High fructose loads in juice cleanses exacerbate de novo lipogenesis in the liver."}
        ],
        "lifestyle_factors": [
            "Strictly eliminate high-fructose corn syrup and sugar-sweetened beverages.",
            "Weight loss of 7-10% body weight induces complete histological resolution of NASH in over 80% of patients."
        ]
    },
    {
        "slug": "ibs-gut-health",
        "name": "Irritable Bowel Syndrome (IBS)",
        "category": "Gut Health",
        "overview": "Disorder of gut-brain interaction featuring abdominal pain, bloating, and altered bowel habits (diarrhea IBS-D, constipation IBS-C, or mixed IBS-M).",
        "tier1_supplements": [
            {"name": "Enteric-Coated Peppermint Oil", "evidence": "Grade A", "magnitude": "High", "dose": "0.2ml - 0.4ml (3x daily before meals)", "notes": "L-menthol acts as a natural calcium antagonist in smooth muscle, eliminating colonic spasms and abdominal pain."},
            {"name": "Partially Hydrolyzed Guar Gum (PHGG)", "evidence": "Grade A", "magnitude": "Moderate", "dose": "5g daily", "notes": "Water-soluble non-gas-producing prebiotic fiber; regulates transit time and normalizes Bristol stool scale."}
        ],
        "tier2_supplements": [
            {"name": "Multi-Strain Probiotics (Bifidobacterium infantis 35624)", "evidence": "Grade B", "magnitude": "Moderate", "dose": "10-50 Billion CFU", "notes": "Reduces mucosal cytokine release and relieves chronic subjective bloating."},
            {"name": "L-Glutamine", "evidence": "Grade B", "magnitude": "Moderate", "dose": "5g - 15g daily", "notes": "Primary fuel for enterocytes; documented to heal tight junctions in post-infectious IBS."}
        ],
        "ineffective_supplements": [
            {"name": "Inulin / FOS prebiotics in acute IBS", "evidence": "Grade D", "notes": "Rapidly fermentable FODMAPs that cause intense colonic gas, distension, and severe pain."}
        ],
        "lifestyle_factors": [
            "Low FODMAP elimination diet (4-6 weeks under clinical supervision) followed by systematic reintroduction.",
            "Diaphragmatic breathing and gut-directed hypnotherapy."
        ]
    },
    {
        "slug": "gerd-acid-reflux",
        "name": "GERD & Gastric Acid Reflux",
        "category": "Gut Health",
        "overview": "Retrograde flow of gastric contents into the esophagus causing heartburn, regurgitation, mucosal erosion, and chronic cough.",
        "tier1_supplements": [
            {"name": "Zinc Carnosine", "evidence": "Grade A", "magnitude": "High", "dose": "75mg - 150mg daily", "notes": "Adheres specifically to gastric and esophageal ulcerations, accelerating epithelial mucosal repair."},
            {"name": "Sodium Alginate (Raft-Forming)", "evidence": "Grade A", "magnitude": "High", "dose": "500mg - 1000mg post-meals", "notes": "Forms a mechanical viscous raft floating on top of gastric contents, physically blocking acid reflux into the esophagus."}
        ],
        "tier2_supplements": [
            {"name": "Deglycyrrhizinated Licorice (DGL)", "evidence": "Grade B", "magnitude": "Moderate", "dose": "400mg chewable before meals", "notes": "Stimulates local mucosal secretion and blood flow without glycyrrhizin-induced pseudoaldosteronism."},
            {"name": "Melatonin", "evidence": "Grade B", "magnitude": "Moderate", "dose": "3mg at bedtime", "notes": "Lower esophageal sphincter (LES) contains melatonin receptors; trial shows enhanced LES tone and acid reduction."}
        ],
        "ineffective_supplements": [
            {"name": "Apple Cider Vinegar during active esophagitis", "evidence": "Grade D", "notes": "Directly burns denuded, ulcerated esophageal squamous epithelium."}
        ],
        "lifestyle_factors": [
            "Elevate head of bed by 6 inches using bed risers.",
            "Strictly avoid food or caloric fluids within 3 hours of reclining."
        ]
    },
    {
        "slug": "chronic-migraines",
        "name": "Chronic Migraines & Neurovascular Pain",
        "category": "Brain & Focus",
        "overview": "Recurrent debilitating headache attacks associated with cortical spreading depression, trigeminovascular activation, and mitochondrial cerebral energy deficits.",
        "tier1_supplements": [
            {"name": "Riboflavin (Vitamin B2)", "evidence": "Grade A", "magnitude": "High", "dose": "400mg daily", "notes": "Critical cofactor for mitochondrial complex I & II; multiple RCTs show a 50% reduction in monthly migraine frequency."},
            {"name": "Magnesium (Glycinate / Citrate)", "evidence": "Grade A", "magnitude": "Moderate", "dose": "400mg - 600mg daily", "notes": "Prevents cerebral vasospasm and antagonizes NMDA receptor hyper-excitability; lowers migraine intensity."}
        ],
        "tier2_supplements": [
            {"name": "Coenzyme Q10 (CoQ10)", "evidence": "Grade B", "magnitude": "Moderate", "dose": "150mg - 300mg daily", "notes": "Restores brain mitochondrial electron transport; significantly reduces headache days."},
            {"name": "Butterbur Extract (Petasites - PA-free)", "evidence": "Grade B", "magnitude": "Moderate", "dose": "75mg (2x daily)", "notes": "Potent anti-spasmodic and anti-inflammatory; must be certified pyrrolizidine alkaloid (PA) free to protect liver."}
        ],
        "ineffective_supplements": [
            {"name": "Feverfew non-standardized powders", "evidence": "Grade D", "notes": "Inconsistent clinical trial outcomes with crude unstandardized plant material."}
        ],
        "lifestyle_factors": [
            "Maintain strict meal timing to avoid hypoglycemia-triggered cortical spreading depression.",
            "Consistent sleep schedule (sleep deprivation or oversleeping both trigger migraine attacks)."
        ]
    },
    {
        "slug": "pcos-hormonal",
        "name": "Polycystic Ovary Syndrome (PCOS)",
        "category": "Hormones",
        "overview": "Complex endocrine disorder characterized by hyperandrogenism, ovulatory dysfunction, polycystic ovarian morphology, and hyperinsulinemia.",
        "tier1_supplements": [
            {"name": "Myo-Inositol + D-Chiro-Inositol (40:1 Ratio)", "evidence": "Grade A", "magnitude": "High", "dose": "2000mg Myo + 50mg D-Chiro (2x daily)", "notes": "Restores physiological ovarian insulin signaling, normalizes LH/FSH ratios, and induces spontaneous ovulation in ~70% of trials."},
            {"name": "Berberine HCl", "evidence": "Grade A", "magnitude": "Moderate", "dose": "500mg (2-3x daily)", "notes": "Reduces visceral adiposity, lowers free testosterone, and matches metformin in improving pregnancy rates."}
        ],
        "tier2_supplements": [
            {"name": "N-Acetyl Cysteine (NAC)", "evidence": "Grade B", "magnitude": "Moderate", "dose": "600mg (3x daily)", "notes": "Improves insulin sensitivity and oocyte quality; acts as a mild ovulation inducer."},
            {"name": "Vitamin D3", "evidence": "Grade B", "magnitude": "Moderate", "dose": "2000IU - 4000IU daily", "notes": "Modulates AMH levels and improves follicular maturation in vitamin D deficient women."}
        ],
        "ineffective_supplements": [
            {"name": "D-Chiro-Inositol alone in high doses", "evidence": "Grade D", "notes": "High doses of D-chiro alone impair oocyte quality and blastocyst development."}
        ],
        "lifestyle_factors": [
            "Low glycemic index diet to prevent postprandial insulin surges that stimulate theca cell androgen production.",
            "High-intensity interval training (HIIT) to improve peripheral insulin receptor sensitivity."
        ]
    },
    {
        "slug": "hypothyroidism-hashimotos",
        "name": "Hashimoto's Thyroiditis / Hypothyroidism",
        "category": "Hormones",
        "overview": "Autoimmune destruction of thyroid follicles mediated by anti-TPO and anti-Tg antibodies, resulting in subclinical or overt hypothyroidism and metabolic slowing.",
        "tier1_supplements": [
            {"name": "Selenium (L-Selenomethionine)", "evidence": "Grade A", "magnitude": "High", "dose": "100mcg - 200mcg daily", "notes": "Essential for iodothyronine deiodinase and glutathione peroxidase; shown in meta-analyses to drop anti-TPO antibody titers by 30-50% within 3-6 months."},
            {"name": "Myo-Inositol + Selenium", "evidence": "Grade A", "magnitude": "Moderate", "dose": "600mg Inositol + 83mcg Selenium", "notes": "Dual therapy demonstrated significant reduction in TSH and normalized thyroid ultrasound echogenicity."}
        ],
        "tier2_supplements": [
            {"name": "Vitamin D3", "evidence": "Grade B", "magnitude": "Moderate", "dose": "3000IU - 5000IU daily", "notes": "Downregulates Th17 autoimmune cascades and reduces autoantibody generation."},
            {"name": "Zinc Bisglycinate", "evidence": "Grade B", "magnitude": "Moderate", "dose": "15mg - 30mg daily", "notes": "Required for the conversion of thyroxine (T4) into active triiodothyronine (T3)."}
        ],
        "ineffective_supplements": [
            {"name": "Excess Iodine / Kelp supplements (>500mcg)", "evidence": "Grade D", "notes": "Wolff-Chaikoff effect triggers dramatic autoimmune flare-up and exacerbates thyroid destruction."}
        ],
        "lifestyle_factors": [
            "Screen for and eliminate gluten if celiac/non-celiac gluten sensitivity is present (molecular mimicry with thyroid tissue).",
            "Manage stress to prevent cortisol-mediated inhibition of T4 to T3 deiodination."
        ]
    },
    {
        "slug": "bph-prostate",
        "name": "Benign Prostatic Hyperplasia (BPH)",
        "category": "Hormones",
        "overview": "Non-malignant adenomatous proliferation of prostate stromal and epithelial cells causing lower urinary tract symptoms (LUTS), weak stream, and nocturia.",
        "tier1_supplements": [
            {"name": "Saw Palmetto Extract (Liposterolic Extract)", "evidence": "Grade A", "magnitude": "Moderate", "dose": "320mg daily (standardized to 85-95% fatty acids)", "notes": "Inhibits 5-alpha-reductase and alpha-1-adrenergic receptors; clinical trials show improved peak urinary flow and reduced International Prostate Symptom Scores (IPSS)."},
            {"name": "Beta-Sitosterol", "evidence": "Grade A", "magnitude": "Moderate", "dose": "60mg - 130mg daily", "notes": "Plant sterol demonstrated in Cochrane reviews to significantly improve urinary flow and reduce residual urine volume."}
        ],
        "tier2_supplements": [
            {"name": "Pygeum Africanum", "evidence": "Grade B", "magnitude": "Moderate", "dose": "100mg - 200mg daily", "notes": "Reduces prostatic inflammation and inhibits bladder hyperactivity."},
            {"name": "Zinc Picolinate", "evidence": "Grade B", "magnitude": "Minor", "dose": "15mg - 30mg daily", "notes": "Prostate contains the highest concentration of zinc in human tissue; supports local cellular homeostasis."}
        ],
        "ineffective_supplements": [
            {"name": "Crude Saw Palmetto Berry Powder (non-extract)", "evidence": "Grade D", "notes": "Lacks the liposterolic concentration necessary to inhibit 5-alpha reductase."}
        ],
        "lifestyle_factors": [
            "Avoid fluid intake within 2 hours of bedtime to prevent severe nocturia.",
            "Limit alcohol and caffeine which irritate the detrusor muscle."
        ]
    },
    {
        "slug": "erectile-dysfunction-libido",
        "name": "Erectile Dysfunction & Microvascular Impairment",
        "category": "Hormones",
        "overview": "Inability to achieve or maintain penile tumescence sufficient for satisfactory sexual performance, predominantly caused by endothelial nitric oxide deficiency or psychogenic stress.",
        "tier1_supplements": [
            {"name": "L-Citrulline", "evidence": "Grade A", "magnitude": "High", "dose": "1.5g - 3g daily", "notes": "Significantly elevates plasma L-arginine and cGMP production in cavernous endothelial cells; proven to reverse mild-to-moderate arteriogenic ED."},
            {"name": "Panax Ginseng (Korean Red Ginseng)", "evidence": "Grade A", "magnitude": "Moderate", "dose": "1000mg (3x daily)", "notes": "Ginsenosides upregulate eNOS release in corpus cavernosum; validated in multiple randomized clinical trials."}
        ],
        "tier2_supplements": [
            {"name": "Tongkat Ali (Eurycoma longifolia)", "evidence": "Grade B", "magnitude": "Moderate", "dose": "200mg - 400mg (100:1 extract)", "notes": "Liberates free testosterone from sex hormone-binding globulin (SHBG) and restores libido."},
            {"name": "Pycnogenol (French Maritime Pine Bark)", "evidence": "Grade B", "magnitude": "Moderate", "dose": "120mg daily", "notes": "Acts synergistically with L-Arginine/Citrulline to accelerate endothelial nitric oxide production."}
        ],
        "ineffective_supplements": [
            {"name": "Tribulus Terrestris for testosterone elevation", "evidence": "Grade D", "notes": "Zero evidence of elevating serum free or total testosterone in healthy men despite libido perception."}
        ],
        "lifestyle_factors": [
            "Cardiovascular exercise (minimum 160 minutes/week) to restore systemic endothelial flow-mediated dilation.",
            "Optimize sleep to support nocturnal LH pulses and peak early morning testosterone production."
        ]
    },
    {
        "slug": "doms-muscle-soreness",
        "name": "Muscle Soreness (DOMS) & Tendinopathy",
        "category": "Performance & Muscle",
        "overview": "Eccentric exercise-induced mechanical micro-trauma, Z-disc disruption, and acute inflammatory neutrophil infiltration resulting in peak soreness 24-72 hours post-exercise.",
        "tier1_supplements": [
            {"name": "Tart Cherry Extract (Anthocyanins)", "evidence": "Grade A", "magnitude": "High", "dose": "480mg extract or 30ml concentrate (2x daily)", "notes": "Potent inhibition of COX-1 and COX-2; reduces isometric strength loss and suppresses serum creatine kinase spikes post-eccentric training."},
            {"name": "Omega-3 Fatty Acids (EPA/DHA)", "evidence": "Grade A", "magnitude": "Moderate", "dose": "2g - 3g daily", "notes": "Attenuates inflammatory eicosanoids (PGE2) and significantly reduces subjective muscle soreness after unaccustomed lifting."}
        ],
        "tier2_supplements": [
            {"name": "Curcumin Phytosome", "evidence": "Grade B", "magnitude": "Moderate", "dose": "500mg - 1000mg", "notes": "Blunts IL-6 and TNF-alpha elevation, accelerating functional muscle recovery."},
            {"name": "Branched-Chain Amino Acids (BCAAs) in fasted states", "evidence": "Grade B", "magnitude": "Minor", "dose": "5g - 10g", "notes": "Provides slight attenuation of DOMS if overall daily dietary protein is insufficient."}
        ],
        "ineffective_supplements": [
            {"name": "High-dose Vitamin C & E immediately post-workout", "evidence": "Grade D", "notes": "Blunts the adaptive ROS signaling required for mitochondrial biogenesis and muscular hypertrophy."}
        ],
        "lifestyle_factors": [
            "Active recovery: low-intensity cycling or walking (20 mins) to enhance capillary clearance of metabolites.",
            "Adequate sleep duration for growth hormone secretion and myofibrillar repair."
        ]
    },
    {
        "slug": "upper-respiratory-infections",
        "name": "Upper Respiratory Infections (Cold & Flu)",
        "category": "Immunity",
        "overview": "Viral infections of the upper respiratory tract (Rhinovirus, Influenza, Coronaviruses) presenting with rhinorrhea, pharyngitis, cough, and immune fatigue.",
        "tier1_supplements": [
            {"name": "Zinc Acetate / Gluconate Lozenges", "evidence": "Grade A", "magnitude": "High", "dose": "75mg - 80mg elemental daily (dissolved slowly every 2-3 hours)", "notes": "Free ionic zinc directly inhibits viral replication in the oropharyngeal mucosa; Cochrane reviews prove a 33% reduction in cold duration when started within 24h."},
            {"name": "Vitamin D3 (Prophylaxis)", "evidence": "Grade A", "magnitude": "High", "dose": "2000IU - 5000IU daily", "notes": "Upregulates cathelicidins and defensins; dramatically reduces incidence of acute respiratory tract infections in baseline deficient subjects."}
        ],
        "tier2_supplements": [
            {"name": "Elderberry Extract (Sambucus nigra)", "evidence": "Grade B", "magnitude": "Moderate", "dose": "600mg - 900mg daily", "notes": "Blocks viral hemagglutinin glycoproteins; shortens flu duration by ~2 days in clinical trials."},
            {"name": "Vitamin C", "evidence": "Grade B", "magnitude": "Minor", "dose": "1g - 2g daily", "notes": "Slightly reduces duration and severity of cold symptoms in physically active individuals."}
        ],
        "ineffective_supplements": [
            {"name": "Echinacea after symptoms have peaked (>48 hours)", "evidence": "Grade D", "notes": "Minimal clinical efficacy once systemic viral replication has already fully established."}
        ],
        "lifestyle_factors": [
            "Frequent hand washing and nasal saline irrigation.",
            "Prioritize 8+ hours of uninterrupted sleep upon first onset of tickle or fatigue."
        ]
    },
    {
        "slug": "chronic-fatigue-syndrome",
        "name": "Chronic Fatigue Syndrome (ME/CFS)",
        "category": "Longevity & Health",
        "overview": "Complex, multi-system chronic illness characterized by profound, incapacitating fatigue, post-exertional malaise (PEM), and cellular bioenergetic collapse.",
        "tier1_supplements": [
            {"name": "Coenzyme Q10 + NADH", "evidence": "Grade A", "magnitude": "High", "dose": "200mg CoQ10 + 20mg NADH daily", "notes": "Validated in multiple randomized controlled trials to enhance mitochondrial ATP production and significantly decrease chronic fatigue scores."},
            {"name": "Acetyl-L-Carnitine (ALCAR)", "evidence": "Grade A", "magnitude": "Moderate", "dose": "1000mg - 2000mg daily", "notes": "Facilitates long-chain fatty acid transport into the mitochondrial matrix for beta-oxidation; improves cognitive and physical stamina."}
        ],
        "tier2_supplements": [
            {"name": "Magnesium Malate", "evidence": "Grade B", "magnitude": "Moderate", "dose": "300mg - 400mg elemental", "notes": "Malic acid is an essential Krebs cycle intermediate; alleviates cellular muscle exhaustion and tender points."},
            {"name": "Rhodiola Rosea", "evidence": "Grade B", "magnitude": "Moderate", "dose": "200mg - 400mg daily", "notes": "Modulates cellular stress responses and supports adrenal output without exhaustion crashes."}
        ],
        "ineffective_supplements": [
            {"name": "High-dose synthetic energy drinks / Guaraná", "evidence": "Grade D", "notes": "Causes catastrophic post-exertional crashes and severe adrenal exhaustion."}
        ],
        "lifestyle_factors": [
            "Strict pacing protocol: stop activities before reaching the anaerobic threshold to avoid triggering post-exertional malaise (PEM).",
            "Heart rate variability (HRV) biofeedback monitoring."
        ]
    },
    {
        "slug": "osteoporosis-bone-density",
        "name": "Osteoporosis & Bone Mineral Density Loss",
        "category": "Joint & Bone",
        "overview": "Microarchitectural deterioration of bone tissue and low bone mass leading to fragility fractures, primarily driven by osteoclast hyper-resorption and estrogen withdrawal.",
        "tier1_supplements": [
            {"name": "Vitamin D3 + Vitamin K2 (MK-7)", "evidence": "Grade A", "magnitude": "High", "dose": "2000IU D3 + 100mcg - 180mcg K2 daily", "notes": "Vitamin D enhances intestinal calcium absorption while K2 carboxylates osteocalcin, directly depositing calcium into the hydroxyapatite matrix instead of arterial walls."},
            {"name": "Calcium (Citrate / Hydroxyapatite)", "evidence": "Grade A", "magnitude": "Moderate", "dose": "500mg - 800mg (diet + supplement)", "notes": "Essential structural mineral substrate; modest reductions in fracture risk when paired with Vitamin D."}
        ],
        "tier2_supplements": [
            {"name": "Magnesium Glycinate", "evidence": "Grade B", "magnitude": "Moderate", "dose": "250mg - 350mg elemental", "notes": "Cofactor for alkaline phosphatase; improves bone mineral density and prevents brittle crystalline structure."},
            {"name": "Boron (Glycinate / Citrate)", "evidence": "Grade B", "magnitude": "Moderate", "dose": "3mg - 6mg daily", "notes": "Significantly decreases urinary excretion of calcium and magnesium and elevates 17-beta estradiol in post-menopausal women."}
        ],
        "ineffective_supplements": [
            {"name": "Single mega-dose Calcium Carbonate (>1200mg bolus)", "evidence": "Grade D", "notes": "Exceeds intestinal absorption capacity, causes arterial calcification, severe constipation, and kidney stones."}
        ],
        "lifestyle_factors": [
            "Axial loading resistance training (deadlifts, squats) and impact loading (jumping) to stimulate osteoblast mechanotransduction.",
            "Smoking cessation and moderate alcohol intake (both directly suppress osteoblast function)."
        ]
    },
    {
        "slug": "systemic-chronic-inflammation",
        "name": "Systemic Chronic Inflammation (High hs-CRP)",
        "category": "Immunity",
        "overview": "Low-grade, non-resolving systemic inflammatory state marked by elevated high-sensitivity C-reactive protein (hs-CRP), IL-6, and TNF-alpha, underlying cardiometabolic and neurodegenerative disease.",
        "tier1_supplements": [
            {"name": "Curcumin Phytosome (Meriva / BCM-95)", "evidence": "Grade A", "magnitude": "High", "dose": "500mg - 1000mg daily", "notes": "Potent NF-kB pathway down-regulator; meta-analyses show consistent and significant reductions in circulating hs-CRP, IL-6, and TNF-alpha."},
            {"name": "Omega-3 Fatty Acids (EPA/DHA)", "evidence": "Grade A", "magnitude": "High", "dose": "2g - 4g daily", "notes": "Displaces arachidonic acid from cell membranes and yields specialized pro-resolving mediators (resolvins, protectins)."}
        ],
        "tier2_supplements": [
            {"name": "Resveratrol (Trans-Resveratrol)", "evidence": "Grade B", "magnitude": "Moderate", "dose": "150mg - 500mg daily", "notes": "Activates SIRT1 and AMPK, suppressing vascular endothelial inflammatory expression."},
            {"name": "Quercetin Phytosome", "evidence": "Grade B", "magnitude": "Moderate", "dose": "500mg daily", "notes": "Flavonoid with powerful antioxidant and mast-cell stabilizing anti-inflammatory properties."}
        ],
        "ineffective_supplements": [
            {"name": "Unformulated standard Turmeric powder", "evidence": "Grade D", "notes": "Extremely poor bioavailability (<1% absorption); almost entirely metabolized in the intestinal mucosa without reaching systemic circulation."}
        ],
        "lifestyle_factors": [
            "Anti-inflammatory Mediterranean dietary pattern rich in polyphenol-dense berries, wild fatty fish, and extra-virgin olive oil.",
            "Attain 7-9 hours of deep sleep to clear circulating inflammatory markers."
        ]
    },
    {
        "slug": "hair-thinning-alopecia",
        "name": "Androgenetic Alopecia & Hair Thinning",
        "category": "Hormones",
        "overview": "Progressive miniaturization of genetically susceptible scalp hair follicles driven by local tissue dihydrotestosterone (DHT) binding and microvascular fibrosis.",
        "tier1_supplements": [
            {"name": "Standardized Saw Palmetto Extract", "evidence": "Grade A", "magnitude": "Moderate", "dose": "320mg daily (85-95% fatty acids)", "notes": "Inhibits type I & II 5-alpha reductase; multiple clinical trials document stabilized hair count and subjective density improvements in mild-to-moderate androgenetic alopecia."},
            {"name": "Rosemary Oil (Topical 1%)", "evidence": "Grade A", "magnitude": "High (Topical)", "dose": "Apply to scalp twice daily", "notes": "Matched pharmaceutical 2% Minoxidil in clinical trials for increasing hair counts after 6 months with significantly less scalp itching."}
        ],
        "tier2_supplements": [
            {"name": "Pumpkin Seed Oil", "evidence": "Grade B", "magnitude": "Moderate", "dose": "400mg daily", "notes": "Contains phytosterols that inhibit 5-alpha-reductase; double-blind trial demonstrated a 40% increase in hair count after 24 weeks."},
            {"name": "Biotin + Zinc", "evidence": "Grade B", "magnitude": "Moderate", "dose": "2.5mg Biotin + 15mg Zinc", "notes": "Essential for keratin synthesis; highly effective if baseline micronutrient deficiency is present."}
        ],
        "ineffective_supplements": [
            {"name": "Massive dose Biotin (>10mg) in non-deficient individuals", "evidence": "Grade D", "notes": "Produces zero hair growth benefits in individuals with normal biotin levels and severely skews clinical lab tests (troponin, thyroid)."}
        ],
        "lifestyle_factors": [
            "Daily scalp massage (4-5 minutes) to stimulate dermal papilla mechanotransduction and subcutaneous perfusion.",
            "Avoid traction hairstyles and excessive heat treatments."
        ]
    },
    {
        "slug": "acne-vulgaris-skin",
        "name": "Acne Vulgaris & Cutaneous Inflammation",
        "category": "Immunity",
        "overview": "Inflammatory pilosebaceous disorder driven by androgen-stimulated sebum overproduction, hyperkeratinization, and Cutibacterium acnes colonization.",
        "tier1_supplements": [
            {"name": "Zinc (Gluconate / Picolinate / Sulfate)", "evidence": "Grade A", "magnitude": "High", "dose": "30mg - 45mg elemental daily", "notes": "Potent anti-bacterial and anti-inflammatory properties; Cochrane reviews confirm substantial reductions in inflammatory papules and pustules comparable to minocycline."},
            {"name": "Omega-3 Fatty Acids (EPA/DHA)", "evidence": "Grade A", "magnitude": "Moderate", "dose": "2g - 3g daily", "notes": "Inhibits leukotriene B4 (LTB4) and downregulates sebum inflammatory cytokine production."}
        ],
        "tier2_supplements": [
            {"name": "Berberine HCl", "evidence": "Grade B", "magnitude": "Moderate", "dose": "500mg daily", "notes": "Downregulates mTORC1 signaling and decreases lipogenesis in sebaceous glands by ~60% in clinical trials."},
            {"name": "Green Tea Extract (EGCG)", "evidence": "Grade B", "magnitude": "Moderate", "dose": "500mg (or 2-3% topical)", "notes": "Inhibits 5-alpha reductase and suppresses IGF-1 mediated sebocyte proliferation."}
        ],
        "ineffective_supplements": [
            {"name": "High-dose Vitamin B12 (>1000mcg) megadoses", "evidence": "Grade D", "notes": "Proven to alter gene expression of skin microbiota and directly trigger acute acneiform eruptions."}
        ],
        "lifestyle_factors": [
            "Eliminate skim milk, whey protein concentrates, and high-glycemic index foods which spike systemic IGF-1.",
            "Use gentle non-comedogenic cleansers and avoid aggressive physical facial scrubbing."
        ]
    },
    {
        "slug": "aerobic-endurance-vo2max",
        "name": "Aerobic Endurance & VO2 Max Deficit",
        "category": "Performance & Muscle",
        "overview": "Limitations in maximal oxygen uptake, submaximal lactate threshold, and mitochondrial efficiency during prolonged cardiovascular exercise.",
        "tier1_supplements": [
            {"name": "Dietary Nitrates (Beetroot Extract)", "evidence": "Grade A", "magnitude": "High", "dose": "400mg - 600mg nitrate (2-3 hours pre-exercise)", "notes": "Reduces oxygen cost of submaximal exercise and extends time-to-exhaustion by 15-25% via enhanced mitochondrial P/O ratio and vasodilation."},
            {"name": "Beta-Alanine", "evidence": "Grade A", "magnitude": "High", "dose": "3.2g - 6.4g daily (chronic)", "notes": "Elevates intramuscular carnosine levels by 60-80%, buffering hydrogen ions and delaying acidosis in efforts lasting 1-10 minutes."}
        ],
        "tier2_supplements": [
            {"name": "Cordyceps Militaris", "evidence": "Grade B", "magnitude": "Moderate", "dose": "1g - 3g standardized extract", "notes": "Improves cellular oxygen utilization and ventilatory threshold during progressive exercise."},
            {"name": "Coenzyme Q10 (Ubiquinol)", "evidence": "Grade B", "magnitude": "Moderate", "dose": "200mg daily", "notes": "Direct electron carrier in the mitochondrial respiratory chain; increases peak power output during prolonged cycling."}
        ],
        "ineffective_supplements": [
            {"name": "L-Carnitine oral without high carbohydrate insulin spike", "evidence": "Grade D", "notes": "Muscle carnitine uptake is negligible without hyperinsulinemia due to OCTN2 transporter kinetics."}
        ],
        "lifestyle_factors": [
            "80/20 polarized training distribution (80% Zone 2 aerobic base, 20% high-intensity VO2 max intervals).",
            "Altitude exposure or heat acclimation protocols (sauna post-run) to stimulate erythropoietin (EPO) and plasma volume expansion."
        ]
    }
]
