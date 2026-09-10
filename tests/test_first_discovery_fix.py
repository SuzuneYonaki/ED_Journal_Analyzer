import pytest
import sqlite3
import json
from app.db.database import init_db
from app.parser.journal_parser import JournalParser

def test_nav_beacon_scan_not_first_discovered():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)

    parser = JournalParser(conn)
    # Jump to Shinrarta Dezhra
    parser.process_journal_line(json.dumps({
        "timestamp": "2023-02-12T13:00:00Z",
        "event": "FSDJump",
        "StarSystem": "Shinrarta Dezhra",
        "SystemAddress": 3932277477610,
        "Population": 85287324
    }))

    # NavBeacon detail scan for Founders World (ELW)
    parser.process_journal_line(json.dumps({
        "timestamp": "2023-02-12T13:09:30Z",
        "event": "Scan",
        "ScanType": "NavBeaconDetail",
        "StarSystem": "Shinrarta Dezhra",
        "SystemAddress": 3932277477610,
        "BodyName": "Founders World",
        "BodyID": 14,
        "DistanceFromArrivalLS": 361.0,
        "PlanetClass": "Earthlike body",
        "WasDiscovered": False,
        "WasMapped": True
    }))

    # NavBeacon detail scan for Primary Star
    parser.process_journal_line(json.dumps({
        "timestamp": "2023-02-12T13:09:30Z",
        "event": "Scan",
        "ScanType": "NavBeaconDetail",
        "StarSystem": "Shinrarta Dezhra",
        "SystemAddress": 3932277477610,
        "BodyName": "Shinrarta Dezhra",
        "BodyID": 1,
        "DistanceFromArrivalLS": 0.0,
        "StarType": "K",
        "WasDiscovered": False,
        "WasMapped": False
    }))

    parser.flush_dirty_systems()

    cursor = conn.cursor()
    cursor.execute("SELECT was_discovered, was_mapped, scan_type FROM bodies WHERE body_id = 14")
    row_planet = cursor.fetchone()
    assert row_planet["was_discovered"] == 1
    assert row_planet["was_mapped"] == 1
    assert row_planet["scan_type"] == "NavBeaconDetail"

    cursor.execute("SELECT was_discovered, was_mapped, scan_type FROM bodies WHERE body_id = 1")
    row_star = cursor.fetchone()
    assert row_star["was_discovered"] == 1
    assert row_star["scan_type"] == "NavBeaconDetail"

    cursor.execute("SELECT has_elw, has_first_discover, first_discovered_bodies FROM systems WHERE system_address = 3932277477610")
    sys_row = cursor.fetchone()
    assert sys_row["has_elw"] == 1  # Founders World IS an ELW
    assert sys_row["has_first_discover"] == 0  # BUT NOT first discovered by player!
    assert sys_row["first_discovered_bodies"] == 0

def test_deep_space_first_discovery():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)

    parser = JournalParser(conn)
    # Jump to undiscovered system
    parser.process_journal_line(json.dumps({
        "timestamp": "2026-09-01T12:00:00Z",
        "event": "FSDJump",
        "StarSystem": "Dryooe Prou AA-A h1",
        "SystemAddress": 1122334455,
        "Population": 0
    }))

    # Detailed FSS scan of undiscovered ELW
    parser.process_journal_line(json.dumps({
        "timestamp": "2026-09-01T12:02:00Z",
        "event": "Scan",
        "ScanType": "Detailed",
        "StarSystem": "Dryooe Prou AA-A h1",
        "SystemAddress": 1122334455,
        "BodyName": "Dryooe Prou AA-A h1 3",
        "BodyID": 3,
        "DistanceFromArrivalLS": 800.0,
        "PlanetClass": "Earthlike body",
        "WasDiscovered": False,
        "WasMapped": False
    }))

    parser.flush_dirty_systems()

    cursor = conn.cursor()
    cursor.execute("SELECT was_discovered, was_mapped FROM bodies WHERE body_id = 3")
    row_planet = cursor.fetchone()
    assert row_planet["was_discovered"] == 0  # Real first discovery!
    assert row_planet["was_mapped"] == 0

    cursor.execute("SELECT has_elw, has_first_discover, first_discovered_bodies FROM systems WHERE system_address = 1122334455")
    sys_row = cursor.fetchone()
    assert sys_row["has_elw"] == 1
    assert sys_row["has_first_discover"] == 1
    assert sys_row["first_discovered_bodies"] == 1

def test_database_migration_fixes_legacy_navbeacon_records():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)

    cursor = conn.cursor()
    # Insert a populated system
    cursor.execute("""
        INSERT INTO systems (system_address, star_system, population, first_visited, last_visited)
        VALUES (777777, 'Sol System', 18000000000, '2023-01-01', '2023-01-01')
    """)

    # Insert legacy bodies that had was_discovered = 0
    cursor.execute("""
        INSERT INTO bodies (system_address, body_id, body_name, star_system, star_type, was_discovered, was_mapped)
        VALUES (777777, 1, 'Sol', 'Sol System', 'G', 0, 0)
    """)
    cursor.execute("""
        INSERT INTO bodies (system_address, body_id, body_name, star_system, planet_class, was_discovered, was_mapped)
        VALUES (777777, 2, 'Earth', 'Sol System', 'Earthlike body', 0, 1)
    """)
    conn.commit()

    # Re-run init_db migration
    init_db(conn)

    cursor.execute("SELECT was_discovered FROM bodies WHERE body_id = 1")
    assert cursor.fetchone()["was_discovered"] == 1
    cursor.execute("SELECT was_discovered FROM bodies WHERE body_id = 2")
    assert cursor.fetchone()["was_discovered"] == 1

    cursor.execute("SELECT has_first_discover, first_discovered_bodies FROM systems WHERE system_address = 777777")
    sys_row = cursor.fetchone()
    assert sys_row["has_first_discover"] == 0
    assert sys_row["first_discovered_bodies"] == 0
