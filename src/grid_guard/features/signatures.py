"""Electricity theft and meter tampering signature extraction."""

from __future__ import annotations

import polars as pl

from grid_guard.features.ratios import safe_div_expr
from grid_guard.features.registry import (
    FeatureCategory,
    FeatureDefinition,
    FeatureRegistry,
    LeakageRisk,
)


def register_signature_features(registry: FeatureRegistry) -> None:
    """Register all tampering signature features in registry."""
    features = [
        # Zero consumption signatures
        FeatureDefinition(
            name="zero_count_7d",
            category=FeatureCategory.ZERO_STREAK,
            source_columns=("consumption_kwh",),
            window_days=7,
            lag_days=None,
            description="Number of zero or near-zero consumption days in trailing 7 days",
            dtype="Int8",
            leakage_risk=LeakageRisk.WARMUP_DEPENDENT,
            min_history_days=7,
        ),
        FeatureDefinition(
            name="zero_ratio_7d",
            category=FeatureCategory.ZERO_STREAK,
            source_columns=("consumption_kwh",),
            window_days=7,
            lag_days=None,
            description="Proportion of zero or near-zero days in trailing 7 days",
            dtype="Float32",
            leakage_risk=LeakageRisk.WARMUP_DEPENDENT,
            min_history_days=7,
        ),
        FeatureDefinition(
            name="zero_count_30d",
            category=FeatureCategory.ZERO_STREAK,
            source_columns=("consumption_kwh",),
            window_days=30,
            lag_days=None,
            description="Number of zero or near-zero consumption days in trailing 30 days",
            dtype="Int8",
            leakage_risk=LeakageRisk.WARMUP_DEPENDENT,
            min_history_days=30,
        ),
        FeatureDefinition(
            name="zero_ratio_30d",
            category=FeatureCategory.ZERO_STREAK,
            source_columns=("consumption_kwh",),
            window_days=30,
            lag_days=None,
            description="Proportion of zero or near-zero days in trailing 30 days",
            dtype="Float32",
            leakage_risk=LeakageRisk.WARMUP_DEPENDENT,
            min_history_days=30,
        ),
        FeatureDefinition(
            name="current_zero_streak",
            category=FeatureCategory.ZERO_STREAK,
            source_columns=("consumption_kwh",),
            window_days=None,
            lag_days=None,
            description="Current trailing count of consecutive zero-consumption days",
            dtype="Int32",
            leakage_risk=LeakageRisk.SAFE,
            min_history_days=1,
        ),
        # Flatline & Variability signatures
        FeatureDefinition(
            name="rolling_cv_7d",
            category=FeatureCategory.VARIABILITY,
            source_columns=("rolling_std_7d", "rolling_mean_7d"),
            window_days=7,
            lag_days=None,
            description="Trailing 7-day coefficient of variation (std / safe(mean))",
            dtype="Float32",
            leakage_risk=LeakageRisk.WARMUP_DEPENDENT,
            min_history_days=7,
        ),
        FeatureDefinition(
            name="rolling_cv_30d",
            category=FeatureCategory.VARIABILITY,
            source_columns=("rolling_std_30d", "rolling_mean_30d"),
            window_days=30,
            lag_days=None,
            description="Trailing 30-day coefficient of variation (std / safe(mean))",
            dtype="Float32",
            leakage_risk=LeakageRisk.WARMUP_DEPENDENT,
            min_history_days=30,
        ),
        FeatureDefinition(
            name="daily_diff_abs_7d_mean",
            category=FeatureCategory.VARIABILITY,
            source_columns=("consumption_kwh",),
            window_days=7,
            lag_days=None,
            description="Trailing 7-day mean of absolute day-to-day consumption changes",
            dtype="Float32",
            leakage_risk=LeakageRisk.WARMUP_DEPENDENT,
            min_history_days=8,
        ),
        FeatureDefinition(
            name="flatline_streak",
            category=FeatureCategory.VARIABILITY,
            source_columns=("consumption_kwh",),
            window_days=None,
            lag_days=None,
            description="Trailing consecutive days of near-constant consumption (|diff| <= tol)",
            dtype="Int32",
            leakage_risk=LeakageRisk.SAFE,
            min_history_days=2,
        ),
        # Sustained Step-Down signatures
        FeatureDefinition(
            name="baseline_deviation_ratio",
            category=FeatureCategory.STEP_DOWN,
            source_columns=("rolling_mean_14d", "rolling_mean_60d"),
            window_days=74,
            lag_days=14,
            description="Ratio of recent 14-day consumption to historical baseline (60d shifted by 14d)",
            dtype="Float32",
            leakage_risk=LeakageRisk.WARMUP_DEPENDENT,
            min_history_days=74,
        ),
        FeatureDefinition(
            name="sustained_drop_ratio",
            category=FeatureCategory.STEP_DOWN,
            source_columns=("rolling_mean_14d", "rolling_mean_60d"),
            window_days=74,
            lag_days=14,
            description="Fractional drop from baseline: max(0, 1 - (recent_14d / safe(baseline_60d)))",
            dtype="Float32",
            leakage_risk=LeakageRisk.WARMUP_DEPENDENT,
            min_history_days=74,
        ),
        FeatureDefinition(
            name="sustained_drop_magnitude",
            category=FeatureCategory.STEP_DOWN,
            source_columns=("rolling_mean_14d", "rolling_mean_60d"),
            window_days=74,
            lag_days=14,
            description="Absolute consumption collapse: max(0, baseline_60d - recent_14d) in kWh",
            dtype="Float32",
            leakage_risk=LeakageRisk.WARMUP_DEPENDENT,
            min_history_days=74,
        ),
        FeatureDefinition(
            name="sustained_drop_duration",
            category=FeatureCategory.STEP_DOWN,
            source_columns=("consumption_kwh", "rolling_mean_60d"),
            window_days=74,
            lag_days=14,
            description="Trailing consecutive days where consumption < 50% of historical baseline",
            dtype="Int32",
            leakage_risk=LeakageRisk.WARMUP_DEPENDENT,
            min_history_days=74,
        ),
    ]
    for feat in features:
        registry.register(feat)


