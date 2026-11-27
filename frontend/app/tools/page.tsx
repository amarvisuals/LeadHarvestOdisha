import type { Metadata } from "next";
import Link from "next/link";
import { buildMetadata } from "@/lib/seo";
import { Calculator, MessageSquare, Link2, FileSpreadsheet, ArrowRight } from "lucide-react";

export const metadata: Metadata = buildMetadata({
  title: "Free B2B Agency & Lead Tools | LeadHarvest India",
  description:
    "Free tools for Indian web designers and agencies: Website Pitch Generator, Agency ROI Calculator, WhatsApp Link Generator, and Excel Lead Tracker Templates.",
  path: "/tools",
});

const TOOLS = [
  {
    slug: "pitch-generator",
    title: "Website Pitch Email & WhatsApp Generator",
    desc: "Generate ready-to-send English and Hindi-friendly cold pitches tailored to clinics, restaurants, real estate, and salons.",
    icon: MessageSquare,
  },
  {
    slug: "agency-roi-calculator",
    title: "Lead Cost & Agency ROI Calculator",
    desc: "Calculate your cost per client and expected monthly revenue based on lead volume, conversion rate, and project price.",
    icon: Calculator,
  },
  {
    slug: "whatsapp-link-generator",
    title: "WhatsApp Link (wa.me) Generator",
    desc: "Build clean +91 WhatsApp click-to-chat links with prefilled outreach messages in seconds.",
    icon: Link2,
  },
  {
    slug: "excel-lead-templates",
    title: "Free Excel Lead & Outreach Tracker Templates",
    desc: "Download structured CSV/Excel templates for B2B lead tracking, follow-ups, and proposal checklists.",
    icon: FileSpreadsheet,
  },
];

export default function ToolsIndexPage() {
  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-16">
      <div className="text-center space-y-2 pt-2">
        <h1 className="text-3xl sm:text-4xl font-black text-slate-900">Free B2B Outreach &amp; Agency Tools</h1>
        <p className="text-sm text-slate-600 max-w-xl mx-auto">
          Practical, free tools built for Indian web designers, digital marketers, and B2B sales teams.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {TOOLS.map((t) => {
          const Icon = t.icon;
          return (
            <Link
              key={t.slug}
              href={`/tools/${t.slug}`}
              className="bg-white rounded-2xl border border-slate-200 p-6 hover:border-brand-400 hover:shadow-md transition-all flex flex-col justify-between space-y-4"
            >
              <div className="space-y-2">
                <div className="w-10 h-10 rounded-xl bg-brand-50 text-brand-700 flex items-center justify-center">
                  <Icon className="w-5 h-5" />
                </div>
                <h2 className="text-lg font-bold text-slate-900">{t.title}</h2>
                <p className="text-xs text-slate-600 leading-relaxed">{t.desc}</p>
              </div>
              <span className="text-xs font-bold text-brand-700 inline-flex items-center space-x-1">
                <span>Open Tool</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
