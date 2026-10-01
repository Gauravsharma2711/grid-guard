"""Unit tests for AMICleaningPipeline."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import polars as pl
import pytest

from grid_guard.data.cleaning import AMICleaningPipeline


@pytest.fixture
def synthetic_raw_with_gaps() -> pl.DataFrame:
    """Synthetic dataset with known gaps: short (interpolable), long (preserved), and edge."""
    return pl.DataFrame(
        {
            "CONS_NO": ["MTR_A", "MTR_B", "MTR_C"],
            # Day 1: MTR_B is edge null (should remain null)
            "1/1/2014": [10.0, None, 5.0],
            # Day 2: MTR_A has 1-day short gap (should be interpolated between 10.0 and 12.0 -> 11.0)
            "1/2/2014": [None, 8.0, 5.0],
            "1/3/2014": [12.0, 8.0, 5.0],
            # Days 4, 5, 6, 7: MTR_B has 4-day long gap (> max_gap 3, should remain null)
            "1/4/2014": [12.0, None, 5.0],
            "1/5/2014": [12.0, None, 5.0],
            "1/6/2014": [12.0, None, 5.0],
            "1/7/2014": [12.0, None, 5.0],
            "1/8/2014": [12.0, 10.0, 5.0],
            "FLAG": [0, 1, 0],
        }
    )


def test_cleaning_interpolation_rules(synthetic_raw_with_gaps: pl.DataFrame) -> None:
    """Verify localized bounded interpolation behavior."""
    pipeline = AMICleaningPipeline(max_impute_gap=3, meter_col="CONS_NO", label_col="FLAG")
    result = pipeline.clean(synthetic_raw_with_gaps, source_name="test_gaps")
    df_clean = result.df_clean_wide

    # 1. Day 2 for MTR_A was a 1-day gap bounded by 10.0 and 12.0 -> should be 11.0
    mtr_a = df_clean.filter(pl.col("meter_id") == "MTR_A")
    val_day2 = mtr_a["2014-01-02"][0]
    assert np.isclose(val_day2, 11.0)

    # 2. Day 1 for MTR_B was an edge null -> should remain null
    mtr_b = df_clean.filter(pl.col("meter_id") == "MTR_B")
    assert np.isnan(mtr_b["2014-01-01"][0])

    # 3. Days 4-7 for MTR_B were a 4-day gap (> max_gap 3) -> should remain null
    assert np.isnan(mtr_b["2014-01-04"][0])
    assert np.isnan(mtr_b["2014-01-05"][0])
    assert np.isnan(mtr_b["2014-01-06"][0])
    assert np.isnan(mtr_b["2014-01-07"][0])

    # 4. Check imputation summary metrics
    summary = result.imputation_summary
    assert summary.max_gap_allowed == 3
    assert summary.values_imputed == 1  # Only MTR_A Day 2 was imputed
    assert summary.meters_affected == 1


def test_cleaning_quality_tier_assignment(synthetic_raw_with_gaps: pl.DataFrame) -> None:
    """Verify quality status flags are computed properly."""
    pipeline = AMICleaningPipeline(max_impute_gap=3, meter_col="CONS_NO", label_col="FLAG")
    result = pipeline.clean(synthetic_raw_with_gaps)
    df_clean = result.df_clean_wide

    # MTR_C has 0 nulls -> EXCELLENT
    mtr_c = df_clean.filter(pl.col("meter_id") == "MTR_C")
    assert mtr_c["data_quality_status"][0] == "EXCELLENT"
    assert mtr_c["missing_ratio"][0] == 0.0

    # MTR_B has 5 nulls out of 8 (62.5% missing) -> SPARSE
    mtr_b = df_clean.filter(pl.col("meter_id") == "MTR_B")
    assert mtr_b["data_quality_status"][0] == "SPARSE"


def test_to_long_format(synthetic_raw_with_gaps: pl.DataFrame) -> None:
    """Verify transformation to canonical long time-series format."""
    pipeline = AMICleaningPipeline(max_impute_gap=3, meter_col="CONS_NO", label_col="FLAG")
    result = pipeline.clean(synthetic_raw_with_gaps)
    df_long = pipeline.to_long_format(result.df_clean_wide, result.canonical_date_columns)

    expected_rows = 3 * 8  # 3 meters * 8 dates = 24 rows
    assert df_long.height == expected_rows
    assert set(df_long.columns) == {
        "meter_id",
        "timestamp",
        "consumption_kwh",
        "tamper_label",
        "data_quality_status",
    }
    assert df_long["timestamp"].dtype == pl.Date


def test_export_canonical(synthetic_raw_with_gaps: pl.DataFrame, tmp_path: Path) -> None:
    """Verify export to Parquet files."""
    pipeline = AMICleaningPipeline(max_impute_gap=3, meter_col="CONS_NO", label_col="FLAG")
    result = pipeline.clean(synthetic_raw_with_gaps)

    wide_path, long_path = pipeline.export_canonical(result, output_dir=tmp_path, export_long=True)
    assert wide_path.is_file()
    assert long_path is not None and long_path.is_file()

    # Re-read with Polars
    df_wide_read = pl.read_parquet(wide_path)
    assert df_wide_read.height == 3
    df_long_read = pl.read_parquet(long_path)
    assert df_long_read.height == 24


def test_cleaning_pipeline_determinism(synthetic_raw_with_gaps: pl.DataFrame) -> None:
    """Verify cleaning pipeline is completely deterministic across repeated executions."""
    pipeline = AMICleaningPipeline(max_impute_gap=3, meter_col="CONS_NO", label_col="FLAG")
    r1 = pipeline.clean(synthetic_raw_with_gaps)
    r2 = pipeline.clean(synthetic_raw_with_gaps)

    assert r1.df_clean_wide.equals(r2.df_clean_wide)
    assert r1.imputation_summary == r2.imputation_summary
