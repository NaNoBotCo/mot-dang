#!/usr/bin/env python3
"""The zone census: where every zone's bounds actually catch places.

    python3 importers/audit_zones.py

Zero network. Two jobs:

1. THE ANCHOR CHECK, standalone. Every zone in data/curated/zones.json names
   anchors — places from our own canonical records that must fall inside it
   (the moat rectangle proven by วัดพระสิงห์ standing inside it). build.py
   runs the same check and refuses the build on a miss; this script is the
   witness you can run without building 22,000 pages.

2. THE CENSUS. For each province with zones, how many records land in each
   zone and how many land in none — printed, because a fallback bucket that
   quietly grows to half a shelf is the road-graph lesson (52% unreached)
   happening again, and the number should be read, not assumed.

Exit 1 on an anchor miss; exit 0 otherwise (the census is information,
not a gate).
"""
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZONES = {k: v for k, v in
         json.loads((ROOT / "data" / "curated" / "zones.json").read_text()).items()
         if not k.startswith("_")}


def zone_of(r, z):
    la, ln = r.get("lat"), r.get("lng")
    if la is None or ln is None:
        return None
    for b in z["boxes"]:
        if b["lat"][0] <= la <= b["lat"][1] and b["lng"][0] <= ln <= b["lng"][1]:
            return b
    for c in z["circles"]:
        if math.hypot((la - c["lat"]) * 111.0, (ln - c["lng"]) * 105.0) <= c["r_km"]:
            return c
    return None


def main():
    bad = 0
    for prov, z in ZONES.items():
        path = ROOT / "data" / "canonical" / f"{prov}.json"
        if not path.exists():
            print(f"{prov}: no canonical file, skipped")
            continue
        records = json.loads(path.read_text())
        print(f"== {prov} · {len(records):,} records ==")
        for b in z["boxes"]:
            for a in b.get("anchors", []):
                hits = [r for r in records if a in (r.get("name") or "")
                        and r.get("lat") is not None]
                ok = any((zone_of(r, z) or {}).get("key") == b["key"] for r in hits)
                mark = "OK  " if ok else ("none" if not hits else "MISS")
                if hits and not ok:
                    bad += 1
                print(f"  {mark} {b['key']:<14} anchor {a} ({len(hits)} hit)")
        census = Counter()
        for r in records:
            zd = zone_of(r, z)
            census[zd["key"] if zd else "(no zone)"] += 1
        for k, n in census.most_common():
            print(f"  {n:6,}  {k}")
    if bad:
        print(f"\n{bad} anchor(s) outside their zone — fix the bounds.")
        sys.exit(1)


if __name__ == "__main__":
    main()
