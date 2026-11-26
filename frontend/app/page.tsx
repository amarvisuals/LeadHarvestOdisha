"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import LocationSelector, { LocationItem } from "@/components/LocationSelector";
import CategorySelector, { CategoryItem, PresetItem } from "@/components/CategorySelector";
import DuplicateFilterUpload, { FileAuditCard } from "@/components/DuplicateFilterUpload";
import ReviewAndStart from "@/components/ReviewAndStart";
import { Sparkles, MapPin, Tag, ShieldAlert } from "lucide-react";

export default function WizardPage() {
  const router = useRouter();

  const [locations, setLocations] = useState<LocationItem[]>([]);
  const [categories, setCategories] = useState<CategoryItem[]>([]);
  const [presets, setPresets] = useState<PresetItem[]>([]);
  
  const [selectedCities, setSelectedCities] = useState<string[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [customCategories, setCustomCategories] = useState<string[]>([]);
  const [rememberLeads, setRememberLeads] = useState(true);
  const [adapterMode, setAdapterMode] = useState<"mock" | "justdial">("mock");

  const [auditCards, setAuditCards] = useState<FileAuditCard[]>([]);
  const [knownRecordsCount, setKnownRecordsCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Load initial configurations
  useEffect(() => {
    async function loadConfig() {
      try {
        const [locRes, catRes, presetRes, statsRes] = await Promise.all([
          fetch("/api/config/locations"),
          fetch("/api/config/categories"),
          fetch("/api/presets"),
          fetch("/api/known-records/stats"),
        ]);

        if (locRes.ok) {
          const locData: LocationItem[] = await locRes.json();
          setLocations(locData);
          // Default state: ALL cities selected!
          setSelectedCities(locData.map((l) => l.name));
        }

        if (catRes.ok) {
          const catData: CategoryItem[] = await catRes.json();
          setCategories(catData);
          // Select first 3 categories by default as a helpful starting point
          if (catData.length > 0) {
            setSelectedCategories(catData.slice(0, 3).map((c) => c.name));
          }
        }

        if (presetRes.ok) {
          const presetData = await presetRes.json();
          setPresets(presetData);
        }

        if (statsRes.ok) {
          const statsData = await statsRes.json();
          setKnownRecordsCount(statsData.total_records || 0);
        }
      } catch (err) {
        console.error("Failed to load initial configurations:", err);
      }
    }
    loadConfig();
  }, []);

  const handleFilesSelected = async (fileList: FileList) => {
    const formData = new FormData();
    for (let i = 0; i < fileList.length; i++) {
      formData.append("files", fileList[i]);
    }

    try {
      const res = await fetch("/api/uploads", {
        method: "POST",
        body: formData,
      });
      if (res.ok) {
        const newCards: FileAuditCard[] = await res.json();
        setAuditCards((prev) => [...prev, ...newCards]);

        // Refresh known records count
        const statsRes = await fetch("/api/known-records/stats");
        if (statsRes.ok) {
          const stats = await statsRes.json();
          setKnownRecordsCount(stats.total_records || 0);
        }
      } else {
        alert("Failed to upload files for auditing");
      }
    } catch (e) {
      console.error("Upload error:", e);
    }
  };

  const handleClearKnownRecords = async () => {
    if (!confirm("Are you sure you want to clear all indexed known records? Future runs will not skip them.")) return;
    try {
      const res = await fetch("/api/known-records", { method: "DELETE" });
      if (res.ok) {
        setKnownRecordsCount(0);
        setAuditCards([]);
      }
    } catch (e) {
      console.error("Clear error:", e);
    }
  };

  const handleUpdateMapping = async (auditId: string, mapping: Record<string, string>) => {
    try {
      await fetch("/api/uploads/mapping", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ audit_id: auditId, column_mapping: mapping }),
      });
      // Refresh count
      const statsRes = await fetch("/api/known-records/stats");
      if (statsRes.ok) {
        const stats = await statsRes.json();
        setKnownRecordsCount(stats.total_records || 0);
      }
    } catch (e) {
      console.error("Mapping update error:", e);
    }
  };

  const handleSavePreset = async (name: string) => {
    try {
      const res = await fetch("/api/presets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          cities: selectedCities,
          categories: selectedCategories,
        }),
      });
      if (res.ok) {
        const newPreset: PresetItem = await res.json();
        setPresets((prev) => [newPreset, ...prev]);
        alert(`Preset "${name}" saved!`);
      }
    } catch (e) {
      console.error("Save preset error:", e);
    }
  };

  const handleLoadPreset = (preset: PresetItem) => {
    setSelectedCities(preset.cities);
    setSelectedCategories(preset.categories);
  };

  const handleStartCollecting = async () => {
    if (selectedCities.length === 0 || selectedCategories.length === 0) {
      setErrorMessage("Please select at least one city and one business category.");
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const res = await fetch("/api/jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          cities: selectedCities,
          categories: selectedCategories,
          adapter: adapterMode,
          remember_leads: rememberLeads,
          custom_categories: customCategories,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to start collection");
      }

      const jobData = await res.json();
      router.push(`/progress/${jobData.id}`);
    } catch (err: any) {
      setErrorMessage(err.message || "Could not launch job runner");
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-8 pb-20">
      {/* Hero Header */}
      <div className="text-center max-w-3xl mx-auto pt-2 pb-4">
        <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-brand-50 border border-brand-200 text-brand-800 text-xs font-semibold mb-3">
          <Sparkles className="w-3.5 h-3.5 text-brand-600" />
          <span>Automated B2B Lead Generator for Odisha</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
          One-Click Business Lead Data Collector
        </h1>
        <p className="mt-2 text-base text-slate-600 max-w-2xl mx-auto">
          Choose your target Odisha cities, select industries, upload previous lists to skip duplicates, and download a ready-to-use formatted Excel file.
        </p>
      </div>

      {errorMessage && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-center space-x-3 text-rose-800 text-sm">
          <ShieldAlert className="w-5 h-5 shrink-0 text-rose-600" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Main 2-Column Responsive Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: 3 Steps Form */}
        <div className="lg:col-span-8 space-y-6">
          {/* Step 1: Locations */}
          <LocationSelector
            locations={locations}
            selectedCities={selectedCities}
            onChange={setSelectedCities}
          />

          {/* Step 2: Categories */}
          <CategorySelector
            categories={categories}
            selectedCategories={selectedCategories}
            customCategories={customCategories}
            presets={presets}
            onChange={setSelectedCategories}
            onCustomChange={setCustomCategories}
            onSavePreset={handleSavePreset}
            onLoadPreset={handleLoadPreset}
          />

          {/* Step 3: Duplicate Filter Upload */}
          <DuplicateFilterUpload
            auditCards={auditCards}
            knownRecordsCount={knownRecordsCount}
            onFilesSelected={handleFilesSelected}
            onClearKnownRecords={handleClearKnownRecords}
            onUpdateMapping={handleUpdateMapping}
          />
        </div>

        {/* Right Column: Sticky Summary & Review Panel */}
        <div className="lg:col-span-4 sticky top-20 space-y-6">
          <ReviewAndStart
            citiesCount={selectedCities.length}
            categoriesCount={selectedCategories.length}
            knownRecordsCount={knownRecordsCount}
            rememberLeads={rememberLeads}
            adapterMode={adapterMode}
            isLoading={isLoading}
            onToggleRememberLeads={setRememberLeads}
            onSelectAdapterMode={setAdapterMode}
            onStartCollecting={handleStartCollecting}
          />

          {/* Sticky Quick Info Box */}
          <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs text-xs space-y-3">
            <h3 className="font-bold text-slate-800 flex items-center space-x-1.5">
              <span>Why LeadHarvest Odisha?</span>
            </h3>
            <ul className="space-y-2 text-slate-600">
              <li className="flex items-start space-x-2">
                <span className="text-brand-600 font-bold">✓</span>
                <span>3-Tier Deduplication: normalized phone, exact name, and fuzzy token matching.</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-brand-600 font-bold">✓</span>
                <span>Automatic 3-sheet Excel report with styled header and clickable links.</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-brand-600 font-bold">✓</span>
                <span>Resumable: pause or cancel anytime while keeping harvested leads.</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
