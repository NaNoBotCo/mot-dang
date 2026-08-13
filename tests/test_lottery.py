#!/usr/bin/env python3
"""หวย — the contracts that keep the lottery record a record.

data/lottery.json (importers/make_lottery.py) and widget_lottery() in
build.py each make promises a test has to keep:

1. The baked file parses and says where it came from: source, generated,
   fetched_at, and a draw whose date reads in both calendars (ISO Gregorian,
   Thai with the พ.ศ. year). be_year is the Gregorian year plus 543 — the
   one arithmetic fact in the file, so it is the one worth checking.
2. Numbers keep their shape. Every prize id is from the known vocabulary,
   labels travel as th/en pairs, and every number is digits of exactly the
   width its tier promises — a five-digit first prize is a corrupted sheet,
   not a result. The four headline groups the tile stands on are present.
3. The next draw date is OMITTED unless the source confirmed it. The
   official schedule shifts around New Year and royal ceremony days;
   presence-only doctrine says a missing fact is omitted, never guessed.
   If a next_draw ever appears it must be a real ISO date after the draw.
4. The tile is a public record, not a tip sheet. When data is present the
   built wall carries the tile, the first-prize number, both calendars and
   the glo.or.th source line — and none of the tip-register words that
   would turn an almanac entry into a hint. Absent data = absent tile,
   never an error.

Run after build.py:

    python3 tests/test_lottery.py
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

failures = []


def check(name, cond, detail=""):
    if cond:
        print("  ok  %s" % name)
    else:
        failures.append(name)
        print("  FAIL %s %s" % (name, detail))


KNOWN = {"first": 6, "front3": 3, "back3": 3, "last2": 2, "near_first": 6,
         "second": 6, "third": 6, "fourth": 6, "fifth": 6}
HEADLINE = ("first", "front3", "back3", "last2")
# The register gate: words that belong to the tip sheets, never to a record.
TIP_WORDS = ("เลขเด็ด", "ใบ้หวย", "หวยเด็ด", "เลขดัง", "เลขมงคล",
             "lucky number", "hot number")

src = ROOT / "data" / "lottery.json"
wall = DOCS / "widgets.html"

if not src.exists():
    # Absent data is a supported state, not a failure — the promise is only
    # that no page then claims a draw.
    print("  --  data/lottery.json absent; checking the tile stayed absent")
    if wall.exists():
        check("absent data -> absent tile", 'id="w-lottery"' not in wall.read_text())
    print()
    if failures:
        print("%d contract(s) broken" % len(failures))
        sys.exit(1)
    print("all good — no record, and no tile pretending to one")
    sys.exit(0)

doc = json.loads(src.read_text())
draw = doc.get("draw") or {}
prizes = draw.get("prizes") or []
by_id = {p.get("id"): p for p in prizes}

# ---- 1. provenance and both calendars -------------------------------------
check("source names the GLO", "glo.or.th" in (doc.get("source") or ""))
check("generated present", bool(doc.get("generated")))
check("fetched_at present", bool(doc.get("fetched_at")))
iso_ok = True
try:
    d = date.fromisoformat(draw.get("date") or "")
except ValueError:
    iso_ok, d = False, None
check("draw date is ISO", iso_ok, repr(draw.get("date")))
if d:
    check("be_year = year + 543", draw.get("be_year") == d.year + 543,
          repr(draw.get("be_year")))
    check("date_th carries the BE year", str(d.year + 543) in (draw.get("date_th") or ""))
    check("date_en carries the Gregorian year", str(d.year) in (draw.get("date_en") or ""))

# ---- 2. numbers keep their shape ------------------------------------------
check("at least one prize", bool(prizes))
for p in prizes:
    pid = p.get("id")
    check("%s is a known tier" % pid, pid in KNOWN)
    if pid not in KNOWN:
        continue
    check("%s label th/en pair" % pid, bool(p.get("th")) and bool(p.get("en")))
    nums = p.get("numbers") or []
    check("%s has numbers" % pid, bool(nums))
    width = KNOWN[pid]
    bad = [n for n in nums if not (str(n).isdigit() and len(str(n)) == width)]
    check("%s numbers are %d digits" % (pid, width), not bad, str(bad[:3]))
for pid in HEADLINE:
    check("headline group %s present" % pid, pid in by_id)

# ---- 3. next draw: omitted unless confirmed -------------------------------
nxt = doc.get("next_draw") or draw.get("next_draw")
if nxt is None:
    check("next_draw omitted (unconfirmed by source)", True)
else:
    ok = True
    try:
        ok = date.fromisoformat(str(nxt)) > d if d else False
    except ValueError:
        ok = False
    check("next_draw is a real date after the draw", ok, repr(nxt))

# ---- 4. the tile renders as a record --------------------------------------
if not wall.exists():
    print("  --  docs/widgets.html not built; run build.py before this test")
else:
    html = wall.read_text()
    check("tile present on the wall", 'id="w-lottery"' in html)
    m = re.search(r'<section class="wtile lot".*?</section>', html, re.S)
    tile = m.group(0) if m else ""
    first_nums = (by_id.get("first") or {}).get("numbers") or []
    if first_nums:
        check("first prize number on the tile", first_nums[0] in tile)
    check("Thai draw date on the tile", (draw.get("date_th") or "!") in tile)
    check("English draw date on the tile", (draw.get("date_en") or "!") in tile)
    check("tile cites glo.or.th", "glo.or.th" in tile)
    hits = [w for w in TIP_WORDS if w in tile.lower()]
    check("no tip-register words on the tile", not hits, str(hits))
    pub = DOCS / "data" / "lottery.json"
    check("docs/data/lottery.json published", pub.exists())
    if pub.exists():
        check("published copy matches data/", pub.read_bytes() == src.read_bytes())

print()
if failures:
    print("%d contract(s) broken" % len(failures))
    sys.exit(1)
print("all good — the record stays a record")
