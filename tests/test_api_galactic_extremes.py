import pytest
import sqlite3
from fastapi.testclient import TestClient
from app.server.api import app, get_db_connection
from app.db.database import init_db

@pytest.fixture
def test_client(tmp_path, monkeypatch):
    test_db = tmp_path / "test_extremes.db"
    
    def mock_get_db_connection():
        conn = sqlite3.connect(str(test_db), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    monkeypatch.setattr("app.server.api.get_db_connection", mock_get_db_connection)
    
    # Initialize DB schema
    conn = mock_get_db_connection()
    init_db(conn, force=True)
    c = conn.cursor()

    # Insert test systems
    # 1. Sol (Origin)
    c.execute("""
        INSERT INTO systems (system_address, star_system, star_pos_x, star_pos_y, star_pos_z, visit_count, is_external, last_visited)
        VALUES (1, 'Sol', 0.0, 0.0, 0.0, 5, 0, '2024-01-01T00:00:00Z')
    """)

    # 2. Galactic North (+Z = 65000)
    c.execute("""
        INSERT INTO systems (system_address, star_system, star_pos_x, star_pos_y, star_pos_z, visit_count, is_external, last_visited)
        VALUES (2, 'Beagle Point', -1111.5, -134.5, 65279.3, 1, 0, '2024-02-01T12:00:00Z')
    """)

    # 3. Galactic South (-Z = -5000)
    c.execute("""
        INSERT INTO systems (system_address, star_system, star_pos_x, star_pos_y, star_pos_z, visit_count, is_external, last_visited)
        VALUES (3, 'Deep South', 10.0, 0.0, -5000.0, 2, 0, '2024-02-05T12:00:00Z')
    """)

    # 4. Galactic East (+X = 25000)
    c.execute("""
        INSERT INTO systems (system_address, star_system, star_pos_x, star_pos_y, star_pos_z, visit_count, is_external, last_visited)
        VALUES (4, 'Far East Star', 25000.0, 10.0, 100.0, 1, 0, '2024-03-01T10:00:00Z')
    """)

    # 5. Galactic West (-X = -30000)
    c.execute("""
        INSERT INTO systems (system_address, star_system, star_pos_x, star_pos_y, star_pos_z, visit_count, is_external, last_visited)
        VALUES (5, 'Far West Star', -30000.0, -20.0, 50.0, 1, 0, '2024-03-05T10:00:00Z')
    """)

    # 6. Galactic Zenith (+Y = 3200)
    c.execute("""
        INSERT INTO systems (system_address, star_system, star_pos_x, star_pos_y, star_pos_z, visit_count, is_external, last_visited)
        VALUES (6, 'Sky High Ceiling', 500.0, 3200.0, 2000.0, 1, 0, '2024-03-10T10:00:00Z')
    """)

    # 7. Galactic Nadir (-Y = -2800)
    c.execute("""
        INSERT INTO systems (system_address, star_system, star_pos_x, star_pos_y, star_pos_z, visit_count, is_external, last_visited)
        VALUES (7, 'Abyss Floor', -300.0, -2800.0, 1500.0, 1, 0, '2024-03-15T10:00:00Z')
    """)

    # 8. External / Unvisited (even though +Z is huge, should be IGNORED)
    c.execute("""
        INSERT INTO systems (system_address, star_system, star_pos_x, star_pos_y, star_pos_z, visit_count, is_external, last_visited)
        VALUES (8, 'Ghost Distant System', 0.0, 0.0, 80000.0, 0, 1, '2024-04-01T00:00:00Z')
    """)

    conn.commit()
    conn.close()

    client = TestClient(app)
    return client

def test_galactic_extremes_endpoint(test_client):
    res = test_client.get("/api/cmdr/galactic_extremes")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    ext = data["extremes"]

    # North (+Z max) should be Beagle Point (Z ~ 65279.3), NOT Ghost Distant System (80000.0)
    assert ext["north"]["star_system"] == "Beagle Point"
    assert ext["north"]["z"] == 65279.3

    # South (-Z min)
    assert ext["south"]["star_system"] == "Deep South"
    assert ext["south"]["z"] == -5000.0

    # East (+X max)
    assert ext["east"]["star_system"] == "Far East Star"
    assert ext["east"]["x"] == 25000.0

    # West (-X min)
    assert ext["west"]["star_system"] == "Far West Star"
    assert ext["west"]["x"] == -30000.0

    # Zenith (+Y max)
    assert ext["zenith"]["star_system"] == "Sky High Ceiling"
    assert ext["zenith"]["y"] == 3200.0

    # Nadir (-Y min)
    assert ext["nadir"]["star_system"] == "Abyss Floor"
    assert ext["nadir"]["y"] == -2800.0

    # Farthest
    assert ext["farthest"]["star_system"] == "Beagle Point"
    assert ext["farthest"]["distance_sol"] > 65000.0
