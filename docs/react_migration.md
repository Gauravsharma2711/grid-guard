# Grid-Guard React Frontend Migration — Phase 1 Architecture & Foundation

**Status:** Phase 1 Complete (Approved Baseline)  
**Author:** Grid-Guard Frontend Migration Engineer  
**Date:** October 2026  
**Scope:** Phase 1 — Repository Audit, Architecture Baseline, and React + TypeScript Foundation  

---

## 1. Migration Objective

Grid-Guard is an electricity meter tampering and non-technical-loss (NTL) detection platform combining smart-meter AMI time-series analysis, temporal feature engineering, cost-sensitive machine learning, dynamic Expected Net Value (ENV) thresholding, and Tree-SHAP explainability.

The operational user interface was previously implemented in **Streamlit**. While effective for early prototypes, enterprise utility deployment requires:
- Highly responsive, asynchronous state management and decoupled rendering.
- Deterministic, testable design system compliance without Streamlit widget quirks.
- Dedicated operational workflows for revenue protection analysts and field dispatch planners.
- Zero-downtime migration preserving all existing backend models, algorithms, and legacy Streamlit capabilities until final switchover.

This migration follows a strict five-phase progression:
- **Phase 1 (Current):** Repository audit, design system mapping, API inventory, and React + TypeScript + Vite foundation.
- **Phase 2:** Design token implementation, theme provider, and core reusable UI components.
- **Phase 3:** Operational views (Fleet Overview, Ranked Inspection Queue, Single-Meter Workbench).
- **Phase 4:** Model insights, Tree-SHAP visualizers, and system introspection views.
- **Phase 5:** End-to-end regression validation, production bundling, Docker containerization, and Streamlit retirement.

---

## 2. Existing Architecture Audit

### 2.1 Pipeline Flow
The backend pipeline operates as follows:
```
AMI Smart Meter Data
  ↳ Ingestion & Validation
  ↳ 60-Feature Causal Temporal Pipeline
  ↳ Baseline Modeling & Class-Imbalance Handling
  ↳ Financially Weighted LightGBM Booster (Phase 6 Champion)
  ↳ Dynamic Expected Net Value (ENV) Optimization
  ↳ Inspection Prioritization & Field Ticket Generation
  ↳ Tree-SHAP Feature Attribution & Physical Tampering Narratives
  ↳ FastAPI REST Service (src/grid_guard/api)
  ↳ Operational User Interfaces
```

### 2.2 Entrypoint Inventory
| Component | Entrypoint Path | Runner Script | Default Port | Notes |
|---|---|---|---|---|
| **FastAPI Backend** | `src/grid_guard/api/main.py:app` | `scripts/run_api.py` | 8000 | ASGI server via Uvicorn. Loads LightGBM booster & SHAP explainer during startup lifespan. |
| **Streamlit UI (Legacy)** | `src/grid_guard/dashboard/app.py` | `scripts/run_dashboard.py` | 8501 | Operational multi-view dashboard. Remains active and intact throughout Phases 1–4. |
| **Combined Services** | — | `scripts/run_services.py` | 8000 & 8501 | Subprocess orchestrator launching backend then Streamlit dashboard. |
| **React Frontend (New)** | `frontend/src/main.tsx` | `npm run dev` (Vite) | 3000 | Independent React application calling FastAPI via CORS/REST. |

### 2.3 Backend Test & Quality Baseline
- **Python Unit Tests:** 133 tests (`tests/unit`) — 100% passing.
- **Python Integration Tests:** 29 tests (`tests/integration`) — 100% passing.
- **Total Backend Tests:** 162 tests passing (`uv run pytest -q`).
- **Python Code Quality:** 100% clean (`uv run ruff check .` passed).

---

## 3. Frontend Architecture & Foundation

