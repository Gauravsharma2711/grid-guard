"""Unit tests for DashboardApiClient."""

from __future__ import annotations

import httpx
import pytest

from grid_guard.dashboard.api_client import DashboardApiClient, DashboardApiError


def test_api_client_initialization() -> None:
    """Verify default client parameters."""
    client = DashboardApiClient(base_url="http://custom-host:9000", timeout=12.5)
    assert client.base_url == "http://custom-host:9000"
    assert client.timeout == 12.5


def test_api_client_connection_error() -> None:
    """Verify handling of unreachable API server."""
    client = DashboardApiClient(base_url="http://127.0.0.1:59999", timeout=0.5)
    with pytest.raises(DashboardApiError) as exc_info:
        client.check_health()

    assert exc_info.value.is_connection_error is True
    msg = exc_info.value.message.lower()
    assert "unavailable" in msg or "timed out" in msg


def test_api_client_mock_health() -> None:
    """Verify health probe parsing with mock transport."""

    def mock_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/health":
            return httpx.Response(
                200, json={"status": "ok", "service": "grid-guard-api", "api_version": "1.0.0"}
            )
        return httpx.Response(404)

    mock_client = httpx.Client(base_url="http://test", transport=httpx.MockTransport(mock_handler))
    client = DashboardApiClient(base_url="http://test", client=mock_client)

    res = client.check_health()
    assert res["status"] == "ok"
    assert res["service"] == "grid-guard-api"


def test_api_client_mock_ticket_error() -> None:
    """Verify 400 Bad Request error detail parsing."""

    def mock_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v1/inspection/ticket":
            return httpx.Response(
                400, json={"detail": "Insufficient historical readings: provided 10, required 30"}
            )
        return httpx.Response(404)

    mock_client = httpx.Client(base_url="http://test", transport=httpx.MockTransport(mock_handler))
    client = DashboardApiClient(base_url="http://test", client=mock_client)

    with pytest.raises(DashboardApiError) as exc_info:
        client.generate_ticket(meter_id="TEST", readings=[])

    assert exc_info.value.status_code == 400
    assert "Insufficient historical readings" in exc_info.value.message
