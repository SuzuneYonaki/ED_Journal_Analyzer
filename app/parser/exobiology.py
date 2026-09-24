"""
Exobiology Candidate Prediction Engine for Elite Dangerous.
Implements multi-parameter physical matrix filtering, signal budget allocation,
and confidence ranking based on Canonn Research Group and BioInsights datasets.

All code, strings, and comments in this module are strictly English ASCII.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set

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

    if val <= 0.0:
        return 0.0

    # In Elite Dangerous journals and DB, SurfacePressure is stored in Pascals (Pa).
    # 1 atm = 101325 Pa. Odyssey landable planet atmospheres range from ~1 Pa to ~15,000 Pa (~0.15 atm).
    # If val > 1.0, it is in Pascals.
    # If body explicitly used journal key 'SurfacePressure', it is always in Pascals.
    if val > 1.0 or "SurfacePressure" in body:
        return val / 101325.0

    # If val <= 1.0 and passed as surface_pressure (e.g. test fixtures in atm), treat as atm.
    return val


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
    st = body.get("star_type") or body.get("StarType")
    if st:
        return str(st).strip().upper()
    # For planets, star_type is not directly on the planet itself. Resolve from parent_star_type,
    # system_main_star_type, or main_star_type
    st = (
        body.get("parent_star_type")
        or body.get("ParentStarType")
        or body.get("system_main_star_type")
        or body.get("main_star_type")
        or body.get("MainStarType")
        or ""
    )
    return str(st).strip().upper()


def match_atmosphere(required_types: List[str], current_atm: str) -> bool:
    """Check if current body atmosphere satisfies required types, strictly distinguishing plain and -rich atmospheres."""
    if not required_types:
        return True
    
    norm_current = normalize_string(current_atm)
    if not norm_current or norm_current in ["none", "no atmosphere"]:
        return any(t in ["none", "no atmosphere"] for t in required_types)

    is_current_rich = ("-rich" in norm_current) or (" rich" in norm_current)

    for req in required_types:
        norm_req = normalize_string(req)
        is_req_rich = ("-rich" in norm_req) or (" rich" in norm_req)

        # Disallow plain atmosphere from matching rich requirement, and vice versa
        if is_req_rich != is_current_rich:
            continue

        # Strip prefixes and suffixes to match base gas name
        clean_req = re.sub(r"-?rich|atmosphere|thin|hot|thick", "", norm_req).strip()
        clean_current = re.sub(r"-?rich|atmosphere|thin|hot|thick", "", norm_current).strip()

        if clean_req and clean_current:
            if clean_req in clean_current or clean_current in clean_req:
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
    g_min = rule.get("grav_min")
    g_max = rule.get("grav_max")
    if g_min is not None and g_max is not None and g_max > g_min:
        g_center = (g_min + g_max) / 2.0
        g_radius = (g_max - g_min) / 2.0
        dist = abs(grav_g - g_center) / g_radius
        score -= min(0.30, 0.30 * dist)

    return max(0.1, score)


def determine_variant_info(rule: Dict[str, Any], star_type: str, fit_score: float) -> Tuple[str, List[str]]:
    """
    Determine primary color variant based on star type, and collect
    all threshold-passing alternate color variants from Canonn star color mapping.
    """
    color_map = rule.get("star_color_map", {})
    if not color_map:
        return "", []

    clean_star = star_type.split()[0] if star_type else "G"
    primary_color = ""

    if clean_star in color_map:
        primary_color = color_map[clean_star]
    else:
        for k, v in color_map.items():
            if clean_star.startswith(k):
                primary_color = v
                break
        if not primary_color:
            primary_color = color_map.get("G") or color_map.get("M") or next(iter(color_map.values()), "")

    # Collect alternate color variants if fit_score exceeds acceptable threshold
    alt_colors = []
    if fit_score >= 0.50:
        for st, col in color_map.items():
            if col and col != primary_color and col not in alt_colors:
                alt_colors.append(col)

    return primary_color, alt_colors


def match_parent_star(rule: Dict[str, Any], star_type: str, luminosity: Optional[str] = None) -> bool:
    """Check if primary/parent star satisfies star type and luminosity class restrictions."""
    allowed_types = rule.get("parent_star_types")
    if not allowed_types:
        return True

    clean_star = star_type.split()[0].upper() if star_type else ""
    if not clean_star:
        return True

    # Check star type match (exact or prefix match, e.g. DA -> D or DAB -> DA)
    type_matched = False
    for req_type in allowed_types:
        req_u = req_type.upper()
        if clean_star == req_u or clean_star.startswith(req_u) or req_u.startswith(clean_star):
            type_matched = True
            break

    if not type_matched:
        return False

    # Check luminosity restrictions if specified
    lum_rules = rule.get("parent_star_luminosities")
    if lum_rules and isinstance(lum_rules, dict) and luminosity:
        clean_lum = luminosity.strip().upper()
        for s_type, valid_lums in lum_rules.items():
            if clean_star.startswith(s_type.upper()):
                if clean_lum not in [v.upper() for v in valid_lums]:
                    return False

    return True


def predict_exobiology_candidates(
    body: Dict[str, Any],
    system_context_species: Optional[Set[str]] = None,
    confirmed_genuses: Optional[Any] = None
) -> List[Dict[str, Any]]:
    """
    Predict possible Exobiology candidate species for a body using
    strict physical parameter matrix filtering, distinct Species signal budgeting (Z signals -> Z species),
    confirmed genus pruning from DSS, and system-level co-occurrence weighting under the same stellar spectrum.
    """
    is_landable = body.get("landable") or body.get("Landable")
    if is_landable is False:
        return []

    # Extract biological signals and mapping status
    bio_signals = body.get("bio_signals")
    if bio_signals is None:
        bio_signals = body.get("BioSignals")
    
    is_mapped = bool(body.get("is_mapped_by_user") or body.get("was_mapped"))

    # BioInsights rule: if bio_signals is explicitly 0, or if mapped with 0 signals, NO life exists!
    if bio_signals is not None and int(bio_signals) == 0:
        return []
    if is_mapped and (bio_signals is None or int(bio_signals) == 0):
        return []

    # Extract physical attributes
    p_class = get_planet_class_string(body)
    atm_type = get_atmosphere_string(body)
    temp_k = get_temperature_k(body)
    press_atm = get_pressure_atm(body)
    grav_g = get_gravity_g(body)
    volcanism = get_volcanism_string(body)
    star_type = get_star_type_string(body)
    luminosity = body.get("luminosity") or body.get("Luminosity")

    # Gas giant and star exclusion
    if "gas giant" in p_class or "stars" in p_class:
        return []

    # Parse confirmed genuses if present (e.g. from SAASignalsFound)
    conf_genuses_raw = confirmed_genuses or body.get("confirmed_genuses")
    confirmed_genus_set: Set[str] = set()
    if conf_genuses_raw:
        if isinstance(conf_genuses_raw, str):
            try:
                conf_genuses_raw = json.loads(conf_genuses_raw)
            except Exception:
                conf_genuses_raw = [conf_genuses_raw]
        if isinstance(conf_genuses_raw, list):
            for cg in conf_genuses_raw:
                clean_cg = re.sub(r"^\$Codex_Ent_|_Genus_Name;?$", "", str(cg), flags=re.IGNORECASE).strip()
                if clean_cg:
                    confirmed_genus_set.add(clean_cg.lower())

    # Rule evaluation from dynamic SSOT ruleset
    candidates: List[Dict[str, Any]] = []
    active_rules = get_effective_exobiology_rules()

    for species_name, rule in active_rules.items():
        genus_name = rule.get("genus", species_name.split()[0])
        
        # If DSS confirmed specific genuses, prune any candidate not in that set
        if confirmed_genus_set and genus_name.lower() not in confirmed_genus_set:
            continue

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

        # 5. Gravity check (considering Any Gravity and Low Gravity g < 0.27)
        any_grav = rule.get("any_gravity", False)
        g_min = rule.get("grav_min")
        g_max = rule.get("grav_max")
        if g_min is not None and grav_g < g_min:
            continue
        if not any_grav and g_max is not None and grav_g > g_max:
            continue

        # 6. Volcanism requirement check
        volc_req = rule.get("volcanism_required")
        if volc_req:
            if not volcanism or volcanism in ["none", "no volcanism"]:
                continue

        # 7. Parent star type & luminosity check (e.g. Electricae)
        if not match_parent_star(rule, star_type, luminosity):
            continue

        # Calculate base fit score
        fit_score = calculate_environment_fit_score(rule, temp_k, press_atm, grav_g)

        # Apply System-level Co-occurrence & Consistency Weighting
        is_coherent = False
        if system_context_species and species_name in system_context_species:
            fit_score = min(1.0, fit_score + 0.15)
            is_coherent = True

        match_pct = round(fit_score * 100)
        primary_color, alt_colors = determine_variant_info(rule, star_type, fit_score)
        base_val = rule.get("base_value", 1000000)
        colony_dist = rule.get("colony_distance_m", 500)

        variant_display = f"{species_name} - {primary_color}" if primary_color else species_name

        candidates.append({
            "species": species_name,
            "genus": genus_name,
            "species_variant": variant_display,
            "variant_color": primary_color,
            "alternate_variants": alt_colors,
            "base_value": base_val,
            "first_discovery_value": base_val * 5,
            "colony_distance_m": colony_dist,
            "fit_score": fit_score,
            "match_percentage": match_pct,
            "possible_pct": match_pct,
            "is_system_coherent": is_coherent,
            "confidence": "possible"
        })

    # Sort candidates by fit score descending, then base value descending
    candidates.sort(key=lambda x: (x["fit_score"], x["base_value"]), reverse=True)

    # Signal Budget Ranking & 1 Species per Genus Law
    if bio_signals is not None and int(bio_signals) > 0:
        z_budget = int(bio_signals)
        
        # Group candidates by Genus
        # Elite Dangerous Odyssey Physical Law: Only 1 species of a given genus can exist per planet.
        genus_groups: Dict[str, List[Dict[str, Any]]] = {}
        for c in candidates:
            g = c["genus"]
            if g not in genus_groups:
                genus_groups[g] = []
            genus_groups[g].append(c)

        # For each distinct genus, pick the best candidate (highest fit_score, then base_value)
        distinct_genus_candidates: List[Dict[str, Any]] = []
        for g, sp_list in genus_groups.items():
            sp_list.sort(key=lambda x: (x["fit_score"], x["base_value"]), reverse=True)
            best_sp = sp_list[0]
            if len(sp_list) > 1:
                best_sp["alternate_species"] = [s["species"] for s in sp_list[1:3]]
            distinct_genus_candidates.append(best_sp)

        # Sort distinct genus candidates by fit score descending
        distinct_genus_candidates.sort(key=lambda x: (x["fit_score"], x["base_value"]), reverse=True)

        if not distinct_genus_candidates:
            return []

        # Split into definite (up to Z) and runner-up (+1)
        definite_list = distinct_genus_candidates[:z_budget]
        for d in definite_list:
            d["confidence"] = "definite"

        result_candidates = list(definite_list)

        # Include qualifying runner-up (+1) if within 10% score threshold
        definite_species_names = {d["species"] for d in definite_list}
        remaining_candidates = [c for c in candidates if c["species"] not in definite_species_names]
        if remaining_candidates:
            runner_up = remaining_candidates[0]
            min_definite_score = min(d["fit_score"] for d in definite_list) if definite_list else 1.0
            score_diff = min_definite_score - runner_up["fit_score"]

            if score_diff < 0.10:
                runner_up["confidence"] = "possible"
                result_candidates.append(runner_up)

        return result_candidates
    else:
        # bio_signals is None and body is not mapped
        # Return top distinct genera as unconfirmed/possible candidates
        genus_seen = set()
        distinct_matches = []
        for c in candidates:
            if c["genus"] not in genus_seen:
                genus_seen.add(c["genus"])
                c["confidence"] = "possible"
                distinct_matches.append(c)
            if len(distinct_matches) >= 3:
                break
        return distinct_matches


def predict_system_exobiology_candidates(
    bodies: List[Dict[str, Any]],
    system_info: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Predict exobiology candidates across all bodies in a system simultaneously,
    applying cross-body co-occurrence & consistency weighting under the same stellar spectrum.
    """
    if not bodies:
        return []

    # Step 1: Preliminary pass to gather prominent / scanned species across the system
    system_known_species: Set[str] = set()

    for b in bodies:
        # Include already scanned or organic-analyzed species
        scanned_list = b.get("scanned_species") or b.get("scanned_species_list") or []
        for s in scanned_list:
            if isinstance(s, dict) and s.get("species"):
                system_known_species.add(s["species"])
            elif isinstance(s, str):
                system_known_species.add(s)

        # Preliminary candidate evaluation for high-signal or high-confidence bodies
        bio_sig = b.get("bio_signals") or b.get("BioSignals") or 0
        if bio_sig > 0:
            prelim_cands = predict_exobiology_candidates(b, system_context_species=None)
            # Add definite high-fit species (fit_score >= 0.70) to system context
            for c in prelim_cands:
                if c.get("confidence") == "definite" and c.get("fit_score", 0) >= 0.70:
                    system_known_species.add(c["species"])

    # Step 2: Final pass applying system-level co-occurrence weighting to each body
    for b in bodies:
        b["exobiology"] = predict_exobiology_candidates(b, system_context_species=system_known_species)

    return bodies


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


