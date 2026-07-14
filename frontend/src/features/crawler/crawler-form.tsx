"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, CheckCircle2, FileType2, Gauge, Globe2, Loader2, ShieldCheck, SlidersHorizontal, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { ApiErrorState } from "@/components/api-error";
import { PageHeading } from "@/components/page-heading";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

const fileTypes = ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "csv", "txt", "json", "xml", "zip", "rar", "7z", "epub", "odt", "ods", "rtf"];
const schema = z.object({
  name: z.string().min(2, "Give this crawl a recognizable name").max(100),
  url: z.url("Enter a complete public URL, including https://"),
  project_id: z.string(),
  max_depth: z.number().int().min(0).max(20),
  max_pages: z.number().int().min(1).max(100000),
  max_downloads: z.number().int().min(1).max(100000),
  same_domain_only: z.boolean(),
  enable_javascript: z.boolean(),
  respect_robots: z.boolean(),
  retry_failed_downloads: z.boolean(),
  timeout_seconds: z.number().int().min(5).max(300),
  rate_limit_seconds: z.number().min(0).max(30),
  max_retries: z.number().int().min(0).max(10),
  file_types: z.array(z.string()).min(1, "Select at least one file type"),
  include_keywords: z.string(),
  exclude_keywords: z.string(),
  filename_contains: z.string(),
  minimum_file_size: z.number().min(0).optional(),
  maximum_file_size: z.number().min(0).optional(),
}).refine((value) => value.minimum_file_size === undefined || value.maximum_file_size === undefined || value.minimum_file_size <= value.maximum_file_size, { message: "Minimum size cannot exceed maximum size", path: ["maximum_file_size"] });

type FormValues = z.infer<typeof schema>;

