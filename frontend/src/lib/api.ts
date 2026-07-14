import type {
  CrawlJob,
  DashboardData,
  DocumentItem,
  Project,
  RuntimeSettings,
} from "@/lib/types";

export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8010/api/v1";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(body.detail ?? "The API request failed", response.status);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string; service: string; version: string }>("/health"),
  dashboard: () => request<DashboardData>("/dashboard"),
  jobs: (projectId?: string) =>
    request<CrawlJob[]>(projectId ? `/jobs?project_id=${encodeURIComponent(projectId)}` : "/jobs"),
  createJob: (payload: unknown) =>
    request<CrawlJob>("/jobs", { method: "POST", body: JSON.stringify(payload) }),
  jobAction: (id: string, action: string) =>
    request<CrawlJob>(`/jobs/${id}/actions`, {
      method: "POST",
      body: JSON.stringify({ action }),
    }),
  deleteJob: (id: string) => request<void>(`/jobs/${id}`, { method: "DELETE" }),
  documents: (search = "") =>
    request<DocumentItem[]>(`/documents?search=${encodeURIComponent(search)}`),
  documentArchiveUrl: (search = "") =>
    `${API_BASE}/documents/archive?search=${encodeURIComponent(search)}`,
  renameDocument: (id: string, name: string) =>
    request<DocumentItem>(`/documents/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ name }),
    }),
  deleteDocument: (id: string, deleteFile = true) =>
    request<void>(`/documents/${id}?delete_file=${deleteFile}`, { method: "DELETE" }),
  clearDocuments: () =>
    request<{ cleared: number; local_files_deleted: false }>("/documents", { method: "DELETE" }),
  projects: () => request<Project[]>("/projects"),
  project: (id: string) => request<Project>(`/projects/${id}`),
  createProject: (payload: { name: string; description: string; color: string }) =>
    request<Project>("/projects", { method: "POST", body: JSON.stringify(payload) }),
  updateProject: (id: string, payload: Partial<Pick<Project, "name" | "description" | "color">>) =>
    request<Project>(`/projects/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteProject: (id: string) => request<void>(`/projects/${id}`, { method: "DELETE" }),
  settings: () => request<RuntimeSettings>("/settings"),
  updateSettings: (payload: unknown) =>
    request<RuntimeSettings>("/settings", {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  logs: () => request<Record<string, string[]>>("/logs"),
  clearLogs: () => request<void>("/logs", { method: "DELETE" }),
};