def evaluate_high_value_bio(
    candidates: List[Dict[str, Any]],
    bio_signals: Optional[int] = None,
    threshold: int = 40_000_000,
    threshold_type: str = "bonus"
) -> Dict[str, Any]:
    """
    Evaluates whether predicted or scanned exobiology candidates qualify as high-value bio.

    Domain Rules:
    - Base value max is Stratum Tectonicas (19,010,800 Cr). No single species has base_value >= 40M Cr.
    - First discovery multiplier is 5x (first_discovery_value = base_value * 5). Stratum Tectonicas gives 95,054,000 Cr (~95M).
    - If threshold_type == 'bonus' (or threshold >= 20,000,000):
        The threshold compares against total estimated first discovery payout (5x bonus).
        A 40M threshold represents ~8M base value, capturing high-tier organics like Stratum Tectonicas.
    - If threshold_type == 'base':
        The threshold compares directly against total estimated base value (1x).
    """
    is_bonus_metric = (threshold_type == "bonus") or (threshold >= 20_000_000)
    if not candidates:
        return {
            "is_high_value": False,
            "total_estimated_base": 0,
            "total_estimated_bonus": 0,
            "comparison_value": 0,
            "is_bonus_metric": is_bonus_metric,
            "qualifying_species": [],
            "top_species": None
        }

    # Slice by bio_signals budget if known
    budget = int(bio_signals) if (bio_signals is not None and int(bio_signals) > 0) else len(candidates)
    definite_candidates = candidates[:budget]

    total_base = 0
    total_bonus = 0

    for cand in definite_candidates:
        base_v = cand.get("base_value") or 1_000_000
        bonus_v = cand.get("first_discovery_value") or (base_v * 5)
        total_base += base_v
        total_bonus += bonus_v

    comparison_val = total_bonus if is_bonus_metric else total_base
    is_high_value = comparison_val >= threshold

    qualifying_species = []
    if is_high_value:
        for cand in definite_candidates:
            val_to_check = cand.get("first_discovery_value", 0) if is_bonus_metric else cand.get("base_value", 0)
            if not val_to_check:
                base_v = cand.get("base_value") or 1_000_000
                val_to_check = (base_v * 5) if is_bonus_metric else base_v

            per_species_thresh = 40_000_000 if is_bonus_metric else 8_000_000
            if val_to_check >= per_species_thresh or val_to_check >= (threshold / max(1, budget)):
                sp = cand.get("species")
                if sp and sp not in qualifying_species:
                    qualifying_species.append(sp)

    top_sp = definite_candidates[0].get("species") if definite_candidates else None

    return {
        "is_high_value": is_high_value,
        "total_estimated_base": total_base,
        "total_estimated_bonus": total_bonus,
        "comparison_value": comparison_val,
        "is_bonus_metric": is_bonus_metric,
        "qualifying_species": qualifying_species,
        "top_species": top_sp
    }

