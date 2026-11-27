"use client";

import React, { useState, useMemo } from "react";
import { Search, CheckSquare, Square, X, MapPin, Lock } from "lucide-react";
import Link from "next/link";

export interface LocationItem {
  id: string;
  name: string;
  district: string;
  tier: string;
  pincode_prefix?: string;
}

export interface StateItem {
  id: string;
  name: string;
  type: string;
  cities: LocationItem[];
}

interface LocationSelectorProps {
  statesList: StateItem[];
  selectedStates: string[];
  selectedCities: string[];
  maxStatesAllowed: number;
  homeState?: string | null;
  allowedStates?: string[];
  allIndia?: boolean;
  onLockedStateClick?: (stateName: string) => void;
  onChangeStates: (states: string[]) => void;
  onChangeCities: (cities: string[]) => void;
}

export default function LocationSelector({
  statesList,
  selectedStates,
  selectedCities,
  maxStatesAllowed,
  homeState,
  allowedStates,
  allIndia = false,
  onLockedStateClick,
  onChangeStates,
  onChangeCities,
}: LocationSelectorProps) {
  const [stateSearch, setStateSearch] = useState("");
  const [citySearch, setCitySearch] = useState("");

  const sortedStates = useMemo(() => {
    const base = [...statesList];
    if (homeState) {
      base.sort((a, b) => {
        if (a.name.toLowerCase() === homeState.toLowerCase()) return -1;
        if (b.name.toLowerCase() === homeState.toLowerCase()) return 1;
        return 0;
      });
    }
    return base;
  }, [statesList, homeState]);

  const filteredStates = useMemo(() => {
    if (!stateSearch.trim()) return sortedStates;
    const q = stateSearch.toLowerCase();
    return sortedStates.filter((s) => s.name.toLowerCase().includes(q));
  }, [sortedStates, stateSearch]);

  const activeStateObjects = useMemo(
    () => statesList.filter((s) => selectedStates.includes(s.name)),
    [statesList, selectedStates]
  );

  const isAllIndia = allIndia || maxStatesAllowed >= 36;

  const isStateLocked = (stateName: string) => {
    if (isAllIndia) return false;
    if (allowedStates && allowedStates.length > 0) {
      return !allowedStates.some((s) => s.toLowerCase() === stateName.toLowerCase());
    }
    if (homeState) return stateName.toLowerCase() !== homeState.toLowerCase();
    return stateName.toLowerCase() !== "odisha";
  };

  const handleToggleState = (st: StateItem) => {
    if (isStateLocked(st.name)) {
      onLockedStateClick?.(st.name);
      return;
    }
    if (selectedStates.includes(st.name)) {
      const nextStates = selectedStates.filter((s) => s !== st.name);
      const stCityNames = new Set(st.cities.map((c) => c.name));
      onChangeStates(nextStates);
      onChangeCities(selectedCities.filter((c) => !stCityNames.has(c)));
    } else {
      const nextStates = [...selectedStates, st.name];
      // Default ON: All cities in newly selected state
      const newCities = Array.from(new Set([...selectedCities, ...st.cities.map((c) => c.name)]));
      onChangeStates(nextStates);
      onChangeCities(newCities);
    }
  };

  const handleSelectAllAllowed = () => {
    const allowedObjs = statesList.filter((s) => !isStateLocked(s.name));
    if (selectedStates.length === allowedObjs.length && allowedObjs.length > 0) {
      const fallback = homeState || allowedObjs[0]?.name || "Odisha";
      const stObj = statesList.find((s) => s.name.toLowerCase() === fallback.toLowerCase());
      onChangeStates([fallback]);
      onChangeCities(stObj ? stObj.cities.map((c) => c.name) : []);
    } else {
      onChangeStates(allowedObjs.map((s) => s.name));
      onChangeCities(allowedObjs.flatMap((s) => s.cities.map((c) => c.name)));
    }
  };

  const handleToggleAllCitiesInState = (st: StateItem) => {
    const stNames = st.cities.map((c) => c.name);
    const allIn = stNames.every((n) => selectedCities.includes(n));
    if (allIn) {
      onChangeCities(selectedCities.filter((c) => !stNames.includes(c)));
    } else {
      onChangeCities(Array.from(new Set([...selectedCities, ...stNames])));
    }
  };

  const handleToggleCity = (cityName: string) => {
    if (selectedCities.includes(cityName)) {
      onChangeCities(selectedCities.filter((c) => c !== cityName));
    } else {
      onChangeCities([...selectedCities, cityName]);
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-3">
        <div>
          <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
            <MapPin className="w-5 h-5 text-brand-600" />
            <span>1. Where: Select States &amp; Cities</span>
          </h2>
          <p className="text-sm text-slate-500 mt-0.5">
            {isAllIndia
              ? "All 28 Indian states & 8 union territories unlocked."
              : homeState
              ? `Your free Home State is ${homeState}. Unlock additional states with Starter or Pro.`
              : "Choose your Home State to start collecting."}
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={handleSelectAllAllowed}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-brand-50 text-brand-700 border border-brand-200 hover:bg-brand-100"
            title={isAllIndia ? "Select all 36 states" : "Selects only allowed states; locked states are skipped"}
          >
            {isAllIndia ? "Select All India" : "Select All (Allowed)"}
          </button>
          {!isAllIndia && (
            <Link
              href="/pricing"
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200 hover:bg-amber-100 flex items-center space-x-1"
            >
              <Lock className="w-3.5 h-3.5" />
              <span>Unlock All India</span>
            </Link>
          )}
        </div>
      </div>

      {/* States Search & Pills */}
      <div>
        <div className="relative mb-2.5">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={stateSearch}
            onChange={(e) => setStateSearch(e.target.value)}
            placeholder="Search Indian states or UTs (e.g. Odisha, Maharashtra, Karnataka, Delhi)..."
            className="w-full pl-9 pr-4 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/20"
          />
        </div>

        <div className="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto pr-1">
          {filteredStates.map((st) => {
            const selected = selectedStates.includes(st.name);
            const locked = isStateLocked(st.name);
            const isHome = Boolean(homeState && st.name.toLowerCase() === homeState.toLowerCase());
            return (
              <button
                key={st.id}
                type="button"
                onClick={() => handleToggleState(st)}
                title={locked ? "Click to unlock this state with a paid plan" : `${st.cities.length} cities`}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium border flex items-center space-x-1.5 transition-all ${
                  selected
                    ? "bg-brand-600 text-white border-brand-600 shadow-xs"
                    : locked
                    ? "bg-slate-50 text-slate-500 border-slate-200 hover:border-amber-300 hover:bg-amber-50/40"
                    : "bg-white text-slate-700 border-slate-200 hover:border-brand-300 hover:bg-brand-50/40"
                }`}
              >
                {locked && <Lock className="w-3 h-3 text-amber-500" />}
                <span>{st.name}</span>
                {isHome && (
                  <span className={`px-1.5 py-0.5 rounded text-[9px] font-black uppercase ${selected ? "bg-white/20 text-white" : "bg-emerald-100 text-emerald-800"}`}>
                    Free for you
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Cities Panel per Selected State */}
      <div className="space-y-3 pt-2 border-t border-slate-100">
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs font-semibold text-slate-700">
            Cities Selected: <strong className="text-brand-700">{selectedCities.length}</strong> across{" "}
            <strong className="text-brand-700">{selectedStates.length}</strong> state(s)
          </span>
          <div className="relative w-56">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={citySearch}
              onChange={(e) => setCitySearch(e.target.value)}
              placeholder="Filter cities..."
              className="w-full pl-8 pr-6 py-1 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none"
            />
            {citySearch && (
              <button onClick={() => setCitySearch("")} className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400">
                <X className="w-3 h-3" />
              </button>
            )}
          </div>
        </div>

        <div className="max-h-60 overflow-y-auto space-y-3 pr-1">
          {activeStateObjects.map((st) => {
            const stCities = st.cities.filter((c) =>
              !citySearch.trim() ? true : c.name.toLowerCase().includes(citySearch.toLowerCase()) || c.district.toLowerCase().includes(citySearch.toLowerCase())
            );
            const allIn = st.cities.every((c) => selectedCities.includes(c.name));
            return (
              <div key={st.id} className="p-3 rounded-xl bg-slate-50/70 border border-slate-200/70">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-slate-800">{st.name}</span>
                  <button
                    type="button"
                    onClick={() => handleToggleAllCitiesInState(st)}
                    className="text-[11px] font-semibold text-brand-700 hover:underline flex items-center space-x-1"
                  >
                    {allIn ? <CheckSquare className="w-3.5 h-3.5" /> : <Square className="w-3.5 h-3.5" />}
                    <span>All cities in {st.name}</span>
                  </button>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
                  {stCities.map((loc) => {
                    const checked = selectedCities.includes(loc.name);
                    return (
                      <div
                        key={loc.id}
                        onClick={() => handleToggleCity(loc.name)}
                        className={`px-2.5 py-1.5 rounded-lg border cursor-pointer text-xs flex items-center justify-between ${
                          checked
                            ? "bg-white border-brand-400 text-brand-900 font-semibold shadow-2xs"
                            : "bg-white/60 border-slate-200 text-slate-600"
                        }`}
                      >
                        <span className="truncate pr-1">{loc.name}</span>
                        {checked && <CheckSquare className="w-3.5 h-3.5 text-brand-600 shrink-0" />}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
