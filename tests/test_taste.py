#!/usr/bin/env python3
"""รสเมือง — the contracts behind the terroir map.

1. Every dot carries a known family, and every family in the legend exists.
2. Presence-only: every dot has a cuisine token — nothing tag-less sneaks in
   to render as "no cuisine".
3. Geography stats are Chiang Mai-scope (the two-province-centroid trap),
   with sane radii, and every stats token meets the n floor.
4. The importer is deterministic.

    python3 tests/test_taste.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "importers"))

failures = []


def check(name, cond, detail=""):
    if cond:
        print("  ok  %s" % name)
    else:
        failures.append(name)
        print("  FAIL %s %s" % (name, detail))


taste = json.loads((ROOT / "data" / "taste.json").read_text())
fam_keys = {f["key"] for f in taste["families"]}

check("every dot's family is in the legend",
      all(d["f"] in fam_keys for d in taste["dots"]))
check("every dot carries a cuisine token",
      all(d.get("t") for d in taste["dots"]))
check("every dot has coordinates",
      all(isinstance(d["la"], float) and isinstance(d["ln"], float)
          for d in taste["dots"]))
check("family counts sum to the dot count",
      sum(f["n"] for f in taste["families"]) == len(taste["dots"]))
check("family_of maps only to known families",
      set(taste["family_of"].values()) <= fam_keys)

check("stats are CM-scope", taste.get("stats_scope") == "cm")
cm_n = sum(1 for d in taste["dots"] if d["p"] == "cm")
check("stats n floor and bounds",
      all(12 <= s["n"] <= cm_n for s in taste["stats"]))
check("huddle radii sane for one city (<15 km)",
      all(0 < s["huddle_m"] < 15000 for s in taste["stats"]),
      [s for s in taste["stats"] if s["huddle_m"] >= 15000][:2])
check("stats tokens are unique",
      len({s["t"] for s in taste["stats"]}) == len(taste["stats"]))

before = (ROOT / "data" / "taste.json").read_bytes()
import build_taste  # noqa: E402
build_taste.main()
after = (ROOT / "data" / "taste.json").read_bytes()
check("importer is deterministic (byte-same rerun)", before == after)

if failures:
    print("\n%d FAILURES: %s" % (len(failures), ", ".join(failures)))
    sys.exit(1)
print("\nall taste contracts hold")
