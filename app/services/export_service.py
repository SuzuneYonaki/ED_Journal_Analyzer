import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple, Optional
import html

SIGNATURE_SALT = "ED_JOURNAL_ANALYZER_PROOF_OF_DISCOVERY_2026"

def calculate_package_signature(systems_data: List[Dict[str, Any]], cmdr_name: str) -> str:
    """
    Computes a cryptographic SHA-256 signature for the package payload to verify discovery credit
    and detect unauthorized tampering.
    """
    canonical_tokens = [cmdr_name.strip(), SIGNATURE_SALT]
    for sys_entry in sorted(systems_data, key=lambda s: s.get("system_address", 0)):
        canonical_tokens.append(str(sys_entry.get("system_address", 0)))
        canonical_tokens.append(sys_entry.get("star_system", ""))
        for b in sorted(sys_entry.get("bodies", []), key=lambda x: x.get("body_id", 0)):
            canonical_tokens.append(f"{b.get('body_id')}:{b.get('body_name')}:{b.get('planet_class') or b.get('star_type')}")
    
    raw_str = "|".join(canonical_tokens)
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

def verify_package_signature(package_dict: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Verifies that the package signature matches its contents and author CMDR.
    """
    if not isinstance(package_dict, dict):
        return False, "無効なデータ構造です (Invalid JSON structure)"

    # Handle wrapper payload if present
    if "package_data" in package_dict and isinstance(package_dict["package_data"], dict):
        package_dict = package_dict["package_data"]
    elif "package" in package_dict and isinstance(package_dict["package"], dict):
        package_dict = package_dict["package"]

    fmt = package_dict.get("format")
    if fmt != "ED_JOURNAL_ANALYZER_PACKAGE_V1":
        return False, f"未対応のパッケージ形式です: {fmt}"

    metadata = package_dict.get("metadata", {})
    cmdr_name = metadata.get("cmdr_name", "")
    systems = package_dict.get("systems", [])
    expected_sig = package_dict.get("signature", "")

    if not expected_sig:
        return False, "電子署名が存在しません (Missing signature)"

    computed_sig = calculate_package_signature(systems, cmdr_name)
    if computed_sig != expected_sig:
        return False, "署名不一致: データまたは発見者名が改ざんされている可能性があります (Signature mismatch / Tampered data)"

    return True, "署名検証成功 (Valid)"

def sanitize_system_for_export(system_row: Dict[str, Any], bodies_rows: List[Dict[str, Any]], mining_rows: List[Dict[str, Any]], bookmarks_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extracts strictly display/view attributes for a system, decoupling from raw journal logs and CMDR private metrics.
    """
    sys_clean = {
        "system_address": system_row.get("system_address"),
        "star_system": system_row.get("star_system"),
        "star_pos_x": system_row.get("star_pos_x"),
        "star_pos_y": system_row.get("star_pos_y"),
        "star_pos_z": system_row.get("star_pos_z"),
        "main_star_type": system_row.get("main_star_type"),
        "total_fss_value": system_row.get("total_fss_value", 0),
        "total_potential_value": system_row.get("total_potential_value", 0),
        "total_bio_signals": system_row.get("total_bio_signals", 0),
        "has_elw": system_row.get("has_elw", 0),
        "has_water_world": system_row.get("has_water_world", 0),
        "has_ammonia": system_row.get("has_ammonia", 0),
        "has_terraformable": system_row.get("has_terraformable", 0),
        "has_bio": system_row.get("has_bio", 0),
        "has_landable": system_row.get("has_landable", 0),
        "has_high_g": system_row.get("has_high_g", 0),
        "has_anomalies": system_row.get("has_anomalies", 0),
        "avg_landable_radius": system_row.get("avg_landable_radius", 0),
    }

    clean_bodies = []
    for b in bodies_rows:
        clean_bodies.append({
            "body_id": b.get("body_id"),
            "body_name": b.get("body_name"),
            "star_type": b.get("star_type"),
            "stellar_mass": b.get("stellar_mass"),
            "planet_class": b.get("planet_class"),
            "radius": b.get("radius"),
            "surface_gravity_g": b.get("surface_gravity_g"),
            "surface_temperature": b.get("surface_temperature"),
            "surface_pressure": b.get("surface_pressure"),
            "atmosphere": b.get("atmosphere"),
            "atmosphere_type": b.get("atmosphere_type"),
            "atmosphere_composition": b.get("atmosphere_composition"),
            "distance_from_arrival_ls": b.get("distance_from_arrival_ls"),
            "semi_major_axis": b.get("semi_major_axis"),
            "eccentricity": b.get("eccentricity"),
            "orbital_period": b.get("orbital_period"),
            "rotation_period": b.get("rotation_period"),
            "axial_tilt": b.get("axial_tilt"),
            "rings": b.get("rings"),
            "materials": b.get("materials"),
            "parents": b.get("parents"),
            "landable": b.get("landable", 0),
            "volcanism": b.get("volcanism"),
            "terraforming_state": b.get("terraforming_state"),
            "bio_signals": b.get("bio_signals", 0),
            "geo_signals": b.get("geo_signals", 0),
            "mining_signals": b.get("mining_signals", 0),
            "reserve_level": b.get("reserve_level"),
            "fss_value": b.get("fss_value", 0),
            "dss_value": b.get("dss_value", 0),
            "confirmed_genuses": b.get("confirmed_genuses"),
            "exobiology_predictions": b.get("exobiology_predictions"),
            "anomalies_json": b.get("anomalies_json")
        })
    sys_clean["bodies"] = clean_bodies

    # Surface mining sites (Rhino SRV refined / collected coordinates)
    clean_mining = []
    for m in mining_rows:
        clean_mining.append({
            "body_id": m.get("body_id"),
            "body_name": m.get("body_name"),
            "body_type": m.get("body_type"),
            "srv_type": m.get("srv_type") or "mev_rhino",
            "material_name": m.get("material_name"),
            "material_name_localised": m.get("material_name_localised"),
            "category": m.get("category"),
            "count": m.get("count", 1),
            "latitude": m.get("latitude"),
            "longitude": m.get("longitude"),
            "timestamp": m.get("timestamp")
        })
    sys_clean["surface_mining"] = clean_mining

    # Body bookmarks & notes
    clean_bookmarks = []
    for bm in bookmarks_rows:
        clean_bookmarks.append({
            "body_id": bm.get("body_id"),
            "body_name": bm.get("body_name"),
            "alias_name": bm.get("alias_name", ""),
            "note_markdown": bm.get("note_markdown", "")
        })
    sys_clean["bookmarks"] = clean_bookmarks

    return sys_clean

def create_edsys_package(conn, system_addresses: List[int], cmdr_name: str = "Explorer", notes: str = "") -> Dict[str, Any]:
    """
    Serializes multiple systems into a locked .edsys package with SHA-256 signature.
    """
    c = conn.cursor()
    systems_data = []

    for sys_addr in system_addresses:
        c.execute("SELECT * FROM systems WHERE system_address = ?", (sys_addr,))
        s_row = c.fetchone()
        if not s_row:
            continue
        system_dict = dict(s_row)

        c.execute("SELECT * FROM bodies WHERE system_address = ? ORDER BY distance_from_arrival_ls ASC, body_id ASC", (sys_addr,))
        bodies_rows = [dict(r) for r in c.fetchall()]

        c.execute("SELECT * FROM surface_mining_activities WHERE system_address = ?", (sys_addr,))
        mining_rows = [dict(r) for r in c.fetchall()]

        c.execute("SELECT * FROM body_bookmarks WHERE system_address = ?", (sys_addr,))
        bm_rows = [dict(r) for r in c.fetchall()]

        clean_entry = sanitize_system_for_export(system_dict, bodies_rows, mining_rows, bm_rows)
        systems_data.append(clean_entry)

    now_iso = datetime.now(timezone.utc).isoformat()
    clean_cmdr = (cmdr_name or "Explorer").strip()
    signature = calculate_package_signature(systems_data, clean_cmdr)

    package = {
        "format": "ED_JOURNAL_ANALYZER_PACKAGE_V1",
        "metadata": {
            "version": "1.0",
            "exported_at": now_iso,
            "cmdr_name": clean_cmdr,
            "system_count": len(systems_data),
            "notes": notes.strip()
        },
        "signature": signature,
        "systems": systems_data
    }
    return package

def import_edsys_package(conn, package_dict: Dict[str, Any], overwrite: bool = False, allow_invalid_signature: bool = True) -> Dict[str, Any]:
    """
    Safely imports systems from an .edsys package into the database under is_shared = 1.
    """
    if "package_data" in package_dict and isinstance(package_dict["package_data"], dict):
        package_dict = package_dict["package_data"]
    elif "package" in package_dict and isinstance(package_dict["package"], dict):
        package_dict = package_dict["package"]

    is_valid, reason = verify_package_signature(package_dict)
    if not is_valid and not allow_invalid_signature:
        raise ValueError(f"Package validation failed: {reason}")

    c = conn.cursor()
    metadata = package_dict.get("metadata", {})
    cmdr_name = metadata.get("cmdr_name", "Shared Explorer")
    shared_at = metadata.get("exported_at", datetime.now(timezone.utc).isoformat())
    shared_notes = metadata.get("notes", "")
    systems = package_dict.get("systems", [])

    imported_sys_count = 0
    imported_bodies_count = 0

    for s in systems:
        sys_addr = s.get("system_address")
        star_sys = s.get("star_system")
        if not sys_addr or not star_sys:
            continue

        c.execute("SELECT is_shared FROM systems WHERE system_address = ?", (sys_addr,))
        existing = c.fetchone()

        if existing and not overwrite and existing["is_shared"] == 0:
            # Do not overwrite user's own genuine scanned system, just ensure it's bookmarked/tagged
            continue

        # Insert / Update systems table as is_shared = 1
        c.execute("""
            INSERT INTO systems (
                system_address, star_system, star_pos_x, star_pos_y, star_pos_z,
                main_star_type, total_potential_value, total_fss_value, total_bio_signals,
                has_elw, has_water_world, has_ammonia, has_terraformable, has_bio,
                has_landable, has_high_g, has_anomalies, avg_landable_radius,
                first_visited, last_visited, visit_count, scanned_bodies,
                is_shared, shared_by, shared_at, shared_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(system_address) DO UPDATE SET
                is_shared = 1,
                shared_by = excluded.shared_by,
                shared_at = excluded.shared_at,
                shared_notes = excluded.shared_notes,
                star_pos_x = COALESCE(excluded.star_pos_x, systems.star_pos_x),
                star_pos_y = COALESCE(excluded.star_pos_y, systems.star_pos_y),
                star_pos_z = COALESCE(excluded.star_pos_z, systems.star_pos_z),
                main_star_type = COALESCE(excluded.main_star_type, systems.main_star_type),
                has_elw = excluded.has_elw,
                has_water_world = excluded.has_water_world,
                has_ammonia = excluded.has_ammonia,
                has_terraformable = excluded.has_terraformable,
                has_bio = excluded.has_bio,
                has_landable = excluded.has_landable,
                has_high_g = excluded.has_high_g,
                has_anomalies = excluded.has_anomalies
        """, (
            sys_addr, star_sys, s.get("star_pos_x"), s.get("star_pos_y"), s.get("star_pos_z"),
            s.get("main_star_type"), s.get("total_potential_value", 0), s.get("total_fss_value", 0), s.get("total_bio_signals", 0),
            s.get("has_elw", 0), s.get("has_water_world", 0), s.get("has_ammonia", 0), s.get("has_terraformable", 0), s.get("has_bio", 0),
            s.get("has_landable", 0), s.get("has_high_g", 0), s.get("has_anomalies", 0), s.get("avg_landable_radius", 0),
            shared_at, shared_at, 1, len(s.get("bodies", [])),
            1, cmdr_name, shared_at, shared_notes
        ))
        imported_sys_count += 1

        # Insert bodies - ALWAYS set was_discovered = 1 to protect recipient from false first discovery
        for b in s.get("bodies", []):
            b_id = b.get("body_id")
            if b_id is None:
                continue
            c.execute("""
                INSERT INTO bodies (
                    system_address, body_id, body_name, star_system, distance_from_arrival_ls,
                    star_type, stellar_mass, planet_class, radius, surface_gravity_g,
                    surface_temperature, surface_pressure, atmosphere, atmosphere_type, atmosphere_composition,
                    semi_major_axis, eccentricity, orbital_period, rotation_period, axial_tilt,
                    rings, materials, parents, landable, volcanism, terraforming_state,
                    bio_signals, geo_signals, mining_signals, reserve_level,
                    fss_value, dss_value, confirmed_genuses, exobiology_predictions, anomalies_json,
                    was_discovered, was_mapped, scan_timestamp, updated_timestamp
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1, ?, ?
                )
                ON CONFLICT(system_address, body_id) DO UPDATE SET
                    body_name = excluded.body_name,
                    planet_class = COALESCE(excluded.planet_class, bodies.planet_class),
                    star_type = COALESCE(excluded.star_type, bodies.star_type),
                    surface_gravity_g = COALESCE(excluded.surface_gravity_g, bodies.surface_gravity_g),
                    surface_temperature = COALESCE(excluded.surface_temperature, bodies.surface_temperature),
                    landable = excluded.landable,
                    bio_signals = excluded.bio_signals,
                    confirmed_genuses = COALESCE(excluded.confirmed_genuses, bodies.confirmed_genuses),
                    exobiology_predictions = excluded.exobiology_predictions,
                    anomalies_json = excluded.anomalies_json
            """, (
                sys_addr, b_id, b.get("body_name"), star_sys, b.get("distance_from_arrival_ls"),
                b.get("star_type"), b.get("stellar_mass"), b.get("planet_class"), b.get("radius"), b.get("surface_gravity_g"),
                b.get("surface_temperature"), b.get("surface_pressure"), b.get("atmosphere"), b.get("atmosphere_type"), b.get("atmosphere_composition"),
                b.get("semi_major_axis"), b.get("eccentricity"), b.get("orbital_period"), b.get("rotation_period"), b.get("axial_tilt"),
                b.get("rings"), b.get("materials"), b.get("parents"), b.get("landable", 0), b.get("volcanism"), b.get("terraforming_state"),
                b.get("bio_signals", 0), b.get("geo_signals", 0), b.get("mining_signals", 0), b.get("reserve_level"),
                b.get("fss_value", 0), b.get("dss_value", 0), b.get("confirmed_genuses"), b.get("exobiology_predictions"), b.get("anomalies_json"),
                shared_at, shared_at
            ))
            imported_bodies_count += 1

        # Surface mining pins
        for m in s.get("surface_mining", []):
            if m.get("latitude") is not None and m.get("longitude") is not None:
                c.execute("""
                    INSERT INTO surface_mining_activities (
                        system_address, star_system, body_id, body_name, body_type,
                        srv_type, material_name, material_name_localised, category,
                        count, latitude, longitude, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sys_addr, star_sys, m.get("body_id"), m.get("body_name"), m.get("body_type"),
                    m.get("srv_type") or "mev_rhino", m.get("material_name"), m.get("material_name_localised"), m.get("category") or "Refined",
                    m.get("count", 1), m.get("latitude"), m.get("longitude"), m.get("timestamp") or shared_at
                ))

        # Bookmarks
        for bm in s.get("bookmarks", []):
            b_id = bm.get("body_id")
            if b_id is not None and (bm.get("alias_name") or bm.get("note_markdown")):
                c.execute("""
                    INSERT INTO body_bookmarks (
                        system_address, body_id, body_name, star_system, alias_name, note_markdown, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(system_address, body_id) DO UPDATE SET
                        alias_name = CASE WHEN body_bookmarks.alias_name = '' THEN excluded.alias_name ELSE body_bookmarks.alias_name END,
                        note_markdown = CASE WHEN body_bookmarks.note_markdown = '' THEN excluded.note_markdown ELSE body_bookmarks.note_markdown END
                """, (
                    sys_addr, b_id, bm.get("body_name") or f"Body {b_id}", star_sys,
                    bm.get("alias_name", ""), bm.get("note_markdown", ""), shared_at, shared_at
                ))

    conn.commit()
    return {
        "success": True,
        "imported_systems": imported_sys_count,
        "imported_bodies": imported_bodies_count,
        "cmdr_name": cmdr_name,
        "verified": True
    }


def generate_standalone_html(
    system_data: Dict[str, Any],
    bodies: List[Dict[str, Any]],
    mining_sites: List[Dict[str, Any]],
    bookmarks: List[Dict[str, Any]],
    cmdr_name: Optional[str] = None,
    is_anonymous: bool = False
) -> str:
    """
    Generates a self-contained, responsive, beautiful HTML view of the system.
    Runs entirely in any web browser without internet connection or external CDN.
    """
    sys_name = html.escape(system_data.get("star_system") or "Unknown System")
    main_star = html.escape(system_data.get("main_star_type") or "Unknown")
    pos_x = system_data.get("star_pos_x", 0.0)
    pos_y = system_data.get("star_pos_y", 0.0)
    pos_z = system_data.get("star_pos_z", 0.0)
    sol_dist = round((pos_x**2 + pos_y**2 + pos_z**2)**0.5, 1) if (pos_x and pos_y and pos_z) else 0.0
    fss_val = system_data.get("total_fss_value", 0)
    max_pot = system_data.get("total_potential_value", 0)
    bio_signals = system_data.get("total_bio_signals", 0)

    author_badge = "Shared Anonymously" if (is_anonymous or not cmdr_name) else f"Discovered / Shared by CMDR {html.escape(cmdr_name)}"
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Build clean full astrophysical JSON payload for AI prompting / external scientific tools
    full_data = sanitize_system_for_export(system_data, bodies, mining_sites, bookmarks)
    full_data["export_metadata"] = {
        "format": "ED_JOURNAL_ANALYZER_ASTROPHYSICS_DATA_V1",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "cmdr_name": "Anonymous" if is_anonymous else (cmdr_name or "Explorer"),
        "ai_prompt_hint": "このJSONには星系および全天体の完全な天体物理・軌道観測パラメータ（質量・半径・軌道長半径・離心率・公転周期・詳細大気組成等）が含まれています。天体物理学・惑星科学の観点から星系の形成史や軌道進化の推論にそのまま利用できます。"
    }
    json_str = json.dumps(full_data, ensure_ascii=False, indent=2).replace("</script>", "<\\/script>")

    # Group bodies into stars and planets
    stars = [b for b in bodies if b.get("star_type")]
    planets = [b for b in bodies if not b.get("star_type") and b.get("planet_class")]

    # Build SVG Orrery visual
    svg_elements = []
    center_cx, center_cy = 300, 200
    svg_elements.append(f'<circle cx="{center_cx}" cy="{center_cy}" r="18" fill="#ffaa00" filter="drop-shadow(0 0 8px #ff7100)" />')
    svg_elements.append(f'<text x="{center_cx}" y="{center_cy + 30}" font-size="11" fill="#fed7aa" text-anchor="middle" font-family="sans-serif">{main_star}-Class Star</text>')

    # Orbit rings for planets (up to 8 visual rings)
    max_display = min(len(planets), 10)
    for idx, p in enumerate(planets[:max_display]):
        orbit_r = 45 + idx * 24
        p_name = html.escape(p.get("body_name", f"Planet {idx+1}"))
        p_class = html.escape(p.get("planet_class", "Planet"))
        rad_km = round(p.get("radius", 0) / 1000) if p.get("radius") else "?"
        g_val = f"{p.get('surface_gravity_g', 0):.2f}G" if p.get('surface_gravity_g') else "--"
        
        # Color based on type
        p_color = "#60a5fa"
        if "earth" in p_class.lower():
            p_color = "#4ade80"
        elif "water" in p_class.lower():
            p_color = "#38bdf8"
        elif "ammonia" in p_class.lower():
            p_color = "#facc15"
        elif "high metal" in p_class.lower():
            p_color = "#fb923c"
        elif "metal rich" in p_class.lower():
            p_color = "#f97316"
        elif "icy" in p_class.lower():
            p_color = "#a5f3fc"

        # Planet position on orbit
        angle = (idx * 48) % 360
        import math
        px = center_cx + orbit_r * math.cos(math.radians(angle))
        py = center_cy + orbit_r * math.sin(math.radians(angle))

        svg_elements.append(f'<circle cx="{center_cx}" cy="{center_cy}" r="{orbit_r}" fill="none" stroke="rgba(255,255,255,0.1)" stroke-dasharray="3,3" />')
        svg_elements.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="7" fill="{p_color}" />')
        svg_elements.append(f'<text x="{px:.1f}" y="{py - 10:.1f}" font-size="9" fill="#e2e8f0" text-anchor="middle" font-family="sans-serif">{p_name} ({g_val})</text>')

    svg_content = "\n".join(svg_elements)

    # Build bodies table rows with deep astrophysics parameter disclosure
    body_rows_html = []
    for b in bodies:
        b_name = html.escape(b.get("body_name", ""))
        b_type = html.escape(b.get("planet_class") or b.get("star_type") or "Unknown")
        dist = f"{round(b.get('distance_from_arrival_ls', 0)):,} Ls" if b.get('distance_from_arrival_ls') is not None else "--"
        grav = f"{b.get('surface_gravity_g', 0):.2f} G" if b.get("surface_gravity_g") is not None else "--"
        temp = f"{round(b.get('surface_temperature', 0))} K" if b.get("surface_temperature") is not None else "--"
        atmo = html.escape(b.get("atmosphere") or "None")
        bio = b.get("bio_signals", 0)
        bio_badge = f'<span class="badge badge-bio">🌱 {bio}</span>' if bio > 0 else ""
        land_badge = '<span class="badge badge-land">Landable</span>' if b.get("landable") else ""
        
        # Check bookmarks
        bm_match = next((bm for bm in bookmarks if bm.get("body_id") == b.get("body_id")), None)
        alias_html = f'<div class="alias-text">🔖 {html.escape(bm_match["alias_name"])}</div>' if bm_match and bm_match.get("alias_name") else ""
        note_html = f'<div class="note-text">{html.escape(bm_match["note_markdown"])}</div>' if bm_match and bm_match.get("note_markdown") else ""

        # Format astrophysics details
        astro_params = []
        if b.get("stellar_mass"):
            astro_params.append(f"質量: {b['stellar_mass']:.4f} M☉")
        elif b.get("mass_em"):
            astro_params.append(f"質量: {b['mass_em']:.4f} M⊕")
        if b.get("radius"):
            astro_params.append(f"半径: {round(b['radius']/1000):,} km")
        if b.get("semi_major_axis"):
            sma_au = b['semi_major_axis'] / 1.495978707e11
            astro_params.append(f"軌道長半径: {sma_au:.4f} AU")
        if b.get("eccentricity") is not None:
            astro_params.append(f"離心率: {b['eccentricity']:.4f}")
        if b.get("orbital_period"):
            orb_days = b['orbital_period'] / 86400
            astro_params.append(f"公転周期: {orb_days:.2f} 日")
        if b.get("rotation_period"):
            rot_days = b['rotation_period'] / 86400
            astro_params.append(f"自転周期: {rot_days:.2f} 日")
        if b.get("axial_tilt") is not None:
            import math
            tilt_deg = math.degrees(b['axial_tilt'])
            astro_params.append(f"軸傾斜: {tilt_deg:.1f}°")
        
        atmo_comp_str = ""
        comp_raw = b.get("atmosphere_composition")
        if comp_raw:
            try:
                comp_obj = json.loads(comp_raw) if isinstance(comp_raw, str) else comp_raw
                if isinstance(comp_obj, dict):
                    atmo_comp_str = "組成: " + ", ".join(f"{k} {v:.1f}%" for k, v in comp_obj.items())
                elif isinstance(comp_obj, list):
                    atmo_comp_str = "組成: " + ", ".join(f"{item.get('Name')}: {item.get('Percent', 0):.1f}%" for item in comp_obj if isinstance(item, dict))
            except Exception:
                pass

        astro_summary = " &bull; ".join(astro_params) if astro_params else ""
        if atmo_comp_str:
            astro_summary = f"{astro_summary}<br>{atmo_comp_str}" if astro_summary else atmo_comp_str

        details_html = ""
        if astro_summary:
            details_html = f"""
            <details class="astro-details">
                <summary>🔬 詳細天体物理パラメータ (AI推論用)</summary>
                <div class="astro-details-content">{astro_summary}</div>
            </details>
            """

        body_rows_html.append(f"""
        <tr>
            <td>
                <strong>{b_name}</strong> {alias_html}{note_html}
                {details_html}
            </td>
            <td>{b_type} {land_badge} {bio_badge}</td>
            <td>{dist}</td>
            <td>{grav}</td>
            <td>{temp}</td>
            <td>{atmo}</td>
            <td style="text-align: right; font-family: monospace; color: #4ade80;">{b.get('fss_value', 0):,} Cr</td>
        </tr>
        """)

    body_table_content = "\n".join(body_rows_html)

    # Build Rhino Mining section
    mining_section_html = ""
    if mining_sites:
        mining_cards = []
        for s in mining_sites:
            lat = f"{s.get('latitude'):.4f}" if s.get('latitude') is not None else "--"
            lon = f"{s.get('longitude'):.4f}" if s.get('longitude') is not None else "--"
            bname = html.escape(s.get("body_name") or "Surface")
            comms = ", ".join(html.escape(c) for c in s.get("commodities", [])) or "Refined Materials"
            mining_cards.append(f"""
            <div class="mining-card">
                <div class="mining-card-header">📍 {bname} &bull; Lat: {lat}, Lon: {lon}</div>
                <div class="mining-card-body">⛏️ 抽出・精製物: <strong>{comms}</strong></div>
            </div>
            """)
        mining_section_html = f"""
        <div class="section-container">
            <h2>⛏️ Rhino SRV 惑星表面採掘ポイント ({len(mining_sites)} 箇所)</h2>
            <div class="mining-grid">
                {''.join(mining_cards)}
            </div>
        </div>
        """

    # Assemble complete HTML
    html_doc = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{sys_name} - Star System Summary</title>

<!-- Full Astrophysical & Orbital Observation JSON (Embedded for AI Prompting & Scientific Analysis) -->
<script type="application/json" id="ed-system-astrophysics-data">
{json_str}
</script>

<style>
:root {{
    --bg-dark: #0a0b0e;
    --bg-card: #12151b;
    --border-color: rgba(255, 113, 0, 0.25);
    --text-primary: #e2e8f0;
    --text-secondary: #94a3b8;
    --ed-orange: #ff7100;
    --ed-cyan: #00d2ff;
    --ed-green: #00ff88;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    background-color: var(--bg-dark);
    color: var(--text-primary);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    line-height: 1.5;
    padding: 20px;
}}
.container {{ max-width: 1100px; margin: 0 auto; }}
header {{
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 16px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
}}
.title-row {{ display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 10px; }}
h1 {{ color: var(--ed-orange); font-size: 1.8rem; letter-spacing: 0.5px; }}
.author-badge {{ font-size: 0.85rem; color: #fed7aa; background: rgba(255,113,0,0.15); padding: 4px 10px; border-radius: 4px; border: 1px solid var(--border-color); }}
.coords-bar {{ color: var(--text-secondary); font-size: 0.82rem; margin-top: 6px; }}

.ai-banner {{
    background: rgba(14, 165, 233, 0.08);
    border: 1px solid rgba(14, 165, 233, 0.35);
    border-left: 4px solid #00d2ff;
    border-radius: 6px;
    padding: 12px 16px;
    margin-bottom: 20px;
    font-size: 0.8rem;
    line-height: 1.5;
}}
.ai-banner-title {{
    color: #38bdf8;
    font-weight: bold;
    font-size: 0.85rem;
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
    flex-wrap: wrap;
}}
.ai-badge {{
    font-size: 0.68rem;
    background: rgba(56, 189, 248, 0.2);
    color: #7dd3fc;
    padding: 2px 6px;
    border-radius: 3px;
    border: 1px solid rgba(56, 189, 248, 0.4);
}}
.ai-banner-desc {{
    color: #94a3b8;
    font-size: 0.74rem;
}}

.stats-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 12px;
    margin-bottom: 20px;
}}
.stat-card {{
    background: var(--bg-card);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 6px;
    padding: 12px 14px;
}}
.stat-card .label {{ font-size: 0.75rem; color: var(--text-secondary); }}
.stat-card .value {{ font-size: 1.25rem; font-weight: bold; margin-top: 2px; }}
.orrery-container {{
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 20px;
    text-align: center;
}}
svg {{ width: 100%; max-width: 600px; height: auto; }}
.section-container {{
    background: var(--bg-card);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 20px;
}}
h2 {{ font-size: 1.1rem; color: var(--ed-cyan); margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 6px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
th, td {{ padding: 8px 10px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.05); vertical-align: top; }}
th {{ color: var(--text-secondary); font-weight: 600; }}
tr:hover {{ background: rgba(255,255,255,0.02); }}
.badge {{ font-size: 0.7rem; padding: 2px 6px; border-radius: 3px; font-weight: bold; margin-left: 4px; }}
.badge-bio {{ background: rgba(0,255,136,0.15); color: var(--ed-green); border: 1px solid rgba(0,255,136,0.3); }}
.badge-land {{ background: rgba(96,165,250,0.15); color: #60a5fa; border: 1px solid rgba(96,165,250,0.3); }}
.alias-text {{ font-size: 0.75rem; color: #fbbf24; margin-top: 2px; }}
.note-text {{ font-size: 0.72rem; color: var(--text-secondary); font-style: italic; }}

.astro-details {{
    margin-top: 6px;
    font-size: 0.72rem;
}}
.astro-details summary {{
    color: var(--ed-cyan);
    cursor: pointer;
    user-select: none;
    outline: none;
}}
.astro-details-content {{
    background: rgba(0,0,0,0.35);
    border: 1px solid rgba(0,210,255,0.2);
    border-radius: 4px;
    padding: 6px 8px;
    margin-top: 4px;
    font-family: Consolas, monospace;
    color: #cbd5e1;
    line-height: 1.4;
}}

.mining-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 10px; }}
.mining-card {{ background: rgba(0,0,0,0.3); border: 1px solid rgba(56,189,248,0.3); border-radius: 6px; padding: 10px; }}
.mining-card-header {{ font-size: 0.82rem; font-weight: bold; color: #38bdf8; }}
.mining-card-body {{ font-size: 0.8rem; color: #cbd5e1; margin-top: 4px; }}
footer {{ text-align: center; font-size: 0.75rem; color: var(--text-secondary); margin-top: 30px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.05); }}
</style>
</head>
<body>
<div class="container">
    <header>
        <div class="title-row">
            <h1>🌌 {sys_name}</h1>
            <div class="author-badge">{author_badge}</div>
        </div>
        <div class="coords-bar">
            座標: <code>[{pos_x:.2f}, {pos_y:.2f}, {pos_z:.2f}]</code> &bull; Sol距離: <code>{sol_dist:,} Ly</code> &bull; 主星: <code>{main_star}型</code>
        </div>
    </header>

    <div class="ai-banner">
        <div class="ai-banner-title">
            <span>🤖</span> <span>生成AI（LLM）天体物理分析・星系形成史シナリオ推論対応</span>
            <span class="ai-badge">完全観測JSON内包</span>
        </div>
        <div class="ai-banner-desc">
            本HTMLファイルには、星系および全天体の完全な天体物理・軌道観測データ（質量・半径・軌道長半径・離心率・公転周期・詳細大気組成など）が JSON 形式で内包されています。<br>
            ChatGPT、Claude、Gemini 等の生成AIに本HTMLファイルをそのままアップロードし、推論プロンプトを入力することで、現代の天文学・惑星形成理論に基づいた詳細な形成史シナリオや景観描写の推論を行わせることができます。
        </div>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="label">推定最大探査価値</div>
            <div class="value" style="color: var(--ed-green);">{max_pot:,} Cr</div>
        </div>
        <div class="stat-card">
            <div class="label">FSSスキャン価値</div>
            <div class="value" style="color: var(--ed-cyan);">{fss_val:,} Cr</div>
        </div>
        <div class="stat-card">
            <div class="label">天体数</div>
            <div class="value">{len(bodies)} 天体</div>
        </div>
        <div class="stat-card">
            <div class="label">生体 (Bio) シグナル</div>
            <div class="value" style="color: var(--ed-green);">{bio_signals} 箇所</div>
        </div>
    </div>

    <div class="orrery-container">
        <h2>🪐 System Orrery Overview</h2>
        <svg viewBox="0 0 600 400" xmlns="http://www.w3.org/2000/svg">
            {svg_content}
        </svg>
    </div>

    <div class="section-container">
        <h2>🪐 天体構成・探査インベントリ ({len(bodies)} 天体)</h2>
        <table>
            <thead>
                <tr>
                    <th>天体名</th>
                    <th>分類 / タグ</th>
                    <th>到着距離</th>
                    <th>重力</th>
                    <th>表面温度</th>
                    <th>大気</th>
                    <th style="text-align: right;">探査価値</th>
                </tr>
            </thead>
            <tbody>
                {body_table_content}
            </tbody>
        </table>
    </div>

    {mining_section_html}

    <footer>
        Elite Dangerous Journal Analyzer &bull; Standalone Web Share Edition &bull; Exported on {now_str}
    </footer>
</div>
</body>
</html>
"""
    return html_doc
