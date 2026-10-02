"""Inference service orchestrating feature engineering, model inference, financial decisioning, and SHAP explainability."""

from __future__ import annotations

import logging
import math
import time
from datetime import date
from pathlib import Path

import lightgbm as lgb
import numpy as np
import polars as pl

from grid_guard.api.schemas.common import DataQualitySummary, ModelMetadataResponse
from grid_guard.api.schemas.inspection import (
    InspectionQueueRequest,
    InspectionQueueResponse,
    InspectionTicketResponse,
)
from grid_guard.api.schemas.prediction import (
    BatchItemError,
    BatchPredictionRequest,
    BatchPredictionResponse,
    DecisionOutput,
    ExplanationOutput,
    FeatureContributionSchema,
    FinancialOutput,
    PredictionOutput,
    SingleMeterPredictionRequest,
    SingleMeterPredictionResponse,
    TamperingSignatureSchema,
    TemporalEvidenceSchema,
)
from grid_guard.config.api import APISettings
from grid_guard.config.decision import DecisionRule
from grid_guard.config.settings import Settings, get_settings
from grid_guard.decision.thresholds import (
    compute_active_threshold,
    compute_bayes_cost_threshold,
    compute_env_threshold,
)
from grid_guard.decision.tickets import generate_deterministic_ticket_id
from grid_guard.evaluation.financial import LeakageEstimator
from grid_guard.explainability.feature_mapping import FeatureMapper
from grid_guard.explainability.narratives import (
    STANDARD_SAFETY_DISCLAIMER,
    NarrativeGenerator,
)
from grid_guard.explainability.shap_explainer import ShapExplainer
from grid_guard.explainability.signatures import TamperingSignatureDetector
from grid_guard.explainability.temporal_attribution import TemporalAttributor
from grid_guard.features.pipeline import FeaturePipeline

logger = logging.getLogger(__name__)


