#!/usr/bin/env python3
"""Find freely-licensed photographs of places we already list, on Wikimedia Commons.

Commons lets you ask "what geotagged files are within N metres of this point",
which is exactly the question a directory wants. Every file it returns carries
its licence and its photographer in the metadata, so attribution is a fact we
are handed rather than something we have to reconstruct later.

Why this and not the obvious alternative: a photograph on a maps or review site
belongs to the person who took it, licensed to that platform and not to us. No
scraping ruling changes who owns the picture. Commons images come with a licence
that names what we may do, which is the difference between using an image and
borrowing one.

Two passes:
  1. by place — geosearch a small radius around each record that has coordinates
  2. by area  — sweep a grid over both provinces to find what else is out there,
                so we can see which unlisted subjects are well photographed

    python3 importers/harvest_commons.py                # both provinces
    python3 importers/harvest_commons.py --radius 120   # tighter matching
    python3 importers/harvest_commons.py --max 400      # stop early

Writes data/commons_images.json — never downloads. build.py links the thumbnail
URL, so nothing is republished without its licence travelling alongside it.
"""
import html
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache", "commons")
OUT = os.path.join(ROOT, "data", "commons_images.json")
API = "https://commons.wikimedia.org/w/api.php"
UA = ("mot-dang-directory/1.0 (+https://motdang.net; matching free images to a "
      "local directory; contact 530kings@proton.me)")
PAUSE = 0.6          # Commons is generous, but there is no reason to be rude

# Licences we will actually publish. Anything else is recorded but not used, so
# a licence change upstream cannot quietly turn a usable image into a liability.
OK_LICENCE = re.compile(
    r"^(cc[ -]?(by|zero|0)|public domain|pd|cc[ -]?by[ -]?sa)", re.I)


def api(params):
    params = dict(params, format="json", formatversion="2")
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)


