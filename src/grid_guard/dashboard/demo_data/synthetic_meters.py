"""Synthetic, deterministic smart-meter time series for Grid-Guard demonstration.

Clearly labeled DEMO DATA. Contains zero real customer information.
Demonstrates 5 core operational archetypes:
1. Normal Stable Residential Meter
2. Sustained Step-Down Anomaly
3. Flatline Invariance Pattern
4. High-Value Commercial Customer Tamper
5. High-Probability but Low-ENV Lifeline Meter (Economics of Dispatch)
"""

from __future__ import annotations

import datetime
from typing import Any


def _generate_dates(start_str: str = "2016-08-01", num_days: int = 91) -> list[str]:
    start = datetime.date.fromisoformat(start_str)
    return [(start + datetime.timedelta(days=i)).isoformat() for i in range(num_days)]


def build_normal_residential() -> dict[str, Any]:
    """Archetype 1: Healthy residential meter with regular weekly variations and no tampering."""
    dates = _generate_dates()
    readings = []
    base_values = [12.0, 12.8, 13.5, 14.1, 12.5, 15.2, 14.8]  # weekly cadence
    for i, d in enumerate(dates):
        kwh = base_values[i % 7] + (0.2 * (i % 3) - 0.1)
        readings.append({"timestamp": d, "consumption_kwh": round(kwh, 2)})

    return {
        "key": "normal_residential",
        "name": "Normal Residential Meter",
        "meter_id": "DEMO_NORMAL_RESIDENTIAL_001",
        "description": "Stable residential customer with consistent consumption (~13 kWh/day) and healthy variance.",
        "customer_type": "residential",
        "expected_behavior": "Low probability (< 0.15), negative ENV, inspection NOT recommended.",
        "readings": readings,
    }


def build_sustained_step_down() -> dict[str, Any]:
    """Archetype 2: Suspicious sustained step-down reduction in recent evaluation window."""
    dates = _generate_dates()
    readings = []
    for i, d in enumerate(dates):
        if i < 60:
            kwh = 28.5 + 1.5 * (i % 5 - 2)
        else:
            kwh = 1.2 + 0.3 * (i % 3 - 1)  # sharp drop from ~28.5 to ~1.2
        readings.append({"timestamp": d, "consumption_kwh": round(kwh, 2)})

    return {
        "key": "sustained_step_down",
        "name": "Sustained Step-Down Anomaly",
        "meter_id": "DEMO_SUSTAINED_STEP_DOWN_002",
        "description": "Baseline consumption (~28 kWh/day) drops precipitously to ~1.2 kWh/day across the last 30 days.",
        "customer_type": "residential",
        "expected_behavior": "Significantly elevated probability (> 4x baseline), positive ENV (+$5,000+), inspection recommended.",
        "readings": readings,
    }


def build_flatline_invariance() -> dict[str, Any]:
    """Archetype 3: Meter reading freezes at constant unvarying consumption (mechanical/bypass stop)."""
    dates = _generate_dates()
    readings = []
    for i, d in enumerate(dates):
        if i < 60:
            kwh = 14.0 + 1.5 * (i % 4 - 1.5)
        else:
            kwh = 1.00  # perfectly invariant flatline
        readings.append({"timestamp": d, "consumption_kwh": round(kwh, 2)})

    return {
        "key": "flatline_invariance",
        "name": "Flatline Pattern Anomaly",
        "meter_id": "DEMO_FLATLINE_INVARIANCE_003",
        "description": "Normal baseline usage followed by constant 1.00 kWh/day zero-variance flatline.",
        "customer_type": "commercial",
        "expected_behavior": "High probability, flatline signature detected, inspection recommended.",
        "readings": readings,
    }


def build_high_value_commercial() -> dict[str, Any]:
    """Archetype 4: High-consumption commercial account with massive financial recovery potential."""
    dates = _generate_dates()
    readings = []
    for i, d in enumerate(dates):
        if i < 60:
            kwh = 240.0 + 15.0 * (i % 7 - 3)
        else:
            kwh = 42.0 + 4.0 * (i % 5 - 2)
        readings.append({"timestamp": d, "consumption_kwh": round(kwh, 2)})

    return {
        "key": "high_value_commercial",
        "name": "High-Value Commercial Account",
        "meter_id": "DEMO_HIGH_VALUE_COMMERCIAL_004",
        "description": "Commercial customer (~240 kWh/day) exhibiting ~82% drop. Huge financial leakage.",
        "customer_type": "commercial",
        "expected_behavior": "Very high recoverable revenue ($3,000+), top ENV rank, immediate priority inspection ticket.",
        "readings": readings,
    }


def build_high_prob_low_env() -> dict[str, Any]:
    """Archetype 5: Low-usage lifeline customer with high tampering probability but negative ENV.

    Demonstrates why Grid-Guard's ENV rule outperforms naive thresholding:
    Even if p=0.85, recoverable revenue is only ~$12. Dispatching a $100 crew costs ~$89 in net loss!
    """
    dates = _generate_dates()
    readings = []
    for i, d in enumerate(dates):
        if i < 60:
            kwh = 0.25 + 0.03 * (i % 3 - 1)
        else:
            kwh = 0.03 + 0.01 * (i % 2)
        readings.append({"timestamp": d, "consumption_kwh": round(kwh, 3)})

    return {
        "key": "high_prob_low_env",
        "name": "High Risk / Low Net Value (Lifeline)",
        "meter_id": "DEMO_LIFELINE_LOW_ENV_005",
        "description": "Very low baseline (~0.25 kWh/day) collapsing to 0.03 kWh/day. Model detects anomaly, but financial recovery (~$12) cannot justify $100 crew dispatch cost.",
        "customer_type": "lifeline_rural",
        "expected_behavior": "High probability, but ENV < 0. Inspection NOT recommended under ENV policy, preventing $100 wasted crew dispatch.",
        "readings": readings,
    }


DEMO_METERS: dict[str, dict[str, Any]] = {
    "normal_residential": build_normal_residential(),
    "sustained_step_down": build_sustained_step_down(),
    "flatline_invariance": build_flatline_invariance(),
    "high_value_commercial": build_high_value_commercial(),
    "high_prob_low_env": build_high_prob_low_env(),
}


def get_demo_meter(key: str) -> dict[str, Any]:
    """Retrieve demo meter payload by key."""
    if key not in DEMO_METERS:
        raise KeyError(f"Unknown demo meter '{key}'. Available: {list(DEMO_METERS.keys())}")
    return DEMO_METERS[key]


def list_demo_meters() -> list[dict[str, Any]]:
    """List all available demo scenarios."""
    return list(DEMO_METERS.values())
