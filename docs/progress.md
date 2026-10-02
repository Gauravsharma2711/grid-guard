# Grid-Guard Project Progress Log

## Phase 1: Data Acquisition & Environment Setup

- **Status**: Completed / Operational
- **Completed Date**: 2026-10-02
- **Lead Implementation Engineer**: Antigravity Autonomous Agent

---

### Phase 1 Summary
- Pinned and isolated CPython 3.11.16 virtual environment with `uv`.
- Configured core dependencies: Polars, PyArrow, NumPy, SciPy, scikit-learn, LightGBM, MLflow, Pydantic.
- Built dataset-agnostic Polars ingestion engine and initial quality validator.
- Configured local MLflow experiment tracking.
- Created AMI data contract and GitHub Actions CI workflow.

---

## Phase 2: EDA, Data Cleaning & AMI Time-Series Understanding

- **Status**: Completed / Operational
- **Completed Date**: 2026-10-02
- **Lead Implementation Engineer**: Antigravity Autonomous Agent

---

### 1. Completed Items

- [x] **Comprehensive Raw Dataset Audit**:
  - Identified and ingested real-world dataset: State Grid Corporation of China (SGCC) Electricity Theft Benchmark (`data/raw/electric-data.csv`, 155.56 MB).
  - Detected 1,036 columns: `CONS_NO` (meter ID), 1,034 date columns spanning `2014-01-01` to `2016-10-31`, and `FLAG` (ground-truth tampering label).
  - Uncovered missing calendar date `2016-09-18` in raw headers (system-wide acquisition blackout).
  - Documented exact class distribution: 38,757 normal consumers (91.47%), 3,615 tampered consumers (8.53%), reflecting an imbalance of ~10.7 to 1.
- [x] **Time-Series Missingness & Quality Profiling (`grid_guard.data.profiling`)**:
  - Implemented `AMIProfiler` computing dataset-level and meter-level statistics natively in Polars.
  - Profiled 43,812,648 reading cells: 11,233,528 missing values (25.64%), 5,788,603 zero values (13.21%), and 0 negative readings.
  - Evaluated meter coverage quality tiers: Excellent ($\le 5\%$ null: 43.1%), Good ($5-20\%$ null: 6.4%), Partial ($20-50\%$ null: 24.1%), Sparse ($50-99\%$ null: 26.4%), and Empty ($100\%$ null: 5 meters).
  - Analyzed missing gap streaks: 74.8% of gaps are $\le 3$ days; 87.6% are $\le 7$ days; 5.1% are $> 30$ days.
- [x] **Deterministic Cleaning Pipeline (`grid_guard.data.cleaning`)**:
  - Implemented `AMICleaningPipeline` with zero raw data mutation.
  - Standardized column names to ISO `YYYY-MM-DD` and cast numeric readings to `Float64` / `Float32`.
  - Implemented localized bounded-gap temporal interpolation (linear interpolation for gaps $\le 3$ days, strictly bounded by valid readings).
  - Preserved long gaps ($> 3$ days) and prefix/suffix edge gaps as `null` without fabricating data.
  - Imputed 290,195 values (2.58% of missing data) across 34,912 meters while recording meter-level `imputation_ratio`.
  - Added quality indicator columns: `data_quality_status`, `coverage_ratio`, `missing_ratio`, and `imputation_ratio`.
- [x] **Canonical Parquet Outputs**:
  - Exported clean canonical wide Parquet: `data/processed/canonical_ami_clean.parquet` (77.6 MB).
  - Exported clean canonical long time-series Parquet: `data/processed/canonical_ami_series.parquet` (395.8 MB, 43,812,648 rows x 5 columns).
  - Preserved `.gitignore` isolation so large Parquet files are never tracked in Git.
- [x] **Data Lineage & Audit Reporting**:
  - Generated full provenance lineage record in `docs/eda/data_lineage.json`.
  - Generated comprehensive statistical profile in `docs/eda/dataset_profile.json`.
  - Generated formal audit markdown report in `docs/eda/eda_report.md` answering all 15 audit criteria.
- [x] **EDA Visualizations (`grid_guard.visualization.eda`)**:
  - Generated 5 high-resolution figures in `docs/eda/figures/`:
    - `fig1_dataset_overview.png`: Ground-truth class imbalance and coverage tiers.
    - `fig2_consumption_distribution.png`: Consumption density and meter-level mean distributions.
    - `fig3_missingness_and_gaps.png`: Meter missing ratio histogram and gap streak breakdown.
    - `fig4_time_series_profiles.png`: Observed 3-year trajectories of normal vs. tampered consumers.
    - `fig5_imputation_impact.png`: Demonstration of bounded interpolation on sample meters.
- [x] **CLI Automation**:
  - Built `scripts/run_eda_cleaning.py` supporting `--profile`, `--clean`, `--visualize`, and `--all`.
- [x] **Automated Testing Suite**:
  - Expanded test suite to 32 unit and integration tests with **90.17%** overall line coverage.

