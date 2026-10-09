#!/usr/bin/env python3
"""What the search index no longer says out loud — 2026-09-10.

Nan, from River Tavern in Chiang Rai: rows announced "Phone number held ·
Facebook page held" beside the phone number itself, "A thin entry" beside a
row that was visibly short, and the place she was sitting in could not be
found with its city attached. Three contracts, checked against the built
index rather than against the code:

  * no row's `t` points at a tag of the `state` family (records management,
    never a chip);
  * a held record (build.held(): no pin, two facts or fewer) IS in the index,
    marked `hd`, carrying no keyword blob;
  * every row carries its province code, which is what the page turns into
    the province words at index time.

Skips, with the reason, when docs/ has not been built.

    python3 tests/test_index_silence.py
"""
import json
import os
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.environ.get("MD_DOCS", os.path.join(ROOT, "docs"))


def main():
    idx_path = os.path.join(DOCS, "data", "index.json")
    tab_path = os.path.join(DOCS, "data", "search_tables.json")
    if not (os.path.exists(idx_path) and os.path.exists(tab_path)):
        print(f"SKIPPED — {idx_path} not built")
        return 0
    rows = json.load(open(idx_path, encoding="utf-8"))
    tables = json.load(open(tab_path, encoding="utf-8"))
    tags = json.load(open(os.path.join(ROOT, "data", "tags.json"), encoding="utf-8"))
    state = {t["slug"] for t in tags["tags"] if t.get("family") == "state"}
    state_ids = {i for i, row in enumerate(tables["tags"]) if row[0] in state}
    bad = 0

    def check(label, ok, why=""):
        nonlocal bad
        print(("  ✓ " if ok else "  ✗ ") + label + ("" if ok else why))
        bad += 0 if ok else 1

    loud = [r["id"] for r in rows if any(i in state_ids for i in (r.get("t") or []))]
    check("no row carries a state-family tag in `t`", not loud,
          f" — {len(loud):,} rows do, e.g. {loud[:3]}")
    held = [r for r in rows if r.get("hd")]
    check("held records are in the index, marked hd", len(held) >= 1,
          " — none; build.held() rows are still being kept out")
    check("a held row carries no keyword blob",
          all("k" not in r for r in held), f" — {sum(1 for r in held if 'k' in r)} do")
    # data/coverage.json: the 17 northern provinces (Nan 2026-09-29)
    keys = {p["key"] for p in json.loads(
        (Path(__file__).resolve().parent.parent / "data" / "coverage.json").read_text())["provinces"]}
    check("every row carries its province code",
          all(r.get("p") in keys for r in rows),
          f" — {sum(1 for r in rows if r.get('p') not in keys):,} rows do not")
    rt = next((r for r in rows if r["id"] == "cr-curated-river-tavern"), None)
    check("River Tavern (cr-curated-river-tavern) is in the index", rt is not None)
    print(f"  {len(rows):,} rows · {len(held):,} held · {len(state):,} state tags kept out")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
