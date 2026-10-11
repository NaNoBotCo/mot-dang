#!/usr/bin/env python3
"""Hold /wats to the four things the page it replaced got wrong.

  1. A STOP IS A WAT. Named วัด or Wat at the head of its own name, from an
     OSM record, never a `geoPrecision: approx` pin at a tambon centroid. The
     published nine-temple rounds carried a Hindu temple, a Chinese shrine, a
     meditation association, a Buddhist hall and an unnamed node.
  2. NINE DIFFERENT WATS, ONCE EACH. Nine stops that are nine wats, and no wat
     on two rounds.
  3. THE ORDER IS THE SHORTEST ONE. The order is rebuilt here from the graph,
     exactly, and has to agree with what shipped — an approximation that lands
     one swap away sends a reader round a block twice.
  4. THE LINE IS THE WALK. Every leg carries the line it is walked along and
     its drawn length matches the metres charged for it, so no leg is a
     straight line through a block.

And, when a build is on disk (MD_DOCS, or docs/): the pages exist, each wat
page names its own wat, and nothing still links to /merit.html.

    python3 tests/test_wats.py
    MD_DOCS=/path/to/docs.scratch python3 tests/test_wats.py
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "importers"))
sys.path.insert(0, str(ROOT))
from routing import Graph, hav                       # noqa: E402
import build_wats as BW                              # noqa: E402

DOCS = Path(os.environ.get("MD_DOCS") or (ROOT / "docs"))
DATA = ROOT / "data" / "wats.json"

FAILED = []


def check(label, ok, detail=""):
    print("  %s  %s%s" % ("ok  " if ok else "FAIL", label,
                          ("  — " + detail) if detail else ""))
    if not ok:
        FAILED.append(label)


def main():
    if not DATA.exists():
        print("no data/wats.json — run importers/build_wats.py first")
        return 1
    doc = json.loads(DATA.read_text())
    rounds = doc.get("rounds") or []
    wats = doc.get("wats") or []
    recs = {r["id"]: r for r in
            json.loads((ROOT / "data" / "canonical" / "cm.json").read_text())}

    print("the set: %d wats, %d rounds" % (len(wats), len(rounds)))
    stops = [s for r in rounds for s in r["stops"]]
    bad_name = [s["name"] for s in stops
                if not re.match(r"^\s*(วัด|Wat\b)",
                                (s.get("name") or s.get("nameTh")
                                 or s.get("nameEn") or "").strip(), re.I)]
    check("every stop is named as a wat", not bad_name, ", ".join(bad_name[:4])
          or "%d stops" % len(stops))
    approx = [s["id"] for s in stops
              if (recs.get(s["id"]) or {}).get("geoPrecision") == "approx"]
    check("no stop is a tambon-centroid pin", not approx, ", ".join(approx[:3]))
    off_map = [s["id"] for s in stops if "-osm-" not in s["id"]]
    check("every stop comes from the map", not off_map, ", ".join(off_map[:3]))
    listed = [w["name"] for w in wats
              if not re.match(r"^\s*(วัด|Wat\b)",
                              (w.get("name") or "").strip(), re.I)]
    check("every wat in the list is named as a wat", not listed,
          ", ".join(listed[:4]) or "%d wats" % len(wats))

    print("\nnine, once each")
    dupe_in = [r["slug"] for r in rounds
               if len({s["id"] for s in r["stops"]}) != 9]
    check("nine different wats in a round", not dupe_in, ", ".join(dupe_in))
    seen, twice = set(), []
    for s in stops:
        if s["id"] in seen:
            twice.append(s["id"])
        seen.add(s["id"])
    check("no wat on two rounds", not twice, ", ".join(twice[:3]))

    print("\nthe order and the line")
    g = Graph.load()
    if g is None:
        check("the road graph loads", False, "no data/road_graph.json")
    else:
        on_foot = g.main_component("foot")
        worse = []
        for r in rounds:
            pts = [(s["lat"], s["lng"]) for s in r["stops"]]
            m = g.matrix(pts, "foot", on_foot)
            shipped = sum(m[i][(i + 1) % 9] for i in range(9)
                          if m[i][(i + 1) % 9] is not None)
            best = BW.best_cycle(m)
            ideal = sum(m[best[i]][best[(i + 1) % 9]] for i in range(9)
                        if m[best[i]][best[(i + 1) % 9]] is not None)
            if shipped > ideal + 1.0:
                worse.append("%s %d m over" % (r["slug"], round(shipped - ideal)))
        check("the shipped order is the shortest one", not worse,
              "; ".join(worse) or "%d rounds solved again" % len(rounds))

    short, straight = [], []
    for r in rounds:
        for i, leg in enumerate(r.get("foot_legs") or []):
            where = "%s leg %d" % (r["slug"], i + 1)
            line = leg.get("line") or []
            if len(line) < 2:
                short.append(where)
                continue
            drawn = sum(hav(line[k], line[k + 1]) for k in range(len(line) - 1))
            drawn += sum(leg.get("snap") or [])
            m = leg.get("m") or 0
            # The road line plus the two walk-ins from the pins is the whole
            # journey the metres are charged for. Before the walk-ins were
            # baked in, four short legs read as 74-78% drawn and the missing
            # quarter was the walk from the pin to the street.
            if m > 120 and drawn < m * 0.95:
                straight.append("%s %d%%" % (where, round(100.0 * drawn / m)))
    check("every leg carries its line", not short, "; ".join(short[:4]))
    check("the line covers the metres it charges for", not straight,
          "; ".join(straight[:4]) or "all legs ≥ 95%")

    print("\nwhat a round claims")
    bad_mode = []
    for r in rounds:
        legs = [x["m"] for x in r["foot_legs"] if x["m"] is not None]
        if r["mode"] == "foot":
            if max(legs) > BW.FOOT_LEG_M or sum(legs) > BW.FOOT_ROUND_M:
                bad_mode.append("%s says foot at %d m" % (r["slug"], sum(legs)))
        elif (r.get("ride_m") or 0) > BW.RIDE_ROUND_M or not r.get("ride_m"):
            bad_mode.append("%s rides %s m" % (r["slug"], r.get("ride_m")))
    check("a round only claims a walk it is", not bad_mode, "; ".join(bad_mode))

    if (DOCS / "wats" / "index.html").exists():
        print("\nthe pages, in %s" % DOCS.name)
        missing = [r["slug"] for r in rounds
                   if not (DOCS / "wats" / (r["slug"] + ".html")).exists()]
        check("a page per round", not missing, ", ".join(missing))
        pages = list((DOCS / "wats" / "w").glob("*.html"))
        check("a page per wat", len(pages) == len(wats),
              "%d pages, %d wats" % (len(pages), len(wats)))
        left = []
        for p in list((DOCS / "wats").rglob("*.html")) + [DOCS / "index.html"]:
            if "merit.html" in p.read_text():
                left.append(p.name)
        check("nothing links to the retired page", not left, ", ".join(left[:4]))
        idx = (DOCS / "wats" / "index.html").read_text()
        check("the index says the order is not a ranking",
              "ทางเดินที่สั้นที่สุด" in idx or "shortest way round" in idx)
    else:
        print("\nno build in %s — skipped the page checks" % DOCS)

    print("\n%s" % ("FAILED: " + "; ".join(FAILED) if FAILED else "all ok"))
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
