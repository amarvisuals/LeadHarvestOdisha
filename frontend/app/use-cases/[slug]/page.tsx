import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import JsonLd from "@/components/JsonLd";
import { USE_CASES_DATA } from "@/lib/marketing-data";
import { buildMetadata, breadcrumbSchema, faqSchema } from "@/lib/seo";
import { ArrowRight, Briefcase, CheckCircle2 } from "lucide-react";

export function generateStaticParams() {
  return USE_CASES_DATA.map((u) => ({ slug: u.slug }));
}

export function generateMetadata({ params }: { params: { slug: string } }): Metadata {
  const uc = USE_CASES_DATA.find((u) => u.slug === params.slug);
  if (!uc) return {};
  return buildMetadata({
    title: uc.metaTitle,
    description: uc.metaDescription,
    path: `/use-cases/${uc.slug}`,
  });
}

export default function UseCaseDetailPage({ params }: { params: { slug: string } }) {
  const uc = USE_CASES_DATA.find((u) => u.slug === params.slug);
  if (!uc) notFound();

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      <JsonLd
        data={[
          breadcrumbSchema([
            { name: "Home", path: "/" },
            { name: uc.title, path: `/use-cases/${uc.slug}` },
          ]),
          faqSchema(uc.faqs),
        ]}
      />

      <nav aria-label="Breadcrumb" className="text-xs text-slate-500 flex items-center space-x-2">
        <Link href="/" className="hover:text-brand-700">Home</Link>
        <span>/</span>
        <span>Use Cases</span>
        <span>/</span>
        <span className="font-semibold text-slate-800">{uc.title}</span>
      </nav>

      <article className="bg-white rounded-3xl border border-slate-200 p-8 sm:p-10 space-y-6 shadow-sm">
        <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-amber-50 text-amber-800 text-xs font-bold border border-amber-200">
          <Briefcase className="w-3.5 h-3.5" />
          <span>{uc.title}</span>
        </span>
        <h1 className="text-3xl sm:text-4xl font-black text-slate-900">{uc.h1}</h1>
        <p className="text-base text-slate-600 leading-relaxed">{uc.summary}</p>

        <div className="p-4 rounded-2xl bg-brand-50 border border-brand-200 text-xs">
          <span className="font-bold uppercase text-brand-800 block mb-1">Recommended Pitch Preset</span>
          <p className="text-sm font-extrabold text-slate-900">{uc.recommendedPreset}</p>
        </div>

        <section className="space-y-3">
          <h2 className="text-xl font-extrabold text-slate-900">Step-by-Step Outbound Workflow</h2>
          <ol className="space-y-2 text-sm text-slate-700">
            {uc.workflowSteps.map((step, idx) => (
              <li key={idx} className="flex items-start space-x-2.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <span>{step}</span>
              </li>
            ))}
          </ol>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-extrabold text-slate-900">Why It Works</h2>
          {uc.bodyParagraphs.map((p, idx) => (
            <p key={idx} className="text-sm text-slate-700 leading-relaxed">{p}</p>
          ))}
        </section>

        <div className="pt-4 flex flex-wrap gap-3">
          <Link href="/" className="px-6 py-3 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs inline-flex items-center space-x-1.5">
            <span>Start 4 Free Runs</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link href="/pricing" className="px-5 py-3 rounded-xl bg-slate-100 text-slate-800 font-bold text-xs">
            Compare Plans (₹499+)
          </Link>
        </div>
      </article>
    </div>
  );
}
