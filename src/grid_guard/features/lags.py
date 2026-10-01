"""Lag feature extraction for AMI time series."""

from __future__ import annotations

import polars as pl

from grid_guard.features.registry import (
    FeatureCategory,
    FeatureDefinition,
    FeatureRegistry,
    LeakageRisk,
)


def register_lag_features(
    registry: FeatureRegistry,
    lags: list[int],
    value_col: str = "consumption_kwh",
) -> None:
    """Register backward lag features in the feature registry."""
    for lag in lags:
        if lag <= 0:
            raise ValueError(f"Lag must be strictly positive to prevent future leakage, got {lag}")
        registry.register(
            FeatureDefinition(
                name=f"{value_col}_lag_{lag}d",
                category=FeatureCategory.LAG,
                source_columns=(value_col,),
                window_days=None,
                lag_days=lag,
                description=f"Backward historical consumption reading shifted by {lag} days",
                dtype="Float32",
                leakage_risk=LeakageRisk.WARMUP_DEPENDENT,
                min_history_days=lag + 1,
            )
        )


class LagFeatureExtractor:
    """Extracts strictly historical backward lag features per meter."""

    def __init__(
        self,
        lags: list[int] | None = None,
        registry: FeatureRegistry | None = None,
    ) -> None:
        self.lags = sorted(lags or [1, 2, 3, 7, 14, 30])
        for lag in self.lags:
            if lag <= 0:
                raise ValueError(
                    f"Lag values must be strictly positive to prevent future leakage, got {lag}"
                )
        self.registry = registry
        if self.registry is not None:
            register_lag_features(self.registry, self.lags)

    def get_expressions(
        self,
        value_col: str = "consumption_kwh",
        meter_col: str = "meter_id",
    ) -> list[pl.Expr]:
        """Generate Polars lag expressions partitioned by meter.

        Args:
            value_col: Column name containing consumption readings.
            meter_col: Identifier column to group window operations over.

        Returns:
            List of Polars expressions.
        """
        exprs: list[pl.Expr] = []
        for lag in self.lags:
            exprs.append(
                pl.col(value_col)
                .shift(lag)
                .over(meter_col)
                .cast(pl.Float32)
                .alias(f"{value_col}_lag_{lag}d")
            )
        return exprs
