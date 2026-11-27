"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { CreditCard, Download, AlertTriangle, ArrowUpRight, FileText } from "lucide-react";
import { apiFetch } from "@/lib/api";

interface BillingStatus {
  plan: {
    id: string;
    name: string;
    price_monthly_inr: number;
    max_states: number;
    max_runs_per_day: number;
    max_leads_per_month: number;
  };
  subscription: {
    status: string;
    billing_cycle: string;
    current_period_end?: string;
    grace_until?: string;
    cancel_at_period_end: boolean;
  };
  usage: {
    runs_today: number;
    leads_this_month: number;
    total_runs: number;
  };
  invoices: Array<{
    id: string;
    invoice_number: string;
    plan_name: string;
    total_inr: number;
    created_at: string;
  }>;
}

export default function BillingPage() {
  const [data, setData] = useState<BillingStatus | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    const res = await apiFetch("/api/billing/status");
    if (res.ok) setData(await res.json());
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  const handleCancel = async () => {
    if (!confirm("Cancel your paid subscription and revert to the Free plan?")) return;
    const res = await apiFetch("/api/billing/cancel", { method: "POST" });
    if (res.ok) await load();
  };

  if (loading) return <div className="py-12 text-center text-sm text-slate-400">Loading billing details...</div>;
  if (!data) {
    return (
      <div className="max-w-lg mx-auto py-16 text-center space-y-3">
        <p className="font-bold text-slate-800">Please sign in to view your billing &amp; invoices.</p>
        <Link href="/login" className="inline-block px-5 py-2.5 bg-brand-600 text-white rounded-xl text-xs font-bold">
          Sign In
        </Link>
      </div>
    );
  }

  const leadsPct = Math.min(100, Math.round((data.usage.leads_this_month / Math.max(data.plan.max_leads_per_month, 1)) * 100));
  const runsPct = Math.min(100, Math.round((data.usage.runs_today / Math.max(data.plan.max_runs_per_day, 1)) * 100));

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-20">
      <div className="flex items-center justify-between pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-black text-slate-900 flex items-center space-x-2">
            <CreditCard className="w-6 h-6 text-brand-600" />
            <span>Billing &amp; Usage</span>
          </h1>
          <p className="text-sm text-slate-500">Manage your subscription, monthly lead quotas, and GST invoices.</p>
        </div>
        <Link href="/pricing" className="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold rounded-xl flex items-center space-x-1">
          <span>Upgrade / Change Plan</span>
          <ArrowUpRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {data.subscription.status === "past_due" && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-900 flex items-center space-x-3 text-xs">
          <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" />
          <span>
            Your last renewal payment failed. You are in a <strong>3-day grace period</strong> until{" "}
            {data.subscription.grace_until ? new Date(data.subscription.grace_until).toLocaleDateString() : "soon"}.
          </span>
        </div>
      )}

      {/* Current Plan & Usage Meters */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-2xl border border-slate-200 p-5 space-y-2">
          <span className="text-[11px] font-bold uppercase text-slate-400">Current Plan</span>
          <p className="text-2xl font-black text-slate-900">{data.plan.name}</p>
          <p className="text-xs text-slate-500 capitalize">
            Status: <strong>{data.subscription.status}</strong> ({data.subscription.billing_cycle})
          </p>
          {data.plan.id !== "free" && (
            <button onClick={handleCancel} className="text-xs font-semibold text-rose-600 hover:underline pt-1">
              Cancel Subscription
            </button>
          )}
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-5 space-y-2">
          <div className="flex justify-between text-xs font-bold text-slate-700">
            <span>Monthly Leads</span>
            <span>{data.usage.leads_this_month.toLocaleString()} / {data.plan.max_leads_per_month.toLocaleString()}</span>
          </div>
          <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden">
            <div className={`h-full rounded-full ${leadsPct >= 80 ? "bg-amber-500" : "bg-brand-600"}`} style={{ width: `${leadsPct}%` }} />
          </div>
          <p className="text-[11px] text-slate-400">{leadsPct}% of monthly quota used</p>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-5 space-y-2">
          <div className="flex justify-between text-xs font-bold text-slate-700">
            <span>Runs Today</span>
            <span>{data.usage.runs_today} / {data.plan.max_runs_per_day}</span>
          </div>
          <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden">
            <div className="h-full bg-emerald-600 rounded-full" style={{ width: `${runsPct}%` }} />
          </div>
          <p className="text-[11px] text-slate-400">Total lifetime runs: {data.usage.total_runs}</p>
        </div>
      </div>

      {/* Invoices Table */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="p-4 border-b border-slate-100 flex items-center space-x-2">
          <FileText className="w-4 h-4 text-brand-600" />
          <h2 className="text-sm font-bold text-slate-900">GST Invoices</h2>
        </div>
        {data.invoices.length === 0 ? (
          <p className="p-6 text-xs text-slate-400 text-center">No invoices yet.</p>
        ) : (
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase text-[10px]">
              <tr>
                <th className="py-2.5 px-4">Invoice No</th>
                <th className="py-2.5 px-4">Plan</th>
                <th className="py-2.5 px-4">Date</th>
                <th className="py-2.5 px-4">Total (INR)</th>
                <th className="py-2.5 px-4 text-right">PDF</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.invoices.map((inv) => (
                <tr key={inv.id}>
                  <td className="py-3 px-4 font-bold text-slate-800">{inv.invoice_number}</td>
                  <td className="py-3 px-4">{inv.plan_name}</td>
                  <td className="py-3 px-4 text-slate-500">{new Date(inv.created_at).toLocaleDateString()}</td>
                  <td className="py-3 px-4 font-bold">₹{inv.total_inr.toLocaleString()}</td>
                  <td className="py-3 px-4 text-right">
                    <a
                      href={`/api/billing/invoices/${inv.id}/pdf`}
                      className="inline-flex items-center space-x-1 px-2.5 py-1 bg-brand-50 text-brand-700 font-bold rounded-lg border border-brand-200"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>PDF</span>
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
