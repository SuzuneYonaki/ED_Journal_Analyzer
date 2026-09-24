"""
test_celestial_stats.py - Tests for Cross-System Celestial & Stellar Statistics API
Elite Dangerous Journal Analyzer
"""

import sqlite3
import pytest
from fastapi.testclient import TestClient

from app.db.database import get_celestial_statistics, init_db
from app.server.api import app


@pytest.fixture
def temp_db(tmp_path):
    """Sets up a temporary SQLite database using official schema."""
    db_file = str(tmp_path / "test_celestial.db")
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    cursor = conn.cursor()

    # Populate with diverse test records
    test_bodies = [
        # Stars
        (101, 0, "Star Sol A", "Sol", "G", None, None),
        (101, 1, "Star Sol B", "Sol", "G", None, None),
        (102, 0, "Star Alpha M", "Alpha", "M", None, None),
        (103, 0, "Star Neutron", "Phaethon", "N", None, None),
        (104, 0, "Star Black Hole", "Singularity", "H", None, None),

        # Terrestrial planets
        (101, 2, "Earth", "Sol", None, "Earthlike body", None),
        (101, 3, "Water World 1", "Sol", None, "Water world", None),
        (102, 2, "Ammonia World 1", "Alpha", None, "Ammonia world", None),
        (102, 3, "Water Giant 1", "Alpha", None, "Water giant", None),
        (102, 4, "High Metal Planet", "Alpha", None, "High metal content body", None),
        (102, 5, "Metal Rich Planet", "Alpha", None, "Metal rich body", None),
        (102, 6, "Rocky Body 1", "Alpha", None, "Rocky body", None),
        (102, 7, "Icy Body 1", "Alpha", None, "Icy body", None),
        (102, 8, "Rocky Ice 1", "Alpha", None, "Rocky ice body", None),

        # Sudarsky & Helium
        (103, 1, "Gas Giant I", "Phaethon", None, "Sudarsky class I gas giant", None),
        (103, 2, "Gas Giant II", "Phaethon", None, "Sudarsky class II gas giant", None),
        (103, 3, "Gas Giant III", "Phaethon", None, "Sudarsky class III gas giant", None),
        (103, 4, "Gas Giant IV", "Phaethon", None, "Sudarsky class IV gas giant", None),
        (103, 5, "Gas Giant V", "Phaethon", None, "Sudarsky class V gas giant", None),
        (103, 6, "Helium Giant", "Phaethon", None, "Helium rich gas giant", None),

        # Water life: 1 ringed, 2 unringed (total 3)
        (104, 1, "Water Life Ringed", "Singularity", None, "Gas giant with water based life", '[{"Name": "Ring A"}]'),
        (104, 2, "Water Life Unringed 1", "Singularity", None, "Gas giant with water based life", None),
        (104, 3, "Water Life Unringed 2", "Singularity", None, "Gas giant with water based life", '[]'),

        # Ammonia life: 1 ringed, 1 unringed (total 2)
        (104, 4, "Ammonia Life Ringed", "Singularity", None, "Gas giant with ammonia based life", '[{"Name": "Ring B"}]'),
        (104, 5, "Ammonia Life Unringed", "Singularity", None, "Gas giant with ammonia based life", ''),

        # Additional ringed body
        (101, 4, "Ringed Icy", "Sol", None, "Icy body", '[{"Name": "Ring C"}]')
    ]

    cursor.executemany("""
        INSERT INTO bodies (system_address, body_id, body_name, star_system, star_type, planet_class, rings)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, test_bodies)
    conn.commit()
    conn.close()

    return db_file


def test_get_celestial_statistics_counts(temp_db):
    conn = sqlite3.connect(temp_db)
    conn.row_factory = sqlite3.Row
    stats = get_celestial_statistics(conn=conn)
    conn.close()

    # 1. Summary verification
    summary = stats["summary"]
    assert summary["total_bodies"] == 26
    assert summary["total_stars"] == 5
    assert summary["total_planets"] == 21
    assert summary["total_ringed"] == 3

    # Dual alias compatibility checks
    assert summary["total_bodies_scanned"] == 26
    assert summary["total_stars_scanned"] == 5
    assert summary["total_planets_scanned"] == 21
    assert summary["total_ringed_bodies"] == 3

    # 2. Stars verification
    stars = stats["stars"]
    assert stars["G"] == 2
    assert stars["M"] == 1
    assert stars["N"] == 1
    assert stars["H"] == 1

    # 3. Planets verification
    planets = stats["planets"]
    assert planets["earth_like"] == 1
    assert planets["water_world"] == 1
    assert planets["ammonia_world"] == 1
    assert planets["water_giant"] == 1

    assert planets["gas_giant_water_life"] == 3
    assert planets["gas_giant_water_life_ringed"] == 1
    assert planets["gas_giant_water_life_unringed"] == 2

    assert planets["gas_giant_ammonia_life"] == 2
    assert planets["gas_giant_ammonia_life_ringed"] == 1
    assert planets["gas_giant_ammonia_life_unringed"] == 1

    assert planets["sudarsky_class_1"] == 1
    assert planets["sudarsky_class_2"] == 1
    assert planets["sudarsky_class_3"] == 1
    assert planets["sudarsky_class_4"] == 1
    assert planets["sudarsky_class_5"] == 1
    assert planets["helium_gas_giant"] == 1

    assert planets["high_metal_content"] == 1
    assert planets["metal_rich"] == 1
    assert planets["rocky_body"] == 1
    assert planets["icy_body"] == 2
    assert planets["rocky_ice"] == 1
    assert planets["gas_giants_total"] == 12
    assert planets["green_gas_giant"] == 0


def test_api_celestial_counts_endpoint(monkeypatch, temp_db):
    def _get_test_conn():
        conn = sqlite3.connect(temp_db)
        conn.row_factory = sqlite3.Row
        return conn

    monkeypatch.setattr("app.db.database.get_db_connection", _get_test_conn)
    monkeypatch.setattr("app.server.api.get_db_connection", _get_test_conn)

    client = TestClient(app)
    response = client.get("/api/stats/celestial_counts")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert "data" in data

    res_data = data["data"]
    assert "summary" in res_data
    assert "stars" in res_data
    assert "planets" in res_data

    # Verify summary fields match exact API specification
    assert res_data["summary"]["total_bodies"] == 26
    assert res_data["summary"]["total_stars"] == 5
    assert res_data["summary"]["total_planets"] == 21
    assert res_data["summary"]["total_ringed"] == 3

    # Verify stars & planets structure
    assert res_data["stars"]["G"] == 2
    assert res_data["planets"]["earth_like"] == 1
    assert res_data["planets"]["gas_giant_water_life"] == 3
    assert res_data["planets"]["gas_giant_water_life_ringed"] == 1
    assert res_data["planets"]["gas_giant_water_life_unringed"] == 2
    assert res_data["planets"]["gas_giants_total"] == 12


def test_api_global_stats_includes_celestial_counts(monkeypatch, temp_db):
    def _get_test_conn():
        conn = sqlite3.connect(temp_db)
        conn.row_factory = sqlite3.Row
        return conn

    monkeypatch.setattr("app.db.database.get_db_connection", _get_test_conn)
    monkeypatch.setattr("app.server.api.get_db_connection", _get_test_conn)

    client = TestClient(app)
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "celestial_counts" in data
    counts = data["celestial_counts"]
    assert counts["earth_like"] == 1
    assert counts["water_world"] == 1
    assert counts["high_metal_content"] == 1
    assert counts["gas_giants_total"] == 12
