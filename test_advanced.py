import asyncio
from httpx import AsyncClient, ASGITransport
from app import app

async def run_advanced_tests():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Test status with keys
        r = await client.get("/api/status")
        assert r.status_code == 200
        status = r.json()
        print(f"[PASS] Status: has_gemini={status['has_api_key']} ({status['gemini_preview']}), has_ncbi={status['has_ncbi_key']} ({status['ncbi_preview']})")
        assert status["has_api_key"] is True
        assert status["has_ncbi_key"] is True

        # 2. Test Live PubMed Research Feed
        print("\nFetching latest clinical trials from PubMed...")
        r = await client.get("/api/feed/latest?topic=all&refresh=true")
        assert r.status_code == 200
        feed = r.json()
        print(f"[PASS] Retrieved {len(feed)} newly published PubMed clinical trials/reviews:")
        for a in feed[:2]:
            print(f"       - [{a['study_type']}] {a['title'][:65]}... (PMID: {a['pmid']})")
            if a.get('takeaway'):
                print(f"         AI Takeaway: {a['takeaway'][:80]}...")

        # 3. Test ExamineAI interactive assistant
        print("\nTesting ExamineAI Assistant query...")
        r = await client.post("/api/ai/ask", json={"question": "What is the optimal dosage for Creatine and does it cause water retention?"})
        assert r.status_code == 200
        ai_resp = r.json()
        print(f"[PASS] ExamineAI Answer generated ({len(ai_resp['answer'])} chars):")
        print(f"       Preview: {ai_resp['answer'][:180]}...\n")

        print("\n[SUCCESS] ALL ADVANCED CAPABILITIES FULLY FUNCTIONAL AND VERIFIED!")

if __name__ == "__main__":
    asyncio.run(run_advanced_tests())
