import os
import sqlite3
from datetime import datetime


DB_PATH = "fishlink.db"
DB_ENV_VAR = "FISHLINK_DB_PATH"


def _get_db_path():
    return os.environ.get(DB_ENV_VAR, DB_PATH)


def get_conn():
    path = _get_db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS farms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                location_text TEXT NOT NULL,
                lat REAL,
                lng REAL,
                maps_url TEXT,
                contact TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS restaurants (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                location_text TEXT NOT NULL,
                lat REAL,
                lng REAL,
                maps_url TEXT,
                contact TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_id TEXT NOT NULL,
                fish_name TEXT,
                quantity_kg REAL NOT NULL,
                price_per_kg REAL NOT NULL,
                slot_today_morning INTEGER NOT NULL,
                slot_today_evening INTEGER NOT NULL,
                slot_next_morning INTEGER NOT NULL,
                slot_next_evening INTEGER NOT NULL,
                allow_delivery INTEGER NOT NULL,
                allow_pickup INTEGER NOT NULL,
                allow_live INTEGER NOT NULL,
                allow_fresh INTEGER NOT NULL,
                approx_time TEXT,
                FOREIGN KEY (farm_id) REFERENCES farms(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_id INTEGER NOT NULL,
                restaurant_id INTEGER NOT NULL,
                status TEXT NOT NULL CHECK (
                    status IN (
                        'Requested',
                        'Accepted',
                        'Preparing',
                        'Ready',
                        'Completed'
                    )
                ),
                quantity_kg REAL NOT NULL,
                preferred_size_text TEXT,
                fish_condition TEXT NOT NULL,
                time_slot TEXT NOT NULL,
                delivery_method TEXT NOT NULL,
                preferred_time_window TEXT,
                notes TEXT,
                distance_km REAL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (listing_id) REFERENCES listings(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER NOT NULL,
                farm_id INTEGER NOT NULL,
                restaurant_id INTEGER NOT NULL,
                stars INTEGER NOT NULL CHECK (stars BETWEEN 1 AND 5),
                comment TEXT,
                FOREIGN KEY (request_id) REFERENCES requests(id)
            )
            """
        )


def ensure_latest_schema():
    path = _get_db_path()
    if not os.path.exists(path):
        init_db()
        return
    conn = sqlite3.connect(path)
    try:
        listing_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(listings)").fetchall()
        }
        farm_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(farms)").fetchall()
        }
        restaurant_columns = {
            row[1] for row in conn.execute(
                "PRAGMA table_info(restaurants)"
            ).fetchall()
        }
    finally:
        conn.close()
    if (
        "slot_today_morning" in listing_columns
        and "contact" in farm_columns
        and "contact" in restaurant_columns
    ):
        return
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = f"{path}.bak-{timestamp}"
    os.rename(path, backup_path)
    init_db()
