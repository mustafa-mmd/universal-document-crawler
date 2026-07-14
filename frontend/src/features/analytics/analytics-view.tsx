"use client";

import { useQuery } from "@tanstack/react-query";
import { BarChart3, Database, FileStack, HardDrive } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ApiErrorState } from "@/components/api-error";
import { PageHeading } from "@/components/page-heading";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { formatBytes } from "@/lib/utils";

export function AnalyticsView() {
  const query = useQuery({ queryKey: ["dashboard"], queryFn: api.dashboard });
  const data = query.data;
  const metrics = [{ label: "Crawls", value: data?.summary.total_jobs ?? 0, icon: Database }, { label: "Documents", value: data?.summary.total_documents ?? 0, icon: FileStack }, { label: "Storage", value: formatBytes(data?.summary.storage_bytes ?? 0), icon: HardDrive }];
  return <div><PageHeading eyebrow="Analytics" title="Document intelligence at a glance" description="Understand which sources and formats account for the growth of your local knowledge base."/>{query.isError && <div className="mb-5"><ApiErrorState message={(query.error as Error).message}/></div>}<div className="grid gap-4 sm:grid-cols-3">{metrics.map(({label,value,icon:Icon}) => <Card key={label}><CardContent className="flex items-center gap-4 p-5"><div className="rounded-lg bg-primary/10 p-3 text-primary"><Icon className="size-5"/></div><div><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 font-mono text-xl font-semibold">{value}</p></div></CardContent></Card>)}</div><div className="mt-4 grid gap-4 xl:grid-cols-2"><Card><CardHeader><CardTitle className="text-sm">Documents by source</CardTitle><CardDescription>Top hosts in your collection</CardDescription></CardHeader><CardContent className="h-80">{data?.websites.length ? <ResponsiveContainer width="100%" height="100%"><BarChart data={data.websites}><CartesianGrid vertical={false} stroke="var(--border)"/><XAxis dataKey="name" tickLine={false} axisLine={false} fontSize={10}/><YAxis tickLine={false} axisLine={false} fontSize={10}/><Tooltip contentStyle={{background:"var(--card)",border:"1px solid var(--border)",borderRadius:10}}/><Bar dataKey="value" fill="var(--primary)" radius={[6,6,0,0]}/></BarChart></ResponsiveContainer> : <Empty/>}</CardContent></Card><Card><CardHeader><CardTitle className="text-sm">Documents by format</CardTitle><CardDescription>Downloaded file-type distribution</CardDescription></CardHeader><CardContent className="h-80">{data?.file_types.length ? <ResponsiveContainer width="100%" height="100%"><BarChart data={data.file_types}><CartesianGrid vertical={false} stroke="var(--border)"/><XAxis dataKey="name" tickLine={false} axisLine={false} fontSize={10}/><YAxis tickLine={false} axisLine={false} fontSize={10}/><Tooltip contentStyle={{background:"var(--card)",border:"1px solid var(--border)",borderRadius:10}}/><Bar dataKey="value" fill="#22d3ee" radius={[6,6,0,0]}/></BarChart></ResponsiveContainer> : <Empty/>}</CardContent></Card></div></div>;
}
function Empty(){ return <div className="flex h-full flex-col items-center justify-center gap-3 text-xs text-muted-foreground"><BarChart3 className="size-5"/>Analytics populate after your first download.</div>; }
