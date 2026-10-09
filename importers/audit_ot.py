#!/usr/bin/env python3
"""What the corpus says about occupational therapy, counted — WO-55.

The question people bring — a child whose development is slow, an adult
relearning a hand or a kitchen after a stroke, an elder whose memory is
going — and what the catalogue actually held when somebody counted,
2026-09-04, 21,047 records in both provinces:

  กิจกรรมบำบัด 0 · occupational 0 · physio names 3 · physio shelf 0 rows
  (no OSM element in CM or CR carries healthcare=physiotherapist, so the
  physio child of the medical tree has never been built, and a link to it
  on /longcare.html was a 404 on a live page for a fortnight).

This file owns the audit, one copy (the audit_longcare arrangement):
  OT_NAME_RX          a name that states occupational therapy itself
  the register check  data/curated/ot.json — every row graded, every
                      stated row sourced, every placeId resolving
  the census          the silences, re-counted against canonical so the
                      page's own sentence (ot_layer.py counts live) and
                      this audit cannot drift

Run:  python3 importers/audit_ot.py          (exit 1 on a broken register)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Same regex as specialty.py's "ot" key. Bare OT is never a rule — it is a
# substring of hotel and a synonym for overtime; "OT clinic" is how one
# Chiang Mai clinic spells itself on its sign.
OT_NAME_RX = re.compile(r"กิจกรรมบำบัด|\boccupational\s+therap|\bOT\s+clinic\b|โอที\s*คลินิก", re.I)
GRADES = {"stated", "listed", "route"}


def names_of(r):
    return " ".join(str(v) for v in
                    (r.get("name"), r.get("nameTh"), r.get("nameEn")) if v)


def main():
    recs = []
    for prov in ("cm", "cr"):
        for r in json.loads((ROOT / "data" / "canonical" / f"{prov}.json").read_text()):
            recs.append((prov, r))
    by_id = {r["id"]: (p, r) for p, r in recs}
    bad = 0

    print(f"== 1 · the name scan — {len(recs):,} records ==")
    hits = [(p, r) for p, r in recs if OT_NAME_RX.search(names_of(r))]
    crawled = [(p, r) for p, r in hits if not r["id"].startswith((f"{p}-curated",))]
    print(f"   {len(hits)} record(s) state occupational therapy in their own name, "
          f"{len(crawled)} of them from a crawl (the rest are curated additions)")
    for p, r in hits:
        spec = (r.get("attrs", {}).get("specialty") or [])
        print(f"   {p} | specialty={','.join(spec) or '—'} | {names_of(r)[:60]} | {r['id']}")

    print("\n== 2 · the specialty field ==")
    spec_rows = [(p, r) for p, r in recs
                 if "ot" in (r.get("attrs", {}).get("specialty") or [])]
    print(f"   {len(spec_rows)} record(s) carry specialty ot")
    for p, r in hits:
        if (p, r) not in spec_rows:
            print(f"   NAME SAYS OT BUT NO SPECIALTY: {names_of(r)[:60]} | {r['id']} — "
                  "specialty.py's ot rule is not running over this record")
            bad = 1

    print("\n== 3 · the physio shelf (facilityType=physio) ==")
    shelf = [(p, r) for p, r in recs
             if r.get("attrs", {}).get("facilityType") == "physio"]
    print(f"   {len(shelf)} record(s) stand on medical/physio "
          f"({'the child is hidden and any link to it is a 404' if not shelf else 'the child builds'})")

    print("\n== 4 · the register — data/curated/ot.json ==")
    reg = json.loads((ROOT / "data" / "curated" / "ot.json").read_text())
    rows = reg.get("rows") or []
    grades = {}
    for row in rows:
        g = row.get("grade")
        grades[g or "?"] = grades.get(g or "?", 0) + 1
        if g not in GRADES:
            print(f"   row {row.get('key')} carries grade {g!r} — the grade is the "
                  f"point and must be one of {sorted(GRADES)}")
            bad = 1
        for pid in row.get("placeIds") or []:
            if pid not in by_id:
                print(f"   UNRESOLVED place id {pid} in row {row.get('key')} — "
                      "a page row silently missing (run import_all.py?)")
                bad = 1
        if g in ("stated", "listed") and not (row.get("src") and row.get("evidence")):
            print(f"   row {row.get('key')} is graded {g} with no src+evidence — "
                  "a stated or listed row quotes where it was read")
            bad = 1
        if not row.get("fetched"):
            print(f"   row {row.get('key')} carries no fetched date")
            bad = 1
        if not row.get("for"):
            print(f"   row {row.get('key')} says who it is for: nobody — add child/adult")
            bad = 1
    print(f"   {len(rows)} row(s): " +
          " · ".join(f"{k} {v}" for k, v in sorted(grades.items())))
    for x in reg.get("registers") or []:
        if not (x.get("url") and x.get("fetched")):
            print(f"   register {x.get('key')} lacks url or fetched date")
            bad = 1

    print("\n== 5 · the census of silences (what no record says) ==")
    for label, rx in [
            ("กิจกรรมบำบัด / occupational (crawled names only)", OT_NAME_RX),
            ("กายภาพบำบัด / physiotherap", re.compile(r"กายภาพบำบัด|physiotherap|physical therap", re.I)),
            ("เวชกรรมฟื้นฟู / เวชศาสตร์ฟื้นฟู / rehabilitation medicine",
             re.compile(r"เวชกรรมฟื้นฟู|เวชศาสตร์ฟื้นฟู|rehabilitation medicine", re.I)),
            ("พัฒนาการเด็ก / child development", re.compile(r"พัฒนาการเด็ก|child development", re.I)),
            ("ออทิสติก / autis", re.compile(r"ออทิส|autis", re.I)),
            ("อรรถบำบัด / speech therap", re.compile(r"อรรถบำบัด|แก้ไขการพูด|speech therap", re.I)),
            ("กายอุปกรณ์ / prosthe", re.compile(r"กายอุปกรณ์|prosthe|orthotic", re.I)),
    ]:
        n = sum(1 for p, r in recs
                if rx.search(names_of(r)) and not r["id"].startswith(f"{p}-curated"))
        print(f"   {label}: {n}")

    sys.exit(bad)


if __name__ == "__main__":
    main()