---

### 2. Validation Performed

1. **Ruff Quality Verification**: `ruff check .` and `ruff format --check .` passed cleanly with 0 errors across 35 files.
2. **Deterministic Test Suite**: `pytest --cov=grid_guard tests/` passed 32/32 tests in 10.69 seconds.
3. **Full Dataset Processing**: Successfully ran `scripts/run_eda_cleaning.py --action all` over the full 42,372 meters (43.8 million records) in 31 seconds.

---

### 3. Known Limitations (Phase 2 Scope Boundaries)

- Normalization and scaling across consumers are intentionally deferred to Phase 3 feature engineering.
- Feature extraction (rolling drops, consumption volatility, temporal Fourier features) belongs to Phase 3.
- Supervised LightGBM model training, cost matrices, and Expected Net Value (ENV) thresholding belong to Phases 4 and 5.

---

## Phase 3: Temporal Feature Engineering & Tampering Signature Extraction

- **Status**: Completed / Operational
- **Completed Date**: 2026-10-02
- **Lead Implementation Engineer**: Antigravity Autonomous Agent

### Summary
- Constructed 60 temporal and statistical features natively in Polars across 43,812,648 records.
- Feature extraction categories:
  - Trailing lags: 1d, 2d, 3d, 7d, 14d, 30d.
  - Multi-window rolling statistics: 7d, 14d, 30d, 60d, 90d (mean, std, min, max, median, CV, absolute difference).
  - Step-down ratios: 14d/60d, 30d/60d, 30d/90d.
  - Tampering signatures: zero streak length, zero ratios, abnormal drop severity.
  - Cyclical calendar features: day of week, day of month, month sine/cosine.
- Validated absence of future lookahead leakage (strict causal windows $\le t$).
- Exported model-ready dataset: `data/processed/canonical_features.parquet` (2,726.35 MB).

---

## Phase 4: Cost Matrix Definition & Unweighted Baseline Modeling

- **Status**: Completed / Operational
- **Completed Date**: 2026-10-02
- **Lead Implementation Engineer**: Antigravity Autonomous Agent

### 1. Completed Items
- [x] **Configurable Financial Framework (`grid_guard.evaluation.financial`)**:
  - Implemented `LeakageEstimator` computing per-meter daily deficit, monthly volume, and cumulative leakage cost ($C_{\text{FN}}$).
  - Implemented `FinancialCostEvaluator` tracking $C_{\text{dispatch}}$, wasted FP dispatch cost, undetected FN leakage cost, and net recovery.
  - Formalized strict 3-tier provenance separation (**Observed** vs. **Derived** vs. **Assumed**).
- [x] **Strictly Time-Aware Data Splitter (`grid_guard.models.splitting`)**:
  - Implemented non-overlapping chronological partitions:
    - Train: `2014-04-01` to `2015-12-31` (932,184 rows, 42,372 meters).
    - Validation: `2016-01-01` to `2016-05-31` (254,232 rows, 42,372 meters).
    - Held-out Test: `2016-06-01` to `2016-10-31` (254,232 rows, 42,372 meters).
  - Ensured strict exclusion of `tamper_label` / `FLAG` and `meter_id` from feature matrix $X$.
- [x] **Unweighted LightGBM Baseline Model (`grid_guard.models.baseline`)**:
  - Trained an ordinary unweighted LightGBM binary classifier on 932,184 samples across 60 features in 17 seconds.
  - Maintained conventional 0.5 decision threshold without class weights or cost weighting.
- [x] **Baseline Evaluation on Real Held-Out Test Set**:
  - **Statistical Metrics**:
    - Prevalence: `8.53%` (21,690 actual thefts vs. 232,542 normal).
    - PR-AUC: `0.2959` (vs. 0.0853 random baseline).
    - ROC-AUC: `0.7711`.
    - Precision: `46.89%` (3,161 TP, 3,580 FP).
    - Recall: `14.57%` (18,529 undetected thefts).
    - F1-Score: `0.2224`.
  - **Operational Ranking Metrics**:
    - Precision@10: `80.00%` (8 / 10).
    - Precision@50: `84.00%` (42 / 50).
    - Precision@100: `82.00%` (82 / 100).
    - Precision@500: `63.20%` (316 / 500).
    - Precision@1000: `57.00%` (570 / 1000).
    - Precision@2000: `51.45%` (1,029 / 2000).
  - **Financial Metrics (Base $C_{\text{dispatch}} = \$100$, Tariff = $\$0.15/\text{kWh}$)**:
    - Wasted FP Dispatch Cost: `USD 358,000.00`
    - Undetected FN Revenue Leakage: `USD 765,766.00`
    - Total Baseline Operational Loss: **`USD 1,123,766.00`**
    - Estimated Gross Recovery: `USD 1,447,265.25`
    - Estimated Net Recovery: `USD 773,165.25`
