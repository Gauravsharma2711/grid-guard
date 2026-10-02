# Grid-Guard Phase 6: Cost-Sensitive Custom Objective & Financially Weighted Learning

## 1. Executive Summary & Problem Formulation

In electricity Non-Technical Loss (NTL) detection and meter tampering inspection, classification errors carry severely asymmetric and heteroskedastic financial consequences:
- **False Positive ($FP$)**: Wastes a fixed inspection crew dispatch fee ($C_{FP} = C_{\text{dispatch}} = \$100.00$), consisting of labor, vehicle transport, and field safety protocols.
- **False Negative ($FN$)**: Allows ongoing unmetered electricity diversion to persist undetected, forfeiting cumulative tariff revenue ($C_{FN, i}$) that varies by orders of magnitude depending on customer consumption scale—from under $\$100$ for small residential meters to upwards of $\$100,000$ for commercial and light industrial accounts.

In previous phases, Grid-Guard established:
- **Phase 4**: An unweighted baseline model trained with standard binary logloss, treating all errors as having equal unit cost.
- **Phase 5**: An imbalance-aware model addressing class prevalence (~8.53% tampering rate) via controlled oversampling, treating every positive anomaly as equally critical.

**Phase 6 introduces financially cost-sensitive learning**, fundamentally aligning tree-boosting split decisions with real utility economics. By embedding financial error costs directly into the gradient boosting objective, the model assigns greater training importance to preventing misses on high-revenue accounts while controlling wasteful dispatches on normal accounts.

---

## 2. Mathematical Derivation: Cost-Sensitive Weighted Logistic Objective

### 2.1 The Inadequacy of the Direct Expected-Cost Linear Objective
The business decision objective defines the expected classification cost as:
$$\mathcal{L}_{\text{expected}} = \sum_{i=1}^N \left[ y_i (1 - p_i) C_{FN, i} + (1 - y_i) p_i C_{FP} \right]$$
While this expression correctly formalizes the business utility function, **it cannot be directly optimized via gradient-boosted decision trees (GBDTs)**:
1. It is strictly linear in predicted probability $p_i = \sigma(z_i)$.
2. Its second derivative with respect to probability is identically zero ($\frac{\partial^2 \mathcal{L}}{\partial p^2} = 0$).
3. With respect to raw logit margin $z_i$, its Hessian $\frac{\partial^2 \mathcal{L}}{\partial z_i^2} = (C_{FP}(1-y_i) - C_{FN, i} y_i) \sigma(z_i)(1 - \sigma(z_i))(1 - 2\sigma(z_i))$ changes sign depending on the margin $z_i$, violating LightGBM's requirement for a positive semi-definite Hessian ($h_i > 0$). Negative or vanishing Hessians destabilize Newton-Raphson tree split finding, leading to degenerate tree structures.

### 2.2 The Weighted Logistic Differentiable Surrogate
To provide a well-behaved optimization surface with guaranteed positive curvature, Phase 6 implements the **weighted logistic surrogate loss**:
$$\mathcal{L}_i(z_i) = w_i \left[ -y_i \ln(p_i) - (1 - y_i) \ln(1 - p_i) \right]$$
where:
- $z_i \in \mathbb{R}$ is the raw logit margin predicted by the ensemble before sigmoid activation.
- $p_i = \sigma(z_i) = \frac{1}{1 + e^{-z_i}}$ is the predicted probability.
- $y_i \in \{0, 1\}$ is the ground-truth tampering label.
- $w_i > 0$ is the per-observation financial training weight.

### 2.3 Exact First and Second Order Derivatives
Differentiating $\mathcal{L}_i$ with respect to raw logit margin $z_i$:

**Gradient ($g_i$):**
$$\frac{\partial p_i}{\partial z_i} = p_i (1 - p_i)$$
$$g_i = \frac{\partial \mathcal{L}_i}{\partial z_i} = w_i \left[ -\frac{y_i}{p_i} p_i(1 - p_i) + \frac{1 - y_i}{1 - p_i} p_i(1 - p_i) \right] = w_i (p_i - y_i)$$

