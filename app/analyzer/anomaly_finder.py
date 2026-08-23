import re

MASS_CODE_REGEX = re.compile(r'\b[A-Za-z]+-[A-Za-z]\s+([a-hA-H])(?:\d+|-|\b)', re.IGNORECASE)

# Standard expected mass code bounds for main star types
# Format: star_type_prefix: max_standard_mass_code ('a'..'h')
# If actual mass code is greater than standard, it's considered unusually heavy!
STANDARD_MAX_MASS_CODE = {
    "L": "b",
    "T": "b",
    "Y": "b",
    "TTS": "b",
    "M": "c",
    "K": "c",
    "G": "d",
    "F": "d",
    "A": "e",
    "N": "e",       # Neutron stars are standard in d/e-box; f/g/h is extreme
    "D": "d",       # White dwarfs are standard in d-box; e/f/g/h is heavy
    "B": "f",       # B-stars are standard up to e/f; g/h is heavy
    "O": "g",       # O-stars are standard up to g; h is supermassive box
}

def extract_mass_code(system_name: str) -> str | None:
    if not system_name:
        return None
    m = MASS_CODE_REGEX.search(system_name)
    if m:
        return m.group(1).lower()
    return None

def detect_heavy_mass_code(system_name: str, star_type: str) -> dict | None:
    if not system_name or not star_type:
        return None
    mc = extract_mass_code(system_name)
    if not mc:
        return None
    
    st = star_type.upper()
    prefix = None
    if st in ["N", "H", "G", "F", "A", "B", "O", "K", "M", "L", "T", "Y", "TTS"]:
        prefix = st
    elif st.startswith("D"):
        prefix = "D"
    elif st.startswith("W"):
        prefix = "W"
    elif st.startswith("C") or st.startswith("S"):
        prefix = "C"
    
    if not prefix:
        return None
        
    max_standard = STANDARD_MAX_MASS_CODE.get(prefix)
    if max_standard and ord(mc) > ord(max_standard):
        diff = ord(mc) - ord(max_standard)
        urgency = "超高質量ボックス" if diff >= 2 else "通常より高質量ボックス"
        return {
            "type": "heavy_mass_code",
            "tag": f"Heavy Mass Code ({mc.upper()}-box)",
            "color": "magenta" if diff >= 2 else "orange",
            "desc": f"{urgency}: {star_type}型星が {mc.upper()}クラス星系コードに存在 (通常 {max_standard.upper()} 以下)"
        }
    return None

