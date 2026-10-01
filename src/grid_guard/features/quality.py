"""Data quality feature propagation and trailing missingness indicators."""

from __future__ import annotations

import polars as pl

from grid_guard.features.registry import (
    FeatureCategory,
    FeatureDefinition,
    FeatureRegistry,
    LeakageRisk,
)


def register_quality_features(registry: FeatureRegistry) -> None:
    """Register data quality features in the registry."""
    features = [
        FeatureDefinition(
            name="coverage_ratio",
            category=FeatureCategory.DATA_QUALITY,
            source_columns=("coverage_ratio",),
            window_days=None,
            lag_days=None,
            description="Historical proportion of valid observed days per meter",
            dtype="Float32",
            leakage_risk=LeakageRisk.SAFE,
            min_history_days=1,
        ),
        FeatureDefinition(
            name="missing_ratio",
            category=FeatureCategory.DATA_QUALITY,
            source_columns=("missing_ratio",),
            window_days=None,
            lag_days=None,
            description="Historical proportion of missing reading days per meter",
            dtype="Float32",
            leakage_risk=LeakageRisk.SAFE,
            min_history_days=1,
        ),
        FeatureDefinition(
            name="imputation_ratio",
            category=FeatureCategory.DATA_QUALITY,
            source_columns=("imputation_ratio",),
            window_days=None,
            lag_days=None,
            description="Historical proportion of values linearly imputed during cleaning",
            dtype="Float32",
            leakage_risk=LeakageRisk.SAFE,
            min_history_days=1,
        ),
        FeatureDefinition(
            name="missing_count_30d",
            category=FeatureCategory.DATA_QUALITY,
            source_columns=("consumption_kwh",),
            window_days=30,
            lag_days=None,
            description="Trailing 30-day count of null / missing readings for this meter",
            dtype="Int8",
            leakage_risk=LeakageRisk.WARMUP_DEPENDENT,
            min_history_days=30,
        ),
        FeatureDefinition(
            name="missing_ratio_30d",
            category=FeatureCategory.DATA_QUALITY,
            source_columns=("consumption_kwh",),
            window_days=30,
            lag_days=None,
            description="Trailing 30-day proportion of null / missing readings for this meter",
            dtype="Float32",
            leakage_risk=LeakageRisk.WARMUP_DEPENDENT,
            min_history_days=30,
        ),
    ]
    for feat in features:
        registry.register(feat)


class QualityFeatureExtractor:
    """Extracts trailing missingness indicators and ensures Phase 2 quality flags are preserved."""

    def __init__(self, registry: FeatureRegistry | None = None) -> None:
        self.registry = registry
        if self.registry is not None:
            register_quality_features(self.registry)

    def get_expressions(
        self,
        value_col: str = "consumption_kwh",
        meter_col: str = "meter_id",
    ) -> list[pl.Expr]:
        """Generate trailing missingness Polars expressions.

        Args:
            value_col: Consumption column name.
            meter_col: Meter identifier column.

        Returns:
            List of Polars expressions.
        """
        is_missing = (pl.col(value_col).is_null() | pl.col(value_col).is_nan()).fill_null(False)

        missing_count_30d = (
            is_missing.cast(pl.Int8)
            .rolling_sum(window_size=30, min_samples=1)
            .over(meter_col)
            .cast(pl.Int8)
            .alias("missing_count_30d")
        )

        missing_ratio_30d = (
            (missing_count_30d.cast(pl.Float32) / 30.0).cast(pl.Float32).alias("missing_ratio_30d")
        )

        return [missing_count_30d, missing_ratio_30d]
