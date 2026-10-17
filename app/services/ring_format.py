from typing import Any, Dict, List, Optional


def to_journal_ring(ring: Dict[str, Any]) -> Dict[str, Any]:
    """Converts an EDSM ring/belt dict to the journal-style shape the app stores and renders.

    EDSM: {"name", "type", "mass" (MT), "innerRadius" (km), "outerRadius" (km)}
    Journal: {"Name", "RingClass", "MassMT", "InnerRad" (m), "OuterRad" (m)}
    Journal-style dicts are returned unchanged.
    """
    if "Name" in ring or "name" not in ring:
        return ring
    converted: Dict[str, Any] = {
        "Name": ring.get("name"),
        "RingClass": f"eRingClass_{(ring.get('type') or 'Unknown').replace(' ', '')}",
        "MassMT": ring.get("mass") or 0,
    }
    if ring.get("innerRadius") is not None:
        converted["InnerRad"] = ring["innerRadius"] * 1000.0
    if ring.get("outerRadius") is not None:
        converted["OuterRad"] = ring["outerRadius"] * 1000.0
    for extra in ("signals", "Hotspots", "signals_updated_at"):
        if extra in ring:
            converted[extra] = ring[extra]
    return converted


def normalize_rings(rings: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
    if not rings:
        return rings
    return [to_journal_ring(r) if isinstance(r, dict) else r for r in rings]
