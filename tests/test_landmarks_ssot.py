"""
Unit tests for Galactic Landmarks SSOT and Distance Calculation Engine.
Verifies dynamic parsing integrity of app/data/landmarks.json and precision of 3D Euclidean distances.

All code, strings, and comments in this module are strictly English ASCII.
"""

import math
import pytest
from app.services.landmark_service import load_landmarks, calculate_landmark_distances, LANDMARKS_FILE


def test_landmarks_json_structure_and_integrity():
    """Verify that landmarks.json exists, contains all required keys and valid 3D coordinates."""
    landmarks = load_landmarks(force_reload=True)
    required_keys = ["sol", "colonia", "rainbows_end", "explorers_anchorage"]

    for k in required_keys:
        assert k in landmarks, f"Missing required landmark key '{k}' in landmarks.json"
        lm = landmarks[k]
        assert "name" in lm and isinstance(lm["name"], str) and len(lm["name"]) > 0
        assert "system_name" in lm and isinstance(lm["system_name"], str) and len(lm["system_name"]) > 0
        assert "description" in lm and isinstance(lm["description"], str)
        assert "coords" in lm
        coords = lm["coords"]
        assert isinstance(coords, list) and len(coords) == 3
        assert all(isinstance(c, (int, float)) for c in coords)


def test_distance_from_sol_to_landmarks():
    """Verify distance calculations from Sol [0, 0, 0] match community known distances."""
    dists = calculate_landmark_distances(0.0, 0.0, 0.0)

    # Sol to Sol must be 0
    assert dists.get("sol_distance_ly") == 0.0

    # Sol to Colonia is approx 22,000 Ly
    col_dist = dists.get("colonia_distance_ly")
    assert col_dist is not None
    assert 21900.0 < col_dist < 22100.0, f"Unexpected Colonia distance from Sol: {col_dist}"

    # Sol to Rainbow's End (DW3 furthest outpost) is approx 48,408 Ly
    rb_dist = dists.get("rainbows_end_distance_ly")
    assert rb_dist is not None
    assert 48300.0 < rb_dist < 48500.0, f"Unexpected Rainbow's End distance from Sol: {rb_dist}"

    # Sol to Explorer's Anchorage (DW2 near Sgr A*) is approx 25,900 Ly
    ea_dist = dists.get("explorers_anchorage_distance_ly")
    assert ea_dist is not None
    assert 25800.0 < ea_dist < 26000.0, f"Unexpected Explorer's Anchorage distance from Sol: {ea_dist}"


def test_distance_from_landmark_to_itself():
    """Verify distance from a landmark to its own coordinate is 0.0 Ly."""
    landmarks = load_landmarks()
    rb_coords = landmarks["rainbows_end"]["coords"]
    dists = calculate_landmark_distances(rb_coords[0], rb_coords[1], rb_coords[2])
    assert dists.get("rainbows_end_distance_ly") == 0.0

    ea_coords = landmarks["explorers_anchorage"]["coords"]
    dists_ea = calculate_landmark_distances(ea_coords[0], ea_coords[1], ea_coords[2])
    assert dists_ea.get("explorers_anchorage_distance_ly") == 0.0


def test_distance_none_handling():
    """Verify missing coordinates return None without throwing exceptions."""
    dists = calculate_landmark_distances(None, None, None)
    assert dists.get("sol_distance_ly") is None
    assert dists.get("colonia_distance_ly") is None
    assert dists.get("rainbows_end_distance_ly") is None
    assert dists.get("explorers_anchorage_distance_ly") is None
