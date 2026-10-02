"""Deterministic human-readable explanation and narrative generation for NTL inspection tickets."""

from __future__ import annotations

import re
from typing import Any

from grid_guard.explainability.schemas import (
    FeatureContribution,
    InspectionExplanation,
    TamperingSignature,
    TemporalEvidence,
)

# Mandatory safety disclaimer required on all inspection reports
STANDARD_SAFETY_DISCLAIMER = (
    "Model evidence reflects statistical consumption anomalies and requires physical field "
    "verification; smart-meter data alone does not establish physical tampering or unauthorized abstraction."
)

# Forbidden unsupported terms that must NEVER appear in generated explanations
FORBIDDEN_UNSUPPORTED_TERMS = [
    "bypass resistor",
    "magnet",
    "stealing electricity",
    "customer is stealing",
    "consumer is stealing",
    "thief",
    "theft proven",
    "proven theft",
    "guilty",
    "criminal",
    "prosecute",
    "neutral line has been bypassed",
    "meter has been tampered",
]


def validate_narrative_safety(narrative_text: str) -> bool:
    """Validate that generated narrative contains zero unsupported physical tampering claims.

    Args:
        narrative_text: Human-readable narrative string to audit.

    Returns:
        True if text satisfies all safety requirements.

    Raises:
        ValueError: If forbidden unsupported physical claims or inflammatory words are detected.
    """
    lower_text = narrative_text.lower()
    for forbidden in FORBIDDEN_UNSUPPORTED_TERMS:
        if re.search(r"\b" + re.escape(forbidden) + r"\b", lower_text):
            raise ValueError(
                f"Narrative safety violation: detected unsupported physical claim '{forbidden}'."
            )
    return True


