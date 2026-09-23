"""
rarity_scorer.py - Rule-based Deterministic Astrophysical Rarity Scorer
Elite Dangerous Journal Analyzer

Calculates deterministic rarity scores, tags, and detailed anomaly reports
from Elite Dangerous journal Scan events based on astrophysical physical models,
stellar evolution constraints, extreme orbital dynamics, and ring morphologies.
"""

from __future__ import annotations

import json
import math
from typing import Any, Dict, List, Optional, Tuple

# Physical Constants (SI & Astronomical)
EARTH_MASS_KG: float = 5.9722e24
SOLAR_MASS_KG: float = 1.98847e30


def _get_field(data: dict, *keys: str, default: Any = None) -> Any:
    """
    Safely retrieve a value from a dictionary using fallback keys with strict None guarding.
    Guarantees that 0, 0.0, False, and empty strings are preserved as valid values,
    falling back only when the key is absent or the value is explicitly None.
    """
    for k in keys:
        if k in data and data[k] is not None:
            return data[k]
    return default


def calculate_density_g_cm3(
    mass_em: Optional[float],
    stellar_mass: Optional[float],
    radius_m: Optional[float]
) -> Optional[float]:
    """
    Calculates mean density in g/cm^3 from mass and radius.
    Supports either Earth Masses (MassEM) or Solar Masses (StellarMass) with radius in meters.
    Strictly guards against None, zero, and negative values.
    """
    if radius_m is None or radius_m <= 0:
        return None

    mass_kg: Optional[float] = None
    if mass_em is not None and mass_em > 0:
        mass_kg = float(mass_em) * EARTH_MASS_KG
    elif stellar_mass is not None and stellar_mass > 0:
        mass_kg = float(stellar_mass) * SOLAR_MASS_KG

    if mass_kg is None or mass_kg <= 0:
        return None

    # Volume in m^3 = (4/3) * pi * r^3
    volume_m3 = (4.0 / 3.0) * math.pi * math.pow(float(radius_m), 3)
    if volume_m3 <= 0:
        return None

    # Density in kg/m^3 -> convert to g/cm^3 (divide by 1000)
    density_kg_m3 = mass_kg / volume_m3
    return density_kg_m3 / 1000.0


