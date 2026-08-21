#!/usr/bin/env python3
"""What the corpus says about ADHD, counted — WO-31.

Report only, no --emit: there is nothing to emit, and that is the finding.
The beauty audit's lesson (importers/audit_beauty.py) was that a shelf can lie
because nobody read the Thai names; this audit reads them, and here the names
genuinely say nothing. The reports keep the hole visible so it cannot be
mistaken for coverage, and check that the curated register standing in for the
corpus stays sound:

  1. the ADHD name scan  — every record whose name matches ADHD_NAME_RX
                           (imported from adhd_layer so this report and the
                           page's own sentence cannot drift apart)
  2. the psychiatry scan — the wider door: จิตเวช / จิตแพทย์ / พัฒนาการเด็ก.
                           This is the number that shows the care is not
                           absent, only unnamed
  3. the register        — every row in data/curated/adhd.json resolved
                           against canonical; an unresolvable place id here is
                           a page row silently missing, so it exits 1
  4. the molecules       — every molecule row carries a class, a carry rule
                           and at least one dated source. A legal claim with
                           no source is the one thing this page must never
                           ship, so a bare row exits 1
  5. the duplicate watch — register place ids whose name appears on more than
                           one record, the pairs a person still has to judge
                           (they are also in adhd.json unverified[])

Run:  python3 importers/audit_adhd.py
"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location(
    "_adhd_layer", str(ROOT / "adhd_layer.py"))
_layer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_layer)
ADHD_NAME_RX = _layer.ADHD_NAME_RX
PSYCH_NAME_RX = _layer.PSYCH_NAME_RX


def names_of(r):
    return " ".join(str(v) for v in
                    (r.get("name"), r.get("nameTh"), r.get("nameEn")) if v)


def main():
    recs = []
    for prov in ("cm", "cr"):
        for r in json.loads((ROOT / "data" / "canonical" / f"{prov}.json").read_text()):
            recs.append((prov, r))
    by_id = {r["id"]: (p, r) for p, r in recs}
    reg = json.loads((ROOT / "data" / "curated" / "adhd.json").read_text())
    bad = 0

    print(f"== 1 · the ADHD name scan — {len(recs):,} records ==")
    hits = [(p, r) for p, r in recs if ADHD_NAME_RX.search(names_of(r))]
    print(f"   {len(hits)} record(s) name this care in their own sign")
    for p, r in hits:
        print(f"   {p} | {names_of(r)[:64]} | {r['id']}")
    if not hits:
        print("   0 of them — the register is the coverage, and this line is "
              "the reason it exists")

    print(f"\n== 2 · the wider psychiatric door ==")
    psych = [(p, r) for p, r in recs if PSYCH_NAME_RX.search(names_of(r))]
    print(f"   {len(psych)} record(s) name psychiatry or child development at all")
    for p, r in psych:
        print(f"   {p} | {names_of(r)[:70]} | {r['id']}")
    print("   The care is not absent — the names simply do not say it, because")
    print("   clinics here are named after their doctors (importers/specialty.py).")

    print(f"\n== 3 · the register — data/curated/adhd.json ==")
    rows = reg.get("rows") or []
    print(f"   {len(rows)} row(s)")
    grades = {}
    for row in rows:
        grades[row.get("grade")] = grades.get(row.get("grade"), 0) + 1
        pid = row.get("place")
        if pid and pid not in by_id:
            print(f"   MISSING  {row.get('key')} → {pid} not in canonical")
            bad += 1
        elif pid:
            p, r = by_id[pid]
            print(f"   ok  {row.get('grade'):10s} {row.get('key'):18s} "
                  f"{names_of(r)[:44]}")
        else:
            print(f"   ok  {row.get('grade'):10s} {row.get('key'):18s} (no place id)")
    print("   grades: " + " · ".join(f"{k}={v}" for k, v in sorted(grades.items())))

    print(f"\n== 4 · the molecules — every legal claim carries a source ==")
    for m in reg.get("molecules") or []:
        srcs = m.get("sources") or []
        ok = bool(m.get("class_th") and m.get("carry") and srcs)
        print(f"   {'ok ' if ok else 'BAD'} {m.get('key'):16s} "
              f"{m.get('class_en', ''):48s} {len(srcs)} source(s)")
        if not ok:
            bad += 1
    if not bad:
        print("   every molecule row states its class, its carry rule and where "
              "it was read")

    print(f"\n== 5 · the duplicate watch ==")
    by_name = {}
    for p, r in recs:
        by_name.setdefault(names_of(r).strip(), []).append(r["id"])
    dupes = 0
    for row in rows:
        pid = row.get("place")
        if not (pid and pid in by_id):
            continue
        _, r = by_id[pid]
        ids = by_name.get(names_of(r).strip(), [])
        if len(ids) > 1:
            print(f"   {row.get('key')}: name appears on {len(ids)} records → {ids}")
            dupes += 1
    # Known and filed: the Suan Prung MOPH record and its OSM twin.
    twins = [i for n, i in by_name.items() if "สวนปรุง" in n for i in [i]]
    flat = [x for gr in twins for x in gr]
    if len(flat) > 1:
        print(f"   สวนปรุง appears on {len(flat)} records → {flat}")
        print("   (filed in adhd.json unverified[] as a merge pair for "
              "data/curated/merges.json)")
        dupes += 1
    if not dupes:
        print("   none")

    print(f"\n== leads still open ==")
    for u in reg.get("unverified") or []:
        print(f"   · {u}")

    if bad:
        print(f"\n{bad} problem(s) — fix before building.")
        return 1
    print("\nclean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
