#!/usr/bin/env python3
"""Bake one accepted ride into the dash app's assets.

The view carries no router and no catalogue — only the ride it was built with.
That is what lets it be a one-megabyte app that works with the phone in
aeroplane mode on a road with no signal.

A REFUSED PLAN CANNOT BE BAKED. `ride_plan.py` decides whether a route keeps
the standing rules; this script's job is to make sure a route that failed that
test can never reach the screen, because a rider following the arrow has no way
to know the rules were broken when it was made.

  python3 dash/build_data.py --ride wat-chiang-yuen-to-thapae
  python3 dash/build_data.py --stop 18.7963,98.9888 --stop 18.7878,98.9933

Writes dash/www/data/ride.js. Run dash/build_apk.py after it.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "importers"))

import ride_plan  # noqa: E402

OUT = HERE / "www" / "data" / "ride.js"

# What the view actually reads. The plan file also carries the leg breakdown and
# the full findings list, which are for a person reading a report rather than a
# rider reading a screen, so they stay out of the asset.
KEEP = ("ok", "mode", "metres", "km", "stops", "line", "cues", "named_from",
        "kind", "direction", "turn_deg", "perimeter_km", "moat_crossings")


# Rules that a person may consciously set aside, and nothing else. `turning` is
# here because เวียนขวา turned out not to be rideable on the moat ring — the
# one-way system runs the other way — so the choice between not lapping at all
# and lapping the other way is hers to make, and she made it.
#
# `quarter` and `gate` are deliberately NOT waivable, and that is the whole
# point of having a list rather than a --force. Those two are about where the
# ride goes; this one is about which way round it runs. A waiver wide enough to
# cover the first two would make the gate decorative.
WAIVABLE = ("turning",)


def bake(plan, name, waive=()):
    waive = tuple(w for w in waive if w in WAIVABLE)
    broken = [f for f in (plan.get("rules") or {}).get("findings", [])
              if not f.get("notice")]
    unwaived = [f for f in broken if f.get("rule") not in waive]

    if plan.get("error") or unwaived or (not plan.get("ok") and not broken):
        first = unwaived[0] if unwaived else (
            (plan.get("rules") or {}).get("first_finding"))
        why = plan.get("why_en") or (first or {}).get("why_en") or plan.get("error")
        extra = ""
        if first and first.get("rule") in WAIVABLE:
            extra = f"\n  it can be set aside on purpose: --waive {first['rule']}"
        sys.exit(f"refused, so nothing was written: {why}{extra}")

    slim = {k: plan[k] for k in KEEP if k in plan}
    slim["name"] = name
    if broken:
        # Written into the asset the app ships, not just printed here. A rule
        # set aside months ago should still be visible to whoever next reads
        # the ride, including on the phone.
        slim["waived"] = sorted({f["rule"] for f in broken})
        slim["waived_why"] = [f.get("why_en") for f in broken]
        slim["ok"] = True
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("window.RIDE=" + json.dumps(slim, ensure_ascii=False,
                                               separators=(",", ":")) + ";\n")
    return slim


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ride", help="a plan already in data/rides/")
    ap.add_argument("--stop", action="append", default=[], metavar="LAT,LNG")
    ap.add_argument("--mode", default="ride", choices=("ride", "foot"))
    ap.add_argument("--name", default=None)
    ap.add_argument("--waive", action="append", default=[], metavar="RULE",
                    help="set aside a waivable rule on purpose: " +
                         ", ".join(WAIVABLE))
    args = ap.parse_args()

    if args.ride:
        p = ROOT / "data" / "rides" / f"{args.ride}.json"
        if not p.exists():
            sys.exit(f"no such ride: {p.relative_to(ROOT)}")
        plan = json.loads(p.read_text())
        name = args.name or args.ride
    elif args.stop:
        stops = [tuple(float(x) for x in s.split(",")) for s in args.stop]
        plan = ride_plan.plan(stops, mode=args.mode)
        name = args.name or "ride"
    else:
        sys.exit("give --ride NAME or at least two --stop LAT,LNG")

    slim = bake(plan, name, waive=args.waive)
    kind = slim.get("kind") or "ride"
    extra = f" {slim['direction']}" if slim.get("direction") else ""
    print(f"{name}: {kind}{extra}, {slim['km']} km, {len(slim['line'])} points, "
          f"{len(slim['cues'])} cues")
    if slim.get("waived"):
        print("  set aside on purpose: " + ", ".join(slim["waived"]))
        for w in slim.get("waived_why", []):
            print(f"    — {w}")
    print(f"wrote {OUT.relative_to(ROOT)}  ({OUT.stat().st_size / 1000:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
