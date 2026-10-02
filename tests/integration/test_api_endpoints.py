"""Integration tests for Grid-Guard FastAPI HTTP endpoints."""

from collections.abc import Generator
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from grid_guard.api.main import create_app


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """TestClient fixture with app lifecycle initialized."""
    app = create_app()
    with TestClient(app) as tc:
        yield tc


def test_endpoint_health(client: TestClient) -> None:
    """Test liveness probe endpoint."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "grid-guard-api"


def test_endpoint_ready(client: TestClient) -> None:
    """Test readiness probe endpoint."""
    res = client.get("/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["model_loaded"] is True
    assert data["explainer_loaded"] is True
    assert data["feature_count"] == 60


def test_endpoint_model_metadata(client: TestClient) -> None:
    """Test model metadata endpoint."""
    res = client.get("/api/v1/metadata/model")
    assert res.status_code == 200
    data = res.json()
    assert data["model_version"] == "phase6_cost_sensitive_v1"
    assert data["feature_count"] == 60
    assert "LightGBM" in data["model_type"]


def test_endpoint_config_metadata(client: TestClient) -> None:
    """Test public configuration endpoint."""
    res = client.get("/api/v1/metadata/config")
    assert res.status_code == 200
    data = res.json()
    assert "limits" in data
    assert data["limits"]["min_readings_per_meter"] == 14
    assert "env" in data["supported_decision_rules"]


def test_endpoint_predict_single_normal(client: TestClient) -> None:
    """Test single meter prediction for normal consumption."""
    readings = [
        {"timestamp": str(date(2016, 8, 1) + timedelta(days=i)), "consumption_kwh": 10.0 + (i % 3)}
        for i in range(60)
    ]
    payload = {
        "meter_id": "API_TEST_NORMAL_01",
        "readings": readings,
        "include_explanation": True,
    }
    res = client.post("/api/v1/predict", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["meter_id"] == "API_TEST_NORMAL_01"
    assert 0.0 <= data["prediction"]["tamper_probability"] <= 1.0
    assert data["prediction"]["tamper_probability"] < 0.35
    assert data["explanation"] is not None
    assert "X-Request-ID" in res.headers
    assert "X-Response-Time-Ms" in res.headers


def test_endpoint_predict_single_suspicious(client: TestClient) -> None:
    """Test single meter prediction for suspicious step-down pattern."""
    readings = []
    for i in range(90):
        # 60 days of 25 kWh, then acute drop to 1 kWh for 30 days
        c = 25.0 if i < 60 else 1.0
        readings.append(
            {"timestamp": str(date(2016, 8, 1) + timedelta(days=i)), "consumption_kwh": c}
        )

    payload = {
        "meter_id": "API_TEST_SUSPICIOUS_01",
        "readings": readings,
        "include_explanation": True,
    }
    res = client.post("/api/v1/predict", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["meter_id"] == "API_TEST_SUSPICIOUS_01"
    assert data["prediction"]["tamper_probability"] > 0.15
    assert data["financial"]["expected_net_value"] > 0.0
    assert data["decision"]["inspection_recommended"] is True

    # Verify detected signatures
    assert data["explanation"] is not None
    sig_types = [s["signature_type"] for s in data["explanation"]["detected_signatures"]]
    assert "sustained_step_down" in sig_types


def test_endpoint_predict_without_explanation(client: TestClient) -> None:
    """Test prediction endpoint with include_explanation=False."""
    readings = [
        {"timestamp": str(date(2016, 8, 1) + timedelta(days=i)), "consumption_kwh": 10.0}
        for i in range(30)
    ]
    payload = {
        "meter_id": "API_FAST_TEST",
        "readings": readings,
        "include_explanation": False,
    }
    res = client.post("/api/v1/predict", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["explanation"] is None


def test_endpoint_predict_insufficient_readings(client: TestClient) -> None:
    """Ensure HTTP 400 when fewer than 14 daily readings are supplied."""
    readings = [
        {"timestamp": str(date(2016, 8, 1) + timedelta(days=i)), "consumption_kwh": 10.0}
        for i in range(5)  # Only 5 readings
    ]
    payload = {"meter_id": "API_SHORT", "readings": readings}
    res = client.post("/api/v1/predict", json=payload)
    assert res.status_code == 400
    data = res.json()
    assert "Insufficient meter history" in data["message"]


def test_endpoint_predict_duplicate_timestamps(client: TestClient) -> None:
    """Ensure HTTP 422 when duplicate timestamps are present in payload."""
    readings = [
        {"timestamp": "2016-10-01", "consumption_kwh": 10.0},
        {"timestamp": "2016-10-01", "consumption_kwh": 12.0},
    ]
    payload = {"meter_id": "API_DUP", "readings": readings}
    res = client.post("/api/v1/predict", json=payload)
    assert res.status_code == 422


def test_endpoint_predict_negative_consumption(client: TestClient) -> None:
    """Ensure HTTP 422 when negative consumption is supplied."""
    readings = [
        {"timestamp": "2016-10-01", "consumption_kwh": -5.0},
    ]
    payload = {"meter_id": "API_NEG", "readings": readings}
    res = client.post("/api/v1/predict", json=payload)
    assert res.status_code == 422


def test_endpoint_predict_batch_success(client: TestClient) -> None:
    """Test multi-meter batch prediction."""
    readings1 = [
        {"timestamp": str(date(2016, 8, 1) + timedelta(days=i)), "consumption_kwh": 10.0 + (i % 2)}
        for i in range(30)
    ]
    readings2 = [
        {"timestamp": str(date(2016, 8, 1) + timedelta(days=i)), "consumption_kwh": 20.0 + (i % 3)}
        for i in range(30)
    ]
    payload = {
        "batch_id": "TEST_BATCH_OK",
        "meters": [
            {"meter_id": "BATCH_MTR_1", "readings": readings1},
            {"meter_id": "BATCH_MTR_2", "readings": readings2},
        ],
        "include_explanation": False,
    }
    res = client.post("/api/v1/predict/batch", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total_items"] == 2
    assert data["successful_items"] == 2
    assert data["failed_items"] == 0
    assert len(data["results"]) == 2


def test_endpoint_predict_batch_partial_failure(client: TestClient) -> None:
    """Test batch processing with one valid meter and one invalid meter (insufficient history)."""
    valid_readings = [
        {"timestamp": str(date(2016, 8, 1) + timedelta(days=i)), "consumption_kwh": 10.0}
        for i in range(30)
    ]
    short_readings = [
        {"timestamp": str(date(2016, 8, 1) + timedelta(days=i)), "consumption_kwh": 10.0}
        for i in range(3)  # Insufficient
    ]
    payload = {
        "batch_id": "TEST_BATCH_PARTIAL",
        "meters": [
            {"meter_id": "VALID_MTR", "readings": valid_readings},
            {"meter_id": "INVALID_SHORT_MTR", "readings": short_readings},
        ],
        "include_explanation": False,
    }
    res = client.post("/api/v1/predict/batch", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total_items"] == 2
    assert data["successful_items"] == 1
    assert data["failed_items"] == 1
    assert data["errors"][0]["meter_id"] == "INVALID_SHORT_MTR"


def test_endpoint_inspection_ticket(client: TestClient) -> None:
    """Test inspection work order ticket generation endpoint."""
    readings = [
        {"timestamp": str(date(2016, 8, 1) + timedelta(days=i)), "consumption_kwh": 12.0}
        for i in range(60)
    ]
    payload = {
        "meter_id": "API_TICKET_MTR",
        "readings": readings,
    }
    res = client.post("/api/v1/inspection/ticket", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["ticket_id"].startswith("TCK-")
    assert data["meter_id"] == "API_TICKET_MTR"
    assert data["dispatch_cost"] == 500.0
    assert data["explanation"] is not None


def test_endpoint_inspection_queue(client: TestClient) -> None:
    """Test inspection queue ranking query endpoint."""
    payload = {
        "max_inspections": 10,
        "min_env": 0.0,
        "include_explanations": True,
    }
    res = client.post("/api/v1/inspection/queue", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["queue_size"] <= 10
    assert data["total_net_value"] > 0.0
    assert len(data["tickets"]) == data["queue_size"]
    assert data["tickets"][0]["priority_rank"] == 1


def test_endpoint_unready_service() -> None:
    """Ensure HTTP 503 is returned when the inference service is unavailable."""
    app = create_app()

    with TestClient(app) as unready_client:
        # Force service into None state after lifespan startup
        app.state.inference_service = None

        ready_res = unready_client.get("/ready")
        assert ready_res.status_code == 503

        readings = [
            {"timestamp": str(date(2016, 8, 1) + timedelta(days=i)), "consumption_kwh": 10.0}
            for i in range(30)
        ]
        pred_res = unready_client.post(
            "/api/v1/predict",
            json={"meter_id": "FAIL_MTR", "readings": readings},
        )
        assert pred_res.status_code == 503
