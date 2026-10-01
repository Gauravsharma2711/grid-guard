"""CLI script for Phase 4 Unweighted Baseline Modeling and Financial Evaluation."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from grid_guard.config.settings import find_project_root, get_settings
from grid_guard.models.pipeline import BaselinePipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("run_baseline")


def main() -> None:
    """CLI Entrypoint for running the baseline modeling pipeline."""
    parser = argparse.ArgumentParser(
        description="Grid-Guard Phase 4: Baseline Modeling & Financial Cost Evaluation"
    )
    parser.add_argument(
        "action",
        choices=["train", "evaluate", "all"],
        default="all",
        nargs="?",
        help="Pipeline action to execute (default: all)",
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
        help="Optional output directory for baseline artifacts (default: artifacts/baseline)",
    )
    parser.add_argument(
        "--stride",
        type=int,
        default=None,
        help="Periodic sampling stride in days (default: from config, e.g. 30)",
    )
    parser.add_argument(
        "--dispatch-cost",
        type=float,
        default=None,
        help="Override field inspection dispatch cost C_dispatch",
    )
    parser.add_argument(
        "--tariff",
        type=float,
        default=None,
        help="Override default electricity tariff rate per kWh",
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
    if args.dispatch_cost is not None:
        settings.financial.dispatch_cost = args.dispatch_cost
    if args.tariff is not None:
        settings.financial.default_tariff = args.tariff

    in_parquet = args.input or (settings.processed_data_dir / "canonical_features.parquet")
    if not in_parquet.is_file():
        logger.error(
            f"Feature dataset '{in_parquet}' not found! Please run Phase 3 feature engineering first."
        )
        sys.exit(1)

    out_dir = args.output or (root / "artifacts" / "baseline")

    pipeline = BaselinePipeline(settings=settings)
    pipeline.run(
        feature_parquet_path=in_parquet,
        output_dir=out_dir,
        enable_mlflow=not args.no_mlflow,
    )
    logger.info("Phase 4 baseline modeling and financial evaluation completed successfully.")


if __name__ == "__main__":
    main()
