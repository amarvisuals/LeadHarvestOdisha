"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Flame, Search, Download, Upload, Plus, RefreshCw, ShieldAlert,
  Sliders, CheckCircle2, Mail, ArrowUpRight, Trash2, Clock, Ban
} from "lucide-react";
import { apiFetch } from "@/lib/api";

type SubTab =
  | "inbound"
  | "public_request"
  | "signal"
  | "kanban"
  | "won"
  | "lost"
  | "sources"
  | "weights"
  | "dnc";

const STAGES = [
  "New",
  "Contacted",
  "Meeting booked",
  "Proposal sent",
  "Negotiation",
  "Won",
  "Lost",
];

export default function HotLeadsSection({ onNotify }: { onNotify: (msg: string) => void }) {
  const [subTab, setSubTab] = useState<SubTab>("inbound");
  const [stats, setStats] = useState<any>(null);
  const [leads, setLeads] = useState<any[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  // Filters & sorting
  const [q, setQ] = useState("");
  const [cityFilter, setCityFilter] = useState("");
  const [catFilter, setCatFilter] = useState("");
  const [minScore, setMinScore] = useState("");
  const [stageFilter, setStageFilter] = useState("");
  const [ownerFilter, setOwnerFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [sortBy, setSortBy] = useState("score");
  const [sortDir, setSortDir] = useState("desc");

  // Sources, weights, DNC
  const [sources, setSources] = useState<any[]>([]);
  const [weights, setWeights] = useState<Record<string, number>>({});
  const [weightLabels, setWeightLabels] = useState<Record<string, string>>({});
  const [dncList, setDncList] = useState<any[]>([]);

  // Forms
  const [srcName, setSrcName] = useState("");
  const [srcKind, setSrcKind] = useState("rss");
  const [srcUrl, setSrcUrl] = useState("");
  const [srcTerms, setSrcTerms] = useState("Public RSS feed within platform terms");
  const [dncPhone, setDncPhone] = useState("");
  const [dncEmail, setDncEmail] = useState("");
  const [dncReason, setDncReason] = useState("Opt-out / DND requested");

  const [newBname, setNewBname] = useState("");
  const [newPhone, setNewPhone] = useState("");
  const [newCity, setNewCity] = useState("");
  const [newBudget, setNewBudget] = useState("Rs 10,000 - Rs 20,000");

  async function loadStats() {
    const res = await apiFetch("/api/admin/hot-leads/stats");
    if (res.ok) setStats(await res.json());
  }

  async function loadLeads() {
    const params = new URLSearchParams();
    if (subTab === "inbound") params.set("source_type", "inbound");
    else if (subTab === "public_request") params.set("source_type", "public_request");
    else if (subTab === "signal") params.set("source_type", "signal");
    else if (subTab === "won") params.set("stage", "Won");
    else if (subTab === "lost") params.set("stage", "Lost");

    if (q) params.set("q", q);
    if (cityFilter) params.set("city", cityFilter);
    if (catFilter) params.set("category", catFilter);
    if (minScore) params.set("min_score", minScore);
    if (stageFilter && subTab !== "won" && subTab !== "lost") params.set("stage", stageFilter);
    if (ownerFilter) params.set("owner", ownerFilter);
    if (dateFrom) params.set("date_from", dateFrom);
    params.set("sort_by", sortBy);
    params.set("sort_dir", sortDir);

    const res = await apiFetch(`/api/admin/hot-leads?${params.toString()}`);
    if (res.ok) {
      const d = await res.json();
      setLeads(d.items || []);
    }
  }

  async function loadExtras() {
    const [sRes, wRes, dRes] = await Promise.all([
      apiFetch("/api/admin/hot-leads/sources"),
      apiFetch("/api/admin/hot-leads/config/weights"),
      apiFetch("/api/admin/hot-leads/dnc"),
    ]);
    if (sRes.ok) setSources(await sRes.json());
    if (wRes.ok) {
      const wd = await wRes.json();
      setWeights(wd.weights || {});
      setWeightLabels(wd.labels || {});
    }
    if (dRes.ok) setDncList(await dRes.json());
  }

  useEffect(() => {
    loadStats();
    loadExtras();
  }, []);

  useEffect(() => {
    if (!["sources", "weights", "dnc"].includes(subTab)) {
      loadLeads();
    }
  }, [subTab, sortBy, sortDir]);

  async function handleBulk(action: string, stage?: string) {
    if (selectedIds.length === 0) return;
    const res = await apiFetch("/api/admin/hot-leads/bulk", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lead_ids: selectedIds, action, stage }),
    });
    if (res.ok) {
      setSelectedIds([]);
      onNotify(`Bulk action '${action}' applied.`);
      loadLeads();
      loadStats();
    }
  }

  async function handleStageMove(leadId: string, stage: string) {
    let lostReason: string | undefined;
    if (stage === "Lost") {
      lostReason = window.prompt("Lost reason (optional):", "Chose another vendor") || "Not specified";
    }
    const res = await apiFetch(`/api/admin/hot-leads/${leadId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ stage, lost_reason: lostReason }),
    });
    if (res.ok) {
      onNotify(`Moved lead to ${stage}`);
      loadLeads();
      loadStats();
    }
  }

  async function handleCsvUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    const res = await apiFetch("/api/admin/hot-leads/import-csv", {
      method: "POST",
      body: fd,
    });
    const d = await res.json();
    if (res.ok) {
      onNotify(`Imported ${d.imported} public requests (${(d.errors || []).length} skipped).`);
      loadLeads();
      loadStats();
    } else {
      onNotify(`CSV error: ${d.detail?.message || d.detail || "Invalid file"}`);
    }
  }

  function tempBadge(temp: string, score: number) {
    if (temp === "Hot") return <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-rose-100 text-rose-700">HOT · {score}</span>;
    if (temp === "Warm") return <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-amber-100 text-amber-800">WARM · {score}</span>;
    return <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-600">COLD · {score}</span>;
  }

  return (
    <div className="space-y-6">
      {/* Header + Actions */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-black text-slate-900 flex items-center space-x-2">
            <Flame className="w-5 h-5 text-rose-600" />
            <span>Hot Leads — Ready-to-Close Pipeline</span>
          </h1>
          <p className="text-xs text-slate-500">
            Compliant inbound quotes, public requests, and LeadHarvest buying-signal leads.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={async () => {
              const r = await apiFetch("/api/admin/hot-leads/reminders/send-digest", { method: "POST" });
              const d = await r.json();
              onNotify(d.sent ? `Reminder digest sent (${d.count} due)` : d.message);
            }}
            className="px-3 py-1.5 rounded-xl bg-white border border-slate-200 text-xs font-bold text-slate-700 hover:bg-slate-50 flex items-center space-x-1"
          >
            <Mail className="w-3.5 h-3.5" />
            <span>Send Due Digest</span>
          </button>
          <a
            href="/api/admin/hot-leads/export?format=csv"
            className="px-3 py-1.5 rounded-xl bg-white border border-slate-200 text-xs font-bold text-slate-700 hover:bg-slate-50 flex items-center space-x-1"
          >
            <Download className="w-3.5 h-3.5" />
            <span>CSV</span>
          </a>
          <a
            href="/api/admin/hot-leads/export?format=xlsx"
            className="px-3 py-1.5 rounded-xl bg-slate-900 text-white text-xs font-bold hover:bg-slate-800 flex items-center space-x-1"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Excel</span>
          </a>
          {stats?.total_leads === 0 && (
            <button
              onClick={async () => {
                const r = await apiFetch("/api/admin/hot-leads/seed-demo", { method: "POST" });
                if (r.ok) {
                  onNotify("Seeded 30 demo Hot Leads.");
                  loadStats();
                  loadLeads();
                  loadExtras();
                }
              }}
              className="px-3 py-1.5 rounded-xl bg-brand-600 text-white text-xs font-bold"
            >
              Seed 30 Demo Leads
            </button>
          )}
        </div>
      </div>

      {/* KPI Dashboard Widgets */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
          <div className="bg-white p-4 rounded-2xl border border-slate-200">
            <span className="text-[10px] font-bold uppercase text-slate-400">New Hot (7d)</span>
            <p className="text-2xl font-black text-rose-600">{stats.new_hot_this_week}</p>
            <span className="text-[11px] text-slate-500">Total: {stats.total_leads} leads</span>
          </div>
          <div className="bg-white p-4 rounded-2xl border border-slate-200">
            <span className="text-[10px] font-bold uppercase text-slate-400">Avg Response</span>
            <p className="text-2xl font-black text-slate-900">{stats.avg_response_hours}h</p>
            <span className="text-[11px] text-slate-500">{stats.overdue_followups} overdue follow-ups</span>
          </div>
          <div className="bg-white p-4 rounded-2xl border border-slate-200">
            <span className="text-[10px] font-bold uppercase text-slate-400">Pipeline Value</span>
            <p className="text-2xl font-black text-brand-700">₹{stats.pipeline_value_inr.toLocaleString()}</p>
            <span className="text-[11px] text-slate-500">Active deals</span>
          </div>
          <div className="bg-white p-4 rounded-2xl border border-slate-200">
            <span className="text-[10px] font-bold uppercase text-slate-400">Revenue Won</span>
            <p className="text-2xl font-black text-emerald-700">₹{stats.revenue_won_inr.toLocaleString()}</p>
            <span className="text-[11px] text-slate-500">{stats.won_count} won / {stats.lost_count} lost</span>
          </div>
          <div className="bg-white p-4 rounded-2xl border border-slate-200">
            <span className="text-[10px] font-bold uppercase text-slate-400">Win Rate by Source</span>
            <div className="text-[11px] mt-1 space-y-0.5 text-slate-700">
              <p>Inbound: <strong>{stats.conversion_by_source?.inbound?.conversion_rate ?? 0}%</strong></p>
              <p>Requests: <strong>{stats.conversion_by_source?.public_request?.conversion_rate ?? 0}%</strong></p>
              <p>Signals: <strong>{stats.conversion_by_source?.signal?.conversion_rate ?? 0}%</strong></p>
            </div>
          </div>
        </div>
      )}

      {/* Sub-Tabs */}
      <div className="flex flex-wrap gap-1.5 border-b border-slate-200 pb-3">
        {[
          { id: "inbound", label: "Inbound" },
          { id: "public_request", label: "Public Requests" },
          { id: "signal", label: "Signal Leads" },
          { id: "kanban", label: "Kanban Pipeline" },
          { id: "won", label: "Won" },
          { id: "lost", label: "Lost" },
          { id: "sources", label: "Sources & CSV Import" },
          { id: "weights", label: "Score Formula" },
          { id: "dnc", label: "Do Not Contact" },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setSubTab(t.id as SubTab)}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-colors ${
              subTab === t.id ? "bg-slate-900 text-white" : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* LIST & FILTER VIEWS */}
      {!["kanban", "sources", "weights", "dnc"].includes(subTab) && (
        <div className="space-y-4">
          {/* Search & Filters */}
          <div className="bg-white p-4 rounded-2xl border border-slate-200 grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2 text-xs">
            <div className="col-span-2 relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search name, phone, email, city..." className="w-full pl-8 pr-3 py-2 rounded-xl border border-slate-200" />
            </div>
            <input value={cityFilter} onChange={(e) => setCityFilter(e.target.value)} placeholder="City" className="px-3 py-2 rounded-xl border border-slate-200" />
            <input value={catFilter} onChange={(e) => setCatFilter(e.target.value)} placeholder="Category" className="px-3 py-2 rounded-xl border border-slate-200" />
            <input type="number" value={minScore} onChange={(e) => setMinScore(e.target.value)} placeholder="Min Score" className="px-3 py-2 rounded-xl border border-slate-200" />
            <select value={stageFilter} onChange={(e) => setStageFilter(e.target.value)} className="px-2 py-2 rounded-xl border border-slate-200 bg-white">
              <option value="">All Stages</option>
              {STAGES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
            <button onClick={loadLeads} className="px-3 py-2 rounded-xl bg-brand-600 text-white font-bold flex items-center justify-center space-x-1">
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Apply</span>
            </button>
          </div>

          {/* Bulk Actions */}
          {selectedIds.length > 0 && (
            <div className="flex flex-wrap items-center gap-2 p-3 rounded-xl bg-amber-50 border border-amber-200 text-xs">
              <span className="font-bold text-amber-900">{selectedIds.length} selected</span>
              <button onClick={() => handleBulk("change_stage", "Contacted")} className="px-2.5 py-1 rounded-lg bg-white border border-amber-300 font-semibold">Mark Contacted</button>
              <button onClick={() => handleBulk("change_stage", "Won")} className="px-2.5 py-1 rounded-lg bg-emerald-600 text-white font-semibold">Mark Won</button>
              <button onClick={() => handleBulk("mark_dnc")} className="px-2.5 py-1 rounded-lg bg-rose-600 text-white font-semibold">Mark DNC</button>
              <button onClick={() => handleBulk("delete")} className="px-2.5 py-1 rounded-lg bg-slate-800 text-white font-semibold">Delete</button>
            </div>
          )}

          {/* Table */}
          <div className="bg-white rounded-2xl border border-slate-200 overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-50 border-b border-slate-200 text-[11px] uppercase text-slate-500">
                <tr>
                  <th className="p-3"><input type="checkbox" onChange={(e) => setSelectedIds(e.target.checked ? leads.map((l) => l.id) : [])} /></th>
                  <th className="p-3 cursor-pointer" onClick={() => { setSortBy("business_name"); setSortDir(sortDir === "asc" ? "desc" : "asc"); }}>Business / Contact</th>
                  <th className="p-3">City &amp; Category</th>
                  <th className="p-3 cursor-pointer" onClick={() => { setSortBy("score"); setSortDir(sortDir === "asc" ? "desc" : "asc"); }}>Score</th>
                  <th className="p-3">Stage</th>
                  <th className="p-3 cursor-pointer" onClick={() => { setSortBy("deal_value_inr"); setSortDir(sortDir === "asc" ? "desc" : "asc"); }}>Value</th>
                  <th className="p-3">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {leads.map((l) => (
                  <tr key={l.id} className="hover:bg-slate-50">
                    <td className="p-3">
                      <input
                        type="checkbox"
                        checked={selectedIds.includes(l.id)}
                        onChange={(e) =>
                          setSelectedIds((prev) => (e.target.checked ? [...prev, l.id] : prev.filter((x) => x !== l.id)))
                        }
                      />
                    </td>
                    <td className="p-3">
                      <div className="font-bold text-slate-900 flex items-center space-x-1.5">
                        <span>{l.business_name}</span>
                        {l.do_not_contact && <span className="px-1.5 py-0.5 rounded bg-rose-100 text-rose-700 text-[10px]">DNC</span>}
                      </div>
                      <div className="text-[11px] text-slate-500">{l.phone || l.email || "No phone"} · {l.source_name}</div>
                    </td>
                    <td className="p-3 text-slate-600">
                      <div>{l.city || "—"}</div>
                      <div className="text-[11px] text-slate-400">{l.business_type || "—"}</div>
                    </td>
                    <td className="p-3">{tempBadge(l.temperature, l.score)}</td>
                    <td className="p-3">
                      <select
                        value={l.stage}
                        onChange={(e) => handleStageMove(l.id, e.target.value)}
                        className="px-2 py-1 rounded-lg border border-slate-200 bg-white text-[11px] font-semibold"
                      >
                        {STAGES.map((s) => <option key={s} value={s}>{s}</option>)}
                      </select>
                    </td>
                    <td className="p-3 font-semibold text-slate-800">₹{(l.deal_value_inr || 0).toLocaleString()}</td>
                    <td className="p-3">
                      <Link
                        href={`/admin/hot-leads/${l.id}`}
                        className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-brand-50 text-brand-700 hover:bg-brand-100 font-bold"
                      >
                        <span>Open</span>
                        <ArrowUpRight className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                ))}
                {leads.length === 0 && (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-slate-400">No leads match these filters.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* KANBAN PIPELINE */}
      {subTab === "kanban" && (
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-7 gap-3 overflow-x-auto">
          {STAGES.map((st) => {
            const colLeads = leads.filter((l) => l.stage === st);
            return (
              <div key={st} className="bg-slate-50 rounded-2xl border border-slate-200 p-3 space-y-2.5 min-w-[200px]">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-black text-slate-800">{st}</span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-white border border-slate-200">{colLeads.length}</span>
                </div>
                <div className="space-y-2">
                  {colLeads.map((l) => (
                    <div key={l.id} className="bg-white p-3 rounded-xl border border-slate-200 shadow-2xs space-y-1.5">
                      <div className="flex items-center justify-between">
                        {tempBadge(l.temperature, l.score)}
                        <span className="text-[10px] font-bold text-slate-500">₹{(l.deal_value_inr || 0).toLocaleString()}</span>
                      </div>
                      <Link href={`/admin/hot-leads/${l.id}`} className="block text-xs font-bold text-slate-900 hover:text-brand-700 truncate">
                        {l.business_name}
                      </Link>
                      <p className="text-[11px] text-slate-500 truncate">{l.city || "India"}</p>
                      <select
                        value={l.stage}
                        onChange={(e) => handleStageMove(l.id, e.target.value)}
                        className="w-full text-[10px] px-2 py-1 rounded-lg border border-slate-200 bg-slate-50"
                      >
                        {STAGES.map((s) => <option key={s} value={s}>{s}</option>)}
                      </select>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* SOURCES, MANUAL ENTRY & CSV IMPORT */}
      {subTab === "sources" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 space-y-4">
            <h2 className="text-sm font-black text-slate-900 flex items-center space-x-2">
              <Upload className="w-4 h-4 text-brand-600" />
              <span>CSV Import (Publicly Posted Requests)</span>
            </h2>
            <p className="text-xs text-slate-500">
              Upload a CSV with columns: <code>business_name, phone, email, city, business_type, budget_range, source_url, terms_note</code>.
            </p>
            <input type="file" accept=".csv" onChange={handleCsvUpload} className="text-xs block w-full" />

            <hr className="border-slate-100" />
            <h3 className="text-xs font-black text-slate-800">Manual Public Request Entry</h3>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <input value={newBname} onChange={(e) => setNewBname(e.target.value)} placeholder="Business Name *" className="px-3 py-2 rounded-xl border border-slate-200" />
              <input value={newPhone} onChange={(e) => setNewPhone(e.target.value)} placeholder="Phone" className="px-3 py-2 rounded-xl border border-slate-200" />
              <input value={newCity} onChange={(e) => setNewCity(e.target.value)} placeholder="City" className="px-3 py-2 rounded-xl border border-slate-200" />
              <input value={newBudget} onChange={(e) => setNewBudget(e.target.value)} placeholder="Budget" className="px-3 py-2 rounded-xl border border-slate-200" />
            </div>
            <button
              onClick={async () => {
                if (!newBname.trim()) return;
                const r = await apiFetch("/api/admin/hot-leads", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ business_name: newBname, phone: newPhone, city: newCity, budget_range: newBudget }),
                });
                if (r.ok) {
                  setNewBname(""); setNewPhone(""); setNewCity("");
                  onNotify("Manual lead added to Hot Leads.");
                  loadStats();
                }
              }}
              className="px-4 py-2 rounded-xl bg-brand-600 text-white text-xs font-bold inline-flex items-center space-x-1"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Lead</span>
            </button>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 space-y-4">
            <h2 className="text-sm font-black text-slate-900">Pluggable Intent Sources</h2>
            <div className="grid grid-cols-1 gap-2 text-xs">
              <input value={srcName} onChange={(e) => setSrcName(e.target.value)} placeholder="Source Name (e.g. Startup RFP RSS)" className="px-3 py-2 rounded-xl border border-slate-200" />
              <div className="flex gap-2">
                <select value={srcKind} onChange={(e) => setSrcKind(e.target.value)} className="px-3 py-2 rounded-xl border border-slate-200 bg-white">
                  <option value="rss">RSS Feed</option>
                  <option value="official_api">Official API</option>
                  <option value="email_alert">Email Alert</option>
                  <option value="manual">Manual</option>
                </select>
                <input value={srcUrl} onChange={(e) => setSrcUrl(e.target.value)} placeholder="Feed URL or API endpoint" className="flex-1 px-3 py-2 rounded-xl border border-slate-200" />
              </div>
              <input value={srcTerms} onChange={(e) => setSrcTerms(e.target.value)} placeholder="Terms-of-use compliance note *" className="px-3 py-2 rounded-xl border border-slate-200" />
              <button
                onClick={async () => {
                  const r = await apiFetch("/api/admin/hot-leads/sources", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ name: srcName, source_kind: srcKind, endpoint_or_query: srcUrl, terms_note: srcTerms }),
                  });
                  if (r.ok) {
                    setSrcName(""); setSrcUrl("");
                    onNotify("Intent source added.");
                    loadExtras();
                  }
                }}
                className="px-4 py-2 rounded-xl bg-slate-900 text-white font-bold w-fit"
              >
                Add Intent Source
              </button>
            </div>
            <div className="space-y-2 pt-2">
              {sources.map((s) => (
                <div key={s.id} className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">
                  <div>
                    <p className="font-bold text-slate-900">{s.name} <span className="text-[10px] uppercase text-brand-700">({s.source_kind})</span></p>
                    <p className="text-[11px] text-slate-500">{s.terms_note}</p>
                  </div>
                  <span className="text-[11px] font-semibold text-slate-600">{s.leads_imported} imported</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* EDITABLE SCORE FORMULA */}
      {subTab === "weights" && (
        <div className="bg-white p-6 rounded-2xl border border-slate-200 space-y-4 max-w-2xl">
          <h2 className="text-sm font-black text-slate-900 flex items-center space-x-2">
            <Sliders className="w-4 h-4 text-brand-600" />
            <span>Hot Lead Score Formula (0–100, Hot 75+ · Warm 50–74 · Cold &lt;50)</span>
          </h2>
          <div className="space-y-2.5 text-xs">
            {Object.entries(weights).map(([k, val]) => (
              <div key={k} className="flex items-center justify-between gap-4 p-2.5 rounded-xl bg-slate-50 border border-slate-200">
                <span className="font-semibold text-slate-700">{weightLabels[k] || k}</span>
                <input
                  type="number"
                  min={0}
                  max={100}
                  value={val}
                  onChange={(e) => setWeights({ ...weights, [k]: Number(e.target.value) })}
                  className="w-20 px-2.5 py-1 rounded-lg border border-slate-300 text-right font-bold"
                />
              </div>
            ))}
          </div>
          <button
            onClick={async () => {
              const r = await apiFetch("/api/admin/hot-leads/config/weights", {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(weights),
              });
              if (r.ok) {
                const d = await r.json();
                onNotify(`Score weights saved & recomputed across ${d.recomputed_leads} leads.`);
                loadLeads();
              }
            }}
            className="px-5 py-2.5 rounded-xl bg-brand-600 text-white text-xs font-bold"
          >
            Save &amp; Recompute All Lead Scores
          </button>
        </div>
      )}

      {/* DO NOT CONTACT LIST */}
      {subTab === "dnc" && (
        <div className="bg-white p-6 rounded-2xl border border-slate-200 space-y-4 max-w-2xl">
          <h2 className="text-sm font-black text-slate-900 flex items-center space-x-2">
            <Ban className="w-4 h-4 text-rose-600" />
            <span>Do Not Contact (DNC / Opt-Out) List</span>
          </h2>
          <p className="text-xs text-slate-500">
            Leads matching any phone or email here are automatically blocked from WhatsApp/email outreach actions.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
            <input value={dncPhone} onChange={(e) => setDncPhone(e.target.value)} placeholder="Phone (10-digit)" className="px-3 py-2 rounded-xl border border-slate-200" />
            <input value={dncEmail} onChange={(e) => setDncEmail(e.target.value)} placeholder="Email" className="px-3 py-2 rounded-xl border border-slate-200" />
            <input value={dncReason} onChange={(e) => setDncReason(e.target.value)} placeholder="Reason" className="px-3 py-2 rounded-xl border border-slate-200" />
          </div>
          <button
            onClick={async () => {
              const r = await apiFetch("/api/admin/hot-leads/dnc", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ phone: dncPhone || null, email: dncEmail || null, reason: dncReason }),
              });
              if (r.ok) {
                setDncPhone(""); setDncEmail("");
                onNotify("Added to Do Not Contact list.");
                loadExtras();
                loadLeads();
              }
            }}
            className="px-4 py-2 rounded-xl bg-rose-600 text-white text-xs font-bold"
          >
            Add to DNC List
          </button>

          <div className="divide-y divide-slate-100 text-xs pt-2">
            {dncList.map((d) => (
              <div key={d.id} className="py-2.5 flex items-center justify-between">
                <div>
                  <p className="font-bold text-slate-900">{d.phone_clean || d.email}</p>
                  <p className="text-[11px] text-slate-500">{d.reason} · {d.source}</p>
                </div>
                <button
                  onClick={async () => {
                    await apiFetch(`/api/admin/hot-leads/dnc/${d.id}`, { method: "DELETE" });
                    loadExtras();
                  }}
                  className="text-rose-600 hover:underline font-semibold"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
