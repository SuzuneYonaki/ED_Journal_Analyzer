"""
rarity_scorer.py - Rule-based Deterministic Astrophysical Rarity Scorer & GGG Detector
Elite Dangerous Journal Analyzer

Calculates deterministic rarity scores, tags, detailed anomaly reports, and
Green Gas Giant (GGG) multi-variable probabilities from Elite Dangerous journal
Scan events based on physical models, stellar evolution constraints, and extreme orbital dynamics.
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


def calculate_ggg_probability(
    body_data: dict,
    main_star_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluates multi-variable probability score for Green Gas Giants (GGG).
    Returns a deterministic assessment dictionary:
    {
        "score": int,
        "is_candidate": bool,
        "alert_level": Optional[str],  # "URGENT" | "NOTICE" | None
        "tts_message": Optional[str],
        "breakdown": list[dict]
    }
    """
    planet_class = _get_field(body_data, "PlanetClass", "planet_class")
    surface_temp = _get_field(body_data, "SurfaceTemperature", "surface_temperature")
    mass_em = _get_field(body_data, "MassEM", "mass_em")
    dist_ls = _get_field(body_data, "DistanceFromArrivalLS", "distance_from_arrival_ls")
    body_name = _get_field(body_data, "BodyName", "body_name", default="Unknown Body")

    # Star type resolution
    resolved_star = main_star_type
    if resolved_star is None:
        resolved_star = _get_field(body_data, "parent_star_type", "main_star_type", "star_type")

    p_str = (planet_class or "").lower()

    # Pre-requisite condition: Must be Sudarsky gas giant with water-based or ammonia-based life
    has_water_life = "water based life" in p_str or "water-based life" in p_str
    has_ammonia_life = "ammonia based life" in p_str or "ammonia-based life" in p_str

    if not (has_water_life or has_ammonia_life):
        return {
            "score": 0,
            "is_candidate": False,
            "alert_level": None,
            "tts_message": None,
            "breakdown": []
        }

    score = 0
    breakdown: List[Dict[str, Any]] = []

    # 1. Base Class Bonus
    if has_water_life:
        score += 35
        breakdown.append({"rule": "Water-based Life Gas Giant", "points": 35})
    elif has_ammonia_life:
        score += 20
        breakdown.append({"rule": "Ammonia-based Life Gas Giant", "points": 20})

    # 2. Surface Temperature
    if surface_temp is not None:
        try:
            st = float(surface_temp)
            if 160.0 <= st <= 260.0:
                score += 25
                breakdown.append({"rule": f"Optimal Temperature ({st:.1f} K in 160-260 K)", "points": 25})
            elif 140.0 <= st <= 300.0:
                score += 15
                breakdown.append({"rule": f"Viable Temperature ({st:.1f} K in 140-300 K)", "points": 15})
        except (ValueError, TypeError):
            pass

    # 3. Mass (Earth Masses)
    if mass_em is not None:
        try:
            m = float(mass_em)
            if 50.0 <= m <= 400.0:
                score += 15
                breakdown.append({"rule": f"Optimal Mass ({m:.1f} M_Earth in 50-400)", "points": 15})
            elif m >= 15.0:
                score += 10
                breakdown.append({"rule": f"Viable Mass ({m:.1f} M_Earth >= 15)", "points": 10})
        except (ValueError, TypeError):
            pass

    # 4. Distance From Arrival (Ls)
    if dist_ls is not None:
        try:
            d = float(dist_ls)
            if 500.0 <= d <= 5000.0:
                score += 15
                breakdown.append({"rule": f"Optimal Habitable Separation ({d:.1f} Ls in 500-5000)", "points": 15})
        except (ValueError, TypeError):
            pass

    # 5. Host Star Spectral Type
    if resolved_star:
        s_upper = str(resolved_star).upper().strip()
        # Eligible: F, G, K, N (Neutron), White Dwarfs (DA/D...), H (Black Hole)
        is_f_g_k = any(s_upper.startswith(pfx) for pfx in ("F", "G", "K"))
        is_neutron = s_upper.startswith("N")
        is_black_hole = s_upper.startswith("H") or "BLACKHOLE" in s_upper
        is_white_dwarf = s_upper.startswith("D") or "WHITE DWARF" in s_upper

        if is_f_g_k or is_neutron or is_black_hole or is_white_dwarf:
            score += 10
            breakdown.append({"rule": f"Favorable Host Star ({s_upper})", "points": 10})

    # Alert level and TTS notification determination
    if score >= 80:
        alert_level = "URGENT"
        is_candidate = True
        tts_message = f"注意。{body_name} は高確率のグリーンガスジャイアント候補です。直ちに目視観測を実施してください。"
    elif score >= 60:
        alert_level = "NOTICE"
        is_candidate = True
        tts_message = f"情報。{body_name} はグリーンガスジャイアントの可能性があります。目視観測を推奨します。"
    else:
        alert_level = None
        is_candidate = False
        tts_message = None

    return {
        "score": score,
        "is_candidate": is_candidate,
        "alert_level": alert_level,
        "tts_message": tts_message,
        "breakdown": breakdown
    }


