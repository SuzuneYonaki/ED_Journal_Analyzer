from app.parser.exobiology import predict_exobiology_candidates, get_species_value, EXOBIOLOGY_SPECIES_CONDITIONS

def test_exobiology_prediction():
    # Candidate on High Metal Content with CO2 atmosphere
    body = {
        "landable": True,
        "planet_class": "High metal content world",
        "atmosphere": "Carbon dioxide",
        "surface_temperature": 250.0,
        "surface_gravity_g": 0.35,
        "surface_pressure": 0.04 * 101325,
        "bio_signals": 2,
        "star_type": "F"
    }
    candidates = predict_exobiology_candidates(body)
    assert len(candidates) > 0
    names = [c["species"] for c in candidates]
    assert any("Stratum" in n for n in names)
    # Stratum Tectonicas has 19M base value
    tectonicas = next((c for c in candidates if "Tectonicas" in c["species"]), None)
    if tectonicas:
        assert tectonicas["base_value"] == 19010800
        assert tectonicas["first_discovery_value"] == 19010800 * 5
        # Variant color for F star is Emerald
        assert tectonicas["variant_color"] == "Emerald"
        assert "Emerald" in tectonicas["species_variant"]


def test_radicoida_unicus_exists_only_in_hip_87621():
    """Radicoida Unicus is unique to HIP 87621; it must not be predicted on look-alike bodies elsewhere."""
    body = {
        "landable": True,
        "planet_class": "High metal content body",
        "atmosphere": "Hot thin carbon dioxide",
        "surface_temperature": 520.0,
        "surface_gravity_g": 0.20,
        "surface_pressure": 0.025 * 101325,
        "volcanism": "Minor Silicate Vapour Geysers",
        "star_type": "M",
        "bio_signals": 1,
        "star_system": "Somewhere Else",
    }
    assert "Radicoida Unicus" not in [c["species"] for c in predict_exobiology_candidates(body)]

    candidates = predict_exobiology_candidates({**body, "star_system": "HIP 87621"})
    radicoida = next((c for c in candidates if c["species"] == "Radicoida Unicus"), None)
    assert radicoida is not None
    assert radicoida["base_value"] == 119037


def test_get_species_value():
    val = get_species_value("Stratum Tectonicas")
    assert val["base_value"] == 19010800
    assert val["first_discovery_value"] == 19010800 * 5
    assert val["colony_distance_m"] == 500

    # Genus fallback
    val_genus = get_species_value("Cactoida UnknownSpecies", "Cactoida")
    assert val_genus["base_value"] == 3667600
    assert val_genus["first_discovery_value"] == 3667600 * 5
    assert val_genus["colony_distance_m"] == 300

def test_scan_organic_stages():
    import json
    from app.server.api import init_db, get_db_connection
    from app.parser.journal_parser import JournalParser
    
    conn = get_db_connection()
    init_db()
    parser = JournalParser(conn)
    
    # 1. Log stage
    event_log = {
        "event": "ScanOrganic",
        "timestamp": "2026-08-28T00:00:00Z",
        "SystemAddress": 999999999,
        "Body": 1,
        "BodyID": 1,
        "ScanType": "Log",
        "Genus": "$Codex_Ent_Stratum_Genus_Name;",
        "Genus_Localised": "Stratum",
        "Species": "$Codex_Ent_Stratum_01_Name;",
        "Species_Localised": "Stratum Tectonicas"
    }
    parser.process_journal_line(json.dumps(event_log))
    parser.flush_dirty_systems()
    
    c = conn.cursor()
    c.execute("SELECT * FROM scanned_organics WHERE system_address = 999999999")
    row = c.fetchone()
    assert row is not None
    assert row["scan_type"] == "Log"
    assert row["species_localised"] == "Stratum Tectonicas"
    assert row["base_value"] == 19010800
    
    conn.close()
