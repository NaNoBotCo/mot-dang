#!/usr/bin/env python3
"""Chiang Mai traffic as measured now: TomTom's flow on the busiest counted roads → data/traffic_now.json.

    python3 importers/make_traffic_now.py            # sample, write data/ and docs/data/, log the sample
    python3 importers/make_traffic_now.py --publish  # and push docs/data/traffic_now.json live

C106 option C (Nan's TomTom developer key, 2026-10-03; key in ~/.config/nanobotco/keys.json "tomtom", never in
this repo). Each run asks TomTom's Flow Segment Data for one point on each of the SAMPLES busiest Department of
Highways sections in central Chiang Mai (data/traffic.json): the speed now, the free-flow speed, TomTom's
confidence, and the stretch of road the answer covers. Every sample is also appended to
cache/traffic_now/<date>.jsonl, so after a few weeks the hour-by-hour curve is our own measurement rather
than TomTom's published 2025 averages.

BUDGET. The free key allows 2,500 flow calls a day. launchd (net.motdang.traffic-now) runs every 30 minutes
from 06:00 to 23:30: 36 runs × 20 calls = 720 a day.
"""
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "traffic_now.json"
LOG = ROOT / "cache" / "traffic_now"
KEYS = Path.home() / ".config" / "nanobotco" / "keys.json"
URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/12/json?point=%.5f,%.5f&unit=KMPH&key=%s"
BOX = (98.86, 18.66, 99.12, 18.90)                      # the roads tile's city view
SAMPLES = 20
BKK = timezone(timedelta(hours=7))


def picks():
    """The SAMPLES busiest sections inside BOX, each with the middle point of its longest line."""
    t = json.loads((ROOT / "data" / "traffic.json").read_text())
    out = []
    for r in sorted(t["roads"], key=lambda r: -r["motor"]):
        if not r.get("lines"):
            continue
        ln = max(r["lines"], key=len)
        x, y = ln[len(ln) // 2]
        if BOX[0] <= x <= BOX[2] and BOX[1] <= y <= BOX[3]:
            out.append({"route": r["route"], "name": r["name"], "motor": r["motor"], "grade": r.get("grade"), "pt": [round(y, 5), round(x, 5)]})
        if len(out) >= SAMPLES:
            break
    return out


def main():
    key = json.loads(KEYS.read_text())["tomtom"]["key"]
    if not key:
        raise SystemExit("no tomtom key in %s" % KEYS)
    now = datetime.now(BKK)
    roads = []
    for p in picks():
        req = urllib.request.Request(URL % (p["pt"][0], p["pt"][1], key), headers={"User-Agent": "motdang.net traffic now"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                f = json.load(r)["flowSegmentData"]
        except (urllib.error.URLError, KeyError, ValueError) as e:
            print("tomtom: %s %s" % (p["route"], e))
            continue
        cur, free = f.get("currentSpeed"), f.get("freeFlowSpeed")
        coords = [[round(c["longitude"], 5), round(c["latitude"], 5)] for c in f.get("coordinates", {}).get("coordinate", [])]
        roads.append(p | {"cur": cur, "free": free, "ratio": round(cur / free, 3) if cur and free else None,
                          "closed": bool(f.get("roadClosure")), "conf": f.get("confidence"), "frc": f.get("frc"), "line": coords})
        time.sleep(0.25)
    doc = {"generated": now.isoformat(timespec="seconds"),
           "source": {"th": "TomTom Traffic Flow (คีย์ของมดแดง)", "en": "TomTom Traffic Flow, Mot Dang's own key", "url": "https://developer.tomtom.com/traffic-api"},
           "roads": roads}
    OUT.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")))
    (ROOT / "docs" / "data").mkdir(parents=True, exist_ok=True)
    (ROOT / "docs" / "data" / "traffic_now.json").write_text(OUT.read_text())
    LOG.mkdir(parents=True, exist_ok=True)
    with (LOG / (now.strftime("%Y-%m-%d") + ".jsonl")).open("a") as fh:
        fh.write(json.dumps({"t": doc["generated"], "s": [[r["route"], r["name"], r["cur"], r["free"], r["conf"]] for r in roads]}, ensure_ascii=False) + "\n")
    rs = [r["ratio"] for r in roads if r["ratio"]]
    print("traffic_now: %d roads, median speed %.0f%% of free flow" % (len(roads), 100 * sorted(rs)[len(rs) // 2] if rs else 0))
    if "--publish" in sys.argv:
        os.chdir(ROOT)
        os.execvp(sys.executable, [sys.executable, "publish/deploy.py", "--files", "data/traffic_now.json", "--yes"])


if __name__ == "__main__":
    main()
