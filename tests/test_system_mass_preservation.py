"""
Tests verifying total_system_mass and main_star_mass preservation on newly visited systems.
"""

from app.db.database import get_db_connection, init_db
from app.services.edsm.stats_aggregator import update_system_aggregated_stats
from app.server.api import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_api_systems_returns_total_mass_for_new_system():
    """Ensure /api/systems returns total_system_mass even when systems.total_system_mass is NULL."""
    conn = get_db_connection()
    init_db(conn)
    c = conn.cursor()

    sys_addr = 7777001
    sys_name = "New Visited Mass Test"

    c.execute("DELETE FROM bodies WHERE system_address = ?", (sys_addr,))
    c.execute("DELETE FROM systems WHERE system_address = ?", (sys_addr,))

    # Newly visited system: total_system_mass and main_star_mass are NULL initially
    c.execute("""
        INSERT INTO systems (system_address, star_system, visit_count, total_system_mass, main_star_mass, first_visited, last_visited)
        VALUES (?, ?, 1, NULL, NULL, '2026-10-27T10:00:00', '2026-10-27T10:00:00')
    """, (sys_addr, sys_name))

    # CMDR scans main star (1.5 solar masses)
    c.execute("""
        INSERT INTO bodies (system_address, body_id, body_name, star_system, star_type, stellar_mass, distance_from_arrival_ls, scan_type)
        VALUES (?, 0, 'New Visited Mass Test A', ?, 'G', 1.5, 0, 'AutoScan')
    """, (sys_addr, sys_name))

    # CMDR scans companion star (0.8 solar masses)
    c.execute("""
        INSERT INTO bodies (system_address, body_id, body_name, star_system, star_type, stellar_mass, distance_from_arrival_ls, scan_type)
        VALUES (?, 1, 'New Visited Mass Test B', ?, 'M', 0.8, 1200, 'Detailed')
    """, (sys_addr, sys_name))
    conn.commit()

    # Query API /api/systems
    res = client.get("/api/systems?limit=50&sort_by=last_visited&sort_dir=desc")
    assert res.status_code == 200
    data = res.json()
    items = data.get("systems", [])
    matching = next((s for s in items if s["system_address"] == sys_addr), None)

    assert matching is not None
    # total_system_mass must NOT be null! 1.5 + 0.8 = 2.3 M☉
    assert matching["main_star_mass"] == 1.5
    assert matching["total_system_mass"] is not None
    assert abs(matching["total_system_mass"] - 2.3) < 0.01

    # Recalculate via stats_aggregator
    update_system_aggregated_stats(conn, sys_addr)
    conn.commit()

    c.execute("SELECT main_star_mass, total_system_mass FROM systems WHERE system_address = ?", (sys_addr,))
    db_row = c.fetchone()
    assert db_row["main_star_mass"] == 1.5
    assert db_row["total_system_mass"] is not None
    assert abs(db_row["total_system_mass"] - 2.3) < 0.01

    conn.close()
