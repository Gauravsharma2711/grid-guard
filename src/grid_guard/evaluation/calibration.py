"""Probability calibration assessment, Brier score, and reliability curve evaluation."""

from __future__ import annotations

from typing import Any

import numpy as np
import polars as pl
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss


class CalibrationEvaluator:
    """Evaluates the calibration quality of predicted probabilities under class imbalance."""

    @staticmethod
    def evaluate(
        y_true: list[int] | np.ndarray | pl.Series,
        y_prob: list[float] | np.ndarray | pl.Series,
        n_bins: int = 10,
    ) -> dict[str, Any]:
        """Compute Brier score, expected calibration error (ECE), and binned reliability coordinates.

        Args:
            y_true: Ground truth binary labels (0 or 1).
            y_prob: Predicted positive class probabilities in [0.0, 1.0].
            n_bins: Number of probability bins for reliability curve.

        Returns:
            Dictionary containing Brier score, ECE, and binned calibration points.
        """
        yt = np.asarray(y_true, dtype=np.int32)
        yp = np.asarray(y_prob, dtype=np.float32)

        # 1. Brier score loss: mean squared error of probability predictions
        brier = float(brier_score_loss(yt, yp))

        # 2. Calibration curve points
        prob_true, prob_pred = calibration_curve(yt, yp, n_bins=n_bins, strategy="uniform")

        # 3. Expected Calibration Error (ECE)
        bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
        ece = 0.0
        total_samples = len(yt)

        binned_records: list[dict[str, float]] = []
        for i in range(len(prob_true)):
            # Find samples falling into this bin
            bin_lower = bin_edges[i]
            bin_upper = bin_edges[i + 1]
            if i == len(prob_true) - 1:
                mask = (yp >= bin_lower) & (yp <= bin_upper)
            else:
                mask = (yp >= bin_lower) & (yp < bin_upper)

            bin_count = int(mask.sum())
            weight = bin_count / total_samples if total_samples > 0 else 0.0
            error = abs(float(prob_true[i]) - float(prob_pred[i]))
            ece += weight * error

            binned_records.append(
                {
                    "bin_index": i,
                    "bin_count": bin_count,
                    "mean_predicted_prob": round(float(prob_pred[i]), 4),
                    "fraction_of_positives": round(float(prob_true[i]), 4),
                    "calibration_gap": round(error, 4),
                }
            )

        return {
            "brier_score": round(brier, 4),
            "expected_calibration_error": round(float(ece), 4),
            "n_bins": n_bins,
            "binned_calibration": binned_records,
            "prob_true": [round(float(v), 4) for v in prob_true],
            "prob_pred": [round(float(v), 4) for v in prob_pred],
        }
