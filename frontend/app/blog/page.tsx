import type { Metadata } from "next";
import Link from "next/link";
import JsonLd from "@/components/JsonLd";
import { getAllStaticPosts, getReadingTimeMinutes } from "@/lib/blog-data";
import { buildMetadata, breadcrumbSchema } from "@/lib/seo";
import { BookOpen, ArrowRight, Clock } from "lucide-react";

export const metadata: Metadata = buildMetadata({
  title: "B2B Lead Generation Blog & Guides | LeadHarvest India",
  description:
    "Practical guides for Indian web designers, digital marketers, and B2B sales teams: finding businesses without websites, scripts, Excel workflows, and DPDP compliance.",
  path: "/blog",
});

export default function BlogIndexPage({
  searchParams,
}: {
  searchParams?: { q?: string };
}) {
  const allPosts = getAllStaticPosts();
  const q = (searchParams?.q || "").trim().toLowerCase();
  const posts = q
    ? allPosts.filter((p) => p.title.toLowerCase().includes(q) || p.excerpt.toLowerCase().includes(q))
    : allPosts;

  const categories = Array.from(new Set(allPosts.map((p) => p.category)));
  const featured = posts[0];
  const rest = posts.slice(1);

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-16">
      <JsonLd data={breadcrumbSchema([{ name: "Home", path: "/" }, { name: "Blog", path: "/blog" }])} />

      <div className="text-center space-y-3 pt-2">
        <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-brand-50 text-brand-700 text-xs font-bold border border-brand-200">
          <BookOpen className="w-3.5 h-3.5" />
          <span>LeadHarvest India Knowledge Hub</span>
        </span>
        <h1 className="text-3xl sm:text-4xl font-black text-slate-900">B2B Lead Generation &amp; Agency Growth Blog</h1>
        <p className="text-sm text-slate-600 max-w-xl mx-auto">
          Step-by-step playbooks for finding local clients, pitching websites, and keeping clean Excel databases in India.
        </p>

        {/* Category Filter Links */}
        <div className="flex flex-wrap justify-center gap-2 pt-2">
          <Link href="/blog" className="px-3 py-1 rounded-full text-xs font-bold bg-slate-900 text-white">
            All Articles ({allPosts.length})
          </Link>
          {categories.map((cat) => (
            <Link
              key={cat}
              href={`/blog/category/${encodeURIComponent(cat.toLowerCase().replace(/[^a-z0-9]+/g, "-"))}`}
              className="px-3 py-1 rounded-full text-xs font-semibold bg-white border border-slate-200 text-slate-700 hover:border-brand-400"
            >
              {cat}
            </Link>
          ))}
        </div>
      </div>

      {/* Featured Post */}
      {featured && (
        <Link
          href={`/blog/${featured.slug}`}
          className="block bg-gradient-to-br from-brand-800 to-brand-600 text-white rounded-3xl p-8 shadow-md hover:shadow-lg transition-all space-y-3"
        >
          <span className="px-2.5 py-0.5 rounded-full bg-white/15 text-[11px] font-bold uppercase tracking-wider">
            Featured · {featured.category}
          </span>
          <h2 className="text-2xl sm:text-3xl font-black leading-tight">{featured.title}</h2>
          <p className="text-sm text-brand-100 max-w-2xl">{featured.excerpt}</p>
          <span className="inline-flex items-center space-x-1.5 text-xs font-bold text-amber-300 pt-1">
            <span>Read Full Guide ({getReadingTimeMinutes(featured.content_md)} min read)</span>
            <ArrowRight className="w-4 h-4" />
          </span>
        </Link>
      )}

      {/* Articles Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {rest.map((post) => (
          <Link
            key={post.slug}
            href={`/blog/${post.slug}`}
            className="bg-white rounded-2xl border border-slate-200 p-5 hover:border-brand-400 hover:shadow-md transition-all flex flex-col justify-between space-y-4"
          >
            <div className="space-y-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-brand-700">{post.category}</span>
              <h2 className="text-base font-extrabold text-slate-900 leading-snug">{post.title}</h2>
              <p className="text-xs text-slate-600 line-clamp-3">{post.excerpt}</p>
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-100">
              <span className="flex items-center space-x-1">
                <Clock className="w-3 h-3" />
                <span>{getReadingTimeMinutes(post.content_md)} min</span>
              </span>
              <span className="text-brand-700 font-bold">Read →</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
