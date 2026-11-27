import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import JsonLd from "@/components/JsonLd";
import { SITE_URL, buildMetadata, breadcrumbSchema, faqSchema } from "@/lib/seo";
import { getAllStatesData, resolveStateHub } from "@/lib/state-seo-data";
import { MapPin, ArrowRight, Globe, Star, ShieldCheck, CheckCircle2, FileBarChart } from "lucide-react";

export const revalidate = 86400;

export function generateStaticParams() {
  return getAllStatesData().map((s) => ({ state: s.slug }));
}

export function generateMetadata({ params }: { params: { state: string } }): Metadata {
  const st = resolveStateHub(params.state);
  if (!st) return {};

  const base = buildMetadata({
    title: `Business Leads in ${st.name} (No-Website Filter) | LeadHarvest`,
    description: `Find ${st.approxBusinesses.toLocaleString()}+ B2B business leads in ${st.name}. ~${st.noWebsitePct}% have no website listed. Your Home State is free to export.`,
    path: `/leads/${st.slug}`,
  });

  const languages: Record<string, string> = {
    "en-IN": `${SITE_URL}/leads/${st.slug}`,
    "x-default": `${SITE_URL}/leads/${st.slug}`,
  };
  if (st.slug === "odisha") languages["or-IN"] = `${SITE_URL}/or/leads/${st.slug}`;
  if (["uttar-pradesh", "madhya-pradesh", "bihar", "rajasthan", "delhi-nct"].includes(st.slug)) {
    languages["hi-IN"] = `${SITE_URL}/hi/leads/${st.slug}`;
  }

  return {
    ...base,
    alternates: {
      canonical: `${SITE_URL}/leads/${st.slug}`,
      languages,
    },
  };
}

