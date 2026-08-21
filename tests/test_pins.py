#!/usr/bin/env python3
"""A pin never claims to be surer than the thing it was copied from.

    python3 tests/test_pins.py          # reads data/canonical only

WHY THIS EXISTS. WO-28 gave every monastic school the coordinates of the
temple the register says it stands in — a far better pin than a district
centroid, and the right thing to do. The first cut then stamped all of them
"±150 m", the width of a temple compound, which is true about the SCHOOL'S
POSITION INSIDE THE TEMPLE and says nothing about where the temple is. วัดโขงขาว
is itself placed by postcode centroid at ±12,523 m, so its school would have
published a twelve-kilometre guess as a hundred-and-fifty-metre fact.

That is the whole class of error worth a gate: a borrowed pin inherits the
lender's error bar, and the borrower's own precision is a FLOOR on top of it,
never a replacement for it. Nothing else on this site can catch it — the
number looks perfectly reasonable on the page, and it is wrong by two orders
of magnitude.

THREE CHECKS
1. Every record that borrows a pin (`attrs.watId`, and any future borrower
   listed in BORROW_KEYS) states an uncertainty at least as large as the
   record it borrowed from.
2. No record claims `geoPrecision: exact` while also naming a pinVia — a
   surveyed pin is not derived from anything.
3. Every approx pin carries a number — ADVISORY. An approximate pin with no
   error bar is the same lie in a quieter voice, but the ones on file are
   hand-placed curated records where a person put the dot there on purpose,
   and restating somebody's field truth as a number they did not choose would
   be the worse error. Those are reported and counted, never failed on.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
# attrs key -> the id of the record this pin was taken from.
BORROW_KEYS = ("watId",)
# What a precision level is worth in metres when the lender states no number.
# `block` is a building outline: build.PLACE_MAP_SPAN draws it at a 120 m
# radius, so that is what it means here too.
FLOOR = {"exact": 0, "block": 120}


def main():
    recs = []
    for prov in ("cm", "cr"):
        p = ROOT / "data" / "canonical" / f"{prov}.json"
        if p.exists():
            recs += json.loads(p.read_text())
    if not recs:
        print("no canonical data — run importers/import_all.py first")
        return 1
    by_id = {r["id"]: r for r in recs}
    bad, warn = [], []
    borrowed = approx = 0

    for r in recs:
        a = r.get("attrs") or {}
        prec = r.get("geoPrecision") or "exact"
        try:
            unc = int(a.get("pinUncertaintyM") or 0)
        except (TypeError, ValueError):
            unc = 0
            if a.get("pinUncertaintyM"):
                bad.append(f"{r['id']}: pinUncertaintyM is not a number "
                           f"({a['pinUncertaintyM']!r})")
        if prec == "approx":
            approx += 1
            if not unc:
                warn.append(f"{r['id']}: approx pin with no uncertainty stated")
        if prec == "exact" and a.get("pinVia"):
            bad.append(f"{r['id']}: claims an exact pin but names a pinVia "
                       f"({a['pinVia']!r}) — a surveyed pin is derived from nothing")
        for key in BORROW_KEYS:
            lender_id = a.get(key)
            if not lender_id:
                continue
            lender = by_id.get(lender_id)
            if not lender:
                continue                       # the link is checked elsewhere
            if r.get("lat") is None:
                continue                       # nothing borrowed after all
            borrowed += 1
            la = lender.get("attrs") or {}
            try:
                lend_unc = int(la.get("pinUncertaintyM") or 0)
            except (TypeError, ValueError):
                lend_unc = 0
            if not lend_unc:
                lend_unc = FLOOR.get(lender.get("geoPrecision") or "exact", 0)
            if unc < lend_unc:
                bad.append(
                    f"{r['id']} borrows its pin from {lender_id} "
                    f"({lender.get('geoPrecision')}, ±{lend_unc} m) but claims "
                    f"±{unc} m — a borrowed pin cannot be surer than its lender")

    print(f"records            {len(recs):,}")
    print(f"approximate pins   {approx:,}")
    print(f"borrowed pins      {borrowed:,}")
    if warn:
        print(f"advisory           {len(warn)} approx pin(s) state no error bar "
              f"(hand-placed curated records — a person chose the dot)")
        for m in warn[:5]:
            print("    ·", m)
    for m in bad[:20]:
        print("  !", m)
    if len(bad) > 20:
        print(f"  ... and {len(bad) - 20} more")
    print("PASS" if not bad else f"FAIL ({len(bad)})")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
