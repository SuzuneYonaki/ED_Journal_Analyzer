import unittest
import sqlite3
from pathlib import Path
from fastapi.testclient import TestClient

from app.server.api import app
from app.db.database import get_db_connection, init_db


class TestPartialDSS(unittest.TestCase):
    def setUp(self):
        self.conn = get_db_connection()
        init_db(self.conn, force=True)
        self.client = TestClient(app)
        self.cursor = self.conn.cursor()

        # Seed test systems and bodies
        # System 1: Fully mapped (2 mappable bodies, 2 user mapped)
        self.cursor.execute("""
            INSERT OR REPLACE INTO systems (system_address, star_system, total_bodies, scanned_bodies, last_visited)
            VALUES (90001, 'Test-Fully-Mapped', 2, 2, '2026-10-26T10:00:00')
        """)
        self.cursor.execute("""
            INSERT OR REPLACE INTO bodies (system_address, body_id, body_name, planet_class, is_mapped_by_user)
            VALUES (90001, 1, 'Test-Fully-Mapped 1', 'High metal content body', 1)
        """)
        self.cursor.execute("""
            INSERT OR REPLACE INTO bodies (system_address, body_id, body_name, planet_class, is_mapped_by_user)
            VALUES (90001, 2, 'Test-Fully-Mapped 2', 'Rocky body', 1)
        """)

        # System 2: Partially mapped (3 mappable bodies, 1 user mapped, 2 unmapped)
        self.cursor.execute("""
            INSERT OR REPLACE INTO systems (system_address, star_system, total_bodies, scanned_bodies, last_visited)
            VALUES (90002, 'Test-Partial-Mapped', 3, 3, '2026-10-26T11:00:00')
        """)
        self.cursor.execute("""
            INSERT OR REPLACE INTO bodies (system_address, body_id, body_name, planet_class, is_mapped_by_user)
            VALUES (90002, 1, 'Test-Partial-Mapped 1', 'High metal content body', 1)
        """)
        self.cursor.execute("""
            INSERT OR REPLACE INTO bodies (system_address, body_id, body_name, planet_class, is_mapped_by_user)
            VALUES (90002, 2, 'Test-Partial-Mapped 2', 'Rocky body', 0)
        """)
        self.cursor.execute("""
            INSERT OR REPLACE INTO bodies (system_address, body_id, body_name, planet_class, is_mapped_by_user)
            VALUES (90002, 3, 'Test-Partial-Mapped 3', 'Icy body', 0)
        """)

        # System 3: Not mapped at all (2 bodies, 0 user mapped)
        self.cursor.execute("""
            INSERT OR REPLACE INTO systems (system_address, star_system, total_bodies, scanned_bodies, last_visited)
            VALUES (90003, 'Test-Not-Mapped', 2, 2, '2026-10-26T12:00:00')
        """)
        self.cursor.execute("""
            INSERT OR REPLACE INTO bodies (system_address, body_id, body_name, planet_class, is_mapped_by_user)
            VALUES (90003, 1, 'Test-Not-Mapped 1', 'High metal content body', 0)
        """)
        self.cursor.execute("""
            INSERT OR REPLACE INTO bodies (system_address, body_id, body_name, planet_class, is_mapped_by_user)
            VALUES (90003, 2, 'Test-Not-Mapped 2', 'Icy body', 0)
        """)
        self.conn.commit()

    def tearDown(self):
        self.cursor.execute("DELETE FROM bodies WHERE system_address IN (90001, 90002, 90003)")
        self.cursor.execute("DELETE FROM systems WHERE system_address IN (90001, 90002, 90003)")
        self.conn.commit()
        self.conn.close()

    def test_api_filter_partial_dss(self):
        # Query with has_partial_dss=1
        res = self.client.get("/api/systems?has_partial_dss=1&q=Test-")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        names = [s["star_system"] for s in data.get("systems", [])]

        # Only Test-Partial-Mapped should match
        self.assertIn("Test-Partial-Mapped", names)
        self.assertNotIn("Test-Fully-Mapped", names)
        self.assertNotIn("Test-Not-Mapped", names)

        # Check metadata payload
        partial_sys = next(s for s in data["systems"] if s["star_system"] == "Test-Partial-Mapped")
        self.assertTrue(partial_sys.get("is_partial_dss"))
        self.assertEqual(partial_sys.get("user_mapped_bodies"), 1)
        self.assertEqual(partial_sys.get("mappable_bodies"), 3)

    def test_ui_components_have_partial_dss(self):
        root = Path(__file__).resolve().parent.parent

        left_content = (root / "app" / "ui" / "components" / "left_pane.html").read_text(encoding="utf-8")
        self.assertIn('data-filter="has_partial_dss"', left_content)
        self.assertIn('dss-chip', left_content)

        i18n_content = (root / "app" / "ui" / "js" / "i18n.js").read_text(encoding="utf-8")
        self.assertIn("filter_partial_dss", i18n_content)
        self.assertIn("tag_partial_dss", i18n_content)

        syslist_content = (root / "app" / "ui" / "js" / "system_list.js").read_text(encoding="utf-8")
        self.assertIn("has_partial_dss", syslist_content)
        self.assertIn("is_partial_dss", syslist_content)
        self.assertIn("tag-partial-dss", syslist_content)


if __name__ == "__main__":
    unittest.main()
