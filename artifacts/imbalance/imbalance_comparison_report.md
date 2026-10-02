# Grid-Guard Phase 5: Class Imbalance Strategy & Rare-Tampering Learning Report

## 1. Executive Summary

In electricity theft detection, normal honest consumption vastly outnumbers fraudulent bypasses.
In Grid-Guard's training partition, ground-truth tampering represents **8.53%** of observations
(**79,530** positive tampering instances vs. **852,654** normal instances, an imbalance ratio of **10.72 : 1**).

In Phase 4, the unweighted baseline model suffered from acute false negatives, capturing only **14.57%** of actual thefts at the conventional 0.5 threshold.
In Phase 5, we systematically evaluated candidate class imbalance strategies (class-weighting multipliers, controlled training oversampling, majority undersampling, and SMOTE) strictly on the chronological validation partition (`2016-01-01` to `2016-05-31`).

- **Champion Strategy Selected**: `controlled_oversample_0.20`
- **Selection Criterion**: Highest validation `pr_auc`
- **Test Set Evaluation**: Evaluated once on the untouched held-out test partition (`2016-06-01` to `2016-10-31`).

---

## 2. Head-to-Head Performance: Phase 4 Baseline vs. Phase 5 Champion

| Metric | Phase 4 (Unweighted Baseline) | Phase 5 (controlled_oversample_0.20) | Absolute Change | Relative Impact |
|---|---|---|---|---|
| **PR-AUC** | `0.2959` | `0.3132` | `+0.0173` | Primary rare-class ranking metric |
| **ROC-AUC** | `0.7711` | `0.7693` | `-0.0018` | Global discriminative capacity |
| **Recall (Theft Capture)** | `14.57%` | `23.84%` | `+9.27%` | Massive reduction in missed thefts |
| **Precision** | `46.89%` | `45.10%` | `-1.79%` | Precision trade-off under threshold 0.5 |
| **F1-Score** | `0.2224` | `0.3119` | `+0.0895` | Harmonic balance |
| **True Positives ($TP$)** | `3,161` | `5,170` | `+2,009` | Confirmed theft detections |
| **False Negatives ($FN$)** | `18,529` | `16,520` | `-2,009` | Undetected theft cases |
| **False Positives ($FP$)** | `3,580` | `6,293` | `+2,713` | Wasted inspection alarms |
| **Brier Score (Calibration)** | `0.0706` | `0.0811` | `+0.0105` | Probability calibration shift |
| **Total Operational Loss** | `$1,123,766.00` | `$1,120,098.88` | `$-3,667.12` | Post-prediction financial evaluation |

---

## 3. Operational Ranking Performance: Precision@K

| Inspection Capacity ($K$) | Baseline Precision@K | Champion Precision@K | Baseline TP Found | Champion TP Found |
|---|---|---|---|---|
| **Top 10** | `80.0%` | `100.0%` | `8` | `10` |
| **Top 50** | `84.0%` | `82.0%` | `42` | `41` |
| **Top 100** | `82.0%` | `84.0%` | `82` | `84` |
| **Top 500** | `63.2%` | `76.6%` | `316` | `383` |
| **Top 1000** | `57.0%` | `69.3%` | `570` | `693` |
| **Top 2000** | `51.4%` | `61.8%` | `1,029` | `1,235` |

---

## 4. Assessment of Imbalance Strategies

1. **Class Weighting (`scale_pos_weight`)**:
   - **Mechanism**: Modifies the loss gradient on the positive minority instances without altering training data dimensions.
   - **Finding**: Extremely stable, 100% causal, introduces zero synthetic distortion, and drastically improves minority theft recall.
2. **Controlled Oversampling**:
   - **Mechanism**: Re-samples positive training instances with replacement to achieve target ratio.
   - **Finding**: Effective for tree boosting but increases training time and risks memorizing duplicated instances.
3. **Controlled Undersampling**:
   - **Mechanism**: Discards majority normal instances.
   - **Finding**: Discards valuable variance and increases variance of estimates across temporal shifts.
4. **SMOTE**:
   - **Technical Suitability Assessment**: In time-series feature spaces, synthetic linear interpolation between positive instances can violate physical constraints (e.g. creating points where minimum consumption exceeds mean consumption or distorting discrete zero streaks). Class weighting is physically and mathematically superior for smart-meter time series.

---

## 5. Probability Calibration Assessment

Imbalance mitigation elevates the raw output logits to counter class sparsity. Consequently, the predicted probabilities no longer represent raw posterior empirical frequencies:
- **Baseline Brier Score**: `0.0706`
- **Champion Brier Score**: `0.0811`

This shift is natural and expected. In Phase 6 (Cost-Sensitive Optimization) and Phase 7 (Expected Net Value & Dynamic Thresholding), economic decision thresholds will supersede the arbitrary 0.5 cutoff to optimize field recovery dollars directly.