def calculate_celestial_rarity(
    body_data: dict,
    star_system_age: Optional[float] = None,
    main_star_type: Optional[str] = None,
    is_confirmed_ggg: bool = False,
    confirmed_ggg_variant: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculates deterministic rarity score, tags, and detailed anomaly metrics
    for an Elite Dangerous celestial body based on journal Scan attributes.

    Returns:
    {
        "rarity_score": int,
        "score": int,
        "tags": list[str],
        "details": dict,
        "ggg_evaluation": dict
    }
    """
    if not isinstance(body_data, dict):
        return {
            "rarity_score": 0,
            "score": 0,
            "tags": [],
            "details": {"breakdown": []},
            "ggg_evaluation": {
                "score": 0,
                "is_candidate": False,
                "alert_level": None,
                "tts_message": None
            }
        }

    score: int = 0
    tags: List[str] = []
    breakdown: List[Dict[str, Any]] = []

    # Safely extract core attributes
    star_type = _get_field(body_data, "StarType", "star_type")
    planet_class = _get_field(body_data, "PlanetClass", "planet_class")
    mass_em = _get_field(body_data, "MassEM", "mass_em")
    stellar_mass = _get_field(body_data, "StellarMass", "stellar_mass")
    radius_m = _get_field(body_data, "Radius", "radius")
    eccentricity = _get_field(body_data, "Eccentricity", "eccentricity")
    orbital_inclination = _get_field(body_data, "OrbitalInclination", "orbital_inclination")
    orbital_period_s = _get_field(body_data, "OrbitalPeriod", "orbital_period")
    axial_tilt_rad = _get_field(body_data, "AxialTilt", "axial_tilt")

    # Rings data normalization
    rings_data = _get_field(body_data, "Rings", "rings")
    if isinstance(rings_data, str):
        try:
            rings_data = json.loads(rings_data)
        except Exception:
            rings_data = []
    elif not isinstance(rings_data, list):
        rings_data = []

    # System Age (Age_MY)
    sys_age_val = star_system_age if star_system_age is not None else _get_field(body_data, "Age_MY", "age_my")
    system_age_my: Optional[float] = None
    if sys_age_val is not None:
        try:
            system_age_my = float(sys_age_val)
        except (ValueError, TypeError):
            system_age_my = None

    # Density Calculation
    density_g_cm3 = calculate_density_g_cm3(
        float(mass_em) if mass_em is not None else None,
        float(stellar_mass) if stellar_mass is not None else None,
        float(radius_m) if radius_m is not None else None
    )

    # Axial Tilt conversion to degrees
    axial_tilt_deg: Optional[float] = None
    if axial_tilt_rad is not None:
        try:
            # Journal AxialTilt is provided in radians
            axial_tilt_deg = abs(float(axial_tilt_rad) * 180.0 / math.pi)
        except (ValueError, TypeError):
            axial_tilt_deg = None

    is_star = bool(star_type)

    # ---------------------------------------------------------
    # 1. Stellar Age & Evolution Anomalies
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

        # Stellar Evolution Anomaly: O or B class star with Age_MY > 300
        if is_star:
            st_upper = (star_type or "").upper()
            if (st_upper.startswith("O") or st_upper.startswith("B")) and system_age_my > 300.0:
                score += 30
                tag = "Stellar Evolution Anomaly (O/B Over-aged)"
                tags.append(tag)
                breakdown.append({
                    "tag": tag,
                    "points": 30,
                    "reason": f"O/B star ({st_upper}) in system aged {system_age_my} MY > 300 MY"
                })

    # ---------------------------------------------------------
    # 2. Orbital Mechanics Extremes
    # ---------------------------------------------------------
    # Eccentricity extremes
    if eccentricity is not None:
        ecc = float(eccentricity)
        if ecc >= 0.9:
            score += 30
            tag = "Hyper-Eccentric"
            tags.append(tag)
            breakdown.append({"tag": tag, "points": 30, "reason": f"Eccentricity {ecc:.4f} >= 0.9"})
        elif ecc >= 0.8:
            score += 15
            tag = "High Eccentricity"
            tags.append(tag)
            breakdown.append({"tag": tag, "points": 15, "reason": f"Eccentricity {ecc:.4f} in [0.8, 0.9)"})

    # Orbital Inclination extremes
    if orbital_inclination is not None:
        inc = float(orbital_inclination)
        abs_inc = abs(inc)
        # Retrograde Orbit: abs(OrbitalInclination) > 90 deg
        if abs_inc > 90.0:
            score += 25
            tag = "Retrograde Orbit"
            tags.append(tag)
            breakdown.append({"tag": tag, "points": 25, "reason": f"Inclination {inc:.2f}° > 90° (Retrograde)"})
        # Polar Orbit: 85 <= abs(OrbitalInclination) <= 95 deg
        if 85.0 <= abs_inc <= 95.0:
            score += 15
            tag = "Polar Orbit"
            tags.append(tag)
            breakdown.append({"tag": tag, "points": 15, "reason": f"Inclination {inc:.2f}° near 90° (Polar)"})

    # Ultra-Short Orbital Period: Planets orbiting in under 1 Earth day (< 86400 s)
    if not is_star and orbital_period_s is not None:
        p_sec = float(orbital_period_s)
        if 0 < p_sec < 86400.0:
            score += 20
            tag = "Ultra-Short Period"
            tags.append(tag)
            breakdown.append({
                "tag": tag,
                "points": 20,
                "reason": f"Orbital period {p_sec / 3600.0:.2f} h < 24.0 h"
            })

    # Extreme Axial Tilt: 80 <= abs(AxialTilt) <= 100 degrees
    if axial_tilt_deg is not None:
        if 80.0 <= axial_tilt_deg <= 100.0:
            score += 15
            tag = "Extreme Axial Tilt (Sideways)"
            tags.append(tag)
            breakdown.append({
                "tag": tag,
                "points": 15,
                "reason": f"Axial tilt {axial_tilt_deg:.2f}° perpendicular to orbital plane"
            })

    # ---------------------------------------------------------
    # 3. Density & Structural Extremes
    # ---------------------------------------------------------
    if density_g_cm3 is not None and not is_star:
        p_class_upper = (planet_class or "").upper()
        # Chthonian / Super-Dense Core: Rocky or High Metal Content with density > 15.0 g/cm^3
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
                        try:
                            ring_width = float(outer_rad) - float(inner_rad)
                            if ring_width > 10.0 * float(radius_m):
                                has_massive_ring = True
                                break
                        except (ValueError, TypeError):
                            pass

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
    # 5. GGG (Green Gas Giant) Probability & Confirmation Evaluation
    # ---------------------------------------------------------
    has_confirmed_ggg = bool(is_confirmed_ggg or _get_field(body_data, "is_confirmed_ggg", "is_confirmed"))
    confirmed_variant = confirmed_ggg_variant or _get_field(body_data, "confirmed_ggg_variant", "ggg_variant")

    ggg_eval = calculate_ggg_probability(body_data, main_star_type=main_star_type)
    if has_confirmed_ggg:
        # 100% Confirmed GGG via Codex Entry
        score += 100
        tag_base = "Confirmed GGG"
        if tag_base not in tags:
            tags.append(tag_base)
        if confirmed_variant:
            tag_variant = f"Confirmed GGG ({confirmed_variant})"
            if tag_variant not in tags:
                tags.append(tag_variant)
        breakdown.append({
            "tag": tag_base,
            "points": 100,
            "reason": f"Codex-verified Green Gas Giant ({confirmed_variant or 'Identified'})"
        })
        ggg_eval["is_candidate"] = False
        ggg_eval["is_confirmed"] = True
        ggg_eval["alert_level"] = "CONFIRMED"
        ggg_eval["confirmed_variant"] = confirmed_variant
        ggg_eval["score"] = max(ggg_eval.get("score", 0), 100)
    elif ggg_eval["is_candidate"]:
        ggg_tag = "GGG Candidate"
        if ggg_tag not in tags:
            tags.append(ggg_tag)
        score += ggg_eval["score"]
        breakdown.append({
            "tag": ggg_tag,
            "points": ggg_eval["score"],
            "reason": f"GGG evaluation alert_level={ggg_eval['alert_level']} (Score: {ggg_eval['score']})"
        })
        ggg_eval["is_confirmed"] = False

    # ---------------------------------------------------------
    # 6. Result Assembly
    # ---------------------------------------------------------
    return {
        "rarity_score": score,
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
        },
        "ggg_evaluation": {
            "score": ggg_eval.get("score", 0),
            "is_candidate": ggg_eval.get("is_candidate", False),
            "is_confirmed": ggg_eval.get("is_confirmed", False),
            "alert_level": ggg_eval.get("alert_level"),
            "tts_message": ggg_eval.get("tts_message"),
            "confirmed_variant": ggg_eval.get("confirmed_variant")
        }
    }
