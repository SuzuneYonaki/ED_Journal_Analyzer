"""
BioInsights & Canonn Exobiology Prediction Engine Accuracy Verification Tests.
Verifies:
1. Zero bio signals suppression (no false alarms on lifeless planets).
2. DSS confirmed genus pruning.
3. Strict 1 species per distinct genus physical law.
4. Correct Pascal-to-Atmosphere low pressure parsing (< 100 Pa).
5. Plain vs -rich atmosphere isolation.
6. Parent star spectral resolution for planetary bodies.

All code, strings, and comments are strictly English ASCII.
"""

import pytest
from app.parser.exobiology import (
    predict_exobiology_candidates,
    get_pressure_atm,
    get_star_type_string,
    match_atmosphere
)


def test_zero_bio_signals_returns_empty():
    """Verify that any body with 0 biological signals produces an empty candidate list (no false alarms)."""
    # 1. Scanned body with bio_signals = 0
    body_zero = {
        "landable": True,
        "planet_class": "High metal content world",
        "atmosphere": "Carbon dioxide",
        "surface_temperature": 230.0,
        "surface_gravity_g": 0.25,
        "surface_pressure": 0.035 * 101325,
        "bio_signals": 0,
        "star_type": "G"
    }
    assert predict_exobiology_candidates(body_zero) == []

    # 2. Mapped body with 0 signals
    body_mapped_zero = {
        "landable": True,
        "planet_class": "High metal content world",
        "atmosphere": "Carbon dioxide",
        "surface_temperature": 230.0,
        "surface_gravity_g": 0.25,
        "surface_pressure": 0.035 * 101325,
        "is_mapped_by_user": 1,
        "bio_signals": 0,
        "star_type": "G"
    }
    assert predict_exobiology_candidates(body_mapped_zero) == []


def test_dss_confirmed_genus_elimination():
    """Verify that when DSS confirmed genuses are present, candidates of unconfirmed genuses are eliminated."""
    body = {
        "landable": True,
        "planet_class": "High metal content world",
        "atmosphere": "Carbon dioxide",
        "surface_temperature": 230.0,
        "surface_gravity_g": 0.25,
        "surface_pressure": 0.035 * 101325,
        "bio_signals": 2,
        "star_type": "G",
        "confirmed_genuses": ["Stratum", "Bacterium"]
    }
    candidates = predict_exobiology_candidates(body)
    assert len(candidates) > 0
    candidate_genera = {c["genus"] for c in candidates}
    
    # All candidates must belong to the confirmed genuses
    assert candidate_genera.issubset({"Stratum", "Bacterium"})
    assert "Cactoida" not in candidate_genera
    assert "Aleoida" not in candidate_genera
    assert "Tubus" not in candidate_genera


def test_single_species_per_genus_enforced():
    """Verify that at most 1 species per distinct genus is allocated across definite signals."""
    body = {
        "landable": True,
        "planet_class": "High metal content world",
        "atmosphere": "Carbon dioxide",
        "surface_temperature": 230.0,
        "surface_gravity_g": 0.25,
        "surface_pressure": 0.035 * 101325,
        "bio_signals": 3,
        "star_type": "G"
    }
    candidates = predict_exobiology_candidates(body)
    definite_candidates = [c for c in candidates if c["confidence"] == "definite"]
    
    # Definite candidates must have distinct genera
    genera_list = [c["genus"] for c in definite_candidates]
    assert len(genera_list) == len(set(genera_list)), "Each signal slot must correspond to a distinct genus"


def test_low_pressure_atmosphere_under_100_pa():
    """Verify that low surface pressures (< 100 Pa) are correctly parsed as atmospheres and not treated as > 10 atm."""
    # 82.44 Pa (approx 0.000813 atm)
    body_low_p = {"surface_pressure": 82.445755}
    p_atm = get_pressure_atm(body_low_p)
    assert pytest.approx(p_atm, 0.0001) == (82.445755 / 101325.0)
    assert p_atm < 0.01

    # 13.65 Pa (approx 0.000134 atm)
    body_ultra_low = {"SurfacePressure": 13.658933}
    p_atm2 = get_pressure_atm(body_ultra_low)
    assert pytest.approx(p_atm2, 0.00001) == (13.658933 / 101325.0)
    assert p_atm2 < 0.001


