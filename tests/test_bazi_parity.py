#!/usr/bin/env python3
"""Prove docs/bazi.js agrees with ../taoist-oracle over a wide span of dates.

KNOWN INCONSISTENCY, reproduced on purpose: taoist-oracle's year_pillar decides
the 立春 boundary by CIVIL DAY, while its month_pillar decides the same boundary
by SOLAR INSTANT. For someone born on the day of 立春 but before the exact
moment, those two disagree — the year says the new cycle has begun and the
month says it has not. The JavaScript copies the civil-day rule so that this
test compares like with like. If that rule is ever corrected, correct it in
taoist-oracle, regenerate with importers/make_bazi_js.py, and this test will
confirm the two still agree.


A birth chart that is subtly wrong is worse than no birth chart: it looks
authoritative and nobody can tell. So the JavaScript restatement is not trusted
because it was written carefully — it is trusted because this runs both engines
over thousands of dates and compares all four pillars.

Needs node on PATH and ../taoist-oracle on disk.

    python3 tests/test_bazi_parity.py            # ~4000 dates
    python3 tests/test_bazi_parity.py --dense    # every day across a decade
"""
import json
import os
import subprocess
import sys
import tempfile
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORACLE = os.path.abspath(os.path.join(ROOT, "..", "taoist-oracle"))
JS = os.path.join(ROOT, "assets", "bazi.js")
TERMS = os.path.join(ROOT, "data", "solar_terms.json")


def sample_dates(dense):
    out = []
    if dense:
        d = date(2015, 1, 1)
        while d <= date(2025, 12, 31):
            out.append(d)
            d += timedelta(days=1)
        return out
    # Spread across the table, and deliberately crowd the 立春 boundary in
    # early February where the year pillar flips.
    for y in range(1925, 2029, 1):
        for m, dd in ((1, 15), (2, 3), (2, 4), (2, 5), (2, 6), (3, 20),
                      (5, 5), (6, 21), (8, 7), (9, 23), (11, 7), (12, 31)):
            try:
                out.append(date(y, m, dd))
            except ValueError:
                pass
    return out


def py_chart(d, hour):
    """The reference chart. Note month_pillar takes the SAME hour the JS uses —
    passing its default 12 while the JS used the real birth hour made every
    birth within two hours of a solar term look like a port bug."""
    from core import ganzhi
    yp = ganzhi.year_pillar(d.year, d.month, d.day)
    mp = ganzhi.month_pillar(d.year, d.month, d.day, hour)
    dp = ganzhi.day_pillar(d.year, d.month, d.day)
    hp = ganzhi.hour_pillar(dp, hour)
    return {"year": yp.index, "month": mp.index, "day": dp.index, "hour": hp.index}


def main():
    dense = "--dense" in sys.argv
    if not os.path.isdir(ORACLE):
        raise SystemExit(f"../taoist-oracle not found at {ORACLE}")
    if not os.path.exists(JS):
        raise SystemExit(f"{JS} missing — run importers/make_bazi_js.py first")
    if not os.path.exists(TERMS):
        raise SystemExit(f"{TERMS} missing — run importers/make_bazi_tables.py first")
    sys.path.insert(0, ORACLE)

    dates = sample_dates(dense)
    hour = 14
    cases = [[d.year, d.month, d.day] for d in dates]

    runner = f"""
const fs = require('fs');
require({json.dumps(JS)});
const TERMS = JSON.parse(fs.readFileSync({json.dumps(TERMS)}, 'utf8'));
const cases = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const out = cases.map(c => {{
  const r = MDBazi.chart(TERMS, c[0], c[1], c[2], {hour}, true);
  if (r.error) return null;
  return {{year: r.pillars.year.index, month: r.pillars.month.index,
          day: r.pillars.day.index, hour: r.pillars.hour.index}};
}});
process.stdout.write(JSON.stringify(out));
"""
    with tempfile.TemporaryDirectory() as td:
        cpath = os.path.join(td, "cases.json")
        rpath = os.path.join(td, "run.js")
        with open(cpath, "w") as fh:
            json.dump(cases, fh)
        with open(rpath, "w") as fh:
            fh.write(runner)
        try:
            proc = subprocess.run(["node", rpath, cpath], capture_output=True,
                                  text=True, timeout=300)
        except FileNotFoundError:
            raise SystemExit("node not on PATH — cannot run the parity check")
        if proc.returncode != 0:
            raise SystemExit("node failed:\n" + proc.stderr[:2000])
        js_out = json.loads(proc.stdout)

    bad, checked, skipped = [], 0, 0
    for d, got in zip(dates, js_out):
        if got is None:
            skipped += 1
            continue
        want = py_chart(d, hour)
        checked += 1
        for k in ("year", "month", "day", "hour"):
            if want[k] != got[k]:
                bad.append((d.isoformat(), k, want[k], got[k]))
                break

    print(f"compared {checked:,} dates ({skipped} outside the table)")
    if bad:
        print(f"MISMATCH on {len(bad)} date(s); first 12:")
        for row in bad[:12]:
            print(f"   {row[0]}  {row[1]}: python={row[2]} js={row[3]}")
        sys.exit(1)
    print("all four pillars agree on every date")


if __name__ == "__main__":
    main()
