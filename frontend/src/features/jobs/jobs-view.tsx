"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Copy, ExternalLink, Loader2, MoreHorizontal, Pause, Play, RefreshCw, RotateCcw, Square, Trash2 } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { ApiErrorState } from "@/components/api-error";
import { JobStatus } from "@/components/job-status";
import { PageHeading } from "@/components/page-heading";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { api } from "@/lib/api";
import type { CrawlJob } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export function JobsView() {
  const client = useQueryClient();
  const [pendingDelete, setPendingDelete] = useState<string | null>(null);
  const query = useQuery({ queryKey: ["jobs"], queryFn: () => api.jobs(), refetchInterval: 2000 });
  const action = useMutation<unknown, Error, { id: string; name: string }>({
    mutationFn: ({ id, name }) => name === "delete" ? api.deleteJob(id) : api.jobAction(id, name),
    onSettled: () => client.invalidateQueries({ queryKey: ["jobs"] }),
  });
  const error = query.error ?? action.error;
  return (
    <div>
      <PageHeading eyebrow="Job queue" title="Crawl operations" description="Start, pause, resume, stop, restart, or duplicate crawls from one operational view." action={<Button variant="outline" onClick={() => query.refetch()}><RefreshCw className={query.isFetching ? "size-4 animate-spin" : "size-4"} /> Refresh</Button>} />
      {error && <div className="mb-5"><ApiErrorState message={(error as Error).message} /></div>}
      <Card>
        <CardContent className="p-0">
          <div className="hidden grid-cols-[minmax(220px,1.4fr)_120px_1fr_120px_170px] gap-4 border-b px-5 py-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground md:grid"><span>Job</span><span>Status</span><span>Progress</span><span>Created</span><span className="text-right">Actions</span></div>
          <div className="divide-y">
            {query.isLoading ? <div className="flex h-40 items-center justify-center"><Loader2 className="size-5 animate-spin text-primary" /></div> : query.data?.length ? query.data.map((job) => <JobRow key={job.id} job={job} pending={action.isPending && action.variables?.id === job.id} confirmDelete={pendingDelete === job.id} onDeleteRequest={() => setPendingDelete(job.id)} onAction={(name) => { action.mutate({ id: job.id, name }); if (name === "delete") setPendingDelete(null); }} />) : <div className="flex flex-col items-center justify-center gap-3 py-20 text-center"><div className="rounded-xl bg-secondary p-3"><MoreHorizontal className="size-5 text-muted-foreground" /></div><div><p className="text-sm font-medium">Your queue is empty</p><p className="mt-1 text-xs text-muted-foreground">Create a crawl and its live progress will appear here.</p></div><Link href="/crawler" className={buttonVariants()}><Play className="size-4" /> Create first job</Link></div>}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function JobRow({ job, pending, confirmDelete, onDeleteRequest, onAction }: { job: CrawlJob; pending: boolean; confirmDelete: boolean; onDeleteRequest: () => void; onAction: (name: string) => void }) {
  const active = ["running", "paused", "queued"].includes(job.status);
  return (
    <div className="grid gap-4 px-5 py-4 md:grid-cols-[minmax(220px,1.4fr)_120px_1fr_120px_170px] md:items-center">
      <div className="min-w-0"><div className="flex items-center gap-2"><p className="truncate text-sm font-medium">{job.name}</p><a href={job.url} target="_blank" rel="noreferrer" aria-label={`Open source for ${job.name}`}><ExternalLink className="size-3 text-muted-foreground hover:text-primary" /></a></div><p className="mt-1 truncate font-mono text-[10px] text-muted-foreground">{job.current_url || job.url}</p>{job.error && <p className="mt-1 truncate text-[10px] text-red-500" title={job.error}>{job.error}</p>}</div>
      <JobStatus status={job.status} />
      <div><div className="mb-2 flex justify-between font-mono text-[10px] text-muted-foreground"><span>{Number(job.stats.visited_pages ?? 0)} pages · {Number(job.stats.downloaded ?? 0)} files</span><span>{Math.round(job.progress)}%</span></div><Progress value={job.progress} /></div>
      <time className="font-mono text-[10px] text-muted-foreground">{formatDate(job.created_at)}</time>
      <div className="flex justify-end gap-1">
        {pending ? <Loader2 className="m-2 size-4 animate-spin text-primary" /> : <>
          {job.status === "queued" && <Action icon={Play} label="Start" onClick={() => onAction("start")} />}
          {job.status === "running" && <Action icon={Pause} label="Pause" onClick={() => onAction("pause")} />}
          {job.status === "paused" && <Action icon={Play} label="Resume" onClick={() => onAction("resume")} />}
          {active && <Action icon={Square} label="Stop" onClick={() => onAction("stop")} />}
          {!active && <Action icon={RotateCcw} label="Restart" onClick={() => onAction("restart")} />}
          <Action icon={Copy} label="Duplicate" onClick={() => onAction("duplicate")} />
          {!active && (confirmDelete ? <Button size="sm" variant="destructive" onClick={() => onAction("delete")}>Confirm</Button> : <Action icon={Trash2} label="Delete" danger onClick={onDeleteRequest} />)}
        </>}
      </div>
    </div>
  );
}

function Action({ icon: Icon, label, danger, onClick }: { icon: typeof Pause; label: string; danger?: boolean; onClick: () => void }) {
  return <Button type="button" variant="ghost" size="icon" title={label} aria-label={label} className={danger ? "text-red-500" : ""} onClick={onClick}><Icon className="size-3.5" /></Button>;
}
