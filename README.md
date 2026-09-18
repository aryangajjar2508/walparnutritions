# Walpar 🔬

A free, self-hosted, evidence-based nutrition and supplement encyclopedia built for your local computer.

It synthesizes clinical research from the **US National Library of Medicine (PubMed)** and biochemical data from **PubChem** to produce **Walpar-grade Human Effect Matrix (HEM)** tables, recommended dosages, and safety profiles.

---

## ✨ Features

- **Human Effect Matrix (HEM)**: Tables breaking down specific health outcomes (Strength, Sleep Latency, Anxiety, etc.) with:
  - **Effect Magnitude** (High, Moderate, Minor, Ineffective)
  - **Evidence Grade** (Grade A: Strong RCTs, Grade B: Moderate, Grade C: Preliminary)
  - **Study Count & Direct PubMed Citations** (Clickable PMIDs)
- **Live Research Feed (New Articles)**: Real-time clinical trials and systematic reviews published in PubMed with AI study breakdowns.
- **Ask WalparAI**: Interactive clinical assistant answering supplement protocols and interactions.
- **PubChem Biochemical Ribbon**: Live molecular formulas, molecular weights, and PubChem CIDs.
- **Dosage & Usage Guidelines**: Clinically effective daily doses, timing, and optimal forms.
- **Safety & Side Effects**: Documented side effects, safety ratings, and contraindications.
- **Category Explorer**: Filter outcomes by *Physical Performance*, *Sleep & Mood*, *Brain & Focus*, *Immunity*, and *Longevity*.
- **Local SQLite Cache (`examine.db`)**: Every analyzed compound is saved locally. Once loaded, it works completely offline with zero latency.
- **On-Demand AI Synthesis**: Enter any supplement name (e.g. *Zinc, Curcumin, Berberine, Rhodiola*) and the system automatically searches PubMed, pulls trials, and creates a comprehensive monograph.

---

## 🚀 How to Run

### Quick Start (Double Click)
Double-click `run.bat` in this folder. It will start the server and open `http://localhost:8080` in your browser.

### Or Run via Terminal
```bash
python app.py
```
Then open your browser to: **http://localhost:8080**
