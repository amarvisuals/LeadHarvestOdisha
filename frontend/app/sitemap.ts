import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/seo";
import { FEATURES_DATA, USE_CASES_DATA } from "@/lib/marketing-data";
import { getAllStaticPosts } from "@/lib/blog-data";
import { getBatch1LocalUrls } from "@/lib/local-seo";

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();

  const staticRoutes = [
    "",
    "/pricing",
    "/about",
    "/contact",
    "/blog",
    "/tools",
    "/tools/pitch-generator",
    "/tools/agency-roi-calculator",
    "/tools/whatsapp-link-generator",
    "/tools/excel-lead-templates",
    "/privacy",
    "/terms",
    "/refund",
  ].map((path) => ({
    url: `${SITE_URL}${path}`,
    lastModified: now,
    changeFrequency: "weekly" as const,
    priority: path === "" ? 1.0 : 0.8,
  }));

  const featureRoutes = FEATURES_DATA.map((f) => ({
    url: `${SITE_URL}/features/${f.slug}`,
    lastModified: now,
    changeFrequency: "monthly" as const,
    priority: 0.8,
  }));

  const useCaseRoutes = USE_CASES_DATA.map((u) => ({
    url: `${SITE_URL}/use-cases/${u.slug}`,
    lastModified: now,
    changeFrequency: "monthly" as const,
    priority: 0.8,
  }));

  const blogRoutes = getAllStaticPosts().map((p) => ({
    url: `${SITE_URL}/blog/${p.slug}`,
    lastModified: new Date(p.updated_at || p.published_at),
    changeFrequency: "monthly" as const,
    priority: 0.7,
  }));

  const localRoutes = getBatch1LocalUrls().map((l) => ({
    url: `${SITE_URL}/leads/${l.state}/${l.city}/${l.category}`,
    lastModified: now,
    changeFrequency: "weekly" as const,
    priority: 0.6,
  }));

  return [...staticRoutes, ...featureRoutes, ...useCaseRoutes, ...blogRoutes, ...localRoutes];
}
