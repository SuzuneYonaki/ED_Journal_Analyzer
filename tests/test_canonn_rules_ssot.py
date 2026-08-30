"""
Automated Consistency Verification test for SSOT (Single Source of Truth) ruleset.
Asserts that canonn_rules.json is correctly structured, dynamically loaded,
and parsed at runtime without attribute corruption or data dropping.

All code, docstrings, and comments are strictly English ASCII.
"""

import json
from pathlib import Path
from app.parser.exobiology import (
    get_effective_exobiology_rules,
    get_species_value,
    predict_exobiology_candidates,
    get_pressure_atm,
    get_temperature_k,
    get_gravity_g,
    CANONN_RULES_FILE
)


def test_canonn_rules_json_ssot_integrity():
    """Verify that external canonn_rules.json conforms to expected schema."""
    assert CANONN_RULES_FILE.is_file(), "canonn_rules.json must exist in app/data/"

    with CANONN_RULES_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, dict), "canonn_rules.json must be a top-level dictionary"
    assert len(data) > 0, "canonn_rules.json should not be empty"

    # Schema validation for each species entry
    for name, rule in data.items():
        assert isinstance(name, str) and len(name) > 0, f"Invalid species key: {name}"
        assert isinstance(rule, dict), f"Rule for {name} must be a dict"
        assert "genus" in rule, f"Rule for {name} missing 'genus'"
        assert "base_value" in rule and isinstance(rule["base_value"], (int, float)), f"Rule for {name} invalid 'base_value'"
        assert "body_types" in rule and isinstance(rule["body_types"], list), f"Rule for {name} invalid 'body_types'"
        assert "atmosphere_types" in rule and isinstance(rule["atmosphere_types"], list), f"Rule for {name} invalid 'atmosphere_types'"


def test_runtime_ssot_rule_merging():
    """Verify that get_effective_exobiology_rules dynamically incorporates external rules."""
    effective_rules = get_effective_exobiology_rules()
    assert isinstance(effective_rules, dict)
    assert len(effective_rules) >= 90, "Should have full matrix of biological species"

    # Verify Stratum Tectonicas values from SSOT
    stratum_rule = effective_rules.get("Stratum Tectonicas")
    assert stratum_rule is not None
    assert stratum_rule["genus"] == "Stratum"
    assert stratum_rule["base_value"] == 19010800
    assert stratum_rule["colony_distance_m"] == 500


def test_zero_speculation_and_strict_attribute_handling():
    """Verify that missing parameters return safe explicit values without hallucination."""
    empty_body = {}
    assert get_pressure_atm(empty_body) == 0.0
    assert get_temperature_k(empty_body) == 0.0
    assert get_gravity_g(empty_body) == 0.0

    # Non-landable bodies should immediately yield zero candidates
    non_landable_body = {"landable": False, "planet_class": "High metal content body"}
    assert predict_exobiology_candidates(non_landable_body) == []

    # Unknown species should return standard safe genus fallback without errors
    val = get_species_value("Unknown NonExistent Organism", "Bacterium")
    assert val["genus"] == "Bacterium"
    assert val["base_value"] > 0
    assert val["first_discovery_value"] == val["base_value"] * 5
