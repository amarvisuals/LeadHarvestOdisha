import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Pricing (INR) – B2B Lead Generation Plans | LeadHarvest India",
  description:
    "Start with 4 free guest tries. Upgrade to Starter (₹499/mo), Pro (₹1,499/mo), or Agency (₹3,999/mo) for All-India leads, No-Website filter & Excel export.",
  path: "/pricing",
});

export default function PricingLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
