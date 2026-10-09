# Grid-Guard Operational Dashboard & FastAPI Integration (Phase 3)

**Status:** Phase 3 Complete  
**Date:** October 2026  
**Author:** Frontend Migration Engineer  
**Component:** `frontend/` (React + TypeScript + Vite)  

---

## 1. Executive Summary

Phase 3 transitions the Grid-Guard user interface from a component library into a fully functional operational revenue protection suite. The new application integrates directly with the live FastAPI service (`src/grid_guard/api/main.py`) and validated machine learning artifacts generated in Phases 4–8.

All screens strictly adhere to `/designsystem.md` ("Calm Proof Flow"), avoiding arbitrary SaaS dashboards, animations, gradients, or permanent sidebars.

---

## 2. Implemented Screens & Workflows

### 2.1 Overview Screen (`/#overview`)
- **Purpose:** Answers *"What needs immediate attention, and what is the expected financial recovery?"*
- **Hero Banner:** Displays network-wide Expected Net Value (ENV) with an `ENV > 0 Economically Justified` badge and active policy citation (`Dynamic ENV Rule (Champion)`).
- **KPI Summary Strip:**
  - Monitored Fleet: 42,372 meters.
  - Recommended Tickets: 801 (1.89% network inspection rate).
  - Projected Gross Recovery: ₹3,55,330.47.
  - Crew Dispatch Cost: ₹80,100.00.
- **System Health Card:** Probes active model checkpoint, input feature count (60 causal features), and SHAP explainer readiness.
- **Top Priority Inspection Preview:** Renders top 5 candidate work orders ranked strictly by Expected Net Value descending.

### 2.2 Inspection Queue Screen (`/#queue`)
- **Purpose:** Field dispatch prioritization and work order management.
- **Controls & Filters:**
  - Client-side meter ID and feeder/neighborhood search.
  - Min ENV threshold filter (`ENV >= ₹X`).
  - Risk probability cutoffs (0%+, 50%+, 75%+, 90%+).
  - Crew capacity limits (25, 50, 100 tickets).
- **Candidate Data Table:**
  - Columns: Rank, Meter ID, Tamper Probability (with risk badge), Projected Recovery, Dispatch Cost, Expected Net Value (`EnvMetric`), Anomaly Signatures, Data Quality status, and Detail action.
- **Inspection Ticket Drawer:**
  - Slide-out drawer opened upon clicking any table row.
  - Displays calibrated risk, financial assessment breakdown, detected anomaly signatures, and forensic audit narrative.
  - One-click handoff to Meter Analysis workbench (`Analyze Meter in Workbench`).

### 2.3 Meter Analysis Screen (`/#meter`)
- **Purpose:** Deep-dive diagnostic workbench for an individual smart meter.
- **Preset Selector:** Realistic test cases sourced from validated project artifacts (`SAMPLE_METER_PRESETS`):
  - Suspicious Step-Down (Sustained Tampering).
  - Normal Residential Consumer (Low Risk).
  - High-Value Commercial Consumer (High Exposure).
  - Short History / Data Quality Deficiency.
- **Time-Series Chart (`TimeSeriesChart`):**
  - Custom SVG line chart plotting daily consumption (kWh) over time.
  - Reference baseline comparison line.
  - Highlighted anomaly window marker.
  - Responsive coordinate mapping, crosshair tooltips, statistical summary bar, and accessible `<details>` data table.
- **Data Quality Alerts:** Telemetry coverage ratio, missing reading flags, and explicit data-quality explanations.
- **Financial Assessment & Signatures:** Sits directly alongside the time-series without clutter.

### 2.4 Model Insights Screen (`/#insights`)
- **Purpose:** Empirical model validation and economic policy evaluation.
- **Champion Checkpoint Surface:** Live introspection of booster type (`LightGBM Booster`), objective (`financially_weighted_logistic`), feature count (60), and base log-odds (-2.3713).
- **Tabbed Analytical Views:**
  1. *Decision Policies (Phase 7):* Compares static 50% cutoff, Bayes cost threshold, and dynamic ENV rule across 42,372 held-out meters.
  2. *Model Progression (Phases 4–6):* Monotonic PR-AUC, ROC-AUC, and Precision@K progression from unweighted baseline to cost-sensitive champion.
  3. *Top-K Precision Trade-Off:* Cumulative financial recovery and precision across Top 10, 25, 50, and 100 queue depth.

