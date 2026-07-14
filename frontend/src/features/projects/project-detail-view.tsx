"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, FolderKanban, Loader2, Plus } from "lucide-react";
import Link from "next/link";
import { ApiErrorState } from "@/components/api-error";
import { JobStatus } from "@/components/job-status";
import { PageHeading } from "@/components/page-heading";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export function ProjectDetailView({ projectId }: { projectId: string }) {
  const project = useQuery({ queryKey: ["project", projectId], queryFn: () => api.project(projectId) });
  const jobs = useQuery({ queryKey: ["jobs", projectId], queryFn: () => api.jobs(projectId), refetchInterval: 3000 });
  const error = project.error ?? jobs.error;
  if (project.isLoading) return <div className="flex h-64 items-center justify-center"><Loader2 className="size-5 animate-spin text-primary" /></div>;
  if (error) return <ApiErrorState message={(error as Error).message} />;
  if (!project.data) return null;
  return (
    <div>
      <Link href="/projects" className="mb-5 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"><ArrowLeft className="size-4" /> All projects</Link>
      <PageHeading eyebrow="Project workspace" title={project.data.name} description={project.data.description || "Crawl jobs grouped in this project."} action={<Link href={`/crawler?project_id=${projectId}`} className={buttonVariants()}><Plus className="size-4" /> New crawl</Link>} />
      <div className="mb-5 grid gap-3 sm:grid-cols-4">
        <Summary label="Total jobs" value={project.data.total_jobs} />
        <Summary label="Active" value={project.data.active_jobs} />
        <Summary label="Completed" value={project.data.completed_jobs} />
        <Summary label="Failed" value={project.data.failed_jobs} />
      </div>
      <Card>
        <CardContent className="p-0">
          {jobs.data?.length ? <div className="divide-y">{jobs.data.map((job) => <Link key={job.id} href="/jobs" className="grid gap-3 px-5 py-4 hover:bg-accent/40 sm:grid-cols-[1fr_auto_auto] sm:items-center"><div className="min-w-0"><p className="truncate text-sm font-medium">{job.name}</p><p className="truncate text-xs text-muted-foreground">{job.url}</p></div><JobStatus status={job.status} /><time className="text-xs text-muted-foreground">{formatDate(job.created_at)}</time></Link>)}</div> : <div className="flex min-h-64 flex-col items-center justify-center text-center"><FolderKanban className="mb-3 size-6 text-muted-foreground" /><p className="font-medium">No jobs in this project</p><p className="mt-1 text-sm text-muted-foreground">Start a crawl and it will appear here.</p></div>}
        </CardContent>
      </Card>
    </div>
  );
}

function Summary({ label, value }: { label: string; value: number }) {
  return <Card><CardContent className="p-4"><div className="font-mono text-2xl font-semibold">{value}</div><div className="text-xs text-muted-foreground">{label}</div></CardContent></Card>;
}
