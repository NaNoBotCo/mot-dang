#!/usr/bin/env python3
"""The front page A/B (Nan, 2026-10-02): the 14-day calendar first, or the map first.

Each browser draws one arm (assets/front/index.html, localStorage md-home-ab) and every
beacon the front page sends carries it as the page: /ab/cal or /ab/map. People only.

  seen      a front page opened in that arm (ab:seen, once a load)
  engaged   a load with any tap: a day, an event, the map, the toggle, a link (ab:engaged)
  ev        an event opened anywhere on the page
  map       a first touch on the map
  to-map / to-cal   the toggle, by hand
  go        a link followed off the front page
  ahead     a tap in Plan ahead: a festival card, add to calendar

The score is engaged ÷ seen. A load is a page view, not a person: one reader opening the
page five times counts five.

  python3 ab_home.py [--since 2026-10-11]

The calendar arm changed on 2026-10-11 (the three bands, Nan's word): the count starts again
that day. --since 2026-10-02 reads the first calendar's run.
"""
import argparse
import datetime as dt
import math
import pathlib

from traffic import sql

OUT = pathlib.Path.home() / "Desktop/1 — NEXT UP/AB — calendar or map first.txt"
START = "2026-10-11"
KEYS = ["seen", "engaged", "ev", "ahead", "map-touch", "to-map", "to-cal", "go"]


def counts(since):
    rows = sql("SELECT blob12 pg, blob11 k, SUM(_sample_interval * double5) AS n FROM traffic_eye "
               f"WHERE blob1 = 'motdang.net' AND blob4 = '/api/map' AND blob2 = 'human' "
               f"AND blob12 IN ('/ab/cal', '/ab/map') AND timestamp >= toDateTime('{since} 00:00:00') "
               "GROUP BY pg, k")
    c = {"cal": dict.fromkeys(KEYS, 0), "map": dict.fromkeys(KEYS, 0)}
    for r in rows:
        arm, k, n = r["pg"][4:], r["k"], int(float(r["n"]))
        k = "ev" if k.startswith("ev:") else k[3:] if k.startswith("ab:") else None
        if k in c[arm]:
            c[arm][k] += n
    return c


def z(a, na, b, nb):
    """Two proportions; the chance a gap this size shows up with no difference at all."""
    if not na or not nb:
        return None
    p = (a + b) / (na + nb)
    se = math.sqrt(p * (1 - p) * (1 / na + 1 / nb)) if 0 < p < 1 else 0
    return math.erfc(abs(a / na - b / nb) / se / math.sqrt(2)) if se else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default=START)
    a = ap.parse_args()
    c = counts(a.since)
    days = (dt.date.today() - dt.date.fromisoformat(a.since)).days + 1
    L = [f"FRONT PAGE A/B — calendar first or map first · since {a.since} ({days} days) · people only", ""]
    L.append(f"{'':22}{'calendar first':>16}{'map first':>12}")
    for k in KEYS:
        L.append(f"{k:22}{c['cal'][k]:>16}{c['map'][k]:>12}")
    L.append("")
    rate = {arm: (c[arm]["engaged"] / c[arm]["seen"] if c[arm]["seen"] else None) for arm in c}
    if rate["cal"] is None or rate["map"] is None:
        L.append("No loads yet in one or both arms.")
    else:
        L.append(f"Tapped something:  calendar first {rate['cal']:.0%} of {c['cal']['seen']} loads · "
                 f"map first {rate['map']:.0%} of {c['map']['seen']} loads")
        p = z(c["cal"]["engaged"], c["cal"]["seen"], c["map"]["engaged"], c["map"]["seen"])
        if p is not None:
            lead = "calendar first" if rate["cal"] > rate["map"] else "map first"
            L.append(f"Chance the gap is luck: {p:.0%}" + (f" — {lead} leads" if p < 0.05 else " — too close to call"))
        # loads per arm to see a 10-point gap at this rate (80% power, 5% level)
        pb = (rate["cal"] + rate["map"]) / 2
        need = math.ceil(2 * (1.96 + 0.84) ** 2 * pb * (1 - pb) / 0.10 ** 2) if 0 < pb < 1 else None
        if need:
            L.append(f"Loads needed per arm to see a 10-point gap: about {need}")
    OUT.write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
