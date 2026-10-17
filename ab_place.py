#!/usr/bin/env python3
"""Photo or drawing on a place page (Nan, 2026-10-15: "Let's a/b test which does better ... based on
photo v doodle. maybe no difference idk").

A place in data/curated/photo_doodle_ab.json shows each browser its photograph or its doodler
portrait at random (build.py photo_doodle_ab). Every beacon from that page carries the arm as the
page: /ab/<tag>/photo or /ab/<tag>/doodle. People only.

  seen       the page opened in that arm, once a load
  contact    a load with a tap on phone, Facebook, website, email, Grab, Guide me here or a map
  engaged    a load with any of those or the LINE share
  phone · facebook · website · email · grab · guide · maps · share-line   taps, each

The score is contact ÷ seen. A load is a page view, not a person.

  python3 ab_place.py [--tag cmds] [--since 2026-10-15]
"""
import argparse
import datetime as dt
import math
import pathlib

from ab_home import z
from traffic import sql

OUT = pathlib.Path.home() / "Desktop/1 — NEXT UP/AB — photo or drawing.txt"
START = "2026-10-15"
KEYS = ["seen", "contact", "engaged", "phone", "facebook", "website", "email", "grab", "guide", "maps", "share-line"]


def counts(tag, since):
    rows = sql("SELECT blob12 pg, blob11 k, SUM(_sample_interval * double5) AS n FROM traffic_eye "
               f"WHERE blob1 = 'motdang.net' AND blob4 = '/api/map' AND blob2 = 'human' "
               f"AND blob12 IN ('/ab/{tag}/photo', '/ab/{tag}/doodle') AND timestamp >= toDateTime('{since} 00:00:00') "
               "GROUP BY pg, k")
    c = {"photo": dict.fromkeys(KEYS, 0), "doodle": dict.fromkeys(KEYS, 0)}
    for r in rows:
        arm, k = r["pg"].rsplit("/", 1)[1], r["k"][3:] if r["k"].startswith("ab:") else ""
        if k in c[arm]:
            c[arm][k] += int(float(r["n"]))
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="cmds")
    ap.add_argument("--since", default=START)
    a = ap.parse_args()
    if not a.tag.replace("-", "").isalnum():
        raise SystemExit("tag: letters, digits and hyphens")
    c = counts(a.tag, a.since)
    days = (dt.date.today() - dt.date.fromisoformat(a.since)).days + 1
    L = [f"PHOTO OR DRAWING — {a.tag} · since {a.since} ({days} days) · people only", ""]
    L.append(f"{'':14}{'photo':>8}{'drawing':>9}")
    for k in KEYS:
        L.append(f"{k:14}{c['photo'][k]:>8}{c['doodle'][k]:>9}")
    L.append("")
    rate = {arm: (c[arm]["contact"] / c[arm]["seen"] if c[arm]["seen"] else None) for arm in c}
    if rate["photo"] is None or rate["doodle"] is None:
        L.append("No loads yet in one or both arms.")
    else:
        L.append(f"Tapped to contact:  photo {rate['photo']:.0%} of {c['photo']['seen']} loads · "
                 f"drawing {rate['doodle']:.0%} of {c['doodle']['seen']} loads")
        p = z(c["photo"]["contact"], c["photo"]["seen"], c["doodle"]["contact"], c["doodle"]["seen"])
        if p is not None:
            lead = "photo" if rate["photo"] > rate["doodle"] else "drawing"
            L.append(f"Chance the gap is luck: {p:.0%}" + (f" — {lead} leads" if p < 0.05 else " — too close to call"))
        pb = (rate["photo"] + rate["doodle"]) / 2
        need = math.ceil(2 * (1.96 + 0.84) ** 2 * pb * (1 - pb) / 0.10 ** 2) if 0 < pb < 1 else None
        if need:
            L.append(f"Loads needed per arm to see a 10-point gap: about {need}")
    OUT.write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
