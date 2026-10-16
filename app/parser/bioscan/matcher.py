# Species matcher: a re-implementation of the rule evaluation in EDMC-BioScan's value_estimate()
# (https://github.com/Silarn/EDMC-BioScan, src/load.py), Copyright (c) Jeremy Rimpo and contributors,
# licensed under the GNU General Public License, version 2 or later. Adapted to this application's
# data structures and distributed under GPL-3.0-or-later. See NOTICE.md.
"""Decides which species (and colour variants) can exist on a body, given the body, its system and its position."""

import math
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from app.parser.bioscan.genus import data as GENUS_DATA
from app.parser.bioscan.nebula_sectors import data as NEBULA_SECTORS
from app.parser.bioscan.nebula_stars import get_nearest_nebula
from app.parser.bioscan.regions import guardian_nebulae, region_map, tuber_zones
from app.parser.bioscan.species import rules as SPECIES_RULES

GRAVITY_DIVISOR = 9.797759  # m/s^2 per G, as used by the rule data
PRESSURE_DIVISOR = 101231.656250  # Pa per atm, as used by the rule data
_LUMINOSITY_FLAGS = ("", "a", "b", "ab", "z")


@dataclass
class StarInfo:
    name: str
    star_type: str
    luminosity: str = ""
    distance: Optional[float] = None
    body_id: Optional[int] = None


@dataclass
class BodyContext:
    name: str
    body_type: str  # journal PlanetClass, e.g. "High metal content body"
    atmosphere: str = ""  # journal AtmosphereType, e.g. "CarbonDioxide"; "" / "None" = no atmosphere
    gravity: float = 0.0  # m/s^2
    temperature: Optional[float] = None  # K
    pressure: Optional[float] = None  # Pa
    volcanism: str = ""  # "" = none
    orbital_period: Optional[float] = None  # s
    distance: Optional[float] = None  # ls from arrival
    materials: FrozenSet[str] = frozenset()
    gases: Dict[str, float] = field(default_factory=dict)
    parent_stars: List[str] = field(default_factory=list)  # names of parent stars


@dataclass
class SystemContext:
    name: str
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    region_id: Optional[int] = None
    stars: Dict[str, StarInfo] = field(default_factory=dict)
    planet_types: List[str] = field(default_factory=list)
    main_star_name: str = ""
    main_star_type: str = ""
    main_star_luminosity: str = ""

    @property
    def stars_known(self) -> bool:
        return bool(self.stars) or bool(self.main_star_type)

    @property
    def has_coordinates(self) -> bool:
        return None not in (self.x, self.y, self.z)

    @property
    def coordinates(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)


