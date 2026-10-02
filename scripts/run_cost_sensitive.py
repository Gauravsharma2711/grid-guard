"""CLI script for Phase 6 Cost-Sensitive Learning & Financially Weighted Objective."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from grid_guard.config.cost_sensitive import CostNormalizationType
from grid_guard.config.settings import find_project_root, get_settings
from grid_guard.models.cost_sensitive_pipeline import CostSensitiveExperimentPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("run_cost_sensitive")


def main() -> None:
    """CLI entrypoint for running cost-sensitive model experiments."""
    parser = argparse.ArgumentParser(
        description="Grid-Guard Phase 6: Cost-Sensitive Custom Objective & Financially Weighted Learning"
    )
    parser.add_argument(
        "action",
        choices=["train", "compare", "all"],
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
        help="Optional output directory for artifacts (default: artifacts/cost_sensitive)",
    )
    parser.add_argument(
        "--dispatch-cost",
        type=float,
        default=None,
        help="Operational cost C_FP per physical inspection dispatch ($)",
    )
    parser.add_argument(
        "--tariff",
        type=float,
        default=None,
        help="Energy tariff ($/kWh) for computing financial leakage",
    )
    parser.add_argument(
        "--norm",
        type=str,
        choices=["dispatch_cost", "mean", "median", "none"],
        default=None,
        help="Global cost normalization method (default: dispatch_cost)",
    )
    parser.add_argument(
        "--capping",
        action="store_true",
        help="Enable winsorization capping of extreme C_FN values",
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
        help="Validation metric for strategy selection (default: total_operational_loss)",
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
        settings.cost_sensitive.dispatch_cost = args.dispatch_cost
    if args.tariff is not None:
        settings.financial.default_tariff = args.tariff
        settings.cost_sensitive.default_tariff = args.tariff
    if args.norm is not None:
        settings.cost_sensitive.cost_normalization = CostNormalizationType(args.norm)
    if args.capping:
        settings.cost_sensitive.cost_capping = True
    if args.metric is not None:
        settings.cost_sensitive.selection_metric = args.metric

    in_parquet = args.input or (settings.processed_data_dir / "canonical_features.parquet")
    if not in_parquet.is_file():
        logger.error(
            f"Feature dataset '{in_parquet}' not found! Please run Phase 3 feature engineering first."
        )
        sys.exit(1)

    out_dir = args.output or (root / "artifacts" / "cost_sensitive")

    pipeline = CostSensitiveExperimentPipeline(settings=settings)
    pipeline.run(
        feature_parquet_path=in_parquet,
        output_dir=out_dir,
        enable_mlflow=not args.no_mlflow,
    )
    logger.info("Phase 6 cost-sensitive learning workflow completed successfully.")


if __name__ == "__main__":
    main()