class TamperingSignatureExtractor:
    """Extracts electricity theft behavioral signatures: zero streaks, flatlines, and step-downs."""

    def __init__(
        self,
        zero_threshold: float = 0.001,
        flatline_tolerance: float = 0.01,
        epsilon: float = 1e-4,
        registry: FeatureRegistry | None = None,
    ) -> None:
        self.zero_threshold = zero_threshold
        self.flatline_tolerance = flatline_tolerance
        self.epsilon = epsilon
        self.registry = registry
        if self.registry is not None:
            register_signature_features(self.registry)

    def get_expressions(
        self,
        value_col: str = "consumption_kwh",
        meter_col: str = "meter_id",
    ) -> list[pl.Expr]:
        """Generate tampering signature expressions.

        Args:
            value_col: Consumption column name.
            meter_col: Meter identifier column.

        Returns:
            List of Polars expressions.
        """
        c = pl.col(value_col)
        eps = self.epsilon
        zero_th = self.zero_threshold
        flat_tol = self.flatline_tolerance

        # 1. Zero Indicators & Rolling Counts/Ratios
        is_zero = (c <= zero_th).fill_null(False)
        zero_count_7d = (
            is_zero.cast(pl.Int8)
            .rolling_sum(window_size=7, min_samples=4)
            .over(meter_col)
            .cast(pl.Int8)
            .alias("zero_count_7d")
        )
        zero_ratio_7d = (
            (
                is_zero.cast(pl.Float32).rolling_sum(window_size=7, min_samples=4).over(meter_col)
                / 7.0
            )
            .cast(pl.Float32)
            .alias("zero_ratio_7d")
        )

        zero_count_30d = (
            is_zero.cast(pl.Int8)
            .rolling_sum(window_size=30, min_samples=15)
            .over(meter_col)
            .cast(pl.Int8)
            .alias("zero_count_30d")
        )
        zero_ratio_30d = (
            (
                is_zero.cast(pl.Float32).rolling_sum(window_size=30, min_samples=15).over(meter_col)
                / 30.0
            )
            .cast(pl.Float32)
            .alias("zero_ratio_30d")
        )

        # Current Zero Streak via Run-Length Encoding
        rle_zero = (
            (is_zero != is_zero.shift(1).over(meter_col))
            .fill_null(False)
            .cast(pl.Int32)
            .cum_sum()
            .over(meter_col)
        )
        current_zero_streak = (
            pl.when(is_zero)
            .then((pl.int_range(0, pl.len()) + 1).over([meter_col, rle_zero]))
            .otherwise(0)
            .cast(pl.Int32)
            .alias("current_zero_streak")
        )

        # 2. Variability & Flatline Indicators
        rolling_cv_7d = (
            safe_div_expr(
                pl.col("rolling_std_7d"),
                pl.col("rolling_mean_7d"),
                epsilon=eps,
                default_zero_over_zero=0.0,
            )
            .cast(pl.Float32)
            .alias("rolling_cv_7d")
        )

        rolling_cv_30d = (
            safe_div_expr(
                pl.col("rolling_std_30d"),
                pl.col("rolling_mean_30d"),
                epsilon=eps,
                default_zero_over_zero=0.0,
            )
            .cast(pl.Float32)
            .alias("rolling_cv_30d")
        )

        daily_diff = (c - c.shift(1).over(meter_col)).abs()
        daily_diff_abs_7d_mean = (
            daily_diff.rolling_mean(window_size=7, min_samples=4)
            .over(meter_col)
            .cast(pl.Float32)
            .alias("daily_diff_abs_7d_mean")
        )

        is_flat = (daily_diff <= flat_tol).fill_null(False)
        rle_flat = (
            (is_flat != is_flat.shift(1).over(meter_col))
            .fill_null(False)
            .cast(pl.Int32)
            .cum_sum()
            .over(meter_col)
        )
        flatline_streak = (
            pl.when(is_flat)
            .then((pl.int_range(0, pl.len()) + 1).over([meter_col, rle_flat]))
            .otherwise(0)
            .cast(pl.Int32)
            .alias("flatline_streak")
        )

        # 3. Sustained Step-Down Signatures
        # Baseline: 60-day trailing mean shifted by 14 days
        baseline_60d_lag14 = pl.col("rolling_mean_60d").shift(14).over(meter_col)
        recent_14d = pl.col("rolling_mean_14d")

        baseline_deviation_ratio = (
            safe_div_expr(
                recent_14d,
                baseline_60d_lag14,
                epsilon=eps,
                default_zero_over_zero=1.0,
            )
            .cast(pl.Float32)
            .alias("baseline_deviation_ratio")
        )

        sustained_drop_ratio = (
            pl.when(baseline_60d_lag14.is_not_null() & (baseline_60d_lag14 > eps))
            .then(
                pl.max_horizontal(
                    pl.lit(0.0),
                    pl.lit(1.0) - (recent_14d / baseline_60d_lag14),
                )
            )
            .otherwise(pl.lit(None))
            .cast(pl.Float32)
            .alias("sustained_drop_ratio")
        )

        sustained_drop_magnitude = (
            pl.when(baseline_60d_lag14.is_not_null())
            .then(
                pl.max_horizontal(
                    pl.lit(0.0),
                    baseline_60d_lag14 - recent_14d,
                )
            )
            .otherwise(pl.lit(None))
            .cast(pl.Float32)
            .alias("sustained_drop_magnitude")
        )

        # Streak of consecutive days where daily consumption < 50% of historical baseline
        is_depressed = ((c < (0.5 * baseline_60d_lag14)) & (baseline_60d_lag14 > 0.1)).fill_null(
            False
        )

        rle_dep = (
            (is_depressed != is_depressed.shift(1).over(meter_col))
            .fill_null(False)
            .cast(pl.Int32)
            .cum_sum()
            .over(meter_col)
        )
        sustained_drop_duration = (
            pl.when(is_depressed)
            .then((pl.int_range(0, pl.len()) + 1).over([meter_col, rle_dep]))
            .otherwise(0)
            .cast(pl.Int32)
            .alias("sustained_drop_duration")
        )

        return [
            zero_count_7d,
            zero_ratio_7d,
            zero_count_30d,
            zero_ratio_30d,
            current_zero_streak,
            rolling_cv_7d,
            rolling_cv_30d,
            daily_diff_abs_7d_mean,
            flatline_streak,
            baseline_deviation_ratio,
            sustained_drop_ratio,
            sustained_drop_magnitude,
            sustained_drop_duration,
        ]
