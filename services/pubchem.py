import requests
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

def get_compound_details(name: str) -> Dict[str, Any]:
    """
    Fetches chemical properties, synonyms, and descriptions for a supplement compound from PubChem.
    Handles cases where the item is a pure chemical or a common botanical.
    """
    clean_name = name.strip()
    result = {
        "name": clean_name,
        "cid": None,
        "formula": "",
        "weight": "",
        "iupac_name": "",
        "description": "",
        "synonyms": [],
        "pubchem_url": ""
    }

    headers = {"User-Agent": "Walpar/2.0 (clinical research tool)"}

    # 1. Fetch Basic Properties
    try:
        prop_url = f"{BASE_URL}/compound/name/{clean_name}/property/MolecularFormula,MolecularWeight,IUPACName,Title/JSON"
        resp = requests.get(prop_url, headers=headers, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            props = data.get("PropertyTable", {}).get("Properties", [])
            if props:
                p = props[0]
                result["cid"] = p.get("CID")
                result["formula"] = p.get("MolecularFormula", "")
                result["weight"] = str(p.get("MolecularWeight", ""))
                result["iupac_name"] = p.get("IUPACName", "")
                if result["cid"]:
                    result["pubchem_url"] = f"https://pubchem.ncbi.nlm.nih.gov/compound/{result['cid']}"
    except Exception as e:
        logger.warning(f"PubChem property fetch error for {clean_name}: {e}")

    # 2. Fetch Description
    try:
        desc_url = f"{BASE_URL}/compound/name/{clean_name}/description/JSON"
        resp = requests.get(desc_url, headers=headers, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            desc_list = data.get("InformationList", {}).get("Information", [])
            descriptions = [item.get("Description") for item in desc_list if item.get("Description")]
            if descriptions:
                result["description"] = descriptions[0]
    except Exception as e:
        logger.warning(f"PubChem description fetch error for {clean_name}: {e}")

    # 3. Fetch Synonyms
    try:
        syn_url = f"{BASE_URL}/compound/name/{clean_name}/synonyms/JSON"
        resp = requests.get(syn_url, headers=headers, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            syn_info = data.get("InformationList", {}).get("Information", [])
            if syn_info and "Synonym" in syn_info[0]:
                # Grab top 6 cleanest synonyms
                syns = syn_info[0]["Synonym"]
                clean_syns = [s for s in syns if len(s) < 40 and not s.isdigit()][:6]
                result["synonyms"] = clean_syns
    except Exception as e:
        logger.warning(f"PubChem synonyms fetch error for {clean_name}: {e}")

    return result

if __name__ == "__main__":
    print(get_compound_details("Creatine"))
