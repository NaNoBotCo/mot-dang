#!/usr/bin/env python3
"""Today's departures and arrivals at CNX and CEI, from AirLabs' schedules API → data/flightboard.json.

    python3 importers/make_flightboard.py            # fetch, write data/ and docs/data/
    python3 importers/make_flightboard.py --publish  # and push docs/data/flightboard.json live
    python3 importers/make_flightboard.py --from-cache

Nan signed up for the free AirLabs key on 2026-10-03 (C122). The key lives in ~/.config/nanobotco/keys.json
under "airlabs"; it never enters this repo, and AirLabs echoes it back inside every response, so the raw
responses cached here are stripped of their "request" block before they are written.

BUDGET. The free key allows 1,000 calls a month. One refresh is four calls (CNX and CEI, departures and
arrivals). The free plan answers 100 rows a question and ignores offset (tested 2026-10-03: page two came back
empty), and at CNX 100 rows reach about seven hours ahead, so the board is refreshed through the day and each
run is merged into the day's file. launchd (net.motdang.flightboard) runs it seven times a day: 28 calls,
about 870 a month.

WHAT IS KEPT. One row per operating flight: codeshare copies (rows naming cs_flight_iata, the operating
flight) are dropped. Times are the airport's local clock, as AirLabs gives them: scheduled, estimated,
actual; status (scheduled, active, landed, cancelled); delay minutes; gate and terminal when given.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "flightboard.json"
CACHE = ROOT / "cache" / "flightboard"
KEYS = Path.home() / ".config" / "nanobotco" / "keys.json"
BASE = "https://airlabs.co/api/v9/schedules"
QUERIES = [("CNX", "dep", 1), ("CNX", "arr", 1), ("CEI", "dep", 1), ("CEI", "arr", 1)]
KEEP = ("flight_iata", "airline_iata", "dep_iata", "arr_iata", "dep_time", "dep_estimated", "dep_actual",
        "arr_time", "arr_estimated", "arr_actual", "status", "delayed", "dep_delayed", "arr_delayed",
        "dep_gate", "dep_terminal", "arr_gate", "arr_terminal", "arr_baggage", "aircraft_icao", "duration",
        "dep_time_ts", "dep_estimated_ts", "dep_actual_ts", "arr_time_ts", "arr_estimated_ts", "arr_actual_ts")
BKK = timezone(timedelta(hours=7))


def fetch(key, airport, side, page):
    q = "?%s_iata=%s&offset=%d&api_key=%s" % (side, airport, page * 100, key)
    req = urllib.request.Request(BASE + q, headers={"User-Agent": "motdang.net flight board", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=40) as r:
        doc = json.load(r)
    if "error" in doc:
        raise SystemExit("airlabs: %s" % doc["error"])
    req_meta = doc.pop("request", {}) or {}
    return doc.get("response") or [], bool(req_meta.get("has_more"))


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    rows = []
    if "--from-cache" in sys.argv:
        for f in sorted(CACHE.glob("*.json")):
            rows += json.loads(f.read_text())
    else:
        key = json.loads(KEYS.read_text())["airlabs"]["key"]
        if not key:
            raise SystemExit("no airlabs key in %s" % KEYS)
        calls = 0
        for airport, side, pages in QUERIES:
            for page in range(pages):
                got, more = fetch(key, airport, side, page)
                calls += 1
                (CACHE / ("%s-%s-%d.json" % (airport, side, page))).write_text(json.dumps(got, ensure_ascii=False))
                rows += got
                time.sleep(1)
                if not more:
                    break
        print("airlabs: %d calls" % calls)
    today = datetime.now(BKK).strftime("%Y-%m-%d")
    fresh = {(f.get("flight_iata"), f.get("dep_iata"), f.get("dep_time")) for f in rows}
    if OUT.exists():                                   # keep today's earlier rows the new answer no longer reaches
        old = json.loads(OUT.read_text()).get("flights", [])
        rows += [f for f in old if (f.get("flight_iata"), f.get("dep_iata"), f.get("dep_time")) not in fresh
                 and (f.get("dep_time", "")[:10] == today or f.get("arr_time", "")[:10] == today)]
    seen, flights = set(), []
    for f in rows:
        if f.get("cs_flight_iata"):
            continue                                   # a marketing copy of a flight listed under its operator
        k = (f.get("flight_iata"), f.get("dep_iata"), f.get("dep_time"))
        if k in seen or not f.get("flight_iata"):
            continue
        seen.add(k)
        flights.append({x: f[x] for x in KEEP if f.get(x) not in (None, "")})
    flights.sort(key=lambda f: f.get("dep_time", ""))
    doc = {"generated": datetime.now(BKK).isoformat(timespec="seconds"),
           "source": {"th": "AirLabs ตารางบินและสถานะ", "en": "AirLabs schedules and status", "url": "https://airlabs.co/"},
           "clock": "local, Asia/Bangkok for CNX and CEI; the other end's local time for its side",
           "flights": flights}
    text = json.dumps(doc, ensure_ascii=False, separators=(",", ":"))
    OUT.write_text(text)
    (ROOT / "docs" / "data").mkdir(parents=True, exist_ok=True)
    (ROOT / "docs" / "data" / "flightboard.json").write_text(text)
    print("flightboard: %d flights (%d departures from CNX/CEI, %d arrivals)" % (
        len(flights), sum(f["dep_iata"] in ("CNX", "CEI") for f in flights), sum(f["arr_iata"] in ("CNX", "CEI") for f in flights)))
    if "--publish" in sys.argv:
        os.chdir(ROOT)
        os.execvp(sys.executable, [sys.executable, "publish/deploy.py", "--files", "data/flightboard.json", "--yes"])


if __name__ == "__main__":
    main()
