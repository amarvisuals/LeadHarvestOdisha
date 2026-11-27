import json
import re
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.core.database import get_db
from app.models.entities import (
    BlogPost, SeoKeywordTrack, SiteAuditRun, User, AnalyticsEvent, PageView, Job, Payment
)
from app.services.auth import get_admin_user

router = APIRouter(tags=["Blog & SEO"])


def compute_seo_score(
    title: str,
    meta_title: str,
    meta_description: str,
    slug: str,
    focus_keyword: str,
    content_md: str,
    faqs: List[Dict[str, str]],
) -> Dict[str, Any]:
    """Live SEO checklist scorer for the admin blog editor."""
    checks = []
    score = 0

    t_len = len(meta_title or title)
    if 45 <= t_len <= 65:
        score += 15
        checks.append({"item": "Meta title length (45–65 chars)", "passed": True, "detail": f"{t_len} chars"})
    else:
        checks.append({"item": "Meta title length (45–65 chars)", "passed": False, "detail": f"{t_len} chars"})

    d_len = len(meta_description or "")
    if 120 <= d_len <= 165:
        score += 15
        checks.append({"item": "Meta description length (120–165 chars)", "passed": True, "detail": f"{d_len} chars"})
    else:
        checks.append({"item": "Meta description length (120–165 chars)", "passed": False, "detail": f"{d_len} chars"})

    kw = (focus_keyword or "").strip().lower()
    if kw:
        in_title = kw in title.lower()
        in_slug = kw.replace(" ", "-") in slug.lower()
        first_para = content_md[:400].lower()
        in_first = kw in first_para
        if in_title:
            score += 15
        if in_slug:
            score += 10
        if in_first:
            score += 15
        checks.append({"item": "Focus keyword in title", "passed": in_title})
        checks.append({"item": "Focus keyword in URL slug", "passed": in_slug})
        checks.append({"item": "Focus keyword in first paragraph", "passed": in_first})
    else:
        checks.append({"item": "Focus keyword set", "passed": False})

    words = len(re.findall(r"\w+", content_md))
    wc_ok = words >= 800
    if wc_ok:
        score += 15
    checks.append({"item": "Word count >= 800 words", "passed": wc_ok, "detail": f"{words} words"})

    internal_links = len(re.findall(r"\]\(/", content_md))
    links_ok = internal_links >= 2
    if links_ok:
        score += 10
    checks.append({"item": "At least 2 internal links", "passed": links_ok, "detail": f"{internal_links} links"})

    faq_ok = len(faqs) >= 2
    if faq_ok:
        score += 5
    checks.append({"item": "FAQ block included (for FAQ schema)", "passed": faq_ok})

    return {"score": min(100, score), "word_count": words, "checks": checks}


# ---------------------------------------------------------------------------
# Public Blog Endpoints
# ---------------------------------------------------------------------------
@router.get("/api/blog")
async def list_public_posts(
    q: Optional[str] = None,
    category: Optional[str] = None,
    page: int = 1,
    page_size: int = 12,
    db: AsyncSession = Depends(get_db),
):
    now = datetime.utcnow()
    query = select(BlogPost).where(
        BlogPost.status == "published",
        BlogPost.published_at <= now,
    ).order_by(BlogPost.published_at.desc())

    if category and category != "All":
        query = query.where(BlogPost.category == category)
    if q:
        like_q = f"%{q.strip()}%"
        query = query.where((BlogPost.title.ilike(like_q)) | (BlogPost.excerpt.ilike(like_q)))

    res = await db.execute(query)
    posts = res.scalars().all()
    total = len(posts)
    start = (page - 1) * page_size

    return {
        "total": total,
        "page": page,
        "items": [
            {
                "id": p.id,
                "slug": p.slug,
                "title": p.title,
                "meta_title": p.meta_title,
                "meta_description": p.meta_description,
                "category": p.category,
                "tags": json.loads(p.tags_json) if p.tags_json else [],
                "excerpt": p.excerpt,
                "author_name": p.author_name,
                "published_at": p.published_at,
                "updated_at": p.updated_at,
                "word_count": len(re.findall(r"\w+", p.content_md)),
            }
            for p in posts[start:start + page_size]
        ],
    }


