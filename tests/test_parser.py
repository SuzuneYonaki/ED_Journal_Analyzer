import pytest
import sqlite3
import json
from app.parser.value_calculator import calculate_planet_value, calculate_star_value, calculate_body_value
from app.parser.journal_parser import JournalParser
from app.analyzer.anomaly_finder import detect_anomalies

def test_value_calculator_elw():
    val = calculate_planet_value("Earthlike body", 1.0, terraformable=True)
    assert val["fss_value"] > 250000
    assert val["dss_value"] > 800000
    assert val["max_potential_value"] > 3000000

def test_value_calculator_black_hole():
    val = calculate_star_value("H", 30.0)
    assert val["fss_value"] > 20000
    assert val["first_discovered_fss"] > 50000

def test_anomaly_detection():
    # Extreme High G body
    body_high_g = {
        "planet_class": "High metal content world",
        "surface_gravity_g": 3.45,
        "landable": True,
        "eccentricity": 0.85,
        "orbital_period": 10000,
        "volcanism": "major water geysers",
        "bio_signals": 4
    }
    anomalies = detect_anomalies(body_high_g)
    tags = [a["tag"] for a in anomalies]
    assert any("Extreme High-G" in t for t in tags)
    assert any("Extreme Eccentricity" in t for t in tags)
    assert any("Active Volcanism" in t for t in tags)

    # Heavy Mass code anomaly: G-Star in H-box or E-box
    body_heavy_g = {
        "star_type": "G",
        "star_system": "Synuefe AA-A h1"
    }
    anomalies_heavy = detect_anomalies(body_heavy_g)
    tags_heavy = [a["tag"] for a in anomalies_heavy]
    assert any("Heavy Mass Code" in t for t in tags_heavy)

    # Heavy Mass code anomaly: Neutron Star in F-box
    body_heavy_n = {
        "star_type": "N",
        "star_system": "Eol Prou AB-C f1-100"
    }
    anomalies_n = detect_anomalies(body_heavy_n)
    tags_n = [a["tag"] for a in anomalies_n]
    assert any("Heavy Mass Code" in t for t in tags_n)

    # Normal Mass code: G-Star in C-box (Not anomaly)
    body_normal_g = {
        "star_type": "G",
        "star_system": "Eol Prou AB-C c1-100"
    }
    anomalies_norm = detect_anomalies(body_normal_g)
    assert not any("Heavy Mass Code" in a.get("tag", "") for a in anomalies_norm)

    # Close Binary Star (< 20 Ls)
    body_close_binary = {
        "star_type": "M",
        "distance_from_arrival_ls": 12.4
    }
    anomalies_cb = detect_anomalies(body_close_binary)
    tags_cb = [a["tag"] for a in anomalies_cb]
    assert any("Close Binary Star" in t for t in tags_cb)

    # Tight Binary Orbit (semi_major_axis < 20 Ls = 5.99e9 m)
    body_tight_orbit = {
        "star_type": "K",
        "semi_major_axis": 299792458.0 * 5.0  # 5 light seconds
    }
    anomalies_to = detect_anomalies(body_tight_orbit)
    tags_to = [a["tag"] for a in anomalies_to]
    assert any("Tight Binary Orbit" in t for t in tags_to)

def test_journal_parser_in_memory():
    from app.db.database import init_db
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)

    parser = JournalParser(conn)
    # Feed FSDJump
    parser.process_journal_line(json.dumps({
        "timestamp": "2026-08-20T10:00:00Z",
        "event": "FSDJump",
        "StarSystem": "Test System Prime",
        "SystemAddress": 99887766,
        "StarPos": [100.5, -20.0, 350.25],
        "JumpDist": 45.2,
        "FuelUsed": 3.5
    }))

    # Feed Scan
    parser.process_journal_line(json.dumps({
        "timestamp": "2026-08-20T10:01:00Z",
        "event": "Scan",
        "StarSystem": "Test System Prime",
        "SystemAddress": 99887766,
        "BodyName": "Test System Prime 3",
        "BodyID": 3,
        "DistanceFromArrivalLS": 450.0,
        "PlanetClass": "Earthlike body",
        "MassEM": 0.95,
        "SurfaceGravity": 9.75,
        "Landable": False,
        "TerraformState": "Terraformable"
    }))
    parser.flush_dirty_systems()

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM systems WHERE system_address = 99887766")
    sys_row = cursor.fetchone()
    assert sys_row is not None
    assert sys_row["star_system"] == "Test System Prime"
    assert sys_row["has_elw"] == 1
    assert sys_row["total_potential_value"] > 0


