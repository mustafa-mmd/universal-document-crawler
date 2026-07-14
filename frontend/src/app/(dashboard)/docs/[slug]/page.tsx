import { ArrowLeft, Info } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { getGuide, guides } from "@/lib/docs";

export function generateStaticParams() { return guides.map((guide) => ({ slug: guide.slug })); }

export default async function GuidePage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const guide = getGuide(slug);
  if (!guide) notFound();
  return <article className="mx-auto max-w-4xl"><Link href="/docs" className="mb-6 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"><ArrowLeft className="size-4" /> Documentation</Link><header className="mb-8"><div className="mb-3 flex gap-2"><Badge tone="info">{guide.category}</Badge><Badge>{guide.readTime}</Badge></div><h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">{guide.title}</h2><p className="mt-3 max-w-2xl text-base leading-7 text-muted-foreground">{guide.description}</p></header><div className="space-y-5">{guide.sections.map((section) => <Card key={section.title}><CardContent className="p-6"><h3 className="mb-3 text-lg font-semibold">{section.title}</h3>{section.paragraphs?.map((paragraph) => <p key={paragraph} className="mb-3 text-sm leading-7 text-muted-foreground last:mb-0">{paragraph}</p>)}{section.steps && <ol className="ml-5 list-decimal space-y-2 text-sm leading-6 text-muted-foreground">{section.steps.map((step) => <li key={step}>{step}</li>)}</ol>}{section.bullets && <ul className="ml-5 list-disc space-y-2 text-sm leading-6 text-muted-foreground">{section.bullets.map((bullet) => <li key={bullet}>{bullet}</li>)}</ul>}{section.code && <pre className="mt-4 overflow-x-auto rounded-lg bg-zinc-950 p-4 text-xs leading-6 text-zinc-200"><code>{section.code}</code></pre>}{section.note && <div className="mt-4 flex gap-3 rounded-lg border border-primary/20 bg-primary/[0.04] p-4 text-xs leading-6 text-muted-foreground"><Info className="mt-1 size-4 shrink-0 text-primary" /><p>{section.note}</p></div>}</CardContent></Card>)}</div></article>;
}
