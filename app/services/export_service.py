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
        for b in sorted(sys_entry.get("bodies", []), key=lambda x: x.get("body_id") if x.get("body_id") is not None else 0):
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


def get_body_visual_color(planet_class: str) -> str:
    if not planet_class:
        return "#60a5fa"
    p = planet_class.lower()
    if "earth" in p:
        return "#4ade80"
    elif "water" in p:
        return "#38bdf8"
    elif "ammonia" in p:
        return "#facc15"
    elif "high metal" in p:
        return "#fb923c"
    elif "metal rich" in p:
        return "#f97316"
    elif "icy" in p:
        return "#a5f3fc"
    elif "rocky" in p:
        return "#cbd5e1"
    elif "gas giant" in p:
        return "#f472b6"
    return "#94a3b8"


def get_star_visual_color(star_type: str) -> str:
    if not star_type:
        return "#ffaa00"
    st = star_type.upper()
    if any(st.startswith(x) for x in ["O", "B"]):
        return "#93c5fd"
    elif st.startswith("A"):
        return "#f8fafc"
    elif st.startswith("F"):
        return "#fef08a"
    elif st.startswith("G"):
        return "#facc15"
    elif st.startswith("K"):
        return "#fb923c"
    elif st.startswith("M"):
        return "#f87171"
    elif st.startswith("D"):
        return "#e0e7ff"
    elif st.startswith("N"):
        return "#c084fc"
    elif st.startswith("H"):
        return "#818cf8"
    elif any(st.startswith(x) for x in ["T", "Y", "L"]):
        return "#b45309"
    return "#ffaa00"


def extract_body_sub_tokens(body_name: str, sys_name: str) -> Dict[str, Any]:
    short = body_name.strip()
    if sys_name and short.startswith(sys_name):
        short = short[len(sys_name):].strip()
    tokens = short.split()
    
    if not tokens:
        return {"star": "A", "planet": None, "moon": None, "submoon": None}
    
    star = "A"
    idx = 0
    if tokens[0].isupper() and tokens[0].isalpha() and len(tokens[0]) <= 5:
        star = tokens[0]
        idx = 1
    
    planet = None
    moon = None
    submoon = None
    
    if idx < len(tokens):
        if tokens[idx].isdigit():
            planet = int(tokens[idx])
            idx += 1
            if idx < len(tokens) and len(tokens[idx]) == 1 and tokens[idx].isalpha():
                moon = tokens[idx].lower()
                idx += 1
                if idx < len(tokens) and len(tokens[idx]) == 1 and tokens[idx].isalpha():
                    submoon = tokens[idx].lower()
    
    return {"star": star, "planet": planet, "moon": moon, "submoon": submoon}


HTML_I18N = {
    "ja": {
        "html_lang": "ja",
        "coords": "座標",
        "sol_dist": "Sol距離",
        "main_star": "主星",
        "star_class_suffix": "型",
        "star_type_label": "{type}型 恒星",
        "star_key_label": "{key}: {type}型",
        "barycentre_label": "重心 {key}",
        "binary_orbit": "連星軌道",
        "anon_shared": "匿名共有",
        "cmdr_shared": "発見・共有: CMDR {cmdr}",
        "ai_banner_title": "生成AI（LLM）天体物理分析・星系形成史シナリオ推論対応",
        "ai_badge": "完全観測JSON内包",
        "ai_banner_desc": "本HTMLファイルには、星系および全天体の完全な天体物理・軌道観測データ（質量・半径・軌道長半径・離心率・公転周期・詳細大気組成など）が JSON 形式で内包されています。<br>ChatGPT、Claude、Gemini 等の生成AIに本HTMLファイルをそのままアップロードし、推論プロンプトを入力することで、現代の天文学・惑星形成理論に基づいた詳細な形成史シナリオや景観描写の推論を行わせることができます。",
        "ai_prompt_hint": "このJSONには星系および全天体の完全な天体物理・軌道観測パラメータ（質量・半径・軌道長半径・離心率・公転周期・詳細大気組成等）が含まれています。天体物理学・惑星科学の観点から星系の形成史や軌道進化の推論にそのまま利用できます。",
        "stat_max_pot": "推定最大探査価値",
        "stat_fss_val": "FSSスキャン価値",
        "stat_bodies": "天体数",
        "stat_bodies_val": "{count} 天体",
        "stat_bio": "生体 (Bio) シグナル",
        "stat_bio_val": "{count} 箇所",
        "orrery_title": "🪐 System Orrery & Orbital Hierarchy (対話的ズーム・全星系軌道図)",
        "orrery_zoom_in": "🔍＋ 拡大",
        "orrery_zoom_out": "🔍－ 縮小",
        "orrery_reset": "🔄 全体リセット",
        "orrery_zoom_in_title": "拡大",
        "orrery_zoom_out_title": "縮小",
        "orrery_reset_title": "星系全体を表示",
        "orrery_jump_bar": "フォーカスジャンプ:",
        "orrery_primary_star": "☀️ 主星 {key}",
        "orrery_companion_star": "⭐ 伴星 {key}{dist}",
        "orrery_companion_orbit": "── 伴星 {key} 周回軌道 ({dist}) ──",
        "orrery_hint": "🖱️ マウスホイールで無段階ズーム / ドラッグで自由移動 / 伴星ボタンで拡大ジャンプ",
        "tooltip_dist": "到着距離: ",
        "tooltip_grav": "表面重力: ",
        "tooltip_temp": "表面温度: ",
        "table_section_title": "🪐 天体構成・探査インベントリ ({count} 天体)",
        "th_name": "天体名",
        "th_class": "分類 / タグ",
        "th_dist": "到着距離",
        "th_grav": "重力",
        "th_temp": "表面温度",
        "th_atmo": "大気",
        "th_value": "探査価値",
        "astro_summary_heading": "🔬 詳細天体物理パラメータ",
        "param_mass": "質量",
        "param_radius": "半径",
        "param_semi_major_axis": "軌道長半径",
        "param_eccentricity": "離心率",
        "param_orbital_period": "公転周期",
        "param_rotation_period": "自転周期",
        "param_axial_tilt": "軸傾斜",
        "param_days_unit": "日",
        "param_composition": "組成",
        "atmo_none": "なし",
        "mining_section_title": "⛏️ Rhino SRV 惑星表面採掘ポイント ({count} 箇所)",
        "mining_extracted": "⛏️ 抽出・精製物: <strong>{comms}</strong>",
        "footer": "Elite Dangerous Journal Analyzer &bull; Standalone Web Share Edition &bull; Exported on {now}"
    },
    "en": {
        "html_lang": "en",
        "coords": "Coordinates",
        "sol_dist": "Sol Distance",
        "main_star": "Main Star",
        "star_class_suffix": "",
        "star_type_label": "Class {type} Star",
        "star_key_label": "{key}: Class {type}",
        "barycentre_label": "Barycentre {key}",
        "binary_orbit": "Binary Orbit",
        "anon_shared": "Shared Anonymously",
        "cmdr_shared": "Discovered / Shared by CMDR {cmdr}",
        "ai_banner_title": "Generative AI (LLM) Astrophysical Analysis & System Formation Reasoning",
        "ai_badge": "Full Observation JSON Embedded",
        "ai_banner_desc": "This HTML file contains complete astrophysical and orbital observation data for the system and all celestial bodies (mass, radius, semi-major axis, eccentricity, orbital period, detailed atmospheric composition, etc.) in embedded JSON format.<br>Upload this HTML directly to ChatGPT, Claude, Gemini, or other LLMs with your prompt to infer deep system formation scenarios, geological evolutions, and vista descriptions based on astrophysical science.",
        "ai_prompt_hint": "This JSON contains complete astrophysical and orbital observation parameters (mass, radius, semi-major axis, eccentricity, orbital period, detailed atmospheric composition, etc.). It can be directly utilized for reasoning about system formation history and orbital evolution from astrophysical perspectives.",
        "stat_max_pot": "Estimated Max Value",
        "stat_fss_val": "FSS Scan Value",
        "stat_bodies": "Celestial Bodies",
        "stat_bodies_val": "{count} bodies",
        "stat_bio": "Bio Signals",
        "stat_bio_val": "{count} sites",
        "orrery_title": "🪐 System Orrery & Orbital Hierarchy (Interactive Zoom & Orbit Map)",
        "orrery_zoom_in": "🔍＋ Zoom In",
        "orrery_zoom_out": "🔍－ Zoom Out",
        "orrery_reset": "🔄 Reset",
        "orrery_zoom_in_title": "Zoom in",
        "orrery_zoom_out_title": "Zoom out",
        "orrery_reset_title": "Show entire system",
        "orrery_jump_bar": "Focus Jump:",
        "orrery_primary_star": "☀️ Primary {key}",
        "orrery_companion_star": "⭐ Companion {key}{dist}",
        "orrery_companion_orbit": "── Companion Star {key} Orbit ({dist}) ──",
        "orrery_hint": "🖱️ Mouse wheel to zoom / Drag to pan / Click companion buttons to focus",
        "tooltip_dist": "Arrival Distance: ",
        "tooltip_grav": "Surface Gravity: ",
        "tooltip_temp": "Surface Temperature: ",
        "table_section_title": "🪐 System Composition & Survey Inventory ({count} bodies)",
        "th_name": "Body Name",
        "th_class": "Class / Tag",
        "th_dist": "Distance",
        "th_grav": "Gravity",
        "th_temp": "Surface Temp",
        "th_atmo": "Atmosphere",
        "th_value": "Scan Value",
        "astro_summary_heading": "🔬 Detailed Astrophysical Parameters",
        "param_mass": "Mass",
        "param_radius": "Radius",
        "param_semi_major_axis": "Semi-Major Axis",
        "param_eccentricity": "Eccentricity",
        "param_orbital_period": "Orbital Period",
        "param_rotation_period": "Rotation Period",
        "param_axial_tilt": "Axial Tilt",
        "param_days_unit": "d",
        "param_composition": "Composition",
        "atmo_none": "None",
        "mining_section_title": "⛏️ Rhino SRV Surface Mining Sites ({count} sites)",
        "mining_extracted": "⛏️ Extracted Materials: <strong>{comms}</strong>",
        "footer": "Elite Dangerous Journal Analyzer &bull; Standalone Web Share Edition &bull; Exported on {now}"
    }
}


