"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, FolderOpen, Loader2, MonitorCog, Network, Save, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { ApiErrorState } from "@/components/api-error";
import { PageHeading } from "@/components/page-heading";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { api } from "@/lib/api";
import type { RuntimeSettings } from "@/lib/types";

const fallback: RuntimeSettings = {
  download_directory: "",
  browser_type: "chromium",
  headless: true,
  user_agent: "UniversalDocumentCrawler/1.0",
  proxy: "",
  timeout_seconds: 30,
  retry_count: 3,
};

export function SettingsView() {
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["settings"], queryFn: api.settings });
  const [values, setValues] = useState<RuntimeSettings>(fallback);
  useEffect(() => { if (query.data) setValues(query.data); }, [query.data]);
  const mutation = useMutation({
    mutationFn: () => api.updateSettings(values),
    onSuccess: (data) => {
      setValues(data);
      queryClient.setQueryData(["settings"], data);
    },
  });
  const set = <Key extends keyof RuntimeSettings>(key: Key, value: RuntimeSettings[Key]) => setValues((current) => ({ ...current, [key]: value }));

  if (query.isLoading) return <div className="flex h-80 items-center justify-center"><Loader2 className="size-5 animate-spin text-primary" /></div>;
  const error = query.error ?? mutation.error;

  return (
    <div>
      <PageHeading eyebrow="Workspace preferences" title="Crawler settings" description="Configure the browser, storage location, and network defaults used by every newly created job." action={<Button onClick={() => mutation.mutate()} disabled={mutation.isPending}>{mutation.isPending ? <Loader2 className="size-4 animate-spin" /> : mutation.isSuccess ? <Check className="size-4" /> : <Save className="size-4" />}{mutation.isSuccess ? "Saved" : "Save changes"}</Button>} />
      {error && <div className="mb-5"><ApiErrorState message={(error as Error).message} /></div>}
      <div className="grid gap-5 xl:grid-cols-2">
        <SettingsCard icon={FolderOpen} title="Storage" description="The backend writes newly downloaded files to this local directory.">
          <Setting label="Download directory" hint="Use an absolute Windows path. Leave empty only if you want the backend's configured default."><Input value={values.download_directory} onChange={(event) => set("download_directory", event.target.value)} placeholder="D:\Document Downloader" /></Setting>
        </SettingsCard>
        <SettingsCard icon={MonitorCog} title="Browser" description="Browser options used for dynamic pages in new jobs.">
          <div className="grid gap-4 sm:grid-cols-2">
            <Setting label="Browser engine" hint="The selected Playwright engine must be installed on the backend."><Select value={values.browser_type} onChange={(event) => set("browser_type", event.target.value as RuntimeSettings["browser_type"])}><option value="chromium">Chromium</option><option value="firefox">Firefox</option><option value="webkit">WebKit</option></Select></Setting>
            <div className="space-y-2"><Label>Execution mode</Label><label className="flex h-10 items-center gap-3 rounded-lg border px-3 text-sm"><Checkbox checked={values.headless} onCheckedChange={(checked) => set("headless", checked)} /><span>Run browser headlessly</span></label><p className="text-[10px] leading-4 text-muted-foreground">Recommended for unattended jobs.</p></div>
          </div>
        </SettingsCard>
        <SettingsCard icon={Network} title="Network" description="Request identity, proxy routing, timeout, and retry behavior.">
          <div className="grid gap-4 sm:grid-cols-2">
            <Setting label="Timeout (seconds)"><Input type="number" min={5} max={300} value={values.timeout_seconds} onChange={(event) => set("timeout_seconds", Number(event.target.value))} /></Setting>
            <Setting label="Retry count"><Input type="number" min={0} max={10} value={values.retry_count} onChange={(event) => set("retry_count", Number(event.target.value))} /></Setting>
          </div>
          <Setting label="Proxy URL" hint="Optional. Use a trusted proxy; credentials are stored in the local settings database."><Input value={values.proxy} onChange={(event) => set("proxy", event.target.value)} placeholder="http://proxy.example:8080" /></Setting>
          <Setting label="User agent"><Input value={values.user_agent} onChange={(event) => set("user_agent", event.target.value)} placeholder="UniversalDocumentCrawler/1.0" /></Setting>
        </SettingsCard>
        <Card>
          <CardHeader><div className="flex gap-3"><div className="rounded-lg bg-emerald-500/10 p-2 text-emerald-500"><ShieldCheck className="size-4" /></div><div><CardTitle className="text-sm">Immutable job snapshots</CardTitle><CardDescription>Predictable execution even after preferences change.</CardDescription></div></div></CardHeader>
          <CardContent><div className="rounded-lg border border-primary/20 bg-primary/[0.04] p-4 text-xs leading-6 text-muted-foreground">When you create a job, these settings are copied into that job. Editing preferences affects future jobs only. Restarting or duplicating a previous job preserves its original browser and network settings.</div></CardContent>
        </Card>
      </div>
    </div>
  );
}

function SettingsCard({ icon: Icon, title, description, children }: { icon: typeof FolderOpen; title: string; description: string; children: React.ReactNode }) {
  return <Card><CardHeader><div className="flex gap-3"><div className="rounded-lg bg-primary/10 p-2 text-primary"><Icon className="size-4" /></div><div><CardTitle className="text-sm">{title}</CardTitle><CardDescription>{description}</CardDescription></div></div></CardHeader><CardContent className="space-y-4">{children}</CardContent></Card>;
}

function Setting({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return <div className="space-y-2"><Label>{label}</Label>{children}{hint && <p className="text-[10px] leading-4 text-muted-foreground">{hint}</p>}</div>;
}
