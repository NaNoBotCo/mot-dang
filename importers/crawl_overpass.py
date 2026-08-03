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

# Some things are too few, and too far apart, to be found in a ring round the
# provincial capital. A coach terminal at Mae Sai, the Mekong piers at Chiang
# Saen and Chiang Khong, an airport out past the ring road — each is a real
# destination and there are a handful of them in a whole province, so asking
# province-wide costs a few queries and no manners. Restaurants and
# hairdressers stay in the near ring, where the density would be unkind to
# Overpass and to a reader.
#
# THE AREA, NOT A RECTANGLE. Chiang Rai's bounding box is not Chiang Rai: the
# province is wedged against Laos and Myanmar, and a rectangle drawn round it
# caught Bokeo International Airport and the Houayxay speedboat pier (Laos),
# the Tha Ton boat landing (Mae Ai, which is Chiang Mai), and the pier out to
# Wat Tilok Aram (Kwan Phayao, which is Phayao). Filing any of those under
# "Chiang Rai" would be a plain falsehood about somebody else's province or
# somebody else's country. ISO 3166-2 names the administrative area exactly and
# in no particular language, so that is what we ask for.
PROVINCE_AREA = {
    "cm": "TH-50",   # เชียงใหม่ Chiang Mai
    "cr": "TH-57",   # เชียงราย Chiang Rai
}
WIDE_GROUPS = {"stations"}      # these go province-wide in EVERY province

# Provinces crawled province-wide for every group. Chiang Rai is here on Nan's
# instruction: a directory that only knows Mueang is not a directory for
# Chiang Rai. Mae Sai, Mae Chan, Chiang Saen, Chiang Khong, Thoeng, Phan,
# Wiang Pa Pao and Mae Salong are where much of the province actually lives and
# works, and they were outside a box drawn round the clock tower.
#
# Chiang Mai stays on its near ring for now: it is far denser, the ring already
# holds 9,075 records, and widening it is a much larger crawl that deserves its
# own decision rather than being carried in on Chiang Rai's coat-tails.
WIDE_PROVINCES = {"cr"}


def is_wide(province, group):
    return province in PROVINCE_AREA and (province in WIDE_PROVINCES
                                          or group in WIDE_GROUPS)

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
    # Terminals, in their own group so it can be fetched without disturbing the
    # rest of `transport`. `transport` asked only for amenity=bus_station and
    # railway=station, which left out every airport in both provinces — the
    # directory's only "Airport" records are a petrol station and a hotel with
    # the word in their names, and a landmark list built by name-matching
    # happily pinned one of them. An aerodrome is also exactly the kind of
    # place /toilets.html is asked about at midnight.
    #
    # Nameless is skipped at import anyway, so ["name"] where a nameless hit
    # would be noise (an aerodrome polygon, a pier) and left off where the
    # feature is worth having even bare (a bus station).
    "stations":   ['nwr["aeroway"="aerodrome"]["name"]',
                   'nwr["aeroway"="terminal"]["name"]',
                   'nwr["amenity"="bus_station"]',
                   'nwr["public_transport"="station"]["name"]',
                   'nwr["railway"="station"]', 'nwr["railway"="halt"]["name"]',
                   'nwr["amenity"="ferry_terminal"]["name"]',
                   'nwr["amenity"="taxi"]["name"]'],
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


class OverpassRemark(Exception):
    """Overpass answered 200 with an error in `remark` and no elements.

    This is the failure that matters most here, because it does not look like
    one. A timed-out query returns a perfectly valid JSON document with an
    empty `elements` list, and the crawler used to write it to cache as though
    it were an answer — and since the crawl is snapshot-first, that empty file
    would never be retried. A shelf would simply be empty forever, with a
    cached file standing there as proof it had been asked.
    """


def fetch(group, selectors, scope, timeout=90):
    """`scope` is either a bbox string or ("area", <ISO 3166-2 code>)."""
    if isinstance(scope, tuple):
        pre = f'area["ISO3166-2"="{scope[1]}"]->.a;'
        clip = "(area.a)"
    else:
        pre, clip = "", f"({scope})"
    q = (f"[out:json][timeout:{timeout}];{pre}("
         + "".join(f"{s}{clip};" for s in selectors) + ");out center tags;")
    body = ("data=" + urllib.parse.quote(q)).encode()
    last = None
    for attempt in range(6):
        api = APIS[attempt % len(APIS)]
        req = urllib.request.Request(api, data=body, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=timeout + 60) as r:
                data = json.load(r)
            remark = data.get("remark") or ""
            if remark and not data.get("elements"):
                raise OverpassRemark(remark.strip())
            return data
        except Exception as e:
            last = e
            rest = RETRY_PAUSE * (attempt + 1)
            print(f"  {group}: {e} on {api.split('/')[2]} — resting {rest}s", flush=True)
            time.sleep(rest)
    raise last


def fetch_wide(group, selectors, scope, timeout=240):
    """One selector at a time, merged.

    A whole province in a single query is what timed out: eight selectors over
    Chiang Rai is more than Overpass will do in 90 seconds, and the answer came
    back empty with the error tucked in a `remark`. Split, each part is small
    and finishes; the pause between them is the same politeness the group loop
    already keeps.
    """
    merged, seen = [], set()
    for i, sel in enumerate(selectors):
        data = fetch(f"{group}[{i + 1}/{len(selectors)}]", [sel], scope, timeout)
        for el in data.get("elements", []):
            key = (el.get("type"), el.get("id"))
            if key not in seen:
                seen.add(key)
                merged.append(el)
        print(f"    {sel} -> {len(data.get('elements', []))}", flush=True)
        if i < len(selectors) - 1:
            time.sleep(PAUSE)
    where = f"area {scope[1]}" if isinstance(scope, tuple) else scope
    return {"elements": merged,
            "note": f"merged from {len(selectors)} per-selector queries over {where}"}


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
            wide = is_wide(province, group)
            if wide:
                data = fetch_wide(group, selectors, ("area", PROVINCE_AREA[province]))
            else:
                data = fetch(group, selectors, BBOX[province])
            # Written the moment a group lands, never at the end: a
            # province-wide run is hours of somebody else's server time, and a
            # crash on group 17 must not throw away the first sixteen. Plain
            # re-run resumes — snapshot-first skips whatever is already cached.
            (cache / f"{group}.json").write_text(json.dumps(data, ensure_ascii=False))
            n = len(data.get("elements", []))
            print(f"  {province}/{group}: {n} elements"
                  f"{' (province-wide)' if wide else ''}", flush=True)
            if i < len(todo) - 1:
                time.sleep(PAUSE)
        print(f"{province}: done — cache/overpass/{province}/ is the snapshot; import_all.py folds it in")


if __name__ == "__main__":
    main()
