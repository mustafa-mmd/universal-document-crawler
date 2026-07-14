"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Info, RefreshCw, ScrollText, Search, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";
import { ApiErrorState } from "@/components/api-error";
import { PageHeading } from "@/components/page-heading";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

const files = ["crawler.log", "download.log", "errors.log"];

export function LogsView() {
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["logs"], queryFn: api.logs, refetchInterval: 5000 });
  const [active, setActive] = useState(files[0]);
  const [search, setSearch] = useState("");
  const [confirmClear, setConfirmClear] = useState(false);
  const clear = useMutation({ mutationFn: api.clearLogs, onSuccess: () => { setConfirmClear(false); queryClient.invalidateQueries({ queryKey: ["logs"] }); } });
  const lines = useMemo(() => (query.data?.[active] ?? []).filter((line) => line.toLowerCase().includes(search.toLowerCase())), [active, query.data, search]);
  const error = query.error ?? clear.error;

  return (
    <div>
      <PageHeading eyebrow="Observability" title="Runtime logs" description="Inspect crawler, download, and error output streamed from the local backend." action={<div className="flex gap-2"><Button variant="outline" onClick={() => query.refetch()}><RefreshCw className={cn("size-4", query.isFetching && "animate-spin")} /> Refresh</Button>{confirmClear ? <Button variant="destructive" onClick={() => clear.mutate()} disabled={clear.isPending}>Confirm clear</Button> : <Button variant="outline" onClick={() => setConfirmClear(true)}><Trash2 className="size-4" /> Clear logs</Button>}</div>} />
      {error && <div className="mb-5"><ApiErrorState message={(error as Error).message} /></div>}
      <div className="mb-4 flex items-start gap-3 rounded-xl border border-primary/20 bg-primary/[0.04] p-4 text-xs leading-5 text-muted-foreground"><Info className="mt-0.5 size-4 shrink-0 text-primary" /><p><strong className="text-foreground">Network errors are contextual.</strong> For example, <code>ERR_INTERNET_DISCONNECTED</code> means the machine or target connection was unavailable during that request; it does not mean the dashboard itself is broken.</p></div>
      <Card>
        <div className="flex flex-col gap-2 border-b p-2 sm:flex-row sm:items-center">
          <div className="flex flex-1 gap-1 overflow-x-auto">{files.map((name) => <Button key={name} size="sm" variant={active === name ? "secondary" : "ghost"} onClick={() => setActive(name)}>{name}</Button>)}</div>
          <div className="relative sm:w-64"><Search className="absolute left-2.5 top-2.5 size-3.5 text-muted-foreground" /><Input aria-label="Filter log lines" value={search} onChange={(event) => setSearch(event.target.value)} className="h-8 pl-8 text-xs" placeholder="Filter current log…" /></div>
        </div>
        <CardContent className="p-0"><div className="h-[58vh] overflow-auto bg-zinc-950 p-4 font-mono text-[11px] leading-6 text-zinc-300">{lines.length ? lines.map((line, index) => <div key={`${active}-${index}-${line}`} className={cn("border-l-2 border-transparent pl-3", /error|failed/i.test(line) && "border-red-500 text-red-300", /warning/i.test(line) && "border-amber-500 text-amber-200")}><span className="mr-4 select-none text-zinc-600">{String(index + 1).padStart(3, "0")}</span>{line}</div>) : <div className="flex h-full flex-col items-center justify-center gap-3 text-zinc-500"><ScrollText className="size-5" /><p>{search ? "No matching entries" : `No entries in ${active}`}</p></div>}</div></CardContent>
      </Card>
    </div>
  );
}
