"""
Landmark Service.
Loads static galactic landmarks dynamically from app/data/landmarks.json (SSOT).
Computes 3D Euclidean distances in light-years from given celestial coordinates.

All code, strings, and comments in this module are strictly English ASCII.
"""

import json
import math
import os
from typing import Dict, Any, Optional, List

LANDMARKS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "landmarks.json")

_landmarks_cache: Optional[Dict[str, Any]] = None


def load_landmarks(force_reload: bool = False) -> Dict[str, Any]:
    """Load galactic landmark definitions from JSON SSOT file."""
    global _landmarks_cache
    if _landmarks_cache is not None and not force_reload:
        return _landmarks_cache

    if not os.path.exists(LANDMARKS_FILE):
        raise FileNotFoundError(f"Landmarks SSOT file not found at: {LANDMARKS_FILE}")

    with open(LANDMARKS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Validate schema integrity
    validated: Dict[str, Any] = {}
    for key, val in data.items():
        coords = val.get("coords")
        if not isinstance(coords, list) or len(coords) != 3:
            continue
        if not all(isinstance(c, (int, float)) for c in coords):
            continue
        validated[key] = {
            "key": key,
            "name": str(val.get("name", key)),
            "system_name": str(val.get("system_name", "")),
            "coords": [float(coords[0]), float(coords[1]), float(coords[2])],
            "description": str(val.get("description", ""))
        }

    _landmarks_cache = validated
    return _landmarks_cache


def calculate_landmark_distances(
    star_pos_x: Optional[float],
    star_pos_y: Optional[float],
    star_pos_z: Optional[float]
) -> Dict[str, Optional[float]]:
    """
    Calculate distances in light-years from the given coordinates to all loaded landmarks.
    Returns a dict mapping '<key>_distance_ly' to rounded float distance, or None if coords missing.
    """
    landmarks = load_landmarks()
    results: Dict[str, Optional[float]] = {}

    if star_pos_x is None or star_pos_y is None or star_pos_z is None:
        for key in landmarks:
            results[f"{key}_distance_ly"] = None
        return results

    px, py, pz = float(star_pos_x), float(star_pos_y), float(star_pos_z)
    for key, lm in landmarks.items():
        lx, ly, lz = lm["coords"]
        dist = math.sqrt((px - lx) ** 2 + (py - ly) ** 2 + (pz - lz) ** 2)
        results[f"{key}_distance_ly"] = round(dist, 1)

    return results
