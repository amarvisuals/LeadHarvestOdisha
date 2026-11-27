import { NextResponse } from "next/server";
import { SITE_URL, SITE_NAME, SUPPORT_EMAIL } from "@/lib/seo";

export async function GET() {
  const content = `# ${SITE_NAME}
> B2B lead-data platform that finds local businesses from public business directories in India by state, city, and category, with smart filters (such as "businesses with no website") and one-click Excel export.

## Key Public Pages
- Home & Collector: ${SITE_URL}/
- Pricing (INR): ${SITE_URL}/pricing
- About Us: ${SITE_URL}/about
- Blog & Guides: ${SITE_URL}/blog
- RSS Feed: ${SITE_URL}/blog/rss.xml

## Core Features
- Find Businesses Without a Website: ${SITE_URL}/features/no-website-filter
- Smart Lead Filters & Opportunity Score: ${SITE_URL}/features/opportunity-score
- All India States & Cities (36 Regions): ${SITE_URL}/features/all-india-coverage
- Automatic Lead Deduplication: ${SITE_URL}/features/auto-deduplication
- One-Click Excel & CSV Export: ${SITE_URL}/features/excel-export

## Free B2B Tools
- Website Pitch Email & WhatsApp Generator: ${SITE_URL}/tools/pitch-generator
- Agency Lead Cost & ROI Calculator: ${SITE_URL}/tools/agency-roi-calculator
- WhatsApp Link (wa.me) Generator: ${SITE_URL}/tools/whatsapp-link-generator
- Free Excel Lead Tracker Templates: ${SITE_URL}/tools/excel-lead-templates

## Contact & Legal
- Contact: ${SITE_URL}/contact (${SUPPORT_EMAIL})
- Privacy Policy (India DPDP Act 2023): ${SITE_URL}/privacy
- Terms of Use: ${SITE_URL}/terms
- Refund Policy: ${SITE_URL}/refund
`;

  return new NextResponse(content, {
    headers: { "Content-Type": "text/plain; charset=utf-8" },
  });
}
