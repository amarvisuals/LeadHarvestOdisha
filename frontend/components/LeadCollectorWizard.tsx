"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import LocationSelector, { StateItem } from "@/components/LocationSelector";
import CategorySelector, { CategoryItem, PresetItem } from "@/components/CategorySelector";
import SmartFilters, { SmartFiltersState, PitchPreset, EMPTY_FILTERS } from "@/components/SmartFilters";
import DuplicateFilterUpload, { FileAuditCard } from "@/components/DuplicateFilterUpload";
import ReviewAndStart from "@/components/ReviewAndStart";
import { ShieldAlert, Lock, CheckCircle2, ArrowRight } from "lucide-react";
import { apiFetch, trackEvent } from "@/lib/api";

interface WizardProps {
  initialState?: string;
  initialCity?: string;
  initialCategory?: string;
}

export default function LeadCollectorWizard({
  initialState,
  initialCity,
  initialCategory,
}: WizardProps) {
  const router = useRouter();

  const [statesList, setStatesList] = useState<StateItem[]>([]);
  const [categories, setCategories] = useState<CategoryItem[]>([]);
  const [pitchPresets, setPitchPresets] = useState<PitchPreset[]>([]);
  const [adapterCaps, setAdapterCaps] = useState<Record<string, Record<string, boolean>>>({});
  const [presets, setPresets] = useState<PresetItem[]>([]);

  const [selectedStates, setSelectedStates] = useState<string[]>([initialState || "Odisha"]);
  const [selectedCities, setSelectedCities] = useState<string[]>(initialCity ? [initialCity] : []);
  const [selectedCategories, setSelectedCategories] = useState<string[]>(initialCategory ? [initialCategory] : []);
  const [customCategories, setCustomCategories] = useState<string[]>([]);
  const [smartFilters, setSmartFilters] = useState<SmartFiltersState>(EMPTY_FILTERS);
  const [rememberLeads, setRememberLeads] = useState(true);
  const [adapterMode, setAdapterMode] = useState<"mock" | "justdial">("mock");

  const [auditCards, setAuditCards] = useState<FileAuditCard[]>([]);
  const [knownRecordsCount, setKnownRecordsCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [gateModal, setGateModal] = useState<{ open: boolean; message: string; type: string }>({
    open: false,
    message: "",
    type: "guest_limit",
  });

  const [maxStatesAllowed, setMaxStatesAllowed] = useState(1);
  const [allowBasicAdv, setAllowBasicAdv] = useState(false);
  const [allowAllFilters, setAllowAllFilters] = useState(false);
  const [allowPresets, setAllowPresets] = useState(false);

  const [locStatus, setLocStatus] = useState<any>(null);
  const [bannerDismissed, setBannerDismissed] = useState(false);
  const [chooserState, setChooserState] = useState("");
  const [chooserSearch, setChooserSearch] = useState("");

  useEffect(() => {
    async function loadConfig() {
      try {
        const [locRes, catRes, pitchRes, adRes, presetRes, statsRes, meRes, locStatusRes] = await Promise.all([
          apiFetch("/api/config/india-locations"),
          apiFetch("/api/config/categories"),
          apiFetch("/api/config/pitch-presets"),
          apiFetch("/api/config/adapters"),
          apiFetch("/api/presets"),
          apiFetch("/api/known-records/stats"),
          apiFetch("/api/auth/me"),
          apiFetch("/api/location/status"),
        ]);

        let stData: StateItem[] = [];
        if (locRes.ok) {
          stData = await locRes.json();
          setStatesList(stData);
        }

        let detectedHome: string | null = null;
        if (locStatusRes.ok) {
          const ls = await locStatusRes.json();
          setLocStatus(ls);
          detectedHome = ls.home_state || null;
        }

        if (stData.length > 0 && !initialCity) {
          const fallbackName = initialState || detectedHome || "Odisha";
          const targetState = stData.find((s) => s.name.toLowerCase() === fallbackName.toLowerCase()) || stData[0];
          if (targetState) {
            setSelectedStates([targetState.name]);
            setSelectedCities(targetState.cities.slice(0, 6).map((c) => c.name));
          }
        }

        if (catRes.ok) {
          const catData: CategoryItem[] = await catRes.json();
          setCategories(catData);
          if (!initialCategory && catData.length > 0) {
            setSelectedCategories([catData[0].name]);
          }
        }

        if (pitchRes.ok) setPitchPresets(await pitchRes.json());
        if (adRes.ok) setAdapterCaps(await adRes.json());
        if (presetRes.ok) setPresets(await presetRes.json());
        if (statsRes.ok) {
          const statsData = await statsRes.json();
          setKnownRecordsCount(statsData.total_records || 0);
        }
        if (meRes.ok) {
          const me = await meRes.json();
          if (me.authenticated && me.plan) {
            setMaxStatesAllowed(me.plan.max_states || 1);
            setAllowBasicAdv(Boolean(me.plan.allow_advanced_filters));
            setAllowAllFilters(Boolean(me.plan.allow_all_filters));
            setAllowPresets(Boolean(me.plan.allow_presets));
          }
        }
      } catch (err) {
        console.error("Failed to load initial configurations:", err);
      }
    }
    loadConfig();
    trackEvent("event", { event_name: "wizard_started" });
  }, [initialState, initialCity, initialCategory]);

  const handleFilesSelected = async (fileList: FileList) => {
    const formData = new FormData();
    for (let i = 0; i < fileList.length; i++) {
      formData.append("files", fileList[i]);
    }
    const res = await apiFetch("/api/uploads", { method: "POST", body: formData });
    if (res.ok) {
      const newCards: FileAuditCard[] = await res.json();
      setAuditCards((prev) => [...prev, ...newCards]);
      const statsRes = await apiFetch("/api/known-records/stats");
      if (statsRes.ok) {
        const stats = await statsRes.json();
        setKnownRecordsCount(stats.total_records || 0);
      }
    }
  };

  const handleClearKnownRecords = async () => {
    if (!confirm("Clear all your indexed known records?")) return;
    const res = await apiFetch("/api/known-records", { method: "DELETE" });
    if (res.ok) {
      setKnownRecordsCount(0);
      setAuditCards([]);
    }
  };

  const handleUpdateMapping = async (auditId: string, mapping: Record<string, string>) => {
    await apiFetch("/api/uploads/mapping", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ audit_id: auditId, column_mapping: mapping }),
    });
    const statsRes = await apiFetch("/api/known-records/stats");
    if (statsRes.ok) {
      const stats = await statsRes.json();
      setKnownRecordsCount(stats.total_records || 0);
    }
  };

  const handleSavePreset = async (name: string) => {
    const res = await apiFetch("/api/presets", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name,
        states: selectedStates,
        cities: selectedCities,
        categories: selectedCategories,
        filters: {
          ...smartFilters,
          min_rating: smartFilters.min_rating === "" ? null : smartFilters.min_rating,
          max_rating: smartFilters.max_rating === "" ? null : smartFilters.max_rating,
          min_reviews: smartFilters.min_reviews === "" ? null : smartFilters.min_reviews,
          max_reviews: smartFilters.max_reviews === "" ? null : smartFilters.max_reviews,
        },
      }),
    });
    if (res.ok) {
      const newPreset: PresetItem = await res.json();
      setPresets((prev) => [newPreset, ...prev]);
    }
  };

  const handleLoadPreset = (preset: PresetItem) => {
    if (preset.states) setSelectedStates(preset.states);
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
      const payloadFilters = {
        ...smartFilters,
        min_rating: smartFilters.min_rating === "" ? null : Number(smartFilters.min_rating),
        max_rating: smartFilters.max_rating === "" ? null : Number(smartFilters.max_rating),
        min_reviews: smartFilters.min_reviews === "" ? null : Number(smartFilters.min_reviews),
        max_reviews: smartFilters.max_reviews === "" ? null : Number(smartFilters.max_reviews),
      };

      const res = await apiFetch("/api/jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          states: selectedStates,
          cities: selectedCities,
          categories: selectedCategories,
          adapter: adapterMode,
          remember_leads: rememberLeads,
          custom_categories: customCategories,
          filters: payloadFilters,
        }),
      });

      if (res.status === 403) {
        const err = await res.json();
        const detail = err.detail || {};
        setGateModal({
          open: true,
          message: detail.message || "Upgrade or create a free account to continue.",
          type: detail.upgrade_hint?.action || "upgrade",
        });
        setIsLoading(false);
        return;
      }

      if (!res.ok) {
        const err = await res.json();
        throw new Error(typeof err.detail === "string" ? err.detail : err.detail?.message || "Failed to start collection");
      }

      const jobData = await res.json();
      router.push(`/progress/${jobData.id}`);
    } catch (err: any) {
      setErrorMessage(err.message || "Could not launch job runner");
      setIsLoading(false);
    }
  };

  const totalSearches = selectedCities.length * selectedCategories.length;

  return (
    <div id="collector-wizard" className="space-y-6">
      {/* First-visit Home State confirmation + IP approximate location consent */}
      {locStatus?.home_state && !locStatus?.all_india && !bannerDismissed && (
        <div className="p-3.5 rounded-2xl bg-emerald-50/80 border border-emerald-200 flex flex-wrap items-center justify-between gap-2 text-xs text-emerald-900">
          <div>
            <span className="font-bold">
              We found you in {locStatus.home_state}. Your free data state is {locStatus.home_state}.
            </span>{" "}
            <span className="text-emerald-700">
              (Approximate location from IP is used to set your free state — never GPS.{" "}
              <Link href="/privacy" className="underline font-semibold">Privacy Policy</Link>)
            </span>
          </div>
          <div className="flex items-center space-x-3">
            {locStatus.actor_type === "guest" && (
              <Link href="/signup?correct=1" className="font-bold text-brand-700 hover:underline">
                Not right? Choose your state
              </Link>
            )}
            <button type="button" onClick={() => setBannerDismissed(true)} className="text-emerald-700 font-bold hover:underline">
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Mismatch protection banner */}
      {locStatus?.mismatch_detected && !locStatus?.all_india && (
        <div className="p-3.5 rounded-2xl bg-amber-50 border border-amber-200 text-xs text-amber-900 flex items-center justify-between gap-2">
          <span>
            Your free state is <strong>{locStatus.home_state}</strong>. Other states are available on paid plans.
          </span>
          <Link href="/pricing" className="font-bold text-amber-900 underline shrink-0">Upgrade Plan</Link>
        </div>
      )}

      {errorMessage && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-center space-x-3 text-rose-800 text-sm">
          <ShieldAlert className="w-5 h-5 shrink-0 text-rose-600" />
          <span>{errorMessage}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        <div className="lg:col-span-8 space-y-6">
          <LocationSelector
            statesList={statesList}
            selectedStates={selectedStates}
            selectedCities={selectedCities}
            maxStatesAllowed={maxStatesAllowed}
            homeState={locStatus?.home_state}
            allowedStates={locStatus?.allowed_states}
            allIndia={Boolean(locStatus?.all_india)}
            onLockedStateClick={(stateName) => {
              apiFetch("/api/location/locked-click", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ state: stateName }),
              }).catch(() => {});
              setGateModal({
                open: true,
                type: "upgrade",
                message: `${stateName} is locked on your current plan. Your free Home State is ${locStatus?.home_state || "set to your region"}. Unlock all India from ₹499/month!`,
              });
            }}
            onChangeStates={setSelectedStates}
            onChangeCities={setSelectedCities}
          />

          <CategorySelector
            categories={categories}
            selectedCategories={selectedCategories}
            customCategories={customCategories}
            presets={presets}
            allowPresets={allowPresets}
            onChange={setSelectedCategories}
            onCustomChange={setCustomCategories}
            onSavePreset={handleSavePreset}
            onLoadPreset={handleLoadPreset}
          />

          <SmartFilters
            filters={smartFilters}
            pitchPresets={pitchPresets}
            allowBasicAdvanced={allowBasicAdv}
            allowAllFilters={allowAllFilters}
            adapterCapabilities={adapterCaps[adapterMode] || { has_website: true, mobile: true, email: true, social_only: true }}
            onChange={setSmartFilters}
          />

          <DuplicateFilterUpload
            auditCards={auditCards}
            knownRecordsCount={knownRecordsCount}
            onFilesSelected={handleFilesSelected}
            onClearKnownRecords={handleClearKnownRecords}
            onUpdateMapping={handleUpdateMapping}
          />
        </div>

        <div className="lg:col-span-4 sticky top-20 space-y-5">
          {totalSearches > 60 && (
            <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900">
              <strong>Large run notice:</strong> {selectedCities.length} cities × {selectedCategories.length} categories ={" "}
              <strong>{totalSearches} searches</strong>. Results will be capped at your plan&apos;s per-run limit.
            </div>
          )}

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
        </div>
      </div>

      {/* One-time Home State Chooser Modal (Outside India / VPN / Detection failed) */}
      {locStatus?.requires_manual_choice && statesList.length > 0 && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <h3 className="text-lg font-black text-slate-900">Choose Your Free Home State</h3>
            <p className="text-xs text-slate-600">
              {locStatus.is_vpn
                ? "We noticed a VPN or proxy connection, so please choose your Home State manually."
                : locStatus.outside_india
                ? "You appear to be visiting from outside India. Choose the one Indian state you want free access to."
                : "We couldn't auto-detect your state. Choose your one free Indian state below (it locks after selection)."}
            </p>
            <input
              type="text"
              value={chooserSearch}
              onChange={(e) => setChooserSearch(e.target.value)}
              placeholder="Search state or UT..."
              className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200"
            />
            <div className="max-h-48 overflow-y-auto grid grid-cols-2 gap-1.5">
              {statesList
                .filter((s) => s.name.toLowerCase().includes(chooserSearch.toLowerCase()))
                .map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => setChooserState(s.name)}
                    className={`px-2.5 py-1.5 rounded-lg text-xs font-semibold border text-left ${
                      chooserState === s.name ? "bg-brand-600 text-white border-brand-600" : "bg-slate-50 text-slate-700 border-slate-200"
                    }`}
                  >
                    {s.name}
                  </button>
                ))}
            </div>
            <button
              type="button"
              disabled={!chooserState}
              onClick={async () => {
                const res = await apiFetch("/api/location/choose", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ state: chooserState }),
                });
                if (res.ok) {
                  window.location.reload();
                }
              }}
              className="w-full py-2.5 rounded-xl bg-brand-600 text-white text-xs font-bold disabled:opacity-50"
            >
              Confirm &amp; Lock {chooserState || "State"}
            </button>
          </div>
        </div>
      )}

      {gateModal.open && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 sm:p-8 shadow-2xl border border-slate-200 space-y-5 text-center">
            <div className="w-14 h-14 rounded-2xl bg-amber-100 text-amber-700 flex items-center justify-center mx-auto">
              <Lock className="w-7 h-7" />
            </div>
            <div>
              <h3 className="text-xl font-black text-slate-900">
                {gateModal.type === "guest_limit" ? "Create a Free Account to Keep Going" : "Unlock This Feature"}
              </h3>
              <p className="text-sm text-slate-600 mt-1.5">{gateModal.message}</p>
            </div>

            <ul className="text-left text-xs space-y-2 bg-slate-50 p-4 rounded-xl border border-slate-200 text-slate-700">
              <li className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>Your previous guest runs &amp; Known Records carry over automatically</span>
              </li>
              <li className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>30-day Excel download history &amp; smart duplicate protection</span>
              </li>
              <li className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>Unlock &ldquo;No Website&rdquo; filter &amp; All India starting at ₹499/mo</span>
              </li>
            </ul>

            <div className="flex flex-col space-y-2.5">
              {gateModal.type === "guest_limit" || gateModal.type === "signup" ? (
                <Link
                  href="/signup"
                  className="w-full py-3 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-sm flex items-center justify-center space-x-1.5 shadow-md"
                >
                  <span>Create Free Account</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>
              ) : (
                <Link
                  href="/pricing"
                  className="w-full py-3 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-sm flex items-center justify-center space-x-1.5 shadow-md"
                >
                  <span>Upgrade Plan</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>
              )}
              <Link href="/pricing" className="text-xs font-semibold text-brand-700 hover:underline py-1">
                Compare Plans &amp; Pricing
              </Link>
              <button
                type="button"
                onClick={() => setGateModal({ ...gateModal, open: false })}
                className="text-xs text-slate-400 hover:text-slate-600"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
