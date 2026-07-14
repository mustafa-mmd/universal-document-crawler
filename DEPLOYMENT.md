# Deployment guide: GitHub, Render, and Vercel

This repository deploys as two services:

- `backend/` and `crawler/`: Docker web service on Render
- `frontend/`: Next.js application on Vercel

## Before deploying

The current cloud profile is a single-instance application. Render must keep one instance because SQLite and downloaded files live on one attached persistent disk.

The committed `render.yaml` uses:

- Render Starter web service
- One 10 GB persistent disk mounted at `/app/data`
- Docker with the Playwright Chromium runtime
- Health check at `/api/v1/health`

This is a paid Render configuration. The free Render plan has an ephemeral filesystem and is not appropriate when jobs, metadata, or downloads must survive restarts.

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
4. Render detects `render.yaml` at the repository root.
5. When prompted for `UDC_ALLOWED_ORIGINS`, enter a temporary expected Vercel URL, for example `https://universal-document-crawler.vercel.app`.
6. Review the paid Starter service and 10 GB disk, then apply the Blueprint.
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
5. Add this environment variable for Production, Preview, and Development:

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

Save and deploy the service. Then open the Vercel frontend and confirm the bottom-left indicator says the API is connected.

## 5. Post-deployment verification

1. Open Overview and confirm the backend connection indicator.
2. Create a project and delete it.
3. Run a very small crawl: depth 0, one page, one file.
4. Confirm the job status updates.
5. Confirm a downloaded document appears in Documents.
6. Redeploy the Render service and verify the job/document metadata still exists on the persistent disk.

## Operational boundaries

- The backend API is publicly reachable. CORS limits browser origins but is not authentication.
- Do not market this deployment as a public multi-user SaaS until authentication, authorization, per-user quotas, rate limiting, and audit logging are added.
- Keep one Render instance while using SQLite and a persistent disk.
- Render disk-backed deploys have brief downtime because the disk can attach to only one service instance.
- Review bandwidth and disk usage regularly; downloaded documents can grow quickly.
