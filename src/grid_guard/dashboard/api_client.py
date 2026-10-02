"""API Client for the Grid-Guard Streamlit Dashboard.

Interfaces exclusively with the FastAPI backend application boundary.
Zero direct machine-learning or feature pipeline module imports.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DEFAULT_API_BASE_URL = os.getenv("GRID_GUARD_API_URL", "http://localhost:8000")
DEFAULT_TIMEOUT_SECONDS = float(os.getenv("GRID_GUARD_API_TIMEOUT", "25.0"))


class DashboardApiError(Exception):
    """Structured error raised when an API request fails."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        detail: str | None = None,
        is_connection_error: bool = False,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.detail = detail
        self.is_connection_error = is_connection_error


class DashboardApiClient:
    """Client for querying the Grid-Guard FastAPI backend service."""

    def __init__(
        self,
        base_url: str = DEFAULT_API_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._custom_client = client

    def _get_client(self) -> tuple[httpx.Client, bool]:
        """Return an active client and a boolean indicating whether it should be closed."""
        if self._custom_client is not None:
            return self._custom_client, False
        return httpx.Client(base_url=self.base_url, timeout=self.timeout), True

    def check_health(self) -> dict[str, Any]:
        """Query liveness probe endpoint."""
        client, should_close = self._get_client()
        try:
            resp = client.get("/health")
            resp.raise_for_status()
            return resp.json()
        except httpx.ConnectError as e:
            raise DashboardApiError(
                f"Grid-Guard API is unavailable at {self.base_url}.",
                is_connection_error=True,
            ) from e
        except httpx.TimeoutException as e:
            raise DashboardApiError(
                "Health check request timed out.",
                is_connection_error=True,
            ) from e
        except httpx.HTTPStatusError as e:
            raise DashboardApiError(
                f"Health check failed with HTTP {e.response.status_code}",
                status_code=e.response.status_code,
                detail=e.response.text,
            ) from e
        finally:
            if should_close:
                client.close()

    def check_ready(self) -> dict[str, Any]:
        """Query readiness probe endpoint."""
        client, should_close = self._get_client()
        try:
            resp = client.get("/ready")
            if resp.status_code == 503:
                return {
                    "status": "unready",
                    "model_loaded": False,
                    "explainer_loaded": False,
                    "features_configured": False,
                    "model_version": "unknown",
                    "feature_count": 0,
                }
            resp.raise_for_status()
            return resp.json()
        except httpx.ConnectError as e:
            raise DashboardApiError(
                f"Grid-Guard API is unavailable at {self.base_url}.",
                is_connection_error=True,
            ) from e
        except httpx.TimeoutException as e:
            raise DashboardApiError(
                "Readiness probe request timed out.",
                is_connection_error=True,
            ) from e
        except httpx.HTTPStatusError as e:
            raise DashboardApiError(
                f"Readiness check failed with HTTP {e.response.status_code}",
                status_code=e.response.status_code,
                detail=e.response.text,
            ) from e
        finally:
            if should_close:
                client.close()

    def get_model_metadata(self) -> dict[str, Any]:
        """Query model metadata introspection endpoint."""
        client, should_close = self._get_client()
        try:
            resp = client.get("/api/v1/metadata/model")
            resp.raise_for_status()
            return resp.json()
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            raise DashboardApiError(
                "Unable to retrieve model metadata from API.",
                is_connection_error=True,
            ) from e
        except httpx.HTTPStatusError as e:
            raise DashboardApiError(
                f"Model metadata query failed with HTTP {e.response.status_code}",
                status_code=e.response.status_code,
                detail=e.response.text,
            ) from e
        finally:
            if should_close:
                client.close()

    def get_public_config(self) -> dict[str, Any]:
        """Query public configuration endpoint."""
        client, should_close = self._get_client()
        try:
            resp = client.get("/api/v1/metadata/config")
            resp.raise_for_status()
            return resp.json()
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            raise DashboardApiError(
                "Unable to retrieve configuration from API.",
                is_connection_error=True,
            ) from e
        except httpx.HTTPStatusError as e:
            raise DashboardApiError(
                f"Config query failed with HTTP {e.response.status_code}",
                status_code=e.response.status_code,
                detail=e.response.text,
            ) from e
        finally:
            if should_close:
                client.close()

    def predict_single(
        self,
        meter_id: str,
        readings: list[dict[str, Any]],
        tariff_per_kwh: float | None = None,
        dispatch_cost: float | None = None,
        decision_rule: str = "env",
        include_explanation: bool = True,
    ) -> dict[str, Any]:
        """Run single-meter prediction and financial assessment."""
        payload: dict[str, Any] = {
            "meter_id": meter_id,
            "readings": readings,
            "decision_rule": decision_rule,
            "include_explanation": include_explanation,
        }
        if tariff_per_kwh is not None:
            payload["tariff_per_kwh"] = tariff_per_kwh
        if dispatch_cost is not None:
            payload["dispatch_cost"] = dispatch_cost

        client, should_close = self._get_client()
        try:
            resp = client.post("/api/v1/predict", json=payload)
            if resp.status_code == 400:
                detail = resp.json().get("detail", "Bad Request")
                raise DashboardApiError(f"Prediction input error: {detail}", status_code=400)
            if resp.status_code == 503:
                raise DashboardApiError("Prediction service is not ready.", status_code=503)
            resp.raise_for_status()
            return resp.json()
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            raise DashboardApiError(
                "Prediction request failed: API connection unavailable or timed out.",
                is_connection_error=True,
            ) from e
        except httpx.HTTPStatusError as e:
            raise DashboardApiError(
                f"Prediction API error ({e.response.status_code}): {e.response.text}",
                status_code=e.response.status_code,
                detail=e.response.text,
            ) from e
        finally:
            if should_close:
                client.close()

    def generate_ticket(
        self,
        meter_id: str,
        readings: list[dict[str, Any]],
        tariff_per_kwh: float | None = None,
        dispatch_cost: float | None = None,
        decision_rule: str = "env",
        include_explanation: bool = True,
    ) -> dict[str, Any]:
        """Generate field inspection ticket with full explainability."""
        payload: dict[str, Any] = {
            "meter_id": meter_id,
            "readings": readings,
            "decision_rule": decision_rule,
            "include_explanation": include_explanation,
        }
        if tariff_per_kwh is not None:
            payload["tariff_per_kwh"] = tariff_per_kwh
        if dispatch_cost is not None:
            payload["dispatch_cost"] = dispatch_cost

        client, should_close = self._get_client()
        try:
            resp = client.post("/api/v1/inspection/ticket", json=payload)
            if resp.status_code == 400:
                detail = resp.json().get("detail", "Bad Request")
                raise DashboardApiError(f"Ticket input error: {detail}", status_code=400)
            if resp.status_code == 503:
                raise DashboardApiError("Prediction service is not ready.", status_code=503)
            resp.raise_for_status()
            return resp.json()
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            raise DashboardApiError(
                "Ticket generation request failed: API connection unavailable or timed out.",
                is_connection_error=True,
            ) from e
        except httpx.HTTPStatusError as e:
            raise DashboardApiError(
                f"Inspection ticket API error ({e.response.status_code}): {e.response.text}",
                status_code=e.response.status_code,
                detail=e.response.text,
            ) from e
        finally:
            if should_close:
                client.close()

    def get_inspection_queue(
        self,
        max_inspections: int = 50,
        decision_rule: str = "env",
        min_env: float = 0.0,
        min_probability: float = 0.5,
        include_explanations: bool = True,
    ) -> dict[str, Any]:
        """Fetch prioritized field inspection queue ranked by ENV descending."""
        payload = {
            "max_inspections": max_inspections,
            "decision_rule": decision_rule,
            "min_env": min_env,
            "min_probability": min_probability,
            "include_explanations": include_explanations,
        }
        client, should_close = self._get_client()
        try:
            resp = client.post("/api/v1/inspection/queue", json=payload)
            resp.raise_for_status()
            return resp.json()
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            raise DashboardApiError(
                "Inspection queue query failed: API connection unavailable or timed out.",
                is_connection_error=True,
            ) from e
        except httpx.HTTPStatusError as e:
            raise DashboardApiError(
                f"Queue API error ({e.response.status_code}): {e.response.text}",
                status_code=e.response.status_code,
                detail=e.response.text,
            ) from e
        finally:
            if should_close:
                client.close()
