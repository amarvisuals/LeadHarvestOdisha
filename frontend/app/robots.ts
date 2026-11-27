import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/seo";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: ["/", "/pricing", "/features/", "/use-cases/", "/blog", "/leads/", "/tools/", "/about", "/contact"],
        disallow: [
          "/admin",
          "/api/",
          "/billing",
          "/profile",
          "/progress/",
          "/history",
          "/settings",
          "/*?*",
        ],
      },
    ],
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
