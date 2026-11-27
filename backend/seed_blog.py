import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.future import select

from app.core.database import AsyncSessionLocal, init_db
from app.models.entities import BlogPost

ARTICLES = [
    {
        "slug": "how-to-find-businesses-without-website-india",
        "title": "How to Find Businesses Without a Website in India (Step-by-Step Workflow)",
        "meta_title": "Find Businesses Without a Website in India | LeadHarvest",
        "meta_description": "Step-by-step workflow to find Indian businesses without a website from public directories, qualify by Opportunity Score, and export Excel leads.",
        "focus_keyword": "find businesses without a website",
        "category": "Web Design Leads",
        "tags": ["no website", "web design leads", "india"],
        "excerpt": "Learn how Indian web designers and agencies find local businesses with strong customer reviews that still lack a website.",
        "faqs": [
            {"question": "Why target businesses without a website?", "answer": "They already have customers and revenue, so you pitch a clear gap rather than convincing them marketing matters."},
            {"question": "Which Indian cities work best?", "answer": "Tier-2 cities like Bhubaneswar, Cuttack, Jaipur, Indore, and Surat have high business density and lower agency competition."}
        ],
        "content_md": """Finding local businesses that do not have a website is one of the highest-converting outbound strategies for web designers and digital agencies in India. Instead of pitching crowded startups or corporates that already work with retainers, you focus on profitable local clinics, salons, restaurants, and contractors who rely purely on word-of-mouth and public business directories.

## Why "No Website" Is the Strongest Buying Signal
When a business in Cuttack or Pune has 4.3 stars and 45 customer reviews in a public directory, but zero website link, two things are true:
1. Customers are actively searching for them and visiting them.
2. Competitors with a clean website are capturing trust from first-time Google searchers.

## Step 1: Pick High-Ticket Local Categories
Not every shop can afford a ₹20,000 custom website. Focus on categories where one or two new clients pay back your fee:
- Dentists & Dental Clinics
- Interior Designers & Modular Kitchen Dealers
- Banquet Halls & Wedding Planners
- Real Estate Agents & Builders
- Coaching Centres & Specialty Hospitals

## Step 2: Filter for "No Website Listed" + Valid Mobile
Use [LeadHarvest's No-Website Filter](/features/no-website-filter) to isolate listings where the website field is empty and a valid 10-digit Indian mobile number is available. Combine this with our [Opportunity Score](/features/opportunity-score) (minimum 60/100) so low-rating or inactive listings are filtered out automatically.

## Step 3: Deduplicate Before You Pitch
Before sending a single WhatsApp message, upload your past spreadsheets so you never contact the same owner twice. Our [automatic deduplication engine](/features/auto-deduplication) checks phone numbers, business names, and fuzzy addresses.

## Step 4: Send a Helpful 1-Page Demo Pitch
Generate your message using our free [Website Pitch Generator](/tools/pitch-generator) and click the `wa.me` link in your exported Excel sheet. Ready to try it? Start with [4 free runs on LeadHarvest India](/)."""
    },
    {
        "slug": "how-web-designers-find-clients-india",
        "title": "How Web Designers Can Find Clients in India: A Complete Guide",
        "meta_title": "How Web Designers Find Clients in India | Complete Guide",
        "meta_description": "Practical client acquisition guide for Indian web designers: niche selection, local directory prospecting, WhatsApp outreach, and pricing.",
        "focus_keyword": "how web designers find clients in India",
        "category": "Agency Growth",
        "tags": ["freelance", "web design", "client acquisition"],
        "excerpt": "A repeatable outbound system for Indian freelance web designers to move beyond crowded bidding marketplaces.",
        "faqs": [
            {"question": "Is Upwork or direct local outreach better in India?", "answer": "Direct local outreach lets you charge ₹15,000–₹45,000 without competing against 50 other bidders on price."},
            {"question": "How many pitches should I send daily?", "answer": "20 well-researched WhatsApp or phone pitches per day is sustainable for a solo freelancer."}
        ],
        "content_md": """Most Indian web designers start on freelance marketplaces where 40 freelancers race to the bottom on a ₹4,000 WordPress job. Building a steady income requires owning your own client pipeline.

## Move From Bidding Platforms to Direct Local B2B Outreach
Every Tier-1 and Tier-2 Indian city has thousands of clinics, coaching centres, hotels, and interior designers that need a fast, mobile-friendly website. By using a structured [web design agency workflow](/use-cases/web-design-agencies), you eliminate price wars and speak directly to decision-makers.

## Build a Niche Portfolio First
Pick two industries—such as dental clinics and interior designers—and build one clean 1-page demo for each. When you message an owner in Bhubaneswar or Jaipur, send a screenshot or link to that demo rather than a generic PDF brochure.

## Automate Your Lead List in 2 Minutes
Instead of copying phone numbers manually into spreadsheets, use [LeadHarvest India](/) to select your city and category, enable the **No Website** filter, and export a clean Excel workbook with clickable WhatsApp links. Check your numbers with our [Agency ROI Calculator](/tools/agency-roi-calculator) and pick a plan on our [Pricing page](/pricing)."""
    },
    {
        "slug": "cold-call-whatsapp-scripts-sell-websites-india",
        "title": "Cold Call and WhatsApp Scripts to Sell Websites to Local Business Owners",
        "meta_title": "Cold Call & WhatsApp Scripts for Web Designers India",
        "meta_description": "Proven English and Hinglish cold call and WhatsApp templates to sell websites to Indian clinics, salons, and local business owners.",
        "focus_keyword": "cold calling script for web designers India",
        "category": "Outreach & Scripts",
        "tags": ["whatsapp scripts", "cold calling", "sales"],
        "excerpt": "Copy-paste WhatsApp and phone call scripts tailored for Indian local business owners—respectful, brief, and focused on bookings.",
        "faqs": [
            {"question": "Should I call or send a WhatsApp message first?", "answer": "Sending a short, polite WhatsApp message with a 1-line observation and demo link usually gets higher response rates than unannounced cold calls."},
            {"question": "What time is best to contact Indian business owners?", "answer": "Between 11:00 AM–1:00 PM or 4:30 PM–6:30 PM on weekdays, avoiding peak lunch/evening rush for restaurants."}
        ],
        "content_md": """Indian business owners receive dozens of spam calls every week. To stand out, your script must be polite, local, and immediately show that you actually looked at their business.

## WhatsApp Script #1: The No-Website Observation (English)
> Namaste [Owner/Clinic Name] ji, I was checking top-rated [Category] in [City] and noticed your [4.4★] reviews—great work! However, I saw there is no dedicated website link yet for patients/customers searching Google. I put together a quick 1-page mobile preview for a [Category] in [City]. May I share the preview link here?

## WhatsApp Script #2: Hinglish / Conversational
> Namaste ji, main [Your Name] bol raha hoon. Maine [City] mein aapke [Business Name] ki acchi rating dekhi, lekin aapki apni website link nahi dikhi. Aajkal log call karne se pehle Google par website dekhte hain. Kya main aapko ek simple mobile demo link WhatsApp par bhej sakta hoon?

## Odia-Friendly Opening Line (For Odisha Outreach)
> Namaskar Sir/Madam, mu [Your Name] kahuchhi. Mu apananka [City] re thiba [Business Name] ra bhal reviews dekhili, kintu website link nathila. Jadi apana chahibe, mu eka simple mobile demo share kariparibi.

## Generate Custom Pitches Instantly
Try our free [Website Pitch Generator](/tools/pitch-generator) or create `wa.me` links with our [WhatsApp Link Generator](/tools/whatsapp-link-generator). Combine these scripts with clean leads from [LeadHarvest's No-Website Filter](/features/no-website-filter)."""
    },
    {
        "slug": "build-local-business-lead-list-excel",
        "title": "How to Build a Local Business Lead List in Excel (Template and Best Practices)",
        "meta_title": "How to Build a Business Lead List in Excel | LeadHarvest",
        "meta_description": "Learn the exact Excel columns, phone formatting (+91), deduplication formulas, and WhatsApp links needed for a high-converting lead list.",
        "focus_keyword": "how to make a lead list in Excel",
        "category": "Excel & Data",
        "tags": ["excel", "lead tracker", "templates"],
        "excerpt": "Structure your Excel lead list properly with +91 phone normalisation, Opportunity Scores, and clickable wa.me links.",
        "faqs": [
            {"question": "Which columns should every B2B lead Excel sheet have?", "answer": "Business Name, Category, Normalized Phone, Has Website (Yes/No), Opportunity Score, WhatsApp Link, City, Rating, and Outreach Status."}
        ],
        "content_md": """A messy spreadsheet kills outbound momentum. When phone numbers have inconsistent spaces, missing country codes, or duplicate rows, sales reps waste hours fixing formatting instead of pitching.

## Essential Columns for an Indian B2B Lead Sheet
1. **Business Name** (Title Case, trimmed whitespace)
2. **Category & City** (for segmentation)
3. **Phone (+91 XXXXX XXXXX)** and **Mobile Available (Yes/No)**
4. **Has Website (Yes/No)** & **Website URL**
5. **WhatsApp Link** (`https://wa.me/91XXXXXXXXXX`)
6. **Opportunity Score (0–100)** & **Lead Tag**

## Formula to Build Clickable WhatsApp Links in Excel
If column `C2` contains a clean 10-digit Indian mobile number, use:
`=HYPERLINK("https://wa.me/91" & C2, "Chat on WhatsApp")`

## Skip the Manual Formatting
Download our free [Excel Lead Tracker Templates](/tools/excel-lead-templates) or let [LeadHarvest's One-Click Excel Export](/features/excel-export) build a styled 3-sheet workbook automatically."""
    },
    {
        "slug": "15-business-types-india-need-website",
        "title": "15 Business Types in India That Most Need a Website (and How to Pitch Each)",
        "meta_title": "15 Indian Business Types That Need a Website | LeadHarvest",
        "meta_description": "Discover 15 high-margin Indian local business categories—from dental clinics to interior designers—that convert fast on website pitches.",
        "focus_keyword": "businesses in India that need a website",
        "category": "Web Design Leads",
        "tags": ["niches", "web design", "india"],
        "excerpt": "Focus your outreach on these 15 profitable Indian service niches where a single new customer covers the cost of a website.",
        "faqs": [
            {"question": "Which business type is easiest to close first?", "answer": "Dental clinics, physiotherapy centres, and interior designers typically have high deal values and clear booking needs."}
        ],
        "content_md": """Pitching a ₹15,000 website to a low-margin corner kiosk rarely works. Instead, focus on high-ticket local service businesses across India where one customer generates ₹5,000 to ₹1,00,000+ in revenue:

1. **Dentists & Dental Clinics** – Pitch online appointment booking and treatment pages (implants, braces).
2. **Interior Designers** – Pitch a fast visual portfolio gallery to win residential projects.
3. **Hotels & Resorts** – Pitch direct room enquiry forms to save OTA commissions.
4. **Banquet & Marriage Halls** – Pitch seasonal availability calendars and photo galleries.
5. **Real Estate Agents & Builders** – Pitch project landing pages with WhatsApp lead capture.
6. **Coaching Centres (IIT/NEET/UPSC)** – Pitch batch schedules, topper results, and enquiry forms.
7. **Diagnostic & Pathology Labs** – Pitch home-sample-collection booking forms.
8. **Salons & Bridal Makeup Studios** – Pitch service menus and bridal package bookings.
9. **Packers and Movers** – Pitch instant quote calculators.
10. **Solar Panel Dealers** – Pitch subsidy calculators and roof-survey bookings.
11. **Chartered Accountants (CA)** – Pitch trust-building service pages for GST & company registration.
12. **Physiotherapy & Rehab Clinics** – Pitch specialist profiles and location maps.
13. **Car Detailing & Ceramic Studios** – Pitch before/after galleries and package pricing.
14. **Boutiques & Bridal Wear** – Pitch WhatsApp catalogue integration.
15. **Travel & Tour Operators** – Pitch custom Odisha/India itinerary pages.

Explore all 205 categories inside [LeadHarvest India](/) and check our [Pricing](/pricing)."""
    },
    {
        "slug": "pitch-website-to-dentist-clinic-owner",
        "title": "How to Pitch a Website to a Dentist or Clinic Owner (With Proposal Outline)",
        "meta_title": "How to Pitch a Website to a Dentist or Clinic Owner India",
        "meta_description": "Learn how to pitch dental clinics in India with no website: pain points, WhatsApp opener, and a 1-page ₹18,000 website proposal outline.",
        "focus_keyword": "how to pitch website to clinic owner",
        "category": "Outreach & Scripts",
        "tags": ["dentists", "clinics", "proposal"],
        "excerpt": "A proven framework and proposal structure for selling websites to dental and medical clinics across Indian cities.",
        "faqs": [
            {"question": "What features do Indian dental clinics actually care about?", "answer": "Doctor qualifications, treatment list (root canal, braces, implants), clinic timings, Google Maps embed, and a 1-click WhatsApp appointment button."}
        ],
        "content_md": """Dental clinics are among the best B2B prospects for web designers in India. One root canal or orthodontic patient covers the clinic's entire website investment.

## Why Many Clinics Still Lack a Website
Doctors are busy treating patients and assume a basic directory listing is enough. However, when families search *"best dentist near me"* or *"dental implant cost"*, clinics with a clean, reassuring website earn significantly more trust.

## Sample 1-Page Proposal Outline (₹15,000 – ₹25,000)
- **Section 1:** Doctor Profile, Degrees (BDS/MDS), and Years of Experience.
- **Section 2:** Clear Treatments Grid (Root Canal, Braces, Implants, Scaling).
- **Section 3:** Patient Reviews & Hygiene Photos.
- **Section 4:** Sticky "Book on WhatsApp" Button + Clinic Timings & Map.

Find clinics in your city using [Dental Clinic Leads in Cuttack](/leads/odisha/cuttack/dentists-and-dental-clinics) or filter across India on [LeadHarvest](/features/no-website-filter)."""
    },
    {
        "slug": "b2b-lead-generation-india-2026",
        "title": "B2B Lead Generation in India: Strategies That Work in 2026",
        "meta_title": "B2B Lead Generation Strategies in India (2026 Guide)",
        "meta_description": "Actionable B2B lead generation strategies for Indian agencies and SaaS teams: hyperlocal directory prospecting, WhatsApp outreach, and lead scoring.",
        "focus_keyword": "B2B lead generation strategies India",
        "category": "Lead Generation",
        "tags": ["b2b", "strategy", "india 2026"],
        "excerpt": "What actually works for B2B lead generation in India right now—from Tier-2 targeting to Opportunity Scoring.",
        "faqs": [
            {"question": "Why are Tier-2 Indian cities performing better for B2B outreach?", "answer": "Business owners in Tier-2 cities receive far fewer cold pitches than Mumbai or Bengaluru founders, resulting in higher reply rates."}
        ],
        "content_md": """Cold email blast tools built for US markets often underperform with Indian SMBs, where owners live on WhatsApp and phone calls rather than checking corporate inboxes all day.

## 1. Hyperlocal Targeting Beats Generic Blasts
Instead of buying a 100,000-row generic list, build focused cohorts by city and niche—for example, Interior Designers in Bhubaneswar or Gyms in Surat.

## 2. Lead With an Audit or Gap
Use [Smart Filters](/features/opportunity-score) to identify visible gaps—such as **No Website** or **Low Review Count**—so your first message feels helpful rather than spammy.

## 3. Keep Your Database Clean
Never call the same prospect twice from different team sheets. Use [automatic deduplication](/features/auto-deduplication) and explore our [B2B Sales Teams workflow](/use-cases/b2b-sales-teams)."""
    },
    {
        "slug": "how-to-qualify-leads-ratings-reviews-website",
        "title": "How to Qualify Leads: Using Ratings, Reviews, and Website Status to Prioritise",
        "meta_title": "How to Qualify Local Business Leads (Ratings & Reviews)",
        "meta_description": "Use website status, star ratings, and review counts to score local Indian business leads from 0 to 100 before reaching out.",
        "focus_keyword": "how to qualify local business leads",
        "category": "Lead Generation",
        "tags": ["lead scoring", "qualification", "reviews"],
        "excerpt": "Stop wasting hours on dead listings. Learn how ratings, review volume, and website gaps reveal who is ready to buy.",
        "faqs": [
            {"question": "What review count indicates a good agency prospect?", "answer": "10 to 50 reviews shows an active, growing business that still lacks professional digital marketing."}
        ],
        "content_md": """Not all leads deserve equal effort. If you have 500 businesses in a spreadsheet, contacting them from top to bottom alphabetically wastes your best selling hours.

## The 3-Signal Qualification Framework
- **Website Status:** No website = custom web design pitch; has website + low reviews = SEO/Ads pitch.
- **Rating Band (3.5★ – 4.7★):** High enough that the owner cares about quality, but room to grow.
- **Review Count (< 50):** Active business that hasn't yet scaled its digital footprint.

## Automated Scoring in LeadHarvest India
Our [Opportunity Score](/features/opportunity-score) computes a transparent 0–100 score on every lead and tags top prospects as **Hot Website Pitch** inside your [Excel export](/features/excel-export)."""
    },
    {
        "slug": "avoid-duplicate-leads-clean-database",
        "title": "How to Avoid Duplicate Leads and Keep a Clean Lead Database",
        "meta_title": "How to Avoid Duplicate Leads in Your Database | LeadHarvest",
        "meta_description": "Prevent embarrassing repeat calls by normalising +91 phone numbers and using fuzzy name+address matching across Excel/CSV sheets.",
        "focus_keyword": "how to clean and deduplicate lead database",
        "category": "Excel & Data",
        "tags": ["deduplication", "data hygiene", "excel"],
        "excerpt": "Why simple Excel 'Remove Duplicates' misses +91 formatting variations—and how 3-tier deduplication solves it.",
        "faqs": [
            {"question": "Why does Excel's built-in Remove Duplicates fail on phone numbers?", "answer": "Excel treats '+91 98610 12345', '09861012345', and '98610-12345' as three completely different values."}
        ],
        "content_md": """Calling the same business owner twice in one week damages your brand's credibility. Yet standard Excel deduplication fails whenever phone numbers include `+91`, leading zeroes, or dashes, or when a business name is spelled slightly differently.

## The 3-Tier Deduplication Standard
1. **Normalized 10-Digit Phone Match:** Strip country prefixes, spaces, and punctuation, then compare the last 10 digits.
2. **Normalized Name + City Match:** Catch branches or alternate numbers under the same name in the same city.
3. **Fuzzy Name + Address Match:** Use token-sort similarity (>= 90%) to catch minor spelling differences.

Read more on our [Automatic Deduplication feature page](/features/auto-deduplication) or test it free on [LeadHarvest India](/)."""
    },
    {
        "slug": "local-seo-basics-pitch-small-business",
        "title": "Local SEO Basics: What to Tell a Small Business Owner When You Pitch",
        "meta_title": "Local SEO Basics to Pitch Small Businesses in India",
        "meta_description": "Plain-English Local SEO talking points for Indian agencies pitching Google Business Profile, reviews, and mobile websites.",
        "focus_keyword": "local SEO pitch for small businesses India",
        "category": "Agency Growth",
        "tags": ["local seo", "pitching", "small business"],
        "excerpt": "Explain Local SEO to non-technical Indian business owners without jargon—and turn website projects into monthly retainers.",
        "faqs": [
            {"question": "How do I explain Local SEO to a clinic or shop owner?", "answer": "Focus on three things: showing up in the top 3 map results, having a fast website link, and collecting steady customer reviews."}
        ],
        "content_md": """Small business owners do not care about 'canonical tags' or 'schema markup'. They care about phone calls and walk-ins.

## 3 Simple Talking Points That Close Retainers
1. **Map Pack Visibility:** People search *"near me"* on their phones before visiting.
2. **Website Credibility:** Linking a clean website from their profile increases trust and click-throughs.
3. **Review Velocity:** Consistently replying to and requesting reviews keeps them ahead of nearby competitors.

Use our [SEO / Ads Pitch Preset](/use-cases/seo-digital-marketers) to find businesses that already have a website but fewer than 30 reviews."""
    },
    {
        "slug": "legal-contact-businesses-public-listings-india-dpdp",
        "title": "Is It Legal to Contact Businesses From Public Listings in India? DPDP, DND & Consent Guide",
        "meta_title": "DPDP Act & DND Rules for B2B Outreach in India | LeadHarvest",
        "meta_description": "Informational plain-English overview of India's DPDP Act 2023, TRAI DND rules, and ethical B2B outreach from public business listings.",
        "focus_keyword": "DPDP Act DND rules B2B cold outreach India",
        "category": "Compliance",
        "tags": ["dpdp act", "dnd", "compliance", "india"],
        "excerpt": "An informational guide (not legal advice) on ethical B2B outreach, TRAI DND rules, and India's DPDP Act 2023.",
        "faqs": [
            {"question": "Is this article legal advice?", "answer": "No. This guide is purely informational. Consult a qualified lawyer for legal advice specific to your business."}
        ],
        "content_md": """*Disclaimer: This article is for general informational purposes only and does not constitute legal advice. Always consult a qualified legal professional regarding compliance.*

## Understanding B2B Outreach in India
When contacting businesses listed in public business directories in India, responsible agencies follow three core principles:

## 1. Respect TRAI DND / NCPR Preferences
Before running automated telemarketing or bulk promotional SMS campaigns, Indian regulations require checking numbers against the National Customer Preference Register (NCPR / DND) and complying with DLT registration rules for bulk messaging.

## 2. DPDP Act 2023 & Publicly Available Data
India's Digital Personal Data Protection (DPDP) Act 2023 includes specific considerations around data made publicly available by the data principal, while still requiring respectful, purpose-limited handling and honouring opt-out requests immediately.

## 3. Ethical Personal Outreach Best Practices
- Send personalised, one-to-one messages rather than automated spam blasts.
- Always honour "not interested / stop" replies immediately and keep them in your [Known Records exclusion list](/features/auto-deduplication).
- Review our [Privacy Policy](/privacy) and [Terms of Use](/terms)."""
    },
    {
        "slug": "lead-generation-tool-vs-buying-database",
        "title": "Lead Generation Tool vs Buying a Database vs Manual Research: Which Is Best?",
        "meta_title": "Lead Generation Tool vs Buying a Database India | LeadHarvest",
        "meta_description": "Compare buying static business databases, manual copy-pasting, and using a live filtered B2B lead generation tool in India.",
        "focus_keyword": "lead generation tool vs buying business database",
        "category": "Lead Generation",
        "tags": ["comparison", "database", "roi"],
        "excerpt": "Why static ₹999 WhatsApp databases bounce and waste time—and when a filtered lead-generation tool wins.",
        "faqs": [
            {"question": "Why do cheap static databases have low response rates?", "answer": "They are often 2–4 years old, resold to thousands of buyers, and lack website-status or rating filters."}
        ],
        "content_md": """Every Indian agency faces the same choice when starting outbound sales: copy listings manually, buy a cheap pre-packaged spreadsheet, or use a filtered lead-generation tool.

## Comparison at a Glance
- **Manual Research:** Free, accurate, but painfully slow (30–40 leads per hour).
- **Buying Static Databases:** Cheap upfront, but filled with outdated numbers, closed shops, and zero website/rating filtering.
- **LeadHarvest India:** Collects fresh listings on demand by state, city, and category, applies Smart Filters like **No Website**, deduplicates against your past files, and exports clean Excel sheets in minutes.

Compare plans on our [Pricing page](/pricing) or test [4 free runs now](/)."""
    },
]


