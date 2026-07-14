import { Card } from "@/components/ui/card";

export default function DashboardLoading() {
  return <div className="animate-pulse"><div className="mb-8 h-8 w-64 rounded bg-secondary" /><div className="mb-6 h-4 w-96 max-w-full rounded bg-secondary" /><div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">{Array.from({ length: 4 }, (_, index) => <Card key={index} className="h-36 bg-card/60" />)}</div></div>;
}
