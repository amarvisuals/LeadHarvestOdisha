"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Database, Trash2, ArrowLeft, ShieldCheck, MapPin, Layers } from "lucide-react";

interface KnownStats {
  total_records: number;
  by_city: Record<string, number>;
  by_source: Record<string, number>;
  last_updated?: string;
}

export default function SettingsPage() {
  const [stats, setStats] = useState<KnownStats | null>(null);
  const [loading, setLoading] = useState(true);

  async function loadStats() {
    try {
      const res = await fetch("/api/known-records/stats");
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
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
            Manage your persistent database of existing businesses across Odisha.
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
