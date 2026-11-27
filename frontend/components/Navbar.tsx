"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Database, History, Sparkles, MapPin, CreditCard,
  ShieldCheck, UserCircle, LogIn, AlertTriangle, LogOut
} from "lucide-react";
import { apiFetch, trackEvent } from "@/lib/api";

export interface AuthState {
  authenticated: boolean;
  impersonated_by?: string | null;
  user?: {
    id: string;
    name: string;
    email: string;
    role: string;
  };
  plan?: {
    id: string;
    name: string;
    max_states: number;
    allow_advanced_filters: boolean;
    allow_all_filters: boolean;
  };
  guest?: {
    runs_used: number;
    max_tries: number;
    remaining_tries: number | null;
    unlimited?: boolean;
  };
}

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [auth, setAuth] = useState<AuthState | null>(null);
  const [banner, setBanner] = useState("");
  const [showConsent, setShowConsent] = useState(false);

  useEffect(() => {
    apiFetch("/api/auth/me")
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => d && setAuth(d))
      .catch(() => {});

    apiFetch("/api/config/public-settings")
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (d?.announcement_banner) setBanner(d.announcement_banner);
      })
      .catch(() => {});

    if (typeof window !== "undefined" && !localStorage.getItem("lh_cookie_consent")) {
      setShowConsent(true);
    }
    trackEvent("pageview", { path: pathname });
  }, [pathname]);

  const handleStopImpersonation = async () => {
    await apiFetch("/api/auth/stop-impersonation", { method: "POST" });
    window.location.href = "/admin";
  };

  const handleLogout = async () => {
    await apiFetch("/api/auth/logout", { method: "POST" });
    window.location.href = "/";
  };

  const handleConsent = (choice: "accepted" | "declined") => {
    localStorage.setItem("lh_cookie_consent", choice);
    setShowConsent(false);
  };

  const navItems = [
    { href: "/", label: "Collector", icon: Sparkles },
    { href: "/pricing", label: "Pricing", icon: CreditCard },
    { href: "/history", label: "History", icon: History },
    { href: "/settings", label: "Known Leads", icon: Database },
  ];

  return (
    <>
      {auth?.impersonated_by && (
        <div className="bg-rose-600 text-white text-xs font-bold py-2 px-4 flex items-center justify-center space-x-3">
          <AlertTriangle className="w-4 h-4" />
          <span>You are viewing as {auth.user?.email} (Admin: {auth.impersonated_by})</span>
          <button
            onClick={handleStopImpersonation}
            className="px-2.5 py-0.5 bg-white text-rose-700 rounded-md hover:bg-rose-50"
          >
            Exit Impersonation
          </button>
        </div>
      )}

      {banner && (
        <div className="bg-amber-50 border-b border-amber-200 text-amber-900 text-xs font-medium py-1.5 px-4 text-center">
          {banner}
        </div>
      )}

      <header className="sticky top-0 z-40 bg-white/90 backdrop-blur-md border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-2">
          <Link href="/" className="flex items-center space-x-2.5 group shrink-0">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-700 to-brand-500 flex items-center justify-center text-white shadow-md shadow-brand-500/20">
              <MapPin className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-1.5">
                <span className="font-bold text-base sm:text-lg text-slate-900 tracking-tight">LeadHarvest</span>
                <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-brand-50 text-brand-700 border border-brand-200 rounded-full">
                  India
                </span>
              </div>
              <p className="text-[11px] text-slate-500 hidden md:block">B2B Lead &amp; Website Pitch Engine</p>
            </div>
          </Link>

          <nav className="flex items-center space-x-1 overflow-x-auto">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center space-x-1.5 px-2.5 sm:px-3 py-1.5 rounded-xl text-xs sm:text-sm font-medium transition-colors whitespace-nowrap ${
                    isActive
                      ? "bg-brand-50 text-brand-700 font-semibold"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? "text-brand-600" : "text-slate-400"}`} />
                  <span className="hidden sm:inline">{item.label}</span>
                </Link>
              );
            })}

            {auth?.authenticated ? (
              <div className="flex items-center space-x-1.5 pl-2 border-l border-slate-200 ml-1">
                <Link
                  href="/billing"
                  className="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100"
                >
                  {auth.plan?.name || "Free"}
                </Link>
                {auth.user?.role === "admin" && (
                  <Link
                    href="/admin"
                    className="px-2.5 py-1 rounded-xl text-xs font-bold bg-slate-900 text-white hover:bg-slate-800 flex items-center space-x-1"
                  >
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span className="hidden md:inline">Admin</span>
                  </Link>
                )}
                <Link
                  href="/profile"
                  className="p-1.5 rounded-xl text-slate-600 hover:bg-slate-100"
                  title={auth.user?.email}
                >
                  <UserCircle className="w-5 h-5" />
                </Link>
                <button
                  onClick={handleLogout}
                  className="p-1.5 rounded-xl text-slate-400 hover:text-rose-600 hover:bg-rose-50"
                  title="Sign Out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-2 pl-2 border-l border-slate-200 ml-1">
                {auth?.guest && !auth.guest.unlimited && auth.guest.max_tries > 0 && (
                  <span className="hidden lg:inline-flex px-2.5 py-1 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-800 border border-amber-200">
                    {auth.guest.remaining_tries} of {auth.guest.max_tries} free tries left
                  </span>
                )}
                <Link
                  href="/login"
                  className="px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-100 flex items-center space-x-1"
                >
                  <LogIn className="w-3.5 h-3.5" />
                  <span>Sign In</span>
                </Link>
                <Link
                  href="/signup"
                  className="px-3 py-1.5 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-700 text-white shadow-xs"
                >
                  Free Account
                </Link>
              </div>
            )}
          </nav>
        </div>
      </header>

      {showConsent && (
        <div className="fixed bottom-4 right-4 z-50 max-w-sm bg-white border border-slate-200 rounded-2xl shadow-xl p-4 text-xs space-y-2.5">
          <p className="font-bold text-slate-900">Privacy-First Analytics</p>
          <p className="text-slate-600 leading-relaxed">
            We use lightweight first-party analytics (no third-party trackers) to improve LeadHarvest India.
          </p>
          <div className="flex items-center justify-end space-x-2">
            <button
              onClick={() => handleConsent("declined")}
              className="px-3 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 font-medium"
            >
              Decline
            </button>
            <button
              onClick={() => handleConsent("accepted")}
              className="px-3 py-1.5 rounded-lg bg-brand-600 text-white font-semibold hover:bg-brand-700"
            >
              Accept
            </button>
          </div>
        </div>
      )}
    </>
  );
}
