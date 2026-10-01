"""Statistical classification metrics and operational Top-K ranking evaluation."""

from __future__ import annotations

from typing import Any

import numpy as np
import polars as pl
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


class ClassificationMetricsEvaluator:
    """Computes standard supervised classification metrics on model predictions."""

    @staticmethod
    def evaluate(
        y_true: list[int] | np.ndarray | pl.Series,
        y_pred: list[int] | np.ndarray | pl.Series,
        y_prob: list[float] | np.ndarray | pl.Series,
    ) -> dict[str, Any]:
        """Compute comprehensive statistical classification metrics.

        Args:
            y_true: Ground truth binary labels (0 or 1).
            y_pred: Predicted binary labels (0 or 1 from threshold).
            y_prob: Predicted positive class probabilities in [0.0, 1.0].

        Returns:
            Dictionary of calculated metrics.
        """
        yt = np.asarray(y_true, dtype=np.int32)
        yp = np.asarray(y_pred, dtype=np.int32)
        prob = np.asarray(y_prob, dtype=np.float32)

        tn, fp, fn, tp = confusion_matrix(yt, yp, labels=[0, 1]).ravel()
        total = len(yt)

        # Handle ROC-AUC and PR-AUC safely if only one class exists
        n_pos = int(yt.sum())
        has_both_classes = 0 < n_pos < total

        pr_auc = float(average_precision_score(yt, prob)) if has_both_classes else 0.0
        roc_auc = float(roc_auc_score(yt, prob)) if has_both_classes else 0.5

        precision = float(precision_score(yt, yp, zero_division=0))
        recall = float(recall_score(yt, yp, zero_division=0))
        f1 = float(f1_score(yt, yp, zero_division=0))

        fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
        pos_pred_rate = float((tp + fp) / total) if total > 0 else 0.0

        return {
            "total_samples": total,
            "actual_positives": n_pos,
            "actual_negatives": total - n_pos,
            "prevalence": round(float(n_pos / total), 4) if total > 0 else 0.0,
            "confusion_matrix": {
                "tp": int(tp),
                "fp": int(fp),
                "tn": int(tn),
                "fn": int(fn),
            },
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "pr_auc": round(pr_auc, 4),
            "roc_auc": round(roc_auc, 4),
            "false_positive_rate": round(fpr, 4),
            "positive_prediction_rate": round(pos_pred_rate, 4),
        }


class RankingEvaluator:
    """Evaluates field inspection prioritization via Top-K ranking performance."""

    @staticmethod
    def evaluate_top_k(
        y_true: list[int] | np.ndarray | pl.Series,
        y_prob: list[float] | np.ndarray | pl.Series,
        k_values: list[int] | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Calculate Precision@K, Recall@K, and True Positives@K across target operational sizes.

        Args:
            y_true: Ground truth binary labels.
            y_prob: Predicted positive class probabilities.
            k_values: List of inspection dispatch capacities to evaluate.

        Returns:
            Dictionary mapping str(K) to ranking statistics.
        """
        yt = np.asarray(y_true, dtype=np.int32)
        prob = np.asarray(y_prob, dtype=np.float32)
        total_positives = int(yt.sum())

        # Sort indices by probability descending
        ranked_indices = np.argsort(prob)[::-1]
        ranked_true = yt[ranked_indices]

        eval_ks = k_values or [10, 50, 100, 500, 1000, 2000]
        results: dict[str, dict[str, Any]] = {}

        for k in eval_ks:
            actual_k = min(k, len(ranked_true))
            top_k_labels = ranked_true[:actual_k]

            tp_at_k = int(top_k_labels.sum())
            fp_at_k = actual_k - tp_at_k
            prec_at_k = float(tp_at_k / actual_k) if actual_k > 0 else 0.0
            recall_at_k = float(tp_at_k / total_positives) if total_positives > 0 else 0.0

            results[str(k)] = {
                "k": actual_k,
                "true_positives": tp_at_k,
                "false_positives": fp_at_k,
                "precision_at_k": round(prec_at_k, 4),
                "recall_at_k": round(recall_at_k, 4),
            }

        return results