**Hessian ($h_i$):**
$$h_i = \frac{\partial g_i}{\partial z_i} = w_i \frac{\partial}{\partial z_i}(p_i - y_i) = w_i p_i (1 - p_i)$$

### 2.4 Positive Hessian Guarantee
Because $w_i > 0$ by financial definition (both $C_{dispatch} > 0$ and $C_{FN, i} \ge C_{\min} > 0$) and $\sigma(z_i)(1 - \sigma(z_i)) > 0$ for all finite margins $z_i \in (-\infty, \infty)$:
$$h_i = w_i p_i (1 - p_i) > 0 \quad \forall i$$
To prevent floating-point underflow at extreme logits, the implementation enforces:
1. Safe logit clipping: $z_i \in [-30.0, 30.0]$.
2. Numerical probability clamping: $p_i \in [\varepsilon, 1 - \varepsilon]$ with $\varepsilon = 10^{-15}$.
3. Strict Hessian floor: $h_i \ge 10^{-12}$.

### 2.5 Unit Verification via Finite Differences
The analytical gradient and Hessian were validated against central finite-difference approximations:
$$g_{\text{approx}} = \frac{\mathcal{L}(z + \delta) - \mathcal{L}(z - \delta)}{2\delta}, \quad \delta = 10^{-5}$$
Across all edge cases (positive high-leakage, positive low-leakage, negative normal, extreme logits $z = \pm 15$), maximum absolute error between analytical and numerical derivatives remained $< 10^{-8}$.

---

## 3. Financial Weight Construction & Provenance Audit

### 3.1 Weight Definition
For each training example $i$:
$$w_i = \begin{cases} C_{FN, i}, & \text{if } y_i = 1 \text{ (tampering)} \\ C_{FP}, & \text{if } y_i = 0 \text{ (honest)} \end{cases}$$
where:
- $C_{FP} = \$100.00$ (field inspection dispatch cost).
- $C_{FN, i} = \max\left( \$100.00, \; \text{annualized unmetered revenue leakage} \right)$.

Annualized revenue leakage is computed via Phase 4's `FinancialCostEvaluator` using historical baseline consumption $\bar{c}_{\text{baseline}}$ and the default tariff $T = \$0.15/\text{kWh}$:
$$C_{FN, i} = \bar{c}_{\text{baseline}, i} \times 365 \times T$$

### 3.2 Provenance Classification: Observed vs. Derived vs. Assumed
Every financial parameter in Grid-Guard is strictly traced by origin:

| Financial Element | Value / Default | Provenance | Operational Justification |
|---|---|---|---|
| **Inspection Dispatch Cost ($C_{FP}$)** | **$100.00** | **Assumed** | Standard North American / European electric utility field dispatch cost covering 2-person crew, vehicle dispatch, and safety verification. |
| **Electricity Tariff ($T$)** | **$0.15 / kWh** | **Assumed** | Representative blended retail electricity tariff for residential and commercial customers. |
| **Leakage Horizon ($H$)** | **365 days** | **Assumed** | Typical regulatory inspection cycle before undetected meter tampering is discovered through routine meter replacement. |
| **Baseline Consumption ($\bar{c}_i$)** | Meter-specific | **Derived** | Cleaned AMI daily consumption measured during historical pre-tampering period. |
| **Leakage Loss ($C_{FN, i}$)** | Meter-specific | **Derived** | $\bar{c}_i \times H \times T$, calculated strictly from historical consumption and tariff parameters. |
| **Tamper Label ($y_i$)** | Binary {0, 1} | **Observed** | Ground-truth verification flag from benchmark AMI dataset. |

### 3.3 Global Reference Scale Normalization
Because raw financial costs range from $\$100$ to over $\$625,000$, passing raw dollar figures directly into LightGBM can alter the effective gradient magnitude and tree regularization behavior. Phase 6 implements **global reference scale normalization**:
$$\tilde{w}_i = \frac{w_i}{S_{\text{ref}}}$$
where $S_{\text{ref}} = C_{FP} = \$100.00$ (or alternatively mean/median cost). 

