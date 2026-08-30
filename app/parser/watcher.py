import time
import threading
import glob
import os
from pathlib import Path
from typing import List, Union, Dict, Tuple, Optional
from app.parser.journal_parser import JournalParser
from app.db.database import get_db_connection

class JournalWatcher(threading.Thread):
    def __init__(self, journal_dirs: Union[str, Path, List[Union[str, Path]]], interval: float = 0.5, on_update_callback=None):
        super().__init__(daemon=True)
        if isinstance(journal_dirs, (str, Path)):
            self.journal_dirs = [Path(journal_dirs)]
        else:
            self.journal_dirs = [Path(d) for d in journal_dirs]
        self.interval = max(0.2, interval)
        self.on_update_callback = on_update_callback
        self.running = True
        self.conn = None
        self.parser = None
        # Track file stats: {filepath: (size, mtime)}
        self.file_stats: Dict[str, Tuple[int, float]] = {}
        self.last_dir_scan_time = 0.0
        self.files_scan_interval = 1.0 # Rescan directories for new files every 1 second

    def run(self):
        # Initialize connection inside the worker thread
        self.conn = get_db_connection()
        self.parser = JournalParser(self.conn)
        self._scan_active_files()

        while self.running:
            try:
                now = time.time()
                # Periodically check for newly created journal files
                if now - self.last_dir_scan_time > self.files_scan_interval:
                    self._scan_active_files()
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

    def _scan_active_files(self):
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
                    # Initialize with (0, 0.0) so first check triggers a parse if not already in DB
                    self.file_stats[fpath] = (0, 0.0)
                except Exception:
                    pass

    def check_file_updates(self):
        if not self.file_stats:
            self._scan_active_files()
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
