from collections import Counter
from typing import Any, Dict, List, Optional, Sequence

_STAGES = {"log": 1, "sample": 2, "analyse": 3, "analyze": 3}
_STAGE_NAMES = {1: "Log", 2: "Sample", 3: "Analyse"}

GEOLOGY_GENUS = "Geology & Anomalies"

SORTS = {
    "found_desc": lambda e: e["first_found_at"] or "",
    "found_asc": lambda e: e["first_found_at"] or "",
    "value_desc": lambda e: e["base_value"],
    "species": lambda e: (e["species"].lower(), e["star_system"].lower()),
    "system": lambda e: (e["star_system"].lower(), e["body_name"].lower()),
}


def _split_variant(text: str):
    base, sep, variant = (text or "").strip().partition(" - ")
    return base.strip(), variant.strip() if sep else ""


def _fallback_genus(species: str, is_geology: bool) -> str:
    # Rows logged from Codex entries have no genus. Geological sites share one group; for the rest,
    # "<Colour> <Genus words>" names (e.g. "Roseum Bioluminescent Anemone") drop the leading colour word.
    if is_geology:
        return GEOLOGY_GENUS
    words = species.split(" ")
    return " ".join(words[1:]) if len(words) >= 3 else words[0]


def collect_bio_entries(conn) -> List[Dict[str, Any]]:
    """One entry per (system, body, species): where it was found, how far sampling got, and the value."""
    geology_names = {
        r[0] for r in conn.execute(
            "SELECT DISTINCT name_localised FROM codex_entries WHERE sub_category LIKE '%Geology%'"
        ).fetchall() if r[0]
    }
    rows = conn.execute("""
        SELECT o.system_address, o.body_id, o.body_name, o.timestamp, o.scan_type,
               o.genus_localised, o.genus, o.species_localised, o.species,
               o.variant_localised, o.base_value, o.first_discovery_value,
               s.star_system
        FROM scanned_organics o
        LEFT JOIN systems s ON s.system_address = o.system_address
        ORDER BY o.timestamp ASC
    """).fetchall()

    entries: Dict[Any, Dict[str, Any]] = {}
    for r in rows:
        raw_species = r["species_localised"] or r["species"] or r["genus_localised"] or r["genus"] or ""
        species, variant_from_species = _split_variant(raw_species)
        species = species or "Unknown"
        _, variant_from_variant = _split_variant(r["variant_localised"] or "")
        row_genus = (r["genus_localised"] or "").strip()
        if row_genus.lower() == "unknown":
            row_genus = ""
        stage = _STAGES.get((r["scan_type"] or "").lower(), 1)
        body_key = r["body_id"] if r["body_id"] is not None else r["body_name"]
        key = (r["system_address"], body_key, species)

        e = entries.get(key)
        if e is None:
            e = entries[key] = {
                "system_address": r["system_address"],
                "star_system": r["star_system"] or f"System {r['system_address']}",
                "body_id": r["body_id"],
                "body_name": r["body_name"] or "",
                "genus": row_genus or _fallback_genus(species, species in geology_names),
                "_genus_known": bool(row_genus),
                "species": species,
                "variant": "",
                "stage": stage,
                "first_found_at": r["timestamp"],
                "last_at": r["timestamp"],
                "base_value": 0,
                "first_discovery_value": 0,
            }
        if row_genus and not e["_genus_known"]:
            e["genus"], e["_genus_known"] = row_genus, True
        e["stage"] = max(e["stage"], stage)
        e["first_found_at"] = min(e["first_found_at"], r["timestamp"])
        e["last_at"] = max(e["last_at"], r["timestamp"])
        e["variant"] = e["variant"] or variant_from_species or variant_from_variant
        e["base_value"] = max(e["base_value"], r["base_value"] or 0)
        e["first_discovery_value"] = max(e["first_discovery_value"], r["first_discovery_value"] or 0)

    out = list(entries.values())
    for e in out:
        del e["_genus_known"]
        e["stage_name"] = _STAGE_NAMES[e["stage"]]
        e["is_completed"] = e["stage"] == 3
    return out


def query_bio_log(
    entries: Sequence[Dict[str, Any]],
    q: str = "",
    genus: Optional[Sequence[str]] = None,
    status: str = "",
    sort: str = "found_desc",
    page: int = 1,
    limit: int = 100,
) -> Dict[str, Any]:
    needle = (q or "").strip().lower()
    wanted_genus = {g.strip().lower() for g in (genus or []) if g.strip()}

    def text_match(e):
        if not needle:
            return True
        hay = " ".join((e["star_system"], e["body_name"], e["species"], e["genus"], e["variant"])).lower()
        return needle in hay

    def status_match(e):
        if status == "completed":
            return e["is_completed"]
        if status == "in_progress":
            return not e["is_completed"]
        return True

    base = [e for e in entries if text_match(e) and status_match(e)]
    genus_counts = Counter(e["genus"] for e in base)
    items = [e for e in base if not wanted_genus or e["genus"].lower() in wanted_genus]

    sort_key = SORTS.get(sort, SORTS["found_desc"])
    items.sort(key=sort_key, reverse=sort in ("found_desc", "value_desc"))

    limit = max(1, min(limit, 500))
    page = max(1, page)
    start = (page - 1) * limit
    return {
        "total": len(items),
        "page": page,
        "limit": limit,
        "summary": {
            "entries": len(items),
            "species": len({e["species"] for e in items}),
            "systems": len({e["system_address"] for e in items}),
        },
        "genus_counts": sorted(({"genus": g, "count": n} for g, n in genus_counts.items()), key=lambda x: (-x["count"], x["genus"])),
        "items": items[start:start + limit],
    }
