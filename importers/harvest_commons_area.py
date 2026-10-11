#!/usr/bin/env python3
"""Every geotagged Commons photograph in Chiang Mai and Chiang Rai, with its metadata.

harvest_commons.py asks "is there a photograph OF this place" one record at a
time. This asks the other question — what has been photographed here at all —
by sweeping both provinces with Commons geosearch. A circle that comes back
full (500 files) is split in four and asked again, so the old city ends up
swept in 600 m circles and the hills in 10 km ones.

    python3 importers/harvest_commons_area.py            # sweep + metadata
    python3 importers/harvest_commons_area.py --meta     # metadata only, from the cached sweep

Writes cache/commons_area/files.json — {title: {lat, lng, w, h, mime, url,
licence, artist, desc, date, cats}}. Never downloads a picture;
importers/commons_pool.py chooses and fetches.
"""
import argparse
import html
import json
import math
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache" / "commons_area"
API = "https://commons.wikimedia.org/w/api.php"
UA = ("mot-dang-directory/1.0 (+https://motdang.net; matching free images to a "
      "local directory; contact 530kings@proton.me)")
PAUSE = 0.35

# Province boxes, generous; points are kept wherever they fall and
# commons_pool.py files them by the amphoe polygons, not by these boxes.
BOXES = {
    "cm": (17.20, 97.30, 20.20, 99.65),
    "cr": (19.05, 99.25, 20.50, 100.65),
}
R0 = 10000          # the API's ceiling, metres


def api(params):
    params = dict(params, format="json", formatversion="2")
    url = API + "?" + urllib.parse.urlencode(params)
    body = None
    if len(url) > 1800:          # fifty Thai titles, percent-encoded, overflow a GET
        url, body = API, urllib.parse.urlencode(params).encode()
    for i in range(5):
        try:
            req = urllib.request.Request(url, data=body, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:                       # noqa: BLE001
            print("  retry", i, e, file=sys.stderr)
            time.sleep(3 * (i + 1))
    return {}


def circle(lat, lng, r):
    d = api({"action": "query", "list": "geosearch", "gscoord": f"{lat}|{lng}",
             "gsradius": int(r), "gslimit": 500, "gsnamespace": 6,
             "gsprop": "type"})
    time.sleep(PAUSE)
    return d.get("query", {}).get("geosearch", [])


def sweep(found, done, lat, lng, r, depth=0):
    key = f"{lat:.5f},{lng:.5f},{int(r)}"
    if key in done:
        return
    rows = circle(lat, lng, r)
    for g in rows:
        found.setdefault(g["title"], {"lat": g["lat"], "lng": g["lon"]})
    done.add(key)
    if len(rows) >= 500 and r > 300:
        # Split: four circles of half the radius at the quarter points, plus
        # the centre, cover the parent circle with overlap.
        h = r / 2
        dlat = h / 111320
        dlng = h / (111320 * math.cos(math.radians(lat)))
        for a, b in ((0, 0), (dlat, dlng), (dlat, -dlng), (-dlat, dlng), (-dlat, -dlng)):
            sweep(found, done, lat + a, lng + b, h * 1.15, depth + 1)
    if len(done) % 25 == 0:
        print(f"  {len(done)} circles, {len(found)} files", flush=True)
        save_sweep(found, done)


def save_sweep(found, done):
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / "sweep.json").write_text(json.dumps(
        {"found": found, "done": sorted(done)}, ensure_ascii=False))


def strip(h):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h or ""))).strip()


def meta(found, out_path=None):
    out_path = out_path or (CACHE / "files.json")
    out = json.loads(out_path.read_text()) if out_path.exists() else {}
    todo = [t for t in found if t not in out]
    print(f"metadata: {len(todo)} to fetch, {len(out)} cached")
    for i in range(0, len(todo), 50):
        batch = todo[i:i + 50]
        d = api({"action": "query", "titles": "|".join(batch),
                 "prop": "imageinfo|categories|coordinates", "iiprop": "url|size|mime|extmetadata",
                 "iiurlwidth": 960, "cllimit": "max", "clshow": "!hidden",
                 "iiextmetadatafilter": "LicenseShortName|Artist|ImageDescription|"
                                        "DateTimeOriginal|ObjectName"})
        time.sleep(PAUSE)
        for pg in d.get("query", {}).get("pages", []):
            t = pg.get("title")
            ii = (pg.get("imageinfo") or [None])[0]
            if not t or not ii:
                continue
            md = ii.get("extmetadata", {})
            g = found.get(t) or {}
            co = (pg.get("coordinates") or [{}])[0]
            out[t] = {
                "lat": g.get("lat") if g.get("lat") is not None else co.get("lat"),
                "lng": g.get("lng") if g.get("lng") is not None else co.get("lon"),
                "w": ii.get("width"), "h": ii.get("height"), "mime": ii.get("mime"),
                "url": ii.get("url"), "thumb": ii.get("thumburl"),
                "page": ii.get("descriptionurl"),
                "licence": strip(md.get("LicenseShortName", {}).get("value")),
                "artist": strip(md.get("Artist", {}).get("value"))[:120],
                "desc": strip(md.get("ImageDescription", {}).get("value"))[:600],
                "name": strip(md.get("ObjectName", {}).get("value"))[:200],
                "date": strip(md.get("DateTimeOriginal", {}).get("value"))[:40],
                "cats": [c["title"][9:] for c in pg.get("categories", [])],
            }
        if (i // 50) % 10 == 0:
            print(f"  {i + len(batch)}/{len(todo)}", flush=True)
            out_path.write_text(json.dumps(out, ensure_ascii=False))
    out_path.write_text(json.dumps(out, ensure_ascii=False))
    print(f"files.json: {len(out)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", action="store_true")
    a = ap.parse_args()
    sw = CACHE / "sweep.json"
    st = json.loads(sw.read_text()) if sw.exists() else {"found": {}, "done": []}
    found, done = st["found"], set(st["done"])
    if not a.meta:
        for key, (s, w, n, e) in BOXES.items():
            step = R0 * 1.4 / 111320        # circles of 10 km on a 15.6 km grid overlap
            lat = s
            while lat <= n:
                lng = w
                while lng <= e:
                    sweep(found, done, round(lat, 5), round(lng, 5), R0)
                    lng += step / math.cos(math.radians(lat))
                lat += step
            print(f"{key}: {len(done)} circles, {len(found)} files", flush=True)
            save_sweep(found, done)
    meta(found)


if __name__ == "__main__":
    main()
