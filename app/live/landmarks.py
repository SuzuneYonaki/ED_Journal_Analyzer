"""
Live landmark distance calculation module.
Calculates distances from current CMDR coordinates to major galactic POIs.
"""

from typing import Dict, Any, Optional
from app.services.landmark_service import load_landmarks, calculate_landmark_distances

def get_landmark_distances_from_coords(x: Optional[float], y: Optional[float], z: Optional[float]) -> Dict[str, Optional[float]]:
    """Calculate distances from given 3D coordinates to all galactic landmarks."""
    return calculate_landmark_distances(x, y, z)

def get_landmark_info(key: str) -> Optional[Dict[str, Any]]:
    """Retrieve details for a specific landmark key (e.g. sol, colonia)."""
    landmarks = load_landmarks()
    return landmarks.get(key)
