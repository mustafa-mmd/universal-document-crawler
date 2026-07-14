export interface GuideSection {
  title: string;
  paragraphs?: string[];
  steps?: string[];
  bullets?: string[];
  code?: string;
  note?: string;
}

export interface Guide {
  slug: string;
  title: string;
  description: string;
  category: "Start here" | "Crawler" | "Operations" | "Reference";
  readTime: string;
  sections: GuideSection[];
}

export const guides: Guide[] = [
  {
    slug: "quick-start",
    title: "Quick start",
    description: "Start the backend and frontend, confirm the connection, and run a safe first crawl.",
    category: "Start here",
    readTime: "6 min",
    sections: [
      { title: "What this application does", paragraphs: ["UDC Pro discovers pages on a public website, identifies supported document links, downloads matching files to local storage, and records searchable metadata. The web dashboard controls jobs while the Python backend performs crawling and persistence."] },
      { title: "1. Start the backend", code: "cd C:\\Users\\musta\\universal-document-crawler\n.\\venv\\Scripts\\Activate.ps1\npython -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8010", note: "Keep this PowerShell window open. A healthy backend prints “Application startup complete.”" },
      { title: "2. Start the frontend", code: "cd C:\\Users\\musta\\universal-document-crawler\\frontend\nnpm install\nnpm run dev -- --port 3001", note: "Use a second PowerShell window. Open http://localhost:3001 after Next.js reports Ready." },
      { title: "3. Confirm connection", steps: ["Open Overview.", "Check the bottom-left workspace indicator. It must say the API is connected.", "If it is disconnected, verify the backend terminal and NEXT_PUBLIC_API_URL in frontend/.env.local."] },
      { title: "4. Create a first crawl", steps: ["Open New crawl.", "Enter a descriptive job name and a public HTTPS URL.", "Keep conservative limits such as depth 1, pages 20, and files 10 for the first run.", "Select PDF and any other required types.", "Keep Respect robots.txt enabled, then start the crawl.", "Watch live progress in Jobs and downloaded results in Documents."] },
    ],
  },
  {
    slug: "crawl-limits",
    title: "Crawl limits explained",
    description: "Understand depth, page, file, retry, and pacing limits before running a job.",
    category: "Crawler",
    readTime: "5 min",
    sections: [
      { title: "Depth", paragraphs: ["Depth is the number of link levels followed from the starting page. Depth 0 inspects only the starting page. Depth 1 also opens pages linked directly from it. Larger depth values can expand the crawl dramatically."] },
      { title: "Pages", paragraphs: ["Pages is the maximum number of HTML pages the crawler may inspect. When the limit is reached, remaining queued pages are not opened."] },
      { title: "Files", paragraphs: ["Files is the maximum number of matching documents saved during the run. It is a hard cap for new downloads, not a performance setting."] },
      { title: "Timeout, delay, and retries", bullets: ["Timeout: maximum seconds allowed for one browser or download request.", "Delay: minimum pause between page visits; increase it to reduce pressure on the target.", "Retries: additional attempts after the first failed download. Zero still means one initial attempt."] },
      { title: "Recommended starting profile", code: "Depth: 1\nPages: 20\nFiles: 10\nDelay: 0.5 seconds\nRetries: 2", note: "Increase limits only after verifying the target structure and your authorization to crawl it." },
    ],
  },
  {
    slug: "filters-and-safety",
    title: "Filters and crawl safety",
    description: "Control what is followed and downloaded while respecting website policies.",
    category: "Crawler",
    readTime: "7 min",
    sections: [
      { title: "Domain and JavaScript controls", bullets: ["Same domain only prevents discovery from expanding to external websites.", "Enable JavaScript renders dynamic pages that do not expose links in their initial HTML.", "Respect robots.txt checks the publisher's machine-readable crawling policy before visiting pages."] },
      { title: "Document filters", bullets: ["File types restrict downloads by supported extension.", "Include keywords require at least one comma-separated term in the document URL.", "Exclude keywords skip any URL containing a blocked term.", "Filename contains adds a strict filename substring check.", "Minimum and maximum size are evaluated when the server provides a valid size or after download validation."] },
      { title: "Built-in protection", paragraphs: ["The backend rejects localhost, private-network, link-local, and other non-public targets. Redirects are validated again. This reduces server-side request forgery risk but does not replace organizational authorization, legal review, or responsible rate limits."] },
    ],
  },
  {
    slug: "jobs-and-projects",
    title: "Jobs and projects",
    description: "Organize work and safely pause, resume, stop, restart, or duplicate crawls.",
    category: "Operations",
    readTime: "6 min",
    sections: [
      { title: "Projects", paragraphs: ["A project is a persisted workspace for related jobs. Create one for a website, client, department, or research objective, then select it when creating a crawl. Deleting a project does not delete its jobs; those jobs become unassigned."] },
      { title: "Job lifecycle", bullets: ["Queued: saved and waiting for its worker to begin.", "Running: actively inspecting pages or downloading files.", "Paused: the worker stops at the next safe control checkpoint.", "Completed: the crawl reached its natural end or configured limits.", "Failed: an unrecoverable error ended the job; inspect its error and Runtime logs.", "Stopped: a user intentionally ended the job."] },
      { title: "Controls", bullets: ["Pause and resume preserve the live in-process crawler state.", "Stop ends the active run at its next safe checkpoint.", "Restart creates and immediately starts a new job from the original immutable configuration.", "Duplicate creates a queued copy that can be reviewed before it is started.", "Delete is allowed only after a job is no longer active."] },
      { title: "Application restart behavior", note: "In-process workers cannot survive a backend process restart. Jobs left queued, running, or paused are recovered as stopped so the dashboard never claims nonexistent work is still active." },
    ],
  },
  {
    slug: "documents-and-logs",
    title: "Documents and logs",
    description: "Manage local files, inspect provenance, and diagnose common failures.",
    category: "Operations",
    readTime: "6 min",
    sections: [
      { title: "Document library", bullets: ["Search by filename or source URL.", "The download icon serves one verified local file through the backend when only a specific document is needed.", "Download all creates one ZIP containing every available document plus a manifest.json file with source and integrity metadata. When search is active, Download results includes only matching documents.", "The archive is assembled on temporary server disk instead of being loaded into RAM. Keep free-tier exports small; large production libraries should export from durable object storage.", "Rename changes both the local filename and the metadata record; the extension cannot be changed.", "Delete removes one local file and its metadata record after an explicit confirmation.", "Clear library removes every document record from the application screen but never deletes files from PC folders. A later crawl may index those files again.", "A missing-file warning means metadata exists but the file was moved or deleted outside the application; delete the stale record to clean it up."] },
      { title: "Runtime logs", paragraphs: ["Crawler, download, and error logs are separate so operational events are easier to filter. The Logs page refreshes automatically, supports text filtering, and can truncate the current log set after confirmation."] },
      { title: "Common errors", bullets: ["ERR_INTERNET_DISCONNECTED: the machine or target connection was unavailable during navigation.", "Timeout: the target did not respond within the configured request limit.", "robots.txt denied: publisher policy blocked the requested page.", "Local file no longer exists: the document was changed outside UDC Pro.", "Backend disconnected: the frontend cannot reach NEXT_PUBLIC_API_URL; check the backend terminal and port."] },
    ],
  },
  {
    slug: "settings-and-production",
    title: "Settings and deployment boundaries",
    description: "Configure runtime behavior and understand the local production profile.",
    category: "Reference",
    readTime: "8 min",
    sections: [
      { title: "Settings behavior", paragraphs: ["Storage, browser engine, headless mode, user agent, proxy, timeout, and retries are real runtime inputs. They are copied into each new job as an immutable snapshot. Changing Settings never silently changes an existing job."] },
      { title: "Browser installation", code: ".\\venv\\Scripts\\python.exe -m playwright install chromium", note: "Install firefox or webkit explicitly before selecting those engines." },
      { title: "Local production profile", bullets: ["FastAPI API bound to a trusted local or internal interface.", "Next.js production build started with npm run build and npm run start.", "SQLite databases and downloaded files backed up together.", "A dedicated operating-system user with limited filesystem permissions.", "TLS and authentication added at a trusted reverse proxy before exposing the service to other users."] },
      { title: "Important boundary", note: "The included profile is production-capable for a trusted single-machine workspace. Public multi-user deployment still requires authentication, authorization, TLS, secret management, centralized workers, durable shared storage, monitoring, backups, and a deployment-specific security review." },
    ],
  },
];

export function getGuide(slug: string) {
  return guides.find((guide) => guide.slug === slug);
}
