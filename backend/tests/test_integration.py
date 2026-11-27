import pytest
import asyncio
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import init_db

@pytest.mark.asyncio
async def test_full_pipeline_mock_run():
    # 1. Initialize DB
    await init_db()

    transport = ASGITransport(app=app)
    headers = {
        "User-Agent": f"pytest-integration-{uuid.uuid4().hex[:8]}",
        "X-Forwarded-For": f"10.0.{uuid.uuid4().int % 250}.{(uuid.uuid4().int >> 8) % 250}",
    }
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as client:
        # Check health
        health = await client.get("/health")
        assert health.status_code == 200

        # Check locations config
        loc_res = await client.get("/api/config/locations")
        assert loc_res.status_code == 200
        locations = loc_res.json()
        assert len(locations) >= 30
        assert any(l["name"] == "Bhubaneswar" for l in locations)

        # Check categories config
        cat_res = await client.get("/api/config/categories")
        assert cat_res.status_code == 200
        categories = cat_res.json()
        assert len(categories) >= 15

        # Check pre-run confirmation preview
        preview_res = await client.post("/api/jobs/preview", json={
            "cities": ["Bhubaneswar", "Cuttack"],
            "categories": ["Restaurants & Cafes"],
            "adapter": "mock"
        })
        assert preview_res.status_code == 200
        preview = preview_res.json()
        assert preview["cities_count"] == 2
        assert preview["categories_count"] == 1

        # Start Job in Mock Engine Mode
        job_res = await client.post("/api/jobs", json={
            "cities": ["Bhubaneswar", "Cuttack"],
            "categories": ["Restaurants & Cafes"],
            "adapter": "mock",
            "remember_leads": True
        })
        assert job_res.status_code == 200
        job_data = job_res.json()
        job_id = job_data["id"]
        assert job_id is not None

        # Wait for the mock job to complete
        max_wait = 25
        completed = False
        final_job = None
        for _ in range(max_wait):
            await asyncio.sleep(1.0)
            status_res = await client.get(f"/api/jobs/{job_id}")
            assert status_res.status_code == 200
            current_job = status_res.json()
            if current_job["status"] == "completed":
                completed = True
                final_job = current_job
                break

        assert completed is True
        assert final_job["new_leads"] > 0
        assert final_job["excel_file"] is not None

        # Download Excel file and verify HTTP response
        download_res = await client.get(f"/api/jobs/{job_id}/download")
        assert download_res.status_code == 200
        assert len(download_res.content) > 1000

        # Verify History lists the job
        hist_res = await client.get("/api/history")
        assert hist_res.status_code == 200
        history = hist_res.json()
        assert any(h["id"] == job_id for h in history)
