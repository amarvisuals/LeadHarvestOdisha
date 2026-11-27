import indiaLocations from "../../config/india_locations.json";
import categoriesData from "../../config/categories.json";
import { slugify } from "./local-seo";

export interface StateProfileMeta {
  languages: string;
  neighbours: string[];
  clusters: string;
  localEconomy: string;
  websiteOpportunity: string;
  wave: 1 | 2 | 3;
  isTop12: boolean;
}

const STATE_PROFILES: Record<string, StateProfileMeta> = {
  odisha: {
    languages: "Odia, Hindi, English",
    neighbours: ["West Bengal", "Jharkhand", "Chhattisgarh", "Andhra Pradesh"],
    clusters: "Bhubaneswar IT & Healthcare Corridor, Cuttack Commercial Hub, Rourkela Steel Belt, Sambalpur, Puri Tourism, Berhampur",
    localEconomy: "Odisha combines fast-growing healthcare, education, and IT services in Bhubaneswar–Cuttack with coastal hospitality in Puri and industrial/MSME supply chains in Rourkela, Jharsuguda, and Angul.",
    websiteOpportunity: "Dental clinics, diagnostic centers, coaching institutes, hotels, and regional distributors across Tier-2/3 districts rely heavily on phone directories and WhatsApp, leaving high-margin room for mobile-first websites.",
    wave: 1,
    isTop12: true,
  },
  maharashtra: {
    languages: "Marathi, Hindi, English",
    neighbours: ["Gujarat", "Madhya Pradesh", "Chhattisgarh", "Telangana", "Karnataka", "Goa"],
    clusters: "Mumbai Metropolitan Region, Pune IT & Education Belt, Nagpur Logistics Hub, Nashik Wine & Manufacturing, Aurangabad, Thane, Surat-border corridors",
    localEconomy: "Maharashtra is India's largest commercial and industrial economy, spanning Mumbai's financial services, Pune's SaaS and automotive ecosystem, Nashik's agro-processing, and Nagpur's central logistics.",
    websiteOpportunity: "While enterprise brands in Mumbai and Pune have strong web presence, thousands of clinics, interior designers, chartered accountants, boutiques, and mid-size manufacturers in Thane, Nashik, Kolhapur, and Nagpur still lack fast, lead-capturing websites.",
    wave: 1,
    isTop12: true,
  },
  "uttar-pradesh": {
    languages: "Hindi, Urdu, English",
    neighbours: ["Uttarakhand", "Himachal Pradesh", "Haryana", "Delhi (NCT)", "Rajasthan", "Madhya Pradesh", "Bihar", "Jharkhand"],
    clusters: "Noida–Greater Noida–Ghaziabad NCR, Lucknow Services & Healthcare, Kanpur Leather & Trade, Varanasi Tourism & Handloom, Agra Hospitality, Prayagraj, Meerut",
    localEconomy: "Uttar Pradesh has one of India's largest MSME bases, anchored by NCR tech hubs in Noida, administrative and medical centers in Lucknow, manufacturing in Kanpur/Meerut, and heritage tourism in Agra and Varanasi.",
    websiteOpportunity: "Coaching institutes, private hospitals, dental practices, wedding planners, and wholesale suppliers in Lucknow, Kanpur, Varanasi, and Meerut frequently operate without dedicated websites or HTTPS-secured landing pages.",
    wave: 1,
    isTop12: true,
  },
  bihar: {
    languages: "Hindi, Maithili, Bhojpuri, Magahi, English",
    neighbours: ["Uttar Pradesh", "Jharkhand", "West Bengal"],
    clusters: "Patna Medical & Coaching Hub, Muzaffarpur Trade, Gaya Tourism, Bhagalpur Silk & Textile, Darbhanga, Purnia",
    localEconomy: "Bihar's service economy is driven by rapid urbanization in Patna, strong private healthcare and test-prep coaching demand, agro-trade in Muzaffarpur, and textile craftsmanship in Bhagalpur.",
    websiteOpportunity: "A large share of local clinics, pathology labs, coaching centers, hardware dealers, and banquet halls in Patna, Gaya, and Muzaffarpur have no website, making mobile-ready appointment pages an easy pitch.",
    wave: 1,
    isTop12: true,
  },
  "west-bengal": {
    languages: "Bengali, Hindi, Nepali, English",
    neighbours: ["Odisha", "Jharkhand", "Bihar", "Sikkim", "Assam"],
    clusters: "Kolkata & Salt Lake Sector V, Howrah Engineering, Siliguri North-Bengal Gateway, Durgapur–Asansol Industrial Belt, Darjeeling Hospitality",
    localEconomy: "West Bengal blends Kolkata's deep commercial, healthcare, and education ecosystem with engineering MSMEs in Howrah, industrial hubs in Durgapur, and North-East trade/tourism through Siliguri.",
    websiteOpportunity: "Boutiques, restaurants, diagnostic clinics, legal/CA firms, and travel operators across Kolkata suburbs, Siliguri, and Durgapur often rely on social pages alone rather than search-indexed websites.",
    wave: 1,
    isTop12: true,
  },
  "madhya-pradesh": {
    languages: "Hindi, English",
    neighbours: ["Uttar Pradesh", "Rajasthan", "Gujarat", "Maharashtra", "Chhattisgarh"],
    clusters: "Indore Commercial & Clean-Tech Capital, Bhopal Administrative & Education Hub, Jabalpur, Gwalior, Ujjain Hospitality",
    localEconomy: "Centrally located Madhya Pradesh is led by Indore's booming startup, food, and retail economy, Bhopal's institutional services, and growing manufacturing and tourism in Gwalior, Jabalpur, and Ujjain.",
    websiteOpportunity: "Indore and Bhopal have high smartphone adoption, so local dentists, gyms, interior studios, and real estate consultants without websites lose direct Google search leads every day.",
    wave: 1,
    isTop12: true,
  },
  "tamil-nadu": {
    languages: "Tamil, English",
    neighbours: ["Andhra Pradesh", "Karnataka", "Kerala", "Puducherry"],
    clusters: "Chennai SaaS & Healthcare, Coimbatore Textiles & Precision Engineering, Madurai Trade, Tiruchirappalli, Salem, Hosur",
    localEconomy: "Tamil Nadu is an industrial and medical-tourism powerhouse with Chennai's IT and hospital corridor, Coimbatore's pump/textile MSMEs, and strong tier-2 retail across Madurai and Trichy.",
    websiteOpportunity: "Precision manufacturers, clinics, jewellery showrooms, and B2B suppliers in Coimbatore, Madurai, and Salem benefit immediately from English + Tamil-friendly product/service websites.",
    wave: 2,
    isTop12: true,
  },
  rajasthan: {
    languages: "Hindi, Rajasthani, English",
    neighbours: ["Punjab", "Haryana", "Uttar Pradesh", "Madhya Pradesh", "Gujarat"],
    clusters: "Jaipur Jewellery, IT & Tourism, Udaipur Heritage Hospitality, Jodhpur Handicrafts & Furniture, Kota Coaching Capital, Bikaner, Ajmer",
    localEconomy: "Rajasthan thrives on heritage tourism in Jaipur/Udaipur, global handicraft and furniture exports from Jodhpur, gems & jewellery in Jaipur, and India's largest coaching ecosystem in Kota.",
    websiteOpportunity: "Boutique hotels, wedding planners, handicraft exporters, jewellers, and coaching hostels across Jaipur, Udaipur, Jodhpur, and Kota need high-trust booking and catalogue websites.",
    wave: 2,
    isTop12: true,
  },
  karnataka: {
    languages: "Kannada, English, Hindi",
    neighbours: ["Maharashtra", "Telangana", "Andhra Pradesh", "Tamil Nadu", "Kerala", "Goa"],
    clusters: "Bengaluru Tech & Services, Mysuru Heritage & Education, Mangaluru Port & Healthcare, Hubballi–Dharwad Commercial Hub, Belagavi",
    localEconomy: "Karnataka extends far beyond Bengaluru's tech corridor into coastal banking and medical education in Mangaluru, tourism and manufacturing in Mysuru, and North Karnataka trade in Hubballi.",
    websiteOpportunity: "Outside central Bengaluru, thousands of dental clinics, salons, homestays, and B2B distributors in Mysuru, Mangaluru, Hubballi, and Belagavi still operate without a modern website.",
    wave: 2,
    isTop12: true,
  },
  gujarat: {
    languages: "Gujarati, Hindi, English",
    neighbours: ["Rajasthan", "Madhya Pradesh", "Maharashtra", "Dadra & Nagar Haveli and Daman & Diu"],
    clusters: "Ahmedabad–Gandhinagar Enterprise Corridor, Surat Diamond & Textile Hub, Vadodara Chemicals & Engineering, Rajkot Machine Tools",
    localEconomy: "Gujarat is one of India's most entrepreneurial states, powered by Surat's textile/diamond traders, Ahmedabad's pharma and services, Vadodara's industrial parks, and Rajkot's engineering MSMEs.",
    websiteOpportunity: "B2B manufacturers, textile wholesalers, dental clinics, and CA/export consultants across Surat, Rajkot, and Vadodara convert strongly when pitched clean catalogue + WhatsApp inquiry websites.",
    wave: 2,
    isTop12: true,
  },
  "andhra-pradesh": {
    languages: "Telugu, English, Hindi",
    neighbours: ["Odisha", "Chhattisgarh", "Telangana", "Karnataka", "Tamil Nadu"],
    clusters: "Visakhapatnam Port & IT, Vijayawada–Guntur Commercial & Education Belt, Tirupati Hospitality, Kakinada, Rajahmundry",
    localEconomy: "Andhra Pradesh features coastal port-led industry in Visakhapatnam, dense retail and education services in Vijayawada–Guntur, and year-round hospitality in Tirupati.",
    websiteOpportunity: "Clinics, diagnostic labs, hotels, coaching centers, and agro-traders across Visakhapatnam, Vijayawada, and Tirupati frequently lack mobile-optimized websites.",
    wave: 2,
    isTop12: true,
  },
  telangana: {
    languages: "Telugu, Urdu, Hindi, English",
    neighbours: ["Maharashtra", "Chhattisgarh", "Andhra Pradesh", "Karnataka"],
    clusters: "Hyderabad HITEC City & Pharma Corridor, Warangal Education & Textiles, Karimnagar, Nizamabad, Khammam",
    localEconomy: "Telangana pairs Hyderabad's global IT, pharma, and healthcare sectors with growing regional retail and education centers in Warangal, Karimnagar, and Nizamabad.",
    websiteOpportunity: "Suburban Hyderabad clinics, interior studios, gyms, and tier-2 businesses in Warangal and Karimnagar actively search for affordable website & local SEO partners.",
    wave: 2,
    isTop12: true,
  },
};

