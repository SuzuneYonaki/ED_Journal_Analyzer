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
from app.parser.bioscan.adapters import build_body_context, build_system_context
from app.parser.bioscan.genus import data as BIOSCAN_GENUS
from app.parser.bioscan.matcher import SystemContext, match_body, match_genus
from app.parser.bioscan.species import rules as BIOSCAN_SPECIES
from app.utils.galactic_regions import get_region_from_coords

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


def rank_candidates_conservatively(cands: List[Dict[str, Any]], diff_threshold: float = 0.10) -> List[Dict[str, Any]]:
    """
    Rank candidate species or genera conservatively.
    When candidate fit scores are within diff_threshold (< 10%),
    the candidate with the lower base_value is prioritized to avoid overestimating payouts.
    """
    if not cands:
        return []
    pool = list(cands)
    ranked: List[Dict[str, Any]] = []
    while pool:
        max_score = max(c.get("fit_score", 0.0) for c in pool)
        # Candidates within threshold of the best remaining score
        competitive = [c for c in pool if (max_score - c.get("fit_score", 0.0)) < diff_threshold]
        # Pick the one with the lowest base_value (tie-breaker: higher fit_score, then species name)
        competitive.sort(key=lambda c: (
            c.get("base_value", 0),
            -c.get("fit_score", 0.0),
            c.get("species", "") or c.get("genus", "")
        ))
        chosen = competitive[0]
        ranked.append(chosen)
        pool.remove(chosen)
    return ranked


def _genus_token(text: str) -> str:
    return re.sub(r"^\$codex_ent_|(_genus)?_name;?$", "", str(text).strip().lower())


# Genus lookups: display name ("Stratum") and Codex key stems ("stratum", "aleoids", "brancae") -> display name.
# A genus can have several catalog keys (Stratum has two), so everything is grouped by display name.
_GENUS_NAME_BY_TOKEN: Dict[str, str] = {}
_GENUS_KEYS_BY_NAME: Dict[str, List[str]] = {}
for _key, _data in BIOSCAN_GENUS.items():
    _GENUS_NAME_BY_TOKEN[_genus_token(_key)] = _data["name"]
    _GENUS_NAME_BY_TOKEN[_data["name"].lower()] = _data["name"]
    _GENUS_KEYS_BY_NAME.setdefault(_data["name"], []).append(_key)

# Species lookup by in-game name -> (genus key, species key, value, genus display name, colony distance)
_SPECIES_BY_NAME: Dict[str, Tuple[str, str, int, str, int]] = {
    _d["name"].lower(): (_g, _k, _d["value"], BIOSCAN_GENUS[_g]["name"], BIOSCAN_GENUS[_g]["distance"])
    for _g, _sp in BIOSCAN_SPECIES.items()
    for _k, _d in _sp.items()
}


def _body_system_context(
    body: Dict[str, Any],
    star_pos: Optional[Any],
    region_id: Optional[int],
    system_context: Optional[SystemContext],
) -> SystemContext:
    """The caller's full system context when given; otherwise one inferred from the body dict alone."""
    if system_context is None:
        system_context = build_system_context(
            [],
            system_name=body.get("star_system") or body.get("StarSystem") or "",
            star_pos=star_pos,
            region_id=region_id,
            fallback_star_type=get_star_type_string(body),
        )
        if body.get("planet_class") or body.get("PlanetClass"):
            from app.parser.bioscan.adapters import normalize_planet_class
            system_context.planet_types.append(
                normalize_planet_class(body.get("planet_class") or body.get("PlanetClass"))
            )
    if region_id is not None:
        system_context.region_id = region_id
    elif system_context.region_id is None and system_context.has_coordinates:
        system_context.region_id = get_region_from_coords(system_context.x, system_context.y, system_context.z)[0]
    return system_context


def _confirmed_genus_names(confirmed_genuses: Any) -> Set[str]:
    if not confirmed_genuses:
        return set()
    if isinstance(confirmed_genuses, str):
        try:
            confirmed_genuses = json.loads(confirmed_genuses)
        except Exception:
            confirmed_genuses = [confirmed_genuses]
    if not isinstance(confirmed_genuses, list):
        return set()
    names: Set[str] = set()
    for name in confirmed_genuses:
        display = _GENUS_NAME_BY_TOKEN.get(_genus_token(name))
        if display:
            names.add(display)
    return names


