"""Builds the matcher's body/system contexts from this application's body rows and journal-style dicts."""

import json
import re
from typing import Any, Dict, Iterable, List, Optional

from app.parser.bioscan.matcher import BodyContext, StarInfo, SystemContext

_PLANET_CLASSES = {
    "high metal content body": "High metal content body",
    "high metal content world": "High metal content body",
    "metal rich body": "Metal rich body",
    "rocky ice body": "Rocky ice body",
    "rocky ice world": "Rocky ice body",
    "rocky body": "Rocky body",
    "icy body": "Icy body",
    "earthlike body": "Earthlike body",
    "earth like world": "Earthlike body",
    "earthlike world": "Earthlike body",
    "water giant": "Water giant",
    "gas giant with water based life": "Gas giant with water based life",
}
_ATMOSPHERE_QUALIFIERS = re.compile(r"\b(hot|thin|thick)\b", re.IGNORECASE)


def normalize_planet_class(value: Any) -> str:
    """Journal PlanetClass form ("High metal content body") from journal or EDSM spellings."""
    text = str(value or "").strip()
    key = re.sub(r"\s+", " ", text.replace("-", " ").lower())
    return _PLANET_CLASSES.get(key, text)


def normalize_atmosphere(value: Any) -> str:
    """Journal AtmosphereType form ("CarbonDioxide", "NeonRich", "None") from journal or EDSM spellings."""
    text = str(value or "").strip()
    if not text or text.lower() in ("none", "no atmosphere"):
        return "None"
    if " " not in text and "-" not in text:
        return text
    cleaned = _ATMOSPHERE_QUALIFIERS.sub(" ", text)
    tokens = [t for t in re.split(r"[\s\-]+", cleaned) if t]
    return "".join(t[:1].upper() + t[1:] for t in tokens) or "None"


def normalize_volcanism(value: Any) -> str:
    text = str(value or "").strip().lower()
    return "" if text in ("", "none", "no volcanism") else text


def _json_list(value: Any) -> List[Any]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            return []
    return value if isinstance(value, list) else []


def _float(value: Any) -> Optional[float]:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _gravity_ms2(body: Dict[str, Any]) -> float:
    raw = _float(body.get("surface_gravity"))
    if raw is None:
        raw = _float(body.get("SurfaceGravity"))
    g = _float(body.get("surface_gravity_g"))
    if raw is not None and raw > 0:
        # Stored in m/s^2; a small value with no separate G column is taken to be in G (test fixtures)
        return raw * 9.80665 if (g is None and raw <= 1.5) else raw
    return (g or 0.0) * 9.80665


def _pressure_pa(body: Dict[str, Any]) -> Optional[float]:
    raw = _float(body.get("surface_pressure"))
    if raw is None:
        raw = _float(body.get("SurfacePressure"))
    if not raw or raw <= 0:
        return None
    # A value <= 1 only appears as atmospheres in fixtures; the journal and DB store Pascals.
    return raw * 101325.0 if (raw <= 1.0 and "SurfacePressure" not in body) else raw


def build_system_context(
    bodies: Iterable[Dict[str, Any]],
    system_name: str = "",
    star_pos: Optional[Any] = None,
    region_id: Optional[int] = None,
    fallback_star_type: str = "",
) -> SystemContext:
    """System-wide facts the rules need: stars, planet classes, position and region."""
    stars: Dict[str, StarInfo] = {}
    planet_types: List[str] = []
    for b in bodies:
        name = b.get("body_name") or b.get("BodyName") or ""
        if b.get("star_type") or b.get("StarType"):
            stars[name] = StarInfo(
                name=name,
                star_type=str(b.get("star_type") or b.get("StarType")),
                luminosity=str(b.get("luminosity") or b.get("Luminosity") or ""),
                distance=_float(b.get("distance_from_arrival_ls")),
                body_id=b.get("body_id"),
            )
        elif b.get("planet_class") or b.get("PlanetClass"):
            planet_types.append(normalize_planet_class(b.get("planet_class") or b.get("PlanetClass")))

    if not stars and fallback_star_type:
        stars[system_name or "Main star"] = StarInfo(
            name=system_name or "Main star", star_type=fallback_star_type, luminosity="", distance=0.0
        )

    main = min(stars.values(), key=lambda s: (s.distance is None, s.distance or 0.0), default=None)
    x = y = z = None
    if isinstance(star_pos, (list, tuple)) and len(star_pos) >= 3:
        x, y, z = (_float(star_pos[0]), _float(star_pos[1]), _float(star_pos[2]))

    return SystemContext(
        name=system_name,
        x=x, y=y, z=z,
        region_id=region_id,
        stars=stars,
        planet_types=planet_types,
        main_star_name=main.name if main else "",
        main_star_type=main.star_type if main else (fallback_star_type or ""),
        main_star_luminosity=main.luminosity if main else "",
    )


