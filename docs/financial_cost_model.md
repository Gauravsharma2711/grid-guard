# Grid-Guard Financial Cost & Revenue Leakage Framework

## 1. Executive Summary

Standard machine learning models optimize statistical loss functions (such as binary cross-entropy or log-loss). In utility operations, however, false positives and false negatives carry fundamentally asymmetric, non-uniform economic consequences:
- **False Positive ($FP$)**: An honest customer is incorrectly flagged for inspection. The utility incurs a direct physical field dispatch cost ($C_{\text{dispatch}}$) while discovering no stolen revenue.
- **False Negative ($FN$)**: A tampered meter remains undetected. The consumer continues to extract unmetered energy, causing cumulative revenue leakage over multiple undetected billing cycles.

Phase 4 of Grid-Guard formalizes this economic distinction into a reproducible, configurable financial cost matrix and revenue leakage estimation framework.

---

## 2. Mathematical Cost Matrix Formulation

For each meter $i$ evaluated at snapshot timestamp $t$:

$$
\text{Financial Impact}(y_i, \hat{y}_i) =
\begin{cases}
C_{\text{inspection}}, & \text{if } y_i = 1, \hat{y}_i = 1 \quad (\text{True Positive: Productive Inspection}) \\
C_{\text{dispatch}}, & \text{if } y_i = 0, \hat{y}_i = 1 \quad (\text{False Positive: Wasted Inspection}) \\
0, & \text{if } y_i = 0, \hat{y}_i = 0 \quad (\text{True Negative: Correct Non-Action}) \\
C_{\text{FN}, i}, & \text{if } y_i = 1, \hat{y}_i = 0 \quad (\text{False Negative: Cumulative Leakage Loss})
\end{cases}
$$

### A. False Positive Dispatch Cost ($C_{\text{FP}}$)

$$
C_{\text{FP}} = C_{\text{dispatch}}
$$

- $C_{\text{dispatch}}$ covers crew truck-roll, field technician hourly labor, physical inspection equipment, and administrative overhead.
- Configurable base default: `$100.00` per field inspection.
- Currency is fully configurable (ISO currency codes, e.g., `USD`, `EUR`, `CNY`).

### B. False Negative Leakage Cost ($C_{\text{FN}, i}$)

$$
C_{\text{FN}, i} = \Delta \text{kWh}_i \times \text{Tariff}_i \times H_{\text{undetected}}
$$

Where:
- $\Delta \text{kWh}_i$: Estimated daily energy consumption deficit (kWh/day).
- $\text{Tariff}_i$: Effective volumetric electricity tariff per kWh.
- $H_{\text{undetected}}$: Expected horizon of undetected theft (configurable monthly billing cycles; default: 12 months).

### C. Estimated Recoverable Revenue (True Positive)

When an active theft is detected and verified by inspection:

$$
\text{Gross Recovery}_i = \Delta \text{kWh}_i \times \text{Tariff}_i \times H_{\text{undetected}}
$$

$$
\text{Net Recovery}_i = \text{Gross Recovery}_i - C_{\text{dispatch}}
$$

---

## 3. Revenue Leakage Proxy Formulation

Because unmetered bypasses cannot be directly measured by the meter itself, Grid-Guard uses a trailing baseline proxy to quantify unbilled deficit:

$$
\Delta \text{kWh}_i = \max\left(0, \text{Baseline}_{60\text{d}, i} - \text{Observed}_{14\text{d}, i}\right)
$$

To prevent normal household fluctuations from triggering spurious leakage costs, a material leakage gate is applied:

$$
\Delta \text{kWh}_i = 
\begin{cases}
\Delta \text{kWh}_i, & \text{if } \Delta \text{kWh}_i \ge \text{min\_leakage\_kwh} \quad (5.0\text{ kWh/day}) \\
0.0, & \text{otherwise}
\end{cases}
$$

Monthly energy deficit:

$$
\text{Deficit Monthly kWh}_i = \Delta \text{kWh}_i \times 30.0
$$

Total cumulative financial exposure:

$$
\text{Estimated Leakage Cost}_i = \text{Deficit Monthly kWh}_i \times \text{Tariff}_i \times H_{\text{undetected}}
$$

---

## 4. Financial Provenance Separation (Audit Trail)

Every parameter in Grid-Guard is explicitly categorized into one of three strict provenance tiers:

| Tier | Definition | Examples in Grid-Guard |
|---|---|---|
| **Observed** | Directly recorded in the source dataset | Meter ID, daily consumption readings, inspection labels |
| **Derived** | Deterministically calculated from observed fields | 60-day baseline, consumption deficit, estimated leakage kWh |
| **Assumed** | Operational or economic simulation parameters from configuration | Dispatch cost (`$100`), regional tariff (`$0.15/kWh`), undetected horizon (`12 months`) |

### Parameter Audit Table

| Parameter | Default Value | Unit | Provenance | Description |
|---|---|---|---|---|
| `currency` | `USD` | ISO Code | **ASSUMED** | Currency for operational metrics |
| `dispatch_cost` | `100.0` | Currency | **ASSUMED** | Physical inspection dispatch cost |
| `default_tariff` | `0.15` | Currency/kWh | **ASSUMED** | Fallback regional volumetric electricity tariff |
| `undetected_cycles` | `12` | Months | **ASSUMED** | Expected duration theft continues undetected |
| `min_leakage_kwh` | `5.0` | kWh/day | **ASSUMED** | Minimum daily deficit threshold for material leakage |
| `estimated_leakage_kwh` | Calculated | kWh | **DERIVED** | $\max(0, \text{baseline}_{60d} - \text{observed}_{14d}) \times 30$ |
| `estimated_leakage_cost` | Calculated | Currency | **DERIVED** | $\text{estimated\_leakage\_kwh} \times \text{tariff} \times 12$ |

---

## 5. Baseline Financial Evaluation Results (Real Dataset)

Evaluated on 254,232 held-out test meter-snapshots (42,372 meters across 6 monthly evaluation periods) at the conventional 0.5 threshold:

| Financial Metric | Conventional Baseline (Threshold = 0.5) |
|---|---|
| **Field Crew Dispatch Cost ($C_{\text{dispatch}}$)** | `$100.00` |
| **Total Dispatches Dispatched ($TP + FP$)** | `6,741` inspections |
| **Productive Inspections ($TP$)** | `3,161` (46.9% dispatch precision) |
| **Wasted Dispatches ($FP$)** | `3,580` (53.1% false alarm rate) |
| **Undetected Thefts ($FN$)** | `18,529` (85.4% of total actual thefts) |
| **Total Wasted FP Dispatch Cost** | **`$358,000.00`** |
| **Total Undetected FN Revenue Leakage** | **`$765,766.00`** |
| **Total Baseline Operational Loss** | **`$1,123,766.00`** |
| **Estimated Gross Recovered Revenue** | `$1,447,265.25` |
| **Estimated Net Financial Recovery** | **`$773,165.25`** |

> [!IMPORTANT]
> The unweighted baseline suffers from severe false negatives (18,529 undetected thefts), incurring `$765,766` in unrecovered revenue leakage because the 0.5 classification threshold is completely blind to the economic asymmetric cost of theft. In subsequent phases (Phase 6 Cost-Sensitive Training and Phase 7 Expected Net Value Dynamic Thresholding), this benchmark serves as the primary evaluation target.
