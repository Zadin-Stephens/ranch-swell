"""Field observations logged in person at the Ranch, kept under version control.

The SQLite database is gitignored and disposable -- every buoy reading in it can
be re-fetched from CDIP at any time. These observations cannot. They exist only
because somebody drove out and looked at the water, so they live in the repo and
get seeded into the database on startup.

Add new sessions to OBSERVATIONS as they come in. `height_ft` is the face height
as called on the day, not a measurement; 0 means flat / not breaking. Where a
number encodes only a relative ordering between two spots rather than a real
difference, the note says so explicitly.
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

RANCH_TZ = ZoneInfo("America/Los_Angeles")

OBSERVATIONS = [
    # --- 2026-08-06, midday -------------------------------------------------
    # First logged session. Mixed sea that day: roughly 3ft of 12.5s S swell out
    # of ~190deg running underneath roughly 3ft of 9s NW windswell out of
    # ~310deg. Buoy total Hs held 2.9-3.7ft across the whole 24h with no build
    # and no drop, so the state at 12:39 was representative of the entire day.
    #
    # Value of this session is as a negative result: a 12.5s S swell produced
    # nothing rideable anywhere east of Point Conception. That supports the 14s
    # period floor the notes assigned to every S-swell rule, which until now was
    # only asserted, never tested against a day that fell below it.
    {
        "spot_slug": "big-drakes",
        "observed_at_local": "2026-08-06T12:39",
        "height_ft": 1.0,
        "note": "Flat to 1ft. Slightly bigger than Little Drakes, but only barely.",
    },
    {
        "spot_slug": "little-drakes",
        "observed_at_local": "2026-08-06T12:39",
        "height_ft": 0.8,
        "note": (
            "Flat. Marginally smaller than Big Drakes -- the 0.8 encodes that ordering "
            "only, the two were within noise of each other."
        ),
    },
    {
        "spot_slug": "bulito",
        "observed_at_local": "2026-08-06T12:39",
        "height_ft": 0.0,
        "note": "Flat, not breaking.",
    },
    {
        "spot_slug": "auggies",
        "observed_at_local": "2026-08-06T12:39",
        "height_ft": 1.0,
        "note": "Breaking a little, but still tiny -- about 1ft.",
    },
    {
        "spot_slug": "point-conception",
        "observed_at_local": "2026-08-06T12:39",
        "height_ft": 2.0,
        "note": "Around 2ft -- clearly the biggest of the spots checked that day.",
    },
]


def _to_utc(observed_at_local: str) -> str:
    """Interpret a naive local timestamp as Ranch time and return UTC ISO-8601."""
    return (
        datetime.fromisoformat(observed_at_local)
        .replace(tzinfo=RANCH_TZ)
        .astimezone(timezone.utc)
        .isoformat()
    )


# Buoy readings land every 30 minutes, so anything inside this window is the
# reading that was current when the observer was standing on the bluff. Beyond
# it there is no matching reading in the database yet and we record none, rather
# than silently pinning an August session to a September swell.
MAX_PIN_DRIFT_S = 45 * 60


def _pin(conn, observed_at_local: str):
    """Return the id of the buoy reading current at that moment, or None."""
    row = conn.execute(
        """SELECT id, ABS(strftime('%s', observed_at_utc) - strftime('%s', ?)) AS drift
           FROM buoy_readings
           ORDER BY drift
           LIMIT 1""",
        (_to_utc(observed_at_local),),
    ).fetchone()
    if row is None or row["drift"] > MAX_PIN_DRIFT_S:
        return None
    return row["id"]


def seed(conn):
    """Insert any field observations not already recorded, and re-pin loose ones.

    Idempotent: the unique index on (spot_id, observed_at_local, source) makes
    re-running this on every startup a no-op once an entry has landed.

    An observation whose buoy reading was not in the database at insert time is
    left unpinned and retried on each subsequent startup, so backfilling the
    buoy history later repairs the link without touching the observation.
    """
    now = datetime.now(timezone.utc).isoformat()
    inserted = 0

    for obs in OBSERVATIONS:
        spot = conn.execute(
            "SELECT id FROM spots WHERE slug = ?", (obs["spot_slug"],)
        ).fetchone()
        if not spot:
            raise ValueError(
                f"field_log references unknown spot slug {obs['spot_slug']!r} -- "
                "add it to seed_data.SPOTS first"
            )

        cur = conn.execute(
            """INSERT OR IGNORE INTO observations
               (spot_id, observed_at_local, observed_height_ft, note,
                nearest_buoy_reading_id, created_at, source)
               VALUES (?, ?, ?, ?, ?, ?, 'field_log')""",
            (
                spot["id"],
                obs["observed_at_local"],
                obs["height_ft"],
                obs["note"],
                _pin(conn, obs["observed_at_local"]),
                now,
            ),
        )
        inserted += cur.rowcount

    repinned = 0
    for row in conn.execute(
        """SELECT id, observed_at_local FROM observations
           WHERE source = 'field_log' AND nearest_buoy_reading_id IS NULL"""
    ).fetchall():
        reading_id = _pin(conn, row["observed_at_local"])
        if reading_id is not None:
            conn.execute(
                "UPDATE observations SET nearest_buoy_reading_id = ? WHERE id = ?",
                (reading_id, row["id"]),
            )
            repinned += 1

    return inserted, repinned
