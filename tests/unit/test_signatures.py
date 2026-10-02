"""Unit tests for rule-based tampering signature detection."""

import pytest

from grid_guard.config.explainability import ExplainabilitySettings
from grid_guard.explainability.signatures import TamperingSignatureDetector


@pytest.fixture
def detector() -> TamperingSignatureDetector:
    """Create standard detector instance."""
    return TamperingSignatureDetector(settings=ExplainabilitySettings())


def test_sustained_step_down_detection(detector: TamperingSignatureDetector) -> None:
    """Test sustained step-down signature detection under various drop conditions."""
    # Case 1: Severe drop with duration
    row_severe = {
        "ratio_14d_60d": 0.35,
        "sustained_drop_ratio": 0.65,
        "sustained_drop_duration": 18,
        "sustained_drop_magnitude": 12.5,
    }
    sigs = detector.detect_all(row_severe)
    assert len(sigs) == 1
    assert sigs[0].signature_type == "sustained_step_down"
    assert sigs[0].severity == "high"
    assert sigs[0].duration_days == 18
    assert sigs[0].magnitude == pytest.approx(0.65)
    assert "12.5 kWh/day deficit" in sigs[0].description

    # Case 2: Moderate drop
    row_mod = {
        "ratio_14d_60d": 0.48,
        "sustained_drop_ratio": 0.52,
        "sustained_drop_duration": 8,
        "sustained_drop_magnitude": 5.0,
    }
    sigs_mod = detector.detect_all(row_mod)
    assert len(sigs_mod) == 1
    assert sigs_mod[0].severity == "moderate"

    # Case 3: Normal consumption (no drop)
    row_normal = {
        "ratio_14d_60d": 1.05,
        "sustained_drop_ratio": 0.0,
        "sustained_drop_duration": 0,
        "sustained_drop_magnitude": 0.0,
    }
    assert len(detector.detect_all(row_normal)) == 0


def test_zero_streak_detection(detector: TamperingSignatureDetector) -> None:
    """Test zero-consumption streak detection."""
    # Active 10-day streak
    row_active_zero = {
        "current_zero_streak": 10,
        "zero_count_7d": 7,
        "zero_count_30d": 15,
    }
    sigs = detector.detect_all(row_active_zero)
    assert len(sigs) == 1
    assert sigs[0].signature_type == "zero_streak"
    assert sigs[0].severity == "high"
    assert sigs[0].duration_days == 10
    assert "10 consecutive days" in sigs[0].description

    # Frequent zero days in 7d without continuous active streak
    row_freq_zero = {
        "current_zero_streak": 1,
        "zero_count_7d": 4,
        "zero_count_30d": 8,
    }
    sigs_freq = detector.detect_all(row_freq_zero)
    assert len(sigs_freq) == 1
    assert sigs_freq[0].severity == "moderate"


def test_flatline_detection(detector: TamperingSignatureDetector) -> None:
    """Test near-constant flatline consumption detection."""
    row_flat = {
        "rolling_cv_7d": 0.015,
        "flatline_streak": 14,
        "rolling_mean_7d": 2.5,
    }
    sigs = detector.detect_all(row_flat)
    assert len(sigs) == 1
    assert sigs[0].signature_type == "flatline"
    assert sigs[0].severity == "high"
    assert sigs[0].duration_days == 14


def test_regime_shift_detection(detector: TamperingSignatureDetector) -> None:
    """Test abrupt week-over-week or monthly transition detection."""
    row_shift = {
        "ratio_7d_30d": 0.38,
        "wow_consumption_change": -0.62,
    }
    sigs = detector.detect_all(row_shift)
    assert len(sigs) == 1
    assert sigs[0].signature_type == "behavior_shift"
    assert sigs[0].severity == "moderate"


def test_normal_consumer_no_signatures(detector: TamperingSignatureDetector) -> None:
    """Verify that a normal stable consumer triggers zero anomalous signatures."""
    normal_row = {
        "ratio_14d_60d": 0.98,
        "sustained_drop_ratio": 0.02,
        "sustained_drop_duration": 0,
        "sustained_drop_magnitude": 0.0,
        "current_zero_streak": 0,
        "zero_count_7d": 0,
        "zero_count_30d": 0,
        "rolling_cv_7d": 0.35,
        "flatline_streak": 0,
        "rolling_mean_7d": 12.0,
        "ratio_7d_30d": 1.02,
        "wow_consumption_change": 0.05,
    }
    sigs = detector.detect_all(normal_row)
    assert len(sigs) == 0
