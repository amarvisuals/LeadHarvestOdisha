import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Privacy Policy (DPDP Act 2023) | LeadHarvest India",
  description: "How LeadHarvest India protects your account data, uploaded Known Records, and privacy rights under India's DPDP Act 2023.",
  path: "/privacy",
});

export default function PrivacyPage() {
  return (
    <div className="max-w-3xl mx-auto bg-white rounded-3xl border border-slate-200 p-8 space-y-5 text-sm text-slate-700 leading-relaxed">
      <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs font-semibold">
        Draft Privacy Policy (India DPDP Act 2023) — Please review with a qualified lawyer.
      </div>
      <h1 className="text-2xl font-black text-slate-900">Privacy Policy</h1>
      <p><strong>1. Data Collected:</strong> We collect your account profile (name, email, optional phone, business type), hashed IP/session identifiers for rate limiting and guest trial enforcement, and first-party analytics.</p>
      <p><strong>2. Search Parameters &amp; Files:</strong> Your run parameters (states, cities, categories, filters) and generated Excel/CSV files are stored securely and may be inspected by the service owner for customer support, abuse prevention, and product improvement.</p>
      <p><strong>3. Data Isolation:</strong> Your uploaded files and Known Records are strictly isolated to your account and are never shared with other customers.</p>
      <p><strong>4. Your Rights (DPDP Act 2023):</strong> You can download all your data or permanently delete your account anytime from your Profile page.</p>
    </div>
  );
}
