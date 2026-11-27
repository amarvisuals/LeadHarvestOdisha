"use client";

import React, { useState, useMemo } from "react";
import { Search, Plus, Bookmark, X, Tag } from "lucide-react";

export interface CategoryItem {
  id: string;
  name: string;
  group?: string;
  keywords: string[];
}

export interface PresetItem {
  id: string;
  name: string;
  states?: string[];
  cities: string[];
  categories: string[];
  filters?: Record<string, any>;
}

interface CategorySelectorProps {
  categories: CategoryItem[];
  selectedCategories: string[];
  customCategories: string[];
  presets: PresetItem[];
  allowPresets?: boolean;
  onChange: (categories: string[]) => void;
  onCustomChange: (customs: string[]) => void;
  onSavePreset: (name: string) => Promise<void>;
  onLoadPreset: (preset: PresetItem) => void;
}

export default function CategorySelector({
  categories,
  selectedCategories,
  customCategories,
  presets,
  allowPresets = true,
  onChange,
  onCustomChange,
  onSavePreset,
  onLoadPreset,
}: CategorySelectorProps) {
  const [search, setSearch] = useState("");
  const [selectedGroup, setSelectedGroup] = useState("All");
  const [newCustomInput, setNewCustomInput] = useState("");
  const [presetNameInput, setPresetNameInput] = useState("");
  const [showSavePreset, setShowSavePreset] = useState(false);

  const groups = useMemo(() => {
    const set = new Set<string>(["All"]);
    categories.forEach((c) => {
      if (c.group) set.add(c.group);
    });
    return Array.from(set);
  }, [categories]);

  const filtered = useMemo(() => {
    return categories.filter((c) => {
      const matchesGroup = selectedGroup === "All" || c.group === selectedGroup;
      if (!matchesGroup) return false;
      if (!search.trim()) return true;
      const q = search.toLowerCase();
      return (
        c.name.toLowerCase().includes(q) ||
        c.keywords.some((k) => k.toLowerCase().includes(q))
      );
    });
  }, [categories, search, selectedGroup]);

  const handleToggleCategory = (catName: string) => {
    if (selectedCategories.includes(catName)) {
      onChange(selectedCategories.filter((c) => c !== catName));
    } else {
      onChange([...selectedCategories, catName]);
    }
  };

  const handleAddCustom = () => {
    const trimmed = newCustomInput.trim();
    if (!trimmed) return;
    if (!customCategories.includes(trimmed) && !selectedCategories.includes(trimmed)) {
      onCustomChange([...customCategories, trimmed]);
      onChange([...selectedCategories, trimmed]);
    }
    setNewCustomInput("");
  };

  const handleRemoveCustom = (name: string) => {
    onCustomChange(customCategories.filter((c) => c !== name));
    onChange(selectedCategories.filter((c) => c !== name));
  };

  const handleSavePresetSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!presetNameInput.trim()) return;
    await onSavePreset(presetNameInput.trim());
    setPresetNameInput("");
    setShowSavePreset(false);
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-3">
        <div>
          <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
            <Tag className="w-5 h-5 text-brand-600" />
            <span>2. What: Select Business Categories ({categories.length}+)</span>
          </h2>
          <p className="text-sm text-slate-500 mt-0.5">
            Browse 200+ B2B-ready industries or add any custom niche.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {presets.length > 0 && (
            <select
              onChange={(e) => {
                const found = presets.find((p) => p.id === e.target.value);
                if (found) onLoadPreset(found);
              }}
              defaultValue=""
              className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-700 font-medium focus:outline-none"
            >
              <option value="" disabled>Load Preset...</option>
              {presets.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          )}

          {allowPresets && (
            <button
              type="button"
              onClick={() => setShowSavePreset(!showSavePreset)}
              className="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-brand-50 text-brand-700 border border-brand-200 hover:bg-brand-100 flex items-center space-x-1"
            >
              <Bookmark className="w-3.5 h-3.5" />
              <span>Save Preset</span>
            </button>
          )}
        </div>
      </div>

      {showSavePreset && (
        <form onSubmit={handleSavePresetSubmit} className="mt-3 p-3 bg-brand-50/70 rounded-xl border border-brand-200 flex items-center space-x-2">
          <input
            type="text"
            value={presetNameInput}
            onChange={(e) => setPresetNameInput(e.target.value)}
            placeholder="Preset Name (e.g. Dental Clinics No Website)"
            className="flex-1 px-3 py-1.5 text-xs bg-white border border-slate-200 rounded-lg focus:outline-none"
          />
          <button type="submit" className="px-3 py-1.5 bg-brand-600 text-white text-xs font-semibold rounded-lg">
            Save
          </button>
          <button type="button" onClick={() => setShowSavePreset(false)} className="p-1 text-slate-400">
            <X className="w-4 h-4" />
          </button>
        </form>
      )}

      {/* Group Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto py-3">
        {groups.map((grp) => (
          <button
            key={grp}
            type="button"
            onClick={() => setSelectedGroup(grp)}
            className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold whitespace-nowrap border transition-colors ${
              selectedGroup === grp
                ? "bg-slate-900 text-white border-slate-900"
                : "bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100"
            }`}
          >
            {grp}
          </button>
        ))}
      </div>

      {/* Custom Category Input */}
      <div className="flex items-center space-x-2 mb-3">
        <input
          type="text"
          value={newCustomInput}
          onChange={(e) => setNewCustomInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), handleAddCustom())}
          placeholder="Add custom category (e.g. Solar Panel Dealers, Dental Implant Clinics)..."
          className="flex-1 px-3.5 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/20"
        />
        <button
          type="button"
          onClick={handleAddCustom}
          className="px-3.5 py-2 bg-slate-800 hover:bg-slate-900 text-white text-xs font-semibold rounded-xl flex items-center space-x-1"
        >
          <Plus className="w-4 h-4" />
          <span>Add Custom</span>
        </button>
      </div>

      {/* Search */}
      <div className="relative mb-3">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search 200+ categories (e.g. Dentists, Builders, Salons, Printing)..."
          className="w-full pl-10 pr-4 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none"
        />
      </div>

      {/* Chips */}
      <div className="flex flex-wrap gap-1.5 max-h-52 overflow-y-auto pr-1">
        {customCategories.map((c) => (
          <span
            key={c}
            className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-300"
          >
            <span>{c}</span>
            <button type="button" onClick={() => handleRemoveCustom(c)} className="text-amber-500 hover:text-amber-700">
              <X className="w-3 h-3" />
            </button>
          </span>
        ))}

        {filtered.map((cat) => {
          const isSelected = selectedCategories.includes(cat.name);
          return (
            <button
              key={cat.id}
              type="button"
              onClick={() => handleToggleCategory(cat.name)}
              className={`px-3 py-1 rounded-full text-xs font-medium border transition-all ${
                isSelected
                  ? "bg-brand-600 text-white border-brand-600 shadow-xs"
                  : "bg-slate-50/80 text-slate-700 border-slate-200 hover:bg-slate-100"
              }`}
            >
              {cat.name}
            </button>
          );
        })}
      </div>
    </div>
  );
}