def detect_anomalies(body: dict) -> list:
    """
    Analyzes body attributes and returns a list of detected anomaly tags and descriptions.
    """
    anomalies = []

    # 1. Rare Stars & Heavy Mass Code
    star_type = (body.get("star_type") or "").upper()
    star_system = body.get("star_system") or ""
    
    if star_type:
        # Check heavy mass code anomaly
        heavy_anomaly = detect_heavy_mass_code(star_system, star_type)
        if heavy_anomaly:
            anomalies.append(heavy_anomaly)

    if star_type in ["H", "SUPERMASSIVEBLACKHOLE"]:
        anomalies.append({"type": "rare_star", "tag": "Black Hole", "color": "purple", "desc": "ブラックホール"})
    elif star_type == "N":
        anomalies.append({"type": "rare_star", "tag": "Neutron Star", "color": "cyan", "desc": "中性子星 (FSD Supercharge)"})
    elif star_type.startswith("D"):
        anomalies.append({"type": "rare_star", "tag": "White Dwarf", "color": "blue", "desc": "白色矮星"})
    elif star_type.startswith("W"):
        anomalies.append({"type": "rare_star", "tag": "Wolf-Rayet", "color": "gold", "desc": "超高温・大質量ウォルフ・ライエ星"})
    elif any(star_type.startswith(c) for c in ["C", "CS", "CN", "CJ", "CH", "MS", "S"]):
        anomalies.append({"type": "rare_star", "tag": "Carbon Star", "color": "orange", "desc": "炭素星/S型星"})
    elif "SUPERGIANT" in star_type or "GIANT" in star_type or star_type in ["O", "B"]:
        anomalies.append({"type": "rare_star", "tag": "Giant/O/B Star", "color": "yellow", "desc": f"大質量・巨星 ({star_type})"})

    # 2. Rare / High-Value Planets
    planet_class = (body.get("planet_class") or "").lower()
    tf_state = (body.get("terraforming_state") or "").lower()
    is_tf = "terraformable" in tf_state or "candidate for terraforming" in tf_state

    if "earthlike" in planet_class or "earth-like" in planet_class:
        anomalies.append({"type": "rare_planet", "tag": "Earth-like World", "color": "green", "desc": "地球型惑星 (最高探査価値)"})
    elif "ammonia world" in planet_class:
        anomalies.append({"type": "rare_planet", "tag": "Ammonia World", "color": "teal", "desc": "アンモニアワールド (超高価値・レア)"})
    elif "water world" in planet_class:
        if is_tf:
            anomalies.append({"type": "rare_planet", "tag": "Terraformable Water World", "color": "deep-blue", "desc": "テラフォーミング可能海洋惑星 (3M+ Cr)"})
        else:
            anomalies.append({"type": "rare_planet", "tag": "Water World", "color": "light-blue", "desc": "海洋惑星 (1M+ Cr)"})
    elif is_tf:
        anomalies.append({"type": "terraformable", "tag": "Terraformable", "color": "lime", "desc": f"テラフォーミング候補 ({body.get('planet_class')})"})

    # 3. Orbital Anomalies (特殊な周回・軌道)
    eccentricity = body.get("eccentricity")
    if eccentricity is not None and eccentricity >= 0.8:
        anomalies.append({"type": "extreme_orbit", "tag": "Extreme Eccentricity", "color": "magenta", "desc": f"極端な高離心率軌道 (e = {eccentricity:.3f})"})

    orbital_period = body.get("orbital_period")  # in seconds
    if orbital_period and orbital_period > 0:
        period_days = orbital_period / 86400.0
        if period_days <= 0.2:
            anomalies.append({"type": "extreme_orbit", "tag": "Ultra-Fast Orbit", "color": "pink", "desc": f"超短公転周期 ({period_days*24:.1f} 時間)"})

    rotation_period = body.get("rotation_period")  # in seconds
    if rotation_period and abs(rotation_period) > 0:
        rot_hours = abs(rotation_period) / 3600.0
        if rot_hours <= 2.0 and not body.get("tidal_lock"):
            anomalies.append({"type": "extreme_spin", "tag": "Rapid Spinner", "color": "pink", "desc": f"超高速自転 ({rot_hours:.1f} 時間)"})

    inclination = body.get("orbital_inclination")
    if inclination is not None and (inclination > 90.0 or inclination < -90.0):
        anomalies.append({"type": "extreme_orbit", "tag": "Retrograde Orbit", "color": "purple", "desc": f"逆行軌道 (傾斜角 {inclination:.1f}°)"})

    # 4. Extreme Gravity & Surface Conditions (Landable bodies only)
    gravity_g = body.get("surface_gravity_g")
    if gravity_g is None and body.get("surface_gravity"):
        gravity_g = body.get("surface_gravity") / 9.80665
    
    if body.get("landable") and gravity_g is not None:
        if gravity_g >= 3.0:
            anomalies.append({"type": "extreme_gravity", "tag": f"Extreme High-G ({gravity_g:.2f}G)", "color": "red", "desc": "超高重力・着陸危険 (Extreme High-G Hazard)"})
        elif gravity_g >= 1.5:
            anomalies.append({"type": "high_gravity", "tag": f"High-G ({gravity_g:.2f}G)", "color": "dark-orange", "desc": "高重力環境 (High-G Landing)"})

    # 5. Rings
    rings = body.get("rings")
    if rings:
        if isinstance(rings, str):
            import json
            try:
                rings = json.loads(rings)
            except Exception:
                rings = []
        if body.get("star_type") and len(rings) > 0:
            anomalies.append({"type": "ringed_star", "tag": "Ringed Star", "color": "amber", "desc": "リングを持つ恒星"})
        for ring in rings:
            outer_rad_km = ring.get("OuterRad", 0) / 1000.0
            if outer_rad_km >= 5000000:
                anomalies.append({"type": "giant_ring", "tag": "Giant Ring System", "color": "gold", "desc": f"巨大リング (外径 {outer_rad_km:,.0f} km)"})
                break

    # 6. Volcanism
    volcanism = (body.get("volcanism") or "").lower()
    if volcanism and volcanism != "none":
        anomalies.append({"type": "volcanism", "tag": "Active Volcanism", "color": "orange", "desc": f"火山活動 ({body.get('volcanism')})"})

    return anomalies
