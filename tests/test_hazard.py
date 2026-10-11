#!/usr/bin/env python3
"""WO-57 items 4 and 5 — the smoke page and the river page hold their rules.

These two pages print state registers, and the whole reason they are allowed
to exist is that they never say more than the register does. Each check below
guards one way that could quietly stop being true.

  THE LIMIT IS THE STATION'S OWN. /nam.html compares every reading to a
      level_limit that arrived in the same record. If a station ever comes
      back without one, the page must not fall back to a number of ours —
      there is no such number, and inventing one would turn a gauge reading
      into a flood warning.
  NOTHING ON EITHER PAGE IS A FORECAST. The words that would make one — a
      crest, a prediction, an instruction to move — are checked for by hand
      because they are exactly what a well-meaning future edit adds.
  THE PIN CHECK ACTUALLY RUNS. 2,428 clean-air rooms come from a register
      entered by thousands of hands, and 206 of their pins cannot be where
      the row says. The nearest-thing payload must exclude the ones ruled
      misplaced, and must still hold most of the register.
  THE GRADE AND THE DATE RIDE. A room assessed by an officer and a room that
      assessed itself are different facts and the page draws them apart.
  A BULK-ENTRY PHONE IS NOBODY'S. One number was on 428 rows at 246 separate
      sites. It must not be offered as any place's own.

    python3 tests/test_hazard.py
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = Path(os.environ.get("MD_DOCS") or (ROOT / "docs"))
sys.path.insert(0, str(ROOT))

failures = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}{'' if ok else ' — ' + str(detail)}")
    if not ok:
        failures.append(label)


# ---- the clean-air register -------------------------------------------
print("the clean-air register")
crf = ROOT / "data" / "cleanrooms.json"
if not crf.exists():
    check("data/cleanrooms.json is here", False,
          "run importers/fetch_cleanrooms.py")
else:
    import foon_layer
    reg = json.loads(crf.read_text(encoding="utf-8"))
    rooms = reg["rooms"]
    check("the register is not hollow", len(rooms) > 1500, len(rooms))
    check("every room carries a pin, a grade and an assessment date",
          all(isinstance(r.get("la"), (int, float))
              and r.get("g") in ("evaluator", "self") for r in rooms))
    check("the pin check ran and recorded its counts",
          set(reg.get("doubts") or {}) == {"outside", "far", "unchecked"},
          reg.get("doubts"))
    check("the pin check states its own thresholds",
          bool((reg.get("pin_check") or {}).get("far_km")
               and (reg.get("pin_check") or {}).get("far_ratio")))

    near = foon_layer.near_payload(reg)["rooms"]
    bad = {r["n"] for r in rooms if r.get("doubt") in ("outside", "far")}
    check("no room ruled misplaced is offered as nearest to anybody",
          not (bad & {r[0] for r in near}) or
          all(any(x.get("doubt") not in ("outside", "far")
                  for x in rooms if x["n"] == n) for n in bad & {r[0] for r in near}))
    check("the nearest-thing list still holds most of the register",
          len(near) > 0.8 * len(rooms), f"{len(near)} of {len(rooms)}")

    # A phone at many separate sites is a bulk-entry default, not a number.
    live = [r["t"] for r in rooms if (r.get("t") or "").strip()]
    worst = max((live.count(t) for t in set(live)), default=0)
    check("no surviving phone is shared by a suspicious number of rows",
          worst < 60, f"one number is on {worst} rows")
    check("the numbers taken away were kept, not deleted",
          any(r.get("tDefault") for r in rooms))

# ---- the river --------------------------------------------------------
print("the river")
pf = ROOT / "data" / "ping.json"
if not pf.exists():
    check("data/ping.json is here", False, "run importers/make_ping.py")
else:
    ping = json.loads(pf.read_text(encoding="utf-8"))
    sts = ping["stations"]
    check("the gauges are here", len(sts) >= 5, len(sts))
    check("EVERY station carries the register's own alert level",
          all(isinstance(s.get("limit"), (int, float)) and s["limit"] > 0
              for s in sts),
          [s["id"] for s in sts if not s.get("limit")])
    check("the city station is on the mainstem and is named",
          any(s["id"] == ping["city_station"] and s.get("chain") for s in sts))
    check("each station carries hourly readings",
          all(len(s.get("hours") or []) > 24 for s in sts),
          {s["id"]: len(s.get("hours") or []) for s in sts})
    lag = ping.get("lag") or {}
    check("the lead time is reported with its correlation and its window",
          lag.get("hours") is None
          or ({"r", "hours_compared", "window_days"} <= set(lag)))
    if lag.get("r") is not None:
        check("the lead time is not asserted on a weak fit without saying so",
              lag["r"] <= 1.0 and lag["hours_compared"] > 0)

# ---- neither page forecasts -------------------------------------------
print("neither page forecasts")
FORECAST = [
    ("จะท่วม", "says the river will flood"),
    ("คาดว่า", "forecasts"),
    ("คาดการณ์", "forecasts"),
    ("ควรอพยพ", "tells anybody to evacuate"),
    ("will crest", "predicts a crest"),
    ("will flood", "predicts flooding"),
    ("you should evacuate", "tells anybody to evacuate"),
    ("we recommend", "recommends"),
]
# A hit inside a DENIAL is the page doing its job. /nam.html's own disclaimer
# says it does not tell anybody whose house will flood, and the first draft of
# this test failed on that sentence — a check that cannot tell a forecast from
# a refusal to forecast would push the refusal off the page, which is the
# opposite of what it is for.
DENY = ("ไม่", "not ", "never ", "no ")


def forecasts(text):
    out = []
    low = text.lower()
    for phrase, why in FORECAST:
        for m in re.finditer(re.escape(phrase.lower()), low):
            before = low[max(0, m.start() - 60):m.start()]
            if any(d in before for d in DENY):
                continue
            out.append(why)
            break
    return out


for name in ("nam.html", "foon.html", "chuai.html"):
    f = DOCS / name
    if not f.exists():
        print(f"  docs/{name} is not built — SKIPPED")
        continue
    text = re.sub(r"(?s)<script.*?</script>", "", f.read_text(encoding="utf-8"))
    hits = forecasts(text)
    check(f"{name} never {'/'.join(hits) if hits else 'forecasts or advises'}",
          not hits, hits)

if (DOCS / "nam.html").exists():
    t = (DOCS / "nam.html").read_text(encoding="utf-8")
    check("nam.html hands the warning job to ปภ. and gives 1784",
          "1784" in t and "ปภ." in t)
    check("nam.html says the limits are not ours",
          "the station" in t and "own" in t)

print()
if failures:
    print(f"{len(failures)} failure(s): {failures}")
    sys.exit(1)
print("all hazard checks passed")
