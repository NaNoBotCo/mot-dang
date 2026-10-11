#!/usr/bin/env python3
"""Fetch the north's administrative areas from OSM: อำเภอ and ตำบล, with extent.

Why this exists. geocode_local builds ตำบล centroids from OUR OWN surveyed
pins, and only from records carrying attrs.subdistrict — which is 60 tambons
across two provinces that hold roughly 330. The register records that most
need placing (temples, schools, health stations) all state a ตำบล and an
อำเภอ, and the gazetteer could not place most of them because it had never
heard of the subdistrict.

OSM holds every one of them as an administrative relation, with a boundary.
Two queries, one per province, and the tambon tier stops being a rumour built
from wherever our crawl happened to land.

Each area is stored with its centre AND its bounding box, so a pin derived
from it can declare a radius that is measured rather than assumed — the same
rule geocode_local already follows: never a bare coordinate, always a point
with the distance it might be wrong by.

  importers/crawl_admin.py            fetch what is missing
  importers/crawl_admin.py --fetch    re-fetch both provinces

Cache: cache/osm-admin/<prov>.json. Built table: data/curated/admin_areas.json.
"""
import argparse, json, math, os, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache", "osm-admin")
OUT = os.path.join(ROOT, "data", "curated", "admin_areas.json")
AREA = {"cm": "TH-50", "cr": "TH-57"}
APIS = ["https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter"]
UA = "mot-dang-directory/1.0 (+https://motdang.net; gentle one-off harvest)"
# 6 = อำเภอ (district). Level 7 in Thailand is meant for ตำบล, but OSM has
# barely drawn them: Chiang Mai returns 25 relations at level 6 — its full set
# of districts — and 15 at level 7, which are เทศบาล municipalities, not
# subdistricts. So the อำเภอ is the real prize here. It is a coarse thing to
# know, but knowing which of 25 districts a temple stands in is exactly what
# tells วัดพระบาท in Mae Rim from วัดพระบาท in Chom Thong.
LEVELS = {"6": "amphoe", "7": "tambon"}


def fetch(prov, timeout=300):
    q = (f'[out:json][timeout:{timeout}];area["ISO3166-2"="{AREA[prov]}"]->.a;'
         f'relation["boundary"="administrative"]["admin_level"~"^(6|7)$"](area.a);'
         f'out tags center bb;')
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
    print(f"fetching {prov} administrative areas…", flush=True)
    d = fetch(prov)
    json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"  {len(d.get('elements') or [])} relations")
    time.sleep(20)
    return d


def _radius_m(bounds, centre):
    """Half the bounding box's diagonal: the honest distance from the centre
    to the far corner of the area, which is what a centroid pin risks."""
    if not bounds:
        return 3000
    la = (bounds["maxlat"] - bounds["minlat"]) * 111000
    ln = (bounds["maxlon"] - bounds["minlon"]) * 111000 * math.cos(math.radians(centre[0]))
    return int(max(300, math.hypot(la, ln) / 2))


def strip(name, *words):
    n = (name or "").strip()
    for w in words:
        if n.startswith(w):
            n = n[len(w):].strip()
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    a = ap.parse_args()
    table = {}
    for prov in ("cm", "cr"):
        d = snapshot(prov, a.fetch)
        got = {"tambon": {}, "amphoe": {}}
        for e in (d.get("elements") or []):
            t = e.get("tags") or {}
            kind = LEVELS.get(str(t.get("admin_level")))
            # `out center` and `out bb` do not travel together on relations:
            # asking for both returns the box and drops the centre. The box is
            # the more useful half, and its midpoint is the centre.
            b = e.get("bounds") or {}
            c = e.get("center") or {}
            if kind and c.get("lat"):
                centre = (round(c["lat"], 6), round(c["lon"], 6))
            elif kind and b.get("minlat") is not None:
                centre = (round((b["minlat"] + b["maxlat"]) / 2, 6),
                          round((b["minlon"] + b["maxlon"]) / 2, 6))
            else:
                continue
            r = _radius_m(b, centre)
            for nm in (t.get("name:th"), t.get("name")):
                # OSM writes these as "ตำบลสุเทพ" / "อำเภอเมืองเชียงใหม่";
                # a register writes "สุเทพ" / "เมืองเชียงใหม่". One shape.
                k = strip(nm, "ตำบล", "อำเภอ", "Tambon ", "Amphoe ")
                if len(k) >= 2:
                    got[kind].setdefault(k, [centre[0], centre[1], r])
        print(f"{prov}: {len(got['tambon'])} ตำบล, {len(got['amphoe'])} อำเภอ")
        table[prov] = got
    doc = {"_note": ("Administrative centres and radii from OpenStreetMap boundary "
                     "relations (admin_level 7 = ตำบล, 6 = อำเภอ), fetched by "
                     "importers/crawl_admin.py. Each entry is [lat, lng, radius_m], "
                     "the radius being half the boundary's bounding-box diagonal — "
                     "the honest distance a centroid pin may be out by. "
                     "© OpenStreetMap contributors, ODbL."),
           "areas": table}
    json.dump(doc, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
    print("wrote", os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
