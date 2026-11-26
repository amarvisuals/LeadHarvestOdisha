"use client";

import React, { useState, useMemo } from "react";
import { Search, Plus, Bookmark, X, Tag } from "lucide-react";

export interface CategoryItem {
  id: string;
  name: string;
  keywords: string[];
}

export interface PresetItem {
  id: string;
  name: string;
  cities: string[];
  categories: string[];
}

interface CategorySelectorProps {
  categories: CategoryItem[];
  selectedCategories: string[];
  customCategories: string[];
  presets: PresetItem[];
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
  onChange,
  onCustomChange,
  onSavePreset,
  onLoadPreset,
}: CategorySelectorProps) {
  const [search, setSearch] = useState("");
  const [newCustomInput, setNewCustomInput] = useState("");
  const [presetNameInput, setPresetNameInput] = useState("");
  const [showSavePreset, setShowSavePreset] = useState(false);

  const filtered = useMemo(() => {
    if (!search.trim()) return categories;
    const q = search.toLowerCase();
    return categories.filter(
      (c) =>
        c.name.toLowerCase().includes(q) ||
        c.keywords.some((k) => k.toLowerCase().includes(q))
    );
  }, [categories, search]);

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
            <span>2. Select Business Categories</span>
          </h2>
          <p className="text-sm text-slate-500 mt-0.5">
            Pick from predefined popular local industries or type your own custom niches.
          </p>
        </div>

        {/* Preset Controls */}
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
              <option value="" disabled>
                Load Preset...
              </option>
              {presets.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          )}

          <button
            type="button"
            onClick={() => setShowSavePreset(!showSavePreset)}
            className="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-brand-50 text-brand-700 border border-brand-200 hover:bg-brand-100 transition-colors flex items-center space-x-1"
          >
            <Bookmark className="w-3.5 h-3.5" />
            <span>Save as Preset</span>
          </button>
        </div>
      </div>

      {/* Save Preset Dialog */}
      {showSavePreset && (
        <form onSubmit={handleSavePresetSubmit} className="mt-3 p-3 bg-brand-50/70 rounded-xl border border-brand-200 flex items-center space-x-2">
          <input
            type="text"
            value={presetNameInput}
            onChange={(e) => setPresetNameInput(e.target.value)}
            placeholder="Preset Name (e.g. Coastal Odisha Restaurants)"
            className="flex-1 px-3 py-1.5 text-xs bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
          <button
            type="submit"
            className="px-3 py-1.5 bg-brand-600 text-white text-xs font-semibold rounded-lg hover:bg-brand-700"
          >
            Save
          </button>
          <button
            type="button"
            onClick={() => setShowSavePreset(false)}
            className="p-1 text-slate-400 hover:text-slate-600"
          >
            <X className="w-4 h-4" />
          </button>
        </form>
      )}

      {/* Custom Category Input */}
      <div className="mt-4 flex items-center space-x-2">
        <input
          type="text"
          value={newCustomInput}
          onChange={(e) => setNewCustomInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), handleAddCustom())}
          placeholder="Add custom category (e.g. Solar Panel Dealers, Organic Stores)..."
          className="flex-1 px-3.5 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
        />
        <button
          type="button"
          onClick={handleAddCustom}
          className="px-3.5 py-2 bg-slate-800 hover:bg-slate-900 text-white text-xs font-semibold rounded-xl flex items-center space-x-1 transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Add Custom</span>
        </button>
      </div>

      {/* Search Input for categories */}
      <div className="relative mt-3 mb-3">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search categories (e.g. Doctors, Real Estate, Printing)..."
          className="w-full pl-10 pr-4 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/20"
        />
      </div>

      {/* Category Chips Cloud */}
      <div className="flex flex-wrap gap-2 max-h-52 overflow-y-auto pr-1">
        {/* Custom Categories First */}
        {customCategories.map((c) => (
          <span
            key={c}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-300 shadow-xs"
          >
            <span>{c}</span>
            <button
              type="button"
              onClick={() => handleRemoveCustom(c)}
              className="text-amber-500 hover:text-amber-700"
            >
              <X className="w-3 h-3" />
            </button>
          </span>
        ))}

        {/* Predefined Categories */}
        {filtered.map((cat) => {
          const isSelected = selectedCategories.includes(cat.name);
          return (
            <button
              key={cat.id}
              type="button"
              onClick={() => handleToggleCategory(cat.name)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-all ${
                isSelected
                  ? "bg-brand-600 text-white border-brand-600 shadow-sm shadow-brand-500/20"
                  : "bg-slate-50/80 text-slate-700 border-slate-200 hover:bg-slate-100 hover:border-slate-300"
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