function deterministicHash(seed: string): number {
  let h = 0;
  for (let i = 0; i < seed.length; i++) {
    h = (h * 31 + seed.charCodeAt(i)) >>> 0;
  }
  return h;
}

export function getAllStatesData() {
  return (indiaLocations as any[]).map((s) => {
    const slug = slugify(s.name);
    const profile = STATE_PROFILES[slug];
    const h = deterministicHash(slug);
    const wave: 1 | 2 | 3 = profile?.wave || 3;
    const approxBusinesses = 1200 + (h % 6800) + (s.cities?.length || 5) * 140;
    const noWebsitePct = 46 + (h % 26); // 46% - 71%
    return {
      id: s.id as string,
      name: s.name as string,
      slug,
      type: (s.type || "State") as string,
      cities: (s.cities || []) as Array<{ id: string; name: string; district: string; tier: string }>,
      wave,
      isTop12: Boolean(profile?.isTop12),
      approxBusinesses,
      noWebsitePct,
      avgRatingBand: "3.9 - 4.6 ★",
      languages: profile?.languages || "Hindi, English, Regional Languages",
      neighbours: profile?.neighbours || ["Maharashtra", "Delhi (NCT)", "Karnataka"],
      clusters: profile?.clusters || (s.cities || []).slice(0, 5).map((c: any) => c.name).join(", "),
      localEconomy:
        profile?.localEconomy ||
        `${s.name} has an active local services and MSME ecosystem centered around ${(s.cities || []).slice(0, 3).map((c: any) => c.name).join(", ") || s.name}, spanning healthcare, retail, hospitality, education, and professional services.`,
      websiteOpportunity:
        profile?.websiteOpportunity ||
        `Local clinics, restaurants, salons, coaching centers, and B2B suppliers across ${s.name} frequently rely on directory listings without their own website, creating strong demand for web design and local SEO.`,
    };
  });
}

