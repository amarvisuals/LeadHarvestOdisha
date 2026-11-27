"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Globe, AlertTriangle, CheckCircle2, Mail, RefreshCw } from "lucide-react";
import { apiFetch } from "@/lib/api";

export default function StateSeoAdmin({ onNotify }: { onNotify: (msg: string) => void }) {
  const [data, setData] = useState<any>(null);
  const [days, setDays] = useState(30);
  const [waveFilter, setWaveFilter] = useState<string>("all");

  async function loadOverview() {
    const res = await apiFetch(`/api/admin/state-seo/overview?days=${days}`);
    if (res.ok) setData(await res.json());
  }

  useEffect(() => {
    loadOverview();
  }, [days]);

  if (!data) {
    return <div className="p-6 bg-white rounded-2xl border border-slate-200 text-xs text-slate-400">Loading State SEO Analytics...</div>;
  }

  const states = (data.states || []).filter((s: any) =>
    waveFilter === "all" ? true : String(s.rollout_wave) === waveFilter
  );

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5 space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-black text-slate-900 flex items-center space-x-2">
            <Globe className="w-4 h-4 text-brand-600" />
            <span>State-Wise SEO Rollout, Traffic &amp; Conversion</span>
          </h2>
          <p className="text-xs text-slate-500">
            Control rollout waves, daily publish caps, quality gates, and Hindi/Odia translation review status.
          </p>
        </div>
        <div className="flex flex-wrap gap-2 text-xs">
          <select value={days} onChange={(e) => setDays(Number(e.target.value))} className="px-3 py-1.5 rounded-xl border border-slate-200 bg-white font-semibold">
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
          <select value={waveFilter} onChange={(e) => setWaveFilter(e.target.value)} className="px-3 py-1.5 rounded-xl border border-slate-200 bg-white font-semibold">
            <option value="all">All Waves</option>
            <option value="1">Wave 1</option>
            <option value="2">Wave 2</option>
            <option value="3">Wave 3</option>
          </select>
          <button
            onClick={async () => {
              const r = await apiFetch("/api/admin/state-seo/alerts/check", { method: "POST" });
              const d = await r.json();
              onNotify(d.alert_sent ? `Alert email sent (${d.unpublished_count} unpublished)` : "All state hubs healthy & indexed.");
            }}
            className="px-3 py-1.5 rounded-xl bg-slate-900 text-white font-bold flex items-center space-x-1"
          >
            <Mail className="w-3.5 h-3.5" />
            <span>Check Traffic/Index Alerts</span>
          </button>
          <button onClick={loadOverview} className="px-3 py-1.5 rounded-xl bg-slate-100 text-slate-700 font-bold flex items-center space-x-1">
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* State Heatmap / Inventory Table */}
      <div className="overflow-x-auto border border-slate-200 rounded-xl">
        <table className="w-full text-xs text-left">
          <thead className="bg-slate-50 text-slate-500 text-[11px] uppercase">
            <tr>
              <th className="p-2.5">State / UT</th>
              <th className="p-2.5">Wave</th>
              <th className="p-2.5">Status</th>
              <th className="p-2.5">Impr / Clicks</th>
              <th className="p-2.5">Avg Pos</th>
              <th className="p-2.5">Signups / Rev</th>
              <th className="p-2.5">Daily Cap</th>
              <th className="p-2.5">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {states.map((s: any) => (
              <tr key={s.state_slug} className="hover:bg-slate-50">
                <td className="p-2.5 font-bold text-slate-900">
                  <Link href={`/leads/${s.state_slug}`} target="_blank" className="hover:text-brand-700">
                    {s.state_name}
                  </Link>
                </td>
                <td className="p-2.5">Wave {s.rollout_wave}</td>
                <td className="p-2.5">
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${s.is_published ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-800"}`}>
                    {s.is_published ? `Published (${s.indexed_pages})` : "Gated / Noindex"}
                  </span>
                </td>
                <td className="p-2.5 text-slate-600">{s.impressions} / {s.clicks}</td>
                <td className="p-2.5 font-semibold">{s.avg_position}</td>
                <td className="p-2.5 text-slate-700">{s.signups} / ₹{s.revenue_inr.toLocaleString()}</td>
                <td className="p-2.5">{s.daily_publish_cap}/day</td>
                <td className="p-2.5">
                  <button
                    onClick={async () => {
                      await apiFetch(`/api/admin/state-seo/${s.state_slug}`, {
                        method: "PUT",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ is_published: !s.is_published }),
                      });
                      onNotify(`${s.state_name} ${!s.is_published ? "published" : "set to noindex"}.`);
                      loadOverview();
                    }}
                    className="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 font-semibold text-slate-800"
                  >
                    {s.is_published ? "Set Noindex" : "Publish"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Opportunity Finder & Cannibalisation */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
          <h3 className="font-black text-slate-800">Opportunity Finder (High Impressions / Low CTR)</h3>
          {(data.opportunities || []).slice(0, 5).map((o: any) => (
            <div key={o.state} className="flex items-center justify-between py-1 border-b border-slate-200/60 last:border-0">
              <span className="font-semibold text-slate-700">{o.query}</span>
              <span className="text-slate-500">{o.impressions} impr · {o.ctr_pct}% CTR</span>
            </div>
          ))}
        </div>
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
          <h3 className="font-black text-slate-800">Cannibalisation &amp; Crawl Health</h3>
          {(data.cannibalisation || []).length === 0 ? (
            <p className="text-emerald-700 font-semibold flex items-center space-x-1.5">
              <CheckCircle2 className="w-4 h-4" />
              <span>Zero keyword cannibalisation detected across state pages.</span>
            </p>
          ) : (
            data.cannibalisation.map((c: any) => (
              <p key={c.keyword} className="text-amber-700 flex items-center space-x-1">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>{c.keyword}: {c.urls.join(", ")}</span>
              </p>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
