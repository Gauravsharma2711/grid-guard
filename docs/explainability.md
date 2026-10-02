# Grid-Guard Explainability & Behavioral Attribution Architecture

## 1. Executive Overview

Explainability in electricity theft and Non-Technical Loss (NTL) detection serves an operational imperative rather than merely a theoretical requirement. Utility inspection crews dispatched to rural or urban substations need transparent, defensible, and actionable justification before conducting physical meter audits.

Traditional black-box machine learning models output a single scalar probability ($p \in [0, 1]$), which fails to answer three critical field questions:
1. **Why was this customer flagged?** (Which specific consumption patterns drove the prediction?)
2. **When did the anomalous behavior begin?** (What is the relevant historical calendar interval?)
3. **What physical or behavioral signature does the telemetry exhibit?** (Did consumption drop abruptly, flatline, or record consecutive zero days?)

Grid-Guard Phase 8 solves this by providing a unified explainability framework combining:
* **Game-Theoretic Tree-SHAP Attributions**: Exact additive feature importance in the model's native log-odds space.
* **Non-Fabricated Temporal Attribution**: Explicit mapping of rolling statistics and lags to verified historical calendar intervals $[t_{\text{start}}, t_{\text{end}}]$.
* **Domain-Grounded Tampering Signatures**: Rule-based detection of structural load collapse, flatlines, zero streaks, and regime shifts independent of model weights.
* **Deterministic Human Narratives**: Concise (card-ready) and detailed technical reports with strict regulatory safety filters preventing unsupported legal claims.

---

## 2. Theoretical Formulation & SHAP Output Space

### A. Additive Tree-SHAP in Log-Odds Space
For tree-boosted models (LightGBM), Grid-Guard implements the Lundberg & Lee (2020) TreeExplainer algorithm. The explanation explains the model's native raw margin $z_i \in (-\infty, +\infty)$:

$$z_i = \ln\left( \frac{\hat{p}_i}{1 - \hat{p}_i} \right) = \mathbb{E}[z] + \sum_{j=1}^{M} \phi_{ij}$$

where:
* $\mathbb{E}[z] = -2.5928$ represents the base expected log-odds across the background distribution (corresponding to a base tampering prevalence of $\sim 6.96\%$).
* $\phi_{ij}$ is the Shapley value (marginal contribution) of feature $j$ for meter $i$.
* $M = 60$ engineered temporal features.

### B. Machine-Precision Additive Reconstruction
The Tree-SHAP implementation satisfies the local accuracy (additivity) property within machine precision:
$$\left| \mathbb{E}[z] + \sum_{j=1}^{60} \phi_{ij} - z_i \right| < 10^{-14}$$

### C. Relationship to Post-Hoc Probability Calibration
Grid-Guard explicitly distinguishes between:
1. **Raw Tree Margin ($z_i$)**: The direct sum of tree leaf outputs explained by Tree-SHAP.
2. **Uncalibrated Sigmoid Probability**: $\hat{p}_i = \sigma(z_i) = \frac{1}{1 + e^{-z_i}}$.
3. **Calibrated Operational Probability ($p_i^*$)**: Derived via validation-fitted Isotonic Regression ($p_i^* = f_{\text{iso}}(\hat{p}_i)$).

Tree-SHAP values explain the native tree margin $z_i$, which monotonically maps to $\hat{p}_i$. The system documents this relationship explicitly to preserve mathematical integrity.

---

## 3. Global Feature Importance Hierarchy

Ranked across the held-out test evaluation set by mean absolute SHAP value $\mathbb{E}[|\phi_j|]$:

| Rank | Feature Name | Display Name | Category | Mean(\|SHAP\|) | Operational Meaning |
|---|---|---|---|---|---|
| **1** | `imputation_ratio` | Imputed Data Ratio | Data Quality | `0.4056` | Verifies data integrity; confirms telemetry is measured rather than imputed |
| **2** | `missing_ratio` | Data Missingness Ratio | Data Quality | `0.2619` | Distinguishes telecom packet loss from customer-side tampering |
| **3** | `coverage_ratio` | Smart-Meter Data Coverage | Data Quality | `0.2437` | High coverage (>95%) rules out communication blackouts |
| **4** | `rolling_std_60d` | 60-Day Historical Volatility | Historical Baseline | `0.1406` | Primary benchmark for normal customer load variance and capacity |
| **5** | `rolling_std_90d` | 90-Day Seasonal Volatility | Historical Baseline | `0.1262` | Multi-month seasonal volatility benchmark |
| **6** | `rolling_std_30d` | 30-Day Trailing Volatility | Historical Baseline | `0.0795` | Monthly load dispersion benchmark |
| **7** | `rolling_min_30d` | Trailing 30-Day Min Load | Rolling | `0.0642` | Baseline non-zero base load |
| **8** | `ratio_14d_60d` | Recent vs. Historical Ratio | Collapse & Step-Down | `0.0397` | Direct measure of two-week consumption drop vs. long-term baseline |
| **9** | `sustained_drop_magnitude`| Consumption Collapse Deficit | Collapse & Step-Down | `0.0377` | Estimated absolute deficit (kWh/day) lost due to consumption drop |
| **10**| `rolling_max_30d` | Trailing 30-Day Peak Load | Rolling | `0.0286` | Historical peak capacity reference |

---

## 4. Non-Fabricated Temporal Attribution

