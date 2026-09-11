import pytest
import sqlite3
from unittest.mock import patch, MagicMock
from app.db.database import init_db
from app.services.edsm_service import edsm_service, _extract_star_type

@pytest.fixture
def test_db(tmp_path):
    db_file = tmp_path / "test_edsm_import.db"
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    init_db(conn)
    yield conn
    conn.close()

def test_extract_star_type():
    assert _extract_star_type({"subType": "M (Red dwarf) Star", "spectralClass": "M"}) == "M"
    assert _extract_star_type({"subType": "Neutron Star"}) == "N"
    assert _extract_star_type({"subType": "Supermassive Black Hole"}) == "SupermassiveBlackHole"
    assert _extract_star_type({"subType": "Black Hole"}) == "H"
    assert _extract_star_type({"subType": "White Dwarf (DA) Star", "spectralClass": "DA"}) == "DA"
    assert _extract_star_type({"subType": "K (Yellow-Orange giant) Star", "spectralClass": "K"}) == "K"

def test_edsm_body_import_and_value_calc(test_db):
    conn = test_db
    c = conn.cursor()

    sys_addr = 123456789
    sys_name = "Test EDSM System"

    c.execute("""
        INSERT INTO systems (system_address, star_system, total_bodies, scanned_bodies)
        VALUES (?, ?, 2, 0)
    """, (sys_addr, sys_name))
    conn.commit()

    mock_bodies = [
        {
            "id": 101,
            "bodyId": 0,
            "name": "Test EDSM System A",
            "type": "Star",
            "subType": "K (Yellow-Orange giant) Star",
            "spectralClass": "K",
            "distanceToArrival": 0,
            "solarMasses": 1.2,
            "solarRadius": 1.1,
            "surfaceTemperature": 4500,
            "discovery": {
                "commander": "Pioneer Commander",
                "date": "2024-01-01 12:00:00"
            }
        },
        {
            "id": 102,
            "bodyId": 1,
            "name": "Test EDSM System 1",
            "type": "Planet",
            "subType": "Water world",
            "distanceToArrival": 500,
            "earthMasses": 1.5,
            "radius": 6800,
            "gravity": 1.1,
            "surfaceTemperature": 290,
            "surfacePressure": 1.2,
            "isLandable": False,
            "terraformingState": "Candidate for terraforming",
            "semiMajorAxis": 1.1,
            "orbitalPeriod": 380,
            "discovery": {
                "commander": "Explorer CMDR",
                "date": "2024-01-02 15:30:00"
            }
        }
    ]

    edsm_service._import_and_complete_bodies(conn, sys_addr, sys_name, mock_bodies)
    edsm_service._update_system_aggregated_stats(conn, sys_addr)
    conn.commit()

    c.execute("SELECT * FROM bodies WHERE system_address = ? ORDER BY body_id ASC", (sys_addr,))
    bodies = c.fetchall()
    assert len(bodies) == 2

    star = bodies[0]
    assert star["body_name"] == "Test EDSM System A"
    assert star["star_type"] == "K"
    assert star["scan_type"] == "EDSM_Known"
    assert star["was_discovered"] == 1
    assert star["edsm_discovered_by"] == "Pioneer Commander"
    assert star["fss_value"] > 0

    planet = bodies[1]
    assert planet["body_name"] == "Test EDSM System 1"
    assert planet["planet_class"] == "Water world"
    assert planet["scan_type"] == "EDSM_Known"
    assert planet["was_discovered"] == 1
    assert planet["edsm_discovered_by"] == "Explorer CMDR"
    assert planet["terraforming_state"] == "Candidate for terraforming"
    assert planet["fss_value"] > 200000
    assert planet["dss_value"] > 1000000

    c.execute("SELECT * FROM systems WHERE system_address = ?", (sys_addr,))
    sys_row = c.fetchone()
    assert sys_row["scanned_bodies"] == 2
    assert sys_row["main_star_type"] == "K"
    assert sys_row["has_water_world"] == 1
    assert sys_row["has_terraformable"] == 1
    assert sys_row["total_fss_value"] > 200000
    assert sys_row["total_dss_value"] > 1000000

def test_edsm_import_protects_player_scans(test_db):
    conn = test_db
    c = conn.cursor()

    sys_addr = 987654321
    sys_name = "Player Scanned System"

    c.execute("""
        INSERT INTO systems (system_address, star_system, scanned_bodies)
        VALUES (?, ?, 1)
    """, (sys_addr, sys_name))

    c.execute("""
        INSERT INTO bodies (
            system_address, body_id, body_name, star_system, planet_class,
            scan_type, fss_value, dss_value, scan_timestamp
        ) VALUES (
            ?, 1, 'Player Scanned Planet', ?, 'Earthlike body',
            'Detailed', 1234567, 3456789, '2026-09-10T10:00:00Z'
        )
    """, (sys_addr, sys_name))
    conn.commit()

    mock_bodies = [
        {
            "id": 999,
            "bodyId": 1,
            "name": "Player Scanned Planet",
            "type": "Planet",
            "subType": "Earthlike body",
            "discovery": {
                "commander": "External Pioneer",
                "date": "2023-01-01"
            }
        }
    ]

    edsm_service._import_and_complete_bodies(conn, sys_addr, sys_name, mock_bodies)
    conn.commit()

    c.execute("SELECT * FROM bodies WHERE system_address = ? AND body_id = 1", (sys_addr,))
    row = c.fetchone()

    assert row["scan_type"] == "Detailed"
    assert row["scan_timestamp"] == "2026-09-10T10:00:00Z"
    assert row["fss_value"] == 1234567
    assert row["edsm_discovered_by"] == "External Pioneer"
