"use client";

import React, { useEffect, useState } from "react";
import { UserCircle, Download, Trash2, KeyRound, Save } from "lucide-react";
import { apiFetch } from "@/lib/api";

export default function ProfilePage() {
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [businessType, setBusinessType] = useState("");
  const [gstin, setGstin] = useState("");
  const [marketingOptOut, setMarketingOptOut] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const [curPw, setCurPw] = useState("");
  const [newPw, setNewPw] = useState("");

  useEffect(() => {
    apiFetch("/api/auth/me")
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (d?.authenticated && d.user) {
          setName(d.user.name || "");
          setPhone(d.user.phone || "");
          setBusinessType(d.user.business_type || "");
          setGstin(d.user.gstin || "");
          setMarketingOptOut(Boolean(d.user.marketing_unsubscribed));
        }
      });
  }, []);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await apiFetch("/api/auth/profile", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name,
        phone,
        business_type: businessType,
        gstin,
        marketing_unsubscribed: marketingOptOut,
      }),
    });
    if (res.ok) setMsg("Profile saved.");
  };

  const handleChangePw = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await apiFetch("/api/auth/change-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ current_password: curPw, new_password: newPw }),
    });
    const data = await res.json();
    setMsg(res.ok ? "Password updated." : data.detail || "Failed to update password.");
    setCurPw("");
    setNewPw("");
  };

  const handleDeleteAccount = async () => {
    if (!confirm("Permanently delete your account, runs, and Known Records? This cannot be undone.")) return;
    const res = await apiFetch("/api/auth/delete-account", { method: "DELETE" });
    if (res.ok) window.location.href = "/";
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6 pb-20">
      <div className="pb-4 border-b border-slate-200">
        <h1 className="text-2xl font-black text-slate-900 flex items-center space-x-2">
          <UserCircle className="w-6 h-6 text-brand-600" />
          <span>Profile &amp; Privacy (DPDP Act 2023)</span>
        </h1>
      </div>

      {msg && (
        <div className="p-3 rounded-xl bg-brand-50 border border-brand-200 text-brand-800 text-xs font-semibold">
          {msg}
        </div>
      )}

      <form onSubmit={handleSaveProfile} className="bg-white rounded-2xl border border-slate-200 p-6 space-y-4 text-xs">
        <h2 className="text-sm font-bold text-slate-900">Account Details</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block font-semibold text-slate-600 mb-1">Full Name</label>
            <input value={name} onChange={(e) => setName(e.target.value)} className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl" />
          </div>
          <div>
            <label className="block font-semibold text-slate-600 mb-1">Phone / WhatsApp</label>
            <input value={phone} onChange={(e) => setPhone(e.target.value)} className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl" />
          </div>
          <div>
            <label className="block font-semibold text-slate-600 mb-1">Business Type</label>
            <input value={businessType} onChange={(e) => setBusinessType(e.target.value)} className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl" />
          </div>
          <div>
            <label className="block font-semibold text-slate-600 mb-1">GSTIN (Optional for Invoices)</label>
            <input value={gstin} onChange={(e) => setGstin(e.target.value)} placeholder="21AAAAA0000A1Z5" className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl" />
          </div>
        </div>
        <label className="flex items-center space-x-2 cursor-pointer">
          <input type="checkbox" checked={marketingOptOut} onChange={(e) => setMarketingOptOut(e.target.checked)} />
          <span>Unsubscribe from product updates &amp; marketing emails</span>
        </label>
        <button type="submit" className="px-4 py-2 bg-brand-600 text-white font-bold rounded-xl inline-flex items-center space-x-1.5">
          <Save className="w-3.5 h-3.5" />
          <span>Save Changes</span>
        </button>
      </form>

      <form onSubmit={handleChangePw} className="bg-white rounded-2xl border border-slate-200 p-6 space-y-4 text-xs">
        <h2 className="text-sm font-bold text-slate-900 flex items-center space-x-1.5">
          <KeyRound className="w-4 h-4 text-brand-600" />
          <span>Change Password</span>
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <input type="password" required value={curPw} onChange={(e) => setCurPw(e.target.value)} placeholder="Current Password" className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl" />
          <input type="password" required minLength={8} value={newPw} onChange={(e) => setNewPw(e.target.value)} placeholder="New Password (min 8 chars)" className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl" />
        </div>
        <button type="submit" className="px-4 py-2 bg-slate-900 text-white font-bold rounded-xl">Update Password</button>
      </form>

      <div className="bg-white rounded-2xl border border-slate-200 p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-xs">
        <div>
          <h2 className="text-sm font-bold text-slate-900">Data Portability &amp; Erasure</h2>
          <p className="text-slate-500">Download a copy of your account data or permanently delete your account.</p>
        </div>
        <div className="flex items-center space-x-2">
          <a href="/api/auth/export-my-data" download="my_leadharvest_data.json" className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold rounded-xl inline-flex items-center space-x-1.5">
            <Download className="w-3.5 h-3.5" />
            <span>Download My Data</span>
          </a>
          <button onClick={handleDeleteAccount} className="px-3.5 py-2 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 font-bold rounded-xl inline-flex items-center space-x-1.5">
            <Trash2 className="w-3.5 h-3.5" />
            <span>Delete Account</span>
          </button>
        </div>
      </div>
    </div>
  );
}
