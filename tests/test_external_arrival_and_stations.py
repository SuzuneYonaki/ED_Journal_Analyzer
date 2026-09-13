import os
import json
import sqlite3
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from app.db.database import get_db_connection, init_db
from app.parser.journal_parser import JournalParser
from app.services.edsm_service import edsm_service
from app.server.api import app

@pytest.fixture(scope="module")
def client():
    init_db()
    return TestClient(app)

def test_jump_clears_external_flag():
    sys_addr = 888111222333
    sys_name = "External To Visited System"
    
    with get_db_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO systems (
                system_address, star_system, star_pos_x, star_pos_y, star_pos_z,
                is_external, visit_count, first_visited, last_visited
            ) VALUES (?, ?, 10.0, 20.0, 30.0, 1, 0, NULL, NULL)
        """, (sys_addr, sys_name))
        conn.commit()

        parser = JournalParser(conn)
        jump_event = {
            "timestamp": "2026-09-13T12:00:00Z",
            "event": "FSDJump",
            "StarSystem": sys_name,
            "SystemAddress": sys_addr,
            "StarPos": [10.0, 20.0, 30.0],
            "FuelLevel": 15.0,
            "FuelCapacity": 32.0
        }
        parser.process_journal_line(json.dumps(jump_event))
        conn.commit()

        row = conn.execute("SELECT is_external, visit_count, first_visited, last_visited FROM systems WHERE system_address = ?", (sys_addr,)).fetchone()
        assert row is not None
        assert row["is_external"] == 0
        assert row["visit_count"] == 1
        assert row["first_visited"] == "2026-09-13T12:00:00Z"
        assert row["last_visited"] == "2026-09-13T12:00:00Z"

def test_location_clears_external_flag():
    sys_addr = 888111222334
    sys_name = "External Location System"

    with get_db_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO systems (
                system_address, star_system, star_pos_x, star_pos_y, star_pos_z,
                is_external, visit_count, first_visited, last_visited
            ) VALUES (?, ?, 10.0, 20.0, 30.0, 1, 0, NULL, NULL)
        """, (sys_addr, sys_name))
        conn.commit()

        parser = JournalParser(conn)
        loc_event = {
            "timestamp": "2026-09-13T13:00:00Z",
            "event": "Location",
            "StarSystem": sys_name,
            "SystemAddress": sys_addr,
            "StarPos": [10.0, 20.0, 30.0]
        }
        parser.process_journal_line(json.dumps(loc_event))
        conn.commit()

        row = conn.execute("SELECT is_external, visit_count, first_visited FROM systems WHERE system_address = ?", (sys_addr,)).fetchone()
        assert row is not None
        assert row["is_external"] == 0
        assert row["visit_count"] == 1
        assert row["first_visited"] == "2026-09-13T13:00:00Z"

