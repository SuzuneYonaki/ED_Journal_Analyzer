"""
Exobiology Candidate Prediction Engine for Elite Dangerous.
Implements multi-parameter physical matrix filtering, signal budget allocation,
and confidence ranking based on Canonn Research Group and BioInsights datasets.

All code, strings, and comments in this module are strictly English ASCII.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

from app.parser.exobiology_rules import EXOBIOLOGY_RULES, GENUS_DEFAULTS

# Load external Canonn Research JSON rules dynamically (SSOT)
CANONN_RULES_FILE = Path(__file__).resolve().parents[1] / "data" / "canonn_rules.json"

def get_effective_exobiology_rules() -> Dict[str, Any]:
    """
    Dynamically loads and returns the effective Exobiology rules.
    Prioritizes external canonn_rules.json if present, merged over static fallback rules.
    """
    rules = dict(EXOBIOLOGY_RULES)
    if CANONN_RULES_FILE.is_file():
        try:
            with CANONN_RULES_FILE.open("r", encoding="utf-8") as f:
                external_rules = json.load(f)
                if isinstance(external_rules, dict):
                    rules.update(external_rules)
        except Exception as e:
            print(f"[Exobiology] Error reading {CANONN_RULES_FILE}: {e}")
    return rules


def normalize_string(val: Optional[str]) -> str:
    """Normalize string to lowercase trimmed ASCII representation."""
    if not val:
        return ""
    return str(val).strip().lower()


def get_pressure_atm(body: Dict[str, Any]) -> float:
    """Extract and normalize surface pressure in atmospheres (atm)."""
    raw_press = body.get("surface_pressure")
    if raw_press is None:
        raw_press = body.get("SurfacePressure", 0.0)
    
    try:
        val = float(raw_press)
    except (ValueError, TypeError):
        return 0.0

    # If value is in Pascals (> 100 Pa), convert to standard atmospheres
    if val > 100.0:
        return val / 101325.0
    return max(0.0, val)


def get_temperature_k(body: Dict[str, Any]) -> float:
    """Extract surface temperature in Kelvin."""
    raw_temp = body.get("surface_temperature")
    if raw_temp is None:
        raw_temp = body.get("SurfaceTemperature", 0.0)
    try:
        return float(raw_temp)
    except (ValueError, TypeError):
        return 0.0


def get_gravity_g(body: Dict[str, Any]) -> float:
    """Extract surface gravity in standard Earth gravities (G)."""
    raw_g = body.get("surface_gravity_g")
    if raw_g is None:
        raw_g = body.get("surface_gravity")
    if raw_g is None:
        raw_g = body.get("SurfaceGravity", 0.0)
    
    try:
        val = float(raw_g)
    except (ValueError, TypeError):
        return 0.0

    # If value is in m/s^2 (> 1.5 and not standard G range for small bodies), check conversion
    if "surface_gravity_g" not in body and val > 1.5 and val < 50.0:
        # Check if raw gravity was stored in m/s2
        if body.get("surface_gravity") == val and not body.get("surface_gravity_g"):
            return val / 9.80665
    return max(0.0, val)


def get_atmosphere_string(body: Dict[str, Any]) -> str:
    """Extract atmosphere description or type."""
    atm = body.get("atmosphere") or body.get("Atmosphere") or body.get("AtmosphereType") or ""
    return normalize_string(atm)


def get_planet_class_string(body: Dict[str, Any]) -> str:
    """Extract normalized planet class string."""
    p_class = body.get("planet_class") or body.get("PlanetClass") or body.get("body_type") or ""
    return normalize_string(p_class)


def get_volcanism_string(body: Dict[str, Any]) -> str:
    """Extract normalized volcanism string."""
    volc = body.get("volcanism") or body.get("Volcanism") or ""
    return normalize_string(volc)


def get_star_type_string(body: Dict[str, Any]) -> str:
    """Extract primary parent star spectral type class."""
    st = body.get("star_type") or body.get("StarType") or ""
    return str(st).strip().upper()


def match_atmosphere(required_types: List[str], current_atm: str) -> bool:
    """Check if current body atmosphere satisfies required types."""
    if not required_types:
        return True
    
    norm_current = normalize_string(current_atm)
    if not norm_current or norm_current in ["none", "no atmosphere"]:
        return any(t in ["none", "no atmosphere"] for t in required_types)

    for req in required_types:
        norm_req = normalize_string(req)
        if norm_req in norm_current or norm_current in norm_req:
            return True
    return False


def match_planet_class(required_classes: List[str], current_class: str) -> bool:
    """Check if current body planet class matches allowed types."""
    if not required_classes:
        return True
    
    norm_current = normalize_string(current_class)
    for req in required_classes:
        norm_req = normalize_string(req)
        if norm_req in norm_current or norm_current in norm_req:
            return True
    return False


def calculate_environment_fit_score(rule: Dict[str, Any], temp_k: float, press_atm: float, grav_g: float) -> float:
    """
    Calculate physical fit score from 0.0 to 1.0 based on how centrally
    the body falls within optimal environmental ranges.
    """
    score = 1.0
    
    # Temperature fit
    t_min = rule.get("temp_min", 0.0)
    t_max = rule.get("temp_max", 1000.0)
    if t_max > t_min:
        t_center = (t_min + t_max) / 2.0
        t_radius = (t_max - t_min) / 2.0
        dist = abs(temp_k - t_center) / t_radius
        score -= min(0.35, 0.35 * dist)

    # Pressure fit
    p_min = rule.get("press_min", 0.0)
    p_max = rule.get("press_max", 1.0)
    if p_max > p_min:
        p_center = (p_min + p_max) / 2.0
        p_radius = (p_max - p_min) / 2.0
        dist = abs(press_atm - p_center) / p_radius
        score -= min(0.35, 0.35 * dist)

    # Gravity fit
    g_min = rule.get("grav_min", 0.0)
    g_max = rule.get("grav_max", 5.0)
    if g_max > g_min:
        g_center = (g_min + g_max) / 2.0
        g_radius = (g_max - g_min) / 2.0
        dist = abs(grav_g - g_center) / g_radius
        score -= min(0.30, 0.30 * dist)

    return max(0.1, score)


def determine_variant_color(rule: Dict[str, Any], star_type: str) -> str:
    """Determine color variant name based on star type mapping."""
    color_map = rule.get("star_color_map", {})
    if not color_map:
        return ""
    
    clean_star = star_type.split()[0] if star_type else "G"
    if clean_star in color_map:
        return color_map[clean_star]
    
    # Prefix match (e.g. M1 -> M)
    for k, v in color_map.items():
        if clean_star.startswith(k):
            return v
            
    # Default fallback
    return color_map.get("G") or color_map.get("M") or next(iter(color_map.values()), "")


def predict_exobiology_candidates(body: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Predict possible Exobiology candidate species for a body using
    strict physical parameter matrix filtering and confidence budget ranking.
    """
    is_landable = body.get("landable") or body.get("Landable")
    if is_landable is False:
        return []

    # Extract physical attributes
    p_class = get_planet_class_string(body)
    atm_type = get_atmosphere_string(body)
    temp_k = get_temperature_k(body)
    press_atm = get_pressure_atm(body)
    grav_g = get_gravity_g(body)
    volcanism = get_volcanism_string(body)
    star_type = get_star_type_string(body)
    bio_signals = body.get("bio_signals") or body.get("BioSignals") or 0

    # Gas giant exclusion
    if "gas giant" in p_class or "stars" in p_class:
        return []

    # Rule evaluation from dynamic SSOT ruleset
    candidates: List[Dict[str, Any]] = []
    active_rules = get_effective_exobiology_rules()

    for species_name, rule in active_rules.items():
        # 1. Planet class check
        if not match_planet_class(rule.get("body_types", []), p_class):
            continue

        # 2. Atmosphere type check
        if not match_atmosphere(rule.get("atmosphere_types", []), atm_type):
            continue

        # 3. Surface temperature check
        t_min = rule.get("temp_min")
        t_max = rule.get("temp_max")
        if t_min is not None and temp_k < t_min:
            continue
        if t_max is not None and temp_k > t_max:
            continue

        # 4. Surface pressure check
        p_min = rule.get("press_min")
        p_max = rule.get("press_max")
        if p_min is not None and press_atm < p_min:
            continue
        if p_max is not None and press_atm > p_max:
            continue

        # 5. Gravity check
        g_min = rule.get("grav_min")
        g_max = rule.get("grav_max")
        if g_min is not None and grav_g < g_min:
            continue
        if g_max is not None and grav_g > g_max:
            continue

        # 6. Volcanism requirement check
        volc_req = rule.get("volcanism_required")
        if volc_req:
            if not volcanism or volcanism in ["none", "no volcanism"]:
                continue

        # Calculate fit score
        fit_score = calculate_environment_fit_score(rule, temp_k, press_atm, grav_g)
        variant_color = determine_variant_color(rule, star_type)
        base_val = rule.get("base_value", 1000000)
        genus_name = rule.get("genus", species_name.split()[0])
        colony_dist = rule.get("colony_distance_m", 500)

        species_display = species_name
        variant_full = f"{species_name} - {variant_color}" if variant_color else species_name

        candidates.append({
            "species": species_name,
            "genus": genus_name,
            "species_variant": variant_full,
            "variant_color": variant_color,
            "base_value": base_val,
            "first_discovery_value": base_val * 5,
            "colony_distance_m": colony_dist,
            "fit_score": fit_score,
            "confidence": "possible"
        })

    # Sort candidates by fit score descending, then base value descending
    candidates.sort(key=lambda x: (x["fit_score"], x["base_value"]), reverse=True)

    # Signal Budget and Genus Diversity Ranking Logic
    if bio_signals > 0:
        definite_list: List[Dict[str, Any]] = []
        genus_selected = set()

        # Pass 1: Select top candidate per distinct genus up to bio_signals count
        for c in candidates:
            if len(definite_list) >= bio_signals:
                break
            if c["genus"] not in genus_selected:
                genus_selected.add(c["genus"])
                c["confidence"] = "definite"
                definite_list.append(c)

        # Pass 2: If budget remains, select remaining highest scoring candidates
        if len(definite_list) < bio_signals:
            for c in candidates:
                if len(definite_list) >= bio_signals:
                    break
                if c not in definite_list:
                    c["confidence"] = "definite"
                    definite_list.append(c)

        # Mark remaining candidates as low_probability or possible
        for c in candidates:
            if c not in definite_list:
                c["confidence"] = "low_probability"

    return candidates


