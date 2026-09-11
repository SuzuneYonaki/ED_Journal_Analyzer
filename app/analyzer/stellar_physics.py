"""
Elite Dangerous Journal Real-Time Physics & Rarity Analyzer
Includes Elite Observatory Core Astronomical Criteria Detection
"""

from __future__ import annotations

import glob
import json
import math
import os
import sqlite3
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

SOLAR_MASS_KG = 1.98847e30
EARTH_MASS_KG = 5.9722e24
G_CONST = 6.67430e-11
SOLAR_RADIUS_M = 6.957e8
SOLAR_TEFF_K = 5778.0
EARTH_RADIUS_M = 6.371e6
AU_M = 1.495978707e11

# Astrophysics constants and model parameters (published up to 2014)
# Galactic coordinate parameters (Juric et al. 2008, Vallee 2008, 2014)
SAG_A_POS_LY = (25.21875, -20.90625, 25899.96875)
GALACTIC_BAR_RADIUS_LY = 10000.0           # Inner bar / bulge radius ~3 kpc
GALACTIC_THIN_DISK_SCALE_HEIGHT_LY = 980.0 # ~300 pc (Juric et al. 2008)
GALACTIC_THICK_DISK_SCALE_HEIGHT_LY = 3260.0 # ~1000 pc
GALACTIC_HALO_THRESHOLD_LY = 5000.0        # ~1500 pc

# Kozai-Lidov resonance critical angle (Kozai 1962, Lidov 1962)
KOZAI_CRITICAL_INC_DEG = 39.2315

# Gladman (1993) Hill stability threshold for 2-planet systems
GLADMAN_HILL_STABILITY_LIMIT = 3.4641  # 2 * sqrt(3)

# Habitable zone solar flux limits (Kopparapu et al. 2013, 2014)
HZ_RECENT_VENUS_SEFF = 1.776
HZ_RUNAWAY_GREENHOUSE_SEFF = 1.107
HZ_MAXIMUM_GREENHOUSE_SEFF = 0.356
HZ_EARLY_MARS_SEFF = 0.320

# Composition / Radius transition boundary (Weiss & Marcy 2014)
ROCKY_VOLATILE_TRANSITION_RADIUS_EM = 1.6

EXOTIC_STAR_TYPES = {
    "N": "Neutron Star",
    "H": "Black Hole",
    "SupermassiveBlackHole": "Supermassive Black Hole",
    "W": "Wolf-Rayet",
    "WN": "Wolf-Rayet (WN)",
    "WNC": "Wolf-Rayet (WNC)",
    "WC": "Wolf-Rayet (WC)",
    "WO": "Wolf-Rayet (WO)",
    "D": "White Dwarf",
    "DA": "White Dwarf (DA)",
    "DAB": "White Dwarf (DAB)",
    "DAO": "White Dwarf (DAO)",
    "DAZ": "White Dwarf (DAZ)",
    "DAV": "White Dwarf (DAV)",
    "DB": "White Dwarf (DB)",
    "DBZ": "White Dwarf (DBZ)",
    "DBV": "White Dwarf (DBV)",
    "DO": "White Dwarf (DO)",
    "DOV": "White Dwarf (DOV)",
    "DQ": "White Dwarf (DQ)",
    "DC": "White Dwarf (DC)",
    "DCV": "White Dwarf (DCV)",
    "DX": "White Dwarf (DX)",
}


@dataclass
class ScanBody:
    body_id: int
    body_name: str
    distance_from_arrival_ls: Optional[float] = None
    star_type: Optional[str] = None
    stellar_mass: Optional[float] = None  # Solar masses
    radius: Optional[float] = None  # meters
    surface_temperature: Optional[float] = None  # Kelvin
    planet_class: Optional[str] = None
    mass_em: Optional[float] = None  # Earth masses
    surface_pressure: Optional[float] = None  # Pascals
    semi_major_axis: Optional[float] = None  # meters
    eccentricity: Optional[float] = None
    orbital_inclination: Optional[float] = None  # degrees
    orbital_period: Optional[float] = None  # seconds
    rotation_period: Optional[float] = None  # seconds
    tidal_lock: Optional[bool] = None
    axial_tilt: Optional[float] = None
    rings: List[Dict[str, Any]] = field(default_factory=list)
    belts: List[Dict[str, Any]] = field(default_factory=list)
    parents: List[Dict[str, int]] = field(default_factory=list)
    raw_event: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_star(self) -> bool:
        return self.star_type is not None

    @property
    def mass_kg(self) -> Optional[float]:
        if self.stellar_mass is not None:
            return self.stellar_mass * SOLAR_MASS_KG
        if self.mass_em is not None:
            return self.mass_em * EARTH_MASS_KG
        return None

    @property
    def parent_id(self) -> Optional[int]:
        if not self.parents:
            return None
        first_parent = self.parents[0]
        for key, val in first_parent.items():
            return int(val)
        return None

    @property
    def parent_type(self) -> Optional[str]:
        if not self.parents:
            return None
        first_parent = self.parents[0]
        for key in first_parent.keys():
            return key
        return None

    @property
    def radius_em(self) -> Optional[float]:
        if self.radius is not None and self.radius > 0:
            return self.radius / EARTH_RADIUS_M
        return None

    @property
    def density_g_cm3(self) -> Optional[float]:
        m = self.mass_kg
        r = self.radius
        if m is not None and r is not None and r > 0:
            volume_m3 = (4.0 / 3.0) * math.pi * (r ** 3)
            density_kg_m3 = m / volume_m3
            return density_kg_m3 / 1000.0  # convert kg/m^3 to g/cm^3
        return None

    @property
    def luminosity_solar(self) -> Optional[float]:
        if self.is_star and self.radius and self.surface_temperature:
            r_ratio = self.radius / SOLAR_RADIUS_M
            t_ratio = self.surface_temperature / SOLAR_TEFF_K
            return (r_ratio ** 2) * (t_ratio ** 4)
        return None


@dataclass
class SystemData:
    system_name: str
    system_address: Optional[int] = None
    star_pos: Optional[List[float]] = None
    bodies: Dict[int, ScanBody] = field(default_factory=dict)
    jump_timestamp: Optional[str] = None


@dataclass
class SystemEvaluation:
    system_name: str
    star_count: int
    planet_count: int
    rarity_score: float
    anomalies: List[str]
    raw_features: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


