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
- **Phase 4: Cost Matrix Definition & Unweighted Baseline Modeling** — *Completed / Operational*
- **Phase 5: Class Imbalance & Representation Strategies** — *Completed / Operational*
- **Phase 6: Cost-Sensitive Custom Objective & Financially Weighted Learning** — *Completed / Operational*
- **Phase 7: Expected Net Value (ENV) & Dynamic Thresholding** — *Completed / Operational*
- **Phase 8: Explainable AI (SHAP Tree Explainer & Attribution)** — *Upcoming*
- **Phase 9: FastAPI Operational Decision Service** — *Upcoming*
- **Phase 10: Interactive Operational Dashboard** — *Upcoming*

> [!NOTE]
> Phases 1–4 establish the empirical benchmark: high-performance Polars ingestion, data validation rules, localized bounded-gap imputation, a 60-feature causal temporal extraction pipeline, a strictly time-aware LightGBM baseline binary classifier, and a configurable financial cost model tracking field dispatch costs vs. undetected revenue leakage.

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

## 12. Cost Matrix Definition & Unweighted Baseline Modeling (Phase 4)

Grid-Guard establishes an ordinary, strictly unweighted LightGBM baseline binary classifier and a formal financial cost matrix. The baseline deliberately avoids SMOTE, class weights, cost weighting, or dynamic thresholds, evaluating at the conventional **0.5 decision threshold** to establish the benchmark against which later cost-sensitive methods will be judged.

### A. Non-Overlapping Chronological Split

| Partition | Date Range | Duration | Sample Count | Meters | Theft Rate |
|---|---|---|---|---|---|
| **Train** | `2014-04-01` to `2015-12-31` | 21 months | 932,184 | 42,372 | 8.53% |
| **Validation** | `2016-01-01` to `2016-05-31` | 5 months | 254,232 | 42,372 | 8.53% |
| **Held-Out Test** | `2016-06-01` to `2016-10-31` | 5 months | 254,232 | 42,372 | 8.53% |

### B. Baseline Empirical Performance (Held-Out Test Set)

| Metric | Measured Baseline Value | Operational Takeaway |
|---|---|---|
| **PR-AUC** | **`0.2959`** | Primary metric under class imbalance (vs. 0.0853 random rate) |
| **ROC-AUC** | `0.7711` | Discriminative ranking capability |
| **Precision** | `46.89%` | 3,161 true thefts detected out of 6,741 inspections |
| **Recall** | **`14.57%`** | **Severe failure of unweighted baseline: 18,529 thefts missed (85.4%)** |
| **F1-Score** | `0.2224` | Harmonic mean |
| **Precision@10** | `80.00%` | 8 out of top 10 ranked meters are true thefts |
| **Precision@50** | `84.00%` | 42 out of top 50 ranked meters are true thefts |
| **Precision@100** | `82.00%` | 82 out of top 100 ranked meters are true thefts |
| **Precision@500** | `63.20%` | 316 out of top 500 ranked meters are true thefts |
| **Precision@1000** | `57.00%` | 570 out of top 1,000 ranked meters are true thefts |

### C. Financial Cost Outcomes

Using configured parameters ($C_{\text{dispatch}} = \$100.00$, Tariff = $\$0.15/\text{kWh}$, $H_{\text{undetected}} = 12$ months):
- **Wasted FP Field Dispatch Cost**: `USD 358,000.00` (3,580 false alarms)
- **Undetected FN Revenue Leakage**: `USD 765,766.00` (18,529 missed thefts)
- **Total Baseline Operational Loss**: **`USD 1,123,766.00`**
- **Estimated Gross Recovered Revenue**: `USD 1,447,265.25`
- **Estimated Net Financial Recovery**: `USD 773,165.25`

### D. Running the Baseline Pipeline

```bash
# Execute end-to-end baseline training, evaluation, artifact export, and MLflow logging
python scripts/run_baseline.py all

# Override operational assumptions
python scripts/run_baseline.py all --stride 30 --dispatch-cost 120.0 --tariff 0.18

# Launch local MLflow dashboard
mlflow ui --backend-store-uri sqlite:///mlruns/mlflow.db
```

