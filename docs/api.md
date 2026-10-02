# Grid-Guard — REST API Reference & User Guide

The **Grid-Guard REST API** exposes trained machine-learning models, financial Expected Net Value (ENV) decisioning, and Tree-SHAP explainability through high-performance HTTP endpoints.

---

## 1. Quickstart & Server Launch

The server can be launched using the pre-configured runner script or standard ASGI CLI:

```bash
# Option A: Standard CLI Runner
uv run python scripts/run_api.py --host 0.0.0.0 --port 8000

# Option B: Direct Uvicorn invocation
uv run uvicorn grid_guard.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Interactive Documentation
Once started, interactive API documentation is available at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc UI**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## 2. Endpoint Catalog

| Method | Path | Summary | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Process Liveness | Confirms application process is running. |
| `GET` | `/ready` | Service Readiness | Validates model booster and explainer in memory. |
| `GET` | `/api/v1/metadata/model` | Model Introspection | Returns model version, base expected value, feature count. |
| `GET` | `/api/v1/metadata/config` | Public Config | Returns supported policies, input limits, financial defaults. |
| `POST` | `/api/v1/predict` | Single Meter Inference | Ingests time series, scores risk, calculates ENV, runs SHAP. |
| `POST` | `/api/v1/predict/batch` | Batch Inference | Synchronously processes up to 50 meters with partial error handling. |
| `POST` | `/api/v1/inspection/ticket` | Ticket Generation | Compiles full field inspection work order with evidence. |
| `POST` | `/api/v1/inspection/queue` | Prioritized Queue | Returns top candidate tickets ranked by ENV descending. |

---

## 3. Request & Response Examples

### A. Evaluate Single Meter (`POST /api/v1/predict`)

#### Request
```json
{
  "meter_id": "CONS_923838E7",
  "readings": [
    {"timestamp": "2016-08-01", "consumption_kwh": 28.5},
    {"timestamp": "2016-08-02", "consumption_kwh": 27.8},
    {"timestamp": "2016-10-30", "consumption_kwh": 1.4}
  ],
  "tariff": 6.5,
  "customer_type": "residential",
  "decision_rule": "env",
  "include_explanation": true
}
```

#### Response (`HTTP 200 OK`)
```json
{
  "meter_id": "CONS_923838E7",
  "evaluation_timestamp": "2016-10-30",
  "model": {
    "model_name": "cost_sensitive_champion_lgb",
    "model_version": "phase6_cost_sensitive_v1",
    "feature_count": 60,
    "base_log_odds": -2.5928
  },
  "data_quality": {
    "coverage_ratio": 1.0,
    "missing_ratio": 0.0,
    "total_readings": 91,
    "status": "good",
    "warnings": []
  },
  "prediction": {
    "raw_score": 3.8412,
    "tamper_probability": 0.9792,
    "calibrated_probability": 0.9792,
    "prediction_label": 1
  },
  "financial": {
    "estimated_leakage_kwh": 780.0,
    "estimated_recoverable_revenue": 60840.0,
    "expected_gross_recovery": 59574.53,
    "dispatch_cost": 500.0,
    "expected_net_value": 59074.53,
    "tariff": 6.5,
    "currency": "INR"
  },
  "decision": {
    "decision_rule": "env",
    "active_threshold": 0.0082,
    "tau_cost": 0.0081,
    "tau_env": 0.0082,
    "inspection_recommended": true,
    "priority_context": "Inspection recommended with positive Expected Net Value of $59,074.53"
  },
  "explanation": {
    "summary": "High tampering risk (97.9% probability) with positive Expected Net Value ($59,074.53). Sustained consumption drop of 94% below baseline. Field inspection recommended to verify physical meter integrity.",
    "detailed_explanation": "### Inspection Explanation: Ticket TCK-2016-10-30-EF550F26...",
    "detected_signatures": [
      {
        "signature_type": "sustained_step_down",
        "detected": true,
        "magnitude": 0.94,
        "severity": "high",
        "description": "Consumption dropped 94.0% below 60-day baseline for 30 consecutive days."
      }
    ],
    "top_positive_contributors": [
      {
        "feature_name": "rolling_std_60d",
        "display_name": "60-Day Load Volatility",
        "shap_value": 2.485,
        "contribution_direction": "positive"
      }
    ],
    "safety_caveat": "Model evidence reflects statistical consumption anomalies and requires physical field verification."
  },
  "processing_time_ms": 31.45
}
```

---

### B. Generate Inspection Work Order Ticket (`POST /api/v1/inspection/ticket`)

```bash
curl -X POST "http://localhost:8000/api/v1/inspection/ticket" \
     -H "Content-Type: application/json" \
     -d @artifacts/api/sample_requests.json
```

---

## 4. Input Constraints & Validation Rules

1. **Daily Cadence**: Telemetry readings must represent consecutive daily electricity consumption in kilowatt-hours.
2. **History Bounds**:
   - Minimum readings: **14 days** (HTTP 400 returned if $< 14$).
   - Recommended readings: **90 days** (sub-90d returns a descriptive data-quality warning).
   - Maximum readings: **730 days** (2 years).
3. **Data Integrity**:
   - Negative consumption is strictly forbidden and rejected via HTTP 422.
   - Non-finite values (`NaN`, `$\pm\infty$`) are rejected via HTTP 422.
   - Duplicate calendar dates are rejected.
4. **Batch Limits**: Bounded to **50 meters** per request.

---

## 5. Standard Error Format

All error responses adhere to the unified schema:

```json
{
  "error_type": "ValidationError",
  "message": "Request schema validation failed.",
  "details": [
    {
      "loc": ["body", "readings", 2, "consumption_kwh"],
      "msg": "consumption_kwh must be non-negative, got -5.0.",
      "type": "value_error"
    }
  ],
  "request_id": "req-9b81f4a1c0d2"
}
```
