import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Contact Support | LeadHarvest India",
  description: "Get in touch with LeadHarvest India support for billing, custom categories, GST invoices, or agency onboarding.",
  path: "/contact",
});

export default function ContactPage() {
  return (
    <div className="max-w-2xl mx-auto bg-white rounded-3xl border border-slate-200 p-8 space-y-4 text-sm text-slate-700">
      <h1 className="text-2xl font-black text-slate-900">Contact Support</h1>
      <p>Need help with a subscription, custom state/category request, or invoice?</p>
      <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-1 text-xs">
        <p><strong>Email:</strong> support@leadharvest.in</p>
        <p><strong>Region:</strong> Bhubaneswar, Odisha, India</p>
        <p><strong>Hours:</strong> Mon–Sat, 10:00 AM – 7:00 PM IST</p>
      </div>
    </div>
  );
}
