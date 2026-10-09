#!/usr/bin/env python3
"""loo_road: road distance to toilets, both halves.

1 · the build side: a place's nearest toilet by road is never nearer than the
    crow, and a point with no road near it gets no named toilet.
2 · the browser side (road-near.js, run in node over cache/road_tiles):
    road ≥ crow, scooter ≥ walker on the moat's one-way ring, the route drawn
    starts at the origin and ends at the toilet.

Needs cache/road_tiles and cache/road_graph_prov.json
(importers/build_road_tiles.py); skips, saying so, without them.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import loo_road  # noqa: E402

FAIL = []


def check(ok, what):
    print(("  ok   " if ok else "  FAIL ") + what)
    if not ok:
        FAIL.append(what)


def main():
    if not loo_road.GRAPH.exists() or not (loo_road.TILES / "index.json").exists():
        print("skip: no road squares — run importers/build_road_tiles.py")
        return 0

    print("1 · build side")
    doors = [(18.79036, 98.98845, {"id": "a", "e": "🛕", "th": "ก", "en": "A", "href": "cm/p/a"}),
             (18.78560, 98.99800, {"id": "b", "e": "⛽", "th": "ข", "en": "B", "href": "cm/p/b"})]
    loo_road.prepare(doors)
    for q in [(18.7877, 98.9933), (18.7930, 98.9800), (18.7860, 99.0010)]:
        hit = loo_road.nearest(*q)
        check(hit is not None, f"a toilet by road from {q}")
        if hit:
            crow = min(loo_road._hav(q[0], q[1], d[0], d[1]) for d in doors)
            check(hit[0] >= crow - 1, f"road {hit[0]:.0f} m ≥ crow {crow:.0f} m")
    check(loo_road.nearest(19.70, 98.20) is None, "no road data → no named toilet")

    print("2 · browser side")
    if not shutil.which("node"):
        print("  skip: no node")
        return 1 if FAIL else 0
    with tempfile.TemporaryDirectory() as td:
        js = Path(td) / "road-near.js"
        js.write_text(loo_road.JS)
        runner = Path(td) / "run.js"
        runner.write_text(r"""
const fs=require('fs'),path=require('path');const D=process.argv[2];
global.document={currentScript:{src:'/x/road-near.js'}};global.window={};
global.fetch=u=>{const f=path.join(D,u.replace('/x/data/roads/',''));
  return Promise.resolve(fs.existsSync(f)?{ok:true,json:()=>Promise.resolve(JSON.parse(fs.readFileSync(f)))}:{ok:false});};
require(process.argv[3]);
(async()=>{const out=[];for(const [a,b,mode] of JSON.parse(process.argv[4])){
  const R=await window.MDROAD.from(a[0],a[1],{mode,reach:8000});
  out.push(R?{m:R.to(b[0],b[1]),p:R.path(b[0],b[1])}:null);}
  console.log(JSON.stringify(out));})();
""")
        a, b = (18.78776, 98.99327), (18.7840, 98.9990)
        pairs = [[a, b, "foot"], [a, b, "ride"], [(19.70, 98.20), b, "foot"]]
        res = json.loads(subprocess.check_output(
            ["node", str(runner), str(loo_road.TILES), str(js), json.dumps(pairs)]))
        crow = loo_road._hav(*a, *b)
        foot, ride, none = res
        check(foot and foot["m"] and foot["m"] >= crow, f"walk {foot and foot['m']:.0f} m ≥ crow {crow:.0f} m")
        check(ride and ride["m"] and ride["m"] >= foot["m"], f"scooter {ride and ride['m']:.0f} m ≥ walk (one-way ring)")
        p = foot["p"]
        check(p and abs(p[0][0] - a[0]) < 1e-6 and abs(p[-1][0] - b[0]) < 1e-6,
              "route starts at the origin and ends at the toilet")
        check(none is None, "no road data → null, the page falls back to straight-line")
    print("FAIL" if FAIL else "loo_road: all checks pass")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
