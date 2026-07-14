# Universal Document Crawler Pro

Universal Document Crawler Pro is a local-first document crawling and management platform. It combines a Playwright-powered crawler, a persisted FastAPI job service, and a polished Next.js control center.

## Introduction

Universal Document Crawler Pro helps you find and download public documents from a website without opening every page manually. You provide a public website address, choose the document formats and limits, and the application explores internal pages, discovers matching files, downloads them, and records their metadata.

The application is useful for:

- Researchers collecting reports, publications, laws, policies, or datasets
- Government and institutional websites with documents spread across many pages
- Teams creating a searchable local document collection
- Developers studying web crawling, FastAPI, Next.js, Playwright, and document-processing architecture
- Portfolio demonstrations of a production-oriented full-stack Python and TypeScript application

Only crawl public websites that you are authorized to access. Respect the website's terms, copyright rules, rate limits, and robots.txt policy.

## What the application does

1. A user creates a crawl job from the Next.js dashboard.
2. FastAPI validates and saves the complete job configuration in SQLite.
3. A background job starts the Playwright browser.
4. The crawler loads the starting webpage and analyzes its links.
5. Internal webpage links are added to the page queue.
6. Matching document links are added to the download queue.
7. HTTPX downloads allowed files into the local download directory.
8. Each file is hashed with SHA-256 to detect duplicate content.
9. Crawl pages, downloaded files, failures, and job progress are stored in SQLite.
10. The dashboard polls the API and displays live status, progress, documents, analytics, and logs.

The browser engine and download engine are separate. Playwright renders JavaScript-heavy webpages, while HTTPX performs efficient streamed file downloads.

## Main features

### Dashboard

- Total, active, completed, and failed crawl jobs
- Total downloaded documents and local storage usage
- Crawl throughput chart
- File-type distribution chart
- Top source websites
- Recent crawl activity
- Designed empty, loading, offline, and error states
- Responsive dark and light themes

### Crawler manager

- Public HTTP and HTTPS starting URL
- Crawl name for easy identification
- Maximum crawl depth
- Maximum number of webpages
- Maximum number of downloads
- Same-domain-only crawling
- JavaScript rendering on or off
- robots.txt enforcement
- Request timeout and rate limiting
- Retry control
- Include and exclude keyword filters
- Filename text filter
- Minimum and maximum file-size filters
- Immutable configuration saved with every job

### Supported document formats

The crawler can detect and download:

- PDF
- DOC and DOCX
- XLS and XLSX
- PPT and PPTX
- CSV and TXT
- JSON and XML
- ZIP, RAR, and 7Z
- EPUB
- ODT and ODS
- RTF

Only the formats selected in the crawl form are accepted for that job.

### Job management

- Start a crawl job
- View live page, file, queue, elapsed-time, and progress information
- Pause and resume an active job
- Stop an active job cooperatively
- Restart a finished, stopped, or failed job
- Duplicate a job configuration
- Start or stop a queued duplicate after reviewing it
- Delete an inactive job
- Persist job history across backend restarts

### Projects

- Create persisted workspaces for a website, client, or research objective
- Edit project names and descriptions
- Assign a new crawl to a project
- View project-specific job counts and history
- Delete a project without deleting its crawl jobs

### Document explorer

- List files recorded by the crawler
- Search by filename, URL, or local path
- View file type, size, source URL, download time, and content hash
- Download an existing local file through the API
- Rename a local file while preserving its extension and metadata link
- Delete a file and its metadata after explicit confirmation
- Clear the entire application library without deleting any files from PC folders
- Detect when a recorded local file no longer exists

### Analytics and logs

- Documents grouped by website
- Documents grouped by file type
- Crawl and storage summary metrics
- Crawler, downloader, and error log views
- Automatic log refresh in the dashboard
- Search within the active log and safely clear runtime logs

### In-application documentation

- Quick-start guide with exact Windows commands
- Crawl-limit and filter explanations
- Project and job operating procedures
- Document-management and troubleshooting reference
- Settings and deployment-boundary guidance

### Settings

- Download-directory preference used by new jobs
- Playwright browser engine and headless-mode preferences
- Timeout and retry preferences
- Proxy and user-agent runtime settings

Settings are persisted for the workspace and copied into each new job as an immutable runtime snapshot. Existing jobs keep their original configuration, including when restarted or duplicated.

### Safety and data integrity

