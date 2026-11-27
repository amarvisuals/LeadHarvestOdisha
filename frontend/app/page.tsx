import Link from "next/link";
import LeadCollectorWizard from "@/components/LeadCollectorWizard";
import JsonLd from "@/components/JsonLd";
import { faqSchema, howToSchema } from "@/lib/seo";
import { Sparkles, Globe, Filter, FileSpreadsheet, ArrowRight, CheckCircle2 } from "lucide-react";

const HOME_FAQS = [
  {
    question: "Where does LeadHarvest India collect business leads from?",
    answer:
      "LeadHarvest India collects publicly listed business data from public business directories in India, normalises Indian phone numbers, scores website opportunities, and exports clean Excel sheets.",
  },
  {
    question: "Can I try LeadHarvest India before creating an account?",
    answer:
      "Yes. Every visitor gets 4 free guest runs in Odisha with no credit card required. When you create a free account, your previous runs and deduplication history carry over automatically.",
  },
  {
    question: "How does the 'No Website' filter help web design agencies?",
    answer:
      "It isolates active local businesses with strong ratings and valid WhatsApp numbers that have no website listed—giving your agency high-intent prospects ready for a custom website pitch.",
  },
  {
    question: "Does it remove duplicate leads from my old Excel sheets?",
    answer:
      "Yes. Upload your existing .xlsx or .csv files and our 3-tier deduplication engine automatically skips matching phone numbers, exact business name + city matches, and fuzzy address matches.",
  },
];