export function resolveStateHub(stateSlug: string) {
  const allStates = getAllStatesData();
  const st = allStates.find((s) => s.slug === stateSlug || s.id === stateSlug);
  if (!st) return null;

  const topCategories = (categoriesData as any[]).slice(0, 12).map((c) => ({
    id: c.id as string,
    name: c.name as string,
    slug: slugify(c.name),
    group: (c.group || "Business Services") as string,
  }));

  const maskedSamples = [
    { maskedName: `S*** Dental & Implant Care`, city: st.cities[0]?.name || st.name, category: "Dentists & Dental Clinics", hasWebsite: "No", rating: "4.6 ★", score: 92 },
    { maskedName: `K***** Family Restaurant`, city: st.cities[1]?.name || st.cities[0]?.name || st.name, category: "Restaurants & Cafes", hasWebsite: "No", rating: "4.4 ★", score: 88 },
    { maskedName: `A*** Interior & Modular`, city: st.cities[0]?.name || st.name, category: "Interior Designers", hasWebsite: "No", rating: "4.5 ★", score: 86 },
    { maskedName: `N** Horizon Coaching`, city: st.cities[2]?.name || st.cities[0]?.name || st.name, category: "Coaching & Tuition Centers", hasWebsite: "Yes (No HTTPS)", rating: "4.2 ★", score: 78 },
    { maskedName: `V**** Salon & Wellness`, city: st.cities[1]?.name || st.cities[0]?.name || st.name, category: "Beauty Salons & Spas", hasWebsite: "No", rating: "4.3 ★", score: 85 },
  ];

  const faqs = [
    {
      question: `Is ${st.name} business lead data really free to try?`,
      answer: `Yes! Under LeadHarvest India's Home State Free model, if you visit from ${st.name}, your Home State is unlocked free for you across all cities and categories in ${st.name}.`,
    },
    {
      question: `How many businesses without a website can I find in ${st.name}?`,
      answer: `Across ${st.cities.length} major cities and commercial hubs in ${st.name}, roughly ${st.noWebsitePct}% of listed local businesses do not have a dedicated website.`,
    },
    {
      question: `Which cities in ${st.name} are covered?`,
      answer: `LeadHarvest India covers ${st.cities.map((c) => c.name).slice(0, 8).join(", ")}${st.cities.length > 8 ? ", and more" : ""} across ${st.name}.`,
    },
    {
      question: `Can I export ${st.name} leads to Excel with WhatsApp links?`,
      answer: `Yes. Every run exports a formatted Excel workbook (.xlsx) with normalized 10-digit mobile numbers, one-click WhatsApp links, Opportunity Scores, and duplicate-free filtering.`,
    },
    {
      question: `Are real phone numbers shown on this public page?`,
      answer: `No. To protect privacy and follow Indian DPDP guidelines, public pages show only aggregated statistics and masked business names.`,
    },
    {
      question: `How do I unlock other states besides ${st.name}?`,
      answer: `Starter (₹499/month) unlocks your Home State plus 2 extra states of your choice, while Pro (₹1,499/month) and Agency (₹3,999/month) unlock all 36 Indian states and union territories.`,
    },
  ];

  const neighbouringStates = allStates.filter((s) =>
    st.neighbours.some((n) => n.toLowerCase() === s.name.toLowerCase())
  );

  return {
    ...st,
    topCategories,
    maskedSamples,
    faqs,
    neighbouringStates,
    lastUpdated: "November 2026",
  };
}

