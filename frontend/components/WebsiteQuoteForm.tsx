"use client";

import React, { useEffect, useState } from "react";
import { CheckCircle2, MessageCircle, Send, ShieldCheck } from "lucide-react";
import { apiFetch } from "@/lib/api";

export default function WebsiteQuoteForm() {
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [businessName, setBusinessName] = useState("");
  const [businessType, setBusinessType] = useState("");
  const [city, setCity] = useState("");
  const [budgetRange, setBudgetRange] = useState("Rs 10,000 - Rs 20,000");
  const [timeline, setTimeline] = useState("Within 2 weeks");
  const [website, setWebsite] = useState("");
  const [notes, setNotes] = useState("");
  const [consent, setConsent] = useState(false);

  const [utms, setUtms] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [submittedId, setSubmittedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const p = new URLSearchParams(window.location.search);
      setUtms({
        utm_source: p.get("utm_source") || "",
        utm_medium: p.get("utm_medium") || "",
        utm_campaign: p.get("utm_campaign") || "",
        utm_term: p.get("utm_term") || "",
        utm_content: p.get("utm_content") || "",
        landing_page: window.location.pathname,
      });
    }
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!consent) {
      setError("Please check the consent box so we can contact you.");
      return;
    }
    setSubmitting(true);
    try {
      const res = await apiFetch("/api/inbound/quote", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          phone,
          email: email || null,
          business_name: businessName || null,
          business_type: businessType,
          city,
          website: website || null,
          budget_range: budgetRange,
          timeline,
          notes: notes || null,
          consent,
          ...utms,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || "Could not submit request. Please check your details.");
      } else {
        setSubmittedId(data.lead_id);
      }
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleWhatsAppClick() {
    try {
      const res = await apiFetch("/api/inbound/whatsapp-click", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          page: typeof window !== "undefined" ? window.location.pathname : "/contact",
          business_type: businessType || undefined,
          city: city || undefined,
          utm_source: utms.utm_source || undefined,
          utm_medium: utms.utm_medium || undefined,
          utm_campaign: utms.utm_campaign || undefined,
        }),
      });
      if (res.ok) {
        const d = await res.json();
        window.open(d.whatsapp_url, "_blank", "noopener,noreferrer");
        return;
      }
    } catch {
      // Fallback
    }
    window.open("https://wa.me/919861000001?text=Hi%20Amar%2C%20I%20would%20like%20a%20website%20quote.", "_blank", "noopener,noreferrer");
  }

  if (submittedId) {
    return (
      <div className="p-6 rounded-2xl bg-emerald-50 border border-emerald-200 text-center space-y-3">
        <CheckCircle2 className="w-10 h-10 text-emerald-600 mx-auto" />
        <h3 className="text-lg font-black text-slate-900">Quote Request Received!</h3>
        <p className="text-xs text-slate-600">
          Reference ID: <span className="font-mono font-bold">{submittedId}</span>. Our web design team will contact you within 2 business hours.
        </p>
        <button
          onClick={handleWhatsAppClick}
          className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold"
        >
          <MessageCircle className="w-4 h-4" />
          <span>Chat on WhatsApp Now</span>
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-slate-100">
        <div>
          <h2 className="text-lg font-black text-slate-900">Get a Free Website Quote</h2>
          <p className="text-xs text-slate-500">Custom, mobile-ready business websites built in 5–10 days.</p>
        </div>
        <button
          type="button"
          onClick={handleWhatsAppClick}
          className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-xs"
        >
          <MessageCircle className="w-4 h-4" />
          <span>WhatsApp Us Directly</span>
        </button>
      </div>

      {error && (
        <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 font-semibold">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
        <div>
          <label className="block font-semibold text-slate-700 mb-1">Your Name *</label>
          <input required value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Dr. Ananya Mishra" className="w-full px-3 py-2 rounded-xl border border-slate-300" />
        </div>
        <div>
          <label className="block font-semibold text-slate-700 mb-1">Mobile / WhatsApp *</label>
          <input required value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="e.g. 98610 11101" className="w-full px-3 py-2 rounded-xl border border-slate-300" />
        </div>
        <div>
          <label className="block font-semibold text-slate-700 mb-1">Email</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@business.in" className="w-full px-3 py-2 rounded-xl border border-slate-300" />
        </div>
        <div>
          <label className="block font-semibold text-slate-700 mb-1">Business Name</label>
          <input value={businessName} onChange={(e) => setBusinessName(e.target.value)} placeholder="e.g. SmileCare Dental Clinic" className="w-full px-3 py-2 rounded-xl border border-slate-300" />
        </div>
        <div>
          <label className="block font-semibold text-slate-700 mb-1">Business Type *</label>
          <input required value={businessType} onChange={(e) => setBusinessType(e.target.value)} placeholder="e.g. Dental Clinic, Restaurant, Salon" className="w-full px-3 py-2 rounded-xl border border-slate-300" />
        </div>
        <div>
          <label className="block font-semibold text-slate-700 mb-1">City *</label>
          <input required value={city} onChange={(e) => setCity(e.target.value)} placeholder="e.g. Bhubaneswar, Pune, Jaipur" className="w-full px-3 py-2 rounded-xl border border-slate-300" />
        </div>
        <div>
          <label className="block font-semibold text-slate-700 mb-1">Budget Range</label>
          <select value={budgetRange} onChange={(e) => setBudgetRange(e.target.value)} className="w-full px-3 py-2 rounded-xl border border-slate-300 bg-white">
            <option>Rs 7,999 - Rs 10,000</option>
            <option>Rs 10,000 - Rs 20,000</option>
            <option>Rs 20,000 - Rs 35,000</option>
            <option>Rs 35,000+</option>
          </select>
        </div>
        <div>
          <label className="block font-semibold text-slate-700 mb-1">Timeline</label>
          <select value={timeline} onChange={(e) => setTimeline(e.target.value)} className="w-full px-3 py-2 rounded-xl border border-slate-300 bg-white">
            <option>Immediate</option>
            <option>Within 1 week</option>
            <option>Within 2 weeks</option>
            <option>This month</option>
            <option>Flexible</option>
          </select>
        </div>
      </div>

      <div className="text-xs">
        <label className="block font-semibold text-slate-700 mb-1">Current Website (if any)</label>
        <input value={website} onChange={(e) => setWebsite(e.target.value)} placeholder="https://... (leave blank if you need a new website)" className="w-full px-3 py-2 rounded-xl border border-slate-300" />
      </div>

      <div className="text-xs">
        <label className="block font-semibold text-slate-700 mb-1">What do you need?</label>
        <textarea rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Pages, WhatsApp booking, Google Maps, online payments, etc." className="w-full px-3 py-2 rounded-xl border border-slate-300" />
      </div>

      <label className="flex items-start space-x-2 text-xs text-slate-600 cursor-pointer">
        <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="mt-0.5 rounded border-slate-300" />
        <span>
          I agree to be contacted by LeadHarvest Web Studio via phone, WhatsApp, or email regarding my website quote (DPDP compliant).
        </span>
      </label>

      <button
        type="submit"
        disabled={submitting}
        className="w-full py-3 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs flex items-center justify-center space-x-2 shadow-sm disabled:opacity-60"
      >
        <Send className="w-4 h-4" />
        <span>{submitting ? "Sending Request..." : "Request Free Website Quote"}</span>
      </button>

      <p className="text-[11px] text-slate-400 flex items-center justify-center space-x-1">
        <ShieldCheck className="w-3.5 h-3.5" />
        <span>No spam. Opt out anytime.</span>
      </p>
    </form>
  );
}
