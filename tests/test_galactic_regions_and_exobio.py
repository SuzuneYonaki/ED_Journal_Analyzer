"""
Unit tests for Galactic Regions coordinate resolver and Exobiology regional constraints.
Validates:
1. Coordinate resolution across key galactic regions (Sol, Sag A*, Formidine Rift, etc.)
2. Safe fallback when coordinates are None or out-of-bounds
3. Exobiology prediction exclusion of Electricae in Inner Orion Spur (Bubble)
4. Exobiology prediction inclusion of Electricae in allowed outer regions (e.g. Formidine Rift)
5. Region-unconstrained species (e.g. Stratum) appearing anywhere in valid physical conditions
6. Discrete parameter calling syntax of predict_exobiology_candidates
"""

import pytest

from app.utils.galactic_regions import (
    get_region_from_coords,
    get_region_info,
    GALACTIC_REGIONS,
    DEFAULT_FALLBACK_REGION,
)
from app.parser.exobiology import (
    predict_exobiology_candidates,
    get_effective_exobiology_rules,
)


def test_galactic_regions_coordinate_resolution():
    """Validates that key landmark coordinates resolve to expected Galactic Regions."""
    # 1. Sol (0, 0, 0) -> Inner Orion Spur (ID 19)
    reg_id, name_en, name_ja = get_region_from_coords(0.0, 0.0, 0.0)
    assert reg_id == 19
    assert name_en == "Inner Orion Spur"
    assert name_ja == "インナー・オリオン・スパー"

    # Bubble proximity (Achenar / Colonia highway start)
    reg_id_bub, _, _ = get_region_from_coords(67.5, -119.5, 4.2)
    assert reg_id_bub == 19

    # 2. Sagittarius A* (~ 25.2, -20.9, 25899.9) -> Galactic Centre (ID 1)
    reg_id_core, name_en_core, name_ja_core = get_region_from_coords(25.2, -20.9, 25899.9)
    assert reg_id_core == 1
    assert name_en_core == "Galactic Centre"
    assert name_ja_core == "銀河中心核"

    # 3. Formidine Rift (-10000, 50, 10000) -> Formidine Rift (ID 17)
    reg_id_rif, name_en_rif, name_ja_rif = get_region_from_coords(-10000.0, 50.0, 10000.0)
    assert reg_id_rif == 17
    assert name_en_rif == "Formidine Rift"
    assert name_ja_rif == "フォーミディン・リフト"

    # 4. Elysian Shore (-15000, 0, -2000) -> Elysian Shore (ID 18)
    reg_id_ely, name_en_ely, _ = get_region_from_coords(-15000.0, 0.0, -2000.0)
    assert reg_id_ely == 18
    assert name_en_ely == "Elysian Shore"

    # 5. Hawking's Gap (10000, 0, 10000) -> Hawking's Gap (ID 20)
    reg_id_hwk, name_en_hwk, _ = get_region_from_coords(10000.0, 0.0, 10000.0)
    assert reg_id_hwk == 20
    assert name_en_hwk == "Hawking's Gap"

    # 6. Dryman's Point (15000, 0, 22000) -> Dryman's Point (ID 22)
    reg_id_dry, name_en_dry, _ = get_region_from_coords(15000.0, 0.0, 22000.0)
    assert reg_id_dry == 22
    assert name_en_dry == "Dryman's Point"


def test_galactic_regions_fallback_on_none_and_invalid():
    """Validates safe fallback to Inner Orion Spur when coordinates are None or invalid."""
    assert get_region_from_coords(None, None, None) == DEFAULT_FALLBACK_REGION
    assert get_region_from_coords(0.0, None, 100.0) == DEFAULT_FALLBACK_REGION
    assert get_region_from_coords("invalid", 0.0, 0.0) == DEFAULT_FALLBACK_REGION

    # Extreme galactic outer space beyond all known boxes
    fallback_res = get_region_from_coords(150000.0, 50000.0, -200000.0)
    assert fallback_res == DEFAULT_FALLBACK_REGION


def test_get_region_info_lookup():
    """Validates region info lookup by ID."""
    assert get_region_info(1) == (1, "Galactic Centre", "銀河中心核")
    assert get_region_info(19) == (19, "Inner Orion Spur", "インナー・オリオン・スパー")
    assert get_region_info(999) == DEFAULT_FALLBACK_REGION
    assert get_region_info(None) == DEFAULT_FALLBACK_REGION


