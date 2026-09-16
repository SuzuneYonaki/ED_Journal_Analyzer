import json
import re
import shutil
import subprocess
from pathlib import Path
import pytest

def parse_parents_list(parents_raw):
    if not parents_raw:
        return []
    if isinstance(parents_raw, list):
        return parents_raw
    try:
        parsed = json.loads(parents_raw)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []

def get_body_short_name(full_name: str, system_name: str) -> str:
    if not full_name:
        return ""
    sys = system_name or ""
    short = full_name.strip()
    if sys and short.startswith(sys):
        short = short[len(sys):].strip()
    return short or full_name

def extract_star_letter(body_name: str):
    if not body_name:
        return None
    clean = body_name.strip()
    m = re.search(r'(?:^|\s+)([A-Z]{1,4})\*?$', clean)
    if m:
        return m.group(1)
    return None

def analyze_system_stars(flat_bodies, system_name):
    all_stars = [b for b in flat_bodies if b.get("star_type") or (b.get("body_type") and str(b.get("body_type")).lower() == "star")]
    root_stars = []
    dwarf_planets = []
    
    for b in all_stars:
        short = get_body_short_name(b.get("body_name", ""), system_name).strip()
        tokens = short.split()
        parents_list = parse_parents_list(b.get("parents"))
        
        has_parent_star = len(parents_list) > 0 and "Star" in parents_list[0]
        is_orbiting_name = (
            (len(tokens) >= 2 and re.match(r'^(?:[A-Z]{1,4}|[A-Z][a-z])$', tokens[0]) and tokens[1].isdigit())
            or (len(tokens) > 0 and tokens[0].isdigit())
        )
        
        if has_parent_star or is_orbiting_name:
            dwarf_planets.append(b)
        else:
            root_stars.append(b)
            
    root_stars.sort(key=lambda s: (abs(s.get("distance_from_arrival_ls", 0)), s.get("body_id", 0)))
    
    claimed_letters = set()
    star_letter_map = {}
    
    for s in root_stars:
        letter = extract_star_letter(s.get("body_name", ""))
        if letter and letter not in claimed_letters:
            claimed_letters.add(letter)
            star_letter_map[s.get("body_id")] = letter
            
    alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    alpha_idx = 0
    for s in root_stars:
        if s.get("body_id") not in star_letter_map:
            while alpha_idx < len(alphabet) and alphabet[alpha_idx] in claimed_letters:
                alpha_idx += 1
            assigned = alphabet[alpha_idx] if alpha_idx < len(alphabet) else f"S{s.get('body_id')}"
            claimed_letters.add(assigned)
            star_letter_map[s.get("body_id")] = assigned
            
    return root_stars, dwarf_planets, star_letter_map

