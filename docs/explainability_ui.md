# Grid-Guard Explainability & Evidence Architecture (Phase 4)

**Status:** Phase 4 Complete  
**Date:** October 2026  
**Author:** Frontend Migration Engineer  
**Component:** `frontend/src/components/explainability/`  

---

## 1. Architectural Overview & Single Source of Truth

The Grid-Guard Explainability UI transforms complex gradient-boosted decision tree outputs into clear, calm, and actionable evidence for revenue protection operators and field technicians.

In strict compliance with `/designsystem.md` and Phase 4 requirements:
- **No Client-Side Recalculation:** The React frontend performs **zero mathematical recalculations** of SHAP attributions, feature normalizations, calibrated probabilities, recoverable leakage, or Expected Net Value. All metrics and explanations are deterministically sourced from the authoritative backend (`grid_guard.explainability.shap_engine` and `grid_guard.decision.policy`).
- **Restrained Visual Palette:** Explanatory attribution elements use the dedicated violet token (`--gg-evidence: #7d6db2`, `--gg-evidence-bg: #f4f2f9`) strictly reserved for model evidence.
- **Progressive Disclosure:** Operators are presented first with high-level diagnostic narratives and top drivers, with deep-dive technical attributions and tabular data accessible via on-demand toggles.
- **Forensic Tone & Safe Framing:** Evidence is consistently described as *model attributions and consumption signatures indicating anomalous behavior*, explicitly stating that on-site physical verification is mandatory. The UI never asserts physical tampering or fraud without field confirmation.

---

## 2. SHAP Attribution Presentation (`ShapContributionPanel`)

### 2.1 Output-Space Semantics: Log-Odds Margin ($\Delta z$)
The underlying Champion model (`CostSensitivePipeline` using LightGBM/XGBoost) produces predictions in margin space:
$$z_i = \ln\left(\frac{p_i}{1 - p_i}\right)$$
Tree-SHAP attributions represent additive shifts in log-odds space around the global dataset base expectation:
$$\mathbb{E}[z] = -2.3713 \quad (\text{corresponding to baseline tampering rate } p \approx 0.085)$$

The UI honors this mathematical property explicitly:
- SHAP values are labeled in margin units: $\Delta z$ (e.g., `+2.4900 Δz` or `-0.3500 Δz`).
- Semantics banners clearly state: *Feature attribution values represent additive shifts in margin score space ($z = \ln(p/(1-p))$), not direct percentage changes in probability.*
- Positive attributions ($\Delta z > 0$) are categorized as **Risk Drivers** pushing prediction toward higher tampering suspicion.
- Negative attributions ($\Delta z < 0$) are categorized as **Mitigating Factors** moderating the risk prediction.

### 2.2 Feature Name Mapping & Categorization
Internal feature names are mapped directly from the Phase 3 / Phase 8 feature registry (`FEATURE_NAME_MAP` and `FEATURE_CATEGORY_MAP`):
- `rolling_std_60d` $\rightarrow$ **60-Day Historical Volatility** (Historical Baseline)
- `missing_ratio` $\rightarrow$ **Data Missingness Ratio** (Data Quality)
- `rolling_mean_7d` $\rightarrow$ **7-Day Trailing Average** (Recent Consumption)
- `ratio_14d_60d` $\rightarrow$ **Recent vs. Historical Consumption Ratio** (Temporal Shift)
- `zero_reading_count_30d` $\rightarrow$ **30-Day Zero Consumption Count** (Electrical Signature)

Unregistered features gracefully fallback to clean title-cased labels while preserving the raw internal identifier in monospace metadata.

### 2.3 Dual-Mode Presentation: Visual Bar & Accessible Table
- **Visual Bar Mode:** Horizontal contribution bars scaled proportionally against the maximum absolute attribution. Positive drivers display violet bars extending right; mitigating factors display muted slate bars extending left.
- **Accessible Table Mode:** Keyboard-navigable table (`<table aria-label="Feature SHAP attributions table">`) detailing Rank, Feature Name, Category, Direction badge, Observed Value, Baseline Reference Value, and Exact Attribution ($\Delta z$).

---

## 3. Temporal Evidence (`TemporalEvidencePanel`)

Temporal evidence anchors model feature attributions to concrete, calendar-dated observation windows:
- **Calendar Bounds:** Explicit display of `source_window_start` through `source_window_end` (e.g., `2016-09-01` to `2016-10-30`). The UI never invents week numbers or anomaly durations.
- **Observed vs. Baseline Readings:** Side-by-side presentation of the actual meter consumption and the expected historical baseline (e.g., Observed `2.15 kWh/day` vs. Reference `16.40 kWh/day`).
- **Relative Deviation:** Formatted percentage difference (e.g., `-86.9%`).
- **Forensic Interpretation:** Narrative context provided directly by the backend explanation engine.
- **Chart Interactive Link:** Clicking "Highlight Interval on Chart" triggers the time-series chart window marker for immediate visual cross-examination.
- **Honest Missing State:** If temporal interval mappings are unavailable for a particular feature, the panel explicitly clarifies: *"Exact source calendar interval not provided by telemetry service."*

---

## 4. Electrical Tampering Signatures (`TamperingSignaturesPanel`)

Rule-based and behavioral electrical tampering signatures evaluated during Phase 8 are surfaced with calibrated severity badges:
1. **Sustained Step-Down:** Detects abrupt, permanent reductions in daily consumption (Magnitude: % drop, Duration: days).
2. **Behavioral Regime Shift:** Detects structural shifts in load profile variance and peak timing.
3. **Unusual Flatline:** Detects invariant non-zero daily load anomalies.
4. **Extended Zero Streak:** Identifies sustained zeroes in active commercial accounts.

**Operational Safety Caveat:** Every signature panel includes a mandatory warning:  
> *"Detected electrical signatures indicate automated heuristic rule flags. They do not constitute legal or physical proof of meter bypass; dispatch confirmation is required."*

---

## 5. Counter-Evidence & Mitigating Factors (`CounterEvidencePanel`)

To maintain objectivity and prevent confirmation bias:
- **Negative Attributions:** Displays all features exerting downward pressure on risk score.
- **Mitigating Summaries:** Details seasonal factors, peer feeder consumption alignment, or telemetry dropouts that could explain consumption drops without illicit activity.
- **Honest Absence State:** When no mitigating factors are present, the UI states: *"No counter-evidence supplied by explanation engine for this evaluation period."* (Distinguishing absence of evidence from evidence of absence).

---

## 6. Financial Decision Context (`DecisionContextPanel`)

Connects machine-learning risk probability to operational dispatch decisioning:
- **Calibrated Risk ($p_i$):** Calibrated isotonic probability of non-technical loss.
- **Estimated Recoverable Leakage:** Physical kWh estimated loss over the exposure period.
- **Expected Gross Recovery ($p_i R_i$):** Expected financial yield before dispatch cost.
- **Crew Dispatch Cost ($C_{\text{dispatch}}$):** Standardized crew inspection cost (₹100.00).
- **Expected Net Value ($ENV_i = p_i R_i - C_{\text{dispatch}}$):** Primary objective function.
- **Decision Rule Comparison:**
  - **Dynamic ENV Rule ($\tau_{\text{ENV}, i} = C_{\text{dispatch}} / R_i$):** Active Champion rule.
  - **Bayes Cost Threshold ($\tau_{\text{cost}, i} = C_{\text{dispatch}} / (C_{\text{dispatch}} + C_{\text{FN}, i})$):** Classical cost-sensitive threshold.
  - **Fixed Cutoff ($\tau = 0.50$):** Uncalibrated baseline cutoff.