def calculate_celestial_rarity(
    body_data: dict,
    star_system_age: Optional[float] = None
) -> dict:
    """
    Calculates astrophysical rarity score and anomaly tags for a celestial body.

    Args:
        body_data: Dictionary containing ED Journal Scan event or DB bodies row.
                   Supports both PascalCase ED journal keys and snake_case DB columns.
        star_system_age: Optional system age in millions of years (Age_MY).

    Returns:
        dict: {
            "score": int,
            "tags": list[str],
            "details": dict
        }
    """
    if not isinstance(body_data, dict):
        return {
            "score": 0,
            "tags": [],
            "details": {"breakdown": []}
        }

    score: int = 0
    tags: List[str] = []
    breakdown: List[Dict[str, Any]] = []

    # ---------------------------------------------------------
    # 0. Field Extractions with Strict None Guarding
    # ---------------------------------------------------------
    # Star / Planet classification
    star_type_raw = _get_field(body_data, "StarType", "star_type")
    star_type: Optional[str] = str(star_type_raw).strip() if star_type_raw is not None else None
    is_star: bool = bool(star_type and star_type != "" and star_type.lower() != "null")

    planet_class_raw = _get_field(body_data, "PlanetClass", "planet_class")
    planet_class: Optional[str] = str(planet_class_raw).strip() if planet_class_raw is not None else None

    # System Age (Age_MY)
    sys_age_val = star_system_age if star_system_age is not None else _get_field(body_data, "Age_MY", "age_my")
    system_age_my: Optional[float] = float(sys_age_val) if sys_age_val is not None else None

    # Orbital Dynamics
    ecc_raw = _get_field(body_data, "Eccentricity", "eccentricity")
    eccentricity: Optional[float] = float(ecc_raw) if ecc_raw is not None else None

    inc_raw = _get_field(body_data, "OrbitalInclination", "orbital_inclination")
    orbital_inclination: Optional[float] = float(inc_raw) if inc_raw is not None else None

    period_raw = _get_field(body_data, "OrbitalPeriod", "orbital_period")
    orbital_period_s: Optional[float] = float(period_raw) if period_raw is not None else None

    tilt_raw = _get_field(body_data, "AxialTilt", "axial_tilt")
    axial_tilt_rad: Optional[float] = float(tilt_raw) if tilt_raw is not None else None

    # Physical Dimensions
    radius_m_raw = _get_field(body_data, "Radius", "radius")
    radius_m: Optional[float] = float(radius_m_raw) if radius_m_raw is not None else None

    mass_em_raw = _get_field(body_data, "MassEM", "mass_em")
    mass_em: Optional[float] = float(mass_em_raw) if mass_em_raw is not None else None

    stellar_mass_raw = _get_field(body_data, "StellarMass", "stellar_mass")
    stellar_mass: Optional[float] = float(stellar_mass_raw) if stellar_mass_raw is not None else None

    # Rings
    rings_data = _get_field(body_data, "Rings", "rings")
    if isinstance(rings_data, str):
        try:
            rings_data = json.loads(rings_data)
        except Exception:
            rings_data = []
    if not isinstance(rings_data, list):
        rings_data = []

    # ---------------------------------------------------------
    # 1. System Age & Stellar Evolution Anomalies
    # ---------------------------------------------------------
    if system_age_my is not None:
        # Ultra-Young System: Age_MY < 10
        if system_age_my < 10.0:
            score += 20
            tag = "Ultra-Young System"
            tags.append(tag)
            breakdown.append({"tag": tag, "points": 20, "reason": f"System age {system_age_my} MY < 10 MY"})

        # Ancient Population II System: Age_MY > 12500
        if system_age_my > 12500.0:
            score += 20
            tag = "Ancient Population II"
            tags.append(tag)
            breakdown.append({"tag": tag, "points": 20, "reason": f"System age {system_age_my} MY > 12500 MY"})

        # Stellar Evolution Anomaly: O/B stars surviving beyond expected lifetime (> 300 MY)
        if is_star and star_type:
            st_upper = star_type.upper()
            if (st_upper.startswith("O") or st_upper.startswith("B")) and system_age_my > 300.0:
                score += 30
                tag = "Stellar Evolution Anomaly (O/B Over-aged)"
                tags.append(tag)
                breakdown.append({
                    "tag": tag,
                    "points": 30,
                    "reason": f"O/B type star '{star_type}' in an aged system ({system_age_my} MY > 300 MY)"
                })

    # ---------------------------------------------------------
    # 2. Orbital Mechanics Limits
    # ---------------------------------------------------------
    # Eccentricity
    if eccentricity is not None:
        if eccentricity >= 0.9:
            score += 30
            tag = "Hyper-Eccentric"
            tags.append(tag)
            breakdown.append({"tag": tag, "points": 30, "reason": f"Eccentricity {eccentricity:.4f} >= 0.9"})
        elif eccentricity >= 0.8:
            score += 15
            tag = "High Eccentricity"
            tags.append(tag)
            breakdown.append({"tag": tag, "points": 15, "reason": f"Eccentricity {eccentricity:.4f} in [0.8, 0.9)"})

    # Orbital Inclination (Degrees)
    if orbital_inclination is not None:
        abs_inc = abs(orbital_inclination)
        # Retrograde Orbit: abs(OrbitalInclination) > 90
        if abs_inc > 90.0:
            score += 25
            tag = "Retrograde Orbit"
            tags.append(tag)
            breakdown.append({"tag": tag, "points": 25, "reason": f"Orbital inclination {orbital_inclination:.2f}° > 90°"})

        # Polar Orbit: 85 <= abs(OrbitalInclination) <= 95
        if 85.0 <= abs_inc <= 95.0:
            score += 15
            tag = "Polar Orbit"
            tags.append(tag)
            breakdown.append({"tag": tag, "points": 15, "reason": f"Orbital inclination {orbital_inclination:.2f}° in [85°, 95°]"})

    # Ultra-Short Orbital Period (Hot Orbit, Planets only, < 1 day)
    if not is_star and orbital_period_s is not None and 0 < orbital_period_s < 86400.0:
        score += 20
        tag = "Ultra-Short Period"
        tags.append(tag)
        breakdown.append({
            "tag": tag,
            "points": 20,
            "reason": f"Orbital period {orbital_period_s / 3600.0:.2f} h < 24 h (1 day)"
        })

    # Extreme Axial Tilt (Sideways Rotation, 80° - 100°)
    axial_tilt_deg: Optional[float] = None
    if axial_tilt_rad is not None:
        axial_tilt_deg = math.degrees(axial_tilt_rad)
        abs_tilt = abs(axial_tilt_deg)
        if 80.0 <= abs_tilt <= 100.0:
            score += 15
            tag = "Extreme Axial Tilt (Sideways)"
            tags.append(tag)
            breakdown.append({
                "tag": tag,
                "points": 15,
                "reason": f"Axial tilt {axial_tilt_deg:.2f}° within sideways range [80°, 100°]"
            })

    # ---------------------------------------------------------
    # 3. Density & Structural Extremes
    # ---------------------------------------------------------
    density_g_cm3 = calculate_density_g_cm3(mass_em, stellar_mass, radius_m)
    if density_g_cm3 is not None and density_g_cm3 > 0:
        p_class_upper = (planet_class or "").upper()
        # Chthonian Candidate / Super-Dense Core: Rock/Metal body with density > 15.0 g/cm^3
        is_rocky_metal = any(k in p_class_upper for k in ["METAL", "ROCKY", "HIGH METAL"])
        if is_rocky_metal and density_g_cm3 > 15.0:
            score += 30
            tag = "Super-Dense Core"
            tags.append(tag)
            breakdown.append({
                "tag": tag,
                "points": 30,
                "reason": f"Rocky/Metal density {density_g_cm3:.2f} g/cm³ > 15.0 g/cm³"
            })

        # Super-Puff Planet: Gas giant with density < 0.1 g/cm^3
        is_gas_giant = any(k in p_class_upper for k in ["GAS", "GIANT", "SUDARSKY", "HELIUM"])
        if is_gas_giant and density_g_cm3 < 0.1:
            score += 25
            tag = "Super-Puff Planet"
            tags.append(tag)
            breakdown.append({
                "tag": tag,
                "points": 25,
                "reason": f"Gas giant density {density_g_cm3:.4f} g/cm³ < 0.1 g/cm³"
            })

    # ---------------------------------------------------------
    # 4. Ring Systems Morphologies
    # ---------------------------------------------------------
    if rings_data:
        has_rings = len(rings_data) > 0
        has_massive_ring = False
        if radius_m is not None and radius_m > 0:
            for r in rings_data:
                if isinstance(r, dict):
                    inner_rad = _get_field(r, "InnerRad", "inner_rad")
                    outer_rad = _get_field(r, "OuterRad", "outer_rad")
                    if inner_rad is not None and outer_rad is not None:
                        ring_width = float(outer_rad) - float(inner_rad)
                        if ring_width > 10.0 * radius_m:
                            has_massive_ring = True
                            break

        if has_massive_ring:
            score += 20
            tag = "Massive Ring System"
            tags.append(tag)
            breakdown.append({
                "tag": tag,
                "points": 20,
                "reason": "Ring width exceeds 10x body radius"
            })

        # Exotic Ring Host: Ringed Star, Earthlike (ELW), or Ammonia World (AW)
        is_exotic_host = False
        p_class_upper = (planet_class or "").upper()
        if is_star:
            is_exotic_host = True
        elif "EARTH" in p_class_upper or "EARTHLIKE" in p_class_upper or "AMMONIA" in p_class_upper:
            is_exotic_host = True

        if has_rings and is_exotic_host:
            score += 35
            tag = "Exotic Ring Host"
            tags.append(tag)
            host_desc = star_type if is_star else planet_class
            breakdown.append({
                "tag": tag,
                "points": 35,
                "reason": f"Exotic body ({host_desc}) harboring a planetary ring system"
            })

    # ---------------------------------------------------------
    # 5. Result Assembly
    # ---------------------------------------------------------
    return {
        "score": score,
        "tags": tags,
        "details": {
            "system_age_my": system_age_my,
            "density_g_cm3": round(density_g_cm3, 4) if density_g_cm3 is not None else None,
            "eccentricity": round(eccentricity, 6) if eccentricity is not None else None,
            "orbital_inclination_deg": round(orbital_inclination, 4) if orbital_inclination is not None else None,
            "orbital_period_s": round(orbital_period_s, 2) if orbital_period_s is not None else None,
            "axial_tilt_deg": round(axial_tilt_deg, 4) if axial_tilt_deg is not None else None,
            "breakdown": breakdown
        }
    }
