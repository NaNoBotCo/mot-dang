#!/usr/bin/env python3
"""Every record's `updatedAt` is a Gregorian date a record could actually
carry. Zero network.

The bug this file exists for: found 2026-09-08 while measuring record
freshness. Four Chiang Mai pharmacies were stamped with a Buddhist-Era year
in a Gregorian field — 2560-12-12, 2306-01-13, 2299-04-28 — because the FDA
retail-licence fold copied the register's `appdate` column through verbatim.
The register is nominally CE and 24,700 of its rows are, so the exceptions
never showed up in the aggregate; they showed up as a shop last updated 534
years from now. import_opendata._ce_date() reads them now.

    CATALOGUE   no record in cm.json or cr.json carries a year outside
                1990..this year. Not "must be 2026": 2,745 records legitimately
                carry a pre-2026 date, an OSM last-edit timestamp, and the
                oldest honest one in the catalogue is 2003.
    DECODER     the three shifts _ce_date reads, and the refusal that matters
                more — a value no shift can land in a livable year returns
                None and takes the blank-date path, rather than being guessed
                from the licence number.

The two floors differ on purpose. _ce_date works to 1900 because that is what
makes a shift decodable — the register holds genuine 1974 licence dates. The
catalogue floor is 1990 because that is what a record's date can sanely be.

    python3 tests/test_updated_at.py
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "importers"))

import import_opendata  # noqa: E402

FLOOR = 1990
CEILING = date.today().year
ISO = re.compile(r"\d{4}-\d{2}-\d{2}$")

failures = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}{'' if ok else ' — ' + str(detail)}")
    if not ok:
        failures.append(label)


print(f"the catalogue — every updatedAt in {FLOOR}..{CEILING}")
for prov in ("cm", "cr"):
    path = ROOT / "data" / "canonical" / f"{prov}.json"
    recs = json.loads(path.read_text())
    if isinstance(recs, dict):
        recs = recs.get("records", [])

    malformed = [r["id"] for r in recs
                 if not ISO.match(str(r.get("updatedAt") or ""))][:6]
    check(f"{prov}: every record carries an ISO updatedAt",
          not malformed, malformed)

    out = [(r["id"], r["updatedAt"], r.get("name"))
           for r in recs
           if ISO.match(str(r.get("updatedAt") or ""))
           and not (FLOOR <= int(str(r["updatedAt"])[:4]) <= CEILING)]
    check(f"{prov}: no updatedAt outside {FLOOR}..{CEILING} "
          f"({len(recs)} records)", not out, out[:6])

print("_ce_date — the register's era arithmetic")
for raw, want, why in (
        ("2019-03-11", "2019-03-11", "a CE date is left alone"),
        ("1974-05-02", "1974-05-02", "…including a genuinely old licence"),
        ("2560-12-12", "2017-12-12", "B.E. left in the CE column: − 543"),
        ("2517-01-01", "1974-01-01", "…the oldest of those"),
        ("1470-01-08", "2013-01-08", "543 taken twice (licence 1/2556): + 543"),
        ("1475-01-05", "2018-01-05", "…and again (licence 2/2561)"),
        ("1464-06-07", "2007-06-07", "…and again (licence 7/2550)"),
        ("2306-01-13", None, "no shift lands it: unreadable, not guessed"),
        ("2299-04-28", None, "…nor this one"),
        ("2109-05-15", None, "…nor this one"),
        ("1484-09-30", None, "a shift into next year is not a landing"),
        ("2024-02-30", None, "31 February in the register is not a date"),
        ("", None, "a blank appdate stays blank"),
        (None, None, "a missing appdate stays missing"),
):
    got = import_opendata._ce_date(raw)
    check(f"{raw!r} -> {want!r}  ({why})", got == want, got)

print("the four records the bug was found in")
cm = json.loads((ROOT / "data" / "canonical" / "cm.json").read_text())
by_id = {r["id"]: r for r in cm}
for rid in ("cm-dgth-fda-0054492517", "cm-dgth-fda-2613789647",
            "cm-dgth-fda-3635193413", "cm-dgth-fda-3986864719"):
    r = by_id.get(rid)
    check(f"{rid} is present and dated sanely",
          r is not None and FLOOR <= int(r["updatedAt"][:4]) <= CEILING,
          r and r.get("updatedAt"))

print()
if failures:
    print(f"{len(failures)} failure(s): {failures}")
    sys.exit(1)
print("all updatedAt checks passed")
