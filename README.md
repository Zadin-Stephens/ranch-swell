# Hollister Swell

Personal wave predictor for Hollister Ranch surf spots, built on the CDIP
Harvest buoy (station 071, off Point Conception). Not affiliated with CDIP,
Surfline, or Hollister Ranch.

## Run locally

```
.venv/bin/uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000

## Run for real (bound to the tailnet)

```
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8420
```

Access from any device on the tailnet at `http://100.71.90.12:8420`.

See `com.zadin.hollister-swell.plist` for the launchd service definition that
keeps this running persistently.

## How predictions work

`app/seed_data.py` holds the per-spot rules transcribed from notes. Rules
marked `confidence: tbd` are best guesses, not confirmed thresholds — expect
them to be wrong until corrected by logged observations. `app/rules.py`
classifies the current buoy reading as an NW or S swell and evaluates each
spot's rule for that swell type against the live Hs/Tp/Dp.

Log what a spot actually looked like via its detail page — those observations
don't feed back into the rules automatically yet (see the plan doc for why),
but they're stored alongside the buoy reading at the time so the correlation
is there once there's enough data to act on.