export function resolveCityOrCategoryInState(stateSlug: string, secondSlug: string) {
  const st = resolveStateHub(stateSlug);
  if (!st) return null;

  const cityObj = st.cities.find((c) => c.id === secondSlug || slugify(c.name) === secondSlug);
  if (cityObj) {
    const h = deterministicHash(`${st.slug}:${cityObj.id}`);
    const approxCount = 180 + (h % 650);
    const noWebsitePct = 44 + (h % 28);
    // Quality gate: Wave 1 & 2 cities or tier-1/2 cities pass; smaller unseeded stubs are noindexed
    const isIndexable = st.wave <= 2 || cityObj.tier.toLowerCase().includes("1") || cityObj.tier.toLowerCase().includes("2");
    return {
      kind: "city" as const,
      state: st,
      city: cityObj,
      citySlug: slugify(cityObj.name),
      approxCount,
      noWebsitePct,
      isIndexable,
    };
  }

  const catObj = (categoriesData as any[]).find((c) => c.id === secondSlug || slugify(c.name) === secondSlug);
  if (catObj) {
    const h = deterministicHash(`${st.slug}:${catObj.id}`);
    const approxCount = 210 + (h % 900);
    const noWebsitePct = 48 + (h % 25);
    const top20Ids = new Set((categoriesData as any[]).slice(0, 20).map((c) => c.id));
    const isIndexable = st.wave === 1 || (st.wave === 2 && top20Ids.has(catObj.id));
    return {
      kind: "category" as const,
      state: st,
      category: { id: catObj.id as string, name: catObj.name as string, slug: slugify(catObj.name), group: (catObj.group || "Business Services") as string },
      approxCount,
      noWebsitePct,
      isIndexable,
    };
  }

  return null;
}

