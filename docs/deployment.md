# Grid-Guard Deployment & Operational Guide

This document details the configuration, local execution, containerization, and production deployment procedures for the **Grid-Guard** financial-aware smart meter tampering detection platform.

---

## 1. System Overview & Service Architecture

Grid-Guard deploys as a decoupled microservices architecture:

```
                      +-----------------------------+
                      |   Client Web Browser        |
                      +--------------+--------------+
                                     |
                                     | Port 8501 (HTTP)
                                     v
                      +-----------------------------+
                      | Streamlit Dashboard         |
                      | (src/grid_guard/dashboard)  |
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
- **Python**: Version `3.11`
- **Package Manager**: `uv` (recommended) or standard `pip`

### 2.2 Installing Dependencies
```bash
# Clone the repository
git clone https://github.com/Gauravsharma2711/grid-guard.git
cd grid-guard

# Synchronize dependencies with uv
uv sync
```

### 2.3 Single-Command Launcher (API + Dashboard)
To run both the FastAPI backend and Streamlit dashboard concurrently in one terminal:
```bash
uv run python scripts/run_services.py
```
This boots FastAPI on `http://localhost:8000` (waiting 3s for lifespan model loading), then launches Streamlit on `http://localhost:8501`.

### 2.4 Independent Service Startup
If you prefer running services in separate terminal sessions:

**Terminal 1 — FastAPI Backend:**
```bash
uv run python scripts/run_api.py --port 8000 --host 0.0.0.0
# Or directly via Uvicorn:
uv run uvicorn grid_guard.api.main:app --host 0.0.0.0 --port 8000
```
Interactive Swagger documentation will be available at: `http://localhost:8000/docs`

**Terminal 2 — Streamlit Dashboard:**
```bash
uv run python scripts/run_dashboard.py --port 8501
# Or directly via Streamlit CLI:
uv run streamlit run src/grid_guard/dashboard/app.py --server.port 8501
```
Dashboard will be available at: `http://localhost:8501`

---

## 3. Container Deployment (Docker & Compose)

Grid-Guard provides production-grade container manifests for reproducible deployment.

### 3.1 Docker Compose Deployment
```bash
# Build and start all services
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
| `grid-guard-dashboard` | `Dockerfile.dashboard` | `python:3.11-slim` | `8501` | `GET /_stcore/health` |

> **Audit Note on Container Validation:**
> Dockerfiles and `docker-compose.yml` are statically validated. If the local Docker daemon is inactive during development, runtime execution in containers is verified upon launching the Docker Desktop engine.

---

## 4. Configuration & Environment Variables

Grid-Guard uses Pydantic Settings reading from `.env` files and environment variables. See `.env.example` for reference templates:

| Environment Variable | Default | Purpose |
| :--- | :--- | :--- |
| `GRID_GUARD_API__HOST` | `0.0.0.0` | Bind IP for FastAPI service |
| `GRID_GUARD_API__PORT` | `8000` | Bind port for FastAPI service |
| `GRID_GUARD_API__WORKERS` | `1` | Number of Uvicorn worker processes |
| `GRID_GUARD_API__RELOAD` | `false` | Enable code auto-reload |
| `GRID_GUARD_API_URL` | `http://localhost:8000` | Backend API URL queried by Dashboard |
| `GRID_GUARD_API_TIMEOUT` | `25.0` | HTTP request timeout in seconds |
| `GRID_GUARD_FINANCIAL__DISPATCH_COST`| `100.0` | Assumed fixed crew visit cost ($C_{\text{FP}}$) |
| `GRID_GUARD_FINANCIAL__DEFAULT_TARIFF`| `0.15` | Default electricity tariff ($/kWh) |
| `GRID_GUARD_DECISION__DECISION_RULE` | `env` | Default policy: `env`, `cost_threshold`, `fixed` |
| `GRID_GUARD_LOG_LEVEL` | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`) |

---

## 5. Health & Readiness Monitoring

Grid-Guard exposes standard Kubernetes/cloud liveness and readiness probe endpoints:

### Liveness Probe (`GET /health`)
- **Status 200 OK**: Process is alive and responding.
```json
{
  "status": "ok",
  "service": "grid-guard-api",
  "api_version": "1.0.0"
}
```

### Readiness Probe (`GET /ready`)
- **Status 200 OK**: LightGBM booster and Tree-SHAP explainer are pinned in memory and ready for inference.
- **Status 503 Service Unavailable**: Model artifacts are still loading or missing.
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

1. **Zero Secret Leakage**: No API keys, credentials, or private file paths are exposed in logs or API responses.
2. **Input Validation**: Daily smart-meter readings are strictly validated against non-finite values (NaN, Inf), negative consumption, duplicate timestamps, and minimum required history (30 days).
3. **Payload Bounds**: Batch requests are capped at 50 meters per synchronous call to ensure predictable memory usage and latency.
4. **Error Handling**: Graceful degradation prevents raw Python stack traces from escaping to client browsers.

---

## 7. Responsibilities Boundary

### Tasks Fully Prepared by Antigravity
- [x] Application source code, models, and feature pipelines.
- [x] Streamlit dashboard with responsive UI and publication-quality charting.
- [x] Production FastAPI backend with OpenAPI schema validation.
- [x] `Dockerfile.api`, `Dockerfile.dashboard`, and `docker-compose.yml`.
- [x] Local concurrency scripts (`scripts/run_services.py`).
- [x] 100% passing test suite across unit, integration, and end-to-end flows.

### Tasks User Must Perform (External Infrastructure)
- [ ] Cloud account provisioning (e.g. AWS, GCP, Azure, DigitalOcean, or Render).
- [ ] Domain registration and DNS routing (e.g. mapping `gridguard.utility.com`).
- [ ] TLS/SSL certificate issuance (e.g. Let's Encrypt / Cloudflare).
- [ ] Production secrets management (e.g. AWS Secrets Manager or Vault).
- [ ] Internal utility enterprise database integrations (if replacing CSV/AMI smart-meter feeds).
