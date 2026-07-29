#!/usr/bin/env python3
"""Bake the sky widget: the moon's phase and Jupiter's four Galilean moons.

Neither number is invented here. Both come from sibling projects that already
own the maths and have tests around it:

  * ../jovilabe    — the geared Jupiter instrument. jove.observe() returns the
                     satellites' sky-plane positions in Jupiter radii from a
                     real ephemeris fit, which is what the disc needs.
  * lunation       — the mean-synodic phase formula shared with coucal-clock
                     and wichaa.net/moon, so all three agree.

Those repos are the source of truth; this writes their answers into
data/sky.json so mot-dang's own build never has to import across repositories.
Bake a month at a time and the tile is correct every day without a rebuild.

    python3 importers/make_sky.py             # 30 days from today
    python3 importers/make_sky.py --days 60

If jovilabe is not on disk the Jupiter half is skipped and the moon half still
writes — the widget degrades to one slide rather than failing the build.
"""
import json
import math
import os
import sys
from datetime import date, datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sky.json")
JOVILABE = os.path.abspath(os.path.join(ROOT, "..", "jovilabe"))

MOONS = [("Io", "ไอโอ"), ("Europa", "ยูโรปา"), ("Ganymede", "แกนีมีด"), ("Callisto", "คัลลิสโต")]

# Same epoch and synodic month as coucal-clock's lunation.py and the moondial —
# they must agree or three of this operator's projects start contradicting each
# other about the same sky.
SYNODIC = 29.530588853
EPOCH_NEW_MOON_JD = 2451550.09766


def jd_of(dt):
    return 2440587.5 + dt.replace(tzinfo=timezone.utc).timestamp() / 86400.0


def moon_for(dt):
    age = (jd_of(dt) - EPOCH_NEW_MOON_JD) % SYNODIC
    frac = age / SYNODIC
    illum = (1 - math.cos(2 * math.pi * frac)) / 2
    if frac < 0.03 or frac > 0.97:
        th, en = "เดือนดับ", "New moon"
    elif abs(frac - 0.25) < 0.03:
        th, en = "ข้างขึ้นครึ่งดวง", "First quarter"
    elif abs(frac - 0.5) < 0.03:
        th, en = "เดือนเพ็ญ", "Full moon"
    elif abs(frac - 0.75) < 0.03:
        th, en = "ข้างแรมครึ่งดวง", "Last quarter"
    elif frac < 0.5:
        th, en = "ข้างขึ้น", "Waxing"
    else:
        th, en = "ข้างแรม", "Waning"
    # Thai lunar reckoning: ขึ้น ๑–๑๕ ค่ำ waxing, then แรม ๑–๑๕ ค่ำ waning.
    # Proportional within each half rather than counting whole days, so the
    # full moon lands on ขึ้น ๑๕ instead of drifting a day.
    half = SYNODIC / 2
    waxing = frac < 0.5
    within = age if waxing else age - half
    thai_day = max(1, min(15, int(within / half * 15) + 1))
    # วันพระ — the Buddhist observance days, 8th and 15th of each half.
    wan_phra = thai_day in (8, 15)
    return {"age": round(age, 3), "frac": round(frac, 5),
            "illum": round(illum, 4), "phase_th": th, "phase_en": en,
            "waxing": waxing, "thai_day": thai_day, "wan_phra": wan_phra,
            "thai_label_th": f'{"ขึ้น" if waxing else "แรม"} {thai_day} ค่ำ',
            "thai_label_en": f'{"waxing" if waxing else "waning"} day {thai_day}'}


def jupiter_for(dt):
    try:
        import jove
    except ImportError:
        return None
    v = jove.observe(jd_of(dt), "earth")
    sats = []
    for i, (en, th) in enumerate(MOONS):
        sats.append({"en": en, "th": th,
                     "x": round(v.x[i], 4),      # along Jupiter's equator, in radii
                     "y": round(v.y[i], 4),      # perpendicular, in radii
                     "front": bool(v.z[i] < 0)})  # nearer to us than Jupiter
    return {"tilt": round(v.tilt, 4), "dist_au": round(v.dist, 4), "sats": sats}


def main():
    days = 30
    if "--days" in sys.argv:
        days = int(sys.argv[sys.argv.index("--days") + 1])
    if os.path.isdir(JOVILABE) and JOVILABE not in sys.path:
        sys.path.insert(0, JOVILABE)

    today = date.today()
    out, have_jup = {}, 0
    for i in range(days):
        d = today + timedelta(days=i)
        dt = datetime(d.year, d.month, d.day, 20, 0)  # a viewing hour, not midnight
        entry = {"moon": moon_for(dt)}
        j = jupiter_for(dt)
        if j:
            entry["jupiter"] = j
            have_jup += 1
        out[d.isoformat()] = entry

    with open(OUT, "w") as fh:
        json.dump({"generated": today.isoformat(), "days": out}, fh,
                  ensure_ascii=False, indent=1)
    print(f"🐜 sky for {len(out)} day(s), {have_jup} with Jupiter -> {OUT}")
    if not have_jup:
        print("⚠  jovilabe not importable — moon only. Expected at " + JOVILABE)


if __name__ == "__main__":
    main()
