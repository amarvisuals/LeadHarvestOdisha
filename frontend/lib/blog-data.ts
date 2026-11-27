import defaultPosts from "./default-posts.json";
import { getStateBlogPosts } from "./state-seo-data";

export interface BlogPostItem {
  slug: string;
  title: string;
  meta_title: string;
  meta_description: string;
  focus_keyword?: string;
  category: string;
  tags: string[];
  excerpt: string;
  content_md: string;
  faqs: Array<{ question: string; answer: string }>;
  author_name: string;
  author_bio: string;
  published_at: string;
  updated_at?: string;
}

export function getAllStaticPosts(): BlogPostItem[] {
  const statePosts = getStateBlogPosts().map((p) => ({
    ...p,
    tags: [p.state_slug, p.category],
    faqs: [],
    author_bio: "Founder of LeadHarvest India & B2B Web Systems Architect.",
  }));
  return [...(defaultPosts as BlogPostItem[]), ...statePosts];
}

export function getStaticPostBySlug(slug: string): BlogPostItem | undefined {
  return getAllStaticPosts().find((p) => p.slug === slug);
}

export function getReadingTimeMinutes(text: string): number {
  const words = text.trim().split(/\s+/).length;
  return Math.max(2, Math.ceil(words / 200));
}

export function extractHeadings(md: string): Array<{ id: string; text: string }> {
  const headings: Array<{ id: string; text: string }> = [];
  for (const line of md.split("\n")) {
    if (line.startsWith("## ")) {
      const text = line.replace(/^##\s+/, "").trim();
      const id = text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
      headings.push({ id, text });
    }
  }
  return headings;
}

export function renderMarkdownToHtml(md: string): string {
  const lines = md.split("\n");
  const out: string[] = [];
  let inList = false;

  const formatInline = (s: string) =>
    s
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-brand-700 font-semibold underline hover:text-brand-800">$1</a>')
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/\*([^*]+)\*/g, "<em>$1</em>")
      .replace(/`([^`]+)`/g, '<code class="px-1.5 py-0.5 bg-slate-100 rounded text-xs font-mono">$1</code>');

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) {
      if (inList) {
        out.push("</ul>");
        inList = false;
      }
      continue;
    }

    if (line.startsWith("## ")) {
      if (inList) { out.push("</ul>"); inList = false; }
      const text = line.replace(/^##\s+/, "");
      const id = text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
      out.push(`<h2 id="${id}" class="text-xl font-extrabold text-slate-900 mt-8 mb-3">${formatInline(text)}</h2>`);
    } else if (line.startsWith("### ")) {
      if (inList) { out.push("</ul>"); inList = false; }
      const text = line.replace(/^###\s+/, "");
      out.push(`<h3 class="text-base font-bold text-slate-900 mt-5 mb-2">${formatInline(text)}</h3>`);
    } else if (line.startsWith("> ")) {
      if (inList) { out.push("</ul>"); inList = false; }
      out.push(`<blockquote class="p-4 my-4 rounded-xl bg-brand-50/70 border-l-4 border-brand-600 text-slate-800 text-sm italic">${formatInline(line.slice(2))}</blockquote>`);
    } else if (line.startsWith("- ") || /^\d+\.\s+/.test(line)) {
      if (!inList) {
        out.push('<ul class="list-disc pl-6 space-y-1.5 my-3 text-slate-700 text-sm">');
        inList = true;
      }
      const itemText = line.replace(/^-\s+/, "").replace(/^\d+\.\s+/, "");
      out.push(`<li>${formatInline(itemText)}</li>`);
    } else {
      if (inList) { out.push("</ul>"); inList = false; }
      out.push(`<p class="my-3 text-sm text-slate-700 leading-relaxed">${formatInline(line)}</p>`);
    }
  }
  if (inList) out.push("</ul>");
  return out.join("\n");
}
