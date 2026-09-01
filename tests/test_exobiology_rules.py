"""
Unit tests for the Exobiology candidate prediction engine and rules dataset.
Verifies multi-parameter physical matrix filtering, signal budget allocation,
confidence scoring, and species value lookups.

All code, docstrings, and comments are strictly English ASCII.
"""

import pytest
from app.parser.exobiology import (
    predict_exobiology_candidates,
    get_species_value,
    get_pressure_atm,
    get_temperature_k,
    get_gravity_g,
    determine_variant_info,
    calculate_environment_fit_score
)
from app.parser.exobiology_rules import EXOBIOLOGY_RULES


def test_pressure_conversion():
    """Verify pressure is converted correctly from Pascals or raw atmospheres."""
    body_pascal = {"surface_pressure": 101325.0} # 1 atm in Pa
    assert pytest.approx(get_pressure_atm(body_pascal), 0.001) == 1.0

    body_atm = {"surface_pressure": 0.045}
    assert pytest.approx(get_pressure_atm(body_atm), 0.001) == 0.045

    body_zero = {"surface_pressure": 0.0}
    assert get_pressure_atm(body_zero) == 0.0


def test_temperature_and_gravity():
    """Verify temperature and gravity extraction."""
    body = {
        "surface_temperature": 250.5,
        "surface_gravity_g": 0.35
    }
    assert get_temperature_k(body) == 250.5
    assert get_gravity_g(body) == 0.35


def test_stratum_tectonicas_prediction():
    """Verify Stratum genus is accurately predicted on standard HMC bodies."""
    body = {
        "landable": True,
        "planet_class": "High metal content world",
        "atmosphere": "Carbon dioxide",
        "surface_temperature": 230.0,
        "surface_gravity_g": 0.25,
        "surface_pressure": 0.035 * 101325, # in Pascals
        "bio_signals": 4,
        "star_type": "F"
    }
    candidates = predict_exobiology_candidates(body)
    assert len(candidates) > 0
    
    # Check that Stratum is present
    stratum_match = next((c for c in candidates if c["genus"] == "Stratum"), None)
    assert stratum_match is not None
    assert stratum_match["base_value"] == 19010800
    assert stratum_match["first_discovery_value"] == 19010800 * 5
    assert stratum_match["variant_color"] in ["Emerald", "Teal"]
    assert stratum_match["variant_color"] in stratum_match["species_variant"]


def test_signal_budget_and_confidence_ranking():
    """Verify that signal budget produces Top X definite candidates plus qualifying runner-up."""
    body = {
        "landable": True,
        "planet_class": "High metal content body",
        "atmosphere": "Carbon dioxide",
        "surface_temperature": 220.0,
        "surface_gravity_g": 0.25,
        "surface_pressure": 0.030 * 101325,
        "bio_signals": 2, # Budget of 2 -> 2 definite matches
        "star_type": "G"
    }
    candidates = predict_exobiology_candidates(body)
    assert len(candidates) in [2, 3], "Should return top X definite candidates and at most 1 runner-up"
    
    definite_matches = [c for c in candidates if c["confidence"] == "definite"]
    assert len(definite_matches) == 2, "Top 2 matches must be marked definite"

    possible_matches = [c for c in candidates if c["confidence"] == "possible"]
    assert len(possible_matches) <= 1, "At most 1 runner-up can be marked possible"


def test_volcanism_requirement():
    """Verify that Fumerola species require volcanic activity."""
    body_no_volc = {
        "landable": True,
        "planet_class": "High metal content body",
        "atmosphere": "Water",
        "surface_temperature": 200.0,
        "surface_gravity_g": 0.20,
        "surface_pressure": 0.02 * 101325,
        "volcanism": "None",
        "bio_signals": 5,
        "star_type": "K"
    }
    candidates_no_volc = predict_exobiology_candidates(body_no_volc)
    fumerola_names_no_volc = [c["species"] for c in candidates_no_volc if "Fumerola" in c["species"]]
    assert len(fumerola_names_no_volc) == 0

    body_with_volc = {
        "landable": True,
        "planet_class": "High metal content body",
        "atmosphere": "Water",
        "surface_temperature": 200.0,
        "surface_gravity_g": 0.20,
        "surface_pressure": 0.02 * 101325,
        "volcanism": "Water Geysers",
        "bio_signals": 5,
        "star_type": "K"
    }
    candidates_volc = predict_exobiology_candidates(body_with_volc)
    fumerola_names_volc = [c["species"] for c in candidates_volc if "Fumerola" in c["species"]]
    assert len(fumerola_names_volc) > 0


