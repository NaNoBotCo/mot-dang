#!/usr/bin/env python3
"""Diff a list of venue names against the canonical catalog. Zero network.

The web-list reconciliation method, made repeatable: the coworking sweep of
2026-08-07 diffed one Thai listicle (northspace.life) against the coworking
shelf by hand and found five venues no crawl carries (StarWork, Life Space,
Yellow, P.Work, Code Space) plus six shelved out of sight. This script is that
diff as a tool — paste any dated list of names into a text file, run it, and
read which names the catalog holds (and on which shelves) and which it lacks.

Usage:
  python3 importers/reconcile_names.py names.txt            # both provinces
  python3 importers/reconcile_names.py names.txt --prov cm

names.txt: one venue per line; blank lines and # comments skipped. Thai or
English or both ("StarWork สตาร์เวิร์ค" on one line is fine — every token is
tried). Absent names are LEADS: verify each against its own source, then hand
it a record in data/curated/additions-*.json with the source dated. Nothing
goes into the catalog from this report directly.

Matching is containment over normalized names (lowercased, spaces and
punctuation stripped), then token overlap as a fallback — generous on purpose:
a false PRESENT is easy to spot in the printed shelf, a false ABSENT sends you
hand-writing a record that already exists.
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STOP = {"the", "cafe", "coffee", "chiangmai", "chiang", "mai", "rai", "chiangrai",
        "shop", "restaurant", "hotel", "co", "and", "เชียงใหม่", "เชียงราย", "ร้าน"}


def squash(s):
    s = unicodedata.normalize("NFC", str(s or "")).lower()
    return re.sub(r"[^a-z0-9ก-๙]+", "", s)


def tokens(s):
    s = unicodedata.normalize("NFC", str(s or "")).lower()
    return {t for t in re.split(r"[^a-z0-9ก-๙]+", s) if len(t) >= 3 and t not in STOP}


def norm(x):
    return x if isinstance(x, list) else ([] if x is None else [x])


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    provs = ["cm", "cr"]
    if "--prov" in sys.argv:
        provs = [sys.argv[sys.argv.index("--prov") + 1]]
    if not args:
        raise SystemExit(__doc__)
    wanted = [ln.strip() for ln in Path(args[0]).read_text().splitlines()
              if ln.strip() and not ln.strip().startswith("#")]
    places = []
    for p in provs:
        places += json.loads((ROOT / "data" / "canonical" / f"{p}.json").read_text())
    index = []
    for p in places:
        names = [p.get(k) for k in ("name", "nameTh", "nameEn") if p.get(k)]
        index.append((p, [squash(n) for n in names], set().union(*(tokens(n) for n in names))))

    absent = []
    for w in wanted:
        wsq, wtok = squash(w), tokens(w)
        hits = []
        for p, sqs, toks in index:
            if any(wsq and (wsq in s or s in wsq) for s in sqs if len(s) >= 6):
                hits.append((p, "name"))
            elif wtok and len(wtok & toks) >= (len(wtok) if len(wtok) <= 2 else len(wtok) - 1):
                hits.append((p, f"tokens:{'/'.join(sorted(wtok & toks))}"))
        if hits:
            for p, how in hits[:3]:
                shelves = "/".join(sorted(set(norm(p.get("cat")) + norm(p.get("sub")))))
                print(f"PRESENT  {w[:36]:38} = {str(p.get('name'))[:34]:36} [{p['id']}] {shelves}  ({how})")
        else:
            absent.append(w)
            print(f"ABSENT   {w[:36]}")
    print(f"\n{len(wanted) - len(absent)} matched lines, {len(absent)} absent")
    if absent:
        print("absent names are leads — verify against the source, then curate into "
              "data/curated/additions-*.json with the source dated")


if __name__ == "__main__":
    main()