def build_body_context(body: Dict[str, Any], system: SystemContext) -> BodyContext:
    star_by_id = {s.body_id: s for s in system.stars.values() if s.body_id is not None}
    parent_names: List[str] = []
    for entry in _json_list(body.get("parents") or body.get("Parents")):
        if isinstance(entry, dict) and "Star" in entry and entry["Star"] in star_by_id:
            name = star_by_id[entry["Star"]].name
            if name not in parent_names:
                parent_names.append(name)
    if not parent_names and system.main_star_name:
        parent_names = [system.main_star_name]

    materials = frozenset(
        str(m.get("Name", "")).lower() for m in _json_list(body.get("materials") or body.get("Materials"))
        if isinstance(m, dict)
    )
    gases = {
        g.get("Name"): float(g.get("Percent") or 0.0)
        for g in _json_list(body.get("atmosphere_composition") or body.get("AtmosphereComposition"))
        if isinstance(g, dict) and g.get("Name")
    }
    atmosphere = body.get("atmosphere_type") or body.get("AtmosphereType") or body.get("atmosphere") or body.get("Atmosphere")

    return BodyContext(
        name=body.get("body_name") or body.get("BodyName") or "",
        body_type=normalize_planet_class(body.get("planet_class") or body.get("PlanetClass") or body.get("body_type")),
        atmosphere=normalize_atmosphere(atmosphere),
        gravity=_gravity_ms2(body),
        temperature=_float(body.get("surface_temperature") if body.get("surface_temperature") is not None else body.get("SurfaceTemperature")),
        pressure=_pressure_pa(body),
        volcanism=normalize_volcanism(body.get("volcanism") if body.get("volcanism") is not None else body.get("Volcanism")),
        orbital_period=_float(body.get("orbital_period") if body.get("orbital_period") is not None else body.get("OrbitalPeriod")),
        distance=_float(body.get("distance_from_arrival_ls") if body.get("distance_from_arrival_ls") is not None else body.get("DistanceFromArrivalLS")),
        materials=materials,
        gases=gases,
        parent_stars=parent_names,
    )


def system_context_from_db(cursor, system_address: int, region_id: Optional[int] = None) -> Optional[SystemContext]:
    """Loads a system's bodies and position through an open DB cursor (sees uncommitted parser writes)."""
    cursor.execute("SELECT star_system, star_pos_x, star_pos_y, star_pos_z, main_star_type FROM systems WHERE system_address = ?", (system_address,))
    sys_row = cursor.fetchone()
    if not sys_row:
        return None
    cursor.execute(
        "SELECT body_id, body_name, star_type, luminosity, planet_class, distance_from_arrival_ls "
        "FROM bodies WHERE system_address = ?",
        (system_address,),
    )
    rows = [dict(r) for r in cursor.fetchall()]
    star_pos = None
    if sys_row["star_pos_x"] is not None:
        star_pos = (sys_row["star_pos_x"], sys_row["star_pos_y"], sys_row["star_pos_z"])
    return build_system_context(
        rows, system_name=sys_row["star_system"] or "", star_pos=star_pos,
        region_id=region_id, fallback_star_type=sys_row["main_star_type"] or "",
    )
