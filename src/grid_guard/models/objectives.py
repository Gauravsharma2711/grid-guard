"""Mathematically verified, numerically stable custom cost-sensitive objectives for gradient boosting."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


def sigmoid_stable(z: np.ndarray, margin_clip: float = 30.0) -> np.ndarray:
    """Compute element-wise numerically stable sigmoid probability with margin clipping.

    Args:
        z: Raw prediction margins / logits.
        margin_clip: Maximum absolute value for logits to prevent overflow/underflow in exp.

    Returns:
        Predicted probabilities in (0, 1).
    """
    z_clipped = np.clip(z, -margin_clip, margin_clip)
    return 1.0 / (1.0 + np.exp(-z_clipped))


def cost_sensitive_logistic_loss(
    z: np.ndarray,
    y: np.ndarray,
    weights: np.ndarray,
    eps: float = 1e-15,
) -> np.ndarray:
    """Compute point-wise cost-weighted logistic loss.

    Formula:
        L_i = w_i * [ -y_i * ln(p_i) - (1 - y_i) * ln(1 - p_i) ]

    Args:
        z: Raw prediction margins / logits.
        y: Ground truth binary labels (0 or 1).
        weights: Per-observation positive financial weights w_i > 0.
        eps: Small probability clipping value to prevent log(0).

    Returns:
        Array of point-wise loss values.
    """
    p = sigmoid_stable(z)
    p_clipped = np.clip(p, eps, 1.0 - eps)
    return weights * (-y * np.log(p_clipped) - (1.0 - y) * np.log(1.0 - p_clipped))


def cost_sensitive_logistic_grad_hess(
    z: np.ndarray,
    y: np.ndarray,
    weights: np.ndarray,
    min_hess: float = 1e-12,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute first and second derivatives of the cost-weighted logistic objective wrt margins.

    Mathematical Derivation:
        L_i = w_i * [ -y_i * ln(p_i) - (1 - y_i) * ln(1 - p_i) ]
        where p_i = sigmoid(z_i) = 1 / (1 + exp(-z_i))

        Gradient wrt margin z_i:
            g_i = dL_i / dz_i = w_i * (p_i - y_i)

        Hessian wrt margin z_i:
            h_i = d^2L_i / dz_i^2 = w_i * p_i * (1 - p_i)

        Positive Hessian Guarantee:
            Since w_i > 0 and 0 < p_i < 1 for all finite margins z_i,
            h_i is strictly positive: h_i > 0.

    Args:
        z: Raw prediction margins / logits (1D array of shape (N,)).
        y: Ground truth binary labels (1D array of shape (N,)).
        weights: Per-observation positive financial weights w_i > 0.
        min_hess: Minimum numerical floor for the Hessian to prevent exact zeros.

    Returns:
        Tuple of (grad, hess) both of shape (N,) as float64 / float32.
    """
    # Enforce 1D array alignment
    z_arr = np.asarray(z, dtype=np.float64).ravel()
    y_arr = np.asarray(y, dtype=np.float64).ravel()
    w_arr = np.asarray(weights, dtype=np.float64).ravel()

    if len(z_arr) != len(y_arr) or len(y_arr) != len(w_arr):
        raise ValueError(
            f"Dimension mismatch in objective: z={len(z_arr)}, y={len(y_arr)}, w={len(w_arr)}."
        )

    # Reject non-positive or invalid weights
    if np.any(np.isnan(w_arr)) or np.any(w_arr <= 0.0):
        invalid_cnt = int(np.sum(np.isnan(w_arr) | (w_arr <= 0.0)))
        raise ValueError(
            f"Financial weights must be strictly positive and finite. Found {invalid_cnt} invalid entries."
        )

    p = sigmoid_stable(z_arr)

    # 1st order gradient: g_i = w_i * (p_i - y_i)
    grad = w_arr * (p - y_arr)

    # 2nd order Hessian: h_i = w_i * p_i * (1 - p_i)
    hess = np.maximum(w_arr * p * (1.0 - p), min_hess)

    return grad, hess


