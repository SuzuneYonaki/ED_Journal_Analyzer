import json
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from star_mapper.server.api import app
from star_mapper.services.mining_client import MiningClient

@pytest.fixture
def client():
    return TestClient(app)

MOCK_SPANSH_SEARCH_RESPONSE = {
    "count": 2,
    "results": [
        {
            "id": 1001,
            "name": "Col 285 Sector CC-K a38-2 1",
            "system_name": "Col 285 Sector CC-K a38-2",
            "distance": 42.5,
            "subtype": "Icy body",
            "reserve_level": "Pristine",
            "rings": [
                {
                    "name": "Ring A",
                    "type": "Icy",
                    "mass": 1000.0,
                    "signals": [
                        {"name": "Tritium", "count": 2},
                        {"name": "Low Temperature Diamond", "count": 1}
                    ]
                }
            ]
        },
        {
            "id": 1002,
            "name": "HIP 59425 2",
            "system_name": "HIP 59425",
            "distance": 89.1,
            "subtype": "High metal content world",
            "reserve_level": "Major",
            "rings": [
                {
                    "name": "Ring A",
                    "type": "Metallic",
                    "mass": 2500.0,
                    "signals": [
                        {"name": "Platinum", "count": 3}
                    ]
                }
            ]
        }
    ]
}

def test_mining_client_search():
    client_instance = MiningClient()
    
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(MOCK_SPANSH_SEARCH_RESPONSE).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        results = client_instance.search_mining_bodies(
            reference_system="Sol",
            max_distance=100.0,
            ring_type="Icy",
            ring_signal="Tritium",
            reserve_level="Pristine"
        )
        
        assert results["count"] == 2
        bodies = results["results"]
        assert len(bodies) == 2
        assert bodies[0]["system_name"] == "Col 285 Sector CC-K a38-2"
        assert bodies[0]["body_name"] == "Col 285 Sector CC-K a38-2 1"
        assert bodies[0]["distance"] == 42.5
        assert bodies[0]["reserve_level"] == "Pristine"
        assert any(h["name"] == "Tritium" for h in bodies[0]["hotspots"])
        assert any(r["type"] == "Icy" for r in bodies[0]["rings"])

def test_api_mining_search_endpoint(client):
    with patch("star_mapper.server.api.mining_client.search_mining_bodies") as mock_search:
        mock_search.return_value = {
            "count": 1,
            "results": [
                {
                    "id": 1001,
                    "system_name": "Col 285 Sector CC-K a38-2",
                    "body_name": "Col 285 Sector CC-K a38-2 1",
                    "distance": 42.5,
                    "subtype": "Icy body",
                    "reserve_level": "Pristine",
                    "rings": [{"name": "Ring A", "type": "Icy"}],
                    "hotspots": [{"name": "Tritium", "count": 2}]
                }
            ]
        }
        
        payload = {
            "reference_system": "Sol",
            "max_distance": 150.0,
            "ring_type": "Icy",
            "ring_signal": "Tritium",
            "reserve_level": "Pristine"
        }
        response = client.post("/api/mining/search", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["system_name"] == "Col 285 Sector CC-K a38-2"

def test_api_mining_export_csv(client):
    with patch("star_mapper.server.api.mining_client.search_mining_bodies") as mock_search:
        mock_search.return_value = {
            "count": 1,
            "results": [
                {
                    "id": 1001,
                    "system_name": "Col 285 Sector CC-K a38-2",
                    "body_name": "Col 285 Sector CC-K a38-2 1",
                    "distance": 42.5,
                    "subtype": "Icy body",
                    "reserve_level": "Pristine",
                    "rings": [{"name": "Ring A", "type": "Icy"}],
                    "hotspots": [{"name": "Tritium", "count": 2}]
                }
            ]
        }
        
        response = client.get("/api/mining/export?reference_system=Sol&max_distance=100")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        content = response.text
        assert "System Name" in content
        assert "Col 285 Sector CC-K a38-2" in content
        assert "Tritium x2" in content
        assert "Landable" in content

def test_mining_search_landable_with_ring(client):
    client_instance = MiningClient()
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({
            "count": 1,
            "results": [
                {
                    "id": 2001,
                    "name": "Luyten's Star 3 b",
                    "system_name": "Luyten's Star",
                    "distance": 12.3,
                    "is_landable": True,
                    "subtype": "Icy body",
                    "reserve_level": "Common",
                    "rings": [{"name": "3 b Ring", "type": "Icy"}],
                    "signals": []
                }
            ]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Test searching Landable has Ring (any_ring + is_landable=True)
        results = client_instance.search_mining_bodies(
            reference_system="Sol",
            max_distance=50.0,
            ring_type="any_ring",
            is_landable=True
        )
        assert results["count"] == 1
        b = results["results"][0]
        assert b["body_name"] == "Luyten's Star 3 b"
        assert b["is_landable"] is True
        assert len(b["rings"]) == 1


