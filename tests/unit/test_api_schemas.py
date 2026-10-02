"""Unit tests for FastAPI Pydantic request and response schemas."""

import pytest
from pydantic import ValidationError

from grid_guard.api.schemas.prediction import (
    BatchPredictionRequest,
    MeterReading,
    SingleMeterPredictionRequest,
)


def test_meter_reading_valid() -> None:
    """Test valid meter reading construction."""
    reading = MeterReading(timestamp="2016-10-30", consumption_kwh=15.42)
    assert reading.timestamp == "2016-10-30"
    assert reading.consumption_kwh == 15.42


def test_meter_reading_negative_consumption_rejected() -> None:
    """Ensure negative consumption values are rejected by schema validator."""
    with pytest.raises(ValidationError, match="consumption_kwh must be non-negative"):
        MeterReading(timestamp="2016-10-30", consumption_kwh=-1.5)


def test_meter_reading_nan_rejected() -> None:
    """Ensure NaN and Infinite consumption values are rejected."""
    with pytest.raises(ValidationError, match="cannot be NaN or Infinite"):
        MeterReading(timestamp="2016-10-30", consumption_kwh=float("nan"))

    with pytest.raises(ValidationError, match="cannot be NaN or Infinite"):
        MeterReading(timestamp="2016-10-30", consumption_kwh=float("inf"))


def test_meter_reading_iso_timestamp_normalized() -> None:
    """Ensure ISO timestamps with times are normalized to YYYY-MM-DD."""
    reading = MeterReading(timestamp="2016-10-30T14:30:00Z", consumption_kwh=10.0)
    assert reading.timestamp == "2016-10-30"


def test_single_meter_prediction_request_valid() -> None:
    """Test valid single meter prediction request."""
    readings = [
        MeterReading(timestamp=f"2016-10-{i:02d}", consumption_kwh=10.0 + i) for i in range(1, 16)
    ]
    req = SingleMeterPredictionRequest(
        meter_id="MTR_TEST_01",
        readings=readings,
        tariff=7.5,
        decision_rule="env",
        include_explanation=True,
    )
    assert req.meter_id == "MTR_TEST_01"
    assert len(req.readings) == 15
    assert req.tariff == 7.5


def test_single_meter_prediction_request_empty_readings() -> None:
    """Ensure empty readings list is rejected."""
    with pytest.raises(ValidationError, match="readings list cannot be empty"):
        SingleMeterPredictionRequest(
            meter_id="MTR_TEST_01",
            readings=[],
        )


def test_single_meter_prediction_request_duplicate_timestamps() -> None:
    """Ensure duplicate timestamps in readings are rejected."""
    readings = [
        MeterReading(timestamp="2016-10-01", consumption_kwh=10.0),
        MeterReading(timestamp="2016-10-01", consumption_kwh=12.0),
    ]
    with pytest.raises(ValidationError, match="Duplicate reading detected"):
        SingleMeterPredictionRequest(
            meter_id="MTR_TEST_01",
            readings=readings,
        )


def test_single_meter_prediction_request_invalid_decision_rule() -> None:
    """Ensure unsupported decision rules are rejected."""
    readings = [
        MeterReading(timestamp=f"2016-10-{i:02d}", consumption_kwh=10.0) for i in range(1, 15)
    ]
    with pytest.raises(ValidationError, match="Invalid decision_rule"):
        SingleMeterPredictionRequest(
            meter_id="MTR_TEST_01",
            readings=readings,
            decision_rule="unsupported_quantum_rule",
        )


def test_batch_prediction_request_valid() -> None:
    """Test batch prediction request validation."""
    readings = [
        MeterReading(timestamp=f"2016-10-{i:02d}", consumption_kwh=10.0) for i in range(1, 15)
    ]
    req1 = SingleMeterPredictionRequest(meter_id="MTR_01", readings=readings)
    req2 = SingleMeterPredictionRequest(meter_id="MTR_02", readings=readings)

    batch_req = BatchPredictionRequest(
        meters=[req1, req2],
        batch_id="TEST-BATCH-001",
        include_explanation=False,
    )
    assert len(batch_req.meters) == 2
    assert batch_req.batch_id == "TEST-BATCH-001"
