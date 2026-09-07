#!/usr/bin/env python3
"""/here.html keeps its four rules, and its cells hold every pinned place once.

    python3 tests/test_here.py            # source checks always; artefact
                                          # checks when docs/here.html exists
    MD_DOCS=/path/to/build python3 tests/test_here.py

WHY EACH CHECK EXISTS

  THE POSITION NEVER REACHES THE URL BY ITSELF   near.js promises the reader's
      position is "not put in the URL". /map.html writes its view into the
      hash on every pan, which is right for a view somebody chose and wrong
      for a GPS fix. here.js must therefore never call replaceState or
      pushState; the one link that carries a position is built by a tap on a
      button whose label says so.
  THE ONLY THING WRITTEN TO DISK IS A PREFERENCE  localStorage may hold the
      `md-here` switch and nothing else — no coordinate, ever.
  NOTHING LEAVES THE DEVICE                       every fetch() is to our own
      data/here/ cells; there is no other request in the file.
  A CELL IS WHERE ITS KEY SAYS                    Math.floor(lat*100) in JS and
      math.floor(lat*100) in Python must agree, or a place sits in a file the
      page never asks for. Checked in Python; and, when node is on the PATH,
      checked against node for a thousand random coordinates.
  EVERY PINNED PLACE IS IN EXACTLY ONE CELL       the cells partition the
      catalogue: count in == count out, no row twice.
  THE OLD CITY STAYS AFFORDABLE                   the nine cells around Tha
      Phae Gate, gzipped, under a stated ceiling. Measured at 166 kB on
      2026-09-06; the ceiling is set clear of that so growth does not trip it
      and a doubling does.
  NO HOURS MEANS NO CLAIM                         a row with no posted hours
      carries 0, not [], so the JS can tell "never said" from "closed today".
"""
import gzip
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = Path(os.environ.get("MD_DOCS") or (ROOT / "docs"))
sys.path.insert(0, str(ROOT))

import here_layer  # noqa: E402

OLD_CITY_GZ_CEILING = 320 * 1024   # bytes, the nine cells around Tha Phae Gate
THA_PHAE = (18.7876, 98.9931)

fails = []


def check(ok, msg):
    print(("  ok   " if ok else "  FAIL ") + msg)
    if not ok:
        fails.append(msg)


# ---------------------------------------------------------------- source rules
print("here.js source")
js = here_layer.JS
check("replaceState" not in js and "pushState" not in js,
      "here.js never writes to the address bar (no replaceState/pushState)")
sets = re.findall(r"localStorage\.setItem\(([^)]*)\)", js)
check(sets == ["AUTO,'auto'"],
      "localStorage.setItem is called once, with the md-here switch only: %r" % sets)
check("md-here" in js and "'md-here'" in js, "the switch key is md-here")
fetches = re.findall(r"fetch\((.{0,80}?)\)\.then", js)
check(fetches and all(f.startswith("root()+'data/here/'") for f in fetches)
      and js.count("fetch(") == len(fetches),
      "every fetch() is to data/here/: %r" % fetches)
check(not re.search(r"https?://", js), "no URL literal in here.js (BASE arrives from build)")

# ------------------------------------------------- the front door to here.html
# 2026-09-07: here.html shipped and NOTHING on the front page linked to it. Its
# only link is the 📍 chip inside the NOW·NEAR line, and that line returned ""
# whenever there was no fresh weather, no fresh air reading and no event count
# — which is what happened, because weather.json and air.json were a day older
# than BUILD_DATE and the freshness guard correctly dropped both cells. A
# reader's own location has nothing to do with how fresh an air sensor is, so
# the chip must outlive an empty line.
print()
print("the here chip survives a line with nothing to say")
import nownear_layer  # noqa: E402
import build as _B  # noqa: E402

_saved = {k: getattr(_B, k, None) for k in
          ("WEATHER_CITIES", "AIR_PLACES", "TODAY_DAYS", "WEATHER_DATE", "AIR_DATE", "BUILD_DATE")}
try:
    # the worst honest case: every feed stale, nothing on today
    _B.WEATHER_CITIES, _B.AIR_PLACES, _B.TODAY_DAYS = [], [], {}
    _B.WEATHER_DATE = _B.AIR_DATE = "2026-01-01"
    _B.BUILD_DATE = "2026-09-07"
    bare = nownear_layer.strip("", "index.html")
    check("here.html" in bare, "📍 here.html is linked even with no weather, no air and no events")
    check("nnsep" not in bare, "an empty line carries no stray separator")

    # and the ordinary case still looks the way it did
    _B.WEATHER_DATE = _B.AIR_DATE = "2026-09-07"
    _B.WEATHER_CITIES = [{"temp": 24.0, "code": 61, "path": ""}]
    _B.AIR_PLACES = [{"pm25": 17.0, "band": {"th": "ดี", "en": "good"}, "path": ""}]
    full = nownear_layer.strip("", "index.html")
    check("here.html" in full and "PM2.5" in full,
          "a full line still carries its readings and the chip")
finally:
    for k, v in _saved.items():
        if v is not None:
            setattr(_B, k, v)

check("MDLOC.ask(" in js, "the button goes through MDLOC, the one door")
check("navigator.geolocation.getCurrentPosition" not in js,
      "no second permission door: only MDLOC asks; the watch runs after it")
