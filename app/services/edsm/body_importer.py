"""
EDSM Celestial Bodies Importer.
Extracts star types, calculates exploration values, detects anomalies and exobiology,
and inserts/updates bodies into SQLite.
"""

import json
from typing import Optional, List, Dict, Any

from app.parser.value_calculator import calculate_body_value, STAR_VALUES
from app.analyzer.anomaly_finder import detect_anomalies
from app.parser.exobiology import predict_exobiology_candidates


def extract_star_type(b: dict) -> str:
    """Extract standard Elite star type code matching STAR_VALUES from EDSM body data."""
    subtype = b.get("subType", "") or ""
    sub_lower = subtype.lower()

    if "supermassive" in sub_lower and "black hole" in sub_lower:
        return "SupermassiveBlackHole"
    if "black hole" in sub_lower:
        return "H"
    if "neutron" in sub_lower:
        return "N"
    if "white dwarf" in sub_lower:
        for wd in ["DA", "DAB", "DAO", "DAZ", "DAV", "DB", "DBZ", "DBV", "DO", "DOV", "DQ", "DC", "DCV", "DX", "D"]:
            if f"({wd.lower()})" in sub_lower or f" {wd.lower()} " in f" {sub_lower} ":
                return wd
        return "D"

    spec = b.get("spectralClass")
    if spec and spec in STAR_VALUES:
        return spec

    # Token-based match (e.g. "M (Red dwarf) Star" -> "M", "TTS (T Tauri) Star" -> "TTS")
    token = subtype.split()[0] if subtype else "M"
    token_clean = token.split("(")[0].strip()
    if token_clean in STAR_VALUES:
        return token_clean

    return spec or "M"


