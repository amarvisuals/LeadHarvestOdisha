import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import JsonLd from "@/components/JsonLd";
import {
  getAllStaticPosts,
  getStaticPostBySlug,
  getReadingTimeMinutes,
  extractHeadings,
  renderMarkdownToHtml,
} from "@/lib/blog-data";
import { buildMetadata, articleSchema, breadcrumbSchema, faqSchema } from "@/lib/seo";
import { Clock, ArrowRight, UserCheck } from "lucide-react";

export function generateStaticParams() {
  return getAllStaticPosts().map((p) => ({ slug: p.slug }));
}

export function generateMetadata({ params }: { params: { slug: string } }): Metadata {
  const post = getStaticPostBySlug(params.slug);
  if (!post) return {};
  return buildMetadata({
    title: post.meta_title || post.title,
    description: post.meta_description || post.excerpt,
    path: `/blog/${post.slug}`,
    type: "article",
  });
}

export default function BlogPostPage({ params }: { params: { slug: string } }) {
  const post = getStaticPostBySlug(params.slug);
  if (!post) notFound();

  const headings = extractHeadings(post.content_md);
  const html = renderMarkdownToHtml(post.content_md);
  const readMins = getReadingTimeMinutes(post.content_md);
  const related = getAllStaticPosts()
    .filter((p) => p.slug !== post.slug)
    .slice(0, 3);

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      <JsonLd
        data={[
          articleSchema({ ...post, description: post.meta_description || post.excerpt }),
          breadcrumbSchema([
            { name: "Home", path: "/" },
            { name: "Blog", path: "/blog" },
            { name: post.title, path: `/blog/${post.slug}` },
          ]),
          ...(post.faqs.length > 0 ? [faqSchema(post.faqs)] : []),
        ]}
      />

      <nav aria-label="Breadcrumb" className="text-xs text-slate-500 flex items-center space-x-2">
        <Link href="/" className="hover:text-brand-700">Home</Link>
        <span>/</span>
        <Link href="/blog" className="hover:text-brand-700">Blog</Link>
        <span>/</span>
        <span className="font-semibold text-slate-800 truncate">{post.title}</span>
      </nav>

      <article className="bg-white rounded-3xl border border-slate-200 p-7 sm:p-10 space-y-6 shadow-sm">
        <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
          <span className="px-2.5 py-0.5 rounded-full bg-brand-50 text-brand-700 font-bold border border-brand-200">
            {post.category}
          </span>
          <span className="flex items-center space-x-1">
            <Clock className="w-3.5 h-3.5" />
            <span>{readMins} min read</span>
          </span>
          <span>Published {new Date(post.published_at).toLocaleDateString("en-IN")}</span>
        </div>

        <h1 className="text-3xl sm:text-4xl font-black text-slate-900 leading-tight">{post.title}</h1>

        {/* Table of Contents */}
        {headings.length > 0 && (
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-xs space-y-1.5">
            <p className="font-bold uppercase tracking-wider text-slate-500 text-[10px]">In This Guide</p>
            <ul className="space-y-1">
              {headings.map((h) => (
                <li key={h.id}>
                  <a href={`#${h.id}`} className="text-brand-700 hover:underline font-medium">
                    • {h.text}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Body */}
        <div dangerouslySetInnerHTML={{ __html: html }} />

        {/* In-Content CTA */}
        <div className="p-6 rounded-2xl bg-gradient-to-r from-brand-700 to-teal-600 text-white flex flex-col sm:flex-row items-center justify-between gap-4 my-6">
          <div>
            <p className="font-black text-base">Find Local Businesses Without a Website in Seconds</p>
            <p className="text-xs text-brand-100">Try 4 free runs in Odisha or unlock all 36 Indian states.</p>
          </div>
          <Link href="/" className="px-5 py-2.5 bg-white text-brand-900 font-bold text-xs rounded-xl inline-flex items-center space-x-1.5 shrink-0">
            <span>Start 4 Free Runs</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {/* FAQ */}
        {post.faqs.length > 0 && (
          <section className="pt-6 border-t border-slate-100 space-y-3">
            <h2 className="text-xl font-extrabold text-slate-900">Frequently Asked Questions</h2>
            {post.faqs.map((f) => (
              <div key={f.question} className="p-4 rounded-2xl bg-slate-50 border border-slate-200">
                <h3 className="text-sm font-bold text-slate-900">{f.question}</h3>
                <p className="text-xs text-slate-600 mt-1">{f.answer}</p>
              </div>
            ))}
          </section>
        )}

        {/* E-E-A-T Author Box */}
        <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 flex items-start space-x-3 text-xs">
          <div className="w-10 h-10 rounded-full bg-brand-600 text-white flex items-center justify-center shrink-0">
            <UserCheck className="w-5 h-5" />
          </div>
          <div>
            <p className="font-bold text-slate-900">{post.author_name}</p>
            <p className="text-slate-600 mt-0.5">{post.author_bio}</p>
          </div>
        </div>
      </article>

      {/* Related Posts */}
      <div className="space-y-3">
        <h2 className="text-lg font-extrabold text-slate-900">Related Articles</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {related.map((r) => (
            <Link key={r.slug} href={`/blog/${r.slug}`} className="bg-white rounded-2xl border border-slate-200 p-4 hover:border-brand-400 text-xs space-y-1.5">
              <span className="text-[10px] font-bold uppercase text-brand-700">{r.category}</span>
              <p className="font-bold text-slate-900">{r.title}</p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