def test_exobiology_electricae_region_constraint():
    """
    Validates that Electricae:
    - Is strictly excluded in Inner Orion Spur (Sol/Bubble, region 19).
    - Is successfully predicted in an allowed outer region (e.g. Formidine Rift, region 17).
    """
    # Test body physically optimal for Electricae (Neon atmosphere, Rocky body, low temp ~75K, A-type parent star)
    electricae_body = {
        "landable": True,
        "planet_class": "Rocky body",
        "atmosphere": "Neon",
        "surface_temperature": 75.0,
        "surface_gravity_g": 0.15,
        "surface_pressure": 0.02 * 101325,
        "bio_signals": 1,
        "star_type": "A",
    }

    # Case 1: In Inner Orion Spur (Sol at 0, 0, 0) -> Electricae MUST NOT appear
    cands_sol = predict_exobiology_candidates(
        electricae_body,
        star_pos=(0.0, 0.0, 0.0)
    )
    assert not any(c.get("genus") == "Electricae" for c in cands_sol), (
        "Electricae must NOT be predicted in Inner Orion Spur / Bubble"
    )

    # Also test by explicit region_id = 19
    cands_reg19 = predict_exobiology_candidates(
        electricae_body,
        region_id=19
    )
    assert not any(c.get("genus") == "Electricae" for c in cands_reg19)

    # Case 2: In Formidine Rift (-10000, 50, 10000, region 17) -> Electricae MUST be predicted
    cands_rift = predict_exobiology_candidates(
        electricae_body,
        star_pos=(-10000.0, 50.0, 10000.0)
    )
    assert any(c.get("genus") == "Electricae" for c in cands_rift), (
        "Electricae should be predicted in Formidine Rift (allowed region)"
    )

    # Also test by explicit region_id = 17
    cands_reg17 = predict_exobiology_candidates(
        electricae_body,
        region_id=17
    )
    assert any(c.get("genus") == "Electricae" for c in cands_reg17)


def test_exobiology_unconstrained_species_in_any_region():
    """
    Validates that species without regional constraints (e.g. Stratum Tectonicas)
    appear across different regions provided physical parameters match.
    """
    stratum_body = {
        "landable": True,
        "planet_class": "High metal content body",
        "atmosphere": "Carbon dioxide",
        "surface_temperature": 180.0,
        "surface_gravity_g": 0.4,
        "surface_pressure": 0.05 * 101325,
        "bio_signals": 1,
        "star_type": "G",
    }

    # Sol / Inner Orion Spur
    cands_sol = predict_exobiology_candidates(stratum_body, star_pos=(0.0, 0.0, 0.0))
    assert any("Stratum" in c.get("species", "") for c in cands_sol)

    # Formidine Rift
    cands_rift = predict_exobiology_candidates(stratum_body, star_pos=(-10000.0, 50.0, 10000.0))
    assert any("Stratum" in c.get("species", "") for c in cands_rift)

    # Galactic Centre
    cands_core = predict_exobiology_candidates(stratum_body, star_pos=(25.0, -21.0, 25900.0))
    assert any("Stratum" in c.get("species", "") for c in cands_core)


def test_predict_exobiology_discrete_parameter_call():
    """
    Validates calling predict_exobiology_candidates using discrete arguments:
    predict_exobiology_candidates(planet_class, atmosphere_type, surface_temp, gravity, star_type, star_pos=..., region_id=...)
    """
    # Discrete call in Inner Orion Spur (Sol) -> Electricae excluded
    cands_sol = predict_exobiology_candidates(
        planet_class="Rocky body",
        atmosphere_type="Neon",
        surface_temp=75.0,
        gravity=0.15,
        star_type="A",
        star_pos=(0.0, 0.0, 0.0)
    )
    assert not any(c.get("genus") == "Electricae" for c in cands_sol)

    # Discrete call in Formidine Rift -> Electricae included
    cands_rift = predict_exobiology_candidates(
        planet_class="Rocky body",
        atmosphere_type="Neon",
        surface_temp=75.0,
        gravity=0.15,
        star_type="A",
        star_pos=(-10000.0, 50.0, 10000.0)
    )
    assert any(c.get("genus") == "Electricae" for c in cands_rift)
