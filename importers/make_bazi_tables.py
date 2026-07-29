#!/usr/bin/env python3
"""Bake the tables that let a birth chart be computed in the reader's browser.

This exists so that nobody has to send us their birth date to get a reading.
The chart is worked out locally; only someone who then chooses to be emailed
sends anything at all. That is the whole point of the table — it buys the
privacy posture.

A BaZi chart needs four pillars. Three are pure arithmetic once you have a
day anchor: the day pillar is a 60-cycle offset, the hour pillar follows from
the day stem, and the year pillar is a 60-cycle offset too. The one thing that
cannot be done with arithmetic is where the months and the year actually
begin, because those turn on solar terms (節氣) — 立春 starts the BaZi year, and
each of the twelve 節 starts a month. So we bake exactly those, from
../taoist-oracle's own ephemeris, and JavaScript does the rest.

    python3 importers/make_bazi_tables.py                 # 1920-2030
    python3 importers/make_bazi_tables.py --from 1900 --to 2040

Output: data/solar_terms.json — one row per year, twelve day-of-year integers.
"""
import json
import os
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "solar_terms.json")
ORACLE = os.path.abspath(os.path.join(ROOT, "..", "taoist-oracle"))

# The twelve 節 that open BaZi months, in solar-longitude degrees, starting at
# 立春 (315°) which also opens the BaZi year. Order matters: index 0 is the
# first month (寅), and the branch order follows from there.
JIE = [
    (315, "立春", "Start of Spring"), (345, "驚蟄", "Awakening of Insects"),
    (15, "清明", "Clear and Bright"), (45, "立夏", "Start of Summer"),
    (75, "芒種", "Grain in Ear"), (105, "小暑", "Minor Heat"),
    (135, "立秋", "Start of Autumn"), (165, "白露", "White Dew"),
    (195, "寒露", "Cold Dew"), (225, "立冬", "Start of Winter"),
    (255, "大雪", "Major Snow"), (285, "小寒", "Minor Cold"),
]


def main():
    y0, y1 = 1920, 2030
    if "--from" in sys.argv:
        y0 = int(sys.argv[sys.argv.index("--from") + 1])
    if "--to" in sys.argv:
        y1 = int(sys.argv[sys.argv.index("--to") + 1])
    if not os.path.isdir(ORACLE):
        raise SystemExit(f"../taoist-oracle not found at {ORACLE}")
    sys.path.insert(0, ORACLE)
    from core import calendar_cn as cc

    years = {}
    for y in range(y0, y1 + 1):
        row = []
        for i, (deg, _zh, _en) in enumerate(JIE):
            # 小寒 (285°) is the LAST month-start of BaZi year y, and it falls in
            # January of y+1. Asking for it in year y returns the one that closed
            # the year before — an off-by-one-year that shifts every late-December
            # chart by a month.
            term_year = y + 1 if i == 11 else y
            jd = cc.term_jd_for_year(term_year, deg)
            # Stored as a Julian Day, not a date. A term is an instant: at noon on
            # 1926-02-04 the sun is at 314.933 deg, so 立春 has NOT happened yet
            # and a birth that day still belongs to the previous month. Day
            # granularity cannot express that.
            row.append(round(jd, 5))
        years[str(y)] = row

    doc = {
        "generated": date.today().isoformat(),
        "note": ("Twelve 節 per BaZi year that open its months; the first (立春) also "
                 "opens the year, and the twelfth (小寒) falls in January of the NEXT "
                 "gregorian year. Each entry is a Julian Day (UT) — a term is an "
                 "instant, not a date. Source: taoist-oracle core.calendar_cn."),
        "jie": [{"deg": d, "zh": z, "en": e} for d, z, e in JIE],
        "from": y0, "to": y1,
        "years": years,
    }
    with open(OUT, "w") as fh:
        json.dump(doc, fh, separators=(",", ":"))
    size = os.path.getsize(OUT)
    print(f"🐜 solar terms {y0}-{y1} ({len(years)} years) -> {OUT} ({size:,} bytes)")

    # Spot-check against dates that are widely published, so a silent drift in
    # the ephemeris shows up here rather than in someone's chart.
    for y, expect in ((2026, (2, 4)), (2000, (2, 4)), (1988, (2, 4))):
        gy, gm, gd = cc.jd_to_civil_date(years[str(y)][0])
        flag = "ok" if (gm, gd) == expect else "CHECK"
        print(f"   {flag}  立春 {y}: {gy}-{gm:02d}-{gd:02d}")
    gy, gm, gd = cc.jd_to_civil_date(years["2025"][11])
    print(f"   {'ok' if gy == 2026 and gm == 1 else 'CHECK'}  小寒 closing 2025: "
          f"{gy}-{gm:02d}-{gd:02d} (must be January of the following year)")


if __name__ == "__main__":
    main()
