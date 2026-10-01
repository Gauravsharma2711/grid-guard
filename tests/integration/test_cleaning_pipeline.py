"""Integration test for full Phase 2 EDA, profiling, and cleaning pipeline."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from grid_guard.data.cleaning import AMICleaningPipeline
from grid_guard.data.profiling import AMIProfiler
from grid_guard.visualization.eda import EDAVisualizer


def test_full_cleaning_and_eda_integration(tmp_path: Path) -> None:
    """Run full Phase 2 workflow on synthetic smart-meter dataset."""
    # 1. Create synthetic raw CSV
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(parents=True)
    raw_csv = raw_dir / "test_electric.csv"

    # 10 meters across 10 dates
    dates = [f"2014-08-{i:02d}" for i in range(1, 11)]
    meters = [f"MTR_{i:03d}" for i in range(10)]

    data: dict[str, list] = {"CONS_NO": meters}
    for d in dates:
        # Some normal, some zeroes, some nulls
        data[d] = [float(i + 1) if (i + int(d[-2:])) % 5 != 0 else None for i in range(10)]
    data["FLAG"] = [1 if i in (2, 7) else 0 for i in range(10)]

    df_synth = pl.DataFrame(data)
    df_synth.write_csv(raw_csv)

    # 2. Run Profiler
    profiler = AMIProfiler(meter_col="CONS_NO", label_col="FLAG")
    profile = profiler.profile_dataset(
        df_synth, dataset_name="integration_test", file_size_bytes=raw_csv.stat().st_size
    )
    assert profile.total_meters == 10
    assert profile.observed_days == 10

    # Export Profile JSON
    profile_json = tmp_path / "dataset_profile.json"
    profile.to_json(profile_json)
    assert profile_json.is_file()

    # 3. Run Cleaning Pipeline
    pipeline = AMICleaningPipeline(max_impute_gap=3, meter_col="CONS_NO", label_col="FLAG")
    cleaning_result = pipeline.clean(df_synth, source_name="test_electric.csv")
    assert cleaning_result.df_clean_wide.height == 10

    # Export Parquet
    proc_dir = tmp_path / "processed"
    wide_path, long_path = pipeline.export_canonical(
        cleaning_result, output_dir=proc_dir, export_long=True
    )
    assert wide_path.is_file()
    assert long_path is not None and long_path.is_file()

    # Export Lineage
    lineage_json = tmp_path / "data_lineage.json"
    cleaning_result.lineage.to_json(lineage_json)
    assert lineage_json.is_file()

    # 4. Generate Visualizations
    fig_dir = tmp_path / "figures"
    visualizer = EDAVisualizer(output_dir=fig_dir)
    figures = visualizer.generate_all_figures(
        df_raw=df_synth,
        df_clean=cleaning_result.df_clean_wide,
        profile=profile,
        canonical_dates=cleaning_result.canonical_date_columns,
        raw_date_cols=dates,
    )
    assert len(figures) == 5
    for f in figures:
        assert f.is_file()
        assert f.stat().st_size > 0
