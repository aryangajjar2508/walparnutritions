# Walpar Formula OCR Evaluator & Instant Costing System

A 100% local, offline-capable web application for **Walpar Nutraceuticals**. It allows customers and R&D teams to upload photos of formulas (scanned specs, labels, or handwritten formula sheets), automatically extracts the formulation data with **PaddleOCR**, scientifically evaluates dosage safety and nutrient synergies, enables live formula editing, and calculates an **instant commercial manufacturing quote**.

---

## Key Features

1. **Local PaddleOCR Extraction**:
   - Fast, local optical character recognition using PaddleOCR.
   - Extracts active ingredients, numerical strengths, and units (`mg`, `mcg`, `IU`, `g`).
   - Interactive visual overlay displaying detected bounding boxes directly on the formula image.

2. **Scientific Formulation Evaluation**:
   - **RDA & Safety Limits**: Flags ingredients exceeding safe upper limits or underdosed below clinical efficacy based on FSSAI/ICMR guidelines.
   - **Synergy Detection**: Detects nutrient synergies (e.g., *Curcumin + Piperine* for 2000% absorption, *Immunity Triad: Vit C + Zinc + Vit D3*, *Bone Matrix: D3 + K2-7 + Calcium*, *Joint Triad: Glucosamine + Chondroitin + MSM*).
   - **Interaction & Conflict Warnings**: Detects nutrient competition (e.g., high Calcium + Iron competition, Zinc without Copper balance).
   - **Delivery Form Feasibility**: Calculates total active bulk weight and checks fit inside standard capsules, tablets, gummies, or recommends powder sachets/effervescent tablets.
   - **1-Click AI Add-ons**: Proactively suggests missing bio-enhancers (e.g., 5mg Piperine for Curcumin) with a single click.

3. **Master Pricing & Instant Quote Engine**:
   - Master raw material cost database in INR (₹/kg).
   - Delivery format processing costs (Tableting, Encapsulation, Gummy cooking, Effervescent processing).
   - Packaging options (Alu-PVC Blister, Alu-Alu, HDPE Bottles 30/60, Effervescent Tubes).
   - Volume discount tiers (5k, 10k, 25k, 50k, 100k units).
   - Instant calculation: Per unit price (₹), Price per pack, Total batch cost (ex-factory & with 18% GST).
   - **Printable Official Quotation**: Ready-to-print proforma estimate with customer reference number and delivery terms.

---

## Quick Start

### 1. Launch the Application
Run the launcher script from terminal:
```bash
python run.py
```
This automatically opens your browser to:
```
http://127.0.0.1:8000
```

### 2. How to Use
1. **Upload or Pick a Sample**:
   - Click on any of the preloaded 1-click sample cards (*Immunity Booster*, *Joint Care*, *Curcumin Synergy*, *Sleep & Relax*), or drag & drop your own formula image.
2. **Review Auto-Extraction**:
   - View the uploaded formula image with bounding boxes side-by-side with the parsed ingredient table.
3. **Customize / Edit**:
   - Modify any dosage value or unit.
   - Add new raw materials from the 100+ ingredient database.
   - Switch delivery formats (e.g. from Tablet to Effervescent or Gummy).
   - Change batch quantity to see tier volume discounts (up to 22% OFF).
4. **Get Instant Quote**:
   - All pricing and evaluation badges update in real-time.
   - Click **"Print / Download Quotation"** to export a clean quotation sheet.

---

## Directory Structure
```
Walpar_ocr/
├── app/
│   ├── config.py              # Application settings and paths
│   ├── ocr_engine.py          # PaddleOCR local inference & line grouping
│   ├── formula_parser.py      # Regex & fuzzy entity extraction
│   ├── evaluator.py           # Safety, RDA limits, synergies & form feasibility
│   ├── pricing_engine.py      # Raw material costing, packaging & batch economics
│   ├── main.py                # FastAPI web routes and endpoints
│   └── data/
│       └── ingredients_db.json # 100+ ingredients catalog with prices & rules
├── samples/                   # Pre-generated sample formula images
├── templates/
│   └── index.html             # Responsive single-page web application
├── static/
│   ├── css/styles.css         # Styling & print stylesheets
│   └── js/app.js              # Canvas visualizer & real-time client logic
├── test_pipeline.py           # CLI test script for pipeline verification
├── run.py                     # One-click launcher
└── README.md
```
