#!/usr/bin/env python3
"""Give the temple register its pins, from OpenStreetMap's surveyed ones.

945 of the 2,116 places with no pin are wats — 45% of the whole gap, and by
far the biggest single block. They arrived from the ONAB register (ทะเบียนวัด,
สำนักงานพระพุทธศาสนาแห่งชาติ), which knows a temple's name, ตำบล, อำเภอ, sect
and founding year, and holds no coordinate at all.

Address geocoding cannot rescue them: their addresses are rural
("บ้านแม่พุง หมู่ 5 ต.ป่าแดด อ.ป่าแดด"), and the local gazetteer's centroids
are built from OUR surveyed pins, which are thin in exactly the districts the
register reaches. The inverse-coverage law, one directory in.

OSM, however, has mapped Thai temples thoroughly and Mot Dang never asked for
them: crawl_overpass.py has 40-odd query groups and not one of them is
place_of_worship. The 249 surveyed wat pins we hold came in sideways, as lens
points and as neighbours inside other groups.

So this asks Overpass once per province for temples, and matches them to
register records BY NAME, with the same rule the rest of this repo uses:

  UNIQUE NAMES ONLY. วัดป่าแดด is the name of more than one temple in Chiang
  Mai. A name that answers to two OSM temples in a province cannot site
  anything, so it is refused unless a ตำบล or อำเภอ tag on the OSM element
  agrees with the register's. A wrong pin on a named temple is worse than no
  pin: it sends someone to the wrong village, confidently.

The pins land in data/curated/pins.json as tier "osm", uncertainty 0 — these
are surveyed points, not inferences, and they should not be dressed as
approximations. Nothing is written into data/canonical/*.json, which
import_all.py regenerates.

Cache is its OWN directory, cache/osm-worship/, and NOT cache/overpass/ —
import_all.py folds everything under the latter into the corpus, and adding
several thousand new temple records is a decision about the catalogue, not a
side effect of fixing pins. The count is printed so that decision can be made
with a number.

  importers/pin_wats_osm.py              fetch what is missing, then match
  importers/pin_wats_osm.py --fetch      re-fetch both provinces
  importers/pin_wats_osm.py --write      merge the matches into pins.json
"""
import argparse, datetime, json, os, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache", "osm-worship")
OUT = os.path.join(ROOT, "data", "curated", "pins.json")
AREA = {"cm": "TH-50", "cr": "TH-57"}
APIS = ["https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter"]
UA = "mot-dang-directory/1.0 (+https://motdang.net; gentle one-off harvest)"
SELECTORS = ['nwr["amenity"="place_of_worship"]["name"]',
             'nwr["building"="temple"]["name"]',
             'nwr["historic"="wayside_shrine"]["name"]']


def fetch(prov, timeout=300):
    q = (f'[out:json][timeout:{timeout}];area["ISO3166-2"="{AREA[prov]}"]->.a;('
         + "".join(f"{s}(area.a);" for s in SELECTORS) + ");out center tags;")
    body = ("data=" + urllib.parse.quote(q)).encode()
    last = None
    for attempt in range(6):
        api = APIS[attempt % len(APIS)]
        try:
            req = urllib.request.Request(api, data=body, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout + 60) as r:
                return json.load(r)
        except Exception as e:
            last = e
            rest = 45 * (attempt + 1)
            print(f"  {prov}: {e} on {api.split('/')[2]} — resting {rest}s", flush=True)
            time.sleep(rest)
    raise last


def snapshot(prov, refetch):
    os.makedirs(CACHE, exist_ok=True)
    f = os.path.join(CACHE, f"{prov}.json")
    if os.path.exists(f) and not refetch:
        return json.load(open(f, encoding="utf-8"))
    print(f"fetching {prov} temples from Overpass (once, slowly)…", flush=True)
    d = fetch(prov)
    json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"  {len(d.get('elements') or [])} elements -> {os.path.relpath(f, ROOT)}")
    time.sleep(20)   # manners between the two provinces
    return d


# วัด is the word "temple", not part of the name; and Thai is written unspaced,
# so "วัด พระสิงห์" and "วัดพระสิงห์" are one name written two ways.
def key(name):
    n = re.sub(r"\s+", "", (name or "").strip()).lower()
    for w in ("วัด", "สำนักสงฆ์", "ที่พักสงฆ์"):
        if n.startswith(w):
            n = n[len(w):]
    return n