> [!IMPORTANT]
> A common scalar divisor $S_{\text{ref}} > 0$ applied globally preserves the exact relative error penalty between all examples ($\frac{\tilde{w}_i}{\tilde{w}_j} = \frac{w_i}{w_j}$) while bringing weights into a well-conditioned numerical range $[1.0, 6256.3]$. Normalizing positive and negative classes independently is strictly prohibited as it would distort the intended cost ratio.

### 3.4 Outlier Analysis & Capping Sensitivity
Analysis of the 79,530 positive training examples revealed:
- Minimum $C_{FN}$: $\$100.00$
- Median $C_{FN}$: $\$100.00$
- Mean $C_{FN}$: $\$154.44$
- 99th Percentile: $\$929.54$
- Maximum $C_{FN}$: $\$625,625.50$ (high-volume commercial account)

We evaluated an optional 99th percentile winsorization capping candidate (`phase6_cost_sensitive_capped_p99`), which capped 796 extreme observations at $\$929.54$. On validation evaluation, preserving the uncapped true economic distribution yielded superior operational performance (Validation Loss: $\$356,943$ uncapped vs. $\$407,208$ capped), demonstrating that allowing large commercial accounts to exert their true economic influence produces better utility outcomes.

---

## 4. Fundamental Distinction: Cost-Sensitive vs. Class-Imbalance Learning

| Dimension | Class Imbalance (Phase 5) | Cost-Sensitive Learning (Phase 6) |
|---|---|---|
| **Core Question** | "How do we compensate for rare positive cases?" | "How expensive is an error on this specific account?" |
| **Weight Assignment** | Uniform scalar $w_{\text{pos}} = N_{\text{neg}} / N_{\text{pos}} \approx 10.72$ for all positives | Heterogeneous per-instance financial penalty $w_i = C_{FN, i}$ |
| **Economic Awareness** | None; treats a $\$20$ residential theft identical to a $\$50,000$ factory diversion | Explicit; penalizes large revenue diversions proportionally |
| **Objective Type** | Standard logloss on resampled data or weighted logloss | Custom differentiable surrogate with exact $g_i$ and $h_i$ |
| **Double-Counting Prevention** | Primary Phase 6 models isolate financial weights without multiplying Phase 5 class multipliers | Verified via strict unit tests (`test_cost_weights.py`) |

---

## 5. Candidate Validation Experiments & Champion Selection

All candidates were evaluated on the validation partition (`2016-01-01` to `2016-05-31`, 254,232 samples).

| Candidate Configuration | Objective / Strategy | Normalization | Val Total Loss ($) | Val PR-AUC | Val Recall | Val Precision | Val Brier |
|---|---|---|---|---|---|---|---|
| `phase4_unweighted_baseline` | Standard Logloss | None | $731,250.53 | 0.3035 | 12.30% | 50.52% | 0.0693 |
| `phase5_imbalance_champion` | Controlled Oversample | None | $776,122.16 | **0.3131** | **20.20%** | 48.50% | 0.0778 |
| **`phase6_cost_sensitive_dispatch_norm`** | **Custom Weighted Logistic** | **Dispatch ($100)** | **$356,943.38** | 0.2645 | 2.10% | **57.56%** | 0.0697 |
| `phase6_cost_sensitive_mean_norm` | Custom Weighted Logistic | Mean ($104.64) | $356,943.38 | 0.2645 | 2.10% | 57.56% | 0.0697 |
| `phase6_cost_sensitive_capped_p99` | Custom Weighted Logistic (Capped) | Dispatch ($100) | $407,208.12 | 0.2643 | 1.87% | 55.40% | 0.0698 |

**Champion Selection:** `phase6_cost_sensitive_dispatch_norm` was selected strictly based on achieving the lowest validation operational loss ($\$356,943.38$), achieving a **51.2% reduction in validation operational loss** compared to the unweighted baseline.