def test_planetary_mining_signals():
    from app.db.database import init_db
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)

    parser = JournalParser(conn)
    # 1. FSSBodySignals with Planetary Mining Location
    parser.process_journal_line(json.dumps({
        "timestamp": "2026-09-02T21:35:02Z",
        "event": "FSSBodySignals",
        "BodyName": "Byeia Ain YP-M d8-326 2 a",
        "BodyID": 16,
        "SystemAddress": 11211987177419,
        "Signals": [
            { "Type": "$PlanetaryMiningLocation_Name;", "Type_Localised": "Planetary Mining Location", "Count": 7 }
        ]
    }))

    # 2. Detailed Scan
    parser.process_journal_line(json.dumps({
        "timestamp": "2026-09-02T21:35:03Z",
        "event": "Scan",
        "ScanType": "Detailed",
        "BodyName": "Byeia Ain YP-M d8-326 2 a",
        "BodyID": 16,
        "Parents": [ {"Planet": 14}, {"Star": 0} ],
        "StarSystem": "Byeia Ain YP-M d8-326",
        "SystemAddress": 11211987177419,
        "DistanceFromArrivalLS": 1875.859928,
        "PlanetClass": "Rocky body",
        "Landable": True
    }))
    parser.flush_dirty_systems()

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bodies WHERE system_address = ? AND body_id = ?", (11211987177419, 16))
    body = cursor.fetchone()
    assert body is not None
    assert body["mining_signals"] == 7
    assert body["bio_signals"] == 0
    assert body["geo_signals"] == 0


def test_avg_landable_radius_calculation_and_sorting():
    from app.db.database import init_db
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)

    parser = JournalParser(conn)

    # System A has two landable bodies: radius 1,000,000 m (1,000 km) and 2,000,000 m (2,000 km) -> avg = 1,500,000 m
    # and one non-landable body with radius 10,000,000 m (should be ignored)
    parser.process_journal_line(json.dumps({
        "timestamp": "2026-09-05T01:00:00Z",
        "event": "Scan",
        "StarSystem": "System A",
        "SystemAddress": 1001,
        "BodyName": "System A 1",
        "BodyID": 1,
        "PlanetClass": "Rocky body",
        "Landable": True,
        "Radius": 1000000.0
    }))
    parser.process_journal_line(json.dumps({
        "timestamp": "2026-09-05T01:01:00Z",
        "event": "Scan",
        "StarSystem": "System A",
        "SystemAddress": 1001,
        "BodyName": "System A 2",
        "BodyID": 2,
        "PlanetClass": "High metal content body",
        "Landable": True,
        "Radius": 2000000.0
    }))
    parser.process_journal_line(json.dumps({
        "timestamp": "2026-09-05T01:02:00Z",
        "event": "Scan",
        "StarSystem": "System A",
        "SystemAddress": 1001,
        "BodyName": "System A 3",
        "BodyID": 3,
        "PlanetClass": "Gas giant with water based life",
        "Landable": False,
        "Radius": 10000000.0
    }))

    # System B has one landable body: radius 3,000,000 m (3,000 km) -> avg = 3,000,000 m
    parser.process_journal_line(json.dumps({
        "timestamp": "2026-09-05T01:05:00Z",
        "event": "Scan",
        "StarSystem": "System B",
        "SystemAddress": 1002,
        "BodyName": "System B 1",
        "BodyID": 1,
        "PlanetClass": "Rocky body",
        "Landable": True,
        "Radius": 3000000.0
    }))

    # System C has NO landable bodies
    parser.process_journal_line(json.dumps({
        "timestamp": "2026-09-05T01:10:00Z",
        "event": "Scan",
        "StarSystem": "System C",
        "SystemAddress": 1003,
        "BodyName": "System C 1",
        "BodyID": 1,
        "PlanetClass": "Gas giant",
        "Landable": False,
        "Radius": 50000000.0
    }))

    parser.flush_dirty_systems()

    cursor = conn.cursor()
    cursor.execute("SELECT star_system, avg_landable_radius FROM systems WHERE system_address = 1001")
    row_a = cursor.fetchone()
    assert row_a is not None
    assert row_a["avg_landable_radius"] == 1500000.0

    cursor.execute("SELECT star_system, avg_landable_radius FROM systems WHERE system_address = 1002")
    row_b = cursor.fetchone()
    assert row_b is not None
    assert row_b["avg_landable_radius"] == 3000000.0

    cursor.execute("SELECT star_system, avg_landable_radius FROM systems WHERE system_address = 1003")
    row_c = cursor.fetchone()
    assert row_c is not None
    assert row_c["avg_landable_radius"] == 0.0

    # Test sorting: DESC should give System B (3,000km) -> System A (1,500km) -> System C (0km)
    cursor.execute("""
        SELECT star_system FROM systems 
        ORDER BY (avg_landable_radius IS NULL OR avg_landable_radius = 0) ASC, avg_landable_radius DESC
    """)
    desc_systems = [r["star_system"] for r in cursor.fetchall()]
    assert desc_systems == ["System B", "System A", "System C"]

    # Test sorting: ASC should give System A (1,500km) -> System B (3,000km) -> System C (0km at end)
    cursor.execute("""
        SELECT star_system FROM systems 
        ORDER BY (avg_landable_radius IS NULL OR avg_landable_radius = 0) ASC, avg_landable_radius ASC
    """)
    asc_systems = [r["star_system"] for r in cursor.fetchall()]
    assert asc_systems == ["System A", "System B", "System C"]


