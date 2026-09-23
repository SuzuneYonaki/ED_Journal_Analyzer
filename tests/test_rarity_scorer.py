"""
test_rarity_scorer.py - Unit tests for Rule-based Deterministic Astrophysical Rarity Scorer
Elite Dangerous Journal Analyzer
"""

import math
import pytest
from app.parser.rarity_scorer import (
    calculate_celestial_rarity,
    calculate_density_g_cm3,
    EARTH_MASS_KG,
)


def test_empty_and_none_input_fallback():
    """Verify complete NULL-safety and safe fallbacks for empty/None inputs."""
    res_empty = calculate_celestial_rarity({})
    assert res_empty["score"] == 0
    assert res_empty["tags"] == []
    assert isinstance(res_empty["details"], dict)

    res_none = calculate_celestial_rarity(None)  # type: ignore
    assert res_none["score"] == 0
    assert res_none["tags"] == []

    # Body with explicit None values across all fields
    res_all_nones = calculate_celestial_rarity({
        "StarType": None,
        "PlanetClass": None,
        "Age_MY": None,
        "Eccentricity": None,
        "OrbitalInclination": None,
        "OrbitalPeriod": None,
        "AxialTilt": None,
        "Radius": None,
        "MassEM": None,
        "Rings": None,
    })
    assert res_all_nones["score"] == 0
    assert res_all_nones["tags"] == []


def test_system_age_young_and_ancient():
    """Test ultra-young and ancient population II system age triggers."""
    # Ultra-Young System: Age_MY < 10
    res_young = calculate_celestial_rarity({"Age_MY": 5.0})
    assert res_young["score"] == 20
    assert "Ultra-Young System" in res_young["tags"]

    # Ancient Population II: Age_MY > 12500
    res_ancient = calculate_celestial_rarity({"Age_MY": 13000.0})
    assert res_ancient["score"] == 20
    assert "Ancient Population II" in res_ancient["tags"]

    # Normal age: No points
    res_normal = calculate_celestial_rarity({"Age_MY": 4500.0})
    assert res_normal["score"] == 0
    assert res_normal["tags"] == []


def test_stellar_evolution_anomaly():
    """Test O/B stars surviving beyond expected lifetime (> 300 MY)."""
    # Normal young B-star
    res_b_young = calculate_celestial_rarity({
        "StarType": "B",
        "Age_MY": 50.0
    })
    assert res_b_young["score"] == 0
    assert "Stellar Evolution Anomaly (O/B Over-aged)" not in res_b_young["tags"]

    # Over-aged O-star (Age > 300 MY)
    res_o_old = calculate_celestial_rarity({
        "StarType": "O_BlueGiant",
        "Age_MY": 450.0
    })
    assert res_o_old["score"] == 30
    assert "Stellar Evolution Anomaly (O/B Over-aged)" in res_o_old["tags"]

    # Over-aged B-star (via snake_case fields)
    res_b_old = calculate_celestial_rarity({
        "star_type": "B",
        "age_my": 500.0
    })
    assert res_b_old["score"] == 30
    assert "Stellar Evolution Anomaly (O/B Over-aged)" in res_b_old["tags"]


def test_orbital_mechanics_eccentricity():
    """Test eccentricity thresholds (0.8 <= e < 0.9 and e >= 0.9)."""
    # High Eccentricity: 0.8 <= e < 0.9
    res_high = calculate_celestial_rarity({"Eccentricity": 0.85})
    assert res_high["score"] == 15
    assert "High Eccentricity" in res_high["tags"]

    # Hyper-Eccentric: e >= 0.9
    res_hyper = calculate_celestial_rarity({"eccentricity": 0.945})
    assert res_hyper["score"] == 30
    assert "Hyper-Eccentric" in res_hyper["tags"]

    # Zero eccentricity (circular orbit) must be preserved as valid 0
    res_circ = calculate_celestial_rarity({"Eccentricity": 0.0})
    assert res_circ["score"] == 0
    assert res_circ["tags"] == []
    assert res_circ["details"]["eccentricity"] == 0.0


def test_orbital_mechanics_inclination():
    """Test retrograde and polar orbit inclination detections."""
    # Polar Orbit: 85° <= abs(inc) <= 95°
    res_polar = calculate_celestial_rarity({"OrbitalInclination": 88.0})
    assert res_polar["score"] == 15
    assert "Polar Orbit" in res_polar["tags"]

    # Retrograde Orbit: abs(inc) > 90° (e.g. 135°)
    res_retro = calculate_celestial_rarity({"OrbitalInclination": -135.0})
    assert res_retro["score"] == 25
    assert "Retrograde Orbit" in res_retro["tags"]

    # Overlapping boundary: 92° is both Polar (85-95) and Retrograde (> 90)
    res_overlap = calculate_celestial_rarity({"OrbitalInclination": 92.0})
    assert res_overlap["score"] == 40
    assert "Retrograde Orbit" in res_overlap["tags"]
    assert "Polar Orbit" in res_overlap["tags"]


