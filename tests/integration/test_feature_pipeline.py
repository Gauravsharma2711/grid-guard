"""Integration tests for FeaturePipeline end-to-end execution."""

from __future__ import annotations

import polars as pl

from grid_guard.features.pipeline import FeaturePipeline
from grid_guard.visualization.feature_validation import FeatureVisualizer
from tests.fixtures.synthetic_ami import (
    generate_synthetic_multimeter_fleet,
    generate_synthetic_series,
)


def test_feature_pipeline_end_to_end_synthetic(tmp_path) -> None:
    """Verify complete feature pipeline execution, chunking, Parquet export, and reporting."""
    fleet_df = generate_synthetic_multimeter_fleet(num_days=100)
    input_series_path = tmp_path / "synthetic_series.parquet"
    output_feature_path = tmp_path / "synthetic_features.parquet"
    report_json_path = tmp_path / "quality_report.json"
    report_md_path = tmp_path / "quality_report.md"

    fleet_df.write_parquet(input_series_path)

    pipeline = FeaturePipeline()
    res_path = pipeline.process_dataset(
        input_series_path=input_series_path,
        output_feature_path=output_feature_path,
        batch_size_meters=2,  # Force batching across 5 meters
    )
    assert res_path.is_file()

    # Read back canonical feature dataset
    df_features = pl.read_parquet(res_path)
    assert len(df_features) == len(fleet_df)
    assert df_features.get_column("meter_id").n_unique() == 5
    assert "ratio_7d_30d" in df_features.columns
    assert "sustained_drop_ratio" in df_features.columns
    assert "current_zero_streak" in df_features.columns
    assert "flatline_streak" in df_features.columns

    # Audit quality report
    report = pipeline.generate_quality_report(
        df_features,
        output_json=report_json_path,
        output_md=report_md_path,
    )
    assert report["total_rows"] == 500
    assert report["total_meters"] == 5
    assert report["duplicate_meter_timestamp_pairs"] == 0
    assert len(report["infinite_value_columns"]) == 0
    assert report_json_path.is_file()
    assert report_md_path.is_file()


def test_feature_visualizations_generation(tmp_path) -> None:
    """Verify generation of all diagnostic validation figures."""
    visualizer = FeatureVisualizer(output_dir=tmp_path / "figures")
    pipeline = FeaturePipeline()

    # Generate step-down series
    step_df = pipeline.transform(generate_synthetic_series(num_days=100, pattern="step_down"))
    fig1 = visualizer.plot_step_down_dynamics(step_df)
    assert fig1.is_file()

    # Generate zero streak series
    zero_df = pipeline.transform(generate_synthetic_series(num_days=80, pattern="zero_streak"))
    fig2 = visualizer.plot_zero_streak_detection(zero_df)
    assert fig2.is_file()

    # Generate flatline series
    flat_df = pipeline.transform(generate_synthetic_series(num_days=70, pattern="flatline"))
    fig3 = visualizer.plot_flatline_variance_collapse(flat_df)
    assert fig3.is_file()

    # Generate normal series for ratios
    norm_df = pipeline.transform(generate_synthetic_series(num_days=90, pattern="normal"))
    fig4 = visualizer.plot_ratios_and_par(norm_df)
    assert fig4.is_file()
