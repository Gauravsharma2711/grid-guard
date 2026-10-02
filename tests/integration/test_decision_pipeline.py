"""Integration test for the Phase 7 DecisionPipeline end-to-end workflow."""

from pathlib import Path

import polars as pl
import pytest

from grid_guard.config.settings import Settings
from grid_guard.models.decision_pipeline import DecisionPipeline


@pytest.fixture
def synthetic_predictions_file(tmp_path: Path) -> Path:
    """Create a temporary synthetic predictions Parquet file."""
    preds_path = tmp_path / "mock_champion_predictions.parquet"
    df = pl.DataFrame(
        {
            "meter_id": [f"METER_{i:04d}" for i in range(100)],
            "timestamp": ["2016-10-30"] * 100,
            "tamper_label": [1 if i < 15 else 0 for i in range(100)],
            "raw_margin": [float(i - 50) / 10.0 for i in range(100)],
            "uncalibrated_prob": [
                min(0.99, max(0.01, 1.0 / (1.0 + 2.718 ** (-(i - 50) / 10.0)))) for i in range(100)
            ],
            "predicted_prob": [min(0.95, max(0.02, float(i) / 100.0)) for i in range(100)],
            "prediction": [1 if i >= 50 else 0 for i in range(100)],
            "estimated_leakage_cost": [float(i * 50.0) for i in range(100)],
        }
    )
    df.write_parquet(preds_path)
    return preds_path


def test_decision_pipeline_end_to_end(
    tmp_path: Path,
    synthetic_predictions_file: Path,
) -> None:
    """Verify end-to-end execution of Phase 7 decision pipeline."""
    out_dir = tmp_path / "decision_artifacts"

    settings = Settings()
    settings.decision.dispatch_cost = 100.0

    pipeline = DecisionPipeline(settings=settings)
    summary = pipeline.run(
        predictions_path=synthetic_predictions_file,
        output_dir=out_dir,
        enable_mlflow=False,
    )

    # 1. Check returned summary structure
    assert "primary_queue_summary" in summary
    assert "policy_comparison" in summary
    assert "top_k_ranking" in summary
    assert "scenario_sensitivity" in summary

    prim_sum = summary["primary_queue_summary"]
    assert prim_sum["total_candidates"] == 100
    assert prim_sum["inspections_recommended"] > 0
    assert prim_sum["expected_financials"]["expected_net_value"] > 0

    # 2. Check exported artifacts
    assert (out_dir / "inspection_tickets.parquet").is_file()
    assert (out_dir / "inspection_tickets.csv").is_file()
    assert (out_dir / "top_100_inspection_tickets.csv").is_file()
    assert (out_dir / "decision_comparison.json").is_file()
    assert (out_dir / "decision_comparison_report.md").is_file()

    # 3. Check figures
    figs_dir = out_dir / "figures"
    assert (figs_dir / "env_distribution.png").is_file()
    assert (figs_dir / "probability_vs_env.png").is_file()
    assert (figs_dir / "threshold_vs_financial_exposure.png").is_file()
    assert (figs_dir / "cumulative_env_by_rank.png").is_file()
    assert (figs_dir / "policy_comparison_bar.png").is_file()

    # 4. Verify parquet schema
    df_tck = pl.read_parquet(out_dir / "inspection_tickets.parquet")
    assert "ticket_id" in df_tck.columns
    assert "meter_id" in df_tck.columns
    assert "env" in df_tck.columns
    assert "tau_cost" in df_tck.columns
    assert "tau_env" in df_tck.columns
    assert "priority_rank" in df_tck.columns
