"use client";

import { RotateCcw, TriangleAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export default function DashboardError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <Card><CardContent className="flex min-h-80 flex-col items-center justify-center text-center"><div className="mb-4 rounded-xl bg-destructive/10 p-3 text-destructive"><TriangleAlert className="size-6" /></div><h2 className="font-semibold">This page could not be rendered</h2><p className="mt-2 max-w-lg text-sm text-muted-foreground">{error.message || "An unexpected interface error occurred."}</p><Button className="mt-5" onClick={reset}><RotateCcw className="size-4" /> Try again</Button></CardContent></Card>;
}
