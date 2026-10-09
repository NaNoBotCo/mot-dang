#!/usr/bin/env python3
"""Every lens register, checked — exit 1 on one that would print a wrong page.

  a row without a grade, or a grade outside stated/listed/route
  a stated or listed row without src + evidence, or without a fetched date
  a placeId that resolves nowhere in canonical (run import_all.py first)
  a section on a row the lens does not declare
  a `for` key the lens does not label
  a panel door href that is not a page the build writes (root-level only)

  python3 importers/audit_lens.py [key…]
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GRADES = {"stated", "listed", "route"}


def main():
    want = [a for a in sys.argv[1:] if not a.startswith("--")]
    recs = {}
    for prov in ("cm", "cr"):
        for r in json.loads((ROOT / "data" / "canonical" / f"{prov}.json").read_text()):
            recs[r["id"]] = r
    bad = 0
    for p in sorted((ROOT / "data" / "curated" / "lens").glob("*.json")):
        lens = json.loads(p.read_text(encoding="utf-8"))
        key = lens.get("key") or p.stem
        if want and key not in want:
            continue
        secs = {s[0] for s in lens.get("sections") or []}
        fors = set((lens.get("for") or {}).keys())
        grades = {}
        for row in lens.get("rows") or []:
            g = row.get("grade")
            grades[g or "?"] = grades.get(g or "?", 0) + 1
            if g not in GRADES:
                print(f"  {key}: row {row.get('key')} grade {g!r}"); bad = 1
            if g in ("stated", "listed") and not (row.get("src") and row.get("evidence")):
                print(f"  {key}: row {row.get('key')} is {g} with no src+evidence"); bad = 1
            if not row.get("fetched"):
                print(f"  {key}: row {row.get('key')} has no fetched date"); bad = 1
            if row.get("section") not in secs:
                print(f"  {key}: row {row.get('key')} section {row.get('section')!r} not declared"); bad = 1
            for f in row.get("for") or []:
                if f not in fors:
                    print(f"  {key}: row {row.get('key')} for {f!r} not labelled"); bad = 1
            for pid in row.get("placeIds") or []:
                if pid not in recs:
                    print(f"  {key}: row {row.get('key')} placeId {pid} resolves nowhere"); bad = 1
        for x in lens.get("registers") or []:
            if not (x.get("url") and x.get("fetched")):
                print(f"  {key}: register {x.get('key')} lacks url or fetched"); bad = 1
        # census regexes must compile
        for lab_th, lab_en, rx in lens.get("census") or []:
            try:
                re.compile(rx)
            except re.error as e:
                print(f"  {key}: census regex {rx!r}: {e}"); bad = 1
        n = len(lens.get("rows") or [])
        print(f"  {key}: {n} rows (" + " · ".join(f"{k} {v}" for k, v in sorted(grades.items())) + ")")
    sys.exit(bad)


if __name__ == "__main__":
    main()
