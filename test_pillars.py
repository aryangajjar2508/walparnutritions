import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8080"

def test_endpoints():
    print("Testing Walpar API endpoints...")
    
    # 1. Supplements
    r = requests.get(f"{BASE_URL}/api/supplements")
    assert r.status_code == 200, f"Supplements failed: {r.status_code}"
    supps = r.json()
    print(f"PASS: Supplements ({len(supps)} loaded)")
    
    # 2. Conditions
    r = requests.get(f"{BASE_URL}/api/conditions")
    assert r.status_code == 200, f"Conditions failed: {r.status_code}"
    conditions = r.json()
    print(f"PASS: Conditions ({len(conditions)} loaded)")
    
    # 2b. Condition detail
    r = requests.get(f"{BASE_URL}/api/condition/insomnia")
    assert r.status_code == 200, f"Condition detail failed: {r.status_code}"
    insomnia = r.json()
    t1 = insomnia.get('tier1_supplements', [])
    print(f"PASS: Insomnia detail (Tier 1 items: {len(t1)}, e.g. {[x['name'] for x in t1]})")
    
    # 3. Categories
    r = requests.get(f"{BASE_URL}/api/categories")
    assert r.status_code == 200, f"Categories failed: {r.status_code}"
    cats = r.json()
    print(f"PASS: Categories ({len(cats)} loaded)")
    
    # 4. Guides
    r = requests.get(f"{BASE_URL}/api/guides")
    assert r.status_code == 200, f"Guides failed: {r.status_code}"
    guides = r.json()
    print(f"PASS: Guides ({len(guides)} loaded)")
    
    # 4b. Guide detail
    r = requests.get(f"{BASE_URL}/api/guide/deep-sleep-protocol")
    assert r.status_code == 200, f"Guide detail failed: {r.status_code}"
    guide = r.json()
    print(f"PASS: Guide detail: {guide.get('title')}")

    # 5. Symptom AI Consultant
    print("\nTesting Symptom-to-Supplement AI Consultant...")
    symptom_payload = {"symptoms": "Trouble falling asleep, chronic anxiety before bed, and waking up groggy"}
    r = requests.post(f"{BASE_URL}/api/consult/symptoms", json=symptom_payload, timeout=60)
    assert r.status_code == 200, f"Symptom consult failed: {r.text}"
    consult_res = r.json()
    t1_supps = consult_res.get('tier1_protocol', [])
    print(f"PASS: Symptom consult returned analysis! Tier 1 recommendations: {len(t1_supps)}")
    for p in t1_supps:
        print(f"   * {p.get('supplement_name')}: {p.get('exact_dosage')} ({p.get('timing')})")
    print("Biological drivers:", consult_res.get("primary_drivers", []))

    # 6. Custom Formulator Validation
    print("\nTesting Custom Supplement Formulator & Stack Builder...")
    formula_payload = {
        "name": "NeuroCalm Night Stack",
        "goal": "Deep sleep latency reduction and mental tranquility",
        "target_user": "Adults experiencing bedtime anxiety",
        "ingredients": [
            {"name": "Magnesium Glycinate", "dose": "400mg", "form": "Bisglycinate Chelate"},
            {"name": "L-Theanine", "dose": "200mg", "form": "Pure Suntheanine"},
            {"name": "Melatonin", "dose": "0.5mg", "form": "Immediate release"}
        ]
    }
    r = requests.post(f"{BASE_URL}/api/formulator/validate", json=formula_payload, timeout=60)
    assert r.status_code == 200, f"Formulator validation failed: {r.text}"
    val_res = r.json()
    print(f"PASS: Formulator synergy evaluated! Score: {val_res.get('synergy_score')}/100, Safety: {val_res.get('safety_status')}")
    print("Executive Summary:", val_res.get("executive_summary", "")[:120], "...")

    # 7. Ask AI Assistant
    print("\nTesting Ask Walpar AI...")
    ask_payload = {"question": "What is the best form of magnesium for sleep and why?"}
    r = requests.post(f"{BASE_URL}/api/ai/ask", json=ask_payload, timeout=60)
    assert r.status_code == 200, f"Ask AI failed: {r.text}"
    ask_res = r.json()
    print("PASS: WalparAI response received:")
    print(ask_res.get("answer", "")[:160], "...")

    print("\n=======================================================")
    print("ALL WALPAR ENDPOINTS & CLINICAL AI TESTS PASSED 100%!")
    print("=======================================================")

if __name__ == "__main__":
    try:
        test_endpoints()
    except Exception as e:
        print(f"FAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
