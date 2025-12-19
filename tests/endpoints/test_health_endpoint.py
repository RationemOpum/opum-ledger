# ruff: noqa: S101, D100, D101, D102, D103
"""Tests for health check endpoint."""

import pytest
from blacksheep.testing import TestClient


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Test health check endpoint."""

    async def test_healthz_returns_ok(self, api_client: TestClient):
        """Test that /healthz endpoint returns ok status."""
        response = await api_client.get("/healthz")

        assert response.status == 200
        data = await response.json()
        assert data == {"status": "ok"}