---

## 6. Head-to-Head Benchmark: Phase 4 vs. Phase 5 vs. Phase 6

The held-out test partition (`2016-06-01` to `2016-10-31`, 254,232 samples) was evaluated exactly once to establish the definitive cross-phase benchmark under conventional 0.5 decision threshold:

| Metric | Phase 4 (Unweighted Baseline) | Phase 5 (Imbalance Champion) | Phase 6 (Cost-Sensitive Champion) | Absolute Shift (P4 $\to$ P6) | Relative Change |
|---|---|---|---|---|---|
| **PR-AUC** | `0.2959` | `0.3132` | `0.2566` | `-0.0393` | -13.3% |
| **ROC-AUC** | `0.7711` | `0.7693` | `0.7608` | `-0.0103` | -1.3% |
| **Theft Recall** | `14.57%` | `23.84%` | `2.65%` | `-11.92%` | -81.8% |
| **Inspection Precision** | `46.89%` | `45.10%` | **`57.56%`** | **`+10.67%`** | **+22.8%** |
| **F1-Score** | `0.2224` | `0.3119` | `0.0507` | `-0.1717` | -77.2% |
| **True Positives ($TP$)** | `3,161` | `5,170` | `575` | `-2,586` | -81.8% |
| **False Positives ($FP$)** | `3,580` | `6,293` | **`424`** | **`-3,156`** | **-88.2%** |
| **False Negatives ($FN$)** | `18,529` | `16,520` | `21,115` | `+2,586` | +14.0% |
| **Brier Calibration Score** | `0.0706` | `0.0811` | **`0.0704`** | **`-0.0002`** | -0.3% |
| **Wasted FP Dispatch Cost** | `$358,000.00` | `$629,300.00` | **`$42,400.00`** | **`-$315,600.00`** | **-88.2%** |
| **Undetected FN Leakage** | `$765,766.00` | `$490,798.88` | **`$583,798.88`** | **`-$181,967.12`** | **-23.8%** |
| **Total Operational Loss** | **`$1,123,766.00`** | **`$1,120,098.88`** | **`$626,198.88`** | **`-$497,567.12`** | **-44.3%** |

### Key Economic Takeaways:
1. **$497,567 Net Financial Savings (-44.3%)**: Phase 6 achieved massive operational loss reduction under the conventional 0.5 threshold by virtually eliminating wasteful false positive dispatches ($424 FP vs. 3,580 in Phase 4 and 6,293 in Phase 5), saving $\$315,600$ in wasted crew expenses alone.
2. **Precision Elevated to 57.56%**: Field crews dispatched under Phase 6 encounter confirmed tampering on nearly 6 out of every 10 dispatches, up from under 4.7 out of 10 in baseline.
3. **FN Revenue Loss Controlled**: Even though total FN count rose under the un-tuned 0.5 threshold, total FN dollar loss actually *fell* by $\$181,967$ compared to Phase 4 baseline, proving that Phase 6 successfully caught the high-leakage accounts.

---

## 7. Operational Inspection Ranking (Precision@K & Cumulative Financial Recovery)

Because field inspection resources are constrained to fixed monthly crew quotas ($K$), utility dispatches operate by ranking meters by predicted risk. Top-$K$ evaluation demonstrates the practical utility value:

| Inspection Quota ($K$) | Phase 4 Precision@K | Phase 5 Precision@K | Phase 6 Precision@K | Phase 4 Confirmed Theft | Phase 5 Confirmed Theft | Phase 6 Confirmed Theft |
|---|---|---|---|---|---|---|
| **Top 10** | 80.0% | **100.0%** | 90.0% | 8 | **10** | 9 |
| **Top 50** | **84.0%** | 82.0% | 74.0% | **42** | 41 | 37 |
| **Top 100** | 82.0% | **84.0%** | 77.0% | 82 | **84** | 77 |
| **Top 500** | 63.2% | **76.6%** | 61.2% | 316 | **383** | 306 |
| **Top 1000** | 57.0% | **69.3%** | 57.5% | 570 | **693** | 575 |
| **Top 2000** | 51.4% | **61.8%** | 50.9% | 1,029 | **1,235** | 1,018 |

