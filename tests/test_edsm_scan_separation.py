"""
Unit tests to verify strict separation of EDSM_Known bodies from CMDR scan statistics.
"""

import sqlite3
from app.db.database import get_db_connection, init_db
from app.services.edsm.stats_aggregator import update_system_aggregated_stats
from app.parser.journal_parser import JournalParser
from app.services.edsm.body_importer import import_and_complete_bodies


def test_edsm_known_bodies_excluded_from_scanned_and_first_discovery():
    """Ensure EDSM_Known bodies are never counted as CMDR-scanned or first-discovered."""
    conn = get_db_connection()
    init_db(conn)
    c = conn.cursor()

    sys_addr = 8888001
    sys_name = "Isolation System Test"

    c.execute("DELETE FROM bodies WHERE system_address = ?", (sys_addr,))
    c.execute("DELETE FROM systems WHERE system_address = ?", (sys_addr,))

    # Seed system as visited by player but no scans done by player
    c.execute("""
        INSERT OR REPLACE INTO systems (system_address, star_system, visit_count, scanned_bodies, has_first_discover, first_discovered_bodies)
        VALUES (?, ?, 1, 0, 0, 0)
    """, (sys_addr, sys_name))

    # Insert an EDSM_Known body with was_discovered = 1 and discoverer = SomeoneElse
    c.execute("""
        INSERT OR REPLACE INTO bodies (
            system_address, body_id, body_name, star_system, star_type,
            scan_type, was_discovered, edsm_discovered_by, fss_value, dss_value
        ) VALUES (?, 1, 'Isolation System Test A', ?, 'M', 'EDSM_Known', 1, 'CMDR ExplorerX', 15000, 30000)
    """, (sys_addr, sys_name))

    # Insert another EDSM_Known planet where discoverer is unknown/null
    c.execute("""
        INSERT OR REPLACE INTO bodies (
            system_address, body_id, body_name, star_system, planet_class,
            scan_type, was_discovered, edsm_discovered_by, fss_value, dss_value
        ) VALUES (?, 2, 'Isolation System Test 1', ?, 'Icy body', 'EDSM_Known', 1, NULL, 5000, 10000)
    """, (sys_addr, sys_name))
    conn.commit()

    # Recalculate via stats_aggregator
    update_system_aggregated_stats(conn, sys_addr)
    conn.commit()

    c.execute("SELECT scanned_bodies, first_discovered_bodies, has_first_discover, total_fss_value FROM systems WHERE system_address = ?", (sys_addr,))
    row = c.fetchone()
    assert row["scanned_bodies"] == 0
    assert row["first_discovered_bodies"] == 0
    assert row["has_first_discover"] == 0
    assert row["total_fss_value"] == 0

    # Now simulate player scanning body 3
    parser = JournalParser(db_conn=conn)
    parser.current_system_address = sys_addr
    parser.current_star_system = sys_name
    c.execute("""
        INSERT OR REPLACE INTO bodies (
            system_address, body_id, body_name, star_system, planet_class,
            scan_type, was_discovered, fss_value, dss_value
        ) VALUES (?, 3, 'Isolation System Test 2', ?, 'High metal content body', 'Detailed', 0, 50000, 100000)
    """, (sys_addr, sys_name))
    conn.commit()

    parser._update_system_stats(sys_addr)
    conn.commit()

    c.execute("SELECT scanned_bodies, first_discovered_bodies, has_first_discover, total_fss_value FROM systems WHERE system_address = ?", (sys_addr,))
    row2 = c.fetchone()
    # Only player's scanned body is counted!
    assert row2["scanned_bodies"] == 1
    assert row2["first_discovered_bodies"] == 1
    assert row2["has_first_discover"] == 1
    assert row2["total_fss_value"] == 50000
    conn.close()


def test_body_importer_sets_was_discovered_1():
    """Ensure import_and_complete_bodies sets was_discovered=1 even if discoverer is null."""
    conn = get_db_connection()
    init_db(conn)
    c = conn.cursor()

    sys_addr = 8888002
    sys_name = "Imported Test System"
    c.execute("DELETE FROM bodies WHERE system_address = ?", (sys_addr,))
    conn.commit()

    mock_bodies = [
        {
            "bodyId": 1,
            "name": "Imported Test System A",
            "type": "Star",
            "subType": "F (White) Star",
            # No discovery section
        }
    ]

    import_and_complete_bodies(conn, sys_addr, sys_name, mock_bodies)
    conn.commit()

    c.execute("SELECT was_discovered, scan_type FROM bodies WHERE system_address = ? AND body_id = 1", (sys_addr,))
    row = c.fetchone()
    conn.close()

    assert row is not None
    assert row["scan_type"] == "EDSM_Known"
    assert row["was_discovered"] == 1
