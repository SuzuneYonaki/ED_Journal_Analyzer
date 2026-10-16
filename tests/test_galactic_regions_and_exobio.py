"""
Unit tests for the Galactic Regions resolver (klightspeed region map) and the
Exobiology regional-constraint mechanism.
"""

import pytest

import app.parser.exobiology as exobiology
from app.utils.galactic_regions import (
    DEFAULT_FALLBACK_REGION,
    GALACTIC_REGIONS,
    find_region_id,
    get_region_from_coords,
    get_region_info,
)
from app.parser.exobiology import (
    DEFAULT_REGION_CONSTRAINTS,
    get_effective_exobiology_rules,
    predict_exobiology_candidates,
)

# (label, x, y, z, official region id, English name)
LANDMARKS = [
    ("Sol", 0.0, 0.0, 0.0, 18, "Inner Orion Spur"),
    ("Sagittarius A*", 25.2, -20.9, 25899.9, 1, "Galactic Centre"),
    ("Colonia", -9530.5, -910.3, 19808.1, 9, "Inner Scutum-Centaurus Arm"),
    ("Beagle Point", -1111.6, -134.2, 65269.8, 40, "The Abyss"),
    ("Odin's Hold area", -8000.0, 0.0, 25000.0, 4, "Odin's Hold"),
]


@pytest.mark.parametrize("label,x,y,z,region_id,name_en", LANDMARKS)
def test_landmark_coordinates_resolve_to_official_regions(label, x, y, z, region_id, name_en):
    assert get_region_from_coords(x, y, z)[:2] == (region_id, name_en), label


def test_region_id_table_matches_official_numbering():
    assert len(GALACTIC_REGIONS) == 42
    # The IDs the guessed table used to get wrong (it was shifted from 17 onwards)
    assert GALACTIC_REGIONS[17][0] == "Temple"
    assert GALACTIC_REGIONS[18][0] == "Inner Orion Spur"
    assert GALACTIC_REGIONS[19][0] == "Hawking's Gap"
    assert GALACTIC_REGIONS[31][0] == "Formidine Rift"
    assert GALACTIC_REGIONS[42][0] == "The Void"
    assert get_region_info(1) == (1, "Galactic Centre", "銀河中心核")
    assert get_region_info(18) == (18, "Inner Orion Spur", "インナー・オリオン・スパー")


def test_region_lookup_depends_on_x_and_z_only():
    assert find_region_id(0.0, 0.0) == find_region_id(0.0, 0.0)
    assert get_region_from_coords(0.0, 500.0, 0.0) == get_region_from_coords(0.0, -500.0, 0.0)


def test_fallback_when_coordinates_missing_invalid_or_outside_the_map():
    assert DEFAULT_FALLBACK_REGION == (18, "Inner Orion Spur", "インナー・オリオン・スパー")
    assert get_region_from_coords(None, None, None) == DEFAULT_FALLBACK_REGION
    assert get_region_from_coords(0.0, None, 100.0) == DEFAULT_FALLBACK_REGION
    assert get_region_from_coords("invalid", 0.0, 0.0) == DEFAULT_FALLBACK_REGION
    assert get_region_from_coords(150000.0, 50000.0, -200000.0) == DEFAULT_FALLBACK_REGION
    assert find_region_id(150000.0, -200000.0) is None
    assert get_region_info(999) == DEFAULT_FALLBACK_REGION
    assert get_region_info(None) == DEFAULT_FALLBACK_REGION


def test_default_region_constraints_use_official_ids_and_are_sourced():
    # Brain Tree: BioScan region group 'brain-tree'
    assert DEFAULT_REGION_CONSTRAINTS == {"Brain Tree": [2, 9, 10, 17, 18, 35]}
    assert all(rid in GALACTIC_REGIONS for ids in DEFAULT_REGION_CONSTRAINTS.values() for rid in ids)


STRATUM_BODY = {
    "landable": True,
    "planet_class": "High metal content body",
    "atmosphere": "Carbon dioxide",
    "surface_temperature": 180.0,
    "surface_gravity_g": 0.4,
    "surface_pressure": 0.05 * 101325,
    "bio_signals": 1,
    "star_type": "G",
}


def _has_stratum(cands):
    return any("Stratum" in c.get("species", "") for c in cands)


def test_unconstrained_species_appear_in_any_region():
    for pos in [(0.0, 0.0, 0.0), (-9530.5, -910.3, 19808.1), (25.0, -21.0, 25900.0)]:
        assert _has_stratum(predict_exobiology_candidates(STRATUM_BODY, star_pos=pos))


def test_region_constraint_excludes_outside_and_keeps_inside(monkeypatch):
    # Mechanism test with a synthetic constraint: Stratum only in the Galactic Centre (1)
    monkeypatch.setattr(exobiology, "DEFAULT_REGION_CONSTRAINTS", {"Stratum": [1]})
    assert get_effective_exobiology_rules()["Stratum Tectonicas"]["allowed_regions"] == [1]

    # Sol (region 18): excluded; Sagittarius A* (region 1): kept
    assert not _has_stratum(predict_exobiology_candidates(STRATUM_BODY, star_pos=(0.0, 0.0, 0.0)))
    assert _has_stratum(predict_exobiology_candidates(STRATUM_BODY, star_pos=(25.2, -20.9, 25899.9)))
    # Explicit region ids win over coordinates
    assert not _has_stratum(predict_exobiology_candidates(STRATUM_BODY, region_id=18))
    assert _has_stratum(predict_exobiology_candidates(STRATUM_BODY, region_id=1))


def test_unknown_region_never_excludes(monkeypatch):
    monkeypatch.setattr(exobiology, "DEFAULT_REGION_CONSTRAINTS", {"Stratum": [1]})
    assert _has_stratum(predict_exobiology_candidates(STRATUM_BODY))


def test_predict_exobiology_discrete_parameter_call():
    cands = predict_exobiology_candidates(
        planet_class="High metal content body",
        atmosphere_type="Carbon dioxide",
        surface_temp=180.0,
        gravity=0.4,
        star_type="G",
        star_pos=(0.0, 0.0, 0.0),
    )
    assert _has_stratum(cands)
