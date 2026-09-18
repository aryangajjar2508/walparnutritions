import requests
import xml.etree.ElementTree as ET
import logging
from typing import List, Dict, Any
from config import get_ncbi_api_key

logger = logging.getLogger(__name__)

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def search_pubmed_studies(supplement_name: str, max_results: int = 12) -> List[Dict[str, Any]]:
    """
    Searches PubMed for human clinical trials, RCTs, and meta-analyses on the given supplement.
    Fetches full title, publication year, journal, and abstract for each PMID.
    """
    import re
    # Clean the name: e.g. "Ashwagandha (Withania somnifera)" -> base "Ashwagandha", alt "Withania somnifera"
    base_name = re.sub(r'\(.*?\)', '', supplement_name).strip()
    alt_name = re.search(r'\((.*?)\)', supplement_name)
    alt_name_str = alt_name.group(1).strip() if alt_name else ""
    if alt_name_str and "/" in alt_name_str:
        alt_name_str = alt_name_str.split("/")[0].strip()

    search_terms = base_name or supplement_name.strip()
    if alt_name_str and alt_name_str.lower() not in search_terms.lower():
        search_terms = f"({base_name} OR {alt_name_str})"

    api_key = get_ncbi_api_key()
    headers = {"User-Agent": "Walpar/2.0 (clinical research tool)"}
    
    # 1. Primary clinical trial search
    query = f"{search_terms} AND (clinical trial[Filter] OR randomized controlled trial[Filter] OR meta-analysis[Filter] OR systematic review[Filter] OR human[Filter])"
    
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": max_results,
        "sort": "pub_date"
    }
    if api_key:
        params["api_key"] = api_key

    try:
        r = requests.get(f"{BASE_URL}/esearch.fcgi", params=params, headers=headers, timeout=8)
        data = r.json()
        pmids = data.get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        logger.error(f"PubMed search error: {e}")
        pmids = []

    # Fallback to broader search if few results
    if len(pmids) < 3:
        params["term"] = f"{base_name} AND (supplement[Title/Abstract] OR trial[Title/Abstract] OR human[Filter])"
        try:
            r = requests.get(f"{BASE_URL}/esearch.fcgi", params=params, headers=headers, timeout=8)
            data = r.json()
            more_pmids = data.get("esearchresult", {}).get("idlist", [])
            for p in more_pmids:
                if p not in pmids:
                    pmids.append(p)
            pmids = pmids[:max_results]
        except Exception:
            pass

    # Final fallback if still empty
    if not pmids and base_name:
        params["term"] = f"{base_name}"
        try:
            r = requests.get(f"{BASE_URL}/esearch.fcgi", params=params, headers=headers, timeout=8)
            data = r.json()
            pmids = data.get("esearchresult", {}).get("idlist", [])[:max_results]
        except Exception:
            pass

    if not pmids:
        return []

    # 2. Fetch full XML records for these PMIDs to extract clean abstracts
    fetch_params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml"
    }
    if api_key:
        fetch_params["api_key"] = api_key

    studies = []
    try:
        fetch_resp = requests.get(f"{BASE_URL}/efetch.fcgi", params=fetch_params, headers=headers, timeout=12)
        if fetch_resp.status_code == 200:
            root = ET.fromstring(fetch_resp.content)
            for article in root.findall(".//PubmedArticle"):
                pmid_elem = article.find(".//MedlineCitation/PMID")
                pmid = pmid_elem.text if pmid_elem is not None else ""
                
                title_elem = article.find(".//ArticleTitle")
                title = "".join(title_elem.itertext()).strip() if title_elem is not None else "Untitled Study"
                
                journal_elem = article.find(".//Journal/Title")
                journal = journal_elem.text if journal_elem is not None else "Medical Journal"
                
                year_elem = article.find(".//JournalIssue/PubDate/Year")
                if year_elem is None:
                    year_elem = article.find(".//JournalIssue/PubDate/MedlineDate")
                year = year_elem.text[:4] if year_elem is not None and year_elem.text else "N/A"
                
                abstract_elems = article.findall(".//Abstract/AbstractText")
                abstract_parts = []
                for ab in abstract_elems:
                    label = ab.get("Label")
                    text = "".join(ab.itertext()).strip()
                    if label:
                        abstract_parts.append(f"{label}: {text}")
                    else:
                        abstract_parts.append(text)
                
                abstract = "\n\n".join(abstract_parts) if abstract_parts else "No abstract available in PubMed record."
                
                studies.append({
                    "pmid": pmid,
                    "title": title,
                    "journal": journal,
                    "year": year,
                    "abstract": abstract,
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                })
    except Exception as e:
        logger.error(f"Error parsing PubMed XML: {e}")

    return studies

