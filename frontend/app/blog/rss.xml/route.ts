import { NextResponse } from "next/server";
import { getAllStaticPosts } from "@/lib/blog-data";
import { SITE_URL, SITE_NAME } from "@/lib/seo";

export async function GET() {
  const posts = getAllStaticPosts();
  const itemsXml = posts
    .map(
      (p) => `
    <item>
      <title><![CDATA[${p.title}]]></title>
      <link>${SITE_URL}/blog/${p.slug}</link>
      <guid>${SITE_URL}/blog/${p.slug}</guid>
      <pubDate>${new Date(p.published_at).toUTCString()}</pubDate>
      <description><![CDATA[${p.excerpt}]]></description>
    </item>`
    )
    .join("");

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>${SITE_NAME} Blog</title>
    <link>${SITE_URL}/blog</link>
    <description>B2B lead generation guides, scripts, and agency playbooks for India.</description>
    <language>en-in</language>
    ${itemsXml}
  </channel>
</rss>`;

  return new NextResponse(xml, {
    headers: { "Content-Type": "application/xml; charset=utf-8" },
  });
}
