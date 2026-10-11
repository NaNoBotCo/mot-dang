#!/usr/bin/env python3
"""Put back the source rows that derive.py's stamps have always named.

    python3 importers/repair_derived_sources.py           # report, writes nothing
    python3 importers/repair_derived_sources.py --write    # apply to data/canonical

THE BUG. `derive.py` reads a record's own address, writes attrs.amphoe,
attrs.tambon, attrs.postcode, attrs.road and attrs.soi, and stamps each one
`derived:address-parse`. It never wrote the matching `sources[]` entry. A
provenance key is only a key: `class_of_key()` looks it up in the record's own
sources, finds nothing, and answers UNKNOWN — which is the answer that means
"do not treat this as accounted for". So 59,719 honest receipts read as dropped
ones, and `provenance.validate()` reported every single one.

Fixed at the source in derive.py (`note_source`), which repairs nothing already
written. This is that repair, and it is the whole of it: one source row per
record that carries the stamp and not the row.

APPENDED, NEVER PREPENDED. build.py reads `sources[0]` as where the record came
from and when it was fetched. An address parse is neither.

`fetched` is taken from the stamp's own `at` where it has one, so the repair
does not claim today for work done on another day.

Idempotent: a second run finds nothing to do.
"""

import argparse
import json
import pathlib
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import provenance as P  # noqa: E402

CANON = ROOT / "data" / "canonical"
SRC_KEY = "derived:address-parse"
SRC_ROW = {"type": "derived", "via": "address-parse"}


def needs_row(record):
    """True when a stamp names the source and the record does not carry it."""
    table = record.get("provenance") or {}
    if not any(e.get("source") == SRC_KEY for e in table.values()
               if isinstance(e, dict)):
        return False
    return not any(P.source_key(s) == SRC_KEY
                   for s in (record.get("sources") or []))


def when(record):
    """The date the stamps claim, or nothing rather than a date we invented."""
    for e in (record.get("provenance") or {}).values():
        if isinstance(e, dict) and e.get("source") == SRC_KEY and e.get("at"):
            return e["at"]
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true",
                    help="apply to data/canonical/*.json (default: report only)")
    args = ap.parse_args()

    before = Counter()
    after = Counter()
    fixed = Counter()

    for pkey in ("cm", "cr"):
        path = CANON / f"{pkey}.json"
        recs = json.loads(path.read_text())

        for r in recs:
            before[len(P.validate(r)) > 0] += 1

        for r in recs:
            if not needs_row(r):
                continue
            row = dict(SRC_ROW)
            at = when(r)
            if at:
                row["fetched"] = at
            r.setdefault("sources", []).append(row)
            fixed[pkey] += 1

        for r in recs:
            after[len(P.validate(r)) > 0] += 1

        if args.write and fixed[pkey]:
            path.write_text(json.dumps(recs, ensure_ascii=False, indent=1))

    print(f"records repaired    cm {fixed['cm']:,}   cr {fixed['cr']:,}   "
          f"total {sum(fixed.values()):,}")
    print(f"records with a validation complaint   "
          f"{before[True]:,} → {after[True]:,}")
    print("written" if args.write else "nothing written (pass --write)")


if __name__ == "__main__":
    main()
