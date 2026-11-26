"use client";

import React from "react";
import { Play, Check, ShieldCheck, Zap, Sparkles } from "lucide-react";

interface ReviewAndStartProps {
  citiesCount: number;
  categoriesCount: number;
  knownRecordsCount: number;
  rememberLeads: boolean;
  adapterMode: "mock" | "justdial";
  isLoading: boolean;
  onToggleRememberLeads: (val: boolean) => void;
  onSelectAdapterMode: (mode: "mock" | "justdial") => void;
  onStartCollecting: () => Promise<void>;
}

export default function ReviewAndStart({
  citiesCount,
  categoriesCount,
  knownRecordsCount,
  rememberLeads,
  adapterMode,
  isLoading,
  onToggleRememberLeads,
  onSelectAdapterMode,
  onStartCollecting,
}: ReviewAndStartProps) {
  const canStart = citiesCount > 0 && categoriesCount > 0;

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm">
      <div className="pb-4 border-b border-slate-100">
        <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
          <Sparkles className="w-5 h-5 text-brand-600" />
          <span>4. Review & Start Lead Harvest</span>
        </h2>
        <p className="text-sm text-slate-500 mt-0.5">
          One-click collection will search, normalize phone numbers, deduplicate, and build your final Excel.
        </p>
      </div>

      {/* Confirmation Summary Badges */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 my-4">
        <div className="p-3 rounded-xl bg-brand-50/60 border border-brand-200/70">
          <span className="text-[11px] font-semibold uppercase text-brand-700 block">Locations</span>
          <span className="text-xl font-extrabold text-slate-900">{citiesCount}</span>
          <span className="text-xs text-slate-500 ml-1">Odisha cities</span>
        </div>

        <div className="p-3 rounded-xl bg-teal-50/60 border border-teal-200/70">
          <span className="text-[11px] font-semibold uppercase text-teal-700 block">Categories</span>
          <span className="text-xl font-extrabold text-slate-900">{categoriesCount}</span>
          <span className="text-xs text-slate-500 ml-1">business niches</span>
        </div>

        <div className="p-3 rounded-xl bg-amber-50/60 border border-amber-200/70">
          <span className="text-[11px] font-semibold uppercase text-amber-700 block">Deduplication</span>
          <span className="text-xl font-extrabold text-slate-900">{knownRecordsCount.toLocaleString()}</span>
          <span className="text-xs text-slate-500 ml-1">leads to skip</span>
        </div>
      </div>

      {/* Engine & Persistence Options */}
      <div className="space-y-3 pt-2 pb-4">
        {/* Persistence Toggle */}
        <label className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200 cursor-pointer hover:bg-slate-100/70 transition-colors">
          <div className="flex items-center space-x-2.5">
            <ShieldCheck className="w-4 h-4 text-brand-600" />
            <div>
              <p className="text-xs font-bold text-slate-800">Remember this data for next time</p>
              <p className="text-[11px] text-slate-500">
                Automatically add collected leads to your Known Records index so future runs never duplicate them.
              </p>
            </div>
          </div>
          <input
            type="checkbox"
            checked={rememberLeads}
            onChange={(e) => onToggleRememberLeads(e.target.checked)}
            className="w-4 h-4 text-brand-600 rounded border-slate-300 focus:ring-brand-500"
          />
        </label>

        {/* Engine Mode Selector */}
        <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-800 flex items-center space-x-1.5">
              <Zap className="w-3.5 h-3.5 text-amber-600" />
              <span>Collection Engine Mode:</span>
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
            <button
              type="button"
              onClick={() => onSelectAdapterMode("mock")}
              className={`p-2.5 rounded-lg border text-left transition-all ${
                adapterMode === "mock"
                  ? "bg-white border-brand-500 ring-2 ring-brand-400/20 shadow-xs"
                  : "bg-white/60 border-slate-200 text-slate-600 hover:bg-white"
              }`}
            >
              <p className="font-bold text-slate-900 flex items-center justify-between">
                <span>Demo / Reliable Engine</span>
                {adapterMode === "mock" && <Check className="w-3.5 h-3.5 text-brand-600" />}
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Instant authentic Odisha dataset across all districts for immediate testing & offline delivery.
              </p>
            </button>

            <button
              type="button"
              onClick={() => onSelectAdapterMode("justdial")}
              className={`p-2.5 rounded-lg border text-left transition-all ${
                adapterMode === "justdial"
                  ? "bg-white border-brand-500 ring-2 ring-brand-400/20 shadow-xs"
                  : "bg-white/60 border-slate-200 text-slate-600 hover:bg-white"
              }`}
            >
              <p className="font-bold text-slate-900 flex items-center justify-between">
                <span>Justdial Live Engine</span>
                {adapterMode === "justdial" && <Check className="w-3.5 h-3.5 text-brand-600" />}
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Playwright async browser scraper with honest pacing and CAPTCHA pause detection.
              </p>
            </button>
          </div>
        </div>
      </div>

      {/* Primary Start Button */}
      <button
        type="button"
        disabled={!canStart || isLoading}
        onClick={onStartCollecting}
        className={`w-full py-4 rounded-xl font-bold text-base flex items-center justify-center space-x-2 shadow-lg transition-all ${
          canStart && !isLoading
            ? "bg-gradient-to-r from-brand-700 via-brand-600 to-teal-600 hover:from-brand-800 hover:to-teal-700 text-white shadow-brand-600/30 hover:scale-[1.01] active:scale-[0.99]"
            : "bg-slate-200 text-slate-400 cursor-not-allowed shadow-none"
        }`}
      >
        <Play className="w-5 h-5 fill-current" />
        <span>{isLoading ? "Starting Collection..." : "Start Collecting"}</span>
      </button>
    </div>
  );
}