class CostSensitiveWeightedLogisticObjective:
    """LightGBM-compatible custom objective callback for cost-sensitive learning.

    Implements the LightGBM objective protocol:
        objective(preds, dataset) -> (grad, hess)
    or
        objective(y_true, y_pred) -> (grad, hess)
    """

    def __init__(self, default_weights: np.ndarray | None = None) -> None:
        """Initialize the objective callback.

        Args:
            default_weights: Optional pre-computed training financial weights.
        """
        self.default_weights = (
            np.asarray(default_weights, dtype=np.float64).ravel()
            if default_weights is not None
            else None
        )

    def __call__(
        self,
        preds: np.ndarray,
        dataset: Any = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Compute gradient and Hessian for current boosting iteration.

        Supports both LightGBM native Dataset interface (fobj(preds, train_data))
        and sklearn callback interface (fobj(y_true, y_pred)).
        """
        # Case 1: LightGBM native Dataset interface: (preds, dataset)
        if hasattr(dataset, "get_label"):
            y = dataset.get_label()
            w = dataset.get_weight()
            if w is None or len(w) == 0:
                if self.default_weights is not None and len(self.default_weights) == len(y):
                    w = self.default_weights
                else:
                    w = np.ones_like(y, dtype=np.float64)
            return cost_sensitive_logistic_grad_hess(z=preds, y=y, weights=w)

        # Case 2: Sklearn API convention: (y_true, y_pred)
        if dataset is not None and isinstance(dataset, (np.ndarray, list)):
            # In sklearn custom objective, signature is (y_true, y_pred)
            y_true = np.asarray(preds, dtype=np.float64).ravel()
            y_pred_margins = np.asarray(dataset, dtype=np.float64).ravel()
            w = (
                self.default_weights
                if self.default_weights is not None
                else np.ones_like(y_true, dtype=np.float64)
            )
            return cost_sensitive_logistic_grad_hess(z=y_pred_margins, y=y_true, weights=w)

        # Fallback
        raise ValueError(
            "Unsupported calling convention for CostSensitiveWeightedLogisticObjective."
        )


def verify_gradients_finite_differences(
    z: float | np.ndarray,
    y: float | np.ndarray,
    weight: float | np.ndarray,
    eps: float = 1e-6,
    rtol: float = 1e-4,
) -> bool:
    """Analytically verify that custom gradient and Hessian match central finite differences.

    Args:
        z: Test margin value(s).
        y: Test label(s).
        weight: Test financial weight(s).
        eps: Small perturbation for numerical differentiation.
        rtol: Relative error tolerance threshold.

    Returns:
        True if all analytical values match numerical approximations within tolerance.
    """
    z_val = np.asarray(z, dtype=np.float64)
    y_val = np.asarray(y, dtype=np.float64)
    w_val = np.asarray(weight, dtype=np.float64)

    # Analytical
    grad_ana, hess_ana = cost_sensitive_logistic_grad_hess(z_val, y_val, w_val)

    # Numerical gradient: (L(z + eps) - L(z - eps)) / (2 * eps)
    l_plus = cost_sensitive_logistic_loss(z_val + eps, y_val, w_val)
    l_minus = cost_sensitive_logistic_loss(z_val - eps, y_val, w_val)
    grad_num = (l_plus - l_minus) / (2.0 * eps)

    # Numerical Hessian: (grad(z + eps) - grad(z - eps)) / (2 * eps)
    g_plus, _ = cost_sensitive_logistic_grad_hess(z_val + eps, y_val, w_val)
    g_minus, _ = cost_sensitive_logistic_grad_hess(z_val - eps, y_val, w_val)
    hess_num = (g_plus - g_minus) / (2.0 * eps)

    grad_matches = np.allclose(grad_ana, grad_num, rtol=rtol, atol=1e-6)
    hess_matches = np.allclose(hess_ana, hess_num, rtol=rtol, atol=1e-6)

    return bool(grad_matches and hess_matches)
