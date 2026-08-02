#!/usr/bin/env python3
"""Pharmacy points for the walking maps — amenity=pharmacy + shop=chemist.

The main crawl never collected pharmacies (the catalog holds 29, all from the
women's-health import), so a density map drawn from canonical records would
show pharmacy deserts that are really crawl gaps. This fetches the point layer
the map needs, snapshot-first into cache/overpass/cm/pharmacy_points.json,
with the same manners as crawl_overpass.py: identified UA, mirror rotation,
skip entirely while the snapshot is fresh. It feeds the MAP only — nothing
here writes canonical records.

Run: python3 importers/fetch_pharmacy_points.py   (--refetch to force)
"""
import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "cache" / "overpass" / "cm" / "pharmacy_points.json"
STALE_DAYS = 30
BBOX = "18.60,98.80,19.05,99.15"  # same Mueang CM box as crawl_overpass
APIS = ["https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter"]
# Same UA the main crawler harvests with — overpass-api.de answered a
# differently-worded UA with 406 Not Acceptable, so don't get creative here.
UA = "mot-dang-directory/1.0 (+https://github.com/NaNoBotCo/mot-dang; gentle one-off harvest)"


def main():
    if OUT.exists() and "--refetch" not in sys.argv:
        age = (time.time() - OUT.stat().st_mtime) / 86400
        if age < STALE_DAYS:
            print(f"snapshot is {age:.0f} days old — keeping it (--refetch to force)")
            return
    q = ('[out:json][timeout:90];('
         f'nwr["amenity"="pharmacy"]({BBOX});'
         f'nwr["shop"="chemist"]({BBOX});'
         ');out center tags;')
    body = ("data=" + urllib.parse.quote(q)).encode()
    last = None
    for attempt in range(6):
        api = APIS[attempt % len(APIS)]
        req = urllib.request.Request(api, data=body, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                doc = json.loads(r.read())
            OUT.parent.mkdir(parents=True, exist_ok=True)
            OUT.write_text(json.dumps(doc, ensure_ascii=False))
            print(f"fetched {len(doc.get('elements', []))} pharmacy elements -> {OUT}")
            return
        except Exception as e:  # noqa: BLE001 - mirror rotation wants any failure
            last = e
            print(f"  attempt {attempt + 1} via {api.split('/')[2]}: {e}")
            time.sleep(45)
    raise SystemExit(f"all attempts failed: {last}")


if __name__ == "__main__":
    main()