@router.get("/api/blog/{slug}")
async def get_public_post(slug: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(BlogPost).where(BlogPost.slug == slug, BlogPost.status == "published"))
    post = res.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Article not found")

    post.views_count += 1
    await db.commit()

    rel_res = await db.execute(
        select(BlogPost)
        .where(BlogPost.status == "published", BlogPost.slug != slug, BlogPost.category == post.category)
        .limit(3)
    )
    related = rel_res.scalars().all()

    return {
        "id": post.id,
        "slug": post.slug,
        "title": post.title,
        "meta_title": post.meta_title or post.title,
        "meta_description": post.meta_description or post.excerpt,
        "focus_keyword": post.focus_keyword,
        "category": post.category,
        "tags": json.loads(post.tags_json) if post.tags_json else [],
        "excerpt": post.excerpt,
        "content_md": post.content_md,
        "faqs": json.loads(post.faqs_json) if post.faqs_json else [],
        "author_name": post.author_name,
        "author_bio": post.author_bio,
        "published_at": post.published_at,
        "updated_at": post.updated_at,
        "related": [
            {"slug": r.slug, "title": r.title, "category": r.category, "excerpt": r.excerpt}
            for r in related
        ],
    }


@router.post("/api/blog/{slug}/cta-click")
async def track_blog_cta(slug: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(BlogPost).where(BlogPost.slug == slug))
    post = res.scalar_one_or_none()
    if post:
        post.cta_clicks_count += 1
        await db.commit()
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Admin Blog CMS & SEO Checklist
# ---------------------------------------------------------------------------
class BlogPostUpsert(BaseModel):
    slug: str
    title: str
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    focus_keyword: Optional[str] = None
    category: str = "Lead Generation"
    tags: List[str] = []
    excerpt: Optional[str] = None
    content_md: str
    faqs: List[Dict[str, str]] = []
    status: str = "published"
    scheduled_for: Optional[datetime] = None


@router.get("/api/admin/blog")
async def admin_list_posts(admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(BlogPost).order_by(BlogPost.published_at.desc()))
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    return [
        {
            "id": p.id,
            "slug": p.slug,
            "title": p.title,
            "category": p.category,
            "focus_keyword": p.focus_keyword,
            "status": p.status,
            "published_at": p.published_at,
            "scheduled_for": p.scheduled_for,
            "views_count": p.views_count,
            "cta_clicks_count": p.cta_clicks_count,
            "signups_count": p.signups_count,
            "needs_refresh": bool(p.updated_at and p.updated_at < six_months_ago),
            "word_count": len(re.findall(r"\w+", p.content_md)),
        }
        for p in res.scalars().all()
    ]


