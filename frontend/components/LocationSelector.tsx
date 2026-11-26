"use client";

import React, { useState, useMemo } from "react";
import { Search, CheckSquare, Square, X, MapPin } from "lucide-react";

export interface LocationItem {
  id: string;
  name: string;
  district: string;
  tier: string;
  pincode_prefix: string;
}

interface LocationSelectorProps {
  locations: LocationItem[];
  selectedCities: string[];
  onChange: (selected: string[]) => void;
}

export default function LocationSelector({
  locations,
  selectedCities,
  onChange,
}: LocationSelectorProps) {
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    if (!search.trim()) return locations;
    const q = search.toLowerCase();
    return locations.filter(
      (l) =>
        l.name.toLowerCase().includes(q) ||
        l.district.toLowerCase().includes(q) ||
        l.tier.toLowerCase().includes(q)
    );
  }, [locations, search]);

  const allSelected = locations.length > 0 && selectedCities.length === locations.length;

  const handleToggleAll = () => {
    if (allSelected) {
      onChange([]);
    } else {
      onChange(locations.map((l) => l.name));
    }
  };

  const handleToggleCity = (name: string) => {
    if (selectedCities.includes(name)) {
      onChange(selectedCities.filter((c) => c !== name));
    } else {
      onChange([...selectedCities, name]);
    }
  };

  const handleClear = () => {
    onChange([]);
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-3">
        <div>
          <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
            <MapPin className="w-5 h-5 text-brand-600" />
            <span>1. Select Odisha Locations</span>
          </h2>
          <p className="text-sm text-slate-500 mt-0.5">
            Choose districts or commercial centers. Default includes all Odisha.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={handleToggleAll}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 border transition-all ${
              allSelected
                ? "bg-brand-50 text-brand-700 border-brand-300"
                : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
            }`}
          >
            {allSelected ? <CheckSquare className="w-4 h-4 text-brand-600" /> : <Square className="w-4 h-4" />}
            <span>{allSelected ? "All Odisha Selected" : "Select All Odisha"}</span>
          </button>

          {selectedCities.length > 0 && (
            <button
              type="button"
              onClick={handleClear}
              className="px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-500 hover:text-rose-600 hover:bg-rose-50 border border-slate-200 transition-colors"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Search Input */}
      <div className="relative mt-4 mb-3">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by city, district (e.g. Bhubaneswar, Cuttack, Ganjam)..."
          className="w-full pl-10 pr-4 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-colors"
        />
        {search && (
          <button
            onClick={() => setSearch("")}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Selected Counter & Chips preview */}
      <div className="flex items-center justify-between text-xs text-slate-500 mb-3 px-1">
        <span>
          <strong className="text-brand-700 font-semibold">{selectedCities.length}</strong> of{" "}
          {locations.length} locations selected
        </span>
        {selectedCities.length === 0 && (
          <span className="text-amber-600 font-medium">Please select at least one city</span>
        )}
      </div>

      {/* Locations Grid */}
      <div className="max-h-64 overflow-y-auto pr-1 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
        {filtered.map((loc) => {
          const isChecked = selectedCities.includes(loc.name);
          return (
            <div
              key={loc.id}
              onClick={() => handleToggleCity(loc.name)}
              className={`p-2.5 rounded-xl border cursor-pointer select-none transition-all flex items-center justify-between ${
                isChecked
                  ? "bg-brand-50/70 border-brand-300 text-brand-950 font-medium shadow-xs"
                  : "bg-white border-slate-200 hover:border-slate-300 text-slate-700 hover:bg-slate-50/50"
              }`}
            >
              <div className="truncate pr-2">
                <p className="text-xs font-semibold truncate">{loc.name}</p>
                <p className="text-[10px] text-slate-400 truncate">
                  {loc.district} • {loc.tier}
                </p>
              </div>
              <div
                className={`w-4 h-4 rounded border flex items-center justify-center shrink-0 ${
                  isChecked
                    ? "bg-brand-600 border-brand-600 text-white"
                    : "border-slate-300 bg-white"
                }`}
              >
                {isChecked && <CheckSquare className="w-3.5 h-3.5 stroke-[3]" />}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
