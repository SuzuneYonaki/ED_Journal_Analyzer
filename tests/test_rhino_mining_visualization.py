import pytest
import sqlite3
from fastapi.testclient import TestClient
from app.server.api import app, extract_rhino_mining_sites
from app.db.database import init_db, get_db_connection

client = TestClient(app)

def test_extract_rhino_mining_sites_filters_materials_and_counts():
    raw_activities = [
        {
            "system_address": 1001,
            "body_id": 1,
            "body_name": "Body A",
            "material_name": "iron",
            "material_name_localised": "Iron",
            "category": "Raw",
            "count": 8,
            "latitude": -34.4439,
            "longitude": -177.0781,
            "timestamp": "2026-09-07T05:23:10Z"
        },
        {
            "system_address": 1001,
            "body_id": 1,
            "body_name": "Body A",
            "material_name": "nickel",
            "material_name_localised": "Nickel",
            "category": "Raw",
            "count": 8,
            "latitude": -34.4439,
            "longitude": -177.0781,
            "timestamp": "2026-09-07T05:23:12Z"
        },
        {
            "system_address": 1001,
            "body_id": 1,
            "body_name": "Body A",
            "material_name": "iridium",
            "material_name_localised": "Iridium",
            "category": "Refined",
            "count": 33,
            "latitude": -34.443912,
            "longitude": -177.078095,
            "timestamp": "2026-09-07T05:23:12Z"
        },
        {
            "system_address": 1001,
            "body_id": 1,
            "body_name": "Body A",
            "material_name": "haematite",
            "material_name_localised": "Haematite",
            "category": "Refined",
            "count": 42,
            "latitude": -34.443901,
            "longitude": -177.078079,
            "timestamp": "2026-09-07T05:32:08Z"
        }
    ]

    sites = extract_rhino_mining_sites(raw_activities)
    assert len(sites) == 1
    site = sites[0]

    # Check that coordinates are present
    assert pytest.approx(site["latitude"], 0.001) == -34.4439
    assert pytest.approx(site["longitude"], 0.001) == -177.0781

    # Check that Raw materials (Iron, Nickel) are excluded
    assert "Iron" not in site["commodities"]
    assert "Nickel" not in site["commodities"]

    # Check that Refined commodities are present without quantities
    assert site["commodities"] == ["Haematite", "Iridium"]
    assert "count" not in site
    assert site["last_mined"] == "2026-09-07T05:32:08Z"


@pytest.fixture
def setup_test_db(monkeypatch, tmp_path):
    db_file = tmp_path / "test_mining_db.db"
    def mock_get_db_connection():
        conn = sqlite3.connect(str(db_file), timeout=15.0)
        conn.row_factory = sqlite3.Row
        return conn

    import app.db.database as db_mod
    import app.server.api as api_mod
    monkeypatch.setattr(db_mod, "DB_PATH", db_file)
    monkeypatch.setattr(db_mod, "get_db_connection", mock_get_db_connection)
    monkeypatch.setattr(api_mod, "get_db_connection", mock_get_db_connection)

    conn = mock_get_db_connection()
    init_db(conn)
    c = conn.cursor()

    c.execute("""
        INSERT INTO systems (system_address, star_system, last_visited)
        VALUES (5001, 'Mining Star', '2026-09-07T05:00:00Z');
    """)
    c.execute("""
        INSERT INTO bodies (system_address, body_id, body_name, star_system, planet_class, landable, mining_signals)
        VALUES (5001, 10, 'Mining Star A 4', 'Mining Star', 'High metal content body', 1, 3);
    """)
    # Insert Raw and Refined
    c.execute("""
        INSERT INTO surface_mining_activities (system_address, star_system, body_id, body_name, srv_type, material_name, material_name_localised, category, count, latitude, longitude, timestamp)
        VALUES (5001, 'Mining Star', 10, 'Mining Star A 4', 'mev_rhino', 'iron', 'Iron', 'Raw', 5, -34.4439, -177.0781, '2026-09-07T05:10:00Z');
    """)
    c.execute("""
        INSERT INTO surface_mining_activities (system_address, star_system, body_id, body_name, srv_type, material_name, material_name_localised, category, count, latitude, longitude, timestamp)
        VALUES (5001, 'Mining Star', 10, 'Mining Star A 4', 'mev_rhino', 'iridium', 'Iridium', 'Refined', 10, -34.4439, -177.0781, '2026-09-07T05:20:00Z');
    """)
    c.execute("""
        INSERT INTO surface_mining_activities (system_address, star_system, body_id, body_name, srv_type, material_name, material_name_localised, category, count, latitude, longitude, timestamp)
        VALUES (5001, 'Mining Star', 10, 'Mining Star A 4', 'mev_rhino', 'haematite', 'Haematite', 'Refined', 20, -34.4439, -177.0781, '2026-09-07T05:30:00Z');
    """)
    conn.commit()
    conn.close()


def test_api_system_detail_returns_rhino_mining_sites(setup_test_db):
    resp = client.get("/api/system/5001")
    assert resp.status_code == 200
    data = resp.json()

    assert "rhino_mining_sites" in data
    sys_sites = data["rhino_mining_sites"]
    assert len(sys_sites) == 1
    assert sys_sites[0]["commodities"] == ["Haematite", "Iridium"]

    body = data["bodies"][0]
    assert "rhino_mining_sites" in body
    body_sites = body["rhino_mining_sites"]
    assert len(body_sites) == 1
    assert body_sites[0]["latitude"] == -34.4439
    assert body_sites[0]["longitude"] == -177.0781
    assert body_sites[0]["commodities"] == ["Haematite", "Iridium"]
