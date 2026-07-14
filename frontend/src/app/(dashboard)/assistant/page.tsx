import { Bot, LockKeyhole, Sparkles } from "lucide-react";
import { PageHeading } from "@/components/page-heading";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function AssistantPage() {
  return <div><PageHeading eyebrow="Future module" title="AI crawl assistant" description="Convert natural-language research intent into a validated, reviewable crawler configuration."/><Card className="relative overflow-hidden"><div className="grid-fade absolute inset-0 opacity-70"/><CardContent className="relative mx-auto flex min-h-[480px] max-w-3xl flex-col items-center justify-center p-8 text-center"><div className="mb-5 flex size-14 items-center justify-center rounded-2xl bg-primary/10 text-primary"><Bot className="size-7"/></div><Badge tone="info"><Sparkles className="mr-1 size-3"/>Planned</Badge><h3 className="mt-4 text-xl font-semibold">Describe what you need. Review before it runs.</h3><p className="mt-2 max-w-lg text-sm leading-6 text-muted-foreground">“Download English agriculture annual reports larger than 1 MB” will become typed filters, limits, and a clear execution preview.</p><div className="mt-7 flex w-full gap-2 rounded-xl border bg-background/80 p-2 shadow-lg backdrop-blur"><Input disabled className="border-0 bg-transparent shadow-none focus-visible:ring-0" placeholder="Ask UDC Pro to find documents…"/><Button disabled><LockKeyhole className="size-4"/>Connect model</Button></div><p className="mt-3 text-[10px] text-muted-foreground">The crawler remains deterministic; AI proposes configuration and never bypasses safety policy.</p></CardContent></Card></div>;
}
