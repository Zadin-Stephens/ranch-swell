"""Swell classification and per-spot prediction engine."""

from dataclasses import dataclass
from statistics import median

NW_WINDOW = (260, 330)
S_WINDOW = (160, 230)

CALL_ORDER = ["FIRING", "GOOD_BUT_INCONSISTENT", "MARGINAL", "FLAT"]

TIDE_LABELS = {
    "low": "best at low tide",
    "mid": "best at mid tide",
    "high": "best at high tide",
    "peak_high": "best at peak high tide",
    "any": "not tide-sensitive (per notes so far)",
}


def classify_swell(dp_deg: float) -> str:
    if NW_WINDOW[0] <= dp_deg <= NW_WINDOW[1]:
        return "NW"
    if S_WINDOW[0] <= dp_deg <= S_WINDOW[1]:
        return "S"
    return "unclear"


@dataclass
class SwellTrain:
    """One swell train seen across a window of buoy readings."""
    swell_type: str
    n: int
    share: float       # fraction of readings in the window this train owned
    hs_ft: float
    tp_s: float
    dp_deg: float

    def summary(self) -> str:
        return (
            f"{self.swell_type} {self.hs_ft:.1f}ft {self.tp_s:.1f}s {self.dp_deg:.0f}deg"
        )


def partition_readings(readings) -> list[SwellTrain]:
    """Separate a window of readings into the distinct swell trains present.

    The buoy reports a single peak direction and period per reading. When two
    trains of comparable energy overlap, that peak alternates between them, so
    consecutive readings disagree wildly about what the ocean is doing. Grouping
    a window by direction window and taking the median of each group recovers
    both trains instead of forcing a single misleading label.
    """
    usable = [r for r in readings if classify_swell(r["dp_deg"]) != "unclear"]
    if not usable:
        return []

    trains = []
    for label in ("S", "NW"):
        members = [r for r in usable if classify_swell(r["dp_deg"]) == label]
        if not members:
            continue
        trains.append(
            SwellTrain(
                swell_type=label,
                n=len(members),
                share=len(members) / len(usable),
                hs_ft=median(r["hs_ft"] for r in members),
                tp_s=median(r["tp_s"] for r in members),
                dp_deg=median(r["dp_deg"] for r in members),
            )
        )
    return sorted(trains, key=lambda t: t.n, reverse=True)


@dataclass
class SpotCall:
    spot_name: str
    spot_slug: str
    call: str
    reasoning: str
    tide_note: str
    confidence: str


def evaluate_spot(spot, rules, reading) -> SpotCall:
    swell_type = classify_swell(reading["dp_deg"])

    if swell_type == "unclear":
        return SpotCall(
            spot_name=spot["name"],
            spot_slug=spot["slug"],
            call="FLAT",
            reasoning=(
                f"Current direction {reading['dp_deg']:.0f}deg doesn't fall in a recognized "
                f"NW ({NW_WINDOW[0]}-{NW_WINDOW[1]}deg) or S ({S_WINDOW[0]}-{S_WINDOW[1]}deg) "
                "swell window."
            ),
            tide_note="",
            confidence="confirmed",
        )

    matching = [r for r in rules if r["swell_type"] == swell_type]
    if not matching:
        return SpotCall(
            spot_name=spot["name"],
            spot_slug=spot["slug"],
            call="FLAT",
            reasoning=f"No rules recorded yet for {swell_type} swells at this spot.",
            tide_note="",
            confidence="tbd",
        )

    rule = matching[0]
    hs, tp, dp = reading["hs_ft"], reading["tp_s"], reading["dp_deg"]
    tide_note = TIDE_LABELS.get(rule["tide_pref"] or "any", "")

    period_ok = rule["min_period_s"] is None or tp >= rule["min_period_s"]
    height_ok = rule["min_height_ft"] is None or hs >= rule["min_height_ft"]

    direction_ok = True
    if swell_type == "NW" and rule["max_dir"] is not None:
        direction_ok = dp <= rule["max_dir"]
    if swell_type == "S" and rule["min_dir"] is not None:
        direction_ok = dp >= rule["min_dir"]

    if not period_ok:
        return SpotCall(
            spot_name=spot["name"], spot_slug=spot["slug"], call="FLAT",
            reasoning=(
                f"Period {tp:.1f}s is below the {rule['min_period_s']:.0f}s floor for this spot "
                f"on a {swell_type} swell."
            ),
            tide_note=tide_note, confidence=rule["confidence"],
        )

    if not direction_ok:
        off_angle_size_ok = height_ok and (
            rule["ideal_period_min_s"] is None or tp >= rule["ideal_period_min_s"]
        )
        if swell_type == "NW" and off_angle_size_ok:
            call, reasoning = "GOOD_BUT_INCONSISTENT", (
                f"Direction {dp:.0f}deg is past the {rule['max_dir']:.0f}deg mark, but size "
                f"({hs:.1f}ft) and period ({tp:.1f}s) are enough to compensate. Can be good "
                "but less reliable at this angle."
            )
        else:
            call, reasoning = "MARGINAL", (
                f"Direction {dp:.0f}deg is outside the ideal window for this spot on a "
                f"{swell_type} swell."
            )
        return SpotCall(
            spot_name=spot["name"], spot_slug=spot["slug"], call=call,
            reasoning=reasoning, tide_note=tide_note, confidence=rule["confidence"],
        )

    if not height_ok:
        return SpotCall(
            spot_name=spot["name"], spot_slug=spot["slug"], call="MARGINAL",
            reasoning=(
                f"Direction and period line up, but {hs:.1f}ft is under the "
                f"{rule['min_height_ft']:.1f}ft this spot usually needs."
            ),
            tide_note=tide_note, confidence=rule["confidence"],
        )

    if (
        rule["ideal_period_max_s"] is not None
        and tp > rule["ideal_period_max_s"]
    ):
        return SpotCall(
            spot_name=spot["name"], spot_slug=spot["slug"], call="GOOD_BUT_INCONSISTENT",
            reasoning=(
                f"{dp:.0f}deg / {hs:.1f}ft / {tp:.1f}s -- period is above the "
                f"{rule['ideal_period_max_s']:.0f}s mark where this spot tends to get good "
                "but inconsistent."
            ),
            tide_note=tide_note, confidence=rule["confidence"],
        )

    return SpotCall(
        spot_name=spot["name"], spot_slug=spot["slug"], call="FIRING",
        reasoning=f"{dp:.0f}deg / {hs:.1f}ft / {tp:.1f}s matches this spot's {swell_type} window.",
        tide_note=tide_note, confidence=rule["confidence"],
    )


def rank_calls(calls: list[SpotCall]) -> list[SpotCall]:
    return sorted(calls, key=lambda c: CALL_ORDER.index(c.call) if c.call in CALL_ORDER else 99)
