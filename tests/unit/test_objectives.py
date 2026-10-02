"""Unit tests for cost-sensitive custom objective mathematics, gradients, and numerical stability."""

from __future__ import annotations

import numpy as np
import pytest

from grid_guard.models.objectives import (
    CostSensitiveWeightedLogisticObjective,
    cost_sensitive_logistic_grad_hess,
    sigmoid_stable,
    verify_gradients_finite_differences,
)


def test_sigmoid_stable_bounds() -> None:
    """Verify that sigmoid_stable avoids numerical overflow/underflow on extreme logits."""
    extreme_z = np.array([-1000.0, -50.0, -10.0, 0.0, 10.0, 50.0, 1000.0])
    p = sigmoid_stable(extreme_z)

    assert np.all(p > 0.0)
    assert np.all(p < 1.0)
    assert np.all(np.isfinite(p))
    assert np.isclose(p[3], 0.5)
    assert p[0] <= p[1] < p[2] < p[3] < p[4] < p[5] <= p[6]


def test_analytical_gradient_and_hessian_formulas() -> None:
    """Verify exact formula values on controlled synthetic cases."""
    z = np.array([0.0, 0.0, 2.0, -2.0])
    y = np.array([1.0, 0.0, 1.0, 0.0])
    w = np.array([10.0, 2.0, 5.0, 4.0])

    grad, hess = cost_sensitive_logistic_grad_hess(z, y, w)

    # For z=0, p=0.5
    # i=0: y=1, w=10 -> grad = 10 * (0.5 - 1) = -5.0, hess = 10 * 0.5 * 0.5 = 2.5
    assert np.isclose(grad[0], -5.0)
    assert np.isclose(hess[0], 2.5)

    # i=1: y=0, w=2 -> grad = 2 * (0.5 - 0) = +1.0, hess = 2 * 0.5 * 0.5 = 0.5
    assert np.isclose(grad[1], 1.0)
    assert np.isclose(hess[1], 0.5)

    # All Hessians strictly positive
    assert np.all(hess > 0.0)


def test_finite_difference_gradient_and_hessian() -> None:
    """Verify analytical gradient and Hessian match central finite differences."""
    margins = [-4.0, -2.0, -0.5, 0.0, 0.5, 2.0, 4.0]
    labels = [0, 1]
    weights = [0.1, 1.0, 10.0, 250.0]

    for z_val in margins:
        for y_val in labels:
            for w_val in weights:
                is_valid = verify_gradients_finite_differences(
                    z=z_val, y=y_val, weight=w_val, eps=1e-6, rtol=1e-4
                )
                assert is_valid, (
                    f"Finite difference check failed for z={z_val}, y={y_val}, w={w_val}"
                )


def test_strictly_positive_hessian_guarantee() -> None:
    """Verify that Hessian remains strictly positive even under extreme margins."""
    extreme_margins = np.array([-100.0, -30.0, 0.0, 30.0, 100.0])
    y = np.array([0, 1, 0, 1, 0])
    w = np.array([1.0, 10.0, 100.0, 1000.0, 50.0])

    grad, hess = cost_sensitive_logistic_grad_hess(extreme_margins, y, w)

    assert np.all(np.isfinite(grad))
    assert np.all(np.isfinite(hess))
    assert np.all(hess > 0.0), f"Hessian values must be strictly positive: {hess}"


def test_invalid_weight_rejection() -> None:
    """Verify that non-positive, NaN, or infinite weights are rejected."""
    z = np.array([0.0, 1.0])
    y = np.array([1, 0])

    with pytest.raises(ValueError, match="strictly positive and finite"):
        cost_sensitive_logistic_grad_hess(z, y, np.array([0.0, 10.0]))

    with pytest.raises(ValueError, match="strictly positive and finite"):
        cost_sensitive_logistic_grad_hess(z, y, np.array([-5.0, 10.0]))

    with pytest.raises(ValueError, match="strictly positive and finite"):
        cost_sensitive_logistic_grad_hess(z, y, np.array([np.nan, 10.0]))


def test_objective_callable_protocol() -> None:
    """Verify CostSensitiveWeightedLogisticObjective works via LightGBM Dataset protocol."""
    z = np.array([0.0, 1.0, -1.0])
    y = np.array([1, 0, 1])
    w = np.array([5.0, 1.0, 10.0])

    class MockDataset:
        def get_label(self) -> np.ndarray:
            return y

        def get_weight(self) -> np.ndarray:
            return w

    obj = CostSensitiveWeightedLogisticObjective()
    grad, hess = obj(z, MockDataset())

    assert len(grad) == 3
    assert len(hess) == 3
    assert np.all(hess > 0.0)
