#!/usr/bin/env python3
"""CLI runner for Grid-Guard Phase 8: SHAP Explainability, Temporal Attribution & Tampering Signatures."""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "src"))

from grid_guard.config.settings import get_settings  # noqa: E402
from grid_guard.models.explainability_pipeline import ExplainabilityPipeline  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("run_explainability")


def main() -> None:
    """CLI entrypoint for Phase 8 Explainability."""
    parser = argparse.ArgumentParser(
        description="Grid-Guard Phase 8: SHAP Explainability, Temporal Attribution & Tampering Signatures"
    )
    parser.add_argument(
        "action",
        nargs="?",
        default="all",
        choices=["all", "global", "tickets", "case-studies"],
        help="Explainability action to run (default: all)",
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default=None,
        help="Path to trained LightGBM model file (default: artifacts/cost_sensitive/champion_model.txt)",
    )
    parser.add_argument(
        "--features-path",
        type=str,
        default=None,
        help="Path to feature dataset parquet (default: data/processed/canonical_features.parquet)",
    )
    parser.add_argument(
        "--tickets-path",
        type=str,
        default=None,
        help="Path to prioritized inspection tickets CSV (default: artifacts/decision/top_100_inspection_tickets.csv)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for explainability artifacts (default: artifacts/explainability)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=100,
        help="Number of prioritized inspection tickets to enrich with full local SHAP and narratives (default: 100)",
    )
    parser.add_argument(
        "--global-samples",
        type=int,
        default=500,
        help="Number of background instances for global SHAP analysis (default: 500)",
    )
    parser.add_argument(
        "--no-mlflow",
        action="store_true",
        help="Disable MLflow experiment tracking",
    )

    args = parser.parse_args()
    settings = get_settings()

    # Apply CLI overrides
    if args.top_k is not None:
        settings.explainability.top_k_tickets = args.top_k
    if args.global_samples is not None:
        settings.explainability.global_sample_size = args.global_samples

    pipeline = ExplainabilityPipeline(settings=settings)

    logger.info(f"Executing Phase 8 explainability action '{args.action}'...")
    results = pipeline.run(
        model_path=args.model_path,
        feature_parquet_path=args.features_path,
        tickets_csv_path=args.tickets_path,
        output_dir=args.output_dir,
        enable_mlflow=not args.no_mlflow,
    )

    logger.info("=" * 70)
    logger.info("PHASE 8 EXPLAINABILITY COMPLETE")
    logger.info(f"Execution Duration: {results['duration_seconds']:.2f}s")
    logger.info(f"Top Tickets Enriched: {results['top_tickets_count']}")
    logger.info(f"Artifacts Directory: {results['artifacts_dir']}")
    logger.info(f"Enriched Tickets CSV: {results['enriched_tickets_csv']}")
    logger.info(f"Markdown Report: {results['report_md']}")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
