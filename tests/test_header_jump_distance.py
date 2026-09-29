"""
test_header_jump_distance.py - Unit tests for header jump distance metrics and API/UI integration
Elite Dangerous Journal Analyzer
"""
import sqlite3
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.server.api import app, get_cmdr_jump_stats


@pytest.fixture
def client():
    return TestClient(app)


def test_get_cmdr_jump_stats_empty():
    """Verifies that get_cmdr_jump_stats safely handles an empty visits table."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        CREATE TABLE visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            system_address INTEGER NOT NULL,
            star_system TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            star_pos_x REAL,
            star_pos_y REAL,
            star_pos_z REAL,
            jump_dist REAL,
            fuel_used REAL,
            is_taxi INTEGER DEFAULT 0
        )
    """)
    c.execute("""
        CREATE TABLE systems (
            system_address INTEGER PRIMARY KEY,
            star_system TEXT NOT NULL,
            star_pos_x REAL,
            star_pos_y REAL,
            star_pos_z REAL,
            first_visited TEXT,
            last_visited TEXT
        )
    """)
    conn.commit()

    stats = get_cmdr_jump_stats(conn)
    assert stats["total_jump_dist"] == 0.0
    assert stats["jump_count"] == 0
    assert stats["straight_dist"] is None
    assert stats["initial_system"] is None
    assert stats["current_system"] is None
    conn.close()


def test_get_cmdr_jump_stats_calculation():
    """Verifies that get_cmdr_jump_stats calculates total jump distance, count, and straight distance."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        CREATE TABLE visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            system_address INTEGER NOT NULL,
            star_system TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            star_pos_x REAL,
            star_pos_y REAL,
            star_pos_z REAL,
            jump_dist REAL,
            fuel_used REAL,
            is_taxi INTEGER DEFAULT 0
        )
    """)
    c.execute("""
        CREATE TABLE systems (
            system_address INTEGER PRIMARY KEY,
            star_system TEXT NOT NULL,
            star_pos_x REAL,
            star_pos_y REAL,
            star_pos_z REAL,
            first_visited TEXT,
            last_visited TEXT
        )
    """)

    # Initial system: Sol (0, 0, 0) at 2026-01-01
    c.execute("""
        INSERT INTO visits (system_address, star_system, timestamp, star_pos_x, star_pos_y, star_pos_z, jump_dist)
        VALUES (1, 'Sol', '2026-01-01T00:00:00Z', 0.0, 0.0, 0.0, 0.0)
    """)
    # Jump 1: Alpha Centauri (10, 0, 0), jump_dist = 10.0
    c.execute("""
        INSERT INTO visits (system_address, star_system, timestamp, star_pos_x, star_pos_y, star_pos_z, jump_dist)
        VALUES (2, 'Alpha Centauri', '2026-01-01T01:00:00Z', 10.0, 0.0, 0.0, 10.0)
    """)
    # Jump 2: Colonia (30, 40, 0), jump_dist = 50.0 (Euclidean from Sol to Colonia = sqrt(30^2 + 40^2) = 50.0)
    c.execute("""
        INSERT INTO visits (system_address, star_system, timestamp, star_pos_x, star_pos_y, star_pos_z, jump_dist)
        VALUES (3, 'Colonia', '2026-01-01T02:00:00Z', 30.0, 40.0, 0.0, 50.0)
    """)
    conn.commit()

    stats = get_cmdr_jump_stats(conn)
    # Total jump distance = 10.0 + 50.0 = 60.0
    assert stats["total_jump_dist"] == 60.0
    assert stats["jump_count"] == 2
    # Straight-line distance from Sol (0,0,0) to Colonia (30,40,0) = 50.0
    assert stats["straight_dist"] == 50.0
    assert stats["initial_system"] == "Sol"
    assert stats["current_system"] == "Colonia"
    conn.close()


def test_api_stats_includes_jump_stats(client):
    """Verifies that /api/stats includes jump_stats in its response."""
    res = client.get("/api/stats")
    assert res.status_code == 200
    data = res.json()
    assert "jump_stats" in data
    js = data["jump_stats"]
    assert "total_jump_dist" in js
    assert "jump_count" in js


def test_api_systems_includes_jump_stats(client):
    """Verifies that /api/systems includes jump_stats in its response."""
    res = client.get("/api/systems?limit=1")
    assert res.status_code == 200
    data = res.json()
    assert "jump_stats" in data


def test_header_html_contains_jump_dist_container():
    """Verifies header.html contains stat-jump-dist-container and stat-jump-dist element."""
    header_file = Path("app/ui/components/header.html")
    assert header_file.exists()
    content = header_file.read_text(encoding="utf-8")

    assert 'id="stat-jump-dist-container"' in content
    assert 'id="stat-jump-dist"' in content
    assert 'data-i18n="stat_jump_dist_label"' in content
    assert 'data-i18n-title="stat_jump_dist_tip"' in content


def test_i18n_contains_jump_dist_keys():
    """Verifies i18n.js has the jump distance keys in both ja and en."""
    i18n_file = Path("app/ui/js/i18n.js")
    assert i18n_file.exists()
    content = i18n_file.read_text(encoding="utf-8")

    # ja
    assert 'stat_jump_dist_label: "🚀 累計ジャンプ"' in content
    assert 'stat_jump_dist_tip:' in content

    # en
    assert 'stat_jump_dist_label: "🚀 Total Jumps"' in content


def test_app_js_handles_jump_stats():
    """Verifies app.js has updateHeaderJumpStats function and updates stat-jump-dist."""
    app_js_file = Path("app/ui/js/app.js")
    assert app_js_file.exists()
    content = app_js_file.read_text(encoding="utf-8")

    assert "function updateHeaderJumpStats(" in content
    assert "stat-jump-dist" in content
    assert "stat-jump-dist-container" in content