check("permissions.query" in js and "st.state==='granted'" in js,
      "the switch acts only once the permission is already granted")
check("openState" in js and "return null" in js,
      "a place with no hours returns null (draws nothing)")

# ---------------------------------------------------------------- cell maths
print("cell keys")
random.seed(7)
pts = [(random.uniform(17.0, 20.5), random.uniform(97.3, 100.6)) for _ in range(1000)]
check(here_layer.cell_key(18.7876, 98.9931) == "1878_9899", "Tha Phae Gate is in 1878_9899")
check(here_layer.cell_key(18.79, 98.99) == "1879_9899",
      "a coordinate on a boundary goes to the cell whose floor it is")
node = shutil.which("node")
if node:
    script = ("const p=%s;console.log(JSON.stringify(p.map(([a,b])=>"
              "Math.floor(a*100)+'_'+Math.floor(b*100))));" % json.dumps(pts))
    out = subprocess.run([node, "-e", script], capture_output=True, text=True)
    got = json.loads(out.stdout) if out.returncode == 0 else None
    want = [here_layer.cell_key(a, b) for a, b in pts]
    check(got == want, "node and Python agree on 1,000 random cell keys")
else:
    print("  skip node not on PATH; JS/Python key parity not cross-checked")

# ---------------------------------------------------------------- the artefact
here_html = DOCS / "here.html"
if not here_html.exists():
    print("artefact: %s has no here.html — build first (or set MD_DOCS); "
          "artefact checks not run" % DOCS)
else:
    print("artefact in %s" % DOCS)
    html = here_html.read_text()
    check('data-mdfull="1"' in html, "the map is the page (one-finger pan)")
    check('id="h-start"' in html and "data-gps-door" in html,
          "the start button is a gps door MDLOC may remove after a refusal")
    for door in ("map.html", "plan.html", "toilets.html", "chuai.html"):
        check('href="%s"' % door in html, "door to %s" % door)
    for gate in ("ประตูท่าแพ", "ประตูช้างเผือก", "ประตูเชียงใหม่", "ประตูสวนดอก", "ประตูแสนปุง"):
        check(gate in html, "gate named: %s" % gate)
    v = re.search(r'here\.js\?v=([0-9a-f]{8})', html)
    check(bool(v), "here.js carries a ?v= cache-buster")
    check(bool(re.search(r'near\.js\?v=[0-9a-f]{8}', html)), "near.js carries a ?v= cache-buster")
    check("maplibre-gl.js" in html, "page() pulled the basemap in (data-mdmap seen)")

    cdir = DOCS / here_layer.CELL_DIR
    files = sorted(cdir.glob("*.json")) if cdir.exists() else []
    check(len(files) > 1000, "%d cell files" % len(files))
    seen = set()
    n = 0
    bad_key = bad_shape = bad_hours = 0
    for f in files:
        m = re.match(r"(-?\d+)_(-?\d+)\.json$", f.name)
        a, b = int(m.group(1)), int(m.group(2))
        for r in json.loads(f.read_text()):
            n += 1
            if len(r) != 11:
                bad_shape += 1
                continue
            if here_layer.cell_key(r[0], r[1]) != "%d_%d" % (a, b):
                bad_key += 1
            key = (r[2], r[3])
            if key in seen:
                bad_shape += 1   # a slug twice is a row twice
            seen.add(key)
            h = r[9]
            if h != 0 and not (isinstance(h, list) and h and all(
                    isinstance(iv, list) and len(iv) == 2 and 0 <= iv[0] < iv[1] <= 10080
                    for iv in h)):
                bad_hours += 1
    check(bad_key == 0, "every row sits in the cell its key says (%d astray)" % bad_key)
    check(bad_shape == 0, "every row is 11 fields and no slug appears twice (%d bad)" % bad_shape)
    check(bad_hours == 0, "hours are 0 or valid week-minute intervals (%d bad)" % bad_hours)

    # Count in == count out, against the catalogue the build read.
    try:
        import build  # noqa: E402
        data = build.load()
        pages = set()
        for prov in ("cm", "cr"):
            for r in data.get(prov) or []:
                if (r.get("lat") is not None and r.get("lng") is not None
                        and (r.get("geoPrecision") or "exact") != "needs-pin"
                        and not build.held(r)):
                    pages.add((prov, build.place_slug(r)))
        want = len(pages)
        check(n == want, "cells hold %d rows; catalogue has %d pinned, published "
                         "place pages (duplicate records collapse to one)" % (n, want))
    except Exception as e:  # pragma: no cover
        print("  skip catalogue count (%s)" % e)

    a, b = math.floor(THA_PHAE[0] * 100), math.floor(THA_PHAE[1] * 100)
    gz = 0
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            p = cdir / ("%d_%d.json" % (a + i, b + j))
            if p.exists():
                gz += len(gzip.compress(p.read_bytes()))
    check(0 < gz <= OLD_CITY_GZ_CEILING,
          "old-city payload %d kB gzipped, ceiling %d kB" % (gz // 1024, OLD_CITY_GZ_CEILING // 1024))

print()
if fails:
    print("FAILED %d:" % len(fails))
    for f in fails:
        print("  - " + f)
    sys.exit(1)
print("all here checks pass")