### E. Generated Baseline Artifacts
- **Model Checkpoint**: `artifacts/baseline/baseline_lightgbm.txt`
- **Scored Test Predictions**: `artifacts/baseline/baseline_predictions.parquet` (254,232 rows)
- **Metrics Report**: `artifacts/baseline/baseline_metrics.json`
- **Financial Audit Report**: `artifacts/baseline/financial_cost_report.md`
- **Diagnostic Charts**:
  - `artifacts/baseline/figures/pr_curve.png`
  - `artifacts/baseline/figures/roc_curve.png`
  - `artifacts/baseline/figures/confusion_matrix.png`
  - `artifacts/baseline/figures/probability_distribution.png`
  - `artifacts/baseline/figures/feature_importance.png`
  - `artifacts/baseline/figures/financial_loss_breakdown.png`
  - `artifacts/baseline/figures/precision_at_k.png`

---

## 13. Class Imbalance Strategy & Rare-Tampering Learning (Phase 5)

Grid-Guard addresses the severe real-world class imbalance (8.53% positive prevalence, 10.72:1 imbalance ratio) by evaluating candidate imbalance handling strategies strictly on the chronological validation partition (`2016-01-01` to `2016-05-31`). The selected champion strategy—**Controlled Minority Oversampling (`controlled_oversample_0.20`)**—was evaluated once on the untouched held-out test partition (`2016-06-01` to `2016-10-31`), directly mitigating the acute false-negative deficiency of the unweighted baseline.

### A. Head-to-Head Performance (Held-Out Test Set)

| Metric | Phase 4 (Unweighted Baseline) | Phase 5 Champion (`controlled_oversample_0.20`) | Absolute Difference | Operational Takeaway |
|---|---|---|---|---|
| **PR-AUC** | `0.2959` | **`0.3132`** | **`+0.0173`** | Primary rare-class ranking metric |
| **ROC-AUC** | `0.7711` | `0.7693` | `-0.0018` | Preserved global separability |
| **Recall (Theft Capture)** | `14.57%` | **`23.84%`** | **`+9.27%`** | **+63.6% relative jump in theft detection** |
| **Precision** | `46.89%` | `45.10%` | `-1.79%` | Minor precision trade-off at 0.5 cutoff |
| **F1-Score** | `0.2224` | **`0.3119`** | **`+0.0895`** | +40.2% improvement in harmonic balance |
| **True Positives ($TP$)** | `3,161` | **`5,170`** | **`+2,009`** | **2,009 additional fraudulent meters detected** |
| **False Negatives ($FN$)** | `18,529` | **`16,520`** | **`-2,009`** | **2,009 fewer undetected theft losses** |
| **False Positives ($FP$)** | `3,580` | `6,293` | `+2,713` | Additional inspections dispatched |
| **Brier Score (Calibration)** | `0.0706` | `0.0811` | `+0.0105` | Predictable probability elevation |
| **Total Operational Loss** | `$1,123,766.00` | **`$1,120,098.88`** | **`-$3,667.12`** | Immediate net dollar savings |

### B. Field Inspection Priority: Precision@K

| Capacity ($K$) | Baseline Precision@K | Champion Precision@K | Baseline TP Caught | Champion TP Caught |
|---|---|---|---|---|
| **Top 10** | `80.0%` | **`100.0%`** | 8 | **10** (100% precision) |
| **Top 50** | **`84.0%`** | `82.0%` | **42** | 41 |
| **Top 100** | `82.0%` | **`84.0%`** | 82 | **84** |
| **Top 500** | `63.2%` | **`76.6%`** | 316 | **383 (+13.4% precision)** |
| **Top 1,000** | `57.0%` | **`69.3%`** | 570 | **693 (+12.3% precision)** |
| **Top 2,000** | `51.4%` | **`61.8%`** | 1,029 | **1,235 (+10.4% precision)** |

### C. Running Imbalance Experiments

