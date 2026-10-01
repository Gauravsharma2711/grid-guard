"""Unit tests for financial cost evaluation and revenue leakage estimation."""

from __future__ import annotations

import polars as pl

from grid_guard.config.financial import FinancialAssumptions
from grid_guard.evaluation.financial import (
    DataSourceType,
    FinancialCostEvaluator,
    LeakageEstimator,
)


def test_leakage_estimator_calculation() -> None:
    """Verify daily deficit, monthly volume, and cumulative revenue leakage calculations."""
    assumptions = FinancialAssumptions(
        default_tariff=0.20,
        undetected_cycles=6,
        min_leakage_kwh=2.0,
    )
    estimator = LeakageEstimator(assumptions=assumptions)

    df = pl.DataFrame(
        {
            "meter_id": ["M1", "M2", "M3"],
            "rolling_mean_60d": [10.0, 15.0, 5.0],
            "rolling_mean_14d": [
                2.0,
                14.5,
                5.0,
            ],  # M1 deficit=8, M2 deficit=0.5 (< min 2.0), M3 deficit=0
        }
    )

    enriched = estimator.estimate_leakage_polars(df)

    # M1: deficit = 8.0 kWh, monthly = 8.0 * 30 = 240 kWh, cost = 240 * 0.20 * 6 = $288.0
    m1 = enriched.filter(pl.col("meter_id") == "M1")
    assert abs(m1["leakage_daily_kwh"][0] - 8.0) < 1e-4
    assert abs(m1["leakage_monthly_kwh"][0] - 240.0) < 1e-4
    assert abs(m1["estimated_leakage_cost"][0] - 288.0) < 1e-4

    # M2: deficit = 0.5 < 2.0 min_leakage_kwh -> clamped to 0.0
    m2 = enriched.filter(pl.col("meter_id") == "M2")
    assert m2["leakage_daily_kwh"][0] == 0.0
    assert m2["estimated_leakage_cost"][0] == 0.0


def test_financial_cost_evaluation() -> None:
    """Verify dispatch costs, leakage penalties, operational losses, and recoveries."""
    assumptions = FinancialAssumptions(
        currency="USD",
        dispatch_cost=75.0,
    )
    evaluator = FinancialCostEvaluator(assumptions=assumptions)

    # 4 records: 1 TP, 1 FP, 1 FN, 1 TN
    y_true = [1, 0, 1, 0]
    y_pred = [1, 1, 0, 0]
    leakage_costs = [500.0, 0.0, 300.0, 0.0]

    res = evaluator.evaluate(y_true, y_pred, leakage_costs)
    counts = res["counts"]
    fin = res["financial_breakdown"]

    assert counts["tp"] == 1
    assert counts["fp"] == 1
    assert counts["fn"] == 1
    assert counts["tn"] == 1
    assert counts["total_inspections"] == 2

    # FP dispatch cost = 1 * $75 = $75
    assert fin["total_fp_dispatch_cost"] == 75.0
    # FN leakage cost = $300
    assert fin["total_fn_leakage_cost"] == 300.0
    # Total operational loss = $75 + $300 = $375
    assert fin["total_baseline_operational_loss"] == 375.0

    # TP: gross recovery = $500, inspection = $75 -> net recovery = 500 - 75 (TP) - 75 (FP) = $350
    assert fin["estimated_gross_recovery"] == 500.0
    assert fin["estimated_net_recovery"] == 350.0


def test_financial_audit_trail_and_report_export(tmp_path) -> None:
    """Verify audit trail provenance categorization and Markdown export."""
    evaluator = FinancialCostEvaluator()
    trail = evaluator.get_audit_trail(has_observed_tariff=False)

    sources = {t.parameter_name: t.source_type for t in trail}
    assert sources["dispatch_cost"] == DataSourceType.ASSUMED
    assert sources["tariff_rate"] == DataSourceType.ASSUMED
    assert sources["estimated_leakage_cost"] == DataSourceType.DERIVED

    # Test report export
    mock_metrics = evaluator.evaluate([1, 0], [1, 0], [100.0, 0.0])
    out_file = tmp_path / "financial_report.md"
    evaluator.export_report_markdown(mock_metrics, out_file)

    assert out_file.is_file()
    content = out_file.read_text(encoding="utf-8")
    assert "Grid-Guard Financial Cost & Revenue Leakage Report" in content
    assert "DERIVED" in content
