# Grid-Guard Deployment & Operational Guide

This document details the configuration, local execution, containerization, and production deployment procedures for the **Grid-Guard** financial-aware smart meter tampering detection platform following the completed React migration.

---

## 1. System Overview & Service Architecture

Grid-Guard deploys as a decoupled microservices architecture:

```
                      +-----------------------------+
                      |   Client Web Browser        |
                      +--------------+--------------+
                                     |
                                     | Port 5173 / 3000 (HTTP)
                                     v
                      +-----------------------------+
                      | React Web Frontend          |
                      | (frontend/ - Vite + Nginx)  |
                      +--------------+--------------+
                                     |
                                     | Port 8000 (REST JSON)
                                     v
                      +-----------------------------+
                      | FastAPI Inference Backend   |
                      | (src/grid_guard/api)        |
                      +--------------+--------------+
                                     |
        +-----------------------------+-----------------------------+
        |                             |                             |
        v                             v                             v
 +--------------+              +--------------+              +--------------+
 | 60-Feature   |              | LightGBM     |              | Tree-SHAP    |
 | Pipeline     |              | Booster      |              | Explainer    |
 +--------------+              +--------------+              +--------------+
```

---

## 2. Local Execution (Development & Demo)

### 2.1 Prerequisites
- **Python**: Version `3.11` (managed via `uv` or standard virtual environment)
- **Node.js**: Version `20.x` or higher (with `npm`)

### 2.2 Installing Dependencies
```bash
# 1. Clone repository
git clone https://github.com/Gauravsharma2711/grid-guard.git
cd grid-guard

# 2. Synchronize Python backend dependencies
uv sync

# 3. Install React frontend dependencies
cd frontend
npm ci
cd ..
```

### 2.3 Single-Command Launcher (API + React Frontend)
To run both the FastAPI backend and React frontend concurrently in one terminal:
```bash
uv run python scripts/run_services.py
```
This boots FastAPI on `http://localhost:8000` (waiting 3s for lifespan model loading), then launches the React Vite development server on `http://localhost:5173`.

### 2.4 Independent Service Startup

**Terminal 1 — FastAPI Backend:**
```bash
uv run uvicorn grid_guard.api.main:app --host 0.0.0.0 --port 8000
```
Interactive OpenAPI documentation will be available at: `http://localhost:8000/docs`

**Terminal 2 — React Frontend:**
```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```
React application will be available at: `http://localhost:5173`

---

## 3. Container Deployment (Docker & Compose)

Grid-Guard provides production-grade container manifests for reproducible deployment.

### 3.1 Docker Compose Deployment
```bash
# Build and start all services in detached mode
docker compose up --build -d

# View service logs
docker compose logs -f

# Check health status
docker compose ps

# Shut down services
docker compose down
```

### 3.2 Container Architecture
| Container | Dockerfile | Base Image | Port | Health Check Endpoint |
| :--- | :--- | :--- | :--- | :--- |
| `grid-guard-api` | `Dockerfile.api` | `python:3.11-slim` | `8000` | `GET /health` |
| `grid-guard-frontend` | `frontend/Dockerfile` | `nginx:alpine` (multi-stage build from `node:20-alpine`) | `3000` | `GET /` |

---

## 4. Configuration & Environment Variables

### Backend Configuration (`.env` or system environment):
| Environment Variable | Default | Purpose |
| :--- | :--- | :--- |
| `GRID_GUARD_API__HOST` | `0.0.0.0` | Bind IP for FastAPI service |
| `GRID_GUARD_API__PORT` | `8000` | Bind port for FastAPI service |
| `GRID_GUARD_API__WORKERS` | `1` | Number of Uvicorn worker processes |
| `GRID_GUARD_LOG_LEVEL` | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`) |
| `GRID_GUARD_FINANCIAL__DISPATCH_COST`| `100.0` | Assumed fixed crew visit cost ($C_{\text{FP}}$) |
| `GRID_GUARD_FINANCIAL__DEFAULT_TARIFF`| `0.15` | Default electricity tariff ($/kWh) |
| `GRID_GUARD_DECISION__DECISION_RULE` | `env` | Default policy: `env`, `cost_threshold`, `fixed` |

### Frontend Configuration (`frontend/.env`):
| Environment Variable | Default | Purpose |
| :--- | :--- | :--- |
| `VITE_API_BASE_URL` | `http://localhost:8000` | FastAPI backend service URL |

---

## 5. Health & Readiness Monitoring

Grid-Guard exposes standard Kubernetes/cloud liveness and readiness probe endpoints:

### Liveness Probe (`GET /health`)
```json
{
  "status": "ok",
  "service": "grid-guard-api",
  "api_version": "1.0.0"
}
```

### Readiness Probe (`GET /ready`)
```json
{
  "status": "ready",
  "model_loaded": true,
  "explainer_loaded": true,
  "features_configured": true,
  "model_version": "phase6_cost_sensitive_dispatch_norm",
  "feature_count": 60,
  "api_version": "1.0.0"
}
```

---

## 6. Production Security & Hardening

1. **Zero Secret Exposure**: No credentials, tokens, or private paths exist in source or client bundles.
2. **Strict Telemetry Validation**: Pydantic models reject negative consumption, non-finite values (NaN, Inf), duplicate timestamps, and short histories (< 30 readings).
3. **Bounded Payloads**: Synchronous batch evaluation is capped at 50 meters per request.
4. **Error Sanitization**: Server-side error handling masks internal stack traces, returning structured JSON error details.
5. **CSV Injection Defense**: Ticket and queue exports RFC 4180 escape all formulas, quotes, and commas.

---

## 7. Responsibilities Boundary

### Automated Tasks Complete
- [x] High-performance React frontend conforming to `/DesignSystem.md`.
- [x] Streamlit legacy UI retired safely without regression.
- [x] Production FastAPI backend with lifespan model pinning.
- [x] `Dockerfile.api`, `frontend/Dockerfile`, and `docker-compose.yml`.
- [x] Local concurrency launcher (`scripts/run_services.py`).
- [x] 100% passing test suites (162 Python pytest + 104 React Vitest).

### External Operations Required for Production Hosting
- [ ] Cloud infrastructure provisioning (AWS ECS, GCP Cloud Run, Azure App Services, or DigitalOcean).
- [ ] Domain registration & DNS records (e.g., `gridguard.utility.internal`).
- [ ] SSL/TLS certificate termination.
- [ ] Centralized monitoring & logging (e.g., Prometheus / Datadog).
