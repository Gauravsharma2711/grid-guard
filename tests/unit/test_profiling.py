"""Unit tests for AMIProfiler and DatasetProfile."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from grid_guard.data.profiling import AMIProfiler, DatasetProfile


def test_profiler_with_synthetic_wide(synthetic_wide_df: pl.DataFrame, tmp_path: Path) -> None:
    """Verify AMIProfiler computes accurate metrics on synthetic wide dataset."""
    profiler = AMIProfiler(meter_col="CONS_NO", label_col="FLAG")
    profile = profiler.profile_dataset(
        synthetic_wide_df, dataset_name="synthetic_test", file_size_bytes=1024
    )

    assert isinstance(profile, DatasetProfile)
    assert profile.total_meters == 3
    assert profile.observed_days == 3
    assert profile.start_date == "2014-08-01"
    assert profile.end_date == "2014-08-03"
    assert profile.tampering_label_available is True
    assert profile.label_distribution == {"0": 2, "1": 1}
    assert profile.tampering_ratio == 0.3333
    assert profile.total_zeros > 0
    assert profile.total_negatives == 0

    # Test JSON export
    json_path = tmp_path / "profile.json"
    profile.to_json(json_path)
    assert json_path.is_file()
    assert '"total_meters": 3' in json_path.read_text(encoding="utf-8")


def test_profiler_detects_missing_calendar_dates() -> None:
    """Verify missing calendar days are detected in headers."""
    # 2014-08-01 and 2014-08-03 (skipping 2014-08-02)
    df = pl.DataFrame(
        {
            "CONS_NO": ["M1"],
            "2014-08-01": [5.0],
            "2014-08-03": [6.0],
            "FLAG": [0],
        }
    )
    profiler = AMIProfiler(meter_col="CONS_NO", label_col="FLAG")
    profile = profiler.profile_dataset(df)

    assert profile.observed_days == 2
    assert profile.expected_days == 3
    assert profile.missing_calendar_dates == ["2014-08-02"]
