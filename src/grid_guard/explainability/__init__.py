"""Explainability package for Grid-Guard: SHAP attributions, signatures, and narratives."""

from grid_guard.explainability.feature_mapping import FeatureMapper, FeatureMetadataInfo
from grid_guard.explainability.narratives import (
    STANDARD_SAFETY_DISCLAIMER,
    NarrativeGenerator,
    validate_narrative_safety,
)
from grid_guard.explainability.schemas import (
    FeatureContribution,
    InspectionExplanation,
    TamperingSignature,
    TemporalEvidence,
)
from grid_guard.explainability.shap_explainer import ShapExplainer
from grid_guard.explainability.signatures import TamperingSignatureDetector
from grid_guard.explainability.temporal_attribution import TemporalAttributor

__all__ = [
    "FeatureContribution",
    "FeatureMapper",
    "FeatureMetadataInfo",
    "InspectionExplanation",
    "NarrativeGenerator",
    "STANDARD_SAFETY_DISCLAIMER",
    "ShapExplainer",
    "TamperingSignature",
    "TamperingSignatureDetector",
    "TemporalAttributor",
    "TemporalEvidence",
    "validate_narrative_safety",
]
