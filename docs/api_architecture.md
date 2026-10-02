# Grid-Guard — API Architecture & System Design

This document details the architectural design, lifecycle, dependency injection patterns, and request flows of the Grid-Guard FastAPI inference service.

---

## 1. System Architecture Overview

The Grid-Guard API is designed as a stateless, high-throughput microservice exposing the complete intelligence pipeline built across Phases 1–8. It adheres strictly to the principle of separation of concerns: routes contain zero algorithmic business logic, delegating completely to the domain and service layers.

```mermaid
flowchart TD
    Client(["HTTP Client / Field Terminal / Web UI"])
    
    subgraph FastAPI_Layer ["FastAPI Presentation Layer"]
        Middleware["Request ID & Logging Middleware<br/>(X-Request-ID, Latency)"]
        ExcHandlers["Centralized Exception Handlers<br/>(400, 422, 500, 503)"]
        Routers["Endpoint Routers<br/>/health, /ready, /metadata, /predict, /inspection"]
    end
    
    subgraph Service_Layer ["Application Service Layer (Singleton)"]
        InfService["InferenceService (Loaded once via Lifespan)"]
    end
    
    subgraph Domain_Pipelines ["Reusable Domain Engines (Phases 1-8)"]
        FeatPipe["FeaturePipeline (Phase 3)<br/>60 Temporal Features"]
        Booster["LightGBM Champion Booster (Phase 6)<br/>Cost-Sensitive Objective"]
        LeakageEst["LeakageEstimator & Prioritizer (Phases 4 & 7)<br/>Dynamic Thresholds & ENV"]
        Explainer["ShapExplainer & Signatures (Phase 8)<br/>Tree-SHAP & Narrative Generator"]
    end

    Client -->|HTTP Request| Middleware
    Middleware --> Routers
    Routers -->|Dependency Injection| InfService
    InfService --> FeatPipe
    InfService --> Booster
    InfService --> LeakageEst
    InfService --> Explainer
    InfService -->|Response Object| Routers
    Routers --> Middleware
    Middleware -->|HTTP JSON Response| Client
```

---

## 2. Application Lifecycle & In-Memory Model Pinning

ML model and explainer reloads are strictly prohibited during normal request handling. Loading large gradient-boosted decision tree structures and constructing TreeExplainer graphs incurs hundreds of milliseconds of initialization overhead.

### Lifespan Protocol
During the application startup phase (`@asynccontextmanager async def lifespan(app: FastAPI)`):
1. **Artifact Verification**: Verifies the existence of `artifacts/cost_sensitive/champion_model.txt`.
2. **Booster Initialization**: Loads the 60-feature LightGBM booster into RAM once.
3. **Explainer Construction**: Pre-computes the TreeExplainer graph and extracts the base expected margin value $\mathbb{E}[z] = -2.5928$.
4. **Domain Engine Attachment**: Binds `FeaturePipeline`, `LeakageEstimator`, `TamperingSignatureDetector`, and `TemporalAttributor`.
5. **Readiness Exposure**: Stores the `InferenceService` instance on `app.state.inference_service`.

If artifact loading fails, the service enters an explicit `unready` state and returns `HTTP 503 Service Unavailable` on prediction and readiness routes, preventing silent degradation.

---

## 3. Request Flow & Execution Pipeline

```mermaid
sequenceDiagram
    autonumber
    actor User as Client
    participant MW as Middleware (X-Request-ID)
    participant Route as Prediction Router
    participant Svc as InferenceService
    participant Feat as FeaturePipeline
    participant Model as LightGBM Champion
    participant Fin as Financial / Decision Engine
    participant SHAP as Tree-SHAP & Narratives

    User->>MW: POST /api/v1/predict
    MW->>Route: Validate JSON Schema
    Route->>Svc: predict_single(request)
    Svc->>Svc: Validate history (min 14d, max 730d)
    Svc->>Feat: transform(daily_readings_df)
    Feat-->>Svc: 60 Engineered Features
    Svc->>Model: predict(X, raw_score=True)
    Model-->>Svc: Raw Margin z = ln(p / (1 - p))
    Svc->>Svc: Sigmoid Probability p = 1 / (1 + exp(-z))
    Svc->>Fin: Calculate Deficit, Leakage Cost & ENV
    Fin-->>Svc: ENV, tau_cost, tau_env, active_threshold, decision
    opt If include_explanation == True
        Svc->>SHAP: explain(X) & detect_all(signatures)
        SHAP-->>Svc: Top SHAP drivers, signatures, temporal bounds, narratives
    end
    Svc-->>Route: SingleMeterPredictionResponse
    Route-->>MW: HTTP 200 OK + Payload
    MW-->>User: Response + Headers (X-Request-ID, X-Response-Time-Ms)
```

---

## 4. Error Handling & Security Model

1. **Uniform Error Schema**: All errors return a standardized `ErrorResponse` containing `error_type`, `message`, `details`, and `request_id`.
2. **Correlation Tracing**: Every inbound request receives an `X-Request-ID` (either client-supplied or generated via `req-{uuid[:12]}`) propagated through response headers and structured logs.
3. **Data Privacy**: Telemetry consumption arrays, tariffs, and account balances are strictly excluded from operational logs. Logs only record metadata (method, route, status code, latency, request ID).
4. **Input Sanitization**:
   - Pydantic models reject negative consumption values ($< 0.0$ kWh).
   - `NaN` and `$\pm\infty$` values trigger explicit 422 Unprocessable Content.
   - Timestamp duplicates are caught and rejected.
   - Bounded batch sizes (max 50) prevent resource starvation.

---

## 5. Performance Benchmarks Summary

Measured on local test environment with 90-day daily meter histories:

| Endpoint / Operation | Latency | Target |
| :--- | :---: | :---: |
| **Cold Startup Time** | **0.265 s** | < 2.0 s |
| **Prediction (Bare Inference)** | **21.87 ms** | < 50.0 ms |
| **Prediction (Full Tree-SHAP + Narratives)** | **29.14 ms** | < 80.0 ms |
| **Batch Prediction (10 meters)** | **250.12 ms** (25.0 ms/meter) | < 500.0 ms |
| **Inspection Ticket Generation** | **34.25 ms** | < 100.0 ms |
| **Inspection Queue Ranking Query** | **14.75 ms** | < 50.0 ms |