def _genus_candidate(
    genus_name: str, remaining: List[Tuple[str, str, List[str]]], genus_certain: bool
) -> Dict[str, Any]:
    """One candidate entry for a genus: the cheapest remaining species stands in, the rest are alternates.

    `remaining` lists (catalog genus key, species key, colours) for every species still possible."""
    ordered = sorted(
        remaining,
        key=lambda e: (BIOSCAN_SPECIES[e[0]][e[1]]["value"], BIOSCAN_SPECIES[e[0]][e[1]]["name"]),
    )
    first_key, first_species, colors = ordered[0]
    first = BIOSCAN_SPECIES[first_key][first_species]
    name = first["name"]
    value = first["value"]
    count = len(ordered)
    single_color = colors[0] if len(colors) == 1 else ""
    pct = round(100 / count)
    return {
        "species": name,
        "genus": genus_name,
        "species_variant": f"{name} - {single_color}" if single_color else name,
        "variant_color": single_color,
        "alternate_variants": colors if len(colors) > 1 else [],
        "base_value": value,
        "first_discovery_value": value * 5,
        "min_value": value,
        "max_value": BIOSCAN_SPECIES[ordered[-1][0]][ordered[-1][1]]["value"],
        "colony_distance_m": BIOSCAN_GENUS[first_key]["distance"],
        "fit_score": 1.0 / count,
        "match_percentage": pct,
        "possible_pct": pct,
        "is_system_coherent": False,
        "species_in_genus": count,
        "alternate_species": [BIOSCAN_SPECIES[e[0]][e[1]]["name"] for e in ordered[1:3]],
        "candidate_species": [BIOSCAN_SPECIES[e[0]][e[1]]["name"] for e in ordered],
        "genus_confirmed": genus_certain,
        "confidence": "definite" if (genus_certain and count == 1) else "possible",
    }


def predict_exobiology_candidates(
    planet_class: Any = None,
    atmosphere_type: Optional[str] = None,
    surface_temp: Optional[float] = None,
    gravity: Optional[float] = None,
    star_type: Optional[str] = None,
    star_pos: Optional[Any] = None,
    region_id: Optional[int] = None,
    system_context_species: Optional[Set[str]] = None,
    confirmed_genuses: Optional[Any] = None,
    system_context: Optional[SystemContext] = None,
    **kwargs: Any
) -> List[Dict[str, Any]]:
    """
    Candidate genera/species for a body, using the species rules ported from EDMC-BioScan
    (physical conditions, parent/other stars, Galactic Region, nebulae, Guardian sites, colours).

    Every species whose rules hold stays a candidate; nothing is ranked by guesswork. One entry per genus
    is returned (the cheapest remaining species stands in, with the others listed as alternates):

    - confidence "definite": the genus is certainly present (confirmed by DSS, or every possible genus is
      needed to account for the body's bio signals) and only one species remains.
    - confidence "possible": anything else.

    Supports both a body dict and discrete parameters
    (planet_class, atmosphere_type, surface_temp, gravity, star_type, star_pos=..., region_id=...).
    `system_context` carries the stars/bodies of the whole system; without it the system is inferred from the body.
    """
    if isinstance(planet_class, dict):
        body = dict(planet_class)
        if star_pos is None:
            star_pos = body.get("star_pos")
            if star_pos is None and ("star_pos_x" in body or "star_x" in body):
                sx = body.get("star_pos_x") if body.get("star_pos_x") is not None else body.get("star_x")
                sy = body.get("star_pos_y") if body.get("star_pos_y") is not None else body.get("star_y")
                sz = body.get("star_pos_z") if body.get("star_pos_z") is not None else body.get("star_z")
                if sx is not None and sy is not None and sz is not None:
                    star_pos = (sx, sy, sz)
        if region_id is None:
            region_id = body.get("region_id")
    else:
        p_cls = planet_class or kwargs.get("planet_class") or ""
        atm = atmosphere_type or kwargs.get("atmosphere") or kwargs.get("atmosphere_type") or ""
        press = kwargs.get("surface_pressure") or kwargs.get("pressure")
        if press is None and atm and str(atm).strip().lower() not in ["none", "no atmosphere", ""]:
            press = 0.02 * 101325  # default thin atmosphere pressure (~0.02 atm) for discrete calls
        grav = gravity if gravity is not None else kwargs.get("gravity")
        temp = surface_temp if surface_temp is not None else kwargs.get("surface_temp") or kwargs.get("surface_temperature")
        body = {
            "planet_class": p_cls,
            "atmosphere": atm,
            "surface_temperature": temp,
            "surface_gravity_g": grav,
            "surface_pressure": press,
            "star_type": star_type or kwargs.get("star_type") or "",
            "landable": True,
            "volcanism": kwargs.get("volcanism"),
            "star_pos": star_pos,
            "region_id": region_id,
        }

    if body.get("landable") is False or body.get("Landable") is False:
        return []

    bio_signals = body.get("bio_signals")
    if bio_signals is None:
        bio_signals = body.get("BioSignals")
    is_mapped = bool(body.get("is_mapped_by_user") or body.get("was_mapped"))
    # If bio_signals is explicitly 0, or the body was mapped and showed none, no life exists
    if bio_signals is not None and int(bio_signals) == 0:
        return []
    if is_mapped and (bio_signals is None or int(bio_signals) == 0):
        return []

    p_class = get_planet_class_string(body)
    if "gas giant" in p_class or "stars" in p_class:
        return []

    system = _body_system_context(body, star_pos, region_id, system_context)
    body_ctx = build_body_context(body, system)
    matches = match_body(body_ctx, system)

    # Group the catalog keys by genus: {genus name: [(catalog key, species key, colours), ...]}
    by_genus: Dict[str, List[Tuple[str, str, List[str]]]] = {}
    for genus_key, species_colors in matches.items():
        for species_key, colors in species_colors.items():
            by_genus.setdefault(BIOSCAN_GENUS[genus_key]["name"], []).append((genus_key, species_key, colors))

    confirmed = _confirmed_genus_names(confirmed_genuses or body.get("confirmed_genuses"))
    if confirmed:
        relaxed_system = SystemContext(name=system.name, stars=system.stars, planet_types=system.planet_types,
                                       main_star_name=system.main_star_name, main_star_type=system.main_star_type,
                                       main_star_luminosity=system.main_star_luminosity)
        kept: Dict[str, List[Tuple[str, str, List[str]]]] = {}
        for genus_name in confirmed:
            remaining = by_genus.get(genus_name)
            if not remaining:
                # DSS says the genus is here: if the rules rule it out, fall back to the physical conditions only
                remaining = [
                    (key, species_key, colors)
                    for key in _GENUS_KEYS_BY_NAME[genus_name]
                    for species_key, colors in match_genus(key, body_ctx, relaxed_system).items()
                ]
            if remaining:
                kept[genus_name] = remaining
        by_genus = kept

    if not by_genus:
        return []

    signals = int(bio_signals) if bio_signals is not None else None
    all_needed = signals is not None and len(by_genus) <= signals
    candidates = [
        _genus_candidate(genus_name, remaining, genus_certain=(genus_name in confirmed) or all_needed)
        for genus_name, remaining in by_genus.items()
    ]
    # Definite first; then the cheapest first, so that summing the first N entries never overstates payouts
    candidates.sort(key=lambda c: (c["confidence"] != "definite", c["base_value"], c["species"]))
    if signals is None:
        candidates = candidates[:3]
    return candidates


