"""Financial cost model, revenue leakage estimation, and inspection cost evaluation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

import polars as pl

from grid_guard.config.financial import FinancialAssumptions


class DataSourceType(StrEnum):
    """Categorization of financial data integrity provenance."""

    OBSERVED = "observed"  # Value directly present in source dataset
    DERIVED = "derived"  # Computed mathematically from observed dataset columns
    ASSUMED = "assumed"  # External business/operational assumption from configuration


@dataclass(frozen=True)
class FinancialAuditRecord:
    """Provenance tracking for a financial parameter."""

    parameter_name: str
    value: Any
    unit: str
    source_type: DataSourceType
    description: str


class LeakageEstimator:
    """Estimates unmetered electrical consumption and financial revenue leakage."""

    def __init__(self, assumptions: FinancialAssumptions | None = None) -> None:
        self.config = assumptions or FinancialAssumptions()

    def estimate_leakage_polars(
        self,
        df: pl.DataFrame,
        baseline_col: str = "rolling_mean_60d",
        observed_col: str = "rolling_mean_14d",
        tariff_col: str | None = None,
    ) -> pl.DataFrame:
        """Calculate per-meter daily deficit, monthly leakage volume, and cumulative loss.

        Args:
            df: Input DataFrame containing baseline and observed consumption columns.
            baseline_col: Historical pre-tampering normal consumption column.
            observed_col: Recent observed consumption column.
            tariff_col: Optional column name for per-meter custom tariff rate.

        Returns:
            DataFrame with leakage volume (kWh) and leakage cost appended.
        """
        # Cache columns set
        cols = df.collect_schema().names() if isinstance(df, pl.LazyFrame) else df.columns

        # Determine tariff expression (observed column or assumed fallback)
        if tariff_col and tariff_col in cols:
            tariff_expr = pl.col(tariff_col).fill_null(self.config.default_tariff)
        else:
            tariff_expr = pl.lit(self.config.default_tariff)

        # Resolve baseline column with fallback candidates
        if baseline_col not in cols:
            for alt in [
                "baseline_consumption_60d",
                "rolling_mean_60d",
                "rolling_mean_30d",
                "rolling_mean_7d",
            ]:
                if alt in cols:
                    baseline_col = alt
                    break

        # Resolve observed column with fallback candidates
        if observed_col not in cols:
            for alt in [
                "rolling_mean_14d",
                "rolling_mean_7d",
                "daily_consumption_kwh",
                "consumption_kwh",
            ]:
                if alt in cols:
                    observed_col = alt
                    break

        base = pl.col(baseline_col).fill_null(0.0) if baseline_col in cols else pl.lit(0.0)
        obs = pl.col(observed_col).fill_null(0.0) if observed_col in cols else pl.lit(0.0)

        # Daily deficit in kWh: max(0.0, baseline - observed)
        raw_deficit = pl.max_horizontal(pl.lit(0.0), base - obs)
        daily_deficit = (
            pl.when(raw_deficit >= self.config.min_leakage_kwh)
            .then(raw_deficit)
            .otherwise(pl.lit(0.0))
            .cast(pl.Float32)
        )

        monthly_leakage_kwh = (daily_deficit * 30.0).cast(pl.Float32)
        cycle_revenue_loss = (monthly_leakage_kwh * tariff_expr).cast(pl.Float32)
        total_leakage_cost = (cycle_revenue_loss * float(self.config.undetected_cycles)).cast(
            pl.Float32
        )

        return df.with_columns(
            [
                daily_deficit.alias("leakage_daily_kwh"),
                monthly_leakage_kwh.alias("leakage_monthly_kwh"),
                total_leakage_cost.alias("estimated_leakage_cost"),
            ]
        )


class FinancialCostEvaluator:
    """Evaluates the financial consequences of classification outcomes (TP, FP, TN, FN)."""

    def __init__(self, assumptions: FinancialAssumptions | None = None) -> None:
        self.config = assumptions or FinancialAssumptions()

    def get_audit_trail(self, has_observed_tariff: bool = False) -> list[FinancialAuditRecord]:
        """Generate mandatory audit trail classifying Observed vs. Derived vs. Assumed values."""
        records = [
            FinancialAuditRecord(
                parameter_name="currency",
                value=self.config.currency,
                unit="ISO code",
                source_type=DataSourceType.ASSUMED,
                description="Monetary currency unit for evaluation",
            ),
            FinancialAuditRecord(
                parameter_name="dispatch_cost",
                value=self.config.dispatch_cost,
                unit=self.config.currency,
                source_type=DataSourceType.ASSUMED,
                description="Operational cost to dispatch a physical field inspection crew",
            ),
            FinancialAuditRecord(
                parameter_name="tariff_rate",
                value=self.config.default_tariff,
                unit=f"{self.config.currency}/kWh",
                source_type=(
                    DataSourceType.OBSERVED if has_observed_tariff else DataSourceType.ASSUMED
                ),
                description=(
                    "Observed meter tariff"
                    if has_observed_tariff
                    else "Configured regional benchmark tariff fallback"
                ),
            ),
            FinancialAuditRecord(
                parameter_name="undetected_billing_cycles",
                value=self.config.undetected_cycles,
                unit="months",
                source_type=DataSourceType.ASSUMED,
                description="Estimated horizon undetected tampering continues before discovery",
            ),
            FinancialAuditRecord(
                parameter_name="estimated_leakage_cost",
                value="Deficit kWh x Tariff x Horizon",
                unit=self.config.currency,
                source_type=DataSourceType.DERIVED,
                description="Derived financial impact of unmetered electricity theft",
            ),
        ]
        return records

    def evaluate(
        self,
        y_true: list[int] | pl.Series,
        y_pred: list[int] | pl.Series,
        leakage_costs: list[float] | pl.Series,
    ) -> dict[str, Any]:
        """Compute operational costs, false positive dispatch waste, and leakage losses.

        Args:
            y_true: Ground truth binary labels (1=tampered, 0=normal).
            y_pred: Predicted binary labels (0 or 1 from threshold).
            leakage_costs: Estimated financial leakage impact per record ($C_FN_i$).

        Returns:
            Dictionary containing detailed financial outcome metrics.
        """
        c_dispatch = self.config.dispatch_cost

        # Convert to Polars Series if necessary
        s_true = y_true if isinstance(y_true, pl.Series) else pl.Series("true", y_true)
        s_pred = y_pred if isinstance(y_pred, pl.Series) else pl.Series("pred", y_pred)
        s_leak = (
            leakage_costs
            if isinstance(leakage_costs, pl.Series)
            else pl.Series("leak", leakage_costs)
        )

        df = pl.DataFrame(
            {
                "y_true": s_true.cast(pl.Int8),
                "y_pred": s_pred.cast(pl.Int8),
                "leakage_cost": s_leak.cast(pl.Float32).fill_null(0.0),
            }
        )

        is_tp = (pl.col("y_true") == 1) & (pl.col("y_pred") == 1)
        is_fp = (pl.col("y_true") == 0) & (pl.col("y_pred") == 1)
        is_fn = (pl.col("y_true") == 1) & (pl.col("y_pred") == 0)
        is_tn = (pl.col("y_true") == 0) & (pl.col("y_pred") == 0)

        evaluated = df.with_columns(
            [
                is_tp.alias("is_tp"),
                is_fp.alias("is_fp"),
                is_fn.alias("is_fn"),
                is_tn.alias("is_tn"),
                pl.when(is_fp).then(pl.lit(c_dispatch)).otherwise(0.0).alias("fp_dispatch_cost"),
                pl.when(is_fn).then(pl.col("leakage_cost")).otherwise(0.0).alias("fn_leakage_cost"),
                pl.when(is_tp).then(pl.lit(c_dispatch)).otherwise(0.0).alias("tp_dispatch_cost"),
                pl.when(is_tp)
                .then(pl.col("leakage_cost"))
                .otherwise(0.0)
                .alias("tp_recovered_leakage"),
            ]
        )

        fp_count = int(evaluated.get_column("is_fp").sum())
        fn_count = int(evaluated.get_column("is_fn").sum())
        tp_count = int(evaluated.get_column("is_tp").sum())
        tn_count = int(evaluated.get_column("is_tn").sum())

        total_fp_cost = float(evaluated.get_column("fp_dispatch_cost").sum())
        total_fn_cost = float(evaluated.get_column("fn_leakage_cost").sum())
        total_loss = total_fp_cost + total_fn_cost

        total_tp_dispatch = float(evaluated.get_column("tp_dispatch_cost").sum())
        gross_recovery = float(evaluated.get_column("tp_recovered_leakage").sum())
        net_recovery = gross_recovery - total_tp_dispatch - total_fp_cost

        result = {
            "currency": self.config.currency,
            "dispatch_cost_per_inspection": c_dispatch,
            "counts": {
                "tp": tp_count,
                "fp": fp_count,
                "tn": tn_count,
                "fn": fn_count,
                "total_inspections": tp_count + fp_count,
            },
            "financial_breakdown": {
                "total_fp_dispatch_cost": round(total_fp_cost, 2),
                "total_fn_leakage_cost": round(total_fn_cost, 2),
                "total_baseline_operational_loss": round(total_loss, 2),
                "total_tp_inspection_cost": round(total_tp_dispatch, 2),
                "estimated_gross_recovery": round(gross_recovery, 2),
                "estimated_net_recovery": round(net_recovery, 2),
            },
            "audit_trail": [asdict(r) for r in self.get_audit_trail()],
        }
        return result

    def export_report_markdown(
        self,
        metrics: dict[str, Any],
        output_path: Path | str,
    ) -> None:
        """Generate human-readable financial assumption and outcome report."""
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        curr = metrics.get("currency", "USD")
        counts = metrics.get("counts", {})
        fin = metrics.get("financial_breakdown", {})
        audit = metrics.get("audit_trail", [])

        lines = [
            "# Grid-Guard Financial Cost & Revenue Leakage Report",
            "",
            "This report documents the financial evaluation framework, tracking operational dispatch costs, ",
            "unmetered electricity revenue leakage, and baseline model economic consequences.",
            "",
            "## 1. Financial Audit Trail: Provenance Separation",
            "",
            "| Parameter | Value | Unit | Provenance | Description |",
            "|---|---|---|---|---|",
        ]
        for a in audit:
            lines.append(
                f"| `{a['parameter_name']}` | {a['value']} | {a['unit']} | "
                f"**{a['source_type'].upper()}** | {a['description']} |"
            )

        lines.extend(
            [
                "",
                "## 2. Baseline Model Economic Outcome",
                "",
                f"- **Field Crew Dispatch Cost ($C_{{dispatch}}$)**: `{curr} {metrics.get('dispatch_cost_per_inspection', 100.0):,.2f}`",
                f"- **Field Inspections Dispatched (TP + FP)**: `{counts.get('total_inspections', 0):,}`",
                f"  - True Positive (Productive Inspections): `{counts.get('tp', 0):,}`",
                f"  - False Positive (Wasted Dispatches): `{counts.get('fp', 0):,}`",
                f"- **False Negative (Undetected Thefts)**: `{counts.get('fn', 0):,}`",
                "",
                "### Financial Totals",
                f"- **Total Wasted FP Dispatch Cost**: `{curr} {fin.get('total_fp_dispatch_cost', 0.0):,.2f}`",
                f"- **Total Undetected FN Revenue Leakage**: `{curr} {fin.get('total_fn_leakage_cost', 0.0):,.2f}`",
                f"- **Total Baseline Operational Loss**: `{curr} {fin.get('total_baseline_operational_loss', 0.0):,.2f}`",
                f"- **Estimated Gross Revenue Recovered**: `{curr} {fin.get('estimated_gross_recovery', 0.0):,.2f}`",
                f"- **Estimated Net Financial Recovery**: `{curr} {fin.get('estimated_net_recovery', 0.0):,.2f}`",
                "",
                "> [!NOTE]",
                "> In Phase 4, the baseline model uses an ordinary unweighted 0.5 decision threshold without cost-sensitive ",
                "> tuning. The baseline loss establishes the benchmark against which Phase 5/6 cost-sensitive models are compared.",
            ]
        )

        with open(target, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