### 3.1 Directory Structure
The React foundation is established in a dedicated, isolated top-level directory: `frontend/`:
```
grid-guard/
├── designsystem.md              # Authoritative design specification
├── frontend/
│   ├── public/
│   │   └── favicon.svg          # SVG brand favicon
│   ├── src/
│   │   ├── config/
│   │   │   ├── env.ts           # Environment resolution & URL normalization
│   │   │   └── env.test.ts      # Configuration unit tests
│   │   ├── services/
│   │   │   └── apiClient.ts     # Type-safe fetch client for FastAPI
│   │   ├── test/
│   │   │   └── setup.ts         # Vitest test setup (jest-dom)
│   │   ├── types/
│   │   │   └── api.ts           # TypeScript interfaces matching FastAPI schemas
│   │   ├── App.css              # App layout styles matching design tokens
│   │   ├── App.test.tsx         # Component unit & integration tests
│   │   ├── App.tsx              # Minimal bootstrap application
│   │   ├── index.css            # CSS custom properties (:root design tokens)
│   │   ├── main.tsx             # DOM mounting entrypoint
│   │   └── vite-env.d.ts        # Vite environment typings
│   ├── .env.example             # Safe environment variable template
│   ├── .gitignore               # Frontend ignore rules (node_modules, dist)
│   ├── eslint.config.js         # ESLint 9 flat configuration with TypeScript
│   ├── index.html               # HTML5 shell importing Space Grotesk, Inter, Plex Mono
│   ├── package.json             # Pinned frontend dependencies and scripts
│   ├── package-lock.json        # Deterministic dependency lockfile
│   ├── tsconfig.json            # Strict TypeScript compiler options
│   └── vite.config.ts           # Vite + React + Vitest configuration
├── src/grid_guard/              # Preserved Python backend and ML pipeline
├── tests/                       # Preserved Python test suite
└── README.md
```

### 3.2 Technology Stack & Tooling
| Tool | Version | Purpose |
|---|---|---|
| **React** | `18.3.1` | Core UI library |
| **React DOM** | `18.3.1` | DOM renderer |
| **TypeScript** | `5.6.3` | Static typing with strict compiler checks (`noExplicitAny`, `strict`, `noUnusedLocals`) |
| **Vite** | `5.4.11` | Build tool and fast HMR development server |
| **Vitest** | `2.1.5` | Fast unit & component test runner |
| **Testing Library** | `16.0.1` | User-centric React testing (`@testing-library/react`, `@testing-library/jest-dom`) |
| **ESLint** | `9.14.0` | Code quality and linting with TypeScript-ESLint |
| **Package Manager**| `npm 11.13.0` | Node.js v22.20.0 native package manager with `package-lock.json` |

---

## 4. Design System Audit & Token Mapping

The visual language adheres strictly to the approved specification in `/designsystem.md` ("Calm Proof Flow"). No competing design systems, generic SaaS themes, gradients, or glassmorphism are permitted.

### 4.1 Palette Token Mapping
Implemented in `frontend/src/index.css`:
| Token Name | Hex Value | Purpose in Grid-Guard | Prohibited Uses |
|---|---|---|---|
| `--gg-canvas` | `#FBFBF7` | Warm off-white page background | Dark code surfaces |
| `--gg-surface` | `#FFFFFF` | Elevated cards, tables, modal/drawer surfaces | Default full-page background |
| `--gg-ink` | `#121512` | Headings, primary actions, critical text | Subdued metadata |
| `--gg-ink-soft` | `#344038` | Body text, emphasis labels, table values | Disabled states |
| `--gg-muted` | `#737B74` | Supporting copy, timestamps, inactive UI | Section titles or critical actions |
| `--gg-rule` | `#E1E5DD` | 1px hairline dividers, quiet control borders | Heavy boxed outlines |
| `--gg-signal` | `#D9FF4A` | Chartreuse accent: selected chips, confirmed actions | General decorative fills, every button |
| `--gg-signal-ink` | `#3F4B08` | High-contrast dark text/icons on chartreuse | Normal body copy |
| `--gg-evidence` | `#7D6DB2` | Violet accent: Tree-SHAP attribution & model evidence | Generic action color, positive financial status |
| `--gg-safe` | `#3F8B61` | Healthy API status, verified safe states | Generic marketing badges |
| `--gg-warning` | `#B88418` | Incomplete history, verification required, offline | Decorative highlights |
| `--gg-danger` | `#C45646` | High severity, failed connection, validation errors | Default hover color |
| `--gg-code` | `#151A16` | Technical data, JSON excerpts, command snippets | Ordinary cards or page canvas |
| `--gg-code-ink` | `#E7EEE7` | Monospace code text | Light surfaces |

