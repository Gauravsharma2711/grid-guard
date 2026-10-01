"""Unit tests for baseline LightGBM model, temporal splitting, and evaluation metrics."""

from __future__ import annotations

from datetime import date, timedelta

import polars as pl
import pytest

from grid_guard.config.financial import BaselineModelSettings
from grid_guard.evaluation.metrics import (
    ClassificationMetricsEvaluator,
    RankingEvaluator,
)
from grid_guard.models.baseline import BaselineLightGBM
from grid_guard.models.splitting import TemporalDataSplitter


def test_temporal_splitter_validation() -> None:
    """Verify temporal splitter validates split boundaries chronologically."""
    # Invalid: val_start <= train_end
    bad_config = BaselineModelSettings(
        train_start="2020-01-01",
        train_end="2020-06-01",
        val_start="2020-05-01",  # Overlaps with train!
        val_end="2020-08-01",
    )
    with pytest.raises(ValueError, match="Invalid temporal split"):
        TemporalDataSplitter(config=bad_config)


def test_temporal_splitter_and_feature_separation() -> None:
    """Verify strictly temporal partitioning and target exclusion from features."""
    config = BaselineModelSettings(
        train_start="2020-01-01",
        train_end="2020-03-31",
        val_start="2020-04-01",
        val_end="2020-05-31",
        test_start="2020-06-01",
        test_end="2020-07-31",
        sampling_stride_days=1,
    )
    splitter = TemporalDataSplitter(config=config)

    # Synthetic daily dataset across 7 months
    dates = [date(2020, 1, 1) + timedelta(days=i) for i in range(210)]
    df = pl.DataFrame(
        {
            "meter_id": ["M1"] * 210,
            "timestamp": dates,
            "feat_a": [float(i % 10) for i in range(210)],
            "feat_b": [float(i * 0.5) for i in range(210)],
            "tamper_label": [0] * 180 + [1] * 30,
            "data_quality_status": ["EXCELLENT"] * 210,
        }
    )

    train_part, val_part, test_part = splitter.split(df, sampling_stride_days=1)

    # Check boundaries
    assert train_part.end_date < val_part.start_date
    assert val_part.end_date < test_part.start_date
    assert train_part.num_samples > 0
    assert val_part.num_samples > 0
    assert test_part.num_samples > 0

    # Ensure target and meter_id are excluded from X
    assert "tamper_label" not in train_part.X.columns
    assert "meter_id" not in train_part.X.columns
    assert "timestamp" not in train_part.X.columns
    assert train_part.X.columns == ["feat_a", "feat_b"]


def test_baseline_lightgbm_training_and_unweighted_spec() -> None:
    """Verify LightGBM trains strictly unweighted and yields deterministic outputs."""
    config = BaselineModelSettings(
        learning_rate=0.1,
        n_estimators=10,
        random_state=42,
    )
    model = BaselineLightGBM(config=config)

    # Verify unweighted specification
    assert model.params["class_weight"] is None
    assert model.params["scale_pos_weight"] == 1.0

    # Synthetic features
    X = pl.DataFrame(
        {
            "feat1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
            "feat2": [0.1, 0.2, 0.1, 0.3, 0.8, 0.9, 0.7, 0.9],
        }
    )
    y = pl.Series("label", [0, 0, 0, 0, 1, 1, 1, 1], dtype=pl.Int8)

    model.fit(X, y)
    probs = model.predict_proba(X)
    preds = model.predict(X, threshold=0.5)

    assert len(probs) == 8
    assert all(0.0 <= p <= 1.0 for p in probs)
    assert len(preds) == 8

    # Feature importance
    imp_gain = model.get_feature_importance("gain")
    assert len(imp_gain) == 2
    assert "importance" in imp_gain.columns
    assert "rank" in imp_gain.columns


def test_classification_and_ranking_metrics() -> None:
    """Verify statistical metrics and operational Top-K precision."""
    y_true = [0, 0, 0, 0, 1, 1, 1, 1]
    y_prob = [0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9]
    y_pred = [0, 0, 0, 0, 1, 1, 1, 1]

    # Classification metrics
    stats = ClassificationMetricsEvaluator.evaluate(y_true, y_pred, y_prob)
    assert stats["precision"] == 1.0
    assert stats["recall"] == 1.0
    assert stats["f1_score"] == 1.0
    assert stats["roc_auc"] == 1.0
    assert stats["pr_auc"] == 1.0
    assert stats["confusion_matrix"]["tp"] == 4
    assert stats["confusion_matrix"]["fp"] == 0

    # Top-K ranking
    top_k = RankingEvaluator.evaluate_top_k(y_true, y_prob, k_values=[2, 4])
    assert top_k["2"]["precision_at_k"] == 1.0  # Top 2 are indices with prob 0.9, 0.8 (both true=1)
    assert top_k["4"]["precision_at_k"] == 1.0  # Top 4 are all true=1
    assert top_k["4"]["recall_at_k"] == 1.0  # All 4 positives captured
