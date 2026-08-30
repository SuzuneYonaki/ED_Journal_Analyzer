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

def test_radicoida_unica_prediction():
    # Test body matching Radicoida Unica Canonn conditions:
    # Body Type: High Metal Content / Rocky
    # Atmosphere: Thin / Hot Thin Carbon Dioxide
    # Gravity: 0.05 – 0.38 G
    # Temperature: 467 – 699 K
    # Pressure: 0.007 – 0.060 atm
    body_radicoida = {
        "landable": True,
        "planet_class": "High metal content body",
        "atmosphere": "Hot thin carbon dioxide",
        "surface_temperature": 520.0,
        "surface_gravity_g": 0.20,
        "surface_pressure": 0.025 * 101325, # 0.025 atm in Pa
        "volcanism": "Minor Silicate Vapour Geysers",
        "star_type": "M",
        "bio_signals": 1
    }
    candidates = predict_exobiology_candidates(body_radicoida)
    names = [c["species"] for c in candidates]
    assert "Radicoida Unica" in names
    
    radicoida = next(c for c in candidates if c["species"] == "Radicoida Unica")
    assert radicoida["base_value"] == 7200000
    assert radicoida["colony_distance_m"] == 1000
    assert radicoida["variant_color"] == "Red"  # M star -> Red

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
