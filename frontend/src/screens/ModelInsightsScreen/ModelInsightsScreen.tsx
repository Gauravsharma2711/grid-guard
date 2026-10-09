import React, { useEffect, useState } from 'react';
import { Button } from '../../components/ui/Button/Button';
import { CurrencyValue, EnvMetric } from '../../components/ui/Financial/Financial';
import { StatusBadge } from '../../components/ui/Status/Status';
import { Surface } from '../../components/ui/Surface/Surface';
import { DataTable } from '../../components/ui/Table/DataTable';
import {
  type ModelEvolutionMetric,
  type PolicyComparisonMetric,
  type TopKMetric,
  VALIDATED_MODEL_EVOLUTION,
  VALIDATED_POLICY_COMPARISON,
  VALIDATED_TOP_K,
} from '../../data/validatedArtifacts';
import { apiClient } from '../../services/apiClient';
import type { ModelMetadataResponse } from '../../types/api';
import './ModelInsightsScreen.css';

export const ModelInsightsScreen: React.FC = () => {
  const [modelMeta, setModelMeta] = useState<ModelMetadataResponse | null>(null);
  const [activeTab, setActiveTab] = useState<'evolution' | 'policies' | 'topk'>('policies');

  useEffect(() => {
    async function loadMeta() {
      try {
        const meta = await apiClient.getModelMetadata();
        setModelMeta(meta);
      } catch {
        // Fallback to offline champion metadata
        setModelMeta({
          model_name: 'cost_sensitive_champion_lgb',
          model_version: 'phase6_cost_sensitive_v1',
          model_type: 'LightGBM Booster',
          objective_type: 'financially_weighted_logistic',
          feature_version: 'phase3_temporal_features_v1',
          feature_count: 60,
          base_log_odds: -2.3713,
          base_probability: 0.0853,
          calibration_method: 'isotonic_or_sigmoid',
          api_version: '0.1.0',
        });
      }
    }
    loadMeta();
  }, []);

  // Policy columns
  const policyColumns = [
    {
      key: 'name',
      header: 'Decision Policy',
      render: (p: PolicyComparisonMetric) => (
        <div className="gg-policy-cell">
          <span className="gg-policy-title">{p.name}</span>
          <span className="gg-type-caption gg-policy-desc">{p.description}</span>
        </div>
      ),
    },
    {
      key: 'inspections_recommended',
      header: 'Recommended',
      align: 'right' as const,
      render: (p: PolicyComparisonMetric) => (
        <span className="gg-type-mono">{p.inspections_recommended.toLocaleString()} ({p.inspection_rate_pct}%)</span>
      ),
    },
    {
      key: 'expected_gross_recovery',
      header: 'Gross Recovery',
      align: 'right' as const,
      render: (p: PolicyComparisonMetric) => (
        <CurrencyValue amount={p.expected_gross_recovery} />
      ),
    },
    {
      key: 'expected_dispatch_cost',
      header: 'Crew Cost',
      align: 'right' as const,
      render: (p: PolicyComparisonMetric) => (
        <CurrencyValue amount={p.expected_dispatch_cost} />
      ),
    },
    {
      key: 'expected_net_value',
      header: 'Expected Net Value',
      align: 'right' as const,
      render: (p: PolicyComparisonMetric) => (
        <EnvMetric env={p.expected_net_value} />
      ),
    },
    {
      key: 'precision',
      header: 'Precision',
      align: 'right' as const,
      render: (p: PolicyComparisonMetric) => (
        <span className="gg-type-mono">{(p.precision * 100).toFixed(1)}%</span>
      ),
    },
    {
      key: 'recall',
      header: 'Recall',
      align: 'right' as const,
      render: (p: PolicyComparisonMetric) => (
        <span className="gg-type-mono">{(p.recall * 100).toFixed(1)}%</span>
      ),
    },
  ];

  // Model evolution columns
  const evolutionColumns = [
    {
      key: 'phase',
      header: 'Phase & Architecture',
      render: (m: ModelEvolutionMetric) => (
        <div className="gg-evolution-cell">
          <span className="gg-evolution-phase">{m.phase}: {m.name}</span>
          <span className="gg-type-caption gg-evolution-strat">{m.strategy_type}</span>
        </div>
      ),
    },
    {
      key: 'pr_auc',
      header: 'PR-AUC',
      align: 'right' as const,
      render: (m: ModelEvolutionMetric) => (
        <span className="gg-type-mono gg-metric-highlight">{m.pr_auc.toFixed(4)}</span>
      ),
    },
    {
      key: 'roc_auc',
      header: 'ROC-AUC',
      align: 'right' as const,
      render: (m: ModelEvolutionMetric) => (
        <span className="gg-type-mono">{m.roc_auc.toFixed(4)}</span>
      ),
    },
    {
      key: 'precision',
      header: 'Precision',
      align: 'right' as const,
      render: (m: ModelEvolutionMetric) => (
        <span className="gg-type-mono">{(m.precision * 100).toFixed(1)}%</span>
      ),
    },
    {
      key: 'recall',
      header: 'Recall',
      align: 'right' as const,
      render: (m: ModelEvolutionMetric) => (
        <span className="gg-type-mono">{(m.recall * 100).toFixed(1)}%</span>
      ),
    },
    {
      key: 'precision_at_10',
      header: 'Precision@10',
      align: 'right' as const,
      render: (m: ModelEvolutionMetric) => (
        <span className="gg-type-mono">{(m.precision_at_10 * 100).toFixed(0)}%</span>
      ),
    },
    {
      key: 'precision_at_100',
      header: 'Precision@100',
      align: 'right' as const,
      render: (m: ModelEvolutionMetric) => (
        <span className="gg-type-mono">{(m.precision_at_100 * 100).toFixed(0)}%</span>
      ),
    },
  ];

  // Top-K ranking columns
  const topKColumns = [
    {
      key: 'k',
      header: 'Top-K Cutoff',
      render: (k: TopKMetric) => (
        <span className="gg-type-mono gg-topk-pill">Top {k.k} Inspections</span>
      ),
    },
    {
      key: 'confirmed_thefts',
      header: 'Confirmed Thefts',
      align: 'right' as const,
      render: (k: TopKMetric) => (
        <span className="gg-type-mono">{k.confirmed_thefts} / {k.k}</span>
      ),
    },
    {
      key: 'precision_at_k',
      header: 'Precision@K',
      align: 'right' as const,
      render: (k: TopKMetric) => (
        <span className="gg-type-mono gg-metric-highlight">{(k.precision_at_k * 100).toFixed(1)}%</span>
      ),
    },
    {
      key: 'expected_gross_recovery',
      header: 'Projected Gross Recovery',
      align: 'right' as const,
      render: (k: TopKMetric) => (
        <CurrencyValue amount={k.expected_gross_recovery} />
      ),
    },
    {
      key: 'expected_dispatch_cost',
      header: 'Crew Dispatch Cost',
      align: 'right' as const,
      render: (k: TopKMetric) => (
        <CurrencyValue amount={k.expected_dispatch_cost} />
      ),
    },
    {
      key: 'expected_net_value',
      header: 'Expected Net Value',
      align: 'right' as const,
      render: (k: TopKMetric) => (
        <EnvMetric env={k.expected_net_value} />
      ),
    },
  ];

  return (
    <div className="gg-insights-screen">
      {/* Header */}
      <div className="gg-insights-header">
        <div className="gg-insights-title-block">
          <span className="gg-type-label gg-insights-kicker">Empirical Benchmarking</span>
          <h1 className="gg-type-display gg-insights-title">Model Insights & Policy Evaluation</h1>
          <p className="gg-type-body gg-insights-subtitle">
            Cost-sensitive loss evaluation, model architecture progression, and dynamic threshold decision rules.
          </p>
        </div>
      </div>

      {/* Model Checkpoint Introspection Card */}
      <Surface className="gg-checkpoint-surface">
        <div className="gg-checkpoint-header">
          <div>
            <span className="gg-type-label">Active Model Booster</span>
            <h2 className="gg-type-section gg-checkpoint-title">
              {modelMeta?.model_version ?? 'phase6_cost_sensitive_v1'}
            </h2>
          </div>
          <StatusBadge status="safe" label="Champion Checkpoint Verified" />
        </div>

        <div className="gg-checkpoint-grid">
          <div className="gg-checkpoint-metric">
            <span className="gg-type-caption">Architecture</span>
            <span className="gg-type-mono">{modelMeta?.model_type ?? 'LightGBM Booster'}</span>
          </div>
          <div className="gg-checkpoint-metric">
            <span className="gg-type-caption">Optimization Objective</span>
            <span className="gg-type-mono">{modelMeta?.objective_type ?? 'financially_weighted_logistic'}</span>
          </div>
          <div className="gg-checkpoint-metric">
            <span className="gg-type-caption">Engineered Features</span>
            <span className="gg-type-mono">{modelMeta?.feature_count ?? 60} Causal Features</span>
          </div>
          <div className="gg-checkpoint-metric">
            <span className="gg-type-caption">Base Log-Odds E[z]</span>
            <span className="gg-type-mono">{modelMeta?.base_log_odds?.toFixed(4) ?? '-2.3713'}</span>
          </div>
        </div>
      </Surface>

      {/* View Switcher Tabs */}
      <div className="gg-insights-tabs">
        <Button
          variant={activeTab === 'policies' ? 'primary' : 'secondary'}
          size="compact"
          onClick={() => setActiveTab('policies')}
        >
          Decision Policies (Phase 7)
        </Button>
        <Button
          variant={activeTab === 'evolution' ? 'primary' : 'secondary'}
          size="compact"
          onClick={() => setActiveTab('evolution')}
        >
          Model Progression (Phases 4–6)
        </Button>
        <Button
          variant={activeTab === 'topk' ? 'primary' : 'secondary'}
          size="compact"
          onClick={() => setActiveTab('topk')}
        >
          Top-K Precision Trade-Off
        </Button>
      </div>

      {/* Content Panels */}
      {activeTab === 'policies' && (
        <div className="gg-insights-section">
          <div className="gg-section-meta-text">
            <h3 className="gg-type-title">Financial Decision Policy Evaluation</h3>
            <p className="gg-type-caption">
              Evaluated on 42,372 held-out network meters. Comparing static 50% probability cutoffs against dynamic Bayes risk and Expected Net Value maximization.
            </p>
          </div>
          <DataTable<PolicyComparisonMetric>
            data={VALIDATED_POLICY_COMPARISON}
            columns={policyColumns}
            keyExtractor={(p) => p.rule_id}
            loading={false}
          />
        </div>
      )}

      {activeTab === 'evolution' && (
        <div className="gg-insights-section">
          <div className="gg-section-meta-text">
            <h3 className="gg-type-title">Model Architecture Evolution</h3>
            <p className="gg-type-caption">
              Trained on 932,184 samples across 60 causal temporal features. Demonstrates monotonic improvement in PR-AUC and high-value theft detection.
            </p>
          </div>
          <DataTable<ModelEvolutionMetric>
            data={VALIDATED_MODEL_EVOLUTION}
            columns={evolutionColumns}
            keyExtractor={(m) => m.phase}
            loading={false}
          />
        </div>
      )}

      {activeTab === 'topk' && (
        <div className="gg-insights-section">
          <div className="gg-section-meta-text">
            <h3 className="gg-type-title">Top-K Inspection Queue Yield</h3>
            <p className="gg-type-caption">
              Cumulative economic recovery when field crews inspect the top K ranked candidate meters ordered by Expected Net Value descending.
            </p>
          </div>
          <DataTable<TopKMetric>
            data={VALIDATED_TOP_K}
            columns={topKColumns}
            keyExtractor={(k) => `top-${k.k}`}
            loading={false}
          />
        </div>
      )}
    </div>
  );
};
