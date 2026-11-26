"use client";

import React, { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import HourglassTimer from "@/components/HourglassTimer";
import RingLoader from "@/components/RingLoader";
import ProgressLine from "@/components/ProgressLine";
import StageStepper from "@/components/StageStepper";
import SuccessConfetti from "@/components/SuccessConfetti";
import { 
  Pause, Play, XCircle, Download, RotateCcw, 
  MapPin, Tag, ShieldCheck, Clock, AlertTriangle 
} from "lucide-react";

interface JobState {
  id: string;
  status: string;
  adapter_name: string;
  total_found: number;
  duplicates_skipped: number;
  new_leads: number;
  progress_pct: number;
  current_stage: string;
  current_detail: string;
  current_city?: string;
  current_category?: string;
  verification_needed?: boolean;
  verification_message?: string;
  error_message?: string;
  excel_file?: string;
  elapsed_seconds?: number;
  estimated_remaining_seconds?: number;
  friendly_tip?: string;
}

export default function ProgressPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params?.jobId as string;

  const [job, setJob] = useState<JobState | null>(null);
  const [isActionLoading, setIsActionLoading] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!jobId) return;
    let isMounted = true;
    let pollInterval: NodeJS.Timeout | null = null;

    // Fetch initial job state immediately so UI renders without waiting for first SSE tick
    fetch(`/api/jobs/${jobId}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (isMounted && data) {
          setJob(data);
        }
      })
      .catch(() => {});

    // Connect directly to FastAPI SSE stream to bypass Next.js proxy buffering
    const sseHost =
      process.env.NEXT_PUBLIC_API_URL ||
      (typeof window !== "undefined" ? `http://${window.location.hostname}:8000` : "http://127.0.0.1:8000");
    const es = new EventSource(`${sseHost}/api/jobs/${jobId}/events`);
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (isMounted) setJob(data);
        if (data.status === "completed" || data.status === "failed" || data.status === "cancelled") {
          es.close();
          if (pollInterval) clearInterval(pollInterval);
        }
      } catch (e) {
        console.error("SSE parse error:", e);
      }
    };

    es.onerror = () => {
      es.close();
      // Fallback polling if SSE connection closes or is unavailable
      if (!pollInterval && isMounted) {
        pollInterval = setInterval(async () => {
          try {
            const res = await fetch(`/api/jobs/${jobId}`);
            if (res.ok) {
              const data = await res.json();
              if (isMounted) setJob(data);
              if (data.status === "completed" || data.status === "failed" || data.status === "cancelled") {
                if (pollInterval) clearInterval(pollInterval);
              }
            }
          } catch (e) {
            // ignore
          }
        }, 1000);
      }
    };

    return () => {
      isMounted = false;
      es.close();
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [jobId]);

  const handlePause = async () => {
    setIsActionLoading(true);
    await fetch(`/api/jobs/${jobId}/pause`, { method: "POST" });
    setIsActionLoading(false);
  };

  const handleResume = async () => {
    setIsActionLoading(true);
    await fetch(`/api/jobs/${jobId}/resume`, { method: "POST" });
    setIsActionLoading(false);
  };

  const handleCancel = async () => {
    if (!confirm("Are you sure you want to stop? Leads collected so far will still be preserved in your Excel file.")) return;
    setIsActionLoading(true);
    await fetch(`/api/jobs/${jobId}/cancel`, { method: "POST" });
    setIsActionLoading(false);
  };

  if (!job) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="w-12 h-12 border-4 border-brand-200 border-t-brand-600 rounded-full animate-spin" />
        <p className="text-slate-600 font-medium text-sm">Connecting to LeadHarvest engine...</p>
      </div>
    );
  }

  const isRunning = job.status === "running" || job.status === "pending";
  const isPaused = job.status === "paused";
  const isCompleted = job.status === "completed";
  const isCancelled = job.status === "cancelled";
  const isFailed = job.status === "failed";

  const elapsedFmt = `${Math.floor((job.elapsed_seconds || 0) / 60)}m ${(job.elapsed_seconds || 0) % 60}s`;
  const remainingFmt = job.estimated_remaining_seconds && job.estimated_remaining_seconds > 0
    ? `${Math.floor(job.estimated_remaining_seconds / 60)}m ${job.estimated_remaining_seconds % 60}s`
    : "Calculating...";

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-20">
      {/* Top Banner: Verification Alert if CAPTCHA encountered */}
      {job.verification_needed && (
        <div className="p-5 rounded-2xl bg-amber-50 border-2 border-amber-300 text-amber-900 shadow-sm flex items-start justify-between">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="w-6 h-6 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <h3 className="font-bold text-sm">Quick Verification Requested</h3>
              <p className="text-xs text-amber-800 mt-1">
                {job.verification_message || "The source website requested a quick check. Please complete it in your visible browser window, then click Resume."}
              </p>
            </div>
          </div>
          <button
            onClick={handleResume}
            className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white font-bold text-xs rounded-xl shadow-sm transition-colors shrink-0"
          >
            Resume Collection
          </button>
        </div>
      )}

      {/* Main Glassmorphic Progress Container */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-10 shadow-sm space-y-8">
        {/* If Completed: Show Celebratory Success View */}
        {isCompleted ? (
          <div className="space-y-6">
            <SuccessConfetti leadCount={job.new_leads} />

            <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
              <a
                href={`/api/jobs/${job.id}/download`}
                download
                className="w-full sm:w-auto px-8 py-4 bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold text-base rounded-2xl shadow-lg shadow-emerald-600/25 flex items-center justify-center space-x-2 transition-all hover:scale-[1.02] active:scale-[0.98]"
              >
                <Download className="w-5 h-5" />
                <span>Download Excel (.xlsx)</span>
              </a>

              <Link
                href="/"
                className="w-full sm:w-auto px-6 py-4 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-sm rounded-2xl flex items-center justify-center space-x-2 transition-colors"
              >
                <RotateCcw className="w-4 h-4" />
                <span>Start Another Collection</span>
              </Link>
            </div>
          </div>
        ) : (
          /* Live Progress Animated Centerpiece */
          <div className="flex flex-col items-center justify-center space-y-6">
            {/* Hourglass with Rotating Rings */}
            <div className="relative flex items-center justify-center">
              <RingLoader percentage={job.progress_pct} size={200} strokeWidth={8} />
              <div className="absolute inset-0 flex items-center justify-center">
                <HourglassTimer isRunning={isRunning} isCompleted={isCompleted} />
              </div>
            </div>

            {/* Stepper with current status message */}
            <StageStepper currentStage={job.current_stage} currentDetail={job.current_detail} />

            {/* Horizontal Line with glowing moving tip */}
            <ProgressLine progressPct={job.progress_pct} />

            {/* Rotating Friendly Tip */}
            <p className="text-xs text-slate-400 italic text-center">
              💡 {job.friendly_tip || "You can keep this tab open. We'll keep working."}
            </p>
          </div>
        )}

        {/* Live Counters Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
          <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/70">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Total Found</span>
            <span className="text-xl font-black text-slate-900">{job.total_found.toLocaleString()}</span>
          </div>

          <div className="p-3.5 rounded-2xl bg-amber-50/60 border border-amber-200/70">
            <span className="text-[10px] font-bold uppercase tracking-wider text-amber-700 block">Duplicates Skipped</span>
            <span className="text-xl font-black text-amber-800">{job.duplicates_skipped.toLocaleString()}</span>
          </div>

          <div className="p-3.5 rounded-2xl bg-emerald-50/60 border border-emerald-200/70">
            <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700 block">New Clean Leads</span>
            <span className="text-xl font-black text-emerald-800">{job.new_leads.toLocaleString()}</span>
          </div>

          <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/70">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Elapsed / Est. Left</span>
            <div className="text-xs font-bold text-slate-800 flex items-center space-x-1 mt-1">
              <Clock className="w-3.5 h-3.5 text-slate-400" />
              <span>{elapsedFmt} / {isCompleted ? "0s" : remainingFmt}</span>
            </div>
          </div>
        </div>

        {/* Active Search Context */}
        {(job.current_city || job.current_category) && !isCompleted && (
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/60 flex items-center justify-between text-xs text-slate-600">
            <span className="flex items-center space-x-1.5">
              <MapPin className="w-3.5 h-3.5 text-brand-600" />
              <span>Current City: <strong className="text-slate-900">{job.current_city || "All"}</strong></span>
            </span>
            <span className="flex items-center space-x-1.5">
              <Tag className="w-3.5 h-3.5 text-brand-600" />
              <span>Category: <strong className="text-slate-900">{job.current_category || "All"}</strong></span>
            </span>
          </div>
        )}

        {/* Execution Controls: Pause, Resume, Cancel */}
        {!isCompleted && !isCancelled && !isFailed && (
          <div className="flex items-center justify-center space-x-3 pt-4 border-t border-slate-100">
            {isPaused ? (
              <button
                type="button"
                disabled={isActionLoading}
                onClick={handleResume}
                className="px-5 py-2.5 bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs rounded-xl shadow-sm flex items-center space-x-1.5 transition-colors"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Resume</span>
              </button>
            ) : (
              <button
                type="button"
                disabled={isActionLoading}
                onClick={handlePause}
                className="px-5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl flex items-center space-x-1.5 transition-colors"
              >
                <Pause className="w-3.5 h-3.5 fill-current" />
                <span>Pause</span>
              </button>
            )}

            <button
              type="button"
              disabled={isActionLoading}
              onClick={handleCancel}
              className="px-5 py-2.5 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 font-bold text-xs rounded-xl flex items-center space-x-1.5 transition-colors"
            >
              <XCircle className="w-3.5 h-3.5" />
              <span>Stop & Save Leads</span>
            </button>
          </div>
        )}

        {/* Cancelled Notice with partial download */}
        {isCancelled && (
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-center space-y-3">
            <p className="text-sm font-bold text-slate-800">Job Stopped by User</p>
            <p className="text-xs text-slate-500">
              {job.new_leads} leads were harvested before stopping. Your partial Excel file is ready:
            </p>
            <a
              href={`/api/jobs/${job.id}/download`}
              download
              className="inline-flex items-center space-x-2 px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl shadow-sm"
            >
              <Download className="w-4 h-4" />
              <span>Download Harvested Leads ({job.new_leads})</span>
            </a>
          </div>
        )}

        {/* Failure Recovery */}
        {isFailed && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-center space-y-3">
            <p className="text-sm font-bold text-rose-800">Collection Stopped</p>
            <p className="text-xs text-rose-600 max-w-md mx-auto">
              {job.error_message || "An issue occurred during data collection."}
            </p>
            <Link
              href="/"
              className="inline-flex items-center space-x-1.5 px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold rounded-xl shadow-sm"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Try Again</span>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
