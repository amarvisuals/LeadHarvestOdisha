import json
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.database import init_db
from app.api.seo_blog_routes import compute_seo_score
from seed_blog import seed_blog_posts


@pytest.mark.asyncio
async def test_public_blog_and_trademark_hygiene():
    await init_db()
    await seed_blog_posts()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/blog?page_size=20")
        assert res.status_code == 200
        items = res.json()["items"]
        assert len(items) >= 12

        seen_titles = set()
        for item in items:
            assert item["title"] not in seen_titles, "Duplicate blog title found"
            seen_titles.add(item["title"])
            assert "justdial" not in item["title"].lower()
            assert "justdial" not in (item.get("meta_title") or "").lower()
            assert "justdial" not in (item.get("meta_description") or "").lower()

        # Fetch single article detail
        detail = await client.get(f"/api/blog/{items[0]['slug']}")
        assert detail.status_code == 200
        assert len(detail.json()["faqs"]) >= 1

        # Verify unauthenticated user cannot access admin SEO endpoints
        admin_res = await client.get("/api/admin/seo/search-console")
        assert admin_res.status_code in (401, 403)


def test_seo_score_calculator():
    res = compute_seo_score(
        title="How to Find Businesses Without a Website in India",
        meta_title="Find Businesses Without a Website in India | LeadHarvest",
        meta_description="Step-by-step workflow to find Indian businesses without a website from public directories, qualify by Opportunity Score, and export Excel leads.",
        slug="how-to-find-businesses-without-website-india",
        focus_keyword="find businesses without a website",
        content_md=("Find businesses without a website in India. " * 200) + " [Link1](/pricing) [Link2](/features/no-website-filter)",
        faqs=[{"question": "Q1", "answer": "A1"}, {"question": "Q2", "answer": "A2"}],
    )
    assert res["score"] >= 85
    assert res["word_count"] >= 800
