# Grid-Guard System Architecture

This document describes the software architecture, design principles, component interfaces, and operational boundaries of the **Grid-Guard** electricity theft and non-technical loss (NTL) detection platform.

---

## 1. High-Level Architecture Diagram

```
                                  USER / OPERATOR
                                         │
                                         ▼
                     ┌───────────────────────────────────────┐
                     │     Streamlit Operational Dashboard   │
                     │  (Overview, Queue, Analysis, Insights)│
                     └───────────────────┬───────────────────┘
                                         │  HTTP / REST (JSON)
                                         ▼
                     ┌───────────────────────────────────────┐
                     │        FastAPI Backend Boundary       │
                     │  (/health, /ready, /predict, /tickets)│
                     └───────────────────┬───────────────────┘
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        ▼                                ▼                                ▼
┌─────────────────┐            ┌───────────────────┐            ┌───────────────────┐
│ FeaturePipeline │            │ InferenceService  │            │ Explainability    │
│  (60 Features)  │            │(LightGBM Booster) │            │ (Tree-SHAP & Sigs)│
└─────────────────┘            └───────────────────┘            └───────────────────┘
        │                                │                                │
        └────────────────────────────────┼────────────────────────────────┘
                                         │
                                         ▼
                     ┌───────────────────────────────────────┐
                     │      Dynamic Financial Decision Engine│
                     │ (Leakage, Recovery, Breakeven tau, ENV)│
                     └───────────────────────────────────────┘
```

---

## 2. Core Architectural Principles

### 2.1 The API is the Strict Application Boundary
The Streamlit dashboard does **NOT** import LightGBM, Pandas training pipelines, or SHAP explainer modules directly. It interacts solely with the backend via `DashboardApiClient`, ensuring that business rules, financial logic, and model execution remain centralized in the FastAPI service.

### 2.2 Strict Temporal Integrity
All feature extraction, historical baselining, and validation partitions respect the arrow of time:
- No future readings leak into rolling averages.
- Train, validation, and test splits are partitioned chronologically.

### 2.3 Financial Stakes Over Pure Statistical Metrics
Traditional ML systems optimize purely for statistical metrics like F1-score or Accuracy. Grid-Guard embeds financial cost awareness directly into:
1. **Model Training**: Sample weights scaled by financial leakage consequences.
2. **Decision Making**: Expected Net Value (ENV) cutoff ensures that every dispatched crew generates positive expected utility:
   $$\text{ENV}_i = p_i \times R_i - C_{\text{dispatch}} > 0$$

### 2.4 Transparent, Audited Explainability
Every high-probability prediction must be defensible to utility field crews:
- Exact Tree-SHAP local attributions.
- Domain-verified electrical signatures (e.g. sustained drop, flatline, zero streak).
- Non-accusatory operational language adhering to regulatory guidelines.

---

## 3. Subsystem Breakdown

### 3.1 Data Cleaning & Ingestion (`grid_guard.data`)
- Normalizes raw AMI consumption time-series.
- Handles missing readings via forward imputation and linear interpolation.
- Rejects corrupt or invalid readings (NaN, Inf, negative consumption).

### 3.2 Temporal Feature Engineering (`grid_guard.features`)
- Computes 60 canonical features across multiple rolling time horizons (7d, 14d, 30d, 60d, 90d, 180d).
- Captures consumption volume, ratios against baseline, temporal variability, weekend vs. weekday habits, and anomaly duration.

### 3.3 Cost-Sensitive Learning (`grid_guard.models`)
- LightGBM gradient boosted decision tree classifier.
- Financially weighted log-loss objective function assigns sample weights proportional to estimated revenue exposure.

### 3.4 Financial Decision Engine (`grid_guard.decision`, `grid_guard.evaluation`)
- Models unmetered energy loss ($\text{kWh}$), tariff multipliers, and revenue recovery factors.
- Calculates dynamic thresholds ($\tau_{\text{cost}}, \tau_{\text{env}}$).
- Prioritizes work order tickets into a ranked queue ordered by ENV descending.

### 3.5 Explainability & Narratives (`grid_guard.explainability`)
- `ShapExplainer`: Computes exact local Shapley values using Tree-SHAP.
- `TamperingSignatureDetector`: Evaluates domain heuristic patterns.
- `NarrativeGenerator`: Translates numerical attributions into human-readable field summaries and counter-evidence.

### 3.6 Production API (`grid_guard.api`)
- Fast, non-blocking asynchronous REST interface built with FastAPI.
- Validates request/response contracts using Pydantic V2 models.
- Lifespan pinning ensures sub-30ms P95 latency.

### 3.7 Operational Dashboard (`grid_guard.dashboard`)
- Built with Streamlit for operational data analysis.
- 5 comprehensive views: Fleet Overview, Inspection Queue, Meter Analysis, Model Insights, and System Status.
- Visualizations built with Matplotlib for publication-grade precision.