def cached_elements(prov):
    """Every named, pinned element the gentle crawl already fetched.

    cache/overpass/<prov>/*.json holds 13,588 of them across forty query
    groups — schools, clinics, markets, parks, government offices. The
    registers that filled our shelves (OBEC's schools, ONAB's temples,
    the health-station lists) were never matched against them, so a school
    OSM has surveyed sits beside our copy of the same school with no pin.
    """
    import glob
    for f in glob.glob(os.path.join(ROOT, "cache", "overpass", prov, "*.json")):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        for e in (d.get("elements") or []):
            yield e


def osm_index(prov, refetch):
    by_name = {}
    els = list(snapshot(prov, refetch).get("elements") or []) + list(cached_elements(prov))
    for e in els:
        t = e.get("tags") or {}
        lat = e.get("lat") or (e.get("center") or {}).get("lat")
        lng = e.get("lon") or (e.get("center") or {}).get("lon")
        if not (lat and lng):
            continue
        for nm in (t.get("name"), t.get("name:th"), t.get("alt_name")):
            k = key(nm)
            if len(k) >= 2:
                by_name.setdefault(k, []).append({
                    "lat": round(lat, 6), "lng": round(lng, 6),
                    "ref": f"{e['type']}/{e['id']}", "name": t.get("name"),
                    "tambon": (t.get("addr:subdistrict") or "").strip(),
                    "amphoe": (t.get("addr:district") or "").strip(),
                })
    return by_name


_GAZ = {"g": None}


def _tambon_point(prov, tambon, amphoe):
    """Where this ตำบล is, and how far its far corner sits from the centre.

    OSM's boundary relations first — every ตำบล in both provinces, with a
    measured extent. geocode_local's own centroids second, for the handful
    OSM has not drawn. The อำเภอ last, and only as a wide net: it is a
    district, so it settles nothing on its own, but it does tell two temples
    of the same name in different halves of the province apart.
    """
    if _GAZ["g"] is None:
        f = os.path.join(ROOT, "data", "curated", "admin_areas.json")
        _GAZ["g"] = (json.load(open(f, encoding="utf-8"))["areas"]
                     if os.path.exists(f) else {})
    areas = (_GAZ["g"] or {}).get(prov) or {}
    if tambon:
        got = (areas.get("tambon") or {}).get(tambon)
        if got:
            return got[0], got[1], got[2]
    if amphoe:
        got = (areas.get("amphoe") or {}).get(amphoe)
        if got:
            return got[0], got[1], got[2]
    return None


def _haversine(a, b):
    from math import radians, sin, cos, asin, sqrt
    la1, lo1, la2, lo2 = map(radians, (a[0], a[1], b[0], b[1]))
    h = sin((la2 - la1) / 2) ** 2 + cos(la1) * cos(la2) * sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371000 * asin(min(1, sqrt(h)))


