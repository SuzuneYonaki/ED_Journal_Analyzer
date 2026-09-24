"""
test_ggg_filter_api.py - Unit tests for GGG system filtering and API response badge flags.
"""
import json
import sqlite3
import pytest
from fastapi.testclient import TestClient

from app.db.database import init_db
from app.server.api import app, get_db_connection


@pytest.fixture
def filter_test_db(tmp_path, monkeypatch):
    """Sets up an isolated SQLite database with systems and bodies for filter testing."""
    db_file = str(tmp_path / "test_filter.db")
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    init_db(conn)

    cursor = conn.cursor()

    # System 1: Has Confirmed GGG
    sys1_addr = 10001
    cursor.execute("""
        INSERT INTO systems (system_address, star_system, last_visited, total_potential_value)
        VALUES (?, 'GGG-System-1', '2026-09-24T10:00:00Z', 5000000)
    """, (sys1_addr,))
    cursor.execute("""
        INSERT INTO bodies (system_address, body_id, body_name, planet_class, anomalies_json)
        VALUES (?, 1, 'GGG-System-1 1', 'Sudarsky class III gas giant', ?)
    """, (sys1_addr, json.dumps([{"type": "confirmed_ggg", "tag": "Confirmed GGG", "color": "green"}])))

    # System 2: Has GGG via codex_entries
    sys2_addr = 10002
    cursor.execute("""
        INSERT INTO systems (system_address, star_system, last_visited, total_potential_value, has_elw)
        VALUES (?, 'GGG-Codex-System-2', '2026-09-24T11:00:00Z', 8000000, 1)
    """, (sys2_addr,))
    cursor.execute("""
        INSERT INTO bodies (system_address, body_id, body_name, planet_class, anomalies_json)
        VALUES (?, 1, 'GGG-Codex-System-2 1', 'Gas giant with water based life', '[]')
    """, (sys2_addr,))
    cursor.execute("""
        INSERT INTO codex_entries (
            system_address, body_id, body_name, entry_id, name, is_ggg, ggg_variant, timestamp, created_at
        ) VALUES (?, 1, 'GGG-Codex-System-2 1', 140002, '$Codex_Ent_Green_Gas_Giant_Water_Life_Name;', 1, 'Gas Giant with Water-based Life', '2026-09-24T11:00:00Z', '2026-09-24T11:00:00Z')
    """, (sys2_addr,))

    # System 3: Normal system (No GGG)
    sys3_addr = 10003
    cursor.execute("""
        INSERT INTO systems (system_address, star_system, last_visited, total_potential_value, has_elw)
        VALUES (?, 'Normal-System-3', '2026-09-24T12:00:00Z', 2000000, 1)
    """, (sys3_addr,))
    cursor.execute("""
        INSERT INTO bodies (system_address, body_id, body_name, planet_class, anomalies_json)
        VALUES (?, 1, 'Normal-System-3 1', 'Earthlike body', '[]')
    """, (sys3_addr,))

    conn.commit()
    conn.close()

    # Monkeypatch get_db_connection in api module
    def get_test_conn():
        c = sqlite3.connect(db_file)
        c.row_factory = sqlite3.Row
        return c

    monkeypatch.setattr("app.server.api.get_db_connection", get_test_conn)

    client = TestClient(app)
    yield client


def test_get_systems_with_has_ggg_filter(filter_test_db):
    client = filter_test_db

    # 1. Unfiltered query returns all 3 systems
    res_all = client.get("/api/systems")
    assert res_all.status_code == 200
    data_all = res_all.json()
    assert data_all["total"] == 3

    # Check that has_ggg flag is properly present on system items
    sys_map = {s["system_address"]: s for s in data_all["systems"]}
    assert sys_map[10001]["has_ggg"] == 1
    assert sys_map[10002]["has_ggg"] == 1
    assert sys_map[10003]["has_ggg"] == 0

    # 2. Filter by has_ggg=true returns only systems 1 and 2
    res_ggg = client.get("/api/systems?has_ggg=true")
    assert res_ggg.status_code == 200
    data_ggg = res_ggg.json()
    assert data_ggg["total"] == 2
    addrs = [s["system_address"] for s in data_ggg["systems"]]
    assert 10001 in addrs
    assert 10002 in addrs
    assert 10003 not in addrs

    # 3. Combine has_ggg with has_elw
    res_combined = client.get("/api/systems?has_ggg=true&has_elw=true")
    assert res_combined.status_code == 200
    data_combined = res_combined.json()
    assert data_combined["total"] == 1
    assert data_combined["systems"][0]["system_address"] == 10002