def get_latest_research_feed(topic: str = "all", max_results: int = 15) -> List[Dict[str, Any]]:
    """
    Fetches the newest published clinical trials and systematic reviews in nutrition & supplementation.
    Sorted by publication date (most recent first).
    """
    api_key = get_ncbi_api_key()
    headers = {"User-Agent": "Walpar/2.0 (clinical research tool)"}

    term_mapping = {
        "all": '("dietary supplements"[MeSH Terms] OR "nutritional supplements"[Title/Abstract] OR "micronutrients"[MeSH Terms]) AND (clinical trial[Filter] OR randomized controlled trial[Filter] OR meta-analysis[Filter])',
        "performance": '("creatine" OR "protein" OR "beta-alanine" OR "sports nutrition") AND (clinical trial[Filter] OR randomized controlled trial[Filter])',
        "sleep": '("sleep" OR "anxiety" OR "stress" OR "melatonin" OR "ashwagandha" OR "magnesium") AND ("dietary supplements"[Filter] OR clinical trial[Filter])',
        "longevity": '("longevity" OR "aging" OR "cardiovascular" OR "omega-3" OR "vitamin d" OR "metabolism") AND (clinical trial[Filter] OR meta-analysis[Filter])',
        "cognition": '("nootropic" OR "memory" OR "cognition" OR "brain" OR "focus") AND ("dietary supplements"[Filter] OR clinical trial[Filter])'
    }

    query = term_mapping.get(topic.lower(), term_mapping["all"])

    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": max_results,
        "sort": "pub_date"
    }
    if api_key:
        params["api_key"] = api_key

    try:
        r = requests.get(f"{BASE_URL}/esearch.fcgi", params=params, headers=headers, timeout=8)
        pmids = r.json().get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        logger.error(f"Failed to search latest feed: {e}")
        return []

    if not pmids:
        return []

    fetch_params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml"
    }
    if api_key:
        fetch_params["api_key"] = api_key

    articles = []
    try:
        resp = requests.get(f"{BASE_URL}/efetch.fcgi", params=fetch_params, headers=headers, timeout=12)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            for article in root.findall(".//PubmedArticle"):
                pmid_elem = article.find(".//MedlineCitation/PMID")
                pmid = pmid_elem.text if pmid_elem is not None else ""

                title_elem = article.find(".//ArticleTitle")
                title = "".join(title_elem.itertext()).strip() if title_elem is not None else "Untitled Study"

                journal_elem = article.find(".//Journal/Title")
                journal = journal_elem.text if journal_elem is not None else "Medical Journal"

                year_elem = article.find(".//JournalIssue/PubDate/Year")
                if year_elem is None:
                    year_elem = article.find(".//JournalIssue/PubDate/MedlineDate")
                year = year_elem.text[:4] if year_elem is not None and year_elem.text else "2026"

                # Author list
                authors = []
                for author in article.findall(".//AuthorList/Author")[:3]:
                    last_name = author.find("LastName")
                    if last_name is not None and last_name.text:
                        authors.append(last_name.text)
                author_str = ", ".join(authors) + (" et al." if len(authors) > 0 else "Research Group")

                # Abstract text
                abstract_elems = article.findall(".//Abstract/AbstractText")
                abstract_parts = []
                for ab in abstract_elems:
                    label = ab.get("Label")
                    text = "".join(ab.itertext()).strip()
                    if label:
                        abstract_parts.append(f"{label}: {text}")
                    else:
                        abstract_parts.append(text)
                abstract = "\n\n".join(abstract_parts) if abstract_parts else "No abstract text provided."

                # Publication Type
                pub_types = [pt.text for pt in article.findall(".//PublicationTypeList/PublicationType") if pt.text]
                study_type = "Clinical Trial"
                for pt in pub_types:
                    if "Randomized Controlled Trial" in pt:
                        study_type = "Randomized Controlled Trial (RCT)"
                        break
                    elif "Meta-Analysis" in pt:
                        study_type = "Meta-Analysis"
                        break
                    elif "Systematic Review" in pt:
                        study_type = "Systematic Review"
                        break

                articles.append({
                    "pmid": pmid,
                    "title": title,
                    "journal": journal,
                    "year": year,
                    "authors": author_str,
                    "study_type": study_type,
                    "abstract": abstract,
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                })
    except Exception as e:
        logger.error(f"Failed to fetch XML for latest feed: {e}")

    return articles
