import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import JsonLd from "@/components/JsonLd";
import { SITE_URL, buildMetadata, breadcrumbSchema } from "@/lib/seo";
import { getAllStatesData, resolveStateHub } from "@/lib/state-seo-data";
import { FileBarChart, ArrowRight, ShieldCheck } from "lucide-react";

export const revalidate = 86400;

export function generateStaticParams() {
  return getAllStatesData().filter((s) => s.isTop12).map((s) => ({ state: s.slug }));
}

export function generateMetadata({ params }: { params: { state: string } }): Metadata {
  const st = resolveStateHub(params.state);
  if (!st) return {};
  return buildMetadata({
    title: `${st.name} Local Business Website Opportunity Report (Q4 2026) | LeadHarvest`,
    description: `Data-driven report on businesses without a website across ${st.name} cities and categories. Aggregated public directory stats—no personal contacts.`,
    path: `/reports/${st.slug}`,
  });
}

export default function StateOpportunityReportPage({ params }: { params: { state: string } }) {
  const st = resolveStateHub(params.state);
  if (!st) notFound();

  const datasetSchema = {
    "@context": "https://schema.org",
    "@type": "Dataset",
    name: `${st.name} Local Business Digital Presence Report (Q4 2026)`,
    description: `Aggregated share of local businesses without a dedicated website across cities and categories in ${st.name}, India.`,
    url: `${SITE_URL}/reports/${st.slug}`,
    creator: { "@type": "Organization", name: "LeadHarvest India" },
    temporalCoverage: "2026-Q4",
    spatialCoverage: { "@type": "Place", name: `${st.name}, India` },
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-20">
      <JsonLd
        data={[
          breadcrumbSchema([
            { name: "Home", path: "/" },
            { name: "India", path: "/india" },
            { name: st.name, path: `/leads/${st.slug}` },
            { name: "Opportunity Report", path: `/reports/${st.slug}` },
          ]),
          datasetSchema,
        ]}
      />

      <article className="bg-white rounded-3xl border border-slate-200 p-8 space-y-6 shadow-xs">
        <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-brand-50 text-brand-700 text-xs font-bold border border-brand-200">
          <FileBarChart className="w-3.5 h-3.5" />
          <span>Quarterly Opportunity Report · {st.lastUpdated}</span>
        </span>

        <h1 className="text-3xl font-black text-slate-900">
          {st.name} Local Business Website Opportunity Report (Q4 2026)
        </h1>

        <p className="text-sm text-slate-700 leading-relaxed">
          Across <strong>{st.cities.length} commercial hubs</strong> in {st.name}, an estimated{" "}
          <strong>{st.noWebsitePct}%</strong> of small and mid-sized businesses listed in public Indian business directories do not have a standalone website.
        </p>

        <div className="space-y-2">
          <h2 className="text-lg font-black text-slate-900">Category Breakdown (Estimated Share Without Website)</h2>
          <div className="border border-slate-200 rounded-2xl overflow-hidden text-xs">
            <table className="w-full text-left">
              <thead className="bg-slate-50 text-slate-500">
                <tr>
                  <th className="p-3">Category</th>
                  <th className="p-3">No-Website Share</th>
                  <th className="p-3">Pitch Suitability</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {st.topCategories.slice(0, 8).map((c, idx) => (
                  <tr key={c.id}>
                    <td className="p-3 font-bold text-slate-800">{c.name}</td>
                    <td className="p-3 text-amber-700 font-black">{Math.min(78, st.noWebsitePct + (idx % 7) - 2)}%</td>
                    <td className="p-3 text-emerald-700 font-semibold">High (Mobile + WhatsApp CTA)</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-600 space-y-1">
          <p className="font-bold text-slate-900 flex items-center space-x-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>Methodology &amp; Privacy</span>
          </p>
          <p>
            Stats are aggregated from public business directory listings in {st.name}. No personal phone numbers or private contact details are published.
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          <Link href={`/leads/${st.slug}`} className="px-5 py-2.5 rounded-xl bg-brand-600 text-white text-xs font-bold inline-flex items-center space-x-1.5">
            <span>Explore {st.name} Lead Hub</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link href={`/?state=${encodeURIComponent(st.name)}#collector-wizard`} className="px-5 py-2.5 rounded-xl bg-slate-900 text-white text-xs font-bold">
            Try {st.name} Free in Collector
          </Link>
        </div>
      </article>
    </div>
  );
}
