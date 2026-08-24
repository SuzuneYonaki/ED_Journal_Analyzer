import time
import threading
import glob
import os
from pathlib import Path
from app.parser.journal_parser import JournalParser
from app.db.database import get_db_connection

class JournalWatcher(threading.Thread):
    def __init__(self, journal_dir: str, interval: float = 2.0, on_update_callback=None):
        super().__init__(daemon=True)
        self.journal_dir = journal_dir
        self.interval = interval
        self.on_update_callback = on_update_callback
        self.running = True
        self.conn = None
        self.parser = None
        self.current_latest_file = None
        self.last_stat = (0, 0.0) # (file_size, mtime)
        self.files_scan_interval = 10.0 # Only rescan directory every 10 seconds
        self.last_dir_scan_time = 0.0

    def run(self):
        # Initialize connection inside the worker thread
        self.conn = get_db_connection()
        self.parser = JournalParser(self.conn)
        self._find_latest_file()

        while self.running:
            try:
                now = time.time()
                # Periodically check for newly created journal files
                if now - self.last_dir_scan_time > self.files_scan_interval:
                    self._find_latest_file()
                    self.last_dir_scan_time = now

                self.check_latest_file_updates()
            except Exception as e:
                print(f"[Watcher Error] {e}")
            time.sleep(self.interval)

        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass

    def _find_latest_file(self):
        if not os.path.exists(self.journal_dir):
            return
        files = glob.glob(os.path.join(self.journal_dir, "Journal.*.log"))
        if not files:
            return
        # Get newest file by sorting
        files.sort()
        newest = files[-1]
        if newest != self.current_latest_file:
            self.current_latest_file = newest
            p = Path(newest)
            if p.exists():
                st = p.stat()
                self.last_stat = (st.st_size, st.st_mtime)

    def check_latest_file_updates(self):
        if not self.current_latest_file:
            return

        p = Path(self.current_latest_file)
        if not p.exists():
            return

        st = p.stat()
        current_stat = (st.st_size, st.st_mtime)

        # Only process if file size or mtime changed
        if current_stat != self.last_stat:
            self.parser.parse_file(self.current_latest_file)
            self.last_stat = current_stat
            if self.on_update_callback:
                try:
                    self.on_update_callback(self.current_latest_file)
                except Exception as cb_err:
                    print(f"[Watcher Callback Error] {cb_err}")

    def stop(self):
        self.running = False
