import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { SITE_URL, buildMetadata } from "@/lib/seo";
import { resolveStateHub } from "@/lib/state-seo-data";
import { ArrowRight, MapPin } from "lucide-react";

export function generateStaticParams() {
  return [{ state: "odisha" }];
}

export function generateMetadata({ params }: { params: { state: string } }): Metadata {
  const st = resolveStateHub(params.state);
  if (!st || st.slug !== "odisha") return {};
  return {
    ...buildMetadata({
      title: `ଓଡ଼ିଶା ବିଜନେସ୍ ଲିଡ୍ସ ଡାଟା (Odisha Business Leads) | LeadHarvest`,
      description: `ଓଡ଼ିଶାର ସମସ୍ତ ଜିଲ୍ଲା ଓ ସହରର ବିଜନେସ୍ ଲିଡ୍ସ ଏବଂ ୱେବସାଇଟ୍ ନଥିବା ଦୋକାନ/କ୍ଲିନିକ୍ ତାଲିକା ମାଗଣାରେ ପାଆନ୍ତୁ।`,
      path: `/or/leads/${st.slug}`,
    }),
    alternates: {
      canonical: `${SITE_URL}/or/leads/${st.slug}`,
      languages: {
        "en-IN": `${SITE_URL}/leads/${st.slug}`,
        "or-IN": `${SITE_URL}/or/leads/${st.slug}`,
        "x-default": `${SITE_URL}/leads/${st.slug}`,
      },
    },
  };
}

export default function OdiaStatePilotPage({ params }: { params: { state: string } }) {
  const st = resolveStateHub(params.state);
  if (!st || st.slug !== "odisha") notFound();

  return (
    <div lang="or-IN" className="max-w-4xl mx-auto space-y-6 pb-20">
      <div className="bg-white rounded-3xl border border-slate-200 p-8 space-y-5 shadow-xs">
        <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 text-xs font-bold border border-emerald-200">
          <MapPin className="w-3.5 h-3.5" />
          <span>ଓଡ଼ିଆ ପାଇଲଟ୍ (Human-Reviewed) · {st.name}</span>
        </span>
        <h1 className="text-3xl font-black text-slate-900">
          ଓଡ଼ିଶାର ବିଜନେସ୍ ଲିଡ୍ସ ଏବଂ ୱେବସାଇଟ୍ ନଥିବା ଗ୍ରାହକ ଖୋଜନ୍ତୁ
        </h1>
        <p className="text-sm text-slate-700 leading-relaxed">
          ଯଦି ଆପଣ ଓଡ଼ିଶାରୁ ଭିଜିଟ୍ କରୁଛନ୍ତି, ତେବେ ଓଡ଼ିଶାର ସମସ୍ତ ସହର (ଭୁବନେଶ୍ୱର, କଟକ, ରାଉରକେଲା, ପୁରୀ, ସମ୍ବଲପୁର) ପାଇଁ ବିଜନେସ୍ ଲିଡ୍ସ ଡାଟା ସମ୍ପୂର୍ଣ୍ଣ ମାଗଣା। ୱେବସାଇଟ୍ ନଥିବା ଦୋକାନ, ଡାକ୍ତରଖାନା ଓ ରେଷ୍ଟୁରାଣ୍ଟ୍ ତାଲିକା Excel ରେ ଡାଉନଲୋଡ୍ କରନ୍ତୁ।
        </p>
        <div className="flex flex-wrap gap-3">
          <Link href="/?state=Odisha#collector-wizard" className="px-5 py-2.5 rounded-xl bg-brand-600 text-white text-xs font-bold inline-flex items-center space-x-1.5">
            <span>ମାଗଣାରେ ଓଡ଼ିଶା ଲିଡ୍ସ ଆରମ୍ଭ କରନ୍ତୁ</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link href={`/leads/${st.slug}`} className="px-5 py-2.5 rounded-xl bg-slate-100 text-slate-800 text-xs font-bold">
            View in English
          </Link>
        </div>
      </div>
    </div>
  );
}
