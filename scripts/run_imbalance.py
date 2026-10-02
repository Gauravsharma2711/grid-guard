"""CLI script for Phase 5 Class Imbalance Experimentation & Rare-Tampering Learning."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from grid_guard.config.settings import find_project_root, get_settings
from grid_guard.models.imbalance_pipeline import ImbalanceExperimentPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("run_imbalance")


def main() -> None:
    """CLI entrypoint for running class imbalance experiments."""
    parser = argparse.ArgumentParser(
        description="Grid-Guard Phase 5: Class Imbalance Strategy & Rare-Tampering Learning"
    )
    parser.add_argument(
        "action",
        choices=["compare", "all"],
        default="all",
        nargs="?",
        help="Action to execute (default: all)",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Optional path to canonical_features.parquet",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output directory for imbalance artifacts (default: artifacts/imbalance)",
    )
    parser.add_argument(
        "--stride",
        type=int,
        default=None,
        help="Periodic sampling stride in days (default: 30)",
    )
    parser.add_argument(
        "--metric",
        type=str,
        default=None,
        help="Validation metric for strategy selection (default: pr_auc)",
    )
    parser.add_argument(
        "--no-mlflow",
        action="store_true",
        help="Disable MLflow experiment tracking",
    )

    args = parser.parse_args()
    root = find_project_root()
    settings = get_settings()

    if args.stride is not None:
        settings.baseline.sampling_stride_days = args.stride
    if args.metric is not None:
        settings.imbalance.selection_metric = args.metric

    in_parquet = args.input or (settings.processed_data_dir / "canonical_features.parquet")
    if not in_parquet.is_file():
        logger.error(
            f"Feature dataset '{in_parquet}' not found! Please run Phase 3 feature engineering first."
        )
        sys.exit(1)

    out_dir = args.output or (root / "artifacts" / "imbalance")

    pipeline = ImbalanceExperimentPipeline(settings=settings)
    pipeline.run(
        feature_parquet_path=in_parquet,
        output_dir=out_dir,
        enable_mlflow=not args.no_mlflow,
    )
    logger.info("Phase 5 class imbalance experimentation completed successfully.")


if __name__ == "__main__":
    main()
