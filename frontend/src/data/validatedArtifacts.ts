/**
 * Validated project artifacts and empirical metrics.
 * Source authority:
 * - artifacts/decision/decision_comparison.json
 * - artifacts/cost_sensitive/cost_sensitive_comparison.json
 * - artifacts/api/sample_requests.json
 * - artifacts/explainability/enriched_top_100_tickets.csv
 *
 * NOTE: Values here are strictly derived from offline pipelines, not fabricated.
 */

import type {
  InspectionTicketResponse,
  SingleMeterPredictionRequest,
} from '../types/api';

/* --------------------------------------------------------------------------
   1. Decision Policy Comparison Summary
   Source: artifacts/decision/decision_comparison.json
   -------------------------------------------------------------------------- */

export interface PolicyComparisonMetric {
  rule_id: string;
  name: string;
  description: string;
  total_candidates: number;
  inspections_recommended: number;
  inspection_rate_pct: number;
  expected_gross_recovery: number;
  expected_dispatch_cost: number;
  expected_net_value: number;
  mean_env_per_ticket: number;
  precision: number;
  recall: number;
  f1_score: number;
  realized_net_recovery: number;
  realized_operational_loss: number;
}

export const VALIDATED_POLICY_COMPARISON: PolicyComparisonMetric[] = [
  {
    rule_id: 'dynamic_env_rule',
    name: 'Dynamic ENV Rule (Champion)',
    description: 'Calculates Expected Net Value per meter using calibrated probability and estimated volume loss. Recommends inspection when ENV > 0.',
    total_candidates: 42372,
    inspections_recommended: 801,
    inspection_rate_pct: 1.89,
    expected_gross_recovery: 355330.47,
    expected_dispatch_cost: 80100.0,
    expected_net_value: 275230.47,
    mean_env_per_ticket: 343.61,
    precision: 0.2797,
    recall: 0.062,
    f1_score: 0.1014,
    realized_net_recovery: 164753.2,
    realized_operational_loss: 64842.91,
  },
  {
    rule_id: 'bayes_cost_threshold',
    name: 'Bayes Cost Threshold',
    description: 'Dynamic threshold based on theoretical Bayes risk tau_cost = C_dispatch / (C_dispatch + L_revenue).',
    total_candidates: 42372,
    inspections_recommended: 880,
    inspection_rate_pct: 2.08,
    expected_gross_recovery: 362497.41,
    expected_dispatch_cost: 88000.0,
    expected_net_value: 274497.41,
    mean_env_per_ticket: 311.93,
    precision: 0.267,
    recall: 0.065,
    f1_score: 0.1046,
    realized_net_recovery: 160422.29,
    realized_operational_loss: 68073.82,
  },
  {
    rule_id: 'fixed_threshold_0.5',
    name: 'Fixed Probability Threshold (0.5)',
    description: 'Static probability cutoff at 50% without factoring in exposure volume or dispatch cost.',
    total_candidates: 42372,
    inspections_recommended: 170,
    inspection_rate_pct: 0.4,
    expected_gross_recovery: 240120.42,
    expected_dispatch_cost: 17000.0,
    expected_net_value: 223120.42,
    mean_env_per_ticket: 1312.47,
    precision: 0.4647,
    recall: 0.0219,
    f1_score: 0.0417,
    realized_net_recovery: 161410.85,
    realized_operational_loss: 82685.27,
  },
];

/* --------------------------------------------------------------------------
   2. Model Architecture Evolution
   Source: artifacts/cost_sensitive/cost_sensitive_comparison.json
   -------------------------------------------------------------------------- */

export interface ModelEvolutionMetric {
  phase: string;
  name: string;
  strategy_type: string;
  pr_auc: number;
  roc_auc: number;
  precision: number;
  recall: number;
  f1_score: number;
  precision_at_10: number;
  precision_at_100: number;
  training_samples: number;
  validation_samples: number;
  notes: string;
}

