export interface FeaturePageData {
  slug: string;
  title: string;
  metaTitle: string;
  metaDescription: string;
  h1: string;
  summary: string;
  sections: Array<{ heading: string; body: string[] }>;
  faqs: Array<{ question: string; answer: string }>;
}

export interface UseCasePageData {
  slug: string;
  title: string;
  metaTitle: string;
  metaDescription: string;
  h1: string;
  summary: string;
  recommendedPreset: string;
  workflowSteps: string[];
  bodyParagraphs: string[];
  faqs: Array<{ question: string; answer: string }>;
}

export const FEATURES_DATA: FeaturePageData[] = [
  {
    slug: "no-website-filter",
    title: "No Website Filter",
    metaTitle: "Find Businesses Without a Website in India | LeadHarvest India",
    metaDescription:
      "Filter local business leads from public business directories in India that have no website listed. Built for web designers and agencies.",
    h1: "Find Local Businesses Without a Website in India",
    summary:
      "The No-Website filter isolates active, well-reviewed Indian businesses that still lack a website—giving web designers and digital agencies high-intent prospects ready for a custom site pitch.",
    sections: [
      {
        heading: "Why Targeting Businesses Without a Website Converts Better",
        body: [
          "Most freelancers and web design agencies waste hours cold-calling random businesses that already have a modern website or an in-house agency. When you filter exclusively for businesses with no website listed in public business directories in India, you immediately remove low-probability calls and focus on owners who have a clear, visible gap.",
          "Think about a dental clinic in Cuttack, an interior designer in Bhubaneswar, or a boutique hotel in Jaipur with 4.3 stars and 40+ customer reviews—yet zero website link. That business already has customers and revenue, which means they can afford a ₹15,000 to ₹45,000 website that turns directory searchers into direct bookings.",
          "LeadHarvest India checks the website field across every collected listing, combines it with our Mobile Available check, and surfaces a clickable WhatsApp link so your outreach starts in seconds."
        ],
      },
      {
        heading: "How the No-Website Workflow Works Step by Step",
        body: [
          "1. Choose your target state and cities (start with Odisha free, or unlock all 36 Indian states and union territories on Pro).",
          "2. Pick high-ticket service categories such as Dental Clinics, Hospitals, Interior Designers, Real Estate Agents, or Coaching Centres.",
          "3. Toggle on 'No Website Listed' or select the one-click 'Website Design Pitch' preset in Step 3.",
          "4. Export your clean Excel workbook with 'Has Website = No', 'Opportunity Score', and ready-to-click WhatsApp links."
        ],
      },
      {
        heading: "Combine With Rating & Review Filters for Maximum ROI",
        body: [
          "Not every business without a website is a good client. A shop with 1 review and a 2.1 rating may not invest in growth. By pairing the No-Website filter with Minimum Rating 3.5+ and Opportunity Score 60+, you build a list of established, growing local businesses that simply haven't built their online home yet."
        ],
      },
    ],
    faqs: [
      {
        question: "How accurate is the No-Website filter?",
        answer: "It inspects the website field from public business directory listings and marks 'Has Website = No' whenever no valid web URL is present. Paid plans can also enable optional HTTP verification.",
      },
      {
        question: "Can I try the No-Website filter for free?",
        answer: "Guests get 4 free standard runs in Odisha. The No-Website Smart Filter unlocks starting on the Starter plan at ₹499/month.",
      },
    ],
  },
  {
    slug: "opportunity-score",
    title: "Opportunity Score & Smart Filters",
    metaTitle: "Lead Opportunity Score (0-100) & Smart Filters | LeadHarvest India",
    metaDescription:
      "Prioritise B2B leads automatically using our transparent 0-100 Opportunity Score, rating bands, review counts, and Pitch Presets.",
    h1: "Smart Lead Filters & 0–100 Opportunity Score",
    summary:
      "Stop treating every row in a spreadsheet equally. LeadHarvest India scores every business from 0 to 100 based on website gap, mobile availability, review count, rating, and address completeness.",
    sections: [
      {
        heading: "Transparent 0–100 Opportunity Score Formula",
        body: [
          "Every collected lead is automatically evaluated using five clear signals: No website listed (+40 points), valid 10-digit Indian mobile number available (+20 points), low review count under 50 (+15 points), healthy rating between 3.5 and 4.7 (+15 points), and complete street address with pincode (+10 points).",
          "A business scoring 85–100 is tagged 'Hot Website Pitch' in your Excel sheet, allowing your sales team or virtual assistant to sort descending and contact the best prospects first every morning."
        ],
      },
      {
        heading: "Three Ready-Made Pitch Presets",
        body: [
          "Website Design Pitch: Targets businesses with no website, a valid mobile number, and rating >= 3.5. Perfect for selling WordPress, Next.js, or Shopify builds.",
          "SEO & Ads Pitch: Targets businesses that already have a website but fewer than 30 reviews—ideal for pitching Google Business Profile optimisation, local SEO, and Meta/Google Ads.",
          "Reputation Pitch: Targets businesses with ratings below 3.5 and 20+ reviews that urgently need reputation management and customer-experience consulting."
        ],
      },
    ],
    faqs: [
      {
        question: "Can I filter by minimum Opportunity Score before exporting?",
        answer: "Yes. On Pro and Agency plans, use the Minimum Opportunity Score slider (0 to 100) so low-value leads are excluded before your Excel file is even generated.",
      },
    ],
  },
  {
    slug: "all-india-coverage",
    title: "All-India Coverage",
    metaTitle: "All 36 Indian States & Cities B2B Lead Data | LeadHarvest India",
    metaDescription:
      "Collect local business leads across all 28 Indian states and 8 union territories with 200+ B2B categories.",
    h1: "All 28 States & 8 Union Territories Across India",
    summary:
      "Start locally in Odisha for free, then scale your outbound prospecting to Tier-1 metros and fast-growing Tier-2 cities across every state and union territory in India.",
    sections: [
      {
        heading: "Why Tier-2 & Tier-3 Indian Cities Are Goldmines",
        body: [
          "While Mumbai, Bengaluru, and Delhi are crowded with agencies pitching the same clinics and restaurants, Tier-2 cities such as Bhubaneswar, Cuttack, Jaipur, Indore, Kochi, Surat, Nagpur, and Lucknow have thousands of profitable businesses that still rely solely on word-of-mouth and directory listings.",
          "LeadHarvest India includes curated city and district lists across all 36 states and union territories, paired with over 200 B2B-relevant categories spanning healthcare, hospitality, real estate, education, manufacturing, and professional services."
        ],
      },
      {
        heading: "Smart Run Sizing & Plan Protection",
        body: [
          "When you pick multiple states, LeadHarvest defaults to selecting all major cities in each state while displaying a live total search counter (states × cities × categories) so you always stay in control of your monthly lead quota."
        ],
      },
    ],
    faqs: [
      {
        question: "Which states are available on Free vs Paid plans?",
        answer: "Guest and Free accounts include Odisha. Starter unlocks up to 3 states per run, while Pro and Agency unlock all 36 Indian states and union territories.",
      },
    ],
  },
  {
    slug: "auto-deduplication",
    title: "Automatic Deduplication",
    metaTitle: "Skip Duplicate Business Leads Automatically | LeadHarvest India",
    metaDescription:
      "Upload existing Excel/CSV lists and let our 3-tier deduplication engine exclude repeats across all your past runs.",
    h1: "Automatic 3-Tier Lead Deduplication",
    summary:
      "Never call the same prospect twice or pay for duplicate rows. Upload your existing Excel/CSV files and let LeadHarvest remember every lead you have ever generated.",
    sections: [
      {
        heading: "How 3-Tier Deduplication Protects Your Outreach",
        body: [
          "Rule 1 (Normalized Indian Phone Match): Strips +91, leading 0, spaces, hyphens, and brackets, then compares the last 10 digits. Even if your old sheet formatted a number as '098610-12345' and a new listing shows '+91 98610 12345', it is caught immediately.",
          "Rule 2 (Normalized Business Name + City): Matches cleaned business names within the same city.",
          "Rule 3 (RapidFuzz Fuzzy Matching): Catches near-identical business names and addresses (>= 90% token-sort similarity) inside the same city."
        ],
      },
      {
        heading: "Strictly Per-User Private Index",
        body: [
          "Every signed-in user gets an isolated Known Records index. Your uploaded client lists and past exports are never shared with other users, and you can inspect or clear your index anytime."
        ],
      },
    ],
    faqs: [
      {
        question: "What happens to skipped duplicates?",
        answer: "They are excluded from Sheet 1 ('Leads') and logged transparently in Sheet 3 ('Skipped Duplicates') with the exact matching rule and source file.",
      },
    ],
  },
  {
    slug: "excel-export",
    title: "One-Click Excel Export",
    metaTitle: "Clean 3-Sheet Excel & CSV Business Lead Export | LeadHarvest India",
    metaDescription:
      "Download formatted Excel (.xlsx) workbooks with clickable WhatsApp links, Opportunity Scores, frozen headers, and audit summaries.",
    h1: "One-Click Formatted Excel & CSV Lead Export",
    summary:
      "Every run produces a clean, ready-to-use 3-sheet Excel workbook—plus CSV export on Pro and Agency plans—so your team can start calling or messaging immediately.",
    sections: [
      {
        heading: "Inside Your 3-Sheet Excel Workbook",
        body: [
          "Sheet 1 (Leads): Styled header row with frozen top pane, auto-filter enabled, auto-fitted column widths, Opportunity Score, Lead Tag, Has Website (Yes/No), Mobile Available, and clickable Website and WhatsApp (wa.me) links.",
          "Sheet 2 (Summary): Complete audit of states, cities, categories, Smart Filters applied, total found, duplicates skipped, and execution duration.",
          "Sheet 3 (Skipped Duplicates): Full transparency showing why duplicate rows were removed."
        ],
      },
      {
        heading: "Resumable Runs & 30-Day to 12-Month Retention",
        body: [
          "Even if you pause or stop a run early, your partial leads are preserved and compiled into your downloadable Excel workbook. Free accounts retain files for 30 days; paid plans retain them for 12 months."
        ],
      },
    ],
    faqs: [
      {
        question: "Do Excel links work directly for WhatsApp outreach?",
        answer: "Yes. Every valid Indian mobile number automatically generates a clickable https://wa.me/91... hyperlink in the WhatsApp Link column.",
      },
    ],
  },
];

