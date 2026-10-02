"""Mathematical calculation of dynamic decision thresholds: Bayes cost threshold and ENV economic threshold."""

from __future__ import annotations

import numpy as np

from grid_guard.config.decision import DecisionRule


def compute_bayes_cost_threshold(
    dispatch_cost: float,
    fn_cost: float | np.ndarray,
) -> float | np.ndarray:
    """Compute the Bayes decision threshold that minimizes expected classification error loss.

    Derivation:
        Expected cost of inspect:   E[Cost | Inspect] = (1 - p_i) * C_dispatch + p_i * 0 = (1 - p_i) * C_dispatch
        Expected cost of no-inspect: E[Cost | No Inspect] = p_i * C_FN_i + (1 - p_i) * 0 = p_i * C_FN_i

        Inspect if E[Cost | Inspect] <= E[Cost | No Inspect]:
            (1 - p_i) * C_dispatch <= p_i * C_FN_i
            C_dispatch <= p_i * (C_dispatch + C_FN_i)
            p_i >= C_dispatch / (C_dispatch + C_FN_i) = tau_cost_i

    Args:
        dispatch_cost: Field crew inspection dispatch cost C_FP = C_dispatch ($).
        fn_cost: Financial leakage cost of missing a tampering case C_FN_i ($).

    Returns:
        tau_cost_i in range [0.0, 1.0].
    """
    if dispatch_cost < 0:
        raise ValueError(f"dispatch_cost must be non-negative, got {dispatch_cost}")

    is_scalar = np.isscalar(fn_cost)
    fn_arr = np.asarray(fn_cost, dtype=np.float64) if not is_scalar else float(fn_cost)

    if dispatch_cost == 0.0:
        return 0.0 if is_scalar else np.zeros_like(fn_arr)

    if is_scalar:
        if fn_arr <= 0.0:
            return 1.0
        denom = dispatch_cost + fn_arr
        val = dispatch_cost / denom
        return float(np.clip(val, 0.0, 1.0))

    # Array computation
    tau = np.ones_like(fn_arr, dtype=np.float64)
    positive_fn = fn_arr > 0.0
    denom = dispatch_cost + fn_arr[positive_fn]
    tau[positive_fn] = np.clip(dispatch_cost / denom, 0.0, 1.0)
    return tau


def compute_env_threshold(
    dispatch_cost: float,
    recoverable_revenue: float | np.ndarray,
) -> float | np.ndarray:
    """Compute the direct economic threshold required for positive Expected Net Value (ENV).

    Derivation:
        ENV_i = p_i * R_i - C_dispatch
        Inspect if ENV_i > 0:
            p_i * R_i - C_dispatch > 0
            p_i > C_dispatch / R_i = tau_env_i (when R_i > 0)

    Args:
        dispatch_cost: Field crew inspection dispatch cost C_dispatch ($).
        recoverable_revenue: Estimated recoverable revenue R_i ($).

    Returns:
        tau_env_i. If R_i <= 0, returns np.inf (inspection can never yield positive ENV).
    """
    if dispatch_cost < 0:
        raise ValueError(f"dispatch_cost must be non-negative, got {dispatch_cost}")

    is_scalar = np.isscalar(recoverable_revenue)
    r_arr = (
        np.asarray(recoverable_revenue, dtype=np.float64)
        if not is_scalar
        else float(recoverable_revenue)
    )

    if dispatch_cost == 0.0:
        return 0.0 if is_scalar else np.zeros_like(r_arr)

    if is_scalar:
        if r_arr <= 0.0:
            return float("inf")
        return float(dispatch_cost / r_arr)

    # Array computation
    tau = np.full_like(r_arr, np.inf, dtype=np.float64)
    positive_r = r_arr > 0.0
    tau[positive_r] = dispatch_cost / r_arr[positive_r]
    return tau


def compute_active_threshold(
    tau_cost: np.ndarray,
    tau_env: np.ndarray,
    decision_rule: DecisionRule | str = DecisionRule.ENV,
    fixed_threshold: float = 0.5,
) -> np.ndarray:
    """Return the threshold array matching the active operational decision rule.

    Args:
        tau_cost: Pre-computed Bayes cost thresholds array.
        tau_env: Pre-computed ENV economic thresholds array.
        decision_rule: Active rule ('env', 'cost_threshold', 'fixed_threshold').
        fixed_threshold: Constant threshold for fixed_threshold mode (default 0.5).

    Returns:
        Array of active threshold values corresponding to each observation.
    """
    rule_str = (
        decision_rule.value if isinstance(decision_rule, DecisionRule) else str(decision_rule)
    )

    if rule_str == DecisionRule.ENV.value:
        return tau_env
    elif rule_str == DecisionRule.COST_THRESHOLD.value:
        return tau_cost
    elif rule_str == DecisionRule.FIXED_THRESHOLD.value:
        return np.full_like(tau_cost, fixed_threshold, dtype=np.float64)
    else:
        raise ValueError(
            f"Unknown decision_rule: '{decision_rule}'. Supported: {[r.value for r in DecisionRule]}"
        )