export default function HomePage({
  searchParams,
}: {
  searchParams?: { state?: string; city?: string; category?: string };
}) {
  return (
    <div className="space-y-14 pb-16">
      <JsonLd
        data={[
          faqSchema(HOME_FAQS),
          howToSchema("How to Collect B2B Business Leads in India", [
            { name: "Choose States & Categories", text: "Pick from 36 Indian states & UTs and 200+ B2B categories." },
            { name: "Apply Smart Filters", text: "Filter for businesses with No Website, valid mobile, and high Opportunity Score." },
            { name: "Export Clean Excel", text: "Download a deduplicated 3-sheet Excel workbook with clickable WhatsApp links." },
          ]),
        ]}
      />

      {/* Server-Rendered Above-the-Fold Hero */}
      <section className="bg-gradient-to-br from-white via-brand-50/40 to-amber-50/30 rounded-3xl border border-slate-200/80 p-6 sm:p-10 shadow-xs text-center space-y-5">
        <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-brand-50 border border-brand-200 text-brand-800 text-xs font-semibold">
          <Sparkles className="w-3.5 h-3.5 text-brand-600" />
          <span>B2B Lead Generation Software for India</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-black text-slate-900 tracking-tight max-w-3xl mx-auto leading-tight">
          Find Local Businesses in India Without a Website—In One Click
        </h1>
        <p className="text-base text-slate-600 max-w-2xl mx-auto">
          Collect verified business leads data from public business directories in India across all 36 states &amp; UTs. Filter by <strong>No Website</strong>, WhatsApp mobile, and Opportunity Score, then export a deduplicated Excel sheet.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-3 pt-1">
          <a
            href="#collector-wizard"
            className="px-6 py-3 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-sm inline-flex items-center space-x-2 shadow-md"
          >
            <span>Try 4 Free Runs Now</span>
            <ArrowRight className="w-4 h-4" />
          </a>
          <Link
            href="/features/no-website-filter"
            className="px-5 py-3 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 text-slate-800 font-bold text-sm"
          >
            See No-Website Filter
          </Link>
        </div>
      </section>

      {/* Interactive 4-Step Wizard */}
      <LeadCollectorWizard
        initialState={searchParams?.state}
        initialCity={searchParams?.city}
        initialCategory={searchParams?.category}
      />

      {/* SSR 3-Step How It Works */}
      <section className="bg-white rounded-3xl border border-slate-200 p-8 space-y-6">
        <div className="text-center max-w-2xl mx-auto space-y-1">
          <h2 className="text-2xl font-black text-slate-900">How LeadHarvest India Works in 3 Steps</h2>
          <p className="text-sm text-slate-500">From target city selection to outreach-ready Excel in under 2 minutes.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
          <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2">
            <Globe className="w-6 h-6 text-brand-600" />
            <h3 className="font-bold text-slate-900">1. Pick States, Cities &amp; Niches</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Target any city across 28 states and 8 union territories and 200+ B2B categories like Dentists, Restaurants, Real Estate, and Gyms.
            </p>
          </div>
          <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2">
            <Filter className="w-6 h-6 text-brand-600" />
            <h3 className="font-bold text-slate-900">2. Filter &amp; Auto-Deduplicate</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Apply the No-Website filter and Opportunity Score, and automatically exclude businesses already present in your uploaded Excel lists.
            </p>
          </div>
          <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2">
            <FileSpreadsheet className="w-6 h-6 text-brand-600" />
            <h3 className="font-bold text-slate-900">3. Export Excel + WhatsApp Links</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Download a formatted 3-sheet workbook with clickable WhatsApp (`wa.me`) links, Lead Tags, and transparent duplicate audit logs.
            </p>
          </div>
        </div>
      </section>

      {/* SSR Use Cases + Pricing Preview */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-3xl border border-slate-200 p-7 space-y-4">
          <h2 className="text-xl font-black text-slate-900">Built for Indian B2B Prospecting</h2>
          <ul className="space-y-2.5 text-xs text-slate-700">
            <li className="flex items-center space-x-2"><CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" /><Link href="/use-cases/web-design-agencies" className="font-semibold hover:text-brand-700">Web Design Agencies: Find businesses with No Website + 3.5★+ rating</Link></li>
            <li className="flex items-center space-x-2"><CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" /><Link href="/use-cases/seo-digital-marketers" className="font-semibold hover:text-brand-700">SEO &amp; Ads Marketers: Find sites with &lt; 30 reviews</Link></li>
            <li className="flex items-center space-x-2"><CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" /><Link href="/use-cases/ca-finance-agents" className="font-semibold hover:text-brand-700">CAs &amp; Finance Advisors: Reach independent MSME owners</Link></li>
            <li className="flex items-center space-x-2"><CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" /><Link href="/use-cases/saas-software-sellers" className="font-semibold hover:text-brand-700">SaaS &amp; POS Sellers: Target clinics, salons, and hotels</Link></li>
          </ul>
        </div>

        <div className="bg-gradient-to-br from-brand-800 to-brand-600 text-white rounded-3xl p-7 flex flex-col justify-between space-y-4">
          <div className="space-y-2">
            <span className="text-xs font-bold uppercase tracking-wider text-brand-200">Simple INR Plans</span>
            <h2 className="text-2xl font-black">Start Free, Upgrade Only When You Grow</h2>
            <p className="text-xs text-brand-100">
              4 free guest tries → Free account (Odisha) → Starter ₹499/mo → Pro ₹1,499/mo (All India + All Smart Filters) → Agency ₹3,999/mo.
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <Link href="/pricing" className="px-5 py-2.5 bg-white text-brand-900 font-bold text-xs rounded-xl">
              View All Plans
            </Link>
            <Link href="/tools/pitch-generator" className="px-4 py-2.5 bg-white/10 border border-white/20 text-white font-semibold text-xs rounded-xl">
              Try Free Pitch Generator
            </Link>
          </div>
        </div>
      </section>

      {/* SSR FAQ Section */}
      <section className="bg-white rounded-3xl border border-slate-200 p-8 space-y-5">
        <h2 className="text-2xl font-black text-slate-900">Frequently Asked Questions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs text-slate-600">
          {HOME_FAQS.map((f) => (
            <div key={f.question} className="space-y-1">
              <h3 className="font-bold text-slate-900 text-sm">{f.question}</h3>
              <p className="leading-relaxed">{f.answer}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