async def seed_blog_posts():
    await init_db()
    now = datetime.utcnow()
    default_export = []

    async with AsyncSessionLocal() as db:
        for idx, art in enumerate(ARTICLES):
            pub_dt = now - timedelta(days=(len(ARTICLES) - idx) * 2)
            res = await db.execute(select(BlogPost).where(BlogPost.slug == art["slug"]))
            existing = res.scalar_one_or_none()
            if not existing:
                post = BlogPost(
                    id=f"post_seed_{idx+1:02d}",
                    slug=art["slug"],
                    title=art["title"],
                    meta_title=art["meta_title"],
                    meta_description=art["meta_description"],
                    focus_keyword=art["focus_keyword"],
                    category=art["category"],
                    tags_json=json.dumps(art["tags"]),
                    excerpt=art["excerpt"],
                    content_md=art["content_md"],
                    faqs_json=json.dumps(art["faqs"]),
                    status="published",
                    published_at=pub_dt,
                    updated_at=pub_dt,
                )
                db.add(post)

            default_export.append({
                "slug": art["slug"],
                "title": art["title"],
                "meta_title": art["meta_title"],
                "meta_description": art["meta_description"],
                "focus_keyword": art["focus_keyword"],
                "category": art["category"],
                "tags": art["tags"],
                "excerpt": art["excerpt"],
                "content_md": art["content_md"],
                "faqs": art["faqs"],
                "author_name": "Amarjeet S.",
                "author_bio": "Founder of LeadHarvest India & B2B Web Systems Architect.",
                "published_at": pub_dt.isoformat(),
                "updated_at": pub_dt.isoformat(),
            })

        await db.commit()

    # Also write static JSON fallback for Next.js SSG/ISR
    out_json = Path(r"C:\Users\HP\.gemini\antigravity\scratch\leadharvest-odisha\frontend\lib\default-posts.json")
    out_json.write_text(json.dumps(default_export, indent=2), encoding="utf-8")
    print(f"Seeded {len(ARTICLES)} blog posts to DB and exported to {out_json}.")


if __name__ == "__main__":
    asyncio.run(seed_blog_posts())
