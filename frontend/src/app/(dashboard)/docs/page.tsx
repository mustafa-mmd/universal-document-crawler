import { ArrowRight, BookOpenText, Clock3 } from "lucide-react";
import Link from "next/link";
import { PageHeading } from "@/components/page-heading";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { guides } from "@/lib/docs";

export default function DocumentationPage() {
  return <div><PageHeading eyebrow="User documentation" title="Learn UDC Pro" description="Practical guides for setup, safe crawling, job operations, document management, troubleshooting, and deployment." /><div className="grid gap-5 lg:grid-cols-2 xl:grid-cols-3">{guides.map((guide) => <Link key={guide.slug} href={`/docs/${guide.slug}`} className="group"><Card className="h-full transition-colors hover:border-primary/40"><CardHeader><div className="mb-3 flex items-center justify-between"><div className="rounded-lg bg-primary/10 p-2 text-primary"><BookOpenText className="size-4" /></div><Badge>{guide.category}</Badge></div><CardTitle className="group-hover:text-primary">{guide.title}</CardTitle><CardDescription className="leading-6">{guide.description}</CardDescription></CardHeader><CardContent className="flex items-center justify-between text-xs text-muted-foreground"><span className="flex items-center gap-1.5"><Clock3 className="size-3.5" />{guide.readTime}</span><span className="flex items-center gap-1 text-primary">Read guide <ArrowRight className="size-3.5 transition-transform group-hover:translate-x-1" /></span></CardContent></Card></Link>)}</div></div>;
}
