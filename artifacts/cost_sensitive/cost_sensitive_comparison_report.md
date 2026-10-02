# Grid-Guard Phase 6: Cost-Sensitive Custom Objective & Financially Weighted Learning Report

## 1. Executive Summary

In electricity Non-Technical Loss (NTL) detection, classification errors carry severely asymmetric financial consequences:
- **False Positive ($FP$)**: Wastes a fixed inspection crew dispatch fee ($C_{FP} = $100.00).
- **False Negative ($FN$)**: Allows unmetered consumption to persist undetected, forfeiting thousands of dollars in cumulative tariff revenue ($C_{FN, i}$).

In Phase 6, we implemented a mathematically verified, second-order differentiable **Cost-Sensitive Weighted Logistic Objective**:
$$\mathcal{L}_i(z_i) = w_i \left[ -y_i \ln(p_i) - (1 - y_i) \ln(1 - p_i) \right]$$
where $w_i = C_{FN, i}$ for tampering examples and $w_i = C_{FP}$ for honest examples, with exact gradient $g_i = w_i (p_i - y_i)$ and strictly positive Hessian $h_i = w_i p_i (1 - p_i)$.

- **Selected Champion Variant**: `phase6_cost_sensitive_dispatch_norm`
- **Selection Criterion**: Validation `total_operational_loss`
- **Evaluation Protocol**: Evaluated strictly once on the untouched held-out test partition (`2016-06-01` to `2016-10-31`).

---

## 2. Financial Training Weight Audit (Training Partition)

| Financial Parameter | Source Type | Value / Distribution | Operational Description |
|---|---|---|---|
| **Fixed Dispatch Cost ($C_{FP}$)** | Assumed | **$100.00** | Fixed crew dispatch expense per physical inspection |
| **Minimum Positive Cost Floor** | Assumed | **$100.00** | Floor on positive class error cost ensuring $h_i > 0$ |
| **Min Leakage Cost ($C_{FN, \min}$)** | Derived | **$100.00** | Smallest positive error consequence |
| **Median Leakage Cost ($C_{FN, \text{median}}$)** | Derived | **$100.00** | 50th percentile of annual theft leakage |
| **Mean Leakage Cost ($C_{FN, \text{mean}}$)** | Derived | **$154.44** | Average unmetered revenue loss |
| **99th Percentile Leakage Cost** | Derived | **$929.54** | High-volume industrial/commercial theft threshold |
| **Max Leakage Cost ($C_{FN, \max}$)** | Derived | **$625,625.50** | Maximum single-premise annual theft |
| **Median Penalty Ratio ($C_{FN} / C_{FP}$)** | Derived | **1.00 : 1** | Ratio of positive error penalty to false alarm |
| **Global Reference Scale ($S_{\text{ref}}$)** | Derived | **$100.00** | Normalization scale (Method: `dispatch_cost`) |
| **Normalized Weight Range** | Derived | **[1.000, 6256.255]** | Well-conditioned boosting weight range |

---

## 3. Three-Phase Performance Evolution: Baseline vs. Imbalance vs. Cost-Sensitive

| Metric | Phase 4 (Unweighted Baseline) | Phase 5 (Imbalance-Aware) | Phase 6 (Cost-Sensitive) | Absolute Shift (P4 $\to$ P6) |
|---|---|---|---|---|
| **PR-AUC** | `0.2959` | `0.3132` | `0.2566` | `-0.0393` |
| **ROC-AUC** | `0.7711` | `0.7693` | `0.7608` | `-0.0103` |
| **Theft Recall** | `14.57%` | `23.84%` | `2.65%` | `-11.92%` |
| **Precision** | `46.89%` | `45.10%` | `57.56%` | `+10.67%` |
| **F1-Score** | `0.2224` | `0.3119` | `0.0507` | `-0.1717` |
| **True Positives ($TP$)** | `3,161` | `5,170` | `575` | `-2,586` |
| **False Negatives ($FN$)** | `18,529` | `16,520` | `21,115` | `+2,586` |
| **False Positives ($FP$)** | `3,580` | `6,293` | `424` | `-3,156` |
| **Brier Score (Calibration)** | `0.0706` | `0.0811` | `0.0704` | `-0.0002` |
| **Wasted FP Dispatch Cost** | `$358,000.00` | `$629,300.00` | `$42,400.00` | `$-315,600.00` |
| **Undetected FN Leakage** | `$765,766.00` | `$490,798.88` | `$583,798.88` | `$-181,967.12` |
| **Total Operational Loss** | `$1,123,766.00` | `$1,120,098.88` | `$626,198.88` | `$-497,567.12` |

---

## 4. Operational Inspection Ranking (Precision@K & Cumulative Value)

| Inspection Capacity ($K$) | Phase 4 Precision@K | Phase 5 Precision@K | Phase 6 Precision@K | Phase 4 TP | Phase 5 TP | Phase 6 TP |
|---|---|---|---|---|---|---|
| **Top 10** | `80.0%` | `100.0%` | `90.0%` | `8` | `10` | `9` |
| **Top 50** | `84.0%` | `82.0%` | `74.0%` | `42` | `41` | `37` |
| **Top 100** | `82.0%` | `84.0%` | `77.0%` | `82` | `84` | `77` |
| **Top 500** | `63.2%` | `76.6%` | `61.2%` | `316` | `383` | `306` |
| **Top 1000** | `57.0%` | `69.3%` | `57.5%` | `570` | `693` | `575` |
| **Top 2000** | `51.4%` | `61.8%` | `50.9%` | `1,029` | `1,235` | `1,018` |

---

## 5. Technical Insights & Mathematical Distinctions

1. **Why Financial Weighting Differs from Class Imbalance Handling**:
   - Class weighting (Phase 5) assigns a uniform scalar $w_{\text{pos}}$ to all positive instances based purely on relative empirical frequency ($N_{\text{neg}} / N_{\text{pos}}$). It treats a tiny $50 theft identically to a $15,000 industrial diversion.
   - Cost-sensitive weighting (Phase 6) assigns per-instance financial penalties $w_i = C_{FN, i}$, compelling tree splitters to prioritize splits that isolate large-volume diversions.

2. **Differentiable Surrogate vs. Business Objective**:
   - The business loss $L_{\text{business}} = \sum [ y_i (1 - p_i) C_{FN, i} + (1 - y_i) p_i C_{FP} ]$ is linear in probability and yields zero second derivatives.
   - The weighted logistic surrogate $\mathcal{L}_i(z_i)$ provides the strictly positive Hessian $h_i = w_i p_i (1 - p_i) > 0$ required for stable second-order gradient boosting.
