"""
Tests for the backend health check endpoint.

Covers:
- /api/v1/rag/health endpoint returns 200 and expected payload
- Handles GET method only (405 for others)
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)

def test_health_check_ok():
    """GET /api/v1/rag/health returns 200 and expected JSON."""
    resp = client.get("/api/v1/rag/health")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert data.get("status") == "ok"
    assert "uptime" in data
    assert isinstance(data["uptime"], float)
    assert data.get("service") == "rag-backend"

def test_health_check_method_not_allowed():
    """POST/PUT/DELETE to /api/v1/rag/health returns 405."""
    for method in ("post", "put", "delete", "patch"):
        resp = getattr(client, method)("/api/v1/rag/health")
        assert resp.status_code == 405
        assert "detail" in resp.json()
