import { CrawlerForm } from "@/features/crawler/crawler-form";

export default async function CrawlerPage({ searchParams }: { searchParams: Promise<{ project_id?: string }> }) {
  const { project_id: projectId } = await searchParams;
  return <CrawlerForm initialProjectId={projectId} />;
}
