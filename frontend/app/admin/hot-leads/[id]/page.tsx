"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft, Flame, Globe, ShieldAlert, CheckCircle2, FileText,
  MessageCircle, Mail, Phone, Download, Trash2, Plus, Activity
} from "lucide-react";
import { apiFetch } from "@/lib/api";

const STAGES = ["New", "Contacted", "Meeting booked", "Proposal sent", "Negotiation", "Won", "Lost"];

export default function HotLeadDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const leadId = params?.id;

  const [data, setData] = useState<any>(null);
  const [lang, setLang] = useState<"english" | "hindi" | "odia">("english");
  const [noteTitle, setNoteTitle] = useState("");
  const [noteBody, setNoteBody] = useState("");
  const [taskDue, setTaskDue] = useState("");
  const [actType, setActType] = useState<"note" | "task">("note");
  const [toast, setToast] = useState<string | null>(null);
  const [healthLoading, setHealthLoading] = useState(false);

  const notify = (m: string) => {
    setToast(m);
    setTimeout(() => setToast(null), 3500);
  };

  async function loadDetail() {
    if (!leadId) return;
    const res = await apiFetch(`/api/admin/hot-leads/${leadId}`);
    if (res.ok) setData(await res.json());
  }

  useEffect(() => {
    loadDetail();
  }, [leadId]);

  if (!data) {
    return <div className="max-w-5xl mx-auto py-16 text-center text-xs text-slate-500">Loading Hot Lead details...</div>;
  }

  const { lead, activities, attachments, outreach } = data;
  const tpl = outreach?.templates?.[lang];

  async function updateField(patch: Record<string, any>) {
    const res = await apiFetch(`/api/admin/hot-leads/${leadId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(patch),
    });
    if (res.ok) {
      notify("Lead updated.");
      loadDetail();
    }
  }

  async function runHealthCheck() {
    setHealthLoading(true);
    const res = await apiFetch(`/api/admin/hot-leads/${leadId}/health-check`, { method: "POST" });
    setHealthLoading(false);
    if (res.ok) {
      notify("Website health check completed.");
      loadDetail();
    }
  }

  async function downloadProposalPdf() {
    const res = await apiFetch(`/api/admin/hot-leads/${leadId}/proposal-pdf`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        package_name: "Growth Business Website",
        price_range: lead.budget_range || "Rs 9,999 - Rs 14,999",
        timeline: lead.timeline || "7 Business Days",
      }),
    });
    if (res.ok) {
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `proposal_${lead.id}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      notify("1-Page Proposal PDF downloaded.");
      loadDetail();
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-20">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link href="/admin" className="inline-flex items-center space-x-1.5 text-xs font-bold text-slate-600 hover:text-slate-900">
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Admin Panel</span>
        </Link>
        <div className="flex flex-wrap gap-2">
          <button onClick={downloadProposalPdf} className="px-3.5 py-2 rounded-xl bg-brand-600 text-white text-xs font-bold flex items-center space-x-1.5">
            <FileText className="w-3.5 h-3.5" />
            <span>Generate 1-Page Proposal PDF</span>
          </button>
          <a
            href={`/api/admin/hot-leads/${lead.id}/gdpr-export`}
            className="px-3 py-2 rounded-xl bg-white border border-slate-200 text-xs font-bold text-slate-700 flex items-center space-x-1"
          >
            <Download className="w-3.5 h-3.5" />
            <span>DPDP Export</span>
          </a>
          <button
            onClick={async () => {
              if (!window.confirm("Permanently delete this lead & all records?")) return;
              const r = await apiFetch(`/api/admin/hot-leads/${lead.id}`, { method: "DELETE" });
              if (r.ok) router.push("/admin");
            }}
            className="px-3 py-2 rounded-xl bg-rose-50 border border-rose-200 text-xs font-bold text-rose-700 flex items-center space-x-1"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Delete</span>
          </button>
        </div>
      </div>

      {toast && <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold">{toast}</div>}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Contact, Score Breakdown, Health Report, Compliance */}
        <div className="space-y-5">
          <div className="bg-white p-5 rounded-2xl border border-slate-200 space-y-3">
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-lg font-black text-slate-900">{lead.business_name}</h1>
                <p className="text-xs text-slate-500">{lead.name} · {lead.business_type || "Business"}</p>
              </div>
              <span className="px-2.5 py-1 rounded-full text-xs font-black bg-rose-100 text-rose-700 flex items-center space-x-1">
                <Flame className="w-3.5 h-3.5" />
                <span>{lead.temperature} {lead.score}/100</span>
              </span>
            </div>

            <div className="text-xs space-y-1 text-slate-700 pt-2 border-t border-slate-100">
              <p><strong>Phone:</strong> {lead.phone || "—"}</p>
              <p><strong>Email:</strong> {lead.email || "—"}</p>
              <p><strong>Location:</strong> {[lead.city, lead.state].filter(Boolean).join(", ") || "—"}</p>
              <p><strong>Website:</strong> {lead.website || "None listed"}</p>
              <p><strong>Budget / Timeline:</strong> {lead.budget_range || "—"} / {lead.timeline || "—"}</p>
              <p><strong>Source:</strong> {lead.source_type} ({lead.source_name})</p>
              {(lead.utm_source || lead.utm_campaign) && (
                <p><strong>UTM:</strong> {lead.utm_source || "—"} / {lead.utm_medium || "—"} / {lead.utm_campaign || "—"}</p>
              )}
            </div>
          </div>

          {/* Why This Score */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200 space-y-2.5">
            <h2 className="text-xs font-black uppercase text-slate-500">Why This Score ({lead.score}/100)</h2>
            <div className="space-y-1.5 text-xs">
              {(lead.score_breakdown || []).map((b: any, i: number) => (
                <div key={i} className="flex items-center justify-between p-2 rounded-xl bg-slate-50">
                  <span className="text-slate-700">{b.reason}</span>
                  <span className="font-black text-emerald-700">+{b.points}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Website Health Report */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-xs font-black uppercase text-slate-500 flex items-center space-x-1">
                <Globe className="w-3.5 h-3.5" />
                <span>Website Health Report</span>
              </h2>
              <button onClick={runHealthCheck} disabled={healthLoading} className="px-2.5 py-1 rounded-lg bg-slate-900 text-white text-[11px] font-bold">
                {healthLoading ? "Checking..." : "Run Check"}
              </button>
            </div>
            {lead.website_health ? (
              <div className="text-xs space-y-1 text-slate-700">
                <p><strong>DNS:</strong> {lead.website_health.dns_ok ? "OK" : "Failed"} · <strong>HTTPS:</strong> {lead.website_health.https_ok ? "Yes" : "No"}</p>
                <p><strong>HTTP:</strong> {lead.website_health.http_status ?? "—"} · <strong>Mobile Tag:</strong> {lead.website_health.mobile_viewport ? "Yes" : "Missing"}</p>
                <p><strong>Response:</strong> {lead.website_health.response_ms ?? "—"} ms</p>
                <p className="text-rose-700 font-semibold">Issues: {(lead.website_health.issues || []).join(", ") || "None"}</p>
                <p className="text-[10px] text-slate-400">Checked: {lead.website_health.checked_at}</p>
              </div>
            ) : (
              <p className="text-xs text-slate-400">Click &ldquo;Run Check&rdquo; to inspect DNS, HTTPS, speed &amp; mobile tag.</p>
            )}
          </div>

          {/* Consent & DNC Compliance */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200 space-y-2.5 text-xs">
            <h2 className="text-xs font-black uppercase text-slate-500 flex items-center space-x-1">
              <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
              <span>Consent &amp; Compliance</span>
            </h2>
            <p className="text-slate-600">{lead.consent_record}</p>
            <p className="text-[11px] text-slate-400">Terms: {lead.terms_note}</p>
            <button
              onClick={() => updateField({ do_not_contact: !lead.do_not_contact, dnc_reason: !lead.do_not_contact ? "Admin toggled DNC" : "" })}
              className={`w-full py-2 rounded-xl font-bold ${
                lead.do_not_contact ? "bg-rose-600 text-white" : "bg-slate-100 text-slate-800 hover:bg-slate-200"
              }`}
            >
              {lead.do_not_contact ? "Marked DO NOT CONTACT (Click to Unblock)" : "Add to Do Not Contact List"}
            </button>
          </div>
        </div>

        {/* Right 2 Columns: Pipeline, Outreach Templates, Notes/Tasks/Timeline */}
        <div className="lg:col-span-2 space-y-5">
          {/* Pipeline Controls */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200 grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs">
            <div>
              <label className="block font-bold text-slate-500 mb-1">Stage</label>
              <select value={lead.stage} onChange={(e) => updateField({ stage: e.target.value })} className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-white font-bold">
                {STAGES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="block font-bold text-slate-500 mb-1">Deal Value (INR)</label>
              <input
                type="number"
                defaultValue={lead.deal_value_inr}
                onBlur={(e) => updateField({ deal_value_inr: Number(e.target.value) })}
                className="w-full px-3 py-2 rounded-xl border border-slate-200 font-bold"
              />
            </div>
            <div>
              <label className="block font-bold text-slate-500 mb-1">Next Follow-Up</label>
              <input
                type="date"
                defaultValue={lead.next_followup_at ? lead.next_followup_at.slice(0, 10) : ""}
                onChange={(e) => updateField({ next_followup_at: e.target.value ? `${e.target.value}T10:00:00` : "" })}
                className="w-full px-3 py-2 rounded-xl border border-slate-200"
              />
            </div>
            <div>
              <label className="block font-bold text-slate-500 mb-1">Owner</label>
              <input
                defaultValue={lead.owner_name}
                onBlur={(e) => updateField({ owner_name: e.target.value })}
                className="w-full px-3 py-2 rounded-xl border border-slate-200"
              />
            </div>
          </div>

          {/* Message Templates (English / Hindi / Odia) */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200 space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-sm font-black text-slate-900">Outreach Templates (1-Click Manual Send)</h2>
              <div className="flex gap-1">
                {(["english", "hindi", "odia"] as const).map((l) => (
                  <button
                    key={l}
                    onClick={() => setLang(l)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-bold capitalize ${
                      lang === l ? "bg-brand-600 text-white" : "bg-slate-100 text-slate-600"
                    }`}
                  >
                    {l}
                  </button>
                ))}
              </div>
            </div>

            <div className="p-2.5 rounded-xl bg-amber-50 border border-amber-200 text-[11px] text-amber-900 font-medium">
              {outreach?.compliance_reminder}
            </div>

            {outreach?.blocked_by_dnc ? (
              <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 font-bold">
                Outreach blocked: This lead is on the Do Not Contact list ({outreach.dnc_reason || "Opt-out"}).
              </div>
            ) : (
              tpl && (
                <div className="space-y-3 text-xs">
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                    <p className="font-bold text-slate-700">WhatsApp Message</p>
                    <p className="text-slate-600">{tpl.whatsapp}</p>
                    {tpl.wa_url && (
                      <a href={tpl.wa_url} target="_blank" rel="noreferrer" className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 text-white font-bold">
                        <MessageCircle className="w-3.5 h-3.5" />
                        <span>Open WhatsApp (wa.me)</span>
                      </a>
                    )}
                  </div>
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                    <p className="font-bold text-slate-700">Email: {tpl.email_subject}</p>
                    <p className="text-slate-600 whitespace-pre-line">{tpl.email_body}</p>
                    {tpl.mailto_url && (
                      <a href={tpl.mailto_url} className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900 text-white font-bold">
                        <Mail className="w-3.5 h-3.5" />
                        <span>Open Email Client</span>
                      </a>
                    )}
                  </div>
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                    <p className="font-bold text-slate-700 flex items-center space-x-1">
                      <Phone className="w-3.5 h-3.5" />
                      <span>Call Script</span>
                    </p>
                    <p className="text-slate-600 italic">{tpl.call_script}</p>
                  </div>
                </div>
              )
            )}
          </div>

          {/* Notes, Tasks, Attachments & Activity Timeline */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200 space-y-4">
            <h2 className="text-sm font-black text-slate-900 flex items-center space-x-1.5">
              <Activity className="w-4 h-4 text-brand-600" />
              <span>Notes, Follow-Up Tasks &amp; Activity Timeline</span>
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
              <select value={actType} onChange={(e) => setActType(e.target.value as any)} className="px-3 py-2 rounded-xl border border-slate-200 bg-white">
                <option value="note">Add Note</option>
                <option value="task">Add Follow-Up Task</option>
              </select>
              <input value={noteTitle} onChange={(e) => setNoteTitle(e.target.value)} placeholder="Title (e.g. Call back at 4 PM)" className="px-3 py-2 rounded-xl border border-slate-200" />
              <input type="datetime-local" value={taskDue} onChange={(e) => setTaskDue(e.target.value)} className="px-3 py-2 rounded-xl border border-slate-200" />
            </div>
            <textarea rows={2} value={noteBody} onChange={(e) => setNoteBody(e.target.value)} placeholder="Details..." className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs" />
            <div className="flex flex-wrap items-center justify-between gap-2">
              <button
                onClick={async () => {
                  if (!noteTitle.trim()) return;
                  const r = await apiFetch(`/api/admin/hot-leads/${leadId}/activities`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ activity_type: actType, title: noteTitle, body: noteBody, due_at: taskDue || null }),
                  });
                  if (r.ok) {
                    setNoteTitle(""); setNoteBody(""); setTaskDue("");
                    notify("Saved to timeline.");
                    loadDetail();
                  }
                }}
                className="px-4 py-2 rounded-xl bg-brand-600 text-white text-xs font-bold inline-flex items-center space-x-1"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add to Timeline</span>
              </button>
              <label className="text-xs font-semibold text-slate-600 cursor-pointer">
                Attach file:{" "}
                <input
                  type="file"
                  className="text-xs"
                  onChange={async (e) => {
                    const f = e.target.files?.[0];
                    if (!f) return;
                    const fd = new FormData();
                    fd.append("file", f);
                    const r = await apiFetch(`/api/admin/hot-leads/${leadId}/attachments`, { method: "POST", body: fd });
                    if (r.ok) {
                      notify("Attachment uploaded.");
                      loadDetail();
                    }
                  }}
                />
              </label>
            </div>

            {attachments.length > 0 && (
              <div className="text-xs text-slate-600 flex flex-wrap gap-2">
                {attachments.map((att: any) => (
                  <span key={att.id} className="px-2.5 py-1 rounded-lg bg-slate-100 border border-slate-200 font-medium">
                    {att.filename} ({Math.round(att.size_bytes / 1024)} KB)
                  </span>
                ))}
              </div>
            )}

            <div className="divide-y divide-slate-100 text-xs">
              {activities.map((a: any) => (
                <div key={a.id} className="py-2.5 flex items-start justify-between gap-2">
                  <div>
                    <p className="font-bold text-slate-900">
                      <span className="uppercase text-[10px] text-brand-700 mr-1.5">[{a.activity_type}]</span>
                      {a.title}
                    </p>
                    {a.body && <p className="text-slate-600 mt-0.5">{a.body}</p>}
                    <p className="text-[10px] text-slate-400 mt-0.5">{a.created_at} {a.actor_email ? `· ${a.actor_email}` : ""}</p>
                  </div>
                  {a.activity_type === "task" && (
                    <button
                      onClick={async () => {
                        await apiFetch(`/api/admin/hot-leads/${leadId}/activities/${a.id}?completed=${!a.completed}`, { method: "PATCH" });
                        loadDetail();
                      }}
                      className={`px-2 py-1 rounded-lg text-[10px] font-bold ${a.completed ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-600"}`}
                    >
                      {a.completed ? "Done" : "Mark Done"}
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