def test_get_species_value_lookups():
    """Verify value lookups for specific species and generic genera."""
    val_tectonicas = get_species_value("Stratum Tectonicas")
    assert val_tectonicas["base_value"] == 19010800
    assert val_tectonicas["first_discovery_value"] == 19010800 * 5
    assert val_tectonicas["colony_distance_m"] == 500

    val_codex = get_species_value("$Codex_Ent_Aleoida_01_Name;")
    assert val_codex["base_value"] > 0
    assert val_codex["first_discovery_value"] == val_codex["base_value"] * 5

    val_genus = get_species_value("UnknownFlora", genus_name="Cactoida")
    assert val_genus["base_value"] == 3667600
    assert val_genus["colony_distance_m"] == 300


def test_nine_bio_signals_filling():
    """Verify that a body with 9 biological signals fills species candidates up to the budget."""
    body = {
        "landable": True,
        "planet_class": "High metal content body",
        "atmosphere": "Carbon dioxide",
        "surface_temperature": 220.0,
        "surface_gravity_g": 0.20,
        "surface_pressure": 0.030 * 101325,
        "bio_signals": 9, # Budget of 9
        "star_type": "G"
    }
    candidates = predict_exobiology_candidates(body)
    assert len(candidates) >= 9, "Should fill species candidates up to 9 or X+1"
    definite_matches = [c for c in candidates if c["confidence"] == "definite"]
    assert len(definite_matches) == 9, "All 9 signal slots should have definite candidate matches"


def test_electricae_parent_star_and_gravity_rules():
    """Verify Electricae parent star (A/B/O/N/H/D) and low gravity (<0.27G) requirements."""
    # Matched body under A-type star with V luminosity class and low gravity
    body_matched = {
        "landable": True,
        "planet_class": "Rocky body",
        "atmosphere": "Neon",
        "surface_temperature": 75.0,
        "surface_gravity_g": 0.15, # < 0.27 G
        "surface_pressure": 0.02 * 101325,
        "bio_signals": 1,
        "star_type": "A",
        "luminosity": "V"
    }
    cand_matched = predict_exobiology_candidates(body_matched)
    electricae_names = [c["species"] for c in cand_matched if "Electricae" in c["species"]]
    assert len(electricae_names) > 0, "Electricae should be predicted on valid parent star and low gravity"

    # Mismatched parent star (M-type star is not allowed for Electricae)
    body_m_star = {
        "landable": True,
        "planet_class": "Rocky body",
        "atmosphere": "Neon",
        "surface_temperature": 75.0,
        "surface_gravity_g": 0.15,
        "surface_pressure": 0.02 * 101325,
        "bio_signals": 1,
        "star_type": "M",
        "luminosity": "V"
    }
    cand_m_star = predict_exobiology_candidates(body_m_star)
    m_star_electricae = [c["species"] for c in cand_m_star if "Electricae" in c["species"]]
    assert len(m_star_electricae) == 0, "Electricae should not spawn on M-type parent star"

    # High gravity body (> 0.27 G)
    body_high_g = {
        "landable": True,
        "planet_class": "Rocky body",
        "atmosphere": "Neon",
        "surface_temperature": 75.0,
        "surface_gravity_g": 0.45, # > 0.27 G
        "surface_pressure": 0.02 * 101325,
        "bio_signals": 1,
        "star_type": "A",
        "luminosity": "V"
    }
    cand_high_g = predict_exobiology_candidates(body_high_g)
    high_g_electricae = [c["species"] for c in cand_high_g if "Electricae" in c["species"]]
    assert len(high_g_electricae) == 0, "Electricae should not spawn on high gravity (> 0.27 G)"
