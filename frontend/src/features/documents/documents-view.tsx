"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, File, FilePenLine, FileSearch, Loader2, Search, ShieldAlert, Trash2, X } from "lucide-react";
import { useDeferredValue, useState } from "react";
import { ApiErrorState } from "@/components/api-error";
import { PageHeading } from "@/components/page-heading";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { API_BASE, api } from "@/lib/api";
import type { DocumentItem } from "@/lib/types";
import { cn, formatBytes, formatDate } from "@/lib/utils";

export function DocumentsView() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState<DocumentItem | null>(null);
  const [newName, setNewName] = useState("");
  const [pendingDelete, setPendingDelete] = useState<string | null>(null);
  const [confirmClear, setConfirmClear] = useState(false);
  const deferred = useDeferredValue(search);
  const query = useQuery({ queryKey: ["documents", deferred], queryFn: () => api.documents(deferred) });
  const refresh = () => queryClient.invalidateQueries({ queryKey: ["documents"] });
  const rename = useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) => api.renameDocument(id, name),
    onSuccess: () => { setEditing(null); refresh(); },
  });
  const remove = useMutation({
    mutationFn: (id: string) => api.deleteDocument(id),
    onSuccess: () => { setPendingDelete(null); refresh(); },
  });
  const clear = useMutation({
    mutationFn: api.clearDocuments,
    onSuccess: () => {
      setConfirmClear(false);
      setPendingDelete(null);
      setEditing(null);
      refresh();
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
  const error = query.error ?? rename.error ?? remove.error ?? clear.error;

  function beginRename(document: DocumentItem) {
    setEditing(document);
    setNewName(document.name);
    setPendingDelete(null);
  }

  return (
    <div>
      <PageHeading
        eyebrow="Document explorer"
        title="Your document library"
        description="Search downloaded files, open their sources, rename local copies, or remove files and metadata safely."
        action={<div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row"><div className="relative sm:w-72"><Search className="absolute left-3 top-3 size-4 text-muted-foreground" /><Input aria-label="Search documents" value={search} onChange={(event) => setSearch(event.target.value)} className="pl-9" placeholder="Search names or URLs…" /></div>{confirmClear ? <div className="flex gap-2"><Button variant="destructive" onClick={() => clear.mutate()} disabled={clear.isPending}>{clear.isPending && <Loader2 className="size-4 animate-spin" />} Confirm clear</Button><Button variant="ghost" onClick={() => setConfirmClear(false)}>Cancel</Button></div> : <Button variant="outline" onClick={() => setConfirmClear(true)} disabled={!query.data?.length}><Trash2 className="size-4" /> Clear library</Button>}</div>}
      />
      {error && <div className="mb-5"><ApiErrorState message={(error as Error).message} /></div>}
      {confirmClear && <div className="mb-5 rounded-xl border border-amber-500/25 bg-amber-500/[0.06] p-4 text-sm leading-6 text-muted-foreground"><strong className="text-foreground">This only clears the application library.</strong> All original files will remain untouched in their PC folders. A later crawl may add existing files back to this list.</div>}
      <Card>
        <CardContent className="p-0">
          <div className="hidden grid-cols-[1.3fr_76px_90px_1fr_110px_150px] gap-4 border-b px-5 py-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground lg:grid"><span>Name</span><span>Type</span><span>Size</span><span>Source</span><span>Downloaded</span><span className="text-right">Actions</span></div>
          <div className="divide-y">
            {query.isLoading ? <div className="flex h-48 items-center justify-center"><Loader2 className="size-5 animate-spin text-primary" /></div> : query.data?.length ? query.data.map((document) => (
              <div key={document.id} className="grid gap-3 px-5 py-4 lg:grid-cols-[1.3fr_76px_90px_1fr_110px_150px] lg:items-center">
                <div className="flex min-w-0 items-center gap-3">
                  <div className={cn("flex size-9 shrink-0 items-center justify-center rounded-lg", document.exists ? "bg-primary/10 text-primary" : "bg-amber-500/10 text-amber-500")}>
                    {document.exists ? <File className="size-4" /> : <ShieldAlert className="size-4" />}
                  </div>
                  <div className="min-w-0 flex-1">
                    {editing?.id === document.id ? (
                      <form className="flex gap-2" onSubmit={(event) => { event.preventDefault(); rename.mutate({ id: document.id, name: newName.trim() }); }}>
                        <Input aria-label="New document filename" value={newName} onChange={(event) => setNewName(event.target.value)} required autoFocus className="h-8" />
                        <Button aria-label="Save filename" size="sm" disabled={rename.isPending || !newName.trim()}>Save</Button>
                        <Button aria-label="Cancel rename" type="button" size="icon" variant="ghost" className="size-8" onClick={() => setEditing(null)}><X className="size-4" /></Button>
                      </form>
                    ) : <><p className="truncate text-sm font-medium">{document.name}</p><p className="truncate font-mono text-[9px] text-muted-foreground">{document.exists ? document.local_path : "Local file is missing"}</p></>}
                  </div>
                </div>
                <div><Badge tone="info">{document.extension || "file"}</Badge></div>
                <span className="font-mono text-xs text-muted-foreground">{formatBytes(document.size)}</span>
                <a href={document.url} target="_blank" rel="noreferrer" title={document.url} className="truncate text-xs text-muted-foreground hover:text-primary">{document.url}</a>
                <time className="font-mono text-[10px] text-muted-foreground">{formatDate(document.downloaded_at)}</time>
                <div className="flex justify-end gap-1">
                  {document.exists && <a aria-label={`Download ${document.name}`} title="Download file" className={buttonVariants({ variant: "ghost", size: "icon" })} href={`${API_BASE}/documents/${document.id}/download`}><Download className="size-4" /></a>}
                  {document.exists && <Button aria-label={`Rename ${document.name}`} title="Rename file" variant="ghost" size="icon" onClick={() => beginRename(document)}><FilePenLine className="size-4" /></Button>}
                  {pendingDelete === document.id ? (
                    <Button aria-label={`Confirm deletion of ${document.name}`} variant="destructive" size="sm" disabled={remove.isPending} onClick={() => remove.mutate(document.id)}>Confirm</Button>
                  ) : (
                    <Button aria-label={`Delete ${document.name}`} title={document.exists ? "Delete file and record" : "Remove stale record"} variant="ghost" size="icon" onClick={() => { setEditing(null); setPendingDelete(document.id); }}><Trash2 className="size-4" /></Button>
                  )}
                </div>
              </div>
            )) : <div className="flex flex-col items-center justify-center gap-3 py-20"><div className="rounded-xl bg-secondary p-3"><FileSearch className="size-5 text-muted-foreground" /></div><div className="text-center"><p className="text-sm font-medium">No documents found</p><p className="mt-1 text-xs text-muted-foreground">Downloaded files appear here with source and local path metadata.</p></div></div>}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