- Private, loopback, and reserved network targets are blocked to reduce SSRF risk
- Optional robots.txt enforcement
- Same-domain restriction enabled by default
- Bounded crawl depth, pages, downloads, retries, and timeouts
- Streamed downloads instead of loading entire files into memory
- Partial-file handling for interrupted downloads
- SHA-256 content hashing
- Duplicate-content detection and hard-link reuse when supported by Windows
- Safe local filenames and per-website storage folders

## How files and data are stored

Downloaded files are stored under the configured download root. The default is `D:\Document Downloader` when that drive is available; otherwise the project uses `downloads\`.

The folder layout is:

```text
download root/
    website-host/
        website-section/
            document.pdf
```

Application data is stored locally:

```text
database/application.db  # jobs and application settings
database/crawler.db      # crawled pages, downloads, failures, and sessions
logs/crawler.log         # crawler activity
logs/download.log        # download activity
logs/errors.log          # errors
```

The application does not upload downloaded documents to an external cloud service in the current local profile.

## Implemented milestone

- Configurable public-website crawling with JavaScript rendering and robots.txt support
- Exact file-type selection across PDF, Office, text, data, archive, and OpenDocument formats
- Crawl limits, keyword filters, filename filters, size limits, retries, timeouts, and throttling
- SQLite resume metadata, SHA-256 duplicate detection, partial downloads, and per-site storage
- Persisted API jobs with live status, progress, pause, resume, stop, restart, duplicate, and delete
- Dashboard metrics, file-type/source analytics, recent activity, document rename/delete/download, settings, and searchable logs
- Persisted project CRUD, project-scoped jobs, and project detail workspaces
- Complete in-application user documentation and operational guidance
- Responsive dark/light Next.js dashboard with offline, empty, loading, and error states
- Private-network/loopback crawl protection to reduce server-side request forgery risk

The current local profile intentionally uses SQLite and in-process job threads. `ApplicationRepository` and `JobManager` are the boundaries for later MongoDB, Redis, and Celery adapters.

## Architecture

```text
Next.js 15 dashboard (frontend/)
        | REST + polling
FastAPI application (backend/)
        | persisted job orchestration
Crawler coordinator (crawler/)
        |- Playwright browser + page analyzer
        |- document detector + robots policy
        |- queue + cooperative job controls
        `- HTTPX downloader + content hashing
                |
        local files + SQLite metadata
```

### Project structure

```text
backend/                 FastAPI routes, schemas, job manager, security, repository
crawler/                 browser, analyzer, detector, queue, downloader, database
frontend/                Next.js dashboard and reusable UI components
frontend/src/app/        application routes and layouts
frontend/src/features/   dashboard, crawler, projects, jobs, documents, logs, settings
tests/                   crawler, database, queue, downloader, and API tests
database/                local SQLite databases (ignored by Git)
downloads/               downloaded documents (ignored by Git)
logs/                    runtime logs and local screenshots (ignored by Git)
app.py                   command-line crawler entry point
config.py                environment-driven crawler defaults
```

## Crawl configuration guide

### Basic fields

| Field | Purpose | Suggested first value |
|---|---|---|
| Job name | Human-readable name shown in Jobs | `Example publications` |
| Website URL | Public page where discovery begins | `https://example.com` |
| Depth | Number of link levels followed from the first page | `2` or `3` |
| Pages | Maximum webpages inspected | `100` |
| Files | Maximum documents downloaded | `100` |

### Important switches

| Setting | Behavior |
|---|---|
| Same domain only | Prevents the crawler from exploring other websites |
| Enable JavaScript | Uses Playwright rendering for dynamic pages |
| Respect robots.txt | Honors the website publisher's crawl instructions |
| Retry failures | Retries temporary download errors up to the configured limit |

### Keyword and size filters

- **Include keywords:** a document URL must contain at least one supplied keyword.
- **Exclude keywords:** a matching document URL is skipped if it contains an excluded keyword.
- **Filename contains:** requires the supplied text to appear in the document URL or filename.
- **Minimum size:** rejects files smaller than the specified number of megabytes.
- **Maximum size:** rejects files larger than the specified number of megabytes.

Keyword filters currently operate on document URLs and filenames, not extracted document text.

### Recommended first crawl

Use a small configuration to confirm the target website behaves correctly:

```text
Depth: 2
Maximum pages: 50
Maximum files: 20
Same domain only: enabled
JavaScript: enabled
Respect robots.txt: enabled
File types: PDF, DOC, DOCX
Rate limit: 0.5 seconds
```

Increase limits only after the small crawl finishes successfully.

## Job statuses and actions