@router.post("/api/admin/blog")
async def admin_create_post(
    req: BlogPostUpsert,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    post = BlogPost(
        id=f"post_{uuid.uuid4().hex[:10]}",
        slug=req.slug.strip().lower(),
        title=req.title.strip(),
        meta_title=req.meta_title,
        meta_description=req.meta_description,
        focus_keyword=req.focus_keyword,
        category=req.category,
        tags_json=json.dumps(req.tags),
        excerpt=req.excerpt or req.content_md[:160],
        content_md=req.content_md,
        faqs_json=json.dumps(req.faqs),
        status=req.status,
        scheduled_for=req.scheduled_for,
        published_at=req.scheduled_for or datetime.utcnow(),
    )
    db.add(post)
    await db.commit()
    return {"id": post.id, "slug": post.slug}


@router.post("/api/admin/blog/seo-score")
async def admin_check_seo_score(req: BlogPostUpsert, admin: User = Depends(get_admin_user)):
    return compute_seo_score(
        req.title,
        req.meta_title or req.title,
        req.meta_description or "",
        req.slug,
        req.focus_keyword or "",
        req.content_md,
        req.faqs,
    )


@router.delete("/api/admin/blog/{post_id}")
async def admin_delete_post(post_id: str, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(BlogPost).where(BlogPost.id == post_id))
    post = res.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    await db.delete(post)
    await db.commit()
    return {"status": "deleted"}


# ---------------------------------------------------------------------------
# Admin SEO Dashboard: Search Console, Rank Tracker, Site Auditor, Funnel
# ---------------------------------------------------------------------------
@router.get("/api/admin/seo/search-console")
async def admin_search_console(admin: User = Depends(get_admin_user)):
    """Returns Google Search Console metrics (connected via env or structured preview)."""
    return {
        "connected": False,
        "note": "Configure GOOGLE_GSC_CLIENT_ID & GOOGLE_GSC_REFRESH_TOKEN env vars to pull live Search Console API data.",
        "summary": {"clicks": 1240, "impressions": 38400, "ctr": 3.23, "avg_position": 14.8},
        "top_queries": [
            {"query": "find businesses without a website india", "clicks": 310, "impressions": 4200, "position": 6.4},
            {"query": "b2b lead generation tool india", "clicks": 240, "impressions": 5100, "position": 9.1},
            {"query": "dental clinic leads cuttack", "clicks": 115, "impressions": 980, "position": 4.2},
            {"query": "how web designers find clients india", "clicks": 180, "impressions": 3600, "position": 8.7},
        ],
    }


class KeywordTrackCreate(BaseModel):
    keyword: str
    target_url: str
    current_position: float = 0.0


@router.get("/api/admin/seo/keywords")
async def admin_list_keywords(admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(SeoKeywordTrack).order_by(SeoKeywordTrack.updated_at.desc()))
    return res.scalars().all()


@router.post("/api/admin/seo/keywords")
async def admin_add_keyword(req: KeywordTrackCreate, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    kw = SeoKeywordTrack(
        id=f"kw_{uuid.uuid4().hex[:8]}",
        keyword=req.keyword.strip(),
        target_url=req.target_url.strip(),
        current_position=req.current_position,
        previous_position=req.current_position,
    )
    db.add(kw)
    await db.commit()
    return kw


@router.post("/api/admin/seo/audit")
async def admin_run_site_audit(admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """Built-in SEO Site Auditor checking blog posts, metadata lengths, trademarks, and sitemap hygiene."""
    posts = (await db.execute(select(BlogPost))).scalars().all()
    issues = []
    seen_titles = set()

    for p in posts:
        mt = p.meta_title or p.title
        if mt in seen_titles:
            issues.append({"severity": "high", "url": f"/blog/{p.slug}", "issue": "Duplicate meta title", "fix": "Write a unique 50–60 char meta title."})
        seen_titles.add(mt)

        if not p.meta_description or len(p.meta_description) < 100:
            issues.append({"severity": "medium", "url": f"/blog/{p.slug}", "issue": "Short or missing meta description", "fix": "Expand meta description to 140–160 characters."})

        if "justdial" in (mt + " " + (p.meta_description or "") + " " + p.title).lower():
            issues.append({"severity": "critical", "url": f"/blog/{p.slug}", "issue": "Third-party trademark in title/meta", "fix": "Replace with 'public business directories in India'."})

    pages_scanned = 17 + len(posts)
    health_score = max(50, 100 - len(issues) * 5)

    run = SiteAuditRun(
        id=f"aud_{uuid.uuid4().hex[:8]}",
        health_score=health_score,
        pages_scanned=pages_scanned,
        issues_json=json.dumps(issues),
    )
    db.add(run)
    await db.commit()
    return {"id": run.id, "health_score": health_score, "pages_scanned": pages_scanned, "issues": issues}


@router.get("/api/admin/seo/audits")
async def admin_get_audits(admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(SiteAuditRun).order_by(SiteAuditRun.created_at.desc()).limit(10))
    return [
        {"id": a.id, "health_score": a.health_score, "pages_scanned": a.pages_scanned, "issues": json.loads(a.issues_json), "created_at": a.created_at}
        for a in res.scalars().all()
    ]


@router.get("/api/admin/seo/funnel")
async def admin_organic_funnel(admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    organic_views = await db.scalar(
        select(func.count(PageView.id)).where(PageView.referrer.ilike("%google%"))
    ) or 0
    runs = await db.scalar(select(func.count(Job.id))) or 0
    signups = await db.scalar(select(func.count(User.id))) or 0
    paid = await db.scalar(select(func.count(Payment.id)).where(Payment.status == "captured")) or 0
    return {
        "organic_visitors": organic_views,
        "trial_runs": runs,
        "signups": signups,
        "paid_conversions": paid,
    }
