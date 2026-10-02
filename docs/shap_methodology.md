# Grid-Guard Tree-SHAP Mathematical Methodology

## 1. Mathematical Foundation of Tree-SHAP

Tree-SHAP (Lundberg et al., 2020) computes exact Shapley values for tree-based ensemble models in polynomial time $\mathcal{O}(T L D^2)$, where $T$ is the number of trees, $L$ is the number of leaves, and $D$ is the maximum tree depth.

In cooperative game theory, the Shapley value $\phi_j$ allocates a fair payout to feature $j$ based on its marginal contribution across all possible feature subsets $S \subseteq F \setminus \{j\}$:

$$\phi_j(x) = \sum_{S \subseteq F \setminus \{j\}} \frac{|S|! (|F| - |S| - 1)!}{|F|!} \left[ f_x(S \cup \{j\}) - f_x(S) \right]$$

where:
* $F$ is the complete set of engineered features ($|F| = 60$).
* $f_x(S) = \mathbb{E}[f(x) \mid x_S]$ is the conditional expectation of the model output given only the subset of features $S$.

---

## 2. Output Space: Raw Margin Log-Odds vs. Probability

A critical architectural distinction in Grid-Guard is the choice of output space for SHAP computation.

### A. Raw Margin Log-Odds ($z_i$)
The LightGBM binary classifier sums the leaf outputs $w_{t}$ of $T$ decision trees:

$$z_i = f(x_i) = \sum_{t=1}^{T} w_{t}(x_i)$$

In this space:
1. **Additivity is Exact**: The model output is a strictly linear sum of tree predictions.
2. **Efficiency**: TreeExplainer computes exact conditional expectations without numerical approximations.
3. **Additive Reconstruction**:
   $$\mathbb{E}[z] + \sum_{j=1}^{60} \phi_{ij} = z_i$$
   where $\mathbb{E}[z] = -2.5928$ is the expected leaf prediction over the training/background data.

### B. Probability Space & Sigmoid Nonlinearity
Converting margin $z_i$ into uncalibrated probability $\hat{p}_i$ introduces the nonlinear sigmoid activation:

$$\hat{p}_i = \sigma(z_i) = \frac{1}{1 + e^{-z_i}}$$

Because the sigmoid is nonlinear ($\sigma(a + b) \neq \sigma(a) + \sigma(b)$), computing SHAP values directly in probability space violates exact leaf additivity and requires path-dependent sampling or Taylor-series approximations.

Therefore, **Grid-Guard computes and stores SHAP values strictly in the native log-odds margin space**, where mathematical additivity is exact to within machine precision ($< 10^{-14}$).

---

## 3. Post-Hoc Probability Calibration Interaction

In Phase 6, Grid-Guard introduced post-hoc Isotonic Regression to calibrate probabilities:

$$p_i^* = f_{\text{iso}}(\hat{p}_i) = f_{\text{iso}}(\sigma(z_i))$$

Because $f_{\text{iso}}$ is a non-decreasing piecewise constant step function, it does not alter the relative ordering of model predictions.

* **SHAP Explains**: The continuous evidence accumulation in log-odds space $z_i$.
* **Calibration Explains**: The empirical frequency of positive cases at that score level.
* **ENV Utilizes**: The calibrated probability $p_i^*$ for financial risk calculations ($\text{ENV}_i = p_i^* R_i - C_{\text{dispatch}}$).

---

## 4. Verification of Additive Reconstruction

To guarantee numerical fidelity, Grid-Guard unit tests enforce the following additive property across all explained samples:

$$\max_{i \in \text{Samples}} \left| \mathbb{E}[z] + \sum_{j=1}^{60} \phi_{ij} - z_i \right| < 10^{-4}$$

Empirical testing on real Phase 6 champion predictions yields a maximum absolute discrepancy of:

$$\text{Max Discrepancy} = 4.44 \times 10^{-15} \text{ (exact within IEEE 754 floating point arithmetic)}$$

---

## 5. Feature Correlation and Grouping

In time-series feature engineering, multi-scale statistics (e.g. `rolling_std_30d` and `rolling_std_60d`, or `rolling_mean_7d` and `rolling_mean_14d`) exhibit natural collinearity. TreeExplainer naturally distributes attribution across correlated features based on their tree-split frequencies.

To assist human field reviewers, Grid-Guard aggregates feature attributions into high-level functional groups:

1. **Historical Baseline Group**: Benchmarks customer capacity and typical load variance (`rolling_std_60d`, `rolling_std_30d`, `rolling_mean_60d`).
2. **Consumption Collapse Group**: Quantifies the magnitude and duration of unmetered load drops (`ratio_14d_60d`, `sustained_drop_magnitude`, `sustained_drop_duration`).
3. **Data Quality Group**: Validates signal completeness and rules out blackout artifacts (`coverage_ratio`, `missing_ratio`, `imputation_ratio`).
4. **Variability & Flatline Group**: Detects loss of natural load variation (`rolling_cv_7d`, `flatline_streak`, `daily_diff_abs_7d_mean`).
5. **Zero Streak Group**: Tracks consecutive unmetered zero days (`current_zero_streak`, `zero_count_7d`).
