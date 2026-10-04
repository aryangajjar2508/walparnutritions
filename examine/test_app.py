import asyncio
from httpx import AsyncClient, ASGITransport
from app import app

async def run_tests():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Test home page
        r = await client.get("/")
        assert r.status_code == 200, f"Home failed: {r.status_code}"
        print("[PASS] Home page renders 200 OK")

        # 2. Test status API
        r = await client.get("/api/status")
        assert r.status_code == 200
        print(f"[PASS] Status API: {r.json()}")

        # 3. Test supplements list
        r = await client.get("/api/supplements")
        assert r.status_code == 200
        supps = r.json()
        print(f"[PASS] Supplements list count: {len(supps)}")
        assert len(supps) >= 4, "Expected seeded supplements"

        # 4. Test detail retrieval for Creatine
        r = await client.get("/api/supplement/creatine")
        assert r.status_code == 200
        data = r.json()
        print(f"[PASS] Creatine detail retrieved: {data['name']}")
        print(f"       - Effect matrix entries: {len(data['effect_matrix'])}")
        print(f"       - PubChem CID: {data['pubchem_data']['cid']}")
        print(f"       - Studies count: {len(data['studies'])}")

        # 5. Test category filter
        r = await client.get("/api/category/Sleep%20%26%20Mood")
        assert r.status_code == 200
        cat_outcomes = r.json()
        print(f"[PASS] Category Sleep & Mood outcomes count: {len(cat_outcomes)}")

        # 6. Test search API
        r = await client.get("/api/search?q=sleep")
        assert r.status_code == 200
        search_res = r.json()
        print(f"[PASS] Search API query 'sleep' matches: {len(search_res)}")

        print("\nAll endpoints verified successfully!")

if __name__ == "__main__":
    asyncio.run(run_tests())
