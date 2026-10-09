#!/usr/bin/env python3
"""🧾 Backfill per-field provenance onto the canonical corpus.

    python3 importers/backfill_provenance.py           # stage + report, writes nothing
    python3 importers/backfill_provenance.py --write    # apply to data/canonical/*.json

WHAT IT CAN HONESTLY WORK OUT, AND WHAT IT REFUSES TO
-----------------------------------------------------
94% of the corpus — 22,652 of 24,059 records — carries exactly ONE source.
For those, provenance is not a guess: every field on the record came from that
source, because there was nowhere else for it to come from. That single fact
does most of the job in one pass.

The other 1,407 records carry two or more sources, and for those this script
fills in only what a MARKER already settles — the pin, which has carried
`attrs.pinSource` and `attrs.pinVia` since the curated overlay existed — and
leaves every remaining field UNKNOWN.

It leaves them unknown on purpose. A rule like "the phone probably came from
the register" would be right most of the time, and provenance that is right
most of the time is worse than none: it reads as a receipt, it will be
uploaded to OpenStreetMap on the strength of looking like one, and the day it
is wrong there is no way to tell which one it was. 9,284 fields sit on those
1,407 records and every one of them is either hand-checkable or re-importable
with `provenance.stamp()` called at the moment the value lands. Both of those
are cheap. Inventing the answer is not.

GRADES, APPLIED
---------------
`stated` for what a source printed. `derived` for cat/sub/tags always — a
shelf is our reading of a name, never a thing the source said, and OSM must
never receive our classification as though it were a survey. `inferred` for a
coordinate that came through the curated pin overlay, which the overlay itself
already says is approximate.

THE POINT OF THE REPORT
-----------------------
The last section prints how many fields became giveable to OpenStreetMap. That
number is the reason this exists, and printing it every run is what keeps the
next change honest — a refactor that quietly halves it will say so.
"""

import argparse
import json
import pathlib
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import provenance as P  # noqa: E402  — the one grammar, imported not restated

CANON = ROOT / "data" / "canonical"
STAGE = ROOT / "_incoming" / "provenance-backfill-2026-09-05.json"

# Our classification, never the source's words. Held apart from the loop
# because the reason is a rule and not a detail: OSM receiving `sub` as
# `stated` would be us telling a surveyor that a register called a shop a
# massage parlour, when what happened is that we read its name.
OUR_READING = ("cat", "sub", "tags")


def backfill_record(r):
    """Provenance entries for one record. Returns {field: entry}, possibly {}."""
    srcs = r.get("sources") or []
    if not srcs:
        return {}
    out = {}
    attrs = r.get("attrs") or {}

    # ---- the pin, whatever else is true. It is the one field that already
    # carries its own receipt, and that receipt outranks the single-source
    # shortcut below: a record can hold one source and still have been pinned
    # by the overlay afterwards.
    if attrs.get("pinSource") == "curated-pins" and r.get("lat") is not None:
        pin_src = next((s for s in srcs
                        if (s.get("via") or "") == attrs.get("pinVia")
                        or (s.get("ref") or "") == attrs.get("pinFrom")), None)
        key = P.source_key(pin_src) if pin_src else f"derived:{attrs.get('pinVia') or 'curated-pins'}"
        for f in ("lat", "lng"):
            out[f] = {"source": key, "how": P.INFERRED}

    # ---- the single-source shortcut, which is not a shortcut but a proof
    if len(srcs) == 1:
        src = srcs[0]
        key = P.source_key(src)
        at = (src.get("fetched") or "").strip()
        for f in P.TRACKED:
            if f in out:
                continue
            if r.get(f) in (None, "", [], {}):
                continue
            how = P.DERIVED if f in OUR_READING else P.STATED
            # A coordinate the record itself calls approximate is not stated,
            # whoever gave it to us. geoPrecision is the record's own word for
            # this and it is already load-bearing elsewhere in the build.
            if f in ("lat", "lng") and (r.get("geoPrecision") or "exact") != "exact":
                how = P.INFERRED
            e = {"source": key, "how": how}
            if at:
                e["at"] = at
            out[f] = e

    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true",
                    help="apply to data/canonical/*.json (default: stage only)")
    args = ap.parse_args()

    staged = {}
    grades = Counter()
    per_prov = Counter()
    give_before = give_after = 0
    waiting = 0
    unaccounted = Counter()
    touched = 0
    files = {}

    for pkey in ("cm", "cr"):
        path = CANON / f"{pkey}.json"
        recs = json.loads(path.read_text())
        files[pkey] = (path, recs)
        for r in recs:
            give_before += len(P.giveable_fields(r))
            new = backfill_record(r)
            if not new:
                continue
            table = r.setdefault("provenance", {})
            added = {f: e for f, e in new.items() if f not in table}
            if not added:
                continue
            table.update(added)
            staged[r["id"]] = added
            touched += 1
            per_prov[pkey] += len(added)
            for e in added.values():
                grades[e["how"]] += 1

    for pkey, (path, recs) in files.items():
        for r in recs:
            give_after += len(P.giveable_fields(r))
            waiting += len(P.waiting_on_licence(r))
            for f in P.unaccounted(r):
                unaccounted[f] += 1

    # ---- the complaints, before anything is written anywhere
    problems = []
    for _pkey, (_path, recs) in files.items():
        for r in recs:
            problems += P.validate(r)

    STAGE.parent.mkdir(exist_ok=True)
    STAGE.write_text(json.dumps(
        {"what": "per-field provenance derived from data/canonical, staged not applied",
         "records": touched, "entries": sum(per_prov.values()),
         "problems": problems[:200],
         "provenance": staged}, ensure_ascii=False, indent=1))

    print(f"records stamped     {touched:,}")
    print(f"entries written     {sum(per_prov.values()):,}   " +
          "  ".join(f"{k} {v:,}" for k, v in per_prov.items()))
    print("by grade            " + "  ".join(f"{g} {grades[g]:,}" for g in P.GRADES))
    print(f"\nfields giveable to OSM TODAY      {give_before:,} → {give_after:,}")
    print(f"fields waiting on a licence reply  {waiting:,}   "
          f"(gov registers — see go/osm-gate, go/dga-letter)")
    print("\nstill unaccounted, by field (the backlog):")
    for f, n in unaccounted.most_common(12):
        print(f"  {n:7,}  {f}")
    if problems:
        print(f"\n⚠ {len(problems)} validation complaint(s); first five:")
        for x in problems[:5]:
            print("   ", x)
    print(f"\nstaged → {STAGE.relative_to(ROOT)}")

    if args.write:
        # Refuse while a build holds the lock. build.py wipes docs/ and reads
        # data/ late; rewriting the corpus under a running build is how a site
        # ships half of one import and half of another.
        lock = ROOT / "cache" / "build.lock"
        if lock.exists():
            print(f"\n✋ cache/build.lock is present ({lock.read_text().strip()!r}) — "
                  f"NOT writing. Re-run when the build is done.")
            return 1
        if problems:
            print("\n✋ validation complaints above — NOT writing.")
            return 1
        for _pkey, (path, recs) in files.items():
            path.write_text(json.dumps(recs, ensure_ascii=False))
            print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
