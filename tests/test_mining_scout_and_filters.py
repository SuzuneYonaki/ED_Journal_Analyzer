import json
import os
import sqlite3
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from app.db.database import get_db_connection, init_db
from app.services.edsm_service import edsm_service
from app.live.rhino.note_integrator import update_ring_hotspots_in_db
from app.parser.journal_parser import JournalParser
from app.server.api import app


@pytest.fixture(scope="module")
def client():
    init_db()
    return TestClient(app)


def test_mining_scout_grade_evaluation():
    init_db()
    sys_addr = 555000111222
    star_system = "Scout-Evaluation-System"

    with get_db_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO systems (system_address, star_system, system_reserve, mining_scout_grade)
            VALUES (?, ?, ?, ?)
            """,
            (sys_addr, star_system, "Pristine", "")
        )
        conn.execute("DELETE FROM bodies WHERE system_address = ?", (sys_addr,))
        conn.commit()

        # 1. Pristine with Metallic ring -> High
        conn.execute(
            """
            INSERT INTO bodies (system_address, body_id, body_name, planet_class, rings)
            VALUES (?, ?, ?, ?, ?)
            """,
            (sys_addr, 1, "Scout Planet 1", "Gas Giant", json.dumps([{"Name": "Ring A", "RingClass": "eRingClass_Metallic"}]))
        )
        conn.commit()

        edsm_service._update_system_aggregated_stats(conn, sys_addr)
        conn.commit()

        row = conn.execute("SELECT mining_scout_grade FROM systems WHERE system_address = ?", (sys_addr,)).fetchone()
        assert row["mining_scout_grade"] == "High"

        # 2. Pristine with Icy ring only -> Medium
        conn.execute("DELETE FROM bodies WHERE system_address = ?", (sys_addr,))
        conn.execute(
            """
            INSERT INTO bodies (system_address, body_id, body_name, planet_class, rings)
            VALUES (?, ?, ?, ?, ?)
            """,
            (sys_addr, 2, "Scout Planet 2", "Gas Giant", json.dumps([{"Name": "Ring B", "RingClass": "eRingClass_Icy"}]))
        )
        conn.commit()

        edsm_service._update_system_aggregated_stats(conn, sys_addr)
        conn.commit()

        row = conn.execute("SELECT mining_scout_grade FROM systems WHERE system_address = ?", (sys_addr,)).fetchone()
        assert row["mining_scout_grade"] == "Medium"

        # 3. Non-Pristine reserve -> empty
        conn.execute("UPDATE systems SET system_reserve = 'Major' WHERE system_address = ?", (sys_addr,))
        conn.commit()

        edsm_service._update_system_aggregated_stats(conn, sys_addr)
        conn.commit()

        row = conn.execute("SELECT mining_scout_grade FROM systems WHERE system_address = ?", (sys_addr,)).fetchone()
        assert row["mining_scout_grade"] == ""


def test_station_has_large_pad_logic():
    sys_addr = 555000333444
    sys_name = "Pad-Test-System"

    with get_db_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO systems (system_address, star_system) VALUES (?, ?)",
            (sys_addr, sys_name)
        )
        conn.execute("DELETE FROM stations WHERE system_address = ?", (sys_addr,))
        conn.commit()

        parser = JournalParser(db_conn=conn)

        # Station Docked event with Large pads
        docked_event = {
            "event": "Docked",
            "SystemAddress": sys_addr,
            "StarSystem": sys_name,
            "MarketID": 90101,
            "StationName": "Coriolis High Hub",
            "StationType": "Coriolis",
            "DistFromStarLS": 150.0,
            "LandingPads": {"Large": 4, "Medium": 8, "Small": 10},
            "timestamp": "2026-09-14T00:00:00Z"
        }
        parser._handle_station_event(docked_event, "2026-09-14T00:00:00Z")

        # Outpost Docked event without Large pads
        outpost_event = {
            "event": "Docked",
            "SystemAddress": sys_addr,
            "StarSystem": sys_name,
            "MarketID": 90102,
            "StationName": "Mining Outpost Small",
            "StationType": "Outpost",
            "DistFromStarLS": 450.0,
            "LandingPads": {"Large": 0, "Medium": 1, "Small": 3},
            "timestamp": "2026-09-14T00:00:00Z"
        }
        parser._handle_station_event(outpost_event, "2026-09-14T00:00:00Z")
        conn.commit()

        s1 = conn.execute("SELECT has_large_pad FROM stations WHERE market_id = 90101").fetchone()
        s2 = conn.execute("SELECT has_large_pad FROM stations WHERE market_id = 90102").fetchone()

        assert s1 is not None and s1["has_large_pad"] == 1
        assert s2 is not None and s2["has_large_pad"] == 0


def test_ring_dss_scan_note_integration():
    sys_addr = 555000555666
    body_id = 15
    body_name = "Gas Giant 4"
    ring_name = "Gas Giant 4 A Ring"

    hotspot_counts = {
        "Platinum": 2,
        "Painite": 1,
        "Tritium": 3
    }

    with get_db_connection() as conn:
        conn.execute("DELETE FROM body_bookmarks WHERE system_address = ? AND body_id = ?", (sys_addr, body_id))
        conn.commit()

        update_ring_hotspots_in_db(
            conn=conn,
            system_address=sys_addr,
            body_id=body_id,
            body_name=body_name,
            star_system="Ring-DSS-System",
            ring_name=ring_name,
            hotspot_counts=hotspot_counts
        )
        conn.commit()

        row = conn.execute(
            "SELECT note_markdown FROM body_bookmarks WHERE system_address = ? AND body_id = ?",
            (sys_addr, body_id)
        ).fetchone()

        assert row is not None
        note = row["note_markdown"]
        assert "Ring DSS Scan (Hotspots)" in note
        assert "Platinum" in note
        assert "x2" in note
        assert "Painite" in note
        assert "Tritium" in note
        assert "x3" in note


def test_api_system_filters_and_coordinates(client):
    sys_addr_high = 7771110001
    sys_addr_med = 7771110002

    with get_db_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO systems (system_address, star_system, mining_scout_grade, system_reserve)
            VALUES (?, 'Scout Alpha High', 'High', 'Pristine')
            """,
            (sys_addr_high,)
        )
        conn.execute("DELETE FROM stations WHERE system_address = ?", (sys_addr_high,))
        conn.execute(
            """
            INSERT INTO stations (market_id, system_address, station_name, has_large_pad, distance_to_arrival_ls)
            VALUES (7001, ?, 'Alpha Starport Large', 1, 1500.0)
            """,
            (sys_addr_high,)
        )

        conn.execute(
            """
            INSERT OR REPLACE INTO systems (system_address, star_system, mining_scout_grade, system_reserve)
            VALUES (?, 'Scout Beta Med', 'Medium', 'Pristine')
            """,
            (sys_addr_med,)
        )
        conn.execute("DELETE FROM stations WHERE system_address = ?", (sys_addr_med,))
        conn.execute(
            """
            INSERT INTO stations (market_id, system_address, station_name, has_large_pad, distance_to_arrival_ls)
            VALUES (7002, ?, 'Beta Outpost Small', 0, 8500.0)
            """,
            (sys_addr_med,)
        )
        conn.commit()

    # 1. Filter by mining_scout
    resp = client.get("/api/systems?mining_scout=High&q=Scout Alpha")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["systems"][0]["star_system"] == "Scout Alpha High"

    # 2. Filter by has_large_pad
    resp = client.get("/api/systems?has_large_pad=true&q=Scout Alpha")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["systems"][0]["star_system"] == "Scout Alpha High"

    # 3. Filter by max_arrival_dist_ls
    resp = client.get("/api/systems?max_arrival_dist_ls=2000&q=Scout")
    assert resp.status_code == 200
    data = resp.json()
    matched_names = [s["star_system"] for s in data["systems"]]
    assert "Scout Alpha High" in matched_names
    assert "Scout Beta Med" not in matched_names

    # 4. CMDR coordinates endpoint
    with patch("app.live.telemetry.telemetry_tracker.read_status_json") as mock_read_status:
        mock_read_status.return_value = {
            "Latitude": -14.2561,
            "Longitude": 128.9104,
            "Altitude": 120.5,
            "Heading": 45,
            "BodyName": "Test Planet Alpha"
        }
        resp = client.get("/api/cmdr/coordinates")
        assert resp.status_code == 200
        coords_data = resp.json()
        assert coords_data["has_coordinates"] is True
        assert "-14.2561" in coords_data["formatted_text"]
        assert "+128.9104" in coords_data["formatted_text"]
