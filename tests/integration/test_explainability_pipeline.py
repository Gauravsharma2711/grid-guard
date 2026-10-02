"""Integration tests for Phase 8 Explainability Pipeline."""

from pathlib import Path

import pytest

from grid_guard.config.settings import get_settings
from grid_guard.models.explainability_pipeline import ExplainabilityPipeline


def test_explainability_pipeline_execution(tmp_path: Path) -> None:
    """Test full explainability pipeline execution on top 5 tickets."""
    root = Path(__file__).resolve().parent.parent.parent
    model_path = root / "artifacts/cost_sensitive/champion_model.txt"
    feat_path = root / "data/processed/canonical_features.parquet"
    tickets_path = root / "artifacts/decision/top_100_inspection_tickets.csv"

    if not model_path.is_file() or not feat_path.is_file() or not tickets_path.is_file():
        pytest.skip("Required Phase 6/7 artifacts not present for integration test")

    settings = get_settings()
    settings.explainability.top_k_tickets = 5
    settings.explainability.global_sample_size = 50

    pipeline = ExplainabilityPipeline(settings=settings)
    out_dir = tmp_path / "explainability"

    results = pipeline.run(
        model_path=model_path,
        feature_parquet_path=feat_path,
        tickets_csv_path=tickets_path,
        output_dir=out_dir,
        enable_mlflow=False,
    )

    assert results["top_tickets_count"] == 5
    assert (out_dir / "global_shap_importance.csv").is_file()
    assert (out_dir / "global_shap_importance.json").is_file()
    assert (out_dir / "enriched_top_100_tickets.csv").is_file()
    assert (out_dir / "enriched_top_100_tickets.parquet").is_file()
    assert (out_dir / "top_10_inspection_explanations.json").is_file()
    assert (out_dir / "explainability_report.md").is_file()
    assert (out_dir / "figures/global_shap_importance.png").is_file()
    assert (out_dir / "figures/category_attribution_pie_bar.png").is_file()
