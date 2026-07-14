# Free deployment guide: GitHub, Render, and Vercel

This repository deploys as two services:

- `backend/` and `crawler/`: Docker web service on Render
- `frontend/`: Next.js application on Vercel

## What the free profile provides

The committed `render.yaml` is configured for a no-cost demo deployment:

- Render Free web service
- Vercel Hobby frontend
- Docker with the Playwright Chromium runtime
- Health check at `/api/v1/health`
- One small crawler job at a time

This is appropriate for personal testing and demonstrations, not production use. Vercel's free Hobby plan is for personal, non-commercial projects. Render Free currently provides limited CPU and 512 MB RAM, spins down after 15 minutes without traffic, and can take about a minute to wake. Its filesystem is ephemeral, so jobs, projects, settings, SQLite metadata, logs, and downloaded files can be erased when the service spins down, restarts, or redeploys.

Use conservative crawl limits on this profile: depth 0 or 1, 5-20 pages, 1-10 files, JavaScript off when the target works without it, and only one running job. Chromium can exceed the free instance's memory on large or JavaScript-heavy sites.

## 1. Push to GitHub

```powershell
cd C:\Users\musta\universal-document-crawler
git status
git push origin main
```

Never commit `frontend/.env.local`, database files, downloads, logs, or credentials. They are ignored by Git.

## 2. Create the Render backend

1. Sign in to Render and connect the GitHub account that owns this repository.
2. Choose **New > Blueprint**.
3. Select `mustafa-mmd/universal-document-crawler` and the `main` branch.
4. Leave **Blueprint Path** blank, or enter `render.yaml`. The file is at the repository root.
5. When prompted for `UDC_ALLOWED_ORIGINS`, enter a temporary expected Vercel URL, for example `https://universal-document-crawler.vercel.app`.
6. Confirm the service plan says **Free** and that no persistent disk is listed, then apply the Blueprint.
7. Wait for the Docker build and health check to finish.
8. Copy the Render service URL, for example:

```text
https://universal-document-crawler-api.onrender.com
```

Verify:

```text
https://YOUR-RENDER-SERVICE.onrender.com/api/v1/health
```

## 3. Create the Vercel frontend

1. Sign in to Vercel and choose **Add New > Project**.
2. Import the same GitHub repository.
3. Set **Root Directory** to `frontend`.
4. Confirm Framework Preset is **Next.js**.
5. Add this environment variable for Production, Preview, and Development (use the exact Render URL from the previous step):

```text
NEXT_PUBLIC_API_URL=https://YOUR-RENDER-SERVICE.onrender.com/api/v1
```

6. Deploy the project.
7. Copy the final production URL, such as `https://universal-document-crawler.vercel.app`.

`NEXT_PUBLIC_API_URL` is browser-visible configuration, not a secret.

## 4. Lock Render CORS to the final Vercel URL

In Render, open the backend service and update:

```text
UDC_ALLOWED_ORIGINS=https://YOUR-FINAL-VERCEL-DOMAIN.vercel.app
```

For multiple exact domains, use a comma-separated list. Do not use `*`.

Save the variable and redeploy the Render service. Then open the Vercel frontend and confirm the bottom-left indicator says the API is connected. The first request after an idle period can take about a minute while Render wakes the service.

## 5. Post-deployment verification

1. Open Overview and confirm the backend connection indicator.
2. Create a project and delete it.
3. Run a very small crawl: depth 0, one page, one file.
4. Confirm the job status updates.
5. Confirm a downloaded document appears in Documents.
6. Refresh the frontend and verify the normal dashboard, Jobs, and Documents requests succeed.

Do not use persistence across restarts as a test on the free profile: local state is expected to disappear.

## Operational boundaries

- The backend API is publicly reachable. CORS limits browser origins but is not authentication.
- Do not market this deployment as a public multi-user SaaS until authentication, authorization, per-user quotas, rate limiting, and audit logging are added.
- The free backend is a temporary demo environment. Never rely on it as the only copy of a downloaded document.
- Keep crawls small. The free service has limited CPU/RAM and may stop a memory-heavy Chromium crawl.
- Download all creates a temporary disk-backed ZIP to keep RAM usage low. Keep free-tier libraries small; large production exports should be generated from durable object storage.
- Render and Vercel usage limits can change. Review both dashboards before enabling public traffic.

## Upgrade path for durable production storage

For a real deployment, change `plan: free` in `render.yaml` to a paid Render instance and attach a persistent disk at `/app/data`, or move metadata to a managed database and documents to object storage. Add authentication, authorization, quotas, rate limiting, backups, and monitoring before serving multiple users.
