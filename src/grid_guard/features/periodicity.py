"""Periodicity, weekly autocorrelation, and profile deviation features."""

from __future__ import annotations

import polars as pl

from grid_guard.features.ratios import safe_div_expr
from grid_guard.features.registry import (
    FeatureCategory,
    FeatureDefinition,
    FeatureRegistry,
    LeakageRisk,
)


def register_periodicity_features(registry: FeatureRegistry) -> None:
    """Register periodicity and profile deviation features in registry."""
    features = [
        FeatureDefinition(
            name="dow_profile_deviation",
            category=FeatureCategory.AUTOCORRELATION,
            source_columns=("consumption_kwh",),
            window_days=28,
            lag_days=7,
            description="Difference between current reading and average of past 4 same-weekday readings",
            dtype="Float32",
            leakage_risk=LeakageRisk.WARMUP_DEPENDENT,
            min_history_days=28,
        ),
        FeatureDefinition(
            name="dow_profile_ratio",
            category=FeatureCategory.AUTOCORRELATION,
            source_columns=("consumption_kwh",),
            window_days=28,
            lag_days=7,
            description="Ratio of current reading to average of past 4 same-weekday readings",
            dtype="Float32",
            leakage_risk=LeakageRisk.WARMUP_DEPENDENT,
            min_history_days=28,
        ),
        FeatureDefinition(
            name="weekly_autocorr_30d",
            category=FeatureCategory.AUTOCORRELATION,
            source_columns=("consumption_kwh",),
            window_days=30,
            lag_days=7,
            description="Trailing 30-day autocorrelation with 7-day backward lag",
            dtype="Float32",
            leakage_risk=LeakageRisk.WARMUP_DEPENDENT,
            min_history_days=37,
        ),
    ]
    for feat in features:
        registry.register(feat)


class PeriodicityFeatureExtractor:
    """Extracts weekly periodicity, autocorrelation, and personal profile deviations."""

    def __init__(
        self,
        epsilon: float = 1e-4,
        registry: FeatureRegistry | None = None,
    ) -> None:
        self.epsilon = epsilon
        self.registry = registry
        if self.registry is not None:
            register_periodicity_features(self.registry)

    def get_expressions(
        self,
        value_col: str = "consumption_kwh",
        meter_col: str = "meter_id",
    ) -> list[pl.Expr]:
        """Generate periodicity and autocorrelation Polars expressions.

        Args:
            value_col: Consumption column name.
            meter_col: Meter identifier column.

        Returns:
            List of Polars expressions.
        """
        c = pl.col(value_col)
        eps = self.epsilon

        # Same day-of-week lags from past 4 weeks
        lag7 = c.shift(7).over(meter_col)
        lag14 = c.shift(14).over(meter_col)
        lag21 = c.shift(21).over(meter_col)
        lag28 = c.shift(28).over(meter_col)

        dow_baseline = (lag7 + lag14 + lag21 + lag28) / 4.0

        dow_profile_dev = (c - dow_baseline).cast(pl.Float32).alias("dow_profile_deviation")

        dow_profile_ratio = (
            safe_div_expr(
                c,
                dow_baseline,
                epsilon=eps,
                default_zero_over_zero=1.0,
            )
            .cast(pl.Float32)
            .alias("dow_profile_ratio")
        )

        # Weekly autocorrelation over trailing 30-day window
        # Covariance between c and lag7 over 30d
        mean_x = c.rolling_mean(window_size=30, min_samples=15).over(meter_col)
        mean_y = lag7.rolling_mean(window_size=30, min_samples=15).over(meter_col)
        std_x = c.rolling_std(window_size=30, min_samples=15).over(meter_col)
        std_y = lag7.rolling_std(window_size=30, min_samples=15).over(meter_col)

        cov = (
            ((c - mean_x) * (lag7 - mean_y))
            .rolling_mean(window_size=30, min_samples=15)
            .over(meter_col)
        )
        raw_corr = cov / (std_x * std_y + eps)

        weekly_autocorr = (
            pl.when(std_x > eps)
            .then(raw_corr.clip(-1.0, 1.0))
            .otherwise(pl.lit(0.0))
            .cast(pl.Float32)
            .alias("weekly_autocorr_30d")
        )

        return [dow_profile_dev, dow_profile_ratio, weekly_autocorr]
