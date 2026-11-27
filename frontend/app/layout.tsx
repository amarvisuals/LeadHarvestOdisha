import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import "./globals.css";
import Navbar from "@/components/Navbar";
import GoogleAnalytics from "@/components/GoogleAnalytics";
import JsonLd from "@/components/JsonLd";
import { buildMetadata, organizationSchema, websiteSchema, softwareAppSchema } from "@/lib/seo";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });

export const metadata: Metadata = {
  ...buildMetadata({
    title: "LeadHarvest India – B2B Business Leads & No-Website Filter",
    description:
      "Find local business leads from public business directories in India by state, city, and category. Filter businesses without a website and export to Excel.",
    path: "/",
  }),
  verification: {
    google: process.env.NEXT_PUBLIC_GSC_VERIFICATION || undefined,
    other: process.env.NEXT_PUBLIC_BING_VERIFICATION
      ? { "msvalidate.01": process.env.NEXT_PUBLIC_BING_VERIFICATION }
      : undefined,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en-IN" className={inter.variable}>
      <body className="min-h-screen flex flex-col bg-slate-50 text-slate-900 antialiased selection:bg-brand-500 selection:text-white">
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:px-4 focus:py-2 focus:bg-brand-700 focus:text-white focus:rounded-xl focus:text-xs focus:font-bold"
        >
          Skip to main content
        </a>
        <JsonLd data={[organizationSchema(), websiteSchema(), softwareAppSchema()]} />
        <GoogleAnalytics />
        <Navbar />
        <main id="main-content" className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
        <footer className="border-t border-slate-200 bg-white/90 py-10 text-xs text-slate-600">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-2 md:grid-cols-4 gap-6 pb-8 border-b border-slate-100">
            <div className="space-y-2">
              <p className="font-bold text-slate-900">LeadHarvest India</p>
              <p className="text-slate-500 leading-relaxed">
                Business leads data from public business directories in India with smart filters and one-click Excel export.
              </p>
            </div>
            <div className="space-y-1.5">
              <p className="font-bold text-slate-900">Features</p>
              <Link href="/features/no-website-filter" className="block hover:text-brand-700">Find Businesses With No Website</Link>
              <Link href="/features/opportunity-score" className="block hover:text-brand-700">Opportunity Score &amp; Filters</Link>
              <Link href="/features/all-india-coverage" className="block hover:text-brand-700">All 36 States &amp; UTs</Link>
              <Link href="/features/auto-deduplication" className="block hover:text-brand-700">Automatic Deduplication</Link>
              <Link href="/features/excel-export" className="block hover:text-brand-700">One-Click Excel Export</Link>
            </div>
            <div className="space-y-1.5">
              <p className="font-bold text-slate-900">Use Cases &amp; Tools</p>
              <Link href="/use-cases/web-design-agencies" className="block hover:text-brand-700">Web Design Agencies</Link>
              <Link href="/use-cases/seo-digital-marketers" className="block hover:text-brand-700">SEO &amp; Digital Marketers</Link>
              <Link href="/tools/pitch-generator" className="block hover:text-brand-700">Pitch &amp; WhatsApp Generator</Link>
              <Link href="/tools/agency-roi-calculator" className="block hover:text-brand-700">Agency ROI Calculator</Link>
              <Link href="/tools/whatsapp-link-generator" className="block hover:text-brand-700">WhatsApp Link Generator</Link>
              <Link href="/tools/excel-lead-templates" className="block hover:text-brand-700">Free Excel Lead Templates</Link>
            </div>
            <div className="space-y-1.5">
              <p className="font-bold text-slate-900">Resources &amp; Legal</p>
              <Link href="/blog" className="block hover:text-brand-700">B2B Lead Generation Blog</Link>
              <Link href="/pricing" className="block hover:text-brand-700">Pricing (INR)</Link>
              <Link href="/about" className="block hover:text-brand-700">About Us</Link>
              <Link href="/contact" className="block hover:text-brand-700">Contact Support</Link>
              <Link href="/privacy" className="block hover:text-brand-700">Privacy Policy</Link>
              <Link href="/terms" className="block hover:text-brand-700">Terms of Use</Link>
              <Link href="/refund" className="block hover:text-brand-700">Refund Policy</Link>
            </div>
          </div>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-slate-500">
            <p>© {new Date().getFullYear()} LeadHarvest India. Built for Indian B2B agencies &amp; web designers.</p>
            <Link href="/blog/rss.xml" className="hover:text-brand-700">RSS Feed</Link>
          </div>
        </footer>
      </body>
    </html>
  );
}
