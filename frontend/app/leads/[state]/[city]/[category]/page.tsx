import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import JsonLd from "@/components/JsonLd";
import { resolveLocalParams } from "@/lib/local-seo";
import { buildMetadata, breadcrumbSchema, faqSchema } from "@/lib/seo";
import { MapPin, ArrowRight, Globe, Star, ShieldCheck, CheckCircle2 } from "lucide-react";

export const revalidate = 86400; // ISR: regenerate daily

export function generateMetadata({
  params,
}: {
  params: { state: string; city: string; category: string };
}): Metadata {
  const data = resolveLocalParams(params.state, params.city, params.category);
  if (!data) return {};

  return buildMetadata({
    title: `${data.category} Leads in ${data.city}, ${data.state} | LeadHarvest`,
    description: `Find ${data.stats.approxCount}+ ${data.category.toLowerCase()} in ${data.city}, ${data.state}. ~${data.stats.noWebsitePct}% have no website listed. Export clean Excel leads.`,
    path: `/leads/${data.stateSlug}/${data.citySlug}/${data.categorySlug}`,
    noindex: !data.isIndexable,
  });
}

export default function LocalLeadsPage({
  params,
}: {
  params: { state: string; city: string; category: string };
}) {
  const data = resolveLocalParams(params.state, params.city, params.category);
  if (!data) notFound();

  const prefillHref = `/?state=${encodeURIComponent(data.state)}&city=${encodeURIComponent(data.city)}&category=${encodeURIComponent(data.category)}#collector-wizard`;

  const faqs = [
    {
      question: `How many ${data.category.toLowerCase()} listings are available in ${data.city}?`,
      answer: `Our directory index shows approximately ${data.stats.approxCount}+ ${data.category.toLowerCase()} across ${data.city} (${data.district} district, ${data.state}), with around ${data.stats.noWebsitePct}% lacking a dedicated website.`,
    },
    {
      question: "Are phone numbers shown publicly on this page?",
      answer: "No. To protect privacy, only aggregated statistics and partially masked samples are displayed publicly. Authenticated users can export clean Excel sheets inside the app.",
    },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      <JsonLd
        data={[
          breadcrumbSchema([
            { name: "Home", path: "/" },
            { name: `${data.city} ${data.category}`, path: `/leads/${data.stateSlug}/${data.citySlug}/${data.categorySlug}` },
          ]),
          faqSchema(faqs),
        ]}
      />

      <nav aria-label="Breadcrumb" className="text-xs text-slate-500 flex items-center space-x-2">
        <Link href="/" className="hover:text-brand-700">Home</Link>
        <span>/</span>
        <span>{data.state}</span>
        <span>/</span>
        <span>{data.city}</span>
        <span>/</span>
        <span className="font-semibold text-slate-800">{data.category}</span>
      </nav>

      <article className="bg-white rounded-3xl border border-slate-200 p-8 space-y-6 shadow-sm">
        <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-brand-50 text-brand-700 text-xs font-bold border border-brand-200">
          <MapPin className="w-3.5 h-3.5" />
          <span>{data.city}, {data.state}</span>
        </span>

        <h1 className="text-3xl sm:text-4xl font-black text-slate-900">
          {data.category} Business Leads in {data.city}, {data.state}
        </h1>

        <p className="text-sm text-slate-700 leading-relaxed">
          Looking to pitch websites, SEO, or B2B services to <strong>{data.category}</strong> in{" "}
          <strong>{data.city}</strong> ({data.district} district, {data.state})? Based on public business directory listings in India, roughly{" "}
          <strong>{data.stats.noWebsitePct}%</strong> of local {data.category.toLowerCase()} in {data.city} do not have a website listed—making them ideal prospects for web designers and digital agencies.
        </p>

        {/* Aggregated Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200">
            <span className="text-slate-400 font-semibold block">Estimated Listings</span>
            <strong className="text-2xl font-black text-slate-900">{data.stats.approxCount}+</strong>
          </div>
          <div className="p-4 rounded-2xl bg-amber-50/70 border border-amber-200">
            <span className="text-amber-800 font-semibold flex items-center space-x-1"><Globe className="w-3.5 h-3.5" /><span>No Website Listed</span></span>
            <strong className="text-2xl font-black text-amber-900">~{data.stats.noWebsitePct}%</strong>
          </div>
          <div className="p-4 rounded-2xl bg-brand-50/70 border border-brand-200">
            <span className="text-brand-800 font-semibold flex items-center space-x-1"><Star className="w-3.5 h-3.5" /><span>Avg Rating Band</span></span>
            <strong className="text-2xl font-black text-brand-900">{data.stats.avgRating} ★</strong>
          </div>
        </div>

        {/* Masked Sample Table (Zero Personal Contact Info) */}
        <div className="space-y-2">
          <h2 className="text-lg font-extrabold text-slate-900">Masked Sample Preview (No Contact Data Exposed)</h2>
          <div className="overflow-x-auto border border-slate-200 rounded-2xl">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase text-[10px]">
                <tr>
                  <th className="py-2.5 px-4">Business (Masked)</th>
                  <th className="py-2.5 px-4">Locality</th>
                  <th className="py-2.5 px-4">Has Website</th>
                  <th className="py-2.5 px-4">Rating</th>
                  <th className="py-2.5 px-4">Opportunity Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.maskedSamples.map((row, idx) => (
                  <tr key={idx}>
                    <td className="py-2.5 px-4 font-bold text-slate-800">{row.maskedName}</td>
                    <td className="py-2.5 px-4 text-slate-600">{row.locality}</td>
                    <td className="py-2.5 px-4">{row.hasWebsite}</td>
                    <td className="py-2.5 px-4">{row.rating}</td>
                    <td className="py-2.5 px-4 font-bold text-brand-700">{row.score}/100</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Who Should Use This */}
        <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-2 text-xs">
          <h2 className="text-sm font-bold text-slate-900 flex items-center space-x-1.5">
            <ShieldCheck className="w-4 h-4 text-brand-600" />
            <span>Who Should Use This {data.city} Lead List?</span>
          </h2>
          <ul className="space-y-1.5 text-slate-600">
            <li className="flex items-center space-x-2"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /><span>Web designers pitching custom sites to {data.category.toLowerCase()} with no website</span></li>
            <li className="flex items-center space-x-2"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /><span>Local SEO &amp; Google Ads freelancers targeting {data.city}</span></li>
            <li className="flex items-center space-x-2"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /><span>B2B software, POS &amp; service providers expanding in {data.state}</span></li>
          </ul>
        </div>

        {/* Pre-filled CTA */}
        <div className="p-6 rounded-2xl bg-gradient-to-r from-brand-700 to-teal-600 text-white flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <p className="font-black text-lg">Collect {data.category} in {data.city}</p>
            <p className="text-xs text-brand-100">Pre-fills the LeadHarvest collector with {data.city} &amp; {data.category}.</p>
          </div>
          <Link href={prefillHref} className="px-5 py-3 bg-white text-brand-900 font-bold text-xs rounded-xl inline-flex items-center space-x-1.5 shrink-0">
            <span>Pre-fill &amp; Start Free</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </article>

      {/* Related Cities & Categories */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
        <div className="bg-white rounded-2xl border border-slate-200 p-5 space-y-2">
          <h2 className="font-bold text-slate-900">More Cities in {data.state}</h2>
          <div className="flex flex-wrap gap-1.5">
            {data.relatedCities.map((c) => (
              <Link key={c.slug} href={`/leads/${data.stateSlug}/${c.slug}/${data.categorySlug}`} className="px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200 hover:border-brand-400">
                {c.name}
              </Link>
            ))}
          </div>
        </div>
        <div className="bg-white rounded-2xl border border-slate-200 p-5 space-y-2">
          <h2 className="font-bold text-slate-900">More Categories in {data.city}</h2>
          <div className="flex flex-wrap gap-1.5">
            {data.relatedCategories.map((cat) => (
              <Link key={cat.slug} href={`/leads/${data.stateSlug}/${data.citySlug}/${cat.slug}`} className="px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200 hover:border-brand-400">
                {cat.name}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
