"""Expected Net Value (ENV) and expected gross recovery calculations."""

from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger(__name__)


def compute_expected_net_value(
    probabilities: np.ndarray | list[float],
    recoverable_revenue: np.ndarray | list[float],
    dispatch_cost: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Calculate expected gross recovery and Expected Net Value (ENV) per candidate meter.

    Equations:
        Expected Recovery_i = p_i * R_i
        ENV_i = Expected Recovery_i - C_dispatch = p_i * R_i - C_dispatch

    Safety & Edge Cases:
        - Validates probabilities in range [0.0, 1.0].
        - Validates dispatch_cost >= 0.0.
        - Clamps any negative recoverable revenue to 0.0 with warning.
        - NaN / Infinite values are rejected with ValueError.

    Args:
        probabilities: Array of predicted tampering probabilities (p_i).
        recoverable_revenue: Array of estimated recoverable revenue values (R_i).
        dispatch_cost: Field crew physical inspection dispatch cost C_dispatch ($).

    Returns:
        Tuple of (expected_gross_recovery, env) as 1D float64 NumPy arrays.
    """
    if dispatch_cost < 0:
        raise ValueError(f"dispatch_cost must be non-negative, got {dispatch_cost}")

    p = np.asarray(probabilities, dtype=np.float64)
    r = np.asarray(recoverable_revenue, dtype=np.float64)

    if p.shape != r.shape:
        raise ValueError(
            f"Shape mismatch: probabilities shape {p.shape} != recoverable_revenue shape {r.shape}"
        )

    if np.any(np.isnan(p)) or np.any(np.isinf(p)):
        raise ValueError("Probabilities contain NaN or Infinite values.")

    if np.any(p < 0.0) or np.any(p > 1.0):
        # Allow tiny numerical epsilon margin
        if np.any(p < -1e-5) or np.any(p > 1.0 + 1e-5):
            raise ValueError(
                f"Probabilities must be within [0.0, 1.0], found min={np.min(p)}, max={np.max(p)}"
            )
        p = np.clip(p, 0.0, 1.0)

    if np.any(np.isnan(r)) or np.any(np.isinf(r)):
        raise ValueError("Recoverable revenue contains NaN or Infinite values.")

    if np.any(r < 0.0):
        neg_count = int(np.sum(r < 0.0))
        logger.warning("Found %d negative recoverable revenue values. Clamping to 0.0.", neg_count)
        r = np.maximum(0.0, r)

    # Core vectorized calculation
    expected_gross_recovery = p * r
    env = expected_gross_recovery - dispatch_cost

    return expected_gross_recovery, env
