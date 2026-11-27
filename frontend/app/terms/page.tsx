import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Terms of Use | LeadHarvest India",
  description: "Terms of Use, lawful B2B outreach responsibilities, DND compliance, and subscription billing terms for LeadHarvest India.",
  path: "/terms",
});

export default function TermsPage() {
  return (
    <div className="max-w-3xl mx-auto bg-white rounded-3xl border border-slate-200 p-8 space-y-5 text-sm text-slate-700 leading-relaxed">
      <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs font-semibold">
        Draft Legal Notice — Please review with a qualified lawyer before commercial launch.
      </div>
      <h1 className="text-2xl font-black text-slate-900">Terms of Use</h1>
      <p><strong>1. Lawful Use &amp; Telemarketing Compliance:</strong> Customers are solely responsible for the lawful use of collected business contact data, including respecting TRAI DND (Do Not Disturb) / NCPR preferences and obtaining consent before sending marketing messages or calls.</p>
      <p><strong>2. Acceptable Use:</strong> You may not attempt to bypass rate limits, guest trial restrictions, or access another user&apos;s data or exports.</p>
      <p><strong>3. Subscriptions &amp; Billing:</strong> Paid plans renew monthly or yearly in INR via Razorpay. You may cancel anytime from your Billing page.</p>
    </div>
  );
}
