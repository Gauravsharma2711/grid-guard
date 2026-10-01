"""Unit tests for Phase 3 temporal feature engineering and tampering signatures."""

from __future__ import annotations

from datetime import date

import polars as pl
import pytest

from grid_guard.features.calendar import CalendarFeatureExtractor
from grid_guard.features.context import ContextFeatureExtractor
from grid_guard.features.lags import LagFeatureExtractor
from grid_guard.features.pipeline import FeaturePipeline
from grid_guard.features.quality import QualityFeatureExtractor
from grid_guard.features.ratios import safe_div_expr
from grid_guard.features.registry import FeatureCategory, FeatureRegistry, LeakageRisk
from grid_guard.features.rolling import RollingFeatureExtractor
from grid_guard.features.signatures import TamperingSignatureExtractor
from tests.fixtures.synthetic_ami import (
    generate_synthetic_series,
)


def test_feature_registry_lifecycle(tmp_path) -> None:
    """Verify registration, lookup, category filtering, and export capabilities."""
    reg = FeatureRegistry()
    assert reg.count() == 0

    _ = FeaturePipeline(registry=reg)
    assert reg.count() > 30

    calendar_feats = reg.by_category(FeatureCategory.CALENDAR)
    assert len(calendar_feats) == 9

    sig_feats = reg.by_category(FeatureCategory.STEP_DOWN)
    assert len(sig_feats) == 4
    for f in sig_feats:
        assert f.leakage_risk == LeakageRisk.WARMUP_DEPENDENT

    # Test export
    json_path = tmp_path / "registry.json"
    md_path = tmp_path / "registry.md"
    reg.export_json(json_path)
    reg.export_markdown(md_path)

    assert json_path.is_file()
    assert md_path.is_file()
    assert "Grid-Guard Feature Dictionary" in md_path.read_text(encoding="utf-8")


def test_calendar_features() -> None:
    """Verify calendar feature extraction and cyclical harmonics."""
    extractor = CalendarFeatureExtractor()
    df = pl.DataFrame(
        {
            "timestamp": [
                date(2024, 1, 1),  # Monday
                date(2024, 1, 6),  # Saturday
                date(2024, 1, 7),  # Sunday
            ]
        }
    )
    res = df.with_columns(extractor.get_expressions())
    assert res.get_column("day_of_week").to_list() == [1, 6, 7]
    assert res.get_column("is_weekend").to_list() == [0, 1, 1]
    assert res.get_column("month").to_list() == [1, 1, 1]
    assert res.get_column("quarter").to_list() == [1, 1, 1]
    assert len(res.get_column("dow_sin")) == 3


def test_lag_features_and_leakage_safety() -> None:
    """Verify lag features look strictly backward and validate invalid lag rejection."""
    with pytest.raises(ValueError, match="strictly positive"):
        LagFeatureExtractor(lags=[0, 1])

    extractor = LagFeatureExtractor(lags=[1, 7])
    df = pl.DataFrame(
        {
            "meter_id": ["M1"] * 10,
            "consumption_kwh": [float(i) for i in range(10)],
        }
    )
    res = df.with_columns(extractor.get_expressions())
    lag1 = res.get_column("consumption_kwh_lag_1d").to_list()
    assert lag1[0] is None
    assert lag1[1] == 0.0
    assert lag1[9] == 8.0

    lag7 = res.get_column("consumption_kwh_lag_7d").to_list()
    assert lag7[6] is None
    assert lag7[7] == 0.0
    assert lag7[9] == 2.0


def test_rolling_features() -> None:
    """Verify trailing rolling window statistics."""
    extractor = RollingFeatureExtractor(windows=[7, 30])
    df = pl.DataFrame(
        {
            "meter_id": ["M1"] * 40,
            "consumption_kwh": [10.0] * 40,
        }
    )
    res = df.with_columns(extractor.get_expressions())
    # Mean should be 10.0, std should be 0.0
    means = res.get_column("rolling_mean_7d").drop_nulls().to_list()
    assert all(abs(m - 10.0) < 1e-4 for m in means)
    stds = res.get_column("rolling_std_7d").drop_nulls().to_list()
    assert all(abs(s - 0.0) < 1e-4 for s in stds)
    mins = res.get_column("rolling_min_7d").drop_nulls().to_list()
    assert all(m == 10.0 for m in mins)