def predict_system_exobiology_candidates(
    bodies: List[Dict[str, Any]],
    system_info: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Predict candidates for every body of a system, sharing one system context (stars, planet classes, position)."""
    if not bodies:
        return []

    system_star_pos = None
    system_region_id = None
    system_name = ""
    if system_info:
        system_name = system_info.get("star_system") or system_info.get("system_name") or ""
        system_star_pos = system_info.get("star_pos")
        if system_star_pos is None and ("star_pos_x" in system_info or "star_x" in system_info):
            sx = system_info.get("star_pos_x") if system_info.get("star_pos_x") is not None else system_info.get("star_x")
            sy = system_info.get("star_pos_y") if system_info.get("star_pos_y") is not None else system_info.get("star_y")
            sz = system_info.get("star_pos_z") if system_info.get("star_pos_z") is not None else system_info.get("star_z")
            if sx is not None and sy is not None and sz is not None:
                system_star_pos = (sx, sy, sz)
        system_region_id = system_info.get("region_id")

    first = bodies[0]
    context = build_system_context(
        bodies,
        system_name=system_name or first.get("star_system") or "",
        star_pos=system_star_pos or first.get("star_pos"),
        region_id=system_region_id,
        fallback_star_type=get_star_type_string(first),
    )
    for b in bodies:
        b["exobiology"] = predict_exobiology_candidates(b, system_context=context)
    return bodies


def get_species_value(species_name: str, genus_name: Optional[str] = None) -> Dict[str, Any]:
    """Base value, first discovery value and colony distance for a species (in-game name) or its genus."""
    clean_name = (species_name or "").replace("$Codex_Ent_", "").replace("_Name;", "").replace(";", "")
    clean_name = clean_name.replace("_", " ").strip()
    lowered = clean_name.lower()

    # In-game species name, optionally followed by " - <colour>"
    exact = _SPECIES_BY_NAME.get(lowered.split(" - ")[0].strip())
    if exact:
        _, _, value, genus, distance = exact
        return {"base_value": value, "first_discovery_value": value * 5, "colony_distance_m": distance, "genus": genus}

    # Older rule table (names that predate the ported data)
    for k, v in get_effective_exobiology_rules().items():
        if k.lower() == lowered or k.lower() in lowered:
            base = v.get("base_value", 1000000)
            return {
                "base_value": base,
                "first_discovery_value": base * 5,
                "colony_distance_m": v.get("colony_distance_m", 500),
                "genus": v.get("genus", ""),
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
            "genus": gen,
        }

    return {"base_value": 1000000, "first_discovery_value": 5000000, "colony_distance_m": 500, "genus": gen}


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

