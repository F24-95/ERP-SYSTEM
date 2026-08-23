"""Tests for public health-check and open endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestPublicHealthCheck:
    async def test_health_check(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200

    async def test_root_endpoint(self, client: AsyncClient):
        resp = await client.get("/")
        assert resp.status_code in (200, 404)

    async def test_docs_endpoint(self, client: AsyncClient):
        resp = await client.get("/docs")
        assert resp.status_code in (200, 404)

    async def test_openapi_endpoint(self, client: AsyncClient):
        resp = await client.get("/openapi.json")
        assert resp.status_code in (200, 404)
