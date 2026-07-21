"""Initial spot/rule data, transcribed from the notes passed down for Hollister Ranch.

Numbers marked confidence='tbd' are best guesses or outright placeholders where the
notes didn't say — they exist so every spot shows up in the UI, not because the
number is trustworthy yet. Log real observations to correct them over time.
"""

SPOTS = [
    {
        "slug": "lefts",
        "name": "Lefts",
        "notes": "Winter and summer workhorse. Best on NW swell, high tide.",
        "rules": [
            {
                "swell_type": "NW",
                "min_dir": None,
                "max_dir": 300,
                "min_period_s": 14,
                "ideal_period_min_s": 15,
                "ideal_period_max_s": 20,
                "min_height_ft": None,
                "tide_pref": "high",
                "quality_label": "firing",
                "confidence": "confirmed",
                "notes": "Under 300deg and 14s+ is the classic window. Over 300deg or under 14s can "
                         "still work but you want ~7ft of swell and 15-20s period to compensate. "
                         "Periods above 20s are good but inconsistent. NW wind in the forecast "
                         "(offshore) noticeably improves quality -- not modeled yet, check manually.",
            },
            {
                "swell_type": "S",
                "min_dir": 180,
                "max_dir": None,
                "min_period_s": 14,
                "ideal_period_min_s": None,
                "ideal_period_max_s": None,
                "min_height_ft": 1.5,
                "tide_pref": "high",
                "quality_label": "firing",
                "confidence": "confirmed",
                "notes": "Notes originally said never below 190deg, but a real 180deg/7ft/16s swell "
                         "fired here at high tide -- so 180deg does work as long as period stays "
                         "above 14s. Gets the most size of the eastern/central spots in summer, "
                         "along with John's Pond.",
            },
        ],
    },
    {
        "slug": "rights",
        "name": "Rights",
        "notes": "Grouped with Lefts in the winter notes; no summer data yet.",
        "rules": [
            {
                "swell_type": "NW",
                "min_dir": None,
                "max_dir": 300,
                "min_period_s": 14,
                "ideal_period_min_s": 15,
                "ideal_period_max_s": 20,
                "min_height_ft": None,
                "tide_pref": "any",
                "quality_label": "firing",
                "confidence": "confirmed",
                "notes": "Same winter window as Lefts (notes group them together as 'Lefts and Rights').",
            },
            {
                "swell_type": "S",
                "min_dir": 200,
                "max_dir": None,
                "min_period_s": 14,
                "ideal_period_min_s": None,
                "ideal_period_max_s": None,
                "min_height_ft": 1.5,
                "tide_pref": "any",
                "quality_label": "marginal",
                "confidence": "tbd",
                "notes": "No specific summer notes for Rights -- defaulted to the general summer rule "
                         "(200deg+, never under 190). Log observations here to refine.",
            },
        ],
    },
    {
        "slug": "big-drakes",
        "name": "Big Drakes",
        "notes": "Eastern spot -- most blocked by the Channel Islands, needs a rare, very westerly south swell.",
        "rules": [
            {
                "swell_type": "S",
                "min_dir": 215,
                "max_dir": None,
                "min_period_s": 14,
                "ideal_period_min_s": None,
                "ideal_period_max_s": None,
                "min_height_ft": 2,
                "tide_pref": "any",
                "quality_label": "marginal",
                "confidence": "tbd",
                "notes": "Notes say eastern spots like Big Drakes need a 'very westerly' south swell to "
                         "break at all, and that it 'does happen' but is uncommon. 215deg is a guess at "
                         "where that threshold sits -- unconfirmed, needs real data.",
            },
        ],
    },
    {
        "slug": "little-drakes",
        "name": "Little Drakes",
        "notes": "No notes passed down yet -- purely placeholder until observations come in.",
        "rules": [],
    },
    {
        "slug": "johns-pond",
        "name": "John's Pond",
        "notes": "Zone that picks up good size alongside Lefts in summer.",
        "rules": [
            {
                "swell_type": "S",
                "min_dir": 200,
                "max_dir": None,
                "min_period_s": 14,
                "ideal_period_min_s": None,
                "ideal_period_max_s": None,
                "min_height_ft": 1.5,
                "tide_pref": "any",
                "quality_label": "firing",
                "confidence": "tbd",
                "notes": "Notes call out 'Lefts and John's Pond zone' as getting the most size in summer, "
                         "but don't give an exact direction/tide threshold -- borrowed the general summer "
                         "rule for now.",
            },
        ],
    },
    {
        "slug": "cojo",
        "name": "Cojo",
        "notes": "Westernmost, least Channel Island blockage -- most size and consistency of any spot.",
        "rules": [
            {
                "swell_type": "S",
                "min_dir": 180,
                "max_dir": None,
                "min_period_s": 14,
                "ideal_period_min_s": None,
                "ideal_period_max_s": None,
                "min_height_ft": 1.5,
                "tide_pref": "peak_high",
                "quality_label": "firing",
                "confidence": "confirmed",
                "notes": "Confirmed working at 180deg/7ft/16s -- 'the best surf you've ever had' at peak "
                         "high tide. Take south swell direction thresholds here as a floor for the ranch: "
                         "if Cojo isn't working, nothing more blocked to the east will be either.",
            },
        ],
    },
    {
        "slug": "govies",
        "name": "Govies",
        "notes": "Grouped with Cojo -- westernmost, less island blockage.",
        "rules": [
            {
                "swell_type": "S",
                "min_dir": 185,
                "max_dir": None,
                "min_period_s": 14,
                "ideal_period_min_s": None,
                "ideal_period_max_s": None,
                "min_height_ft": 1.5,
                "tide_pref": "any",
                "quality_label": "firing",
                "confidence": "tbd",
                "notes": "Notes group Govies with Cojo ('head up to Cojo and Govies') but only give a "
                         "specific example for Cojo -- assumed similar, slightly more conservative "
                         "direction floor until confirmed.",
            },
        ],
    },
    {
        "slug": "rennys",
        "name": "Rennys",
        "notes": "South swell spot, best at low tide.",
        "rules": [
            {
                "swell_type": "S",
                "min_dir": 180,
                "max_dir": None,
                "min_period_s": 14,
                "ideal_period_min_s": None,
                "ideal_period_max_s": None,
                "min_height_ft": 1.5,
                "tide_pref": "low",
                "quality_label": "firing",
                "confidence": "confirmed",
                "notes": "Confirmed working at 180deg/7ft/16s at low tide.",
            },
        ],
    },
]


