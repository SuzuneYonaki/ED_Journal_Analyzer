"""
Unit tests for Landable celestial body types (HMC, Metal Rich, Rocky, Icy, Rocky Ice),
Ringed Landables, and Planetary Mining Location filtering and radius summary.
"""

import json
import sqlite3
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.db.database import init_db
from app.server.api import app


def test_landable_mining_filters_and_radius_summary(tmp_path):
    db_path = str(tmp_path / "test_mining.db")

    def get_test_db():
        c = sqlite3.connect(db_path)
        c.row_factory = sqlite3.Row
        return c

    conn = get_test_db()
    init_db(conn)
    cursor = conn.cursor()

    # System 1: Has Landable HMC (radius 2,400km) and Landable Ringed Rocky (radius 1,200km) with 7 mining signals
    cursor.execute("""
        INSERT INTO systems (system_address, star_system, total_potential_value, scanned_bodies, has_landable, avg_landable_radius, last_visited)
        VALUES (3001, 'Mining Alpha', 5000000, 2, 1, 1800000.0, '2026-09-05T10:00:00')
    """)
    cursor.execute("""
        INSERT INTO bodies (system_address, body_id, body_name, planet_class, landable, radius, surface_gravity_g, rings, mining_signals)
        VALUES (3001, 1, 'Mining Alpha 1', 'High metal content body', 1, 2400000.0, 0.45, NULL, 0)
    """)
    cursor.execute("""
        INSERT INTO bodies (system_address, body_id, body_name, planet_class, landable, radius, surface_gravity_g, rings, mining_signals)
        VALUES (3001, 2, 'Mining Alpha 2', 'Rocky body', 1, 1200000.0, 0.22, '[{"Name":"Mining Alpha 2 A Ring"}]', 7)
    """)

    # System 2: Has Non-landable Gas Giant, Non-landable HMC body, and Landable Icy body (radius 800km)
    cursor.execute("""
        INSERT INTO systems (system_address, star_system, total_potential_value, scanned_bodies, has_landable, avg_landable_radius, last_visited)
        VALUES (3002, 'Icy Beta', 1000000, 3, 1, 800000.0, '2026-09-05T11:00:00')
    """)
    cursor.execute("""
        INSERT INTO bodies (system_address, body_id, body_name, planet_class, landable, radius, surface_gravity_g, rings, mining_signals)
        VALUES (3002, 1, 'Icy Beta 1', 'Sudarsky class I gas giant', 0, 45000000.0, 1.8, '[{"Name":"Ring"}]', 0)
    """)
    cursor.execute("""
        INSERT INTO bodies (system_address, body_id, body_name, planet_class, landable, radius, surface_gravity_g, rings, mining_signals)
        VALUES (3002, 2, 'Icy Beta 2', 'High metal content body', 0, 3000000.0, 0.6, NULL, 0)
    """)
    cursor.execute("""
        INSERT INTO bodies (system_address, body_id, body_name, planet_class, landable, radius, surface_gravity_g, rings, mining_signals)
        VALUES (3002, 3, 'Icy Beta 3', 'Icy body', 1, 800000.0, 0.15, NULL, 0)
    """)

    # System 3: Has Metal Rich landable and Rocky Ice landable
    cursor.execute("""
        INSERT INTO systems (system_address, star_system, total_potential_value, scanned_bodies, has_landable, avg_landable_radius, last_visited)
        VALUES (3003, 'Metal Gamma', 3000000, 2, 1, 1500000.0, '2026-09-05T12:00:00')
    """)
    cursor.execute("""
        INSERT INTO bodies (system_address, body_id, body_name, planet_class, landable, radius, surface_gravity_g, rings, mining_signals)
        VALUES (3003, 1, 'Metal Gamma 1', 'Metal rich body', 1, 1800000.0, 0.75, NULL, 0)
    """)
    cursor.execute("""
        INSERT INTO bodies (system_address, body_id, body_name, planet_class, landable, radius, surface_gravity_g, rings, mining_signals)
        VALUES (3003, 2, 'Metal Gamma 2', 'Rocky ice body', 1, 1200000.0, 0.28, NULL, 0)
    """)

    conn.commit()
    conn.close()

    with patch("app.server.api.get_db_connection", side_effect=get_test_db):
        client = TestClient(app)

        # 1. Test filtering by HMC landable: System 1 has Landable HMC. System 2 has non-landable HMC so it must be ignored!
        res_hmc = client.get("/api/systems", params={"has_landable_hmc": "true"})
        assert res_hmc.status_code == 200
        hmc_sys_names = [s["star_system"] for s in res_hmc.json()["systems"]]
        assert hmc_sys_names == ["Mining Alpha"]

        # 2. Test filtering by Ringed Landable: System 1 body 2 is a Rocky landable with rings. System 2 gas giant has rings but is not landable!
        res_ringed = client.get("/api/systems", params={"has_landable_ringed": "true"})
        assert res_ringed.status_code == 200
        ringed_sys_names = [s["star_system"] for s in res_ringed.json()["systems"]]
        assert ringed_sys_names == ["Mining Alpha"]

        # 3. Test filtering by Mining Signals: System 1 body 2 has 7 mining signals.
        res_mining = client.get("/api/systems", params={"has_mining_signals": "true"})
        assert res_mining.status_code == 200
        mining_sys_names = [s["star_system"] for s in res_mining.json()["systems"]]
        assert mining_sys_names == ["Mining Alpha"]

        # 4. Test filtering by Metal Rich: Only System 3
        res_mr = client.get("/api/systems", params={"has_landable_metal_rich": "true"})
        assert res_mr.status_code == 200
        mr_sys_names = [s["star_system"] for s in res_mr.json()["systems"]]
        assert mr_sys_names == ["Metal Gamma"]

        # 5. Test filtering by Rocky Ice: Only System 3
        res_ri = client.get("/api/systems", params={"has_landable_rocky_ice": "true"})
        assert res_ri.status_code == 200
        ri_sys_names = [s["star_system"] for s in res_ri.json()["systems"]]
        assert ri_sys_names == ["Metal Gamma"]

        # 6. Test filtering by Icy Landable: Only System 2
        res_icy = client.get("/api/systems", params={"has_landable_icy": "true"})
        assert res_icy.status_code == 200
        icy_sys_names = [s["star_system"] for s in res_icy.json()["systems"]]
        assert icy_sys_names == ["Icy Beta"]

        # 7. Test landable_bodies summary payload in systems response
        res_all = client.get("/api/systems", params={"sort_by": "last_visited", "sort_order": "asc"})
        assert res_all.status_code == 200
        sys1 = next(s for s in res_all.json()["systems"] if s["system_address"] == 3001)
        assert len(sys1["landable_bodies"]) == 2
        
        # Verify first body (HMC, radius 2,400,000 m -> 2400 km)
        b1 = sys1["landable_bodies"][0]
        assert b1["type"] == "HMC"
        assert b1["radius_km"] == 2400
        assert b1["is_ringed"] is False
        assert b1["mining_signals"] == 0

        # Verify second body (Rocky, radius 1,200,000 m -> 1200 km, Ringed, 7 mining signals)
        b2 = sys1["landable_bodies"][1]
        assert b2["type"] == "Rocky"
        assert b2["radius_km"] == 1200
        assert b2["is_ringed"] is True
        assert b2["mining_signals"] == 7
