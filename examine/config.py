import os
from pathlib import Path
from dotenv import load_dotenv

ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

def get_gemini_api_key() -> str:
    # Check .env or system environment
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""

def get_ncbi_api_key() -> str:
    return os.getenv("NCBI_API_KEY", "")

def set_gemini_api_key(key: str) -> None:
    key = key.strip()
    os.environ["GEMINI_API_KEY"] = key
    _save_to_env("GEMINI_API_KEY", key)

def set_ncbi_api_key(key: str) -> None:
    key = key.strip()
    os.environ["NCBI_API_KEY"] = key
    _save_to_env("NCBI_API_KEY", key)

def _save_to_env(k_name: str, val: str) -> None:
    env_content = {}
    if ENV_PATH.exists():
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    env_content[k.strip()] = v.strip()
    
    env_content[k_name] = val
    
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        for k, v in env_content.items():
            f.write(f"{k}={v}\n")