def import_and_complete_bodies(conn, system_address: int, star_system: str, bodies_list: list) -> int:
    """
    Completes missing celestial bodies from EDSM for known systems where player
    did not receive FSS Scan journal events. Respects and preserves any existing
    player-scanned records (AutoScan, Detailed, NavBeacon).
    Returns number of completed/imported bodies.
    """
    c = conn.cursor()
    completed_count = 0

    # Query existing bodies for this system
    c.execute("SELECT id, body_id, body_name, scan_type, scan_timestamp FROM bodies WHERE system_address = ?", (system_address,))
    existing_rows = c.fetchall()
    existing_by_name = {r["body_name"]: dict(r) for r in existing_rows}
    existing_by_id = {r["body_id"]: dict(r) for r in existing_rows if r["body_id"] is not None}

    for b in bodies_list:
        b_name = b.get("name")
        b_id = b.get("bodyId")
        if not b_name:
            continue

        disc = b.get("discovery") or {}
        discoverer = disc.get("commander")
        discovered_at = disc.get("date")

        existing = existing_by_name.get(b_name) or (existing_by_id.get(b_id) if b_id is not None else None)

        # If body already exists and was scanned by player, preserve local data and only update discoverer
        if existing and existing.get("scan_type") and existing.get("scan_type") != "EDSM_Known":
            if discoverer:
                c.execute("""
                    UPDATE bodies SET
                        edsm_discovered_by = ?,
                        edsm_discovered_at = ?
                    WHERE id = ?
                """, (discoverer, discovered_at, existing["id"]))
            continue

        # Determine whether this body is a star or planet
        b_type = (b.get("type") or "").strip()
        subtype = (b.get("subType") or "").strip()
        is_star = (b_type.lower() == "star") or ("star" in subtype.lower() and "gas giant" not in subtype.lower())

        dist_ls = b.get("distanceToArrival")
        semi_major_m = (b.get("semiMajorAxis") * 149597870700.0) if b.get("semiMajorAxis") is not None else None
        eccentricity = b.get("orbitalEccentricity")
        inclination = b.get("orbitalInclination")
        periapsis = b.get("argOfPeriapsis")
        orbital_period_s = (b.get("orbitalPeriod") * 86400.0) if b.get("orbitalPeriod") is not None else None
        rotation_period_s = (b.get("rotationalPeriod") * 86400.0) if b.get("rotationalPeriod") is not None else None
        axial_tilt = b.get("axialTilt")

        parents_json = json.dumps(b.get("parents")) if b.get("parents") else None
        rings_json = json.dumps(b.get("belts") or b.get("rings")) if (b.get("belts") or b.get("rings")) else None
        materials_json = json.dumps(b.get("materials")) if b.get("materials") else None

        if is_star:
            star_type = extract_star_type(b)
            planet_class = None
            stellar_mass = b.get("solarMasses") or 1.0
            radius_m = (b.get("solarRadius") * 696340000.0) if b.get("solarRadius") else ((b.get("radius") * 1000.0) if b.get("radius") else None)
            surface_temp = b.get("surfaceTemperature")
            abs_mag = b.get("absoluteMagnitude")
            luminosity = b.get("spectralClass")
            mass_em = None
            gravity_g = None
            gravity_raw = None
            surface_pressure = None
            landable = 0
            volcanism = None
            atmosphere = None
            atmosphere_type = None
            terraforming = None
            calc_arg = {"star_type": star_type, "stellar_mass": stellar_mass}
        else:
            star_type = None
            luminosity = None
            stellar_mass = None
            abs_mag = None
            planet_class = subtype or "Icy body"
            radius_m = (b.get("radius") * 1000.0) if b.get("radius") is not None else None
            surface_temp = b.get("surfaceTemperature")
            mass_em = b.get("earthMasses")
            g_val = b.get("gravity")
            gravity_g = round(g_val, 4) if g_val is not None else None
            gravity_raw = (g_val * 9.80665) if g_val is not None else None
            p_val = b.get("surfacePressure")
            surface_pressure = (p_val * 101325.0) if p_val is not None else None
            landable = 1 if b.get("isLandable") else 0
            volcanism = b.get("volcanismType")
            atmosphere = b.get("atmosphereType")
            atmosphere_type = b.get("atmosphereType")
            terraforming = b.get("terraformingState")
            calc_arg = {
                "planet_class": planet_class,
                "mass_em": mass_em or 0.001,
                "terraforming_state": terraforming
            }

        # Value calculation
        val_res = calculate_body_value(calc_arg)
        fss_val = val_res.get("fss_value", 0)
        dss_val = val_res.get("dss_value", 0)
        fd_fss = val_res.get("first_discovered_fss", 0)
        fm_dss = val_res.get("first_mapped_dss", 0)
        max_pot = val_res.get("max_potential_value", 0)

        # Anomaly & Exobiology detection
        anomaly_arg = {
            "body_name": b_name,
            "star_system": star_system,
            "star_type": star_type,
            "planet_class": planet_class,
            "distance_from_arrival_ls": dist_ls,
            "semi_major_axis": semi_major_m,
            "orbital_period": orbital_period_s,
            "rotation_period": rotation_period_s,
            "eccentricity": eccentricity,
            "orbital_inclination": inclination,
            "landable": landable,
            "surface_gravity_g": gravity_g,
            "rings": rings_json,
            "volcanism": volcanism,
            "terraforming_state": terraforming,
            "parents": parents_json
        }
        anomalies = detect_anomalies(anomaly_arg)
        anomalies_json = json.dumps(anomalies)

        # Exobiology predictions
        bio_preds = []
        if not is_star and (atmosphere or landable):
            bio_preds = predict_exobiology_candidates(anomaly_arg)
        bio_pred_json = json.dumps(bio_preds)

        if existing:
            # Update existing EDSM_Known record
            c.execute("""
                UPDATE bodies SET
                    body_id = COALESCE(?, body_id),
                    body_name = ?,
                    star_system = ?,
                    distance_from_arrival_ls = ?,
                    star_type = ?,
                    luminosity = ?,
                    stellar_mass = ?,
                    absolute_magnitude = ?,
                    radius = ?,
                    surface_temperature = ?,
                    planet_class = ?,
                    atmosphere = ?,
                    atmosphere_type = ?,
                    mass_em = ?,
                    surface_gravity = ?,
                    surface_gravity_g = ?,
                    surface_pressure = ?,
                    landable = ?,
                    volcanism = ?,
                    terraforming_state = ?,
                    semi_major_axis = ?,
                    eccentricity = ?,
                    orbital_inclination = ?,
                    periapsis = ?,
                    orbital_period = ?,
                    rotation_period = ?,
                    axial_tilt = ?,
                    rings = ?,
                    materials = ?,
                    parents = ?,
                    was_discovered = 1,
                    was_mapped = CASE WHEN ? IS NOT NULL THEN 1 ELSE was_mapped END,
                    edsm_discovered_by = ?,
                    edsm_discovered_at = ?,
                    fss_value = ?,
                    dss_value = ?,
                    first_discovered_fss = ?,
                    first_mapped_dss = ?,
                    max_potential_value = ?,
                    anomalies_json = ?,
                    exobiology_predictions = ?
                WHERE id = ?
            """, (
                b_id, b_name, star_system, dist_ls,
                star_type, luminosity, stellar_mass, abs_mag, radius_m, surface_temp,
                planet_class, atmosphere, atmosphere_type,
                mass_em, gravity_raw, gravity_g, surface_pressure, landable,
                volcanism, terraforming, semi_major_m, eccentricity,
                inclination, periapsis, orbital_period_s, rotation_period_s,
                axial_tilt, rings_json, materials_json, parents_json,
                discoverer, discoverer, discovered_at,
                fss_val, dss_val, fd_fss, fm_dss, max_pot,
                anomalies_json, bio_pred_json, existing["id"]
            ))
            completed_count += 1
        else:
            # Insert new EDSM_Known body
            c.execute("""
                INSERT INTO bodies (
                    system_address, body_id, body_name, star_system,
                    distance_from_arrival_ls, star_type, luminosity, stellar_mass,
                    absolute_magnitude, radius, surface_temperature, planet_class,
                    atmosphere, atmosphere_type, mass_em, surface_gravity,
                    surface_gravity_g, surface_pressure, landable, volcanism,
                    terraforming_state, semi_major_axis, eccentricity,
                    orbital_inclination, periapsis, orbital_period, rotation_period,
                    axial_tilt, rings, materials, parents, was_discovered, was_mapped,
                    scan_type, edsm_discovered_by, edsm_discovered_at,
                    fss_value, dss_value, first_discovered_fss, first_mapped_dss,
                    max_potential_value, anomalies_json, exobiology_predictions
                ) VALUES (
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?, 1, ?,
                    'EDSM_Known', ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?
                )
            """, (
                system_address, b_id, b_name, star_system,
                dist_ls, star_type, luminosity, stellar_mass,
                abs_mag, radius_m, surface_temp, planet_class,
                atmosphere, atmosphere_type, mass_em, gravity_raw,
                gravity_g, surface_pressure, landable, volcanism,
                terraforming, semi_major_m, eccentricity,
                inclination, periapsis, orbital_period_s, rotation_period_s,
                axial_tilt, rings_json, materials_json, parents_json,
                1 if discoverer else 0,
                discoverer, discovered_at,
                fss_val, dss_val, fd_fss, fm_dss,
                max_pot, anomalies_json, bio_pred_json
            ))
            completed_count += 1

    return completed_count