export const USE_CASES_DATA: UseCasePageData[] = [
  {
    slug: "web-design-agencies",
    title: "Web Design Agencies & Freelancers",
    metaTitle: "Find Clients for Web Design in India | LeadHarvest India",
    metaDescription:
      "Get daily lists of Indian clinics, restaurants, and local businesses without websites, complete with WhatsApp links and Opportunity Scores.",
    h1: "Lead Generation for Web Design Agencies & Freelancers",
    summary:
      "Stop competing on crowded freelance marketplaces. Pitch local Indian businesses that have strong customer reviews but no website yet.",
    recommendedPreset: "Website Design Pitch (No Website + Mobile + Rating ≥ 3.5)",
    workflowSteps: [
      "Select 2–3 high-margin categories like Dentists, Interior Designers, or Banquet Halls.",
      "Choose your target cities across Odisha or All India.",
      "Apply the 'Website Design Pitch' preset to filter for No Website + Valid Mobile.",
      "Sort your Excel sheet by Opportunity Score (80–100) and send 20 personalised WhatsApp messages per day."
    ],
    bodyParagraphs: [
      "When you pitch a business owner who already gets 4.2-star reviews but has no website, you are not convincing them that marketing matters—you are showing them the customers they are losing every week to competitors who have a clean site.",
      "Using LeadHarvest India, a solo web designer can build a targeted 100-lead Excel sheet in under 2 minutes, skip any clients they already pitched last month, and focus 100% of their time on closing ₹15,000–₹40,000 website projects."
    ],
    faqs: [
      {
        question: "How many leads do I need to close one website client?",
        answer: "Most agencies see 10–20% reply rates on tailored WhatsApp outreach to businesses with no website, meaning 50–100 qualified leads often generate 2–5 discovery calls.",
      },
    ],
  },
  {
    slug: "seo-digital-marketers",
    title: "SEO & Digital Marketers",
    metaTitle: "Local SEO & Ads Leads for Digital Marketers India | LeadHarvest",
    metaDescription:
      "Find under-marketed Indian businesses with websites and low review counts to pitch Local SEO, Google Ads, and Meta Ads.",
    h1: "Local SEO & Performance Marketing Leads in India",
    summary:
      "Identify businesses that already value online presence (they have a website) but suffer from low review counts or low ratings.",
    recommendedPreset: "SEO / Ads Pitch (Has Website + Reviews < 30)",
    workflowSteps: [
      "Enable 'Has Website' and set Maximum Reviews to 30.",
      "Target competitive local niches like Real Estate, Salons, Gyms, and Coaching Centres.",
      "Audit their website speed and Google Business Profile, then pitch a monthly SEO + review-growth retainer."
    ],
    bodyParagraphs: [
      "Businesses that already paid for a website understand digital value—they just lack traffic, rankings, and consistent reviews. The SEO / Ads Pitch preset isolates these exact prospects in one click."
    ],
    faqs: [
      {
        question: "Can I also find businesses needing reputation management?",
        answer: "Yes. Use the 'Reputation Pitch' preset (Rating < 3.5 and Reviews >= 20) to help clinics and restaurants fix customer feedback workflows.",
      },
    ],
  },
  {
    slug: "ca-finance-agents",
    title: "CAs, Tax & Insurance Advisors",
    metaTitle: "B2B Business Owner Leads for CAs & Finance Agents India",
    metaDescription:
      "Build clean lists of newly listed clinics, shops, and MSMEs across India for GST, tax filing, business loans, and insurance.",
    h1: "B2B Prospecting for CAs, Tax Consultants & Insurance Advisors",
    summary:
      "Reach MSME owners, clinic founders, and retail proprietors across your district with verified phone numbers and zero duplicate calls.",
    recommendedPreset: "Mobile Only + Exclude Chains/Franchises",
    workflowSteps: [
      "Select local commercial hubs in your district or state.",
      "Toggle 'Exclude Chains/Franchises' so you speak directly with independent business owners.",
      "Upload your existing client Excel list so current clients are automatically skipped."
    ],
    bodyParagraphs: [
      "Independent business owners make fast decisions on GST compliance, accounting retainers, and commercial insurance. Excluding multi-city chains ensures your team focuses strictly on local decision-makers."
    ],
    faqs: [
      {
        question: "Will it skip my existing client list?",
        answer: "Yes. Upload your current client Excel or CSV in Step 4 and our 3-tier deduplication engine excludes every existing client automatically.",
      },
    ],
  },
  {
    slug: "saas-software-sellers",
    title: "Software & SaaS Sellers",
    metaTitle: "Vertical SaaS Lead Lists in India (Clinics, Gyms, Hotels) | LeadHarvest",
    metaDescription:
      "Target specific Indian verticals like dental clinics, gyms, salons, and restaurants to sell POS, CRM, or booking software.",
    h1: "Vertical SaaS & POS Software Prospecting Across India",
    summary:
      "Selling clinic management, gym software, or restaurant billing? Build hyper-targeted city-by-city prospect lists across all 36 Indian states.",
    recommendedPreset: "Mobile Only + Rating ≥ 3.5 + Exclude Chains",
    workflowSteps: [
      "Pick your exact vertical (e.g., Dentists, Gyms, Salons, Hotels).",
      "Target Tier-1 and Tier-2 cities where SaaS adoption is growing fastest.",
      "Export CSV or Excel directly into your outbound CRM."
    ],
    bodyParagraphs: [
      "Vertical SaaS outbound works best when your sales reps know the prospect's exact category, city, rating, and review volume before dialing. LeadHarvest India delivers all of that in one clean spreadsheet."
    ],
    faqs: [
      {
        question: "Is CSV export supported for CRM import?",
        answer: "Yes, Pro and Agency plans include one-click CSV export alongside the formatted 3-sheet Excel workbook.",
      },
    ],
  },
  {
    slug: "b2b-sales-teams",
    title: "B2B Sales Teams",
    metaTitle: "B2B Sales Team Lead Generation & Deduplication India",
    metaDescription:
      "Equip your inside sales team with fresh, deduplicated regional business leads across India without manual copy-paste.",
    h1: "Scalable Outbound Lists for Indian B2B Sales Teams",
    summary:
      "Stop letting SDRs spend 2 hours a day searching directories manually. Deliver clean, territory-assigned Excel sheets in minutes.",
    recommendedPreset: "Mobile Only + Min Opportunity Score 60",
    workflowSteps: [
      "Assign specific states or cities to each sales rep.",
      "Upload your master CRM export so reps never call already-worked accounts.",
      "Use Agency seats and up to 40,000 leads/month."
    ],
    bodyParagraphs: [
      "Every hour an SDR spends researching phone numbers is an hour not spent pitching. LeadHarvest India centralises territory collection and deduplication."
    ],
    faqs: [
      {
        question: "How many team seats are included?",
        answer: "The Agency plan includes 3 team seats, 40,000 leads/month, and CSV + Excel export.",
      },
    ],
  },
  {
    slug: "startups",
    title: "Startups & Local Marketplaces",
    metaTitle: "Supply-Side Onboarding Leads for Indian Startups | LeadHarvest",
    metaDescription:
      "Onboard local merchants, clinics, tutors, and service providers across Indian cities faster with clean Excel lead lists.",
    h1: "Fast Merchant & Supply Onboarding for Indian Startups",
    summary:
      "Launching a hyperlocal marketplace, fintech product, or B2B supply app? Build your city-launch merchant list in minutes.",
    recommendedPreset: "All Categories in Target Launch Cities",
    workflowSteps: [
      "Select your launch city and target merchant categories.",
      "Run a quick collection and filter for active businesses with phone numbers.",
      "Hand the Excel sheet to your city-launch field or telesales team."
    ],
    bodyParagraphs: [
      "City launches live or die by how quickly you can contact local merchants. Start with 4 free guest tries in Odisha, then scale across India on Starter or Pro."
    ],
    faqs: [
      {
        question: "Can we test with 4 free runs before subscribing?",
        answer: "Yes, every visitor gets 4 free guest runs without a credit card.",
      },
    ],
  },
];