def test_orbital_period_ultra_short():
    """Test ultra-short period planet (< 1 day = 86400 s)."""
    # Planet orbiting in 12 hours (43200 s)
    res_hot = calculate_celestial_rarity({
        "PlanetClass": "High metal content body",
        "OrbitalPeriod": 43200.0
    })
    assert res_hot["score"] == 20
    assert "Ultra-Short Period" in res_hot["tags"]

    # Star should NOT trigger ultra-short period
    res_star_fast = calculate_celestial_rarity({
        "StarType": "M",
        "OrbitalPeriod": 40000.0
    })
    assert "Ultra-Short Period" not in res_star_fast["tags"]


def test_axial_tilt_sideways():
    """Test extreme sideways axial tilt (80° to 100° in radians)."""
    # 90 degrees = pi / 2 radians
    tilt_90_rad = math.pi / 2.0
    res_tilt = calculate_celestial_rarity({"AxialTilt": tilt_90_rad})
    assert res_tilt["score"] == 15
    assert "Extreme Axial Tilt (Sideways)" in res_tilt["tags"]

    # 45 degrees should not trigger
    res_normal_tilt = calculate_celestial_rarity({"AxialTilt": math.pi / 4.0})
    assert "Extreme Axial Tilt (Sideways)" not in res_normal_tilt["tags"]


def test_density_extremes_super_dense_and_puff():
    """Test Chthonian super-dense planet and super-puff gas giant."""
    # Earth radius ~ 6,371,000 m. Earth density ~ 5.51 g/cm^3
    r_earth = 6371000.0
    # 1. Super-Dense Core: 10 Earth masses with 1 Earth radius -> density ~ 55.1 g/cm^3 > 15.0
    res_dense = calculate_celestial_rarity({
        "PlanetClass": "Metal rich body",
        "MassEM": 10.0,
        "Radius": r_earth
    })
    assert res_dense["score"] == 30
    assert "Super-Dense Core" in res_dense["tags"]
    assert res_dense["details"]["density_g_cm3"] > 15.0

    # 2. Super-Puff Planet: Gas Giant with 5 Earth masses but 100,000,000 m radius -> density ~ 0.007 g/cm^3 < 0.1
    res_puff = calculate_celestial_rarity({
        "PlanetClass": "Sudarsky class I gas giant",
        "MassEM": 5.0,
        "Radius": 100000000.0
    })
    assert res_puff["score"] == 25
    assert "Super-Puff Planet" in res_puff["tags"]
    assert 0 < res_puff["details"]["density_g_cm3"] < 0.1


def test_ring_system_morphology():
    """Test massive ring systems and exotic host detection."""
    # Radius = 10,000,000 m
    # Ring width = 250,000,000 m - 100,000,000 m = 150,000,000 m > 10 * 10,000,000 m
    massive_rings = [
        {
            "Name": "A Ring",
            "RingClass": "eRingClass_Icy",
            "InnerRad": 100000000.0,
            "OuterRad": 250000000.0
        }
    ]

    # Massive ring on gas giant
    res_massive = calculate_celestial_rarity({
        "PlanetClass": "Gas giant with water based life",
        "Radius": 10000000.0,
        "Rings": massive_rings
    })
    assert res_massive["score"] == 20
    assert "Massive Ring System" in res_massive["tags"]

    # Exotic Ring Host 1: Ringed Star
    res_ringed_star = calculate_celestial_rarity({
        "StarType": "T",
        "Radius": 50000000.0,
        "Rings": [{"InnerRad": 60000000.0, "OuterRad": 80000000.0}]
    })
    assert "Exotic Ring Host" in res_ringed_star["tags"]
    assert res_ringed_star["score"] >= 35

    # Exotic Ring Host 2: Ringed Earth-like World (ELW)
    res_ringed_elw = calculate_celestial_rarity({
        "PlanetClass": "Earthlike body",
        "Radius": 6371000.0,
        "Rings": [{"InnerRad": 10000000.0, "OuterRad": 20000000.0}]
    })
    assert "Exotic Ring Host" in res_ringed_elw["tags"]
    assert res_ringed_elw["score"] >= 35


def test_cumulative_scoring():
    """Verify that multiple anomalies combine correctly into a total score."""
    # Body with:
    # - Ultra-Young System (Age 5 MY: +20)
    # - Hyper-Eccentric (0.92: +30)
    # - Ultra-Short Period (10h = 36000s: +20)
    # Total = 70 pt
    res_combo = calculate_celestial_rarity({
        "Age_MY": 5.0,
        "PlanetClass": "High metal content body",
        "Eccentricity": 0.92,
        "OrbitalPeriod": 36000.0
    })
    assert res_combo["score"] == 70
    assert len(res_combo["tags"]) == 3
    assert set(res_combo["tags"]) == {
        "Ultra-Young System",
        "Hyper-Eccentric",
        "Ultra-Short Period"
    }
