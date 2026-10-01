"""Synthetic smart-meter AMI time-series generators for testing and simulation."""

from __future__ import annotations

from datetime import date, timedelta

import polars as pl


def generate_synthetic_series(
    meter_id: str = "TEST_METER_001",
    num_days: int = 120,
    pattern: str = "normal",
    start_date: date = date(2020, 1, 1),
    tamper_label: int = 0,
    base_val: float = 10.0,
    feeder_id: str | None = None,
) -> pl.DataFrame:
    """Generate a controlled synthetic daily time series for a single meter.

    Patterns:
        - "normal": Stable consumption with day-of-week periodicity and mild noise.
        - "step_down": Baseline for 70 days, then drops to 15% of baseline (theft).
        - "zero_streak": Baseline with a 12-day streak of zero consumption.
        - "flatline": Baseline with a 15-day streak of constant identical readings.
        - "sparse": Baseline with intermittent null (missing) days.

    Args:
        meter_id: Meter identifier.
        num_days: Number of calendar days.
        pattern: Anomaly pattern type.
        start_date: Starting calendar date.
        tamper_label: Ground truth flag (0=normal, 1=tampered).
        base_val: Baseline consumption level in kWh.
        feeder_id: Optional feeder/transformer identifier.

    Returns:
        Polars DataFrame matching canonical series schema.
    """
    dates = [start_date + timedelta(days=i) for i in range(num_days)]
    values: list[float | None] = []

    for i in range(num_days):
        # Day of week variation (weekends slightly higher)
        dow = dates[i].weekday()
        dow_factor = 1.15 if dow in (5, 6) else 1.0
        val = base_val * dow_factor + ((i % 5) - 2) * 0.2

        if pattern == "step_down":
            # Tampering starts on day 70: sudden collapse
            if i >= 70:
                val = base_val * 0.15
        elif pattern == "zero_streak":
            # Zero streak between days 50 and 62
            if 50 <= i < 62:
                val = 0.0
        elif pattern == "flatline":
            # Exactly identical value between days 40 and 55
            if 40 <= i < 55:
                val = 7.77
        elif pattern == "sparse":
            # Missing days
            if i % 8 == 0:
                val = None  # type: ignore[assignment]

        values.append(val)

    data: dict[str, list] = {
        "meter_id": [meter_id] * num_days,
        "timestamp": dates,
        "consumption_kwh": values,
        "tamper_label": [tamper_label] * num_days,
        "data_quality_status": ["CLEAN"] * num_days,
    }
    if feeder_id is not None:
        data["feeder_id"] = [feeder_id] * num_days

    return pl.DataFrame(data).with_columns(
        [
            pl.col("timestamp").cast(pl.Date),
            pl.col("consumption_kwh").cast(pl.Float32),
            pl.col("tamper_label").cast(pl.Int8),
        ]
    )


def generate_synthetic_multimeter_fleet(
    num_days: int = 100,
    start_date: date = date(2020, 1, 1),
) -> pl.DataFrame:
    """Generate a fleet of synthetic meters covering multiple behavioral signatures.

    Returns:
        Combined DataFrame of 5 distinct meters with varying patterns.
    """
    dfs = [
        generate_synthetic_series(
            meter_id="METER_NORMAL",
            num_days=num_days,
            pattern="normal",
            start_date=start_date,
            tamper_label=0,
            base_val=12.0,
            feeder_id="FEEDER_A",
        ),
        generate_synthetic_series(
            meter_id="METER_STEP_DOWN",
            num_days=num_days,
            pattern="step_down",
            start_date=start_date,
            tamper_label=1,
            base_val=15.0,
            feeder_id="FEEDER_A",
        ),
        generate_synthetic_series(
            meter_id="METER_ZERO_STREAK",
            num_days=num_days,
            pattern="zero_streak",
            start_date=start_date,
            tamper_label=1,
            base_val=10.0,
            feeder_id="FEEDER_A",
        ),
        generate_synthetic_series(
            meter_id="METER_FLATLINE",
            num_days=num_days,
            pattern="flatline",
            start_date=start_date,
            tamper_label=1,
            base_val=8.0,
            feeder_id="FEEDER_B",
        ),
        generate_synthetic_series(
            meter_id="METER_SPARSE",
            num_days=num_days,
            pattern="sparse",
            start_date=start_date,
            tamper_label=0,
            base_val=14.0,
            feeder_id="FEEDER_B",
        ),
    ]
    return pl.concat(dfs).sort(["meter_id", "timestamp"])
