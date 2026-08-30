"""
Real-time Journal File Watcher Module for Elite Dangerous.
Monitors configured journal directories for Journal.*.log file updates and
dispatches line-level events and batch update notifications.

All code, strings, and comments in this module are strictly English ASCII.
"""

import time
import threading
import glob
import os
from pathlib import Path
from typing import List, Union, Dict, Tuple, Optional
from app.parser.journal_parser import JournalParser
from app.db.database import get_db_connection

class JournalWatcher(threading.Thread):
    def __init__(
        self,
        journal_dirs: Union[str, Path, List[Union[str, Path]]],
        interval: float = 0.4,
        on_update_callback=None,
        on_event_callback=None
    ):
        super().__init__(daemon=True)
        if isinstance(journal_dirs, (str, Path)):
            self.journal_dirs = [Path(journal_dirs)]
        else:
            self.journal_dirs = [Path(d) for d in journal_dirs]
        self.interval = max(0.1, interval)
        self.on_update_callback = on_update_callback
        self.on_event_callback = on_event_callback
        self.running = True
        self.conn = None
        self.parser = None
        # Track file stats: {filepath: (size, mtime)}
        self.file_stats: Dict[str, Tuple[int, float]] = {}
        self.last_dir_scan_time = 0.0
        self.files_scan_interval = 1.0
        self.initialized = False

    def _handle_journal_event(self, event_name: str, event_data: dict):
        if self.on_event_callback:
            try:
                self.on_event_callback(event_name, event_data)
            except Exception as e:
                print(f"[Watcher Event Error] {e}")

    def run(self):
        self.conn = get_db_connection()
        self.parser = JournalParser(self.conn, event_callback=self._handle_journal_event)
        
        # Initial scan: seed file stats without triggering events for past data
        self._scan_active_files(initial_seed=True)
        self.initialized = True

        while self.running:
            try:
                now = time.time()
                if now - self.last_dir_scan_time > self.files_scan_interval:
                    self._scan_active_files(initial_seed=False)
                    self.last_dir_scan_time = now

                self.check_file_updates()
            except Exception as e:
                print(f"[Watcher Error] {e}")
            time.sleep(self.interval)

        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass

    def _scan_active_files(self, initial_seed: bool = False):
        """Scans all monitored directories for Journal.*.log files and tracks the most recent ones."""
        found_files = []
        for j_dir in self.journal_dirs:
            if not j_dir.exists():
                continue
            pattern = str(j_dir / "Journal.*.log")
            matched = glob.glob(pattern)
            found_files.extend(matched)

        if not found_files:
            return

        # Sort files by modification time descending
        found_files.sort(key=lambda f: os.path.getmtime(f) if os.path.exists(f) else 0, reverse=True)
        
        # Track recent files (e.g. latest 5 files)
        recent_files = found_files[:5]
        for fpath in recent_files:
            if fpath not in self.file_stats:
                try:
                    st = os.stat(fpath)
                    if initial_seed:
                        # On initial startup, record current file stats so only future writes trigger events
                        self.file_stats[fpath] = (st.st_size, st.st_mtime)
                    else:
                        # New file appeared while running: trigger full parse
                        self.file_stats[fpath] = (0, 0.0)
                except Exception:
                    pass

    def check_file_updates(self):
        if not self.file_stats:
            self._scan_active_files(initial_seed=False)
            if not self.file_stats:
                return

        updated_any = False
        latest_updated_file = None

        for fpath, last_stat in list(self.file_stats.items()):
            p = Path(fpath)
            if not p.exists():
                continue
            try:
                st = p.stat()
                current_stat = (st.st_size, st.st_mtime)

                if current_stat != last_stat:
                    # File size or mtime changed: parse newly appended lines
                    self.parser.parse_file(fpath)
                    self.file_stats[fpath] = current_stat
                    updated_any = True
                    latest_updated_file = fpath
            except Exception as err:
                print(f"[Watcher Check Error] {fpath}: {err}")

        if updated_any and self.on_update_callback:
            try:
                self.on_update_callback(latest_updated_file)
            except Exception as cb_err:
                print(f"[Watcher Callback Error] {cb_err}")

    def stop(self):
        self.running = False
