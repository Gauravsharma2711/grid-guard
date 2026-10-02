"""Unit tests for InferenceService orchestration logic."""

from datetime import date, timedelta

import pytest

from grid_guard.api.schemas.prediction import MeterReading, SingleMeterPredictionRequest
from grid_guard.api.services.inference import InferenceService


@pytest.fixture(scope="module")
def inference_service() -> InferenceService:
    """Fixture providing initialized InferenceService."""
    return InferenceService()


def test_service_initialization(inference_service: InferenceService) -> None:
    """Verify service is initialized and reports ready."""
    assert inference_service.is_ready
    assert len(inference_service.feature_names) == 60
    assert inference_service.booster is not None
    assert inference_service.explainer is not None


def test_service_metadata(inference_service: InferenceService) -> None:
    """Verify metadata introspection output."""
    meta = inference_service.get_metadata()
    assert meta.model_version == "phase6_cost_sensitive_v1"
    assert meta.feature_count == 60
    assert meta.base_log_odds < 0.0  # Champion base value is ~ -2.5928
    assert 0.0 < meta.base_probability < 0.15


def test_service_insufficient_history(inference_service: InferenceService) -> None:
    """Ensure service raises ValueError when fewer than 14 daily readings are supplied."""
    readings = [
        MeterReading(timestamp=f"2016-10-{i:02d}", consumption_kwh=10.0)
        for i in range(1, 10)  # Only 9 readings
    ]
    req = SingleMeterPredictionRequest(meter_id="SHORT_MTR", readings=readings)
    with pytest.raises(ValueError, match="Insufficient meter history"):
        inference_service.predict_single(req)


def test_service_predict_single_normal_meter(inference_service: InferenceService) -> None:
    """Test full inference pipeline on a normal stable consumer."""
    readings = [
        MeterReading(
            timestamp=str(date(2016, 8, 1) + timedelta(days=i)),
            consumption_kwh=15.0 + (i % 4),
        )
        for i in range(90)
    ]
    req = SingleMeterPredictionRequest(
        meter_id="NORMAL_MTR_TEST",
        readings=readings,
        include_explanation=True,
    )
    res = inference_service.predict_single(req)

    assert res.meter_id == "NORMAL_MTR_TEST"
    assert res.data_quality.total_readings == 90
    assert res.data_quality.status == "good"
    assert 0.0 <= res.prediction.tamper_probability <= 1.0
    assert res.prediction.tamper_probability < 0.35  # Stable meter should have low risk
    assert res.financial.dispatch_cost == 500.0

    # Verify ENV mathematical consistency: env = p * R - dispatch
    expected_env = round(
        res.prediction.calibrated_probability * res.financial.estimated_recoverable_revenue
        - res.financial.dispatch_cost,
        2,
    )
    assert abs(res.financial.expected_net_value - expected_env) < 0.1

    # Verify explanation components
    assert res.explanation is not None
    assert len(res.explanation.summary) > 10
    assert len(res.explanation.detailed_explanation) > 50
    assert "field" in res.explanation.safety_caveat.lower()


def test_service_predict_single_without_explanation(inference_service: InferenceService) -> None:
    """Test that setting include_explanation=False skips expensive SHAP computation."""
    readings = [
        MeterReading(
            timestamp=str(date(2016, 8, 1) + timedelta(days=i)),
            consumption_kwh=15.0,
        )
        for i in range(30)
    ]
    req = SingleMeterPredictionRequest(
        meter_id="FAST_MTR_TEST",
        readings=readings,
        include_explanation=False,
    )
    res = inference_service.predict_single(req)
    assert res.explanation is None
    assert res.prediction.tamper_probability >= 0.0
