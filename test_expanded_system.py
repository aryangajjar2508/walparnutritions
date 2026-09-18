import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8080"

def test_expanded_system():
    print("==================================================")
    print("Testing Walpar Expanded Clinical Architecture")
    print("==================================================")

    # 1. Supplements
    r = requests.get(f"{BASE_URL}/api/supplements")
    assert r.status_code == 200, f"Supplements failed: {r.status_code}"
    supps = r.json()
    print(f"PASS: Supplements Encyclopedia ({len(supps)} compounds loaded)")
    assert len(supps) >= 50, f"Expected >= 50 supplements, found {len(supps)}"

    # 2. Conditions
    r = requests.get(f"{BASE_URL}/api/conditions")
    assert r.status_code == 200, f"Conditions failed: {r.status_code}"
    conditions = r.json()
    print(f"PASS: Clinical Conditions Directory ({len(conditions)} conditions loaded)")
    assert len(conditions) >= 25, f"Expected >= 25 conditions, found {len(conditions)}"

    # 3. Categories
    r = requests.get(f"{BASE_URL}/api/categories")
    assert r.status_code == 200, f"Categories failed: {r.status_code}"
    cats = r.json()
    print(f"PASS: Physiological Categories ({len(cats)} categories loaded)")

    # 4. Guides
    r = requests.get(f"{BASE_URL}/api/guides")
    assert r.status_code == 200, f"Guides failed: {r.status_code}"
    guides = r.json()
    print(f"PASS: Master Protocol Guides ({len(guides)} guides loaded)")

    # 5. ClinicalTrials.gov Dedicated Endpoint
    print("\nTesting ClinicalTrials.gov API v2 Live Service...")
    r = requests.get(f"{BASE_URL}/api/clinicaltrials/ashwagandha", timeout=15)
    assert r.status_code == 200, f"ClinicalTrials.gov failed: {r.status_code}"
    trials = r.json()
    print(f"PASS: ClinicalTrials.gov returned {len(trials)} completed human interventional trials for Ashwagandha!")
    if trials:
        t0 = trials[0]
        print(f"   * [{t0['nct_id']}] {t0['title'][:80]}... (N={t0['sample_size']}, Design: {t0['study_design']})")

    # 6. Supplement Detail with Real-time ClinicalTrials.gov enrichment
    print("\nTesting Supplement Detail Enrichment...")
    r = requests.get(f"{BASE_URL}/api/supplement/creatine", timeout=20)
    assert r.status_code == 200, f"Supplement detail failed: {r.status_code}"
    creatine = r.json()
    ct_data = creatine.get("clinical_trials", [])
    hem_rows = creatine.get("effect_matrix", [])
    pubmed_studies = creatine.get("studies", [])
    print(f"PASS: Creatine Detail Verified:")
    print(f"   * Effect Matrix Outcomes: {len(hem_rows)}")
    print(f"   * Cited PubMed Studies: {len(pubmed_studies)}")
    print(f"   * ClinicalTrials.gov Registered Human Trials: {len(ct_data)}")

    # 7. Test Condition Detail
    r = requests.get(f"{BASE_URL}/api/condition/insomnia")
    assert r.status_code == 200, f"Condition insomnia failed: {r.status_code}"
    insomnia = r.json()
    print(f"\nPASS: Condition 'Insomnia' Detail:")
    print(f"   * Tier 1 Interventions: {[x['name'] for x in insomnia.get('tier1_supplements', [])]}")
    print(f"   * Tier 2 Supportive: {[x['name'] for x in insomnia.get('tier2_supplements', [])]}")
    print(f"   * Ineffective: {[x['name'] for x in insomnia.get('ineffective_supplements', [])]}")

    print("\n==================================================")
    print("ALL 7 CLINICAL DATABASE & API VERIFICATIONS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    try:
        test_expanded_system()
    except Exception as e:
        print(f"FAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
