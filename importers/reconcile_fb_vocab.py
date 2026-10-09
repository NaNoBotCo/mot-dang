#!/usr/bin/env python3
"""reconcile_fb_vocab.py — grow the query vocabulary from what this city's
businesses actually call themselves. Stdlib, no network.

Nan, 2026-09-06: "identifying what potential information sources exist and
growing/scaling around them. In perpetuity." A vocabulary we wrote by hand is a
guess about Chiang Mai. The vocabulary a business picks for its own page is not.
Every page facebook-reader reads carries attrs.fbCategories; this folds the ones
that are new into data/curated/fb_vocabulary.json, with the date and the count
of pages in these two provinces that chose it. Those words then generate their
own queries on the next sweep, which finds more pages, which grow the
vocabulary — the loop that makes the lane finish rather than plateau.

A word enters only if at least --min pages (default 2) chose it, so one shop's
odd self-description does not spend 44 queries. Nothing is ever removed: a word
that stops being used keeps its last_seen date, so nobody re-adds it.

    python3 importers/reconcile_fb_vocab.py [--min 2] [--dry-run]
"""
import argparse
import collections
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VOCAB = ROOT / "data" / "curated" / "fb_vocabulary.json"
ADDS = [ROOT / "data" / "curated" / f"additions-chiang-{x}.json" for x in ("mai", "rai")]


def harvested():
    seen = collections.Counter()
    for f in ADDS:
        if not f.exists():
            continue
        for r in json.loads(f.read_text(encoding="utf-8")):
            for c in ((r.get("attrs") or {}).get("fbCategories") or []):
                c = str(c).strip()
                if c:
                    seen[c] += 1
    return seen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min", type=int, default=2)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    doc = json.loads(VOCAB.read_text(encoding="utf-8"))
    words = doc["tier2_words"]
    have = {w["w"] for w in words}
    today = dt.date.today().isoformat()
    counts = harvested()
    added = []
    for w, n in counts.most_common():
        if w in have:
            for row in words:
                if row["w"] == w:
                    row["pages"] = n
                    row["last_seen"] = today
            continue
        if n < a.min:
            continue
        added.append({"w": w, "group": "harvested", "pages": n, "last_seen": today,
                      "lang": "th" if any("฀" <= c <= "๿" for c in w) else "en",
                      "from": f"fbCategories on {n} pages read, {today}"})
    if added and not a.dry_run:
        words.extend(added)
        doc["counts"]["tier2_seed"] = len(words)
        doc["_built"] = today
        VOCAB.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(counts)} distinct fbCategories on pages read; {len(added)} new word(s) "
          f"{'would be' if a.dry_run else ''} added; vocabulary now {len(words)}")
    for w in added:
        print("  +", w["w"], f"({w['pages']} pages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
