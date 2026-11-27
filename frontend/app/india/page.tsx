import type { Metadata } from "next";
import Link from "next/link";
import JsonLd from "@/components/JsonLd";
import { buildMetadata, breadcrumbSchema } from "@/lib/seo";
import { getAllStatesData } from "@/lib/state-seo-data";
import { MapPin, ArrowRight, Globe, ShieldCheck } from "lucide-react";

export const revalidate = 86400;

export const metadata: Metadata = buildMetadata({
  title: "All-India B2B Business Leads Directory (36 States & UTs) | LeadHarvest",
  description:
    "Explore B2B business leads across all 28 Indian states and 8 union territories. Your Home State is free forever; unlock any other state with a plan.",
  path: "/india",
});

export default function IndiaHubPage() {
  const states = getAllStatesData();
  const wave1 = states.filter((s) => s.wave === 1);
  const wave2 = states.filter((s) => s.wave === 2);
  const wave3 = states.filter((s) => s.wave === 3);

  return (
    <div className="max-w-6xl mx-auto space-y-10 pb-20">
      <JsonLd
        data={breadcrumbSchema([
          { name: "Home", path: "/" },
          { name: "India Business Leads", path: "/india" },
        ])}
      />

      <section className="bg-white rounded-3xl border border-slate-200 p-8 sm:p-10 space-y-4 shadow-xs">
        <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 text-xs font-bold border border-emerald-200">
          <Globe className="w-3.5 h-3.5" />
          <span>28 States &amp; 8 Union Territories</span>
        </span>
        <h1 className="text-3xl sm:text-4xl font-black text-slate-900">
          B2B Business Leads Across Every Indian State
        </h1>
        <p className="text-sm text-slate-600 max-w-3xl leading-relaxed">
          Your own <strong>Home State is free</strong> to collect and export. Select any state or union territory below to explore local business clusters, share of businesses without a website, top cities, and masked samples—all collected from public business directories in India.
        </p>
        <div className="flex flex-wrap gap-3 pt-2">
          <Link
            href="/#collector-wizard"
            className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold inline-flex items-center space-x-1.5"
          >
            <span>Start Collecting Free in Your State</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            href="/pricing"
            className="px-5 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold"
          >
            Unlock All 36 States &amp; UTs
          </Link>
        </div>
      </section>

      {/* Accessible Interactive India Coverage Map & Grid */}
      <section aria-label="Interactive State Directory" className="space-y-8">
        {[
          { title: "Wave 1: Priority Launch States", items: wave1, badge: "Top Opportunity" },
          { title: "Wave 2: High-Growth Commercial States", items: wave2, badge: "High Demand" },
          { title: "Wave 3: All Remaining States & Union Territories", items: wave3, badge: "All India" },
        ].map((grp) => (
          <div key={grp.title} className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-black text-slate-900">{grp.title}</h2>
              <span className="text-[11px] font-bold px-2.5 py-1 rounded-full bg-brand-50 text-brand-700 border border-brand-200">
                {grp.items.length} regions · {grp.badge}
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {grp.items.map((st) => (
                <Link
                  key={st.slug}
                  href={`/leads/${st.slug}`}
                  className="group bg-white p-4 rounded-2xl border border-slate-200 hover:border-brand-300 hover:shadow-sm transition-all flex items-center justify-between"
                >
                  <div className="min-w-0 pr-2">
                    <p className="text-sm font-black text-slate-900 group-hover:text-brand-700 flex items-center space-x-1.5">
                      <MapPin className="w-3.5 h-3.5 text-brand-600 shrink-0" />
                      <span className="truncate">{st.name}</span>
                    </p>
                    <p className="text-[11px] text-slate-500 mt-1">
                      {st.cities.length} cities · ~{st.noWebsitePct}% without website
                    </p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-brand-600 shrink-0" />
                </Link>
              ))}
            </div>
          </div>
        ))}
      </section>

      <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-600 flex items-center space-x-2">
        <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
        <span>Privacy-first: public state hubs show only aggregated directory statistics and masked samples—never raw phone numbers.</span>
      </div>
    </div>
  );
}