```bash
# Run complete Phase 5 pipeline: candidate training, validation selection, test evaluation, plots, MLflow
python scripts/run_imbalance.py all

# Customize validation metric or stride
python scripts/run_imbalance.py all --metric pr_auc --stride 30
```

### D. Generated Phase 5 Artifacts
- **Model Booster**: `artifacts/imbalance/champion_model.txt`
- **Test Predictions Parquet**: `artifacts/imbalance/champion_predictions.parquet`
- **Comparison JSON**: `artifacts/imbalance/imbalance_comparison.json`
- **Markdown Report**: `artifacts/imbalance/imbalance_comparison_report.md`
- **Detailed Documentation**: `docs/class_imbalance_strategies.md`
- **7 Publication-Grade Plots**: `artifacts/imbalance/figures/`
  (`pr_curves_comparison.png`, `roc_curves_comparison.png`, `precision_at_k_comparison.png`, `calibration_curves.png`, `probability_distributions_comparison.png`, `financial_loss_comparison.png`, `confusion_matrix_champion.png`)

---

## 14. Cost-Sensitive Custom Objective & Financially Weighted Learning (Phase 6)

Grid-Guard aligns tree-boosting splits directly with electricity utility economics through a custom second-order differentiable **Weighted Logistic Objective**:
$$\mathcal{L}_i(z_i) = w_i \left[ -y_i \ln(p_i) - (1 - y_i) \ln(1 - p_i) \right]$$
where $w_i = C_{FN, i}$ (annualized unmetered revenue leakage) for tampering examples and $w_i = C_{FP} = \$100.00$ (field dispatch cost) for honest accounts. The surrogate guarantees strictly positive Hessians ($h_i = w_i p_i(1 - p_i) > 0$) for numerical stability in LightGBM and scales weights globally via reference factor $S_{\text{ref}} = \$100.00$ without altering relative economic ratios.

### A. Three-Phase Performance Evolution (Held-Out Test Set)

| Metric | Phase 4 (Unweighted Baseline) | Phase 5 (Imbalance Champion) | Phase 6 (Cost-Sensitive Champion) | Shift (P4 $\to$ P6) | Economic Takeaway |
|---|---|---|---|---|---|
| **PR-AUC** | `0.2959` | `0.3132` | `0.2566` | `-0.0393` | Shifted toward financial volume rather than frequency |
| **ROC-AUC** | `0.7711` | `0.7693` | `0.7608` | `-0.0103` | Stable discriminative capacity |
| **Theft Recall** | `14.57%` | `23.84%` | `2.65%` | `-11.92%` | Conventional 0.5 threshold suppresses low-leakage cases |
| **Precision** | `46.89%` | `45.10%` | **`57.56%`** | **`+10.67%`** | **Nearly 6 out of 10 dispatched inspections confirm theft** |
| **False Positives ($FP$)** | `3,580` | `6,293` | **`424`** | **`-3,156`** | **-88.2% drop in wasted crew dispatches** |
| **Brier Calibration Score** | `0.0706` | `0.0811` | **`0.0704`** | **`-0.0002`** | Superior probability calibration |
| **Wasted FP Dispatch Cost** | `$358,000.00` | `$629,300.00` | **`$42,400.00`** | **`-$315,600.00`** | **$315.6k saved in wasted inspection dispatches** |
| **Undetected FN Leakage** | `$765,766.00` | `$490,798.88` | **`$583,798.88`** | **`-$181,967.12`** | High-volume theft prioritized |
| **Total Operational Loss** | **`$1,123,766.00`** | **`$1,120,098.88`** | **`$626,198.88`** | **`-$497,567.12`** | **-44.3% Net Financial Loss Reduction!** |

### B. Operational Inspection Ranking (Precision@K)

| Quota ($K$) | Phase 4 Precision@K | Phase 5 Precision@K | Phase 6 Precision@K | Phase 6 Confirmed Thefts |
|---|---|---|---|---|
| **Top 10** | 80.0% | **100.0%** | 90.0% | 9 |
| **Top 50** | **84.0%** | 82.0% | 74.0% | 37 |
| **Top 100** | 82.0% | **84.0%** | 77.0% | 77 |
| **Top 500** | 63.2% | **76.6%** | 61.2% | 306 |
| **Top 1,000** | 57.0% | **69.3%** | 57.5% | 575 |
| **Top 2,000** | 51.4% | **61.8%** | 50.9% | 1,018 |

