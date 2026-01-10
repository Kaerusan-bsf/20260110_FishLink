import glob
import os
import sqlite3
import unittest

from db import ensure_latest_schema, get_conn


class DbSchemaTests(unittest.TestCase):
    def setUp(self):
        self.db_path = "fishlink_schema_test.db"
        os.environ["FISHLINK_DB_PATH"] = self.db_path
        for path in glob.glob(f"{self.db_path}.bak-*"):
            os.remove(path)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def tearDown(self):
        for path in glob.glob(f"{self.db_path}.bak-*"):
            os.remove(path)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.environ.pop("FISHLINK_DB_PATH", None)

    def test_ensure_latest_schema_recreates_old_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE listings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    farm_id INTEGER NOT NULL,
                    fish_name TEXT
                )
                """
            )
        ensure_latest_schema()
        backups = glob.glob(f"{self.db_path}.bak-*")
        self.assertEqual(len(backups), 1)
        with get_conn() as conn:
            columns = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(listings)").fetchall()
            }
            farm_columns = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(farms)").fetchall()
            }
        self.assertIn("slot_today_morning", columns)
        self.assertIn("contact", farm_columns)


if __name__ == "__main__":
    unittest.main()
