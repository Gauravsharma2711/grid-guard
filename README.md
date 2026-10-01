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
- **Phase 2: EDA, Data Cleaning & AMI Time-Series Understanding** — *Completed / Operational*
- **Phase 3: Temporal Feature Engineering & Tampering Signatures** — *Completed / Operational*
- **Phase 4: Anomaly & Supervised Classification Modeling (LightGBM/XGBoost)** — *Upcoming*
- **Phase 5: Financial Loss Function & Dynamic ENV Thresholding** — *Upcoming*
- **Phase 6: Explainable AI (SHAP Tampering Signatures)** — *Upcoming*
- **Phase 7: Real-Time FastAPI Inference Engine & Monitoring Dashboard** — *Upcoming*

> [!NOTE]
> Phases 1–3 establish the production foundation: high-performance Polars ingestion, data validation rules, localized bounded-gap imputation, EDA reports, and a 60-feature temporal extraction pipeline capturing sudden consumption collapses, zero streaks, flatlines, multi-scale ratios, and week-over-week dynamics.

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

## 10. EDA, Profiling & Data Cleaning (Phase 2)

Grid-Guard provides an end-to-end command for profiling, localized bounded temporal imputation, canonical Parquet export, and visualization:

```bash
# Run full profiling, cleaning, Parquet export, and figure generation
python scripts/run_eda_cleaning.py --action all

# Run specific stages or with custom imputation gap limits:
python scripts/run_eda_cleaning.py --action profile
python scripts/run_eda_cleaning.py --action clean --max-gap 3
python scripts/run_eda_cleaning.py --action visualize
```

### Generated Artifacts
- **Clean Wide Parquet**: `data/processed/canonical_ami_clean.parquet` (77.6 MB)
- **Clean Long Series Parquet**: `data/processed/canonical_ami_series.parquet` (395.8 MB, 43,812,648 rows)
- **Comprehensive Audit Report**: `docs/eda/eda_report.md`
- **Transformation Lineage**: `docs/eda/data_lineage.json`
- **Statistical Profile JSON**: `docs/eda/dataset_profile.json`
- **Figures Suite**: `docs/eda/figures/fig1_dataset_overview.png` to `fig5_imputation_impact.png`

---

## 11. Temporal Feature Engineering & Tampering Signatures (Phase 3)

Grid-Guard converts canonical smart-meter time series into a documented, leakage-safe, model-ready feature representation. All 60 registered features use strictly backward trailing windows ($\le t$), preserving mathematical causality and preventing future data leakage.

### Feature Families
1. **Calendar & Cyclical Harmonics** (9 features): Day of week, day of month, month, quarter, weekend indicator, and cyclical sine/cosine harmonics (`dow_sin`, `dow_cos`, `month_sin`, `month_cos`).
2. **Backward Lags** (6 features): Previous-day and previous-week lags (`1d`, `2d`, `3d`, `7d`, `14d`, `30d`).
3. **Trailing Rolling Statistics** (16 features): Trailing mean, std, min, max, and median across `7d`, `14d`, `30d`, `60d`, and `90d` historical windows.
4. **Multi-Scale Ratios & Dynamics** (7 features): Moving average ratios (`7d/30d`, `14d/60d`, `30d/90d`), Week-over-Week changes/ratios, and Peak-to-Average Ratios (`PAR 7d`, `PAR 30d`).
5. **Tampering Signatures** (13 features):
   - **Zero Streaks**: Trailing zero count (`7d`, `30d`), zero ratio, and current continuous zero streak.
   - **Flatline Metering**: Trailing coefficient of variation (`CV 7d`, `CV 30d`), daily absolute differences, and consecutive identical-reading streaks.
   - **Sustained Step-Down**: Baseline collapse ratio ($R_{14d} / B_{60d}$), sustained drop ratio, absolute drop magnitude, and depressed consumption duration.
6. **Periodicity & Autocorrelation** (3 features): Same-weekday personal profile deviation (`dow_profile_deviation`, `dow_profile_ratio`) and trailing 30-day weekly lag-7 autocorrelation.
7. **Context & Quality** (6 features): Historical coverage ratio, missing ratio, imputation ratio, trailing 30-day missingness, and leave-one-out peer aggregates (when feeder metadata exists).

### Running Feature Engineering

```bash
# Run complete feature pipeline: export dictionary, generate figures, process dataset, and audit
python scripts/run_feature_engineering.py all

# Run specific actions:
python scripts/run_feature_engineering.py dictionary  # Exports registry JSON & Markdown dictionary
python scripts/run_feature_engineering.py visualize   # Generates diagnostic validation plots
python scripts/run_feature_engineering.py generate    # Computes canonical_features.parquet
python scripts/run_feature_engineering.py validate    # Audits distributions, finiteness & uniqueness
```

### Generated Artifacts
- **Canonical Feature Parquet**: `data/processed/canonical_features.parquet` (2,726.35 MB, 43,812,648 rows $\times$ 64 columns)
- **Feature Dictionary (Markdown)**: `docs/features/feature_dictionary.md`
- **Machine-Readable Registry (JSON)**: `docs/features/feature_registry.json`
- **Feature Quality & Audit Report (JSON)**: `docs/features/feature_quality_report.json`
- **Feature Summary Report (Markdown)**: `docs/features/feature_summary_report.md`
- **Validation Figures**:
  - `docs/features/figures/fig1_step_down_tampering.png`
  - `docs/features/figures/fig2_zero_streak_detection.png`
  - `docs/features/figures/fig3_flatline_variance_collapse.png`
  - `docs/features/figures/fig4_multi_scale_ratios_and_par.png`
  - `docs/features/figures/fig5_real_meters_comparison.png`

---

## 12. Upcoming Phases

- **Phase 4**: Anomaly & Supervised Classification Modeling (LightGBM/XGBoost with temporal CV).
- **Phase 5**: Custom Financial Loss Function & Dynamic ENV Threshold Optimization.
- **Phase 6**: SHAP Tree Explainers & Field Inspector Briefing Sheets.
- **Phase 7**: FastAPI Operational Microservice & Real-Time Triage Dashboard.

