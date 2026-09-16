import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "hollister.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS buoy_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    observed_at_utc TEXT NOT NULL UNIQUE,
    hs_m REAL NOT NULL,
    hs_ft REAL NOT NULL,
    tp_s REAL NOT NULL,
    ta_s REAL NOT NULL,
    dp_deg REAL NOT NULL,
    fetched_at_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS spots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS spot_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    spot_id INTEGER NOT NULL REFERENCES spots(id),
    swell_type TEXT NOT NULL CHECK(swell_type IN ('NW', 'S')),
    min_dir REAL,
    max_dir REAL,
    min_period_s REAL,
    ideal_period_min_s REAL,
    ideal_period_max_s REAL,
    min_height_ft REAL,
    tide_pref TEXT CHECK(tide_pref IN ('low', 'mid', 'high', 'peak_high', 'any')) DEFAULT 'any',
    quality_label TEXT,
    confidence TEXT NOT NULL CHECK(confidence IN ('confirmed', 'tbd')) DEFAULT 'tbd',
    notes TEXT
);

CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    spot_id INTEGER NOT NULL REFERENCES spots(id),
    observed_at_local TEXT NOT NULL,
    observed_height_ft REAL NOT NULL,
    note TEXT,
    nearest_buoy_reading_id INTEGER REFERENCES buoy_readings(id),
    created_at TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'ui'
);

CREATE UNIQUE INDEX IF NOT EXISTS observations_unique
    ON observations (spot_id, observed_at_local, source);
"""


@contextmanager
def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        _migrate(conn)
        conn.executescript(SCHEMA)


def _migrate(conn):
    """Bring a pre-existing database up to the current schema.

    Runs before the CREATE statements so the unique index below can be built on
    a table that already has the column it indexes.
    """
    tables = {
        r["name"]
        for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }
    if "observations" not in tables:
        return  # fresh database; SCHEMA creates it correctly

    columns = {r["name"] for r in conn.execute("PRAGMA table_info(observations)")}
    if "source" not in columns:
        conn.execute(
            "ALTER TABLE observations ADD COLUMN source TEXT NOT NULL DEFAULT 'ui'"
        )


def latest_buoy_reading(conn):
    return conn.execute(
        "SELECT * FROM buoy_readings ORDER BY observed_at_utc DESC LIMIT 1"
    ).fetchone()


def insert_buoy_reading(conn, observed_at_utc, hs_m, hs_ft, tp_s, ta_s, dp_deg, fetched_at_utc):
    conn.execute(
        """INSERT OR IGNORE INTO buoy_readings
           (observed_at_utc, hs_m, hs_ft, tp_s, ta_s, dp_deg, fetched_at_utc)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (observed_at_utc, hs_m, hs_ft, tp_s, ta_s, dp_deg, fetched_at_utc),
    )


def all_spots(conn):
    return conn.execute("SELECT * FROM spots ORDER BY name").fetchall()


def spot_by_slug(conn, slug):
    return conn.execute("SELECT * FROM spots WHERE slug = ?", (slug,)).fetchone()


def rules_for_spot(conn, spot_id):
    return conn.execute(
        "SELECT * FROM spot_rules WHERE spot_id = ?", (spot_id,)
    ).fetchall()


def nearest_buoy_reading_to(conn, observed_at_local_utc):
    return conn.execute(
        """SELECT * FROM buoy_readings
           ORDER BY ABS(strftime('%s', observed_at_utc) - strftime('%s', ?))
           LIMIT 1""",
        (observed_at_local_utc,),
    ).fetchone()


def readings_around(conn, center_utc, hours=3):
    """Every buoy reading within `hours` either side of a moment in time.

    A single reading reports only whichever swell train happened to own the
    spectral peak at that instant, which on a mixed day flips back and forth.
    A window of them shows what was actually in the water.
    """
    return conn.execute(
        """SELECT * FROM buoy_readings
           WHERE ABS(strftime('%s', observed_at_utc) - strftime('%s', ?)) <= ?
           ORDER BY observed_at_utc""",
        (center_utc, hours * 3600),
    ).fetchall()


def insert_observation(conn, spot_id, observed_at_local, observed_height_ft, note, nearest_buoy_reading_id, created_at):
    conn.execute(
        """INSERT INTO observations
           (spot_id, observed_at_local, observed_height_ft, note, nearest_buoy_reading_id, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (spot_id, observed_at_local, observed_height_ft, note, nearest_buoy_reading_id, created_at),
    )


def observations_for_spot(conn, spot_id):
    return conn.execute(
        """SELECT o.*, b.hs_ft, b.tp_s, b.dp_deg, b.observed_at_utc AS buoy_observed_at_utc
           FROM observations o
           LEFT JOIN buoy_readings b ON b.id = o.nearest_buoy_reading_id
           WHERE o.spot_id = ?
           ORDER BY o.observed_at_local DESC""",
        (spot_id,),
    ).fetchall()
