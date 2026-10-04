import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "app"
DATA_DIR = APP_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads"
SAMPLE_DIR = BASE_DIR / "samples"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

EXCEL_DB_PATH = BASE_DIR / "rate avg.xlsx"
INGREDIENTS_DB_PATH = DATA_DIR / "walpar_master_ingredients.json"
CACHE_DB_PATH = DATA_DIR / "ocr_knowledge_cache.json"
CLOUDFLARE_URL_FILE = DATA_DIR / "cloudflare_url.txt"
EXAMINE_DIR = BASE_DIR / "examine"
EXAMINE_DB_PATH = EXAMINE_DIR / "examine.db"

# Create directories if not exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Google Gemini API Configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-3.6-flash"

# PaddleOCR configuration
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
