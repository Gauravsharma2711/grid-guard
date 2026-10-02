"""Comprehensive End-to-End Pipeline Integration Test.

Validates the complete execution chain:
Raw Smart-Meter Time-Series
  → Feature Pipeline (60 features)
  → Phase 6 Cost-Sensitive Booster
  → Financial Exposure & Expected Net Value (ENV)
  → Dynamic Decisioning
  → Tree-SHAP Local Attribution
  → Tampering Signature Extraction
  → FastAPI Endpoints
  → Dashboard Client Response Compatibility
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from grid_guard.api.main import app
from grid_guard.dashboard.api_client import DashboardApiClient
from grid_guard.dashboard.demo_data.synthetic_meters import (
    get_demo_meter,
)


@pytest.fixture(scope="module")
def api_client() -> TestClient:
    """Provide initialized FastAPI TestClient with lifespan context."""
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="module")
def dashboard_client(api_client: TestClient) -> DashboardApiClient:
    """Provide DashboardApiClient hooked directly into the TestClient."""
    return DashboardApiClient(base_url="http://testserver", client=api_client)


def test_end_to_end_health_and_readiness(dashboard_client: DashboardApiClient) -> None:
    """Verify health and readiness probe responses match Phase 9/10 contracts."""
    health = dashboard_client.check_health()
    assert health["status"] == "ok"
    assert health["service"] == "grid-guard-api"

    ready = dashboard_client.check_ready()
    assert ready["status"] == "ready"
    assert ready["model_loaded"] is True
    assert ready["explainer_loaded"] is True
    assert ready["feature_count"] == 60


def test_end_to_end_suspicious_meter_flow(dashboard_client: DashboardApiClient) -> None:
    """Verify full prediction-to-ticket workflow for suspicious step-down meter."""
    demo = get_demo_meter("sustained_step_down")

    # 1. Single meter prediction via Dashboard Client
    pred = dashboard_client.predict_single(
        meter_id=demo["meter_id"],
        readings=demo["readings"],
        tariff_per_kwh=0.15,
        dispatch_cost=100.0,
        decision_rule="env",
        include_explanation=True,
    )

    # Statistical checks
    p_raw = pred["prediction"]["tamper_probability"]
    p_cal = pred["prediction"]["calibrated_probability"]
    assert 0.0 <= p_raw <= 1.0
    assert 0.0 <= p_cal <= 1.0
    assert p_raw > 0.25, (
        "Sustained step-down anomaly should yield elevated tamper probability (> 4x baseline)"
    )

    # Financial checks
    fin = pred["financial"]
    r = fin["estimated_recoverable_revenue"]
    c_disp = fin["dispatch_cost"]
    env = fin["expected_net_value"]
    expected_gross = fin["expected_gross_recovery"]

    assert r >= 0.0
    assert c_disp == 100.0
    # Numerical consistency: expected_gross ~= p_cal * R (within float rounding), ENV = expected_gross - C_disp
    assert abs(expected_gross - (p_cal * r)) < 2.0
    assert abs(env - (expected_gross - c_disp)) < 0.01

    # Decision rule consistency
    decision = pred["decision"]
    if env > 0:
        assert decision["inspection_recommended"] is True

    # Explainability checks
    exp = pred.get("explanation")
    assert exp is not None
    assert len(exp["top_positive_contributors"]) > 0
    assert len(exp["detected_signatures"]) > 0

    # 2. Ticket generation
    ticket = dashboard_client.generate_ticket(
        meter_id=demo["meter_id"],
        readings=demo["readings"],
        tariff_per_kwh=0.15,
        dispatch_cost=100.0,
        decision_rule="env",
        include_explanation=True,
    )

    assert ticket["ticket_id"].startswith("TCK-")
    assert ticket["meter_id"] == demo["meter_id"]
    assert ticket["env"] == env
    assert "safety_caveat" in ticket
    assert "explanation" in ticket


def test_end_to_end_normal_meter_flow(dashboard_client: DashboardApiClient) -> None:
    """Verify normal stable meter produces low probability and no dispatch."""
    demo = get_demo_meter("normal_residential")

    pred = dashboard_client.predict_single(
        meter_id=demo["meter_id"],
        readings=demo["readings"],
        tariff_per_kwh=0.15,
        dispatch_cost=100.0,
        decision_rule="env",
        include_explanation=False,
    )

    p = pred["prediction"]["tamper_probability"]
    assert 0.0 <= p <= 1.0
    assert p < 0.40, "Normal residential meter should have low tamper probability"
    assert pred["decision"]["inspection_recommended"] is False


def test_end_to_end_high_prob_low_env_economics(dashboard_client: DashboardApiClient) -> None:
    """Verify economic dispatch breakeven: high p with tiny R yields negative ENV and no dispatch."""
    demo = get_demo_meter("high_prob_low_env")

    ticket = dashboard_client.generate_ticket(
        meter_id=demo["meter_id"],
        readings=demo["readings"],
        tariff_per_kwh=0.15,
        dispatch_cost=100.0,
        decision_rule="env",
        include_explanation=True,
    )

    # Even if anomaly is detected, total recoverable revenue cannot justify $100 crew dispatch
    assert ticket["env"] < 0, f"Expected negative ENV for lifeline meter, got {ticket['env']}"
    assert ticket["inspection_recommended"] is False, (
        "ENV policy must NOT recommend dispatch when expected gross recovery is below crew cost"
    )


def test_end_to_end_inspection_queue_query(dashboard_client: DashboardApiClient) -> None:
    """Verify prioritized queue retrieval and ENV descending ranking."""
    queue = dashboard_client.get_inspection_queue(
        max_inspections=20,
        decision_rule="env",
        min_env=0.0,
        min_probability=0.0,
        include_explanations=True,
    )

    assert "queue_size" in queue
    assert "total_net_value" in queue
    assert "tickets" in queue

    tickets = queue["tickets"]
    if len(tickets) >= 2:
        # Verify strictly descending ENV order
        envs = [t["env"] for t in tickets]
        assert envs == sorted(envs, reverse=True), "Queue tickets must be sorted by ENV descending"
