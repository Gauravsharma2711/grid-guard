/**
 * TypeScript contract interfaces for Grid-Guard FastAPI backend.
 * Derived strictly from backend Pydantic schemas in src/grid_guard/api/schemas.
 */

export interface HealthResponse {
  status: string;
  service: string;
  api_version: string;
}

export interface ReadyResponse {
  status: string;
  model_loaded: boolean;
  explainer_loaded: boolean;
  features_configured: boolean;
  model_version: string;
  feature_count: number;
  api_version: string;
}

export interface ModelMetadataResponse {
  model_version: string;
  feature_count: number;
  feature_names: string[];
  base_expected_value: number;
  objective: string;
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

export interface FinancialSummary {
  estimated_recovery: number;
  dispatch_cost: number;
  expected_gross_recovery?: number;
  expected_net_value: number;
  currency: string;
  decision_rule: string;
  threshold_used: number;
}

export interface DetectedSignature {
  signature_type: string;
  description: string;
  severity: 'low' | 'medium' | 'high';
  start_date?: string;
  end_date?: string;
}

export interface ShapContribution {
  feature_name: string;
  display_name: string;
  attribution_value: number;
  feature_value: number;
  direction: 'positive' | 'negative';
}

export interface SingleMeterPredictionResponse {
  meter_id: string;
  evaluation_date: string;
  tamper_probability: number;
  is_tampering_risk: boolean;
  dispatch_recommended: boolean;
  financial_summary: FinancialSummary;
  signatures: DetectedSignature[];
  shap_attributions?: ShapContribution[];
}

export interface InspectionTicketResponse {
  ticket_id: string;
  meter_id: string;
  created_at: string;
  tamper_probability: number;
  dispatch_recommended: boolean;
  financial_summary: FinancialSummary;
  detected_signatures: DetectedSignature[];
  narrative: string;
  verification_caveat: string;
}

export interface InspectionQueueItem {
  rank: number;
  ticket_id: string;
  meter_id: string;
  tamper_probability: number;
  estimated_recoverable_revenue: number;
  dispatch_cost: number;
  expected_net_value: number;
  decision: string;
  recommended: boolean;
  primary_signature?: string;
}

export interface InspectionQueueResponse {
  total_candidates: number;
  returned_count: number;
  ranking_criterion: string;
  items: InspectionQueueItem[];
}