def analyze_body_designation(body_or_name, system_name, is_star_or_letter_map=False, root_stars=None, body_by_id_map=None):
    if root_stars is None:
        root_stars = []
    if body_by_id_map is None:
        body_by_id_map = {}
        
    if isinstance(body_or_name, dict):
        body = body_or_name
    else:
        body = {"body_name": str(body_or_name), "body_type": "Star" if is_star_or_letter_map is True else "Planet"}
        
    star_letter_map = is_star_or_letter_map if isinstance(is_star_or_letter_map, dict) else {}
    is_star_type = bool(body.get("star_type") or (body.get("body_type") and str(body.get("body_type")).lower() == "star") or is_star_or_letter_map is True)
    is_root_star = any(rs.get("body_id") == body.get("body_id") for rs in root_stars)
    
    if is_root_star:
        assigned_letter = star_letter_map.get(body.get("body_id"), "A")
        raw_short = get_body_short_name(body.get("body_name", ""), system_name).strip()
        return {
            "shortName": raw_short or (body.get("body_name", "").strip() or "Star"),
            "starGroup": assigned_letter,
            "isStar": True,
            "planetNum": None,
            "moonLetter": None,
            "submoonLetter": None,
            "level": 0
        }
        
    short = get_body_short_name(body.get("body_name", ""), system_name).strip()
    tokens = short.split()
    parents_list = parse_parents_list(body.get("parents"))
    
    star_group = "A"
    planet_num = None
    moon_letter = None
    submoon_letter = None
    level = 1
    
    # 1. Determine star_group from direct parent if possible
    if parents_list:
        direct_parent = parents_list[0]
        if "Star" in direct_parent and direct_parent["Star"] in star_letter_map:
            star_group = star_letter_map[direct_parent["Star"]]
        elif "Planet" in direct_parent:
            level = 2
            if len(parents_list) > 1 and "Planet" in parents_list[1]:
                level = 3
            parent_planet = body_by_id_map.get(direct_parent["Planet"])
            if parent_planet and parent_planet.get("starGroup"):
                star_group = parent_planet["starGroup"]
                
    # 2. Parse name tokens
    idx = 0
    if tokens:
        if re.match(r'^[A-Z]{1,4}$', tokens[0]) or (re.match(r'^[A-Z][a-z]$', tokens[0]) and len(tokens) >= 2 and tokens[1].isdigit()):
            star_group = tokens[0].upper()
            idx = 1
            
        if idx < len(tokens):
            if tokens[idx].isdigit():
                planet_num = int(tokens[idx])
                idx += 1
                if level < 2:
                    level = 1
                if idx < len(tokens) and re.match(r'^[a-z]$', tokens[idx], re.I):
                    moon_letter = tokens[idx].lower()
                    idx += 1
                    level = 2
                    if idx < len(tokens) and re.match(r'^[a-z]$', tokens[idx], re.I):
                        submoon_letter = tokens[idx].lower()
                        level = 3
            elif re.match(r'^[a-z]$', tokens[idx], re.I):
                moon_letter = tokens[idx].lower()
                level = 2
                
    if is_star_type and planet_num is None and level < 2:
        level = 0
        
    final_short_name = short if planet_num is not None else (short or body.get("body_name", ""))
    return {
        "shortName": final_short_name,
        "starGroup": star_group,
        "isStar": is_star_type and (planet_num is None and level == 0),
        "planetNum": planet_num,
        "moonLetter": moon_letter,
        "submoonLetter": submoon_letter,
        "level": level
    }

def get_star_group_sort_score(key: str) -> float:
    if not key or not re.match(r'^[A-Z]+$', key.upper().strip()):
        return 9999.0
    clean = key.upper().strip()
    if len(clean) == 1:
        return (ord(clean) - ord('A') + 1) * 100.0
    
    start_val = (ord(clean[0]) - ord('A') + 1) * 100.0
    end_val = (ord(clean[-1]) - ord('A') + 1) * 100.0
    
    if len(clean) == 2:
        return (start_val + end_val) / 2.0
    else:
        if clean[0] != 'A':
            return start_val - 10.0
        else:
            return end_val + 50.0