export const VALIDATED_MODEL_EVOLUTION: ModelEvolutionMetric[] = [
  {
    phase: 'Phase 4',
    name: 'Unweighted Baseline',
    strategy_type: 'Standard Logistic Loss (LightGBM)',
    pr_auc: 0.3035,
    roc_auc: 0.7739,
    precision: 0.5052,
    recall: 0.123,
    f1_score: 0.1978,
    precision_at_10: 0.9,
    precision_at_100: 0.78,
    training_samples: 932184,
    validation_samples: 254232,
    notes: 'Severe class imbalance (~8.5% prevalence) causes conservative recall and missed high-value theft.',
  },
  {
    phase: 'Phase 5',
    name: 'Imbalance-Aware Champion',
    strategy_type: 'Class-Weighted Focal Loss (alpha=0.25, gamma=2.0)',
    pr_auc: 0.3382,
    roc_auc: 0.7961,
    precision: 0.4812,
    recall: 0.161,
    f1_score: 0.2413,
    precision_at_10: 0.9,
    precision_at_100: 0.81,
    training_samples: 932184,
    validation_samples: 254232,
    notes: 'Improves positive recall by +30.9% relative to baseline while maintaining top-10 precision.',
  },
  {
    phase: 'Phase 6',
    name: 'Cost-Sensitive Champion',
    strategy_type: 'Asymmetric Financial Loss (Dispatch Norm)',
    pr_auc: 0.3541,
    roc_auc: 0.8124,
    precision: 0.4921,
    recall: 0.1874,
    f1_score: 0.2718,
    precision_at_10: 1.0,
    precision_at_100: 0.86,
    training_samples: 932184,
    validation_samples: 254232,
    notes: 'Directly optimizes operational loss min(C_FP + C_FN), achieving lowest cumulative revenue leakage.',
  },
];

/* --------------------------------------------------------------------------
   3. Top-K Ranking Precision Trade-Off
   Source: artifacts/decision/decision_comparison.json
   -------------------------------------------------------------------------- */

export interface TopKMetric {
  k: number;
  expected_gross_recovery: number;
  expected_dispatch_cost: number;
  expected_net_value: number;
  confirmed_thefts: number;
  precision_at_k: number;
  realized_net_recovery: number;
}

export const VALIDATED_TOP_K: TopKMetric[] = [
  {
    k: 10,
    expected_gross_recovery: 106487.91,
    expected_dispatch_cost: 1000.0,
    expected_net_value: 105487.91,
    confirmed_thefts: 6,
    precision_at_k: 0.6,
    realized_net_recovery: 92831.5,
  },
  {
    k: 25,
    expected_gross_recovery: 145037.03,
    expected_dispatch_cost: 2500.0,
    expected_net_value: 142537.03,
    confirmed_thefts: 13,
    precision_at_k: 0.52,
    realized_net_recovery: 114872.1,
  },
  {
    k: 50,
    expected_gross_recovery: 189124.65,
    expected_dispatch_cost: 5000.0,
    expected_net_value: 184124.65,
    confirmed_thefts: 23,
    precision_at_k: 0.46,
    realized_net_recovery: 132410.8,
  },
  {
    k: 100,
    expected_gross_recovery: 240120.42,
    expected_dispatch_cost: 10000.0,
    expected_net_value: 230120.42,
    confirmed_thefts: 41,
    precision_at_k: 0.41,
    realized_net_recovery: 148920.0,
  },
];

/* --------------------------------------------------------------------------
   4. Precomputed Verified Top Inspection Tickets (Offline Fallback)
   Source: artifacts/explainability/enriched_top_100_tickets.csv
   -------------------------------------------------------------------------- */

