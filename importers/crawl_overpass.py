#!/usr/bin/env python3
"""Slow, soft-footed Overpass crawl for Chiang Mai's empty shelves.

Manners first: snapshot-first (nothing is fetched if a cache file exists),
one query at a time, a long pause between queries, generous server timeout,
an identified User-Agent, and one gentle retry on 429/504. Run with --fetch
to (re)download; without it, only missing cache files are fetched.

  python3 importers/crawl_overpass.py          # fetch only what's missing
  python3 importers/crawl_overpass.py --fetch  # refresh everything (slow, on purpose)

Cache: cache/overpass/<group>.json — import_all.py folds these in.
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache" / "overpass"
APIS = ["https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter"]
UA = "mot-dang-directory/1.0 (+https://github.com/NaNoBotCo/mot-dang; gentle one-off harvest)"
BBOX = "18.60,98.80,19.05,99.15"   # Mueang Chiang Mai and the near ring
PAUSE = 12                          # seconds between queries — slower and more subtle
RETRY_PAUSE = 45

QUERIES = {
    "hotels":     ['nwr["tourism"="hotel"]', 'nwr["tourism"="guest_house"]',
                   'nwr["tourism"="hostel"]'],
    "markets":    ['nwr["amenity"="marketplace"]', 'nwr["shop"="mall"]',
                   'nwr["shop"="department_store"]'],
    "schools":    ['nwr["amenity"="school"]["name"~"International|นานาชาติ"]',
                   'nwr["amenity"="university"]', 'nwr["amenity"="language_school"]'],
    "realestate": ['nwr["office"="estate_agent"]', 'nwr["building"="apartments"]["name"]'],
    "transport":  ['nwr["amenity"="fuel"]', 'nwr["amenity"="car_rental"]',
                   'nwr["shop"="motorcycle_rental"]', 'nwr["amenity"="bus_station"]',
                   'nwr["railway"="station"]'],
    "repair":     ['nwr["shop"="car_repair"]', 'nwr["shop"="motorcycle_repair"]',
                   'nwr["shop"="computer"]', 'nwr["shop"="mobile_phone"]'],
    "beauty":     ['nwr["shop"="hairdresser"]', 'nwr["shop"="beauty"]'],
    "pets":       ['nwr["amenity"="veterinary"]', 'nwr["shop"="pet"]',
                   'nwr["shop"="pet_grooming"]'],
    "fitness":    ['nwr["leisure"="fitness_centre"]'],
    "essentials": ['nwr["amenity"="bank"]', 'nwr["amenity"="post_office"]',
                   'nwr["shop"="convenience"]', 'nwr["amenity"="townhall"]'],
    "culture":    ['nwr["tourism"="museum"]', 'nwr["tourism"="gallery"]',
                   'nwr["tourism"="viewpoint"]', 'nwr["historic"]["name"]'],
    "shopping":   ['nwr["shop"="doityourself"]', 'nwr["shop"="hardware"]',
                   'nwr["shop"="gift"]', 'nwr["shop"="second_hand"]',
                   'nwr["shop"="herbalist"]', 'nwr["healthcare"="alternative"]'],
    "cafes":      ['nwr["amenity"="cafe"]'],
    "whats-on":   ['nwr["amenity"="cinema"]', 'nwr["amenity"="music_venue"]',
                   'nwr["amenity"="events_venue"]', 'nwr["amenity"="theatre"]'],
}


def fetch(group, selectors):
    q = "[out:json][timeout:90];(" + "".join(f"{s}({BBOX});" for s in selectors) + ");out center tags;"
    body = ("data=" + urllib.parse.quote(q)).encode()
    last = None
    for attempt in range(4):
        api = APIS[attempt % len(APIS)]
        req = urllib.request.Request(api, data=body, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=150) as r:
                return json.load(r)
        except Exception as e:
            last = e
            rest = RETRY_PAUSE * (attempt + 1)
            print(f"  {group}: {e} on {api.split('/')[2]} — resting {rest}s", flush=True)
            time.sleep(rest)
    raise last


def main():
    force = "--fetch" in sys.argv
    CACHE.mkdir(parents=True, exist_ok=True)
    todo = [(g, s) for g, s in QUERIES.items()
            if force or not (CACHE / f"{g}.json").exists()]
    if not todo:
        print("all cached — nothing to fetch (use --fetch to refresh)")
        return
    print(f"{len(todo)} groups to fetch, {PAUSE}s between each — slow on purpose")
    for i, (group, selectors) in enumerate(todo):
        data = fetch(group, selectors)
        (CACHE / f"{group}.json").write_text(json.dumps(data, ensure_ascii=False))
        n = len(data.get("elements", []))
        print(f"  {group}: {n} elements")
        if i < len(todo) - 1:
            time.sleep(PAUSE)
    print("done — cache/overpass/ is the snapshot; import_all.py folds it in")


if __name__ == "__main__":
    main()
