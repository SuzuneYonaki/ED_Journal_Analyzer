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



def test_stratum_on_high_metal_content_body_is_tectonicas():
    """Only Stratum Tectonicas grows on high metal content bodies, so it is the one species left in the genus."""
    body = {
        "landable": True,
        "planet_class": "High metal content world",  # EDSM spelling is accepted
        "atmosphere": "Carbon dioxide",
        "surface_temperature": 230.0,
        "surface_gravity_g": 0.25,
        "surface_pressure": 0.035 * 101325,  # in Pascals
        "bio_signals": 4,
        "star_type": "F"
    }
    candidates = predict_exobiology_candidates(body)
    stratum = next((c for c in candidates if c["genus"] == "Stratum"), None)
    assert stratum is not None
    assert stratum["species"] == "Stratum Tectonicas"
    assert stratum["species_in_genus"] == 1
    assert stratum["base_value"] == 19010800
    assert stratum["first_discovery_value"] == 19010800 * 5
    assert stratum["variant_color"] in stratum["species_variant"]


def test_conservative_species_prediction_within_threshold():
    """
    Verify that when candidate species within the same genus have fit score differences < 10%,
    the lower base value candidate is prioritized, but when difference is >= 10%, the higher fit score wins.
    """
    from app.parser.exobiology import rank_candidates_conservatively

    # Within 10% threshold: 0.95 vs 0.90 -> choose lower base_value (1.5M over 19M)
    cands_close = [
        {"species": "Stratum Tectonicas", "genus": "Stratum", "fit_score": 0.95, "base_value": 19010800},
        {"species": "Stratum Cucumisis", "genus": "Stratum", "fit_score": 0.90, "base_value": 1500000},
    ]
    ranked = rank_candidates_conservatively(cands_close, diff_threshold=0.10)
    assert ranked[0]["species"] == "Stratum Cucumisis"

    # Beyond 10% threshold: 0.95 vs 0.80 -> higher fit score wins regardless of base_value
    cands_distinct = [
        {"species": "Stratum Tectonicas", "genus": "Stratum", "fit_score": 0.95, "base_value": 19010800},
        {"species": "Stratum Cucumisis", "genus": "Stratum", "fit_score": 0.80, "base_value": 1500000},
    ]
    ranked_dist = rank_candidates_conservatively(cands_distinct, diff_threshold=0.10)
    assert ranked_dist[0]["species"] == "Stratum Tectonicas"



def test_genera_are_definite_only_when_the_signals_require_them():
    """With 2 signals and exactly 2 possible genera both must be present; with 1 signal neither is certain."""
    body = {
        "landable": True,
        "planet_class": "High metal content body",
        "atmosphere": "Carbon dioxide",
        "surface_temperature": 240.0,
        "surface_gravity_g": 0.30,
        "surface_pressure": 0.035 * 101325,
        "bio_signals": 2,
        "star_type": "F"
    }
    two_signals = predict_exobiology_candidates(body)
    assert {c["genus"] for c in two_signals} == {"Bacterium", "Stratum"}
    assert all(c["confidence"] == "definite" for c in two_signals)

    one_signal = predict_exobiology_candidates({**body, "bio_signals": 1})
    assert {c["genus"] for c in one_signal} == {"Bacterium", "Stratum"}
    assert all(c["confidence"] == "possible" for c in one_signal)


def test_dss_confirmed_genus_narrows_the_candidates():
    body = {
        "landable": True,
        "planet_class": "High metal content body",
        "atmosphere": "Carbon dioxide",
        "surface_temperature": 240.0,
        "surface_gravity_g": 0.30,
        "surface_pressure": 0.035 * 101325,
        "bio_signals": 2,
        "star_type": "F",
        "confirmed_genuses": ["Stratum"],
    }
    candidates = predict_exobiology_candidates(body)
    assert [c["genus"] for c in candidates] == ["Stratum"]
    assert candidates[0]["confidence"] == "definite" and candidates[0]["genus_confirmed"] is True



