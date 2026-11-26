"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Download, History, ArrowLeft, CheckCircle2, Clock, XCircle, AlertCircle } from "lucide-react";

interface HistoryJob {
  id: string;
  status: string;
  adapter_name: string;
  cities: string[];
  categories: string[];
  total_found: number;
  duplicates_skipped: number;
  new_leads: number;
  excel_file?: string;
  started_at?: string;
  completed_at?: string;
}

export default function HistoryPage() {
  const [jobs, setJobs] = useState<HistoryJob[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadHistory() {
      try {
        const res = await fetch("/api/history");
        if (res.ok) {
          const data = await res.json();
          setJobs(data);
        }
      } catch (e) {
        console.error("Failed to load history:", e);
      } finally {
        setLoading(false);
      }
    }
    loadHistory();
  }, []);

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-20">
      <div className="flex items-center justify-between pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 flex items-center space-x-2">
            <History className="w-6 h-6 text-brand-600" />
            <span>Collection History</span>
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            View all past lead harvesting runs and re-download your Excel workbooks.
          </p>
        </div>

        <Link
          href="/"
          className="px-3.5 py-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-semibold text-xs rounded-xl flex items-center space-x-1.5 transition-colors shadow-xs"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>New Collection</span>
        </Link>
      </div>

      {loading ? (
        <div className="text-center py-12 text-slate-400 text-sm">Loading past runs...</div>
      ) : jobs.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-2xl border border-slate-200/80 p-8 space-y-3">
          <p className="text-base font-bold text-slate-700">No collection jobs yet</p>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Once you launch your first lead collection, details and re-download links will appear here.
          </p>
          <Link
            href="/"
            className="inline-flex items-center space-x-1.5 px-4 py-2 bg-brand-600 text-white font-bold text-xs rounded-xl shadow-sm"
          >
            <span>Start Your First Run</span>
          </Link>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-600 uppercase font-semibold text-[10px]">
                  <th className="py-3 px-4">Date & Time</th>
                  <th className="py-3 px-4">Locations & Categories</th>
                  <th className="py-3 px-4 text-center">Found</th>
                  <th className="py-3 px-4 text-center">Skipped</th>
                  <th className="py-3 px-4 text-center">New Leads</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-right">Download</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {jobs.map((job) => {
                  const dateStr = job.started_at ? new Date(job.started_at).toLocaleString() : "Recent";
                  const isDone = job.status === "completed";
                  const isCancelled = job.status === "cancelled";

                  return (
                    <tr key={job.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="py-3.5 px-4 font-medium text-slate-900 whitespace-nowrap">
                        {dateStr}
                        <span className="block text-[10px] text-slate-400 font-mono">{job.id}</span>
                      </td>

                      <td className="py-3.5 px-4 max-w-xs truncate">
                        <span className="font-semibold text-slate-800">{job.cities.slice(0, 2).join(", ")}</span>
                        {job.cities.length > 2 && <span className="text-slate-400"> +{job.cities.length - 2} more</span>}
                        <span className="block text-[11px] text-slate-500 truncate">
                          {job.categories.slice(0, 2).join(", ")}
                          {job.categories.length > 2 ? ` +${job.categories.length - 2} more` : ""}
                        </span>
                      </td>

                      <td className="py-3.5 px-4 text-center font-bold text-slate-700">
                        {job.total_found.toLocaleString()}
                      </td>

                      <td className="py-3.5 px-4 text-center font-bold text-amber-700">
                        {job.duplicates_skipped.toLocaleString()}
                      </td>

                      <td className="py-3.5 px-4 text-center font-bold text-emerald-700">
                        {job.new_leads.toLocaleString()}
                      </td>

                      <td className="py-3.5 px-4 text-center">
                        <span
                          className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                            isDone
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                              : isCancelled
                              ? "bg-slate-100 text-slate-700 border border-slate-200"
                              : "bg-amber-50 text-amber-700 border border-amber-200"
                          }`}
                        >
                          {isDone ? <CheckCircle2 className="w-3 h-3" /> : <Clock className="w-3 h-3" />}
                          <span className="capitalize">{job.status}</span>
                        </span>
                      </td>

                      <td className="py-3.5 px-4 text-right whitespace-nowrap">
                        {job.excel_file ? (
                          <a
                            href={`/api/jobs/${job.id}/download`}
                            download
                            className="inline-flex items-center space-x-1 px-3 py-1.5 bg-brand-50 hover:bg-brand-100 text-brand-700 font-bold rounded-lg border border-brand-200 transition-colors"
                          >
                            <Download className="w-3.5 h-3.5" />
                            <span>Excel</span>
                          </a>
                        ) : (
                          <span className="text-slate-400 text-[11px]">Not ready</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
