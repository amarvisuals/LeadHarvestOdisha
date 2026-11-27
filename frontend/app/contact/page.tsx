import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import WebsiteQuoteForm from "@/components/WebsiteQuoteForm";

export const metadata: Metadata = buildMetadata({
  title: "Contact & Free Website Quote | LeadHarvest India",
  description: "Request a free custom website quote or contact LeadHarvest India support for billing, custom categories, GST invoices, or agency onboarding.",
  path: "/contact",
});

export default function ContactPage() {
  return (
    <div className="max-w-4xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6 pb-16">
      <div className="lg:col-span-2 bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-xs">
        <WebsiteQuoteForm />
      </div>

      <div className="bg-white rounded-3xl border border-slate-200 p-6 space-y-4 text-sm text-slate-700 h-fit">
        <h2 className="text-lg font-black text-slate-900">Contact Support</h2>
        <p className="text-xs text-slate-500">
          Need help with a subscription, custom state/category request, or invoice?
        </p>
        <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-1.5 text-xs">
          <p><strong>Email:</strong> support@leadharvest.in</p>
          <p><strong>Region:</strong> Bhubaneswar, Odisha, India</p>
          <p><strong>Hours:</strong> Mon–Sat, 10:00 AM – 7:00 PM IST</p>
        </div>
        <div className="p-4 rounded-2xl bg-brand-50 border border-brand-200 space-y-1 text-xs text-brand-900">
          <p className="font-bold">Why Businesses Choose Us</p>
          <p className="text-[11px] text-brand-800">
            Fast mobile-first websites, WhatsApp lead buttons, Google Maps setup, and local SEO — delivered in 5–10 days.
          </p>
        </div>
      </div>
    </div>
  );
}
