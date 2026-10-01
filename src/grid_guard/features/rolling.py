"""Rolling statistical feature extraction over trailing historical windows."""

from __future__ import annotations

import polars as pl

from grid_guard.features.registry import (
    FeatureCategory,
    FeatureDefinition,
    FeatureRegistry,
    LeakageRisk,
)


def register_rolling_features(
    registry: FeatureRegistry,
    windows: list[int],
    value_col: str = "consumption_kwh",
) -> None:
    """Register trailing rolling window features in the registry."""
    for w in windows:
        # Mean & Std for all windows
        registry.register(
            FeatureDefinition(
                name=f"rolling_mean_{w}d",
                category=FeatureCategory.ROLLING,
                source_columns=(value_col,),
                window_days=w,
                lag_days=None,
                description=f"Trailing {w}-day rolling mean consumption",
                dtype="Float32",
                leakage_risk=LeakageRisk.WARMUP_DEPENDENT,
                min_history_days=max(2, w // 2),
            )
        )
        registry.register(
            FeatureDefinition(
                name=f"rolling_std_{w}d",
                category=FeatureCategory.ROLLING,
                source_columns=(value_col,),
                window_days=w,
                lag_days=None,
                description=f"Trailing {w}-day rolling standard deviation of consumption",
                dtype="Float32",
                leakage_risk=LeakageRisk.WARMUP_DEPENDENT,
                min_history_days=max(3, w // 2),
            )
        )
        # Min & Max for core windows (7d, 30d)
        if w in (7, 30):
            registry.register(
                FeatureDefinition(
                    name=f"rolling_min_{w}d",
                    category=FeatureCategory.ROLLING,
                    source_columns=(value_col,),
                    window_days=w,
                    lag_days=None,
                    description=f"Trailing {w}-day minimum consumption reading",
                    dtype="Float32",
                    leakage_risk=LeakageRisk.WARMUP_DEPENDENT,
                    min_history_days=max(2, w // 2),
                )
            )
            registry.register(
                FeatureDefinition(
                    name=f"rolling_max_{w}d",
                    category=FeatureCategory.ROLLING,
                    source_columns=(value_col,),
                    window_days=w,
                    lag_days=None,
                    description=f"Trailing {w}-day maximum (peak) consumption reading",
                    dtype="Float32",
                    leakage_risk=LeakageRisk.WARMUP_DEPENDENT,
                    min_history_days=max(2, w // 2),
                )
            )
            registry.register(
                FeatureDefinition(
                    name=f"rolling_median_{w}d",
                    category=FeatureCategory.ROLLING,
                    source_columns=(value_col,),
                    window_days=w,
                    lag_days=None,
                    description=f"Trailing {w}-day median (50th percentile) consumption",
                    dtype="Float32",
                    leakage_risk=LeakageRisk.WARMUP_DEPENDENT,
                    min_history_days=max(2, w // 2),
                )
            )


class RollingFeatureExtractor:
    """Extracts trailing rolling statistics partitioned per meter."""

    def __init__(
        self,
        windows: list[int] | None = None,
        registry: FeatureRegistry | None = None,
    ) -> None:
        self.windows = sorted(windows or [7, 14, 30, 60, 90])
        self.registry = registry
        if self.registry is not None:
            register_rolling_features(self.registry, self.windows)

    def get_expressions(
        self,
        value_col: str = "consumption_kwh",
        meter_col: str = "meter_id",
    ) -> list[pl.Expr]:
        """Generate trailing rolling window Polars expressions.

        Args:
            value_col: Consumption readings column.
            meter_col: Meter identifier column.

        Returns:
            List of Polars expressions.
        """
        exprs: list[pl.Expr] = []
        c = pl.col(value_col)

        for w in self.windows:
            min_s = max(2, w // 2)
            exprs.append(
                c.rolling_mean(window_size=w, min_samples=min_s)
                .over(meter_col)
                .cast(pl.Float32)
                .alias(f"rolling_mean_{w}d")
            )
            exprs.append(
                c.rolling_std(window_size=w, min_samples=max(3, min_s))
                .over(meter_col)
                .cast(pl.Float32)
                .alias(f"rolling_std_{w}d")
            )
            if w in (7, 30):
                exprs.append(
                    c.rolling_min(window_size=w, min_samples=min_s)
                    .over(meter_col)
                    .cast(pl.Float32)
                    .alias(f"rolling_min_{w}d")
                )
                exprs.append(
                    c.rolling_max(window_size=w, min_samples=min_s)
                    .over(meter_col)
                    .cast(pl.Float32)
                    .alias(f"rolling_max_{w}d")
                )
                exprs.append(
                    c.rolling_median(window_size=w, min_samples=min_s)
                    .over(meter_col)
                    .cast(pl.Float32)
                    .alias(f"rolling_median_{w}d")
                )

        return exprs
