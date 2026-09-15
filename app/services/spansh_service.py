"""
Spansh API Integration Service.
Queries the Spansh Bodies search API (https://spansh.co.uk/api/bodies/search) to retrieve
ring DSS hotspots (e.g. Platinum, Painite, Tritium, Core minerals) and Planetary Mining Locations (PML).
Merges hotspot data into bodies.rings and records ring DSS hotspots in body_bookmarks notes.
All code, strings, and comments in this module are strictly English ASCII.
"""

import json
import logging
import sqlite3
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

SPANSH_BODIES_SEARCH_URL = "https://spansh.co.uk/api/bodies/search"
DEFAULT_USER_AGENT = "EDJournalAnalyzer/0.1.7"
SPANSH_TIMEOUT_SEC = 12


class SpanshService:
    def __init__(self, timeout: int = SPANSH_TIMEOUT_SEC, user_agent: str = DEFAULT_USER_AGENT):
        self.timeout = timeout
        self.user_agent = user_agent

    def fetch_system_bodies(self, system_name: str) -> List[Dict[str, Any]]:
        """
        Queries Spansh Bodies Search API for the given system name.
        Returns a list of body dictionaries matching the system name.
        """
        if not system_name or not system_name.strip():
            return []

        clean_sys_name = system_name.strip()
        payload = {
            "filters": {
                "system_name": {
                    "value": clean_sys_name
                }
            },
            "size": 100
        }

        req = urllib.request.Request(
            SPANSH_BODIES_SEARCH_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "User-Agent": self.user_agent
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if resp.status != 200:
                    logger.warning("Spansh bodies search returned HTTP %s for %s", resp.status, clean_sys_name)
                    return []
                raw_data = resp.read()
                data = json.loads(raw_data.decode("utf-8"))
                results = data.get("results", [])
                
                # Filter exact system name matches (case-insensitive)
                exact_results = [
                    r for r in results
                    if r.get("system_name", "").strip().lower() == clean_sys_name.lower()
                ]
                return exact_results if exact_results else results
        except urllib.error.URLError as e:
            logger.warning("Network error querying Spansh for %s: %s", clean_sys_name, e)
            return []
        except Exception as e:
            logger.error("Unexpected error querying Spansh for %s: %s", clean_sys_name, e)
            return []

    def sync_system_spansh(
        self,
        conn: sqlite3.Connection,
        system_address: int,
        system_name: str
    ) -> Dict[str, Any]:
        """
        Fetches Spansh data for the system and merges:
        1. Ring DSS hotspots into bodies.rings JSON
        2. Planetary Mining Locations into bodies.mining_signals
        3. Reserve level into bodies.reserve_level & systems.system_reserve
        4. Auto-generates ring DSS hotspot notes in body_bookmarks
        Returns a summary dict.
        """
        summary: Dict[str, Any] = {
            "success": True,
            "system_name": system_name,
            "system_address": system_address,
            "bodies_updated": 0,
            "hotspots_found": 0,
            "pml_found": 0,
            "rings_with_hotspots": []
        }

        spansh_bodies = self.fetch_system_bodies(system_name)
        if not spansh_bodies:
            summary["message"] = "No bodies found on Spansh for this system."
            return summary

        cursor = conn.cursor()

        # Load existing bodies for this system
        cursor.execute(
            "SELECT id, body_id, body_name, rings, mining_signals, reserve_level, landable "
            "FROM bodies WHERE system_address = ?",
            (system_address,)
        )
        db_bodies = cursor.fetchall()
        
        # Index DB bodies by body_id and lowercase body_name
        body_by_id: Dict[int, Dict[str, Any]] = {}
        body_by_name: Dict[str, Dict[str, Any]] = {}

        for row in db_bodies:
            b_info = {
                "id": row[0],
                "body_id": row[1],
                "body_name": row[2],
                "rings": row[3],
                "mining_signals": row[4] or 0,
                "reserve_level": row[5] or "",
                "landable": row[6] or 0,
            }
            if row[1] is not None:
                body_by_id[row[1]] = b_info
            if row[2]:
                body_by_name[row[2].strip().lower()] = b_info

        from app.live.rhino.note_integrator import update_ring_hotspots_in_db

        overall_reserve = ""

        for sb in spansh_bodies:
            sb_name = (sb.get("name") or "").strip()
            sb_id = sb.get("body_id")
            sb_reserve = (sb.get("reserve_level") or "").strip()
            if sb_reserve and not overall_reserve:
                overall_reserve = sb_reserve

            # Find matching DB body
            target_b = None
            if sb_id is not None and sb_id in body_by_id:
                target_b = body_by_id[sb_id]
            elif sb_name.lower() in body_by_name:
                target_b = body_by_name[sb_name.lower()]

            if not target_b:
                continue

            updated_fields = False
            b_db_id = target_b["id"]
            actual_body_id = target_b["body_id"] if target_b["body_id"] is not None else (sb_id or 0)
            actual_body_name = target_b["body_name"] or sb_name

            # 1. Check Planetary Mining Locations in sb["signals"]
            pml_count = 0
            for sig in sb.get("signals", []) or []:
                s_name = (sig.get("name") or "").strip()
                if s_name.lower() == "planetary mining location" or "planetary mining" in s_name.lower():
                    pml_count += int(sig.get("count", 1))

            if pml_count > target_b["mining_signals"]:
                cursor.execute(
                    "UPDATE bodies SET mining_signals = ? WHERE id = ?",
                    (pml_count, b_db_id)
                )
                target_b["mining_signals"] = pml_count
                summary["pml_found"] += pml_count
                updated_fields = True

            # 2. Check reserve level
            if sb_reserve and not target_b["reserve_level"]:
                cursor.execute(
                    "UPDATE bodies SET reserve_level = ? WHERE id = ?",
                    (sb_reserve, b_db_id)
                )
                target_b["reserve_level"] = sb_reserve
                updated_fields = True

            # 3. Check rings and ring hotspots
            sb_rings = sb.get("rings") or []
            if sb_rings:
                existing_rings_raw = target_b["rings"]
                existing_rings = []
                if existing_rings_raw and existing_rings_raw not in ("[]", '""'):
                    try:
                        existing_rings = json.loads(existing_rings_raw) if isinstance(existing_rings_raw, str) else existing_rings_raw
                    except Exception:
                        existing_rings = []

                rings_modified = False

                if existing_rings:
                    for er in existing_rings:
                        er_name = (er.get("Name") or "").strip().lower()
                        for sr in sb_rings:
                            sr_name = (sr.get("name") or "").strip().lower()
                            if sr_name == er_name:
                                sr_signals = sr.get("signals") or []
                                if sr_signals:
                                    er["signals"] = sr_signals
                                    hotspot_map = {
                                        s.get("name"): int(s.get("count", 1))
                                        for s in sr_signals if s.get("name")
                                    }
                                    er["Hotspots"] = hotspot_map
                                    if sr.get("signals_updated_at"):
                                        er["signals_updated_at"] = sr.get("signals_updated_at")
                                    rings_modified = True

                                    # Update note in DB
                                    update_ring_hotspots_in_db(
                                        conn=conn,
                                        system_address=system_address,
                                        body_id=actual_body_id,
                                        body_name=actual_body_name,
                                        star_system=system_name,
                                        ring_name=er.get("Name") or sr.get("name"),
                                        hotspot_counts=hotspot_map
                                    )
                                    summary["hotspots_found"] += sum(hotspot_map.values())
                                    summary["rings_with_hotspots"].append({
                                        "body_name": actual_body_name,
                                        "ring_name": er.get("Name") or sr.get("name"),
                                        "hotspots": hotspot_map
                                    })
                else:
                    # Construct rings list from Spansh
                    converted_rings = []
                    for sr in sb_rings:
                        sr_signals = sr.get("signals") or []
                        hotspot_map = {
                            s.get("name"): int(s.get("count", 1))
                            for s in sr_signals if s.get("name")
                        } if sr_signals else {}

                        r_dict: Dict[str, Any] = {
                            "Name": sr.get("name"),
                            "RingClass": f"eRingClass_{sr.get('type', '').replace(' ', '')}",
                            "InnerRad": sr.get("inner_radius"),
                            "OuterRad": sr.get("outer_radius"),
                            "MassMT": sr.get("mass", 0) / 1e9 if sr.get("mass") else 0,
                        }
                        if sr_signals:
                            r_dict["signals"] = sr_signals
                            r_dict["Hotspots"] = hotspot_map
                            if sr.get("signals_updated_at"):
                                r_dict["signals_updated_at"] = sr.get("signals_updated_at")

                            update_ring_hotspots_in_db(
                                conn=conn,
                                system_address=system_address,
                                body_id=actual_body_id,
                                body_name=actual_body_name,
                                star_system=system_name,
                                ring_name=sr.get("name") or "Ring",
                                hotspot_counts=hotspot_map
                            )
                            summary["hotspots_found"] += sum(hotspot_map.values())
                            summary["rings_with_hotspots"].append({
                                "body_name": actual_body_name,
                                "ring_name": sr.get("name"),
                                "hotspots": hotspot_map
                            })

                        converted_rings.append(r_dict)

                    existing_rings = converted_rings
                    rings_modified = True

                if rings_modified:
                    new_rings_json = json.dumps(existing_rings)
                    cursor.execute(
                        "UPDATE bodies SET rings = ? WHERE id = ?",
                        (new_rings_json, b_db_id)
                    )
                    target_b["rings"] = new_rings_json
                    updated_fields = True

            if updated_fields:
                summary["bodies_updated"] += 1

        # Update systems.system_reserve if present
        if overall_reserve:
            cursor.execute(
                "UPDATE systems SET system_reserve = ? WHERE system_address = ? AND (system_reserve IS NULL OR system_reserve = '')",
                (overall_reserve, system_address)
            )

        conn.commit()
        return summary


spansh_service = SpanshService()
