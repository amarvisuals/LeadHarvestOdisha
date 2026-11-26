"use client";

import React from "react";
import { 
  Sparkles, Search, Database, Filter, 
  FileSpreadsheet, CheckCircle2, Clock 
} from "lucide-react";

export interface Stage {
  key: string;
  label: string;
  description: string;
}

export const STAGES: Stage[] = [
  { key: "preparing", label: "Preparing", description: "Getting everything ready…" },
  { key: "searching", label: "Searching", description: "Querying directory categories…" },
  { key: "collecting", label: "Collecting", description: "Extracting business phone and addresses…" },
  { key: "filtering", label: "Filtering", description: "Checking against your previous files…" },
  { key: "creating_file", label: "Creating file", description: "Building your styled Excel file…" },
  { key: "almost_done", label: "Almost done", description: "Final checks… getting ready to deliver" },
  { key: "success", label: "Success", description: "All done! Leads are ready." },
];

const ICONS = [Sparkles, Search, Database, Filter, FileSpreadsheet, Clock, CheckCircle2];

interface StageStepperProps {
  currentStage: string;
  currentDetail: string;
}

export default function StageStepper({ currentStage, currentDetail }: StageStepperProps) {
  const currentIndex = STAGES.findIndex((s) => s.key === currentStage);
  const activeIndex = currentIndex === -1 ? 0 : currentIndex;

  return (
    <div className="w-full">
      {/* Live Detail Banner with subtle pulsing dot */}
      <div className="mb-6 p-4 rounded-xl bg-brand-50/70 border border-brand-200/60 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-brand-600"></span>
          </span>
          <div>
            <p className="text-xs uppercase tracking-wider font-semibold text-brand-700">Live Status</p>
            <p className="text-sm font-medium text-slate-800">{currentDetail || "Processing requests..."}</p>
          </div>
        </div>
        <span className="text-xs font-semibold px-2.5 py-1 bg-white rounded-lg border border-brand-200 text-brand-800 shadow-sm">
          Stage {activeIndex + 1} of {STAGES.length}
        </span>
      </div>

      {/* Stepper Grid / Timeline */}
      <div className="grid grid-cols-1 sm:grid-cols-7 gap-2">
        {STAGES.map((stage, idx) => {
          const Icon = ICONS[idx];
          const isDone = idx < activeIndex;
          const isCurrent = idx === activeIndex;

          return (
            <div
              key={stage.key}
              className={`p-3 rounded-xl border transition-all ${
                isCurrent
                  ? "bg-white border-brand-500 shadow-md ring-2 ring-brand-400/20"
                  : isDone
                  ? "bg-brand-50/40 border-brand-200 text-slate-700"
                  : "bg-slate-50/60 border-slate-200 text-slate-400 opacity-60"
              }`}
            >
              <div className="flex items-center space-x-2 mb-1.5">
                <div
                  className={`w-6 h-6 rounded-lg flex items-center justify-center text-xs ${
                    isCurrent
                      ? "bg-brand-600 text-white font-bold"
                      : isDone
                      ? "bg-brand-200 text-brand-800"
                      : "bg-slate-200 text-slate-500"
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                </div>
                <span className={`text-xs font-semibold ${isCurrent ? "text-brand-900" : ""}`}>
                  {stage.label}
                </span>
              </div>
              <p className="text-[11px] leading-tight text-slate-500 line-clamp-2">
                {stage.description}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
