#!/usr/bin/env python3
"""harvest_inat.py — iNaturalist sightings near listed places, baked (Nan, 2026-10-02).

    python3 importers/harvest_inat.py            # fetch, pick, download photos
    python3 importers/harvest_inat.py --no-fetch # re-pick + download from the cached pull

Source: api.inaturalist.org/v1, no key. Research-grade observations in the
Chiang Mai (place 13320) and Chiang Rai (13321) places, open location, photo
licence CC0 / CC BY / CC BY-SA — the licences that allow use on a page that
carries sponsored work. iNaturalist's default photo licence is CC BY-NC, so
most of the north's sightings are not here; that is the licence, not the API.

Kept: a sighting whose positional accuracy is 300 m or better (or unstated),
because a strip that says "350 m from here" on a pin that could be 4 km out
is wrong. Picked: for each place record with coordinates, up to SHOW distinct
species within RADIUS_KM, nearest first, one per species. Only picked
sightings have their photo downloaded (500 px "medium", from the
inaturalist-open-data bucket on AWS Open Data) into assets/inat/.

Writes:
  cache/inat/raw.json      the full pull (re-pick without refetching)
  data/inat.json           {"obs": {id: {...}}, "near": {record_id: [[id, metres], ...]}}
  assets/inat/<id>.jpg     the photos the pages show

Read by inat_layer.py.
"""
import argparse
import json
import math
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ingest  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "cache" / "inat" / "raw.json"
OUT = ROOT / "data" / "inat.json"
PICS = ROOT / "assets" / "inat"
API = "https://api.inaturalist.org/v1"
UA = "mot-dang-directory/1.0 (+https://motdang.net; baked sightings near listed places)"
PLACES = {"cm": 13320, "cr": 13321}
LICENCES = "cc0,cc-by,cc-by-sa"
MAX_ACC_M = 300
RADIUS_KM = 1.0
SHOW = 4
MIN_SPECIES = 2


def get(path, **q):
    url = API + path + "?" + urllib.parse.urlencode(q)
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:
            print("   retry", attempt + 1, e)
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("iNaturalist did not answer: " + url)


def fetch():
    rows = {}
    for prov, place in PLACES.items():
        above = 0
        while True:
            d = get("/observations", place_id=place, quality_grade="research",
                    photo_license=LICENCES, geoprivacy="open", taxon_geoprivacy="open",
                    order_by="id", order="asc", id_above=above, per_page=200)
            res = d.get("results") or []
            if not res:
                break
            for o in res:
                above = max(above, o["id"])
                acc = o.get("positional_accuracy")
                if not o.get("location") or o.get("obscured") or (acc is not None and acc > MAX_ACC_M):
                    continue
                ph = next((p for p in o.get("photos") or []
                           if (p.get("license_code") or "") in ("cc0", "cc-by", "cc-by-sa")
                           and not p.get("hidden")), None)
                t = o.get("taxon") or {}
                if not ph or not t.get("id"):
                    continue
                lat, lng = (float(x) for x in o["location"].split(","))
                u = o.get("user") or {}
                rows[o["id"]] = {
                    "lat": round(lat, 6), "lng": round(lng, 6), "acc": acc,
                    "date": o.get("observed_on"), "prov": prov,
                    "taxon": t["id"], "sci": t.get("name"), "en": t.get("preferred_common_name"),
                    "group": t.get("iconic_taxon_name"),
                    "photo": ph["url"].replace("/square.", "/medium."),
                    "licence": ph["license_code"], "credit": ph.get("attribution"),
                    "user": u.get("name") or u.get("login"),
                }
            print("  ", prov, len(rows), "kept, id >", above)
            time.sleep(1.1)
    # Thai common names, 30 taxa a call
    taxa = sorted({r["taxon"] for r in rows.values()})
    th = {}
    for i in range(0, len(taxa), 30):
        d = get("/taxa/" + ",".join(map(str, taxa[i:i + 30])), locale="th")
        for t in d.get("results") or []:
            n = t.get("preferred_common_name")
            if n and any("฀" <= c <= "๿" for c in n):
                th[t["id"]] = n
        time.sleep(1.1)
    for r in rows.values():
        if r["taxon"] in th:
            r["th"] = th[r["taxon"]]
    print("   Thai names for", len(th), "of", len(taxa), "species")
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(rows, ensure_ascii=False))
    return rows


def km(a1, o1, a2, o2):
    p = math.pi / 180
    x = (o2 - o1) * p * math.cos((a1 + a2) * p / 2)
    return 6371 * math.hypot(x, (a2 - a1) * p)


def pick(rows):
    grid = defaultdict(list)
    for oid, r in rows.items():
        grid[(int(r["lat"] * 50), int(r["lng"] * 50))].append(oid)
    near = {}
    for prov in PLACES:
        for rec in json.loads((ROOT / "data" / "canonical" / (prov + ".json")).read_text()):
            lat, lng = rec.get("lat"), rec.get("lng")
            if lat is None or lng is None:
                continue
            gy, gx = int(lat * 50), int(lng * 50)
            cand = []
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    for oid in grid.get((gy + dy, gx + dx), ()):
                        r = rows[oid]
                        d = km(lat, lng, r["lat"], r["lng"])
                        if d <= RADIUS_KM:
                            cand.append((d, oid))
            cand.sort()
            seen, keep = set(), []
            for d, oid in cand:
                t = rows[oid]["taxon"]
                if t in seen:
                    continue
                seen.add(t)
                keep.append([oid, int(round(d * 1000))])
                if len(keep) >= SHOW:
                    break
            if len(keep) >= MIN_SPECIES:
                near[rec["id"]] = keep
    return near


def download(ids, rows):
    PICS.mkdir(parents=True, exist_ok=True)
    got = 0
    for oid in sorted(ids):
        f = PICS / ("%s.jpg" % oid)
        if f.exists() and f.stat().st_size > 0:
            got += 1
            continue
        try:
            req = urllib.request.Request(rows[oid]["photo"], headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                f.write_bytes(r.read())
            subprocess.run(["sips", "-Z", "500", "-s", "format", "jpeg", "-s", "formatOptions", "72",
                            str(f), "--out", str(f)], capture_output=True)
            got += 1
        except Exception as e:
            print("   ! photo", oid, e)
        time.sleep(0.15)
    return got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-fetch", action="store_true")
    a = ap.parse_args()
    if a.no_fetch and RAW.exists():
        rows = {int(k): v for k, v in json.loads(RAW.read_text()).items()}
    else:
        rows = fetch()
    near = pick(rows)
    used = {oid for v in near.values() for oid, _ in v}
    print("  ", len(near), "place pages,", len(used), "photos to hold")
    have = download(used, rows)
    ok = {oid for oid in used if (PICS / ("%s.jpg" % oid)).exists()}
    near = {k: [x for x in v if x[0] in ok] for k, v in near.items()}
    near = {k: v for k, v in near.items() if len(v) >= MIN_SPECIES}
    obs = {str(oid): {k: v for k, v in rows[oid].items() if k != "photo"} for oid in ok}
    doc = {"source": "iNaturalist research-grade observations, CC0 / CC BY / CC BY-SA photos",
           "radius_km": RADIUS_KM, "obs": obs,
           "near": {k: [[str(o), m] for o, m in v] for k, v in near.items()}}
    ingest.write(OUT, doc, count=len(doc["near"]), min_rows=50,
                 sources_ok=["api.inaturalist.org"], label="inat.json")
    print("   photos on disk:", have)


if __name__ == "__main__":
    main()
