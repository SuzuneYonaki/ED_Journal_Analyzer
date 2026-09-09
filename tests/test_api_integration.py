"""
API integration tests for Star Mapper.
"""

from fastapi.testclient import TestClient
from star_mapper.server.api import app

client = TestClient(app)


def test_api_status_endpoint():
    resp = client.get("/api/scan/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "current_radius" in data
    assert "total_systems" in data


def test_api_systems_sort_and_filter():
    resp = client.get("/api/scan/systems?sort_by=distance_asc&filter_disc=all")
    assert resp.status_code == 200
    data = resp.json()
    assert "count" in data
    assert "systems" in data


def test_api_export_csv():
    resp = client.get("/api/scan/export?format=csv&sort_by=distance_asc&filter_disc=all")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers.get("content-type", "")
    assert "System Name,Distance (ly)" in resp.text
