from app.parser.exobiology import predict_exobiology_candidates, get_species_value, EXOBIOLOGY_SPECIES_DB

def test_exobiology_prediction():
    # Candidate on High Metal Content with CO2 atmosphere
    body = {
        "landable": True,
        "planet_class": "High metal content world",
        "atmosphere": "Carbon dioxide",
        "surface_temperature": 250.0,
        "surface_gravity_g": 0.8,
        "bio_signals": 2
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

def test_get_species_value():
    val = get_species_value("Stratum Tectonicas")
    assert val["base_value"] == 19010800
    assert val["first_discovery_value"] == 19010800 * 5
    assert val["colony_distance_m"] == 500

    # Genus fallback
    val_genus = get_species_value("Cactoida UnknownSpecies", "Cactoida")
    assert val_genus["base_value"] == 3600000
    assert val_genus["colony_distance_m"] == 300
    assert val_genus["first_discovery_value"] == 3600000 * 5

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


