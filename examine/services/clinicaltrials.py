import requests
import logging
from typing import List, Dict, Any

logger = logging.getLogger("clinicaltrials-service")

CLINICAL_TRIALS_V2_BASE = "https://clinicaltrials.gov/api/v2/studies"

def search_clinical_trials(query: str, max_results: int = 6) -> List[Dict[str, Any]]:
    """
    Search official US ClinicalTrials.gov registry (v2) for completed human interventional studies
    for a given dietary supplement, bioactive compound, or clinical intervention.
    """
    if not query:
        return []

    params = {
        "query.intr": query,
        "pageSize": max_results,
        "filter.overallStatus": "COMPLETED",
        "format": "json"
    }

    headers = {
        "User-Agent": "Walpar-Clinical-Platform/2.0 (Clinical Nutrition Research; mailto:info@walpar.internal)"
    }

    try:
        response = requests.get(CLINICAL_TRIALS_V2_BASE, params=params, headers=headers, timeout=10)
        if response.status_code != 200:
            logger.warning(f"ClinicalTrials.gov returned status {response.status_code}")
            return []

        data = response.json()
        studies = data.get("studies", [])
        results = []

        for item in studies:
            proto = item.get("protocolSection", {})
            ident = proto.get("identificationModule", {})
            design = proto.get("designModule", {})
            outcomes = proto.get("outcomesModule", {})
            sponsor = proto.get("sponsorCollaboratorsModule", {})
            conditions = proto.get("conditionsModule", {})

            nct_id = ident.get("nctId", "")
            if not nct_id:
                continue

            brief_title = ident.get("briefTitle", "")
            official_title = ident.get("officialTitle", brief_title)

            # Masking / Blinding
            design_info = design.get("designInfo", {})
            masking_info = design_info.get("maskingInfo", {})
            masking = masking_info.get("masking", "OPEN").replace("_", " ").title()
            allocation = design_info.get("allocation", "").replace("_", " ").title()

            study_type = design.get("studyType", "INTERVENTIONAL").replace("_", " ").title()
            design_label = f"{study_type}"
            if allocation:
                design_label += f" | {allocation}"
            if masking:
                design_label += f" | {masking} Masking"

            # Enrollment / Sample size
            enrollment_info = design.get("enrollmentInfo", {})
            sample_size = enrollment_info.get("count", 0)

            # Primary outcomes
            primary_outcomes_raw = outcomes.get("primaryOutcomes", [])
            primary_outcomes = []
            for po in primary_outcomes_raw[:2]:
                measure = po.get("measure", "")
                time_frame = po.get("timeFrame", "")
                if measure:
                    text = measure
                    if time_frame:
                        text += f" ({time_frame})"
                    primary_outcomes.append(text)

            lead_sponsor = sponsor.get("leadSponsor", {}).get("name", "Academic Medical Center")
            cond_list = conditions.get("conditions", [])

            results.append({
                "nct_id": nct_id,
                "title": brief_title or official_title,
                "official_title": official_title,
                "url": f"https://clinicaltrials.gov/study/{nct_id}",
                "study_design": design_label,
                "sample_size": sample_size,
                "sponsor": lead_sponsor,
                "conditions": cond_list[:3],
                "primary_outcomes": primary_outcomes,
                "status": "Completed"
            })

        return results

    except Exception as e:
        logger.error(f"Failed to query ClinicalTrials.gov for {query}: {e}")
        return []

if __name__ == "__main__":
    trials = search_clinical_trials("creatine", max_results=3)
    print(f"Found {len(trials)} trials for Creatine:")
    for t in trials:
        print(f"- [{t['nct_id']}] {t['title']} (N={t['sample_size']}, Design: {t['study_design']})")