def strip(s):
    """Commons descriptions are HTML fragments. We want the sentence."""
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def haversine(a1, o1, a2, o2):
    r = 6371000.0
    p1, p2 = math.radians(a1), math.radians(a2)
    dp, dl = math.radians(a2 - a1), math.radians(o2 - o1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def geosearch(lat, lng, radius, limit=100):
    try:
        d = api({"action": "query", "generator": "geosearch",
                 "ggscoord": f"{lat}|{lng}", "ggsradius": str(int(radius)),
                 "ggslimit": str(limit), "ggsnamespace": "6",
                 "prop": "imageinfo|coordinates",
                 "iiprop": "url|extmetadata", "iiurlwidth": "640"})
    except (urllib.error.URLError, urllib.error.HTTPError, OSError):
        return []
    time.sleep(PAUSE)
    return d.get("query", {}).get("pages", []) or []


# Words that appear in half the filenames in Chiang Mai and identify nothing.
GENERIC = {"chiang", "mai", "rai", "thailand", "district", "mueang", "wat", "temple",
           "street", "road", "city", "photo", "panoramio", "img", "dsc", "view",
           "thai", "province", "moat", "old", "town", "market", "night"}


def name_tokens(s):
    s = re.sub(r"[^\w\u0E00-\u0E7F\s]", " ", (s or "").lower())
    return {t for t in s.split() if t not in GENERIC and len(t) > 2}


def identifies(place_names, title, description):
    """Does this file claim to BE this place, or merely stand near it?

    Distance alone matched a massage shop to a photograph of electric scooters
    parked forty metres away, and a barber to a street view of the district.
    Both were within the radius; neither was a picture of the business. So a
    match now needs the place's own name to appear in the file's title or its
    description. Far fewer matches, all of them actually of the subject.
    """
    hay = name_tokens(title + " " + (description or ""))
    if not hay:
        return False, None
    for nm in place_names:
        toks = name_tokens(nm)
        if not toks:
            continue
        hit = toks & hay
        # every distinctive word of a short name, or two of a longer one
        need = 1 if len(toks) == 1 else 2
        if len(hit) >= min(need, len(toks)) and len(hit) >= 1 and toks <= hay | toks:
            if len(hit) >= need or toks <= hay:
                return True, ",".join(sorted(hit))
    return False, None


def describe(meta, title):
    """What the photograph shows, in words, from the file's own metadata.

    This is the alt text. It is also just worth reading — a caption that says
    'Wat Chedi Luang during Inthakin, offerings piled at the base' tells a
    sighted reader something a thumbnail does not.
    """
    desc = strip((meta.get("ImageDescription") or {}).get("value"))
    obj = strip((meta.get("ObjectName") or {}).get("value"))
    name = re.sub(r"^File:|\.\w+$", "", title).replace("_", " ")
    for candidate in (desc, obj, name):
        if candidate and len(candidate) > 3:
            return candidate[:400]
    return name[:400]


def usable(meta):
    lic = strip((meta.get("LicenseShortName") or {}).get("value"))
    return bool(lic) and bool(OK_LICENCE.match(lic)), lic


def main():
    radius = 150
    cap = None
    if "--radius" in sys.argv:
        radius = int(sys.argv[sys.argv.index("--radius") + 1])
    if "--max" in sys.argv:
        cap = int(sys.argv[sys.argv.index("--max") + 1])
    os.makedirs(CACHE, exist_ok=True)

    recs = []
    for p in ("cm", "cr"):
        path = os.path.join(ROOT, "data", "canonical", f"{p}.json")
        recs += [r for r in json.load(open(path)) if r.get("lat") is not None]
    # --cat narrows the sweep. Aim it where Commons coverage actually exists:
    # wats and landmarks are photographed and named, a noodle stall is neither.
    if "--cat" in sys.argv:
        want = set(sys.argv[sys.argv.index("--cat") + 1].split(","))
        recs = [r for r in recs if want & set(r.get("cat") or [])]
    # Skip anything that already has a downloaded photo.
    photos = os.path.join(ROOT, "assets", "photos")
    if os.path.isdir(photos):
        have = {f.rsplit(".", 1)[0] for f in os.listdir(photos)}
        recs = [r for r in recs if r["id"] not in have]
    # Merge rather than replace, so a narrow run never discards a wide one.
    prior = {}
    if os.path.exists(OUT):
        try:
            prior = json.load(open(OUT)).get("images", {})
        except (ValueError, OSError):
            prior = {}
    if cap:
        recs = recs[:cap]
    print(f"🐜 {len(recs):,} placed records to look for")

    matches, seen_files, skipped, unnamed = {}, {}, 0, 0
    for i, r in enumerate(recs, 1):
        pages = geosearch(r["lat"], r["lng"], radius, limit=12)
        place_names = [n for n in (r.get("name"), r.get("nameEn"), r.get("nameTh")) if n]
        best = None
        for pg in pages:
            ii = (pg.get("imageinfo") or [{}])[0]
            meta = ii.get("extmetadata") or {}
            ok, lic = usable(meta)
            if not ok:
                skipped += 1
                continue
            co = (pg.get("coordinates") or [{}])[0]
            dist = haversine(r["lat"], r["lng"], co.get("lat", r["lat"]),
                             co.get("lon", r["lng"])) if co else radius
            cand = {
                "placeId": r["id"], "title": pg.get("title", ""),
                "thumb": ii.get("thumburl"), "full": ii.get("descriptionurl"),
                "licence": lic,
                "artist": strip((meta.get("Artist") or {}).get("value")) or "unknown",
                "credit": strip((meta.get("Credit") or {}).get("value")),
                "description": describe(meta, pg.get("title", "")),
                "distance_m": round(dist),
            }
            ok_id, why = identifies(place_names, cand["title"], cand["description"])
            if not ok_id:
                unnamed += 1
                continue
            cand["matched_on"] = why
            if cand["thumb"] and (best is None or dist < best["distance_m"]):
                best = cand
        if best:
            matches[r["id"]] = best
            seen_files[best["title"]] = seen_files.get(best["title"], 0) + 1
        if i % 25 == 0:
            print(f"   {i:,}/{len(recs):,} · {len(matches)} matched")

    # A file that matches many places is a wide shot of a district, not a
    # portrait of any one of them — drop those rather than caption them wrongly.
    crowded = {t for t, n in seen_files.items() if n > 3}
    for pid in [k for k, v in matches.items() if v["title"] in crowded]:
        del matches[pid]

    merged = dict(prior)
    merged.update(matches)
    matches = merged
    with open(OUT, "w") as fh:
        json.dump({"generated": date.today().isoformat(),
                   "radius_m": radius, "count": len(matches),
                   "source": "Wikimedia Commons",
                   "images": matches}, fh, ensure_ascii=False, indent=1)
    print(f"🐜 {len(matches)} place(s) matched to a freely-licensed photo -> {OUT}")
    print(f"   {len(crowded)} file(s) dropped for matching too many places")
    print(f"   {skipped} file(s) skipped on licence")
    print(f"   {unnamed} nearby file(s) rejected — near the place, not OF it")


if __name__ == "__main__":
    main()
