"""Lightweight performance benchmark for Grid-Guard FastAPI inference service."""

from __future__ import annotations

import statistics
import time
from datetime import date, timedelta

from fastapi.testclient import TestClient

from grid_guard.api.main import create_app


def run_benchmark() -> dict[str, float]:
    """Execute end-to-end benchmark measuring startup, single inference, SHAP explanation, and batch throughput."""
    print("=" * 60)
    print("GRID-GUARD API PERFORMANCE BENCHMARK")
    print("=" * 60)

    # 1. Cold Startup Latency
    t0 = time.perf_counter()
    app = create_app()
    with TestClient(app) as client:
        # Trigger startup lifespan
        _ = client.get("/health")
        cold_startup_sec = time.perf_counter() - t0
        print(f"Cold Startup Time (Lifespan + Model + Explainer): {cold_startup_sec:.3f} s")

        # Prepare synthetic 90-day time series
        readings_90d = [
            {
                "timestamp": str(date(2016, 8, 1) + timedelta(days=i)),
                "consumption_kwh": 12.0 + (i % 5),
            }
            for i in range(90)
        ]

        # 2. Warm Prediction Latency (Without Explanation)
        durations_no_exp: list[float] = []
        for _ in range(20):
            req = {
                "meter_id": "BENCH_FAST_01",
                "readings": readings_90d,
                "include_explanation": False,
            }
            t_req = time.perf_counter()
            res = client.post("/api/v1/predict", json=req)
            assert res.status_code == 200
            durations_no_exp.append((time.perf_counter() - t_req) * 1000.0)

        mean_fast = statistics.mean(durations_no_exp)
        median_fast = statistics.median(durations_no_exp)
        p95_fast = sorted(durations_no_exp)[int(len(durations_no_exp) * 0.95)]
        print(
            f"Prediction (No Explanation) - Mean: {mean_fast:.2f} ms | Median: {median_fast:.2f} ms | P95: {p95_fast:.2f} ms"
        )

        # 3. Warm Prediction Latency (With Full Tree-SHAP & Narrative)
        durations_with_exp: list[float] = []
        for _ in range(20):
            req = {
                "meter_id": "BENCH_EXPLAIN_01",
                "readings": readings_90d,
                "include_explanation": True,
            }
            t_req = time.perf_counter()
            res = client.post("/api/v1/predict", json=req)
            assert res.status_code == 200
            durations_with_exp.append((time.perf_counter() - t_req) * 1000.0)

        mean_exp = statistics.mean(durations_with_exp)
        median_exp = statistics.median(durations_with_exp)
        p95_exp = sorted(durations_with_exp)[int(len(durations_with_exp) * 0.95)]
        print(
            f"Prediction (Full Explanation) - Mean: {mean_exp:.2f} ms | Median: {median_exp:.2f} ms | P95: {p95_exp:.2f} ms"
        )

        # 4. Batch Prediction Latency (10 meters)
        batch_10_req = {
            "batch_id": "BENCH_BATCH_10",
            "meters": [
                {"meter_id": f"BATCH_MTR_{i:02d}", "readings": readings_90d} for i in range(10)
            ],
            "include_explanation": False,
        }
        t_b10 = time.perf_counter()
        res_b10 = client.post("/api/v1/predict/batch", json=batch_10_req)
        assert res_b10.status_code == 200
        batch_10_ms = (time.perf_counter() - t_b10) * 1000.0
        print(
            f"Batch (10 meters, No Exp) - Total: {batch_10_ms:.2f} ms | Per Meter: {batch_10_ms / 10.0:.2f} ms"
        )

        # 5. Inspection Ticket Latency
        t_tck = time.perf_counter()
        res_tck = client.post(
            "/api/v1/inspection/ticket", json={"meter_id": "TCK_BENCH", "readings": readings_90d}
        )
        assert res_tck.status_code == 200
        tck_ms = (time.perf_counter() - t_tck) * 1000.0
        print(f"Inspection Ticket Generation - Latency: {tck_ms:.2f} ms")

        # 6. Inspection Queue Query Latency
        t_q = time.perf_counter()
        res_q = client.post(
            "/api/v1/inspection/queue", json={"max_inspections": 50, "include_explanations": True}
        )
        assert res_q.status_code == 200
        q_ms = (time.perf_counter() - t_q) * 1000.0
        print(f"Inspection Queue Query (Top 50) - Latency: {q_ms:.2f} ms")

        print("=" * 60)
        return {
            "cold_startup_seconds": round(cold_startup_sec, 3),
            "fast_prediction_mean_ms": round(mean_fast, 2),
            "fast_prediction_p95_ms": round(p95_fast, 2),
            "explain_prediction_mean_ms": round(mean_exp, 2),
            "explain_prediction_p95_ms": round(p95_exp, 2),
            "batch_10_total_ms": round(batch_10_ms, 2),
            "batch_10_per_meter_ms": round(batch_10_ms / 10.0, 2),
            "ticket_generation_ms": round(tck_ms, 2),
            "queue_query_ms": round(q_ms, 2),
        }


if __name__ == "__main__":
    run_benchmark()
