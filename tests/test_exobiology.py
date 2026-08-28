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

