"""Feature engineering module for Grid-Guard (Phase 3)."""

from grid_guard.features.calendar import CalendarFeatureExtractor
from grid_guard.features.context import ContextFeatureExtractor
from grid_guard.features.lags import LagFeatureExtractor
from grid_guard.features.periodicity import PeriodicityFeatureExtractor
from grid_guard.features.pipeline import FeaturePipeline
from grid_guard.features.quality import QualityFeatureExtractor
from grid_guard.features.ratios import RatioFeatureExtractor
from grid_guard.features.registry import (
    FeatureCategory,
    FeatureDefinition,
    FeatureRegistry,
    LeakageRisk,
)
from grid_guard.features.rolling import RollingFeatureExtractor
from grid_guard.features.signatures import TamperingSignatureExtractor

__all__ = [
    "CalendarFeatureExtractor",
    "ContextFeatureExtractor",
    "FeatureCategory",
    "FeatureDefinition",
    "FeaturePipeline",
    "FeatureRegistry",
    "LagFeatureExtractor",
    "LeakageRisk",
    "PeriodicityFeatureExtractor",
    "QualityFeatureExtractor",
    "RatioFeatureExtractor",
    "RollingFeatureExtractor",
    "TamperingSignatureExtractor",
]