- [x] **Experiment Tracking & Artifact Generation (`grid_guard.tracking.experiment`)**:
  - Tracked parameters, scalar metrics, and visual artifacts to MLflow experiment `grid-guard-ntl-detection` (Run ID: `3ab6e61fd27a4c96b0c87cbed14dad80`).
  - Exported `artifacts/baseline/` containing `baseline_metrics.json`, `financial_cost_report.md`, `baseline_predictions.parquet`, `feature_importance_gain.csv`, and 7 figures.
- [x] **CLI Pipeline Script**:
  - Created `scripts/run_baseline.py` supporting `--stride`, `--dispatch-cost`, and `--tariff`.
- [x] **Test Suite & Verification**:
  - 57 automated unit, leakage audit, and pipeline integration tests passing with **88.88%** line coverage.
  - Ruff linting and formatting 100% clean across 68 files.

---

## Phase 5: Class Imbalance Strategy & Rare-Tampering Learning

- **Status**: Completed / Operational
- **Completed Date**: 2026-10-02
- **Lead Implementation Engineer**: Antigravity Autonomous Agent

### 1. Completed Items
- [x] **Ground-Truth Class Prevalence Audit**:
  - Measured exact training class distribution: 852,654 normal instances (91.47%) vs. 79,530 positive instances (8.53%), reflecting an imbalance ratio of **10.72 : 1**.
  - Documented target granularity (temporal observation snapshot for meter $m$ at time $t$ over causal trailing features $\le t$).
- [x] **Strict Leakage Prevention & Audit (`grid_guard.data.sampling`, `test_imbalance_leakage.py`)**:
  - Verified training-only class weighting and resampling. Validation (254,232 rows) and test (254,232 rows) remain 100% untouched.
  - Implemented 10-point leakage audit verifying absence of test mutations on training weights, absence of synthetic timestamps/meter IDs, and strict temporal boundary compliance.
- [x] **Candidate Imbalance Strategies Evaluated**:
  - Evaluated 8 candidate strategies across 4 paradigms on chronological validation partition (`2016-01-01` to `2016-05-31`):
    - `unweighted_baseline` ($w = 1.0$): Validation PR-AUC = 0.3035
    - Class Weighting Sensitivity Grid ($w \in \{2.0, 3.0, 5.0, 10.72\}$): Validation PR-AUC = 0.2262, 0.1630, 0.1760, 0.1292
    - Controlled Oversampling (`target_pos_ratio = 0.20`): Validation PR-AUC = **0.3131** (Winner!)
    - Controlled Undersampling (`target_pos_ratio = 0.33`): Validation PR-AUC = 0.3027
    - SMOTE ($k=5$, `target_pos_ratio = 0.20`): Validation PR-AUC = 0.2810
  - Completed technical suitability assessment documenting why vanilla SMOTE introduces synthetic boundary distortions on AMI consumption features.
- [x] **Validation Selection & Held-Out Test Evaluation**:
  - Champion strategy (`controlled_oversample_0.20`) selected strictly on validation PR-AUC.
  - Evaluated once on held-out test partition (`2016-06-01` to `2016-10-31`):
    - **PR-AUC**: Improved from `0.2959` to **`0.3132`** (`+0.0173`).
    - **Theft Recall**: Increased from `14.57%` to **`23.84%`** (**+9.27% absolute increase**, catching **2,009 more thieves**).
    - **Precision@10**: **100.0%** (vs. 80.0%).
    - **Precision@500**: **76.6%** (vs. 63.2%, +13.4% lift).
    - **Precision@1000**: **69.3%** (vs. 57.0%, +12.3% lift).
    - **Precision@2000**: **61.8%** (vs. 51.4%, +10.4% lift, catching 1,235 confirmed thefts).
    - **Financial Operational Loss**: Reduced to **`$1,120,098.88`** (saving **`$274,967.12`** in unrecovered theft leakage).
- [x] **Calibration & Reliability Analysis (`grid_guard.evaluation.calibration`)**:
  - Quantified calibration shift via Brier score (`0.0706` to `0.0811`) and ECE (`0.0239` to `0.0384`).
- [x] **MLflow Experiment Tracking & Visualizations**:
  - Logged run `imbalance_champion_controlled_oversample_0.20` to MLflow experiment `grid-guard-ntl-detection` (Run ID: `885ac4d64cfd404881af51940d89d628`).
  - Generated 7 publication-grade comparison plots in `artifacts/imbalance/figures/`.
  - Exported `artifacts/imbalance/imbalance_comparison_report.md` and `imbalance_comparison.json`.
- [x] **CLI & Test Suite**:
  - Built `scripts/run_imbalance.py` for automated reproduction.
  - Test suite expanded to 70 tests with **89.50%** code coverage.
  - Ruff formatting and linting 100% compliant.

---

### 2. Next Phase

- **Phase 6: Cost-Sensitive Optimization & Utility Objective Loss**
  - Implement asymmetric financial loss functions directly in gradient boosting, incorporating per-meter consumption volume, tariff structure, and dispatch cost into tree splits.

