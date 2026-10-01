# Grid-Guard

**Smart-Meter Tampering & Non-Technical Loss (NTL) Detection System with Cost-Sensitive Decision Optimization**

---

## 1. Project Purpose & Problem Statement

Power distribution utilities worldwide lose billions of dollars annually due to **Non-Technical Losses (NTL)**—primarily electricity theft, meter tampering, billing anomalies, and unmetered consumption. Traditional detection mechanisms rely heavily on manual periodic inspections, static consumption heuristics, or isolated anomaly detection models that maximize statistical recall without considering economic reality.

In practical utility operations, false positives incur steep operational inspection costs ($C_{fp}$ dispatching field crews), whereas false negatives allow cumulative revenue leakage ($C_{fn}$). A high-accuracy classifier that triggers dozens of unmerited field inspections in remote areas can cost a utility far more money than it recovers.

## 2. Core Idea

Grid-Guard departs from naive probability-only classification. The central operating thesis is:

$$\text{Detection Probability alone is NOT the final inspection decision.}$$

Grid-Guard calculates an **Expected Net Value (ENV)** for every flagged meter before recommending action:

$$\text{Tampering Probability } (P) \times \text{Estimated Financial Leakage Recovery } (L) - \text{Inspection Dispatch Cost } (C) = \text{Expected Net Value (ENV)}$$

Field inspections are prioritized strictly when $\text{ENV} > 0$ and ranked to maximize net utility recovery under workforce capacity constraints.

---

## 3. Current Project Status

- **Phase 1: Data Acquisition & Environment Setup** — *Completed / Operational*
- **Phase 2: Data Preprocessing & Validation Pipeline** — *Upcoming*
- **Phase 3: Feature Engineering (Temporal & Theft Signatures)** — *Upcoming*
- **Phase 4: Anomaly & Supervised Classification Modeling (LightGBM/XGBoost)** — *Upcoming*
- **Phase 5: Financial Loss Function & Dynamic ENV Thresholding** — *Upcoming*
- **Phase 6: Explainable AI (SHAP Tampering Signatures)** — *Upcoming*
- **Phase 7: Real-Time FastAPI Inference Engine & Monitoring Dashboard** — *Upcoming*

> [!NOTE]
> Phase 1 establishes the engineering foundation, dependency management, high-performance Polars ingestion framework, validation engine, local MLflow tracking, test suite, and data governance contracts. Model training, FastAPI endpoints, and dashboard are planned for subsequent phases.

---

## 4. Architecture at a High Level

```
[ Smart-Meter AMI Time-Series (CSV / Parquet) ]
                      │
                      ▼
[ Ingestion & Schema Mapping Engine (Polars) ]
                      │
                      ▼
[ Data Quality & Integrity Validation (Polars / Pydantic) ]
                      │
                      ▼
[ Feature Store: Temporal, Rolling, Aggregates & Signatures ] (Phase 3)
                      │
                      ▼
[ LightGBM Classifier & Tampering Estimator ] (Phase 4)
                      │
                      ▼
[ Cost-Sensitive ENV Decision Matrix Engine ] (Phase 5)
                      │
                      ▼
[ Field Inspection Priority Ranking & Explainability (SHAP) ] (Phase 6)
                      │
                      ▼
[ FastAPI Operational API & Decision Dashboard ] (Phase 7)
```

---

## 5. Repository Structure

```
grid-guard/
├── .github/
│   └── workflows/
│       └── ci.yml               # Automated CI: linting & tests
├── configs/
│   ├── default.yaml             # Core runtime and path configurations
│   └── dataset_mappings.yaml    # Column mappings for AMI datasets (e.g., SGCC)
├── data/
│   ├── raw/                     # Original immutable raw smart-meter datasets (.gitkeep)
│   ├── interim/                 # Transformed / intermediate datasets (.gitkeep)
│   ├── processed/               # Clean, model-ready Parquet datasets (.gitkeep)
│   └── external/                # External tariffs, weather, feeder data (.gitkeep)
├── docs/
│   ├── data_contract.md         # Conceptual AMI schema and validation expectations
│   └── progress.md              # Phase tracking, validation reports, and roadmap
├── notebooks/                   # Exploratory analysis notebooks (.gitkeep)
├── scripts/
│   ├── inspect_raw_data.py      # Quick CLI inspection of raw data files
│   └── verify_setup.py          # End-to-end environment validation smoke test
├── src/
│   └── grid_guard/
│       ├── __init__.py
│       ├── py.typed
│       ├── config/
│       │   ├── __init__.py
│       │   └── settings.py      # Pydantic-based configuration management
│       ├── data/
│       │   ├── __init__.py
│       │   ├── ingestion.py     # High-performance Polars ingestion engine
│       │   └── validation.py    # Time-series schema & sanity validation rules
│       ├── features/            # Feature extraction (Phase 3)
│       ├── models/              # Classification models (Phase 4)
│       ├── evaluation/          # Cost-sensitive evaluation & ENV metrics (Phase 5)
│       ├── tracking/
│       │   ├── __init__.py
│       │   └── experiment.py    # MLflow experiment tracking utilities
│       └── utils/
│           ├── __init__.py
│           └── logging.py       # Standardized structured logging
├── tests/
│   ├── conftest.py              # Synthetic data fixtures (CSV / Parquet)
│   ├── unit/
│   │   ├── test_config.py       # Configuration loading tests
│   │   ├── test_ingestion.py    # Polars reader and ingestion tests
│   │   ├── test_validation.py   # Dataset validation rules tests
│   │   └── test_tracking.py     # MLflow tracking tests
│   └── integration/
│       └── test_pipeline_smoke.py # End-to-end ingestion and validation pipeline test
├── .gitignore                   # Comprehensive ignores (raw data, virtualenvs, mlruns)
├── .python-version              # Python version pin (3.11.16)
├── pyproject.toml               # PEP 621 package metadata & dependencies
└── README.md                    # Project documentation
```

