# Deploying ChronoArb to Render (hackathon demo)

This deployment runs the project as two Render Web Services plus one Render
Postgres database. Authentication is intentionally disabled so reviewers can open
the site without creating an account.

> **Demo only.** `CHRONOARB_AUTH_MODE=disabled` grants the seeded demo user every
> permission. Do not use this configuration for a public or production system.

## What gets deployed

| Render resource | Type | Root directory | Purpose |
|---|---|---|---|
| `chronoarb-api` | Python Web Service | `apps/api` | FastAPI API |
| `chronoarb-web` | Node Web Service | `apps/web` | Next.js frontend |
| `chronoarb-db` | PostgreSQL | — | Stores seeded demo data |

The repository root contains [`render.yaml`](../../render.yaml), so Render can
create all three resources from one Blueprint.

## 1. Push the repository to GitHub

Render deploys from a Git repository:

```powershell
git add .
git commit -m "Prepare hackathon deployment"
git push origin main
```

## 2. Create the Blueprint on Render

1. Sign in at <https://dashboard.render.com>.
2. Choose **New +** → **Blueprint**.
3. Connect the GitHub repository.
4. Select the branch that contains `render.yaml` and approve the Blueprint.
5. When Render asks for `NEXT_PUBLIC_BRYNTUM_LICENSE_KEY`, paste the Bryntum
   Business license key from your local `.env`.
6. Apply the Blueprint and wait for the database and both services to become
   live.

The API start command runs the idempotent seed on every boot:

```text
python -m apps.api.seed && python -m uvicorn apps.api.main:app --host 0.0.0.0 --port $PORT
```

A fresh database is therefore populated with the demo organizations, users,
listings, opportunities, alerts, and admin data automatically.

## 3. Check the generated URLs

Render normally assigns:

- Web: `https://chronoarb-web.onrender.com`
- API: `https://chronoarb-api.onrender.com`

If either name was already taken, Render adds a suffix. Update these variables in
the Render dashboard to the real URLs:

**`chronoarb-api` service**

- `CHRONOARB_CORS_ORIGINS` = the web URL, e.g. `https://chronoarb-web.onrender.com`
- `CHRONOARB_WEB_BASE_URL` = the web URL
- `CHRONOARB_PAYPAL_RETURN_URL` / `CHRONOARB_PAYPAL_CANCEL_URL` = the web URL with the settings paths from `render.yaml`

**`chronoarb-web` service**

- `NEXT_PUBLIC_API_BASE_URL` = the API URL, e.g. `https://chronoarb-api.onrender.com`

`NEXT_PUBLIC_*` values are baked into the JavaScript bundle at build time, so
after changing `NEXT_PUBLIC_API_BASE_URL` or `NEXT_PUBLIC_BRYNTUM_LICENSE_KEY`,
choose **Manual Deploy → Clear build cache & deploy** for the web service.

## 4. Environment variables that matter

| Variable | Service | Value |
|---|---|---|
| `CHRONOARB_ENVIRONMENT` | API | `production` |
| `CHRONOARB_AUTH_MODE` | API | `disabled` |
| `CHRONOARB_DEMO_USER_EMAIL` | API | `owner@demo.example.com` |
| `CHRONOARB_DATABASE_URL` | API | Injected from `chronoarb-db` |
| `CHRONOARB_CORS_ORIGINS` | API | Web service URL |
| `CHRONOARB_WEB_BASE_URL` | API | Web service URL |
| `NEXT_PUBLIC_API_BASE_URL` | Web | API service URL |
| `NEXT_PUBLIC_BRYNTUM_LICENSE_KEY` | Web | Bryntum Business key |

Render's PostgreSQL connection string starts with `postgresql://`. ChronoArb
automatically rewrites it to `postgresql+asyncpg://`, so you can paste Render's
value directly into `CHRONOARB_DATABASE_URL`.

Optional integrations remain disabled until their keys are provided:

- Telegram: `CHRONOARB_TELEGRAM_BOT_TOKEN`, `CHRONOARB_TELEGRAM_BOT_USERNAME`, `CHRONOARB_TELEGRAM_CHAT_ID`
- PayPal: `CHRONOARB_PAYPAL_CLIENT_ID`, `CHRONOARB_PAYPAL_CLIENT_SECRET`, `CHRONOARB_PAYPAL_PLAN_IDS`

## 5. Verify the deployment

- API health: `https://chronoarb-api.onrender.com/health`
- API readiness: `https://chronoarb-api.onrender.com/ready`
- Web: `https://chronoarb-web.onrender.com/opportunities`
- Admin console: `https://chronoarb-web.onrender.com/admin`
- Watches, Alerts, and Activity should open directly with no login screen.

The first request after idle time can take 30–60 seconds on Render's free plan
while the services wake up.

## Local equivalent

To run the same demo mode locally, set these in the repository-root `.env`:

```dotenv
CHRONOARB_AUTH_MODE=disabled
CHRONOARB_DEMO_USER_EMAIL=owner@demo.example.com
```

Then start the API and seed the database once:

```powershell
Set-Location .\apps\api
python -m apps.api.seed
python -m uvicorn apps.api.main:app --reload
```

In another terminal:

```powershell
Set-Location .\apps\web
pnpm dev
```

## Troubleshooting

- **Web shows "Failed to fetch"**: `NEXT_PUBLIC_API_BASE_URL` was wrong at build
  time. Fix the value and redeploy with a cleared build cache.
- **CORS error in the browser**: update `CHRONOARB_CORS_ORIGINS` on the API to the
  exact web origin, including `https://` and no trailing slash.
- **API returns 503 about demo data**: check the API logs for seed errors; the
  start command must run `python -m apps.api.seed` before Uvicorn.
- **Database connection error**: make sure the API service uses the internal
  Render connection string from the `chronoarb-db` database, not an external URL.
- **Bryntum shows a trial badge**: confirm `NEXT_PUBLIC_BRYNTUM_LICENSE_KEY` is set
  on the web service and rebuild the web app.
