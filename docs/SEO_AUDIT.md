# LeadHarvest India – Technical & On-Page SEO Audit

**Audit Date:** 2026-11-27  
**Scope:** Existing Next.js 14 App Router (`frontend/`) + FastAPI (`backend/`) SaaS codebase.

---

## 1. What Currently Exists
- **App Router Foundation**: Next.js 14 App Router with semantic `<header>`, `<main>`, `<footer>` landmarks in `frontend/app/layout.tsx`.
- **Clean Route Slugs**: Lowercase hyphenated routes for `/`, `/pricing`, `/login`, `/signup`, `/forgot-password`, `/billing`, `/profile`, `/history`, `/settings`, `/terms`, `/privacy`, `/refund`, `/contact`.
- **Security Headers**: FastAPI middleware adds `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and `Referrer-Policy`.
- **Font Optimization**: `Inter` loaded via `next/font/google`.
- **First-Party Analytics**: Cookie consent banner with consent-aware event tracking.

---

## 2. Missing Items & Issues Found (with Severity & Fixes)

| # | Area | Issue Found | Severity | Remediation Plan |
|---|---|---|---|---|
| 1 | **Rendering (SSR/SSG)** | `frontend/app/page.tsx` is `"use client"` at the root, meaning crawlers receive minimal pre-rendered marketing copy and no FAQ/use-case HTML. | **Critical** | Split `/` into a Server Component (`page.tsx`) with rich SSR marketing sections, FAQ, and schema, embedding the interactive client Wizard. |
| 2 | **Robots & Indexing** | Missing `robots.txt` (`app/robots.ts`). Private/app routes (`/admin`, `/billing`, `/profile`, `/history`, `/settings`, `/progress`) are not blocked via `noindex` or `robots.txt`. | **Critical** | Add `app/robots.ts` disallowing `/admin`, `/api`, `/billing`, `/profile`, `/progress`, `/history`, `/settings`, and parameter URLs; add `robots: { index: false, follow: false }` metadata on private layouts. |
| 3 | **XML Sitemap & RSS** | No `sitemap.xml` or blog RSS feed exists. | **Critical** | Add dynamic `app/sitemap.ts` (including static pages, feature/use-case pages, tools, published blog posts, and quality-gated local pages) + `/blog/rss.xml`. |
| 4 | **Per-Page Metadata & OG** | Only `layout.tsx` defines metadata; inner public pages (`/pricing`, `/contact`, etc.) lack unique `title`, `description`, canonical URLs, Open Graph, Twitter cards, and generated OG images. | **High** | Add `generateMetadata` / `metadata` exports with unique 50–60 char titles, 140–160 char descriptions, canonicals, and dynamic `/api/og` (`next/og`) image generation. |
| 5 | **Structured Data (JSON-LD)** | Zero JSON-LD schema markup across the site. | **High** | Implement reusable JSON-LD generator for `Organization`, `WebSite`, `SoftwareApplication` + `Offer`, `FAQPage`, `Article`, `BreadcrumbList`, and `HowTo`. |
| 6 | **Language & Accessibility** | `<html lang="en">` instead of `lang="en-IN"`; missing skip-to-content link; missing `hreflang` readiness. | **Medium** | Set `lang="en-IN"`, add `<a href="#main-content" className="sr-only focus:not-sr-only">Skip to main content</a>`, and configure `alternates.languages`. |
| 7 | **Content & Topic Clusters** | No `/features/*`, `/use-cases/*`, `/blog/*`, `/tools/*`, `/about`, or `/leads/<state>/<city>/<category>` pages exist. | **High** | Build all 5 feature pages, 6 use-case pages, 4 free tools, `/about`, full DB-backed blog with 12 initial articles, and quality-gated programmatic local pages. |
| 8 | **Custom 404 & Redirects** | No custom `not-found.tsx` helpful 404 page; no trailing-slash normalization. | **Medium** | Add `app/not-found.tsx` with search/links and `trailingSlash: false` in `next.config.mjs`. |
| 9 | **AI Search Readiness** | Missing `/llms.txt` and concise direct-answer blocks. | **Medium** | Add `/llms.txt` route and clear summary definitions + comparison tables on key pages. |
| 10 | **Webmaster & GA4** | No Google Search Console / Bing verification meta tags; no consent-gated GA4 loader. | **Low** | Add env-driven `verification` metadata and consent-gated GA4 script. |
| 11 | **Trademark Hygiene** | Ensure zero third-party directory trademarks appear in public titles, H1s, meta tags, or URLs. | **High** | Audit all public copy and replace any directory references with *"public business directories in India"*. |
