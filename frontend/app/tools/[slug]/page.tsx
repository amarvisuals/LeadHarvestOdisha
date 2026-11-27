import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import JsonLd from "@/components/JsonLd";
import FreeToolsInteractive from "@/components/FreeToolsInteractive";
import { buildMetadata, breadcrumbSchema, faqSchema } from "@/lib/seo";
import { ArrowRight } from "lucide-react";

const TOOL_DETAILS: Record<string, { title: string; metaTitle: string; metaDesc: string; h1: string; intro: string }> = {
  "pitch-generator": {
    title: "Pitch & WhatsApp Generator",
    metaTitle: "Website Pitch Email & WhatsApp Generator India | LeadHarvest",
    metaDesc: "Generate personalised English & Hinglish cold outreach pitches for local Indian businesses without a website.",
    h1: "Website Pitch Email & WhatsApp Message Generator",
    intro: "Create high-reply outreach messages tailored to Indian business owners in your target category and city.",
  },
  "agency-roi-calculator": {
    title: "Agency ROI Calculator",
    metaTitle: "Lead Cost & Web Agency ROI Calculator (INR) | LeadHarvest India",
    metaDesc: "Calculate how many website clients and INR revenue your agency can generate from monthly business leads.",
    h1: "Lead Cost & Agency ROI Calculator",
    intro: "Estimate your cost per lead, expected client conversions, and monthly agency ROI before launching an outbound campaign.",
  },
  "whatsapp-link-generator": {
    title: "WhatsApp Link Generator",
    metaTitle: "Free WhatsApp wa.me Link Generator (+91 India) | LeadHarvest",
    metaDesc: "Create instant click-to-chat WhatsApp links with prefilled outreach messages for +91 Indian mobile numbers.",
    h1: "Free WhatsApp (wa.me) Link Generator for India",
    intro: "Convert any 10-digit Indian mobile number and pitch message into a clickable WhatsApp outreach link.",
  },
  "excel-lead-templates": {
    title: "Free Excel Lead Templates",
    metaTitle: "Free Excel Lead Tracker & Outreach Templates | LeadHarvest India",
    metaDesc: "Download free B2B lead tracker, WhatsApp follow-up tracker, and website proposal checklist spreadsheets.",
    h1: "Free Downloadable Excel Lead & Outreach Templates",
    intro: "Organise your sales pipeline with three ready-to-use spreadsheet templates designed for Indian agencies.",
  },
};

export function generateStaticParams() {
  return Object.keys(TOOL_DETAILS).map((slug) => ({ slug }));
}

export function generateMetadata({ params }: { params: { slug: string } }): Metadata {
  const t = TOOL_DETAILS[params.slug];
  if (!t) return {};
  return buildMetadata({ title: t.metaTitle, description: t.metaDesc, path: `/tools/${params.slug}` });
}

export default function ToolDetailPage({ params }: { params: { slug: string } }) {
  const tool = TOOL_DETAILS[params.slug];
  if (!tool) notFound();

  const faqs = [
    {
      question: `Is the ${tool.title} free to use?`,
      answer: "Yes, all 4 tools on LeadHarvest India are 100% free with no login required.",
    },
    {
      question: "Where can I get leads to use with this tool?",
      answer: "Use LeadHarvest India's main collector to find businesses without a website across India (4 free runs included).",
    },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      <JsonLd
        data={[
          breadcrumbSchema([
            { name: "Home", path: "/" },
            { name: "Tools", path: "/tools" },
            { name: tool.title, path: `/tools/${params.slug}` },
          ]),
          faqSchema(faqs),
        ]}
      />

      <div className="bg-white rounded-3xl border border-slate-200 p-8 space-y-6 shadow-sm">
        <h1 className="text-3xl font-black text-slate-900">{tool.h1}</h1>
        <p className="text-sm text-slate-600">{tool.intro}</p>

        <FreeToolsInteractive slug={params.slug} />

        <div className="pt-4 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-slate-600">
            Want ready-to-contact leads with Opportunity Scores and WhatsApp links already built?
          </p>
          <Link href="/" className="px-5 py-2.5 bg-brand-600 text-white font-bold text-xs rounded-xl inline-flex items-center space-x-1.5 shrink-0">
            <span>Try 4 Free Runs</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}
