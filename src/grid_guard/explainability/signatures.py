"""Rule-based tampering signature detection independent of machine learning model weights."""

from __future__ import annotations

from typing import Any

from grid_guard.config.explainability import ExplainabilitySettings
from grid_guard.explainability.schemas import TamperingSignature


class TamperingSignatureDetector:
    """Detects behavioral non-technical loss signatures using deterministic rule-based criteria."""

    def __init__(self, settings: ExplainabilitySettings | None = None) -> None:
        self.settings = settings or ExplainabilitySettings()

    def detect_all(self, feature_row: dict[str, Any]) -> list[TamperingSignature]:
        """Evaluate all signature criteria against a meter's feature values.

        Args:
            feature_row: Dictionary mapping feature names to numerical values.

        Returns:
            List of detected TamperingSignature objects.
        """
        signatures: list[TamperingSignature] = []

        # 1. Sustained Step-Down Signature
        step_down = self._check_sustained_step_down(feature_row)
        if step_down is not None:
            signatures.append(step_down)

        # 2. Zero Streak Signature
        zero_streak = self._check_zero_streak(feature_row)
        if zero_streak is not None:
            signatures.append(zero_streak)

        # 3. Flatline / Low-Variability Signature
        flatline = self._check_flatline(feature_row)
        if flatline is not None:
            signatures.append(flatline)

        # 4. Behavioral Regime Shift Signature
        regime_shift = self._check_regime_shift(feature_row)
        if regime_shift is not None:
            signatures.append(regime_shift)

        # 5. Abnormal Peak-to-Average Load Signature
        par_sig = self._check_abnormal_peak(feature_row)
        if par_sig is not None:
            signatures.append(par_sig)

        return signatures

    def _check_sustained_step_down(self, row: dict[str, Any]) -> TamperingSignature | None:
        """Check for structural collapse in consumption relative to historical baseline."""
        ratio_14_60 = row.get("ratio_14d_60d")
        drop_ratio = row.get("sustained_drop_ratio")
        duration = row.get("sustained_drop_duration")
        magnitude_kwh = row.get("sustained_drop_magnitude")

        # Determine if step-down conditions are met
        is_step_down = False
        effective_drop = 0.0
        dur_days = int(duration) if duration is not None and duration > 0 else None

        if drop_ratio is not None and drop_ratio >= (1.0 - self.settings.step_down_ratio_threshold):
            is_step_down = True
            effective_drop = float(drop_ratio)
        elif ratio_14_60 is not None and ratio_14_60 <= self.settings.step_down_ratio_threshold:
            is_step_down = True
            effective_drop = 1.0 - float(ratio_14_60)
        elif dur_days is not None and dur_days >= self.settings.step_down_min_days:
            is_step_down = True
            effective_drop = float(drop_ratio) if drop_ratio is not None else 0.50

        if not is_step_down or effective_drop <= 0.20:
            return None

        # Determine severity
        if effective_drop >= 0.70 or (dur_days is not None and dur_days >= 14):
            severity = "high"
        elif effective_drop >= 0.50 or (dur_days is not None and dur_days >= 7):
            severity = "moderate"
        else:
            severity = "low"

        mag_str = (
            f" ({magnitude_kwh:.1f} kWh/day deficit)" if magnitude_kwh and magnitude_kwh > 0 else ""
        )
        dur_str = f" persisting for {dur_days} consecutive days" if dur_days else ""

        return TamperingSignature(
            signature_type="sustained_step_down",
            detected=True,
            magnitude=round(effective_drop, 3),
            duration_days=dur_days,
            severity=severity,
            description=(
                f"Sustained consumption reduction of {effective_drop * 100:.1f}% below "
                f"historical baseline{mag_str}{dur_str}."
            ),
        )

    def _check_zero_streak(self, row: dict[str, Any]) -> TamperingSignature | None:
        """Check for consecutive or frequent zero-consumption observations."""
        current_streak = row.get("current_zero_streak")
        zero_count_7d = row.get("zero_count_7d")
        zero_count_30d = row.get("zero_count_30d")

        streak_len = int(current_streak) if current_streak is not None else 0
        z7 = int(zero_count_7d) if zero_count_7d is not None else 0
        z30 = int(zero_count_30d) if zero_count_30d is not None else 0

        if streak_len >= self.settings.zero_streak_min_days:
            severity = "high" if streak_len >= 7 else "moderate"
            return TamperingSignature(
                signature_type="zero_streak",
                detected=True,
                magnitude=float(streak_len),
                duration_days=streak_len,
                severity=severity,
                description=f"Active streak of {streak_len} consecutive days with zero metered consumption.",
            )

        if z7 >= 3:
            severity = "high" if z7 >= 5 else "moderate"
            return TamperingSignature(
                signature_type="zero_streak",
                detected=True,
                magnitude=float(z7),
                duration_days=z7,
                severity=severity,
                description=f"Recorded {z7} zero-consumption days in the trailing 7-day window.",
            )

        if z30 >= 10:
            return TamperingSignature(
                signature_type="zero_streak",
                detected=True,
                magnitude=float(z30),
                duration_days=z30,
                severity="moderate",
                description=f"Persistent zero usage across {z30} days in the trailing 30-day billing cycle.",
            )

        return None

    def _check_flatline(self, row: dict[str, Any]) -> TamperingSignature | None:
        """Check for artificial absence of load variance or constant metered readings."""
        cv_7d = row.get("rolling_cv_7d")
        streak = row.get("flatline_streak")
        mean_7d = row.get("rolling_mean_7d")

        streak_len = int(streak) if streak is not None else 0

        # Only flag flatline if there is some consumption (>0.05 kWh) so it doesn't duplicate zero streak
        is_non_zero = mean_7d is None or mean_7d > 0.05

        if streak_len >= self.settings.flatline_min_days and is_non_zero:
            severity = "high" if streak_len >= 14 else "moderate"
            return TamperingSignature(
                signature_type="flatline",
                detected=True,
                magnitude=float(streak_len),
                duration_days=streak_len,
                severity=severity,
                description=(
                    f"Consumption has remained near-constant for {streak_len} consecutive days "
                    "with negligible daily load variance."
                ),
            )

        if cv_7d is not None and cv_7d < self.settings.flatline_max_cv and is_non_zero:
            return TamperingSignature(
                signature_type="flatline",
                detected=True,
                magnitude=round(float(cv_7d), 4),
                duration_days=7,
                severity="moderate" if cv_7d < 0.02 else "low",
                description=(
                    f"Unusually low coefficient of variation ({float(cv_7d):.3f}) over past 7 days, "
                    "indicating unnatural load constancy."
                ),
            )

        return None

    def _check_regime_shift(self, row: dict[str, Any]) -> TamperingSignature | None:
        """Check for abrupt week-over-week or monthly profile transition."""
        ratio_7_30 = row.get("ratio_7d_30d")
        wow_change = row.get("wow_consumption_change")

        if ratio_7_30 is not None and ratio_7_30 < 0.45:
            drop_pct = (1.0 - ratio_7_30) * 100.0
            return TamperingSignature(
                signature_type="behavior_shift",
                detected=True,
                magnitude=round(1.0 - ratio_7_30, 3),
                duration_days=7,
                severity="moderate",
                description=(
                    f"Abrupt transition: trailing 7-day consumption dropped by {drop_pct:.1f}% "
                    "relative to the 30-day baseline."
                ),
            )

        if wow_change is not None and wow_change < -0.50:
            drop_pct = min(100.0, abs(float(wow_change)) * 100.0)
            return TamperingSignature(
                signature_type="behavior_shift",
                detected=True,
                magnitude=round(abs(float(wow_change)), 3),
                duration_days=7,
                severity="moderate",
                description=(f"Week-over-week consumption contracted by {drop_pct:.1f}%."),
            )

        return None

    def _check_abnormal_peak(self, row: dict[str, Any]) -> TamperingSignature | None:
        """Check for abnormal peak-to-average ratio collapse."""
        par_7d = row.get("par_7d")
        par_30d = row.get("par_30d")

        if par_7d is not None and par_7d < 1.05 and (par_30d is not None and par_30d > 1.30):
            return TamperingSignature(
                signature_type="abnormal_peak_behavior",
                detected=True,
                magnitude=round(float(par_7d), 3),
                duration_days=7,
                severity="low",
                description=(
                    f"Peak-to-Average Ratio collapsed from 30d baseline ({float(par_30d):.2f}) "
                    f"to near-unity ({float(par_7d):.2f}) over trailing 7 days."
                ),
            )

        return None
