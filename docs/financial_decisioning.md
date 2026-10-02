# Grid-Guard Phase 7: Dynamic Thresholding, Expected Net Value (ENV) & Inspection Prioritization

## 1. Executive Summary & Problem Formulation

In electricity Non-Technical Loss (NTL) detection and utility meter tampering investigations, **predicted probability alone cannot serve as the final dispatch decision**.

Deploying field inspection crews incurs a fixed operational fee ($C_{\text{dispatch}} = \$100.00$), encompassing labor, vehicle transport, specialized testing instrumentation, and field safety protocols. Traditional static probability thresholds (such as the conventional $p \ge 0.5$) make two catastrophic financial errors:
1. **Low-Revenue False Alarms**: They dispatch costly inspection crews to small residential accounts with high detection probability ($p = 0.85$) but negligible unmetered consumption ($R = \$40$), guaranteeing negative net utility return ($\text{ENV} = 0.85 \times \$40 - \$100 = -\$66.00$).
2. **High-Revenue Missed Opportunities**: They ignore high-volume commercial or industrial diversions with moderate probability ($p = 0.25 < 0.5$) where potential recovery ($R = \$5,000$) dwarfs the dispatch cost, missing thousands of dollars in net recoverable revenue ($\text{ENV} = 0.25 \times \$5,000 - \$100 = +\$1,150.00$).

**Phase 7 implements Grid-Guard's operational decision engine**, converting Phase 6 calibrated probability predictions into an economically prioritized field inspection queue.

---

## 2. Mathematical Formulations: Dynamic Thresholds & Expected Net Value

### 2.1 The Bayes Cost Threshold (Error Loss Minimization)
The Bayes decision threshold is derived by comparing the expected loss of dispatching an inspection versus taking no action:

$$\mathbb{E}[\text{Loss} \mid \text{Inspect}] = (1 - p_i) C_{\text{dispatch}} + p_i \cdot 0 = (1 - p_i) C_{\text{dispatch}}$$
$$\mathbb{E}[\text{Loss} \mid \text{No Inspect}] = p_i C_{FN, i} + (1 - p_i) \cdot 0 = p_i C_{FN, i}$$

An inspection is warranted when $\mathbb{E}[\text{Loss} \mid \text{Inspect}] \le \mathbb{E}[\text{Loss} \mid \text{No Inspect}]$:
$$(1 - p_i) C_{\text{dispatch}} \le p_i C_{FN, i}$$
$$C_{\text{dispatch}} \le p_i (C_{\text{dispatch}} + C_{FN, i})$$
$$p_i \ge \frac{C_{\text{dispatch}}}{C_{\text{dispatch}} + C_{FN, i}} = \tau_{\text{cost}, i}$$

**Properties of $\tau_{\text{cost}, i}$:**
- Bound: $\tau_{\text{cost}, i} \in [0.0, 1.0]$.
- When $C_{FN, i} \to \infty$, $\tau_{\text{cost}, i} \to 0.0$ (urgent priority to avoid catastrophic missed loss).
- When $C_{FN, i} = C_{\text{dispatch}}$, $\tau_{\text{cost}, i} = 0.5$.
- When $C_{FN, i} \le 0$, $\tau_{\text{cost}, i} = 1.0$ (never inspect if zero cost for missing).

### 2.2 The Direct Economic ENV Threshold (Positive Net Recovery)
From Grid-Guard's business utility objective, an inspection yields positive Expected Net Value (ENV) when:
$$\text{ENV}_i = p_i \times R_i - C_{\text{dispatch}} > 0$$
where $R_i$ is the estimated recoverable tariff revenue. Solving for $p_i$:
$$p_i > \frac{C_{\text{dispatch}}}{R_i} = \tau_{\text{env}, i} \quad (\text{for } R_i > 0)$$

**Properties of $\tau_{\text{env}, i}$:**
- When $R_i \le 0$, $\tau_{\text{env}, i} = \infty$, strictly preventing dispatches where zero revenue is recoverable.
- When $R_i = C_{\text{dispatch}}$, $\tau_{\text{env}, i} = 1.0$ (only 100% certain fraud breaks even).
- When $R_i = 10 \times C_{\text{dispatch}}$, $\tau_{\text{env}, i} = 0.10$.

### 2.3 The Critical Mathematical Distinction ($\tau_{\text{cost}} < \tau_{\text{env}}$)
For any candidate meter with identical financial exposure $R_i = C_{FN, i} > 0$ and $C_{\text{dispatch}} > 0$:
$$\frac{C_{\text{dispatch}}}{C_{\text{dispatch}} + R_i} < \frac{C_{\text{dispatch}}}{R_i} \implies \tau_{\text{cost}, i} < \tau_{\text{env}, i}$$

