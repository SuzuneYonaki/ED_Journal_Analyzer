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

def test_journal_parser_in_memory():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    # Run init
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS systems (
            system_address INTEGER PRIMARY KEY,
            star_system TEXT NOT NULL,
            star_pos_x REAL, star_pos_y REAL, star_pos_z REAL,
            system_allegiance TEXT, system_economy TEXT, system_government TEXT, system_security TEXT,
            population INTEGER, first_visited TEXT, last_visited TEXT, visit_count INTEGER DEFAULT 1,
            total_bodies INTEGER DEFAULT 0, scanned_bodies INTEGER DEFAULT 0, main_star_type TEXT,
            total_potential_value INTEGER DEFAULT 0, total_fss_value INTEGER DEFAULT 0, total_dss_value INTEGER DEFAULT 0, total_bio_value INTEGER DEFAULT 0, total_bio_signals INTEGER DEFAULT 0,
            has_elw INTEGER DEFAULT 0, has_water_world INTEGER DEFAULT 0, has_ammonia INTEGER DEFAULT 0, has_terraformable INTEGER DEFAULT 0,
            has_bio INTEGER DEFAULT 0, has_landable INTEGER DEFAULT 0, has_high_g INTEGER DEFAULT 0, has_anomalies INTEGER DEFAULT 0
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bodies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            system_address INTEGER NOT NULL,
            body_id INTEGER, body_name TEXT NOT NULL, star_system TEXT, distance_from_arrival_ls REAL,
            star_type TEXT, stellar_mass REAL, absolute_magnitude REAL, radius REAL, surface_temperature REAL,
            planet_class TEXT, atmosphere TEXT, atmosphere_type TEXT, atmosphere_composition TEXT,
            mass_em REAL, surface_gravity REAL, surface_gravity_g REAL, surface_pressure REAL,
            landable INTEGER DEFAULT 0, volcanism TEXT, terraforming_state TEXT, tidal_lock INTEGER DEFAULT 0,
            semi_major_axis REAL, eccentricity REAL, orbital_inclination REAL, periapsis REAL,
            orbital_period REAL, ascending_node REAL, mean_anomaly REAL, rotation_period REAL,
            axial_tilt REAL, rings TEXT, materials TEXT, parents TEXT, was_discovered INTEGER DEFAULT 0,
            was_mapped INTEGER DEFAULT 0, is_mapped_by_user INTEGER DEFAULT 0, is_first_discovered_by_user INTEGER DEFAULT 0,
            bio_signals INTEGER DEFAULT 0, geo_signals INTEGER DEFAULT 0, fss_value INTEGER DEFAULT 0,
            dss_value INTEGER DEFAULT 0, first_discovered_fss INTEGER DEFAULT 0, first_mapped_dss INTEGER DEFAULT 0,
            max_potential_value INTEGER DEFAULT 0, exobiology_predictions TEXT, anomalies_json TEXT,
            scan_timestamp TEXT, updated_timestamp TEXT,
            UNIQUE(system_address, body_id)
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT, system_address INTEGER NOT NULL, star_system TEXT NOT NULL,
            timestamp TEXT NOT NULL, jump_dist REAL, fuel_used REAL, ship TEXT, is_taxi INTEGER DEFAULT 0, is_carrier INTEGER DEFAULT 0
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scanned_organics (
            id INTEGER PRIMARY KEY AUTOINCREMENT, system_address INTEGER NOT NULL, body_id INTEGER,
            body_name TEXT, timestamp TEXT NOT NULL, scan_type TEXT, genus TEXT, genus_localised TEXT,
            species TEXT, species_localised TEXT, variant TEXT, variant_localised TEXT,
            base_value INTEGER DEFAULT 0, first_discovery_value INTEGER DEFAULT 0
        );
    """)
    conn.commit()

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

    cursor.execute("SELECT * FROM systems WHERE system_address = 99887766")
    sys_row = cursor.fetchone()
    assert sys_row is not None
    assert sys_row["star_system"] == "Test System Prime"
    assert sys_row["has_elw"] == 1
    assert sys_row["total_potential_value"] > 0
