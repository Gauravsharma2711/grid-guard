# Grid-Guard Phase 7: Dynamic Thresholding, Expected Net Value & Inspection Prioritization Report

## 1. Executive Summary

In electricity Non-Technical Loss (NTL) detection, **prediction probability alone is not the final inspection decision**.
Deploying physical field inspection crews incurs a non-trivial fixed operational cost ($C_{\text{dispatch}} = $100.00).
A conventional fixed-threshold model (e.g. $p \ge 0.5$) commits severe economic errors:
1. It dispatches costly crews to low-consumption residential accounts with high detection probability but negligible recoverable revenue ($ENV < 0$).
2. It ignores high-volume industrial/commercial diversions with moderate probability where potential recovery exceeds inspection fees by orders of magnitude.

In Phase 7, Grid-Guard establishes the **operational decision engine**:
- Calculates per-meter dynamic thresholds: **Bayes Cost Threshold** ($\tau_{\text{cost}}$) and **Direct ENV Threshold** ($\tau_{\text{env}}$).
- Computes **Expected Net Value**: $\text{ENV}_i = p_i \times R_i - C_{\text{dispatch}}$.
- Dispatches inspections only when economically justified ($\text{ENV}_i > 0$).
- Ranks candidates into a prioritized work-order queue based on expected financial yield.

---

## 2. Decision Logic & Mathematical Formulation

### 2.1 Bayes Cost Threshold (Error Loss Minimization)
Comparing expected cost of inspecting vs. not inspecting:
$$\tau_{\text{cost}, i} = \frac{C_{\text{dispatch}}}{C_{\text{dispatch}} + C_{FN, i}}$$
where $C_{FN, i}$ is the financial penalty of failing to inspect a tampered meter. As potential leakage $C_{FN, i} \to \infty$, $\tau_{\text{cost}, i} \to 0$.

### 2.2 Direct ENV Economic Threshold (Positive Net Recovery)
Inspecting yields positive expected financial return when:
$$\text{ENV}_i = p_i \times R_i - C_{\text{dispatch}} > 0 \iff p_i > \frac{C_{\text{dispatch}}}{R_i} = \tau_{\text{env}, i}$$
where $R_i$ is the estimated recoverable tariff revenue. When $R_i \le 0$, $\tau_{\text{env}, i} = \infty$, preventing loss-making dispatches.

---

## 3. Controlled Policy Benchmark: Fixed 0.5 vs. Bayes Cost vs. Dynamic ENV

| Operational Metric | Policy A: Fixed Threshold ($p \ge 0.5$) | Policy B: Bayes Cost Threshold ($p \ge \tau_{\text{cost}}$) | Policy C: Dynamic ENV Rule ($\text{ENV} > 0$) |
|---|---|---|---|
| **Candidates Evaluated** | `42,372` | `42,372` | `42,372` |
| **Inspections Recommended** | `170` | `880` | `801` |
| **Inspection Rate** | `0.40%` | `2.08%` | `1.89%` |
| **Expected Gross Recovery** | `$240,120.42` | `$362,497.41` | `$355,330.47` |
| **Expected Dispatch Cost** | `$17,000.00` | `$88,000.00` | `$80,100.00` |
| **Expected Net Value (ENV)** | `$223,120.42` | `$274,497.41` | **`$275,230.47`** |
| **Mean ENV per Ticket** | `$1,312.47` | `$311.93` | **`$343.61`** |
| **Realized Precision** | `46.47%` | `26.70%` | `27.97%` |
| **Realized Recall** | `2.19%` | `6.50%` | `6.20%` |
| **Confirmed Thefts ($TP$)** | `79` | `235` | `224` |
| **Wasted Dispatches ($FP$)** | `91` | `645` | `577` |
| **Realized Total Dispatch Cost** | `$17,000.00` | `$88,000.00` | `$80,100.00` |
| **Realized Gross Recovery** | `$178,410.85` | `$248,422.29` | `$244,853.20` |
| **Realized Net Recovery** | `$161,410.85` | `$160,422.29` | **`$164,753.20`** |

---

## 4. Top-K Field Inspection Prioritization Queue

Utility field crews operate under finite monthly inspection capacity constraints ($K$).
Sorting tickets by Expected Net Value ensures each dispatched crew captures maximum financial yield:

| Capacity ($K$) | Inspected | Expected Gross Recovery | Expected Dispatch Cost | Expected Net Value | Precision@K | Realized Recovery | Realized Net Recovery |
|---|---|---|---|---|---|---|---|
| **Top 10** | `10` | `$106,487.91` | `$1,000.00` | **`$105,487.91`** | `60.0%` | `$93,832` | `$92,832` |
| **Top 25** | `25` | `$145,037.03` | `$2,500.00` | **`$142,537.03`** | `52.0%` | `$117,436` | `$114,936` |
| **Top 50** | `50` | `$179,998.40` | `$5,000.00` | **`$174,998.40`** | `46.0%` | `$137,658` | `$132,658` |
| **Top 100** | `100` | `$221,126.09` | `$10,000.00` | **`$211,126.09`** | `37.0%` | `$155,887` | `$145,887` |
| **Top 250** | `250` | `$274,194.28` | `$25,000.00` | **`$249,194.28`** | `33.6%` | `$190,436` | `$165,436` |
| **Top 500** | `500` | `$319,437.91` | `$50,000.00` | **`$269,437.91`** | `31.6%` | `$223,164` | `$173,164` |
| **Top 1,000** | `1,000` | `$368,675.35` | `$100,000.00` | **`$268,675.35`** | `24.4%` | `$251,161` | `$151,161` |
| **Top 2,000** | `2,000` | `$370,809.94` | `$200,000.00` | **`$170,809.94`** | `31.8%` | `$251,996` | `$51,996` |

---

## 5. Economic Scenario Sensitivity Analysis

| Scenario | Dispatch Cost | Recovery Factor | Recommended Tickets | Expected Gross Recovery | Expected Net Value | Mean ENV / Ticket |
|---|---|---|---|---|---|---|
| **baseline** | `$100` | `1.00` | `801` | `$355,330.47` | **`$275,230.47`** | `$343.61` |
| **high_dispatch_cost_200** | `$200` | `1.00` | `313` | `$288,043.04` | **`$225,443.04`** | `$720.27` |
| **low_dispatch_cost_50** | `$50` | `1.00` | `937` | `$366,117.34` | **`$319,267.34`** | `$340.73` |
| **conservative_recovery_0.70** | `$100` | `0.70` | `510` | `$224,613.75` | **`$173,613.75`** | `$340.42` |
| **high_tariff_0.25** | `$100` | `1.67` | `917` | `$608,364.03` | **`$516,664.03`** | `$563.43` |
| **low_tariff_0.08** | `$100` | `0.53` | `342` | `$156,594.88` | **`$122,394.88`** | `$357.88` |

---

## 6. Operational Guardrails & Capacity Policy

- **One Ticket Per Inspection Unit**: Multitemporal snapshot records are grouped to the latest evaluation snapshot (`latest_snapshot`), eliminating duplicate work orders.
- **Strictly Positive ENV Policy**: Negative-ENV meters are rejected from dispatch by default, preventing wasteful quota-filling dispatches.
- **Deterministic Work Orders**: Every ticket receives an immutable `ticket_id` derived cryptographically from `meter_id` and evaluation period.