| Status | Meaning |
|---|---|
| Queued | The configuration is saved and waiting to start |
| Running | The crawler is actively processing pages or downloads |
| Paused | Work is temporarily suspended and can be resumed |
| Completed | The crawler finished all available work within its limits |
| Failed | An unrecoverable browser, network, validation, or filesystem error occurred |
| Stopped | The user stopped the job or the backend interrupted it |

- **Pause** waits at a cooperative control point; a currently executing browser request may finish first.
- **Resume** continues a paused job.
- **Stop** ends active processing without deleting existing downloads.
- **Restart** creates a new execution from the saved configuration.
- **Duplicate** copies a configuration so it can be reused or adjusted.
- **Delete** removes the application job record, not the downloaded documents.

## Current local-profile limitations

- Jobs run in the FastAPI process using local background threads. Redis and Celery are planned for distributed execution.
- The crawler coordinator processes one page/download queue per job synchronously; concurrency controls are not advertised in the interface.
- Keyword filters inspect URLs and filenames; full-text filtering is a future document-intelligence feature.
- Authentication, multi-user workspaces, and role-based access are not implemented yet.
- AI assistant, summarization, semantic search, previews, language classification, and document question-answering are not advertised as available features.
- MongoDB is not required in the current local profile; SQLite is used so the application runs without external infrastructure.

This profile is suitable for a trusted single-machine workspace. Before exposing it publicly or serving multiple users, add authentication and authorization, TLS, secret management, centralized durable workers, shared storage, monitoring, backups, rate limiting, and a deployment-specific security review.

## Windows: first-time setup

Install Python 3.11 or newer and Node.js 20 or newer. Then open PowerShell and run these commands one at a time:

```powershell
cd C:\Users\musta\universal-document-crawler

# Create the virtual environment. Skip this if the venv folder already exists.
python -m venv venv

# Activate the virtual environment.
.\venv\Scripts\Activate.ps1

# Install backend and crawler dependencies.
pip install -r requirements.txt

# Install the Chromium browser used by the crawler.
python -m playwright install chromium

# Install frontend dependencies.
cd C:\Users\musta\universal-document-crawler\frontend
npm.cmd install
```

The first-time setup only needs to be performed once.

## Start the application

The backend and frontend must run at the same time. Use two separate PowerShell terminals and leave both terminals open.

### Step 1: start the backend

Open the first PowerShell terminal and run:

```powershell
cd C:\Users\musta\universal-document-crawler
.\venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8010
```

The backend is ready when the terminal displays:

```text
Application startup complete.
```

Backend API documentation: `http://127.0.0.1:8010/docs`

If PowerShell already shows `(venv)` before the prompt, the virtual environment is active and you can skip the activation command.

### Step 2: start the frontend

Open a second PowerShell terminal and run:

```powershell
cd C:\Users\musta\universal-document-crawler\frontend
$env:NEXT_PUBLIC_API_URL="http://127.0.0.1:8010/api/v1"
npm.cmd run dev
```

The frontend terminal will print its address. Normally it is:

```text
http://localhost:3000
```

If port 3000 is occupied, Next.js may use `http://localhost:3001`. Open the exact address displayed in the frontend terminal.

### Step 3: use the application

1. Open the frontend address in Chrome or Edge.
2. Select **New crawl** in the sidebar.
3. Enter a public website URL.
4. Select the document formats you want to download.
5. Select **Start crawl**.
6. Open **Jobs** to monitor progress.
7. Open **Documents** to view downloaded files.
8. Open **Documentation** in the sidebar for complete operating guidance.

### Stop the application

Press `Ctrl+C` in the frontend terminal and then in the backend terminal.

## Optional: save the backend URL permanently

To avoid setting `NEXT_PUBLIC_API_URL` every time, create `frontend/.env.local` containing:

```text
NEXT_PUBLIC_API_URL=http://127.0.0.1:8010/api/v1
```

After creating or changing `.env.local`, stop and restart the frontend server.

## Common startup problems

### Port 8000 is blocked

The commands above use backend port `8010` because some Windows systems reserve or block port 8000.

### Backend connection unavailable

- Confirm the backend terminal is running on port `8010`.
- Confirm the frontend uses `NEXT_PUBLIC_API_URL=http://127.0.0.1:8010/api/v1`.
- Hard-refresh the browser with `Ctrl+Shift+R`.
- The backend accepts local development frontends on ports such as 3000 and 3001.

### PowerShell shows `(venv)`

This is normal. It confirms that the Python virtual environment is active.

### Chromium executable is missing

Run this once from the project root:

```powershell
.\venv\Scripts\python.exe -m playwright install chromium
```

