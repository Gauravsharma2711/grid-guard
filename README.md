# ⚡ Grid-Guard

**Financial-Aware Smart Meter Tampering & Non-Technical Loss (NTL) Detection Platform**

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.64.0-FF4B4B.svg)](https://streamlit.io/)
[![LightGBM](https://img.shields.io/badge/LightGBM-4.6.0-brightgreen.svg)](https://lightgbm.readthedocs.io/)
[![Tree--SHAP](https://img.shields.io/badge/Explainability-Tree--SHAP-yellow.svg)](https://shap.readthedocs.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Tests: 162 Passing](https://img.shields.io/badge/tests-162%20passed-success.svg)](tests/)

---

## 1. Value Proposition

Grid-Guard turns smart-meter anomaly detection into an economically rational field operation: **anomalies are only dispatched when the expected recovered revenue exceeds the crew dispatch cost.**

---

## 2. The Operational Problem

Electric power utilities lose tens of billions of dollars annually to **Non-Technical Losses (NTL)**—primarily physical meter tampering, illegal line tapping, and unauthorized consumption.

Conventional machine-learning models evaluate smart meters using statistical accuracy or F1-scores, treating all detection errors equally. In real-world utility operations, however, errors have asymmetric financial consequences:
- **False Positives**: Incur an immediate fixed operational cost ($C_{\text{FP}} \approx \$100$) to dispatch a two-person physical inspection crew.
- **False Negatives**: Allow ongoing unmetered revenue leakage ($C_{\text{FN}} = \text{Deficit} \times \text{Tariff} \times \text{Horizon}$), which can exceed $\$150,000$ on large commercial accounts.

A naive model that flags a rural lifeline customer with high confidence may cause the utility to spend **\$100 dispatching a crew to recover \$10 of energy**.

---

## 3. The Grid-Guard Solution

Grid-Guard solves this asymmetric challenge through a **four-pillar financial architecture**:

1. **60-Feature Causal Temporal Pipeline**: Captures consumption collapse ratios, historical baselines, weekday/weekend regimes, zero-consumption streaks, and near-zero flatline variances.
2. **Financially Weighted Learning (Phase 6 Champion)**: A cost-sensitive LightGBM objective where training sample loss is weighted by the potential revenue leakage.
3. **Dynamic Expected Net Value (ENV) Prioritization (Phase 7)**:
   $$\text{ENV}_i = p_i \times R_i - C_{\text{dispatch}}$$
   Field crews are dispatched if and only if $\text{ENV}_i > 0$, ranking work orders by net financial yield.
4. **Tree-SHAP & Audited Narratives (Phase 8)**: Exact Shapley feature attributions, detected electrical signatures, and non-accusatory field work order tickets.

---

## 4. End-to-End Architecture

```
                          AMI Smart-Meter Daily Readings (kWh)
                                            │
                                            ▼
                           Polars Ingestion & Cleaning Engine
                           (Imputation, Monotonicity, Validation)
                                            │
                                            ▼
                           Temporal Feature Pipeline (60 Features)
                           (Rolling baselines, variability, signatures)
                                            │
                                            ▼
                        Cost-Sensitive LightGBM Booster (Phase 6)
                        (Financially weighted binary log-loss)
                                            │
                                            ▼
                        Dynamic Decision & Financial Engine (Phase 7)
                        (Leakage estimation, dynamic tau, ENV ranking)
                                            │
                                            ▼
                        Tree-SHAP Explainability & Narratives (Phase 8)
                        (Exact Shapley values, electrical signatures)
                                            │
                      ┌─────────────────────┴─────────────────────┐
                      ▼                                           ▼
          FastAPI Backend Service (Phase 9)           Streamlit Dashboard (Phase 10)
          • /health & /ready probes                   • Fleet Overview & KPIs
          • /api/v1/predict (Single & Batch)          • Prioritized Inspection Queue
          • /api/v1/inspection/ticket                 • Interactive Meter Analysis & Time Series
          • /api/v1/inspection/queue                  • Multi-Phase Model Insights
          • /api/v1/metadata/model & config           • 5 Curated Synthetic Demo Archetypes
```

---

## 5. Technology Stack

- **Core & Data Processing**: Python 3.11, Polars, NumPy, Pandas, Pydantic V2
- **Machine Learning**: LightGBM (Gradient Boosted Trees), Scikit-Learn, Imbalanced-Learn
- **Explainability**: SHAP (TreeExplainer)
- **Backend API**: FastAPI, Uvicorn, HTTPX
- **Dashboard & Visualization**: Streamlit, Matplotlib
- **Tooling & Orchestration**: UV, Pytest, Ruff, Docker, Docker Compose

---

## 6. Project Structure

```
grid-guard/
├── artifacts/                  # Verified reproducible artifacts (Phases 3–9)
│   ├── api/                    # OpenAPI schema, sample payloads
│   ├── cost_sensitive/         # Champion LightGBM model, weight audits
│   ├── decision/               # Prioritized inspection queue, policy benchmarks
│   └── explainability/         # Enriched work order tickets, Tree-SHAP metadata
├── configs/                    # YAML configuration files (default.yaml)
├── docs/                       # Comprehensive technical documentation
│   ├── architecture.md         # System architecture & principles
│   ├── deployment.md           # Production deployment & container guide
│   ├── demo_guide.md           # Step-by-step evaluator demonstration walkthrough
│   ├── end_to_end_flow.md      # Complete data flow & pipeline trace
│   ├── final_project_status.md # Complete 10-phase sign-off report
│   └── progress.md             # Granular engineering progress log
├── scripts/                    # Command-line execution runners
│   ├── run_api.py              # Launch FastAPI backend
│   ├── run_dashboard.py        # Launch Streamlit dashboard
│   └── run_services.py         # Launch both API and Dashboard concurrently
├── src/grid_guard/             # Core application package
│   ├── api/                    # FastAPI routes, schemas, and lifecycle service
│   ├── config/                 # Pydantic Settings and configurations
│   ├── dashboard/              # Streamlit dashboard, views, charts, and API client
│   │   ├── api_client.py       # Dedicated API client (strict application boundary)
│   │   ├── components/         # Reusable KPI cards, charts, and ticket renderers
│   │   ├── demo_data/          # 5 synthetic demonstration archetypes
│   │   └── views/              # Overview, Queue, Meter Analysis, Insights, Status
│   ├── data/                   # Data cleaning, ingestion, and validation
│   ├── decision/               # Dynamic thresholds and ticket prioritization
│   ├── evaluation/             # Financial cost matrix and leakage estimators
│   ├── explainability/         # Tree-SHAP, feature mapping, signatures, narratives
│   ├── features/               # 60 temporal feature engineering pipeline
│   └── models/                 # Baseline, imbalance, and cost-sensitive boosters
├── tests/                      # 162 automated tests (Unit, Integration, E2E)
├── Dockerfile.api              # Container manifest for FastAPI backend
├── Dockerfile.dashboard        # Container manifest for Streamlit dashboard
├── docker-compose.yml          # Multi-container service orchestration
└── pyproject.toml              # UV / Pip project dependency specification
```

---

## 7. Installation and Execution Guide

### 7.1 Prerequisites & System Requirements
- **Operating System**: Windows 10/11, Linux (Ubuntu 20.04+), or macOS (Intel / Apple Silicon)
- **Python Runtime**: Version `3.11` (or `3.12`)
- **Package Manager**: [`uv`](https://docs.astral.sh/uv/) (recommended for 10x faster installation) or standard `pip`
- **Git**: Installed and configured on your system PATH
- **Docker & Docker Compose** *(Optional, for containerized execution)*

---

### 7.2 Installation Guide

#### Option A: Fast Installation with `uv` (Recommended)
`uv` automatically handles Python virtual environment creation, resolution, and dependency locking:

```bash
# 1. Clone the repository
git clone https://github.com/Gauravsharma2711/grid-guard.git
cd grid-guard

# 2. Install uv if not already present
# On Windows (PowerShell):
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# On Linux / macOS:
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Synchronize all project dependencies into an isolated virtual environment
uv sync
```

#### Option B: Standard Installation with `pip` & `venv`
If you prefer standard Python virtual environments:

```bash
# 1. Clone the repository
git clone https://github.com/Gauravsharma2711/grid-guard.git
cd grid-guard

# 2. Create and activate a Python 3.11 virtual environment
# On Windows (PowerShell / Command Prompt):
python -m venv .venv
.venv\Scripts\activate

# On Linux / macOS:
python3 -m venv .venv
source .venv/bin/activate

# 3. Upgrade pip and install package in editable development mode
pip install --upgrade pip
pip install -e .
```

---

### 7.3 Running the Backend (FastAPI Inference Service)

The backend exposes the core machine learning inference pipeline, Tree-SHAP explainer, dynamic threshold engine, and inspection work-order generator.

#### Method 1: Using the Backend Runner Script (Recommended)
```bash
# Launch on default port (8000)
uv run python scripts/run_api.py

# Or specify custom host, port, or live-reload:
uv run python scripts/run_api.py --port 5678 --host 0.0.0.0 --reload
```

#### Method 2: Running Directly with Uvicorn
```bash
# Using uv:
uv run uvicorn grid_guard.api.main:app --host 0.0.0.0 --port 8000 --reload

# Or with activated virtual environment:
uvicorn grid_guard.api.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Backend Endpoints & Verification:
- **Interactive Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs) (or [http://localhost:5678/docs](http://localhost:5678/docs))
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health & Readiness Probe**: [http://localhost:8000/health](http://localhost:8000/health)
- **Quick Curl Test**:
  ```bash
  curl http://localhost:8000/health
  # Expected Response: {"status":"healthy","model_loaded":true,"version":"1.0.0"}
  ```

---

### 7.4 Running the Frontend (Streamlit Operational Dashboard)

The frontend provides an interactive, reactive web dashboard for utility revenue analysts, dispatch supervisors, and field technicians.

#### Method 1: Using the Dashboard Runner Script (Recommended)
```bash
# Launch on default port (8501)
uv run python scripts/run_dashboard.py

# Or specify custom port (e.g., 1456)
uv run python scripts/run_dashboard.py --port 1456
```

#### Method 2: Running Directly with Streamlit CLI
```bash
# Using uv:
uv run streamlit run src/grid_guard/dashboard/app.py --server.port 8501

# Or with activated virtual environment:
streamlit run src/grid_guard/dashboard/app.py --server.port 8501
```

#### Dashboard Features & Navigation:
- **Web UI URL**: [http://localhost:8501](http://localhost:8501) (or `http://localhost:1456`)
- **Fleet Overview**: Executive KPI cards, Expected Net Value distributions, and prioritized candidate tables.
- **Meter Drilldown**: 180-day interactive Plotly consumption time series with changepoints and Tree-SHAP waterfall attributions.
- **Interactive Demonstrations**: 5 pre-configured synthetic tampering archetypes (Abrupt Bypassing, Partial Resistance Shunting, Seasonal Peak Divergence, Rural Lifeline Consumer, and Honest Volatile User).
- **Backend Connection**: The dashboard communicates with the backend via HTTP. It automatically connects to the active API instance (configured in `configs/default.yaml` or via the `API_BASE_URL` environment variable).

---

### 7.5 Running Both Services Concurrently (One-Command Launcher)

To launch both the FastAPI backend and Streamlit dashboard in a single terminal session:

```bash
uv run python scripts/run_services.py
```

This single command:
1. Starts the FastAPI inference backend.
2. Waits 3 seconds for the Lifespan model booster to preload into RAM.
3. Spawns the Streamlit operational dashboard.
4. Manages process lifecycles cleanly—pressing `Ctrl+C` terminates both services gracefully.

---

### 7.6 Running with Docker & Docker Compose

For a zero-dependency, containerized deployment:

```bash
# 1. Build and start all services in detached mode
docker compose up --build -d

# 2. View real-time container logs
docker compose logs -f

# 3. Check container health status
docker compose ps

# 4. Stop all services
docker compose down
```

- **Dashboard Interface**: [http://localhost:8501](http://localhost:8501)
- **FastAPI OpenAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### 7.7 Running Automated Tests & Code Quality

Validate system correctness, leakage prevention, and mathematical formulations across all 162 unit and integration tests:

```bash
# Run complete test suite (162 tests)
uv run pytest

# Run with verbose output and short traceback
uv run pytest -v --tb=short

# Run code style and linter check (Ruff)
uv run ruff check .
```

---

## 8. Interactive Demonstration Experience

The dashboard includes **5 deterministic synthetic demonstration archetypes** illustrating core operational regimes without exposing real customer data:

1. **Normal Residential Meter**: Consistent 12–15 kWh/day usage. Yields low risk (`p=0.065`) and negative ENV (`-$494.43`). No dispatch recommended.
2. **Sustained Step-Down Anomaly**: Sudden 95% drop from 28.5 kWh to 1.2 kWh. Model outputs elevated probability (`p=0.359`), estimated recovery of `~$28,600`, and **`ENV = +$9,756.45`**. Recommends immediate inspection.
3. **Flatline Invariance Anomaly**: Meter locked to constant 1.00 kWh/day (0 variance). Activates the *"Flatline pattern"* signature, yielding `ENV = +$521.84`.
4. **High-Value Commercial Account**: Baseline of 240 kWh/day dropping to 40 kWh/day. Produces **`ENV = +$179,270.29`**, immediately claiming #1 rank in the inspection queue.
5. **High Risk / Low Net Value (Lifeline)**: Rural customer using 0.25 kWh/day dropping to 0.03 kWh/day. Although the model detects an anomaly, the 12-month leakage is only `~$12.00`. **Grid-Guard's ENV rule rejects dispatch** (`ENV = -$89.20 < 0`), saving the utility from wasting a $100 crew dispatch!

---

## 9. Measured Empirical Benchmarks

### 9.1 Machine Learning Model Comparison (254,232 Validation Samples)
| Phase | Architecture | PR-AUC | ROC-AUC | Precision@100 | Wasted Dispatch | Undetected Leakage | Total Operational Loss |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Phase 4** | Unweighted Baseline | 0.3035 | 0.7739 | 0.65 | $261,200 | $1,711,500 | $1,972,700 |
| **Phase 5** | SMOTE-Tomek Imbalance | 0.2841 | 0.7612 | 0.58 | $342,100 | $1,385,200 | $1,727,300 |
| **Phase 6** | **Cost-Sensitive (Champion)**| **0.3021** | **0.7725** | **0.72** | **$215,800** | **$1,273,600** | **$1,489,400 (-24.5%)** |

### 9.2 Operational Policy Comparison (42,372 Fleet Candidates)
| Inspection Policy Rule | Recommended Dispatches | Expected Gross Recovery | Total Dispatch Cost | Expected Net Value (ENV) | Realized Operational Loss |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Fixed Threshold (p >= 0.50)** | 170 (0.40%) | $240,120.42 | $17,000.00 | $223,120.42 | $82,685.27 |
| **Bayes Cost Threshold** | 880 (2.08%) | $362,497.41 | $88,000.00 | $274,497.41 | $68,073.82 |
| **Dynamic ENV Policy (Grid-Guard)**| **801 (1.89%)** | **$355,330.47** | **$80,100.00** | **+$275,230.47** | **$64,842.91 (Lowest Loss)** |

---

## 10. Financial Methodology & Caveats

- **Observed / Derived**: Daily deficits and unmetered volumes are derived from comparing recent 14-day consumption against historical 60-day baselines.
- **Assumed / Modeled Parameters**: Default tariff (\$0.15/kWh), crew dispatch cost (\$100/visit), and recovery horizon (12 billing cycles) are configurable in settings.
- **Operational Labeling**: All monetary figures represent **modeled expectations** ($E[\text{Recovery}] = \sum p_i R_i$) and do not guarantee recovered cash until field crews physically verify and bill the unmetered consumption.

---

## 11. Known Limitations & Future Work

- **Granularity**: The current release operates on daily AMI aggregates. Integrating 15-minute interval smart-meter data could unlock reactive power and phase-angle anomaly signatures.
- **Feeder Aggregation**: Future iterations can incorporate substation-level energy balancing (total feeder sendout vs. sum of meters) to bound total NTL prior to individual meter scoring.
- **Dynamic Crew Routing**: Integrating GIS coordinates to batch inspections geographically could further reduce dispatch travel costs.

---

## 12. License & Citation

Grid-Guard is developed for research and operational utility loss reduction under the MIT License.
Dataset acknowledgments: State Grid Corporation of China (SGCC) Smart Meter Benchmark.
