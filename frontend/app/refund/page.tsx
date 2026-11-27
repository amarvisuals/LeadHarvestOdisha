import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Refund & Cancellation Policy | LeadHarvest India",
  description: "7-day money-back guarantee and one-click subscription cancellation policy for LeadHarvest India.",
  path: "/refund",
});

export default function RefundPage() {
  return (
    <div className="max-w-3xl mx-auto bg-white rounded-3xl border border-slate-200 p-8 space-y-5 text-sm text-slate-700 leading-relaxed">
      <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs font-semibold">
        Draft Refund Policy — Please review with a qualified lawyer.
      </div>
      <h1 className="text-2xl font-black text-slate-900">Refund &amp; Cancellation Policy</h1>
      <p><strong>7-Day Money-Back Guarantee:</strong> If you are not satisfied with any paid plan within 7 days of your initial purchase, contact support for a full refund.</p>
      <p><strong>Cancellations:</strong> You can cancel your subscription anytime from the Billing page. Your plan remains active until the end of the current billing period.</p>
    </div>
  );
}
