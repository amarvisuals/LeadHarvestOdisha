import type { Metadata } from "next";
import Link from "next/link";
import { getAllStaticPosts } from "@/lib/blog-data";
import { buildMetadata } from "@/lib/seo";

export function generateMetadata({ params }: { params: { cat: string } }): Metadata {
  return buildMetadata({
    title: `${params.cat.replace(/-/g, " ")} Articles | LeadHarvest India Blog`,
    description: "Curated B2B lead generation guides and scripts for Indian agencies.",
    path: `/blog/category/${params.cat}`,
  });
}

export default function BlogCategoryPage({ params }: { params: { cat: string } }) {
  const posts = getAllStaticPosts().filter(
    (p) => p.category.toLowerCase().replace(/[^a-z0-9]+/g, "-") === params.cat
  );

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-16">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-black text-slate-900 capitalize">
          Category: {params.cat.replace(/-/g, " ")}
        </h1>
        <Link href="/blog" className="text-xs font-bold text-brand-700 hover:underline">← All Posts</Link>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {posts.map((p) => (
          <Link key={p.slug} href={`/blog/${p.slug}`} className="bg-white rounded-2xl border border-slate-200 p-5 hover:border-brand-400 space-y-2">
            <h2 className="text-base font-bold text-slate-900">{p.title}</h2>
            <p className="text-xs text-slate-600">{p.excerpt}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
