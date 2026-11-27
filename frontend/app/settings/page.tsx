"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Database, Trash2, ArrowLeft, ShieldCheck, MapPin, Layers, Lock } from "lucide-react";
import { apiFetch } from "@/lib/api";

interface KnownStats {
  total_records: number;
  by_city: Record<string, number>;
  by_source: Record<string, number>;
  last_updated?: string;
}

export default function SettingsPage() {
  const [stats, setStats] = useState<KnownStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [locStatus, setLocStatus] = useState<any>(null);
  const [statesList, setStatesList] = useState<Array<{ id: string; name: string }>>([]);
  const [changeTo, setChangeTo] = useState("");
  const [changeReason, setChangeReason] = useState("");
  const [extraSelection, setExtraSelection] = useState<string[]>([]);
  const [stateMsg, setStateMsg] = useState<string | null>(null);

  async function loadStats() {
    try {
      const [res, locRes, stRes] = await Promise.all([
        fetch("/api/known-records/stats"),
        apiFetch("/api/location/status"),
        apiFetch("/api/config/india-locations"),
      ]);
      if (res.ok) setStats(await res.json());
      if (locRes.ok) {
        const ls = await locRes.json();
        setLocStatus(ls);
        setExtraSelection(ls.extra_states || []);
      }
      if (stRes.ok) setStatesList(await stRes.json());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadStats();
  }, []);

  const handleClear = async () => {
    if (!confirm("Are you sure you want to permanently clear all known records? Future runs will not skip these records.")) return;
    try {
      await fetch("/api/known-records", { method: "DELETE" });
      await loadStats();
      alert("Known records index cleared successfully.");
    } catch (e) {
      alert("Failed to clear index.");
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-20">
      <div className="flex items-center justify-between pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 flex items-center space-x-2">
            <Database className="w-6 h-6 text-brand-600" />
            <span>Known Records & Deduplication Index</span>
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Manage your Home State, Starter extra states, and persistent Known Records deduplication index.
          </p>
        </div>

        <Link
          href="/"
          className="px-3.5 py-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-semibold text-xs rounded-xl flex items-center space-x-1.5 transition-colors shadow-xs"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Wizard</span>
        </Link>
      </div>

      {/* My Home State & Starter Extra States */}
      {locStatus && locStatus.actor_type === "user" && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h2 className="text-base font-black text-slate-900 flex items-center space-x-2">
                <MapPin className="w-4 h-4 text-emerald-600" />
                <span>My Home State: {locStatus.home_state || "Unset"}</span>
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                {locStatus.all_india
                  ? "Your plan includes All 36 Indian States & UTs."
                  : locStatus.locked
                  ? "Your Home State is locked. You can request a change once every 90 days."
                  : "Your migrated Home State is unlocked for one free change."}
              </p>
            </div>
            {locStatus.pending_change_request && (
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800">
                Change pending → {locStatus.pending_change_request.to_state}
              </span>
            )}
          </div>

          {stateMsg && (
            <div className="p-3 rounded-xl bg-brand-50 border border-brand-200 text-xs font-semibold text-brand-800">
              {stateMsg}
            </div>
          )}

          {!locStatus.all_india && !locStatus.pending_change_request && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs pt-2 border-t border-slate-100">
              <select value={changeTo} onChange={(e) => setChangeTo(e.target.value)} className="px-3 py-2 rounded-xl border border-slate-200 bg-white">
                <option value="">Request Home State change...</option>
                {statesList.map((s) => <option key={s.id} value={s.name}>{s.name}</option>)}
              </select>
              <input value={changeReason} onChange={(e) => setChangeReason(e.target.value)} placeholder="Reason (e.g. Relocated office)" className="px-3 py-2 rounded-xl border border-slate-200" />
              <button
                type="button"
                onClick={async () => {
                  const r = await apiFetch("/api/location/change-request", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ to_state: changeTo, reason: changeReason }),
                  });
                  const d = await r.json();
                  setStateMsg(r.ok ? d.message : d.detail || "Could not submit change request.");
                  if (r.ok) loadStats();
                }}
                className="px-4 py-2 rounded-xl bg-slate-900 text-white font-bold"
              >
                Request Change
              </button>
            </div>
          )}

          {locStatus.max_extra_slots > 0 && !locStatus.all_india && (
            <div className="pt-4 border-t border-slate-100 space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-800">
                  Starter Extra States ({extraSelection.length} / {locStatus.max_extra_slots} slots used)
                </span>
                <span className="text-slate-500">Editable once every 30 days</span>
              </div>
              <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto">
                {statesList
                  .filter((s) => s.name.toLowerCase() !== (locStatus.home_state || "").toLowerCase())
                  .map((s) => {
                    const active = extraSelection.includes(s.name);
                    return (
                      <button
                        key={s.id}
                        type="button"
                        onClick={() => {
                          if (active) setExtraSelection(extraSelection.filter((x) => x !== s.name));
                          else if (extraSelection.length < locStatus.max_extra_slots) setExtraSelection([...extraSelection, s.name]);
                        }}
                        className={`px-2.5 py-1 rounded-lg text-xs font-semibold border ${
                          active ? "bg-brand-600 text-white border-brand-600" : "bg-slate-50 text-slate-700 border-slate-200"
                        }`}
                      >
                        {s.name}
                      </button>
                    );
                  })}
              </div>
              <button
                type="button"
                onClick={async () => {
                  const r = await apiFetch("/api/location/extra-states", {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ states: extraSelection }),
                  });
                  const d = await r.json();
                  setStateMsg(r.ok ? "Starter extra states saved!" : d.detail || "Could not update extra states.");
                  if (r.ok) loadStats();
                }}
                className="px-4 py-2 rounded-xl bg-brand-600 text-white text-xs font-bold"
              >
                Save Extra States
              </button>
            </div>
          )}
        </div>
      )}

      {loading ? (
        <div className="text-center py-12 text-slate-400 text-sm">Loading index statistics...</div>
      ) : (
        <div className="space-y-6">
          {/* Main Metric Card */}
          <div className="p-6 rounded-2xl bg-gradient-to-tr from-brand-800 to-brand-600 text-white shadow-md flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <span className="text-xs font-semibold uppercase tracking-wider text-brand-200 flex items-center space-x-1.5">
                <ShieldCheck className="w-4 h-4 text-brand-300" />
                <span>Total Indexed Businesses</span>
              </span>
              <p className="text-4xl font-black mt-1">
                {(stats?.total_records || 0).toLocaleString()}
              </p>
              <p className="text-xs text-brand-100 mt-1">
                These records are automatically skipped during every collection run.
              </p>
            </div>

            {(stats?.total_records || 0) > 0 && (
              <button
                type="button"
                onClick={handleClear}
                className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white border border-white/30 text-xs font-bold rounded-xl flex items-center space-x-2 transition-colors self-start sm:self-auto"
              >
                <Trash2 className="w-4 h-4 text-rose-300" />
                <span>Clear All Records</span>
              </button>
            )}
          </div>

          {/* Breakdown by City */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <h2 className="text-sm font-bold text-slate-900 flex items-center space-x-2 mb-4">
              <MapPin className="w-4 h-4 text-brand-600" />
              <span>Records by City / Location</span>
            </h2>

            {stats && Object.keys(stats.by_city).length > 0 ? (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                {Object.entries(stats.by_city).map(([city, count]) => (
                  <div key={city} className="p-2.5 rounded-xl bg-slate-50 border border-slate-200/60 flex items-center justify-between">
                    <span className="font-medium text-slate-700 truncate pr-2">{city}</span>
                    <span className="font-bold text-brand-700">{count}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400">No records indexed yet. Upload past files or complete a run.</p>
            )}
          </div>

          {/* Breakdown by Source */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <h2 className="text-sm font-bold text-slate-900 flex items-center space-x-2 mb-4">
              <Layers className="w-4 h-4 text-brand-600" />
              <span>Records by Origin Source</span>
            </h2>

            {stats && Object.keys(stats.by_source).length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                {Object.entries(stats.by_source).map(([src, count]) => (
                  <div key={src} className="p-3 rounded-xl bg-slate-50 border border-slate-200/60 flex items-center justify-between">
                    <span className="font-semibold text-slate-800 capitalize">
                      {src === "upload" ? "Uploaded Spreadsheet Audit" : "LeadHarvest Scraping Run"}
                    </span>
                    <span className="font-bold text-slate-900">{count.toLocaleString()} leads</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400">No sources indexed yet.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
