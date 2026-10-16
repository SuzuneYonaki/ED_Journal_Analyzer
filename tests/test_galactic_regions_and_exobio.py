"""
Unit tests for the Galactic Regions resolver (klightspeed region map) and the
Exobiology regional-constraint mechanism.
"""

import pytest

from app.utils.galactic_regions import (
    DEFAULT_FALLBACK_REGION,
    GALACTIC_REGIONS,
    find_region_id,
    get_region_from_coords,
    get_region_info,
)
from app.parser.exobiology import predict_exobiology_candidates
from app.parser.bioscan.matcher import BodyContext, SystemContext, ruleset_passes
from app.parser.bioscan.regions import region_map

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


def test_region_groups_use_official_region_ids():
    assert all(rid in GALACTIC_REGIONS for ids in region_map.values() for rid in ids)


def _ctx(region_id):
    return SystemContext(name="Test", region_id=region_id)


def test_region_rule_includes_and_excludes_by_region_group():
    body = BodyContext(name="b", body_type="Rocky body")
    # Colonia (9) is in the Sagittarius-Carina group but not in Orion-Cygnus; Sol (18) is in both
    assert ruleset_passes({"regions": ["orion-cygnus"]}, body, _ctx(18))
    assert not ruleset_passes({"regions": ["orion-cygnus"]}, body, _ctx(9))
    assert ruleset_passes({"regions": ["sagittarius-carina"]}, body, _ctx(9))
    # "!" excludes a group
    assert not ruleset_passes({"regions": ["!orion-cygnus-core"]}, body, _ctx(18))
    assert ruleset_passes({"regions": ["!orion-cygnus-core"]}, body, _ctx(1))


def test_unknown_region_never_excludes():
    body = BodyContext(name="b", body_type="Rocky body")
    assert ruleset_passes({"regions": ["orion-cygnus"]}, body, _ctx(None))


# Tussock Pennata: Carbon dioxide, rocky, 0.04-0.09 G, 146-154 K, no volcanism, and only in the
# sagittarius-carina-core-9 / perseus-core / orion-cygnus-core regions.
TUSSOCK_BODY = {
    "landable": True,
    "planet_class": "Rocky body",
    "atmosphere_type": "CarbonDioxide",
    "surface_temperature": 150.0,
    "surface_gravity_g": 0.06,
    "surface_pressure": 0.004 * 101325,
    "volcanism": "",
    "bio_signals": 2,
    "star_type": "G",
}


def _species(cands):
    return {c["species"] for c in cands} | {a for c in cands for a in c.get("alternate_species", [])}


def test_end_to_end_region_decides_the_species():
    in_sol = predict_exobiology_candidates(TUSSOCK_BODY, star_pos=(0.0, 0.0, 0.0))  # Inner Orion Spur (18)
    in_core = predict_exobiology_candidates(TUSSOCK_BODY, star_pos=(25.2, -20.9, 25899.9))  # Galactic Centre (1)
    assert "Tussock Pennata" in _species(in_sol)
    assert "Tussock Pennata" not in _species(in_core)
    # An explicit region id wins over the coordinates
    assert "Tussock Pennata" in _species(predict_exobiology_candidates(TUSSOCK_BODY, region_id=18))
    assert "Tussock Pennata" not in _species(predict_exobiology_candidates(TUSSOCK_BODY, region_id=1))


def test_discrete_parameter_call():
    cands = predict_exobiology_candidates(
        planet_class="Rocky body",
        atmosphere_type="Carbon dioxide",
        surface_temp=150.0,
        gravity=0.06,
        star_type="G",
        star_pos=(0.0, 0.0, 0.0),
    )
    assert "Tussock Pennata" in _species(cands)