def test_atmosphere_rich_vs_plain_isolation():
    """Verify that -rich atmospheres and plain atmospheres do not falsely cross-match."""
    # Plain carbon dioxide atmosphere must not match rich-only rule
    assert match_atmosphere(["carbon dioxide"], "thin carbon dioxide atmosphere") is True
    assert match_atmosphere(["carbon dioxide-rich"], "thin carbon dioxide atmosphere") is False

    # Carbon dioxide-rich atmosphere must not match plain-only rule
    assert match_atmosphere(["carbon dioxide-rich"], "thin carbon dioxide-rich atmosphere") is True
    assert match_atmosphere(["carbon dioxide-rich"], "thin carbon dioxide rich atmosphere") is True
    assert match_atmosphere(["carbon dioxide"], "thin carbon dioxide-rich atmosphere") is False


def test_parent_star_resolution_for_planets():
    """Verify that planets with star_type: None properly resolve parent star spectral class."""
    body_planet = {
        "landable": True,
        "planet_class": "Rocky body",
        "atmosphere": "Neon",
        "surface_temperature": 75.0,
        "surface_gravity_g": 0.15,
        "surface_pressure": 0.02 * 101325,
        "bio_signals": 1,
        "star_type": None,
        "parent_star_type": "M"  # M star is not allowed for Electricae
    }
    cand_m = predict_exobiology_candidates(body_planet)
    assert not any("Electricae" in c["species"] for c in cand_m)

    # When parent_star_type is A-type, Electricae is allowed
    body_planet["parent_star_type"] = "A"
    cand_a = predict_exobiology_candidates(body_planet)
    assert any("Electricae" in c["species"] for c in cand_a)


def test_saa_signals_found_zero_bio_clears_predictions(tmp_path):
    """Verify that when DSS scan (SAASignalsFound) finds 0 biological signals, predictions are strictly wiped to []."""
    import json
    import sqlite3
    from app.db.database import init_db
    from app.parser.journal_parser import JournalParser

    db_path = str(tmp_path / "test_zero_bio.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    parser = JournalParser(conn)

    sys_addr = 555555555
    body_id = 2

    # Step 1: FSS Scan of planet with CO2 atmosphere (unmapped, signals unknown yet)
    scan_event = {
        "timestamp": "2026-09-10T12:00:00Z",
        "event": "Scan",
        "ScanType": "Detailed",
        "StarSystem": "Bio Test System",
        "SystemAddress": sys_addr,
        "BodyName": "Bio Test System 2",
        "BodyID": body_id,
        "DistanceFromArrivalLS": 450.0,
        "PlanetClass": "High metal content body",
        "Atmosphere": "thin carbon dioxide atmosphere",
        "AtmosphereType": "CarbonDioxide",
        "SurfaceTemperature": 240.0,
        "SurfaceGravity": 2.5, # ~0.25 G
        "SurfacePressure": 3500.0, # ~0.034 atm
        "Landable": True
    }
    parser.process_journal_line(json.dumps(scan_event))
    parser.flush_dirty_systems()

    # Step 2: SAASignalsFound arrives with ONLY geological signals (0 biological signals)
    saa_event = {
        "timestamp": "2026-09-10T12:05:00Z",
        "event": "SAASignalsFound",
        "SystemAddress": sys_addr,
        "BodyName": "Bio Test System 2",
        "BodyID": body_id,
        "Signals": [
            {"Type": "$SAA_SignalType_Geological;", "Count": 4}
        ]
    }
    parser.process_journal_line(json.dumps(saa_event))
    parser.flush_dirty_systems()

    # Verify that in database, exobiology_predictions is strictly empty '[]'
    c = conn.cursor()
    c.execute("SELECT bio_signals, geo_signals, is_mapped_by_user, exobiology_predictions FROM bodies WHERE system_address = ? AND body_id = ?", (sys_addr, body_id))
    row = c.fetchone()
    assert row["bio_signals"] == 0
    assert row["geo_signals"] == 4
    assert row["is_mapped_by_user"] == 1
    assert row["exobiology_predictions"] == "[]"
    conn.close()

