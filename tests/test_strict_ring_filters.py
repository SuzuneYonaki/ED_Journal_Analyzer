"""
Unit tests for strict genuine ring filters (excluding asteroid belts / AB).
Verifies:
1. Anomaly detection (ringed_star, giant_ring) ignores asteroid belts.
2. Stellar physics wide ring analyzer ignores asteroid belts.
3. API celestial filters (ringed, ringed_star, wide_ring) strictly match genuine rings.

All code, strings, and docstrings are strictly English ASCII.
"""

import json
import pytest
from starlette.testclient import TestClient
from app.analyzer.anomaly_finder import detect_anomalies
from app.analyzer.stellar_physics import StellarPhysicsEngine, SystemData, ScanBody
from app.db.database import init_db, get_db_connection
from app.server.api import app


def test_anomaly_finder_strict_rings():
    """Verify anomaly detector differentiates between asteroid belts and genuine rings."""
    # Star with only an Asteroid Belt
    star_with_belt = {
        "star_type": "M",
        "rings": [
            {
                "Name": "Col 285 Sector A Belt",
                "RingClass": "eRingClass_MetalRich",
                "OuterRad": 15000000000.0 # 15,000,000 km
            }
        ]
    }
    anoms_belt = detect_anomalies(star_with_belt)
    anom_types_belt = [a["type"] for a in anoms_belt]
    assert "ringed_star" not in anom_types_belt
    assert "giant_ring" not in anom_types_belt

    # Star with a genuine Ring
    star_with_ring = {
        "star_type": "Y",
        "rings": [
            {
                "Name": "Col 285 Sector B Ring A",
                "RingClass": "eRingClass_Icy",
                "OuterRad": 6000000000.0 # 6,000,000 km
            }
        ]
    }
    anoms_ring = detect_anomalies(star_with_ring)
    anom_types_ring = [a["type"] for a in anoms_ring]
    assert "ringed_star" in anom_types_ring
    assert "giant_ring" in anom_types_ring

    # Planet with a genuine Giant Wide Ring
    planet_with_wide_ring = {
        "planet_class": "Class II gas giant",
        "rings": [
            {
                "Name": "Col 285 Sector 1 A Ring",
                "RingClass": "eRingClass_Icy",
                "OuterRad": 8000000000.0 # 8,000,000 km
            }
        ]
    }
    anoms_planet = detect_anomalies(planet_with_wide_ring)
    anom_types_planet = [a["type"] for a in anoms_planet]
    assert "giant_ring" in anom_types_planet


def test_stellar_physics_wide_ring_excludes_belts():
    """Verify stellar physics engine skips asteroid belts when evaluating wide rings."""
    body_with_belt = ScanBody(
        body_id=1,
        body_name="Col 285 Sector A",
        star_type="M",
        radius=500000000.0,
        rings=[
            {
                "Name": "Col 285 Sector A Belt",
                "InnerRad": 10000000000.0,
                "OuterRad": 20000000000.0 # width = 10,000,000 km
            }
        ]
    )
    sys_data_belt = SystemData(system_address=123, system_name="Col 285", bodies={1: body_with_belt})
    eval_belt = StellarPhysicsEngine.evaluate(sys_data_belt)
    assert len(eval_belt.raw_features["observatory_details"]["wide_rings"]) == 0

    body_with_ring = ScanBody(
        body_id=2,
        body_name="Col 285 Sector 1",
        planet_class="Class II gas giant",
        radius=60000000.0,
        rings=[
            {
                "Name": "Col 285 Sector 1 A Ring",
                "InnerRad": 100000000.0,
                "OuterRad": 2000000000.0 # width = 1,900,000 km (width >= 1,000,000 km)
            }
        ]
    )
    sys_data_ring = SystemData(system_address=124, system_name="Col 285", bodies={2: body_with_ring})
    eval_ring = StellarPhysicsEngine.evaluate(sys_data_ring)
    assert len(eval_ring.raw_features["observatory_details"]["wide_rings"]) == 1


