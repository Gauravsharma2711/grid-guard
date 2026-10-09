# Grid-Guard: Production Deployment Guide for Render

This guide outlines the production deployment of the **Grid-Guard** smart-meter tampering and non-technical loss (NTL) detection platform on [Render](https://render.com).

---

## 1. Architecture Overview

Grid-Guard is deployed as two decoupled, independently scalable services on Render:

```
┌───────────────────────────────────────────────┐
│              Render Static Site               │
│             `grid-guard-frontend`             │
│   React 18 + TypeScript + Vite + CSS Tokens   │
│   Origin: https://grid-guard-frontend.onrender.com
└───────────────────────┬───────────────────────┘
                        │
                        │ HTTPS REST API Calls
                        │ (VITE_API_BASE_URL)
                        ▼
┌───────────────────────────────────────────────┐
│            Render Python Web Service          │
│               `grid-guard-api`                │
│    FastAPI + Uvicorn + LightGBM + Tree-SHAP   │
│    Origin: https://grid-guard-api.onrender.com│
└───────────────────────────────────────────────┘
```

1. **Frontend (`grid-guard-frontend`)**: Deployed as a **Render Static Site** hosting the compiled React SPA bundle. Uses client-side hash routing (`#overview`, `#queue`, etc.) with an SPA rewrite rule (`/* -> /index.html`).
2. **Backend (`grid-guard-api`)**: Deployed as a **Render Web Service** running the FastAPI ASGI application with Uvicorn bound to `0.0.0.0` on `$PORT`.
3. **Communication**: Cross-Origin HTTP requests guarded by FastAPI's `CORSMiddleware`, configured via the `CORS_ORIGINS` environment variable.

---

## 2. Directories and Root Configuration

| Service | Component | Directory Path in Repo | Render Root Directory (`rootDir`) |
| :--- | :--- | :--- | :--- |
| **Backend** | FastAPI Service | `/` (Python package in `src/grid_guard`) | `.` (Repository root) |
| **Frontend** | React SPA | `/frontend` | `frontend` |

---

## 3. Backend (FastAPI Web Service) Configuration

### Build & Start Commands

- **Runtime**: Python `3.11.16`
- **Build Command**:
  ```bash
  pip install uv && uv sync --frozen --no-dev
  ```
  *(Alternative if using pip: `pip install -r requirements.txt`)*
- **Start Command**:
  ```bash
  uv run uvicorn grid_guard.api.main:app --host 0.0.0.0 --port $PORT
  ```
  *(Alternative if using pip: `uvicorn grid_guard.api.main:app --host 0.0.0.0 --port $PORT`)*
- **Health Check Path**: `/health`

### Environment Variables for Backend

Configure these in the Render Dashboard under **Service Settings > Environment**:

| Variable Name | Required | Default / Recommended Value | Description |
| :--- | :---: | :--- | :--- |
| `PYTHON_VERSION` | Yes | `3.11.16` | Python runtime version. Matches `.python-version`. |
| `PORT` | Auto | *(Injected by Render)* | Port assigned dynamically by Render (e.g. `10000`). |
| `CORS_ORIGINS` | Yes | `https://grid-guard-frontend.onrender.com,http://localhost:5173` | Comma-separated list of permitted client origins. **Must include the deployed frontend URL.** |
| `GRID_GUARD_API__MODEL_PATH` | No | `artifacts/cost_sensitive/champion_model.txt` | Path to trained champion LightGBM booster. |
| `GRID_GUARD_LOG_LEVEL` | No | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

---

## 4. Frontend (Static Site) Configuration

### Build & Publish Configuration

- **Runtime**: Static Site
- **Root Directory**: `frontend`
- **Build Command**:
  ```bash
  npm ci && npm run build
  ```
- **Publish Directory**: `dist`
- **Routing Rules (SPA Rewrite)**:
  - **Type**: `Rewrite`
  - **Source**: `/*`
  - **Destination**: `/index.html`

### Environment Variables for Frontend

| Variable Name | Required | Example Value | Description |
| :--- | :---: | :--- | :--- |
| `VITE_API_BASE_URL` | Yes | `https://grid-guard-api.onrender.com` | Deployed backend URL. Embedded into client JS at build time. |

> [!IMPORTANT]
> Because Vite embeds `VITE_*` environment variables during `npm run build`, you must set `VITE_API_BASE_URL` before running the frontend build. If modified later, trigger a **Manual Deploy > Clear build cache & deploy**.

---

## 5. Automated Deployment via `render.yaml` Blueprint

The repository contains a root `render.yaml` Blueprint. To deploy both services simultaneously:

1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** > **Blueprint**.
3. Connect your GitHub repository: `Gauravsharma2711/grid-guard`.
4. Render will parse `render.yaml` and display both services (`grid-guard-api` and `grid-guard-frontend`).
5. Click **Apply**.
6. After initial creation:
   - Note the exact URL of `grid-guard-api` (e.g., `https://grid-guard-api-xxxx.onrender.com`).
   - Note the exact URL of `grid-guard-frontend` (e.g., `https://grid-guard-frontend-xxxx.onrender.com`).
   - Verify `CORS_ORIGINS` on the API matches your frontend URL.
   - Verify `VITE_API_BASE_URL` on the frontend matches your API URL.

---

## 6. Model Artifacts & Ephemeral Storage Considerations

1. **Model Checkpoint**: The LightGBM champion booster (`champion_model.txt`, 537 KB) is committed to the Git repository under `artifacts/cost_sensitive/champion_model.txt`. Render receives it upon cloning.
2. **Ephemeral Filesystem**: Render Web Services run on ephemeral filesystems. File modifications made at runtime do not persist across restarts or redeployments. Grid-Guard's inference engine operates fully in-memory and does not write state to disk, ensuring 100% compatibility with ephemeral instances.
3. **Memory Sizing**: The LightGBM model and Tree-SHAP explainer require ~350–450 MB RAM at runtime. The Render Free/Starter tier (512 MB RAM) or Standard tier (2 GB RAM) is sufficient.

---

## 7. Health Checks & Smoke Testing

### Liveness Probe (`/health`)
- **URL**: `https://<YOUR_API_DOMAIN>/health`
- **Expected Status**: `200 OK`
- **Payload**:
  ```json
  {
    "status": "ok",
    "service": "grid-guard-api",
    "api_version": "0.1.0"
  }
  ```

### Readiness Probe (`/ready`)
- **URL**: `https://<YOUR_API_DOMAIN>/ready`
- **Expected Status**: `200 OK` (or `503 Service Unavailable` if model failed to load)
- **Payload**:
  ```json
  {
    "status": "ready",
    "model_loaded": true,
    "explainer_loaded": true,
    "features_configured": true,
    "model_version": "phase6_cost_sensitive_v1",
    "feature_count": 60,
    "api_version": "0.1.0"
  }
  ```

### Post-Deployment Verification Checklist
1. Visit `https://<YOUR_FRONTEND_DOMAIN>/`.
2. Verify the top header shows **`API ONLINE`** (emerald green glowing indicator).
3. Check the **Operational Overview** screen:
   - Hero expected net value: `₹24,700`
   - Active policy: `Expected Net Value (ENV)`
4. Navigate to **Inspection Queue**:
   - Verify 50 candidate tickets load from `/api/v1/inspection/queue`.
   - Click a ticket to inspect telemetry in the slide-out drawer.
5. Navigate to **Meter Analysis**:
   - Select preset `SAMPLE_SUSPICIOUS_STEPDOWN` and click **Re-evaluate**.
   - Verify consumption time-series chart renders.
   - Verify Tree-SHAP feature contributions and detected electrical tampering signatures render.

---

## 8. Common Troubleshooting

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| **Frontend displays `API DISCONNECTED`** | 1. Backend still spinning up (cold start on free tier takes 30-50s).<br>2. `VITE_API_BASE_URL` was not set at build time.<br>3. CORS rejection. | 1. Wait for backend to wake up.<br>2. Set `VITE_API_BASE_URL` in frontend env vars and trigger a clear-cache rebuild.<br>3. Add frontend URL to `CORS_ORIGINS` in API settings. |
| **CORS policy error in browser console** | `CORS_ORIGINS` does not contain the frontend URL. | In Render Dashboard for `grid-guard-api`, update `CORS_ORIGINS` to include `https://your-frontend.onrender.com`. Redeploy will take ~10s. |
| **`GET /ready` returns 503** | Model artifact path invalid or missing file. | Confirm `artifacts/cost_sensitive/champion_model.txt` exists. Check API logs for initialization trace. |
| **Vite 404 on direct URL navigation** | Render Static Site missing SPA rewrite rule. | In Render Dashboard > `grid-guard-frontend` > **Redirects/Rewrites**, ensure rule `/* -> /index.html` (Rewrite) is active. |

---

## 9. Manual Render Dashboard Actions Summary

1. **Create Services**: Use **New + > Blueprint** and select `render.yaml`.
2. **Synchronize URLs**:
   - Copy the deployed API URL (e.g. `https://grid-guard-api.onrender.com`).
   - Paste into frontend's `VITE_API_BASE_URL`.
   - Copy the deployed frontend URL (e.g. `https://grid-guard-frontend.onrender.com`).
   - Ensure it is included in backend's `CORS_ORIGINS`.
3. **Rebuild Frontend**: Re-deploy frontend once `VITE_API_BASE_URL` is set so Vite bakes the URL into the static bundle.
