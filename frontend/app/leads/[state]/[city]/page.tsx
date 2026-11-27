import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import JsonLd from "@/components/JsonLd";
import { buildMetadata, breadcrumbSchema, faqSchema } from "@/lib/seo";
import { resolveCityOrCategoryInState } from "@/lib/state-seo-data";
import { MapPin, ArrowRight } from "lucide-react";

export const revalidate = 86400;

export function generateMetadata({
  params,
}: {
  params: { state: string; city: string };
}): Metadata {
  const data = resolveCityOrCategoryInState(params.state, params.city);
  if (!data) return {};

  if (data.kind === "city") {
    return buildMetadata({
      title: `Business Leads in ${data.city.name}, ${data.state.name} | LeadHarvest`,
      description: `Find ${data.approxCount}+ B2B businesses in ${data.city.name}, ${data.state.name}. ~${data.noWebsitePct}% have no website listed.`,
      path: `/leads/${data.state.slug}/${data.citySlug}`,
      noindex: !data.isIndexable,
    });
  }

  return buildMetadata({
    title: `${data.category.name} Leads in ${data.state.name} | LeadHarvest`,
    description: `Find ${data.approxCount}+ ${data.category.name.toLowerCase()} across ${data.state.name}. ~${data.noWebsitePct}% have no website listed.`,
    path: `/leads/${data.state.slug}/${data.category.slug}`,
    noindex: !data.isIndexable,
  });
}

export default function StateCityOrCategoryPage({
  params,
}: {
  params: { state: string; city: string };
}) {
  const data = resolveCityOrCategoryInState(params.state, params.city);
  if (!data) notFound();

  const st = data.state;
  const label = data.kind === "city" ? data.city.name : data.category.name;
  const path =
    data.kind === "city"
      ? `/leads/${st.slug}/${data.citySlug}`
      : `/leads/${st.slug}/${data.category.slug}`;

  const prefillHref =
    data.kind === "city"
      ? `/?state=${encodeURIComponent(st.name)}&city=${encodeURIComponent(data.city.name)}#collector-wizard`
      : `/?state=${encodeURIComponent(st.name)}&category=${encodeURIComponent(data.category.name)}#collector-wizard`;

  const faqs = [
    {
      question: `How many ${label} prospects are indexed in ${st.name}?`,
      answer: `Our public directory index estimates ${data.approxCount}+ active listings, with roughly ${data.noWebsitePct}% having no dedicated website.`,
    },
    {
      question: `Can I try ${st.name} leads for free?`,
      answer: `Yes. Under our Home State Free model, visitors from ${st.name} get free access to ${st.name} data. Out-of-state users can unlock ${st.name} via Starter or Pro.`,
    },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      <JsonLd
        data={[
          breadcrumbSchema([
            { name: "Home", path: "/" },
            { name: "India", path: "/india" },
            { name: st.name, path: `/leads/${st.slug}` },
            { name: label, path },
          ]),
          faqSchema(faqs),
        ]}
      />

      <nav aria-label="Breadcrumb" className="text-xs text-slate-500 flex items-center space-x-2">
        <Link href="/" className="hover:text-brand-700">Home</Link>
        <span>/</span>
        <Link href="/india" className="hover:text-brand-700">India</Link>
        <span>/</span>
        <Link href={`/leads/${st.slug}`} className="hover:text-brand-700">{st.name}</Link>
        <span>/</span>
        <span className="font-semibold text-slate-800">{label}</span>
      </nav>

      <article className="bg-white rounded-3xl border border-slate-200 p-8 space-y-6 shadow-xs">
        <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-brand-50 text-brand-700 text-xs font-bold border border-brand-200">
          <MapPin className="w-3.5 h-3.5" />
          <span>{label} · {st.name}</span>
        </span>

        <h1 className="text-3xl font-black text-slate-900">
          {data.kind === "city"
            ? `B2B Business Leads in ${data.city.name}, ${st.name}`
            : `${data.category.name} Leads in ${st.name}`}
        </h1>

        <p className="text-sm text-slate-700 leading-relaxed">
          {data.kind === "city"
            ? `Explore verified local businesses across ${data.city.name} (${data.city.district} district, ${st.name}). Roughly ${data.noWebsitePct}% of local listings have no dedicated website—making ${data.city.name} an ideal market for web designers, SEO freelancers, and B2B agencies.`
            : `Discover ${data.category.name.toLowerCase()} across ${st.cities.length} cities in ${st.name}. Approximately ${data.noWebsitePct}% lack a dedicated website, giving web agencies and SaaS teams an immediate outreach advantage.`}
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200">
            <span className="text-slate-400 font-semibold block">Estimated Listings</span>
            <strong className="text-2xl font-black text-slate-900">{data.approxCount}+</strong>
          </div>
          <div className="p-4 rounded-2xl bg-amber-50/70 border border-amber-200">
            <span className="text-amber-800 font-semibold block">No Website Listed</span>
            <strong className="text-2xl font-black text-amber-700">{data.noWebsitePct}%</strong>
          </div>
          <div className="p-4 rounded-2xl bg-emerald-50/70 border border-emerald-200">
            <span className="text-emerald-800 font-semibold block">Home State Access</span>
            <strong className="text-sm font-black text-emerald-800">Free if in {st.name}</strong>
          </div>
        </div>

        <Link
          href={prefillHref}
          className="inline-flex items-center space-x-2 px-5 py-3 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold"
        >
          <span>Collect {label} Leads in Excel</span>
          <ArrowRight className="w-4 h-4" />
        </Link>

        {/* Cross-links to city+category pages */}
        <div className="pt-4 border-t border-slate-100 space-y-2">
          <h2 className="text-sm font-black text-slate-900">
            {data.kind === "city"
              ? `Popular Categories in ${data.city.name}`
              : `Top Cities in ${st.name} for ${data.category.name}`}
          </h2>
          <div className="flex flex-wrap gap-1.5 text-xs">
            {data.kind === "city"
              ? st.topCategories.slice(0, 8).map((cat) => (
                  <Link
                    key={cat.id}
                    href={`/leads/${st.slug}/${data.citySlug}/${cat.slug}`}
                    className="px-3 py-1.5 rounded-xl bg-slate-50 hover:bg-brand-50 border border-slate-200 font-semibold text-slate-700"
                  >
                    {cat.name} in {data.city.name}
                  </Link>
                ))
              : st.cities.slice(0, 8).map((c) => (
                  <Link
                    key={c.id}
                    href={`/leads/${st.slug}/${c.id}/${data.category.slug}`}
                    className="px-3 py-1.5 rounded-xl bg-slate-50 hover:bg-brand-50 border border-slate-200 font-semibold text-slate-700"
                  >
                    {data.category.name} in {c.name}
                  </Link>
                ))}
          </div>
        </div>
      </article>
    </div>
  );
}