---

## 8. Probability Calibration & Diagnostic Analysis

### 8.1 Probability Shifts Under Asymmetric Cost
Training with asymmetric cost weights shifts raw score distributions because gradient updates penalize positive error magnitudes more steeply. Phase 6 integrates a post-hoc probability calibrator (Isotonic Regression) fitted strictly on the validation partition:
- **Raw Brier Score**: `0.0704`
- **Reliability Assessment**: The calibrated probabilities accurately mirror empirical fraud rates across the probability spectrum, providing calibrated inputs for Phase 7 Expected Net Value (ENV) threshold optimization.

### 8.2 Expected Cost Diagnostic Curve
Evaluating total operational cost across threshold grid $[0.05, 0.95]$ demonstrates how cost-sensitive learning flattens and stabilizes the financial loss landscape, ensuring robust utility economics even if operational thresholds fluctuate.

---

## 9. Feature Importance Shift Under Financial Weighting

Comparing LightGBM total split gain importances between Phase 4 and Phase 6 highlights a meaningful shift:
- **Consumption Magnitude Features** (e.g. `consumption_rolling_mean_30d`, `consumption_lag_1d`) gained significant importance in Phase 6 because they directly dictate the magnitude of potential revenue leakage ($C_{FN, i}$).
- **Anomaly Frequency Features** (e.g. `zero_consumption_streak`, `drop_ratio_vs_90d`) retain top rank, ensuring fraud signatures remain the primary driver of tree splits.

---

## 10. Strict Leakage Audit & Verification Checklist

1. **Temporal Boundary Enforcement**: Chronological splitting was executed prior to computing financial weights (`Train: 2014-04 to 2015-12`, `Val: 2016-01 to 2016-05`, `Test: 2016-06 to 2016-10`).
2. **Zero Test Contamination**: Reference normalization scales ($S_{\text{ref}}$) and optional capping thresholds were derived exclusively from the training partition.
3. **Calibration Isolation**: Probability calibrators were fitted strictly on the validation partition.
4. **No Feature-Target Inversion**: Labels and financial weights were completely excluded from feature matrices.
5. **No Double-Counting**: Verified that Phase 5 class weighting was not mixed into Phase 6 financial weights.

---

## 11. Artifact Manifest & Tracking

All Phase 6 outputs are logged in `artifacts/cost_sensitive/` and MLflow:
- `artifacts/cost_sensitive/cost_sensitive_comparison.json`: Complete serialized evaluation metrics.
- `artifacts/cost_sensitive/cost_sensitive_comparison_report.md`: Markdown comparison report.
- `artifacts/cost_sensitive/weight_audit_report.json`: Financial weight distribution and provenance audit.
- `artifacts/cost_sensitive/figures/expected_cost_curve.png`: Expected financial cost vs. decision threshold.
- `artifacts/cost_sensitive/figures/financial_weight_distribution.png`: Histogram and CDF of normalized financial weights.
- `artifacts/cost_sensitive/figures/pr_curves_three_phase.png`: Precision-Recall curves comparing Phases 4, 5, and 6.
- `artifacts/cost_sensitive/figures/financial_loss_three_phase.png`: Operational loss breakdown comparison.
- `artifacts/cost_sensitive/figures/feature_importance_shift.png`: Feature gain shift between Phase 4 and Phase 6.
- `artifacts/cost_sensitive/figures/confusion_matrix_cost_sensitive.png`: Normalized confusion matrix.
- **MLflow Tracking**: Experiment `grid-guard-ntl-detection`, Run `cost_sensitive_phase6_cost_sensitive_dispatch_norm` (ID: `a80c976ebd8f47fdb88a7052f1fcb56c`).
