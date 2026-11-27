import Link from "next/link";
import { Search, ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <div className="max-w-xl mx-auto py-20 text-center space-y-5 bg-white rounded-3xl border border-slate-200 p-8 shadow-sm">
      <div className="w-14 h-14 rounded-2xl bg-brand-50 text-brand-700 flex items-center justify-center mx-auto">
        <Search className="w-7 h-7" />
      </div>
      <h1 className="text-3xl font-black text-slate-900">Page Not Found (404)</h1>
      <p className="text-sm text-slate-600">
        The page you are looking for may have moved. Explore our lead collector, free agency tools, or B2B guides below.
      </p>
      <div className="flex flex-wrap items-center justify-center gap-2 text-xs font-bold pt-2">
        <Link href="/" className="px-4 py-2.5 bg-brand-600 text-white rounded-xl inline-flex items-center space-x-1.5">
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Home Collector</span>
        </Link>
        <Link href="/features/no-website-filter" className="px-4 py-2.5 bg-slate-100 text-slate-800 rounded-xl">
          No-Website Filter
        </Link>
        <Link href="/tools" className="px-4 py-2.5 bg-slate-100 text-slate-800 rounded-xl">
          Free Tools
        </Link>
        <Link href="/blog" className="px-4 py-2.5 bg-slate-100 text-slate-800 rounded-xl">
          Blog
        </Link>
      </div>
    </div>
  );
}
