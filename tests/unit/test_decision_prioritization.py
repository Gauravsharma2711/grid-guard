"""Unit tests for prioritization engine, period aggregation, capacity dispatch, and deterministic ticket IDs."""

import polars as pl

from grid_guard.config.decision import (
    AggregationPeriod,
    CapacityPolicy,
    DecisionRule,
    DecisionSettings,
    RankingStrategy,
)
from grid_guard.decision.capacity import CapacityDispatcher
from grid_guard.decision.prioritization import InspectionPrioritizer
from grid_guard.decision.tickets import generate_deterministic_ticket_id


def test_deterministic_ticket_id() -> None:
    """Verify ticket IDs are deterministic and reproducible across calls."""
    id1 = generate_deterministic_ticket_id("METER_123", "2016-10-30")
    id2 = generate_deterministic_ticket_id("METER_123", "2016-10-30")
    id_other_meter = generate_deterministic_ticket_id("METER_999", "2016-10-30")
    id_other_period = generate_deterministic_ticket_id("METER_123", "2016-09-30")

    assert id1 == id2
    assert id1.startswith("TCK-2016-10-30-")
    assert id1 != id_other_meter
    assert id1 != id_other_period


def test_aggregation_period_latest_snapshot() -> None:
    """Verify multi-snapshot records collapse to strictly ONE ticket per meter on latest timestamp."""
    # 2 meters with 3 timestamps each
    data = {
        "meter_id": ["M1", "M1", "M1", "M2", "M2", "M2"],
        "timestamp": [
            "2016-08-01",
            "2016-09-01",
            "2016-10-01",
            "2016-08-01",
            "2016-09-01",
            "2016-10-01",
        ],
        "predicted_prob": [0.1, 0.4, 0.8, 0.2, 0.5, 0.3],
        "estimated_leakage_cost": [100.0, 200.0, 800.0, 50.0, 150.0, 300.0],
    }
    df = pl.DataFrame(data)

    settings = DecisionSettings(
        aggregation_period=AggregationPeriod.LATEST_SNAPSHOT,
        decision_rule=DecisionRule.ENV,
    )
    prioritizer = InspectionPrioritizer(settings=settings)
    df_tickets = prioritizer.prioritize(df)

    # Must collapse to exactly 2 rows (one for M1, one for M2)
    assert len(df_tickets) == 2
    assert set(df_tickets["meter_id"].to_list()) == {"M1", "M2"}
    # Verify latest timestamp '2016-10-01' was chosen
    assert set(df_tickets["evaluation_period"].to_list()) == {"2016-10-01"}


def test_ranking_strategy_env_descending() -> None:
    """Verify tickets are ordered descending by ENV with deterministic tie-breaking."""
    data = {
        "meter_id": ["M_LOW", "M_HIGH", "M_MED"],
        "timestamp": ["2016-10-01", "2016-10-01", "2016-10-01"],
        "predicted_prob": [0.9, 0.5, 0.6],
        "estimated_leakage_cost": [
            50.0,
            2000.0,
            500.0,
        ],  # ENVs: 0.9*50-100 = -55, 0.5*2000-100 = +900, 0.6*500-100 = +200
    }
    df = pl.DataFrame(data)

    settings = DecisionSettings(
        ranking_strategy=RankingStrategy.ENV_DESCENDING,
        decision_rule=DecisionRule.ENV,
        capacity_policy=CapacityPolicy.FILL_QUOTA,  # include all for ranking check
    )
    prioritizer = InspectionPrioritizer(settings=settings)
    df_tickets = prioritizer.prioritize(df, filter_dispatched_only=True)

    assert df_tickets["meter_id"].to_list() == [
        "M_HIGH",
        "M_MED",
    ]  # M_LOW is recommended=False because ENV < 0
    assert df_tickets["priority_rank"].to_list() == [1, 2]


def test_capacity_policy_strictly_positive_env() -> None:
    """Verify that strictly positive ENV policy never dispatches negative ENV meters."""
    df_ranked = pl.DataFrame(
        {
            "meter_id": ["M1", "M2", "M3"],
            "inspection_recommended": [True, True, True],
            "env": [500.0, 50.0, -20.0],
        }
    )

    # Capacity = 10 (ample spare quota)
    df_disp = CapacityDispatcher.apply_capacity(
        df_ranked=df_ranked,
        max_inspections=10,
        policy=CapacityPolicy.STRICTLY_POSITIVE_ENV,
        filter_dispatched_only=True,
    )

    # M3 with negative ENV must be excluded despite spare capacity!
    assert len(df_disp) == 2
    assert df_disp["meter_id"].to_list() == ["M1", "M2"]
    assert df_disp["priority_rank"].to_list() == [1, 2]


def test_capacity_policy_fill_quota() -> None:
    """Verify that fill_quota policy includes recommended meters up to capacity cap."""
    df_ranked = pl.DataFrame(
        {
            "meter_id": ["M1", "M2", "M3"],
            "inspection_recommended": [True, True, True],
            "env": [500.0, -10.0, -50.0],
        }
    )

    df_disp = CapacityDispatcher.apply_capacity(
        df_ranked=df_ranked,
        max_inspections=2,
        policy=CapacityPolicy.FILL_QUOTA,
        filter_dispatched_only=True,
    )

    assert len(df_disp) == 2
    assert df_disp["meter_id"].to_list() == ["M1", "M2"]
    assert df_disp["priority_rank"].to_list() == [1, 2]
