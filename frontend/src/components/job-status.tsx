import { Badge } from "@/components/ui/badge";
import type { JobStatus as Status } from "@/lib/types";

const tones: Record<Status, "neutral" | "success" | "warning" | "danger" | "info"> = {
  queued: "neutral",
  running: "info",
  paused: "warning",
  completed: "success",
  failed: "danger",
  stopped: "neutral",
};

export function JobStatus({ status }: { status: Status }) {
  return <Badge tone={tones[status]}><span className="mr-1.5 size-1.5 rounded-full bg-current" />{status}</Badge>;
}