class InferenceService:
    """Singleton application service managing model lifecycle and end-to-end inference workflows."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.api_settings: APISettings = self.settings.api

        # 1. Resolve and verify model artifact path
        raw_mpath = Path(self.api_settings.model_path)
        if not raw_mpath.is_absolute():
            self.model_path = (self.settings.project_root / raw_mpath).resolve()
        else:
            self.model_path = raw_mpath.resolve()

        if not self.model_path.is_file():
            raise FileNotFoundError(
                f"Model checkpoint not found at '{self.model_path}'. "
                "Ensure Phase 6 champion model has been generated or configure API_SETTINGS.model_path."
            )

        logger.info(f"Loading LightGBM champion booster from '{self.model_path}'...")
        self.booster = lgb.Booster(model_file=str(self.model_path))
        self.feature_names = list(self.booster.feature_name())
        logger.info(f"Successfully loaded booster with {len(self.feature_names)} features.")

        # 2. Initialize feature pipeline & domain helpers
        self.feature_pipeline = FeaturePipeline(config=self.settings.features)
        self.feature_mapper = FeatureMapper()
        self.leakage_estimator = LeakageEstimator(assumptions=self.settings.financial)

        # 3. Initialize explainability components
        logger.info("Initializing Tree-SHAP explainer...")
        self.explainer = ShapExplainer(model=self.booster, feature_mapper=self.feature_mapper)
        self.base_value = self.explainer.base_value
        self.base_probability = float(1.0 / (1.0 + np.exp(-self.base_value)))
        self.signature_detector = TamperingSignatureDetector(settings=self.settings.explainability)
        self.temporal_attributor = TemporalAttributor(feature_mapper=self.feature_mapper)
        logger.info(
            f"Explainability initialized: Base log-odds={self.base_value:.4f}, "
            f"Prevalence={self.base_probability * 100:.2f}%."
        )

        self._is_ready = True

    @property
    def is_ready(self) -> bool:
        """Check if service is initialized and ready to serve predictions."""
        return self._is_ready and self.booster is not None and self.explainer is not None

    def get_metadata(self) -> ModelMetadataResponse:
        """Return safe, non-sensitive model and pipeline metadata."""
        return ModelMetadataResponse(
            model_name="cost_sensitive_champion_lgb",
            model_version="phase6_cost_sensitive_v1",
            model_type="LightGBM Booster (Custom Cost-Sensitive Objective)",
            objective_type="financially_weighted_logistic",
            feature_version="phase3_temporal_features_v1",
            feature_count=len(self.feature_names),
            base_log_odds=round(self.base_value, 4),
            base_probability=round(self.base_probability, 4),
            calibration_method="sigmoid_stable",
            api_version=self.api_settings.version,
        )

    def predict_single(
        self, request: SingleMeterPredictionRequest
    ) -> SingleMeterPredictionResponse:
        """Execute end-to-end inference, decisioning, and explainability for a single meter."""
        start_time = time.perf_counter()

        # Step 1: Input Validation on Readings Length
        readings = request.readings
        n_readings = len(readings)
        if n_readings < self.api_settings.min_readings_per_meter:
            raise ValueError(
                f"Insufficient meter history: request contains {n_readings} readings, but at least "
                f"{self.api_settings.min_readings_per_meter} daily readings are required to compute temporal features."
            )
        if n_readings > self.api_settings.max_readings_per_meter:
            raise ValueError(
                f"Payload exceeds limit: request contains {n_readings} readings, maximum permitted is "
                f"{self.api_settings.max_readings_per_meter}."
            )

        # Step 2: Convert to Polars DataFrame
        dates = [date.fromisoformat(r.timestamp) for r in readings]
        consumptions = [float(r.consumption_kwh) for r in readings]
        meter_ids = [request.meter_id] * n_readings

        df_raw = pl.DataFrame(
            {
                "meter_id": meter_ids,
                "timestamp": dates,
                "consumption_kwh": consumptions,
            }
        ).sort("timestamp")

        # Step 3: Compute Data Quality Metrics
        earliest_date = df_raw.get_column("timestamp").min()
        latest_date = df_raw.get_column("timestamp").max()
        history_days = max(1, (latest_date - earliest_date).days + 1)
        coverage_ratio = round(float(min(1.0, n_readings / history_days)), 4)
        missing_ratio = round(float(max(0.0, 1.0 - coverage_ratio)), 4)
        imputation_ratio = 0.0

        warnings: list[str] = []
        if n_readings < self.api_settings.recommended_readings_per_meter:
            warnings.append(
                f"History length ({n_readings} days) is below the recommended 90 days. "
                "Seasonal 60-day and 90-day baselines may be partially attenuated."
            )
        if coverage_ratio < 0.85:
            warnings.append(
                f"Low data coverage ({coverage_ratio:.1%}). Irregular time-series telemetry detected."
            )

        quality_status = (
            "good"
            if coverage_ratio >= 0.90 and n_readings >= 60
            else ("adequate" if n_readings >= 14 else "insufficient_history")
        )

        data_quality = DataQualitySummary(
            coverage_ratio=coverage_ratio,
            missing_ratio=missing_ratio,
            imputation_ratio=imputation_ratio,
            total_readings=n_readings,
            history_days=history_days,
            status=quality_status,
            warnings=warnings,
        )

        # Step 4: Run Feature Engineering Pipeline
        df_transformed = self.feature_pipeline.transform(
            df_raw, value_col="consumption_kwh", timestamp_col="timestamp", meter_col="meter_id"
        )

        # Attach telemetry data quality features matching training schema
        df_transformed = df_transformed.with_columns(
            [
                pl.lit(coverage_ratio).cast(pl.Float32).alias("coverage_ratio"),
                pl.lit(missing_ratio).cast(pl.Float32).alias("missing_ratio"),
                pl.lit(imputation_ratio).cast(pl.Float32).alias("imputation_ratio"),
            ]
        )

        # Step 5: Extract Snapshot Evaluation Row
        if request.evaluation_date:
            target_date = date.fromisoformat(request.evaluation_date)
            snapshot_df = df_transformed.filter(pl.col("timestamp") == target_date)
            if snapshot_df.is_empty():
                # Take latest available date <= target_date
                snapshot_df = df_transformed.filter(pl.col("timestamp") <= target_date).tail(1)
                if snapshot_df.is_empty():
                    snapshot_df = df_transformed.tail(1)
        else:
            snapshot_df = df_transformed.tail(1)

        eval_timestamp = str(snapshot_df.get_column("timestamp")[0])
        snapshot_dict = snapshot_df.to_dicts()[0]

        # Step 6: Model Inference (Raw Margin & Sigmoid Probability)
        X_df = snapshot_df.select(self.feature_names).to_pandas()
        raw_margin = float(self.booster.predict(X_df, raw_score=True)[0])
        tamper_prob = float(1.0 / (1.0 + np.exp(-raw_margin)))
        calibrated_prob = tamper_prob  # Raw sigmoid is the calibrated baseline for champion booster

        # Step 7: Financial Estimation & Economic Decisioning
        tariff = float(
            request.tariff if request.tariff is not None else self.api_settings.default_tariff
        )
        dispatch_cost = float(
            request.dispatch_cost
            if request.dispatch_cost is not None
            else self.api_settings.default_dispatch_cost
        )

        # Baseline & Observed consumption for leakage calculation
        base_60d = float(
            snapshot_dict.get("rolling_mean_60d") or snapshot_dict.get("rolling_mean_30d") or 0.0
        )
        obs_14d = float(
            snapshot_dict.get("rolling_mean_14d") or snapshot_dict.get("consumption_kwh") or 0.0
        )
        daily_deficit = max(0.0, base_60d - obs_14d)

        leakage_monthly_kwh = daily_deficit * 30.0
        cycle_revenue_loss = leakage_monthly_kwh * tariff
        undetected_cycles = float(self.settings.financial.undetected_cycles)
        estimated_leakage_cost = cycle_revenue_loss * undetected_cycles

        recovery_factor = float(self.settings.decision.recovery_factor)
        recoverable_revenue = estimated_leakage_cost * recovery_factor
        expected_gross_recovery = calibrated_prob * recoverable_revenue
        env = expected_gross_recovery - dispatch_cost

        # Thresholds
        tau_cost = float(
            compute_bayes_cost_threshold(
                dispatch_cost=dispatch_cost, fn_cost=estimated_leakage_cost
            )
        )
        tau_env = float(
            compute_env_threshold(
                dispatch_cost=dispatch_cost, recoverable_revenue=recoverable_revenue
            )
        )
        decision_rule_enum = DecisionRule(request.decision_rule)
        active_tau = float(
            compute_active_threshold(
                tau_cost=tau_cost,
                tau_env=tau_env,
                decision_rule=decision_rule_enum,
                fixed_threshold=request.fixed_threshold,
            )
        )

        # Decision Recommendation
        if decision_rule_enum == DecisionRule.ENV:
            inspection_recommended = bool(
                env > self.settings.decision.min_env
                and calibrated_prob >= self.settings.decision.min_probability
                and recoverable_revenue >= self.settings.decision.min_recoverable_revenue
            )
        elif decision_rule_enum == DecisionRule.COST_THRESHOLD:
            inspection_recommended = bool(
                calibrated_prob >= tau_cost
                and calibrated_prob >= self.settings.decision.min_probability
            )
        elif decision_rule_enum == DecisionRule.FIXED_THRESHOLD:
            inspection_recommended = bool(calibrated_prob >= request.fixed_threshold)
        else:
            inspection_recommended = bool(env > 0.0)

        prediction_label = 1 if inspection_recommended else 0
        priority_context = (
            f"Inspection recommended with positive Expected Net Value of ${env:,.2f}"
            if inspection_recommended
            else "Inspection not justified under active economic threshold criteria."
        )

        # Step 8: Tree-SHAP Explainability & Narratives (Optional)
        explanation_output: ExplanationOutput | None = None
        if request.include_explanation:
            shap_matrix = self.explainer.explain(X_df, verify_reconstruction=False)
            pos_contribs, neg_contribs = self.explainer.explain_instance(
                snapshot_dict, shap_matrix[0]
            )

            # Detect Domain Tampering Signatures
            signatures = self.signature_detector.detect_all(snapshot_dict)

            # Build Temporal Attribution Evidence
            temporal_evidences = [
                self.temporal_attributor.attribute(
                    feature_name=f.feature_name,
                    anchor_date=eval_timestamp,
                    observed_value=f.feature_value,
                    shap_contribution=f.shap_value,
                    feature_values_row=snapshot_dict,
                )
                for f in pos_contribs[:3]
            ]

            fin_context = {
                "env": env,
                "estimated_recoverable_revenue": recoverable_revenue,
                "dispatch_cost": dispatch_cost,
                "tariff": tariff,
            }

            short_narrative = NarrativeGenerator.generate_short_explanation(
                calibrated_prob=calibrated_prob,
                top_positive_features=pos_contribs,
                detected_signatures=signatures,
                financial_context=fin_context,
            )

            ticket_id = generate_deterministic_ticket_id(request.meter_id, eval_timestamp)
            detailed_narrative = NarrativeGenerator.generate_detailed_explanation(
                meter_id=request.meter_id,
                ticket_id=ticket_id,
                evaluation_period=eval_timestamp,
                model_probability=tamper_prob,
                calibrated_probability=calibrated_prob,
                raw_score=raw_margin,
                base_value=self.base_value,
                top_positive=pos_contribs,
                top_negative=neg_contribs,
                signatures=signatures,
                temporal_evidence=temporal_evidences,
                financial_context=fin_context,
            )

            explanation_output = ExplanationOutput(
                summary=short_narrative,
                detailed_explanation=detailed_narrative,
                top_positive_contributors=[
                    FeatureContributionSchema(**c.to_dict()) for c in pos_contribs
                ],
                top_negative_contributors=[
                    FeatureContributionSchema(**c.to_dict()) for c in neg_contribs
                ],
                detected_signatures=[TamperingSignatureSchema(**s.to_dict()) for s in signatures],
                temporal_evidence=[
                    TemporalEvidenceSchema(**e.to_dict()) for e in temporal_evidences
                ],
                counter_evidence_summary=(
                    f"Moderated by {len(neg_contribs)} negative drivers including {neg_contribs[0].display_name}."
                    if neg_contribs
                    else None
                ),
                safety_caveat=STANDARD_SAFETY_DISCLAIMER,
            )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        return SingleMeterPredictionResponse(
            meter_id=request.meter_id,
            evaluation_timestamp=eval_timestamp,
            model=self.get_metadata(),
            data_quality=data_quality,
            prediction=PredictionOutput(
                raw_score=round(raw_margin, 4),
                tamper_probability=round(tamper_prob, 4),
                calibrated_probability=round(calibrated_prob, 4),
                prediction_label=prediction_label,
            ),
            financial=FinancialOutput(
                estimated_leakage_kwh=round(leakage_monthly_kwh, 2),
                estimated_recoverable_revenue=round(recoverable_revenue, 2),
                expected_gross_recovery=round(expected_gross_recovery, 2),
                dispatch_cost=round(dispatch_cost, 2),
                expected_net_value=round(env, 2),
                tariff=tariff,
                currency=self.api_settings.currency,
            ),
            decision=DecisionOutput(
                decision_rule=request.decision_rule,
                active_threshold=round(active_tau, 4) if not math.isinf(active_tau) else 1.0,
                tau_cost=round(tau_cost, 4),
                tau_env=round(tau_env, 4) if not math.isinf(tau_env) else 999.0,
                inspection_recommended=inspection_recommended,
                priority_context=priority_context,
            ),
            explanation=explanation_output,
            processing_time_ms=elapsed_ms,
        )

    def predict_batch(self, request: BatchPredictionRequest) -> BatchPredictionResponse:
        """Process bounded multi-meter batch prediction request with partial success support."""
        start_time = time.perf_counter()
        n_items = len(request.meters)
        if n_items > self.api_settings.max_batch_size:
            raise ValueError(
                f"Batch size {n_items} exceeds maximum permitted batch size of {self.api_settings.max_batch_size}."
            )

        batch_id = request.batch_id or f"BATCH-{int(time.time())}"
        results: list[SingleMeterPredictionResponse] = []
        errors: list[BatchItemError] = []

        for m_req in request.meters:
            # Propagate batch include_explanation flag if not explicitly set
            if not m_req.include_explanation and request.include_explanation:
                m_req.include_explanation = True

            try:
                res = self.predict_single(m_req)
                results.append(res)
            except Exception as e:
                logger.warning(f"Batch item failed for meter '{m_req.meter_id}': {e}")
                errors.append(
                    BatchItemError(
                        meter_id=m_req.meter_id,
                        error=str(e),
                        error_type=type(e).__name__,
                    )
                )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        return BatchPredictionResponse(
            batch_id=batch_id,
            total_items=n_items,
            successful_items=len(results),
            failed_items=len(errors),
            results=results,
            errors=errors,
            processing_time_ms=elapsed_ms,
        )

    def generate_ticket(self, request: SingleMeterPredictionRequest) -> InspectionTicketResponse:
        """Generate a complete field inspection work order ticket for a single meter."""
        # Force explanation generation for inspection ticket
        request.include_explanation = True
        pred_res = self.predict_single(request)

        ticket_id = generate_deterministic_ticket_id(
            pred_res.meter_id, pred_res.evaluation_timestamp
        )

        sig_summary = "Multivariate Feature Anomaly"
        if pred_res.explanation and pred_res.explanation.detected_signatures:
            sig_summary = "; ".join(
                [
                    f"{s.signature_type.replace('_', ' ').title()} ({s.severity})"
                    for s in pred_res.explanation.detected_signatures
                ]
            )

        return InspectionTicketResponse(
            ticket_id=ticket_id,
            meter_id=pred_res.meter_id,
            evaluation_period=pred_res.evaluation_timestamp,
            tamper_probability=pred_res.prediction.tamper_probability,
            calibrated_probability=pred_res.prediction.calibrated_probability,
            estimated_leakage_kwh=pred_res.financial.estimated_leakage_kwh,
            estimated_recoverable_revenue=pred_res.financial.estimated_recoverable_revenue,
            dispatch_cost=pred_res.financial.dispatch_cost,
            expected_gross_recovery=pred_res.financial.expected_gross_recovery,
            env=pred_res.financial.expected_net_value,
            tau_cost=pred_res.decision.tau_cost,
            tau_env=pred_res.decision.tau_env,
            active_threshold=pred_res.decision.active_threshold,
            decision_rule=pred_res.decision.decision_rule,
            inspection_recommended=pred_res.decision.inspection_recommended,
            priority_rank=1 if pred_res.decision.inspection_recommended else None,
            customer_type=request.customer_type,
            feeder_id=request.feeder_id,
            data_quality_status=pred_res.data_quality.status,
            signatures_summary=sig_summary,
            explanation=pred_res.explanation,
            safety_caveat=STANDARD_SAFETY_DISCLAIMER,
        )

    def get_inspection_queue(self, request: InspectionQueueRequest) -> InspectionQueueResponse:
        """Query or generate a prioritized inspection queue using Phase 7/8 precomputed artifacts."""
        start_time = time.perf_counter()

        # Locate precomputed Phase 8 enriched tickets
        enriched_path = (
            self.settings.artifacts_dir / "explainability" / "enriched_top_100_tickets.csv"
        )
        fallback_path = self.settings.artifacts_dir / "decision" / "top_100_inspection_tickets.csv"

        target_file = enriched_path if enriched_path.is_file() else fallback_path
        if not target_file.is_file():
            raise FileNotFoundError(
                f"Inspection tickets artifact not found at '{target_file}'. "
                "Run Phase 7/8 pipelines first to populate the inspection queue."
            )

        df = pl.read_csv(target_file)

        # Apply filtering
        if "env" in df.columns:
            df = df.filter(pl.col("env") >= request.min_env)
        if "calibrated_probability" in df.columns:
            df = df.filter(pl.col("calibrated_probability") >= request.min_probability)

        # Slice to max_inspections
        df_queue = df.head(request.max_inspections)

        tickets: list[InspectionTicketResponse] = []
        for rank, row in enumerate(df_queue.to_dicts(), 1):
            t_id = row.get("ticket_id") or generate_deterministic_ticket_id(
                row["meter_id"], str(row.get("evaluation_period", "2016-10-30"))
            )

            # Build minimal explanation record if available
            exp_record: ExplanationOutput | None = None
            if request.include_explanations and "short_narrative" in row and row["short_narrative"]:
                exp_record = ExplanationOutput(
                    summary=row["short_narrative"],
                    detailed_explanation=row["short_narrative"],
                    safety_caveat=STANDARD_SAFETY_DISCLAIMER,
                )

            tickets.append(
                InspectionTicketResponse(
                    ticket_id=t_id,
                    meter_id=row["meter_id"],
                    evaluation_period=str(row.get("evaluation_period", "2016-10-30")),
                    tamper_probability=float(row.get("tamper_probability", 0.0)),
                    calibrated_probability=float(row.get("calibrated_probability", 0.0)),
                    estimated_leakage_kwh=float(row.get("estimated_leakage_kwh", 0.0)),
                    estimated_recoverable_revenue=float(
                        row.get("estimated_recoverable_revenue", 0.0)
                    ),
                    dispatch_cost=float(row.get("dispatch_cost", 500.0)),
                    expected_gross_recovery=float(row.get("expected_gross_recovery", 0.0)),
                    env=float(row.get("env", 0.0)),
                    tau_cost=float(row.get("tau_cost", 0.5)),
                    tau_env=float(row.get("tau_env", 0.5)),
                    active_threshold=float(row.get("active_threshold", 0.5)),
                    decision_rule=request.decision_rule,
                    inspection_recommended=bool(row.get("inspection_recommended", True)),
                    priority_rank=rank,
                    customer_type=str(row.get("customer_type", "standard")),
                    feeder_id=str(row.get("feeder_id", "unknown")),
                    data_quality_status=str(row.get("data_quality_status", "good")),
                    signatures_summary=str(
                        row.get("detected_signatures_summary", "Multivariate Feature Anomaly")
                    ),
                    explanation=exp_record,
                    safety_caveat=STANDARD_SAFETY_DISCLAIMER,
                )
            )

        total_recovery = sum(t.expected_gross_recovery for t in tickets)
        total_dispatch = sum(t.dispatch_cost for t in tickets)
        total_env = sum(t.env for t in tickets)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        return InspectionQueueResponse(
            queue_size=len(tickets),
            total_expected_recovery=round(total_recovery, 2),
            total_dispatch_cost=round(total_dispatch, 2),
            total_net_value=round(total_env, 2),
            decision_rule=request.decision_rule,
            tickets=tickets,
            processing_time_ms=elapsed_ms,
        )
