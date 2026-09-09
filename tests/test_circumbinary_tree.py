import pytest
import re

def analyze_body_designation(body_name: str, system_name: str, is_star: bool):
    short = body_name
    if system_name and short.startswith(system_name):
        short = short[len(system_name):].strip()
    
    tokens = short.split()
    if not tokens:
        return {
            "shortName": short or "Star",
            "starGroup": "A",
            "isStar": True,
            "planetNum": None,
            "moonLetter": None,
            "submoonLetter": None,
            "level": 0
        }
    
    star_group = "A"
    planet_num = None
    moon_letter = None
    submoon_letter = None
    level = 1
    
    idx = 0
    if re.match(r'^[A-Z]{1,6}$', tokens[0]):
        star_group = tokens[0]
        idx = 1
        
    if idx < len(tokens):
        tok = tokens[idx]
        if tok.isdigit():
            planet_num = int(tok)
            idx += 1
            level = 1
            if idx < len(tokens) and re.match(r'^[a-z]$', tokens[idx], re.I):
                moon_letter = tokens[idx].lower()
                idx += 1
                level = 2
                if idx < len(tokens) and re.match(r'^[a-z]$', tokens[idx], re.I):
                    submoon_letter = tokens[idx].lower()
                    level = 3
        elif re.match(r'^[a-z]$', tok, re.I):
            moon_letter = tok.lower()
            level = 2
            
    is_actual_star = bool(is_star and planet_num is None)
    if is_actual_star:
        level = 0
        
    return {
        "shortName": short,
        "starGroup": star_group,
        "isStar": is_actual_star,
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
