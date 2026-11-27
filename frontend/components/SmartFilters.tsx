"use client";

import React from "react";
import Link from "next/link";
import { Filter, Lock, Sparkles, Globe, PhoneCall, Star, ShieldCheck, Info } from "lucide-react";

export interface SmartFiltersState {
  no_website: boolean;
  has_website: boolean;
  mobile_only: boolean;
  has_email: boolean;
  verified_only: boolean;
  has_social_only: boolean;
  exclude_chains: boolean;
  min_rating: number | "";
  max_rating: number | "";
  min_reviews: number | "";
  max_reviews: number | "";
  min_opportunity_score: number;
}

export interface PitchPreset {
  id: string;
  name: string;
  description: string;
  badge: string;
  filters: Record<string, any>;
}

interface SmartFiltersProps {
  filters: SmartFiltersState;
  pitchPresets: PitchPreset[];
  allowBasicAdvanced: boolean;
  allowAllFilters: boolean;
  adapterCapabilities: Record<string, boolean>;
  onChange: (next: SmartFiltersState) => void;
}

export const EMPTY_FILTERS: SmartFiltersState = {
  no_website: false,
  has_website: false,
  mobile_only: false,
  has_email: false,
  verified_only: false,
  has_social_only: false,
  exclude_chains: false,
  min_rating: "",
  max_rating: "",
  min_reviews: "",
  max_reviews: "",
  min_opportunity_score: 0,
};

