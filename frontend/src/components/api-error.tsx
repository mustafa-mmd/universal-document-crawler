import { AlertTriangle, ServerOff } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

export function ApiErrorState({ message }: { message?: string }) {
  return (
    <Card className="border-amber-500/25 bg-amber-500/[0.04]">
      <CardContent className="flex items-start gap-3 p-4">
        <div className="rounded-lg bg-amber-500/10 p-2 text-amber-500"><ServerOff className="size-4" /></div>
        <div><p className="text-sm font-medium">Backend connection unavailable</p><p className="mt-1 text-xs leading-5 text-muted-foreground">{message ?? "Start the FastAPI service on port 8000, then refresh this view."}</p></div>
        <AlertTriangle className="ml-auto size-4 text-amber-500" />
      </CardContent>
    </Card>
  );
}
