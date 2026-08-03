#!/usr/bin/env python3
"""Fill in what a chain branch actually has, from evidence already on disk.

Two branches of the same chain get identical records from a crawl — same
brand, same wikidata id, same website — and the directory ends up with 386
7-Elevens that are, as far as a reader can tell, one shop pinned 386 times.
The differences people actually navigate by (a cash machine, a bake-off oven,
somewhere to sit) are what a facet holds.

Almost none of that is in OSM as a tag on the shop. Of 385 7-Elevens in the
snapshot: two carried has:slurpee, one carried amenity=atm, one carried
internet_access. So this importer works two seams instead:

  near — OSM maps an ATM as its own node *beside* the store, not as a tag on
         it. Joining amenity=atm within 30m turns 1 known ATM into 82. The
         hit curve flattens past 30m (73 at 20m, 79 at 30m, 87 at 50m); the
         extra hits at 50m are bank lobbies across the road, not the store's
         own machine, so 30m is where evidence stops and guessing starts.

  tag  — the handful of stores that *do* carry wheelchair / air_conditioning /
         internet_access / opening_hours=24-7. Small numbers, free to take.

Everything else waits for a person at the door — see data/facets.json, where
a facet without an `auto` rule is one only a human can answer. Nothing here
ever writes a false: an unfilled facet is unknown, and unknown renders as
silence. Claiming "no ATM" on evidence we do not have is worse than claiming
nothing, because a reader would believe it.

Called by import_all.py after the records are merged. Zero network.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ATM_RADIUS_M = 30      # the store's own machine, not the bank across the road
TOILET_RADIUS_M = 30   # "there is one around here", never "this shop has one"

FACETS = json.loads((ROOT / "data" / "facets.json").read_text())

# OSM tags that speak for themselves. value -> the facet is present; anything
# else (including an explicit "no") leaves the facet unset rather than false,
# because "we asked OSM and it said no" is not the same claim as "there is none".
TAG_RULES = [
    ("open24", "opening_hours", lambda v: v.replace(" ", "") in
     ("24/7", "Mo-Su,PH00:00-00:00", "Mo-Su00:00-00:00", "Mo-Su00:00-24:00")),
    ("wifi", "internet_access", lambda v: v in ("wlan", "yes", "terminal")),
    ("aircon", "air_conditioning", lambda v: v == "yes"),
    ("aircon", "airconditioned", lambda v: v == "yes"),
    ("wheelchair", "wheelchair", lambda v: v in ("yes", "limited")),
]


def haversine(lat1, lng1, lat2, lng2):
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def _applies():
    """sub-key -> facet set key, from data/facets.json."""
    out = {}
    for s in FACETS["sets"]:
        for sub in s.get("appliesTo", []):
            out.setdefault(sub, s["key"])
    return out


def _known():
    """facet set key -> the keys that set actually defines.

    With one set every rule below was valid everywhere. With two, they are
    not: a restaurant's set asks about its own toilet, not about an ATM 30 m
    up the road, so writing an `atm` key onto it would store a fact the page
    is right to never render. Filtering here keeps the stored record and the
    rendered page saying the same thing."""
    return {s["key"]: {f["key"] for f in s["facets"]} for s in FACETS["sets"]}


def load_fixtures(province):
    """The ATMs and toilets, as bare points. These are never directory records —
    nobody looks up an ATM by name — so they live only as evidence."""
    p = ROOT / "cache" / "overpass" / province / "fixtures.json"
    if not p.exists():
        return []
    out = []
    for el in json.loads(p.read_text()).get("elements", []):
        t = el.get("tags", {})
        lat = el.get("lat") or (el.get("center") or {}).get("lat")
        lng = el.get("lon") or (el.get("center") or {}).get("lon")
        if lat is None or not t.get("amenity"):
            continue
        out.append((t["amenity"], lat, lng))
    return out


def load_tags(province):
    """ref ("node/123") -> raw OSM tags, across every cached group."""
    cache = ROOT / "cache" / "overpass" / province
    out = {}
    if not cache.exists():
        return out
    for f in sorted(cache.glob("*.json")):
        for el in json.loads(f.read_text()).get("elements", []):
            if el.get("tags"):
                out[f"{el['type']}/{el['id']}"] = el["tags"]
    return out


def apply(records, province):
    """Set attrs.facets on every record a facet set applies to. Mutates in place.

    A facet value is its provenance, not a boolean — "osm-near", "osm-tag" —
    so the page can say how it knows, and so an owner's claim can outrank it
    later without the two being confusable. Presence is the truth; absence is
    silence.
    """
    applies = _applies()
    known = _known()
    subjects = [r for r in records
                if any(s in applies for s in (r.get("sub") or []))
                and r.get("lat") is not None]
    if not subjects:
        return {}

    def set_of(r):
        for s in r.get("sub") or []:
            if s in applies:
                return applies[s]
        return None

    fixtures = load_fixtures(province)
    tags = load_tags(province)
    atms = [(la, ln) for k, la, ln in fixtures if k == "atm"]
    toilets = [(la, ln) for k, la, ln in fixtures if k == "toilets"]
    counts = {}

    def near(r, points, radius):
        for la, ln in points:
            # cheap bbox reject first — 0.002 deg is ~220m, comfortably outside
            # any radius we use, so this never discards a real hit
            if abs(la - r["lat"]) > 0.002 or abs(ln - r["lng"]) > 0.002:
                continue
            if haversine(r["lat"], r["lng"], la, ln) <= radius:
                return True
        return False

    for r in subjects:
        ours = known.get(set_of(r), set())
        found = dict((r.get("attrs") or {}).get("facets") or {})
        if "atm" in ours and near(r, atms, ATM_RADIUS_M):
            found["atm"] = "osm-near"
        if "toilet" in ours and near(r, toilets, TOILET_RADIUS_M):
            found["toilet"] = "osm-near"
        ref = (r.get("sources") or [{}])[0].get("ref")
        t = tags.get(ref, {})
        for key, tag, ok in TAG_RULES:
            if key not in ours:
                continue
            v = t.get(tag)
            if v and ok(v):
                found[key] = "osm-tag"
        if found:
            r.setdefault("attrs", {})["facets"] = found
            for k in found:
                counts[k] = counts.get(k, 0) + 1
    return counts


def main():
    """Standalone run reports the yield without writing anything."""
    for province in ("cm", "cr"):
        f = ROOT / "data" / "canonical" / f"{province}.json"
        if not f.exists():
            continue
        records = json.loads(f.read_text())
        counts = apply(records, province)
        n = sum(1 for r in records if (r.get("attrs") or {}).get("facets"))
        print(f"{province}: {n} records carry facets — "
              + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))


if __name__ == "__main__":
    main()
