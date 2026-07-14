"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, FolderKanban, Loader2, Pencil, Plus, Trash2, X } from "lucide-react";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { ApiErrorState } from "@/components/api-error";
import { PageHeading } from "@/components/page-heading";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import type { Project } from "@/lib/types";
import { cn, formatDate } from "@/lib/utils";

const colors = ["#3b82f6", "#06b6d4", "#10b981", "#f59e0b", "#8b5cf6", "#ef4444"];

export function ProjectsView() {
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["projects"], queryFn: api.projects });
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [color, setColor] = useState(colors[0]);
  const [editing, setEditing] = useState<Project | null>(null);
  const [pendingDelete, setPendingDelete] = useState<string | null>(null);

  const refresh = () => queryClient.invalidateQueries({ queryKey: ["projects"] });
  const create = useMutation({
    mutationFn: api.createProject,
    onSuccess: () => {
      setName("");
      setDescription("");
      setShowForm(false);
      refresh();
    },
  });
  const update = useMutation({
    mutationFn: (project: Project) =>
      api.updateProject(project.id, {
        name: project.name,
        description: project.description,
        color: project.color,
      }),
    onSuccess: () => {
      setEditing(null);
      refresh();
    },
  });
  const remove = useMutation({
    mutationFn: api.deleteProject,
    onSuccess: () => {
      setPendingDelete(null);
      refresh();
    },
  });

  function submit(event: FormEvent) {
    event.preventDefault();
    create.mutate({ name: name.trim(), description: description.trim(), color });
  }

  const error = query.error ?? create.error ?? update.error ?? remove.error;

  return (
    <div>
      <PageHeading
        eyebrow="Organization"
        title="Projects"
        description="Group related crawl jobs by website, client, or research objective and monitor each workspace independently."
        action={
          <Button onClick={() => setShowForm((value) => !value)}>
            {showForm ? <X className="size-4" /> : <Plus className="size-4" />}
            {showForm ? "Cancel" : "New project"}
          </Button>
        }
      />

      {error && <div className="mb-5"><ApiErrorState message={(error as Error).message} /></div>}

      {showForm && (
        <Card className="mb-5">
          <form onSubmit={submit}>
            <CardHeader>
              <CardTitle>Create a project</CardTitle>
              <CardDescription>A project is a permanent workspace for related crawl jobs.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-[1fr_1.5fr_auto] md:items-end">
              <div className="space-y-2">
                <Label htmlFor="project-name">Project name</Label>
                <Input id="project-name" value={name} onChange={(event) => setName(event.target.value)} minLength={2} maxLength={100} required placeholder="Sindh legal research" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="project-description">Description</Label>
                <Input id="project-description" value={description} onChange={(event) => setDescription(event.target.value)} maxLength={500} placeholder="Gazettes and notifications from official sources" />
              </div>
              <Button type="submit" disabled={create.isPending || name.trim().length < 2}>
                {create.isPending && <Loader2 className="size-4 animate-spin" />} Create project
              </Button>
              <fieldset className="flex gap-2 md:col-span-3">
                <legend className="sr-only">Project color</legend>
                {colors.map((value) => (
                  <button key={value} type="button" aria-label={`Use ${value}`} aria-pressed={color === value} onClick={() => setColor(value)} className={cn("size-7 rounded-full border-2 border-background ring-offset-2 ring-offset-background", color === value && "ring-2 ring-primary")} style={{ backgroundColor: value }} />
                ))}
              </fieldset>
            </CardContent>
          </form>
        </Card>
      )}

      {query.isLoading ? (
        <div className="flex h-64 items-center justify-center"><Loader2 className="size-5 animate-spin text-primary" /></div>
      ) : query.data?.length ? (
        <div className="grid gap-5 lg:grid-cols-2 2xl:grid-cols-3">
          {query.data.map((project) => (
            <Card key={project.id} className="overflow-hidden">
              <div className="h-1" style={{ backgroundColor: project.color }} />
              {editing?.id === project.id ? (
                <form onSubmit={(event) => { event.preventDefault(); update.mutate(editing); }}>
                  <CardHeader>
                    <div className="space-y-2"><Label htmlFor={`edit-${project.id}`}>Project name</Label><Input id={`edit-${project.id}`} value={editing.name} onChange={(event) => setEditing({ ...editing, name: event.target.value })} minLength={2} required /></div>
                    <div className="space-y-2"><Label htmlFor={`description-${project.id}`}>Description</Label><Input id={`description-${project.id}`} value={editing.description} onChange={(event) => setEditing({ ...editing, description: event.target.value })} /></div>
                  </CardHeader>
                  <CardContent className="flex justify-end gap-2"><Button type="button" variant="ghost" onClick={() => setEditing(null)}>Cancel</Button><Button type="submit" disabled={update.isPending}>Save</Button></CardContent>
                </form>
              ) : (
                <>
                  <CardHeader>
                    <div className="flex items-start justify-between gap-4">
                      <div><CardTitle>{project.name}</CardTitle><CardDescription className="mt-1 min-h-10">{project.description || "No description added."}</CardDescription></div>
                      <div className="flex gap-1">
                        <Button aria-label={`Edit ${project.name}`} title="Edit project" size="icon" variant="ghost" onClick={() => setEditing(project)}><Pencil className="size-4" /></Button>
                        {pendingDelete === project.id ? (
                          <Button aria-label={`Confirm deletion of ${project.name}`} title="Confirm delete" size="sm" variant="destructive" onClick={() => remove.mutate(project.id)} disabled={remove.isPending}>Confirm</Button>
                        ) : (
                          <Button aria-label={`Delete ${project.name}`} title="Delete project" size="icon" variant="ghost" onClick={() => setPendingDelete(project.id)}><Trash2 className="size-4" /></Button>
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-3 gap-3 rounded-lg bg-secondary/50 p-3 text-center">
                      <ProjectMetric label="Jobs" value={project.total_jobs} />
                      <ProjectMetric label="Active" value={project.active_jobs} />
                      <ProjectMetric label="Finished" value={project.completed_jobs} />
                    </div>
                    <div className="mt-4 flex items-center justify-between gap-3">
                      <Badge>{`Updated ${formatDate(project.updated_at)}`}</Badge>
                      <Link href={`/projects/${project.id}`} className={buttonVariants({ variant: "outline", size: "sm" })}>Open project <ArrowRight className="size-3.5" /></Link>
                    </div>
                  </CardContent>
                </>
              )}
            </Card>
          ))}
        </div>
      ) : (
        <Card><CardContent className="flex min-h-80 flex-col items-center justify-center text-center"><div className="mb-4 rounded-xl bg-primary/10 p-3 text-primary"><FolderKanban className="size-6" /></div><h3 className="font-semibold">Create your first project</h3><p className="mt-2 max-w-sm text-sm text-muted-foreground">Projects keep jobs organized without changing how the crawler works.</p><Button className="mt-5" onClick={() => setShowForm(true)}><Plus className="size-4" /> New project</Button></CardContent></Card>
      )}
    </div>
  );
}

function ProjectMetric({ label, value }: { label: string; value: number }) {
  return <div><div className="font-mono text-lg font-semibold">{value}</div><div className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</div></div>;
}
