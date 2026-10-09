# ⚡ Grid-Guard

**Financial-Aware Smart Meter Tampering & Non-Technical Loss (NTL) Detection Platform**

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5-3178C6.svg)](https://www.typescriptlang.org/)
[![LightGBM](https://img.shields.io/badge/LightGBM-4.6.0-brightgreen.svg)](https://lightgbm.readthedocs.io/)
[![Tree--SHAP](https://img.shields.io/badge/Explainability-Tree--SHAP-yellow.svg)](https://shap.readthedocs.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Tests: 162 Python | 104 React](https://img.shields.io/badge/tests-266%20passed-success.svg)](tests/)

---

## 1. About Grid-Guard

Electric power utilities lose tens of billions of dollars each year to **Non-Technical Losses (NTL)**—predominantly physical meter tampering, line bypassing, and unauthorized consumption. 

Conventional machine-learning models evaluate smart meters using purely statistical metrics such as ROC-AUC, Precision, or F1-score. In real-world utility operations, however, errors have deeply **asymmetric financial consequences**:
- **False Positives (Wasted Dispatch)**: Incur an immediate fixed operational cost ($C_{\text{FP}} \approx \$100.00$) to dispatch a two-person physical field inspection crew to an honest customer.
- **False Negatives (Unrecovered Leakage)**: Permit ongoing unmetered electricity theft ($C_{\text{FN}} = \text{Deficit} \times \text{Tariff} \times \text{Horizon}$), which can exceed $\$150,000$ on large commercial and industrial accounts.

A naive model that flags a rural lifeline customer with 95% statistical confidence may trigger **\$100 of utility crew expenditure to recover \$10 of energy**.

**Grid-Guard** bridges the gap between predictive machine learning and utility economics: **anomalies are dispatched if and only if the expected recovered revenue exceeds the crew dispatch cost.**

$$\text{ENV}_i = p_i \times R_i - C_{\text{dispatch}} > 0$$

Where:
- $p_i$ is the calibrated probability of tampering for meter $i$.
- $R_i$ is the estimated recoverable revenue over the recovery horizon ($R_i = \text{Leakage (kWh)} \times \text{Tariff} \times \text{Horizon}$).
- $C_{\text{dispatch}}$ is the fixed marginal cost of dispatching a physical inspection crew.
- $\text{ENV}_i$ is the **Expected Net Value** of the inspection.

---

## 2. Core Pillars & Capabilities

1. **60-Feature Causal Temporal Pipeline**: Robust feature extraction engine that derives rolling consumption baseline ratios (14d/60d, 30d/90d), weekday/weekend volatility, zero-consumption streaks, and near-zero flatline variances without forward lookahead bias.
2. **Financially Weighted Learning (LightGBM Champion)**: A cost-sensitive gradient boosted tree booster trained with sample weights proportional to estimated revenue leakage, reducing realized fleet operational loss by **24.5%**.
3. **Dynamic Expected Net Value ($\text{ENV}$) Decisioning**: Fleet-wide work-order prioritization that sorts candidate meters in strictly descending order of net dollar yield, ensuring maximum capital efficiency for utility dispatch operations.
4. **Tree-SHAP Explainability & Physical Signatures**: Exact Shapley value attributions decomposed into positive risk factors, negative moderating evidence, detected physical tampering signatures (sustained step-down, flatline invariance), and non-accusatory field work orders.
5. **Calm Proof Flow Operational Interface**: Enterprise React 18 + TypeScript web application built under the strict `/DesignSystem.md` specification—featuring high-contrast typography, live API telemetry, tactile elevation, and zero generic SaaS aesthetics.

---

## 3. End-to-End System Architecture

```
                          AMI Smart-Meter Daily Readings (kWh)
                                            │
                                            ▼
                    ┌──────────────────────────────────────────────┐
                    │      Polars Ingestion & Validation Engine    │
                    │   • Monotonic checks  • Imputation checks    │
                    │   • Ingestion constraints (14–730 days)      │
                    └──────────────────────┬───────────────────────┘
                                           │
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │      60-Feature Causal Temporal Pipeline     │
                    │   • Trailing 14d/30d/60d/90d baselines       │
                    │   • Volatility, skewness, zero streaks       │
                    │   • Weekend vs. weekday consumption regimes  │
                    └──────────────────────┬───────────────────────┘
                                           │
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │     Cost-Sensitive LightGBM Booster (Phase 6)│
                    │   • Financially weighted binary log-loss     │
                    │   • Calibrated tamper probability (p_i)      │
                    └──────────────────────┬───────────────────────┘
                                           │
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │     Financial Decision Engine (Phase 7)      │
                    │   • Dynamic breakeven threshold tau_cost     │
                    │   • Expected gross recovery: p_i * R_i       │
                    │   • Expected Net Value: ENV_i = p*R - C_disp │
                    └──────────────────────┬───────────────────────┘
                                           │
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │    Tree-SHAP Explainability Engine (Phase 8) │
                    │   • Exact local Shapley feature attributions │
                    │   • Physical signatures & counter-evidence   │
                    │   • Non-accusatory work order synthesis      │
                    └──────────────────────┬───────────────────────┘
                                           │
                 ┌─────────────────────────┴─────────────────────────┐
                 ▼                                                   ▼
┌─────────────────────────────────┐                 ┌─────────────────────────────────┐
│     FastAPI Backend (Phase 9)   │                 │     React 18 Frontend (Phase 5) │
│  • Asynchronous Lifespan Model  │                 │  • Calm Proof Flow Design       │
│  • /health & /ready probes      │◄──REST API (JSON)──┤  • Prioritized Queue & Filter   │
│  • /api/v1/predict (Single/Batch│                 │  • Diagnostic Workbench & SHAP  │
│  • /api/v1/inspection/ticket    │                 │  • Model Insights & Comparison  │
│  • /api/v1/inspection/queue     │                 │  • Zero generic UI libraries    │
└─────────────────────────────────┘                 └─────────────────────────────────┘
```

### Architectural Layer Responsibilities

| Layer | Module / Location | Primary Responsibility |
| :--- | :--- | :--- |
| **Ingestion & Data Quality** | `src/grid_guard/data/` | Validates daily meter telemetry, enforces 14-day minimum window, verifies non-negativity, and formats Polars/NumPy arrays. |
| **Feature Engineering** | `src/grid_guard/features/` | Calculates 60 temporal features capturing historical baseline divergence, variance collapses, and consumption drops without data leakage. |
| **Inference Engine** | `src/grid_guard/models/` | Houses the LightGBM champion booster (`phase6_cost_sensitive_v1`) trained with revenue-weighted sample loss. |
| **Financial Engine** | `src/grid_guard/decision/` | Evaluates individual customer tariffs ($\$0.15$/kWh default), dispatch costs ($\$100.00$), dynamic thresholds ($\tau_{\text{cost}}$), and net dollar values ($\text{ENV}$). |
| **Explainability Engine** | `src/grid_guard/explainability/` | Computes Tree-SHAP attributions, detects physical electrical tampering signatures, balances counter-evidence, and formats forensic tickets. |
| **REST API Service** | `src/grid_guard/api/` | FastAPI service with lifespan model preloading, OpenAPI documentation, and sub-10ms response times. |
| **User Interface** | `frontend/` | React 18 + TypeScript + Vite SPA conforming strictly to `/DesignSystem.md` ("Calm Proof Flow"). |

---

## 4. Operational User Workflows

Grid-Guard supports three primary role-based user workflows designed for day-to-day utility revenue protection operations:

```
[ Revenue Protection Dispatcher ]          [ Field Auditor / Analyst ]           [ Executive / Lead Data Scientist ]
               │                                        │                                           │
   1. Inspect Fleet Overview                1. Select Meter from Queue                   1. Review Model Governance
   2. Filter by Minimum ENV ($)             2. Execute 1-Click Evaluation                2. Compare Decision Policies
   3. Review Priority Work Orders           3. Analyze 180-Day Telemetry                 3. Audit Financial Trade-offs
   4. Export Dispatch Queue (CSV)           4. Inspect Tree-SHAP Waterfall               4. Inspect Checkpoint Provenance
               │                            5. Audit Electrical Signatures                          │
               ▼                            6. Export Inspection Ticket                             ▼
   [ Dispatched Field Crews ]                           │                        [ Operational Fleet Optimization ]
                                                        ▼
                                           [ Forensic Work Order Ticket ]
```

---

### Workflow 1: Fleet-Wide Risk Monitoring & Prioritized Work Order Dispatch
**Target Role**: *Revenue Protection Manager* / *Field Crew Dispatch Supervisor*

1. **Monitor Fleet Overview**: Review real-time aggregate metrics across the fleet (42,372 meters): Total Modeled Tamper Risk, Projected Fleet Leakage, Total Modeled Net Recovery ($\text{ENV}$), and Dispatched Candidate Count.
2. **Filter Candidate Meters**:
   - Set **Minimum Net Recovery ($\text{ENV}$)** filter (e.g., $\text{ENV} \ge \$500.00$) to guarantee inspection profitability.
   - Set **Minimum Tamper Probability** filter (e.g., $p \ge 0.50$).
   - Filter by **Shift Capacity** (e.g., 20, 50, or 100 meters per day) matching available field crew headcount.
   - Search by exact **Meter ID** or **Feeder ID**.
3. **Quick-Inspect Candidates**: Click any row in the queue table to open the **Slide-Out Inspection Drawer**, previewing economic stats, detected signatures, and narrative summaries without leaving the table.
4. **Dispatch Work Orders**: Click **"Export Queue (CSV)"** to generate a structured work-order manifest compatible with utility ERP systems, field tablets, and GIS routing tools.

---

### Workflow 2: Deep-Dive Forensic Meter Investigation & Tree-SHAP Explainability
**Target Role**: *Revenue Protection Analyst* / *Technical Field Auditor*

1. **Select Meter**: Choose a candidate directly from the Prioritized Queue or pick one of the 5 pre-configured synthetic demonstration archetypes in the **Meter Analysis Workbench**.
2. **Execute Diagnostic Evaluation**: Click **"Re-evaluate"** to run the 60-feature causal pipeline, model scoring, threshold evaluation, and Tree-SHAP attribution in real time.
3. **Analyze Consumption Telemetry**:
   - Inspect the interactive 180-day consumption chart.
   - Compare daily consumption (blue curve) against trailing 14-day rolling baselines (green dashed line).
   - Review highlighted pink windows identifying the exact historical changepoint where consumption collapsed.
4. **Deconstruct Tree-SHAP Attribution**:
   - Review the **Local Tree-SHAP Attribution Panel** decomposing risk into ranked positive contributors (e.g., `ratio_14d_60d`, `rolling_mean_14d`, `zero_consumption_streak`).
   - Examine the **Moderating Counter-Evidence** panel identifying factors that reduce risk (e.g., consistent long-term baseline, seasonal stability).
5. **Verify Electrical Tampering Signatures**:
   - Inspect physical tampering flags: *Sustained Step-Down Anomaly*, *Flatline Invariance*, or *High-Volume Deficit*.
6. **Generate & Export Inspection Ticket**:
   - Click **"View Inspection Ticket →"** to open the full forensic work-order document.
   - Review crew safety disclaimers, economic summary, and technical metadata.
   - Click **"Export Ticket (JSON)"** to persist the cryptographically traceable audit record.

---

### Workflow 3: Model Governance & Policy Benchmarking
**Target Role**: *Lead Data Scientist* / *Chief Risk Officer* / *Utility Economist*

1. **Audit Model Checkpoint**: Inspect active booster provenance (`phase6_cost_sensitive_v1`), training objective (`financially_weighted_logistic`), feature dimensions (60), base log-odds (`-2.3713`), and live HTTP health probes.
2. **Compare Operational Policies**: Evaluate the three decision policies across 42,372 candidate meters:
   - *Fixed Threshold ($p \ge 0.50$)*: Conventional unweighted ML rule.
   - *Bayes Cost Threshold*: Theoretical cost-ratio cutoff ($\tau = \frac{C_{\text{FP}}}{C_{\text{FP}} + C_{\text{FN}}}$).
   - *Dynamic Expected Net Value ($\text{ENV}$)*: Grid-Guard's dollar-weighted rule.
3. **Validate Empirical Superiority**:
   - Confirm that Dynamic $\text{ENV}$ generates **+$52,100.00** higher net recovery than fixed cutoff while achieving the lowest realized operational loss (**\$64.8k** vs. **\$82.7k**).

---

## 5. Technology Stack

| Domain | Technology | Purpose & Details |
| :--- | :--- | :--- |
| **Data Processing** | Python 3.11, Polars, NumPy, Pandas | High-performance columnar ingestion, feature computation, and array manipulation |
| **Machine Learning** | LightGBM 4.6.0, Scikit-Learn | Cost-sensitive gradient boosted decision trees with custom sample weighting |
| **Explainability** | SHAP 0.44+ (`TreeExplainer`) | Exact local Shapley values, feature additivity, and narrative attribution |
| **Backend Framework** | FastAPI 1.0+, Uvicorn, Pydantic V2 | Asynchronous REST API, lifespan preloading, OpenAPI 3.1 schema specification |
| **Frontend Framework** | React 18, TypeScript 5.5, Vite 5.4 | Enterprise Single-Page Application adhering to `/DesignSystem.md` ("Calm Proof Flow") |
| **Testing & Quality** | Vitest, React Testing Library, Pytest, Ruff | Automated test suites (266 total tests), strict TypeScript compilation, ESLint |
| **Containers & Deploy**| Docker, Docker Compose, Nginx | Multi-stage container builds, production static serving, healthcheck probes |

---

## 6. Project Directory Structure

```
grid-guard/
├── artifacts/                      # Verified reproducible artifacts & model weights
│   ├── api/                        # OpenAPI schemas and sample payloads
│   ├── cost_sensitive/             # Champion LightGBM booster & evaluation records
│   ├── decision/                   # Prioritized queue outputs & policy benchmark data
│   └── explainability/             # Tree-SHAP metadata and sample inspection tickets
├── configs/                        # YAML configuration files (default.yaml)
├── docs/                           # Technical documentation & guides
│   ├── architecture.md             # In-depth architectural specification
│   ├── deployment.md               # Production deployment guide
│   ├── demo_guide.md               # Step-by-step evaluator walkthrough
│   └── react_migration.md          # 5-phase React migration audit
├── frontend/                       # React 18 + TypeScript + Vite Web Application
│   ├── src/
│   │   ├── components/             # Reusable UI components (Calm Proof Flow)
│   │   │   ├── explainability/     # SHAP waterfall, signatures, decision context
│   │   │   ├── layout/             # AppHeader, AppShell, Layout primitives
│   │   │   ├── tickets/            # Comprehensive InspectionTicketView
│   │   │   └── ui/                 # Button, Input, Table, Chart, Status, Surface
│   │   ├── screens/                # Operational screens
│   │   │   ├── OverviewScreen/     # Fleet health overview & executive KPIs
│   │   │   ├── InspectionQueueScreen/ # Prioritized candidate work-order queue
│   │   │   ├── MeterAnalysisScreen/   # Diagnostic workbench & time series
│   │   │   └── ModelInsightsScreen/   # Model governance & policy comparison
│   │   ├── services/               # Typed apiClient with backend fallback resilience
│   │   └── styles/                 # Authoritative design tokens (tokens.css)
│   ├── Dockerfile                  # Multi-stage production Nginx container
│   ├── package.json                # Dependencies, Vitest, TypeScript, ESLint
│   └── vite.config.ts              # Vite bundler configuration & test runner
├── scripts/                        # Automation & execution runner scripts
│   ├── run_api.py                  # Standalone FastAPI launcher
│   └── run_services.py             # Concurrent API + React launcher
├── src/grid_guard/                 # Core Python application package
│   ├── api/                        # FastAPI routes, schemas, and lifecycle service
│   ├── config/                     # Pydantic Settings & environment variables
│   ├── data/                       # Ingestion, validation, and Polars cleaning
│   ├── decision/                   # Dynamic thresholds & ticket prioritization
│   ├── evaluation/                 # Cost matrices, leakage estimators, metrics
│   ├── explainability/             # Tree-SHAP, feature mapping, physical signatures
│   ├── features/                   # 60 temporal feature engineering pipeline
│   └── models/                     # Baseline, SMOTE, and cost-sensitive boosters
├── tests/                          # 162 automated Python tests (Unit, Integration, E2E)
├── Dockerfile.api                  # Container manifest for FastAPI backend
├── docker-compose.yml              # Multi-container orchestration (API + Frontend)
└── pyproject.toml                  # UV / Python dependency specification
```

---

## 7. Installation, Build & Execution Guide

### 7.1 Prerequisites & System Requirements
- **Operating System**: Windows 10/11, Linux (Ubuntu 20.04+), or macOS (Intel / Apple Silicon)
- **Python**: Version `3.11` (or `3.12`)
- **Node.js**: Version `18.x` or `20.x` LTS (with `npm 9+`)
- **Package Manager**: [`uv`](https://docs.astral.sh/uv/) (recommended for 10x faster Python resolution) or `pip`
- **Git**: Installed and available on system PATH
- **Docker & Docker Compose** *(Optional, for containerized execution)*

---

### 7.2 Installation

#### 1. Clone Repository
```bash
git clone https://github.com/Gauravsharma2711/grid-guard.git
cd grid-guard
```

#### 2. Backend Environment Setup
**Option A: Using `uv` (Recommended)**
```bash
# Install uv (if not already installed)
# Windows: powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# Linux/macOS: curl -LsSf https://astral.sh/uv/install.sh | sh

# Synchronize all Python dependencies into an isolated virtual environment
uv sync
```

**Option B: Using standard `pip` and `venv`**
```bash
python -m venv .venv

# Activate virtual environment
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate

pip install --upgrade pip
pip install -e .
```

#### 3. Frontend Dependencies Setup
```bash
cd frontend
npm install
cd ..
```

---

### 7.3 Running Locally (Development Mode)

#### Method 1: Single-Command Integrated Launcher (Recommended)
Launch both the FastAPI backend and React frontend concurrently in a single terminal session:

```bash
uv run python scripts/run_services.py
```

This command automatically:
1. Boots the FastAPI backend on `http://localhost:8000`.
2. Preloads the LightGBM booster into memory.
3. Launches the React Vite development server on `http://localhost:5173`.
4. Terminates both processes cleanly when `Ctrl+C` is pressed.

#### Method 2: Running Standalone Services

**Terminal 1 — FastAPI Backend**:
```bash
uv run python scripts/run_api.py --host 127.0.0.1 --port 8000 --reload
# Or directly via uvicorn:
uv run uvicorn grid_guard.api.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 — React Frontend**:
```bash
cd frontend
npm run dev
```

---

### 7.4 Build Commands (Production Bundles)

#### 1. Building the Frontend Production Bundle
Compile TypeScript and generate the optimized, tree-shaken static production bundle with Vite:

```bash
cd frontend
npm run build
```
- **Output**: Minified production artifacts generated in `frontend/dist/`.
- **Bundle Contents**: `dist/index.html`, minified CSS (`dist/assets/*.css`), and chunked JavaScript (`dist/assets/*.js`).

#### 2. Previewing the Production Build Locally
Verify the production build before deployment:

```bash
cd frontend
npm run preview
# Preview server available at: http://localhost:4173
```

#### 3. Building via Docker & Docker Compose
Build and run the entire multi-container production system (FastAPI on port 8000, Nginx serving React on port 3000):

```bash
# Build images and start containers in detached mode
docker compose up --build -d

# Check status of both services
docker compose ps

# View live container logs
docker compose logs -f

# Terminate containers
docker compose down
```

---

### 7.5 Automated Testing & Code Quality Verification

Grid-Guard maintains a **100% passing test suite across all 266 automated tests**:

```bash
# --------------------------------------------------------------------------
# 1. Backend Python Test Suite (162 tests)
# --------------------------------------------------------------------------
uv run pytest -q

# --------------------------------------------------------------------------
# 2. Backend Python Linting & Formatting Check (Ruff)
# --------------------------------------------------------------------------
uv run ruff check .

# --------------------------------------------------------------------------
# 3. Frontend React Unit & Integration Test Suite (104 tests / 27 files)
# --------------------------------------------------------------------------
cd frontend
npm run test

# --------------------------------------------------------------------------
# 4. Frontend Strict TypeScript Typechecking (zero compile errors)
# --------------------------------------------------------------------------
npm run typecheck

# --------------------------------------------------------------------------
# 5. Frontend ESLint Verification (zero warnings/errors)
# --------------------------------------------------------------------------
npm run lint

# --------------------------------------------------------------------------
# 6. Production Bundle Build Verification
# --------------------------------------------------------------------------
npm run build
cd ..
```

---

## 8. REST API Reference & Endpoints

The FastAPI backend exposes fully typed REST endpoints conforming to OpenAPI 3.1. Interactive Swagger UI is available at **`http://localhost:8000/docs`**.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Liveness health probe returning service status and loaded model version. |
| `GET` | `/ready` | Readiness probe confirming model booster and Tree-SHAP explainer are preloaded in RAM. |
| `POST` | `/api/v1/predict` | Score a single smart meter: computes 60 features, calibrated probability, financial metrics, and Tree-SHAP explanation. |
| `POST` | `/api/v1/predict/batch` | Batch scoring endpoint for up to 50 smart meters concurrently. |
| `GET` | `/api/v1/inspection/queue` | Returns prioritized work-order candidates filtered by `min_env`, `min_probability`, and `max_inspections`. |
| `POST` | `/api/v1/inspection/ticket` | Generates a complete forensic inspection work order with evidence narratives and signatures. |
| `GET` | `/api/v1/metadata/model` | Introspects model architecture, hyperparameters, training objective, and feature metadata. |
| `GET` | `/api/v1/metadata/config` | Retrieves active operational defaults (tariff, crew dispatch cost, recovery horizon). |

### Example API Request (Curl)
```bash
curl -X POST "http://localhost:8000/api/v1/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "meter_id": "METER_DEMO_001",
    "customer_type": "residential",
    "feeder_id": "FEEDER_NORTH_04",
    "tariff_per_kwh": 0.15,
    "dispatch_cost": 100.0,
    "decision_rule": "env",
    "include_explanation": true,
    "readings": [
      {"date": "2024-01-01", "consumption_kwh": 25.4},
      {"date": "2024-01-02", "consumption_kwh": 26.1},
      {"date": "2024-01-03", "consumption_kwh": 2.1}
    ]
  }'
```

---

## 9. Measured Empirical Benchmarks

### 9.1 Machine Learning Model Benchmark (254,232 Validation Samples)
The cost-sensitive LightGBM champion booster was evaluated on historical smart-meter validation data against unweighted and imbalance-oversampled baselines:

| Architecture | PR-AUC | ROC-AUC | Precision@100 | Wasted Dispatch Cost | Undetected Leakage Cost | Total Operational Loss |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Phase 4: Unweighted Baseline** | 0.3035 | 0.7739 | 0.65 | $261,200 | $1,711,500 | $1,972,700 |
| **Phase 5: SMOTE-Tomek Imbalance** | 0.2841 | 0.7612 | 0.58 | $342,100 | $1,385,200 | $1,727,300 |
| **Phase 6: Cost-Sensitive (Champion)** | **0.3021** | **0.7725** | **0.72** | **$215,800** | **$1,273,600** | **$1,489,400 (-24.5%)** |

### 9.2 Operational Policy Benchmark (42,372 Fleet Candidates)
Evaluating decision rules across the operational fleet demonstrates that prioritizing by Expected Net Value maximizes recovery and minimizes wasted crew dispatches:

| Inspection Policy Rule | Recommended Dispatches | Expected Gross Recovery | Total Crew Dispatch Cost | Expected Net Value ($\text{ENV}$) | Realized Operational Loss |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Fixed Cutoff ($p \ge 0.50$)** | 170 (0.40%) | $240,120.42 | $17,000.00 | $223,120.42 | $82,685.27 |
| **Bayes Cost Threshold** | 880 (2.08%) | $362,497.41 | $88,000.00 | $274,497.41 | $68,073.82 |
| **Dynamic ENV Policy (Grid-Guard)**| **801 (1.89%)** | **$355,330.47** | **$80,100.00** | **+$275,230.47** | **$64,842.91 (Lowest Loss)** |

---

## 10. Calm Proof Flow Design System

The user interface adheres strictly to `/DesignSystem.md` ("Calm Proof Flow"), rejecting generic dashboard templates and arbitrary SaaS styling:

- **Visual Density & Typography**:
  - Display & Headings: `Space Grotesk` (600/700 weight) for authoritative structure.
  - Body Text: `IBM Plex Sans` for legibility across telemetry records.
  - Tabular Numbers & Codes: `JetBrains Mono` with `tabular-nums` for precise alignment of currency, percentages, and dates.
- **Curated Color Tokens**:
  - Ink: `#121512` (authoritative deep forest-black)
  - Canvas: `#F4F5F0` (calm warm off-white surface)
  - Surface: `#FFFFFF` (elevated cards with hairline borders)
  - Chartreuse: `#D4F04A` (sparing operational highlight & active states)
  - Safe Green: `#3F8B61` (positive Expected Net Value & moderating evidence)
  - Threat Violet: `#7D6DB2` (strictly reserved for Tree-SHAP evidence attribution)
  - Danger Red: `#C45646` (critical electrical tampering severity)
- **Restrained Motion**: Subtle 120ms–260ms easing transitions for hover lift and slide-out drawers, eliminating distracting animations during critical dispatch operations.

---

## 11. Financial Methodology & Caveats

- **Deficit Derivation**: Unmetered consumption is derived by measuring recent trailing consumption (e.g., 14-day window) against pre-anomaly baselines (60-day window).
- **Tariff & Horizon Assumptions**: Standard default tariff ($\$0.15$/kWh), crew dispatch cost ($\$100.00$), and recovery horizon (12 billing cycles) can be customized per feeder, tariff class, or utility contract.
- **Probabilistic Modeling**: All monetary figures represent **modeled expectations** ($E[\text{Recovery}] = \sum p_i R_i$) and do not represent verified cash until physical on-site inspection confirms the bypass and revenue recovery billing is issued.

---

## 12. Known Limitations & Roadmap

- **Telemetry Frequency**: The platform currently processes daily AMI consumption aggregates. Future releases will introduce 15-minute interval smart-meter ingestion to analyze reactive power signatures, power factor deviations, and phase-angle distortions.
- **Substation Energy Balancing**: Planned feeder-level energy mass-balancing (substation sendout minus sum of consumer meters) to bound total NTL volume before individual meter scoring.
- **GIS Route Optimization**: Geographic batching of candidate work orders to reduce travel time and crew dispatch expenses.

---

## 13. License & Acknowledgments

Grid-Guard is distributed under the **MIT License**.

- **Dataset Acknowledgments**: State Grid Corporation of China (SGCC) Smart Meter Benchmark dataset.
- **Research Foundations**: Cost-sensitive machine learning in utility revenue protection and Tree-SHAP local game-theoretic attribution.
