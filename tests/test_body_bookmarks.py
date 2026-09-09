import pytest
import sqlite3
from fastapi.testclient import TestClient
from app.server.api import app
from app.db.database import init_db, get_db_connection

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch, tmp_path):
    db_file = tmp_path / "test_ed_journal.db"
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

    # Insert test system and bodies
    c = conn.cursor()
    c.execute("""
        INSERT INTO systems (system_address, star_system, star_pos_x, star_pos_y, star_pos_z, scanned_bodies, total_potential_value, last_visited)
        VALUES (1001, 'Colonia 1', 10.0, 20.0, 30.0, 2, 5000000, '2026-09-01T12:00:00Z');
    """)
    c.execute("""
        INSERT INTO systems (system_address, star_system, star_pos_x, star_pos_y, star_pos_z, scanned_bodies, total_potential_value, last_visited)
        VALUES (1002, 'Sol Sector A', 0.0, 0.0, 0.0, 1, 1000000, '2026-09-02T12:00:00Z');
    """)

    c.execute("""
        INSERT INTO bodies (system_address, body_id, body_name, star_system, planet_class, landable, radius, surface_gravity_g, surface_temperature)
        VALUES (1001, 1, 'Colonia 1 A', 'Colonia 1', 'High metal content body', 1, 5000000, 0.25, 210.5);
    """)
    c.execute("""
        INSERT INTO bodies (system_address, body_id, body_name, star_system, planet_class, landable, radius, surface_gravity_g, surface_temperature)
        VALUES (1001, 2, 'Colonia 1 B', 'Colonia 1', 'Icy body', 0, 3000000, 0.10, 85.0);
    """)
    c.execute("""
        INSERT INTO bodies (system_address, body_id, body_name, star_system, planet_class, landable, radius, surface_gravity_g, surface_temperature)
        VALUES (1002, 1, 'Sol Sector A 1', 'Sol Sector A', 'Metal rich body', 1, 4000000, 1.2, 450.0);
    """)
    conn.commit()
    conn.close()

def test_bookmark_lifecycle():
    # 1. Initially no bookmark
    res = client.get("/api/bookmark/1001/1")
    assert res.status_code == 404

    # 2. Create bookmark with alias and markdown note
    payload = {
        "system_address": 1001,
        "body_id": 1,
        "body_name": "Colonia 1 A",
        "star_system": "Colonia 1",
        "alias_name": "Mining Base Rhino Alpha",
        "note_markdown": "# Rhino Rig Note\n- Max durability under 0.25G\n- **Bastnasite** rich hotspot"
    }
    res = client.post("/api/bookmark", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    # 3. Retrieve bookmark
    res = client.get("/api/bookmark/1001/1")
    assert res.status_code == 200
    data = res.json()
    assert data["alias_name"] == "Mining Base Rhino Alpha"
    assert "Bastnasite" in data["note_markdown"]

    # 4. Update bookmark
    payload["alias_name"] = "Mining Base Rhino Beta"
    res = client.post("/api/bookmark", json=payload)
    assert res.status_code == 200

    res = client.get("/api/bookmark/1001/1")
    assert res.json()["alias_name"] == "Mining Base Rhino Beta"

    # 5. List bookmarks
    res = client.get("/api/bookmarks")
    assert res.status_code == 200
    bms = res.json()["bookmarks"]
    assert len(bms) == 1
    assert bms[0]["alias_name"] == "Mining Base Rhino Beta"

    # 6. Delete bookmark
    res = client.delete("/api/bookmark/1001/1")
    assert res.status_code == 200

    res = client.get("/api/bookmark/1001/1")
    assert res.status_code == 404

def test_systems_search_with_bookmarks():
    # Add a bookmark with alias and note to Colonia 1 A
    client.post("/api/bookmark", json={
        "system_address": 1001,
        "body_id": 1,
        "body_name": "Colonia 1 A",
        "star_system": "Colonia 1",
        "alias_name": "Valuable outpost",
        "note_markdown": "Key resource: Tritium and LTD"
    })

    # Search by alias name
    res = client.get("/api/systems?q=Valuable")
    assert res.status_code == 200
    systems = res.json()["systems"]
    assert len(systems) == 1
    assert systems[0]["system_address"] == 1001
    assert len(systems[0]["bookmarks"]) == 1
    assert systems[0]["bookmarks"][0]["alias_name"] == "Valuable outpost"

    # Search by note content
    res = client.get("/api/systems?q=Tritium")
    assert res.status_code == 200
    systems = res.json()["systems"]
    assert len(systems) == 1
    assert systems[0]["system_address"] == 1001

    # Search with has_bookmarks filter
    res = client.get("/api/systems?has_bookmarks=true")
    assert res.status_code == 200
    systems = res.json()["systems"]
    assert len(systems) == 1
    assert systems[0]["system_address"] == 1001

    # Check landable_bodies has temp_k and surface_temperature
    lb = systems[0]["landable_bodies"]
    assert len(lb) == 1
    assert lb[0]["gravity_g"] == 0.25
    assert lb[0]["temp_k"] == 210
    assert lb[0]["surface_temperature"] == 210.5

def test_system_detail_with_bookmarks():
    # Add bookmark
    client.post("/api/bookmark", json={
        "system_address": 1001,
        "body_id": 1,
        "body_name": "Colonia 1 A",
        "star_system": "Colonia 1",
        "alias_name": "Test Alias",
        "note_markdown": "Note content"
    })

    res = client.get("/api/system/1001")
    assert res.status_code == 200
    data = res.json()
    assert "bookmarks" in data["system"]
    assert len(data["system"]["bookmarks"]) == 1
    # Check body 1 has bookmark attached
    b1 = next(b for b in data["bodies"] if b["body_id"] == 1)
    assert b1["bookmark"] is not None
    assert b1["bookmark"]["alias_name"] == "Test Alias"
    # Body 2 has no bookmark
    b2 = next(b for b in data["bodies"] if b["body_id"] == 2)
    assert b2["bookmark"] is None