def test_api_celestial_filters_strict_rings():
    """Verify API endpoint filters out asteroid belts for ringed, ringed_star, and wide_ring."""
    client = TestClient(app)
    init_db()

    sys_belt_star = 888001
    sys_ring_star = 888002
    sys_belt_planet = 888003
    sys_wide_ring_planet = 888004

    with get_db_connection() as conn:
        for s_addr, s_name in [
            (sys_belt_star, "StrictRing-BeltStar"),
            (sys_ring_star, "StrictRing-RingStar"),
            (sys_belt_planet, "StrictRing-BeltPlanet"),
            (sys_wide_ring_planet, "StrictRing-WideRingPlanet")
        ]:
            conn.execute("INSERT OR REPLACE INTO systems (system_address, star_system) VALUES (?, ?)", (s_addr, s_name))
            conn.execute("DELETE FROM bodies WHERE system_address = ?", (s_addr,))

        # 1. Belt Star (Only Asteroid Belt)
        conn.execute("""
            INSERT INTO bodies (system_address, body_id, body_name, star_type, rings, anomalies_json)
            VALUES (?, 1, 'Belt Star A', 'M', ?, '[]')
        """, (sys_belt_star, json.dumps([{"Name": "Belt Star A Belt", "OuterRad": 15000000000.0}])))

        # 2. Ring Star (Genuine Ringed Star)
        conn.execute("""
            INSERT INTO bodies (system_address, body_id, body_name, star_type, rings, anomalies_json)
            VALUES (?, 1, 'Ring Star A', 'Y', ?, '[]')
        """, (sys_ring_star, json.dumps([{"Name": "Ring Star A Ring", "OuterRad": 200000000.0}])))

        # 3. Belt Planet (Only Asteroid Belt entry)
        conn.execute("""
            INSERT INTO bodies (system_address, body_id, body_name, planet_class, rings, anomalies_json)
            VALUES (?, 1, 'Belt Planet 1', 'High metal content body', ?, '[]')
        """, (sys_belt_planet, json.dumps([{"Name": "Belt Planet 1 Belt", "OuterRad": 100000000.0}])))

        # 4. Wide Ring Planet (Genuine Ring with OuterRad >= 5,000,000 km)
        conn.execute("""
            INSERT INTO bodies (system_address, body_id, body_name, planet_class, rings, anomalies_json)
            VALUES (?, 1, 'Wide Ring Planet 1', 'Class II gas giant', ?, '[]')
        """, (sys_wide_ring_planet, json.dumps([{"Name": "Wide Ring Planet 1 A Ring", "OuterRad": 6000000000.0}])))
        conn.commit()

    # Query: ringed
    res_ringed = client.get("/api/systems?q=StrictRing&celestial_filters=ringed")
    assert res_ringed.status_code == 200
    ringed_names = {s["star_system"] for s in res_ringed.json()["systems"]}
    assert "StrictRing-RingStar" in ringed_names
    assert "StrictRing-WideRingPlanet" in ringed_names
    assert "StrictRing-BeltStar" not in ringed_names
    assert "StrictRing-BeltPlanet" not in ringed_names

    # Query: ringed_star
    res_ringed_star = client.get("/api/systems?q=StrictRing&celestial_filters=ringed_star")
    assert res_ringed_star.status_code == 200
    ringed_star_names = {s["star_system"] for s in res_ringed_star.json()["systems"]}
    assert ringed_star_names == {"StrictRing-RingStar"}

    # Query: wide_ring
    res_wide_ring = client.get("/api/systems?q=StrictRing&celestial_filters=wide_ring")
    assert res_wide_ring.status_code == 200
    wide_ring_names = {s["star_system"] for s in res_wide_ring.json()["systems"]}
    assert wide_ring_names == {"StrictRing-WideRingPlanet"}