export default function StateHubPage({ params }: { params: { state: string } }) {
  const st = resolveStateHub(params.state);
  if (!st) notFound();

  const prefillHref = `/?state=${encodeURIComponent(st.name)}#collector-wizard`;

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-20">
      <JsonLd
        data={[
          breadcrumbSchema([
            { name: "Home", path: "/" },
            { name: "India", path: "/india" },
            { name: st.name, path: `/leads/${st.slug}` },
          ]),
          faqSchema(st.faqs),
        ]}
      />

      <nav aria-label="Breadcrumb" className="text-xs text-slate-500 flex items-center space-x-2">
        <Link href="/" className="hover:text-brand-700">Home</Link>
        <span>/</span>
        <Link href="/india" className="hover:text-brand-700">India</Link>
        <span>/</span>
        <span className="font-semibold text-slate-800">{st.name}</span>
      </nav>

      {/* Hero + Home State Free Callout */}
      <article className="bg-white rounded-3xl border border-slate-200 p-8 space-y-6 shadow-xs">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-brand-50 text-brand-700 text-xs font-bold border border-brand-200">
            <MapPin className="w-3.5 h-3.5" />
            <span>{st.name} · {st.type}</span>
          </span>
          <span className="text-[11px] text-slate-400">Data last updated: {st.lastUpdated}</span>
        </div>

        <h1 className="text-3xl sm:text-4xl font-black text-slate-900">
          B2B Business Leads &amp; No-Website Prospects in {st.name}
        </h1>

        <p className="text-sm text-slate-700 leading-relaxed">
          Collect verified business leads from public business directories across {st.name}, filter out companies that already have a website, and export clean Excel sheets with WhatsApp outreach links.
        </p>

        {/* Home State Free CTA Box */}
        <div className="p-5 rounded-2xl bg-emerald-50 border border-emerald-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <p className="text-sm font-black text-emerald-950">
              Visiting from {st.name}? Your state&apos;s data is free.
            </p>
            <p className="text-xs text-emerald-800 mt-0.5">
              Start with {st.name} pre-selected in the collector—no credit card required.
            </p>
          </div>
          <Link
            href={prefillHref}
            className="px-5 py-2.5 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold inline-flex items-center space-x-1.5 shrink-0"
          >
            <span>Collect {st.name} Leads Free</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {/* Computed Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200">
            <span className="text-slate-400 font-semibold block">Businesses Indexed</span>
            <strong className="text-2xl font-black text-slate-900">{st.approxBusinesses.toLocaleString()}+</strong>
          </div>
          <div className="p-4 rounded-2xl bg-amber-50/70 border border-amber-200">
            <span className="text-amber-800 font-semibold block">No Website Listed</span>
            <strong className="text-2xl font-black text-amber-700">{st.noWebsitePct}%</strong>
          </div>
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200">
            <span className="text-slate-400 font-semibold block">Cities Covered</span>
            <strong className="text-2xl font-black text-slate-900">{st.cities.length}</strong>
          </div>
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200">
            <span className="text-slate-400 font-semibold block">Avg Rating Band</span>
            <strong className="text-lg font-black text-slate-900 flex items-center space-x-1">
              <Star className="w-4 h-4 text-amber-500" />
              <span>{st.avgRatingBand}</span>
            </strong>
          </div>
        </div>

        {/* Unique State Business Overview */}
        <div className="space-y-3 text-sm text-slate-700 leading-relaxed pt-2">
          <h2 className="text-xl font-black text-slate-900">{st.name} Business Ecosystem &amp; Website Opportunity</h2>
          <p>{st.localEconomy}</p>
          <p>{st.websiteOpportunity}</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-2">
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
              <strong className="block text-slate-900 mb-1">Major Business Clusters</strong>
              <span>{st.clusters}</span>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
              <strong className="block text-slate-900 mb-1">Primary Business Languages</strong>
              <span>{st.languages}</span>
            </div>
          </div>
        </div>

        {/* Who Uses This in {State} */}
        <div className="space-y-3 pt-2">
          <h2 className="text-xl font-black text-slate-900">Who Uses LeadHarvest in {st.name}</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            {[
              { role: "Web Designers & Studios", desc: `Use the No-Website filter across ${st.cities[0]?.name || st.name} to pitch ₹10k–₹25k custom websites to clinics, salons, and restaurants.` },
              { role: "SEO & Google Ads Freelancers", desc: `Find established businesses in ${st.name} with strong reviews that need Google Business optimization and landing pages.` },
              { role: "CAs, Insurance & FinTech", desc: `Build clean regional MSME prospect lists across ${st.clusters} for GST, compliance, and business loan outreach.` },
              { role: "SaaS & Billing Software Sellers", desc: `Target retail stores, gyms, and clinics in ${st.name} ready for POS, appointment, or CRM software.` },
            ].map((u) => (
              <div key={u.role} className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-1">
                <p className="font-bold text-slate-900">{u.role}</p>
                <p className="text-slate-600">{u.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Top Cities & Top Categories */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
          <div className="space-y-2.5">
            <h2 className="text-base font-black text-slate-900">Top Cities in {st.name}</h2>
            <div className="flex flex-wrap gap-1.5">
              {st.cities.slice(0, 14).map((c) => (
                <Link
                  key={c.id}
                  href={`/leads/${st.slug}/${c.id}`}
                  className="px-3 py-1.5 rounded-xl bg-slate-50 hover:bg-brand-50 border border-slate-200 text-xs font-semibold text-slate-700 hover:text-brand-700"
                >
                  {c.name}
                </Link>
              ))}
            </div>
          </div>

          <div className="space-y-2.5">
            <h2 className="text-base font-black text-slate-900">Top Categories in {st.name}</h2>
            <div className="flex flex-wrap gap-1.5">
              {st.topCategories.map((cat) => (
                <Link
                  key={cat.id}
                  href={`/leads/${st.slug}/${cat.slug}`}
                  className="px-3 py-1.5 rounded-xl bg-slate-50 hover:bg-brand-50 border border-slate-200 text-xs font-semibold text-slate-700 hover:text-brand-700"
                >
                  {cat.name}
                </Link>
              ))}
            </div>
          </div>
        </div>

        {/* Masked Sample Table */}
        <div className="space-y-2 pt-2">
          <h2 className="text-base font-black text-slate-900">Masked Sample Leads in {st.name}</h2>
          <p className="text-xs text-slate-500">Phone numbers are hidden on public pages for privacy.</p>
          <div className="overflow-x-auto border border-slate-200 rounded-2xl">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-50 text-slate-500">
                <tr>
                  <th className="p-3">Business (Masked)</th>
                  <th className="p-3">City</th>
                  <th className="p-3">Category</th>
                  <th className="p-3">Website</th>
                  <th className="p-3">Opportunity Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {st.maskedSamples.map((row, idx) => (
                  <tr key={idx}>
                    <td className="p-3 font-semibold text-slate-800">{row.maskedName}</td>
                    <td className="p-3 text-slate-600">{row.city}</td>
                    <td className="p-3 text-slate-600">{row.category}</td>
                    <td className="p-3 text-amber-700 font-bold">{row.hasWebsite}</td>
                    <td className="p-3 font-black text-brand-700">{row.score}/100</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Opportunity Report & Pricing Link */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 text-xs">
          <Link href={`/reports/${st.slug}`} className="p-4 rounded-2xl bg-brand-50 border border-brand-200 hover:bg-brand-100/70 flex items-center justify-between">
            <div>
              <p className="font-black text-brand-900 flex items-center space-x-1.5">
                <FileBarChart className="w-4 h-4" />
                <span>Q4 {st.name} Opportunity Report</span>
              </p>
              <p className="text-brand-800 mt-0.5">Category &amp; city breakdown of businesses without websites</p>
            </div>
            <ArrowRight className="w-4 h-4 text-brand-700" />
          </Link>
          <Link href="/pricing" className="p-4 rounded-2xl bg-slate-900 text-white hover:bg-slate-800 flex items-center justify-between">
            <div>
              <p className="font-black">Unlock Multi-State &amp; Smart Filters</p>
              <p className="text-slate-300 mt-0.5">Starter ₹499/mo · Pro ₹1,499/mo (All 36 States)</p>
            </div>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {/* FAQ */}
        <div className="space-y-3 pt-4 border-t border-slate-100">
          <h2 className="text-xl font-black text-slate-900">Frequently Asked Questions ({st.name})</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            {st.faqs.map((f, i) => (
              <div key={i} className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-1">
                <p className="font-bold text-slate-900">{f.question}</p>
                <p className="text-slate-600 leading-relaxed">{f.answer}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Neighbouring States & Back to India Hub */}
        <div className="pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="font-bold text-slate-500">Nearby States:</span>
            {st.neighbouringStates.map((n) => (
              <Link key={n.slug} href={`/leads/${n.slug}`} className="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 font-semibold text-slate-700">
                {n.name}
              </Link>
            ))}
          </div>
          <Link href="/india" className="font-bold text-brand-700 hover:underline">
            ← All 36 Indian States &amp; UTs
          </Link>
        </div>
      </article>
    </div>
  );
}
