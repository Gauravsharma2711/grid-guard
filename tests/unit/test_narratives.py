"""Unit tests for deterministic narrative generation and language safety auditing."""

import pytest

from grid_guard.explainability.narratives import (
    STANDARD_SAFETY_DISCLAIMER,
    NarrativeGenerator,
    validate_narrative_safety,
)
from grid_guard.explainability.schemas import (
    FeatureContribution,
    TamperingSignature,
    TemporalEvidence,
)


def test_narrative_safety_audit() -> None:
    """Verify that validate_narrative_safety passes clean text and rejects forbidden words."""
    # Clean text
    clean_text = (
        "Model prediction is an anomaly risk assessment consistent with sustained "
        "consumption drop. Field verification is recommended."
    )
    assert validate_narrative_safety(clean_text) is True

    # Forbidden word 1: bypass resistor
    with pytest.raises(ValueError, match="unsupported physical claim"):
        validate_narrative_safety("Inspection revealed a bypass resistor on the meter.")

    # Forbidden word 2: magnet
    with pytest.raises(ValueError, match="unsupported physical claim"):
        validate_narrative_safety("Customer used a magnet to distort magnetic field.")

    # Forbidden word 3: stealing electricity
    with pytest.raises(ValueError, match="unsupported physical claim"):
        validate_narrative_safety("Evidence proves the consumer is stealing electricity.")


def test_short_narrative_generation() -> None:
    """Test short explanation generation for inspection ticket cards."""
    pos_feats = [
        FeatureContribution(
            feature_name="ratio_14d_60d",
            display_name="Recent vs. Historical Consumption Ratio",
            category="Consumption Collapse",
            feature_value=0.35,
            baseline_value=12.0,
            shap_value=1.45,
            contribution_direction="positive",
            rank=1,
            description="Ratio of recent 14d to 60d baseline",
        ),
        FeatureContribution(
            feature_name="rolling_std_60d",
            display_name="60-Day Historical Volatility",
            category="Historical Baseline",
            feature_value=5.2,
            baseline_value=2.1,
            shap_value=0.85,
            contribution_direction="positive",
            rank=2,
            description="Historical variance",
        ),
    ]
    sigs = [
        TamperingSignature(
            signature_type="sustained_step_down",
            detected=True,
            magnitude=0.65,
            duration_days=18,
            severity="high",
            description="Sustained reduction of 65.0% below historical baseline.",
        )
    ]
    fin_ctx = {"env": 5869.04, "estimated_recoverable_revenue": 7054.32}

    narrative = NarrativeGenerator.generate_short_explanation(
        calibrated_prob=0.985,
        top_positive_features=pos_feats,
        detected_signatures=sigs,
        financial_context=fin_ctx,
    )

    assert "98.5% probability" in narrative
    assert "$5,869.04" in narrative
    assert "sustained consumption drop of 65% below baseline" in narrative.lower()
    assert "Field inspection recommended" in narrative
    # Must pass safety audit
    assert validate_narrative_safety(narrative) is True


def test_detailed_narrative_generation() -> None:
    """Test detailed technical explanation report generation."""
    pos_feats = [
        FeatureContribution(
            feature_name="sustained_drop_magnitude",
            display_name="Estimated Consumption Collapse Magnitude",
            category="Consumption Collapse",
            feature_value=8.5,
            baseline_value=12.0,
            shap_value=1.2,
            contribution_direction="positive",
            rank=1,
            description="Deficit in daily usage",
        )
    ]
    neg_feats = [
        FeatureContribution(
            feature_name="coverage_ratio",
            display_name="Smart-Meter Data Coverage Ratio",
            category="Data Quality",
            feature_value=0.99,
            baseline_value=None,
            shap_value=-0.35,
            contribution_direction="negative",
            rank=1,
            description="Completeness of readings",
        )
    ]
    sigs = [
        TamperingSignature(
            signature_type="sustained_step_down",
            detected=True,
            magnitude=0.60,
            duration_days=14,
            severity="high",
            description="Drop of 60.0% below baseline.",
        )
    ]
    temp_ev = [
        TemporalEvidence(
            anchor_date="2016-10-30",
            source_window_start="2016-09-01",
            source_window_end="2016-10-30",
            feature_name="sustained_drop_magnitude",
            display_name="Consumption Collapse Magnitude",
            observed_value=8.5,
            reference_value=12.0,
            relative_difference_pct=-70.8,
            shap_contribution=1.2,
            interpretation="Deficit observed over trailing 60-day interval.",
        )
    ]

    detailed = NarrativeGenerator.generate_detailed_explanation(
        meter_id="620E9685A1D2F4C35855EF1A3E0968AB",
        ticket_id="TCK-2016-10-30-EF550F26",
        evaluation_period="2016-10-30",
        model_probability=0.993,
        calibrated_probability=1.0,
        raw_score=4.82,
        base_value=-2.59,
        top_positive=pos_feats,
        top_negative=neg_feats,
        signatures=sigs,
        temporal_evidence=temp_ev,
        financial_context={
            "env": 32275.68,
            "estimated_recoverable_revenue": 32375.68,
            "dispatch_cost": 100.0,
        },
    )

    assert "Ticket TCK-2016-10-30-EF550F26" in detailed
    assert "Expected Net Value (ENV) of $32,275.68" in detailed
    assert "Estimated Consumption Collapse Magnitude" in detailed
    assert "Counter-Evidence & Mitigating Factors" in detailed
    assert STANDARD_SAFETY_DISCLAIMER in detailed
    assert validate_narrative_safety(detailed) is True