### A crawl completes with zero documents

Check the following:

1. Confirm that the website actually links to downloadable documents.
2. Select the correct file formats in **New crawl**.
3. Temporarily remove include, exclude, filename, and size filters.
4. Increase crawl depth from 1 to 2 or 3.
5. Increase the maximum-pages limit.
6. Keep JavaScript enabled for dynamic websites.
7. Review **Logs** for blocked pages, robots.txt decisions, and download errors.
8. Verify that the files are public and do not require login, CAPTCHA, or a private session.

### A job remains paused or stopped

- Use **Resume** only for a currently paused in-memory job.
- After a backend restart, previously active jobs are marked stopped because their browser process no longer exists.
- Use **Restart** to create a fresh execution from the saved configuration.

### A job fails immediately

- Open **Jobs** and read the error displayed under the job name.
- Open **Logs**, especially `errors.log`.
- Verify the URL includes `http://` or `https://`.
- Confirm the hostname resolves in your browser.
- Private IP addresses, localhost targets, and reserved networks are intentionally blocked.
- Confirm Windows allows Python and Chromium to access the network.

### Where are downloaded documents?

Check `D:\Document Downloader` first. If the D: drive is unavailable, check:

```text
C:\Users\musta\universal-document-crawler\downloads
```

The exact recorded path is also displayed in the **Documents** module.

### Changes do not appear in the browser

1. Confirm the frontend development server is running.
2. Hard-refresh with `Ctrl+Shift+R`.
3. If an environment variable changed, stop the frontend with `Ctrl+C` and start it again.
4. Check the frontend terminal for TypeScript or compilation errors.

## Daily usage summary

After the one-time setup, the normal daily workflow is:

```text
1. Start backend terminal on port 8010
2. Start frontend terminal on port 3000 or 3001
3. Open the frontend URL
4. Create or restart a crawl job
5. Monitor Jobs and Logs
6. Review files in Documents
7. Stop both terminals with Ctrl+C when finished
```

## CLI mode

The crawler can also run without the web application:

```powershell
cd C:\Users\musta\universal-document-crawler
.\venv\Scripts\python.exe app.py https://example.com
```

Environment defaults are documented in `config.py`. Notable options include `UDC_DOWNLOAD_FOLDER`, `UDC_FILE_TYPES`, `UDC_HEADLESS`, `UDC_MAX_PAGES`, `UDC_MAX_CRAWL_DEPTH`, `UDC_MAX_RETRIES`, `UDC_REQUEST_TIMEOUT`, and `UDC_RATE_LIMIT_SECONDS`.

## Verification

```powershell
# Backend and crawler tests
cd C:\Users\musta\universal-document-crawler
.\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp .pytest-run

# Frontend checks
cd C:\Users\musta\universal-document-crawler\frontend
npm.cmd run lint
npm.cmd run build
npm.cmd audit --omit=dev

# Optional browser smoke test while both servers are running
cd C:\Users\musta\universal-document-crawler
.\venv\Scripts\python.exe tests\browser_smoke.py --base-url http://localhost:3001
```

## Cloud deployment

For the no-cost GitHub + Render backend + Vercel frontend workflow, including environment variables, CORS, platform limits, and post-deploy verification, see [DEPLOYMENT.md](DEPLOYMENT.md).

The committed Render Blueprint uses Docker because Chromium requires browser system dependencies and selects Render's Free service plan. Free storage is temporary: SQLite metadata, jobs, settings, logs, and downloaded files can disappear whenever the backend spins down, restarts, or redeploys. Use it only for demos and small tests; durable production deployment requires paid persistent storage or managed database/object storage.

## API surface

- `GET /api/v1/health`
- `GET /api/v1/dashboard`
- `GET|POST /api/v1/jobs`
- `GET|DELETE /api/v1/jobs/{id}`
- `POST /api/v1/jobs/{id}/actions`
- `GET /api/v1/documents`
- `DELETE /api/v1/documents` (clears library metadata; preserves local files)
- `PATCH|DELETE /api/v1/documents/{id}`
- `GET /api/v1/documents/{id}/download`
- `GET|POST /api/v1/projects`
- `GET|PATCH|DELETE /api/v1/projects/{id}`
- `GET|PATCH /api/v1/settings`
- `GET|DELETE /api/v1/logs`

## Next production slices

Authentication/RBAC, WebSocket/SSE push updates, PostgreSQL or managed database repositories, Redis/Celery workers, full-text document extraction, previews/indexing, and retrieval-augmented AI are future deployment slices rather than mocked as completed behavior.