class NarrativeGenerator:
    """Generates concise and detailed deterministic explanations for inspection tickets."""

    @staticmethod
    def generate_short_explanation(
        calibrated_prob: float,
        top_positive_features: list[FeatureContribution],
        detected_signatures: list[TamperingSignature],
        financial_context: dict[str, Any] | None = None,
    ) -> str:
        """Generate a concise 2-3 sentence summary suitable for field dispatch cards."""
        fin = financial_context or {}
        env_val = fin.get("env")

        # 1. Opening risk & economic assessment
        prob_pct = calibrated_prob * 100.0
        if env_val is not None and env_val > 0:
            opening = (
                f"High tampering risk ({prob_pct:.1f}% probability) with positive "
                f"Expected Net Value (${env_val:,.2f})."
            )
        else:
            opening = f"Elevated tampering risk ({prob_pct:.1f}% predicted probability)."

        # 2. Key behavioral anomaly / signature
        evidence_phrases: list[str] = []
        if detected_signatures:
            sig = detected_signatures[0]
            if sig.signature_type == "sustained_step_down":
                evidence_phrases.append(
                    f"sustained consumption drop of {sig.magnitude * 100:.0f}% below baseline"
                )
            elif sig.signature_type == "zero_streak":
                evidence_phrases.append(
                    f"extended streak of {int(sig.magnitude)} zero-consumption days"
                )
            elif sig.signature_type == "flatline":
                evidence_phrases.append("abnormal flatline load profile with negligible variance")
            elif sig.signature_type == "behavior_shift":
                evidence_phrases.append("sudden week-over-week consumption collapse")

        # 3. Add top 1-2 feature drivers if needed
        for feat in top_positive_features[:2]:
            if "std" in feat.feature_name and "volatility" not in " ".join(evidence_phrases):
                evidence_phrases.append(
                    "elevated historical load volatility contrasting recent readings"
                )
            elif "ratio_14d_60d" in feat.feature_name and "drop" not in " ".join(evidence_phrases):
                evidence_phrases.append(
                    "recent 14-day usage severely depressed relative to 60-day baseline"
                )
            elif "zero" in feat.feature_name and "zero" not in " ".join(evidence_phrases):
                evidence_phrases.append(
                    f"frequent zero-usage days ({feat.feature_value:.0f} recorded)"
                )

        if evidence_phrases:
            evidence_summary = "; ".join(evidence_phrases[:2]).capitalize() + "."
        else:
            evidence_summary = (
                "Anomalous temporal load pattern detected across trailing billing windows."
            )

        closing = "Field inspection recommended to verify physical meter integrity."
        short_text = f"{opening} {evidence_summary} {closing}"
        validate_narrative_safety(short_text)
        return short_text

    @staticmethod
    def generate_detailed_explanation(
        meter_id: str,
        ticket_id: str,
        evaluation_period: str,
        model_probability: float,
        calibrated_probability: float,
        raw_score: float,
        base_value: float,
        top_positive: list[FeatureContribution],
        top_negative: list[FeatureContribution],
        signatures: list[TamperingSignature],
        temporal_evidence: list[TemporalEvidence],
        financial_context: dict[str, Any] | None = None,
    ) -> str:
        """Generate a complete multi-section technical explanation report."""
        fin = financial_context or {}
        env_val = fin.get("env")
        leakage_val = fin.get("estimated_recoverable_revenue")
        dispatch_cost = fin.get("dispatch_cost", 100.0)

        lines: list[str] = [
            f"### Inspection Explanation: Ticket {ticket_id}",
            f"**Target Meter**: `{meter_id}` | **Evaluation Period**: {evaluation_period}",
            f"**Model Risk Score**: {raw_score:+.3f} log-odds (Base: {base_value:+.3f}) | "
            f"**Raw Probability**: {model_probability:.3f} | **Calibrated Probability**: {calibrated_probability:.3f}",
            "",
            "#### 1. Operational & Economic Decision",
        ]

        if env_val is not None and env_val > 0:
            lines.append(
                f"Field inspection is economically justified with an **Expected Net Value (ENV) of ${env_val:,.2f}** "
                f"(projected recoverable revenue of ${leakage_val:,.2f} versus dispatch crew cost of ${dispatch_cost:,.2f})."
            )
        else:
            lines.append(
                "Inspection decision evaluated under statistical risk thresholding "
                f"with predicted tampering probability of {calibrated_probability:.3f}."
            )

        lines.append("")
        lines.append("#### 2. Primary Contributing Evidence (Positive Model Drivers)")
        if top_positive:
            for feat in top_positive:
                ref_str = (
                    f" (Baseline: {feat.baseline_value:.2f})"
                    if feat.baseline_value is not None
                    else ""
                )
                lines.append(
                    f"- **{feat.display_name}** (`{feat.feature_name}` = {feat.feature_value:.2f}{ref_str}): "
                    f"Contributed **{feat.shap_value:+.3f}** to risk margin. {feat.description}."
                )
        else:
            lines.append("- No individual positive feature exceeded reporting threshold.")

        lines.append("")
        lines.append("#### 3. Detected Behavioral Signatures")
        if signatures:
            for sig in signatures:
                lines.append(
                    f"- **[{sig.severity.upper()} SEVERITY] {sig.signature_type.replace('_', ' ').title()}**: "
                    f"{sig.description}"
                )
        else:
            lines.append(
                "- No rule-based heuristic signatures triggered; anomaly identified primarily through multivariate feature interaction."
            )

        lines.append("")
        lines.append("#### 4. Historical Time Window Attribution")
        if temporal_evidence:
            for ev in temporal_evidence[:3]:
                diff_str = (
                    f", {ev.relative_difference_pct:+.1f}% vs baseline"
                    if ev.relative_difference_pct is not None
                    else ""
                )
                lines.append(
                    f"- **{ev.display_name}**: Source window `{ev.source_window_start}` to `{ev.source_window_end}` "
                    f"(observed: {ev.observed_value:.2f}{diff_str}). {ev.interpretation}"
                )
        else:
            lines.append(f"- Active evaluation anchor date: {evaluation_period}.")

        lines.append("")
        lines.append("#### 5. Counter-Evidence & Mitigating Factors (Negative Model Drivers)")
        if top_negative:
            for feat in top_negative:
                lines.append(
                    f"- **{feat.display_name}** (`{feat.feature_name}` = {feat.feature_value:.2f}): "
                    f"Moderated risk score by **{feat.shap_value:-.3f}**. {feat.description}."
                )
        else:
            lines.append(
                "- Negligible counter-evidence detected; indicators consistently lean toward anomalous risk."
            )

        lines.append("")
        lines.append("#### 6. Regulatory & Safety Disclaimer")
        lines.append(STANDARD_SAFETY_DISCLAIMER)

        full_text = "\n".join(lines)
        validate_narrative_safety(full_text)
        return full_text

    @classmethod
    def compose_explanation(
        cls,
        ticket_id: str,
        meter_id: str,
        evaluation_period: str,
        model_probability: float,
        calibrated_probability: float,
        raw_score: float,
        base_value: float,
        top_positive: list[FeatureContribution],
        top_negative: list[FeatureContribution],
        signatures: list[TamperingSignature],
        temporal_evidence: list[TemporalEvidence],
        financial_context: dict[str, Any] | None = None,
        priority_rank: int | None = None,
        inspection_recommended: bool = True,
    ) -> InspectionExplanation:
        """Compose a canonical InspectionExplanation instance."""
        fin = financial_context or {}
        env_val = fin.get("env")

        short_exp = cls.generate_short_explanation(
            calibrated_prob=calibrated_probability,
            top_positive_features=top_positive,
            detected_signatures=signatures,
            financial_context=fin,
        )

        detailed_exp = cls.generate_detailed_explanation(
            meter_id=meter_id,
            ticket_id=ticket_id,
            evaluation_period=evaluation_period,
            model_probability=model_probability,
            calibrated_probability=calibrated_probability,
            raw_score=raw_score,
            base_value=base_value,
            top_positive=top_positive,
            top_negative=top_negative,
            signatures=signatures,
            temporal_evidence=temporal_evidence,
            financial_context=fin,
        )

        counter_summary = (
            f"{len(top_negative)} counter-evidence features moderated risk margin"
            if top_negative
            else "No significant counter-evidence"
        )

        return InspectionExplanation(
            ticket_id=ticket_id,
            meter_id=meter_id,
            evaluation_period=evaluation_period,
            model_probability=model_probability,
            calibrated_probability=calibrated_probability,
            raw_score=raw_score,
            base_value=base_value,
            expected_net_value=env_val,
            inspection_recommended=inspection_recommended,
            priority_rank=priority_rank,
            short_explanation=short_exp,
            detailed_explanation=detailed_exp,
            top_positive_features=top_positive,
            top_negative_features=top_negative,
            detected_signatures=signatures,
            temporal_evidence=temporal_evidence,
            counter_evidence_summary=counter_summary,
            financial_context=fin,
            safety_caveat=STANDARD_SAFETY_DISCLAIMER,
        )
