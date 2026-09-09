"""
Test for verifying fix of TypeError when bodyCount or other fields are None.
"""

from star_mapper.services.edsm_client import EDSMClient
from star_mapper.services.mapper_service import mapper_service
from fastapi.testclient import TestClient
from star_mapper.server.api import app


def test_edsm_client_safe_parsing_null_bodycount():
    client = EDSMClient()
    # Mock response from EDSM containing None for bodyCount, coords, distance, etc.
    mock_data = [
        {
            "name": "System With Nulls",
            "id64": 1111111111,
            "distance": None,
            "coords": {"x": 1.23, "y": None, "z": 4.56},
            "bodyCount": None,
            "information": {}
        },
        {
            "name": "System With String BodyCount",
            "id64": "2222222222",
            "distance": 5.5,
            "coords": {"x": "10.0", "y": "20.0", "z": "30.0"},
            "bodyCount": "15",
            "information": {}
        }
    ]

    # Monkey patch _http_get_json
    client._http_get_json = lambda url, timeout=12.0: mock_data

    results = client.get_sphere_systems("Sol", 0, 10)
    assert len(results) == 2

    # Verify first system with None fields
    s1 = results[0]
    assert s1["name"] == "System With Nulls"
    assert s1["distance"] == 0.0
    assert s1["pos_x"] == 1.23
    assert s1["pos_y"] is None
    assert s1["pos_z"] == 4.56
    assert s1["body_count"] == 0

    # Verify second system with string fields
    s2 = results[1]
    assert s2["name"] == "System With String BodyCount"
    assert s2["distance"] == 5.5
    assert s2["pos_x"] == 10.0
    assert s2["pos_y"] == 20.0
    assert s2["pos_z"] == 30.0
    assert s2["body_count"] == 15


def test_api_step_scan_with_params():
    api_client = TestClient(app)
    resp = api_client.post("/api/scan/step", json={
        "center_system": "Sol",
        "step_ly": 2.5,
        "max_ly": 5.0,
        "delay_sec": 1.0,
        "source_mode": "edsm"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
