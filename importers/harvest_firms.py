#!/usr/bin/env python3
"""harvest_firms.py — NASA FIRMS fire hotspots over the north, kept day by day (Nan, 2026-10-02).

    python3 importers/harvest_firms.py

Source: NASA LANCE FIRMS near-real-time files, no key —
firms.modaps.eosdis.nasa.gov/data/active_fire/<sensor>/csv/<file>_SouthEast_Asia_7d.csv
for VIIRS on Suomi NPP, NOAA-20 and NOAA-21, and MODIS. A file holds the last
seven days, so one run a day loses nothing; each run appends what is new to
the archive, and the archive grows from the first run onward.

Box: the Smoky Season map's own, 96.0–104.5 E, 15.5–23.5 N (Shan State to past
the Mekong), so the same picture can carry it.

Writes:
  data/firms/archive.csv                        every hotspot ever pulled, deduplicated
  data/firms.json                               the last 7 days + counts per day
  assets/sites/smoky-season/data/week.json      the same 7 days, for the fire map
"""
import csv
import io
import json
import sys
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ingest  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ARCH = ROOT / "data" / "firms" / "archive.csv"
OUT = ROOT / "data" / "firms.json"
WEEK = ROOT / "assets" / "sites" / "smoky-season" / "data" / "week.json"
BASE = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/"
FEEDS = [
    ("VIIRS S-NPP", "suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_SouthEast_Asia_7d.csv"),
    ("VIIRS NOAA-20", "noaa-20-viirs-c2/csv/J1_VIIRS_C2_SouthEast_Asia_7d.csv"),
    ("VIIRS NOAA-21", "noaa-21-viirs-c2/csv/J2_VIIRS_C2_SouthEast_Asia_7d.csv"),
    ("MODIS", "modis-c6.1/csv/MODIS_C6_1_SouthEast_Asia_7d.csv"),
]
BOX = (96.0, 15.5, 104.5, 23.5)
UA = "mot-dang-directory/1.0 (+https://motdang.net; daily fire hotspots)"
COLS = ["sensor", "lat", "lng", "date", "time", "confidence", "frp", "daynight"]
# Province boxes for the daily counts on motdang; the map draws the points.
PROV = {"cm": (98.0, 17.2, 99.6, 20.2), "cr": (99.2, 19.2, 100.6, 20.5)}


def fetch(path):
    req = urllib.request.Request(BASE + path, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read().decode("utf-8", "replace")


def main():
    rows, ok, failed = [], [], []
    for sensor, path in FEEDS:
        try:
            text = fetch(path)
        except Exception as e:
            failed.append((sensor, str(e)))
            print("   !", sensor, e)
            continue
        ok.append(sensor)
        for r in csv.DictReader(io.StringIO(text)):
            try:
                lat, lng = float(r["latitude"]), float(r["longitude"])
            except (KeyError, ValueError):
                continue
            if not (BOX[0] <= lng <= BOX[2] and BOX[1] <= lat <= BOX[3]):
                continue
            rows.append({"sensor": sensor, "lat": "%.4f" % lat, "lng": "%.4f" % lng,
                         "date": r["acq_date"], "time": r["acq_time"],
                         "confidence": r.get("confidence", ""), "frp": r.get("frp", ""),
                         "daynight": r.get("daynight", "")})
    if not ok:
        return ingest.refuse(OUT, "no FIRMS feed answered", ok, failed)

    ARCH.parent.mkdir(parents=True, exist_ok=True)
    seen = set()
    if ARCH.exists():
        with ARCH.open() as f:
            for r in csv.DictReader(f):
                seen.add(tuple(r[c] for c in COLS[:5]))
    new = [r for r in rows if tuple(r[c] for c in COLS[:5]) not in seen]
    first = not ARCH.exists()
    with ARCH.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        if first:
            w.writeheader()
        w.writerows(new)
    print("   archive: +%d new, %d this pull" % (len(new), len(rows)))

    today = datetime.now(timezone.utc).date()
    days = [(today - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    di = {d: i for i, d in enumerate(days)}
    pts, per_day, per_prov = [], Counter(), Counter()
    # VIIRS only on the map: 375 m pixels against MODIS's 1 km, and the three
    # VIIRS satellites see the same fire, so one point per ~400 m cell per day.
    cells = set()
    for r in rows:
        if r["date"] not in di or not r["sensor"].startswith("VIIRS"):
            continue
        lat, lng = float(r["lat"]), float(r["lng"])
        key = (r["date"], round(lat / 0.004), round(lng / 0.004))
        if key in cells:
            continue
        cells.add(key)
        pts.append([round(lng, 3), round(lat, 3), di[r["date"]]])
        per_day[r["date"]] += 1
        for p, b in PROV.items():
            if b[0] <= lng <= b[2] and b[1] <= lat <= b[3]:
                per_prov[(p, r["date"])] += 1
    doc = {"source": "NASA LANCE FIRMS, VIIRS 375 m (S-NPP, NOAA-20, NOAA-21)",
           "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
           "box": list(BOX), "days": days, "per_day": [per_day[d] for d in days],
           "prov": {p: [per_prov[(p, d)] for d in days] for p in PROV}, "pts": pts}
    WEEK.parent.mkdir(parents=True, exist_ok=True)
    WEEK.write_text(json.dumps(doc, separators=(",", ":")))
    ingest.write(OUT, doc, count=len(pts), min_rows=0, sources_ok=ok,
                 sources_failed=failed, label="firms.json")


if __name__ == "__main__":
    main()
