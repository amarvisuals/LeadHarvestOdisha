"use client";

import React, { useState } from "react";
import { Copy, Check, Download } from "lucide-react";
import { apiFetch } from "@/lib/api";

export default function FreeToolsInteractive({ slug }: { slug: string }) {
  const [copied, setCopied] = useState(false);

  // Tool 1: Pitch Generator
  const [bizCategory, setBizCategory] = useState("Dental Clinic");
  const [city, setCity] = useState("Cuttack");
  const [lang, setLang] = useState<"en" | "hi">("en");
  const [yourName, setYourName] = useState("Amar");

  // Tool 2: ROI Calculator
  const [leadsPerMonth, setLeadsPerMonth] = useState(300);
  const [convPct, setConvPct] = useState(2);
  const [projectPrice, setProjectPrice] = useState(18000);
  const [planCost, setPlanCost] = useState(1499);

  // Tool 3: WhatsApp Link Generator
  const [waPhone, setWaPhone] = useState("9861012345");
  const [waMsg, setWaMsg] = useState("Namaste! I noticed your business in Cuttack has great reviews but no website yet. Can I share a quick 1-page demo?");

  // Tool 4: Email-gated Template Download
  const [leadEmail, setLeadEmail] = useState("");
  const [unlockedTemplate, setUnlockedTemplate] = useState(false);

  const copyText = (txt: string) => {
    navigator.clipboard.writeText(txt);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };

  if (slug === "pitch-generator") {
    const script =
      lang === "en"
        ? `Subject: Quick idea for your ${bizCategory} in ${city}\n\nNamaste,\n\nI was looking at top-rated ${bizCategory} listings in ${city} and noticed your business has strong customer reviews, but no dedicated website link yet.\n\nMost customers searching Google in ${city} check a clinic/business website before calling. I put together a simple, mobile-friendly demo layout tailored for ${bizCategory} owners.\n\nWould you like me to share the demo link on WhatsApp?\n\nBest regards,\n${yourName}`
        : `Namaste ji,\n\nMain ${yourName} bol raha hoon. Maine ${city} mein aapke ${bizCategory} ki acchi ratings dekhi, lekin abhi aapki apni website link nahi dikhi.\n\nAajkal log Google par search karke website dekhne ke baad call karte hain. Maine aapke business ke liye ek simple mobile-friendly demo banaya hai. Kya main WhatsApp par link bhej sakta hoon?\n\nDhanyawad,\n${yourName}`;

    return (
      <div className="space-y-4 bg-slate-50 p-5 rounded-2xl border border-slate-200 text-xs">
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
          <input value={bizCategory} onChange={(e) => setBizCategory(e.target.value)} placeholder="Business Category" className="px-3 py-2 bg-white border rounded-xl" />
          <input value={city} onChange={(e) => setCity(e.target.value)} placeholder="City" className="px-3 py-2 bg-white border rounded-xl" />
          <input value={yourName} onChange={(e) => setYourName(e.target.value)} placeholder="Your Name" className="px-3 py-2 bg-white border rounded-xl" />
          <select value={lang} onChange={(e) => setLang(e.target.value as "en" | "hi")} className="px-3 py-2 bg-white border rounded-xl">
            <option value="en">English (Formal)</option>
            <option value="hi">Hinglish (WhatsApp Friendly)</option>
          </select>
        </div>
        <textarea readOnly rows={8} value={script} className="w-full p-4 bg-white border border-slate-200 rounded-xl font-mono text-xs" />
        <button onClick={() => copyText(script)} className="px-4 py-2 bg-brand-600 text-white font-bold rounded-xl inline-flex items-center space-x-1.5">
          {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
          <span>{copied ? "Copied!" : "Copy Pitch"}</span>
        </button>
      </div>
    );
  }

  if (slug === "agency-roi-calculator") {
    const clients = Math.round((leadsPerMonth * convPct) / 100);
    const revenue = clients * projectPrice;
    const costPerLead = (planCost / Math.max(leadsPerMonth, 1)).toFixed(2);
    const roiPct = planCost > 0 ? Math.round(((revenue - planCost) / planCost) * 100) : 0;

    return (
      <div className="space-y-5 bg-slate-50 p-5 rounded-2xl border border-slate-200 text-xs">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <label className="font-semibold">Leads / Month
            <input type="number" value={leadsPerMonth} onChange={(e) => setLeadsPerMonth(Number(e.target.value))} className="w-full mt-1 px-3 py-2 bg-white border rounded-xl" />
          </label>
          <label className="font-semibold">Conversion (%)
            <input type="number" step="0.5" value={convPct} onChange={(e) => setConvPct(Number(e.target.value))} className="w-full mt-1 px-3 py-2 bg-white border rounded-xl" />
          </label>
          <label className="font-semibold">Avg Deal (₹)
            <input type="number" value={projectPrice} onChange={(e) => setProjectPrice(Number(e.target.value))} className="w-full mt-1 px-3 py-2 bg-white border rounded-xl" />
          </label>
          <label className="font-semibold">Tool Cost (₹)
            <input type="number" value={planCost} onChange={(e) => setPlanCost(Number(e.target.value))} className="w-full mt-1 px-3 py-2 bg-white border rounded-xl" />
          </label>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-white p-4 rounded-xl border"><span className="text-slate-400 block">Est. New Clients</span><strong className="text-xl text-slate-900">{clients}</strong></div>
          <div className="bg-white p-4 rounded-xl border"><span className="text-slate-400 block">Est. Revenue</span><strong className="text-xl text-emerald-700">₹{revenue.toLocaleString()}</strong></div>
          <div className="bg-white p-4 rounded-xl border"><span className="text-slate-400 block">Cost / Lead</span><strong className="text-xl text-slate-900">₹{costPerLead}</strong></div>
          <div className="bg-white p-4 rounded-xl border"><span className="text-slate-400 block">Projected ROI</span><strong className="text-xl text-brand-700">{roiPct}%</strong></div>
        </div>
      </div>
    );
  }

  if (slug === "whatsapp-link-generator") {
    const cleanDigits = waPhone.replace(/\D/g, "").slice(-10);
    const waUrl = `https://wa.me/91${cleanDigits}?text=${encodeURIComponent(waMsg)}`;
    return (
      <div className="space-y-4 bg-slate-50 p-5 rounded-2xl border border-slate-200 text-xs">
        <input value={waPhone} onChange={(e) => setWaPhone(e.target.value)} placeholder="10-digit Indian mobile (e.g. 9861012345)" className="w-full px-3 py-2 bg-white border rounded-xl" />
        <textarea rows={3} value={waMsg} onChange={(e) => setWaMsg(e.target.value)} className="w-full p-3 bg-white border rounded-xl" />
        <div className="p-3 bg-white border rounded-xl font-mono break-all text-brand-700">{waUrl}</div>
        <div className="flex items-center space-x-2">
          <button onClick={() => copyText(waUrl)} className="px-4 py-2 bg-brand-600 text-white font-bold rounded-xl inline-flex items-center space-x-1.5">
            {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
            <span>{copied ? "Copied!" : "Copy wa.me Link"}</span>
          </button>
          <a href={waUrl} target="_blank" rel="noopener noreferrer" className="px-4 py-2 bg-emerald-600 text-white font-bold rounded-xl">
            Test in WhatsApp
          </a>
        </div>
      </div>
    );
  }

  // Tool 4: Excel Lead Templates (Email-gated lead magnet)
  const downloadTemplateCsv = (templateName: string, content: string) => {
    const blob = new Blob([content], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${templateName}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4 bg-slate-50 p-5 rounded-2xl border border-slate-200 text-xs">
      {!unlockedTemplate ? (
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            if (!leadEmail.includes("@")) return;
            await apiFetch("/api/analytics/track", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                type: "event",
                event_name: "lead_magnet_unlock",
                properties: { email: leadEmail, tool: "excel-lead-templates" },
              }),
            });
            setUnlockedTemplate(true);
          }}
          className="flex flex-col sm:flex-row gap-2"
        >
          <input
            type="email"
            required
            value={leadEmail}
            onChange={(e) => setLeadEmail(e.target.value)}
            placeholder="Enter your email to unlock all 3 templates..."
            className="flex-1 px-3.5 py-2.5 bg-white border border-slate-200 rounded-xl"
          />
          <button type="submit" className="px-5 py-2.5 bg-brand-600 text-white font-bold rounded-xl">
            Unlock Free Templates
          </button>
        </form>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <button
            onClick={() => downloadTemplateCsv("LeadHarvest_Lead_Tracker", "Business Name,Category,Phone,City,Has Website,Opportunity Score,Status,Notes\n")}
            className="p-3 bg-white border border-emerald-200 rounded-xl font-bold text-emerald-700 flex items-center justify-center space-x-1.5"
          >
            <Download className="w-4 h-4" />
            <span>1. Lead Tracker.csv</span>
          </button>
          <button
            onClick={() => downloadTemplateCsv("LeadHarvest_Outreach_Tracker", "Business Name,WhatsApp Sent Date,Follow-up 1,Follow-up 2,Reply Status,Deal Value INR\n")}
            className="p-3 bg-white border border-emerald-200 rounded-xl font-bold text-emerald-700 flex items-center justify-center space-x-1.5"
          >
            <Download className="w-4 h-4" />
            <span>2. Outreach Tracker.csv</span>
          </button>
          <button
            onClick={() => downloadTemplateCsv("LeadHarvest_Proposal_Checklist", "Step,Item,Completed,Notes\n1,Verify business has no website,Yes,\n2,Prepare 1-page demo mockup,No,\n")}
            className="p-3 bg-white border border-emerald-200 rounded-xl font-bold text-emerald-700 flex items-center justify-center space-x-1.5"
          >
            <Download className="w-4 h-4" />
            <span>3. Proposal Checklist.csv</span>
          </button>
        </div>
      )}
    </div>
  );
}
