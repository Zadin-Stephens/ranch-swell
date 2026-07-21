import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import cdip, db, rules, seed_data

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("hollister-swell")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


async def poll_buoy():
    try:
        readings = await cdip.fetch_latest_readings(n=5)
    except Exception:
        log.exception("CDIP poll failed")
        return
    with db.get_conn() as conn:
        for r in readings:
            db.insert_buoy_reading(
                conn,
                r["observed_at_utc"], r["hs_m"], r["hs_ft"],
                r["tp_s"], r["ta_s"], r["dp_deg"],
                datetime.now(timezone.utc).isoformat(),
            )
    log.info("polled CDIP, latest reading %s", readings[-1] if readings else None)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    with db.get_conn() as conn:
        seed_data.seed(conn)
    await poll_buoy()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(poll_buoy, "interval", minutes=30, id="cdip_poll")
    scheduler.start()
    app.state.scheduler = scheduler
    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


def _minutes_ago(iso_ts):
    if not iso_ts:
        return None
    ts = datetime.fromisoformat(iso_ts)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return round((datetime.now(timezone.utc) - ts).total_seconds() / 60)


def _build_dashboard_context(conn):
    latest = db.latest_buoy_reading(conn)
    calls = []
    if latest:
        reading = dict(latest)
        swell_type = rules.classify_swell(reading["dp_deg"])
        for spot in db.all_spots(conn):
            spot_rules = db.rules_for_spot(conn, spot["id"])
            calls.append(rules.evaluate_spot(spot, spot_rules, reading))
        calls = rules.rank_calls(calls)
    else:
        swell_type = None
    return latest, swell_type, calls


@app.get("/")
def dashboard(request: Request):
    with db.get_conn() as conn:
        latest, swell_type, calls = _build_dashboard_context(conn)
    age = _minutes_ago(latest["observed_at_utc"]) if latest else None
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "latest": latest,
            "swell_type": swell_type,
            "calls": calls,
            "age_minutes": age,
        },
    )


@app.post("/refresh")
async def refresh(request: Request):
    await poll_buoy()
    return RedirectResponse(url="/", status_code=303)


@app.get("/spots/{slug}")
def spot_detail(request: Request, slug: str):
    with db.get_conn() as conn:
        spot = db.spot_by_slug(conn, slug)
        if not spot:
            return RedirectResponse(url="/")
        spot_rules = db.rules_for_spot(conn, spot["id"])
        observations = db.observations_for_spot(conn, spot["id"])
        latest = db.latest_buoy_reading(conn)
        call = None
        if latest:
            call = rules.evaluate_spot(spot, spot_rules, dict(latest))
    age = _minutes_ago(latest["observed_at_utc"]) if latest else None
    return templates.TemplateResponse(
        request,
        "spot_detail.html",
        {
            "spot": spot,
            "rules": spot_rules,
            "observations": observations,
            "latest": latest,
            "call": call,
            "age_minutes": age,
            "now": datetime.now().strftime("%Y-%m-%dT%H:%M"),
        },
    )


@app.post("/spots/{slug}/observe")
def log_observation(
    slug: str,
    observed_at_local: str = Form(...),
    observed_height_ft: float = Form(...),
    note: str = Form(""),
):
    with db.get_conn() as conn:
        spot = db.spot_by_slug(conn, slug)
        if not spot:
            return RedirectResponse(url="/", status_code=303)
        observed_utc = datetime.fromisoformat(observed_at_local).astimezone(timezone.utc).isoformat()
        nearest = db.nearest_buoy_reading_to(conn, observed_utc)
        db.insert_observation(
            conn,
            spot["id"],
            observed_at_local,
            observed_height_ft,
            note,
            nearest["id"] if nearest else None,
            datetime.now(timezone.utc).isoformat(),
        )
    return RedirectResponse(url=f"/spots/{slug}", status_code=303)
