"""Unit tests for Expected Net Value (ENV) calculation, edge cases, and monotonicity."""

import numpy as np
import pytest

from grid_guard.decision.env import compute_expected_net_value
from grid_guard.decision.thresholds import (
    compute_bayes_cost_threshold,
    compute_env_threshold,
)


def test_compute_expected_net_value_core() -> None:
    """Verify core ENV calculation: ENV = p * R - C_dispatch."""
    probs = np.array([0.8, 0.5, 0.1])
    revs = np.array([1000.0, 200.0, 50.0])
    c_disp = 100.0

    exp_rec, env = compute_expected_net_value(probs, revs, c_disp)

    # Expected gross: [0.8*1000, 0.5*200, 0.1*50] = [800.0, 100.0, 5.0]
    assert np.allclose(exp_rec, [800.0, 100.0, 5.0])
    # ENV: [800-100, 100-100, 5-100] = [700.0, 0.0, -95.0]
    assert np.allclose(env, [700.0, 0.0, -95.0])


def test_env_edge_cases_economic_justification() -> None:
    """Verify that probability alone does not dictate positive ENV."""
    c_disp = 100.0

    # Case A: High probability (0.95), but tiny recovery ($40) -> Loss-making!
    _, env_a = compute_expected_net_value(np.array([0.95]), np.array([40.0]), c_disp)
    assert env_a[0] < 0.0, "High probability with tiny revenue must yield negative ENV"
    assert np.isclose(env_a[0], 0.95 * 40.0 - 100.0)  # -62.0

    # Case B: Moderate probability (0.15), but huge commercial recovery ($10,000) -> Profitable!
    _, env_b = compute_expected_net_value(np.array([0.15]), np.array([10000.0]), c_disp)
    assert env_b[0] > 0.0, "Moderate probability with massive revenue must yield positive ENV"
    assert np.isclose(env_b[0], 0.15 * 10000.0 - 100.0)  # +1400.0

    # Case C: Zero recovery -> ENV equals -C_dispatch
    _, env_c = compute_expected_net_value(np.array([1.0]), np.array([0.0]), c_disp)
    assert np.isclose(env_c[0], -100.0)


def test_env_monotonicity() -> None:
    """Verify strict mathematical monotonicity relationships of ENV."""
    p_fixed = 0.5
    r_fixed = 500.0
    c_fixed = 100.0

    # 1. Monotonicity wrt Dispatch Cost: Increasing C_dispatch must decrease ENV
    disp_costs = np.array([50.0, 100.0, 150.0, 200.0])
    envs_disp = [
        compute_expected_net_value(np.array([p_fixed]), np.array([r_fixed]), c)[1][0]
        for c in disp_costs
    ]
    for i in range(len(envs_disp) - 1):
        assert envs_disp[i] > envs_disp[i + 1]

    # 2. Monotonicity wrt Recoverable Revenue: Increasing R must increase ENV
    revenues = np.array([100.0, 250.0, 500.0, 1000.0])
    _, envs_rev = compute_expected_net_value(np.full_like(revenues, p_fixed), revenues, c_fixed)
    for i in range(len(envs_rev) - 1):
        assert envs_rev[i] < envs_rev[i + 1]

    # 3. Monotonicity wrt Probability: Increasing p must increase ENV
    probs = np.array([0.1, 0.3, 0.5, 0.8, 0.95])
    _, envs_prob = compute_expected_net_value(probs, np.full_like(probs, r_fixed), c_fixed)
    for i in range(len(envs_prob) - 1):
        assert envs_prob[i] < envs_prob[i + 1]

    # 4. Monotonicity of Bayes Threshold wrt FN Cost: Increasing C_FN must decrease tau_cost
    fn_costs = np.array([50.0, 100.0, 500.0, 2000.0])
    taus_bayes = compute_bayes_cost_threshold(c_fixed, fn_costs)
    for i in range(len(taus_bayes) - 1):
        assert taus_bayes[i] > taus_bayes[i + 1]

    # 5. Monotonicity of ENV Threshold wrt R: Increasing R must decrease tau_env
    taus_env = compute_env_threshold(c_fixed, revenues)
    for i in range(len(taus_env) - 1):
        assert taus_env[i] > taus_env[i + 1]


def test_env_validation_errors() -> None:
    """Verify input validation handles invalid domains properly."""
    # Negative dispatch cost
    with pytest.raises(ValueError, match="dispatch_cost must be non-negative"):
        compute_expected_net_value([0.5], [100.0], dispatch_cost=-50.0)

    # Probabilities out of bounds
    with pytest.raises(ValueError, match="Probabilities must be within"):
        compute_expected_net_value([-0.1, 0.5], [100.0, 100.0], dispatch_cost=100.0)

    with pytest.raises(ValueError, match="Probabilities must be within"):
        compute_expected_net_value([0.5, 1.5], [100.0, 100.0], dispatch_cost=100.0)

    # NaN in inputs
    with pytest.raises(ValueError, match="NaN or Infinite"):
        compute_expected_net_value([np.nan], [100.0], dispatch_cost=100.0)

    with pytest.raises(ValueError, match="NaN or Infinite"):
        compute_expected_net_value([0.5], [np.nan], dispatch_cost=100.0)