### 2.5 System Status Screen (`/#system`)
- **Purpose:** Infrastructure and API verification.
- **Live Status Cards:** FastAPI readiness (`/ready`), health (`/health`), model metadata, and public configuration.

---

## 3. API Integration Contract Mapping

| Frontend Feature | HTTP Method | Path | Backend Contract / Pydantic Schema | Source Priority |
|---|---|---|---|---|
| System Readiness Probe | `GET` | `/ready` | `ReadyResponse` | Live FastAPI |
| System Health Ping | `GET` | `/health` | `HealthResponse` | Live FastAPI |
| Model Metadata Probe | `GET` | `/api/v1/metadata/model` | `ModelMetadataResponse` | Live FastAPI |
| Public Configuration | `GET` | `/api/v1/metadata/config` | `PublicConfigResponse` | Live FastAPI |
| Inspection Queue Feed | `POST` | `/api/v1/inspection/queue` | `InspectionQueueRequest` → `InspectionQueueResponse` | Live FastAPI |
| Single Meter Predict | `POST` | `/api/v1/predict` | `SingleMeterPredictionRequest` → `SingleMeterPredictionResponse` | Live FastAPI |
| Policy Comparison | — | Offline Artifact | `artifacts/decision/decision_comparison.json` | Validated Project Artifact |
| Model Evolution | — | Offline Artifact | `artifacts/cost_sensitive/cost_sensitive_comparison.json` | Validated Project Artifact |
| Sample Meter Presets | — | Offline Artifact | `artifacts/api/sample_requests.json` | Validated Project Artifact |

---

## 4. Financial & Decision Integrity Safeguards

1. **No Frontend ENV Recalculation:** The React application never calculates Expected Net Value or prioritizes records using a frontend formula. The backend decision engine (`grid_guard.decision`) remains the sole authority.
2. **Distinct Financial Concepts:**
   - *Probability* = Calibrated statistical likelihood of tampering.
   - *Estimated Recovery* = Gross financial volume at risk.
   - *Dispatch Cost* = Cost of crew vehicle, labor, and metering equipment.
   - *Expected Net Value (ENV)* = Expected economic benefit ($ENV = p \cdot R - C$).
3. **No Synthetic Zero Substitution:** Missing telemetry or financial values are rendered honestly as `Not available` or `—`, never substituted as `₹0`.
4. **Currency Localization:** Formatted in Indian Rupees (`₹`) in compliance with system-wide utility configuration.

---

## 5. Verification & Test Suite Summary (Phase 4 Baseline)

### Frontend Verification (`frontend/`)
- **Unit & Integration Tests:** 104 tests passing across 27 test files (`npm run test`).
- **TypeScript Typecheck:** 0 errors (`tsc --noEmit`).
- **ESLint Cleanliness:** 0 warnings/errors (`eslint .`).
- **Production Build:** Succeeded (`dist/assets/index-l1nBnwWN.js` 262.07 kB, gzip: 74.75 kB).
- **Inspection & Explainability Workflows:** Verified end-to-end user journey (Queue -> Drawer -> Full Ticket -> Workbench -> Export).

### Backend Verification (Repository Root)
- **Pytest Suite:** 162 tests passing (`uv run pytest -q`, 100% passing).
- **Ruff Linter:** 0 errors (`uv run ruff check .`).
- **API Runtime:** Verified live responses from `grid_guard.api.app:app`.
- **Legacy Streamlit:** Fully operational and intact (`src/grid_guard/dashboard/app.py`).

---

## 6. Phase 4 Accomplishments & Phase 5 Boundary

Phase 4 successfully implemented:
- Full local Tree-SHAP attributions in log-odds margin space with feature name registry mapping.
- Source calendar temporal evidence intervals, observed vs reference readings, and interactive chart highlight integration.
- Electrical tampering signatures (sustained step-downs, behavioral regime shifts) with calibrated severity status.
- Objective counter-evidence and mitigating factor presentations.
- Economic decision context comparing Dynamic ENV, Bayes cost thresholds, and fixed cutoffs.
- Full forensic field inspection work order ticket view (`InspectionTicketView`).
- Export utilities: JSON for full ticket document and RFC 4180 CSV for inspection queues.

The boundary for Phase 5 (Final Release & Migration) includes:
- Comprehensive multi-browser end-to-end regression testing.
- Migration validation and formal Streamlit retirement plan.
- Production deployment packaging and final release sign-off.
