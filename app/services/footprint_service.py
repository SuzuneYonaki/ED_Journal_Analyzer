"""
External Footprint Check Service (Inara, Spansh, EDSM).
Verifies whether a star system has been previously visited/recorded in the galaxy.
If the star system exists in the local database (systems table), external queries are skipped.
Results are cached in memory for 15 minutes to respect external community API rate limits.
"""

import time
import json
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional

from app.db.database import get_db_connection

CACHE_TTL_SEC = 900.0  # 15 minutes cache
EXTERNAL_TIMEOUT_SEC = 4.5  # Fast response timeout


class FootprintService:
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_times: Dict[str, float] = {}

    def check_system_footprint(self, system_name: str) -> Dict[str, Any]:
        clean_name = (system_name or "").strip()
        if not clean_name:
            return {
                "system_name": "",
                "in_local_db": False,
                "has_footprint": False,
                "services": {},
                "summary": "not_found"
            }

        cache_key = clean_name.lower()
        now = time.time()

        if cache_key in self._cache:
            cached_at = self._cache_times.get(cache_key, 0)
            if (now - cached_at) < CACHE_TTL_SEC:
                return self._cache[cache_key]

        # 1. First, check if the system exists in our local DB
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT system_address, star_system, visit_count, total_potential_value FROM systems WHERE LOWER(star_system) = LOWER(?) LIMIT 1", (clean_name,))
        row = c.fetchone()
        conn.close()

        if row:
            result = {
                "system_name": row["star_system"] or clean_name,
                "in_local_db": True,
                "has_footprint": True,
                "services": {
                    "local_db": {
                        "found": True,
                        "url": "",
                        "details": f"Visits: {row['visit_count']}"
                    },
                    "edsm": {
                        "found": True,
                        "url": f"https://www.edsm.net/show-system?systemName={urllib.parse.quote(clean_name)}",
                        "details": "Local DB recorded"
                    },
                    "spansh": {
                        "found": True,
                        "url": "https://spansh.co.uk/systems/search",
                        "details": "Local DB recorded"
                    },
                    "inara": {
                        "found": True,
                        "url": f"https://inara.cz/elite/starsystem/?search={urllib.parse.quote(clean_name)}",
                        "details": "Local DB recorded"
                    }
                },
                "summary": "local_db"
            }
            self._cache[cache_key] = result
            self._cache_times[cache_key] = now
            return result

        # 2. Not in local DB -> query external services concurrently
        services_result = {
            "edsm": {"found": False, "url": f"https://www.edsm.net/show-system?systemName={urllib.parse.quote(clean_name)}", "details": None},
            "spansh": {"found": False, "url": "https://spansh.co.uk/systems/search", "details": None},
            "inara": {"found": False, "url": f"https://inara.cz/elite/starsystem/?search={urllib.parse.quote(clean_name)}", "details": None}
        }

        with ThreadPoolExecutor(max_workers=3) as executor:
            future_edsm = executor.submit(self._check_edsm, clean_name)
            future_spansh = executor.submit(self._check_spansh, clean_name)
            future_inara = executor.submit(self._check_inara, clean_name)

            try:
                services_result["edsm"] = future_edsm.result(timeout=EXTERNAL_TIMEOUT_SEC)
            except Exception as e:
                services_result["edsm"]["details"] = str(e)

            try:
                services_result["spansh"] = future_spansh.result(timeout=EXTERNAL_TIMEOUT_SEC)
            except Exception as e:
                services_result["spansh"]["details"] = str(e)

            try:
                services_result["inara"] = future_inara.result(timeout=EXTERNAL_TIMEOUT_SEC)
            except Exception as e:
                services_result["inara"]["details"] = str(e)

        has_footprint = any(s["found"] for s in services_result.values())
        summary = "found" if has_footprint else "not_found"

        result = {
            "system_name": clean_name,
            "in_local_db": False,
            "has_footprint": has_footprint,
            "services": services_result,
            "summary": summary
        }

        self._cache[cache_key] = result
        self._cache_times[cache_key] = now
        return result

    def _check_edsm(self, system_name: str) -> Dict[str, Any]:
        encoded = urllib.parse.quote(system_name)
        url = f"https://www.edsm.net/api-v1/system?systemName={encoded}&showInformation=1&showCoordinates=1"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "EDJournalAnalyzer/v0.1.0 (Footprint Check)"}
        )
        try:
            with urllib.request.urlopen(req, timeout=EXTERNAL_TIMEOUT_SEC) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    if isinstance(data, dict) and data.get("name"):
                        info = data.get("information", {})
                        details = f"Gov: {info.get('government', 'None')}" if info else "Recorded in EDSM"
                        return {
                            "found": True,
                            "url": f"https://www.edsm.net/show-system?systemName={encoded}",
                            "details": details
                        }
        except Exception:
            pass

        return {
            "found": False,
            "url": f"https://www.edsm.net/show-system?systemName={encoded}",
            "details": None
        }

    def _check_spansh(self, system_name: str) -> Dict[str, Any]:
        url = "https://spansh.co.uk/api/systems/search"
        payload = {
            "filters": {
                "name": {"value": system_name}
            },
            "sort": [{"name": {"direction": "asc"}}],
            "size": 1,
            "page": 0
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "User-Agent": "EDJournalAnalyzer/v0.1.0 (Footprint Check)",
                "Content-Type": "application/json"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=EXTERNAL_TIMEOUT_SEC) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    results = data.get("results", [])
                    for r in results:
                        r_name = r.get("name", "").strip()
                        if r_name.lower() == system_name.lower():
                            id64 = r.get("id64")
                            sys_url = f"https://spansh.co.uk/system/{id64}" if id64 else "https://spansh.co.uk/systems"
                            return {
                                "found": True,
                                "url": sys_url,
                                "details": f"Bodies: {len(r.get('bodies', []))}"
                            }
        except Exception:
            pass

        return {
            "found": False,
            "url": "https://spansh.co.uk/systems/search",
            "details": None
        }

    def _check_inara(self, system_name: str) -> Dict[str, Any]:
        encoded = urllib.parse.quote(system_name)
        url = f"https://inara.cz/elite/starsystem/?search={encoded}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=EXTERNAL_TIMEOUT_SEC) as resp:
                if resp.status == 200:
                    html = resp.read().decode("utf-8", errors="ignore")
                    has_id_link = "/elite/starsystem/" in html and any(f"/elite/starsystem/{i}" in html for i in range(10))
                    if has_id_link:
                        return {
                            "found": True,
                            "url": url,
                            "details": "Recorded in Inara"
                        }
        except Exception:
            pass

        return {
            "found": False,
            "url": url,
            "details": None
        }


footprint_service = FootprintService()
