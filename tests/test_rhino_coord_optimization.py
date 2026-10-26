import unittest
import sqlite3
from unittest.mock import MagicMock
import time

from app.db.database import init_db, save_or_merge_mining_site
from app.live.rhino.note_integrator import update_body_note_in_db
from app.live.telemetry import TelemetryTracker
from app.parser.journal_parser import JournalParser


class CommitCountingConnection:
    """Wrapper around sqlite3.Connection to count commit() calls."""
    def __init__(self, real_conn):
        self._real_conn = real_conn
        self.commit_count = 0

    def commit(self):
        self.commit_count += 1
        return self._real_conn.commit()

    def cursor(self):
        return self._real_conn.cursor()

    def close(self):
        return self._real_conn.close()

    def __getattr__(self, name):
        return getattr(self._real_conn, name)


class TestRhinoCoordOptimization(unittest.TestCase):
    def setUp(self):
        real_conn = sqlite3.connect(":memory:")
        real_conn.row_factory = sqlite3.Row
        init_db(real_conn)
        self.conn = CommitCountingConnection(real_conn)

    def tearDown(self):
        self.conn.close()

    def test_save_or_merge_mining_site_skips_redundant_update(self):
        # First save
        site_id = save_or_merge_mining_site(
            conn=self.conn,
            system_address=1001,
            star_system="TestSys",
            body_id=1,
            body_name="Body 1",
            latitude=12.3456,
            longitude=-45.6789,
            material_name="Iron"
        )
        self.assertIsNotNone(site_id)
        self.assertEqual(self.conn.commit_count, 1)

        # Reset count
        self.conn.commit_count = 0

        # Second save with exact same material at same site -> should be skipped (no commit)
        same_site_id = save_or_merge_mining_site(
            conn=self.conn,
            system_address=1001,
            star_system="TestSys",
            body_id=1,
            body_name="Body 1",
            latitude=12.3457,  # slightly different coordinate within same site threshold
            longitude=-45.6788,
            material_name="Iron"
        )
        self.assertEqual(same_site_id, site_id)
        self.assertEqual(self.conn.commit_count, 0, "Redundant UPDATE should not trigger conn.commit()")

        # Third save with a NEW material at same site -> should trigger commit
        save_or_merge_mining_site(
            conn=self.conn,
            system_address=1001,
            star_system="TestSys",
            body_id=1,
            body_name="Body 1",
            latitude=12.3457,
            longitude=-45.6788,
            material_name="Nickel"
        )
        self.assertEqual(self.conn.commit_count, 1, "New material should trigger commit")

    def test_update_body_note_skips_redundant_update(self):
        # First save
        note1 = update_body_note_in_db(
            conn=self.conn,
            system_address=1001,
            body_id=1,
            body_name="Body 1",
            star_system="TestSys",
            lat=12.3456,
            lon=-45.6789,
            minerals=["Iron"]
        )
        self.assertIn("Iron", note1)
        self.assertEqual(self.conn.commit_count, 1)

        self.conn.commit_count = 0

        # Second save with same mineral and coordinates -> should not trigger commit
        note2 = update_body_note_in_db(
            conn=self.conn,
            system_address=1001,
            body_id=1,
            body_name="Body 1",
            star_system="TestSys",
            lat=12.3456,
            lon=-45.6789,
            minerals=["Iron"]
        )
        self.assertEqual(note1, note2)
        self.assertEqual(self.conn.commit_count, 0, "Redundant note update should skip conn.commit()")

    def test_telemetry_tracker_burst_caching(self):
        tracker = TelemetryTracker()
        tracker.last_status = {"Latitude": 10.5, "Longitude": -20.5, "Flags": 0x04000000}
        tracker.last_read_time = time.monotonic()

        # Should immediately return cached coordinates without checking disk
        lat, lon = tracker.get_coordinates()
        self.assertEqual(lat, 10.5)
        self.assertEqual(lon, -20.5)

    def test_journal_parser_unlocated_mining_optimization(self):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        parser = JournalParser(db_conn=mock_conn)
        parser.current_system_address = 1001
        parser.current_body_id = 1
        parser._has_unlocated_mining = False

        # Status event with coords when _has_unlocated_mining is False
        parser.process_journal_line('{"event":"Status", "Latitude":12.34, "Longitude":56.78}')

        # Cursor execute should NOT have been called with "UPDATE surface_mining_activities"
        for call_args in mock_cursor.execute.call_args_list:
            sql = call_args[0][0]
            self.assertNotIn("UPDATE surface_mining_activities", sql)

        # Now simulate unlocated mining
        parser._has_unlocated_mining = True
        parser.process_journal_line('{"event":"Status", "Latitude":12.34, "Longitude":56.78}')

        # Now it SHOULD have been called once and reset flag to False
        executed_sqls = [call_args[0][0] for call_args in mock_cursor.execute.call_args_list]
        self.assertTrue(any("UPDATE surface_mining_activities" in s for s in executed_sqls))
        self.assertFalse(parser._has_unlocated_mining)


if __name__ == "__main__":
    unittest.main()