export function CrawlerForm({ initialProjectId = "" }: { initialProjectId?: string }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [advanced, setAdvanced] = useState(false);
  const projects = useQuery({ queryKey: ["projects"], queryFn: api.projects });
  const settings = useQuery({ queryKey: ["settings"], queryFn: api.settings });
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      url: "",
      project_id: initialProjectId,
      max_depth: 3,
      max_pages: 500,
      max_downloads: 500,
      same_domain_only: true,
      enable_javascript: true,
      respect_robots: true,
      retry_failed_downloads: true,
      timeout_seconds: 30,
      rate_limit_seconds: 0.25,
      max_retries: 3,
      file_types: ["pdf", "doc", "docx"],
      include_keywords: "",
      exclude_keywords: "",
      filename_contains: "",
    },
  });

  useEffect(() => {
    if (settings.data && !form.formState.isDirty) {
      form.setValue("timeout_seconds", settings.data.timeout_seconds);
      form.setValue("max_retries", settings.data.retry_count);
    }
  }, [form, settings.data]);

  const selected = form.watch("file_types");
  const mutation = useMutation({
    mutationFn: (values: FormValues) => api.createJob({
      ...values,
      project_id: values.project_id || null,
      include_keywords: splitKeywords(values.include_keywords),
      exclude_keywords: splitKeywords(values.exclude_keywords),
      minimum_file_size: values.minimum_file_size === undefined ? null : values.minimum_file_size * 1024 * 1024,
      maximum_file_size: values.maximum_file_size === undefined ? null : values.maximum_file_size * 1024 * 1024,
    }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["jobs"] }),
        queryClient.invalidateQueries({ queryKey: ["projects"] }),
      ]);
      router.push("/jobs");
    },
  });

  const toggleFile = (type: string) => form.setValue("file_types", selected.includes(type) ? selected.filter((item) => item !== type) : [...selected, type], { shouldValidate: true, shouldDirty: true });

  return (
    <div>
      <PageHeading eyebrow="Crawler manager" title="Start a precise crawl" description="Choose a public website, define hard limits, and specify exactly which documents should be kept." />
      <form onSubmit={form.handleSubmit((values) => mutation.mutate(values))} className="grid gap-5 xl:grid-cols-[1.25fr_.75fr]">
        <div className="space-y-5">
          <Card>
            <CardHeader><SectionTitle icon={Globe2} title="Source website" description="Use a public HTTP or HTTPS website you have permission to crawl." /></CardHeader>
            <CardContent className="space-y-4">
              <Field label="Job name" error={form.formState.errors.name?.message}><Input placeholder="Punjab agriculture publications" {...form.register("name")} /></Field>
              <Field label="Website URL" error={form.formState.errors.url?.message}><div className="relative"><Input className="h-12 pl-10 font-mono text-xs" placeholder="https://example.gov/publications" {...form.register("url")} /><Globe2 className="absolute left-3.5 top-4 size-4 text-muted-foreground" /></div></Field>
              <Field label="Project" hint="Optional. Projects group related jobs without changing crawl behavior."><Select {...form.register("project_id")}><option value="">No project</option>{projects.data?.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}</Select></Field>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><SectionTitle icon={FileType2} title="Document types" description="Only selected formats will be downloaded." /></CardHeader>
            <CardContent><div className="grid grid-cols-3 gap-2 sm:grid-cols-6">{fileTypes.map((type) => { const checked = selected.includes(type); return <div key={type} className={cn("flex h-11 items-center gap-2 rounded-lg border px-3 text-xs font-semibold uppercase transition-all", checked ? "border-primary/45 bg-primary/8 text-primary" : "bg-background text-muted-foreground")}><Checkbox aria-label={`Download ${type.toUpperCase()} files`} checked={checked} onCheckedChange={() => toggleFile(type)} />{type}</div>; })}</div>{form.formState.errors.file_types && <p className="mt-3 text-xs text-red-500">{form.formState.errors.file_types.message}</p>}</CardContent>
          </Card>

          <Card>
            <button type="button" aria-expanded={advanced} className="flex w-full items-center gap-3 p-5 text-left" onClick={() => setAdvanced((value) => !value)}><div className="rounded-lg bg-violet-500/10 p-2 text-violet-500"><SlidersHorizontal className="size-4" /></div><div className="flex-1"><CardTitle className="text-sm">Advanced filters and network controls</CardTitle><CardDescription>Keywords, file size, pacing, timeout, and retry behavior.</CardDescription></div><span className="text-xs font-medium text-primary">{advanced ? "Hide" : "Show"}</span></button>
            {advanced && <CardContent className="grid gap-4 border-t pt-5 sm:grid-cols-2">
              <Field label="Include keywords" hint="Comma-separated. At least one must appear in the file URL."><Input placeholder="annual report, agriculture" {...form.register("include_keywords")} /></Field>
              <Field label="Exclude keywords" hint="Comma-separated. Matching file URLs are skipped."><Input placeholder="draft, archive" {...form.register("exclude_keywords")} /></Field>
              <Field label="Filename contains"><Input placeholder="notification" {...form.register("filename_contains")} /></Field>
              <Field label="Request timeout (seconds)" error={form.formState.errors.timeout_seconds?.message}><Input type="number" {...form.register("timeout_seconds", { valueAsNumber: true })} /></Field>
              <Field label="Minimum size (MB)"><Input type="number" min="0" step="0.1" {...form.register("minimum_file_size", { setValueAs: optionalNumber })} /></Field>
              <Field label="Maximum size (MB)" error={form.formState.errors.maximum_file_size?.message}><Input type="number" min="0" step="0.1" {...form.register("maximum_file_size", { setValueAs: optionalNumber })} /></Field>
              <Field label="Delay between pages (seconds)" hint="Increase this for sensitive or rate-limited websites."><Input type="number" min="0" max="30" step="0.05" {...form.register("rate_limit_seconds", { valueAsNumber: true })} /></Field>
              <Field label="Retries after first attempt"><Input type="number" min="0" max="10" {...form.register("max_retries", { valueAsNumber: true })} /></Field>
            </CardContent>}
          </Card>
        </div>

        <div className="space-y-5">
          <Card className="xl:sticky xl:top-24">
            <CardHeader><SectionTitle icon={Gauge} title="Crawl limits" description="Hard boundaries keep discovery predictable." /></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-3">
                <Field label="Depth" hint="Link levels from start."><Input type="number" min="0" max="20" {...form.register("max_depth", { valueAsNumber: true })} /></Field>
                <Field label="Pages" hint="Maximum pages opened."><Input type="number" min="1" {...form.register("max_pages", { valueAsNumber: true })} /></Field>
                <Field label="Files" hint="Maximum files saved."><Input type="number" min="1" {...form.register("max_downloads", { valueAsNumber: true })} /></Field>
              </div>
              <div className="space-y-1 border-t pt-4">
                <Toggle label="Same domain only" detail="Do not follow links to external websites" checked={form.watch("same_domain_only")} onChange={(value) => form.setValue("same_domain_only", value, { shouldDirty: true })} />
                <Toggle label="Enable JavaScript" detail="Render pages that load links dynamically" checked={form.watch("enable_javascript")} onChange={(value) => form.setValue("enable_javascript", value, { shouldDirty: true })} />
                <Toggle label="Respect robots.txt" detail="Honor the website publisher's crawl policy" checked={form.watch("respect_robots")} onChange={(value) => form.setValue("respect_robots", value, { shouldDirty: true })} />
                <Toggle label="Retry failed downloads" detail="Retry transient network and server failures" checked={form.watch("retry_failed_downloads")} onChange={(value) => form.setValue("retry_failed_downloads", value, { shouldDirty: true })} />
              </div>
              <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/[0.05] p-3"><div className="flex gap-2"><ShieldCheck className="mt-0.5 size-4 shrink-0 text-emerald-500" /><p className="text-[11px] leading-5 text-muted-foreground">Private-network and local targets are blocked. Use conservative limits and crawl only content you are authorized to access.</p></div></div>
              {mutation.isError && <ApiErrorState message={(mutation.error as Error).message} />}
              <Button type="submit" size="lg" className="w-full" disabled={mutation.isPending}>{mutation.isPending ? <Loader2 className="size-4 animate-spin" /> : <Sparkles className="size-4" />}{mutation.isPending ? "Creating job…" : "Start crawl"}<ArrowRight className="ml-auto size-4" /></Button>
              <p className="flex items-center justify-center gap-1.5 text-[10px] text-muted-foreground"><CheckCircle2 className="size-3 text-emerald-500" /> Configuration and runtime settings are saved before execution</p>
            </CardContent>
          </Card>
        </div>
      </form>
    </div>
  );
}

