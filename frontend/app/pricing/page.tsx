"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Check, Sparkles, ShieldCheck, ArrowRight } from "lucide-react";
import { apiFetch } from "@/lib/api";

interface PlanItem {
  id: string;
  name: string;
  description: string;
  price_monthly_inr: number;
  price_yearly_inr: number;
  max_states: number;
  max_runs_per_day: number;
  max_leads_per_run: number;
  max_leads_per_month: number;
  retention_days: number;
  allow_advanced_filters: boolean;
  allow_all_filters: boolean;
  allow_presets: boolean;
  allow_csv_export: boolean;
  allow_webhook_export: boolean;
  team_seats: number;
  is_popular: boolean;
}

export default function PricingPage() {
  const router = useRouter();
  const [plans, setPlans] = useState<PlanItem[]>([]);
  const [yearly, setYearly] = useState(false);
  const [refundNote, setRefundNote] = useState("7-day money-back guarantee.");
  const [couponCode, setCouponCode] = useState("");
  const [processingPlan, setProcessingPlan] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    apiFetch("/api/billing/plans")
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (d) {
          setPlans(d.plans || []);
          setRefundNote(d.refund_guarantee_text || refundNote);
        }
      });
  }, []);

  const handleChoosePlan = async (plan: PlanItem) => {
    if (plan.price_monthly_inr === 0) {
      router.push("/signup");
      return;
    }

    setProcessingPlan(plan.id);
    setMessage(null);

    try {
      const meRes = await apiFetch("/api/auth/me");
      const me = await meRes.json();
      if (!me.authenticated) {
        router.push(`/signup?plan=${plan.id}`);
        return;
      }

      // Simulated or Razorpay checkout
      const simRes = await apiFetch("/api/billing/simulate-complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          plan_id: plan.id,
          billing_cycle: yearly ? "yearly" : "monthly",
          coupon_code: couponCode.trim() || null,
          outcome: "success",
        }),
      });
      if (simRes.ok) {
        setMessage(`Upgraded to ${plan.name} plan! Redirecting to Billing...`);
        setTimeout(() => router.push("/billing"), 1200);
      } else {
        const err = await simRes.json();
        setMessage(err.detail || "Checkout failed.");
      }
    } finally {
      setProcessingPlan(null);
    }
  };

  return (
    <div className="space-y-10 pb-20 max-w-6xl mx-auto">
      <div className="text-center space-y-3 pt-4">
        <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-brand-50 text-brand-700 border border-brand-200 text-xs font-bold">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Simple, Transparent INR Pricing</span>
        </span>
        <h1 className="text-3xl sm:text-4xl font-black text-slate-900">
          Turn Local Business Leads Into Paid Website Clients
        </h1>
        <p className="text-sm text-slate-600 max-w-xl mx-auto">{refundNote}</p>

        {/* Billing Cycle Toggle + Coupon */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-3">
          <div className="inline-flex items-center p-1 bg-slate-200/70 rounded-xl text-xs font-bold">
            <button
              onClick={() => setYearly(false)}
              className={`px-4 py-2 rounded-lg transition-all ${!yearly ? "bg-white text-slate-900 shadow-xs" : "text-slate-600"}`}
            >
              Monthly
            </button>
            <button
              onClick={() => setYearly(true)}
              className={`px-4 py-2 rounded-lg transition-all ${yearly ? "bg-white text-brand-700 shadow-xs" : "text-slate-600"}`}
            >
              Yearly (2 Months Free)
            </button>
          </div>

          <input
            type="text"
            value={couponCode}
            onChange={(e) => setCouponCode(e.target.value)}
            placeholder="Have a coupon? (e.g. WELCOME20)"
            className="px-3.5 py-2 text-xs bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500/20"
          />
        </div>
      </div>

      {message && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm font-semibold text-center">
          {message}
        </div>
      )}

      {/* Plan Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {plans.map((plan) => {
          const price = yearly ? plan.price_yearly_inr : plan.price_monthly_inr;
          return (
            <div
              key={plan.id}
              className={`rounded-3xl p-6 flex flex-col justify-between bg-white border transition-all ${
                plan.is_popular
                  ? "border-brand-500 ring-4 ring-brand-500/10 shadow-xl"
                  : "border-slate-200 shadow-sm"
              }`}
            >
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-extrabold text-slate-900">{plan.name}</h2>
                  {plan.is_popular && (
                    <span className="px-2.5 py-0.5 text-[10px] font-bold uppercase bg-brand-600 text-white rounded-full">
                      Most Popular
                    </span>
                  )}
                </div>

                <div>
                  <span className="text-3xl font-black text-slate-900">
                    ₹{price.toLocaleString()}
                  </span>
                  <span className="text-xs text-slate-500 ml-1">
                    {price === 0 ? "forever" : yearly ? "/year" : "/month"}
                  </span>
                </div>

                <p className="text-xs text-slate-600 min-h-[36px]">{plan.description}</p>

                <ul className="space-y-2 text-xs text-slate-700 pt-2 border-t border-slate-100">
                  <li className="flex items-center space-x-2">
                    <Check className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span>
                      {plan.max_states >= 36
                        ? "All 36 Indian States & UTs"
                        : plan.max_states === 1
                        ? "Your Home State (Free)"
                        : `Home State + ${plan.max_states - 1} Extra States`}
                    </span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <Check className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span>{plan.max_leads_per_month.toLocaleString()} leads / month</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <Check className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span>{plan.max_runs_per_day} runs / day</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <Check className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span>
                      {plan.allow_all_filters
                        ? "ALL Smart Filters & Score"
                        : plan.allow_advanced_filters
                        ? "Basic Smart Filters (No Website)"
                        : "Standard Filters Only"}
                    </span>
                  </li>
                  {plan.allow_csv_export && (
                    <li className="flex items-center space-x-2">
                      <Check className="w-4 h-4 text-emerald-600 shrink-0" />
                      <span>Excel + CSV Export</span>
                    </li>
                  )}
                  {plan.team_seats > 1 && (
                    <li className="flex items-center space-x-2">
                      <Check className="w-4 h-4 text-emerald-600 shrink-0" />
                      <span>{plan.team_seats} Team Seats + Webhooks</span>
                    </li>
                  )}
                </ul>
              </div>

              <button
                type="button"
                disabled={processingPlan === plan.id}
                onClick={() => handleChoosePlan(plan)}
                className={`mt-6 w-full py-3 rounded-xl text-xs font-bold flex items-center justify-center space-x-1.5 transition-all ${
                  plan.is_popular
                    ? "bg-brand-600 hover:bg-brand-700 text-white shadow-md"
                    : "bg-slate-900 hover:bg-slate-800 text-white"
                }`}
              >
                <span>
                  {processingPlan === plan.id
                    ? "Activating..."
                    : price === 0
                    ? "Start Free"
                    : `Choose ${plan.name}`}
                </span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          );
        })}
      </div>

      {/* How Home State Works */}
      <div id="how-it-works" className="bg-white rounded-2xl border border-slate-200 p-6 space-y-2 text-xs text-slate-700">
        <h2 className="text-base font-black text-slate-900">Your own state is free. Unlock any other state with a plan.</h2>
        <p>
          When you first visit LeadHarvest India, we use your approximate IP location (never GPS) to detect your Indian state and unlock it free for you. You can confirm or correct it once during signup; after that, your Home State is locked (changeable once every 90 days in Settings).
        </p>
      </div>

      {/* FAQ Section */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 space-y-4">
        <h3 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
          <ShieldCheck className="w-5 h-5 text-brand-600" />
          <span>Frequently Asked Questions</span>
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs text-slate-600">
          <div>
            <p className="font-bold text-slate-900 mb-1">How does &ldquo;No Website&rdquo; filtering help my agency?</p>
            <p>Instead of calling random businesses, you get a clean list of high-rating businesses (e.g., dental clinics or restaurants) that have no website listed and a valid WhatsApp number—ready for your pitch.</p>
          </div>
          <div>
            <p className="font-bold text-slate-900 mb-1">Are my Known Records kept private?</p>
            <p>Yes. Every user&apos;s uploaded lists and past runs are strictly isolated to their own account and never shared with other customers.</p>
          </div>
          <div>
            <p className="font-bold text-slate-900 mb-1">What payment methods are supported?</p>
            <p>UPI, Credit/Debit Cards, and Netbanking via Razorpay (with GST-ready PDF invoices generated automatically).</p>
          </div>
          <div>
            <p className="font-bold text-slate-900 mb-1">Can I cancel anytime?</p>
            <p>Yes—cancel in one click from your Billing page, plus {refundNote}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
