"""Unit tests for dynamic decision thresholds: Bayes cost threshold and ENV economic threshold."""

import numpy as np
import pytest

from grid_guard.config.decision import DecisionRule
from grid_guard.decision.thresholds import (
    compute_active_threshold,
    compute_bayes_cost_threshold,
    compute_env_threshold,
)


def test_bayes_cost_threshold_scalar() -> None:
    """Verify scalar Bayes cost threshold calculation."""
    dispatch_cost = 100.0

    # When FN cost equals dispatch cost, threshold is exactly 0.5
    tau_equal = compute_bayes_cost_threshold(dispatch_cost=dispatch_cost, fn_cost=100.0)
    assert np.isclose(tau_equal, 0.5)

    # When FN cost is 900, threshold is 100 / (100 + 900) = 0.1
    tau_high_fn = compute_bayes_cost_threshold(dispatch_cost=dispatch_cost, fn_cost=900.0)
    assert np.isclose(tau_high_fn, 0.1)

    # When FN cost is 0, threshold is 1.0 (never inspect if zero cost for missing)
    tau_zero_fn = compute_bayes_cost_threshold(dispatch_cost=dispatch_cost, fn_cost=0.0)
    assert np.isclose(tau_zero_fn, 1.0)

    # When dispatch cost is 0, threshold is 0.0 (free inspection)
    tau_free_disp = compute_bayes_cost_threshold(dispatch_cost=0.0, fn_cost=100.0)
    assert np.isclose(tau_free_disp, 0.0)


def test_bayes_cost_threshold_array() -> None:
    """Verify vectorized Bayes cost threshold calculation."""
    fn_costs = np.array([0.0, 100.0, 300.0, 900.0, 9900.0])
    taus = compute_bayes_cost_threshold(dispatch_cost=100.0, fn_cost=fn_costs)

    assert isinstance(taus, np.ndarray)
    assert len(taus) == 5
    assert np.isclose(taus[0], 1.0)
    assert np.isclose(taus[1], 0.5)
    assert np.isclose(taus[2], 0.25)
    assert np.isclose(taus[3], 0.10)
    assert np.isclose(taus[4], 0.01)


def test_env_threshold_scalar() -> None:
    """Verify scalar direct ENV economic threshold calculation."""
    dispatch_cost = 100.0

    # When R = 200, tau_env = 100 / 200 = 0.5
    tau_50 = compute_env_threshold(dispatch_cost=dispatch_cost, recoverable_revenue=200.0)
    assert np.isclose(tau_50, 0.5)

    # When R = 1000, tau_env = 100 / 1000 = 0.1
    tau_10 = compute_env_threshold(dispatch_cost=dispatch_cost, recoverable_revenue=1000.0)
    assert np.isclose(tau_10, 0.1)

    # When R <= 0, tau_env is infinity (inspection can never yield positive ENV)
    tau_zero_r = compute_env_threshold(dispatch_cost=100.0, recoverable_revenue=0.0)
    assert np.isinf(tau_zero_r)

    tau_neg_r = compute_env_threshold(dispatch_cost=100.0, recoverable_revenue=-50.0)
    assert np.isinf(tau_neg_r)


def test_env_threshold_array() -> None:
    """Verify vectorized direct ENV economic threshold calculation."""
    revenues = np.array([0.0, 100.0, 200.0, 500.0, 1000.0])
    taus = compute_env_threshold(dispatch_cost=100.0, recoverable_revenue=revenues)

    assert np.isinf(taus[0])
    assert np.isclose(taus[1], 1.0)
    assert np.isclose(taus[2], 0.5)
    assert np.isclose(taus[3], 0.2)
    assert np.isclose(taus[4], 0.1)


def test_threshold_distinction_theorem() -> None:
    """Mathematically prove that tau_cost < tau_env for all positive C_dispatch, R = C_FN."""
    c_disp = 100.0
    revenues = np.array([50.0, 100.0, 250.0, 500.0, 2000.0, 10000.0])

    tau_cost = compute_bayes_cost_threshold(dispatch_cost=c_disp, fn_cost=revenues)
    tau_env = compute_env_threshold(dispatch_cost=c_disp, recoverable_revenue=revenues)

    # For all positive values, C/(C+R) < C/R
    assert np.all(tau_cost < tau_env)


def test_compute_active_threshold() -> None:
    """Verify selection of active threshold array according to DecisionRule."""
    tau_cost = np.array([0.1, 0.2, 0.3])
    tau_env = np.array([0.4, 0.5, 0.6])

    # Rule: ENV
    active_env = compute_active_threshold(tau_cost, tau_env, decision_rule=DecisionRule.ENV)
    assert np.array_equal(active_env, tau_env)

    # Rule: COST_THRESHOLD
    active_cost = compute_active_threshold(
        tau_cost, tau_env, decision_rule=DecisionRule.COST_THRESHOLD
    )
    assert np.array_equal(active_cost, tau_cost)

    # Rule: FIXED_THRESHOLD
    active_fixed = compute_active_threshold(
        tau_cost, tau_env, decision_rule=DecisionRule.FIXED_THRESHOLD, fixed_threshold=0.5
    )
    assert np.all(active_fixed == 0.5)


def test_threshold_invalid_dispatch_cost() -> None:
    """Verify negative dispatch cost raises ValueError."""
    with pytest.raises(ValueError, match="dispatch_cost must be non-negative"):
        compute_bayes_cost_threshold(dispatch_cost=-10.0, fn_cost=100.0)

    with pytest.raises(ValueError, match="dispatch_cost must be non-negative"):
        compute_env_threshold(dispatch_cost=-10.0, recoverable_revenue=100.0)
