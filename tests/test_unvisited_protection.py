import unittest
import sqlite3
from pathlib import Path
from fastapi.testclient import TestClient

from app.server.api import app
from app.db.database import get_db_connection, init_db
from app.parser.journal_parser import JournalParser
from app.services.edsm.stats_aggregator import update_system_aggregated_stats


class TestUnvisitedProtection(unittest.TestCase):
    def setUp(self):
        self.conn = get_db_connection()
        init_db(self.conn, force=True)
        self.client = TestClient(app)
        self.cursor = self.conn.cursor()

        # Seed an unvisited external system with bodies that have was_discovered = 0 (EDSM import scenario)
        self.cursor.execute("""
            INSERT OR REPLACE INTO systems (system_address, star_system, total_bodies, scanned_bodies, visit_count, is_external, has_first_discover, first_discovered_bodies)
            VALUES (99901, 'Unvisited-External-Sys', 3, 0, 0, 1, 0, 0)
        """)
        self.cursor.execute("""
            INSERT OR REPLACE INTO bodies (system_address, body_id, body_name, planet_class, was_discovered, is_mapped_by_user)
            VALUES (99901, 1, 'Unvisited-External-Sys 1', 'High metal content body', 0, 0)
        """)
        self.cursor.execute("""
            INSERT OR REPLACE INTO bodies (system_address, body_id, body_name, planet_class, was_discovered, is_mapped_by_user)
            VALUES (99901, 2, 'Unvisited-External-Sys 2', 'Rocky body', 0, 0)
        """)
        self.conn.commit()

    def tearDown(self):
        self.cursor.execute("DELETE FROM bodies WHERE system_address = 99901")
        self.cursor.execute("DELETE FROM systems WHERE system_address = 99901")
        self.conn.commit()
        self.conn.close()

    def test_stats_aggregator_guards_unvisited_first_discovery(self):
        # Run stats aggregator
        update_system_aggregated_stats(self.conn, 99901)
        self.conn.commit()

        self.cursor.execute("SELECT has_first_discover, first_discovered_bodies, scanned_bodies FROM systems WHERE system_address = 99901")
        row = self.cursor.fetchone()
        self.assertIsNotNone(row)
        # Must be 0 because CMDR has never visited this system!
        self.assertEqual(row["has_first_discover"], 0)
        self.assertEqual(row["first_discovered_bodies"], 0)
        self.assertEqual(row["scanned_bodies"], 0)

    def test_api_systems_does_not_flag_unvisited_as_first_discover(self):
        res = self.client.get("/api/systems?has_first_discover=1&q=Unvisited-External-Sys")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        names = [s["star_system"] for s in data.get("systems", [])]
        self.assertNotIn("Unvisited-External-Sys", names)

    def test_app_js_has_unvisited_system_protection(self):
        root = Path(__file__).resolve().parent.parent
        app_js = (root / "app" / "ui" / "js" / "app.js").read_text(encoding="utf-8")

        self.assertIn("isUnvisitedSys", app_js)
        self.assertIn("unvisited-system-placeholder", app_js)
        self.assertIn("btn-preview-external-map", app_js)
        self.assertIn("state.previewExternalMap", app_js)


if __name__ == "__main__":
    unittest.main()
