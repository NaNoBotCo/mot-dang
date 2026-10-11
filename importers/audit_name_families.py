#!/usr/bin/env python3
"""ชื่อพ้องคนละสคริปต์ — the spelling-union review pass. Zero network.

Prints, for a shelf (default the housing one), every pair of romanised name
tokens that a loose test would join and a person has not yet ruled on in
data/curated/name_families.json. Nothing is written to canonical, ever: this
is the same shape as audit_beauty.py and the condo register's near-miss file —
the machine proposes, a person settles.

    python3 importers/audit_name_families.py                 # realestate
    python3 importers/audit_name_families.py --cat wat       # any shelf
    python3 importers/audit_name_families.py --families      # what is grouped now
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import namejoin as N  # noqa: E402


def load(cat):
    out = []
    for pv in ("cm", "cr"):
        p = os.path.join(ROOT, "data", "canonical", f"{pv}.json")
        if not os.path.exists(p):
            continue
        for r in json.load(open(p, encoding="utf-8")):
            if cat in (r.get("cat") or []):
                r["_pv"] = pv
                out.append(r)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cat", default="realestate")
    ap.add_argument("--families", action="store_true",
                    help="print the groups the confirmed unions produce today")
    a = ap.parse_args()
    recs = load(a.cat)
    unions = N.load_unions()
    print(f"{a.cat}: {len(recs):,} records · {len(unions)} confirmed spelling(s) "
          f"in {len({v for v in unions.values()})} family(ies)")

    if a.families:
        fam = N.families(recs, unions)
        multi = {k: v for k, v in fam.items() if len(v) > 1}
        print(f"\n{len(multi)} family(ies) of two or more, "
              f"{sum(len(v) for v in multi.values())} records:\n")
        for k, v in sorted(multi.items(), key=lambda kv: -len(kv[1])):
            pins = sum(1 for r in v if r.get("lat") is not None)
            print(f"  {k:12} {len(v):3} records · {pins} pinned · "
                  f"{len(v) - pins} waiting on a pin")
            for r in sorted(v, key=lambda r: r.get("name") or "")[:14]:
                mark = "📍" if r.get("lat") is not None else "  "
                at = (r.get("attrs") or {}).get("tambon") or ""
                print(f"      {mark} {(r.get('name') or '')[:44]:46} {at}")
        return 0

    cands = N.union_candidates(recs, unions)
    if not cands:
        print("\nno unruled candidates — every loose pair is settled")
        return 0
    print(f"\n{len(cands)} pair(s) a loose test would join, none of them applied.")
    print("A true one goes in data/curated/name_families.json with "
          "\"confirmed\": true;\na false one belongs there too, confirmed false, "
          "so nobody re-reads it.\n")
    for a_, b_, how, n, ex in cands:
        print(f"  {a_:12} = {b_:12} {how:16} joins {n:3}")
        for e in ex[:4]:
            print(f"        {e[:56]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
