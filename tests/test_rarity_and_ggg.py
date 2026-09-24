"""
test_rarity_and_ggg.py - Unit Tests for Astrophysical Rarity Scorer, GGG Evaluation, and TTS Priority Queue
Elite Dangerous Journal Analyzer
"""

import asyncio
import math
import pytest
from app.parser.rarity_scorer import (
    calculate_celestial_rarity,
    calculate_ggg_probability,
    calculate_density_g_cm3
)
from app.services.tts_service import TTSService


# =====================================================================
# 1. Stellar Age & Evolution Tests
# =====================================================================

def test_ultra_young_system():
    body = {
        "BodyName": "Young Star A",
        "StarType": "T",
        "Age_MY": 5.0
    }
    result = calculate_celestial_rarity(body)
    assert "Ultra-Young System" in result["tags"]
    assert result["rarity_score"] >= 20
    assert result["score"] == result["rarity_score"]


def test_ancient_population_ii_system():
    body = {
        "BodyName": "Ancient Star",
        "StarType": "M",
        "Age_MY": 13000.0
    }
    result = calculate_celestial_rarity(body)
    assert "Ancient Population II" in result["tags"]
    assert result["rarity_score"] >= 20


def test_stellar_evolution_anomaly():
    # O-type star with age > 300 MY is physically anomalous (O stars live only ~10-30 MY)
    body = {
        "BodyName": "Anomalous O Star",
        "StarType": "O",
        "Age_MY": 500.0
    }
    result = calculate_celestial_rarity(body)
    assert "Stellar Evolution Anomaly (O/B Over-aged)" in result["tags"]
    assert result["rarity_score"] >= 30


# =====================================================================
# 2. Orbital Mechanics & Density Extreme Tests
# =====================================================================

def test_hyper_eccentric_orbit():
    body = {
        "BodyName": "Eccentric Planet",
        "PlanetClass": "High metal content body",
        "Eccentricity": 0.95
    }
    result = calculate_celestial_rarity(body)
    assert "Hyper-Eccentric" in result["tags"]
    assert result["rarity_score"] >= 30


def test_retrograde_and_polar_orbits():
    # Retrograde (> 90 deg)
    body_retro = {
        "BodyName": "Retro Planet",
        "PlanetClass": "Rocky body",
        "OrbitalInclination": 120.0
    }
    res_retro = calculate_celestial_rarity(body_retro)
    assert "Retrograde Orbit" in res_retro["tags"]
    assert res_retro["rarity_score"] >= 25

    # Polar (85 to 95 deg)
    body_polar = {
        "BodyName": "Polar Planet",
        "PlanetClass": "Rocky body",
        "OrbitalInclination": 89.5
    }
    res_polar = calculate_celestial_rarity(body_polar)
    assert "Polar Orbit" in res_polar["tags"]
    assert res_polar["rarity_score"] >= 15


def test_ultra_short_period():
    # Orbital period under 1 day (86400 s) for a planet
    body = {
        "BodyName": "Hot Super-Earth",
        "PlanetClass": "High metal content body",
        "OrbitalPeriod": 43200.0  # 12 hours
    }
    result = calculate_celestial_rarity(body)
    assert "Ultra-Short Period" in result["tags"]
    assert result["rarity_score"] >= 20


def test_extreme_axial_tilt():
    # 90 degrees tilt in radians: pi / 2
    body = {
        "BodyName": "Sideways Planet",
        "PlanetClass": "Icy body",
        "AxialTilt": math.pi / 2.0  # ~1.570796 rad = 90 deg
    }
    result = calculate_celestial_rarity(body)
    assert "Extreme Axial Tilt (Sideways)" in result["tags"]
    assert result["rarity_score"] >= 15


def test_super_dense_core():
    # Earth Mass = 5.0, Radius = 3,000,000 m (3,000 km)
    # Volume = 4/3 * pi * (3e6)^3 = 1.13097e20 m^3
    # Mass = 5 * 5.9722e24 = 2.9861e25 kg
    # Density = 2.9861e25 / 1.13097e20 = 26403 kg/m^3 = 26.4 g/cm^3 > 15 g/cm^3
    body = {
        "BodyName": "Chthonian Remnant",
        "PlanetClass": "High metal content body",
        "MassEM": 5.0,
        "Radius": 3000000.0
    }
    result = calculate_celestial_rarity(body)
    assert "Super-Dense Core" in result["tags"]
    assert result["rarity_score"] >= 30


def test_super_puff_gas_giant():
    # Gas giant with huge radius and low mass: Mass = 15 M_Earth, Radius = 70,000,000 m
    # Volume = 4/3 * pi * (7e7)^3 = 1.4367e24 m^3
    # Mass = 15 * 5.9722e24 = 8.9583e25 kg
    # Density = 8.9583e25 / 1.4367e24 = 62.3 kg/m^3 = 0.062 g/cm^3 < 0.1 g/cm^3
    body = {
        "BodyName": "Cotton Candy Giant",
        "PlanetClass": "Sudarsky class I gas giant",
        "MassEM": 15.0,
        "Radius": 70000000.0
    }
    result = calculate_celestial_rarity(body)
    assert "Super-Puff Planet" in result["tags"]
    assert result["rarity_score"] >= 25