def build_system_map_tree(flat_bodies, system_name):
    if not flat_bodies:
        return []
    root_stars, dwarf_planets, star_letter_map = analyze_system_stars(flat_bodies, system_name)
    body_by_id_map = {b.get("body_id"): b for b in flat_bodies}
    
    analyzed_list = []
    for b in flat_bodies:
        info = analyze_body_designation(b, system_name, star_letter_map, root_stars, body_by_id_map)
        combined = {**b, **info, "moons": [], "submoons": []}
        body_by_id_map[b.get("body_id")] = combined
        analyzed_list.append(combined)
        
    star_map = {}
    stars = [b for b in analyzed_list if b["isStar"]]
    if not stars:
        star_map["A"] = {
            "starKey": "A",
            "isBarycentre": False,
            "rootStar": analyzed_list[0],
            "planets": []
        }
    else:
        for s in stars:
            key = s["starGroup"]
            if key in star_map:
                key = f"{key}-{s['body_id']}"
            star_map[key] = {
                "starKey": key,
                "isBarycentre": False,
                "rootStar": s,
                "planets": []
            }
            
    def get_or_create_section(s_group, sample_body=None):
        if s_group in star_map:
            return star_map[s_group]
        is_multi = len(s_group) > 1
        bary_node = {
            "body_id": f"barycentre-{s_group}",
            "body_name": f"{system_name} [{s_group}] Orbit" if is_multi else f"{system_name} {s_group}",
            "shortName": f"[{s_group}]" if is_multi else s_group,
            "starGroup": s_group,
            "isStar": False,
            "isBarycentre": is_multi,
            "distance_from_arrival_ls": sample_body.get("distance_from_arrival_ls", 0) if sample_body else 0,
            "level": 0,
            "moons": [],
            "submoons": []
        }
        sec = {
            "starKey": s_group,
            "isBarycentre": is_multi,
            "rootStar": bary_node,
            "planets": []
        }
        star_map[s_group] = sec
        return sec
        
    planets = [b for b in analyzed_list if not b["isStar"] and b["level"] == 1]
    moons = [b for b in analyzed_list if not b["isStar"] and b["level"] == 2]
    submoons = [b for b in analyzed_list if not b["isStar"] and b["level"] == 3]
    
    planet_by_id_map = {}
    planet_key_map = {}
    
    for p in planets:
        s_group = p.get("starGroup") or "A"
        sec = get_or_create_section(s_group, p)
        planet_by_id_map[p.get("body_id")] = p
        p_num = p.get("planetNum") if p.get("planetNum") is not None else p.get("distance_from_arrival_ls", 0)
        key = f"{s_group}-{p_num}"
        planet_key_map[key] = p
        sec["planets"].append(p)
        
    for m in moons:
        s_group = m.get("starGroup") or "A"
        parents_list = parse_parents_list(m.get("parents"))
        attached = False
        if parents_list and "Planet" in parents_list[0]:
            parent_planet = planet_by_id_map.get(parents_list[0]["Planet"])
            if parent_planet:
                parent_planet["moons"].append(m)
                attached = True
        if not attached:
            key = f"{s_group}-{m.get('planetNum')}"
            if key in planet_key_map:
                planet_key_map[key]["moons"].append(m)
            else:
                sec = get_or_create_section(s_group, m)
                placeholder = {
                    "body_id": f"p-{key}",
                    "body_name": f"{system_name} {s_group} {m.get('planetNum', '')}".strip(),
                    "shortName": f"{s_group + ' ' if s_group != 'A' else ''}{m.get('planetNum') or 'Planet'}",
                    "starGroup": s_group,
                    "isStar": False,
                    "planetNum": m.get("planetNum"),
                    "distance_from_arrival_ls": m.get("distance_from_arrival_ls", 0),
                    "level": 1,
                    "moons": [m],
                    "submoons": []
                }
                planet_key_map[key] = placeholder
                sec["planets"].append(placeholder)
                
    for sm in submoons:
        s_group = sm.get("starGroup") or "A"
        parents_list = parse_parents_list(sm.get("parents"))
        attached = False
        if parents_list and "Planet" in parents_list[0]:
            parent_moon = next((b for b in analyzed_list if b.get("body_id") == parents_list[0]["Planet"]), None)
            if parent_moon and "submoons" in parent_moon:
                parent_moon["submoons"].append(sm)
                attached = True
        if not attached:
            key = f"{s_group}-{sm.get('planetNum')}"
            if key in planet_key_map:
                p = planet_key_map[key]
                parent_moon = next((m for m in p["moons"] if m.get("moonLetter") == sm.get("moonLetter")), None)
                if parent_moon:
                    parent_moon["submoons"].append(sm)
                else:
                    p["moons"].append(sm)
                    
    # 5.5 Extract Asteroid Belts from Stars and add as independent orbital nodes in the rail
    for s in stars:
        raw_rings = s.get("rings_list")
        if not raw_rings and s.get("rings") and s.get("rings") not in ['[]', '""']:
            try:
                raw_rings = json.loads(s.get("rings")) if isinstance(s.get("rings"), str) else s.get("rings")
            except Exception:
                raw_rings = []
        raw_rings = raw_rings if isinstance(raw_rings, list) else []
        belt_items = [r for r in raw_rings if r and "belt" in (r.get("Name") or "").lower()]

        if belt_items:
            s_group = s.get("starGroup") or "A"
            sec = get_or_create_section(s_group, s)
            for b_idx, belt in enumerate(belt_items):
                belt_avg_dist_m = ((belt.get("InnerRad", 0) + belt.get("OuterRad", 0)) / 2.0) if (belt.get("InnerRad") and belt.get("OuterRad")) else (belt.get("InnerRad") or belt.get("OuterRad") or 0)
                belt_dist_ls = (belt_avg_dist_m / 299792458.0) if belt_avg_dist_m else s.get("distance_from_arrival_ls", 0)
                
                clean_short_name = belt.get("Name") or "Belt"
                if system_name and clean_short_name.startswith(system_name):
                    clean_short_name = clean_short_name[len(system_name):].strip()
                if s.get("starGroup") and clean_short_name.startswith(s.get("starGroup") + " "):
                    clean_short_name = clean_short_name[len(s.get("starGroup")) + 1:].strip()
                clean_short_name = re.sub(r'^Asteroid\s+Belt', 'Belt', clean_short_name, flags=re.IGNORECASE).strip()
                if not clean_short_name:
                    clean_short_name = f"Belt {b_idx + 1}"

                belt_node = {
                    "body_id": f"belt-{s.get('body_id')}-{b_idx}",
                    "body_name": belt.get("Name") or f"{s.get('body_name')} Belt",
                    "shortName": clean_short_name,
                    "starGroup": s_group,
                    "isStar": False,
                    "isAsteroidBelt": True,
                    "planetNum": None,
                    "semi_major_axis": belt_avg_dist_m,
                    "distance_from_arrival_ls": belt_dist_ls,
                    "planet_class": "Asteroid Belt",
                    "level": 1,
                    "moons": [],
                    "submoons": []
                }
                sec["planets"].append(belt_node)

    def get_body_orbital_distance_ls(body, parent_star=None):
        sma = body.get("semi_major_axis")
        if sma is not None and sma > 0:
            return sma / 299792458.0
        dist = body.get("distance_from_arrival_ls")
        if dist is not None:
            if parent_star and parent_star.get("distance_from_arrival_ls") is not None:
                return abs(dist - parent_star.get("distance_from_arrival_ls", 0))
            return dist
        return 0.0

    star_sections = list(star_map.values())
    star_sections.sort(key=lambda s: get_star_group_sort_score(s["starKey"]))
    
    for sec in star_sections:
        parent_star = sec.get("rootStar")
        sec["planets"].sort(key=lambda p: (
            round(get_body_orbital_distance_ls(p, parent_star), 3),
            p.get("planetNum") if p.get("planetNum") is not None else 0,
            p.get("body_id") if isinstance(p.get("body_id"), int) else 0
        ))
        for p in sec["planets"]:
            p["moons"].sort(key=lambda m: (
                m.get("moonLetter") or "",
                round(get_body_orbital_distance_ls(m), 3),
                m.get("body_id") if isinstance(m.get("body_id"), int) else 0
            ))
            for m in p["moons"]:
                m["submoons"].sort(key=lambda sm: (
                    sm.get("submoonLetter") or "",
                    round(get_body_orbital_distance_ls(sm), 3),
                    sm.get("body_id") if isinstance(sm.get("body_id"), int) else 0
                ))
                
    return star_sections

