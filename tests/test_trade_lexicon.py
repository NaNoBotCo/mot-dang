#!/usr/bin/env python3
"""The trade-tag lexicon is whole, and readings print only where they are sound.

Nan, 2026-09-06: readings are one of the most useful things this site does and
it does far too little of it. data/trade_lexicon.json (built by
importers/build_trade_lexicon.py) is the one table the place page, the index
and the AI read a trade tag's reading and gloss from. This holds:

  1. Every trade tag on a canonical record has a lexicon entry.
  2. A reading marked suspect never prints — the page shows the Thai alone.
     (Checked on the built pages when docs/ exists.)
  3. Every gloss names its source (glossVia); none is machine-translated.
  4. Every tambon/amphoe name in admin_areas.json has a reading.

    python3 tests/test_trade_lexicon.py
"""
import glob
import html
import json
import os
import random
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEX = os.path.join(ROOT, "data", "trade_lexicon.json")
GLOSS_VIA = {"record", "thesaurus", "shelf-label", "curated"}


def main():
    fails = []
    if not os.path.exists(LEX):
        print("FAIL: data/trade_lexicon.json missing — run importers/build_trade_lexicon.py")
        return 1
    doc = json.load(open(LEX, encoding="utf-8"))
    tags, areas = doc.get("tags") or {}, doc.get("areas") or {}

    recs = []
    for f in glob.glob(os.path.join(ROOT, "data", "canonical", "*.json")):
        recs += json.load(open(f, encoding="utf-8"))
    seen = set()
    for r in recs:
        for t in ((r.get("attrs") or {}).get("tradeTags") or []):
            if isinstance(t, str) and t.strip():
                seen.add(t.strip())
    missing = sorted(seen - set(tags))
    if missing:
        fails.append(f"{len(missing)} trade tags have no lexicon entry, e.g. {missing[:5]}")

    for t, e in tags.items():
        if e.get("gloss") and e.get("glossVia") not in GLOSS_VIA:
            fails.append(f"{t!r}: gloss with no source ({e.get('glossVia')!r})")
        if not e.get("suspect") and e.get("reading") and re.search(r"[฀-๿]", e["reading"]):
            fails.append(f"{t!r}: reading still carries Thai — {e['reading']!r}")

    admin = json.load(open(os.path.join(ROOT, "data", "curated", "admin_areas.json"),
                           encoding="utf-8")).get("areas") or {}
    for pv in admin.values():
        for kind in ("amphoe", "tambon"):
            for name in (pv.get(kind) or {}):
                if name not in areas:
                    fails.append(f"area {name!r} has no reading")

    # 2. on the built pages: a suspect reading must not print
    pages = glob.glob(os.path.join(ROOT, "docs", "*", "p", "*.html"))
    if pages:
        random.seed(9)
        sample = random.sample(pages, min(1500, len(pages)))
        rows = 0
        for p in sample:
            t = open(p, encoding="utf-8", errors="replace").read()
            if "Listed as doing" in t:
                rows += 1
                # only the tag row — a NAME's reading elsewhere on the page is
                # name_bi()'s business, and may coincide with a tag's letters
                dd = re.search(r'Listed as doing</span></span></dt><dd>(.*?)</dd>', t, re.S)
                seg = dd.group(1) if dd else ""
                for th, rd in re.findall(r'<span class="th solo" lang="th">([^<]+)</span> '
                                         r'<span class="en roman" lang="en">([^<]+)</span>', seg):
                    if (tags.get(html.unescape(th)) or {}).get("suspect"):
                        fails.append(f"{os.path.relpath(p, ROOT)} prints a suspect reading "
                                     f"{rd!r} for {th!r}")
                        break
        print(f"pages sampled: {len(sample):,} · with a trade-tag row: {rows:,}")
    c = doc.get("counts") or {}
    print(f"tags {c.get('tags')} · glossed {c.get('tagsWithGloss')} · suspect {c.get('tagsSuspect')} "
          f"· areas {c.get('areas')}")
    if fails:
        print("\n".join(fails[:30]))
        print(f"FAIL: {len(fails)}")
        return 1
    print("OK: lexicon whole; suspect readings stay off the page")
    return 0


if __name__ == "__main__":
    sys.exit(main())
