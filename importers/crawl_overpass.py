#!/usr/bin/env python3
"""Slow, soft-footed Overpass crawl for empty shelves, one province at a time.

Manners first: snapshot-first (nothing is fetched if a cache file exists),
one query at a time, a long pause between queries, generous server timeout,
an identified User-Agent, and rests-with-mirror-rotation on 429/504. Run with
--fetch to (re)download a province; without it, only missing cache files fetch.

  python3 importers/crawl_overpass.py             # CM: fetch only what's missing
  python3 importers/crawl_overpass.py --fetch     # CM: refresh everything (slow, on purpose)
  python3 importers/crawl_overpass.py cr          # CR: fetch only what's missing
  python3 importers/crawl_overpass.py cr --fetch  # CR: refresh everything

Cache: cache/overpass/<province>/<group>.json — import_all.py folds these in.
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APIS = ["https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter"]
UA = "mot-dang-directory/1.0 (+https://github.com/NaNoBotCo/mot-dang; gentle one-off harvest)"
PAUSE = 12                          # seconds between queries — slower and more subtle
RETRY_PAUSE = 45

BBOX = {
    "cm": "18.60,98.80,19.05,99.15",   # Mueang Chiang Mai and the near ring
    "cr": "19.80,99.70,20.00,99.95",   # Mueang Chiang Rai and the near ring
}

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
    "restaurants": ['nwr["amenity"="restaurant"]', 'nwr["amenity"="fast_food"]',
                    'nwr["amenity"="food_court"]', 'nwr["amenity"="bar"]',
                    'nwr["amenity"="pub"]', 'nwr["amenity"="biergarten"]',
                    'nwr["shop"="bakery"]', 'nwr["amenity"="ice_cream"]'],
    "whats-on":   ['nwr["amenity"="cinema"]', 'nwr["amenity"="music_venue"]',
                   'nwr["amenity"="events_venue"]', 'nwr["amenity"="theatre"]'],
    # Parks were never queried, which is why the directory had none. The 31
    # "park" hits in the data were all false positives from names — "Royal
    # Orchid Park Hotel", "Near the park Backpack hostel". Named features only:
    # an unnamed patch of grass is not a place anyone looks up.
    "parks":      ['nwr["leisure"="park"]["name"]', 'nwr["leisure"="garden"]["name"]',
                   'nwr["leisure"="nature_reserve"]["name"]',
                   'nwr["boundary"="national_park"]["name"]',
                   'nwr["leisure"="playground"]["name"]', 'nwr["natural"="water"]["name"]'],
    # 41 tattoo records were sitting in 'sights' with no rule; crawl them properly.
    "tattoo":     ['nwr["shop"="tattoo"]', 'nwr["shop"="piercing"]'],
    # Fixtures, not destinations. Nobody looks up an ATM by name, so these never
    # become directory records — import_fixtures.py joins them by distance onto
    # the shops they sit at. OSM maps an ATM as its own node beside the store,
    # almost never as a tag on it: of 385 7-Elevens in the snapshot, exactly one
    # carried amenity=atm. The neighbours are where the truth is.
    "fixtures":   ['nwr["amenity"="atm"]', 'nwr["amenity"="toilets"]',
                   'nwr["amenity"="vending_machine"]["vending"~"parcel|drinks"]'],
    # Three whole categories — home-services, community, business — were given
    # shelves at launch and never a query, so they have sat at zero ever since:
    # a reader saw "the ants are still collecting" where the truth was that no
    # ant was ever sent. These are the tags OSM actually uses for them here.
    # Named features only, on the same rule as parks: an unnamed craft=plumber
    # node is a dot on a map, not a tradesman anyone can ring.
    "crafts":     ['nwr["craft"]["name"]', 'nwr["shop"="laundry"]["name"]',
                   'nwr["shop"="dry_cleaning"]["name"]',
                   'nwr["shop"="garden_centre"]["name"]'],
    "community":  ['nwr["amenity"="community_centre"]["name"]',
                   'nwr["office"="ngo"]["name"]', 'nwr["office"="charity"]["name"]',
                   'nwr["office"="association"]["name"]',
                   'nwr["amenity"="social_facility"]["name"]', 'nwr["club"]["name"]'],
    "business":   ['nwr["shop"="wholesale"]["name"]', 'nwr["shop"="trade"]["name"]',
                   'nwr["office"="coworking"]["name"]',
                   'nwr["amenity"="coworking_space"]["name"]',
                   'nwr["office"="lawyer"]["name"]',
                   'nwr["office"="accountant"]["name"]'],
}


def fetch(group, selectors, bbox):
    q = "[out:json][timeout:90];(" + "".join(f"{s}({bbox});" for s in selectors) + ");out center tags;"
    body = ("data=" + urllib.parse.quote(q)).encode()
    last = None
    for attempt in range(6):
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
    args = sys.argv[1:]
    force = "--fetch" in args
    provinces = [a for a in args if a != "--fetch"] or ["cm"]
    for province in provinces:
        if province not in BBOX:
            print(f"unknown province {province!r} — choices: {list(BBOX)}", file=sys.stderr)
            continue
        cache = ROOT / "cache" / "overpass" / province
        cache.mkdir(parents=True, exist_ok=True)
        todo = [(g, s) for g, s in QUERIES.items()
                if force or not (cache / f"{g}.json").exists()]
        if not todo:
            print(f"{province}: all cached — nothing to fetch (use --fetch to refresh)")
            continue
        print(f"{province}: {len(todo)} groups to fetch, {PAUSE}s between each — slow on purpose")
        for i, (group, selectors) in enumerate(todo):
            data = fetch(group, selectors, BBOX[province])
            (cache / f"{group}.json").write_text(json.dumps(data, ensure_ascii=False))
            n = len(data.get("elements", []))
            print(f"  {province}/{group}: {n} elements")
            if i < len(todo) - 1:
                time.sleep(PAUSE)
        print(f"{province}: done — cache/overpass/{province}/ is the snapshot; import_all.py folds it in")


if __name__ == "__main__":
    main()
