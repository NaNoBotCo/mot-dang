#!/usr/bin/env python3
"""A place that has shut or moved says so under its name and lights no lamp.

    python3 tests/test_status.py          (no build needed)

The path: data/curated/status.json → importers/import_all.py
apply_curated_status() → record["status"] → build.py status_line() under the
h1, no `sched` in the place .json and no `hk` on the index row. A lamp on a
shut shop is a lamp that lies. A record with no status is untouched, and an
empty status.json changes nothing — which is the state the file ships in.

Rendered through build.detail_page() and build.place_json() on a real record
from data/canonical, the way tests/test_sabai.py does, so what is checked is
what the site prints.
"""
import copy
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "importers"))

import build  # noqa: E402
import import_all  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print("%-4s %s%s" % ("ok" if ok else "FAIL", name, "" if ok else "  — " + detail))
    if not ok:
        fails.append(name)


prov = build.PROVINCES[0]
base = next((r for r in build.load()[prov["key"]]
             if any(c in build.CATS for c in r.get("cat", []))
             and r.get("lat") is not None and "status" not in r), None)
check("a record with a known shelf exists to test", base is not None)
if base is None:
    print("\nFAIL: no record")
    sys.exit(1)

# The record stands in the schedule table, so a lamp is on offer to it.
build._LAMPS_CACHE = ([[[0, 1439]]], {base["id"]: 0})

plain = copy.deepcopy(base)
closed = copy.deepcopy(base)
closed["status"] = {"state": "closed", "since": "2026-09-01", "source": "owner, by email"}
moved = copy.deepcopy(base)
moved["status"] = {"state": "moved", "since": "2026-08-15",
                   "to": "https://motdang.net/cm/p/elsewhere.html", "source": "reader"}
other = copy.deepcopy(base)
other["status"] = {"state": "duplicate", "source": "reader"}

# The page side lives in build.py (place_status, status_line, the two lamp
# gates). Absent, every page check below fails by name rather than crashing,
# and the fold checks further down still run.
has_page = hasattr(build, "place_status") and hasattr(build, "status_line")
check("build.py carries place_status() and status_line()", has_page,
      "the page side of status.json is not in build.py")

# ------------------------------------------------------------------ the line
if has_page:
    h_plain = build.detail_page(plain, prov)
    h_closed = build.detail_page(closed, prov)
    h_moved = build.detail_page(moved, prov)
    h_other = build.detail_page(other, prov)
    print("the line under the name")
    check("a closed place says so directly under the h1",
          re.search(r'</h1><p class="placestatus">', h_closed) is not None)
    check("in both languages, with the date it shut",
          "ปิดถาวร" in h_closed and "permanently closed" in h_closed
          and "(2026-09-01)</p>" in h_closed)
    check("a moved place says so and links where it went",
          re.search(r'</h1><p class="placestatus">', h_moved) is not None
          and "ย้ายแล้ว" in h_moved and "moved" in h_moved and "→" in h_moved
          and 'href="https://motdang.net/cm/p/elsewhere.html"' in h_moved)
    check("a record with no status prints no line", 'class="placestatus"' not in h_plain)
    check("a state the page does not know prints no line", 'class="placestatus"' not in h_other)
    _t = lambda h: re.search(r"<title>.*?</title>", h, re.S).group(0)  # noqa: E731
    check("the page is otherwise the same page", _t(h_plain) == _t(h_closed) == _t(h_moved))

    # ------------------------------------------------------------------ the lamp
    print("no lamp on a shut shop")
    j_plain = build.place_json(plain)
    j_closed = build.place_json(closed)
    j_moved = build.place_json(moved)
    check("a plain record with hours carries its schedule", "sched" in j_plain)
    check("a closed record carries none", "sched" not in j_closed)
    check("a moved record carries none", "sched" not in j_moved)
    check("the status rides in the place .json",
          (j_closed.get("status") or {}).get("state") == "closed")
    check("place_status() is the one gate, and unknown stays None",
          build.place_status(closed) is not None and build.place_status(plain) is None
          and build.place_status(other) is None)
    src = (ROOT / "build.py").read_text(encoding="utf-8")
    check("the index row's hk passes the same gate",
          'None if place_status(r) else _SI["hours"].get(r["id"])' in src)
    check("the JSON-LD carries no openingHours to strip", "openingHours" not in src)

# ------------------------------------------------------------------ the fold
print("the fold")
with tempfile.TemporaryDirectory() as td:
    empty = Path(td) / "empty.json"
    empty.write_text("{}")
    recs = [copy.deepcopy(base)]
    before = copy.deepcopy(recs)
    check("an empty status.json changes nothing",
          import_all.apply_curated_status(recs, path=empty) == 0 and recs == before)

    some = Path(td) / "some.json"
    some.write_text(json.dumps({"status": {
        base["id"]: {"state": "closed", "since": "2026-09-01", "source": "owner",
                     "reported": "2026-09-03"},
        "no-such-id": {"state": "closed", "since": "2026-09-01", "source": "owner"}}}))
    recs = [copy.deepcopy(base)]
    n = import_all.apply_curated_status(recs, path=some)
    check("a listed id is folded, an id nobody holds is skipped", n == 1, str(n))
    check("the record carries the status",
          recs[0].get("status") == {"state": "closed", "since": "2026-09-01", "source": "owner"},
          str(recs[0].get("status")))
    check("and the receipt, like every curated fold",
          any(s.get("via") == "data/curated/status.json" and s.get("ref") == "owner"
              and s.get("fetched") == "2026-09-03" for s in recs[0].get("sources") or []))
    check("the receipt's date is the report's, never the closing date",
          not any(s.get("fetched") == "2026-09-01" for s in recs[0].get("sources") or []))

    flat = Path(td) / "flat.json"
    flat.write_text(json.dumps({"_readme": "x", base["id"]: {
        "state": "moved", "to": "ถนนช้างม่อย", "since": "2026-08-15", "source": "reader"}}))
    recs = [copy.deepcopy(base)]
    check("ids at the top level read the same",
          import_all.apply_curated_status(recs, path=flat) == 1
          and recs[0]["status"]["state"] == "moved" and recs[0]["status"]["to"] == "ถนนช้างม่อย")

    dup = Path(td) / "dup.json"
    dup.write_text(json.dumps({"status": {base["id"]: {"state": "duplicate", "source": "reader"}}}))
    recs = [copy.deepcopy(base)]
    check("any other state is left alone",
          import_all.apply_curated_status(recs, path=dup) == 0 and "status" not in recs[0])

# --------------------------------------------------------------- the file
disk = json.loads((ROOT / "data" / "curated" / "status.json").read_text())
check("data/curated/status.json parses as an object", isinstance(disk, dict))

print("\n%s" % ("PASS" if not fails else "FAIL: " + ", ".join(fails)))
sys.exit(1 if fails else 0)
