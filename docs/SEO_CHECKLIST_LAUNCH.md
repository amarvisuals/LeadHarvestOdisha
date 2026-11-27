# LeadHarvest India – SEO Launch Checklist

1. **Canonical Domain & Redirects**:
   - Set `NEXT_PUBLIC_SITE_URL=https://your-domain.com` in Vercel / Docker environment.
   - Configure 301 redirect from `www` to apex domain (or vice versa) in DNS/Vercel.
2. **Verify Search Consoles**:
   - Set `NEXT_PUBLIC_GSC_VERIFICATION` and `NEXT_PUBLIC_BING_VERIFICATION` env vars.
   - Verify domain ownership in Google Search Console & Bing Webmaster Tools.
3. **Submit Sitemap & RSS**:
   - Submit `https://your-domain.com/sitemap.xml` in GSC and Bing.
   - Verify `https://your-domain.com/robots.txt` allows public pages and blocks `/admin`, `/api`, `/billing`, `/profile`, `/history`, `/settings`, `/progress`.
   - Verify `https://your-domain.com/llms.txt` is reachable.
4. **Structured Data Validation**:
   - Test `/`, `/pricing`, `/blog/<slug>`, and `/leads/odisha/cuttack/dentists-and-dental-clinics` in Google Rich Results Test.
5. **GA4 & Consent**:
   - Set `NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX` and confirm GA4 script loads only after clicking **Accept** on the cookie banner.
6. **Lighthouse Check**:
   - Run Lighthouse Mobile on `/`, `/pricing`, `/features/no-website-filter`, `/blog/<slug>`, and `/leads/...` targeting 90+ across Performance, SEO, Accessibility, and Best Practices.
