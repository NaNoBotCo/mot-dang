#!/usr/bin/env python3
"""WO-41 4d/4e — the Coming-up strip under a frozen clock. Zero network.

The bug this file exists for: on 2026-08-28 the homepage listed Mother's Day
(12 August, sixteen days gone) as "เดือนนี้ · this month", because the
selector worked in month distance and the relative words were baked at build.
These checks freeze the clock at that exact day and hold the repair:

  SELECTION   a fixed-date festival whose day has passed is NOT coming up —
              it has rolled to next year's date (4e) and left the horizon;
              an announced multi-day instance stays until its end date;
              a movable with no announcement sits in the "around this time
              of year" line, never among the dated rows (4d).
  WORDING     the rendered strip contains no build-time relative literal —
              no เดือนนี้, no เดือนหน้า, no "this month", no "next month".
              The no-JS reader gets absolute dates, which stay true.
  SELF-REPAIR every dated row carries data-until (ISO), and md.js carries
              the load-time pruner keyed on MD_TODAY — the strip corrects
              itself even if every walk stops.

    python3 tests/test_freshness.py
"""
import datetime
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import build            # noqa: E402  (module-level loads; build() not called)
import festivals_layer  # noqa: E402

failures = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}{'' if ok else ' — ' + str(detail)}")
    if not ok:
        failures.append(label)


FESTS = json.loads((ROOT / "data" / "festivals.json").read_text())["festivals"]
BY_ID = {f["id"]: f for f in FESTS}
TODAY = datetime.date(2026, 8, 28)   # the day the symptom was reported

G = {"bi": build.bi, "MONTH_TH": build.MONTH_TH, "MONTH_EN": build.MONTH_EN,
     "_ANNOUNCED": {}}

print("occurrence — the resolved date (4e)")
occ = festivals_layer.occurrence(BY_ID["mothers-day"], None, TODAY)
check("Mother's Day on Aug 28 resolves to NEXT year's 12 August",
      occ and occ[0] == datetime.date(2027, 8, 12), occ)
occ = festivals_layer.occurrence(BY_ID["mothers-day"], None, datetime.date(2026, 8, 1))
check("…and on Aug 1 it is still this year's",
      occ and occ[0] == datetime.date(2026, 8, 12), occ)
occ = festivals_layer.occurrence(BY_ID["songkran-pi-mai-muang"], None, TODAY)
check("Songkran rolls to 13 April next year",
      occ and occ[0] == datetime.date(2027, 4, 13), occ)
ann = [{"date_start": "2026-08-20", "date_end": "2026-08-30"}]
occ = festivals_layer.occurrence(BY_ID["mothers-day"], ann, TODAY)
check("an announced multi-day instance spanning today STAYS until its end",
      occ and occ[1] == datetime.date(2026, 8, 30) and occ[2] == "announced", occ)
ann_over = [{"date_start": "2026-08-01", "date_end": "2026-08-02"}]
occ = festivals_layer.occurrence(BY_ID["mothers-day"], ann_over, TODAY)
check("announced-and-over falls through to the rolled fixed date",
      occ and occ[0] == datetime.date(2027, 8, 12), occ)
occ = festivals_layer.occurrence(BY_ID["yi-peng"], None, TODAY) \
    if "yi-peng" in BY_ID else None
check("a lunar movable with no announcement resolves to nothing (a window is "
      "not a date)", occ is None, occ)

print("the strip, frozen at 2026-08-28")
html = festivals_layer.coming_up(FESTS, TODAY, depth=0, g=G)
check("Mother's Day does not appear", "mothers-day" not in html)
# Exact id, not a substring: "akha" also lives inside mAKHA-bucha — the
# WO-24 namesake lesson, caught here by this very test's first draft.
akha = "akha-swing-festival" if "akha-swing-festival" in BY_ID else None
check("the Akha swing window sits in the around-line, not the dated rows",
      akha is None or re.search(
          r'class="cuitem"[^>]*>\s*<a href="festivals/' + akha, html) is not None)
for lit in ("เดือนนี้", "เดือนหน้า", "this month", "next month"):
    check(f"no baked relative literal: {lit!r}", lit not in html)
lis = re.findall(r"<li\b[^>]*>", html)
check("every dated row carries an ISO data-until",
      bool(lis) == bool(re.findall(r'<li data-until="\d{4}-\d{2}-\d{2}"', html))
      and all('data-until="' in li for li in lis), lis[:2])

print("the strip, frozen at 2026-08-01 (the date not yet passed)")
html_aug1 = festivals_layer.coming_up(FESTS, datetime.date(2026, 8, 1), depth=0, g=G)
check("Mother's Day IS coming up on Aug 1, with its absolute date",
      "mothers-day" in html_aug1 and "12 สิงหาคม" in html_aug1)

print("self-repair wiring")
check("md.js carries the load-time pruner", ".comingup" in build.JS
      and "data-until" in build.JS and "MD_TODAY" in build.JS)

print()
if failures:
    print(f"{len(failures)} failure(s): {failures}")
    sys.exit(1)
print("all freshness checks passed")
