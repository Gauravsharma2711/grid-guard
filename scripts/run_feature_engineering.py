"""CLI script for Phase 3 Feature Engineering, Validation, and Documentation."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import polars as pl

from grid_guard.config.settings import find_project_root, get_settings
from grid_guard.features.pipeline import FeaturePipeline
from grid_guard.utils.synthetic import generate_synthetic_series
from grid_guard.visualization.feature_validation import FeatureVisualizer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("run_feature_engineering")


def export_dictionary(project_root: Path) -> None:
    """Export feature registry to JSON and Markdown dictionary."""
    pipeline = FeaturePipeline()
    docs_dir = project_root / "docs" / "features"
    docs_dir.mkdir(parents=True, exist_ok=True)

    json_path = docs_dir / "feature_registry.json"
    md_path = docs_dir / "feature_dictionary.md"

    pipeline.registry.export_json(json_path)
    pipeline.registry.export_markdown(md_path)
    logger.info(f"Feature registry exported to '{json_path}' and '{md_path}'.")


def generate_visualizations(project_root: Path) -> None:
    """Generate visual feature validation figures."""
    figs_dir = project_root / "docs" / "features" / "figures"
    figs_dir.mkdir(parents=True, exist_ok=True)
    visualizer = FeatureVisualizer(output_dir=figs_dir)
    pipeline = FeaturePipeline()

    logger.info("Generating diagnostic feature validation plots...")
    # 1. Step-down
    step_df = pipeline.transform(generate_synthetic_series(num_days=100, pattern="step_down"))
    visualizer.plot_step_down_dynamics(step_df)

    # 2. Zero streak
    zero_df = pipeline.transform(generate_synthetic_series(num_days=80, pattern="zero_streak"))
    visualizer.plot_zero_streak_detection(zero_df)

    # 3. Flatline
    flat_df = pipeline.transform(generate_synthetic_series(num_days=70, pattern="flatline"))
    visualizer.plot_flatline_variance_collapse(flat_df)

    # 4. Ratios & PAR
    norm_df = pipeline.transform(generate_synthetic_series(num_days=90, pattern="normal"))
    visualizer.plot_ratios_and_par(norm_df)

    # 5. Real meters comparison if canonical dataset exists
    features_parquet = project_root / "data" / "processed" / "canonical_features.parquet"
    if features_parquet.is_file():
        normal_id = (
            pl.scan_parquet(features_parquet)
            .filter((pl.col("tamper_label") == 0) & (pl.col("data_quality_status") == "EXCELLENT"))
            .select("meter_id")
            .first()
            .collect()
            .item()
        )
        theft_id = (
            pl.scan_parquet(features_parquet)
            .filter((pl.col("tamper_label") == 1) & (pl.col("data_quality_status") == "EXCELLENT"))
            .select("meter_id")
            .first()
            .collect()
            .item()
        )
        norm_m = pl.scan_parquet(features_parquet).filter(pl.col("meter_id") == normal_id).collect()
        theft_m = pl.scan_parquet(features_parquet).filter(pl.col("meter_id") == theft_id).collect()
        visualizer.plot_real_meter_profiles(norm_m, theft_m)

    logger.info(f"Diagnostic plots saved to '{figs_dir}'.")


def generate_features(
    project_root: Path,
    input_path: Path | None = None,
    output_path: Path | None = None,
    batch_size: int = 10000,
) -> Path:
    """Run full feature engineering on the canonical AMI time-series dataset."""
    settings = get_settings()
    in_series = input_path or settings.processed_data_dir / "canonical_ami_series.parquet"
    clean_wide = settings.processed_data_dir / "canonical_ami_clean.parquet"
    out_features = output_path or settings.processed_data_dir / "canonical_features.parquet"

    if not in_series.is_file():
        logger.error(f"Input series '{in_series}' not found! Run Phase 2 cleaning first.")
        sys.exit(1)

    pipeline = FeaturePipeline(config=settings.features)
    res_path = pipeline.process_dataset(
        input_series_path=in_series,
        output_feature_path=out_features,
        clean_wide_path=clean_wide,
        batch_size_meters=batch_size,
    )

    # Generate feature quality reports
    logger.info("Auditing generated feature dataset...")
    df_sample = pl.read_parquet(res_path)
    reports_dir = project_root / "docs" / "features"
    reports_dir.mkdir(parents=True, exist_ok=True)

    report_json = reports_dir / "feature_quality_report.json"
    report_md = reports_dir / "feature_summary_report.md"

    pipeline.generate_quality_report(
        df_sample,
        output_json=report_json,
        output_md=report_md,
    )
    logger.info(f"Quality report saved to '{report_json}' and '{report_md}'.")
    return res_path


def validate_features(
    project_root: Path,
    features_path: Path | None = None,
) -> None:
    """Audit and validate an existing canonical feature dataset."""
    settings = get_settings()
    out_features = features_path or settings.processed_data_dir / "canonical_features.parquet"
    if not out_features.is_file():
        logger.error(f"Features dataset '{out_features}' not found! Run generate first.")
        sys.exit(1)

    pipeline = FeaturePipeline(config=settings.features)
    logger.info(f"Auditing existing feature dataset '{out_features}'...")
    df_sample = pl.read_parquet(out_features)
    reports_dir = project_root / "docs" / "features"
    reports_dir.mkdir(parents=True, exist_ok=True)

    report_json = reports_dir / "feature_quality_report.json"
    report_md = reports_dir / "feature_summary_report.md"

    pipeline.generate_quality_report(
        df_sample,
        output_json=report_json,
        output_md=report_md,
    )
    logger.info(f"Quality report refreshed at '{report_json}' and '{report_md}'.")


def main() -> None:
    """CLI Entrypoint."""
    parser = argparse.ArgumentParser(
        description="Grid-Guard Phase 3: Temporal Feature Engineering Pipeline"
    )
    parser.add_argument(
        "action",
        choices=["generate", "validate", "visualize", "dictionary", "all"],
        default="all",
        nargs="?",
        help="Pipeline action to execute",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Optional path to input canonical_ami_series.parquet",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path for output canonical_features.parquet",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10000,
        help="Number of meters per processing batch (default: 10000)",
    )

    args = parser.parse_args()
    root = find_project_root()

    if args.action in ("dictionary", "all"):
        export_dictionary(root)

    if args.action in ("visualize", "all"):
        generate_visualizations(root)

    if args.action in ("generate", "all"):
        generate_features(
            project_root=root,
            input_path=args.input,
            output_path=args.output,
            batch_size=args.batch_size,
        )

    if args.action == "validate":
        validate_features(project_root=root, features_path=args.output)

    logger.info("Phase 3 feature engineering operations completed successfully.")


if __name__ == "__main__":
    main()
