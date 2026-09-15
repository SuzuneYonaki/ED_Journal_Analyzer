"""
Unit tests for Spansh Hotspots and Planetary Mining Location integration (Step 2).
Tests SpanshService, note integration, database persistence, and FastAPI sync endpoints.
All code, strings, and comments in this module are strictly English ASCII.
"""

import json
import sqlite3
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.server.api import app
from app.services.spansh_service import SpanshService
from app.live.rhino.note_integrator import RING_HOTSPOT_HEADER


SAMPLE_SPANSH_RESPONSE = {
    "results": [
        {
            "name": "TestSystem 1",
            "body_id": 10,
            "system_name": "TestSystem",
            "reserve_level": "Pristine",
            "is_landable": False,
            "rings": [
                {
                    "name": "TestSystem 1 A Ring",
                    "type": "Metallic",
                    "inner_radius": 100000000.0,
                    "outer_radius": 150000000.0,
                    "mass": 500000000000.0,
                    "signals": [
                        {"name": "Platinum", "count": 4},
                        {"name": "Painite", "count": 2}
                    ],
                    "signals_updated_at": "2026-09-15T12:00:00Z"
                },
                {
                    "name": "TestSystem 1 B Ring",
                    "type": "Icy",
                    "inner_radius": 160000000.0,
                    "outer_radius": 250000000.0,
                    "mass": 800000000000.0,
                    "signals": [
                        {"name": "Tritium", "count": 3}
                    ],
                    "signals_updated_at": "2026-09-15T12:00:00Z"
                }
            ]
        },
        {
            "name": "TestSystem 2 a",
            "body_id": 21,
            "system_name": "TestSystem",
            "reserve_level": "Pristine",
            "is_landable": True,
            "signals": [
                {"name": "Planetary Mining Location", "count": 14},
                {"name": "Geological", "count": 3}
            ]
        }
    ]
}


@pytest.fixture
def mock_db():
    """Create an in-memory SQLite DB with systems, bodies, and body_bookmarks tables."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        CREATE TABLE systems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            system_address INTEGER UNIQUE,
            star_system TEXT,
            system_reserve TEXT DEFAULT ''
        )
    """)
    c.execute("""
        CREATE TABLE bodies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            system_address INTEGER,
            body_id INTEGER,
            body_name TEXT,
            rings TEXT,
            mining_signals INTEGER DEFAULT 0,
            reserve_level TEXT,
            landable INTEGER DEFAULT 0
        )
    """)
    c.execute("""
        CREATE TABLE body_bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            system_address INTEGER,
            body_id INTEGER,
            body_name TEXT,
            star_system TEXT,
            alias_name TEXT DEFAULT '',
            note_markdown TEXT DEFAULT '',
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()
    return conn


def test_fetch_system_bodies_filtering():
    """Test fetch_system_bodies filters results matching the exact system name."""
    service = SpanshService()
    
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps({
        "results": [
            {"system_name": "Sol", "name": "Sol 3"},
            {"system_name": "Solitude", "name": "Solitude 1"}
        ]
    }).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = service.fetch_system_bodies("Sol")
        assert len(res) == 1
        assert res[0]["system_name"] == "Sol"


def test_sync_system_spansh_updates_rings_and_notes(mock_db):
    """Test sync_system_spansh merges ring hotspots and creates markdown notes in body_bookmarks."""
    c = mock_db.cursor()
    c.execute("INSERT INTO systems (system_address, star_system) VALUES (?, ?)", (12345678, "TestSystem"))
    
    existing_rings = [
        {
            "Name": "TestSystem 1 A Ring",
            "RingClass": "eRingClass_MetalRich",
            "InnerRad": 100000000.0,
            "OuterRad": 150000000.0,
            "MassMT": 500.0
        }
    ]
    c.execute(
        "INSERT INTO bodies (system_address, body_id, body_name, rings, mining_signals, landable) VALUES (?, ?, ?, ?, ?, ?)",
        (12345678, 10, "TestSystem 1", json.dumps(existing_rings), 0, 0)
    )
    c.execute(
        "INSERT INTO bodies (system_address, body_id, body_name, rings, mining_signals, landable) VALUES (?, ?, ?, ?, ?, ?)",
        (12345678, 21, "TestSystem 2 a", None, 0, 1)
    )
    mock_db.commit()

    service = SpanshService()

    with patch.object(service, "fetch_system_bodies", return_value=SAMPLE_SPANSH_RESPONSE["results"]):
        summary = service.sync_system_spansh(mock_db, 12345678, "TestSystem")

    assert summary["success"] is True
    assert summary["hotspots_found"] == 6  # 4 Pt + 2 Pa
    assert summary["pml_found"] == 14
    assert summary["bodies_updated"] == 2

    # Check bodies.rings updated with Hotspots
    c.execute("SELECT rings, reserve_level FROM bodies WHERE body_id = 10")
    row_ring = c.fetchone()
    rings_data = json.loads(row_ring["rings"])
    assert len(rings_data) == 1
    assert rings_data[0]["Hotspots"] == {"Painite": 2, "Platinum": 4}
    assert row_ring["reserve_level"] == "Pristine"

    # Check bodies.mining_signals updated
    c.execute("SELECT mining_signals FROM bodies WHERE body_id = 21")
    row_landable = c.fetchone()
    assert row_landable["mining_signals"] == 14

    # Check systems.system_reserve updated
    c.execute("SELECT system_reserve FROM systems WHERE system_address = 12345678")
    row_sys = c.fetchone()
    assert row_sys["system_reserve"] == "Pristine"

    # Check body_bookmarks has ring DSS hotspots note
    c.execute("SELECT note_markdown FROM body_bookmarks WHERE body_id = 10")
    bm_row = c.fetchone()
    assert bm_row is not None
    note = bm_row["note_markdown"]
    assert RING_HOTSPOT_HEADER in note
    assert "Painite x2" in note
    assert "Platinum x4" in note


def test_sync_system_spansh_handles_network_failure(mock_db):
    """Test SpanshService gracefully handles URLError without raising."""
    service = SpanshService()
    with patch("urllib.request.urlopen", side_effect=Exception("Connection timed out")):
        summary = service.sync_system_spansh(mock_db, 9999, "FailedSystem")
        assert summary["success"] is True
        assert summary["bodies_updated"] == 0
        assert "message" in summary


def test_api_spansh_sync_endpoint():
    """Test POST /api/systems/{system_address}/spansh_sync via FastAPI TestClient."""
    client = TestClient(app)
    
    with patch("app.server.api.get_db_connection") as mock_conn_fn, \
         patch("app.server.api.spansh_service.sync_system_spansh") as mock_sync_fn:
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"star_system": "Colonia"}
        mock_conn.cursor.return_value = mock_cursor
        mock_conn_fn.return_value = mock_conn

        mock_sync_fn.return_value = {
            "success": True,
            "bodies_updated": 3,
            "hotspots_found": 8,
            "pml_found": 18
        }

        resp = client.post("/api/systems/2868212502146/spansh_sync")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["hotspots_found"] == 8
        assert data["pml_found"] == 18
