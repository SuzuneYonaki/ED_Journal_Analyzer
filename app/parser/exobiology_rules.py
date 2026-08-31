"""
Exobiology Condition Rule Dataset Module for Elite Dangerous.
Loads environmental parameter requirements, physical thresholds, base exploration payouts,
minimum colony distances, and star color variants directly from app/data/canonn_rules.json (SSOT).

All code, strings, and comments in this module are strictly English ASCII.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional

CANONN_RULES_FILE = Path(__file__).resolve().parents[1] / "data" / "canonn_rules.json"

def load_rules_from_json() -> Dict[str, Dict[str, Any]]:
    """Loads all Exobiology species rules directly from the SSOT canonn_rules.json file."""
    if CANONN_RULES_FILE.is_file():
        try:
            with CANONN_RULES_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception as e:
            print(f"[exobiology_rules] Error loading {CANONN_RULES_FILE}: {e}")
    return {}

# Build primary EXOBIOLOGY_RULES dictionary from SSOT json
EXOBIOLOGY_RULES: Dict[str, Dict[str, Any]] = load_rules_from_json()

def build_genus_defaults(rules: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Builds genus fallback averages directly from available species rules."""
    genus_map: Dict[str, Dict[str, Any]] = {
        "Aleoida": {"base_value": 6000000, "colony_distance_m": 150},
        "Bacterium": {"base_value": 1000000, "colony_distance_m": 500},
        "Cactoida": {"base_value": 3667600, "colony_distance_m": 300},
        "Clypeus": {"base_value": 8418600, "colony_distance_m": 150},
        "Concha": {"base_value": 4571100, "colony_distance_m": 150},
        "Electricae": {"base_value": 6284600, "colony_distance_m": 1000},
        "Fonticulua": {"base_value": 3110600, "colony_distance_m": 500},
        "Frutexa": {"base_value": 7794300, "colony_distance_m": 150},
        "Fumerola": {"base_value": 6692200, "colony_distance_m": 100},
        "Osseus": {"base_value": 3280300, "colony_distance_m": 800},
        "Radicoida": {"base_value": 7200000, "colony_distance_m": 1000},
        "Recepta": {"base_value": 14805700, "colony_distance_m": 600},
        "Stratum": {"base_value": 19010800, "colony_distance_m": 500},
        "Tubus": {"base_value": 2904800, "colony_distance_m": 800},
        "Tussock": {"base_value": 3724800, "colony_distance_m": 200},
    }
    for rule in rules.values():
        g = rule.get("genus")
        if g and g not in genus_map:
            genus_map[g] = {
                "base_value": rule.get("base_value", 1000000),
                "colony_distance_m": rule.get("colony_distance_m", 500)
            }
    return genus_map

GENUS_DEFAULTS: Dict[str, Dict[str, Any]] = build_genus_defaults(EXOBIOLOGY_RULES)