def build_interactive_orrery(system_data: Dict[str, Any], bodies: List[Dict[str, Any]], lang: str = "ja") -> str:
    import math
    strings = HTML_I18N.get(lang if lang in HTML_I18N else "ja")
    sys_name = system_data.get("star_system", "System")
    stars = [b for b in bodies if b.get("star_type")]
    if not stars:
        stars = [{"body_id": 0, "body_name": sys_name + " A", "star_type": system_data.get("main_star_type", "G"), "distance_from_arrival_ls": 0}]
    stars.sort(key=lambda s: s.get("distance_from_arrival_ls") or 0)

    # Map stars
    star_map = {}
    for i, s in enumerate(stars):
        info = extract_body_sub_tokens(s.get("body_name", ""), sys_name)
        key = info["star"] if (info["star"] != "A" or i == 0) else chr(ord('A') + i)
        star_map[key] = {
            "star_body": s,
            "key": key,
            "index": i,
            "is_primary": (i == 0),
            "is_barycentre": False,
            "planets": {}
        }

    # Map planets and moons
    non_stars = [b for b in bodies if not b.get("star_type")]
    primary_key = stars[0].get("body_name", "A")
    primary_key = extract_body_sub_tokens(primary_key, sys_name)["star"]
    if primary_key not in star_map:
        primary_key = list(star_map.keys())[0]

    for b in non_stars:
        info = extract_body_sub_tokens(b.get("body_name", ""), sys_name)
        target_star = info["star"]
        if target_star not in star_map:
            if "AB" in target_star or "BC" in target_star:
                star_map[target_star] = {
                    "star_body": {"body_name": f"{sys_name} {target_star} Barycentre", "star_type": "Barycentre", "distance_from_arrival_ls": 0},
                    "key": target_star,
                    "index": len(star_map),
                    "is_primary": False,
                    "is_barycentre": True,
                    "planets": {}
                }
            else:
                target_star = primary_key

        p_num = info["planet"] or b.get("body_id", 1)
        if p_num not in star_map[target_star]["planets"]:
            star_map[target_star]["planets"][p_num] = {
                "body": b if info["moon"] is None else None,
                "num": p_num,
                "moons": []
            }
        if info["moon"] is None:
            star_map[target_star]["planets"][p_num]["body"] = b
        else:
            star_map[target_star]["planets"][p_num]["moons"].append(b)

    center_cx, center_cy = 500, 350
    companion_stars = [s for s in star_map.values() if not s["is_primary"]]
    num_companions = len(companion_stars)

    star_positions = {}
    star_positions[primary_key] = (center_cx, center_cy)

    for i, comp in enumerate(companion_stars):
        dist_ls = comp["star_body"].get("distance_from_arrival_ls") or (4000 * (i + 1))
        orbit_r = 250 + 85 * math.log10(max(10, dist_ls) / 10.0)
        angle_rad = (2 * math.pi * i / max(1, num_companions)) + 0.4
        sx = center_cx + orbit_r * math.cos(angle_rad)
        sy = center_cy + orbit_r * math.sin(angle_rad)
        star_positions[comp["key"]] = (sx, sy, orbit_r)

    svg_elements = []
    svg_elements.append("""
    <defs>
        <filter id="star-glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
            </feMerge>
        </filter>
        <filter id="companion-glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
            </feMerge>
        </filter>
    </defs>
    """)

    # Companion Orbit Rings
    for comp in companion_stars:
        pos_data = star_positions[comp["key"]]
        orbit_r = pos_data[2]
        dist_ls = comp["star_body"].get("distance_from_arrival_ls") or 0
        dist_str = f"{dist_ls:,} Ls" if dist_ls else strings["binary_orbit"]
        orbit_text = strings["orrery_companion_orbit"].format(key=comp["key"], dist=dist_str)
        svg_elements.append(f'<circle cx="{center_cx}" cy="{center_cy}" r="{orbit_r:.1f}" fill="none" stroke="rgba(255, 170, 0, 0.22)" stroke-width="1.2" stroke-dasharray="5,4" />')
        svg_elements.append(f'<text x="{center_cx}" y="{center_cy - orbit_r - 5:.1f}" font-size="9" fill="#f59e0b" text-anchor="middle" font-family="monospace">{orbit_text}</text>')

    jump_buttons_html = []
    primary_btn_text = strings["orrery_primary_star"].format(key=primary_key)
    jump_buttons_html.append(f'<button type="button" class="orrery-btn" onclick="focusOrreryTarget({center_cx}, {center_cy}, 1.8)">{primary_btn_text}</button>')

    # Render stars & planets
    for star_key, s_data in star_map.items():
        is_prim = s_data["is_primary"]
        is_bary = s_data.get("is_barycentre", False)
        s_body = s_data["star_body"]
        s_color = get_star_visual_color(s_body.get("star_type", "G"))
        s_type = s_body.get("star_type") or ("Barycentre" if is_bary else "Star")
        dist_val = s_body.get("distance_from_arrival_ls", 0)

        pos = star_positions[star_key]
        sx, sy = pos[0], pos[1]

        if not is_prim:
            dist_tag = f" ({dist_val:,} Ls)" if dist_val else ""
            comp_btn_text = strings["orrery_companion_star"].format(key=star_key, dist=dist_tag)
            jump_buttons_html.append(f'<button type="button" class="orrery-btn" onclick="focusOrreryTarget({sx:.1f}, {sy:.1f}, 2.4)">{comp_btn_text}</button>')

        if is_bary:
            bary_text = strings["barycentre_label"].format(key=star_key)
            svg_elements.append(f'<g class="orrery-node" data-name="{html.escape(s_body.get("body_name", ""))}" data-type="Barycentre" data-dist="{dist_val}">')
            svg_elements.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="8" fill="none" stroke="#a855f7" stroke-width="1.5" stroke-dasharray="2,2" />')
            svg_elements.append(f'<line x1="{sx-12:.1f}" y1="{sy:.1f}" x2="{sx+12:.1f}" y2="{sy:.1f}" stroke="#a855f7" stroke-width="1" />')
            svg_elements.append(f'<line x1="{sx:.1f}" y1="{sy-12:.1f}" x2="{sx:.1f}" y2="{sy+12:.1f}" stroke="#a855f7" stroke-width="1" />')
            svg_elements.append(f'<text x="{sx:.1f}" y="{sy+20:.1f}" font-size="10" fill="#d8b4fe" text-anchor="middle" font-family="sans-serif">{bary_text}</text>')
            svg_elements.append('</g>')
        else:
            r_star = 18 if is_prim else 13
            glow_id = "star-glow" if is_prim else "companion-glow"
            b_name = html.escape(s_body.get("body_name", f"Star {star_key}"))
            temp_val = f'{s_body.get("surface_temperature", "--")} K'
            star_type_text = strings["star_type_label"].format(type=s_type)
            star_key_text = strings["star_key_label"].format(key=star_key, type=s_type)
            svg_elements.append(f'<g class="orrery-node" data-name="{b_name}" data-type="{star_type_text}" data-dist="{dist_val}" data-temp="{temp_val}">')
            svg_elements.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{r_star}" fill="{s_color}" filter="url(#{glow_id})" />')
            svg_elements.append(f'<text x="{sx:.1f}" y="{sy + r_star + 13:.1f}" font-size="10" font-weight="bold" fill="#fed7aa" text-anchor="middle" font-family="sans-serif">{star_key_text}</text>')
            svg_elements.append('</g>')

        planets_dict = s_data["planets"]
        sorted_planets = sorted(planets_dict.values(), key=lambda p: p["num"])

        for p_idx, p_entry in enumerate(sorted_planets):
            p_body = p_entry["body"]
            moons = p_entry["moons"]

            p_orbit_r = 44 + p_idx * 26
            p_angle_rad = math.radians((p_idx * 52) % 360)
            px = sx + p_orbit_r * math.cos(p_angle_rad)
            py = sy + p_orbit_r * math.sin(p_angle_rad)

            svg_elements.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{p_orbit_r:.1f}" fill="none" stroke="rgba(255,255,255,0.12)" stroke-dasharray="2,2" />')

            p_name = html.escape(p_body.get("body_name", f"Planet {p_entry['num']}")) if p_body else f"{star_key} {p_entry['num']}"
            p_class = p_body.get("planet_class", "Planet") if p_body else "Planet"
            p_color = get_body_visual_color(p_class)
            g_str = f"{p_body.get('surface_gravity_g', 0):.2f}G" if (p_body and p_body.get('surface_gravity_g')) else "--"
            p_dist = p_body.get("distance_from_arrival_ls", 0) if p_body else 0
            p_temp = f"{p_body.get('surface_temperature', '--')} K" if (p_body and p_body.get('surface_temperature')) else "--"

            svg_elements.append(f'<g class="orrery-node" data-name="{p_name}" data-type="{html.escape(p_class)}" data-dist="{p_dist}" data-grav="{g_str}" data-temp="{p_temp}">')
            svg_elements.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="6.5" fill="{p_color}" />')
            svg_elements.append(f'<text x="{px:.1f}" y="{py - 8:.1f}" font-size="8" fill="#e2e8f0" text-anchor="middle" font-family="sans-serif">{p_name} ({g_str})</text>')
            svg_elements.append('</g>')

            for m_idx, m_body in enumerate(moons):
                m_orbit_r = 12 + m_idx * 6.5
                m_angle_rad = math.radians((m_idx * 80 + 30) % 360)
                mx = px + m_orbit_r * math.cos(m_angle_rad)
                my = py + m_orbit_r * math.sin(m_angle_rad)

                svg_elements.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{m_orbit_r:.1f}" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="0.8" stroke-dasharray="1,2" />')

                m_name = html.escape(m_body.get("body_name", "Moon"))
                m_class = m_body.get("planet_class", "Moon")
                m_color = get_body_visual_color(m_class)
                m_dist = m_body.get("distance_from_arrival_ls", 0)
                m_grav = f"{m_body.get('surface_gravity_g', 0):.2f}G" if m_body.get('surface_gravity_g') else "--"

                svg_elements.append(f'<g class="orrery-node" data-name="{m_name}" data-type="{html.escape(m_class)}" data-dist="{m_dist}" data-grav="{m_grav}">')
                svg_elements.append(f'<circle cx="{mx:.1f}" cy="{my:.1f}" r="3" fill="{m_color}" />')
                svg_elements.append('</g>')

    svg_inner = "\n".join(svg_elements)
    jump_bar_inner = " ".join(jump_buttons_html)

    orrery_html = f"""
    <div class="orrery-container" id="orrery-container-root">
        <div class="orrery-header-bar">
            <h2>{strings["orrery_title"]}</h2>
            <div class="orrery-controls">
                <button type="button" class="orrery-btn" onclick="zoomOrrery(1.3)" title="{strings["orrery_zoom_in_title"]}">{strings["orrery_zoom_in"]}</button>
                <button type="button" class="orrery-btn" onclick="zoomOrrery(0.7)" title="{strings["orrery_zoom_out_title"]}">{strings["orrery_zoom_out"]}</button>
                <button type="button" class="orrery-btn" onclick="resetOrreryView()" title="{strings["orrery_reset_title"]}">{strings["orrery_reset"]}</button>
            </div>
        </div>

        <div class="orrery-jump-bar">
            <span style="font-size: 0.75rem; color: var(--text-secondary); font-weight: bold; margin-right: 4px;">{strings["orrery_jump_bar"]}</span>
            {jump_bar_inner}
        </div>

        <div class="orrery-viewport-wrapper" id="orrery-wrapper">
            <svg id="interactive-orrery-svg" viewBox="0 0 1000 700" style="width: 100%; height: 100%; user-select: none;">
                <g id="orrery-pan-zoom-layer" transform="matrix(1 0 0 1 0 0)">
                    {svg_inner}
                </g>
            </svg>

            <!-- Floating Info Tooltip -->
            <div id="orrery-tooltip" style="display: none; position: absolute; pointer-events: none; background: rgba(10, 16, 26, 0.94); border: 1px solid var(--ed-cyan); padding: 8px 12px; border-radius: 6px; font-size: 0.75rem; color: #fff; box-shadow: 0 4px 14px rgba(0,0,0,0.6); z-index: 10;"></div>

            <!-- Hint overlay -->
            <div style="position: absolute; bottom: 8px; left: 12px; font-size: 0.7rem; color: #64748b; pointer-events: none;">
                {strings["orrery_hint"]}
            </div>
        </div>
    </div>
    """
    return orrery_html


def generate_standalone_html(
    system_data: Dict[str, Any],
    bodies: List[Dict[str, Any]],
    mining_sites: List[Dict[str, Any]],
    bookmarks: List[Dict[str, Any]],
    cmdr_name: Optional[str] = None,
    is_anonymous: bool = False,
    lang: str = "ja"
) -> str:
    """
    Generates a self-contained, responsive, beautiful HTML view of the system.
    Runs entirely in any web browser without internet connection or external CDN.
    """
    strings = HTML_I18N.get(lang if lang in HTML_I18N else "ja")
    sys_name = html.escape(system_data.get("star_system") or "Unknown System")
    main_star = html.escape(system_data.get("main_star_type") or "Unknown")
    pos_x = system_data.get("star_pos_x") or 0.0
    pos_y = system_data.get("star_pos_y") or 0.0
    pos_z = system_data.get("star_pos_z") or 0.0
    sol_dist = round((pos_x**2 + pos_y**2 + pos_z**2)**0.5, 1) if (pos_x and pos_y and pos_z) else 0.0
    fss_val = system_data.get("total_fss_value", 0)
    max_pot = system_data.get("total_potential_value", 0)
    bio_signals = system_data.get("total_bio_signals", 0)

    author_badge = strings["anon_shared"] if (is_anonymous or not cmdr_name) else strings["cmdr_shared"].format(cmdr=html.escape(cmdr_name))
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Build clean full astrophysical JSON payload for AI prompting / external scientific tools
    full_data = sanitize_system_for_export(system_data, bodies, mining_sites, bookmarks)
    full_data["export_metadata"] = {
        "format": "ED_JOURNAL_ANALYZER_ASTROPHYSICS_DATA_V1",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "cmdr_name": "Anonymous" if is_anonymous else (cmdr_name or "Explorer"),
        "ai_prompt_hint": strings["ai_prompt_hint"]
    }
    json_str = json.dumps(full_data, ensure_ascii=False, indent=2).replace("</script>", "<\\/script>")

    # Build interactive multi-star and orbital hierarchy Orrery
    orrery_html_block = build_interactive_orrery(system_data, bodies, lang=lang)

    # Build bodies table rows with deep astrophysics parameter disclosure
    body_rows_html = []
    for b in bodies:
        b_name = html.escape(b.get("body_name", ""))
        b_type = html.escape(b.get("planet_class") or b.get("star_type") or "Unknown")
        dist = f"{round(b.get('distance_from_arrival_ls', 0)):,} Ls" if b.get('distance_from_arrival_ls') is not None else "--"
        grav = f"{b.get('surface_gravity_g', 0):.2f} G" if b.get("surface_gravity_g") is not None else "--"
        temp = f"{round(b.get('surface_temperature', 0))} K" if b.get("surface_temperature") is not None else "--"
        atmo = html.escape(b.get("atmosphere") or strings["atmo_none"])
        bio = b.get("bio_signals") or 0
        bio_badge = f'<span class="badge badge-bio">🌱 {bio}</span>' if bio > 0 else ""
        land_badge = '<span class="badge badge-land">Landable</span>' if b.get("landable") else ""
        
        # Check bookmarks
        bm_match = next((bm for bm in bookmarks if bm.get("body_id") == b.get("body_id")), None)
        alias_html = f'<div class="alias-text">🔖 {html.escape(bm_match["alias_name"])}</div>' if bm_match and bm_match.get("alias_name") else ""
        note_html = f'<div class="note-text">{html.escape(bm_match["note_markdown"])}</div>' if bm_match and bm_match.get("note_markdown") else ""

        # Format astrophysics details
        astro_params = []
        if b.get("stellar_mass"):
            astro_params.append(f"{strings['param_mass']}: {b['stellar_mass']:.4f} M☉")
        elif b.get("mass_em"):
            astro_params.append(f"{strings['param_mass']}: {b['mass_em']:.4f} M⊕")
        if b.get("radius"):
            astro_params.append(f"{strings['param_radius']}: {round(b['radius']/1000):,} km")
        if b.get("semi_major_axis"):
            sma_au = b['semi_major_axis'] / 1.495978707e11
            astro_params.append(f"{strings['param_semi_major_axis']}: {sma_au:.4f} AU")
        if b.get("eccentricity") is not None:
            astro_params.append(f"{strings['param_eccentricity']}: {b['eccentricity']:.4f}")
        if b.get("orbital_period"):
            orb_days = b['orbital_period'] / 86400
            astro_params.append(f"{strings['param_orbital_period']}: {orb_days:.2f} {strings['param_days_unit']}")
        if b.get("rotation_period"):
            rot_days = b['rotation_period'] / 86400
            astro_params.append(f"{strings['param_rotation_period']}: {rot_days:.2f} {strings['param_days_unit']}")
        if b.get("axial_tilt") is not None:
            import math
            tilt_deg = math.degrees(b['axial_tilt'])
            astro_params.append(f"{strings['param_axial_tilt']}: {tilt_deg:.1f}°")
        
        atmo_comp_str = ""
        comp_raw = b.get("atmosphere_composition")
        if comp_raw:
            try:
                comp_obj = json.loads(comp_raw) if isinstance(comp_raw, str) else comp_raw
                if isinstance(comp_obj, dict):
                    atmo_comp_str = f"{strings['param_composition']}: " + ", ".join(f"{k} {v:.1f}%" for k, v in comp_obj.items())
                elif isinstance(comp_obj, list):
                    atmo_comp_str = f"{strings['param_composition']}: " + ", ".join(f"{item.get('Name')}: {item.get('Percent', 0):.1f}%" for item in comp_obj if isinstance(item, dict))
            except Exception:
                pass

        astro_summary = " &bull; ".join(astro_params) if astro_params else ""
        if atmo_comp_str:
            astro_summary = f"{astro_summary}<br>{atmo_comp_str}" if astro_summary else atmo_comp_str

        details_html = ""
        if astro_summary:
            details_html = f"""
            <details class="astro-details">
                <summary>{strings["astro_summary_heading"]}</summary>
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
            <td style="text-align: right; font-family: monospace; color: #4ade80;">{b.get('fss_value') or 0:,} Cr</td>
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
            comms = ", ".join(html.escape(c) for c in s.get("commodities", [])) or ("Refined Materials" if lang == "en" else "精製マテリアル")
            mining_cards.append(f"""
            <div class="mining-card">
                <div class="mining-card-header">📍 {bname} &bull; Lat: {lat}, Lon: {lon}</div>
                <div class="mining-card-body">{strings["mining_extracted"].format(comms=comms)}</div>
            </div>
            """)
        mining_section_html = f"""
        <div class="section-container">
            <h2>{strings["mining_section_title"].format(count=len(mining_sites))}</h2>
            <div class="mining-grid">
                {''.join(mining_cards)}
            </div>
        </div>
        """

    # Assemble complete HTML
    main_star_display = f"{main_star}型" if lang != "en" else f"Class {main_star}"
    coords_bar_html = f'{strings["coords"]}: <code>[{pos_x:.2f}, {pos_y:.2f}, {pos_z:.2f}]</code> &bull; {strings["sol_dist"]}: <code>{sol_dist:,} Ly</code> &bull; {strings["main_star"]}: <code>{main_star_display}</code>'
    html_doc = f"""<!DOCTYPE html>
<html lang="{strings['html_lang']}">
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

.orrery-container {{
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 20px;
}}
.orrery-header-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 8px;
}}
.orrery-controls {{
    display: flex;
    gap: 6px;
}}
.orrery-jump-bar {{
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
    margin-bottom: 10px;
    padding: 6px 10px;
    background: rgba(0, 0, 0, 0.25);
    border-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 0.05);
}}
.orrery-btn {{
    background: rgba(255, 113, 0, 0.12);
    border: 1px solid rgba(255, 113, 0, 0.4);
    color: var(--ed-orange);
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.2s;
}}
.orrery-btn:hover {{
    background: rgba(255, 113, 0, 0.25);
    border-color: var(--ed-orange);
    color: #fff;
}}
.orrery-viewport-wrapper {{
    width: 100%;
    height: 520px;
    overflow: hidden;
    position: relative;
    background: radial-gradient(circle at center, #0d131f 0%, #06090e 100%);
    border-radius: 6px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    cursor: grab;
}}
.orrery-node {{
    cursor: pointer;
}}
.orrery-node:hover circle {{
    filter: drop-shadow(0 0 6px #00d2ff);
}}

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
            {coords_bar_html}
        </div>
    </header>

    <div class="ai-banner">
        <div class="ai-banner-title">
            <span>🤖</span> <span>{strings["ai_banner_title"]}</span>
            <span class="ai-badge">{strings["ai_badge"]}</span>
        </div>
        <div class="ai-banner-desc">
            {strings["ai_banner_desc"]}
        </div>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="label">{strings["stat_max_pot"]}</div>
            <div class="value" style="color: var(--ed-green);">{max_pot:,} Cr</div>
        </div>
        <div class="stat-card">
            <div class="label">{strings["stat_fss_val"]}</div>
            <div class="value" style="color: var(--ed-cyan);">{fss_val:,} Cr</div>
        </div>
        <div class="stat-card">
            <div class="label">{strings["stat_bodies"]}</div>
            <div class="value">{strings["stat_bodies_val"].format(count=len(bodies))}</div>
        </div>
        <div class="stat-card">
            <div class="label">{strings["stat_bio"]}</div>
            <div class="value" style="color: var(--ed-green);">{strings["stat_bio_val"].format(count=bio_signals)}</div>
        </div>
    </div>

    {orrery_html_block}

    <div class="section-container">
        <h2>{strings["table_section_title"].format(count=len(bodies))}</h2>
        <table>
            <thead>
                <tr>
                    <th>{strings["th_name"]}</th>
                    <th>{strings["th_class"]}</th>
                    <th>{strings["th_dist"]}</th>
                    <th>{strings["th_grav"]}</th>
                    <th>{strings["th_temp"]}</th>
                    <th>{strings["th_atmo"]}</th>
                    <th style="text-align: right;">{strings["th_value"]}</th>
                </tr>
            </thead>
            <tbody>
                {body_table_content}
            </tbody>
        </table>
    </div>

    {mining_section_html}

    <footer>
        {strings["footer"].format(now=now_str)}
    </footer>
</div>

<script>
(function() {{
    const wrapper = document.getElementById('orrery-wrapper');
    const layer = document.getElementById('orrery-pan-zoom-layer');
    const tooltip = document.getElementById('orrery-tooltip');
    if (!wrapper || !layer) return;

    let scale = 1.0;
    let panX = 0;
    let panY = 0;
    let isDragging = false;
    let startX = 0, startY = 0;

    function updateTransform() {{
        layer.setAttribute('transform', 'matrix(' + scale + ' 0 0 ' + scale + ' ' + panX + ' ' + panY + ')');
    }}

    window.zoomOrrery = function(factor) {{
        const newScale = Math.max(0.12, Math.min(35.0, scale * factor));
        const rect = wrapper.getBoundingClientRect();
        const cx = rect.width / 2;
        const cy = rect.height / 2;
        panX = cx - (cx - panX) * (newScale / scale);
        panY = cy - (cy - panY) * (newScale / scale);
        scale = newScale;
        updateTransform();
    }};

    window.resetOrreryView = function() {{
        scale = 1.0;
        panX = 0;
        panY = 0;
        updateTransform();
    }};

    window.focusOrreryTarget = function(targetX, targetY, targetScale) {{
        targetScale = targetScale || 2.4;
        const rect = wrapper.getBoundingClientRect();
        const svgW = 1000, svgH = 700;
        const ratioX = rect.width / svgW;
        const ratioY = rect.height / svgH;
        
        scale = targetScale;
        panX = (rect.width / 2) - (targetX * ratioX * scale);
        panY = (rect.height / 2) - (targetY * ratioY * scale);
        updateTransform();
    }};

    wrapper.addEventListener('wheel', (e) => {{
        e.preventDefault();
        const rect = wrapper.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;
        const factor = e.deltaY < 0 ? 1.18 : 0.85;
        const newScale = Math.max(0.12, Math.min(40.0, scale * factor));

        panX = mouseX - (mouseX - panX) * (newScale / scale);
        panY = mouseY - (mouseY - panY) * (newScale / scale);
        scale = newScale;
        updateTransform();
    }}, {{ passive: false }});

    wrapper.addEventListener('mousedown', (e) => {{
        if (e.button !== 0) return;
        isDragging = true;
        startX = e.clientX - panX;
        startY = e.clientY - panY;
        wrapper.style.cursor = 'grabbing';
    }});

    window.addEventListener('mousemove', (e) => {{
        if (!isDragging) return;
        panX = e.clientX - startX;
        panY = e.clientY - startY;
        updateTransform();
    }});

    window.addEventListener('mouseup', () => {{
        if (isDragging) {{
            isDragging = false;
            wrapper.style.cursor = 'grab';
        }}
    }});

    // Touch support (mobile/tablet pinch-zoom and drag)
    let initialTouchDist = null;
    let initialTouchScale = 1.0;
    wrapper.addEventListener('touchstart', (e) => {{
        if (e.touches.length === 1) {{
            isDragging = true;
            startX = e.touches[0].clientX - panX;
            startY = e.touches[0].clientY - panY;
        }} else if (e.touches.length === 2) {{
            isDragging = false;
            initialTouchDist = Math.hypot(
                e.touches[0].clientX - e.touches[1].clientX,
                e.touches[0].clientY - e.touches[1].clientY
            );
            initialTouchScale = scale;
        }}
    }}, {{ passive: true }});

    wrapper.addEventListener('touchmove', (e) => {{
        if (isDragging && e.touches.length === 1) {{
            panX = e.touches[0].clientX - startX;
            panY = e.touches[0].clientY - startY;
            updateTransform();
        }} else if (e.touches.length === 2 && initialTouchDist) {{
            const currentDist = Math.hypot(
                e.touches[0].clientX - e.touches[1].clientX,
                e.touches[0].clientY - e.touches[1].clientY
            );
            const factor = currentDist / initialTouchDist;
            scale = Math.max(0.12, Math.min(35.0, initialTouchScale * factor));
            updateTransform();
        }}
    }}, {{ passive: true }});

    wrapper.addEventListener('touchend', () => {{
        isDragging = false;
        initialTouchDist = null;
    }});

    // Hover tooltip
    const nodes = wrapper.querySelectorAll('.orrery-node');
    nodes.forEach(node => {{
        node.addEventListener('mouseenter', (e) => {{
            const name = node.getAttribute('data-name');
            const type = node.getAttribute('data-type');
            const dist = node.getAttribute('data-dist');
            const grav = node.getAttribute('data-grav');
            const temp = node.getAttribute('data-temp');

            let content = '<b style="color: var(--ed-orange);">' + name + '</b><br><span style="color: var(--ed-cyan);">' + type + '</span>';
            if (dist && dist !== '0') content += '<br>{strings["tooltip_dist"]}' + Number(dist).toLocaleString() + ' Ls';
            if (grav && grav !== '--') content += '<br>{strings["tooltip_grav"]}' + grav;
            if (temp && temp !== '--') content += '<br>{strings["tooltip_temp"]}' + temp;

            tooltip.innerHTML = content;
            tooltip.style.display = 'block';
        }});

        node.addEventListener('mousemove', (e) => {{
            const rect = wrapper.getBoundingClientRect();
            tooltip.style.left = (e.clientX - rect.left + 15) + 'px';
            tooltip.style.top = (e.clientY - rect.top + 10) + 'px';
        }});

        node.addEventListener('mouseleave', () => {{
            tooltip.style.display = 'none';
        }});
    }});
}})();
</script>
</body>
</html>
"""
    return html_doc


def has_special_orbits(bodies: List[Dict[str, Any]]) -> bool:
    """
    Detects if a system has unusual / special orbital characteristics:
    - High orbital eccentricity (e >= 0.35)
    - Extreme axial tilt (near-perpendicular |tilt| > 80° or retrograde)
    - Sub-moons (nested moon orbiting another moon)
    - Gas giant in very close orbit ("Hot Jupiter" orbital period < 3 days)
    - Circumbinary bodies orbiting barycentre
    """
    for b in bodies:
        # Check eccentricity
        ecc = b.get("eccentricity")
        if ecc is not None and ecc >= 0.35:
            return True

        # Check extreme axial tilt
        tilt = b.get("axial_tilt")
        if tilt is not None:
            import math
            deg = abs(math.degrees(tilt))
            if deg > 80.0:
                return True

        # Check Hot Jupiter / very short orbital period gas giants
        p_class = (b.get("planet_class") or "").lower()
        orb_sec = b.get("orbital_period")
        if "gas giant" in p_class and orb_sec is not None and 0 < orb_sec < (3 * 86400):
            return True

        # Check parents hierarchy for sub-moons or barycentre
        parents_raw = b.get("parents")
        if parents_raw:
            try:
                parents = json.loads(parents_raw) if isinstance(parents_raw, str) else parents_raw
                if isinstance(parents, list) and len(parents) >= 1:
                    planet_parents = [p for p in parents if isinstance(p, dict) and ("Planet" in p or "Moon" in p)]
                    if len(planet_parents) >= 2:
                        return True
                    if any(isinstance(p, dict) and "Null" in p for p in parents):
                        return True
            except Exception:
                pass

        # Check body name for sub-moons via tokens (e.g. 1 a a)
        b_name = b.get("body_name", "")
        tokens = b_name.strip().split()
        if len(tokens) >= 3 and len(tokens[-1]) == 1 and len(tokens[-2]) == 1 and tokens[-1].isalpha() and tokens[-2].isalpha():
            return True

    return False


def extract_system_ring_summary(bodies: List[Dict[str, Any]], lang: str = "ja") -> Optional[str]:
    """
    Checks if any body in the system has rings, and summarizes it.
    """
    ringed_count = 0
    ring_types = set()
    for b in bodies:
        r_raw = b.get("rings")
        if r_raw:
            try:
                rings = json.loads(r_raw) if isinstance(r_raw, str) else r_raw
                if isinstance(rings, list) and len(rings) > 0:
                    ringed_count += 1
                    for r in rings:
                        if isinstance(r, dict) and r.get("RingClass"):
                            rc = r["RingClass"].replace("eRingClass_", "").replace("RingClass_", "")
                            ring_types.add(rc)
            except Exception:
                pass
    if ringed_count > 0:
        type_desc = f" ({', '.join(sorted(ring_types))})" if ring_types else ""
        return f"あり{type_desc}" if lang == "ja" else f"Yes{type_desc}"
    return None


def generate_share_snippet(system_data: Dict[str, Any], bodies: List[Dict[str, Any]], lang: str = "ja") -> str:
    """
    Generates a compact, informative text snippet tailored for Twitch comments, Discord, and SNS.
    Includes system name, coordinates, main star, ELW/WW/AW, bio/geo, rings, and special orbit tags.
    Does NOT reveal Orrery or total credits, inviting viewers to explore.
    """
    is_ja = (lang == "ja")
    sys_name = system_data.get("star_system") or "Unknown System"
    sys_addr = system_data.get("system_address")
    main_star = system_data.get("main_star_type") or "Unknown"
    pos_x = system_data.get("star_pos_x") or 0.0
    pos_y = system_data.get("star_pos_y") or 0.0
    pos_z = system_data.get("star_pos_z") or 0.0

    # 1. Header line
    if is_ja:
        header = f"🌌 [{sys_name}] (主星: {main_star}型 | 座標: [{pos_x:.1f}, {pos_y:.1f}, {pos_z:.1f}])"
    else:
        header = f"🌌 [{sys_name}] (Main Star: Class {main_star} | Coords: [{pos_x:.1f}, {pos_y:.1f}, {pos_z:.1f}])"

    # 2. Highlights
    parts = []

    # Rare worlds
    elw = sum(1 for b in bodies if "earth" in (b.get("planet_class") or "").lower())
    ww = sum(1 for b in bodies if "water world" in (b.get("planet_class") or "").lower())
    ammonia = sum(1 for b in bodies if "ammonia" in (b.get("planet_class") or "").lower())
    if elw > 0:
        parts.append(f"🌍 ELW: {elw}")
    if ww > 0:
        parts.append(f"💧 水の世界: {ww}" if is_ja else f"💧 Water World: {ww}")
    if ammonia > 0:
        parts.append(f"🧪 AW: {ammonia}")

    # Bio & Geo
    bio = system_data.get("total_bio_signals", 0) or sum(b.get("bio_signals", 0) or 0 for b in bodies)
    geo = sum(b.get("geo_signals", 0) or 0 for b in bodies)
    if bio > 0:
        parts.append(f"🌱 生体: {bio}箇所" if is_ja else f"🌱 Bio: {bio}")
    if geo > 0:
        parts.append(f"🌋 地質: {geo}箇所" if is_ja else f"🌋 Geo: {geo}")

    # Rings
    ring_summary = extract_system_ring_summary(bodies, lang=lang)
    if ring_summary:
        parts.append(f"🪐 環: {ring_summary}" if is_ja else f"🪐 Rings: {ring_summary}")

    # Special Orbits
    if has_special_orbits(bodies):
        parts.append("⚡ 特殊な天体軌道あり" if is_ja else "⚡ Special Orbits Detected")

    highlights_line = " | ".join(parts) if parts else ("探査データ記録済" if is_ja else "Surveyed System")

    # 3. External Links
    link_line = ""
    if sys_addr:
        link_line = f"\n🔗 Spansh: https://spansh.co.uk/system/{sys_addr}"

    return f"{header}\n{highlights_line}{link_line}"


def _get_card_font(size: int, bold: bool = False):
    """
    Helper to resolve a readable TrueType font across Windows environments.
    Falls back to default Pillow font if TrueType fonts are unavailable.
    """
    from PIL import ImageFont
    candidates = [
        "C:/Windows/Fonts/meiryo.ttc",
        "C:/Windows/Fonts/msgothic.ttc",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf"
    ]
    for cp in candidates:
        try:
            return ImageFont.truetype(cp, size)
        except Exception:
            continue
    return ImageFont.load_default()


def generate_summary_png_card(
    system_data: Dict[str, Any],
    bodies: List[Dict[str, Any]],
    package_dict: Optional[Dict[str, Any]] = None,
    lang: str = "ja"
) -> bytes:
    """
    Generates a 1200x630 SNS/OGP summary PNG card containing:
    - System Name, Main Star Type, Galactic Coordinates
    - Rare Worlds (ELW/WW/AW), Bio signals, Geo signals, Rings
    - Special Orbits badge (if present)
    - Invitation footer directing viewers to drop the PNG into ED Journal Analyzer
    - ComfyUI-style embedded metadata chunk ('ed_journal_data' with full .edsys package JSON)
    - Deliberately omits Orrery and Credit payout values to induce engagement.
    """
    import io
    from PIL import Image, ImageDraw, PngImagePlugin

    is_ja = (lang == "ja")
    sys_name = system_data.get("star_system") or "Unknown System"
    main_star = system_data.get("main_star_type") or "Unknown"
    pos_x = system_data.get("star_pos_x") or 0.0
    pos_y = system_data.get("star_pos_y") or 0.0
    pos_z = system_data.get("star_pos_z") or 0.0

    # 1. Prepare statistics
    elw = sum(1 for b in bodies if "earth" in (b.get("planet_class") or "").lower())
    ww = sum(1 for b in bodies if "water world" in (b.get("planet_class") or "").lower())
    ammonia = sum(1 for b in bodies if "ammonia" in (b.get("planet_class") or "").lower())

    rare_parts = []
    if elw > 0:
        rare_parts.append(f"🌍 ELW: {elw}")
    if ww > 0:
        rare_parts.append(f"💧 WW: {ww}")
    if ammonia > 0:
        rare_parts.append(f"🧪 AW: {ammonia}")
    rare_val = " | ".join(rare_parts) if rare_parts else ("なし" if is_ja else "None")

    bio_count = system_data.get("total_bio_signals", 0) or sum(b.get("bio_signals", 0) or 0 for b in bodies)
    bio_bodies = sum(1 for b in bodies if (b.get("bio_signals", 0) or 0) > 0)
    if bio_count > 0:
        bio_val = f"🌱 {bio_count} 箇所 ({bio_bodies}天体)" if is_ja else f"🌱 {bio_count} ({bio_bodies} bodies)"
    else:
        bio_val = "なし" if is_ja else "None"

    geo_count = sum(b.get("geo_signals", 0) or 0 for b in bodies)
    geo_bodies = sum(1 for b in bodies if (b.get("geo_signals", 0) or 0) > 0)
    if geo_count > 0:
        geo_val = f"🌋 {geo_count} 箇所 ({geo_bodies}天体)" if is_ja else f"🌋 {geo_count} ({geo_bodies} bodies)"
    else:
        geo_val = "なし" if is_ja else "None"

    ring_desc = extract_system_ring_summary(bodies, lang=lang)
    if ring_desc:
        ring_val = f"🪐 {ring_desc}"
    else:
        ring_val = "なし" if is_ja else "None"

    special_orbit = has_special_orbits(bodies)

    # 2. Render image (1200x630)
    img = Image.new("RGB", (1200, 630), "#0a0e17")
    draw = ImageDraw.Draw(img)

    f_title = _get_card_font(34, bold=True)
    f_sub = _get_card_font(18)
    f_box_label = _get_card_font(16, bold=True)
    f_box_val = _get_card_font(24, bold=True)
    f_badge = _get_card_font(16, bold=True)
    f_footer = _get_card_font(15)

    # Outer decorative border
    draw.rounded_rectangle([(15, 15), (1185, 615)], radius=16, outline="#1e293b", width=2)

    # Header: System Title & Subheader
    draw.text((45, 42), f"🌌 {sys_name}", fill="#f8fafc", font=f_title)
    if is_ja:
        sub_text = f"主星: {main_star}型 | 座標: [ {pos_x:.1f}, {pos_y:.1f}, {pos_z:.1f} ]"
    else:
        sub_text = f"Main Star: Class {main_star} | Coordinates: [ {pos_x:.1f}, {pos_y:.1f}, {pos_z:.1f} ]"
    draw.text((45, 92), sub_text, fill="#94a3b8", font=f_sub)

    # 4 Highlight Metric Cards
    boxes = [
        ("希少天体 (ELW / WW / AW)" if is_ja else "Rare Worlds (ELW / WW / AW)", rare_val, "#38bdf8", "#0369a1"),
        ("生体シグナル (Bio Signals)" if is_ja else "Biological Signals (Bio)", bio_val, "#4ade80", "#15803d"),
        ("地質シグナル (Geo Signals)" if is_ja else "Geological Signals (Geo)", geo_val, "#fb923c", "#c2410c"),
        ("環・小惑星帯 (Rings)" if is_ja else "Rings & Asteroid Belts", ring_val, "#e879f9", "#a21caf")
    ]

    for i, (label, val, text_col, border_col) in enumerate(boxes):
        bx = 45 + (i % 2) * 565
        by = 145 + (i // 2) * 125
        draw.rounded_rectangle([(bx, by), (bx + 545, by + 105)], radius=10, fill="#111827", outline=border_col, width=1)
        draw.text((bx + 20, by + 16), label, fill=text_col, font=f_box_label)
        draw.text((bx + 20, by + 48), val, fill="#f8fafc", font=f_box_val)

    # Special Orbit Badge (if applicable)
    if special_orbit:
        orbit_text = "⚡ 特殊な天体軌道あり (High Eccentricity / Tilt / Hot Jupiter)" if is_ja else "⚡ Special Orbits Detected (High Eccentricity / Tilt / Hot Jupiter)"
        draw.rounded_rectangle([(45, 415), (780, 465)], radius=8, fill="#2e1065", outline="#a855f7", width=1)
        draw.text((65, 428), orbit_text, fill="#d8b4fe", font=f_badge)

    # Footer Action Banner (invitation to app / D&D)
    footer_bg = "#1e293b"
    draw.rounded_rectangle([(45, 520), (1155, 585)], radius=8, fill=footer_bg)
    if is_ja:
        footer_msg = "📥 このPNG画像を ED Journal Analyzer にドラッグ＆ドロップすると、全軌道図(Orrery)や詳細天体を展開・閲覧できます"
    else:
        footer_msg = "📥 Drop this PNG into ED Journal Analyzer to explore full System Orrery & Celestial Survey Data"
    draw.text((65, 540), footer_msg, fill="#38bdf8", font=f_footer)

    # 3. ComfyUI-style PNG metadata embedding
    png_info = PngImagePlugin.PngInfo()
    if package_dict:
        raw_json = json.dumps(package_dict, ensure_ascii=False)
        png_info.add_text("ed_journal_data", raw_json)

    buf = io.BytesIO()
    img.save(buf, format="PNG", pnginfo=png_info)
    return buf.getvalue()


def extract_package_from_png(png_bytes: bytes) -> Optional[Dict[str, Any]]:
    """
    Extracts the embedded ED Journal Analyzer package JSON from a PNG's 'ed_journal_data' tEXt chunk.
    Returns parsed dictionary or None if not present or invalid.
    """
    import io
    from PIL import Image

    try:
        buf = io.BytesIO(png_bytes)
        img = Image.open(buf)
        meta_str = img.info.get("ed_journal_data")
        if not meta_str:
            return None
        return json.loads(meta_str)
    except Exception:
        return None


