# Grid-Guard Financial Cost & Revenue Leakage Report

This report documents the financial evaluation framework, tracking operational dispatch costs, 
unmetered electricity revenue leakage, and baseline model economic consequences.

## 1. Financial Audit Trail: Provenance Separation

| Parameter | Value | Unit | Provenance | Description |
|---|---|---|---|---|
| `currency` | USD | ISO code | **ASSUMED** | Monetary currency unit for evaluation |
| `dispatch_cost` | 100.0 | USD | **ASSUMED** | Operational cost to dispatch a physical field inspection crew |
| `tariff_rate` | 0.15 | USD/kWh | **ASSUMED** | Configured regional benchmark tariff fallback |
| `undetected_billing_cycles` | 12 | months | **ASSUMED** | Estimated horizon undetected tampering continues before discovery |
| `estimated_leakage_cost` | Deficit kWh x Tariff x Horizon | USD | **DERIVED** | Derived financial impact of unmetered electricity theft |

## 2. Baseline Model Economic Outcome

- **Field Crew Dispatch Cost ($C_{dispatch}$)**: `USD 100.00`
- **Field Inspections Dispatched (TP + FP)**: `6,741`
  - True Positive (Productive Inspections): `3,161`
  - False Positive (Wasted Dispatches): `3,580`
- **False Negative (Undetected Thefts)**: `18,529`

### Financial Totals
- **Total Wasted FP Dispatch Cost**: `USD 358,000.00`
- **Total Undetected FN Revenue Leakage**: `USD 765,766.00`
- **Total Baseline Operational Loss**: `USD 1,123,766.00`
- **Estimated Gross Revenue Recovered**: `USD 1,447,265.25`
- **Estimated Net Financial Recovery**: `USD 773,165.25`

> [!NOTE]
> In Phase 4, the baseline model uses an ordinary unweighted 0.5 decision threshold without cost-sensitive 
> tuning. The baseline loss establishes the benchmark against which Phase 5/6 cost-sensitive models are compared.
