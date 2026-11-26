# Compliance, Legal Notice & Technical Limitations

## 1. Compliance & Ethical Data Extraction Notice
LeadHarvest Odisha is designed strictly as a productivity tool for legitimate business-to-business (B2B) discovery.
- **Adherence to Terms of Service**: Web scraping of public directories must comply with the target website's Terms of Use, Robots Exclusion Protocol (`robots.txt`), and local regulations.
- **No CAPTCHA / Access Control Bypass**: In accordance with security engineering best practices and strict ethical guidelines, LeadHarvest Odisha **does not** implement CAPTCHA bypasses, proxy rotators, or fingerprint spoofers. If a verification challenge or bot detection is encountered, the platform gracefully pauses and alerts the operator.
- **Responsible Rate Limiting**: The system enforces deliberate pacing (2 to 5 second random delays between requests) and restricts page concurrency to 1–2 simultaneous contexts to avoid placing undue load on public web servers.

## 2. Data Protection Responsibilities (DPDP Act, India)
- Under the **Digital Personal Data Protection Act (DPDP Act, 2023)** of India, users must ensure that commercial contact information collected is handled in accordance with Indian privacy laws.
- Contact numbers should only be used for legitimate business inquiries.
- Unsolicited bulk telemarketing (spam) is prohibited under TRAI and DND (Do Not Disturb) regulations. Always verify phone numbers against the National Customer Preference Register (NCPR) before initiating telephone sales calls.

## 3. Known Limitations
1. **Dynamic Website Structure Changes**:
   - Public directories periodically alter their DOM class names, script structures, or internal API schemas. While LeadHarvest employs multi-tier extraction (API payload intercept -> `__NEXT_DATA__` JSON parsing -> DOM fallback), major site revamps may require updating DOM selector rules in `JustdialAdapter`.
2. **Missing Contact Numbers on Protected Listings**:
   - Certain business listings on Justdial conceal telephone numbers behind user login gates or virtual telephony routing (e.g., Click-to-Call masks). These records are safely filtered out to ensure only actionable leads with valid 10-digit Indian numbers reach the final output.
3. **Hardware & Network Pacing**:
   - Playwright browser automation requires system memory for headless browser instances. Running high scroll depths (>10) across dozens of cities in live mode requires sufficient RAM and stable internet connectivity.
