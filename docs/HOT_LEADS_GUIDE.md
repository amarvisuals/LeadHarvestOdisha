# Hot Leads — Ready-to-Close Pipeline Guide

The **Hot Leads** section in the Admin Panel (`/admin` → **Hot Leads**) helps you track, score, and close businesses that genuinely need a website—using only compliant sources:
1. **Inbound:** "Get a Free Website Quote" form (`/contact`), tracked WhatsApp click-to-chat CTA, and Google Ads Lead Form webhook (`POST /api/webhooks/google-ads`).
2. **Public Requests:** Manual entries, CSV imports, and pluggable Intent Sources (RSS feeds, official APIs, owner-forwarded email alerts).
3. **Signal Leads:** Businesses automatically surfaced from LeadHarvest's own Smart Filters (no website, broken website, no HTTPS, slow site, not mobile-friendly, advertising without a website).

> **Compliance Rule:** Never attempt to identify individuals from private Google searches. Always respect TRAI DND rules, WhatsApp Business opt-in policy, and DPDP Act 2023.

---

## 1. How to Add an Intent Source
1. Open **`/admin` → Hot Leads → Sources & CSV Import**.
2. Choose a source kind (`rss`, `official_api`, `email_alert`, or `manual`).
3. Enter the feed/API URL and a mandatory **Terms-of-Use compliance note**.
4. To add a new programmatic adapter in code, subclass `BaseIntentSource` in `backend/app/services/hot_leads.py`, implement `fetch_leads()`, and register it in `INTENT_SOURCE_REGISTRY`. Disallowed domains (such as Google Search, LinkedIn, Facebook, Instagram) are blocked automatically.

---

## 2. How to Edit Hot Lead Score Weights
1. Open **`/admin` → Hot Leads → Score Formula**.
2. Adjust the weights for any factor (e.g., `contacted_directly`, `requested_quote`, `no_website`, `broken_or_outdated_website`, `mobile_available`, `good_rating_or_active`, `recently_listed`, `budget_stated`).
3. Click **Save & Recompute All Lead Scores** (`PUT /api/admin/hot-leads/config/weights`).
   - **Hot:** 75–100 · **Warm:** 50–74 · **Cold:** 0–49.
   - Every lead detail page (`/admin/hot-leads/[id]`) displays a **"Why This Score"** breakdown.

---

## 3. How to Import Public Requests via CSV
1. Open **`/admin` → Hot Leads → Sources & CSV Import**.
2. Prepare a `.csv` file with `business_name` (required) and at least one contact method (`phone`, `email`, or `source_url`), plus optional columns: `city`, `state`, `business_type`, `budget_range`, `timeline`, `website`, `notes`, `terms_note`.
3. Upload the CSV. Rows are validated, checked against the **Do Not Contact** list, scored, and added to **Public Requests**.

---

## 4. Google Ads Lead-Form Webhook Setup
- **Endpoint:** `POST /api/webhooks/google-ads`
- **Secret Key:** Set `LEADHARVEST_GOOGLE_ADS_WEBHOOK_SECRET` in Render/environment variables and pass it as `google_key` in the Google Ads Lead Form webhook configuration.
