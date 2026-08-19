#!/usr/bin/env python3
"""Hold importers/make_horo.py and assets/horo.js to the same arithmetic.

The horoscope layer computes in two places on purpose — Python bakes today's
readings into the static page, JavaScript recomputes any later day in the
reader's browser — so a drift between them would show as a page that
contradicts itself the morning after a build. This runs both engines over the
whole baked window (and a wide spread of birth dates for the finder) and
compares every index that decides a reading: day pillar, จุลศักราช year and
animal, ทักษา station for every birth slot, branch relation for every year,
the seven longitudes and the per-sign Western verdicts.

It also pins the tradition itself: the eight classical กาลกิณี pairings, the
published ปีชง list, เถลิงศก on 16 April 2025–2027, ตรุษจีน on dates every
Thai-Chinese family calendar prints, and Chinese New Year against
../taoist-oracle's astronomical calendar when that repo is on disk.

Needs node on PATH.

    python3 tests/test_horo_parity.py
"""
import json
import os
import subprocess
import sys
import tempfile
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "importers"))
import make_horo as H  # noqa: E402

HORO = json.load(open(os.path.join(ROOT, "data", "horo.json")))
JS = os.path.join(ROOT, "assets", "horo.js")


def js_run(dates, births):
    script = r"""
const M = require(process.argv[2]).MDHoro;
const D = JSON.parse(require('fs').readFileSync(process.argv[3], 'utf8'));
M._setData(D);
const T = D.tables;
const inp = JSON.parse(require('fs').readFileSync(process.argv[4], 'utf8'));
const out = {days: {}, births: {}};
for (const iso of inp.dates) {
  const [y, m, d] = iso.split('-').map(Number);
  const jd = M.gregToJD(y, m, d, 5.0);
  const lons = M.longitudes(jd);
  const cs = M.csForDate(y, m, d);
  const slot = new Date(y, m - 1, d).getDay();
  out.days[iso] = {
    dp: M.dayPillarIndex(y, m, d),
    cs: cs, animal: M.thaiAnimalIndex(cs),
    lon: lons.map(x => +x.toFixed(3)),
    station: [0,1,2,3,4,5,6,7].map(b => M.wheelStation(b, slot)),
    rel: [0,1,2,3,4,5,6,7,8,9,10,11].map(b => M.branchRelation(M.dayPillarIndex(y,m,d) % 12, b)),
    west: [0,1,2,3,4,5,6,7,8,9,10,11].map(s => { const r = M.westReading(T, s, lons);
      return [r.moon_sign, r.moon_aspect, r.top ? r.top.join(':') : null, r.verdict]; })
  };
}
for (const iso of inp.births) {
  const [y, m, d] = iso.split('-').map(Number);
  const f = M.findSigns(y, m, d);
  out.births[iso] = [f.thaiSlot, f.thaiAnimal, f.cnBranch, f.sunSign, f.cusp ? 1 : 0];
}
process.stdout.write(JSON.stringify(out));
"""
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as fj, \
         tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fi:
        fj.write(script)
        json.dump({"dates": dates, "births": births}, fi)
    try:
        res = subprocess.run(["node", fj.name, JS, os.path.join(ROOT, "data", "horo.json"), fi.name],
                             capture_output=True, text=True, check=True)
    finally:
        os.unlink(fj.name)
        os.unlink(fi.name)
    return json.loads(res.stdout)