### C. Running Cost-Sensitive Experiments

```bash
# Execute end-to-end Phase 6 pipeline: candidate training, validation selection, test evaluation, plots, MLflow
python scripts/run_cost_sensitive.py all

# Customize operational dispatch cost and normalization strategy
python scripts/run_cost_sensitive.py all --dispatch-cost 100.0 --tariff 0.15 --normalization dispatch_cost
```

### D. Generated Phase 6 Artifacts
- **Model Checkpoint**: `artifacts/cost_sensitive/champion_model.txt`
- **Scored Predictions**: `artifacts/cost_sensitive/champion_predictions.parquet`
- **Weight Audit Report**: `artifacts/cost_sensitive/weight_audit_report.json`
- **Comparison JSON**: `artifacts/cost_sensitive/cost_sensitive_comparison.json`
- **Markdown Report**: `artifacts/cost_sensitive/cost_sensitive_comparison_report.md`
- **Detailed Documentation**: `docs/cost_sensitive_learning.md`
- **Publication-Grade Diagnostic Plots**: `artifacts/cost_sensitive/figures/`
  (`expected_cost_curve.png`, `financial_weight_distribution.png`, `pr_curves_three_phase.png`, `financial_loss_three_phase.png`, `feature_importance_shift.png`, `confusion_matrix_cost_sensitive.png`)

---

## 15. Dynamic Thresholding, Expected Net Value & Inspection Prioritization (Phase 7)

Phase 7 transforms the Phase 6 cost-sensitive model outputs into a financially informed operational decision engine. Rather than using arbitrary global classification cutoffs (e.g., $p \ge 0.5$), Grid-Guard derives per-meter dynamic thresholds and computes **Expected Net Value (ENV)** to guide operational field crew dispatches.

### A. Mathematical Formulation

For meter $i$, with tamper probability $p_i$, estimated annual recoverable revenue $R_i$, and dispatch cost $C_{\text{dispatch}}$:

1. **Expected Net Value (ENV)**:
   $$\text{ENV}_i = p_i \times R_i - C_{\text{dispatch}}$$
   $$\text{Decision Rule: Inspect if } \text{ENV}_i > 0$$

2. **Bayes Cost Threshold ($\tau_{\text{cost}, i}$)**:
   Minimizes expected classification loss where $C_{FP} = C_{\text{dispatch}}$ and $C_{FN, i} = R_i$:
   $$\tau_{\text{cost}, i} = \frac{C_{\text{dispatch}}}{C_{\text{dispatch}} + C_{FN, i}}$$

3. **Direct ENV Economic Threshold ($\tau_{\text{env}, i}$)**:
   Guarantees non-negative expected net cash flow ($p_i \times R_i \ge C_{\text{dispatch}}$):
   $$\tau_{\text{env}, i} = \frac{C_{\text{dispatch}}}{R_i}$$

> [!NOTE]
> **Threshold Inequality**: For all valid economic parameters ($R_i = C_{FN, i} > 0, C_{\text{dispatch}} > 0$), $\tau_{\text{cost}, i} < \tau_{\text{env}, i}$. The Bayes cost threshold is slightly more permissive (minimizing aggregate risk), whereas the ENV threshold enforces positive expected cash flow per ticket.

### B. Three-Policy Operational Benchmark (42,372 Candidate Meters)

Evaluated on the held-out test evaluation period:

