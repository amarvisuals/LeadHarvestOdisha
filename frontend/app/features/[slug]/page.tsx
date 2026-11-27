import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import JsonLd from "@/components/JsonLd";
import { FEATURES_DATA } from "@/lib/marketing-data";
import { buildMetadata, breadcrumbSchema, faqSchema } from "@/lib/seo";
import { ArrowRight, CheckCircle2, Sparkles } from "lucide-react";

export function generateStaticParams() {
  return FEATURES_DATA.map((f) => ({ slug: f.slug }));
}

export function generateMetadata({ params }: { params: { slug: string } }): Metadata {
  const feat = FEATURES_DATA.find((f) => f.slug === params.slug);
  if (!feat) return {};
  return buildMetadata({
    title: feat.metaTitle,
    description: feat.metaDescription,
    path: `/features/${feat.slug}`,
  });
}

export default function FeatureDetailPage({ params }: { params: { slug: string } }) {
  const feat = FEATURES_DATA.find((f) => f.slug === params.slug);
  if (!feat) notFound();

  const otherFeatures = FEATURES_DATA.filter((f) => f.slug !== feat.slug);

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      <JsonLd
        data={[
          breadcrumbSchema([
            { name: "Home", path: "/" },
            { name: feat.title, path: `/features/${feat.slug}` },
          ]),
          faqSchema(feat.faqs),
        ]}
      />

      <nav aria-label="Breadcrumb" className="text-xs text-slate-500 flex items-center space-x-2">
        <Link href="/" className="hover:text-brand-700">Home</Link>
        <span>/</span>
        <span>Features</span>
        <span>/</span>
        <span className="font-semibold text-slate-800">{feat.title}</span>
      </nav>

      <article className="bg-white rounded-3xl border border-slate-200 p-8 sm:p-10 space-y-6 shadow-sm">
        <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-brand-50 text-brand-700 text-xs font-bold border border-brand-200">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Feature Spotlight</span>
        </span>
        <h1 className="text-3xl sm:text-4xl font-black text-slate-900 leading-tight">{feat.h1}</h1>
        <p className="text-base text-slate-600 leading-relaxed bg-slate-50 p-4 rounded-2xl border border-slate-200">
          {feat.summary}
        </p>

        <div className="space-y-6 pt-2">
          {feat.sections.map((sec) => (
            <section key={sec.heading} className="space-y-2.5">
              <h2 className="text-xl font-extrabold text-slate-900">{sec.heading}</h2>
              {sec.body.map((p, idx) => (
                <p key={idx} className="text-sm text-slate-700 leading-relaxed">
                  {p}
                </p>
              ))}
            </section>
          ))}
        </div>

        {/* FAQ */}
        <section className="pt-6 border-t border-slate-100 space-y-4">
          <h2 className="text-xl font-extrabold text-slate-900">Frequently Asked Questions</h2>
          <div className="space-y-3">
            {feat.faqs.map((f) => (
              <div key={f.question} className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80">
                <h3 className="text-sm font-bold text-slate-900">{f.question}</h3>
                <p className="text-xs text-slate-600 mt-1 leading-relaxed">{f.answer}</p>
              </div>
            ))}
          </div>
        </section>

        {/* CTA */}
        <div className="p-6 rounded-2xl bg-gradient-to-r from-brand-700 to-teal-600 text-white flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <p className="font-black text-lg">Ready to try {feat.title}?</p>
            <p className="text-xs text-brand-100">Start with 4 free guest runs—no credit card required.</p>
          </div>
          <Link href="/" className="px-5 py-3 bg-white text-brand-900 font-bold text-xs rounded-xl inline-flex items-center space-x-1.5 shrink-0">
            <span>Start 4 Free Runs</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </article>

      {/* Related Features */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-3">
        <h2 className="text-sm font-bold text-slate-900">Explore More Features</h2>
        <div className="flex flex-wrap gap-2">
          {otherFeatures.map((o) => (
            <Link key={o.slug} href={`/features/${o.slug}`} className="px-3 py-1.5 rounded-xl bg-slate-50 hover:bg-brand-50 border border-slate-200 text-xs font-semibold text-slate-700 inline-flex items-center space-x-1">
              <CheckCircle2 className="w-3.5 h-3.5 text-brand-600" />
              <span>{o.title}</span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