function splitKeywords(value: string) { return value.split(",").map((item) => item.trim()).filter(Boolean); }
function optionalNumber(value: string) { return value === "" ? undefined : Number(value); }

function SectionTitle({ icon: Icon, title, description }: { icon: typeof Globe2; title: string; description: string }) {
  return <div className="flex items-center gap-3"><div className="rounded-lg bg-primary/10 p-2 text-primary"><Icon className="size-4" /></div><div><CardTitle className="text-sm">{title}</CardTitle><CardDescription>{description}</CardDescription></div></div>;
}

function Field({ label, hint, error, children }: { label: string; hint?: string; error?: string; children: React.ReactNode }) {
  return <div className="space-y-2"><Label>{label}</Label>{children}{hint && <p className="text-[10px] leading-4 text-muted-foreground">{hint}</p>}{error && <p className="text-xs text-red-500">{error}</p>}</div>;
}

function Toggle({ label, detail, checked, onChange }: { label: string; detail: string; checked: boolean; onChange: (value: boolean) => void }) {
  return <button type="button" role="switch" aria-checked={checked} className="flex w-full items-center gap-3 rounded-lg p-2 text-left hover:bg-accent/50" onClick={() => onChange(!checked)}><div className={cn("flex h-5 w-9 items-center rounded-full p-0.5 transition-colors", checked ? "bg-primary" : "bg-secondary")}><span className={cn("size-4 rounded-full bg-white shadow-sm transition-transform", checked && "translate-x-4")} /></div><div className="flex-1"><p className="text-xs font-medium">{label}</p><p className="text-[10px] text-muted-foreground">{detail}</p></div></button>;
}