def test_station_events_ingestion_and_api(client):
    sys_addr = 777111222333
    sys_name = "Station Test System"

    with get_db_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO systems (
                system_address, star_system, star_pos_x, star_pos_y, star_pos_z,
                is_external, visit_count
            ) VALUES (?, ?, 0.0, 0.0, 0.0, 0, 1)
        """, (sys_addr, sys_name))
        conn.execute("""
            INSERT OR REPLACE INTO bodies (
                body_id, system_address, body_name, planet_class
            ) VALUES (1, ?, 'Station Test System 1', 'High metal content world')
        """, (sys_addr,))
        conn.commit()

        parser = JournalParser(conn)
        
        # 1. Docked event
        docked_event = {
            "timestamp": "2026-09-13T14:00:00Z",
            "event": "Docked",
            "StationName": "Alpha Orbital",
            "StationType": "Coriolis",
            "MarketID": 1280001,
            "SystemAddress": sys_addr,
            "StarSystem": sys_name,
            "Body": "Station Test System 1",
            "BodyID": 1,
            "DistFromStarLS": 150.5,
            "StationFaction": {"Name": "Test Corp"},
            "StationGovernment": "$government_Democracy;",
            "StationAllegiance": "Federation",
            "StationEconomy": "$economy_Industrial;"
        }
        parser.process_journal_line(json.dumps(docked_event))

        # 2. ApproachSettlement event
        settlement_event = {
            "timestamp": "2026-09-13T14:10:00Z",
            "event": "ApproachSettlement",
            "Name": "Bravo Base",
            "MarketID": 1280002,
            "SystemAddress": sys_addr,
            "BodyName": "Station Test System 1",
            "BodyID": 1,
            "Latitude": -12.3456,
            "Longitude": 78.9012
        }
        parser.process_journal_line(json.dumps(settlement_event))
        conn.commit()

        # Check DB
        stations = conn.execute("SELECT * FROM stations WHERE system_address = ? ORDER BY station_name", (sys_addr,)).fetchall()
        assert len(stations) == 2
        alpha = next(s for s in stations if s["station_name"] == "Alpha Orbital")
        assert alpha["station_type"] == "Coriolis"
        assert alpha["distance_to_arrival_ls"] == 150.5
        assert alpha["controlling_faction"] == "Test Corp"

        bravo = next(s for s in stations if s["station_name"] == "Bravo Base")
        assert bravo["latitude"] == -12.3456
        assert bravo["longitude"] == 78.9012
        assert bravo["is_planetary"] == 1

    # Check API /api/system/{sys_addr}
    res = client.get(f"/api/system/{sys_addr}")
    assert res.status_code == 200
    data = res.json()
    assert "stations" in data
    assert len(data["stations"]) == 2

    # Check stations attached to body
    body = next(b for b in data["bodies"] if b["body_name"] == "Station Test System 1")
    assert "stations" in body
    assert len(body["stations"]) == 2

def test_celestial_filters_all_and_any(client):
    sys_both = 555001
    sys_ecc_only = 555002
    sys_highg_only = 555003
    sys_normal = 555004

    with get_db_connection() as conn:
        for s_addr, s_name in [(sys_both, "Sys Both"), (sys_ecc_only, "Sys Ecc"), (sys_highg_only, "Sys HighG"), (sys_normal, "Sys Normal")]:
            conn.execute("""
                INSERT OR REPLACE INTO systems (system_address, star_system, star_pos_x, star_pos_y, star_pos_z, visit_count, last_visited)
                VALUES (?, ?, 0, 0, 0, 1, '2026-09-13T15:00:00Z')
            """, (s_addr, s_name))

        # Both: eccentricity 0.65, landable=1, surface_gravity_g 2.0
        conn.execute("""
            INSERT OR REPLACE INTO bodies (body_id, system_address, body_name, eccentricity, landable, surface_gravity_g, planet_class)
            VALUES (1, ?, 'Sys Both 1', 0.65, 1, 2.0, 'High metal content world')
        """, (sys_both,))

        # Ecc only: eccentricity 0.7, landable=1, surface_gravity_g 0.8
        conn.execute("""
            INSERT OR REPLACE INTO bodies (body_id, system_address, body_name, eccentricity, landable, surface_gravity_g, planet_class)
            VALUES (1, ?, 'Sys Ecc 1', 0.7, 1, 0.8, 'High metal content world')
        """, (sys_ecc_only,))

        # High-G only: eccentricity 0.05, landable=1, surface_gravity_g 2.5
        conn.execute("""
            INSERT OR REPLACE INTO bodies (body_id, system_address, body_name, eccentricity, landable, surface_gravity_g, planet_class)
            VALUES (1, ?, 'Sys HighG 1', 0.05, 1, 2.5, 'High metal content world')
        """, (sys_highg_only,))

        # Normal: eccentricity 0.01, landable=0, surface_gravity_g 1.0
        conn.execute("""
            INSERT OR REPLACE INTO bodies (body_id, system_address, body_name, eccentricity, landable, surface_gravity_g, planet_class)
            VALUES (1, ?, 'Sys Normal 1', 0.01, 0, 1.0, 'High metal content world')
        """, (sys_normal,))
        conn.commit()

    # Query ALL mode: both eccentric AND high_g required (limit=500 to ensure test systems included)
    res_all = client.get("/api/systems", params={
        "celestial_filters": "eccentric,high_g",
        "celestial_match_mode": "all",
        "limit": 500
    })
    assert res_all.status_code == 200
    names_all = [s["star_system"] for s in res_all.json()["systems"]]
    assert "Sys Both" in names_all
    assert "Sys Ecc" not in names_all
    assert "Sys HighG" not in names_all
    assert "Sys Normal" not in names_all

    # Query ANY mode: eccentric OR high_g (limit=500)
    res_any = client.get("/api/systems", params={
        "celestial_filters": "eccentric,high_g",
        "celestial_match_mode": "any",
        "limit": 500
    })
    assert res_any.status_code == 200
    names_any = [s["star_system"] for s in res_any.json()["systems"]]
    assert "Sys Both" in names_any
    assert "Sys Ecc" in names_any
    assert "Sys HighG" in names_any
    assert "Sys Normal" not in names_any

def test_edsm_stations_import():
    sys_addr = 666111222333
    sys_name = "EDSM Station Test System"

    with get_db_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO systems (system_address, star_system, star_pos_x, star_pos_y, star_pos_z, visit_count)
            VALUES (?, ?, 0, 0, 0, 1)
        """, (sys_addr, sys_name))
        conn.commit()

        fake_edsm_response = {
            "name": sys_name,
            "id": 9999,
            "stations": [
                {
                    "name": "Explorer Gateway",
                    "type": "Orbis Starport",
                    "distanceToArrival": 420.0,
                    "allegiance": "Empire",
                    "economy": "Extraction",
                    "government": "Patronage",
                    "controllingFaction": {"name": "Citizens of Sol"}
                },
                {
                    "name": "Outpost Charlie",
                    "type": "Planetary Settlement",
                    "distanceToArrival": 850.5,
                    "body": {
                        "name": "EDSM Station Test System 3 a",
                        "latitude": 35.6895,
                        "longitude": 139.6917
                    }
                }
            ]
        }

        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps(fake_edsm_response).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp

        with patch("urllib.request.urlopen", return_value=mock_resp):
            imported_count = edsm_service._import_and_complete_stations(conn, sys_addr, sys_name)
            conn.commit()

        assert imported_count == 2

        stations = conn.execute("SELECT * FROM stations WHERE system_address = ? ORDER BY station_name", (sys_addr,)).fetchall()
        assert len(stations) == 2

        gateway = next(s for s in stations if s["station_name"] == "Explorer Gateway")
        assert gateway["station_type"] == "Orbis Starport"
        assert gateway["distance_to_arrival_ls"] == 420.0
        assert gateway["controlling_faction"] == "Citizens of Sol"
        assert gateway["is_planetary"] == 0

        outpost = next(s for s in stations if s["station_name"] == "Outpost Charlie")
        assert outpost["is_planetary"] == 1
        assert outpost["latitude"] == 35.6895
        assert outpost["longitude"] == 139.6917
        assert outpost["body_name"] == "EDSM Station Test System 3 a"
