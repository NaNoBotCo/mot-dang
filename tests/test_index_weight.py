#!/usr/bin/env python3
"""The search index's relations resolve to real rows. It reports its weight.

WHAT THIS USED TO BE, AND WHY IT IS NOT THAT ANY MORE
-----------------------------------------------------
Until 2026-09-08 this file failed a build when index.json passed 10,000,000
bytes. Nan, asked where that number came from: *"the 10 mb ceiling is a
hallucination that needs nuked."* She is right, and the file's own docstring
proved it — the number was the index's size on the afternoon of 2026-09-07
plus the cost of that day's change, rounded up. A ceiling derived from what
the file happened to weigh on Sunday is a ratchet against Sunday, not a
judgment about what a reader can afford, and nobody ever asked her.

It was also, by then, measuring nothing: she approved the Overture fold and
the catalogue went 25,914 -> 88,161 records, so the gate failed on a change
she had already said yes to.

The real cost is not a raw byte count on one file. It is what a phone fetches
before it can show the first character of an answer — 1.5 MB gzipped today —
and Nan's word on that, the same day: *"1.5 mb before an answer is a problem
that needs fixed."* That is a work order, not a tripwire, and it is not this
file's job. This file now REPORTS weight and never fails on it.

WHAT IT STILL FAILS ON, WHICH IS CORRECTNESS AND NOT TASTE
-----------------------------------------------------------
WO-69 put five relations on an index row — `t` tags, `tt` trade tags, `st`
street, `ar` district, `hk` opening schedule — every one an INT into
docs/data/search_tables.json. An int that points outside its table is a chip
that renders as nothing or as the wrong place's name, and no reader could
ever tell. Those checks stay, and so does the check that the unread `h`
string has not crept back.

    MD_DOCS=/path/to/scratch python3 tests/test_index_weight.py
"""
import json
import os
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = Path(os.environ.get("MD_DOCS") or (ROOT / "docs"))


def gz(path):
    """What the reader's phone actually pulls down, not what the disk holds."""
    return len(zlib.compress(path.read_bytes(), 6))

# No ceilings here. Both numbers that used to live on these two lines were
# "what it weighed the day someone wrote this, rounded up" — see the docstring.


def main():
    idx_p, tab_p = DOCS / "data" / "index.json", DOCS / "data" / "search_tables.json"
    if not idx_p.exists():
        print(f"no built index at {idx_p} — build first, or point MD_DOCS at a scratch build")
        return 0
    bad = []
    # Reported, never judged. What a reader actually pays is the gzipped size
    # of everything search.html must have before it can answer, which is a
    # question about the whole door and not about this one file.
    n_idx = idx_p.stat().st_size
    print(f"data/index.json         {n_idx:>10,} bytes raw  "
          f"({gz(idx_p):>9,} gzipped)")
    if not tab_p.exists():
        bad.append("data/search_tables.json missing")
        tab = {}
    else:
        print(f"data/search_tables.json {tab_p.stat().st_size:>10,} bytes raw  "
              f"({gz(tab_p):>9,} gzipped)")
        tab = json.loads(tab_p.read_text())
    rows = json.loads(idx_p.read_text())
    counts = {k: sum(1 for e in rows if k in e) for k in ("t", "tt", "st", "ar", "hk", "h")}
    print("rows carrying:", ", ".join(f"{k} {v:,}" for k, v in counts.items()))
    if counts["h"]:
        bad.append(f"{counts['h']} rows still carry the unread `h` string")
    if not counts["t"] or not counts["st"] or not counts["hk"]:
        bad.append("a relation field is empty on every row — the tables did not reach the index")
    hours = tab.get("hours") or []
    for e in rows:
        if "hk" in e and not (0 <= e["hk"] < len(hours)):
            bad.append(f"{e['id']}: hk={e['hk']} resolves to no schedule"); break
        for k, tname in (("t", "tags"), ("tt", "trade"), ("st", "streets"), ("ar", "areas")):
            v = e.get(k)
            if v is None:
                continue
            vs = v if isinstance(v, list) else [v]
            n = len(tab.get(tname) or [])
            if any(not (0 <= i < n) for i in vs):
                bad.append(f"{e['id']}: {k}={v} points outside {tname} ({n})"); break
    # every pinned row has at least two things a chip can be made of: its
    # shelf, and a street / district / (on the client) a landmark within
    # 1.5 km — the last is computed at render, so here the floor is the shelf
    pinned = [e for e in rows if e.get("lat") is not None]
    no_shelf = sum(1 for e in pinned if not (e.get("su") or e.get("c")))
    print(f"pinned rows {len(pinned):,}, without any shelf {no_shelf:,}")
    if no_shelf:
        bad.append(f"{no_shelf} pinned rows have neither su nor c")
    for b in bad:
        print("  !", b)
    print("PASS" if not bad else f"FAIL ({len(bad)})")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
