"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "next-themes";
import {
  Activity,
  BarChart3,
  BookOpenText,
  CircleCheck,
  CircleX,
  FileSearch,
  FolderKanban,
  Gauge,
  Menu,
  Moon,
  Plus,
  ScanSearch,
  ScrollText,
  Settings,
  Sun,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Button, buttonVariants } from "@/components/ui/button";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

const navigation = [
  { label: "Overview", href: "/dashboard", icon: Gauge },
  { label: "New crawl", href: "/crawler", icon: ScanSearch },
  { label: "Jobs", href: "/jobs", icon: Activity },
  { label: "Documents", href: "/documents", icon: FileSearch },
  { label: "Projects", href: "/projects", icon: FolderKanban },
  { label: "Analytics", href: "/analytics", icon: BarChart3 },
  { label: "Logs", href: "/logs", icon: ScrollText },
];

const secondary = [
  { label: "Documentation", href: "/docs", icon: BookOpenText },
  { label: "Settings", href: "/settings", icon: Settings },
];

function NavLink({ item, onClick }: { item: (typeof navigation)[number]; onClick?: () => void }) {
  const pathname = usePathname();
  const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
  const Icon = item.icon;
  return (
    <Link
      href={item.href}
      onClick={onClick}
      className={cn(
        "group flex h-10 items-center gap-3 rounded-lg px-3 text-sm font-medium text-muted-foreground transition-colors",
        active ? "bg-accent text-foreground" : "hover:bg-accent/60 hover:text-foreground",
      )}
    >
      <Icon className={cn("size-4", active && "text-primary")} />
      <span className="flex-1">{item.label}</span>
    </Link>
  );
}

function Sidebar({ close }: { close?: () => void }) {
  const health = useQuery({
    queryKey: ["health"],
    queryFn: api.health,
    refetchInterval: 10_000,
    retry: 1,
  });
  const connected = health.isSuccess;
  return (
    <div className="flex h-full flex-col">
      <div className="flex h-16 items-center gap-3 px-5">
        <div className="flex size-9 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-[0_0_28px_-6px_var(--primary)]">
          <ScanSearch className="size-5" />
        </div>
        <div>
          <div className="text-sm font-semibold tracking-tight">UDC Pro</div>
          <div className="text-[10px] font-medium uppercase tracking-[0.18em] text-muted-foreground">Document intelligence</div>
        </div>
      </div>
      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
        <div className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground/70">Workspace</div>
        {navigation.map((item) => <NavLink key={item.href} item={item} onClick={close} />)}
        <div className="mb-2 mt-6 px-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground/70">Platform</div>
        {secondary.map((item) => <NavLink key={item.href} item={item} onClick={close} />)}
      </nav>
      <div className="border-t p-3">
        <div className="flex items-center gap-3 rounded-lg border bg-background/50 p-2.5">
          <div className={cn("flex size-8 items-center justify-center rounded-full", connected ? "bg-emerald-500/10 text-emerald-500" : "bg-destructive/10 text-destructive")}>
            {connected ? <CircleCheck className="size-4" /> : <CircleX className="size-4" />}
          </div>
          <div className="min-w-0 flex-1">
            <div className="truncate text-xs font-medium">Local workspace</div>
            <div className="truncate text-[10px] text-muted-foreground">{connected ? `API ${health.data.version} connected` : "Backend disconnected"}</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const { resolvedTheme, setTheme } = useTheme();
  const pathname = usePathname();
  useEffect(() => setMounted(true), []);
  const active = [...navigation, ...secondary].find((item) => pathname.startsWith(item.href));
  return (
    <div className="min-h-screen bg-background">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-60 border-r bg-card/80 backdrop-blur-xl lg:block"><Sidebar /></aside>
      {open && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button aria-label="Close menu" className="absolute inset-0 bg-black/55" onClick={() => setOpen(false)} />
          <aside className="absolute inset-y-0 left-0 w-72 border-r bg-card shadow-2xl"><Sidebar close={() => setOpen(false)} /><Button variant="ghost" size="icon" className="absolute right-3 top-3" onClick={() => setOpen(false)}><X /></Button></aside>
        </div>
      )}
      <div className="lg:pl-60">
        <header className="sticky top-0 z-20 flex h-16 items-center gap-4 border-b bg-background/85 px-4 backdrop-blur-xl sm:px-6">
          <Button aria-label="Open navigation" variant="ghost" size="icon" className="lg:hidden" onClick={() => setOpen(true)}><Menu /></Button>
          <div className="min-w-0 flex-1"><h1 className="truncate text-sm font-semibold">{active?.label ?? "Universal Document Crawler"}</h1><p className="hidden text-xs text-muted-foreground sm:block">Monitor discovery, downloads, and document intelligence</p></div>
          <Button variant="ghost" size="icon" aria-label="Toggle theme" onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}>
            {mounted && resolvedTheme === "dark" ? <Sun className="size-4" /> : <Moon className="size-4" />}
          </Button>
          <Link className={cn(buttonVariants(), "hidden sm:inline-flex")} href="/crawler"><Plus className="size-4" /> New crawl</Link>
        </header>
        <main className="mx-auto max-w-[1600px] p-4 sm:p-6 lg:p-8">{children}</main>
      </div>
    </div>
  );
}