def test_composite_and_tertiary_sorting(tmp_path):
    from fastapi.testclient import TestClient
    from app.server.api import app
    from unittest.mock import patch

    db_path = str(tmp_path / "test_sorting.db")

    def get_test_db():
        c = sqlite3.connect(db_path)
        c.row_factory = sqlite3.Row
        return c

    conn = get_test_db()
    from app.db.database import init_db
    init_db(conn)

    cursor = conn.cursor()
    # Insert 3 systems for composite and multi-tier testing
    # System Alpha: highest value, but lowest radius and bio
    cursor.execute("""
        INSERT INTO systems (
            system_address, star_system, total_potential_value, total_fss_value, 
            avg_landable_radius, total_bio_signals, first_discovered_bodies, 
            sol_distance_ly, scanned_bodies, visit_count, last_visited, first_visited
        ) VALUES (
            2001, 'System Alpha', 10000000, 500000, 
            1000000.0, 1, 0, 
            100.0, 10, 1, '2026-09-01T10:00:00', '2026-09-01T10:00:00'
        )
    """)
    # System Beta: almost same value as Alpha (9.9M), but max radius (5M) and moderate bio (5)
    cursor.execute("""
        INSERT INTO systems (
            system_address, star_system, total_potential_value, total_fss_value, 
            avg_landable_radius, total_bio_signals, first_discovered_bodies, 
            sol_distance_ly, scanned_bodies, visit_count, last_visited, first_visited
        ) VALUES (
            2002, 'System Beta', 9900000, 500000, 
            5000000.0, 5, 2, 
            200.0, 15, 1, '2026-09-02T10:00:00', '2026-09-02T10:00:00'
        )
    """)
    # System Gamma: lower value (1M), medium radius (2M), highest bio (10)
    cursor.execute("""
        INSERT INTO systems (
            system_address, star_system, total_potential_value, total_fss_value, 
            avg_landable_radius, total_bio_signals, first_discovered_bodies, 
            sol_distance_ly, scanned_bodies, visit_count, last_visited, first_visited
        ) VALUES (
            2003, 'System Gamma', 1000000, 500000, 
            2000000.0, 10, 5, 
            300.0, 20, 1, '2026-09-03T10:00:00', '2026-09-03T10:00:00'
        )
    """)
    conn.commit()
    conn.close()

    with patch("app.server.api.get_db_connection", side_effect=get_test_db):
        client = TestClient(app)

        # 1. Strict mode: 1st=total_potential_value DESC, 2nd=avg_landable_radius DESC, 3rd=total_bio_signals DESC
        # System Alpha (10M) > Beta (9.9M) > Gamma (1M)
        res_strict = client.get("/api/systems", params={
            "sort_by": "total_potential_value",
            "sort_order": "desc",
            "sort_by_2": "avg_landable_radius",
            "sort_order_2": "desc",
            "sort_by_3": "total_bio_signals",
            "sort_order_3": "desc",
            "sort_mode": "strict"
        })
        assert res_strict.status_code == 200
        data_strict = res_strict.json()
        strict_names = [s["star_system"] for s in data_strict["systems"]]
        assert strict_names == ["System Alpha", "System Beta", "System Gamma"]

        # 2. Composite mode (Method B weighted blending):
        # Even though Alpha has slightly higher value (10M vs 9.9M),
        # Beta has drastically larger landable radius (5M vs 1M) and higher bio (5 vs 1).
        # Composite score blends 50% 1st + 35% 2nd + 15% 3rd, making Beta the winner!
        res_comp = client.get("/api/systems", params={
            "sort_by": "total_potential_value",
            "sort_order": "desc",
            "sort_by_2": "avg_landable_radius",
            "sort_order_2": "desc",
            "sort_by_3": "total_bio_signals",
            "sort_order_3": "desc",
            "sort_mode": "composite"
        })
        assert res_comp.status_code == 200
        data_comp = res_comp.json()
        comp_systems = data_comp["systems"]
        comp_names = [s["star_system"] for s in comp_systems]

        # Beta should rank #1 thanks to composite weighting
        assert comp_names[0] == "System Beta"
        assert comp_systems[0]["composite_score"] is not None
        assert comp_systems[0]["composite_score"] > comp_systems[1]["composite_score"]

        # 3. Composite mode with 2 criteria
        res_comp2 = client.get("/api/systems", params={
            "sort_by": "total_potential_value",
            "sort_order": "desc",
            "sort_by_2": "avg_landable_radius",
            "sort_order_2": "desc",
            "sort_mode": "composite"
        })
        assert res_comp2.status_code == 200
        data_comp2 = res_comp2.json()
        assert data_comp2["systems"][0]["star_system"] == "System Beta"
        assert "composite_score" in data_comp2["systems"][0]



