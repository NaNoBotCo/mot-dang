#!/usr/bin/env python3
"""WO-41 Phase 2 — the write discipline, and the two events defects. No network.

These are the work order's acceptance tests 4 and 5, plus the two defects that
actually emptied the feed. Each one FAILED against the tree before Phase 2:

  4  a source that errors leaves the previous data file byte-identical and
     increments consecutive_failures.
  5  a payload with 1 row where min_rows is 15 is refused.
  +  SELECTION — the events harvester takes only sources that yield events.
     data/sources.json is the whole fleet's registry: the OBEC school register
     (17 MB, method json, verified) was being handed to the events parser.
  +  SHAPE — a parser handed a bare list raises inside the per-source net
     rather than killing the batch. This is the one that ran for four days.

Everything writes into a temporary directory; the repo's own data/ is never
touched.

    python3 tests/test_ingest.py
"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "importers"))

import ingest            # noqa: E402
import harvest_events    # noqa: E402

failures = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}{'' if ok else ' — ' + str(detail)}")
    if not ok:
        failures.append(label)


tmp = Path(tempfile.mkdtemp(prefix="md-ingest-"))
DATA = tmp / "events.json"

print("acceptance 5 — validate before write")
ingest.write(DATA, {"events": list(range(20))}, count=20, min_rows=15)
good = DATA.read_bytes()
wrote = ingest.write(DATA, {"events": [1]}, count=1, min_rows=15)
check("a 1-row payload against min_rows 15 is refused", wrote is False)
check("the previous file is byte-identical afterward", DATA.read_bytes() == good)

print("acceptance 4 — a failed fetch is never destructive")
before_meta = ingest.read_meta(DATA)
ingest.refuse(DATA, "HTTP 500 from the source", sources_ok=[], sources_failed=[("luma", "500")])
m = ingest.read_meta(DATA)
check("the data file is still byte-identical", DATA.read_bytes() == good)
check("consecutive_failures incremented",
      m["consecutive_failures"] == before_meta["consecutive_failures"] + 1,
      m["consecutive_failures"])
check("last_success_at is unchanged by the failure",
      m["last_success_at"] == before_meta["last_success_at"])
check("row_count still describes the data that is actually on disk",
      m["row_count"] == 20, m["row_count"])
check("the failed source is named, not swallowed",
      any("luma" in str(x) for x in m["sources_failed"]), m["sources_failed"])

print("recovery and quorum")
ingest.write(DATA, {"events": list(range(20))}, count=20, min_rows=15)
check("a good run resets the failure count",
      ingest.read_meta(DATA)["consecutive_failures"] == 0)
mtime = DATA.stat().st_mtime_ns
ingest.write(DATA, {"events": list(range(20))}, count=20, min_rows=15)
check("a byte-identical write does not touch the data file",
      DATA.stat().st_mtime_ns == mtime)
check("but the run is still recorded", bool(ingest.read_meta(DATA)["checked_at"]))
wrote = ingest.write(DATA, {"events": list(range(20))}, count=20, min_rows=15,
                     sources_ok=["a"], sources_failed=[("b", "err"), ("c", "err")],
                     quorum=2)
check("a batch under quorum is refused even when it carries rows", wrote is False)

print("no half files")
half = tmp / "atomic.json"
try:
    ingest.write(half, {"bad": {1, 2}}, count=9, min_rows=1)   # a set is not JSON
except TypeError:
    pass
check("a write that dies mid-serialisation leaves no file at all",
      not half.exists())
check("and leaves no temp litter behind",
      not [p for p in tmp.iterdir() if p.name.startswith(".") and p.name.endswith(".tmp")],
      list(tmp.iterdir()))

print("the events defects")
registry = json.loads((ROOT / "data" / "sources.json").read_text())["sources"]
chosen = [s for s in registry
          if s.get("status") == "verified"
          and s.get("method") in ("ical", "json")
          and "events" in (s.get("yields") or [])]
ids = {s["id"] for s in chosen}
check("the OBEC school register is not an events source", "obec-school-007" not in ids)
check("Open-Meteo is not an events source", "open-meteo" not in ids)
check("the real events sources are still chosen",
      {"meetup-ical", "payap-lll"} <= ids, sorted(ids))

# The shape defect, driven through the real parser with a cached bare list.
cache = Path(harvest_events.CACHE)
cache.mkdir(parents=True, exist_ok=True)
key = "md-test-barelist"
snap = cache / (key + "-p1.json")
snap.write_text(json.dumps({"url": "test://", "fetched": harvest_events.date.today().isoformat(),
                            "body": json.dumps([{"id": 1}, {"id": 2}])}))
try:
    raised = None
    try:
        harvest_events.parse_tribe(key, "test://", False)
    except Exception as ex:                      # noqa: BLE001 — that is the point
        raised = ex
    check("a bare-list payload raises a plain ValueError, not AttributeError",
          isinstance(raised, ValueError), type(raised).__name__ if raised else "nothing raised")
    check("and the message names the source",
          raised is not None and key in str(raised), str(raised)[:80])
finally:
    snap.unlink(missing_ok=True)

print()
if failures:
    print(f"{len(failures)} failure(s): {failures}")
    sys.exit(1)
print("all ingest checks passed")
