/**
 * TypeScript type definitions mirroring FastAPI Pydantic models.
 * Authority: src/grid_guard/api/schemas/
 */

/* --------------------------------------------------------------------------
   1. System Health & Readiness Schemas
   -------------------------------------------------------------------------- */

export interface HealthResponse {
  status: string;
  service: string;
  api_version: string;
}

export interface ReadyResponse {
  status: 'ready' | 'unready' | string;
  model_loaded: boolean;
  explainer_loaded: boolean;
  features_configured: boolean;
  model_version: string;
  feature_count: number;
  api_version: string;
}

/* --------------------------------------------------------------------------
   2. Model & Public Metadata Schemas
   -------------------------------------------------------------------------- */

export interface ModelMetadataResponse {
  model_name: string;
  model_version: string;
  model_type: string;
  objective_type: string;
  feature_version: string;
  feature_count: number;
  base_log_odds: number;
  base_probability: number;
  calibration_method: string;
  api_version: string;
}

export interface PublicConfigResponse {
  api_version: string;
  input_cadence: string;
  limits: {
    min_readings_per_meter: number;
    max_readings_per_meter: number;
    recommended_readings_per_meter: number;
    max_batch_size: number;
  };
  financial_defaults: {
    default_tariff: number;
    default_dispatch_cost: number;
    currency: string;
    recovery_factor: number;
    undetected_cycles: number;
  };
  supported_decision_rules: string[];
  default_decision_rule: string;
  feature_categories: string[];
}

export interface DataQualitySummary {
  coverage_ratio: number;
  missing_ratio: number;
  imputation_ratio: number;
  total_readings: number;
  history_days: number;
  status: 'good' | 'adequate' | 'insufficient_history' | string;
  warnings: string[];
}

/* --------------------------------------------------------------------------
   3. Single Meter Prediction & Time-Series Schemas
   -------------------------------------------------------------------------- */

export interface MeterReading {
  timestamp: string;
  consumption_kwh: number;
}

export interface SingleMeterPredictionRequest {
  meter_id: string;
  readings: MeterReading[];
  evaluation_date?: string | null;
  tariff?: number | null;
  customer_type?: string;
  feeder_id?: string;
  dispatch_cost?: number | null;
  decision_rule?: 'env' | 'cost_threshold' | 'fixed_threshold' | string;
  fixed_threshold?: number;
  include_explanation?: boolean;
}

export interface PredictionOutput {
  raw_score: number;
  tamper_probability: number;
  calibrated_probability: number;
  prediction_label: number;
}

export interface FinancialOutput {
  estimated_leakage_kwh: number;
  estimated_recoverable_revenue: number;
  expected_gross_recovery: number;
  dispatch_cost: number;
  expected_net_value: number;
  tariff: number;
  currency: string;
}

export interface DecisionOutput {
  decision_rule: string;
  active_threshold: number;
  tau_cost: number;
  tau_env: number;
  inspection_recommended: boolean;
  priority_context?: string | null;
}

export interface FeatureContributionSchema {
  feature_name: string;
  display_name: string;
  category: string;
  feature_value: number;
  baseline_value?: number | null;
  shap_value: number;
  contribution_direction: 'positive' | 'negative' | string;
  rank: number;
  description: string;
}

export interface TamperingSignatureSchema {
  signature_type: string;
  detected: boolean;
  magnitude: number;
  duration_days?: number | null;
  severity: string;
  description: string;
}

export interface TemporalEvidenceSchema {
  anchor_date: string;
  source_window_start: string;
  source_window_end: string;
  feature_name: string;
  display_name: string;
  observed_value: number;
  reference_value?: number | null;
  relative_difference_pct?: number | null;
  shap_contribution: number;
  interpretation: string;
}

export interface ExplanationOutput {
  summary: string;
  detailed_explanation: string;
  top_positive_contributors: FeatureContributionSchema[];
  top_negative_contributors: FeatureContributionSchema[];
  detected_signatures: TamperingSignatureSchema[];
  temporal_evidence: TemporalEvidenceSchema[];
  counter_evidence_summary?: string | null;
  safety_caveat: string;
}

export interface SingleMeterPredictionResponse {
  meter_id: string;
  evaluation_timestamp: string;
  model: ModelMetadataResponse;
  data_quality: DataQualitySummary;
  prediction: PredictionOutput;
  financial: FinancialOutput;
  decision: DecisionOutput;
  explanation?: ExplanationOutput | null;
  processing_time_ms: number;
}

/* --------------------------------------------------------------------------
   4. Multi-Meter Batch Prediction Schemas
   -------------------------------------------------------------------------- */

export interface BatchItemError {
  meter_id: string;
  error: string;
  error_type: string;
}

export interface BatchPredictionRequest {
  meters: SingleMeterPredictionRequest[];
  batch_id?: string | null;
  include_explanation?: boolean;
}

export interface BatchPredictionResponse {
  batch_id: string;
  total_items: number;
  successful_items: number;
  failed_items: number;
  results: SingleMeterPredictionResponse[];
  errors: BatchItemError[];
  processing_time_ms: number;
}

/* --------------------------------------------------------------------------
   5. Inspection Ticket & Prioritized Queue Schemas
   -------------------------------------------------------------------------- */

export interface InspectionTicketResponse {
  ticket_id: string;
  meter_id: string;
  evaluation_period: string;
  tamper_probability: number;
  calibrated_probability: number;
  estimated_leakage_kwh: number;
  estimated_recoverable_revenue: number;
  dispatch_cost: number;
  expected_gross_recovery: number;
  env: number;
  tau_cost: number;
  tau_env: number;
  active_threshold: number;
  decision_rule: string;
  inspection_recommended: boolean;
  priority_rank?: number | null;
  customer_type: string;
  feeder_id: string;
  data_quality_status: string;
  signatures_summary: string;
  explanation?: ExplanationOutput | null;
  safety_caveat: string;
}

export interface InspectionQueueRequest {
  max_inspections?: number;
  decision_rule?: string;
  min_env?: number;
  min_probability?: number;
  include_explanations?: boolean;
}

export interface InspectionQueueResponse {
  queue_size: number;
  total_expected_recovery: number;
  total_dispatch_cost: number;
  total_net_value: number;
  decision_rule: string;
  tickets: InspectionTicketResponse[];
  processing_time_ms: number;
}