def get_species_value(species_name: str, genus_name: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve base value, first discovery value, and colony distance for a species or genus."""
    if not species_name:
        species_name = ""

    # Clean input name
    clean_name = species_name.replace("$Codex_Ent_", "").replace("_Name;", "").replace(";", "")
    clean_name = clean_name.replace("_", " ").strip()

    # Exact match in active dynamic rules (SSOT)
    active_rules = get_effective_exobiology_rules()
    for k, v in active_rules.items():
        if k.lower() == clean_name.lower() or k.lower() in clean_name.lower():
            base = v.get("base_value", 1000000)
            return {
                "base_value": base,
                "first_discovery_value": base * 5,
                "colony_distance_m": v.get("colony_distance_m", 500),
                "genus": v.get("genus", "")
            }

    # Genus fallback
    gen = genus_name or (clean_name.split()[0] if clean_name else "")
    if gen in GENUS_DEFAULTS:
        g_info = GENUS_DEFAULTS[gen]
        base = g_info.get("base_value", 1000000)
        return {
            "base_value": base,
            "first_discovery_value": base * 5,
            "colony_distance_m": g_info.get("colony_distance_m", 500),
            "genus": gen
        }

    # Default fallback
    return {
        "base_value": 1000000,
        "first_discovery_value": 5000000,
        "colony_distance_m": 500,
        "genus": gen
    }


# Backwards compatibility condition table mapping
EXOBIOLOGY_SPECIES_CONDITIONS = EXOBIOLOGY_RULES
