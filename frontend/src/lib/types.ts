export type JobStatus = "queued" | "running" | "paused" | "completed" | "failed" | "stopped";

export interface CrawlJob {
  id: string;
  name: string;
  url: string;
  status: JobStatus;
  progress: number;
  config: Record<string, unknown>;
  stats: Record<string, number | string>;
  current_url?: string | null;
  current_file?: string | null;
  error?: string | null;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  color: string;
  created_at: string;
  updated_at: string;
  total_jobs: number;
  active_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
}

export interface DashboardData {
  summary: {
    total_jobs: number;
    active_jobs: number;
    completed_jobs: number;
    failed_jobs: number;
    total_documents: number;
    storage_bytes: number;
    total_projects: number;
  };
  file_types: Array<{ name: string; value: number }>;
  websites: Array<{ name: string; value: number }>;
  recent_jobs: CrawlJob[];
}

export interface RuntimeSettings {
  download_directory: string;
  browser_type: "chromium" | "firefox" | "webkit";
  headless: boolean;
  user_agent: string;
  proxy: string;
  timeout_seconds: number;
  retry_count: number;
}

export interface DocumentItem {
  id: string;
  name: string;
  url: string;
  local_path: string;
  size: number;
  sha256?: string;
  mime_type?: string;
  downloaded_at: string;
  extension: string;
  exists: boolean;
}