def test_ratios_and_safe_division() -> None:
    """Verify safe division prevents division-by-zero without infinities."""
    df = pl.DataFrame(
        {
            "a": [10.0, 0.0, 5.0],
            "b": [2.0, 0.0, 0.0],
        }
    )
    res = df.select(
        safe=safe_div_expr(pl.col("a"), pl.col("b"), epsilon=1e-4, default_zero_over_zero=1.0)
    )
    vals = res["safe"].to_list()
    assert vals[0] == 5.0
    assert vals[1] == 1.0  # 0 / 0 safe default
    assert vals[2] is None  # 5 / 0 becomes null, not infinity


def test_zero_streak_detection() -> None:
    """Verify zero streak tracking and zero ratios on synthetic zero pattern."""
    df = generate_synthetic_series(pattern="zero_streak", num_days=80)
    extractor = TamperingSignatureExtractor()
    rolling = RollingFeatureExtractor()
    res = df.with_columns(rolling.get_expressions()).with_columns(extractor.get_expressions())

    # Days 50 to 61 have zero consumption
    streaks = res.get_column("current_zero_streak").to_list()
    assert streaks[49] == 0
    assert streaks[50] == 1
    assert streaks[51] == 2
    assert streaks[61] == 12
    assert streaks[62] == 0  # resumed normal consumption


def test_flatline_detection() -> None:
    """Verify flatline streak and variance collapse."""
    df = generate_synthetic_series(pattern="flatline", num_days=70)
    extractor = TamperingSignatureExtractor()
    rolling = RollingFeatureExtractor()
    res = df.with_columns(rolling.get_expressions()).with_columns(extractor.get_expressions())

    # Days 40 to 54 are constant 7.77
    flat_streaks = res.get_column("flatline_streak").to_list()
    assert flat_streaks[41] > 0
    assert flat_streaks[53] > 10


def test_step_down_detection() -> None:
    """Verify sustained step-down tampering detection signatures."""
    df = generate_synthetic_series(pattern="step_down", num_days=100)
    rolling = RollingFeatureExtractor(windows=[7, 14, 30, 60, 90])
    sigs = TamperingSignatureExtractor()

    res = df.with_columns(rolling.get_expressions()).with_columns(sigs.get_expressions())

    # Before day 70: normal baseline, drop ratio near 0
    drop_before = res.filter(pl.col("timestamp") < date(2020, 3, 10))[
        "sustained_drop_ratio"
    ].drop_nulls()
    if len(drop_before) > 0:
        assert drop_before.mean() < 0.2

    # After day 70: severe drop ratio > 0.6
    drop_after = res.filter(pl.col("timestamp") > date(2020, 3, 25))[
        "sustained_drop_ratio"
    ].drop_nulls()
    assert len(drop_after) > 0
    assert drop_after.mean() > 0.6

    # Duration should climb
    dur_after = res.filter(pl.col("timestamp") > date(2020, 3, 25))[
        "sustained_drop_duration"
    ].to_list()
    assert max(dur_after) > 5


def test_context_peer_features() -> None:
    """Verify leave-one-out peer calculation when feeder metadata exists."""
    df = pl.DataFrame(
        {
            "meter_id": ["M1", "M2", "M3", "M1", "M2", "M3"],
            "timestamp": [date(2020, 1, 1)] * 3 + [date(2020, 1, 2)] * 3,
            "consumption_kwh": [10.0, 20.0, 30.0, 15.0, 25.0, 35.0],
            "feeder_id": ["F1", "F1", "F1", "F1", "F1", "F1"],
        }
    )
    extractor = ContextFeatureExtractor()
    assert extractor.is_available(df.columns)

    res = extractor.extract(df)
    assert "peer_group_mean" in res.columns
    assert "meter_to_peer_ratio" in res.columns

    # For M1 at day 1: peers are M2 (20) and M3 (30) -> mean = 25.0
    m1_row = res.filter((pl.col("meter_id") == "M1") & (pl.col("timestamp") == date(2020, 1, 1)))
    peer_mean = m1_row["peer_group_mean"][0]
    assert abs(peer_mean - 25.0) < 1e-4
    assert abs(m1_row["meter_to_peer_ratio"][0] - (10.0 / 25.0)) < 1e-4


def test_quality_features() -> None:
    """Verify trailing missingness counts and ratios."""
    extractor = QualityFeatureExtractor()
    df = pl.DataFrame(
        {
            "meter_id": ["M1"] * 10,
            "consumption_kwh": [1.0, None, None, 4.0, 5.0, None, 7.0, 8.0, 9.0, 10.0],
        }
    )
    res = df.with_columns(extractor.get_expressions())
    assert "missing_count_30d" in res.columns
    assert "missing_ratio_30d" in res.columns
    assert res["missing_count_30d"][-1] == 3