def _is_gap(r, prior):
    """A record with no pin of its OWN.

    Three ways to be one, and the second is the one that was missing: a record
    still marked needs-pin; a record whose only pin came from the curated
    overlay (attrs.pinSource), which is inferred and must be re-derived under
    today's cap; or one simply listed in the overlay file we are about to
    rewrite. The first two are facts about the record and hold no matter where
    the output file is, which is what makes a re-run reproduce rather than
    shrink.
    """
    if (r.get("geoPrecision") or "exact") == "needs-pin" and not (r.get("lat") and r.get("lng")):
        return True
    if (r.get("attrs") or {}).get("pinSource") == "curated-pins":
        return True
    return r["id"] in prior


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--show", type=int, default=6)
    ap.add_argument("--only", default="", help="a cat or sub slug to limit to")
    a = ap.parse_args()
    only = a.only

    today = datetime.date.today().isoformat()
    prior = set()
    if os.path.exists(OUT):
        try:
            prior = set((json.load(open(OUT, encoding="utf-8")) or {}).get("pins") or {})
        except Exception:
            prior = set()
    pins, matched, ambiguous, unmatched, samples = {}, 0, 0, 0, []
    by_area = 0
    held = 0
    for prov in ("cm", "cr"):
        idx = osm_index(prov, a.fetch)
        recs = json.load(open(os.path.join(ROOT, "data", "canonical", f"{prov}.json"),
                              encoding="utf-8"))
        held += sum(1 for v in idx.values() for _ in v)
        # Same idempotence rule as geocode_gaps: a record this script already
        # pinned is no longer marked needs-pin, and must still count as a gap
        # or a re-run quietly shrinks its own answer.
        gap = [r for r in recs if _is_gap(r, prior)]
        if only:
            gap = [r for r in gap
                   if only in (r.get("cat") or []) or only in (r.get("sub") or [])]
        for r in gap:
            k = key(r.get("nameTh") or r.get("name"))
            # A two-character name is a coincidence waiting to happen once
            # shops are in scope as well as temples.
            if len(k) < 4:
                unmatched += 1
                continue
            cands = idx.get(k) or []
            if not cands:
                unmatched += 1
                continue
            if len(cands) > 1:
                # A repeated name — วัดพระบาท answers to nine temples in
                # Chiang Mai — is settled by AREA, never by picking the first.
                # Two chances, in order of strength:
                #
                #  1. the register's ตำบล/อำเภอ against an addr: tag on the
                #     element, when OSM happens to carry one;
                #  2. the ตำบล CENTROID from geocode_local. The register knows
                #     which subdistrict the temple is in and the gazetteer
                #     knows roughly where that subdistrict is, so the coarse
                #     signal picks which surveyed point is the right one. The
                #     area narrows; OSM supplies the precision. Accepted only
                #     when exactly one candidate falls inside the ตำบล's own
                #     measured spread — if two do, the centroid cannot tell
                #     them apart and the record stays unpinned.
                at = (r.get("attrs") or {})
                want_t = (at.get("tambon") or at.get("subdistrict") or "").strip()
                want_a = (at.get("amphoe") or at.get("district") or "").strip()
                narrowed = [c for c in cands
                            if (want_t and c["tambon"] == want_t)
                            or (want_a and c["amphoe"] == want_a)]
                if len(narrowed) != 1:
                    centre = _tambon_point(prov, want_t, want_a)
                    if not centre:
                        ambiguous += 1
                        continue
                    la, ln, spread = centre
                    # An อำเภอ is 25-30 km across, so "inside the radius" lets
                    # several candidates through and settles nothing. The
                    # discriminating question is not who is inside but who is
                    # CLEARLY nearest: the winner must sit within the area and
                    # the runner-up must be at least twice as far. วัดพระบาท in
                    # Mae Rim and วัดพระบาท in Chom Thong are 70 km apart, and
                    # that is the case this is for; two of the same name in one
                    # district stays refused, because there the register cannot
                    # tell them apart either.
                    ranked = sorted(cands, key=lambda c: _haversine((la, ln), (c["lat"], c["lng"])))
                    d0 = _haversine((la, ln), (ranked[0]["lat"], ranked[0]["lng"]))
                    d1 = _haversine((la, ln), (ranked[1]["lat"], ranked[1]["lng"]))
                    if d0 > spread or d1 < d0 * 2:
                        ambiguous += 1
                        continue
                    narrowed = [ranked[0]]
                    by_area += 1
                cands = narrowed
            c = cands[0]
            matched += 1
            pins[r["id"]] = {
                "lat": c["lat"], "lng": c["lng"],
                # NOT ZERO. Zero would say the identity match is as certain
                # as standing at the gate, and it is a NAME match — refused
                # when the name answers to two temples, agreed by ตำบล/อำเภอ
                # where it could be, but still a match. 50 m is the OSM
                # element's own footprint: if this is the right temple, this
                # is where it is. import_all files every pins.json pin as
                # `approx` for the same reason.
                "tier": "osm", "uncertainty_m": 50,
                "via": "osm-temple-name-match",
                "from": c["ref"],
                "source": "OpenStreetMap contributors (ODbL)",
                "fetched": today,
            }
            if len(samples) < a.show:
                samples.append((r.get("name"), c["name"], c["ref"]))

    print(f"\nOSM name entries held: {held} across both provinces")
    print(f"records with no pin considered: {matched + ambiguous + unmatched}")
    print(f"  matched      {matched:5d}  (name unique in the province, or ตำบล/อำเภอ agreed)")
    print(f"  ambiguous    {ambiguous:5d}  (name answers to more than one element — refused)")
    print(f"  not in OSM   {unmatched:5d}")
    print(f"  (of the matches, {by_area} were settled by the ตำบล centroid)")
    for a_, b, ref in samples:
        print(f"   {str(a_)[:34]:34} -> {str(b)[:30]:30} {ref}")

    if not a.write:
        print("\ndry run. --write to merge into", os.path.relpath(OUT, ROOT))
        return
    doc = {"pins": {}}
    if os.path.exists(OUT):
        doc = json.load(open(OUT, encoding="utf-8"))
    # A surveyed OSM pin outranks anything inferred from an address, so these
    # overwrite a geocode_local row for the same record; nothing else is touched.
    doc.setdefault("pins", {}).update(pins)
    doc["generated"] = today
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    print(f"\nwrote {os.path.relpath(OUT, ROOT)} ({len(doc['pins'])} pins in total)")


if __name__ == "__main__":
    main()
