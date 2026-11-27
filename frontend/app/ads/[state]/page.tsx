import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { buildMetadata } from "@/lib/seo";
import { resolveStateHub } from "@/lib/state-seo-data";
import { ArrowRight, CheckCircle2, MapPin } from "lucide-react";

export function generateMetadata({ params }: { params: { state: string } }): Metadata {
  const st = resolveStateHub(params.state);
  if (!st) return {};
  return buildMetadata({
    title: `Get Business Leads in ${st.name} Free | LeadHarvest India`,
    description: `Instant B2B business leads in ${st.name} with No-Website filter and Excel export.`,
    path: `/ads/${st.slug}`,
    noindex: true,
  });
}

export default function StateAdsLandingPage({ params }: { params: { state: string } }) {
  const st = resolveStateHub(params.state);
  if (!st) notFound();

  const wizardUrl = `/?state=${encodeURIComponent(st.name)}&utm_source=google_ads&utm_campaign=${st.slug}#collector-wizard`;

  return (
    <div className="max-w-3xl mx-auto py-8 pb-20">
      <div className="bg-white rounded-3xl border border-slate-200 p-8 sm:p-10 space-y-6 shadow-sm">
        <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 text-xs font-bold border border-emerald-200">
          <MapPin className="w-3.5 h-3.5" />
          <span>{st.name} B2B Lead Engine</span>
        </span>
        <h1 className="text-3xl font-black text-slate-900">
          Find {st.approxBusinesses.toLocaleString()}+ Businesses Without a Website in {st.name}
        </h1>
        <p className="text-sm text-slate-600">
          Built for web designers, agencies, and B2B sales teams in {st.name}. Collect clean Excel sheets with 10-digit mobile numbers and WhatsApp links in minutes.
        </p>
        <ul className="space-y-2 text-xs text-slate-700">
          <li className="flex items-center space-x-2"><CheckCircle2 className="w-4 h-4 text-emerald-600" /><span>~{st.noWebsitePct}% of {st.name} businesses have no website listed</span></li>
          <li className="flex items-center space-x-2"><CheckCircle2 className="w-4 h-4 text-emerald-600" /><span>Covers {st.cities.length} cities including {st.cities.slice(0, 4).map((c) => c.name).join(", ")}</span></li>
          <li className="flex items-center space-x-2"><CheckCircle2 className="w-4 h-4 text-emerald-600" /><span>Automatic deduplication so you never pay for repeat leads</span></li>
        </ul>
        <div className="flex flex-wrap gap-3 pt-2">
          <Link href={wizardUrl} className="px-6 py-3 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold inline-flex items-center space-x-2">
            <span>Start Free in {st.name}</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link href="/contact?utm_source=google_ads" className="px-6 py-3 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold">
            Request Custom Website Quote
          </Link>
        </div>
      </div>
    </div>
  );
}