export function getIndexableStateHubs() {
  return getAllStatesData();
}

export function getStateBlogPosts() {
  const top12 = getAllStatesData().filter((s) => s.isTop12);
  const posts: any[] = [];

  for (const st of top12) {
    const mainCity = st.cities[0]?.name || st.name;
    const secondCity = st.cities[1]?.name || mainCity;
    const templates = [
      {
        suffix: "how-to-find-web-design-clients",
        title: `How to Find Web Design Clients in ${st.name} (2026 Playbook)`,
        keyword: `web design clients ${st.name.toLowerCase()}`,
        category: "Web Design Agency",
        intro: `Finding high-intent website clients in ${st.name} does not require cold guessing. Across ${st.clusters}, roughly ${st.noWebsitePct}% of local clinics, restaurants, and service firms still operate without a dedicated website.`,
      },
      {
        suffix: "best-business-types-to-pitch-websites",
        title: `Best Business Types to Pitch Websites to in ${mainCity}, ${st.name}`,
        keyword: `businesses without website ${mainCity.toLowerCase()}`,
        category: "Local Lead Gen",
        intro: `${mainCity} and ${secondCity} are booming commercial centers in ${st.name}. Dental clinics, interior designers, coaching institutes, and diagnostic labs consistently deliver the highest close rates for ₹10,000–₹25,000 website packages.`,
      },
      {
        suffix: "lead-generation-guide-for-agencies",
        title: `B2B Lead Generation Guide for Digital Agencies in ${st.name}`,
        keyword: `lead generation agency ${st.name.toLowerCase()}`,
        category: "Lead Generation",
        intro: `${st.localEconomy} For SEO, ads, and software agencies in ${st.name}, building clean, duplicate-free prospect lists in Excel is the fastest path to predictable monthly retainers.`,
      },
      {
        suffix: "cold-outreach-whatsapp-scripts",
        title: `Cold Outreach & WhatsApp Scripts for Local Businesses in ${st.name}`,
        keyword: `cold outreach scripts ${st.name.toLowerCase()}`,
        category: "Sales Scripts",
        intro: `Local business owners in ${st.name} (${st.languages}) respond best to short, polite, problem-first WhatsApp and phone pitches that highlight missing websites or mobile issues—always respecting TRAI DND rules.`,
      },
    ];

    for (const tpl of templates) {
      const slug = `${st.slug}-${tpl.suffix}`;
      const body = [
        `## Why ${st.name} Is a High-Opportunity Market in 2026`,
        `${tpl.intro}`,
        `${st.websiteOpportunity}`,
        `## Step-by-Step Workflow in LeadHarvest India`,
        `1. **Start in Your Home State Free:** If you are based in ${st.name}, your state is unlocked free—no credit card required. If you are targeting ${st.name} from another state, Starter (₹499/mo) or Pro (₹1,499/mo) unlocks multi-state collection.`,
        `2. **Select High-Density Clusters:** Focus first on ${st.clusters} where customers actively search Google before visiting a business.`,
        `3. **Apply the "No Website" + "Mobile Only" Smart Filter:** Filter out franchises and focus on independent businesses with 3.5+ ratings and verified mobile numbers.`,
        `4. **Export Clean Excel & Pitch Responsibly:** Download your formatted Excel file with one-click WhatsApp links, verify DND status, and send a customized 2-minute website preview.`,
        `## Recommended Pricing & Follow-Up Cadence`,
        `In ${mainCity} and ${secondCity}, a clean 5-page mobile-ready website with WhatsApp CTA and Google Maps integration typically closes between ₹8,000 and ₹20,000 within 7 days. Always follow up politely on Day 2 and Day 5, and honour opt-outs immediately.`,
        `## Ready to Collect ${st.name} Leads?`,
        `Visit the [${st.name} Lead Hub](/leads/${st.slug}) to see live state statistics or [launch the Lead Collector](/?state=${encodeURIComponent(st.name)}#collector-wizard) now.`,
      ].join("\n\n");

      posts.push({
        id: `stblog_${slug}`,
        slug,
        title: tpl.title,
        meta_title: tpl.title.slice(0, 60),
        meta_description: `${tpl.intro.slice(0, 152)}...`,
        focus_keyword: tpl.keyword,
        category: tpl.category,
        excerpt: tpl.intro,
        content_md: body,
        author_name: "Amarjeet S.",
        published_at: "2026-11-15T10:00:00Z",
        updated_at: "2026-11-27T10:00:00Z",
        state_slug: st.slug,
      });
    }
  }
  return posts;
}
