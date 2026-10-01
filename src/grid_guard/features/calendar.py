"""Calendar and cyclical temporal feature extraction."""

from __future__ import annotations

import math

import polars as pl

from grid_guard.features.registry import (
    FeatureCategory,
    FeatureDefinition,
    FeatureRegistry,
    LeakageRisk,
)


def register_calendar_features(registry: FeatureRegistry) -> None:
    """Register all calendar-derived features in the registry."""
    features = [
        FeatureDefinition(
            name="day_of_week",
            category=FeatureCategory.CALENDAR,
            source_columns=("timestamp",),
            window_days=None,
            lag_days=None,
            description="Day of week (1=Monday, 7=Sunday)",
            dtype="Int8",
            leakage_risk=LeakageRisk.SAFE,
        ),
        FeatureDefinition(
            name="day_of_month",
            category=FeatureCategory.CALENDAR,
            source_columns=("timestamp",),
            window_days=None,
            lag_days=None,
            description="Day of month (1-31)",
            dtype="Int8",
            leakage_risk=LeakageRisk.SAFE,
        ),
        FeatureDefinition(
            name="month",
            category=FeatureCategory.CALENDAR,
            source_columns=("timestamp",),
            window_days=None,
            lag_days=None,
            description="Calendar month (1-12)",
            dtype="Int8",
            leakage_risk=LeakageRisk.SAFE,
        ),
        FeatureDefinition(
            name="quarter",
            category=FeatureCategory.CALENDAR,
            source_columns=("timestamp",),
            window_days=None,
            lag_days=None,
            description="Calendar quarter (1-4)",
            dtype="Int8",
            leakage_risk=LeakageRisk.SAFE,
        ),
        FeatureDefinition(
            name="is_weekend",
            category=FeatureCategory.CALENDAR,
            source_columns=("timestamp",),
            window_days=None,
            lag_days=None,
            description="Binary indicator for Saturday or Sunday (1=Weekend, 0=Weekday)",
            dtype="Int8",
            leakage_risk=LeakageRisk.SAFE,
        ),
        FeatureDefinition(
            name="dow_sin",
            category=FeatureCategory.CALENDAR,
            source_columns=("timestamp",),
            window_days=None,
            lag_days=None,
            description="Cyclical sine encoding of day of week",
            dtype="Float32",
            leakage_risk=LeakageRisk.SAFE,
        ),
        FeatureDefinition(
            name="dow_cos",
            category=FeatureCategory.CALENDAR,
            source_columns=("timestamp",),
            window_days=None,
            lag_days=None,
            description="Cyclical cosine encoding of day of week",
            dtype="Float32",
            leakage_risk=LeakageRisk.SAFE,
        ),
        FeatureDefinition(
            name="month_sin",
            category=FeatureCategory.CALENDAR,
            source_columns=("timestamp",),
            window_days=None,
            lag_days=None,
            description="Cyclical sine encoding of calendar month",
            dtype="Float32",
            leakage_risk=LeakageRisk.SAFE,
        ),
        FeatureDefinition(
            name="month_cos",
            category=FeatureCategory.CALENDAR,
            source_columns=("timestamp",),
            window_days=None,
            lag_days=None,
            description="Cyclical cosine encoding of calendar month",
            dtype="Float32",
            leakage_risk=LeakageRisk.SAFE,
        ),
    ]
    for feat in features:
        registry.register(feat)


class CalendarFeatureExtractor:
    """Extracts calendar and cyclical temporal representations from timestamps."""

    def __init__(self, registry: FeatureRegistry | None = None) -> None:
        self.registry = registry
        if self.registry is not None:
            register_calendar_features(self.registry)

    def get_expressions(self, timestamp_col: str = "timestamp") -> list[pl.Expr]:
        """Generate Polars expressions for calendar features.

        Args:
            timestamp_col: Name of the timestamp or date column.

        Returns:
            List of Polars expressions.
        """
        pi2 = 2.0 * math.pi
        col = pl.col(timestamp_col)

        dow = col.dt.weekday()
        dom = col.dt.day()
        m = col.dt.month()
        q = col.dt.quarter()

        return [
            dow.cast(pl.Int8).alias("day_of_week"),
            dom.cast(pl.Int8).alias("day_of_month"),
            m.cast(pl.Int8).alias("month"),
            q.cast(pl.Int8).alias("quarter"),
            (dow >= 6).cast(pl.Int8).alias("is_weekend"),
            (dow * (pi2 / 7.0)).sin().cast(pl.Float32).alias("dow_sin"),
            (dow * (pi2 / 7.0)).cos().cast(pl.Float32).alias("dow_cos"),
            (m * (pi2 / 12.0)).sin().cast(pl.Float32).alias("month_sin"),
            (m * (pi2 / 12.0)).cos().cast(pl.Float32).alias("month_cos"),
        ]
