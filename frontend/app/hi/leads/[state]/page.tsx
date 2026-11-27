import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { SITE_URL, buildMetadata } from "@/lib/seo";
import { resolveStateHub } from "@/lib/state-seo-data";
import { ArrowRight, MapPin } from "lucide-react";

const HI_STATES = ["uttar-pradesh", "madhya-pradesh", "bihar", "rajasthan", "delhi-nct"];

export function generateStaticParams() {
  return HI_STATES.map((state) => ({ state }));
}

export function generateMetadata({ params }: { params: { state: string } }): Metadata {
  const st = resolveStateHub(params.state);
  if (!st || !HI_STATES.includes(st.slug)) return {};
  return {
    ...buildMetadata({
      title: `${st.name} बिज़नेस लीड्स डेटा (बिना वेबसाइट वाले क्लाइंट) | LeadHarvest`,
      description: `${st.name} के सभी शहरों के बिज़नेस लीड्स और बिना वेबसाइट वाले क्लिनिक, दुकान व रेस्टोरेंट की Excel लिस्ट फ्री में शुरू करें।`,
      path: `/hi/leads/${st.slug}`,
    }),
    alternates: {
      canonical: `${SITE_URL}/hi/leads/${st.slug}`,
      languages: {
        "en-IN": `${SITE_URL}/leads/${st.slug}`,
        "hi-IN": `${SITE_URL}/hi/leads/${st.slug}`,
        "x-default": `${SITE_URL}/leads/${st.slug}`,
      },
    },
  };
}

export default function HindiStatePilotPage({ params }: { params: { state: string } }) {
  const st = resolveStateHub(params.state);
  if (!st || !HI_STATES.includes(st.slug)) notFound();

  return (
    <div lang="hi-IN" className="max-w-4xl mx-auto space-y-6 pb-20">
      <div className="bg-white rounded-3xl border border-slate-200 p-8 space-y-5 shadow-xs">
        <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 text-xs font-bold border border-emerald-200">
          <MapPin className="w-3.5 h-3.5" />
          <span>हिंदी पायलट (Human-Reviewed) · {st.name}</span>
        </span>
        <h1 className="text-3xl font-black text-slate-900">
          {st.name} में बिज़नेस लीड्स और बिना वेबसाइट वाले क्लाइंट खोजें
        </h1>
        <p className="text-sm text-slate-700 leading-relaxed">
          यदि आप {st.name} से विज़िट कर रहे हैं, तो आपका होम स्टेट डेटा बिल्कुल फ्री है। वेब डिज़ाइनर्स और डिजिटल मार्केटिंग एजेंसियां {st.name} के लगभग {st.noWebsitePct}% बिना वेबसाइट वाले बिज़नेस की क्लीन Excel शीट तुरंत डाउनलोड कर सकती हैं।
        </p>
        <div className="flex flex-wrap gap-3">
          <Link href={`/?state=${encodeURIComponent(st.name)}#collector-wizard`} className="px-5 py-2.5 rounded-xl bg-brand-600 text-white text-xs font-bold inline-flex items-center space-x-1.5">
            <span>{st.name} लीड्स फ्री में शुरू करें</span>
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
