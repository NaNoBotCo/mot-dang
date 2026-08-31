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

         WO-38 adds a second join, against our own fuel records rather than a
         fixture crawl: the shop on a petrol-station forecourt. Same
         measurement discipline — 41 branches at 30 m, 92 at 50, 110 at 80,
         125 at 120, 140 at 150. The hit rate falls from 2.55/m (30→50) to
         0.6 (50→80) and settles near background (~0.4–0.5/m) past 80: a
         forecourt is 40–70 m deep, so 50 m still splits a station from its
         own shop, and past 80 m the additions are neighbours across the
         road. 80 m, and the facet is WORDED "in/beside a petrol station" so
         the boundary case sits inside the claim rather than beyond it.

  tag  — the handful of stores that *do* carry wheelchair / air_conditioning /
         internet_access / opening_hours=24-7. Small numbers, free to take —
         including has:slurpee, which exactly two stores in the snapshot
         carry, and two witnesses are still evidence.

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
FUEL_RADIUS_M = 80     # the forecourt itself — see the curve in the docstring

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
    # Somewhere to sit. Two tags, one facet: OSM records the terrace and the
    # room separately and a reader asking "can I sit down" does not care which.
    ("seating", "outdoor_seating", lambda v: v == "yes"),
    ("seating", "indoor_seating", lambda v: v == "yes"),
    ("delivery", "delivery", lambda v: v in ("yes", "only")),
    # Cards. Any one of these saying yes answers the question; none of them
    # saying anything leaves it unanswered, which is not the same as cash-only.
    ("card", "payment:cards", lambda v: v == "yes"),
    ("card", "payment:credit_cards", lambda v: v == "yes"),
    ("card", "payment:debit_cards", lambda v: v == "yes"),
    ("card", "payment:visa", lambda v: v == "yes"),
    ("card", "payment:mastercard", lambda v: v == "yes"),
    # A small, real, entirely local cluster: four of the thirty-two cannabis
    # shops in the Chiang Mai snapshot take Lightning. Same tags the record's
    # `crypto` attr already reads — this only lifts them into the facet row so
    # they can be filtered on.
    ("crypto", "currency:XBT", lambda v: v in ("yes", "only")),
    ("crypto", "payment:onchain", lambda v: v in ("yes", "only")),
    ("crypto", "payment:lightning", lambda v: v in ("yes", "only")),
    ("crypto", "payment:lightning_contactless", lambda v: v in ("yes", "only")),
    ("openlate", "opening_hours", lambda v: _open_late(v)),
    # WO-22. Who the chair is for. male/female/unisex are the ONLY three
    # things OpenStreetMap knows about a hair shop beyond its existence, and
    # until now the import threw all three away: 15 shops in Chiang Mai say
    # male=yes, 14 say female=yes, 3 say unisex=yes, and every one of them
    # arrived on the shelf saying nothing. A barber shop that has already
    # answered "do you cut men's hair" should not be asked again at the door.
    #
    # Only `yes` counts. male=no is a real and different statement — a shop
    # declaring it does NOT cut men's hair — and this facet layer has no way
    # to render an absence, so recording it as a blank is the honest handling.
    # The women-only salon is not thereby called a men's shop; it is left
    # silent, and the door survey is what fills it in.
    ("mencut", "male", lambda v: v == "yes"),
    ("womencut", "female", lambda v: v == "yes"),
    ("unisex", "unisex", lambda v: v == "yes"),
    # WO-38. Two stores in the snapshot say so themselves. A facet with two
    # witnesses is small, real, and free to take; the door survey grows it.
    ("slurpee", "has:slurpee", lambda v: v == "yes"),
]


def _open_late(v):
    """True when the stated hours run past 22:00 — including past midnight.

    The question behind the facet is "is it still open when I want it", asked
    at an hour when being wrong means a wasted ride. So the test is on the
    CLOSING time of any range: 22:00 or later, or a wrap past midnight, where
    an end earlier than its own start means the shutters come down tomorrow
    ("18:00-02:00"). An end of exactly 00:00 is midnight tonight and counts.

    Deliberately shallow. opening_hours is a whole grammar — holidays,
    seasons, "Su off" — and this reads clock ranges out of it and nothing
    else. Being unsure renders as silence, which costs a reader nothing; the
    facet only ever appears when the hours plainly say late.
    """
    import re as _re
    v = (v or "").strip()
    if not v:
        return False
    if v.replace(" ", "") in ("24/7", "Mo-Su00:00-24:00", "Mo-Su00:00-00:00"):
        return True
    for start, end in _re.findall(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", v):
        sh, sm = (int(x) for x in start.split(":"))
        eh, em = (int(x) for x in end.split(":"))
        s, e = sh * 60 + sm, eh * 60 + em
        if e <= s:            # wraps past midnight
            return True
        if e >= 22 * 60:
            return True
    return False


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


def _beauty_stated():
    """place id -> the services its own site states (WO-22, door 2).

    Read once. An absent file is normal — this is curated data that only
    exists once somebody has run the reader — and an absent file must never
    be an error, only an empty dict.
    """
    f = ROOT / "data" / "curated" / "beauty.json"
    if not f.exists():
        return {}
    doc = json.loads(f.read_text())
    return {s["place"]: (s.get("stated") or {}) for s in doc.get("shops", [])}


BEAUTY_STATED = _beauty_stated()


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
    # WO-38: the petrol-station join needs no fixture crawl — the stations are
    # full records of our own, on the same shelf tree, already in hand.
    fuels = [(r["lat"], r["lng"]) for r in records
             if "fuel" in (r.get("sub") or []) and r.get("lat") is not None]
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
        if "atstation" in ours and near(r, fuels, FUEL_RADIUS_M):
            found["atstation"] = "osm-near"
        ref = (r.get("sources") or [{}])[0].get("ref")
        t = tags.get(ref, {})
        for key, tag, ok in TAG_RULES:
            if key not in ours:
                continue
            v = t.get(tag)
            if v and ok(v):
                found[key] = "osm-tag"
        # WO-22, door 2. What the shop states on its OWN site outranks a
        # mapper's tag — the shop is the authority on what the shop does — so
        # the register is merged last and wins any key it names. Every claim in
        # that file carries the sentence it was read from; see
        # importers/read_beauty_sites.py.
        for key in (BEAUTY_STATED.get(r["id"]) or {}):
            if key in ours:
                found[key] = "site"
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
