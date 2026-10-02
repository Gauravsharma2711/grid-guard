"""Unit tests for temporal source attribution."""

from datetime import date

from grid_guard.explainability.temporal_attribution import TemporalAttributor


def test_temporal_attribution_rolling_60d() -> None:
    """Test calendar window calculation for trailing 60d feature."""
    attributor = TemporalAttributor()
    anchor = "2016-10-30"
    evidence = attributor.attribute(
        feature_name="rolling_std_60d",
        anchor_date=anchor,
        observed_value=4.52,
        shap_contribution=1.25,
        feature_values_row={"rolling_std_30d": 2.10},
    )
    assert evidence.anchor_date == "2016-10-30"
    assert evidence.source_window_end == "2016-10-30"
    assert evidence.source_window_start == "2016-09-01"  # 59 days prior
    assert evidence.observed_value == 4.52
    assert evidence.reference_value == 2.10
    assert evidence.relative_difference_pct is not None
    assert evidence.shap_contribution == 1.25


def test_temporal_attribution_ratio_14d_60d() -> None:
    """Test calendar window and drop percentage calculation for ratio_14d_60d."""
    attributor = TemporalAttributor()
    evidence = attributor.attribute(
        feature_name="ratio_14d_60d",
        anchor_date=date(2016, 10, 30),
        observed_value=0.35,
        shap_contribution=0.85,
        feature_values_row={
            "rolling_mean_14d": 3.5,
            "rolling_mean_60d": 10.0,
        },
    )
    assert evidence.source_window_end == "2016-10-30"
    assert evidence.source_window_start == "2016-09-01"
    assert evidence.reference_value == 10.0
    # (3.5 - 10.0) / 10.0 = -65.0%
    assert evidence.relative_difference_pct == -65.0
    assert "65.0% below 60-day baseline" in evidence.interpretation


def test_temporal_attribution_streak() -> None:
    """Test calendar interval calculation for active streaks."""
    attributor = TemporalAttributor()
    evidence = attributor.attribute(
        feature_name="current_zero_streak",
        anchor_date="2016-10-30",
        observed_value=10.0,
        shap_contribution=1.5,
    )
    assert evidence.source_window_end == "2016-10-30"
    assert evidence.source_window_start == "2016-10-21"  # 10 days ending on 2016-10-30
    assert "Continuous streak of 10 days" in evidence.interpretation