def test_massive_and_exotic_rings():
    # Earth-like world with rings (Exotic Ring Host)
    body = {
        "BodyName": "Ringed Earth",
        "PlanetClass": "Earthlike body",
        "Radius": 6371000.0,
        "Rings": [
            {
                "Name": "Ring A",
                "InnerRad": 10000000.0,
                "OuterRad": 80000000.0  # width = 70,000 km > 10 * 6,371 km
            }
        ]
    }
    result = calculate_celestial_rarity(body)
    assert "Exotic Ring Host" in result["tags"]
    assert "Massive Ring System" in result["tags"]
    assert result["rarity_score"] >= 55


# =====================================================================
# 3. Green Gas Giant (GGG) Probability Scoring Tests
# =====================================================================

def test_ggg_non_candidate():
    # Standard class III without life
    body = {
        "BodyName": "Standard Giant",
        "PlanetClass": "Sudarsky class III gas giant",
        "SurfaceTemperature": 200.0,
        "MassEM": 100.0
    }
    ggg = calculate_ggg_probability(body)
    assert ggg["score"] == 0
    assert ggg["is_candidate"] is False
    assert ggg["alert_level"] is None
    assert ggg["tts_message"] is None


def test_ggg_notice_candidate():
    # Ammonia-based life (20) + Temp 200K (25) + Mass 100 (15) = 60pt -> NOTICE
    body = {
        "BodyName": "Ammonia Giant",
        "PlanetClass": "Gas giant with ammonia based life",
        "SurfaceTemperature": 200.0,
        "MassEM": 100.0,
        "DistanceFromArrivalLS": 100.0,  # outside 500-5000 (0pt)
        "star_type": "M"  # M star (0pt)
    }
    ggg = calculate_ggg_probability(body)
    assert ggg["score"] == 60
    assert ggg["is_candidate"] is True
    assert ggg["alert_level"] == "NOTICE"
    assert ggg["tts_message"] == "Ammonia Giantはグリーンガスジャイアント候補です。"


def test_ggg_urgent_candidate():
    # Water-based life (35) + Temp 220K (25) + Mass 150 (15) + Dist 1500 (15) + Host Star G (10) = 100pt -> URGENT
    body = {
        "BodyName": "Green Giant Alpha",
        "PlanetClass": "Sudarsky class I gas giant with water based life",
        "SurfaceTemperature": 220.0,
        "MassEM": 150.0,
        "DistanceFromArrivalLS": 1500.0,
        "parent_star_type": "G"
    }
    ggg = calculate_ggg_probability(body)
    assert ggg["score"] == 100
    assert ggg["is_candidate"] is True
    assert ggg["alert_level"] == "URGENT"
    assert ggg["tts_message"] == "Green Giant Alphaはグリーンガスジャイアント候補です。"

    # When evaluated through calculate_celestial_rarity
    res = calculate_celestial_rarity(body)
    assert "GGG Candidate" in res["tags"]
    assert res["ggg_evaluation"]["alert_level"] == "URGENT"


# =====================================================================
# 4. TTS Service Priority Queue Tests
# =====================================================================

def test_tts_priority_queue_ordering():
    def _run_test():
        tts = TTSService()
        tts.config["enabled"] = True

        # Enqueue routine messages first
        tts.enqueue_speak("Routine message 1", priority=False)
        tts.enqueue_speak("Routine message 2", priority=False)

        # Enqueue urgent message later
        tts.enqueue_speak("URGENT: GGG Candidate detected!", priority=True)

        # Next normal message
        tts.enqueue_speak("Routine message 3", priority=False)

        # Pop from internal queue directly to verify extraction order
        # Expected order:
        # 1. URGENT (priority=0)
        # 2. Routine 1 (priority=1, seq=1)
        # 3. Routine 2 (priority=1, seq=2)
        # 4. Routine 3 (priority=1, seq=4)
        items = []
        while not tts._queue.empty():
            rank, seq, text = tts._queue.get_nowait()
            items.append((rank, text))

        assert items[0] == (0, "URGENT: GGG Candidate detected!")
        assert items[1] == (1, "Routine message 1")
        assert items[2] == (1, "Routine message 2")
        assert items[3] == (1, "Routine message 3")

    asyncio.run(asyncio.to_thread(_run_test))


# =====================================================================
# 5. Strict NULL and Boundary Safety Tests
# =====================================================================

def test_rarity_strict_null_safety():
    # All fields zero or None
    body_zeros = {
        "BodyName": "Zero Planet",
        "PlanetClass": None,
        "Eccentricity": 0.0,
        "OrbitalInclination": 0.0,
        "OrbitalPeriod": 0.0,
        "AxialTilt": 0.0,
        "MassEM": 0.0,
        "Radius": 0.0,
        "SurfaceTemperature": 0.0,
        "DistanceFromArrivalLS": 0.0
    }
    res = calculate_celestial_rarity(body_zeros)
    assert res["rarity_score"] == 0
    assert res["tags"] == []
    assert res["details"]["eccentricity"] == 0.0
    assert res["details"]["orbital_inclination_deg"] == 0.0
    assert res["details"]["density_g_cm3"] is None  # radius 0 cannot produce valid density
    assert res["ggg_evaluation"]["is_candidate"] is False


def test_calculate_density_invalid_inputs():
    assert calculate_density_g_cm3(None, None, 1000.0) is None
    assert calculate_density_g_cm3(1.0, None, None) is None
    assert calculate_density_g_cm3(1.0, None, 0.0) is None
    assert calculate_density_g_cm3(0.0, None, 1000.0) is None
    assert calculate_density_g_cm3(-5.0, None, 1000.0) is None
    assert calculate_density_g_cm3(None, -1.0, 1000.0) is None
