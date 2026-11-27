"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  LayoutDashboard, Users, PlayCircle, CreditCard, Wrench,
  Download, Eye, RefreshCw, CheckCircle2, AlertCircle, Search, Flame
} from "lucide-react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, AreaChart, Area, CartesianGrid
} from "recharts";
import { apiFetch } from "@/lib/api";
import HotLeadsSection from "@/components/HotLeadsSection";

type AdminTab = "dashboard" | "hot_leads" | "users" | "runs" | "plans" | "seo" | "testing";

export default function AdminPanelPage() {
  const [tab, setTab] = useState<AdminTab>("dashboard");
  const [days, setDays] = useState(30);
  const [dash, setDash] = useState<any>(null);
  const [hotStats, setHotStats] = useState<any>(null);
  const [usersData, setUsersData] = useState<any[]>([]);
  const [userSearch, setUserSearch] = useState("");
  const [runs, setRuns] = useState<any[]>([]);
  const [insights, setInsights] = useState<any>(null);
  const [plans, setPlans] = useState<any[]>([]);
  const [coupons, setCoupons] = useState<any[]>([]);
  const [sysChecks, setSysChecks] = useState<any>(null);
  const [flags, setFlags] = useState<any[]>([]);
  const [settingsList, setSettingsList] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [authError, setAuthError] = useState(false);

  // Testing / Creation state
  const [newUserEmail, setNewUserEmail] = useState("");
  const [newUserPlan, setNewUserPlan] = useState("pro");
  const [newCouponCode, setNewCouponCode] = useState("");
  const [newCouponPct, setNewCouponPct] = useState(20);
  const [toast, setToast] = useState<string | null>(null);

  // SEO & Blog state
  const [gscData, setGscData] = useState<any>(null);
  const [kwList, setKwList] = useState<any[]>([]);
  const [kwInput, setKwInput] = useState("");
  const [kwUrl, setKwUrl] = useState("/features/no-website-filter");
  const [auditResult, setAuditResult] = useState<any>(null);
  const [blogPosts, setBlogPosts] = useState<any[]>([]);
  const [organicFunnel, setOrganicFunnel] = useState<any>(null);
  const [newPostTitle, setNewPostTitle] = useState("");
  const [newPostSlug, setNewPostSlug] = useState("");
  const [newPostKw, setNewPostKw] = useState("");
  const [newPostBody, setNewPostBody] = useState("");
  const [seoScorePreview, setSeoScorePreview] = useState<any>(null);

  const notify = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3500);
  };

  async function loadDashboard() {
    const [res, hRes] = await Promise.all([
      apiFetch(`/api/admin/dashboard?days=${days}`),
      apiFetch("/api/admin/hot-leads/stats"),
    ]);
    if (res.status === 401 || res.status === 403) {
      setAuthError(true);
      return;
    }
    if (res.ok) setDash(await res.json());
    if (hRes.ok) setHotStats(await hRes.json());
  }

  async function loadUsers() {
    const res = await apiFetch(`/api/admin/users?q=${encodeURIComponent(userSearch)}`);
    if (res.ok) {
      const d = await res.json();
      setUsersData(d.items || []);
    }
  }

  async function loadRunsAndInsights() {
    const [rRes, iRes] = await Promise.all([apiFetch("/api/admin/runs"), apiFetch("/api/admin/insights")]);
    if (rRes.ok) setRuns(await rRes.json());
    if (iRes.ok) setInsights(await iRes.json());
  }

  async function loadPlansAndCoupons() {
    const [pRes, cRes] = await Promise.all([apiFetch("/api/billing/plans"), apiFetch("/api/admin/coupons")]);
    if (pRes.ok) setPlans((await pRes.json()).plans || []);
    if (cRes.ok) setCoupons(await cRes.json());
  }

  async function loadTestingTools() {
    const [sRes, fRes, stRes, aRes] = await Promise.all([
      apiFetch("/api/admin/system-checks"),
      apiFetch("/api/admin/flags"),
      apiFetch("/api/admin/settings"),
      apiFetch("/api/admin/audit-logs"),
    ]);
    if (sRes.ok) setSysChecks(await sRes.json());
    if (fRes.ok) setFlags(await fRes.json());
    if (stRes.ok) setSettingsList(await stRes.json());
    if (aRes.ok) setAuditLogs(await aRes.json());
  }

  async function loadSeoAndBlog() {
    const [gRes, kRes, aRes, bRes, fRes] = await Promise.all([
      apiFetch("/api/admin/seo/search-console"),
      apiFetch("/api/admin/seo/keywords"),
      apiFetch("/api/admin/seo/audits"),
      apiFetch("/api/admin/blog"),
      apiFetch("/api/admin/seo/funnel"),
    ]);
    if (gRes.ok) setGscData(await gRes.json());
    if (kRes.ok) setKwList(await kRes.json());
    if (aRes.ok) {
      const audits = await aRes.json();
      if (audits.length > 0) setAuditResult(audits[0]);
    }
    if (bRes.ok) setBlogPosts(await bRes.json());
    if (fRes.ok) setOrganicFunnel(await fRes.json());
  }

  useEffect(() => {
    loadDashboard();
  }, [days]);

  useEffect(() => {
    if (tab === "users") loadUsers();
    if (tab === "runs") loadRunsAndInsights();
    if (tab === "plans") loadPlansAndCoupons();
    if (tab === "seo") loadSeoAndBlog();
    if (tab === "testing") loadTestingTools();
  }, [tab]);

  if (authError) {
    return (
      <div className="max-w-md mx-auto py-16 text-center space-y-3 bg-white rounded-3xl border border-slate-200 p-8">
        <AlertCircle className="w-10 h-10 text-rose-500 mx-auto" />
        <h1 className="text-xl font-black text-slate-900">Admin Access Required</h1>
        <p className="text-xs text-slate-500">Sign in with your owner/admin account to access the control panel.</p>
      </div>
    );
  }

  const navItems: Array<{ id: AdminTab; label: string; icon: any }> = [
    { id: "dashboard", label: "Dashboard & Funnel", icon: LayoutDashboard },
    { id: "hot_leads", label: "Hot Leads", icon: Flame },
    { id: "users", label: "Users & Contacts", icon: Users },
    { id: "runs", label: "Runs & Insights", icon: PlayCircle },
    { id: "plans", label: "Plans & Coupons", icon: CreditCard },
    { id: "seo", label: "SEO & Blog CMS", icon: Search },
    { id: "testing", label: "Testing & Settings", icon: Wrench },
  ];

  return (
    <div className="flex flex-col lg:flex-row gap-6 pb-20">
      {/* Sidebar */}
      <aside className="lg:w-60 shrink-0 bg-white rounded-2xl border border-slate-200 p-3 h-fit space-y-1">
        <p className="px-3 py-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">Owner Admin</p>
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = tab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setTab(item.id)}
              className={`w-full flex items-center space-x-2.5 px-3 py-2.5 rounded-xl text-xs font-semibold transition-colors ${
                active ? "bg-brand-600 text-white" : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{item.label}</span>
            </button>
          );
        })}
      </aside>

      {/* Main Content */}
      <div className="flex-1 space-y-6 min-w-0">
        {toast && (
          <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold">
            {toast}
          </div>
        )}

        {/* TAB 1: DASHBOARD */}
        {tab === "dashboard" && dash && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h1 className="text-xl font-black text-slate-900">SaaS Metrics &amp; Conversion Funnel</h1>
              <select
                value={days}
                onChange={(e) => setDays(Number(e.target.value))}
                className="text-xs bg-white border border-slate-200 rounded-xl px-3 py-1.5 font-semibold"
              >
                <option value={1}>Today</option>
                <option value={7}>Last 7 days</option>
                <option value={30}>Last 30 days</option>
                <option value={90}>Last 90 days</option>
              </select>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="bg-white p-4 rounded-2xl border border-slate-200">
                <span className="text-[10px] font-bold uppercase text-slate-400">MRR</span>
                <p className="text-2xl font-black text-emerald-700">₹{dash.kpis.mrr_inr.toLocaleString()}</p>
                <span className="text-[11px] text-slate-500">ARPU: ₹{dash.kpis.arpu_inr}</span>
              </div>
              <div className="bg-white p-4 rounded-2xl border border-slate-200">
                <span className="text-[10px] font-bold uppercase text-slate-400">Paying Subscribers</span>
                <p className="text-2xl font-black text-slate-900">{dash.kpis.active_paying_subscribers}</p>
                <span className="text-[11px] text-slate-500">Churn: {dash.kpis.churn_rate_pct}%</span>
              </div>
              <div className="bg-white p-4 rounded-2xl border border-slate-200">
                <span className="text-[10px] font-bold uppercase text-slate-400">Visitors / Guest Runs</span>
                <p className="text-2xl font-black text-slate-900">{dash.kpis.unique_visitors} / {dash.kpis.guest_runs}</p>
                <span className="text-[11px] text-slate-500">{dash.kpis.guests_hit_limit} hit 4-run limit</span>
              </div>
              <div className="bg-white p-4 rounded-2xl border border-slate-200">
                <span className="text-[10px] font-bold uppercase text-slate-400">Signups (Conv %)</span>
                <p className="text-2xl font-black text-brand-700">{dash.kpis.signups}</p>
                <span className="text-[11px] text-slate-500">{dash.kpis.signup_conversion_pct}% visitor→signup</span>
              </div>
            </div>

            {/* Today's Focus Card (Hot Leads Follow-Ups) */}
            {hotStats && (
              <div className="bg-white p-5 rounded-2xl border border-rose-200 space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center space-x-2">
                    <Flame className="w-4 h-4 text-rose-600" />
                    <h2 className="text-sm font-black text-slate-900">
                      Today&apos;s Focus: {hotStats.todays_focus?.length || 0} Follow-Ups Due
                    </h2>
                    {hotStats.overdue_followups > 0 && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-rose-100 text-rose-700">
                        {hotStats.overdue_followups} overdue
                      </span>
                    )}
                  </div>
                  <button
                    onClick={() => setTab("hot_leads")}
                    className="text-xs font-bold text-brand-700 hover:underline"
                  >
                    Open Hot Leads Pipeline →
                  </button>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5 text-xs">
                  {(hotStats.todays_focus || []).slice(0, 6).map((hl: any) => (
                    <Link
                      key={hl.id}
                      href={`/admin/hot-leads/${hl.id}`}
                      className="p-3 rounded-xl bg-slate-50 hover:bg-rose-50/40 border border-slate-200 flex items-center justify-between"
                    >
                      <div className="min-w-0 pr-2">
                        <p className="font-bold text-slate-900 truncate">{hl.business_name}</p>
                        <p className="text-[11px] text-slate-500 truncate">{hl.city || "India"} · {hl.stage}</p>
                      </div>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-rose-100 text-rose-700 shrink-0">
                        {hl.score}
                      </span>
                    </Link>
                  ))}
                  {(!hotStats.todays_focus || hotStats.todays_focus.length === 0) && (
                    <p className="text-xs text-slate-400">No follow-ups due today. Check Hot Leads for new inquiries.</p>
                  )}
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              <div className="bg-white p-5 rounded-2xl border border-slate-200 space-y-3">
                <h2 className="text-xs font-bold uppercase text-slate-500">Conversion Funnel</h2>
                <div className="h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={dash.funnel}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="stage" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip />
                      <Bar dataKey="count" fill="#0f766e" radius={[6, 6, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="bg-white p-5 rounded-2xl border border-slate-200 space-y-3">
                <h2 className="text-xs font-bold uppercase text-slate-500">Daily Runs &amp; Revenue</h2>
                <div className="h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={dash.daily_series}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip />
                      <Area type="monotone" dataKey="runs" stroke="#0f766e" fill="#ccfbf1" />
                      <Area type="monotone" dataKey="signups" stroke="#f59e0b" fill="#fef3c7" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div className="bg-white p-4 rounded-2xl border border-slate-200 space-y-2">
                <h3 className="font-bold text-slate-800">Top States</h3>
                {dash.top_states.map((s: any) => (
                  <div key={s.name} className="flex justify-between"><span>{s.name}</span><strong>{s.count}</strong></div>
                ))}
              </div>
              <div className="bg-white p-4 rounded-2xl border border-slate-200 space-y-2">
                <h3 className="font-bold text-slate-800">Top Categories</h3>
                {dash.top_categories.map((c: any) => (
                  <div key={c.name} className="flex justify-between"><span className="truncate pr-2">{c.name}</span><strong>{c.count}</strong></div>
                ))}
              </div>
              <div className="bg-white p-4 rounded-2xl border border-slate-200 space-y-2">
                <h3 className="font-bold text-slate-800">Most Used Smart Filters</h3>
                {dash.top_filters.length === 0 ? <p className="text-slate-400">No filter usage yet</p> : dash.top_filters.map((f: any) => (
                  <div key={f.name} className="flex justify-between"><span>{f.name}</span><strong>{f.count}</strong></div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB: HOT LEADS */}
        {tab === "hot_leads" && <HotLeadsSection onNotify={notify} />}

        {/* TAB 2: USERS & CONTACT EXPORT */}
        {tab === "users" && (
          <div className="bg-white rounded-2xl border border-slate-200 p-5 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <h1 className="text-lg font-black text-slate-900">Users &amp; Lead Contact List</h1>
              <div className="flex items-center space-x-2">
                <input
                  value={userSearch}
                  onChange={(e) => setUserSearch(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && loadUsers()}
                  placeholder="Search name, email, phone..."
                  className="px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl"
                />
                <button onClick={loadUsers} className="px-3 py-1.5 bg-slate-900 text-white text-xs font-bold rounded-xl">Search</button>
                <a
                  href="/api/admin/users/export/contacts.csv"
                  className="px-3 py-1.5 bg-emerald-600 text-white text-xs font-bold rounded-xl inline-flex items-center space-x-1"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Export Contacts CSV</span>
                </a>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 uppercase text-[10px]">
                  <tr>
                    <th className="py-2.5 px-3">User</th>
                    <th className="py-2.5 px-3">Phone &amp; Niche</th>
                    <th className="py-2.5 px-3">Plan</th>
                    <th className="py-2.5 px-3">Runs / Leads</th>
                    <th className="py-2.5 px-3">LTV</th>
                    <th className="py-2.5 px-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {usersData.map((u) => (
                    <tr key={u.id}>
                      <td className="py-2.5 px-3">
                        <p className="font-bold text-slate-900">{u.name}</p>
                        <p className="text-[11px] text-slate-500">{u.email}</p>
                      </td>
                      <td className="py-2.5 px-3">
                        <p>{u.phone || "-"}</p>
                        <p className="text-[11px] text-slate-400">{u.business_type || "-"}</p>
                      </td>
                      <td className="py-2.5 px-3">
                        <select
                          value={u.plan_id}
                          onChange={async (e) => {
                            await apiFetch(`/api/admin/users/${u.id}/plan`, {
                              method: "POST",
                              headers: { "Content-Type": "application/json" },
                              body: JSON.stringify({ plan_id: e.target.value }),
                            });
                            notify(`Updated ${u.email} to ${e.target.value}`);
                            loadUsers();
                          }}
                          className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 font-semibold"
                        >
                          <option value="free">Free</option>
                          <option value="starter">Starter</option>
                          <option value="pro">Pro</option>
                          <option value="agency">Agency</option>
                        </select>
                      </td>
                      <td className="py-2.5 px-3 font-semibold">{u.total_runs} / {u.leads_generated}</td>
                      <td className="py-2.5 px-3 font-bold text-emerald-700">₹{u.lifetime_revenue_inr}</td>
                      <td className="py-2.5 px-3 text-right space-x-1.5 whitespace-nowrap">
                        <button
                          onClick={async () => {
                            await apiFetch(`/api/admin/impersonate/${u.id}`, { method: "POST" });
                            window.location.href = "/";
                          }}
                          className="px-2 py-1 bg-brand-50 text-brand-700 rounded-lg font-semibold inline-flex items-center space-x-1"
                        >
                          <Eye className="w-3 h-3" />
                          <span>View As</span>
                        </button>
                        <button
                          onClick={async () => {
                            await apiFetch(`/api/admin/users/${u.id}/suspend`, { method: "POST" });
                            loadUsers();
                          }}
                          className="px-2 py-1 bg-rose-50 text-rose-700 rounded-lg font-semibold"
                        >
                          {u.is_suspended ? "Unsuspend" : "Suspend"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 3: RUNS & SEARCH INTENT INSIGHTS */}
        {tab === "runs" && (
          <div className="space-y-5">
            {insights && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="bg-white p-5 rounded-2xl border border-slate-200 space-y-2">
                  <h2 className="font-bold text-slate-900">Top Search-Intent Combos</h2>
                  {insights.top_combos.map((c: any) => (
                    <div key={c.combo} className="flex justify-between"><span>{c.combo}</span><strong>{c.searches}</strong></div>
                  ))}
                </div>
                <div className="bg-white p-5 rounded-2xl border border-slate-200 space-y-2">
                  <h2 className="font-bold text-slate-900">Smart Filter Popularity</h2>
                  {insights.filter_popularity.map((f: any) => (
                    <div key={f.filter} className="flex justify-between"><span>{f.filter}</span><strong>{f.uses}</strong></div>
                  ))}
                </div>
              </div>
            )}

            <div className="bg-white rounded-2xl border border-slate-200 p-5 overflow-x-auto">
              <h2 className="text-sm font-bold text-slate-900 mb-3">All Recent Runs</h2>
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 uppercase text-[10px]">
                  <tr>
                    <th className="py-2 px-3">Job ID</th>
                    <th className="py-2 px-3">Owner</th>
                    <th className="py-2 px-3">Scope</th>
                    <th className="py-2 px-3">Leads</th>
                    <th className="py-2 px-3">Status</th>
                    <th className="py-2 px-3 text-right">File</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {runs.map((r) => (
                    <tr key={r.id}>
                      <td className="py-2.5 px-3 font-mono">{r.id}</td>
                      <td className="py-2.5 px-3">{r.user_id || r.guest_id || "anon"}</td>
                      <td className="py-2.5 px-3 max-w-xs truncate">{r.states.join(", ")} · {r.categories[0]}</td>
                      <td className="py-2.5 px-3 font-bold text-emerald-700">{r.new_leads}</td>
                      <td className="py-2.5 px-3 capitalize">{r.status}</td>
                      <td className="py-2.5 px-3 text-right">
                        {r.excel_file && (
                          <a href={`/api/jobs/${r.id}/download`} className="text-brand-700 font-bold hover:underline">Excel</a>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 4: LIVE PLAN EDITOR & COUPONS */}
        {tab === "plans" && (
          <div className="space-y-6">
            <div className="bg-white rounded-2xl border border-slate-200 p-5 space-y-4">
              <h2 className="text-sm font-bold text-slate-900">Live Plan Editor (Changes apply immediately)</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {plans.map((p) => (
                  <div key={p.id} className="p-4 rounded-xl border border-slate-200 space-y-2 text-xs">
                    <div className="flex justify-between font-bold text-slate-900">
                      <span>{p.name} ({p.id})</span>
                      <span>₹{p.price_monthly_inr}/mo</span>
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                      <label>Monthly ₹
                        <input
                          type="number"
                          defaultValue={p.price_monthly_inr}
                          onBlur={async (e) => {
                            await apiFetch(`/api/admin/plans/${p.id}`, {
                              method: "PUT",
                              headers: { "Content-Type": "application/json" },
                              body: JSON.stringify({ price_monthly_inr: Number(e.target.value) }),
                            });
                            notify(`Saved ${p.name} monthly price`);
                          }}
                          className="w-full px-2 py-1 border rounded mt-0.5"
                        />
                      </label>
                      <label>Max States
                        <input
                          type="number"
                          defaultValue={p.max_states}
                          onBlur={async (e) => {
                            await apiFetch(`/api/admin/plans/${p.id}`, {
                              method: "PUT",
                              headers: { "Content-Type": "application/json" },
                              body: JSON.stringify({ max_states: Number(e.target.value) }),
                            });
                            notify(`Saved ${p.name} max states`);
                          }}
                          className="w-full px-2 py-1 border rounded mt-0.5"
                        />
                      </label>
                      <label>Leads / Mo
                        <input
                          type="number"
                          defaultValue={p.max_leads_per_month}
                          onBlur={async (e) => {
                            await apiFetch(`/api/admin/plans/${p.id}`, {
                              method: "PUT",
                              headers: { "Content-Type": "application/json" },
                              body: JSON.stringify({ max_leads_per_month: Number(e.target.value) }),
                            });
                            notify(`Saved ${p.name} monthly quota`);
                          }}
                          className="w-full px-2 py-1 border rounded mt-0.5"
                        />
                      </label>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200 p-5 space-y-4 text-xs">
              <h2 className="text-sm font-bold text-slate-900">Coupon Codes</h2>
              <div className="flex items-center space-x-2">
                <input value={newCouponCode} onChange={(e) => setNewCouponCode(e.target.value)} placeholder="SAVE25" className="px-3 py-1.5 border rounded-xl uppercase" />
                <input type="number" value={newCouponPct} onChange={(e) => setNewCouponPct(Number(e.target.value))} className="w-20 px-3 py-1.5 border rounded-xl" />
                <button
                  onClick={async () => {
                    if (!newCouponCode.trim()) return;
                    await apiFetch("/api/admin/coupons", {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({ code: newCouponCode, discount_type: "percent", discount_value: newCouponPct }),
                    });
                    setNewCouponCode("");
                    loadPlansAndCoupons();
                  }}
                  className="px-3.5 py-1.5 bg-brand-600 text-white font-bold rounded-xl"
                >
                  Create % Coupon
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {coupons.map((c) => (
                  <span key={c.id} className="px-3 py-1 rounded-full bg-slate-100 font-bold">
                    {c.code} ({c.discount_value}% off · {c.uses_count}/{c.max_uses} used)
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 5: SEO & BLOG CMS */}
        {tab === "seo" && (
          <div className="space-y-6 text-xs">
            {/* Search Console + Organic Funnel */}
            {gscData && (
              <div className="bg-white rounded-2xl border border-slate-200 p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-sm font-bold text-slate-900">Google Search Console &amp; Organic Funnel</h2>
                  <span className="px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200 font-semibold">
                    {gscData.connected ? "Connected" : "Preview Mode (Env OAuth Ready)"}
                  </span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="p-3 bg-slate-50 rounded-xl"><span className="text-slate-400 block">Clicks</span><strong className="text-lg">{gscData.summary.clicks}</strong></div>
                  <div className="p-3 bg-slate-50 rounded-xl"><span className="text-slate-400 block">Impressions</span><strong className="text-lg">{gscData.summary.impressions.toLocaleString()}</strong></div>
                  <div className="p-3 bg-slate-50 rounded-xl"><span className="text-slate-400 block">Avg CTR</span><strong className="text-lg">{gscData.summary.ctr}%</strong></div>
                  <div className="p-3 bg-slate-50 rounded-xl"><span className="text-slate-400 block">Avg Position</span><strong className="text-lg">{gscData.summary.avg_position}</strong></div>
                </div>
                {organicFunnel && (
                  <p className="text-[11px] text-slate-600">
                    <strong>Organic Funnel:</strong> {organicFunnel.organic_visitors} search visits → {organicFunnel.trial_runs} runs → {organicFunnel.signups} signups → {organicFunnel.paid_conversions} paid.
                  </p>
                )}
              </div>
            )}

            {/* Built-in Site Auditor & Keyword Tracker */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white rounded-2xl border border-slate-200 p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <h2 className="text-sm font-bold text-slate-900">Built-in SEO Site Auditor</h2>
                  <button
                    onClick={async () => {
                      const res = await apiFetch("/api/admin/seo/audit", { method: "POST" });
                      if (res.ok) setAuditResult(await res.json());
                      notify("Site audit complete.");
                    }}
                    className="px-3 py-1.5 bg-brand-600 text-white font-bold rounded-xl"
                  >
                    Run Audit Now
                  </button>
                </div>
                {auditResult && (
                  <div className="space-y-2">
                    <p>Health Score: <strong className="text-emerald-700 text-base">{auditResult.health_score}/100</strong> ({auditResult.pages_scanned} pages scanned)</p>
                    {auditResult.issues.length === 0 ? (
                      <p className="text-emerald-700 font-semibold">No critical SEO issues found!</p>
                    ) : (
                      auditResult.issues.map((iss: any, i: number) => (
                        <div key={i} className="p-2 rounded bg-rose-50 border border-rose-200">
                          <strong>[{iss.severity}] {iss.url}</strong>: {iss.issue} — <em>{iss.fix}</em>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>

              <div className="bg-white rounded-2xl border border-slate-200 p-5 space-y-3">
                <h2 className="text-sm font-bold text-slate-900">Keyword Rank Tracker</h2>
                <div className="flex gap-2">
                  <input value={kwInput} onChange={(e) => setKwInput(e.target.value)} placeholder="Target keyword" className="flex-1 px-2.5 py-1.5 border rounded-xl" />
                  <input value={kwUrl} onChange={(e) => setKwUrl(e.target.value)} placeholder="/target-url" className="w-36 px-2.5 py-1.5 border rounded-xl" />
                  <button
                    onClick={async () => {
                      if (!kwInput) return;
                      await apiFetch("/api/admin/seo/keywords", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ keyword: kwInput, target_url: kwUrl }),
                      });
                      setKwInput("");
                      loadSeoAndBlog();
                    }}
                    className="px-3 py-1.5 bg-slate-900 text-white font-bold rounded-xl"
                  >
                    Track
                  </button>
                </div>
                <div className="space-y-1 max-h-36 overflow-y-auto">
                  {kwList.map((k) => (
                    <div key={k.id} className="flex justify-between py-1 border-b border-slate-100">
                      <span><strong>{k.keyword}</strong> ({k.target_url})</span>
                      <span>Pos: {k.current_position || "Tracking"}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Blog CMS & Live SEO Score */}
            <div className="bg-white rounded-2xl border border-slate-200 p-5 space-y-4">
              <h2 className="text-sm font-bold text-slate-900">Blog Editor &amp; Live SEO Checklist ({blogPosts.length} Posts)</h2>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                <input value={newPostTitle} onChange={(e) => setNewPostTitle(e.target.value)} placeholder="Article Title" className="px-3 py-2 border rounded-xl" />
                <input value={newPostSlug} onChange={(e) => setNewPostSlug(e.target.value)} placeholder="url-slug-here" className="px-3 py-2 border rounded-xl" />
                <input value={newPostKw} onChange={(e) => setNewPostKw(e.target.value)} placeholder="Focus Keyword" className="px-3 py-2 border rounded-xl" />
              </div>
              <textarea rows={4} value={newPostBody} onChange={(e) => setNewPostBody(e.target.value)} placeholder="Markdown / MDX article content (## Heading)..." className="w-full p-3 border rounded-xl font-mono" />
              <div className="flex items-center space-x-2">
                <button
                  onClick={async () => {
                    const res = await apiFetch("/api/admin/blog/seo-score", {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({ title: newPostTitle, slug: newPostSlug, focus_keyword: newPostKw, content_md: newPostBody }),
                    });
                    if (res.ok) setSeoScorePreview(await res.json());
                  }}
                  className="px-3.5 py-2 bg-slate-100 font-bold rounded-xl"
                >
                  Check SEO Score
                </button>
                <button
                  onClick={async () => {
                    if (!newPostTitle || !newPostSlug) return;
                    await apiFetch("/api/admin/blog", {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({ title: newPostTitle, slug: newPostSlug, focus_keyword: newPostKw, content_md: newPostBody, status: "published" }),
                    });
                    setNewPostTitle(""); setNewPostSlug(""); setNewPostBody("");
                    notify("Blog post published.");
                    loadSeoAndBlog();
                  }}
                  className="px-4 py-2 bg-brand-600 text-white font-bold rounded-xl"
                >
                  Publish Post
                </button>
              </div>
              {seoScorePreview && (
                <div className="p-3 bg-slate-50 rounded-xl border space-y-1">
                  <p className="font-bold">SEO Score: {seoScorePreview.score}/100 ({seoScorePreview.word_count} words)</p>
                  <div className="flex flex-wrap gap-2">
                    {seoScorePreview.checks.map((c: any, idx: number) => (
                      <span key={idx} className={`px-2 py-0.5 rounded ${c.passed ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"}`}>
                        {c.passed ? "✓" : "✗"} {c.item}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="divide-y divide-slate-100 max-h-56 overflow-y-auto">
                {blogPosts.map((p) => (
                  <div key={p.id} className="py-2 flex items-center justify-between">
                    <div>
                      <span className="font-bold text-slate-900">{p.title}</span>
                      <span className="block text-[11px] text-slate-400">/blog/{p.slug} · {p.word_count} words · {p.views_count} views</span>
                    </div>
                    <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 font-semibold capitalize">{p.status}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 6: TESTING TOOLS, FLAGS, SETTINGS & SYSTEM CHECKS */}
        {tab === "testing" && (
          <div className="space-y-5 text-xs">
            {/* System Checks */}
            {sysChecks && (
              <div className="bg-white rounded-2xl border border-slate-200 p-5 space-y-3">
                <h2 className="text-sm font-bold text-slate-900">System Health Checks</h2>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {Object.entries(sysChecks).map(([k, v]: any) => (
                    <div key={k} className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center space-x-2">
                      <CheckCircle2 className={`w-4 h-4 ${v.status === "green" ? "text-emerald-600" : "text-rose-600"}`} />
                      <div>
                        <p className="font-bold capitalize">{k}</p>
                        <p className="text-[11px] text-slate-500">{v.detail}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Quick Testing Actions */}
            <div className="bg-white rounded-2xl border border-slate-200 p-5 space-y-4">
              <h2 className="text-sm font-bold text-slate-900">Owner Testing Tools</h2>
              <div className="flex flex-wrap gap-2 items-center">
                <button
                  onClick={async () => {
                    await apiFetch("/api/admin/test/reset-my-guest", { method: "POST" });
                    notify("Guest trial counter reset to 0.");
                  }}
                  className="px-3.5 py-2 bg-amber-100 text-amber-900 font-bold rounded-xl inline-flex items-center space-x-1.5"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Reset My Guest Counter</span>
                </button>

                <input
                  value={newUserEmail}
                  onChange={(e) => setNewUserEmail(e.target.value)}
                  placeholder="testuser@leadharvest.in"
                  className="px-3 py-2 border rounded-xl"
                />
                <select value={newUserPlan} onChange={(e) => setNewUserPlan(e.target.value)} className="px-3 py-2 border rounded-xl">
                  <option value="free">Free</option>
                  <option value="starter">Starter</option>
                  <option value="pro">Pro</option>
                  <option value="agency">Agency</option>
                </select>
                <button
                  onClick={async () => {
                    if (!newUserEmail) return;
                    await apiFetch("/api/admin/test/create-user", {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({ email: newUserEmail, plan_id: newUserPlan }),
                    });
                    notify(`Created ${newUserEmail} on ${newUserPlan} (password: TestPass123!)`);
                    setNewUserEmail("");
                  }}
                  className="px-3.5 py-2 bg-brand-600 text-white font-bold rounded-xl"
                >
                  Create Test User
                </button>
              </div>
            </div>

            {/* Feature Flags & CMS Settings */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white rounded-2xl border border-slate-200 p-5 space-y-3">
                <h2 className="text-sm font-bold text-slate-900">Feature Flags</h2>
                {flags.map((f) => (
                  <label key={f.key} className="flex items-center justify-between p-2 rounded-lg bg-slate-50 cursor-pointer">
                    <span><strong>{f.key}</strong><span className="block text-[11px] text-slate-400">{f.description}</span></span>
                    <input
                      type="checkbox"
                      checked={f.enabled}
                      onChange={async (e) => {
                        await apiFetch(`/api/admin/flags/${f.key}?enabled=${e.target.checked}`, { method: "PUT" });
                        loadTestingTools();
                      }}
                    />
                  </label>
                ))}
              </div>

              <div className="bg-white rounded-2xl border border-slate-200 p-5 space-y-3">
                <h2 className="text-sm font-bold text-slate-900">Site Settings &amp; Copy</h2>
                {settingsList.map((s) => (
                  <div key={s.key}>
                    <label className="font-bold text-slate-700">{s.key}</label>
                    <input
                      defaultValue={s.value}
                      onBlur={async (e) => {
                        await apiFetch("/api/admin/settings", {
                          method: "PUT",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({ [s.key]: e.target.value }),
                        });
                        notify(`Saved ${s.key}`);
                      }}
                      className="w-full px-2.5 py-1.5 border rounded-lg mt-0.5"
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Audit Log */}
            <div className="bg-white rounded-2xl border border-slate-200 p-5 space-y-2">
              <h2 className="text-sm font-bold text-slate-900">Recent Admin Audit Logs</h2>
              <div className="max-h-48 overflow-y-auto divide-y divide-slate-100">
                {auditLogs.map((a) => (
                  <div key={a.id} className="py-1.5 flex justify-between text-[11px]">
                    <span><strong>{a.actor_email}</strong> → {a.action} ({a.target_type}:{a.target_id})</span>
                    <span className="text-slate-400">{new Date(a.created_at).toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