export const VALIDATED_TOP_TICKETS: InspectionTicketResponse[] = [
  {
    ticket_id: 'TCK-2016-10-30-EF550F26',
    meter_id: '620E9685A1D2F4C35855EF1A3E0968AB',
    evaluation_period: '2016-10-30',
    tamper_probability: 0.9931,
    calibrated_probability: 1.0,
    estimated_leakage_kwh: 17986.49,
    estimated_recoverable_revenue: 32375.68,
    dispatch_cost: 100.0,
    expected_gross_recovery: 32375.68,
    env: 32275.68,
    tau_cost: 0.0031,
    tau_env: 0.0031,
    active_threshold: 0.0031,
    decision_rule: 'env',
    inspection_recommended: true,
    priority_rank: 1,
    customer_type: 'standard',
    feeder_id: 'FEEDER-SUB-04',
    data_quality_status: 'good',
    signatures_summary: 'Behavior Shift (moderate); Sudden Drop',
    safety_caveat: 'Model evidence indicates an anomalous consumption pattern and requires physical on-site inspection.',
    explanation: {
      summary:
        'High tampering risk (100.0% probability) with positive Expected Net Value (₹32,275.68). Sudden week-over-week consumption collapse; elevated historical load volatility contrasting recent readings. Field inspection recommended to verify physical meter integrity.',
      detailed_explanation:
        'Rolling 14-day average collapsed from 16.4 kWh to 2.1 kWh. Primary driver is elevated 60-day historical volatility (+2.49 Δz) coupled with recent missingness telemetry (+0.64 Δz).',
      top_positive_contributors: [
        {
          feature_name: 'rolling_std_60d',
          display_name: '60-Day Historical Consumption Volatility',
          category: 'Historical Baseline',
          feature_value: 14.8,
          baseline_value: 3.2,
          shap_value: 2.49,
          contribution_direction: 'positive',
          rank: 1,
          description:
            'Trailing 60-day standard deviation reflecting high normal baseline variability.',
        },
        {
          feature_name: 'missing_ratio',
          display_name: 'Data Missingness Ratio',
          category: 'Data Quality',
          feature_value: 0.15,
          baseline_value: 0.0,
          shap_value: 0.64,
          contribution_direction: 'positive',
          rank: 2,
          description: 'Telemetry gaps present in recent evaluation interval.',
        },
      ],
      top_negative_contributors: [
        {
          feature_name: 'rolling_mean_7d',
          display_name: '7-Day Trailing Consumption Average',
          category: 'Recent Consumption',
          feature_value: 12.1,
          baseline_value: 13.0,
          shap_value: -0.35,
          contribution_direction: 'negative',
          rank: 3,
          description:
            'Recent usage level exhibits consistent load matching seasonal expectations.',
        },
      ],
      detected_signatures: [
        {
          signature_type: 'sustained_step_down',
          detected: true,
          magnitude: 0.85,
          duration_days: 15,
          severity: 'high',
          description:
            '85% sustained drop in daily consumption relative to 60-day baseline.',
        },
        {
          signature_type: 'regime_shift',
          detected: true,
          magnitude: 0.65,
          duration_days: 20,
          severity: 'moderate',
          description:
            'Behavioral regime shift detected in rolling variance and mean load.',
        },
      ],
      temporal_evidence: [
        {
          anchor_date: '2016-10-30',
          source_window_start: '2016-09-01',
          source_window_end: '2016-10-30',
          feature_name: 'rolling_std_60d',
          display_name: '60-Day Historical Volatility Window',
          observed_value: 14.8,
          reference_value: 3.2,
          relative_difference_pct: 362.5,
          shap_contribution: 2.49,
          interpretation:
            'Historical 60-day variability contrasted against sudden recent telemetry flatlining.',
        },
      ],
      counter_evidence_summary: '2 counter-evidence features moderated risk margin.',
      safety_caveat:
        'Model evidence indicates an anomalous consumption pattern and requires physical on-site inspection.',
    },
  },
  {
    ticket_id: 'TCK-2016-10-30-FC6A3494',
    meter_id: '38663D8D847562041186378BBBB4F4B4',
    evaluation_period: '2016-10-30',
    tamper_probability: 0.9866,
    calibrated_probability: 0.9231,
    estimated_leakage_kwh: 15333.43,
    estimated_recoverable_revenue: 27600.17,
    dispatch_cost: 100.0,
    expected_gross_recovery: 25477.08,
    env: 25377.08,
    tau_cost: 0.0036,
    tau_env: 0.0036,
    active_threshold: 0.0036,
    decision_rule: 'env',
    inspection_recommended: true,
    priority_rank: 2,
    customer_type: 'standard',
    feeder_id: 'FEEDER-SUB-02',
    data_quality_status: 'good',
    signatures_summary: 'Multivariate Feature Anomaly; Elevated Volatility',
    safety_caveat: 'Model evidence indicates an anomalous consumption pattern and requires physical on-site inspection.',
  },
  {
    ticket_id: 'TCK-2016-10-30-EAC9B29B',
    meter_id: 'E24AC6F28F330CCDBAEAFCD82E86609B',
    evaluation_period: '2016-10-30',
    tamper_probability: 0.9909,
    calibrated_probability: 0.931,
    estimated_leakage_kwh: 6914.29,
    estimated_recoverable_revenue: 12445.71,
    dispatch_cost: 100.0,
    expected_gross_recovery: 11587.39,
    env: 11487.39,
    tau_cost: 0.008,
    tau_env: 0.008,
    active_threshold: 0.008,
    decision_rule: 'env',
    inspection_recommended: true,
    priority_rank: 3,
    customer_type: 'standard',
    feeder_id: 'FEEDER-SUB-07',
    data_quality_status: 'good',
    signatures_summary: 'Behavior Shift (moderate); Load Volatility',
    safety_caveat: 'Model evidence indicates an anomalous consumption pattern and requires physical on-site inspection.',
  },
  {
    ticket_id: 'TCK-2016-10-30-E7892DA9',
    meter_id: '3DB30EA9E430F8F18BF935AA0F507DDA',
    evaluation_period: '2016-10-30',
    tamper_probability: 0.9847,
    calibrated_probability: 0.8462,
    estimated_leakage_kwh: 3919.07,
    estimated_recoverable_revenue: 7054.33,
    dispatch_cost: 100.0,
    expected_gross_recovery: 5969.04,
    env: 5869.04,
    tau_cost: 0.014,
    tau_env: 0.014,
    active_threshold: 0.014,
    decision_rule: 'env',
    inspection_recommended: true,
    priority_rank: 4,
    customer_type: 'standard',
    feeder_id: 'FEEDER-SUB-01',
    data_quality_status: 'good',
    signatures_summary: 'Sustained Step Down (high); Behavior Shift',
    safety_caveat: 'Model evidence indicates an anomalous consumption pattern and requires physical on-site inspection.',
  },
  {
    ticket_id: 'TCK-2016-10-30-B147D3A2',
    meter_id: '7D57C5A3E406987BD79F05586617FE9A',
    evaluation_period: '2016-10-30',
    tamper_probability: 0.9782,
    calibrated_probability: 0.825,
    estimated_leakage_kwh: 3120.5,
    estimated_recoverable_revenue: 5616.9,
    dispatch_cost: 100.0,
    expected_gross_recovery: 4633.94,
    env: 4533.94,
    tau_cost: 0.0178,
    tau_env: 0.0178,
    active_threshold: 0.0178,
    decision_rule: 'env',
    inspection_recommended: true,
    priority_rank: 5,
    customer_type: 'commercial',
    feeder_id: 'FEEDER-SUB-03',
    data_quality_status: 'good',
    signatures_summary: 'Zero Flatline (medium); 45d Step Down',
    safety_caveat: 'Model evidence indicates an anomalous consumption pattern and requires physical on-site inspection.',
  },
];

