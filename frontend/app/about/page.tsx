import type { Metadata } from "next";
import Link from "next/link";
import JsonLd from "@/components/JsonLd";
import { buildMetadata, breadcrumbSchema, SUPPORT_EMAIL } from "@/lib/seo";
import { MapPin, ShieldCheck, Sparkles, ArrowRight } from "lucide-react";

export const metadata: Metadata = buildMetadata({
  title: "About LeadHarvest India – B2B Lead Data Platform for Agencies",
  description:
    "Learn how LeadHarvest India helps web designers, SEO agencies, and B2B sales teams discover local businesses without websites across all 36 Indian states.",
  path: "/about",
});

export default function AboutPage() {
  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      <JsonLd data={breadcrumbSchema([{ name: "Home", path: "/" }, { name: "About", path: "/about" }])} />

      <div className="bg-white rounded-3xl border border-slate-200 p-8 sm:p-10 space-y-5 shadow-sm">
        <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-brand-50 text-brand-700 text-xs font-bold border border-brand-200">
          <Sparkles className="w-3.5 h-3.5" />
          <span>About LeadHarvest India</span>
        </span>
        <h1 className="text-3xl sm:text-4xl font-black text-slate-900">
          Built for Indian Web Designers, Marketers &amp; B2B Sales Teams
        </h1>
        <p className="text-base text-slate-600 leading-relaxed">
          LeadHarvest India started in Bhubaneswar, Odisha with a simple frustration: agencies and freelancers spend hours every week copying business listings from public business directories in India into spreadsheets, checking who already has a website, and removing duplicate phone numbers.
        </p>
        <p className="text-base text-slate-600 leading-relaxed">
          We built LeadHarvest India to automate that entire workflow into a calm, transparent, one-click experience. Select your target Indian states and cities, pick from 200+ B2B categories, apply Smart Filters like <strong>No Website Listed</strong> and <strong>Opportunity Score</strong>, skip your previous Excel lists automatically, and download a clean workbook ready for outreach.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4">
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-1.5">
            <h2 className="text-sm font-bold text-slate-900 flex items-center space-x-1.5">
              <ShieldCheck className="w-4 h-4 text-brand-600" />
              <span>Privacy &amp; Compliance First</span>
            </h2>
            <p className="text-xs text-slate-600">
              Your uploaded lead sheets and Known Records are strictly isolated to your account. We design for India&apos;s DPDP Act 2023 and never expose personal contact numbers on public pages.
            </p>
          </div>
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-1.5">
            <h2 className="text-sm font-bold text-slate-900 flex items-center space-x-1.5">
              <MapPin className="w-4 h-4 text-brand-600" />
              <span>Headquartered in Odisha, Serving All India</span>
            </h2>
            <p className="text-xs text-slate-600">
              Supporting all 28 states and 8 union territories across India. Questions? Reach us anytime at{" "}
              <a href={`mailto:${SUPPORT_EMAIL}`} className="text-brand-700 font-semibold underline">{SUPPORT_EMAIL}</a>.
            </p>
          </div>
        </div>

        <div className="pt-4">
          <Link href="/" className="inline-flex items-center space-x-2 px-6 py-3 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-sm shadow-sm">
            <span>Try 4 Free Runs Now</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}
