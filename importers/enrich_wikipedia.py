#!/usr/bin/env python3
"""Give a place its first sentence, from the encyclopaedia article it already cites.

WHY
12,296 of 12,319 pages open with a name and a pin and nothing else. Meanwhile
~350 records carry `attrs.wikidata`, `attrs.brandWikipedia` or `attrs.heritage`
— a mapper already established that this temple, this museum, this waterfall has
an article about it. The sentence exists; nobody has ever fetched it.

WHAT IT TAKES
The lead extract only — the one or two sentences an encyclopaedia opens with,
which is exactly the length a directory entry wants. Thai first and English
second, both when both exist, because this is a Thai-first site about Thai
places and the Thai article is usually the fuller one.

LICENCE, WHICH IS A CONDITION AND NOT A COURTESY
Wikipedia text is CC BY-SA 4.0. Every extract lands with its article URL, its
title, the licence and the revision date, and `build.py` prints the credit with
the sentence — the same arrangement the photographs already keep. An extract
whose attribution fields are incomplete is dropped rather than shown, because a
sentence we cannot credit is a sentence we cannot use.

POLITENESS, on somebody else's donated servers:
  - the REST summary endpoint, which exists for exactly this and is cheap
  - one request at a time, one second between them
  - a User-Agent that says who we are and where to complain (the Wikimedia
    User-Agent policy asks for this by name)
  - cached under cache/wikipedia/, so a re-run costs nothing
  - anything slow or missing is skipped, never retried in a loop

    python3 importers/enrich_wikipedia.py --limit 20 --dry-run
    python3 importers/enrich_wikipedia.py --limit 100
    python3 importers/enrich_wikipedia.py                  # the whole queue

Writes data/curated/enrich.json — never data/canonical/, which the crawl
rewrites wholesale.
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
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANON = os.path.join(ROOT, "data", "canonical")
OUT = os.path.join(ROOT, "data", "curated", "enrich.json")
CACHE = os.path.join(ROOT, "cache", "wikipedia")
UA = ("MotDangBot/1.0 (+https://motdang.net/about.html; directory enrichment; "
      "530kings@proton.me)")
PAUSE = 1.0
TIMEOUT = 20
LICENCE = "CC BY-SA 4.0"
LICENCE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
# A directory entry wants the opening sentences, not the article.
MAX_CHARS = 420
# Shelves where an encyclopaedia article is about the PLACE. A branch of a
# chain is deliberately excluded: the article about 7-Eleven is about the
# company, and printing it under one shop in Chiang Mai would say something
# untrue about that shop.
# An article whose title announces it is a LIST is about a set, never about
# one member of it. See extract_of for the case that found this.
LIST_TITLE = re.compile(r"^(รายชื่อ|รายการ|Lists? of\b)", re.I)
WANTED_CATS = {"wat", "sights", "museums-galleries", "parks", "market",
               "sport", "community", "transport"}


def load(path, default):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def cache_path(lang, title):
    """A cache filename that cannot collide.

    The first version replaced every non-ASCII character with "_", which meant
    every Thai title of the same LENGTH shared one file: อุทยานแห่งชาติแม่ปืม
    was served มหาวิทยาลัยเชียงใหม่'s article, and Mae Puem National Park went
    out described as a university. On a Thai-first site a cache key that cannot
    hold Thai is not a cache, it is a way of quietly swapping one place's facts
    for another's. The readable stem is kept for anyone reading the directory,
    and a hash of the real title makes it unique.
    """
    stem = re.sub(r"[^A-Za-z0-9_.-]", "", f"{lang}-{title}")[:60]
    digest = hashlib.sha1(f"{lang}{title}".encode("utf-8")).hexdigest()[:12]
    return os.path.join(CACHE, f"{stem}-{digest}.json" if stem else f"{digest}.json")


def fetch_summary(lang, title, session):
    """The REST summary for one article, or None. Cached on disk."""
    cp = cache_path(lang, title)
    cached = load(cp, None)
    if cached is not None:
        return cached or None
    url = (f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/"
           + urllib.parse.quote(title.replace(" ", "_"), safe=""))
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            doc = json.loads(resp.read(400_000).decode("utf-8", "replace"))
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError,
            TimeoutError, OSError):
        doc = {}
    time.sleep(PAUSE)
    os.makedirs(CACHE, exist_ok=True)
    with open(cp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False)
    return doc or None


def extract_of(doc):
    """(text, url, title, revision) — or None when anything needed is absent.

    A disambiguation page is not a description of anywhere, and neither is an
    article we reached by a redirect we cannot verify points at this place.

    NEITHER IS A LIST. Found 2026-08-21: สถานีรถไฟสารภี cites a Wikidata item
    whose Thai sitelink is รายชื่อสถานีรถไฟ สายเหนือ — "List of railway
    stations, Northern Line" — so the station's Thai blurb described the LINE,
    on a page named for one station. Its English sitelink is the station's own
    article, which is what makes this the same animal as the chain exclusion
    above: the article is real, and it is about something larger than the
    place. A list cannot be a description of one of its entries, so it is
    refused in whichever language it arrives, and the other language still
    stands on its own.
    """
    if not doc or doc.get("type") == "disambiguation":
        return None
    if LIST_TITLE.match((doc.get("title") or "").strip()):
        return None
    text = (doc.get("extract") or "").strip()
    if len(text) < 40:
        return None
    if len(text) > MAX_CHARS:
        cut = text[:MAX_CHARS]
        text = cut[:cut.rfind(" ")] if " " in cut else cut
        text = text.rstrip(" ,;:") + "…"
    page = ((doc.get("content_urls") or {}).get("desktop") or {}).get("page")
    title = doc.get("title")
    rev = (doc.get("timestamp") or "")[:10]
    if not (page and title):
        return None
    return {"text": text, "url": page, "title": title, "revision": rev}


def wikidata_sitelinks(qid):
    """{lang: title} for a Wikidata item, from its own entity file. Cached.

    Most records that cite an encyclopaedia do it with a Q-id rather than an
    article title — 44 here against 9 — because that is what OSM's `wikidata`
    tag holds. The item's sitelinks are the mapping from that id to the article
    in each language, so this is a lookup of a stated fact, not a search by
    name: the Q-id says WHICH thing, and a name search could not.
    """
    if not re.fullmatch(r"Q\d+", qid or ""):
        return {}
    cp = cache_path("wikidata", qid)
    doc = load(cp, None)
    if doc is None:
        url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
        req = urllib.request.Request(url, headers={"User-Agent": UA,
                                                   "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                doc = json.loads(resp.read(3_000_000).decode("utf-8", "replace"))
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError,
                TimeoutError, OSError):
            doc = {}
        time.sleep(PAUSE)
        os.makedirs(CACHE, exist_ok=True)
        # Only the sitelinks are kept: an entity file runs to megabytes and the
        # rest of it is nothing this importer will ever ask for again.
        ent = ((doc.get("entities") or {}).get(qid) or {})
        doc = {lang[:-4]: v.get("title")
               for lang, v in (ent.get("sitelinks") or {}).items()
               if lang.endswith("wiki") and v.get("title")}
        with open(cp, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False)
    return doc or {}


def wiki_targets(r):
    """[(lang, title)] this record itself points at. Never a guess from the name."""
    a = r.get("attrs") or {}
    out = []
    for lang, title in sorted(wikidata_sitelinks(a.get("wikidata") or "").items()):
        if lang in ("th", "en"):
            out.append((lang, title))
    # A mapper wrote wikipedia="th:วัดเจดีย์หลวง" or brand:wikipedia="en:7-Eleven".
    for key in ("wikipedia", "brandWikipedia"):
        v = a.get(key)
        if isinstance(v, str) and ":" in v:
            lang, _, title = v.partition(":")
            if len(lang) <= 3 and title and key == "wikipedia":
                out.append((lang.strip(), title.strip()))
    for key, lang in (("summary", "th"), ("article", "th")):
        v = a.get(key)
        if isinstance(v, str) and v.startswith("http"):
            m = re.match(r"https?://([a-z-]+)\.wikipedia\.org/wiki/(.+)$", v)
            if m:
                out.append((m.group(1), urllib.parse.unquote(m.group(2))))
    return list(dict.fromkeys(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--refresh", action="store_true",
                    help="re-read places that already carry a researched blurb")
    args = ap.parse_args()

    enrich = load(OUT, {})
    records = []
    for prov in ("cm", "cr"):
        records += load(os.path.join(CANON, f"{prov}.json"), [])

    queue = []
    for r in records:
        if not (set(r.get("cat") or []) & WANTED_CATS):
            continue
        cur = enrich.get(r["id"]) or {}
        if cur.get("blurb") and not args.refresh:
            continue
        targets = wiki_targets(r)
        if targets:
            queue.append((r, targets))
    if args.limit:
        queue = queue[:args.limit]

    print(f"{len(queue)} place(s) with an article to read"
          + (" (dry run)" if args.dry_run else ""))
    wrote = 0
    for r, targets in queue:
        got = {}
        for lang, title in targets:
            if lang not in ("th", "en") or lang in got:
                continue
            ext = extract_of(fetch_summary(lang, title, None))
            if ext:
                got[lang] = ext
        if not got:
            continue
        blurb = {"source": "wikipedia", "licence": LICENCE,
                 "licenceUrl": LICENCE_URL, "fetched": date.today().isoformat()}
        for lang in ("th", "en"):
            if lang in got:
                blurb[lang] = got[lang]
        name = r.get("nameEn") or r.get("name") or r["id"]
        print(f"  {name[:44]:<44} {' + '.join(sorted(got))}"
              f"  {list(got.values())[0]['text'][:52]}…")
        if not args.dry_run:
            enrich.setdefault(r["id"], {})["blurb"] = blurb
            wrote += 1

    if not args.dry_run and wrote:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w", encoding="utf-8") as fh:
            json.dump(enrich, fh, ensure_ascii=False, indent=1, sort_keys=True)
    print(f"\n{wrote} blurb(s) written to data/curated/enrich.json"
          if not args.dry_run else "\nnothing written (dry run)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