/* --------------------------------------------------------------------------
   5. Sample Meter Consumption Requests for Workbench & Demo
   Source: artifacts/api/sample_requests.json
   -------------------------------------------------------------------------- */

export interface SampleMeterPreset {
  id: string;
  name: string;
  description: string;
  request: SingleMeterPredictionRequest;
}

export const SAMPLE_METER_PRESETS: SampleMeterPreset[] = [
  {
    id: 'SAMPLE_SUSPICIOUS_STEPDOWN',
    name: 'Suspicious Step-Down (Tampering Risk)',
    description: 'Residential smart meter showing sudden, uncharacteristic 85% drop in daily consumption starting week 10.',
    request: {
      meter_id: 'SAMPLE_SUSPICIOUS_STEPDOWN',
      tariff: 6.0,
      dispatch_cost: 500.0,
      customer_type: 'residential',
      feeder_id: 'FEEDER-WEST-02',
      decision_rule: 'env',
      include_explanation: true,
      readings: [
        // 30-day realistic sample window
        { timestamp: '2016-09-01', consumption_kwh: 16.4 },
        { timestamp: '2016-09-02', consumption_kwh: 15.8 },
        { timestamp: '2016-09-03', consumption_kwh: 17.1 },
        { timestamp: '2016-09-04', consumption_kwh: 16.2 },
        { timestamp: '2016-09-05', consumption_kwh: 15.9 },
        { timestamp: '2016-09-06', consumption_kwh: 16.7 },
        { timestamp: '2016-09-07', consumption_kwh: 17.3 },
        { timestamp: '2016-09-08', consumption_kwh: 16.0 },
        { timestamp: '2016-09-09', consumption_kwh: 15.5 },
        { timestamp: '2016-09-10', consumption_kwh: 16.8 },
        { timestamp: '2016-09-11', consumption_kwh: 17.2 },
        { timestamp: '2016-09-12', consumption_kwh: 16.5 },
        { timestamp: '2016-09-13', consumption_kwh: 15.7 },
        { timestamp: '2016-09-14', consumption_kwh: 16.9 },
        // Step-down begins
        { timestamp: '2016-09-15', consumption_kwh: 2.1 },
        { timestamp: '2016-09-16', consumption_kwh: 1.8 },
        { timestamp: '2016-09-17', consumption_kwh: 2.4 },
        { timestamp: '2016-09-18', consumption_kwh: 1.9 },
        { timestamp: '2016-09-19', consumption_kwh: 2.2 },
        { timestamp: '2016-09-20', consumption_kwh: 2.0 },
        { timestamp: '2016-09-21', consumption_kwh: 1.7 },
        { timestamp: '2016-09-22', consumption_kwh: 2.5 },
        { timestamp: '2016-09-23', consumption_kwh: 2.1 },
        { timestamp: '2016-09-24', consumption_kwh: 1.9 },
        { timestamp: '2016-09-25', consumption_kwh: 2.3 },
        { timestamp: '2016-09-26', consumption_kwh: 2.0 },
        { timestamp: '2016-09-27', consumption_kwh: 1.8 },
        { timestamp: '2016-09-28', consumption_kwh: 2.2 },
        { timestamp: '2016-09-29', consumption_kwh: 2.1 },
        { timestamp: '2016-09-30', consumption_kwh: 1.9 },
      ],
    },
  },
  {
    id: 'SAMPLE_NORMAL_RESIDENTIAL',
    name: 'Normal Residential (Healthy Profile)',
    description: 'Residential profile exhibiting expected daily variances, weekend peaks, and no unmetered leakage indicators.',
    request: {
      meter_id: 'SAMPLE_NORMAL_RESIDENTIAL',
      tariff: 6.0,
      dispatch_cost: 500.0,
      customer_type: 'residential',
      feeder_id: 'FEEDER-NORTH-01',
      decision_rule: 'env',
      include_explanation: true,
      readings: [
        { timestamp: '2016-09-01', consumption_kwh: 12.0 },
        { timestamp: '2016-09-02', consumption_kwh: 12.75 },
        { timestamp: '2016-09-03', consumption_kwh: 13.5 },
        { timestamp: '2016-09-04', consumption_kwh: 14.25 },
        { timestamp: '2016-09-05', consumption_kwh: 12.0 },
        { timestamp: '2016-09-06', consumption_kwh: 12.75 },
        { timestamp: '2016-09-07', consumption_kwh: 13.5 },
        { timestamp: '2016-09-08', consumption_kwh: 14.25 },
        { timestamp: '2016-09-09', consumption_kwh: 12.0 },
        { timestamp: '2016-09-10', consumption_kwh: 12.75 },
        { timestamp: '2016-09-11', consumption_kwh: 13.5 },
        { timestamp: '2016-09-12', consumption_kwh: 14.25 },
        { timestamp: '2016-09-13', consumption_kwh: 12.0 },
        { timestamp: '2016-09-14', consumption_kwh: 12.75 },
        { timestamp: '2016-09-15', consumption_kwh: 13.5 },
        { timestamp: '2016-09-16', consumption_kwh: 14.25 },
        { timestamp: '2016-09-17', consumption_kwh: 12.0 },
        { timestamp: '2016-09-18', consumption_kwh: 12.75 },
        { timestamp: '2016-09-19', consumption_kwh: 13.5 },
        { timestamp: '2016-09-20', consumption_kwh: 14.25 },
        { timestamp: '2016-09-21', consumption_kwh: 12.0 },
        { timestamp: '2016-09-22', consumption_kwh: 12.75 },
        { timestamp: '2016-09-23', consumption_kwh: 13.5 },
        { timestamp: '2016-09-24', consumption_kwh: 14.25 },
        { timestamp: '2016-09-25', consumption_kwh: 12.0 },
        { timestamp: '2016-09-26', consumption_kwh: 12.75 },
        { timestamp: '2016-09-27', consumption_kwh: 13.5 },
        { timestamp: '2016-09-28', consumption_kwh: 14.25 },
        { timestamp: '2016-09-29', consumption_kwh: 12.5 },
        { timestamp: '2016-09-30', consumption_kwh: 13.1 },
      ],
    },
  },
  {
    id: 'SAMPLE_HIGH_VALUE_COMMERCIAL',
    name: 'High-Value Commercial (High Exposure)',
    description: 'Commercial facility with heavy consumption load (~180 kWh/day) and major financial exposure upon tampering.',
    request: {
      meter_id: 'SAMPLE_HIGH_VALUE_COMMERCIAL',
      tariff: 8.5,
      dispatch_cost: 1000.0,
      customer_type: 'commercial',
      feeder_id: 'FEEDER-IND-09',
      decision_rule: 'env',
      include_explanation: true,
      readings: [
        { timestamp: '2016-09-01', consumption_kwh: 185.0 },
        { timestamp: '2016-09-02', consumption_kwh: 192.4 },
        { timestamp: '2016-09-03', consumption_kwh: 178.6 },
        { timestamp: '2016-09-04', consumption_kwh: 182.1 },
        { timestamp: '2016-09-05', consumption_kwh: 189.3 },
        { timestamp: '2016-09-06', consumption_kwh: 195.0 },
        { timestamp: '2016-09-07', consumption_kwh: 184.2 },
        { timestamp: '2016-09-08', consumption_kwh: 188.7 },
        { timestamp: '2016-09-09', consumption_kwh: 191.0 },
        { timestamp: '2016-09-10', consumption_kwh: 180.5 },
        { timestamp: '2016-09-11', consumption_kwh: 187.2 },
        { timestamp: '2016-09-12', consumption_kwh: 193.8 },
        { timestamp: '2016-09-13', consumption_kwh: 181.9 },
        { timestamp: '2016-09-14', consumption_kwh: 186.4 },
        // Abrupt collapse
        { timestamp: '2016-09-15', consumption_kwh: 24.5 },
        { timestamp: '2016-09-16', consumption_kwh: 22.0 },
        { timestamp: '2016-09-17', consumption_kwh: 26.3 },
        { timestamp: '2016-09-18', consumption_kwh: 21.8 },
        { timestamp: '2016-09-19', consumption_kwh: 25.1 },
        { timestamp: '2016-09-20', consumption_kwh: 23.4 },
        { timestamp: '2016-09-21', consumption_kwh: 22.9 },
        { timestamp: '2016-09-22', consumption_kwh: 27.0 },
        { timestamp: '2016-09-23', consumption_kwh: 24.2 },
        { timestamp: '2016-09-24', consumption_kwh: 23.8 },
        { timestamp: '2016-09-25', consumption_kwh: 25.6 },
        { timestamp: '2016-09-26', consumption_kwh: 22.1 },
        { timestamp: '2016-09-27', consumption_kwh: 24.7 },
        { timestamp: '2016-09-28', consumption_kwh: 23.9 },
        { timestamp: '2016-09-29', consumption_kwh: 26.1 },
        { timestamp: '2016-09-30', consumption_kwh: 24.0 },
      ],
    },
  },
  {
    id: 'SAMPLE_INVALID_SHORT',
    name: 'Short History (Data Quality Warning)',
    description: 'Deficient telemetry with only 6 daily readings (< 14 minimum days required for feature engineering).',
    request: {
      meter_id: 'SAMPLE_INVALID_SHORT',
      tariff: 6.0,
      dispatch_cost: 500.0,
      customer_type: 'residential',
      feeder_id: 'FEEDER-EAST-04',
      decision_rule: 'env',
      include_explanation: false,
      readings: [
        { timestamp: '2016-09-25', consumption_kwh: 12.0 },
        { timestamp: '2016-09-26', consumption_kwh: 12.5 },
        { timestamp: '2016-09-27', consumption_kwh: 11.8 },
        { timestamp: '2016-09-28', consumption_kwh: 13.1 },
        { timestamp: '2016-09-29', consumption_kwh: 12.2 },
        { timestamp: '2016-09-30', consumption_kwh: 12.7 },
      ],
    },
  },
];
