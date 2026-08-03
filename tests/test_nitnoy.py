#!/usr/bin/env python3
"""เมืองหลับนิดหน่อย — the contracts that keep a wrong lamp off the map.

Three promises the page makes that only a test can keep:

1. The parser reads what it claims and refuses what it cannot represent —
   a half-understood hours string must come out as None, never as a wrong
   schedule (a lamp burning at the wrong hour is a lie about a named shop).
2. Presence-only holds in the baked file: every place in open_lamps.json has
   a real schedule, and the with_hours/parsed/excluded arithmetic closes —
   no place without hours can sneak in and render as always-closed.
3. The importer is deterministic: same canonical data, byte-same JSON.

    python3 tests/test_nitnoy.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "importers"))
from build_open_lamps import parse_hours, WEEK, day_curve, classify  # noqa: E402

failures = []


def check(name, cond, detail=""):
    if cond:
        print("  ok  %s" % name)
    else:
        failures.append(name)
        print("  FAIL %s %s" % (name, detail))


def total(sched):
    return sum(b - a for a, b in sched)


# ---- 1. the parser reads what it claims ----------------------------------

check("24/7 is the whole week", parse_hours("24/7") == [[0, WEEK]])

s = parse_hours("Mo-Su 10:00-22:00")
check("daily span parses", s is not None and total(s) == 7 * 720, s)

s = parse_hours("Mo-Fr 11:00-21:00; Sa,Su 10:00-21:00")
check("two rules with day list", s is not None
      and total(s) == 5 * 600 + 2 * 660, s)

s = parse_hours("Mo-Su 17:00-01:00")
check("overnight wraps into next day", s is not None and total(s) == 7 * 480,
      s)
check("overnight covers 00:30", s is not None
      and any(a <= 1440 + 30 < b for a, b in s))

s = parse_hours("Mo-Sa 09:00-18:00; Su off")
check("off rule closes the day", s is not None and total(s) == 6 * 540, s)

s = parse_hours("Mo-Fr 17:30-23:30 Sa-Su 09:00-23:45")
check("packed day-groups without separator", s is not None
      and total(s) == 5 * 360 + 2 * 885, s)

s = parse_hours("7.00-20.00 น.")
check("dotted Thai clock, no day part = daily", s is not None
      and total(s) == 7 * 780, s)

s = parse_hours("Su-Sa 11:55 AM-11:00 PM")
check("12-hour clock with wrapped day range", s is not None
      and total(s) == 7 * 665, s)

s = parse_hours("Mo, We, Fr 7pm-10pm")
check("bare-hour pm, listed days", s is not None and total(s) == 3 * 180, s)

s = parse_hours("2pm - midnight")
check("midnight closes at 24:00", s is not None and total(s) == 7 * 600, s)

s = parse_hours('Mo-Su 09:00-21:00 "closed 20th each month"')
check("quoted comment is ignored", s is not None and total(s) == 7 * 720, s)

# ---- and refuses what it cannot represent --------------------------------

for raw in ("Su 10:00+",                   # open-ended
            "09:30-16:00; Su[-1] off",     # nth-weekday rule
            "Jan-Mar Mo-Su 09:00-17:00",   # seasonal
            "Mo-Su 00:00-00:00",           # zero-length, ambiguous
            "Lunch & Dinner",              # prose
            "sunrise-sunset"):
    check("refuses %r" % raw, parse_hours(raw) is None)

check("mangled 4:00PM stays intact",
      parse_hours("sunday only  4:00PM - 11:00 PM") is not None
      and total(parse_hours("sunday only  4:00PM - 11:00 PM")) == 420)

# ---- 2. presence-only in the baked file ----------------------------------

lamps = json.loads((ROOT / "data" / "open_lamps.json").read_text())
P, S = lamps["places"], lamps["schedules"]

check("every place points at a real schedule",
      all(0 <= p["k"] < len(S) for p in P))
check("every schedule holds real open time",
      all(0 < total(s) <= WEEK for s in S))
check("intervals sorted, merged, in range",
      all(all(0 <= a < b <= WEEK for a, b in s)
          and all(s[i][1] < s[i + 1][0] for i in range(len(s) - 1))
          for s in S))
pr = lamps["parse"]
check("with_hours = parsed + excluded",
      pr["with_hours"] == pr["parsed"] + pr["excluded"],
      "%d != %d + %d" % (pr["with_hours"], pr["parsed"], pr["excluded"]))
check("places count matches parsed", len(P) == pr["parsed"])
check("every lamp has coordinates",
      all(isinstance(p["la"], float) and isinstance(p["ln"], float)
          for p in P))

for m in lamps["meals"]["subs"] + lamps["meals"]["cuisines"]:
    if not (len(m["curve"]) == 48
            and all(0 <= v <= 1 for v in m["curve"])
            and set(m["bands"]) <=
            {"breakfast", "lunch", "dinner", "late", "allday"}):
        check("meal curve sane: %s" % m.get("sub", m.get("cuisine")), False)
        break
else:
    check("meal curves are 48 slots of fractions with known bands", True)

check("market ledger arithmetic",
      lamps["markets"]["with_hours"] == len(lamps["markets"]["list"])
      and lamps["markets"]["with_hours"] <= lamps["markets"]["total"])

# ---- 3. determinism ------------------------------------------------------

before = (ROOT / "data" / "open_lamps.json").read_bytes()
import build_open_lamps  # noqa: E402
build_open_lamps.main()
after = (ROOT / "data" / "open_lamps.json").read_bytes()
check("importer is deterministic (byte-same rerun)", before == after)

# ---- classify() sanity: a curve peaking at night is dinner/late ----------

night = [0.0] * 48
for i in list(range(36, 48)):
    night[i] = 1.0
bands, _ = classify(night)
check("night-peaked curve claims dinner/late, never breakfast",
      "breakfast" not in bands and "late" in bands, bands)

if failures:
    print("\n%d FAILURES: %s" % (len(failures), ", ".join(failures)))
    sys.exit(1)
print("\nall nitnoy contracts hold")