---

## 6. Environment Setup & Dependency Installation

### Prerequisites

- **Python**: `3.11.x` (Recommended: Python 3.11.16)
- **uv**: Fast package and environment manager (Recommended) or standard `python -m venv`

### Quick Setup with `uv`

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Gauravsharma2711/grid-guard.git
   cd grid-guard
   ```

2. **Create the isolated environment:**
   ```bash
   uv venv --python 3.11 .venv
   ```

3. **Activate the environment:**
   - **Windows (PowerShell):**
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS:**
     ```bash
     source .venv/bin/activate
     ```

4. **Install all dependencies (including dev tools):**
   ```bash
   uv pip install -e ".[dev]"
   ```

---

## 7. Dataset Placement & Data Governance Policy

### Dataset Location

Download your smart-meter dataset (e.g. the State Grid Corporation of China [SGCC] electricity theft dataset) and place it directly inside:

```
data/raw/
```

Expected file example: `data/raw/electric-data.csv`

### Governance Rules

1. **Immutability**: Raw files in `data/raw/` must **NEVER** be modified in place or overwritten by code.
2. **Intermediate Data**: Cleaning, pivoting, and unpivoting output belongs exclusively in `data/interim/`.
3. **Model Datasets**: Scaled, encoded, feature-engineered Parquet files belong in `data/processed/`.
4. **External References**: Feeder topologies, geographic tariffs, or substation logs belong in `data/external/`.
5. **Git Protection**: Git ignores all data files (`*.csv`, `*.parquet`, etc.) automatically. Never force-add raw datasets into version control.

---

## 8. Running Tests & Code Quality Checks

### Run Automated Tests

The test suite runs against deterministic in-memory and synthetic disk fixtures:

```bash
pytest
```

With coverage report:

```bash
pytest --cov=grid_guard tests/
```

### Run Code Quality (Ruff)

```bash
# Check code style and linting
ruff check .

# Format code
ruff format .
```

---

## 9. Local MLflow Experiment Tracking

Grid-Guard uses local MLflow tracking without requiring cloud credentials or external servers.

1. **Verify tracking locally:**
   ```bash
   python -c "import mlflow; mlflow.set_experiment('grid-guard-smoke'); print('MLflow operational')"
   ```

2. **Launch the MLflow UI (optional):**
   ```bash
   mlflow ui --port 5000
   ```
   Access the dashboard at `http://127.0.0.1:5000` to inspect runs, parameters, metrics, and models.

---

## 10. Development Workflow

1. Configure settings in `configs/default.yaml` or through environment variables prefixed with `GRID_GUARD_`.
2. Map new dataset schemas in `configs/dataset_mappings.yaml`.
3. Ingest datasets through `grid_guard.data.ingestion.DataIngestionEngine`.
4. Validate data integrity through `grid_guard.data.validation.DataValidator`.
5. Run `verify_setup.py` to confirm environment health:
   ```bash
   python scripts/verify_setup.py
   ```

---

## 11. Upcoming Phases

- **Phase 2**: Automated reshaping (wide-to-long), missing timestamp imputation, calendar alignment.
- **Phase 3**: Extraction of daily profiles, consumption volatility, zero-consumption runs, abnormal drop ratios.
- **Phase 4**: LightGBM training with temporal cross-validation and SMOTE/class-weighting for extreme imbalance.
- **Phase 5**: Implementation of the custom utility financial loss function and optimal threshold selection ($ENV^*$).
- **Phase 6**: SHAP tree explainers generating inspector briefing sheets for field validation.
- **Phase 7**: FastAPI microservice for scoring streaming meter readings and operational triage dashboard.