A common failure mode in AI explainability is fabricating time windows (e.g. claiming "Week 12 caused theft" when only summary aggregations exist). Grid-Guard prevents this through an explicit, deterministic mapping between feature semantics and historical calendar windows:

* **Trailing Rolling Windows**:
  Given anchor date $t$ (e.g. `2016-10-30`):
  * `rolling_*_7d`: Trailing 7 days $[t - 6\text{d}, t]$ (`2016-10-24` to `2016-10-30`)
  * `rolling_*_14d`: Trailing 14 days $[t - 13\text{d}, t]$ (`2016-10-17` to `2016-10-30`)
  * `rolling_*_30d`: Trailing 30 days $[t - 29\text{d}, t]$ (`2016-10-01` to `2016-10-30`)
  * `rolling_*_60d`: Trailing 60 days $[t - 59\text{d}, t]$ (`2016-09-01` to `2016-10-30`)
  * `rolling_*_90d`: Trailing 90 days $[t - 89\text{d}, t]$ (`2016-08-02` to `2016-10-30`)
* **Lag Observations**:
  * `consumption_kwh_lag_30d`: Single reference day at $t - 30\text{d}$ (`2016-09-30`)
  * `consumption_kwh_lag_7d`: Single reference day at $t - 7\text{d}$ (`2016-10-23`)
* **Multi-Scale Comparison Intervals**:
  * `ratio_14d_60d`: Recent 14-day window $[t - 13\text{d}, t]$ compared against 60-day baseline $[t - 59\text{d}, t]$.
* **Active Streak Intervals**:
  * `current_zero_streak` ($k$ days): $[t - k + 1, t]$ consecutive zero-metered days.
  * `flatline_streak` ($k$ days): $[t - k + 1, t]$ consecutive near-constant consumption days.

---

## 5. Domain-Grounded Tampering Signatures

Independent of model feature weights, Grid-Guard runs rule-based pattern detectors to identify recognizable electrical anomaly signatures:

1. **Sustained Step-Down**:
   * *Criterion*: Recent consumption $< 50\%$ of historical baseline for $\ge 7$ consecutive days, or fractional drop $\ge 50\%$.
   * *Severity*: High ($\ge 70\%$ drop or $\ge 14$ days), Moderate ($\ge 50\%$ drop or $\ge 7$ days), Low ($\ge 35\%$ drop).
2. **Zero Streak**:
   * *Criterion*: Active streak of $\ge 3$ consecutive zero days, or $\ge 3$ zero days in trailing week.
   * *Severity*: High ($\ge 7$ consecutive zero days), Moderate ($\ge 3$ consecutive zero days).
3. **Flatline (Near-Zero Load Variance)**:
   * *Criterion*: Near-constant daily consumption for $\ge 7$ consecutive days ($|diff| \le 0.01$ kWh) or rolling CV $< 0.05$ with active load.
   * *Severity*: High ($\ge 14$ days or CV $< 0.01$), Moderate ($\ge 7$ days).
4. **Behavioral Regime Shift**:
   * *Criterion*: Trailing 7-day usage dropped by $> 55\%$ relative to 30-day baseline, or week-over-week contraction $> 50\%$.
   * *Severity*: Moderate.
5. **Abnormal Peak-to-Average Load (PAR)**:
   * *Criterion*: 7-day Peak-to-Average Ratio collapses to near-unity ($< 1.05$) while historical baseline exhibited normal peaking ($> 1.30$).
   * *Severity*: Low.

---

## 6. Regulatory Safety & Ethical Audit

Grid-Guard enforces automated linguistic safety auditing on every generated explanation:

### A. Forbidden Claims
The explanation engine programmatically rejects and forbids the following terms:
* `"bypass resistor"`, `"magnet"`, `"neutral line bypassed"` (physical mechanisms cannot be proven by smart meter data alone).
* `"customer is stealing"`, `"theft proven"`, `"guilty"`, `"criminal"`, `"prosecute"` (presumption of innocence; avoids legal exposure for utilities).

### B. Mandatory Standard Disclaimer
Every generated inspection ticket and report includes the following mandatory statement:
> *"Model evidence reflects statistical consumption anomalies and requires physical field verification; smart-meter data alone does not establish physical tampering or unauthorized abstraction."*

---

## 7. Canonical Case Studies

| Case Study | Ticket ID | Actual Label | Predicted Probability | Raw Log-Odds | Expected Net Value (ENV) | Primary Technical Insight |
|---|---|---|---|---|---|---|
| **True Positive (TP)** | `TCK-2016-10-30-EF550F26` | `1` | `1.000` | `+4.970` | `$32,275.68` | Severe week-over-week collapse contrasting high baseline volatility ($832.22$ kWh); confirmed high-volume theft. |
| **True Negative (TN)** | `TN-000395F8` | `0` | `0.080` | `-2.444` | *N/A* | Normal stable consumption with consistent weekly cycles; absence of collapse or flatline signatures. |
| **False Positive (FP)** | `TCK-2016-10-30-25152B5A` | `0` | `0.923` | `+4.219` | `$5,664.99` | Unmerited dispatch caused by customer structural vacancy or prolonged vacation; genuine consumption drop but honest account. |
| **False Negative (FN)** | `FN-FD2D487A` | `1` | `0.072` | `-2.552` | *N/A* | Low-amplitude partial theft where bypassed load was small enough to remain within natural customer variance bounds. |
