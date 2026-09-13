import os
import sqlite3
import pytest
from fastapi.testclient import TestClient
from app.server.api import app
from app.db.database import get_db_connection, init_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    test_db = str(tmp_path / "test_stellar.db")

    def get_test_db():
        c = sqlite3.connect(test_db)
        c.row_factory = sqlite3.Row
        return c

    monkeypatch.setattr("app.server.api.get_db_connection", get_test_db)
    monkeypatch.setattr("app.db.database.get_db_connection", get_test_db)

    conn = get_test_db()
    init_db(conn)
    c = conn.cursor()

    # Insert test systems with different main stars
    c.execute("""
        INSERT INTO systems (system_address, star_system, main_star_type, total_potential_value, last_visited)
        VALUES (1001, 'System O-Star', 'O', 50000000, '2026-09-01T12:00:00'),
               (1002, 'System M-Dwarf', 'M', 10000000, '2026-09-02T12:00:00'),
               (1003, 'System BlackHole', 'H', 80000000, '2026-09-03T12:00:00'),
               (1004, 'System Binary-N-H', 'N', 90000000, '2026-09-04T12:00:00')
    """)

    # Insert bodies for these systems:
    # Sys 1001 has O main star
    c.execute("INSERT INTO bodies (system_address, body_id, body_name, star_type) VALUES (1001, 1, 'System O-Star A', 'O')")
    
    # Sys 1002 has M main star and companion L brown dwarf
    c.execute("INSERT INTO bodies (system_address, body_id, body_name, star_type) VALUES (1002, 1, 'System M-Dwarf A', 'M')")
    c.execute("INSERT INTO bodies (system_address, body_id, body_name, star_type) VALUES (1002, 2, 'System M-Dwarf B', 'L')")
    
    # Sys 1003 has H (Black Hole)
    c.execute("INSERT INTO bodies (system_address, body_id, body_name, star_type) VALUES (1003, 1, 'System BlackHole A', 'H')")
    
    # Sys 1004 has Neutron (N) AND Black Hole (H) in the same system
    c.execute("INSERT INTO bodies (system_address, body_id, body_name, star_type) VALUES (1004, 1, 'System Binary-N-H A', 'N')")
    c.execute("INSERT INTO bodies (system_address, body_id, body_name, star_type) VALUES (1004, 2, 'System Binary-N-H B', 'H')")

    conn.commit()
    conn.close()

def test_sort_by_main_star_type():
    # Ascending spectral order: O -> M -> N -> H
    res = client.get("/api/systems?sort_by=main_star_type&sort_order=asc&sort_mode=strict")
    assert res.status_code == 200
    data = res.json()
    names = [s["star_system"] for s in data["systems"]]
    assert names[0] == "System O-Star"
    assert names[1] == "System M-Dwarf"
    assert names[2] == "System Binary-N-H" # N = 160
    assert names[3] == "System BlackHole"  # H = 170

    # Descending spectral order: H -> N -> M -> O
    res_desc = client.get("/api/systems?sort_by=main_star_type&sort_order=desc&sort_mode=strict")
    assert res_desc.status_code == 200
    names_desc = [s["star_system"] for s in res_desc.json()["systems"]]
    assert names_desc[0] == "System BlackHole"
    assert names_desc[1] == "System Binary-N-H"
    assert names_desc[-1] == "System O-Star"

def test_filter_by_stellar_types_any():
    # Search systems containing L or N (should match Sys 1002 and Sys 1004)
    res = client.get("/api/systems?star_types=L,N&star_match_mode=any")
    assert res.status_code == 200
    addrs = [s["system_address"] for s in res.json()["systems"]]
    assert 1002 in addrs
    assert 1004 in addrs
    assert 1001 not in addrs
    assert 1003 not in addrs

def test_filter_by_stellar_types_all():
    # Search systems containing BOTH N and H (should ONLY match Sys 1004)
    res = client.get("/api/systems?star_types=N,H&star_match_mode=all")
    assert res.status_code == 200
    systems = res.json()["systems"]
    assert len(systems) == 1
    assert systems[0]["system_address"] == 1004
    assert systems[0]["star_system"] == "System Binary-N-H"

def test_filter_aebe_collision_prevention():
    """Ensure AeBe (and subtypes like AeBe2) does not collide with Class A or Class B filters, and is found by AeBe filter."""
    from app.server.api import get_db_connection as get_api_db
    conn = get_api_db()
    c = conn.cursor()
    # Add an A-type system, a B-type system, and AeBe systems (both base AeBe and subclass AeBe2)
    c.execute("""
        INSERT OR REPLACE INTO systems (system_address, star_system, main_star_type, total_potential_value, last_visited)
        VALUES (2001, 'System Pure A', 'A', 1000, '2026-09-05T12:00:00'),
               (2002, 'System Pure B', 'B', 2000, '2026-09-05T12:00:00'),
               (2003, 'System Herbig AeBe Base', 'AeBe', 3000, '2026-09-05T12:00:00'),
               (2004, 'System Herbig AeBe2 Subclass', 'AeBe2', 4000, '2026-09-05T12:00:00')
    """)
    c.execute("DELETE FROM bodies WHERE system_address IN (2001, 2002, 2003, 2004)")
    c.execute("INSERT INTO bodies (system_address, body_id, body_name, star_type) VALUES (2001, 1, 'System Pure A 1', 'A')")
    c.execute("INSERT INTO bodies (system_address, body_id, body_name, star_type) VALUES (2002, 1, 'System Pure B 1', 'B')")
    c.execute("INSERT INTO bodies (system_address, body_id, body_name, star_type) VALUES (2003, 1, 'System Herbig AeBe Base 1', 'AeBe')")
    c.execute("INSERT INTO bodies (system_address, body_id, body_name, star_type) VALUES (2004, 1, 'System Herbig AeBe2 Subclass 1', 'AeBe2')")
    conn.commit()
    conn.close()

    # 1. Searching for 'A' should match 2001, but NOT 2003 or 2004
    res_a = client.get("/api/systems?star_types=A")
    assert res_a.status_code == 200
    addrs_a = [s["system_address"] for s in res_a.json()["systems"]]
    assert 2001 in addrs_a
    assert 2003 not in addrs_a
    assert 2004 not in addrs_a

    # 2. Searching for 'B' should match 2002, but NOT 2003 or 2004
    res_b = client.get("/api/systems?star_types=B")
    assert res_b.status_code == 200
    addrs_b = [s["system_address"] for s in res_b.json()["systems"]]
    assert 2002 in addrs_b
    assert 2003 not in addrs_b
    assert 2004 not in addrs_b

    # 3. Searching for 'AeBe' should match BOTH 2003 and 2004, but NOT 2001 or 2002
    res_aebe = client.get("/api/systems?star_types=AeBe")
    assert res_aebe.status_code == 200
    addrs_aebe = [s["system_address"] for s in res_aebe.json()["systems"]]
    assert 2003 in addrs_aebe
    assert 2004 in addrs_aebe
    assert 2001 not in addrs_aebe
    assert 2002 not in addrs_aebe

