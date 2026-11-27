import { NextResponse } from "next/server";
import { SITE_URL } from "@/lib/seo";
import { resolveStateHub } from "@/lib/state-seo-data";

export async function GET(
  _req: Request,
  { params }: { params: { state: string } }
) {
  const st = resolveStateHub(params.state);
  if (!st) {
    return new NextResponse("Not found", { status: 404 });
  }

  const urls: string[] = [
    `${SITE_URL}/leads/${st.slug}`,
    ...st.cities.slice(0, 15).map((c) => `${SITE_URL}/leads/${st.slug}/${c.id}`),
    ...st.topCategories.map((cat) => `${SITE_URL}/leads/${st.slug}/${cat.slug}`),
  ];
  if (st.isTop12) {
    urls.push(`${SITE_URL}/reports/${st.slug}`);
  }

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls
  .map(
    (u) => `  <url>
    <loc>${u}</loc>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>`
  )
  .join("\n")}
</urlset>`;

  return new NextResponse(xml, {
    headers: { "Content-Type": "application/xml" },
  });
}
