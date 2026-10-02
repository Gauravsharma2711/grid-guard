#!/usr/bin/env python3
"""CLI runner for Grid-Guard Phase 7: Dynamic Thresholding, Expected Net Value, and Prioritization."""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "src"))

from grid_guard.config.decision import DecisionRule  # noqa: E402
from grid_guard.config.settings import get_settings  # noqa: E402
from grid_guard.models.decision_pipeline import DecisionPipeline  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("run_decision_engine")


def main() -> None:
    """CLI entrypoint for Phase 7 Decision Engine."""
    parser = argparse.ArgumentParser(
        description="Grid-Guard Phase 7: Dynamic Decisioning, ENV Prioritization & Ticket Dispatch"
    )
    parser.add_argument(
        "action",
        nargs="?",
        default="all",
        choices=["all", "tickets", "evaluate", "scenarios"],
        help="Pipeline action to execute (default: all)",
    )
    parser.add_argument(
        "--predictions-path",
        type=str,
        default=None,
        help="Path to Phase 6 predictions parquet file (default: artifacts/cost_sensitive/champion_predictions.parquet)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for generated ticket files and comparison reports (default: artifacts/decision)",
    )
    parser.add_argument(
        "--rule",
        type=str,
        default="env",
        choices=["env", "cost_threshold", "fixed_threshold"],
        help="Primary operational decision rule (default: env)",
    )
    parser.add_argument(
        "--dispatch-cost",
        type=float,
        default=None,
        help="Override field inspection dispatch cost (USD, default: 100.0)",
    )
    parser.add_argument(
        "--tariff",
        type=float,
        default=None,
        help="Override electricity tariff rate (USD/kWh, default: 0.15)",
    )
    parser.add_argument(
        "--recovery-factor",
        type=float,
        default=None,
        help="Override unmetered leakage recovery factor (default: 1.0)",
    )
    parser.add_argument(
        "--no-mlflow",
        action="store_true",
        help="Disable MLflow experiment tracking",
    )

    args = parser.parse_args()

    settings = get_settings()

    # Apply CLI overrides if specified
    if args.rule:
        settings.decision.decision_rule = DecisionRule(args.rule)
    if args.dispatch_cost is not None:
        settings.decision.dispatch_cost = args.dispatch_cost
    if args.tariff is not None:
        settings.decision.default_tariff = args.tariff
    if args.recovery_factor is not None:
        settings.decision.recovery_factor = args.recovery_factor

    pipeline = DecisionPipeline(settings=settings)

    print("=" * 80)
    print("  GRID-GUARD PHASE 7: DYNAMIC THRESHOLDING & EXPECTED NET VALUE PRIORITIZATION")
    print(f"  Primary Decision Rule: {settings.decision.decision_rule.value.upper()}")
    print(
        f"  Dispatch Cost: ${settings.decision.dispatch_cost:.2f} | Tariff: ${settings.decision.default_tariff:.2f}/kWh"
    )
    print(f"  Action: {args.action.upper()}")
    print("=" * 80)

    res = pipeline.run(
        predictions_path=args.predictions_path,
        output_dir=args.output_dir,
        enable_mlflow=not args.no_mlflow,
    )

    prim_sum = res["primary_queue_summary"]
    exp_fin = prim_sum["expected_financials"]
    print("\n[PHASE 7 COMPLETED SUCCESSFULLY]")
    print(f"Total Candidates Evaluated: {prim_sum['total_candidates']:,}")
    print(
        f"Inspections Recommended:    {prim_sum['inspections_recommended']:,} ({prim_sum['inspection_rate_pct']}%)"
    )
    print(f"Expected Gross Recovery:    ${exp_fin['expected_gross_recovery']:,.2f}")
    print(f"Expected Inspection Cost:   ${exp_fin['expected_dispatch_cost']:,.2f}")
    print(f"Expected Net Value (ENV):   ${exp_fin['expected_net_value']:,.2f}")
    print(f"Mean ENV per Ticket:        ${exp_fin['mean_env_per_ticket']:,.2f}")
    print("=" * 80)


if __name__ == "__main__":
    main()