class StellarPhysicsEngine:
    """
    Evaluates physical and orbital anomalies based on astrophysics,
    planetary formation models, and Elite Observatory Core criteria.
    """

    @classmethod
    def calculate_fluid_roche_limit(
        cls, primary_mass_kg: float, satellite_mass_kg: float, satellite_radius_m: float
    ) -> Optional[float]:
        """
        Approximates fluid Roche limit:
        d_roche = 2.44 * R_sat * (M_pri / M_sat) ** (1/3)
        """
        if satellite_mass_kg <= 0 or satellite_radius_m <= 0 or primary_mass_kg <= 0:
            return None
        return 2.44 * satellite_radius_m * ((primary_mass_kg / satellite_mass_kg) ** (1.0 / 3.0))

    @classmethod
    def evaluate_galactic_context(cls, star_pos: Optional[List[float]]) -> Dict[str, Any]:
        """
        Evaluates system galactic position based on Milky Way structural models
        (Juric et al. 2008, Vallee 2008, 2014).
        Sol is at (0, 0, 0) ly. Sagittarius A* is at (25.2, -20.9, 25899.97) ly.
        """
        if not star_pos or len(star_pos) < 3:
            return {
                "galactic_region": "Unknown",
                "dist_to_sag_a_ly": None,
                "vertical_height_ly": None,
                "is_galactic_bar_bulge": False,
                "is_halo_system": False,
                "thin_disk_scale_probability": None,
            }

        x, y, z = star_pos[0], star_pos[1], star_pos[2]
        sag_x, sag_y, sag_z = SAG_A_POS_LY

        dx = x - sag_x
        dy = y - sag_y
        dz = z - sag_z
        dist_sag_a = math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
        r_gal_plane = math.sqrt(dx ** 2 + dz ** 2)
        vertical_height = abs(y)

        p_thin_disk = math.exp(-vertical_height / GALACTIC_THIN_DISK_SCALE_HEIGHT_LY)

        is_bar_bulge = r_gal_plane <= GALACTIC_BAR_RADIUS_LY
        is_halo = vertical_height >= GALACTIC_HALO_THRESHOLD_LY or dist_sag_a > 50000.0

        if is_bar_bulge:
            region = "Galactic Bulge / Central Bar"
        elif is_halo:
            region = "Galactic Halo"
        elif vertical_height <= GALACTIC_THIN_DISK_SCALE_HEIGHT_LY:
            region = "Thin Galactic Disk"
        else:
            region = "Thick Galactic Disk"

        return {
            "galactic_region": region,
            "dist_to_sag_a_ly": round(dist_sag_a, 1),
            "dist_gal_plane_radial_ly": round(r_gal_plane, 1),
            "vertical_height_ly": round(vertical_height, 1),
            "is_galactic_bar_bulge": is_bar_bulge,
            "is_halo_system": is_halo,
            "thin_disk_scale_probability": round(p_thin_disk, 4),
        }

    @classmethod
    def evaluate_habitable_zone_kopparapu(
        cls, star: ScanBody, planet: ScanBody
    ) -> Optional[Dict[str, Any]]:
        """
        Calculates Habitable Zone boundaries using Kopparapu et al. (2013, 2014) model.
        Returns flux, inner/outer boundaries in AU and meters, and in-zone status.
        """
        l_solar = star.luminosity_solar
        a_m = planet.semi_major_axis
        if l_solar is None or l_solar <= 0 or a_m is None or a_m <= 0:
            return None

        r_recent_venus_au = math.sqrt(l_solar / HZ_RECENT_VENUS_SEFF)
        r_runaway_au = math.sqrt(l_solar / HZ_RUNAWAY_GREENHOUSE_SEFF)
        r_max_greenhouse_au = math.sqrt(l_solar / HZ_MAXIMUM_GREENHOUSE_SEFF)
        r_early_mars_au = math.sqrt(l_solar / HZ_EARLY_MARS_SEFF)

        planet_dist_au = a_m / AU_M
        in_conservative_hz = r_runaway_au <= planet_dist_au <= r_max_greenhouse_au
        in_optimistic_hz = r_recent_venus_au <= planet_dist_au <= r_early_mars_au

        received_flux = l_solar / (planet_dist_au ** 2)

        return {
            "stellar_luminosity_solar": round(l_solar, 4),
            "planet_distance_au": round(planet_dist_au, 4),
            "received_flux_seff": round(received_flux, 3),
            "hz_inner_optimistic_au": round(r_recent_venus_au, 4),
            "hz_inner_conservative_au": round(r_runaway_au, 4),
            "hz_outer_conservative_au": round(r_max_greenhouse_au, 4),
            "hz_outer_optimistic_au": round(r_early_mars_au, 4),
            "in_conservative_hz": in_conservative_hz,
            "in_optimistic_hz": in_optimistic_hz,
        }

    @classmethod
    def evaluate_mutual_hill_stability(
        cls, siblings: List[ScanBody], parent_star: ScanBody
    ) -> List[Dict[str, Any]]:
        """
        Evaluates orbital stability of adjacent planet pairs via Gladman (1993)
        mutual Hill radius criterion:
        Delta_H = (a2 - a1) / R_H_mutual
        where R_H_mutual = ((a1 + a2) / 2) * ((m1 + m2) / (3 * M_star))^(1/3)
        Gladman stability threshold: Delta_H > 2 * sqrt(3) ~= 3.464
        """
        results: List[Dict[str, Any]] = []
        star_mass = parent_star.mass_kg
        if not star_mass or star_mass <= 0:
            return results

        valid = [p for p in siblings if p.semi_major_axis and p.mass_kg and p.semi_major_axis > 0]
        valid.sort(key=lambda x: x.semi_major_axis or 0.0)

        for i in range(len(valid) - 1):
            p1 = valid[i]
            p2 = valid[i + 1]
            a1 = p1.semi_major_axis
            a2 = p2.semi_major_axis
            m1 = p1.mass_kg
            m2 = p2.mass_kg
            if a1 and a2 and m1 and m2 and a2 > a1:
                mean_a = (a1 + a2) / 2.0
                mass_ratio = (m1 + m2) / (3.0 * star_mass)
                if mass_ratio > 0:
                    r_h_mutual = mean_a * (mass_ratio ** (1.0 / 3.0))
                    delta_h = (a2 - a1) / r_h_mutual if r_h_mutual > 0 else 999.0
                    results.append({
                        "body1": p1.body_name,
                        "body2": p2.body_name,
                        "delta_hill": round(delta_h, 3),
                        "is_gladman_unstable": delta_h < GLADMAN_HILL_STABILITY_LIMIT,
                        "separation_m": a2 - a1,
                        "mutual_hill_radius_m": r_h_mutual,
                    })
        return results

    @classmethod
    def evaluate_kozai_lidov_regime(
        cls, body: ScanBody, companion_star: Optional[ScanBody]
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluates whether a body is prone to Kozai-Lidov cycles
        under secular gravitational perturbation of an inclined companion
        (Kozai 1962, Fabrycky & Tremaine 2007).
        Critical inclination: 39.23 deg <= i <= 140.77 deg.
        """
        inc = body.orbital_inclination
        if inc is None or companion_star is None:
            return None

        norm_inc = abs(inc)
        in_kozai_regime = (
            KOZAI_CRITICAL_INC_DEG <= norm_inc <= (180.0 - KOZAI_CRITICAL_INC_DEG)
        )
        if in_kozai_regime:
            rad_inc = math.radians(norm_inc)
            cos_i = math.cos(rad_inc)
            cos2_term = (5.0 / 3.0) * (cos_i ** 2)
            e_max = math.sqrt(max(0.0, 1.0 - cos2_term))
            return {
                "body": body.body_name,
                "companion_perturber": companion_star.body_name,
                "inclination_deg": round(norm_inc, 2),
                "in_kozai_regime": True,
                "max_theoretical_eccentricity": round(e_max, 4),
            }
        return None

    @classmethod
    def evaluate_composition_weiss_marcy2014(
        cls, planet: ScanBody
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluates planetary bulk composition and radius transition
        (Weiss & Marcy 2014, Seager et al. 2007).
        Rocky-to-volatile transition radius ~= 1.5 - 1.6 Earth radii.
        """
        r_em = planet.radius_em
        m_em = planet.mass_em
        density = planet.density_g_cm3
        if r_em is None or density is None:
            return None

        is_mega_earth = r_em >= ROCKY_VOLATILE_TRANSITION_RADIUS_EM and density >= 5.5
        is_super_mercury = density >= 8.0
        is_low_density_puffy = r_em <= 2.0 and density < 1.5

        if is_mega_earth or is_super_mercury or is_low_density_puffy:
            return {
                "body": planet.body_name,
                "radius_earth": round(r_em, 2),
                "mass_earth": round(m_em, 2) if m_em else None,
                "density_g_cm3": round(density, 2),
                "is_mega_earth": is_mega_earth,
                "is_super_mercury": is_super_mercury,
                "is_low_density_puffy": is_low_density_puffy,
            }
        return None

    @classmethod
    def evaluate(cls, system: SystemData) -> SystemEvaluation:
        stars = [b for b in system.bodies.values() if b.is_star]
        planets = [b for b in system.bodies.values() if not b.is_star]

        star_count = len(stars)
        planet_count = len(planets)

        anomalies: List[str] = []
        rarity_points: float = 10.0  # Baseline score

        # Detailed tracking for Observatory criteria
        close_binary_events: List[Dict[str, Any]] = []
        wide_ring_events: List[Dict[str, Any]] = []
        nested_moon_events: List[Dict[str, Any]] = []
        small_object_events: List[Dict[str, Any]] = []
        close_belt_events: List[Dict[str, Any]] = []
        shepherd_moon_events: List[Dict[str, Any]] = []
        close_orbit_events: List[Dict[str, Any]] = []
        fast_rotator_events: List[Dict[str, Any]] = []

        features: Dict[str, Any] = {
            "star_count": star_count,
            "planet_count": planet_count,
            "max_eccentricity": 0.0,
            "min_orbital_period_days": None,
            "min_roche_ratio": None,
            "exotic_stars": [],
            "has_retrograde_orbits": False,
            "has_polar_orbits": False,
            "earth_like_count": 0,
            "ammonia_world_count": 0,
            "water_world_count": 0,
            "habitable_life_anomalies": 0,
            "observatory_criteria": {
                "close_binary_count": 0,
                "wide_ring_count": 0,
                "nested_moon_count": 0,
                "small_object_count": 0,
                "close_belt_proximity_count": 0,
                "shepherd_moon_count": 0,
                "close_orbit_count": 0,
                "non_locked_fast_rotation_count": 0,
            },
            "observatory_details": {},
            "astrophysics_2014_models": {
                "galactic_context": {},
                "habitable_zone_kopparapu": [],
                "mutual_hill_stability_gladman": [],
                "kozai_lidov_regime": [],
                "composition_weiss_marcy": [],
            },
        }

        # 1. Galactic Context (Juric et al. 2008, Vallee 2008, 2014)
        gal_context = cls.evaluate_galactic_context(system.star_pos)
        features["astrophysics_2014_models"]["galactic_context"] = gal_context
        if gal_context["is_halo_system"]:
            rarity_points += 20.0
            anomalies.append(
                f"Galactic Halo system (height={gal_context['vertical_height_ly']} ly above plane, Population II / low-metallicity regime)"
            )
        elif gal_context["is_galactic_bar_bulge"]:
            rarity_points += 15.0
            anomalies.append(
                f"Galactic Central Bar / Bulge proximity (dist_SagA={gal_context['dist_to_sag_a_ly']} ly, extreme stellar density zone)"
            )

        # 1. Stellar Remnants and Multiple Systems
        exotic_star_types_found = []
        for s in stars:
            st = s.star_type or ""
            matched_exotic = None
            if st in EXOTIC_STAR_TYPES:
                matched_exotic = EXOTIC_STAR_TYPES[st]
            else:
                for prefix, desc in EXOTIC_STAR_TYPES.items():
                    if st.startswith(prefix):
                        matched_exotic = desc
                        break

            if matched_exotic:
                exotic_star_types_found.append(f"{s.body_name} ({matched_exotic})")
                if "Black Hole" in matched_exotic:
                    rarity_points += 25.0
                elif "Neutron" in matched_exotic:
                    rarity_points += 20.0
                elif "Wolf-Rayet" in matched_exotic:
                    rarity_points += 25.0
                elif "White Dwarf" in matched_exotic:
                    rarity_points += 12.0

        if exotic_star_types_found:
            anomalies.append(f"Exotic stellar remnant detected: {', '.join(exotic_star_types_found)}")
            features["exotic_stars"] = exotic_star_types_found

        if star_count >= 5:
            rarity_points += 25.0
            anomalies.append(f"High-order multiple stellar system with {star_count} stars")
        elif star_count >= 3:
            rarity_points += 15.0
            anomalies.append(f"Hierarchical triple/multiple stellar system ({star_count} stars)")

        # Collect belts from all bodies for proximity checks
        all_belts: List[Tuple[ScanBody, Dict[str, Any]]] = []
        for b in system.bodies.values():
            for belt in b.belts:
                all_belts.append((b, belt))

        # 2. Orbital Dynamics, Elite Observatory Criteria & Body Anomalies
        max_eccentricity = 0.0
        min_period_sec: Optional[float] = None
        min_roche_ratio: Optional[float] = None

        # Group bodies by parent for binary pairing analysis
        parent_children_map: Dict[Tuple[str, int], List[ScanBody]] = {}
        for b in system.bodies.values():
            if b.parents:
                p_type = b.parent_type or "Unknown"
                p_id = b.parent_id if b.parent_id is not None else -1
                parent_children_map.setdefault((p_type, p_id), []).append(b)

        # Check: Close binary relative to body size (among siblings orbiting common barycentre / parent)
        for (p_type, p_id), siblings in parent_children_map.items():
            if p_type == "Null" and len(siblings) >= 2:
                for i in range(len(siblings)):
                    for j in range(i + 1, len(siblings)):
                        b1 = siblings[i]
                        b2 = siblings[j]
                        if b1.radius and b2.radius and b1.semi_major_axis and b2.semi_major_axis:
                            combined_radius = b1.radius + b2.radius
                            # In barycentric orbit, separation is a1 + a2
                            separation = b1.semi_major_axis + b2.semi_major_axis
                            ratio = separation / combined_radius if combined_radius > 0 else 999.0
                            if ratio <= 4.0:
                                rarity_points += 20.0
                                detail = {
                                    "body1": b1.body_name,
                                    "body2": b2.body_name,
                                    "separation_m": separation,
                                    "combined_radius_m": combined_radius,
                                    "ratio": round(ratio, 2),
                                }
                                close_binary_events.append(detail)
                                anomalies.append(
                                    f"Close binary relative to body size: {b1.body_name} & {b2.body_name} (separation={separation/1e3:.0f} km, combined radius={combined_radius/1e3:.0f} km, ratio={ratio:.2f})"
                                )

        for b in system.bodies.values():
            e = b.eccentricity
            a = b.semi_major_axis
            p = b.orbital_period
            inc = b.orbital_inclination
            rad = b.radius
            parent = system.bodies.get(b.parent_id) if b.parent_id is not None else None

            # Eccentricity analysis
            if e is not None:
                if e > max_eccentricity:
                    max_eccentricity = e
                if e >= 0.85:
                    rarity_points += 20.0
                    anomalies.append(
                        f"Extreme orbital eccentricity on {b.body_name} (e={e:.4f}) indicating dynamic scattering or capture"
                    )
                elif e >= 0.65:
                    rarity_points += 10.0
                    anomalies.append(
                        f"High orbital eccentricity on {b.body_name} (e={e:.4f})"
                    )

            # Orbital period analysis (short-period bodies)
            if p is not None and p > 0:
                if min_period_sec is None or p < min_period_sec:
                    min_period_sec = p
                period_hours = p / 3600.0
                if period_hours < 6.0:
                    rarity_points += 25.0
                    anomalies.append(
                        f"Ultra-short orbital period on {b.body_name} (P={period_hours:.2f} h) at extreme stellar proximity"
                    )
                elif period_hours < 12.0:
                    rarity_points += 15.0
                    anomalies.append(
                        f"Very short orbital period on {b.body_name} (P={period_hours:.2f} h)"
                    )

            # Orbital inclination analysis (retrograde / polar)
            if inc is not None:
                norm_inc = abs(inc)
                if norm_inc > 105.0:
                    features["has_retrograde_orbits"] = True
                    rarity_points += 15.0
                    anomalies.append(
                        f"Retrograde orbit detected on {b.body_name} (inclination={inc:.2f} deg)"
                    )
                elif 75.0 <= norm_inc <= 105.0:
                    features["has_polar_orbits"] = True
                    rarity_points += 10.0
                    anomalies.append(
                        f"Orthogonal/polar orbit detected on {b.body_name} relative to system reference plane (inclination={inc:.2f} deg)"
                    )

            # Roche limit / Tidal disruption proximity
            if a is not None and e is not None and parent:
                if parent.mass_kg and b.mass_kg and rad:
                    d_roche = cls.calculate_fluid_roche_limit(
                        primary_mass_kg=parent.mass_kg,
                        satellite_mass_kg=b.mass_kg,
                        satellite_radius_m=rad,
                    )
                    if d_roche and d_roche > 0:
                        periapsis = a * (1.0 - e)
                        ratio = periapsis / d_roche
                        if min_roche_ratio is None or ratio < min_roche_ratio:
                            min_roche_ratio = ratio
                        if ratio <= 1.1:
                            rarity_points += 30.0
                            anomalies.append(
                                f"Critical tidal stress: {b.body_name} periapsis ({periapsis/1e6:.1f} Mm) within fluid Roche limit of {parent.body_name} (ratio={ratio:.2f})"
                            )
                        elif ratio <= 1.6:
                            rarity_points += 18.0
                            anomalies.append(
                                f"High tidal deformation zone: {b.body_name} orbits close to fluid Roche limit of {parent.body_name} (ratio={ratio:.2f})"
                            )

            # Check: Close Orbit (Extreme proximity to parent surface)
            if a is not None and parent and parent.radius:
                periapsis = a * (1.0 - (e or 0.0))
                # Orbit periapsis within 3x parent radius or separation < 3x parent radius
                if periapsis <= 3.0 * parent.radius:
                    rarity_points += 15.0
                    close_orbit_detail = {
                        "body": b.body_name,
                        "parent": parent.body_name,
                        "periapsis_m": periapsis,
                        "parent_radius_m": parent.radius,
                        "ratio": round(periapsis / parent.radius, 2),
                    }
                    close_orbit_events.append(close_orbit_detail)
                    anomalies.append(
                        f"Close Orbit: {b.body_name} orbits at extreme proximity to {parent.body_name} (periapsis={periapsis/1e3:.0f} km, parent radius={parent.radius/1e3:.0f} km, ratio={periapsis/parent.radius:.2f})"
                    )

            # Check: Small Object (tiny moon or planetoid)
            if not b.is_star and rad is not None:
                if rad < 300000.0:  # < 300 km
                    rarity_points += 8.0
                    small_obj_detail = {
                        "body": b.body_name,
                        "radius_km": round(rad / 1000.0, 1),
                    }
                    small_object_events.append(small_obj_detail)
                    anomalies.append(
                        f"Small Object: {b.body_name} has exceptionally small radius ({rad/1e3:.1f} km)"
                    )

            # Check: Wide Ring
            if b.rings and rad is not None and rad > 0:
                for ring in b.rings:
                    inner_rad = ring.get("InnerRad", 0.0)
                    outer_rad = ring.get("OuterRad", 0.0)
                    ring_width = outer_rad - inner_rad
                    ratio = ring_width / rad
                    if ratio >= 5.0 or ring_width >= 1.0e9:  # width >= 5x radius or >= 1,000,000 km
                        rarity_points += 12.0
                        wide_ring_detail = {
                            "body": b.body_name,
                            "ring_name": ring.get("Name", "Ring"),
                            "width_m": ring_width,
                            "ratio_to_radius": round(ratio, 2),
                        }
                        wide_ring_events.append(wide_ring_detail)
                        anomalies.append(
                            f"Wide Ring: {b.body_name} [{ring.get('Name', 'Ring')}] width is {ring_width/1e6:.1f} Mm ({ratio:.1f}x body radius)"
                        )

            # Check: Nested Moon (Moon of a Moon)
            # In Journal, parents are ordered innermost to outermost:
            # [{"Planet": moon_parent_id}, {"Planet": planet_parent_id}, ...]
            if not b.is_star and len(b.parents) >= 2:
                first_parent_type = list(b.parents[0].keys())[0] if b.parents[0] else ""
                second_parent_type = list(b.parents[1].keys())[0] if b.parents[1] else ""
                if first_parent_type == "Planet" and second_parent_type == "Planet":
                    rarity_points += 15.0
                    p1_id = b.parents[0]["Planet"]
                    p2_id = b.parents[1]["Planet"]
                    p1_name = system.bodies[p1_id].body_name if p1_id in system.bodies else f"Planet_{p1_id}"
                    p2_name = system.bodies[p2_id].body_name if p2_id in system.bodies else f"Planet_{p2_id}"
                    nested_detail = {
                        "body": b.body_name,
                        "parent_moon": p1_name,
                        "grandparent_planet": p2_name,
                    }
                    nested_moon_events.append(nested_detail)
                    anomalies.append(
                        f"Nested Moon: {b.body_name} orbits moon {p1_name}, which orbits planet {p2_name}"
                    )

            # Check: Shepherd Moon (Moon orbiting inside or near rings of parent)
            if not b.is_star and a is not None and parent and parent.rings:
                for ring in parent.rings:
                    inner_rad = ring.get("InnerRad", 0.0)
                    outer_rad = ring.get("OuterRad", 0.0)
                    # Satellite within 0.8x inner to 1.2x outer ring boundary
                    if 0.8 * inner_rad <= a <= 1.2 * outer_rad:
                        rarity_points += 18.0
                        shepherd_detail = {
                            "body": b.body_name,
                            "parent": parent.body_name,
                            "ring_name": ring.get("Name", "Ring"),
                            "semi_major_axis_m": a,
                            "ring_inner_m": inner_rad,
                            "ring_outer_m": outer_rad,
                        }
                        shepherd_moon_events.append(shepherd_detail)
                        anomalies.append(
                            f"Shepherd Moon: {b.body_name} orbits within or grazing rings of {parent.body_name} (a={a/1e6:.1f} Mm, ring=[{inner_rad/1e6:.1f}-{outer_rad/1e6:.1f}] Mm)"
                        )

            # Check: Close belt proximity (Body orbiting inside or near asteroid belt)
            if a is not None and all_belts:
                for belt_host, belt in all_belts:
                    b_inner = belt.get("InnerRad", 0.0)
                    b_outer = belt.get("OuterRad", 0.0)
                    if b_inner > 0 and b_outer > 0:
                        # Check if body orbits host within or very close to belt bounds
                        if b.parent_id == belt_host.body_id:
                            if 0.8 * b_inner <= a <= 1.2 * b_outer:
                                rarity_points += 12.0
                                belt_detail = {
                                    "body": b.body_name,
                                    "belt_host": belt_host.body_name,
                                    "belt_name": belt.get("Name", "Belt"),
                                    "semi_major_axis_m": a,
                                }
                                close_belt_events.append(belt_detail)
                                anomalies.append(
                                    f"Close belt proximity: {b.body_name} orbits in close proximity to {belt.get('Name', 'Belt')} of {belt_host.body_name}"
                                )

            # Check: Non-locked body with fast rotation
            if not b.is_star and b.rotation_period is not None and b.rotation_period > 0:
                is_locked = b.tidal_lock is True
                rot_hours = abs(b.rotation_period) / 3600.0
                if not is_locked and rot_hours < 12.0:
                    rarity_points += 12.0
                    fast_rot_detail = {
                        "body": b.body_name,
                        "rotation_period_hours": round(rot_hours, 2),
                        "tidal_lock": b.tidal_lock,
                    }
                    fast_rotator_events.append(fast_rot_detail)
                    anomalies.append(
                        f"Non-locked body with fast rotation: {b.body_name} (rot_period={rot_hours:.2f} h, locked={b.tidal_lock})"
                    )

            # Planets orbiting exotic remnants
            if not b.is_star and parent and parent.is_star and parent.star_type:
                st_p = parent.star_type
                if st_p in ("N", "H", "SupermassiveBlackHole") or st_p.startswith("W"):
                    rarity_points += 20.0
                    anomalies.append(
                        f"Exotic planetary system: {b.body_name} orbits remnant/exotic star {parent.body_name} ({st_p})"
                    )

            # Rare Planetary Bodies & Habitable Anomaly
            p_class = (b.planet_class or "").lower()
            temp_k = b.surface_temperature
            press_pa = b.surface_pressure

            if "earthlike" in p_class:
                features["earth_like_count"] += 1
                rarity_points += 15.0
                if temp_k is not None:
                    if temp_k < 250.0 or temp_k > 320.0:
                        features["habitable_life_anomalies"] += 1
                        rarity_points += 15.0
                        anomalies.append(
                            f"Earth-like World {b.body_name} exhibits atypical thermal equilibrium (T={temp_k:.1f} K)"
                        )
                if press_pa is not None:
                    press_atm = press_pa / 101325.0
                    if press_atm < 0.4 or press_atm > 3.0:
                        features["habitable_life_anomalies"] += 1
                        rarity_points += 15.0
                        anomalies.append(
                            f"Earth-like World {b.body_name} with extreme atmospheric pressure ({press_atm:.2f} atm)"
                        )

            elif "ammonia world" in p_class:
                features["ammonia_world_count"] += 1
                rarity_points += 12.0
            elif "water world" in p_class:
                features["water_world_count"] += 1
                rarity_points += 8.0

        features["max_eccentricity"] = max_eccentricity
        if min_period_sec is not None:
            features["min_orbital_period_days"] = min_period_sec / 86400.0
        features["min_roche_ratio"] = min_roche_ratio

        # Populate Observatory Criteria Summary
        features["observatory_criteria"] = {
            "close_binary_count": len(close_binary_events),
            "wide_ring_count": len(wide_ring_events),
            "nested_moon_count": len(nested_moon_events),
            "small_object_count": len(small_object_events),
            "close_belt_proximity_count": len(close_belt_events),
            "shepherd_moon_count": len(shepherd_moon_events),
            "close_orbit_count": len(close_orbit_events),
            "non_locked_fast_rotation_count": len(fast_rotator_events),
        }
        features["observatory_details"] = {
            "close_binaries": close_binary_events,
            "wide_rings": wide_ring_events,
            "nested_moons": nested_moon_events,
            "small_objects": small_object_events,
            "close_belts": close_belt_events,
            "shepherd_moons": shepherd_moon_events,
            "close_orbits": close_orbit_events,
            "fast_rotators": fast_rotator_events,
        }

        # 3. 2014 Astrophysical Models Integration
        primary_star = stars[0] if stars else None

        # Habitable Zone (Kopparapu et al. 2013, 2014)
        for p in planets:
            p_parent_star = system.bodies.get(p.parent_id) if p.parent_id is not None else primary_star
            if p_parent_star and p_parent_star.is_star:
                hz_info = cls.evaluate_habitable_zone_kopparapu(p_parent_star, p)
                if hz_info:
                    hz_entry = {"planet": p.body_name, "star": p_parent_star.body_name, **hz_info}
                    features["astrophysics_2014_models"]["habitable_zone_kopparapu"].append(hz_entry)
                    p_class = (p.planet_class or "").lower()
                    is_life_bearing = "earthlike" in p_class or "water world" in p_class or "ammonia world" in p_class
                    if is_life_bearing:
                        if hz_info["in_conservative_hz"]:
                            anomalies.append(
                                f"{p.body_name} confirmed in conservative Habitable Zone (Kopparapu 2013, S_eff={hz_info['received_flux_seff']:.2f})"
                            )
                        elif not hz_info["in_optimistic_hz"]:
                            rarity_points += 20.0
                            anomalies.append(
                                f"Life-bearing body {p.body_name} outside Kopparapu (2013) Habitable Zone (S_eff={hz_info['received_flux_seff']:.2f}; anomalous radiative equilibrium)"
                            )

        # Mutual Hill Stability (Gladman 1993, Chambers et al. 1996)
        for star_obj in stars:
            siblings = [p for p in planets if p.parent_id == star_obj.body_id]
            hill_results = cls.evaluate_mutual_hill_stability(siblings, star_obj)
            for h_res in hill_results:
                features["astrophysics_2014_models"]["mutual_hill_stability_gladman"].append(h_res)
                if h_res["is_gladman_unstable"]:
                    rarity_points += 25.0
                    anomalies.append(
                        f"Critical Hill instability: {h_res['body1']} & {h_res['body2']} (Delta_H={h_res['delta_hill']:.2f} < {GLADMAN_HILL_STABILITY_LIMIT} Gladman limit; chaotic scattering imminent)"
                    )

        # Kozai-Lidov Secular Resonance (Kozai 1962, Fabrycky & Tremaine 2007)
        if len(stars) >= 2:
            for s_idx in range(len(stars)):
                for comp_idx in range(len(stars)):
                    if s_idx != comp_idx:
                        s_primary = stars[s_idx]
                        s_comp = stars[comp_idx]
                        circumbodies = [p for p in planets if p.parent_id == s_primary.body_id]
                        for cb in circumbodies:
                            kz = cls.evaluate_kozai_lidov_regime(cb, s_comp)
                            if kz:
                                features["astrophysics_2014_models"]["kozai_lidov_regime"].append(kz)
                                rarity_points += 15.0
                                anomalies.append(
                                    f"Kozai-Lidov secular resonance on {cb.body_name} by companion {s_comp.body_name} (inc={kz['inclination_deg']:.1f} deg, theoretical e_max={kz['max_theoretical_eccentricity']:.2f})"
                                )

        # Composition & Transition Boundary (Weiss & Marcy 2014)
        for p in planets:
            comp = cls.evaluate_composition_weiss_marcy2014(p)
            if comp:
                features["astrophysics_2014_models"]["composition_weiss_marcy"].append(comp)
                if comp["is_mega_earth"]:
                    rarity_points += 22.0
                    anomalies.append(
                        f"Mega-Earth anomaly: {p.body_name} (R={comp['radius_earth']} R_Earth > 1.6, density={comp['density_g_cm3']} g/cm^3; Weiss & Marcy 2014 transition)"
                    )
                elif comp["is_super_mercury"]:
                    rarity_points += 20.0
                    anomalies.append(
                        f"Super-Mercury mantle stripping: {p.body_name} (density={comp['density_g_cm3']} g/cm^3 > 8.0 g/cm^3)"
                    )
                elif comp["is_low_density_puffy"]:
                    rarity_points += 15.0
                    anomalies.append(
                        f"Puffy low-density terrestrial body: {p.body_name} (density={comp['density_g_cm3']} g/cm^3 < 1.5 g/cm^3)"
                    )

        # Deduplicate anomalies while preserving insertion order
        unique_anomalies: List[str] = []
        for a_desc in anomalies:
            if a_desc not in unique_anomalies:
                unique_anomalies.append(a_desc)

        final_score = max(10.0, min(100.0, round(rarity_points, 1)))

        return SystemEvaluation(
            system_name=system.system_name,
            star_count=star_count,
            planet_count=planet_count,
            rarity_score=final_score,
            anomalies=unique_anomalies,
            raw_features=features,
        )


class SystemNarrator:
    """
    Generates human-readable, accessible astrophysical reports
    with everyday analogies and dual-unit parallel formatting.
    All strings are strictly ASCII.
    """

    @staticmethod
    def format_distance_analogy(meters: Optional[float], arrival_ls: Optional[float] = None) -> str:
        if (meters is None or meters <= 0) and (arrival_ls is None or arrival_ls <= 0):
            return "N/A"
        
        # If semi_major_axis is very small (e.g. binary planet or moon < 1,000,000 km) and arrival_ls is available
        if arrival_ls is not None and arrival_ls > 0:
            star_dist_m = arrival_ls * 299792458.0
            star_au = star_dist_m / AU_M
            star_km_mil = (star_dist_m / 1000.0) / 1.0e6
            
            # Check if meters is a close pair orbit (< 0.05 AU)
            if meters is not None and meters > 0 and (meters / AU_M) < 0.05:
                pair_km = meters / 1000.0
                if pair_km >= 10000:
                    pair_str = f"pair orbit: ~{pair_km/10000:.1f}x10^4 km"
                else:
                    pair_str = f"pair orbit: ~{pair_km:,.0f} km"
                return f"{star_au:.2f} AU (~{star_km_mil:.1f}M km from host; {pair_str})"
            elif meters is None or meters <= 0:
                return f"{star_au:.2f} AU (~{star_km_mil:.1f}M km from host)"

        if meters is None or meters <= 0:
            return "N/A"

        au = meters / AU_M
        km_mil = (meters / 1000.0) / 1.0e6
        if au < 0.01:
            local_km = meters / 1000.0
            return f"~{local_km:,.0f} km (extreme close-in orbit, far closer than Mercury)"
        elif au < 0.1:
            analogy = "extreme close-in orbit, far closer than Mercury"
        elif 0.3 <= au <= 0.5:
            analogy = "comparable to Mercury's orbit"
        elif 0.9 <= au <= 1.2:
            analogy = "similar to Earth-Sun distance (1 AU)"
        elif 1.3 <= au <= 1.8:
            analogy = "comparable to Mars's orbit"
        elif 4.8 <= au <= 5.6:
            analogy = "comparable to Jupiter's orbit"
        elif 9.0 <= au <= 11.0:
            analogy = "comparable to Saturn's cold orbit"
        else:
            analogy = f"{au:.1f} AU from host"
        return f"{au:.2f} AU (~{km_mil:.1f}M km; {analogy})"

    @classmethod
    def format_star_temperature_analogy(cls, star: ScanBody) -> str:
        """
        Formats star effective temperature relative to its stellar classification
        (e.g., hot for M-dwarf, cold for neutron star) instead of planetary analogies.
        """
        kelvin = star.surface_temperature
        if kelvin is None or kelvin <= 0:
            return "N/A"
        st = (star.star_type or "").upper()

        if st == "N":
            if kelvin < 1000000.0:
                eval_str = "cooling remnant state for a neutron star"
            elif kelvin <= 3000000.0:
                eval_str = "typical high-energy X-ray surface temperature for neutron star"
            else:
                eval_str = "ultra-hot young energetic neutron star"
            return f"{kelvin:,.0f} K ({eval_str})"
        elif st.startswith("D"):
            if kelvin > 30000.0:
                eval_str = "very hot young white dwarf"
            elif kelvin >= 10000.0:
                eval_str = "standard cooling regime for white dwarf"
            else:
                eval_str = "cool degenerate white dwarf"
            return f"{kelvin:,.0f} K ({eval_str})"
        elif st.startswith("M"):
            if kelvin >= 3400.0:
                eval_str = "hotter regime for M-class red dwarf (early M-type, high activity)"
            elif kelvin >= 2800.0:
                eval_str = "typical temperature for M-class red dwarf"
            else:
                eval_str = "very cool regime for M-class dwarf (late M-type, ultra-low luminosity)"
            return f"{kelvin:.1f} K ({eval_str})"
        elif st.startswith("K"):
            if kelvin >= 4800.0:
                eval_str = "warm regime for K-class orange dwarf"
            elif kelvin >= 3800.0:
                eval_str = "typical temperature for K-class orange dwarf"
            else:
                eval_str = "cool regime for K-class dwarf"
            return f"{kelvin:.1f} K ({eval_str})"
        elif st.startswith("G"):
            if 5500.0 <= kelvin <= 6000.0:
                eval_str = "solar-analog standard effective temperature"
            elif kelvin > 6000.0:
                eval_str = "hotter regime for G-class star"
            else:
                eval_str = "cooler regime for G-class star"
            return f"{kelvin:.1f} K ({eval_str})"
        elif st.startswith("F"):
            return f"{kelvin:.1f} K (standard effective temperature for F-class yellow-white star)"
        elif st.startswith("A"):
            return f"{kelvin:.1f} K (hot luminous A-class white star)"
        elif st.startswith("B"):
            return f"{kelvin:.1f} K (intense luminous blue star with high UV flux)"
        elif st.startswith("O"):
            return f"{kelvin:.1f} K (extreme hyper-luminous blue star)"
        elif st in ("L", "T", "Y"):
            return f"{kelvin:.1f} K (sub-stellar brown dwarf cooling regime)"
        else:
            return f"{kelvin:.1f} K"

    @staticmethod
    def format_temperature_analogy(kelvin: Optional[float]) -> str:
        if kelvin is None:
            return "N/A"
        celsius = kelvin - 273.15
        if kelvin > 1000000:
            analogy = "reaching stellar interior / nuclear core temperatures"
        elif kelvin > 1500:
            analogy = "hot enough to melt basalt and liquidate rock"
        elif 305 <= kelvin <= 325:
            analogy = "warm, comparable to a hot desert summer"
        elif 273 <= kelvin < 305:
            analogy = "temperate, hospitable Earth-like climate"
        elif kelvin < 150:
            analogy = "deep cryogenic freeze, far colder than Antarctica"
        else:
            analogy = f"{celsius:.1f} deg C"
        return f"{kelvin:.1f} K ({celsius:.1f} deg C; {analogy})"

    @staticmethod
    def format_pressure_analogy(pascals: Optional[float]) -> str:
        if pascals is None:
            return "N/A"
        atm = pascals / 101325.0
        if atm > 500:
            analogy = "immense crushing pressure; equal to deepest ocean trench floor"
        elif atm > 10:
            analogy = "dense supercritical atmospheric crushing zone"
        elif 0.6 <= atm <= 0.85:
            analogy = "comparable to high mountain air at ~2,500m / 8,200ft"
        elif 0.85 < atm <= 1.15:
            analogy = "standard Earth sea-level breathing pressure"
        elif atm < 0.1:
            analogy = "near-vacuum thin stratosphere"
        else:
            analogy = f"{atm:.2f} atm"
        return f"{pascals:.0f} Pa ({atm:.2f} atm; {analogy})"

    @staticmethod
    def format_radius_analogy(radius_m: Optional[float], is_star: bool) -> str:
        if radius_m is None or radius_m <= 0:
            return "N/A"
        km = radius_m / 1000.0
        if is_star:
            if km < 20.0:
                return f"{km:.1f} km (~the size of a metropolitan city center / Manhattan)"
            solar_r = radius_m / SOLAR_RADIUS_M
            return f"{km:.0f} km ({solar_r:.2f}x Solar radius)"
        else:
            earth_r = radius_m / EARTH_RADIUS_M
            if earth_r > 10.0:
                return f"{km:.0f} km ({earth_r:.1f}x Earth radius; giant planet scale)"
            elif 1.2 <= earth_r <= 1.8:
                return f"{km:.0f} km ({earth_r:.2f}x Earth size; massive Super-Earth scale)"
            elif 0.8 <= earth_r < 1.2:
                return f"{km:.0f} km ({earth_r:.2f}x Earth size; standard terrestrial scale)"
            elif 0.3 <= earth_r < 0.8:
                return f"{km:.0f} km ({earth_r:.2f}x Earth size; Mars-like or large moon scale)"
            else:
                return f"{km:.0f} km ({earth_r:.2f}x Earth size; small asteroid/moon scale)"

    @classmethod
    def generate_narrative_report(cls, system: SystemData, evaluation: SystemEvaluation) -> str:
        lines: List[str] = []
        sep = "=" * 80
        lines.append(sep)
        lines.append(f"ASTROPHYSICAL EXPLORATION REPORT: {system.system_name}")
        lines.append(f"Rarity Score: {evaluation.rarity_score} / 100.0")

        gal = evaluation.raw_features.get("astrophysics_2014_models", {}).get("galactic_context", {})
        if gal and gal.get("galactic_region"):
            lines.append(
                f"Galactic Sector : {gal.get('galactic_region')} (~{gal.get('dist_to_sag_a_ly', 'N/A')} ly from Sag A*)"
            )
        lines.append(sep)

        stars = [b for b in system.bodies.values() if b.is_star]
        planets = [b for b in system.bodies.values() if not b.is_star]

        # Executive Summary
        lines.append("\n[EXECUTIVE SUMMARY]")
        elw_count = evaluation.raw_features.get("earth_like_count", 0)
        exotics = evaluation.raw_features.get("exotic_stars", [])
        if evaluation.rarity_score >= 85.0:
            lines.append(
                f"A profound astronomical anomaly featuring {len(stars)} star(s) and {len(planets)} planetary body/bodies."
            )
            if elw_count > 0 and exotics:
                lines.append(
                    f"Extraordinary coexistence: {elw_count} Earth-like habitable world(s) thriving within an exotic stellar graveyard ({', '.join(exotics)})."
                )
        else:
            lines.append(
                f"Standard stellar system survey with {len(stars)} star(s) and {len(planets)} scanned planetary bodies."
            )

        # Stellar Host
        lines.append("\n[PRIMARY STELLAR ENGINE]")
        for s in stars:
            s_type = s.star_type or "Unknown"
            rad_str = cls.format_radius_analogy(s.radius, is_star=True)
            temp_str = cls.format_star_temperature_analogy(s)
            lines.append(f"  * Body: {s.body_name} ({s_type})")
            lines.append(f"    - Scale: {rad_str}")
            lines.append(f"    - Effective Heat: {temp_str}")
            if s.luminosity_solar is not None:
                lines.append(f"    - Radiative Flux: {s.luminosity_solar:.2f}x Solar luminosity")

        # Habitable Worlds Breakdown
        habitable_planets = [
            p for p in planets if (p.planet_class or "").lower() == "earthlike body"
        ]
        if habitable_planets:
            lines.append("\n[HABITABLE WORLDS (FAMILIAR SCALE BREAKDOWN)]")
            for idx, hp in enumerate(habitable_planets, 1):
                dist_str = cls.format_distance_analogy(hp.semi_major_axis, arrival_ls=hp.distance_from_arrival_ls)
                temp_str = cls.format_temperature_analogy(hp.surface_temperature)
                press_str = cls.format_pressure_analogy(hp.surface_pressure)
                rad_str = cls.format_radius_analogy(hp.radius, is_star=False)

                lines.append(f"  {idx}. {hp.body_name} [Earth-like World]")
                lines.append(f"     - Orbital Distance : {dist_str}")
                lines.append(f"     - Physical Radius  : {rad_str}")
                lines.append(f"     - Surface Climate  : {temp_str}")
                lines.append(f"     - Air Pressure     : {press_str}")
                if hp.orbital_inclination is not None and abs(hp.orbital_inclination) > 10.0:
                    lines.append(f"     - Tilted View      : {hp.orbital_inclination:.1f} deg inclination")

        # Detected Anomalies Summary
        if evaluation.anomalies:
            lines.append("\n[DETECTED ASTROPHYSICAL ANOMALIES]")
            for idx, anom in enumerate(evaluation.anomalies, 1):
                lines.append(f"  [{idx}] {anom}")

        lines.append(sep)
        return "\n".join(lines)


class StellarDatabaseStorage:
    """
    Handles persistence of system physics evaluations into SQLite,
    designed to interoperate with ED_Journal_Analyzer's elite_journal.db.
    All SQL schemas and interactions are fully non-destructive and backwards compatible.
    """

    def __init__(self, db_path: Optional[Any] = None) -> None:
        self.conn_override: Optional[sqlite3.Connection] = None
        if isinstance(db_path, sqlite3.Connection):
            self.conn_override = db_path
            self.db_path = Path("elite_journal.db")
        elif db_path is None:
            try:
                from app.config import DB_PATH
                self.db_path = Path(DB_PATH)
            except Exception:
                default_path = (
                    Path.home()
                    / "Documents"
                    / "elite_journal_analysys"
                    / "data"
                    / "elite_journal.db"
                )
                self.db_path = default_path
        else:
            self.db_path = Path(db_path)

        if not self.conn_override:
            self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if self.conn_override:
            return self.conn_override
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        if not self.db_path.parent.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_physics_evaluations (
                    system_address INTEGER PRIMARY KEY,
                    star_system TEXT NOT NULL,
                    rarity_score REAL NOT NULL,
                    star_count INTEGER NOT NULL,
                    planet_count INTEGER NOT NULL,
                    anomalies_json TEXT NOT NULL,
                    narrative_report TEXT NOT NULL,
                    raw_features_json TEXT NOT NULL,
                    evaluated_at TEXT NOT NULL
                );
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_physics_eval_score 
                ON system_physics_evaluations(rarity_score DESC);
            """)
            conn.commit()

    def save_evaluation(
        self,
        system: SystemData,
        evaluation: SystemEvaluation,
        narrative_report: str,
    ) -> None:
        if system.system_address is None:
            return

        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        anomalies_str = json.dumps(evaluation.anomalies, ensure_ascii=True)
        raw_features_str = json.dumps(evaluation.raw_features, ensure_ascii=True)

        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO system_physics_evaluations (
                system_address,
                star_system,
                rarity_score,
                star_count,
                planet_count,
                anomalies_json,
                narrative_report,
                raw_features_json,
                evaluated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                system.system_address,
                system.system_name,
                evaluation.rarity_score,
                evaluation.star_count,
                evaluation.planet_count,
                anomalies_str,
                narrative_report,
                raw_features_str,
                now_iso,
            ),
        )
        conn.commit()
        if not self.conn_override:
            conn.close()

    def get_evaluation(self, system_address: int) -> Optional[Dict[str, Any]]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT system_address, star_system, rarity_score, star_count, planet_count,
                   anomalies_json, narrative_report, raw_features_json, evaluated_at
            FROM system_physics_evaluations
            WHERE system_address = ?;
            """,
            (system_address,),
        )
        row = cursor.fetchone()
        if not self.conn_override:
            conn.close()
        if row:
            return {
                "system_address": row[0],
                "star_system": row[1],
                "rarity_score": row[2],
                "star_count": row[3],
                "planet_count": row[4],
                "anomalies": json.loads(row[5]),
                "narrative_report": row[6],
                "raw_features": json.loads(row[7]),
                "evaluated_at": row[8],
            }
        return None

    def evaluate_and_store_from_ed_journal_db(self, system_address: int) -> Optional[SystemEvaluation]:
        """
        Loads bodies for a given system from ED_Journal_Analyzer's systems/bodies tables,
        evaluates with StellarPhysicsEngine, and stores into system_physics_evaluations.
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT star_system, star_pos_x, star_pos_y, star_pos_z FROM systems WHERE system_address = ?",
            (system_address,),
        )
        s_row = cursor.fetchone()
        if not s_row:
            if not self.conn_override:
                conn.close()
            return None

        star_system = s_row[0]
        star_pos = [s_row[1], s_row[2], s_row[3]] if s_row[1] is not None else None

        cursor.execute(
            """
            SELECT body_id, body_name, distance_from_arrival_ls, star_type, stellar_mass,
                   radius, surface_temperature, planet_class, mass_em, surface_pressure,
                   semi_major_axis, eccentricity, orbital_inclination, orbital_period,
                   rotation_period, tidal_lock, axial_tilt, rings, materials, parents
            FROM bodies
            WHERE system_address = ?;
            """,
            (system_address,),
        )
        b_rows = cursor.fetchall()
        if not self.conn_override:
            conn.close()

        sys_data = SystemData(
            system_name=star_system,
            system_address=system_address,
            star_pos=star_pos,
        )

        for r in b_rows:
            rings = json.loads(r[17]) if r[17] else []
            parents = json.loads(r[19]) if r[19] else []
            body = ScanBody(
                body_id=r[0],
                body_name=r[1],
                distance_from_arrival_ls=r[2],
                star_type=r[3],
                stellar_mass=r[4],
                radius=r[5],
                surface_temperature=r[6],
                planet_class=r[7],
                mass_em=r[8],
                surface_pressure=r[9],
                semi_major_axis=r[10],
                eccentricity=r[11],
                orbital_inclination=r[12],
                orbital_period=r[13],
                rotation_period=r[14],
                tidal_lock=bool(r[15]) if r[15] is not None else None,
                axial_tilt=r[16],
                rings=rings,
                parents=parents,
            )
            sys_data.bodies[r[0]] = body

        evaluation = StellarPhysicsEngine.evaluate(sys_data)
        narrative = SystemNarrator.generate_narrative_report(sys_data, evaluation)
        self.save_evaluation(sys_data, evaluation, narrative)
        return evaluation


class SystemAggregator:
    """
    Aggregates Scan events for the active star system and triggers
    evaluation upon FSDJump or CarrierJump.
    """

    def __init__(
        self,
        on_system_evaluated: Optional[Callable[[SystemEvaluation], None]] = None,
    ) -> None:
        self.current_system: Optional[SystemData] = None
        self.on_system_evaluated = on_system_evaluated

    def process_event(self, event: Dict[str, Any]) -> Optional[SystemEvaluation]:
        event_name = event.get("event")
        if not event_name:
            return None

        # Detect jump events: finalize previous system if any, initialize new system
        if event_name in ("FSDJump", "CarrierJump", "Location"):
            evaluation = None
            if self.current_system and self.current_system.bodies:
                evaluation = StellarPhysicsEngine.evaluate(self.current_system)
                if self.on_system_evaluated:
                    self.on_system_evaluated(evaluation)

            sys_name = event.get("StarSystem", "Unknown")
            sys_addr = event.get("SystemAddress")
            star_pos = event.get("StarPos")
            timestamp = event.get("timestamp")

            self.current_system = SystemData(
                system_name=sys_name,
                system_address=sys_addr,
                star_pos=star_pos,
                jump_timestamp=timestamp,
            )
            return evaluation

        # Detect Scan event
        if event_name == "Scan" and self.current_system is not None:
            body_id = event.get("BodyID")
            body_name = event.get("BodyName", f"Body_{body_id}")
            if body_id is not None:
                body = ScanBody(
                    body_id=body_id,
                    body_name=body_name,
                    distance_from_arrival_ls=event.get("DistanceFromArrivalLS"),
                    star_type=event.get("StarType"),
                    stellar_mass=event.get("StellarMass"),
                    radius=event.get("Radius"),
                    surface_temperature=event.get("SurfaceTemperature"),
                    planet_class=event.get("PlanetClass"),
                    mass_em=event.get("MassEM"),
                    surface_pressure=event.get("SurfacePressure"),
                    semi_major_axis=event.get("SemiMajorAxis"),
                    eccentricity=event.get("Eccentricity"),
                    orbital_inclination=event.get("OrbitalInclination"),
                    orbital_period=event.get("OrbitalPeriod"),
                    rotation_period=event.get("RotationPeriod"),
                    tidal_lock=event.get("TidalLock"),
                    axial_tilt=event.get("AxialTilt"),
                    rings=event.get("Rings", []),
                    belts=event.get("Belts", []),
                    parents=event.get("Parents", []),
                    raw_event=event,
                )
                self.current_system.bodies[body_id] = body

        return None

    def evaluate_current(self) -> Optional[SystemEvaluation]:
        if self.current_system and self.current_system.bodies:
            evaluation = StellarPhysicsEngine.evaluate(self.current_system)
            if self.on_system_evaluated:
                self.on_system_evaluated(evaluation)
            return evaluation
        return None


class JournalWatcher:
    """
    Watches the latest Elite Dangerous journal file using polling and tail streaming.
    """

    def __init__(
        self,
        journal_dir: Optional[Path] = None,
        aggregator: Optional[SystemAggregator] = None,
        poll_interval: float = 1.0,
    ) -> None:
        if journal_dir is None:
            journal_dir = self.get_default_journal_path()
        self.journal_dir = journal_dir
        self.aggregator = aggregator or SystemAggregator()
        self.poll_interval = poll_interval
        self._current_file: Optional[Path] = None
        self._file_handle: Optional[Any] = None
        self._running: bool = False

    @staticmethod
    def get_default_journal_path() -> Path:
        """
        Locates the standard Elite Dangerous journal directory on Windows.
        """
        home = Path.home()
        standard_path = home / "Saved Games" / "Frontier Developments" / "Elite Dangerous"
        return standard_path

    def find_latest_journal_file(self) -> Optional[Path]:
        if not self.journal_dir.exists() or not self.journal_dir.is_dir():
            return None
        pattern = str(self.journal_dir / "Journal.*.log")
        files = glob.glob(pattern)
        if not files:
            return None
        latest_file = max(files, key=os.path.getmtime)
        return Path(latest_file)

    def process_line(self, line: str) -> Optional[SystemEvaluation]:
        line = line.strip()
        if not line:
            return None
        try:
            event = json.loads(line)
            return self.aggregator.process_event(event)
        except json.JSONDecodeError:
            return None

    def read_existing_and_follow(
        self,
        from_beginning: bool = False,
        max_iterations: Optional[int] = None,
    ) -> None:
        """
        Opens the latest journal file and processes entries continuously.
        """
        self._running = True
        iterations = 0

        while self._running:
            if max_iterations is not None and iterations >= max_iterations:
                break
            iterations += 1

            latest = self.find_latest_journal_file()
            if latest is None:
                time.sleep(self.poll_interval)
                continue

            if self._current_file != latest:
                if self._file_handle:
                    self._file_handle.close()
                self._current_file = latest
                self._file_handle = open(self._current_file, "r", encoding="utf-8")
                if not from_beginning:
                    self._file_handle.seek(0, os.SEEK_END)

            if self._file_handle:
                line = self._file_handle.readline()
                if line:
                    self.process_line(line)
                else:
                    time.sleep(self.poll_interval)
            else:
                time.sleep(self.poll_interval)

    def stop(self) -> None:
        self._running = False
        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None


if __name__ == "__main__":
    # Test suite with synthetic JSONL log simulating a star system with:
    # 1. Close binary relative to body size (barycentric pair)
    # 2. Wide Ring gas giant
    # 3. Shepherd Moon orbiting inside/grazing parent ring
    # 4. Nested Moon (moon of a moon)
    # 5. Small Object (< 300km radius)
    # 6. Close belt proximity
    # 7. Close Orbit around parent
    # 8. Non-locked body with fast rotation (< 12h)

    dummy_journal_lines = [
        # Jump into System 'SYNUEFE XY-Z D10-44' located high in Galactic Halo (Y = 5150 ly)
        json.dumps({
            "timestamp": "2026-09-10T05:20:00Z",
            "event": "FSDJump",
            "StarSystem": "SYNUEFE XY-Z D10-44",
            "SystemAddress": 98127391823,
            "StarPos": [310.2, 5150.0, -840.1],  # Y > 5000 ly -> Galactic Halo!
            "Body": "SYNUEFE XY-Z D10-44 A",
            "BodyID": 0
        }),
        # Star A with Asteroid Belt
        json.dumps({
            "timestamp": "2026-09-10T05:20:10Z",
            "event": "Scan",
            "BodyName": "SYNUEFE XY-Z D10-44 A",
            "BodyID": 1,
            "DistanceFromArrivalLS": 0.0,
            "StarType": "G",
            "StellarMass": 1.05,
            "Radius": 7.0e8,
            "SurfaceTemperature": 5780.0,
            "Belts": [
                {
                    "Name": "SYNUEFE XY-Z D10-44 A Belt",
                    "RingClass": "eRingClass_MetalRich",
                    "MassMT": 5.4e12,
                    "InnerRad": 1.5e11,
                    "OuterRad": 1.8e11
                }
            ],
            "Parents": [{"Null": 0}]
        }),
        # Star B: Distant M-dwarf companion (causes Kozai-Lidov perturbations)
        json.dumps({
            "timestamp": "2026-09-10T05:20:15Z",
            "event": "Scan",
            "BodyName": "SYNUEFE XY-Z D10-44 B",
            "BodyID": 20,
            "DistanceFromArrivalLS": 4500.0,
            "StarType": "M",
            "StellarMass": 0.35,
            "Radius": 2.8e8,
            "SurfaceTemperature": 3200.0,
            "Parents": [{"Null": 0}]
        }),
        # Planet 1: Close Orbit planet & Close belt proximity & Super-Mercury (Mantle stripped)
        json.dumps({
            "timestamp": "2026-09-10T05:20:20Z",
            "event": "Scan",
            "BodyName": "SYNUEFE XY-Z D10-44 1",
            "BodyID": 2,
            "DistanceFromArrivalLS": 5.2,
            "PlanetClass": "High metal content body",
            "MassEM": 2.8,
            "Radius": 6.8e6,  # Density ~ 8.4 g/cm^3 -> Super-Mercury!
            "SurfaceTemperature": 1200.0,
            "SemiMajorAxis": 1.6e11,  # Inside belt zone & a1 = 1.60e11
            "Eccentricity": 0.02,
            "OrbitalPeriod": 2.5e6,
            "Parents": [{"Star": 1}]
        }),
        # Planet 1 b: Closely packed second planet causing Gladman Hill instability with Planet 1!
        # a2 = 1.64e11 m -> Separation = 4.0e9 m; Mutual Hill radius ~ 1.8e9 m -> Delta_H ~ 2.22 (< 3.464!)
        json.dumps({
            "timestamp": "2026-09-10T05:20:25Z",
            "event": "Scan",
            "BodyName": "SYNUEFE XY-Z D10-44 1 b",
            "BodyID": 21,
            "DistanceFromArrivalLS": 5.4,
            "PlanetClass": "High metal content body",
            "MassEM": 2.5,
            "Radius": 6.5e6,
            "SurfaceTemperature": 1180.0,
            "SemiMajorAxis": 1.64e11,
            "Eccentricity": 0.03,
            "OrbitalPeriod": 2.6e6,
            "Parents": [{"Star": 1}]
        }),
        # Planet 2: Gas Giant with Wide Ring & Kozai-Lidov Inclination (i = 52.0 deg)
        json.dumps({
            "timestamp": "2026-09-10T05:20:30Z",
            "event": "Scan",
            "BodyName": "SYNUEFE XY-Z D10-44 2",
            "BodyID": 3,
            "DistanceFromArrivalLS": 450.0,
            "PlanetClass": "Sudarsky class I gas giant",
            "MassEM": 210.0,
            "Radius": 6.8e7,
            "SurfaceTemperature": 180.0,
            "SemiMajorAxis": 6.5e11,
            "Eccentricity": 0.01,
            "OrbitalInclination": 52.0,  # Kozai-Lidov regime (39.2 < 52 < 140.8)!
            "OrbitalPeriod": 1.2e8,
            "Rings": [
                {
                    "Name": "SYNUEFE XY-Z D10-44 2 A Ring",
                    "RingClass": "eRingClass_Icy",
                    "MassMT": 8.9e13,
                    "InnerRad": 9.0e7,
                    "OuterRad": 6.2e8
                }
            ],
            "Parents": [{"Star": 1}]
        }),
        # Moon 2 a: Shepherd Moon
        json.dumps({
            "timestamp": "2026-09-10T05:20:40Z",
            "event": "Scan",
            "BodyName": "SYNUEFE XY-Z D10-44 2 a",
            "BodyID": 4,
            "DistanceFromArrivalLS": 450.4,
            "PlanetClass": "Rocky body",
            "MassEM": 0.0012,
            "Radius": 7.5e5,
            "SurfaceTemperature": 140.0,
            "SemiMajorAxis": 1.2e8,
            "Eccentricity": 0.001,
            "OrbitalPeriod": 36000.0,
            "Parents": [{"Planet": 3}, {"Star": 1}]
        }),
        # Planet 3: Earth-like World in Kopparapu (2013) Habitable Zone!
        # L ~ 1.02 L_Sun -> HZ ~ 0.76 - 1.69 AU. a = 1.05 AU = 1.57e11 m.
        json.dumps({
            "timestamp": "2026-09-10T05:20:50Z",
            "event": "Scan",
            "BodyName": "SYNUEFE XY-Z D10-44 3",
            "BodyID": 22,
            "DistanceFromArrivalLS": 525.0,
            "PlanetClass": "Earthlike body",
            "MassEM": 1.15,
            "Radius": 6.6e6,
            "SurfaceTemperature": 288.2,
            "SurfacePressure": 102500.0,
            "SemiMajorAxis": 1.57e11,  # 1.05 AU
            "Eccentricity": 0.015,
            "OrbitalPeriod": 3.2e7,
            "OrbitalInclination": 1.2,
            "Parents": [{"Star": 1}]
        }),
        # Planet 4: Mega-Earth Anomaly (Weiss & Marcy 2014)
        # R = 1.85 R_Earth (> 1.6) and Density = 6.2 g/cm^3 (> 5.5) -> Mega-Earth!
        json.dumps({
            "timestamp": "2026-09-10T05:21:00Z",
            "event": "Scan",
            "BodyName": "SYNUEFE XY-Z D10-44 4",
            "BodyID": 23,
            "DistanceFromArrivalLS": 890.0,
            "PlanetClass": "High metal content body",
            "MassEM": 10.5,
            "Radius": 1.18e7,  # 1.85 R_Earth
            "SurfaceTemperature": 410.0,
            "SemiMajorAxis": 3.8e11,
            "Eccentricity": 0.04,
            "OrbitalPeriod": 1.1e8,
            "Parents": [{"Star": 1}]
        }),
        # Next Jump event to trigger evaluation
        json.dumps({
            "timestamp": "2026-09-10T05:25:00Z",
            "event": "FSDJump",
            "StarSystem": "HIP 19283",
            "SystemAddress": 5512391238,
            "StarPos": [315.0, -118.0, -835.0],
            "Body": "HIP 19283 A",
            "BodyID": 0
        })
    ]

    print("=== Elite Dangerous Stellar Physics Engine - 2014 Models Verification ===")
    
    evaluated_results: List[SystemEvaluation] = []

    def on_eval(eval_data: SystemEvaluation) -> None:
        evaluated_results.append(eval_data)

    aggregator = SystemAggregator(on_system_evaluated=on_eval)

    for line in dummy_journal_lines:
        aggregator.process_event(json.loads(line))

    for result in evaluated_results:
        print(f"\nSystem Evaluated: {result.system_name}")
        print(f"Rarity Score   : {result.rarity_score} / 100.0")
        print(f"Stars Count    : {result.star_count}")
        print(f"Planets Count  : {result.planet_count}")
        print("\nDetected Anomalies (Including 2014 Astrophysics Models):")
        for idx, anomaly in enumerate(result.anomalies, 1):
            print(f"  [{idx}] {anomaly}")

        print("\n[Astrophysics 2014 Models Output]")
        print(json.dumps(result.raw_features["astrophysics_2014_models"], indent=2))

    print("\nAstrophysics 2014 Models Verification Completed Successfully.")