### 4.2 Typography Hierarchy
Imported via Google Fonts in `frontend/index.html`:
- **Space Grotesk** (`--gg-font-display`): Page display titles (48–64px), section titles (28–36px), meter IDs (16–20px).
- **Inter** (`--gg-font-body`): Body prose (14–16px), interface labels and buttons (12–13px), table cells (12–14px).
- **IBM Plex Mono** (`--gg-font-mono`): Technical metadata, model checkpoint versions, timestamps, feature keys (9–12px), code surfaces (12–13px).

### 4.3 Spacing & Geometry Scale
- Spacing: `--gg-space-1` (4px) to `--gg-space-20` (80px).
- Radii: `--gg-radius-xs` (4px), `--gg-radius-sm` (6px for buttons/inputs), `--gg-radius-lg` (10px for containers).
- Controls: Minimum 44px tap target height (`--gg-control-height`).
- Header: Fixed 58px height (`--gg-header-height`).
- Max Layout Widths: 640px reading/decision canvas (`--gg-content-width`), 1440px wide operational container (`--gg-page-max-width`), 480px maximum drawer width (`--gg-drawer-width`).

---

## 5. Backend API Inventory & Contract Documentation

The FastAPI backend exposes 8 REST endpoints across 4 functional domains.

### 5.1 System Health & Readiness Probes
1. **`GET /health`**
   - **Purpose:** Process liveness probe.
   - **Request:** None.
   - **Response (`HealthResponse`):** `{"status": "ok", "service": "grid-guard-api", "api_version": "0.1.0"}`
   - **Errors:** Standard HTTP 500 if process is corrupted.
   - **Artifacts Required:** None (operates even if ML models fail to load).

2. **`GET /ready`**
   - **Purpose:** Inference readiness probe. Confirms LightGBM champion booster and Tree-SHAP explainer are resident in RAM.
   - **Request:** None.
   - **Response (`ReadyResponse`):** `{"status": "ready", "model_loaded": true, "explainer_loaded": true, "features_configured": true, "model_version": "phase6_cost_sensitive_v1", "feature_count": 60, "api_version": "0.1.0"}`
   - **Errors:** HTTP 503 `{"status": "unready", ...}` if booster or explainer is uninitialized.
   - **Artifacts Required:** `artifacts/cost_sensitive/champion_model.txt`.

### 5.2 Metadata & Introspection
3. **`GET /api/v1/metadata/model`**
   - **Purpose:** Introspect loaded model booster characteristics, feature names, base expected values, and objective type.
   - **Request:** None.
   - **Response (`ModelMetadataResponse`):** Contains `model_version`, `feature_count: 60`, `feature_names`, `base_expected_value: -2.3713`, `objective: "custom_cost_sensitive"`.
   - **Errors:** HTTP 503 if unready.
   - **Artifacts Required:** Loaded `InferenceService`.

4. **`GET /api/v1/metadata/config`**
   - **Purpose:** Public operational configuration limits, supported decision policies, and financial defaults.
   - **Request:** None.
   - **Response (`dict`):** Limits (`min_readings: 14`, `max_readings: 730`, `max_batch: 50`), financial defaults (`tariff: 6.0`, `dispatch_cost: 500.0`, `currency: INR`), `supported_decision_rules: ["env", "cost_threshold", "fixed_threshold"]`.
   - **Errors:** None.
   - **Artifacts Required:** None.

### 5.3 Inference & Prediction
5. **`POST /api/v1/predict`**
   - **Purpose:** Evaluates single meter consumption time-series, calculates 60 causal features, outputs tamper probability, financial exposure, Expected Net Value (ENV), and Tree-SHAP local attributions.
   - **Request (`SingleMeterPredictionRequest`):** `meter_id`, `readings` (list of `{"date": "YYYY-MM-DD", "consumption_kwh": float}`), `tariff?`, `dispatch_cost?`, `include_explanation?`.
   - **Response (`SingleMeterPredictionResponse`):** `meter_id`, `evaluation_date`, `tamper_probability`, `is_tampering_risk`, `dispatch_recommended`, `financial_summary`, `signatures`, `shap_attributions`.
   - **Errors:** HTTP 400 (insufficient readings <14, duplicates), HTTP 422 (schema violation), HTTP 503 (model unready).
   - **Artifacts Required:** Champion model booster.

6. **`POST /api/v1/predict/batch`**
   - **Purpose:** Synchronously processes a bounded batch of smart meters (up to 50 meters). Supports partial failures with item-level error structures.
   - **Request (`BatchPredictionRequest`):** List of up to 50 meter payloads.
   - **Response (`BatchPredictionResponse`):** `total_requested`, `successful_count`, `failed_count`, `results: [...]`, `errors: [...]`.
   - **Errors:** HTTP 400 (batch exceeds 50), HTTP 422 (validation error).