export default function SmartFilters({
  filters,
  pitchPresets,
  allowBasicAdvanced,
  allowAllFilters,
  adapterCapabilities,
  onChange,
}: SmartFiltersProps) {
  const applyPreset = (preset: PitchPreset) => {
    if (!allowBasicAdvanced) return;
    const f = preset.filters;
    onChange({
      ...EMPTY_FILTERS,
      no_website: Boolean(f.no_website),
      has_website: Boolean(f.has_website),
      mobile_only: Boolean(f.mobile_only),
      min_rating: f.min_rating ?? "",
      max_rating: f.max_rating ?? "",
      min_reviews: f.min_reviews ?? "",
      max_reviews: f.max_reviews ?? "",
      min_opportunity_score: allowAllFilters ? (f.min_opportunity_score ?? 0) : 0,
    });
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-3">
        <div>
          <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
            <Filter className="w-5 h-5 text-brand-600" />
            <span>3. Smart Lead Filters (&ldquo;Find Real Leads&rdquo;)</span>
          </h2>
          <p className="text-sm text-slate-500 mt-0.5">
            Filter out low-value listings and target businesses ready to buy your services.
          </p>
        </div>

        {!allowBasicAdvanced && (
          <Link
            href="/pricing"
            className="px-3 py-1.5 rounded-xl bg-amber-50 text-amber-800 border border-amber-200 text-xs font-bold flex items-center space-x-1.5 hover:bg-amber-100 shrink-0"
          >
            <Lock className="w-3.5 h-3.5" />
            <span>Unlock Paid Filters</span>
          </Link>
        )}
      </div>

      {/* Ready-made Pitch Presets */}
      <div>
        <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
          One-Click Pitch Presets
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
          {pitchPresets.map((preset) => (
            <button
              key={preset.id}
              type="button"
              disabled={!allowBasicAdvanced}
              onClick={() => applyPreset(preset)}
              className={`p-3 rounded-xl border text-left transition-all ${
                allowBasicAdvanced
                  ? "bg-slate-50/70 hover:bg-brand-50/50 border-slate-200 hover:border-brand-300"
                  : "bg-slate-50 border-slate-200 opacity-60 cursor-not-allowed"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold text-slate-900">{preset.name}</span>
                <span className="px-1.5 py-0.5 text-[10px] font-bold rounded bg-brand-100 text-brand-800">
                  {preset.badge}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 leading-snug">{preset.description}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Flagship "No Website" Highlight */}
      <div
        className={`p-4 rounded-xl border-2 transition-all flex items-center justify-between ${
          filters.no_website
            ? "bg-brand-50/80 border-brand-500"
            : "bg-gradient-to-r from-brand-50/40 to-amber-50/40 border-brand-200"
        }`}
      >
        <div className="flex items-start space-x-3">
          <div className="p-2 rounded-lg bg-brand-600 text-white shrink-0">
            <Globe className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-bold text-slate-900">No Website Listed</span>
              <span className="px-2 py-0.5 text-[10px] font-bold bg-amber-100 text-amber-800 rounded-full">
                Perfect for web design agencies
              </span>
            </div>
            <p className="text-xs text-slate-600 mt-0.5">
              Only collect businesses that do not have a website yet — your highest-converting web design prospects.
            </p>
          </div>
        </div>
        <input
          type="checkbox"
          disabled={!allowBasicAdvanced}
          checked={filters.no_website}
          onChange={(e) =>
            onChange({
              ...filters,
              no_website: e.target.checked,
              has_website: e.target.checked ? false : filters.has_website,
            })
          }
          className="w-5 h-5 text-brand-600 rounded border-slate-300 cursor-pointer"
        />
      </div>

      {/* Filter Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 text-xs">
        <label className={`p-3 rounded-xl border flex items-center justify-between ${!allowBasicAdvanced ? "opacity-60" : "cursor-pointer hover:bg-slate-50"}`}>
          <span className="font-semibold text-slate-700 flex items-center space-x-1.5">
            <PhoneCall className="w-3.5 h-3.5 text-brand-600" />
            <span>Mobile / WhatsApp Only</span>
          </span>
          <input
            type="checkbox"
            disabled={!allowBasicAdvanced}
            checked={filters.mobile_only}
            onChange={(e) => onChange({ ...filters, mobile_only: e.target.checked })}
            className="w-4 h-4 text-brand-600 rounded"
          />
        </label>

        <label className={`p-3 rounded-xl border flex items-center justify-between ${!allowBasicAdvanced ? "opacity-60" : "cursor-pointer hover:bg-slate-50"}`}>
          <span className="font-semibold text-slate-700">Has Website (SEO Pitch)</span>
          <input
            type="checkbox"
            disabled={!allowBasicAdvanced}
            checked={filters.has_website}
            onChange={(e) =>
              onChange({
                ...filters,
                has_website: e.target.checked,
                no_website: e.target.checked ? false : filters.no_website,
              })
            }
            className="w-4 h-4 text-brand-600 rounded"
          />
        </label>

        <label
          title={!adapterCapabilities.email ? "Not supported by selected live source" : ""}
          className={`p-3 rounded-xl border flex items-center justify-between ${
            !allowAllFilters || !adapterCapabilities.email ? "opacity-50 cursor-not-allowed" : "cursor-pointer hover:bg-slate-50"
          }`}
        >
          <span className="font-semibold text-slate-700 flex items-center space-x-1">
            {!allowAllFilters && <Lock className="w-3 h-3 text-amber-500" />}
            <span>Has Email</span>
          </span>
          <input
            type="checkbox"
            disabled={!allowAllFilters || !adapterCapabilities.email}
            checked={filters.has_email}
            onChange={(e) => onChange({ ...filters, has_email: e.target.checked })}
            className="w-4 h-4 text-brand-600 rounded"
          />
        </label>

        <label className={`p-3 rounded-xl border flex items-center justify-between ${!allowAllFilters ? "opacity-50" : "cursor-pointer hover:bg-slate-50"}`}>
          <span className="font-semibold text-slate-700 flex items-center space-x-1">
            {!allowAllFilters && <Lock className="w-3 h-3 text-amber-500" />}
            <span>Verified Listings Only</span>
          </span>
          <input
            type="checkbox"
            disabled={!allowAllFilters}
            checked={filters.verified_only}
            onChange={(e) => onChange({ ...filters, verified_only: e.target.checked })}
            className="w-4 h-4 text-brand-600 rounded"
          />
        </label>

        <label
          title={!adapterCapabilities.social_only ? "Not supported by selected live source" : ""}
          className={`p-3 rounded-xl border flex items-center justify-between ${
            !allowAllFilters || !adapterCapabilities.social_only ? "opacity-50 cursor-not-allowed" : "cursor-pointer hover:bg-slate-50"
          }`}
        >
          <span className="font-semibold text-slate-700 flex items-center space-x-1">
            {!allowAllFilters && <Lock className="w-3 h-3 text-amber-500" />}
            <span>Social Profile Only</span>
          </span>
          <input
            type="checkbox"
            disabled={!allowAllFilters || !adapterCapabilities.social_only}
            checked={filters.has_social_only}
            onChange={(e) => onChange({ ...filters, has_social_only: e.target.checked })}
            className="w-4 h-4 text-brand-600 rounded"
          />
        </label>

        <label className={`p-3 rounded-xl border flex items-center justify-between ${!allowAllFilters ? "opacity-50" : "cursor-pointer hover:bg-slate-50"}`}>
          <span className="font-semibold text-slate-700 flex items-center space-x-1">
            {!allowAllFilters && <Lock className="w-3 h-3 text-amber-500" />}
            <span>Exclude Chains/Franchises</span>
          </span>
          <input
            type="checkbox"
            disabled={!allowAllFilters}
            checked={filters.exclude_chains}
            onChange={(e) => onChange({ ...filters, exclude_chains: e.target.checked })}
            className="w-4 h-4 text-brand-600 rounded"
          />
        </label>
      </div>

      {/* Rating, Reviews & Opportunity Score Slider */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-slate-100 text-xs">
        <div className="space-y-2">
          <span className="font-semibold text-slate-700 flex items-center space-x-1">
            <Star className="w-3.5 h-3.5 text-amber-500" />
            <span>Rating &amp; Review Count Range</span>
          </span>
          <div className="grid grid-cols-4 gap-2">
            <input
              type="number"
              step="0.1"
              min="0"
              max="5"
              disabled={!allowBasicAdvanced}
              value={filters.min_rating}
              onChange={(e) => onChange({ ...filters, min_rating: e.target.value ? Number(e.target.value) : "" })}
              placeholder="Min ★"
              className="px-2 py-1.5 bg-slate-50 border border-slate-200 rounded-lg"
            />
            <input
              type="number"
              step="0.1"
              min="0"
              max="5"
              disabled={!allowBasicAdvanced}
              value={filters.max_rating}
              onChange={(e) => onChange({ ...filters, max_rating: e.target.value ? Number(e.target.value) : "" })}
              placeholder="Max ★"
              className="px-2 py-1.5 bg-slate-50 border border-slate-200 rounded-lg"
            />
            <input
              type="number"
              min="0"
              disabled={!allowAllFilters}
              value={filters.min_reviews}
              onChange={(e) => onChange({ ...filters, min_reviews: e.target.value ? Number(e.target.value) : "" })}
              placeholder="Min Rev"
              className="px-2 py-1.5 bg-slate-50 border border-slate-200 rounded-lg"
            />
            <input
              type="number"
              min="0"
              disabled={!allowAllFilters}
              value={filters.max_reviews}
              onChange={(e) => onChange({ ...filters, max_reviews: e.target.value ? Number(e.target.value) : "" })}
              placeholder="Max Rev"
              className="px-2 py-1.5 bg-slate-50 border border-slate-200 rounded-lg"
            />
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span
              className="font-semibold text-slate-700 flex items-center space-x-1"
              title="Formula: No Website (+40) + Mobile (+20) + Low Reviews <50 (+15) + Good Rating (+15) + Full Address (+10)"
            >
              <Sparkles className="w-3.5 h-3.5 text-brand-600" />
              <span>Min Opportunity Score: <strong className="text-brand-700">{filters.min_opportunity_score}/100</strong></span>
              <Info className="w-3 h-3 text-slate-400" />
            </span>
            {!allowAllFilters && <span className="text-[10px] font-bold text-amber-700">Pro Feature</span>}
          </div>
          <input
            type="range"
            min={0}
            max={100}
            step={10}
            disabled={!allowAllFilters}
            value={filters.min_opportunity_score}
            onChange={(e) => onChange({ ...filters, min_opportunity_score: Number(e.target.value) })}
            className="w-full accent-brand-600"
          />
        </div>
      </div>
    </div>
  );
}
