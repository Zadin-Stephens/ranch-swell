"""Fetch and parse real-time wave data from the CDIP Harvest buoy (station 071)."""

import re
from datetime import datetime, timezone

import httpx

STATION = "071p1"
BASE = f"https://thredds.cdip.ucsd.edu/thredds/dodsC/cdip/realtime/{STATION}_rt.nc"
M_TO_FT = 3.28084


class CdipError(RuntimeError):
    pass


async def _dataset_length(client: httpx.AsyncClient) -> int:
    resp = await client.get(f"{BASE}.dds")
    resp.raise_for_status()
    match = re.search(r"waveTime\[waveTime\s*=\s*(\d+)\]", resp.text)
    if not match:
        raise CdipError("could not determine waveTime array length from .dds response")
    return int(match.group(1))


def _parse_ascii_row(text: str, var: str) -> list[float]:
    match = re.search(rf"{var}\[\d+\]\s*\n([^\n]+)", text)
    if not match:
        raise CdipError(f"variable {var} not found in CDIP ascii response")
    return [float(v) for v in match.group(1).split(",")]


async def fetch_latest_readings(n: int = 5) -> list[dict]:
    """Fetch the most recent `n` readings from the Harvest buoy, oldest first."""
    async with httpx.AsyncClient(timeout=20.0) as client:
        length = await _dataset_length(client)
        start = max(0, length - n)
        end = length - 1
        query = (
            f"waveTime[{start}:1:{end}],"
            f"waveHs[{start}:1:{end}],"
            f"waveTp[{start}:1:{end}],"
            f"waveTa[{start}:1:{end}],"
            f"waveDp[{start}:1:{end}]"
        )
        resp = await client.get(f"{BASE}.ascii?{query}")
        resp.raise_for_status()
        text = resp.text

    times = _parse_ascii_row(text, "waveTime")
    hs = _parse_ascii_row(text, "waveHs")
    tp = _parse_ascii_row(text, "waveTp")
    ta = _parse_ascii_row(text, "waveTa")
    dp = _parse_ascii_row(text, "waveDp")

    readings = []
    for t, h, p, a, d in zip(times, hs, tp, ta, dp):
        if h < -900 or p < -900 or d < -900:
            continue  # CDIP fill value (-999.99) marks missing/bad data
        readings.append(
            {
                "observed_at_utc": datetime.fromtimestamp(t, tz=timezone.utc).isoformat(),
                "hs_m": h,
                "hs_ft": round(h * M_TO_FT, 2),
                "tp_s": p,
                "ta_s": a,
                "dp_deg": d,
            }
        )
    return readings
