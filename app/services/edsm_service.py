"""
EDSM (Elite Dangerous Star Map) API Integration Service.
Provides asynchronous rate-limited queries (minimum 1.0s delay per request)
to query system registration, discovery status, and celestial body discoveries.
Results are persisted into the local SQLite database as a permanent cache.

All code, strings, and comments in this module are strictly English ASCII.
"""

import json
import time
import urllib.parse
import urllib.request
import threading
import queue
from typing import Dict, Any, Optional

from app.db.database import get_db_connection

EDSM_SYSTEM_API = "https://www.edsm.net/api-v1/system"
EDSM_BODIES_API = "https://www.edsm.net/api-system-v1/bodies"
REQUEST_DELAY_SEC = 1.0  # Respectful community delay between external API calls
UNREGISTERED_RECHECK_COOLDOWN_SEC = 1800.0  # 30-minute in-memory cooldown before re-querying unregistered system


class EDSMService:
    def __init__(self):
        self.request_queue: queue.Queue = queue.Queue()
        self.queued_systems = set()
        self.recent_unregistered_cache: Dict[int, float] = {}
        self.last_request_time = 0.0
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

    def queue_system_check(self, system_address: int, system_name: str, force_recheck: bool = False):
        """Queue a system for EDSM registration and discovery verification."""
        if not system_address or not system_name:
            return

        if system_address in self.queued_systems:
            return

        # Check in-memory cooldown for recent unregistered checks
        now = time.time()
        if not force_recheck and system_address in self.recent_unregistered_cache:
            if (now - self.recent_unregistered_cache[system_address]) < UNREGISTERED_RECHECK_COOLDOWN_SEC:
                return

        # Check if already cached in DB as REGISTERED
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT edsm_checked, edsm_registered FROM systems WHERE system_address = ?", (system_address,))
        row = c.fetchone()
        conn.close()

        # If already registered on EDSM (edsm_registered == 1), keep permanent cache
        if not force_recheck and row and row["edsm_checked"] == 1 and row["edsm_registered"] == 1:
            return

        self.queued_systems.add(system_address)
        self.request_queue.put((system_address, system_name))

    def _worker_loop(self):
        """Background worker loop that processes queued systems with strict rate limiting."""
        while self.is_running:
            try:
                item = self.request_queue.get(timeout=2.0)
            except queue.Empty:
                continue

            system_address, system_name = item
            try:
                self._throttle_delay()
                self._fetch_and_update_system(system_address, system_name)
            except Exception as e:
                print(f"[EDSM Service] Error checking {system_name} ({system_address}): {e}")
            finally:
                self.queued_systems.discard(system_address)
                self.request_queue.task_done()

    def _throttle_delay(self):
        """Enforces a strict minimum delay between external HTTP requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < REQUEST_DELAY_SEC:
            time.sleep(REQUEST_DELAY_SEC - elapsed)
        self.last_request_time = time.time()

    def _fetch_and_update_system(self, system_address: int, system_name: str):
        """Fetches system info and body discoveries from EDSM and updates the database."""
        encoded_name = urllib.parse.quote(system_name)
        sys_url = f"{EDSM_SYSTEM_API}?systemName={encoded_name}&showInformation=1&showCoordinates=1"

        req = urllib.request.Request(
            sys_url,
            headers={"User-Agent": "ED_Journal_Analyzer/v0.0.7 (EDSM Discovery Integration)"}
        )

        try:
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                if resp.status != 200:
                    self._mark_checked_unregistered(system_address)
                    return
                sys_data = json.loads(resp.read().decode("utf-8"))
        except Exception:
            self._mark_checked_unregistered(system_address)
            return

        # An empty dictionary or missing name indicates system is not in EDSM
        if not sys_data or not isinstance(sys_data, dict) or not sys_data.get("name"):
            self._mark_checked_unregistered(system_address)
            return

        # System is registered on EDSM
        # Check bodies for first discoverer
        self._throttle_delay()
        bodies_url = f"{EDSM_BODIES_API}?systemName={encoded_name}"
        bodies_req = urllib.request.Request(
            bodies_url,
            headers={"User-Agent": "ED_Journal_Analyzer/v0.0.7 (EDSM Discovery Integration)"}
        )

        first_discoverer = None
        submitted_at = None
        body_count = 0
        bodies_list = []

        try:
            with urllib.request.urlopen(bodies_req, timeout=10.0) as b_resp:
                if b_resp.status == 200:
                    b_data = json.loads(b_resp.read().decode("utf-8"))
                    if isinstance(b_data, dict):
                        body_count = b_data.get("bodyCount", 0)
                        bodies_list = b_data.get("bodies", [])
        except Exception as e:
            print(f"[EDSM Service] Error fetching bodies for {system_name}: {e}")

        # Extract discoverer from primary star or bodies
        for b in bodies_list:
            disc = b.get("discovery")
            if isinstance(disc, dict) and disc.get("commander"):
                if not first_discoverer:
                    first_discoverer = disc.get("commander")
                    submitted_at = disc.get("date")
                break

        # Save to SQLite
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""
            UPDATE systems SET
                edsm_checked = 1,
                edsm_registered = 1,
                edsm_first_discoverer = ?,
                edsm_submitted_at = ?,
                edsm_body_count = ?
            WHERE system_address = ?
        """, (first_discoverer, submitted_at, body_count, system_address))

        # Update body discoverers if available
        for b in bodies_list:
            b_name = b.get("name")
            disc = b.get("discovery")
            if b_name and isinstance(disc, dict) and disc.get("commander"):
                c.execute("""
                    UPDATE bodies SET
                        edsm_discovered_by = ?,
                        edsm_discovered_at = ?
                    WHERE system_address = ? AND body_name = ?
                """, (disc.get("commander"), disc.get("date"), system_address, b_name))

        conn.commit()
        conn.close()

    def _mark_checked_unregistered(self, system_address: int):
        """Mark system as checked and unregistered on EDSM in SQLite."""
        self.recent_unregistered_cache[system_address] = time.time()
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""
            UPDATE systems SET
                edsm_checked = 1,
                edsm_registered = 0,
                edsm_first_discoverer = NULL,
                edsm_submitted_at = NULL
            WHERE system_address = ?
        """, (system_address,))
        conn.commit()
        conn.close()


# Singleton instance
edsm_service = EDSMService()