### 5.4 Inspection & Field Work Orders
7. **`POST /api/v1/inspection/ticket`**
   - **Purpose:** Generates a formal, actionable field inspection ticket with deterministic ticket ID, risk score, financial calculations, physical tampering signatures, and human-readable audit narrative.
   - **Request (`SingleMeterPredictionRequest`):** Target meter time series.
   - **Response (`InspectionTicketResponse`):** `ticket_id`, `meter_id`, `created_at`, `tamper_probability`, `dispatch_recommended`, `financial_summary`, `detected_signatures`, `narrative`, `verification_caveat`.
   - **Errors:** HTTP 400 (insufficient history), HTTP 503 (unready).

8. **`POST /api/v1/inspection/queue`**
   - **Purpose:** Retrieves candidate inspection tickets ranked strictly by Expected Net Value (ENV) descending. Supports dynamic filtering by minimum ENV, probability cutoff, and crew capacity.
   - **Request (`InspectionQueueRequest`):** `min_env?`, `min_probability?`, `limit?`, `decision_rule?`.
   - **Response (`InspectionQueueResponse`):** `total_candidates`, `returned_count`, `ranking_criterion: "expected_net_value_descending"`, `items: [...]`.
   - **Errors:** HTTP 404 (if precomputed candidate evaluation artifacts are missing), HTTP 503 (unready).

---

## 6. Environment Configuration & CORS

### 6.1 Frontend Environment Configuration
- Environment template: `frontend/.env.example`
- Environment resolution: `frontend/src/config/env.ts`
- Variables:
  - `VITE_API_BASE_URL`: Base URL for the FastAPI backend (defaults to `http://localhost:8000`).
- Safety rules:
  - Trailing slashes are automatically sanitized.
  - No secrets or local file paths are exposed.
  - The application renders gracefully even when the backend is unreachable.

### 6.2 CORS Configuration
- In `src/grid_guard/config/api.py`, the default setting is `cors_origins: ["*"]` with `cors_allow_credentials: True`.
- Local React development server runs on `http://localhost:3000` (or `http://localhost:4173` for Vite preview).
- All browser requests from `localhost:3000` are permitted by the backend without requiring backend changes.

---

## 7. Developer Experience & Operational Commands

### 7.1 Frontend Development
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (npm)
npm install

# Start Vite development server (http://localhost:3000)
npm run dev

# Run strict TypeScript compiler check (noEmit)
npm run typecheck

# Run ESLint check
npm run lint

# Run Vitest unit & component test suite
npm run test

# Run Vitest in interactive watch mode
npm run test:watch

# Build production bundle to frontend/dist
npm run build

# Preview production build locally
npm run preview
```

### 7.2 Backend & Legacy Streamlit Operations (Preserved)
```bash
# Start FastAPI backend (http://localhost:8000)
uv run python scripts/run_api.py
# Or directly via uvicorn:
uv run uvicorn grid_guard.api.main:app --port 8000 --reload

# Start legacy Streamlit dashboard (http://localhost:8501)
uv run python scripts/run_dashboard.py
# Or directly via streamlit:
uv run streamlit run src/grid_guard/dashboard/app.py --server.port 8501

# Run both backend and Streamlit concurrently
uv run python scripts/run_services.py

# Run Python automated test suite (162 tests)
uv run pytest -q

# Run Python code quality linter (Ruff)
uv run ruff check .
```

---

## 8. Known Limitations & Next-Phase Boundary

### Current Phase 1 Deliverable:
- Minimal, clean application bootstrap demonstrating verified React + TypeScript mounting, design token integration, strict type-checking, honest connection probing, and automated frontend testing.
- Preserves all 162 backend tests, Streamlit entrypoint, and ML model weights without modification.

### Explicit Phase Boundaries:
- **Not in Phase 1:** Overview dashboard KPI cards, inspection queue table with sorting/filtering, meter analysis time-series charts, SHAP attribution waterfall visualizers, model performance comparison tables, and field ticket export workflows.
- These components will be built in **Phase 2** (Component Library & Theme System), **Phase 3** (Inspection Queue & Meter Workbench), and **Phase 4** (Explainability & Model Insights).
