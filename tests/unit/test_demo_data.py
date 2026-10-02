"""Unit tests for synthetic demo meter datasets."""

from __future__ import annotations

import datetime

from grid_guard.dashboard.demo_data.synthetic_meters import (
    DEMO_METERS,
    get_demo_meter,
    list_demo_meters,
)


def test_demo_meters_contain_all_archetypes() -> None:
    """Verify all 5 required demonstration archetypes are present."""
    required_keys = [
        "normal_residential",
        "sustained_step_down",
        "flatline_invariance",
        "high_value_commercial",
        "high_prob_low_env",
    ]
    for key in required_keys:
        assert key in DEMO_METERS, f"Missing demo archetype: {key}"
        demo = get_demo_meter(key)
        assert demo["key"] == key
        assert demo["meter_id"].startswith("DEMO_")
        assert len(demo["readings"]) >= 90


def test_demo_readings_integrity() -> None:
    """Verify timestamps and consumption values for all demo datasets."""
    for demo in list_demo_meters():
        readings = demo["readings"]
        assert len(readings) >= 90

        timestamps = [r["timestamp"] for r in readings]
        parsed_dates = [datetime.date.fromisoformat(ts) for ts in timestamps]

        # Verify sorted ascending dates
        assert parsed_dates == sorted(parsed_dates), f"Dates not chronological in {demo['key']}"

        # Verify non-negative consumption
        for r in readings:
            assert isinstance(r["consumption_kwh"], (int, float))
            assert r["consumption_kwh"] >= 0.0


def test_demo_flatline_has_zero_variance_in_anomaly_window() -> None:
    """Verify flatline anomaly archetype exhibits perfect constant readings in recent window."""
    flatline = get_demo_meter("flatline_invariance")
    recent_readings = [r["consumption_kwh"] for r in flatline["readings"][-30:]]
    assert len(set(recent_readings)) == 1, (
        "Flatline demo readings must have zero variance in recent period"
    )
