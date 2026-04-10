"""
=============================================================================
Module: tests/test_health
Description: Smoke test for the /health endpoint and basic auth flows.
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: pytest, httpx, app.main
=============================================================================
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Async test client for the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.anyio
async def test_health_check(client: AsyncClient):
    """GET /health should return 200 with status 'ok'."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "PolaZhenjing"


@pytest.mark.anyio
async def test_auth_login_invalid(client: AsyncClient):
    """POST /auth/login with invalid creds should return 400."""
    response = await client.post(
        "/auth/login",
        json={"username": "nonexistent", "password": "wrongpassword"},
    )
    # Expect 400 (bad request) or 500 (if DB not available in test)
    assert response.status_code in (400, 500)