def seed(conn):
    for spot in SPOTS:
        existing = conn.execute("SELECT id FROM spots WHERE slug = ?", (spot["slug"],)).fetchone()
        if existing:
            spot_id = existing["id"]
        else:
            cur = conn.execute(
                "INSERT INTO spots (name, slug, notes) VALUES (?, ?, ?)",
                (spot["name"], spot["slug"], spot["notes"]),
            )
            spot_id = cur.lastrowid

        has_rules = conn.execute(
            "SELECT COUNT(*) AS c FROM spot_rules WHERE spot_id = ?", (spot_id,)
        ).fetchone()["c"]
        if has_rules:
            continue

        for rule in spot["rules"]:
            conn.execute(
                """INSERT INTO spot_rules
                   (spot_id, swell_type, min_dir, max_dir, min_period_s,
                    ideal_period_min_s, ideal_period_max_s, min_height_ft,
                    tide_pref, quality_label, confidence, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    spot_id,
                    rule["swell_type"],
                    rule["min_dir"],
                    rule["max_dir"],
                    rule["min_period_s"],
                    rule["ideal_period_min_s"],
                    rule["ideal_period_max_s"],
                    rule["min_height_ft"],
                    rule["tide_pref"],
                    rule["quality_label"],
                    rule["confidence"],
                    rule["notes"],
                ),
            )
