"""Unit tests for synthetic economic scenarios proving that financial exposure alters decisions."""

import polars as pl

from grid_guard.config.decision import DecisionRule, DecisionSettings
from grid_guard.decision.prioritization import InspectionPrioritizer


def test_synthetic_scenario_residential_vs_commercial() -> None:
    """Prove that Grid-Guard ENV prioritizes commercial diversion over high-probability residential anomaly.

    Scenario:
        Meter A (Low-value Residential): p = 0.85 (High prob), R = $50.00 (Tiny volume)
            - Fixed 0.5 decision: INSPECT (p >= 0.5) -> Loses money! Realized gain = $50 - $100 = -$50
            - ENV decision: DO NOT INSPECT (ENV = 0.85 * 50 - 100 = -$57.50 <= 0)

        Meter B (High-value Commercial): p = 0.25 (Moderate prob), R = $5,000.00 (Large volume)
            - Fixed 0.5 decision: DO NOT INSPECT (p < 0.5) -> Misses $5,000 theft!
            - ENV decision: INSPECT (ENV = 0.25 * 5000 - 100 = +$1,150.00 > 0)
    """
    df = pl.DataFrame(
        {
            "meter_id": ["RESIDENTIAL_A", "COMMERCIAL_B"],
            "timestamp": ["2016-10-01", "2016-10-01"],
            "predicted_prob": [0.85, 0.25],
            "estimated_leakage_cost": [50.0, 5000.0],
            "actual_tamper_label": [1, 1],
        }
    )

    # 1. Evaluate with Fixed 0.5 Rule
    cfg_fixed = DecisionSettings(decision_rule=DecisionRule.FIXED_THRESHOLD, fixed_threshold=0.5)
    p_fixed = InspectionPrioritizer(settings=cfg_fixed)
    tickets_fixed = p_fixed.prioritize(df)

    res_fixed = tickets_fixed.filter(pl.col("meter_id") == "RESIDENTIAL_A")[
        "inspection_recommended"
    ][0]
    com_fixed = tickets_fixed.filter(pl.col("meter_id") == "COMMERCIAL_B")[
        "inspection_recommended"
    ][0]
    assert res_fixed is True, "Fixed 0.5 naively inspects residential"
    assert com_fixed is False, "Fixed 0.5 mistakenly skips commercial"

    # 2. Evaluate with Dynamic ENV Rule
    cfg_env = DecisionSettings(decision_rule=DecisionRule.ENV, dispatch_cost=100.0)
    p_env = InspectionPrioritizer(settings=cfg_env)
    tickets_env = p_env.prioritize(df)

    res_env = tickets_env.filter(pl.col("meter_id") == "RESIDENTIAL_A")["inspection_recommended"][0]
    com_env = tickets_env.filter(pl.col("meter_id") == "COMMERCIAL_B")["inspection_recommended"][0]
    assert res_env is False, "Dynamic ENV correctly rejects loss-making residential inspection"
    assert com_env is True, "Dynamic ENV correctly recommends profitable commercial inspection"

    # Top ticket in ENV queue must be Commercial B
    top_meter = tickets_env["meter_id"][0]
    assert top_meter == "COMMERCIAL_B"
    assert tickets_env["priority_rank"][0] == 1


def test_synthetic_scenario_dispatch_cost_sensitivity() -> None:
    """Verify that varying dispatch cost logically contracts/expands the inspection queue."""
    df = pl.DataFrame(
        {
            "meter_id": ["M1", "M2", "M3"],
            "timestamp": ["2016-10-01", "2016-10-01", "2016-10-01"],
            "predicted_prob": [0.5, 0.5, 0.5],
            "estimated_leakage_cost": [100.0, 300.0, 600.0],  # Exp recovery: 50, 150, 300
        }
    )

    # Low dispatch cost ($40): M1 (50>40), M2 (150>40), M3 (300>40) -> All 3 viable!
    cfg_low = DecisionSettings(decision_rule=DecisionRule.ENV, dispatch_cost=40.0)
    p_low = InspectionPrioritizer(settings=cfg_low)
    t_low = p_low.prioritize(df)
    assert int(t_low["inspection_recommended"].sum()) == 3

    # Medium dispatch cost ($100): M1 (50<100, reject), M2 (150>100, accept), M3 (300>100, accept) -> 2 viable
    cfg_med = DecisionSettings(decision_rule=DecisionRule.ENV, dispatch_cost=100.0)
    p_med = InspectionPrioritizer(settings=cfg_med)
    t_med = p_med.prioritize(df)
    assert int(t_med["inspection_recommended"].sum()) == 2

    # High dispatch cost ($200): M1 (50<200), M2 (150<200), M3 (300>200) -> Only 1 viable!
    cfg_high = DecisionSettings(decision_rule=DecisionRule.ENV, dispatch_cost=200.0)
    p_high = InspectionPrioritizer(settings=cfg_high)
    t_high = p_high.prioritize(df)
    assert int(t_high["inspection_recommended"].sum()) == 1
    assert t_high["meter_id"][0] == "M3"