def test_volcanism_rule_semantics():
    """The rule data distinguishes "Any", "None", substring lists and "!" exclusions of volcanism."""
    from app.parser.bioscan.matcher import BodyContext, SystemContext, ruleset_passes

    system = SystemContext(name="S")

    def passes(rule, volcanism):
        return ruleset_passes({"volcanism": rule}, BodyContext(name="b", body_type="Rocky body", volcanism=volcanism), system)

    assert passes("Any", "minor water geysers volcanism") and not passes("Any", "")
    assert passes("None", "") and not passes("None", "minor water geysers volcanism")
    assert passes(["water"], "major water geysers volcanism") and not passes(["water"], "minor metallic magma volcanism")
    assert passes(["silicate", "metallic", "rocky"], "minor metallic magma volcanism")
    assert not passes(["major silicate vapour"], "minor silicate vapour geysers volcanism")
    assert passes(["major silicate vapour"], "major silicate vapour geysers volcanism")
    # "No volcanism" from EDSM is treated as none
    from app.parser.bioscan.adapters import normalize_volcanism
    assert normalize_volcanism("No volcanism") == "" and normalize_volcanism(None) == ""


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



def test_candidates_are_not_padded_to_the_signal_count():
    """A body with more signals than possible genera lists only the genera that can exist."""
    body = {
        "landable": True,
        "planet_class": "High metal content body",
        "atmosphere": "Carbon dioxide",
        "surface_temperature": 220.0,
        "surface_gravity_g": 0.20,
        "surface_pressure": 0.030 * 101325,
        "bio_signals": 9,
        "star_type": "G"
    }
    candidates = predict_exobiology_candidates(body)
    assert 0 < len(candidates) < 9
    assert len({c["genus"] for c in candidates}) == len(candidates), "one entry per genus"
    assert all(c["genus_confirmed"] for c in candidates), "9 signals need every possible genus"
    assert all(c["confidence"] == "definite" for c in candidates if c["species_in_genus"] == 1)



ELECTRICAE_BODY = {
    "landable": True,
    "planet_class": "Icy body",
    "atmosphere_type": "Argon",
    "surface_temperature": 100.0,
    "surface_gravity_g": 0.15,
    "surface_pressure": 0.02 * 101325,
    "bio_signals": 1,
    "star_type": "A",
    "luminosity": "V",
}


def _names(cands):
    return {c["species"] for c in cands} | {a for c in cands for a in c.get("alternate_species", [])}


def test_electricae_pluma_needs_icy_body_low_gravity_and_a_suitable_parent_star():
    """Electricae Pluma: icy body, <= 0.276 G, parent star A/N/D/H/AeBe."""
    assert "Electricae Pluma" in _names(predict_exobiology_candidates(ELECTRICAE_BODY))
    assert "Electricae Pluma" not in _names(predict_exobiology_candidates({**ELECTRICAE_BODY, "star_type": "M"}))
    assert "Electricae Pluma" not in _names(predict_exobiology_candidates({**ELECTRICAE_BODY, "surface_gravity_g": 0.45}))
    assert "Electricae Pluma" not in _names(predict_exobiology_candidates({**ELECTRICAE_BODY, "planet_class": "Rocky body"}))



def test_system_prediction_uses_the_parent_star_of_each_body():
    """predict_system_exobiology_candidates shares one system context: each body is judged by its own parent star."""
    from app.parser.exobiology import predict_system_exobiology_candidates

    def icy(name, parent_id):
        return {
            "body_name": name, "body_id": 10 + parent_id, "landable": True, "planet_class": "Icy body",
            "atmosphere_type": "Argon", "surface_temperature": 100.0, "surface_gravity_g": 0.15,
            "surface_pressure": 0.02 * 101325, "bio_signals": 1, "parents": [{"Star": parent_id}],
        }

    star_m = {"body_name": "Test A", "body_id": 1, "star_type": "M", "luminosity": "Va", "distance_from_arrival_ls": 0.0}
    star_a = {"body_name": "Test B", "body_id": 2, "star_type": "A", "luminosity": "V", "distance_from_arrival_ls": 500.0}
    around_m, around_a = icy("Test A 1", 1), icy("Test B 1", 2)
    predict_system_exobiology_candidates([star_m, star_a, around_m, around_a], {"star_system": "Test"})

    assert "Electricae Pluma" not in _names(around_m["exobiology"])
    assert "Electricae Pluma" in _names(around_a["exobiology"])
