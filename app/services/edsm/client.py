"""
EDSM Client & Worker Queue Manager.
Handles rate-limiting delays, background request priority queues, and unregistered system cooldowns.
"""

import time
import queue
import threading
from typing import Dict, Optional, Set, Callable

from app.db.database import get_db_connection
from app.services.edsm.constants import (
    REQUEST_DELAY_SEC,
    UNREGISTERED_RECHECK_COOLDOWN_SEC,
    ENABLE_EDSM_BODY_COMPLETION
)


class EDSMClient:
    def __init__(self, processor_callback: Optional[Callable[[int, str], None]] = None):
        self.high_priority_queue: queue.Queue = queue.Queue()
        self.low_priority_queue: queue.Queue = queue.Queue()
        self.queued_systems: Set[int] = set()
        self.priority_systems: Set[int] = set()
        self.recent_unregistered_cache: Dict[int, float] = {}
        self.last_request_time: float = 0.0
        self.is_running: bool = True
        self.processor_callback = processor_callback
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

    def set_processor_callback(self, cb: Callable[[int, str], None]):
        self.processor_callback = cb

    def throttle_delay(self):
        """Enforces a strict minimum delay between external HTTP requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < REQUEST_DELAY_SEC:
            time.sleep(REQUEST_DELAY_SEC - elapsed)
        self.last_request_time = time.time()

    def queue_system_check(self, system_address: int, system_name: str, force_recheck: bool = False, priority: bool = False):
        """Queue a system for EDSM registration and discovery verification."""
        if not system_address or not system_name:
            return

        # If priority requested, skip if already queued in high priority
        if priority:
            if system_address in self.priority_systems:
                return
        else:
            if system_address in self.queued_systems or system_address in self.priority_systems:
                return

        # Check in-memory cooldown for recent unregistered checks
        now = time.time()
        if not force_recheck and system_address in self.recent_unregistered_cache:
            if (now - self.recent_unregistered_cache[system_address]) < UNREGISTERED_RECHECK_COOLDOWN_SEC:
                return

        # Check if already cached in DB as REGISTERED
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT edsm_checked, edsm_registered, edsm_body_count FROM systems WHERE system_address = ?", (system_address,))
        row = c.fetchone()
        
        needs_body_completion = False
        if row and row["edsm_checked"] == 1 and row["edsm_registered"] == 1:
            if ENABLE_EDSM_BODY_COMPLETION and (row["edsm_body_count"] or 0) > 0:
                c.execute("SELECT COUNT(*) as cnt FROM bodies WHERE system_address = ?", (system_address,))
                b_row = c.fetchone()
                if b_row and b_row["cnt"] == 0:
                    needs_body_completion = True
        conn.close()

        # If already registered on EDSM (edsm_registered == 1), keep permanent cache
        # unless body completion is needed or force_recheck is specified
        if not force_recheck and row and row["edsm_checked"] == 1 and row["edsm_registered"] == 1:
            if not needs_body_completion:
                return

        if priority:
            self.priority_systems.add(system_address)
            self.high_priority_queue.put((system_address, system_name))
        else:
            self.queued_systems.add(system_address)
            self.low_priority_queue.put((system_address, system_name))

    def _worker_loop(self):
        """Background worker loop that processes queued systems with strict rate limiting."""
        while self.is_running:
            item = None
            is_priority = False
            try:
                item = self.high_priority_queue.get_nowait()
                is_priority = True
            except queue.Empty:
                try:
                    item = self.low_priority_queue.get(timeout=1.0)
                    is_priority = False
                except queue.Empty:
                    continue

            system_address, system_name = item
            try:
                self.throttle_delay()
                if self.processor_callback:
                    self.processor_callback(system_address, system_name)
            except Exception as e:
                print(f"[EDSM Service] Error checking {system_name} ({system_address}): {e}")
            finally:
                if is_priority:
                    self.priority_systems.discard(system_address)
                    self.high_priority_queue.task_done()
                else:
                    self.queued_systems.discard(system_address)
                    self.low_priority_queue.task_done()

    def mark_checked_unregistered(self, system_address: int):
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
