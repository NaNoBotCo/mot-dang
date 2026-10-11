#!/usr/bin/env python3
"""No blurbs, and no page that tells a reader to go and ask.

Nan, 2026-09-06: "if you need a blurb, you're doing it wrong. All information
should be structured." And: "No website of mine should ever tell a user 'just
go ask'. That's why they used SEARCH."

Until that day the site carried 2,725 "blurbs": 2,455 were a machine join of a
Thai directory's trade tags plus a street (importers/cmhy_records.py), 242 were
prose typed by Claude sessions into data/curated/additions-*.json, and any
blurb at all put a ★ on the page. Ten of the English ones told the reader to
ring the shop and ask. This test holds three things:

  1. No record on disk — canonical or curated — carries blurb_th / blurb_en.
  2. No record's rendered text tells the reader to phone / ring / ask to find
     out, or narrates the gap ("nobody has", "we haven't"). The gap is a
     missing FIELD, and a field is rendered as a field or not at all.
  3. If docs/ is built: no place page carries the ★ paragraph or the
     .osmblurb paragraph.

    python3 tests/test_no_blurbs.py
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BLURB_KEYS = ("blurb_th", "blurb_en")

# The "just go ask" set. Enforced by regex and rejection, not by politeness.
GO_ASK = re.compile(
    r"(ring and ask|call and ask|phone them|ring them|ask them|worth asking"
    r"|call (?:them|ahead|first)|phone (?:ahead|first)"
    r"|nobody has|no one has|we haven'?t"
    r"|ควรโทรถาม|โทรถาม(?!ก่อน)|ลองโทร|ยังไม่ได้ไป|ยังไม่มีใคร|ยังไม่ได้ยืนดู)",
    re.I)

# Fields that never reach a page as prose: provenance notes for the ants,
# encyclopaedia sections carried for citation, and every URL.
SKIP_PATHS = ("sources", "pinNote", "unverified", "article", "summaryEn",
              "summaryTh", "history", "_note", "note", "ref", "url", "why")


def records():
    out = []
    for f in glob.glob(os.path.join(ROOT, "data", "canonical", "*.json")):
        d = json.load(open(f, encoding="utf-8"))
        out += [(f, r) for r in d if isinstance(r, dict)]
    for f in glob.glob(os.path.join(ROOT, "data", "curated", "*.json")):
        d = json.load(open(f, encoding="utf-8"))
        lists = [d] if isinstance(d, list) else [v for v in d.values() if isinstance(v, list)]
        for lst in lists:
            out += [(f, r) for r in lst if isinstance(r, dict) and "id" in r]
    return out


def walk(o, path=()):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in SKIP_PATHS or k.startswith("_"):
                continue
            yield from walk(v, path + (k,))
    elif isinstance(o, list):
        for v in o:
            yield from walk(v, path)
    elif isinstance(o, str):
        yield path, o


def main():
    fails = []
    recs = records()
    for f, r in recs:
        for k in BLURB_KEYS:
            if r.get(k):
                fails.append(f"{os.path.relpath(f, ROOT)} {r.get('id')}: carries {k}")
        for path, s in walk(r):
            if GO_ASK.search(s):
                fails.append(f"{os.path.relpath(f, ROOT)} {r.get('id')} "
                             f"{'.'.join(path)}: tells the reader to go ask — {s[:80]!r}")
    # 3. the built pages, when there are any
    pages = glob.glob(os.path.join(ROOT, "docs", "*", "p", "*.html"))
    star = osm = 0
    for p in pages:
        t = open(p, encoding="utf-8", errors="replace").read()
        if '<p class="featured">' in t:
            star += 1
        if 'class="osmblurb"' in t:
            osm += 1
    if star:
        fails.append(f"docs/: {star} place pages still carry the ★ blurb paragraph")
    if osm:
        fails.append(f"docs/: {osm} place pages still carry an .osmblurb paragraph")
    print(f"records checked: {len(recs):,} · place pages checked: {len(pages):,}")
    if fails:
        print("\n".join(fails[:40]))
        if len(fails) > 40:
            print(f"... and {len(fails) - 40} more")
        print(f"FAIL: {len(fails)}")
        return 1
    print("OK: no blurbs, nobody told to go ask")
    return 0


if __name__ == "__main__":
    sys.exit(main())