def main():
    fails = []
    # --- the tradition, pinned -------------------------------------------
    KALAKINI = {0: 5, 1: 0, 2: 1, 3: 2, 4: 6, 5: 7, 6: 3, 7: 4}
    for born, kk in KALAKINI.items():
        got = next(t for t in range(8) if H.wheel_station(born, t) == 7)
        if got != kk:
            fails.append(f"กาลกิณี slot {born}: {got} != {kk}")
    for cs, y in ((1387, 2025), (1388, 2026), (1389, 2027)):
        if H.thaloengsok_date(cs) != date(y, 4, 16):
            fails.append(f"เถลิงศก CS{cs}: {H.thaloengsok_date(cs)}")
    for y, iso in (("2024", "2024-02-10"), ("2025", "2025-01-29"), ("2026", "2026-02-17"),
                   ("2027", "2027-02-06"), ("2000", "2000-02-05"), ("1997", "1997-02-07"),
                   ("1988", "1988-02-17"), ("1965", "1965-02-02")):
        if HORO["years"]["cny"].get(y) != iso:
            fails.append(f"CNY {y}: {HORO['years']['cny'].get(y)} != {iso}")
    horse = 6
    chong_list = {b for b in range(12)
                  if H.branch_relation(horse, b) in ("chong", "same", "xing", "hai", "po")}
    if chong_list != {0, 6, 1, 3}:
        fails.append(f"ปีชง 2569 set: {sorted(chong_list)}")
    if H.sun_sign_index(2026, 8, 18) != 4:
        fails.append("Sun sign 2026-08-18 not สิงห์")

    # --- Python vs JS over the baked window + births -----------------------
    dates = sorted(HORO["days"])
    births = []
    d0 = date(1925, 3, 3)
    while d0 < date(2030, 1, 1):
        births.append(d0.isoformat())
        d0 += timedelta(days=97)
    births += ["2000-01-28", "2000-02-04", "2000-02-05", "2026-04-15", "2026-04-16",
               "1976-04-13", "1978-04-16", "2026-03-20", "2026-08-23", "1990-12-22"]
    js = js_run(dates, births)
    n = 0
    for iso in dates:
        y, m, dd = (int(x) for x in iso.split("-"))
        d = date(y, m, dd)
        py = HORO["days"][iso]
        j = js["days"][iso]
        n += 1
        if py["dp"] != j["dp"]:
            fails.append(f"{iso} dp {py['dp']} != {j['dp']}")
        cs = H.cs_for_date(d)
        if cs != j["cs"] or H.thai_animal_index(cs) != j["animal"]:
            fails.append(f"{iso} cs/animal py {cs} js {j['cs']}")
        for a, b in zip(py["lon"], j["lon"]):
            if abs(a - b) > 0.002:
                fails.append(f"{iso} lon {py['lon']} vs {j['lon']}")
                break
        slot = (d.weekday() + 1) % 7
        if [H.wheel_station(b, slot) for b in range(8)] != j["station"]:
            fails.append(f"{iso} stations differ")
        if [H.branch_relation(py["dp"] % 12, b) for b in range(12)] != j["rel"]:
            fails.append(f"{iso} branch relations differ")
        for s in range(12):
            r = H.west_reading(s, py["lon"])
            top = f"{r['top'][0]}:{r['top'][1]}" if r["top"] else None
            if [r["moon_sign"], r["moon_aspect"], top, r["verdict"]] != j["west"][s]:
                fails.append(f"{iso} west sign {s}: py {[r['moon_sign'], r['moon_aspect'], top, r['verdict']]} js {j['west'][s]}")
                break
    for iso in births:
        y, m, dd = (int(x) for x in iso.split("-"))
        d = date(y, m, dd)
        cs = H.cs_for_date(d)
        cny = HORO["years"]["cny"].get(str(y))
        gy = y - 1 if (cny and iso < cny) else y
        exp = [(d.weekday() + 1) % 7, H.thai_animal_index(cs), (gy - 4) % 12,
               H.sun_sign_index(y, m, dd)]
        got = js["births"][iso][:4]
        if exp != got:
            fails.append(f"finder {iso}: py {exp} js {got}")

    # --- Chinese New Year against the astronomical calendar --------------
    try:
        sys.path.insert(0, H.ORACLE)
        from core import calendar_cn as cal
        for y in (1930, 1950, 1970, 1990, 2010, 2026, 2029):
            iso = HORO["years"]["cny"][str(y)]
            yy, mm, dd = (int(x) for x in iso.split("-"))
            ld = cal.lunar_date(yy, mm, dd)
            prev = date(yy, mm, dd) - timedelta(days=1)
            ldp = cal.lunar_date(prev.year, prev.month, prev.day)
            if not (ld["month"] == 1 and ld["day"] == 1 and not ld["is_leap"] and ldp["month"] != 1):
                fails.append(f"CNY {y} {iso} is not lunar 1/1")
    except ImportError:
        print("  (../taoist-oracle absent — CNY astronomical check skipped)")

    print(f"  {n} days × 8 birth slots × 12 branches × 12 signs, {len(births)} finder births")
    if fails:
        print("FAIL")
        for f in fails[:25]:
            print("  ", f)
        sys.exit(1)
    print("OK — horo.js agrees with make_horo.py, and the tradition holds")


if __name__ == "__main__":
    main()
