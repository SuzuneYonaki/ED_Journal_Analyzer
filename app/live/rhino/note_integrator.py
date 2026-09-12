"""
Rhino Mining Note Integrator.
Elegantly formats and updates celestial body markdown notes with mining coordinates
and mined materials, keeping the note compact, readable, and free of redundant clutter.
"""

import re
from datetime import datetime, timezone
from typing import Optional, List, Dict, Set, Any
import sqlite3

MINING_SECTION_HEADER = "### ⛏️ 採掘記録 (Rhino)"

def format_coord_key(lat: Optional[float], lon: Optional[float]) -> str:
    """Format coordinates into a clean canonical bracket string."""
    if lat is not None and lon is not None:
        lat_fmt = f"{lat:+.4f}"
        lon_fmt = f"{lon:+.4f}"
        return f"[Lat: {lat_fmt}°, Lon: {lon_fmt}°]"
    return "[座標未記録]"

def format_single_mining_line(coord_str: str, minerals: List[str]) -> str:
    """Formats a single clean line: '- [Lat: +XX.XXXX°, Lon: +YY.YYYY°]: Mineral1, Mineral2'"""
    sorted_minerals = sorted(list(dict.fromkeys(minerals)))
    minerals_str = ", ".join(sorted_minerals) if sorted_minerals else "採掘物なし"
    return f"- {coord_str}: {minerals_str}"

def parse_existing_mining_section(note_text: str) -> tuple[str, Dict[str, Set[str]], bool]:
    """
    Parses an existing note text.
    Returns:
        (base_text_without_mining, dict_of_coord_to_minerals, has_mining_section)
    """
    if not note_text:
        return "", {}, False

    lines = note_text.splitlines()
    header_idx = -1
    for i, line in enumerate(lines):
        if MINING_SECTION_HEADER in line:
            header_idx = i
            break

    if header_idx == -1:
        return note_text.strip(), {}, False

    base_text = "\n".join(lines[:header_idx]).rstrip()
    mining_lines = lines[header_idx + 1:]

    coord_minerals_map: Dict[str, Set[str]] = {}
    
    # Regex to match: - [Lat: +12.3456°, Lon: -45.6789°]: A, B, C or - [座標未記録]: A, B
    line_pattern = re.compile(r"^-\s*(\[[^\]]+\])\s*:\s*(.*)$")

    for m_line in mining_lines:
        stripped = m_line.strip()
        if not stripped:
            continue
        # If another markdown heading starts, stop mining section
        if stripped.startswith("#") and not stripped.startswith(MINING_SECTION_HEADER):
            # Preserve trailing sections if any
            break
        match = line_pattern.match(stripped)
        if match:
            coord_bracket = match.group(1).strip()
            items_str = match.group(2).strip()
            items = [item.strip() for item in items_str.split(",") if item.strip() and item.strip() != "採掘物なし"]
            if coord_bracket not in coord_minerals_map:
                coord_minerals_map[coord_bracket] = set()
            coord_minerals_map[coord_bracket].update(items)

    return base_text, coord_minerals_map, True

def build_merged_note(base_text: str, coord_minerals_map: Dict[str, Set[str]]) -> str:
    """Builds the complete note by combining user base text and the compact mining section."""
    mining_lines = []
    for coord_str in sorted(coord_minerals_map.keys()):
        minerals = sorted(list(coord_minerals_map[coord_str]))
        mining_lines.append(format_single_mining_line(coord_str, minerals))

    if not mining_lines:
        return base_text

    section_block = f"{MINING_SECTION_HEADER}\n" + "\n".join(mining_lines)
    if base_text:
        return f"{base_text}\n\n{section_block}".strip()
    return section_block.strip()

def append_or_merge_mining_site_to_note(
    existing_note: str,
    lat: Optional[float],
    lon: Optional[float],
    new_minerals: List[str]
) -> str:
    """
    Takes an existing note, and merges new minerals for the given coordinates.
    Keeps note compact and clean, updating in-place if coordinate already exists.
    """
    base_text, coord_map, _ = parse_existing_mining_section(existing_note or "")
    coord_key = format_coord_key(lat, lon)

    if coord_key not in coord_map:
        coord_map[coord_key] = set()

    for m in new_minerals:
        clean_m = (m or "").strip()
        if clean_m:
            coord_map[coord_key].add(clean_m)

    return build_merged_note(base_text, coord_map)

def update_body_note_in_db(
    conn: sqlite3.Connection,
    system_address: int,
    body_id: int,
    body_name: str,
    star_system: str,
    lat: Optional[float],
    lon: Optional[float],
    minerals: List[str]
) -> str:
    """
    Updates the body_bookmarks table for a celestial body, merging the mining entry.
    Creates a new body_bookmark record if none exists yet.
    Returns the updated note_markdown.
    """
    c = conn.cursor()
    c.execute("SELECT alias_name, note_markdown FROM body_bookmarks WHERE system_address = ? AND body_id = ?", (system_address, body_id))
    row = c.fetchone()

    now = datetime.now(timezone.utc).isoformat()
    if row:
        alias_name = row["alias_name"] if isinstance(row, sqlite3.Row) else row[0]
        curr_note = row["note_markdown"] if isinstance(row, sqlite3.Row) else row[1]
        updated_note = append_or_merge_mining_site_to_note(curr_note or "", lat, lon, minerals)
        c.execute("""
            UPDATE body_bookmarks
            SET note_markdown = ?, updated_at = ?
            WHERE system_address = ? AND body_id = ?
        """, (updated_note, now, system_address, body_id))
    else:
        alias_name = ""
        updated_note = append_or_merge_mining_site_to_note("", lat, lon, minerals)
        c.execute("""
            INSERT INTO body_bookmarks (system_address, body_id, body_name, star_system, alias_name, note_markdown, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (system_address, body_id, body_name, star_system, alias_name, updated_note, now, now))

    conn.commit()
    return updated_note
