"""Multi-scale moving average ratios, PAR, and week-over-week behavior features."""

from __future__ import annotations

import polars as pl

from grid_guard.features.registry import (
    FeatureCategory,
    FeatureDefinition,
    FeatureRegistry,
    LeakageRisk,
)


def safe_div_expr(
    numerator: pl.Expr,
    denominator: pl.Expr,
    epsilon: float = 1e-4,
    default_zero_over_zero: float = 1.0,
) -> pl.Expr:
    """Safe division expression that prevents division by zero and infinity.

    Args:
        numerator: Numerator expression.
        denominator: Denominator expression.
        epsilon: Minimum denominator absolute magnitude.
        default_zero_over_zero: Value when both num and denom are near zero.

    Returns:
        Safe ratio expression.
    """
    return (
        pl.when(denominator.abs() > epsilon)
        .then(numerator / denominator)
        .when((numerator.abs() <= epsilon) & (denominator.abs() <= epsilon))
        .then(pl.lit(default_zero_over_zero))
        .otherwise(pl.lit(None))
    )


def register_ratio_features(registry: FeatureRegistry) -> None:
    """Register moving average ratios, WoW, and PAR features in registry."""
    features = [
        FeatureDefinition(
            name="ratio_7d_30d",
            category=FeatureCategory.RATIO,
            source_columns=("rolling_mean_7d", "rolling_mean_30d"),
            window_days=30,
            lag_days=None,
            description="Ratio of trailing 7-day mean to 30-day baseline mean",
            dtype="Float32",
            leakage_risk=LeakageRisk.WARMUP_DEPENDENT,
            min_history_days=30,
        ),
        FeatureDefinition(
            name="ratio_14d_60d",
            category=FeatureCategory.RATIO,
            source_columns=("rolling_mean_14d", "rolling_mean_60d"),
            window_days=60,
            lag_days=None,
            description="Ratio of trailing 14-day mean to 60-day baseline mean",
            dtype="Float32",
            leakage_risk=LeakageRisk.WARMUP_DEPENDENT,
            min_history_days=60,
        ),
        FeatureDefinition(
            name="ratio_30d_90d",
            category=FeatureCategory.RATIO,
            source_columns=("rolling_mean_30d", "rolling_mean_90d"),
            window_days=90,
            lag_days=None,
            description="Ratio of trailing 30-day mean to 90-day baseline mean",
            dtype="Float32",
            leakage_risk=LeakageRisk.WARMUP_DEPENDENT,
            min_history_days=90,
        ),
        FeatureDefinition(
            name="wow_consumption_change",
            category=FeatureCategory.BEHAVIOR_SHIFT,
            source_columns=("rolling_mean_7d",),
            window_days=14,
            lag_days=7,
            description="Absolute week-over-week difference in 7-day rolling mean",
            dtype="Float32",
            leakage_risk=LeakageRisk.WARMUP_DEPENDENT,
            min_history_days=14,
        ),
        FeatureDefinition(
            name="wow_consumption_ratio",
            category=FeatureCategory.BEHAVIOR_SHIFT,
            source_columns=("rolling_mean_7d",),
            window_days=14,
            lag_days=7,
            description="Ratio of current 7-day mean to preceding 7-day mean (lagged by 7d)",
            dtype="Float32",
            leakage_risk=LeakageRisk.WARMUP_DEPENDENT,
            min_history_days=14,
        ),
        FeatureDefinition(
            name="par_7d",
            category=FeatureCategory.PEAK,
            source_columns=("rolling_max_7d", "rolling_mean_7d"),
            window_days=7,
            lag_days=None,
            description="Peak-to-Average Ratio over trailing 7 days (max_7d / mean_7d)",
            dtype="Float32",
            leakage_risk=LeakageRisk.WARMUP_DEPENDENT,
            min_history_days=7,
        ),
        FeatureDefinition(
            name="par_30d",
            category=FeatureCategory.PEAK,
            source_columns=("rolling_max_30d", "rolling_mean_30d"),
            window_days=30,
            lag_days=None,
            description="Peak-to-Average Ratio over trailing 30 days (max_30d / mean_30d)",
            dtype="Float32",
            leakage_risk=LeakageRisk.WARMUP_DEPENDENT,
            min_history_days=30,
        ),
    ]
    for feat in features:
        registry.register(feat)


class RatioFeatureExtractor:
    """Extracts moving average ratios, WoW change, and Peak-to-Average Ratios."""

    def __init__(
        self,
        epsilon: float = 1e-4,
        registry: FeatureRegistry | None = None,
    ) -> None:
        self.epsilon = epsilon
        self.registry = registry
        if self.registry is not None:
            register_ratio_features(self.registry)

    def get_expressions(self, meter_col: str = "meter_id") -> list[pl.Expr]:
        """Generate ratio, WoW, and PAR Polars expressions.

        Expects rolling mean/max columns to be present or computed in the pipeline.

        Args:
            meter_col: Meter identifier column for partitioned lags.

        Returns:
            List of Polars expressions.
        """
        eps = self.epsilon

        # Multi-scale ratios
        r_7_30 = (
            safe_div_expr(
                pl.col("rolling_mean_7d"),
                pl.col("rolling_mean_30d"),
                epsilon=eps,
            )
            .cast(pl.Float32)
            .alias("ratio_7d_30d")
        )

        r_14_60 = (
            safe_div_expr(
                pl.col("rolling_mean_14d"),
                pl.col("rolling_mean_60d"),
                epsilon=eps,
            )
            .cast(pl.Float32)
            .alias("ratio_14d_60d")
        )

        r_30_90 = (
            safe_div_expr(
                pl.col("rolling_mean_30d"),
                pl.col("rolling_mean_90d"),
                epsilon=eps,
            )
            .cast(pl.Float32)
            .alias("ratio_30d_90d")
        )

        # Week-over-week expressions (using lagged 7-day rolling mean)
        lag7_mean_7d = pl.col("rolling_mean_7d").shift(7).over(meter_col)

        wow_change = (
            (pl.col("rolling_mean_7d") - lag7_mean_7d)
            .cast(pl.Float32)
            .alias("wow_consumption_change")
        )

        wow_ratio = (
            safe_div_expr(
                pl.col("rolling_mean_7d"),
                lag7_mean_7d,
                epsilon=eps,
            )
            .cast(pl.Float32)
            .alias("wow_consumption_ratio")
        )

        # Peak-to-Average Ratios
        par_7d = (
            safe_div_expr(
                pl.col("rolling_max_7d"),
                pl.col("rolling_mean_7d"),
                epsilon=eps,
                default_zero_over_zero=1.0,
            )
            .cast(pl.Float32)
            .alias("par_7d")
        )

        par_30d = (
            safe_div_expr(
                pl.col("rolling_max_30d"),
                pl.col("rolling_mean_30d"),
                epsilon=eps,
                default_zero_over_zero=1.0,
            )
            .cast(pl.Float32)
            .alias("par_30d")
        )

        return [r_7_30, r_14_60, r_30_90, wow_change, wow_ratio, par_7d, par_30d]
