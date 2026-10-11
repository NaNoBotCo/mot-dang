#!/usr/bin/env python3
"""Photographs for places whose OSM element links to Wikidata or Commons.

harvest_commons.py and commons_pool.py match a Commons file to a place by
distance and name. This takes the other route: an OSM element tagged
`wikidata=Q…` names the item, and the item's P18 names its photograph; a
`wikimedia_commons=File:…` or a Commons `image=` tag names the file directly.
The link was made by a mapper, so no name test is needed.

Reads the OSM elements cached under cache/overpass/ and cache/osm-*/, or with
--fresh asks Overpass for every element in both provinces that carries one of
those tags. Merges into data/commons_images.json for places with no entry
there and no lead photo in assets/photos/; existing rows are kept. Never
downloads a picture.

    python3 importers/harvest_wikidata_photos.py            # from the cache
    python3 importers/harvest_wikidata_photos.py --fresh    # ask Overpass too
"""
import glob
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "importers"))
import harvest_commons as hc  # noqa: E402

OUT = os.path.join(ROOT, "data", "commons_images.json")
WD = "https://www.wikidata.org/w/api.php"
OVERPASS = ("https://overpass.kumi.systems/api/interpreter",
            "https://overpass-api.de/api/interpreter")
# Chiang Mai and Chiang Rai provinces, s,w,n,e
BBOX = "17.2,97.3,20.5,100.6"
PAUSE = 0.6


def get(url, params=None, data=None, timeout=60):
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, data=data, headers={
        "User-Agent": hc.UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def cached_elements():
    out = []
    for f in (glob.glob(os.path.join(ROOT, "cache", "overpass", "**", "*.json"), recursive=True)
              + glob.glob(os.path.join(ROOT, "cache", "osm-*", "**", "*.json"), recursive=True)):
        try:
            d = json.load(open(f))
        except (ValueError, OSError):
            continue
        if isinstance(d, dict):
            out += d.get("elements") or []
    return out


def fresh_elements():
    """The two provinces in four quarters; the whole box times out (504)."""
    s, w, n, e = (float(v) for v in BBOX.split(","))
    ms, mw = (s + n) / 2, (w + e) / 2
    out = []
    for box in ((s, w, ms, mw), (s, mw, ms, e), (ms, w, n, mw), (ms, mw, n, e)):
        bb = "%s,%s,%s,%s" % box
        q = ("[out:json][timeout:180];(nwr[wikidata](%s);nwr[wikimedia_commons](%s);"
             "nwr[image~\"commons.wikimedia\"](%s););out tags;" % (bb, bb, bb))
        for url in OVERPASS:
            try:
                out += get(url, data=urllib.parse.urlencode({"data": q}).encode(),
                           timeout=240).get("elements") or []
                break
            except Exception as ex:
                print("  %s did not answer for %s (%s)" % (url, bb, ex))
    return out


def commons_title(v):
    """'File:X.jpg' from a wikimedia_commons or image tag, or None."""
    v = (v or "").strip()
    if v.startswith("File:"):
        return v.split(";")[0]
    m = re.search(r"commons\.wikimedia\.org/wiki/(File:[^?#]+)", v)
    if m:
        return urllib.parse.unquote(m.group(1)).replace("_", " ")
    m = re.search(r"upload\.wikimedia\.org/wikipedia/commons/(?:thumb/)?\w/\w\w/([^/?#]+)", v)
    if m:
        return "File:" + urllib.parse.unquote(m.group(1)).replace("_", " ")
    return None


def p18(qids):
    """{Q…: 'File:…'} for items that carry an image."""
    out, qids = {}, sorted(qids)
    for i in range(0, len(qids), 50):
        d = get(WD, {"action": "wbgetentities", "ids": "|".join(qids[i:i + 50]),
                     "props": "claims", "format": "json"})
        for q, ent in (d.get("entities") or {}).items():
            for c in (ent.get("claims") or {}).get("P18") or []:
                v = ((c.get("mainsnak") or {}).get("datavalue") or {}).get("value")
                if v:
                    out[q] = "File:" + v
                    break
        time.sleep(PAUSE)
    return out


def imageinfo(titles):
    out, titles = {}, sorted(set(titles))
    for i in range(0, len(titles), 40):
        d = hc.api({"action": "query", "titles": "|".join(titles[i:i + 40]),
                    "prop": "imageinfo", "iiprop": "url|extmetadata",
                    "iiurlwidth": "960"})
        q = d.get("query") or {}
        norm = {n["to"]: n["from"] for n in q.get("normalized") or []}
        for pg in q.get("pages") or []:
            ii = (pg.get("imageinfo") or [{}])[0]
            if ii:
                out[norm.get(pg["title"], pg["title"])] = ii
                out[pg["title"]] = ii
        time.sleep(PAUSE)
    return out


def main():
    ids = set()
    for p in ("cm", "cr"):
        ids |= {r["id"] for r in json.load(open(os.path.join(ROOT, "data", "canonical", "%s.json" % p)))}
    els = cached_elements() + (fresh_elements() if "--fresh" in sys.argv else [])
    links = {}
    for x in els:
        t = x.get("tags") or {}
        for p in ("cm", "cr"):
            rid = "%s-osm-%s-%s" % (p, x.get("type"), x.get("id"))
            if rid in ids and (t.get("wikidata") or t.get("wikimedia_commons") or t.get("image")):
                links[rid] = t

    ci = json.load(open(OUT)) if os.path.exists(OUT) else {"images": {}}
    imgs = ci.setdefault("images", {})
    photos = os.path.join(ROOT, "assets", "photos")
    have = {f.rsplit(".", 1)[0] for f in os.listdir(photos)} if os.path.isdir(photos) else set()
    todo = {rid: t for rid, t in links.items() if rid not in imgs and rid not in have}
    print("places linked to Wikidata or Commons: %d · without a photo: %d" % (len(links), len(todo)))

    qmap = p18({t["wikidata"].strip() for t in todo.values()
                if re.fullmatch(r"Q\d+", (t.get("wikidata") or "").strip())})
    want = {}
    for rid, t in todo.items():
        title = (commons_title(t.get("wikimedia_commons")) or commons_title(t.get("image"))
                 or qmap.get((t.get("wikidata") or "").strip()))
        if title:
            want[rid] = (title, "wikidata P18" if title == qmap.get((t.get("wikidata") or "").strip())
                         else "OSM commons tag")
    info = imageinfo(t for t, _ in want.values())

    added = skipped = 0
    for rid, (title, how) in sorted(want.items()):
        ii = info.get(title)
        if not ii or not ii.get("thumburl"):
            continue
        meta = ii.get("extmetadata") or {}
        ok, lic = hc.usable(meta)
        if not ok:
            skipped += 1
            continue
        imgs[rid] = {
            "placeId": rid, "title": title, "thumb": ii["thumburl"],
            "full": ii.get("descriptionurl"), "licence": lic,
            "artist": hc.strip((meta.get("Artist") or {}).get("value")) or "unknown",
            "credit": hc.strip((meta.get("Credit") or {}).get("value")),
            "description": hc.describe(meta, title), "distance_m": 0,
            "matched_on": how, "via": "harvest_wikidata_photos",
        }
        added += 1
    ci["count"] = len(imgs)
    ci["generated_wikidata"] = date.today().isoformat()
    with open(OUT, "w") as fh:
        json.dump(ci, fh, ensure_ascii=False, indent=1)
    print("named a photo: %d · licence not usable: %d · added: %d · now %d places"
          % (len(want), skipped, added, len(imgs)))


if __name__ == "__main__":
    main()