def run_js_build_system_map_tree(flat_bodies, system_name):
    """Executes the actual app/ui/js/system_map.js via Node.js for true end-to-end verification."""
    node_exe = shutil.which("node")
    if not node_exe:
        pytest.skip("Node.js is not installed or not in PATH")
        
    js_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "system_map.js"
    runner_script = f"""
    const fs = require('fs');
    global.state = {{ selectedSystem: {{ star_system: {json.dumps(system_name)} }} }};
    const code = fs.readFileSync({json.dumps(str(js_path))}, 'utf8');
    eval(code);
    const bodies = {json.dumps(flat_bodies)};
    const tree = buildSystemMapTree(bodies, {json.dumps(system_name)});
    console.log(JSON.stringify(tree));
    """
    proc = subprocess.run([node_exe, "-e", runner_script], capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def test_designation_parsing():
    assert analyze_body_designation("LHS 47 A", "LHS 47", True)["isStar"] is True
    assert analyze_body_designation("LHS 47 A", "LHS 47", True)["level"] == 0
    assert analyze_body_designation("LHS 47 A", "LHS 47", True)["starGroup"] == "A"
    
    # Circumbinary planet
    ab1 = analyze_body_designation("LHS 47 AB 1", "LHS 47", False)
    assert ab1["isStar"] is False
    assert ab1["level"] == 1
    assert ab1["starGroup"] == "AB"
    assert ab1["planetNum"] == 1
    
    # Circumbinary moon
    ab5a = analyze_body_designation("LHS 47 AB 5 a", "LHS 47", False)
    assert ab5a["isStar"] is False
    assert ab5a["level"] == 2
    assert ab5a["starGroup"] == "AB"
    assert ab5a["planetNum"] == 5
    assert ab5a["moonLetter"] == "a"
    
    # 4-star multi-star circumbinary planet
    abcd1e = analyze_body_designation("Ross 775 ABCD 1 e", "Ross 775", False)
    assert abcd1e["starGroup"] == "ABCD"
    assert abcd1e["planetNum"] == 1
    assert abcd1e["moonLetter"] == "e"
    assert abcd1e["level"] == 2


def test_star_group_ordering():
    keys = ["A", "B", "AB", "C", "D", "CD", "ABCD", "E", "BCD"]
    sorted_keys = sorted(keys, key=get_star_group_sort_score)
    # Expected: A (100) -> AB (150) -> BCD (190) -> B (200) -> C (300) -> CD (350) -> D (400) -> ABCD (450) -> E (500)
    assert sorted_keys == ["A", "AB", "BCD", "B", "C", "CD", "D", "ABCD", "E"]
    
    # Test LHS 47
    lhs47_keys = ["A", "B", "AB"]
    assert sorted(lhs47_keys, key=get_star_group_sort_score) == ["A", "AB", "B"]
    
    # Test Ross 775
    ross775_keys = ["A", "B", "C", "D", "CD", "ABCD", "E"]
    assert sorted(ross775_keys, key=get_star_group_sort_score) == ["A", "B", "C", "CD", "D", "ABCD", "E"]


def test_circumstellar_stars_rail():
    """Verify that circumstellar stars (A 1, A 2, A 8, B 1, B 9, AB 1, Ab 2)
    are parsed as planets/dwarfs on the parent star's / circumbinary rail."""
    bodies = [
        {"body_id": 1, "body_name": "HIP 99999 A", "star_type": "G", "parents": '[{"Null": 0}]', "distance_from_arrival_ls": 0.0},
        {"body_id": 2, "body_name": "HIP 99999 B", "star_type": "K", "parents": '[{"Null": 0}]', "distance_from_arrival_ls": 3000.0},
        {"body_id": 3, "body_name": "HIP 99999 A 1", "star_type": "T", "parents": '[{"Star": 1}]', "distance_from_arrival_ls": 25.0},
        {"body_id": 4, "body_name": "HIP 99999 A 2", "planet_class": "High metal content body", "parents": '[{"Star": 1}]', "distance_from_arrival_ls": 80.0},
        {"body_id": 5, "body_name": "HIP 99999 A 8", "star_type": "Y", "parents": '[{"Star": 1}]', "distance_from_arrival_ls": 500.0},
        {"body_id": 6, "body_name": "HIP 99999 B 1", "star_type": "L", "parents": '[{"Star": 2}]', "distance_from_arrival_ls": 3050.0},
        {"body_id": 7, "body_name": "HIP 99999 B 9", "star_type": "M", "parents": '[{"Star": 2}]', "distance_from_arrival_ls": 4500.0},
        {"body_id": 8, "body_name": "HIP 99999 AB 1", "planet_class": "Icy body", "parents": '[{"Null": 0}]', "distance_from_arrival_ls": 8000.0},
        {"body_id": 9, "body_name": "HIP 99999 Ab 2", "star_type": "T", "parents": '[{"Null": 0}]', "distance_from_arrival_ls": 12000.0},
    ]
    tree = build_system_map_tree(bodies, "HIP 99999")
    assert len(tree) == 3
    # Section A
    assert tree[0]["starKey"] == "A"
    assert [p["shortName"] for p in tree[0]["planets"]] == ["A 1", "A 2", "A 8"]
    # Section AB
    assert tree[1]["starKey"] == "AB"
    assert [p["shortName"] for p in tree[1]["planets"]] == ["AB 1", "Ab 2"]
    # Section B
    assert tree[2]["starKey"] == "B"
    assert [p["shortName"] for p in tree[2]["planets"]] == ["B 1", "B 9"]

    # Verify directly via system_map.js Node execution
    js_tree = run_js_build_system_map_tree(bodies, "HIP 99999")
    assert len(js_tree) == 3
    assert js_tree[0]["starKey"] == "A"
    assert [p["shortName"] for p in js_tree[0]["planets"]] == ["A 1", "A 2", "A 8"]
    assert js_tree[1]["starKey"] == "AB"
    assert [p["shortName"] for p in js_tree[1]["planets"]] == ["AB 1", "Ab 2"]
    assert js_tree[2]["starKey"] == "B"
    assert [p["shortName"] for p in js_tree[2]["planets"]] == ["B 1", "B 9"]


def test_custom_named_bodies_shinrarta():
    """Verify Shinrarta Dezhra where Founders World is placed between A 1 and A 2 on Star A rail."""
    bodies = [
        {"body_id": 1, "body_name": "Shinrarta Dezhra A", "star_type": "F", "parents": '[{"Null": 0}]', "distance_from_arrival_ls": 0.0},
        {"body_id": 2, "body_name": "Shinrarta Dezhra A 1", "planet_class": "High metal content body", "parents": '[{"Star": 1}]', "distance_from_arrival_ls": 120.0},
        {"body_id": 3, "body_name": "Founders World", "planet_class": "Earthlike body", "parents": '[{"Star": 1}]', "distance_from_arrival_ls": 340.0},
        {"body_id": 4, "body_name": "Shinrarta Dezhra A 2", "planet_class": "Gas giant with water based life", "parents": '[{"Star": 1}]', "distance_from_arrival_ls": 650.0},
        {"body_id": 5, "body_name": "Shinrarta Dezhra AB 1", "planet_class": "Icy body", "parents": '[{"Null": 0}]', "distance_from_arrival_ls": 2000.0}
    ]
    tree = build_system_map_tree(bodies, "Shinrarta Dezhra")
    assert len(tree) == 2
    assert tree[0]["starKey"] == "A"
    assert [p["shortName"] for p in tree[0]["planets"]] == ["A 1", "Founders World", "A 2"]
    assert tree[1]["starKey"] == "AB"
    assert [p["shortName"] for p in tree[1]["planets"]] == ["AB 1"]

    # Verify directly via system_map.js Node execution
    js_tree = run_js_build_system_map_tree(bodies, "Shinrarta Dezhra")
    assert len(js_tree) == 2
    assert js_tree[0]["starKey"] == "A"
    assert [p["shortName"] for p in js_tree[0]["planets"]] == ["A 1", "Founders World", "A 2"]
    assert js_tree[1]["starKey"] == "AB"
    assert [p["shortName"] for p in js_tree[1]["planets"]] == ["AB 1"]


def test_custom_named_bodies_sol():
    """Verify Sol system where Earth has Moon attached as its child moon."""
    bodies = [
        {"body_id": 1, "body_name": "Sol", "star_type": "G", "parents": "[]", "distance_from_arrival_ls": 0.0},
        {"body_id": 2, "body_name": "Mercury", "planet_class": "Metal rich body", "parents": '[{"Star": 1}]', "distance_from_arrival_ls": 180.0},
        {"body_id": 3, "body_name": "Venus", "planet_class": "High metal content body", "parents": '[{"Star": 1}]', "distance_from_arrival_ls": 360.0},
        {"body_id": 4, "body_name": "Earth", "planet_class": "Earthlike body", "parents": '[{"Star": 1}]', "distance_from_arrival_ls": 500.0},
        {"body_id": 5, "body_name": "Moon", "planet_class": "Rocky body", "parents": '[{"Planet": 4}, {"Star": 1}]', "distance_from_arrival_ls": 501.0},
        {"body_id": 6, "body_name": "Mars", "planet_class": "High metal content body", "parents": '[{"Star": 1}]', "distance_from_arrival_ls": 750.0}
    ]
    tree = build_system_map_tree(bodies, "Sol")
    assert len(tree) == 1
    assert tree[0]["starKey"] == "A"
    planets = tree[0]["planets"]
    assert [p["shortName"] for p in planets] == ["Mercury", "Venus", "Earth", "Mars"]
    earth = next(p for p in planets if p["shortName"] == "Earth")
    assert len(earth["moons"]) == 1
    assert earth["moons"][0]["shortName"] == "Moon"

    # Verify directly via system_map.js Node execution
    js_tree = run_js_build_system_map_tree(bodies, "Sol")
    assert len(js_tree) == 1
    js_planets = js_tree[0]["planets"]
    assert [p["shortName"] for p in js_planets] == ["Mercury", "Venus", "Earth", "Mars"]
    js_earth = next(p for p in js_planets if p["shortName"] == "Earth")
    assert len(js_earth["moons"]) == 1
    assert js_earth["moons"][0]["shortName"] == "Moon"


def test_special_stars_sagittarius_a():
    """Verify Sagittarius A* and Source 2 are treated as distinct root stars A and B."""
    bodies = [
        {"body_id": 1, "body_name": "Sagittarius A*", "star_type": "SupermassiveBlackHole", "parents": '[{"Null": 0}]', "distance_from_arrival_ls": 0.0},
        {"body_id": 2, "body_name": "Source 2", "star_type": "B", "parents": '[{"Null": 0}]', "distance_from_arrival_ls": 74105.0}
    ]
    tree = build_system_map_tree(bodies, "Sagittarius A*")
    assert len(tree) == 2
    assert tree[0]["starKey"] == "A"
    assert tree[0]["rootStar"]["body_name"] == "Sagittarius A*"
    assert tree[1]["starKey"] == "B"
    assert tree[1]["rootStar"]["body_name"] == "Source 2"

    # Verify directly via system_map.js Node execution
    js_tree = run_js_build_system_map_tree(bodies, "Sagittarius A*")
    assert len(js_tree) == 2
    assert js_tree[0]["starKey"] == "A"
    assert js_tree[0]["rootStar"]["body_name"] == "Sagittarius A*"
    assert js_tree[1]["starKey"] == "B"
    assert js_tree[1]["rootStar"]["body_name"] == "Source 2"


def test_planet_orbital_distance_sorting_mixed_units():
    """Verify that planets with SemiMajorAxis (meters) and distance_from_arrival_ls (light seconds)
    are sorted strictly by actual orbital distance in light seconds from the host star."""
    # Body 1: Star A at 0 ls
    # Body 2: Planet 2 with semi_major_axis = 1.496e11 m (~499 Ls)
    # Body 3: Planet 1 with distance_from_arrival_ls = 100 Ls (no semi_major_axis, e.g. uncompleted scan)
    # Body 4: Planet 3 with semi_major_axis = 3.0e11 m (~1000 Ls)
    # Body 5: Planet 4 with distance_from_arrival_ls = 2000 Ls
    bodies = [
        {"body_id": 1, "body_name": "Proxima Centauri", "star_type": "M", "parents": '[{"Null": 0}]', "distance_from_arrival_ls": 0.0},
        {"body_id": 2, "body_name": "Proxima Centauri 2", "planet_class": "Earthlike body", "parents": '[{"Star": 1}]', "semi_major_axis": 149597870700.0, "distance_from_arrival_ls": 499.0},
        {"body_id": 3, "body_name": "Proxima Centauri 1", "planet_class": "Metal rich body", "parents": '[{"Star": 1}]', "distance_from_arrival_ls": 100.0},
        {"body_id": 4, "body_name": "Proxima Centauri 3", "planet_class": "Gas giant with water based life", "parents": '[{"Star": 1}]', "semi_major_axis": 299792458000.0, "distance_from_arrival_ls": 1000.0},
        {"body_id": 5, "body_name": "Proxima Centauri 4", "planet_class": "Icy body", "parents": '[{"Star": 1}]', "distance_from_arrival_ls": 2000.0},
    ]
    tree = build_system_map_tree(bodies, "Proxima Centauri")
    assert len(tree) == 1
    planets = tree[0]["planets"]
    assert [p["shortName"] for p in planets] == [
        "1",                    # 100 Ls
        "2",                    # ~499 Ls (1.496e11 m)
        "3",                    # 1000 Ls (3.0e11 m)
        "4"                     # 2000 Ls
    ]

    # Verify directly via system_map.js Node execution
    js_tree = run_js_build_system_map_tree(bodies, "Proxima Centauri")
    assert len(js_tree) == 1
    js_planets = js_tree[0]["planets"]
    assert [p["shortName"] for p in js_planets] == ["1", "2", "3", "4"]


def test_asteroid_belt_orbital_distance_sorting():
    """Verify that Asteroid Belts on the star are positioned accurately by orbital radius between planets."""
    # Star A at 0 Ls with an asteroid belt between 200 Ls and 300 Ls (avg 250 Ls = ~7.5e10 m)
    # Planet 1 at 100 Ls
    # Planet 2 at 500 Ls
    bodies = [
        {
            "body_id": 1,
            "body_name": "Alpha Test A",
            "star_type": "G",
            "parents": '[{"Null": 0}]',
            "distance_from_arrival_ls": 0.0,
            "rings_list": [
                {
                    "Name": "Alpha Test A Asteroid Belt",
                    "RingClass": "eRingClass_MetalRich",
                    "InnerRad": 60000000000.0,  # ~200 Ls
                    "OuterRad": 90000000000.0,  # ~300 Ls
                    "MassMT": 5000000.0
                }
            ]
        },
        {"body_id": 2, "body_name": "Alpha Test A 1", "planet_class": "Metal rich body", "parents": '[{"Star": 1}]', "distance_from_arrival_ls": 100.0},
        {"body_id": 3, "body_name": "Alpha Test A 2", "planet_class": "High metal content body", "parents": '[{"Star": 1}]', "distance_from_arrival_ls": 500.0},
    ]
    tree = build_system_map_tree(bodies, "Alpha Test")
    assert len(tree) == 1
    planets = tree[0]["planets"]
    # Order should strictly be: Planet 1 (100 Ls) -> Belt (250 Ls) -> Planet 2 (500 Ls)
    assert [p["shortName"] for p in planets] == ["A 1", "Belt", "A 2"]

    # Verify directly via system_map.js Node execution
    js_tree = run_js_build_system_map_tree(bodies, "Alpha Test")
    assert len(js_tree) == 1
    js_planets = js_tree[0]["planets"]
    assert [p["shortName"] for p in js_planets] == ["A 1", "Belt", "A 2"]


