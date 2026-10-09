#!/usr/bin/env python3
"""What each wat is, from the encyclopaedia, in both languages.

`enrich_wikipedia.py` fills a place's first sentence only where the record
itself points at an article — a Q-id or a `wikipedia=` tag — and takes no
article that only a name search found. That rule is right and this file keeps
it. It reaches the rest a different way: Wikipedia will answer "which
articles have coordinates within 300 m of this point", so identity is proved on
the ground first and the name only has to agree with it. That is the same
standard `harvest_commons.py` holds a photograph to.

Two things it collects for /wats:

  * the Thai lead for the 25 wats in the box that have no summary on disk —
    Wat Phra Singh among them, which is the most visited wat in Chiang Mai
  * the ENGLISH lead for every wat that has one, reached by the Thai article's
    own langlink. 67 wats on this disk carry a Thai summary and not one carries
    an English one, so every English reader of the wat pages was being handed a
    name and a pin.

Wikipedia text is CC BY-SA 4.0: every extract lands with its article URL, its
title, the licence and the revision date, and the page prints the credit beside
the sentence. An extract missing any of that is dropped rather than shown.

Politeness, on somebody else's donated servers: the REST summary and the
geosearch API, one request at a time, a second between them, a User-Agent that
says who we are, everything cached under cache/wikipedia/ so a re-run is free.

    python3 importers/enrich_wats.py --dry-run
    python3 importers/enrich_wats.py

Writes data/curated/wat_wiki.json. Reads data/wats.json for which wats to ask
about, so it follows the rounds rather than sweeping the catalogue.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "importers"))
sys.path.insert(0, ROOT)
from build_wats import skeleton                        # noqa: E402

CANON = os.path.join(ROOT, "data", "canonical", "cm.json")
WATS = os.path.join(ROOT, "data", "wats.json")
OUT = os.path.join(ROOT, "data", "curated", "wat_wiki.json")
CACHE = os.path.join(ROOT, "cache", "wikipedia")
UA = ("MotDangBot/1.0 (+https://motdang.net/about.html; wat pages; "
      "530kings@proton.me)")
PAUSE = 1.0
TIMEOUT = 20
MAX_CHARS = 700
LICENCE = "CC BY-SA 4.0"
LICENCE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
NEAR_M = 300
LIST_TITLE = re.compile(r"^(รายชื่อ|รายการ|Lists? of\b)", re.I)


def load(path, default):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def cache_path(kind, key):
    stem = re.sub(r"[^A-Za-z0-9_.-]", "", f"{kind}-{key}")[:60]
    digest = hashlib.sha1(f"{kind}{key}".encode("utf-8")).hexdigest()[:12]
    return os.path.join(CACHE, f"{stem}-{digest}.json" if stem else f"{digest}.json")


def get(url, kind, key):
    """One cached GET of JSON. A failure caches as empty and is not retried."""
    cp = cache_path(kind, key)
    doc = load(cp, None)
    if doc is not None:
        return doc or {}
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                              "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            doc = json.loads(resp.read(600_000).decode("utf-8", "replace"))
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError,
            TimeoutError, OSError) as exc:
        print("      ! %s" % exc)
        doc = {}
    time.sleep(PAUSE)
    os.makedirs(CACHE, exist_ok=True)
    with open(cp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False)
    return doc


def nearby(lang, lat, lng):
    """Articles with coordinates within NEAR_M of a point, nearest first."""
    q = urllib.parse.urlencode({
        "action": "query", "list": "geosearch", "format": "json",
        "gscoord": "%.6f|%.6f" % (lat, lng), "gsradius": NEAR_M, "gslimit": 10})
    doc = get("https://%s.wikipedia.org/w/api.php?%s" % (lang, q),
              "geo" + lang, "%.5f,%.5f" % (lat, lng))
    return ((doc.get("query") or {}).get("geosearch") or [])


def summary(lang, title):
    url = ("https://%s.wikipedia.org/api/rest_v1/page/summary/%s"
           % (lang, urllib.parse.quote(title.replace(" ", "_"), safe="")))
    return get(url, "sum" + lang, title)


def langlink(lang, title, want):
    q = urllib.parse.urlencode({
        "action": "query", "prop": "langlinks", "format": "json",
        "titles": title, "lllang": want, "redirects": 1})
    doc = get("https://%s.wikipedia.org/w/api.php?%s" % (lang, q),
              "ll%s%s" % (lang, want), title)
    for pg in ((doc.get("query") or {}).get("pages") or {}).values():
        for ll in pg.get("langlinks") or []:
            if ll.get("lang") == want and ll.get("*"):
                return ll["*"]
    return None


def extract_of(doc):
    """(text, url, title, revision), or None when anything needed is absent."""
    if not doc or doc.get("type") == "disambiguation":
        return None
    if LIST_TITLE.match((doc.get("title") or "").strip()):
        return None
    text = (doc.get("extract") or "").strip()
    if len(text) < 40:
        return None
    if len(text) > MAX_CHARS:
        cut = text[:MAX_CHARS]
        text = (cut[:cut.rfind(" ")] if " " in cut else cut).rstrip(" ,;:") + "…"
    page = ((doc.get("content_urls") or {}).get("desktop") or {}).get("page")
    if not (page and doc.get("title")):
        return None
    return {"text": text, "url": page, "title": doc["title"],
            "revision": (doc.get("timestamp") or "")[:10],
            "license": LICENCE, "licenseUrl": LICENCE_URL}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    wats = load(WATS, {}).get("wats") or []
    if not wats:
        print("no data/wats.json — run importers/build_wats.py first",
              file=sys.stderr)
        return 1
    recs = {r["id"]: r for r in load(CANON, [])}
    out = load(OUT, {})
    if args.limit:
        wats = wats[:args.limit]

    found_th = found_en = 0
    for i, w in enumerate(wats, 1):
        r = recs.get(w["id"]) or {}
        have = ((r.get("attrs") or {}).get("summary") or {})
        entry = dict(out.get(w["id"]) or {})
        th_title = have.get("title") if have.get("lang") == "th" else None
        name = w.get("name") or ""
        keys = {k for k in (skeleton(n) for n in
                            (w.get("name"), w.get("nameTh"), w.get("nameEn")) if n)
                if len(k) >= 4}

        if not th_title and "th" not in entry:
            # Identity on the ground first: which articles are AT this wat.
            for hit in nearby("th", w["lat"], w["lng"]):
                title = hit.get("title") or ""
                if skeleton(title) not in keys:
                    continue
                ex = extract_of(summary("th", title))
                if ex:
                    ex["matched_on"] = "%d m + name" % round(hit.get("dist") or 0)
                    entry["th"] = ex
                    th_title = title
                    found_th += 1
                    print("   +th %-34s %s" % (name[:34], title))
                    break

        src_title = th_title or (entry.get("th") or {}).get("title")
        if src_title and "en" not in entry:
            en_title = langlink("th", src_title, "en")
            if en_title:
                ex = extract_of(summary("en", en_title))
                if ex:
                    ex["matched_on"] = "langlink from %s" % src_title
                    entry["en"] = ex
                    found_en += 1
                    print("   +en %-34s %s" % (name[:34], en_title))
        if entry:
            out[w["id"]] = entry
        if i % 20 == 0:
            print("   %d/%d" % (i, len(wats)))

    print("\n%d Thai leads found, %d English leads found" % (found_th, found_en))
    if args.dry_run:
        print("dry run — nothing written")
        return 0
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, sort_keys=True)
    print("%d wats with an encyclopaedia lead  →  %s"
          % (len(out), os.path.relpath(OUT, ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