| Operational Metric | Policy A (Fixed $p \ge 0.5$) | Policy B (Bayes Cost $p \ge \tau_{\text{cost}}$) | Policy C (Dynamic ENV $\text{ENV} > 0$) | Economic Takeaway |
|---|---|---|---|---|
| **Dispatched Inspections** | `170` | `880` | **`801`** | Dynamic ENV filters out 79 loss-making dispatches |
| **Confirmed Thefts ($TP$)** | `79` | **`235`** | **`224`** | **+183.5% more thefts caught** than fixed 0.5 |
| **False Positives ($FP$)** | `91` | `645` | `577` | Operational trade-off to capture high-value theft |
| **Inspection Precision** | **`46.47%`** | `26.70%` | `27.97%` | Precision on broad financial coverage |
| **Theft Recall** | `2.62%` | **`7.78%`** | **`7.42%`** | Triple the recall of fixed thresholding |
| **Total Crew Dispatch Cost** | **`$17,000.00`** | `$88,000.00` | `$80,100.00` | $7.9k saved vs Bayes Cost |
| **Expected Net Value (ENV)** | `$223,120.42` | `$274,497.41` | **`$275,230.47`** | **Highest projected economic surplus** |
| **Realized Gross Recovery** | `$178,410.85` | `$248,422.29` | **`$244,853.20`** | **+$66.4k (+37.2%) revenue recovered** over fixed 0.5 |
| **Realized Net Recovery** | `$161,410.85` | `$160,422.29` | **`$164,753.20`** | **Highest net return after subtracting dispatch costs** |

### C. Top-K Ranked Inspection Queue (Capacity-Constrained Dispatch)

Meters are sorted deterministically by $\text{ENV}_i$ descending with secondary tie-breakers. Enforces strict capacity limits without dispatching negative-ENV candidates:

| Inspection Quota ($K$) | Target Dispatches | Confirmed Thefts | Precision@K | Cumulative Crew Cost | Realized Gross Recovery | Realized Net Value |
|---|---|---|---|---|---|---|
| **Top 10** | 10 | 6 | **60.0%** | $1,000.00 | $93,832.00 | **$92,832.00** |
| **Top 25** | 25 | 11 | **44.0%** | $2,500.00 | $116,913.00 | **$114,413.00** |
| **Top 50** | 50 | 23 | **46.0%** | $5,000.00 | $137,658.00 | **$132,658.00** |
| **Top 100** | 100 | 37 | **37.0%** | $10,000.00 | $155,887.00 | **$145,887.00** |
| **Top 250** | 250 | 92 | **36.8%** | $25,000.00 | $185,553.00 | **$160,553.00** |
| **Top 500** | 500 | 170 | **34.0%** | $50,000.00 | $223,164.00 | **$173,164.00** |
| **Top 801 (All Positive)** | 801 | 224 | **28.0%** | $80,100.00 | $244,853.20 | **$164,753.20** |

### D. Running the Decision Engine

```bash
# Execute end-to-end decision pipeline: thresholds, ENV, ranking, tickets, comparisons, plots, MLflow
python scripts/run_decision_engine.py all

# Customize dispatch capacity or operational rule
python scripts/run_decision_engine.py run --rule env_positive --max-inspections 500

# Run economic scenario sensitivity analysis
python scripts/run_decision_engine.py scenarios
```

### E. Generated Phase 7 Artifacts
- **Prioritized Tickets Parquet**: `artifacts/decision/inspection_tickets.parquet`
- **Prioritized Tickets CSV**: `artifacts/decision/inspection_tickets.csv`
- **Top 100 Operational Tickets**: `artifacts/decision/top_100_inspection_tickets.csv`
- **Policy Comparison JSON**: `artifacts/decision/decision_comparison.json`
- **Comprehensive Markdown Report**: `artifacts/decision/decision_comparison_report.md`
- **Detailed Documentation**: `docs/financial_decisioning.md`
- **5 Publication-Grade Visualizations**: `artifacts/decision/figures/`
  (`env_distribution.png`, `probability_vs_env.png`, `threshold_vs_financial_exposure.png`, `cumulative_env_by_rank.png`, `policy_comparison_bar.png`)

---

## 16. Upcoming Phases

- **Phase 8**: Explainable AI (TreeSHAP Feature Attribution, Waterfall Inspection Reports, Watermark Auditing).
- **Phase 9**: FastAPI Operational Decision Microservice (Real-time Scoring, Dynamic Dispatch Tickets).
- **Phase 10**: Interactive Streamlit / Web Operational Dashboard for Field Crew Operations.