def system_distance(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> float:
    return math.sqrt(sum((p - q) ** 2 for p, q in zip(a, b)))


def star_check(star_query: str, star_type: str) -> bool:
    """Whether a journal star type matches a base type identifier (super giants and sub-types included)."""
    star_type = star_type or ""
    match star_query:
        case "A":
            return star_type in ("A", "A_BlueWhiteSuperGiant")
        case "B":
            return star_type in ("B", "B_BlueWhiteSuperGiant")
        case "F":
            return star_type in ("F", "F_WhiteSuperGiant")
        case "G":
            return star_type in ("G", "G_WhiteSuperGiant")
        case "K":
            return star_type in ("K", "K_OrangeGiant")
        case "M":
            return star_type in ("M", "M_RedGiant", "M_RedSuperGiant")
        case "D" | "C" | "W":
            return star_type.startswith(star_query)
        case "Ae":
            return star_type in ("Ae", "AeBe")
        case _:
            return star_type == star_query


def _luminosity_matches(wanted: str, actual: str) -> bool:
    if not actual:
        return True  # luminosity unknown: do not rule the species out
    return any(wanted + flag == actual for flag in _LUMINOSITY_FLAGS)


def _star_entry_matches(entry, star_type: str, luminosity: str) -> bool:
    if isinstance(entry, tuple):
        return star_check(entry[0], star_type) and _luminosity_matches(entry[1], luminosity)
    return star_check(entry, star_type)


def _designation(star: StarInfo, system: SystemContext) -> str:
    prefix = system.name + " "
    return star.name[len(prefix):] if star.name.startswith(prefix) else star.name


def _orbits_black_hole(star: StarInfo, body: BodyContext, system: SystemContext) -> bool:
    """A non-parent star may supply colour when the body orbits a black hole that this star also orbits."""
    holes = [system.stars[n] for n in body.parent_stars if n in system.stars and system.stars[n].star_type == "H"]
    if not holes:
        return False
    if system.main_star_type == "H":
        return True
    star_designation = _designation(star, system)
    for hole in holes:
        hole_designation = _designation(hole, system)
        if hole_designation and hole_designation in star_designation.split(" ")[0] and star.name != hole.name:
            return True
    return False


def _region_ok(value: List[str], system: SystemContext) -> bool:
    if system.region_id is None:
        return True
    for region in value:
        if region.startswith("!") and system.region_id in region_map[region[1:]]:
            return False
    included = [r for r in value if not r.startswith("!")]
    return not included or any(system.region_id in region_map[r] for r in included)


def _guardian_ok(required: bool, system: SystemContext) -> bool:
    if not required or not system.has_coordinates:
        return True
    return any(
        system_distance(system.coordinates, coordinates) < max_distance
        for max_distance, coordinates in guardian_nebulae.values()
    )


def _tuber_ok(value, system: SystemContext) -> bool:
    if not system.has_coordinates:
        return True
    for zone, ((min_distance, max_distance), coordinates) in tuber_zones.items():
        if value == "Any" or zone in value:
            if min_distance <= system_distance(system.coordinates, coordinates) <= max_distance:
                return True
    return False


def _nebula_ok(value: str, system: SystemContext) -> bool:
    if not system.has_coordinates:
        return True
    if any(system.name.startswith(sector) for sector in NEBULA_SECTORS):
        return True
    here = system.coordinates
    for coordinates in get_nearest_nebula(here).values():
        if system_distance(here, coordinates) < 150.0:
            return True
    if value == "all":
        for coordinates in get_nearest_nebula(here, "planetary").values():
            if system_distance(here, coordinates) < 100.0:
                return True
    return False


def _volcanism_ok(value, volcanism: str) -> bool:
    if isinstance(value, list):
        for volc_type in value:
            if volc_type.startswith("="):
                if volcanism == volc_type[1:]:
                    return True
            elif volc_type in volcanism:
                return True
        return False
    if value == "Any":
        return volcanism != ""
    if value == "None":
        return volcanism == ""
    if value.startswith("!"):
        return value[1:] not in volcanism and volcanism != ""
    return True


def ruleset_passes(ruleset: dict, body: BodyContext, system: SystemContext) -> bool:
    """True when every condition of one ruleset holds. Unknown inputs never eliminate a species."""
    for rule_type, value in ruleset.items():
        if rule_type == "atmosphere":
            if value == "Any":
                if body.atmosphere in ("", "None"):
                    return False
            elif body.atmosphere not in value:
                return False
        elif rule_type == "atmosphere_component":
            if any(body.gases.get(gas, 0.0) < percent for gas, percent in value.items()):
                return False
        elif rule_type == "max_gravity":
            if body.gravity / GRAVITY_DIVISOR > value:
                return False
        elif rule_type == "min_gravity":
            if body.gravity / GRAVITY_DIVISOR < value:
                return False
        elif rule_type == "max_temperature":
            if body.temperature and body.temperature > value:
                return False
        elif rule_type == "min_temperature":
            if body.temperature and body.temperature < value:
                return False
        elif rule_type == "min_pressure":
            if body.pressure and body.pressure / PRESSURE_DIVISOR < value:
                return False
        elif rule_type == "max_pressure":
            if body.pressure and body.pressure / PRESSURE_DIVISOR >= value:
                return False
        elif rule_type == "max_orbital_period":
            if body.orbital_period is not None and body.orbital_period >= value:
                return False
        elif rule_type == "volcanism":
            if not _volcanism_ok(value, body.volcanism):
                return False
        elif rule_type == "body_type":
            if body.body_type not in value:
                return False
        elif rule_type in ("regions", "region"):
            if not _region_ok(value, system):
                return False
        elif rule_type == "guardian":
            if not _guardian_ok(bool(value), system):
                return False
        elif rule_type == "tuber":
            if not _tuber_ok(value, system):
                return False
        elif rule_type == "nebula":
            if not _nebula_ok(value, system):
                return False
        elif rule_type == "bodies":
            if not any(t in value for t in system.planet_types):
                return False
        elif rule_type in ("main_star", "parent_star", "star") and not system.stars_known:
            continue
        elif rule_type == "main_star":
            entries = value if isinstance(value, list) else [value]
            if not any(_star_entry_matches(e, system.main_star_type, system.main_star_luminosity) for e in entries):
                return False
        elif rule_type == "parent_star":
            candidates = [system.main_star_type] + [
                system.stars[n].star_type for n in body.parent_stars if n in system.stars
            ]
            if not any(star_check(star_type, c) for star_type in value for c in candidates):
                return False
        elif rule_type == "star":
            entries = value if isinstance(value, list) else [value]
            if not any(
                _star_entry_matches(e, s.star_type, s.luminosity) for s in system.stars.values() for e in entries
            ):
                return False
        elif rule_type == "distance":
            if body.distance is not None and body.distance < value:
                return False
        elif rule_type == "system":
            if system.name != value:
                return False
    return True


def _star_colors(colors: Dict[str, str], body: BodyContext, system: SystemContext) -> Set[str]:
    """Colours from the parent stars (first match), plus other stars at the arrival point or orbiting a black hole."""
    found: Set[str] = set()
    for name in body.parent_stars:
        star = system.stars.get(name)
        if not star:
            continue
        hit = next((color for star_type, color in colors.items() if star_check(star_type, star.star_type)), None)
        if hit:
            found.add(hit)
            break
    for name, star in system.stars.items():
        if name in body.parent_stars:
            continue
        if star.distance == 0 or _orbits_black_hole(star, body, system):
            hit = next((color for star_type, color in colors.items() if star_check(star_type, star.star_type)), None)
            if hit:
                found.add(hit)
    return found


def match_genus(genus: str, body: BodyContext, system: SystemContext) -> Dict[str, List[str]]:
    """Possible species of one genus on this body, mapped to their possible colour variants."""
    species_rules = SPECIES_RULES.get(genus)
    genus_data = GENUS_DATA.get(genus)
    if not species_rules or genus_data is None:
        return {}

    possible: Dict[str, Set[str]] = {
        species: set()
        for species, data in species_rules.items()
        if any(ruleset_passes(rs, body, system) for rs in data["rulesets"])
    }

    colors = genus_data.get("colors")
    if colors and system.stars_known:
        eliminated: Set[str] = set()
        if "species" in colors:
            for species in possible:
                species_colors = colors["species"].get(species, {})
                if "star" in species_colors:
                    possible[species] |= _star_colors(species_colors["star"], body, system)
                elif "element" in species_colors:
                    if not body.materials:
                        continue  # surface materials unknown (no detailed scan): cannot rule the species out
                    for element, color in species_colors["element"].items():
                        if element in body.materials:
                            possible[species].add(color)
                if not possible[species]:
                    eliminated.add(species)
        else:
            found = _star_colors(colors["star"], body, system)
            if not found:
                return {}
            for species in possible:
                possible[species] |= found
        for species in eliminated:
            del possible[species]

    return {species: sorted(c) for species, c in possible.items()}


def match_body(body: BodyContext, system: SystemContext) -> Dict[str, Dict[str, List[str]]]:
    """Possible species and colours for every genus that can exist on this body."""
    results = {}
    for genus in SPECIES_RULES:
        species = match_genus(genus, body, system)
        if species:
            results[genus] = species
    return results
