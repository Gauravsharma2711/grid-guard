"""Unit tests for SHAP TreeExplainer wrapper and additive reconstruction."""

from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
import pytest

from grid_guard.explainability.shap_explainer import ShapExplainer


@pytest.fixture
def champion_model_path() -> Path:
    """Resolve path to Phase 6 champion LightGBM model."""
    root = Path(__file__).resolve().parent.parent.parent
    path = root / "artifacts/cost_sensitive/champion_model.txt"
    if not path.is_file():
        pytest.skip(f"Model file not found at {path}")
    return path


def test_shap_explainer_init(champion_model_path: Path) -> None:
    """Test TreeExplainer initialization and expected base value."""
    explainer = ShapExplainer(model=champion_model_path)
    assert len(explainer.feature_names) == 60
    # Expected base log-odds value around -2.59
    assert -3.0 < explainer.base_value < -2.0


def test_shap_explain_and_additive_reconstruction(champion_model_path: Path) -> None:
    """Test SHAP value computation and exact additive reconstruction on synthetic test batch."""
    explainer = ShapExplainer(model=champion_model_path)
    np.random.seed(42)

    # Generate synthetic observations with realistic positive values
    n_samples = 10
    synth_data = np.abs(np.random.randn(n_samples, len(explainer.feature_names)) * 5.0)
    df_synth = pd.DataFrame(synth_data, columns=explainer.feature_names)

    # Compute SHAP and verify reconstruction
    shap_matrix = explainer.explain(df_synth, verify_reconstruction=True, tolerance=1e-4)

    assert shap_matrix.shape == (n_samples, 60)
    assert not np.isnan(shap_matrix).any()
    assert not np.isinf(shap_matrix).any()

    # Manual verification of additive property: base_val + sum(shap) == raw_margin
    model = lgb.Booster(model_file=str(champion_model_path))
    raw_margin = model.predict(df_synth, raw_score=True)
    reconstructed = explainer.base_value + shap_matrix.sum(axis=1)

    np.testing.assert_allclose(reconstructed, raw_margin, atol=1e-5)


def test_global_importance(champion_model_path: Path) -> None:
    """Test global feature importance ranking calculation."""
    explainer = ShapExplainer(model=champion_model_path)
    np.random.seed(42)
    synth_data = np.abs(np.random.randn(20, len(explainer.feature_names)))
    df_synth = pd.DataFrame(synth_data, columns=explainer.feature_names)

    shap_matrix = explainer.explain(df_synth, verify_reconstruction=True)
    importance = explainer.get_global_importance(shap_matrix)

    assert len(importance) == 60
    assert importance[0]["rank"] == 1
    # Verify sorted descending by mean_abs_shap
    for i in range(len(importance) - 1):
        assert importance[i]["mean_abs_shap"] >= importance[i + 1]["mean_abs_shap"]


def test_instance_breakdown(champion_model_path: Path) -> None:
    """Test decomposition of individual sample into positive and negative drivers."""
    explainer = ShapExplainer(model=champion_model_path)
    np.random.seed(42)
    synth_data = np.abs(np.random.randn(1, len(explainer.feature_names)))
    df_synth = pd.DataFrame(synth_data, columns=explainer.feature_names)

    shap_matrix = explainer.explain(df_synth, verify_reconstruction=True)
    pos, neg = explainer.explain_instance(
        instance_row=df_synth.iloc[0],
        shap_row=shap_matrix[0],
        max_positive=4,
        max_negative=2,
    )

    assert len(pos) <= 4
    assert len(neg) <= 2
    for p in pos:
        assert p.contribution_direction == "positive"
        assert p.shap_value > 0
    for n in neg:
        assert n.contribution_direction == "negative"
        assert n.shap_value < 0
