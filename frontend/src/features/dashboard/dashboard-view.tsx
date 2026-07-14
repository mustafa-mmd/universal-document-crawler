"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Activity, CircleCheck, Database, FileStack, Globe2, HardDrive, TriangleAlert } from "lucide-react";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ApiErrorState } from "@/components/api-error";
import { JobStatus } from "@/components/job-status";
import { PageHeading } from "@/components/page-heading";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { formatBytes, formatDate } from "@/lib/utils";

const EMPTY = {
  summary: { total_jobs: 0, active_jobs: 0, completed_jobs: 0, failed_jobs: 0, total_documents: 0, storage_bytes: 0 },
  file_types: [], websites: [], recent_jobs: [],
};
const colors = ["var(--primary)", "#22d3ee", "#34d399", "#f59e0b", "#a78bfa"];

export function DashboardView() {
  const query = useQuery({ queryKey: ["dashboard"], queryFn: api.dashboard, refetchInterval: 5000 });
  const data = query.data ?? EMPTY;
  const summary = [
    { label: "Total jobs", value: data.summary.total_jobs, icon: Database, detail: "All crawl sessions" },
    { label: "Active", value: data.summary.active_jobs, icon: Activity, detail: "Queued, running, paused" },
    { label: "Documents", value: data.summary.total_documents, icon: FileStack, detail: "Discovered and saved" },
    { label: "Storage", value: formatBytes(data.summary.storage_bytes), icon: HardDrive, detail: "Local disk usage" },
  ];
  const trend = data.recent_jobs.slice().reverse().map((job, index) => ({ name: `#${index + 1}`, pages: Number(job.stats.visited_pages ?? 0), files: Number(job.stats.downloaded ?? 0) }));

  return (
    <div>
      <PageHeading eyebrow="Control center" title="Good to see you." description="A live view of crawling health, document growth, and the work currently moving through your queue." />
      {query.isError && <div className="mb-5"><ApiErrorState message={(query.error as Error).message} /></div>}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {summary.map((item, index) => (
          <motion.div key={item.label} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.04 }}>
            <Card className="relative overflow-hidden"><div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/60 to-transparent" /><CardContent className="p-5"><div className="mb-5 flex items-center justify-between"><span className="text-xs font-medium text-muted-foreground">{item.label}</span><div className="rounded-lg bg-primary/10 p-2 text-primary"><item.icon className="size-4" /></div></div><p className="font-mono text-2xl font-semibold tracking-tight">{item.value}</p><p className="mt-1.5 text-[11px] text-muted-foreground">{item.detail}</p></CardContent></Card>
          </motion.div>
        ))}
      </div>
      <div className="mt-4 grid gap-4 xl:grid-cols-[1.7fr_1fr]">
        <Card><CardHeader><CardTitle className="text-sm">Crawl throughput</CardTitle><CardDescription>Pages inspected and files saved per recent job</CardDescription></CardHeader><CardContent className="h-72">
          {trend.length ? <ResponsiveContainer width="100%" height="100%"><AreaChart data={trend}><defs><linearGradient id="pages" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="var(--primary)" stopOpacity={0.35}/><stop offset="95%" stopColor="var(--primary)" stopOpacity={0}/></linearGradient></defs><CartesianGrid stroke="var(--border)" vertical={false}/><XAxis dataKey="name" tickLine={false} axisLine={false} fontSize={11}/><YAxis tickLine={false} axisLine={false} fontSize={11}/><Tooltip contentStyle={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 10 }}/><Area type="monotone" dataKey="pages" stroke="var(--primary)" fill="url(#pages)" strokeWidth={2}/><Area type="monotone" dataKey="files" stroke="#22d3ee" fill="transparent" strokeWidth={2}/></AreaChart></ResponsiveContainer> : <EmptyChart icon={Activity} text="Run your first crawl to see throughput." />}
        </CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm">File type mix</CardTitle><CardDescription>Distribution across downloaded documents</CardDescription></CardHeader><CardContent className="h-72">
          {data.file_types.length ? <ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={data.file_types} innerRadius={62} outerRadius={92} paddingAngle={3} dataKey="value">{data.file_types.map((entry, index) => <Cell key={entry.name} fill={colors[index % colors.length]} />)}</Pie><Tooltip contentStyle={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 10 }}/></PieChart></ResponsiveContainer> : <EmptyChart icon={FileStack} text="Document types will appear here." />}
        </CardContent></Card>
      </div>
      <div className="mt-4 grid gap-4 xl:grid-cols-[1.7fr_1fr]">
        <Card><CardHeader className="flex-row items-center justify-between"><div><CardTitle className="text-sm">Recent activity</CardTitle><CardDescription>Latest crawl jobs across the workspace</CardDescription></div><CircleCheck className="size-4 text-emerald-500" /></CardHeader><CardContent>
          <div className="divide-y">{data.recent_jobs.length ? data.recent_jobs.slice(0, 6).map((job) => <div key={job.id} className="flex items-center gap-3 py-3"><div className="flex size-9 items-center justify-center rounded-lg bg-secondary"><Globe2 className="size-4 text-muted-foreground" /></div><div className="min-w-0 flex-1"><p className="truncate text-sm font-medium">{job.name}</p><p className="truncate text-xs text-muted-foreground">{job.url}</p></div><JobStatus status={job.status}/><time className="hidden w-24 text-right font-mono text-[10px] text-muted-foreground sm:block">{formatDate(job.created_at)}</time></div>) : <div className="py-12 text-center text-sm text-muted-foreground">No crawl activity yet.</div>}</div>
        </CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm">Top websites</CardTitle><CardDescription>Documents grouped by source host</CardDescription></CardHeader><CardContent className="h-64">{data.websites.length ? <ResponsiveContainer width="100%" height="100%"><BarChart data={data.websites} layout="vertical"><XAxis type="number" hide/><YAxis type="category" dataKey="name" width={92} tickLine={false} axisLine={false} fontSize={10}/><Tooltip contentStyle={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 10 }}/><Bar dataKey="value" fill="var(--primary)" radius={[0,6,6,0]} barSize={14}/></BarChart></ResponsiveContainer> : <EmptyChart icon={Globe2} text="Source websites will appear here." />}</CardContent></Card>
      </div>
      {data.summary.failed_jobs > 0 && <div className="mt-4 flex items-center gap-2 text-xs text-red-500"><TriangleAlert className="size-4" />{data.summary.failed_jobs} job{data.summary.failed_jobs === 1 ? "" : "s"} need attention.</div>}
    </div>
  );
}

function EmptyChart({ icon: Icon, text }: { icon: typeof Activity; text: string }) {
  return <div className="flex h-full flex-col items-center justify-center gap-3 text-muted-foreground"><div className="rounded-xl bg-secondary p-3"><Icon className="size-5" /></div><p className="text-xs">{text}</p></div>;
}