**Operational Meaning:**
- The Bayes threshold $\tau_{\text{cost}}$ is more permissive because it accounts for the loss avoided by detecting an ongoing theft.
- The ENV threshold $\tau_{\text{env}}$ is more conservative because it demands that expected cash recovery strictly exceeds the physical dispatch expense.
- Grid-Guard maintains explicit separate code paths for both thresholds in [`src/grid_guard/decision/thresholds.py`](file:///c:/Gaurav's%20Den/crazy-shits/grid-guard/src/grid_guard/decision/thresholds.py).

---

## 3. Decision Engine Architecture & Pipeline

The decision engine operates as an autonomous multi-stage pipeline:

```
[ Model Predictions (p_cal, p_uncal) + Historical Metadata (R_i, C_FN) ]
                              │
                              ▼
        [ Inspection Unit Aggregation (latest_snapshot) ]
                              │
                              ▼
  [ Dynamic Threshold Engine: tau_cost & tau_env Calculation ]
                              │
                              ▼
   [ Expected Net Value (ENV) & Gross Recovery Computation ]
                              │
                              ▼
    [ Multi-Key Prioritization (ENV desc, prob desc, rev desc) ]
                              │
                              ▼
   [ Capacity Dispatcher (Strictly Positive ENV & Quota Cap) ]
                              │
                              ▼
  [ Canonical Inspection Tickets: Parquet, Audit CSV & Reports ]
```

### Operational Guardrails:
1. **One Ticket Per Inspection Unit**: Smart-meter AMI data contains multiple periodic snapshot timestamps. Grouping to the latest evaluation snapshot (`latest_snapshot`) collapses 254,232 prediction records into exactly **42,372 unique candidate meters**, eliminating duplicate work orders.
2. **Strictly Positive ENV Policy**: Utility crew quotas are never filled with loss-making inspections merely because crew capacity exists.
3. **Cryptographically Deterministic Ticket IDs**: Every inspection ticket receives an immutable work-order identifier derived via SHA-256: `TCK-{eval_period}-{hash[:8]}` (e.g. `TCK-2016-10-30-A1B2C3D4`).

---

## 4. Controlled Policy Benchmark: Fixed 0.5 vs. Bayes Cost vs. Dynamic ENV

Evaluated across the 42,372 unique candidate meters in the held-out test partition (`2016-06-01` to `2016-10-31`):

| Operational Metric | Policy A: Fixed Threshold ($p \ge 0.5$) | Policy B: Bayes Cost Threshold ($p \ge \tau_{\text{cost}}$) | Policy C: Dynamic ENV Rule ($\text{ENV} > 0$) |
|---|---|---|---|
| **Candidate Meters Evaluated** | `42,372` | `42,372` | `42,372` |
| **Inspections Recommended** | `170` | `880` | **`801`** |
| **Inspection Rate** | `0.40%` | `2.08%` | **`1.89%`** |
| **Expected Gross Recovery** | `$240,120.42` | `$362,497.41` | **`$355,330.47`** |
| **Expected Dispatch Cost** | `$17,000.00` | `$88,000.00` | **`$80,100.00`** |
| **Expected Net Value (ENV)** | `$223,120.42` | `$274,497.41` | **`$275,230.47`** (Highest) |
| **Mean ENV per Ticket** | `$1,312.47` | `$311.93` | **`$343.61`** |
| **Confirmed Thefts ($TP$)** | `79` | `235` | **`224`** |
| **Wasted Dispatches ($FP$)** | `91` | `645` | **`577`** |
| **Realized Total Dispatch Cost** | `$17,000.00` | `$88,000.00` | **`$80,100.00`** |
| **Realized Gross Recovery** | `$178,410.85` | `$248,422.29` | **`$244,853.20`** |
| **Realized Net Recovery** | `$161,410.85` | `$160,422.29` | **`$164,753.20`** (Highest) |

### Key Economic Takeaways:
1. **Dynamic ENV Delivers Highest Realized Net Recovery ($164,753.20)**: Exceeds both the naive 0.5 fixed threshold ($161,410.85) and the Bayes cost threshold ($160,422.29).
2. **Filtering Marginal Losses**: Comparing Dynamic ENV to Bayes Cost Threshold, Dynamic ENV filtered out 79 marginal inspections that cost $7,900 to dispatch but returned only $3,569 in revenue, thereby increasing net recovery by **+$4,330.91**.
3. **Tripling Theft Detections Over Fixed 0.5**: Dynamic ENV uncovered **224 confirmed thefts** compared to only 79 under Fixed 0.5 (+183.5% more confirmed thieves caught), capturing **+$66,442.35 in additional recovered revenue**.

---

## 5. Top-K Field Inspection Prioritization Queue

Field crews operate under finite monthly inspection quotas ($K$). Sorting candidate work orders by Expected Net Value descending ensures crews capture maximum utility value within any assigned capacity:

| Inspection Quota ($K$) | Inspected | Expected Gross Recovery | Expected Dispatch Cost | Expected Net Value | Precision@K | Realized Recovery | Realized Net Recovery |
|---|---|---|---|---|---|---|---|
| **Top 10** | `10` | `$106,487.91` | `$1,000.00` | **`$105,487.91`** | `60.0%` | `$93,832` | **`$92,832`** |
| **Top 25** | `25` | `$145,037.03` | `$2,500.00` | **`$142,537.03`** | `52.0%` | `$117,436` | **`$114,936`** |
| **Top 50** | `50` | `$179,998.40` | `$5,000.00` | **`$174,998.40`** | `46.0%` | `$137,658` | **`$132,658`** |
| **Top 100** | `100` | `$221,126.09` | `$10,000.00` | **`$211,126.09`** | `37.0%` | `$155,887` | **`$145,887`** |
| **Top 250** | `250` | `$274,194.28` | `$25,000.00` | **`$249,194.28`** | `33.6%` | `$190,436` | **`$165,436`** |
| **Top 500** | `500` | `$319,437.91` | `$50,000.00` | **`$269,437.91`** | `31.6%` | `$223,164` | **`$173,164`** |
| **Top 1,000** | `1,000` | `$368,675.35` | `$100,000.00` | **`$268,675.35`** | `24.4%` | `$251,161` | **`$151,161`** |

> [!NOTE]
> Cumulative net recovery peaks at **$173,164** around Top 500 inspections. Dispatched crews beyond Top 500 face diminishing marginal returns as candidate ENVs approach the $100 dispatch cost hurdle.

---

## 6. Economic Scenario Sensitivity Analysis

We evaluated the robustness of the decision engine across operational cost and tariff shifts:

| Operational Scenario | Dispatch Cost | Recovery Factor | Recommended Tickets | Expected Gross Recovery | Expected Net Value | Mean ENV / Ticket |
|---|---|---|---|---|---|---|
| **Baseline** | `$100` | `1.00` | **`801`** | `$355,330.47` | **`$275,230.47`** | `$343.61` |
| **High Dispatch Cost ($200)** | `$200` | `1.00` | **`313`** | `$288,043.04` | **`$225,443.04`** | `$720.27` |
| **Low Dispatch Cost ($50)** | `$50` | `1.00` | **`937`** | `$366,117.34` | **`$319,267.34`** | `$340.73` |
| **High Tariff ($0.25/kWh)** | `$100` | `1.67` | **`917`** | `$608,364.03` | **`$516,664.03`** | `$563.43` |
| **Low Tariff ($0.08/kWh)** | `$100` | `0.53` | **`342`** | `$156,594.88` | **`$122,394.88`** | `$357.88` |
| **Conservative Recovery (70%)** | `$100` | `0.70` | **`510`** | `$224,613.75` | **`$173,613.75`** | `$340.42` |

**Economic Observations:**
- When dispatch costs double to $200, the queue automatically contracts by 61% (to 313 tickets) while average ticket ENV surges to $720.27.
- When tariffs rise to $0.25/kWh, additional moderate anomalies become profitable, expanding the queue to 917 tickets.

---

## 7. Artifact Manifest & Tracking

All Phase 7 outputs are stored in `artifacts/decision/` and tracked in MLflow:
- `artifacts/decision/inspection_tickets.parquet`: Complete strongly-typed tickets dataset (42,372 meters).
- `artifacts/decision/top_100_inspection_tickets.csv`: Work orders for the top 100 field dispatches.
- `artifacts/decision/decision_comparison.json`: Complete serialized metrics dictionary.
- `artifacts/decision/decision_comparison_report.md`: Markdown comparison audit report.
- `artifacts/decision/figures/env_distribution.png`: Histogram & KDE of Expected Net Value.
- `artifacts/decision/figures/probability_vs_env.png`: Scatter plot showing probability vs. ENV decoupling.
- `artifacts/decision/figures/threshold_vs_financial_exposure.png`: Theoretical curves of $\tau_{\text{cost}}$ vs $\tau_{\text{env}}$.
- `artifacts/decision/figures/cumulative_env_by_rank.png`: Cumulative financial yield by rank.
- `artifacts/decision/figures/policy_comparison_bar.png`: Comparative bar chart of inspections and net recovery.
- **MLflow Run**: Experiment `grid-guard-ntl-detection`, Run `decision_engine_env` (ID: `c0dfbc322a8241c5b00ec5d9192ab988`).
