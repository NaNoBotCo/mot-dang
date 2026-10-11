#!/usr/bin/env python3
"""Every pin on every map lands where it says it is.

    python3 tests/test_map_sanity.py                   # the gate
    python3 tests/test_map_sanity.py --write-baseline  # re-record known rows

Nan, 2026-09-25: "the maps are diseased … Pls add basemaps and do sanity
checks everywhere." Putting real ground under the drawings showed what blank
paper hid: the แจ่งหัวลิน record is pinned at the middle of a 300 m wall ruin,
190 m east of the moat corner; Natural Earth names Chaiyaphum ชัยนาท; 307
records filed under Chiang Mai or Chiang Rai stand in Phrae, Lampang or
Sukhothai. Each check below is one of those classes.

HARD — fails the gate
  1. a record pin swapped (lat/lng), outside Thailand, or outside the cm-cr
     basemap fence
  2. a record pin more than OUTSIDE_KM outside its own province (Natural Earth
     admin-1, which is coarse: the tolerance covers it)
  3. a record more than STREET_KM from the street its own address names, where
     the street's geometry is held for the same province
  4. a curated map register off its own ground: a hot spring outside its
     province, the indigo route outside its country, the Tawai village
     outside Chiang Mai
  5. a drawn pin outside its SVG frame: every top-level page, every page of a
     site built in another repo and copied in from assets/<name>/ (the loop,
     muay-thai, roads, field, sites/…), and a fixed sample of the generated
     place and tag pages, which come from a few templates. Decorative art
     (aria-hidden) is not a map and is skipped.
  6. a basemap mount centred outside map_shell's fence
  7. a served GeoJSON point outside the fence ([lng, lat] order, so a swap
     lands in the sea and fails here)
  8. regional_ground: a Thai province name used twice
  9. a record named for the other province (Chiang Rai on a cm record, Chiang
     Mai on a cr one) still pinned within CITY_KM of its own city centre —
     derive.apply_pin_doubt marks those needs-pin

Checks 2, 3, 5 and 6b ratchet (5 keyed by page, 6b by folder). The rows standing on the day the gate went in are in
tests/map_sanity_known.json and are printed, not failed; a NEW row fails. A
known row that clears is reported so the file can shrink.

ADVISORY — printed
  - coordinates on a 1/256-degree grid (~430 m): a geocoder's rounding
  - a place joined to a same-named street in the other province
  - the moat ring's west and east sides more than 2° apart
"""
import json
import math
import os
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
DOCS = Path(os.environ.get("MD_DOCS") or (ROOT / "docs"))
KNOWN = ROOT / "tests" / "map_sanity_known.json"
OFF_FRAME = {}   # check 5's rows, for --write-baseline
NO_GROUND = {}   # check 6b's rows (by folder), for --write-baseline

import regional_ground as rg  # noqa: E402
sys.path.insert(0, str(ROOT / "tools"))
import holdback  # noqa: E402  a page or site held back this round is not read

THAILAND = (5.5, 97.2, 20.6, 105.7)          # S, W, N, E
FENCE = (17.0, 97.3, 20.5, 100.6)            # cm-cr.pmtiles extract
ISO = {"cm": "TH-50", "cr": "TH-57"}
OUTSIDE_KM = 3.0
STREET_KM = 2.0
SAMPLE = 400
# Check 9 (derive.apply_pin_doubt, 2026-09-25). Tha Phae Gate and the Chiang
# Rai clock tower. The two ids are Overture pages registered at a Chiang Mai
# tour office and pinned 161 m from the gate.
CITY = {"cm": (18.7877, 98.9933), "cr": (19.9072, 99.8309)}
CITY_KM = 15.0
OTHER = {"cm": "cr", "cr": "cm"}
NAMED = {"cm": r"chiang\s*-?\s*mai|chiangmai|เชียงใหม่",
         "cr": r"chiang\s*-?\s*rai|chiangrai|chaing\s*rai|เชียงราย"}
PIN_DOUBT_CASES = ("cm-ovt-8fbb1fff-4899-4d77-a6f9-80ba88cf8b44",   # Chiang Rai White Temple
                   "cm-ovt-fec3f686-4697-4625-8cd6-b74a3087b896")  # The Golden Triangle

FAILED, ADVISE = [], []
HELD_OK = set()   # failed labels whose every row is a page or site tools/holdback.py can hold


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILED.append(label)


def within(box, lat, lng):
    s, w, n, e = box
    return s <= lat <= n and w <= lng <= e


def seg_km(lat, lng, a, b):
    kx = math.cos(math.radians(lat)) * 111.32
    ax, ay = (a[1] - lng) * kx, (a[0] - lat) * 110.57
    bx, by = (b[1] - lng) * kx, (b[0] - lat) * 110.57
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / L))
    return math.hypot(ax + t * dx, ay + t * dy)


def line_km(lat, lng, runs):
    return min((seg_km(lat, lng, a, b) for run in runs for a, b in zip(run, run[1:])),
               default=1e9)


def outside_km(g, iso, lat, lng):
    """0 inside the province; else km to its nearest edge."""
    if rg.contains(g, iso, lat, lng):
        return 0.0
    prov = next(p for p in g["provinces"] if p["iso"] == iso)
    return line_km(lat, lng, [r + r[:1] for r in prov["rings"]])


def ratchet(name, found, known, fmt):
    """found: {id: detail}. Fails on ids not in known."""
    new = sorted(set(found) - set(known))
    gone = sorted(set(known) - set(found))
    check(f"{name}: no new rows", not new,
          f"{len(found)} standing, {len(found) - len(new)} known, {len(new)} new")
    for i in new[:25]:
        print("        new  " + fmt(i, found[i]))
    if gone:
        print(f"        {len(gone)} known row(s) cleared — rerun with --write-baseline to shrink the list")
    return new


def hold(label, paths, why):
    """Name a failed check's pages for tools/holdback.py (Nan, 2026-10-11)."""
    if paths and holdback.propose(paths, "map sanity: " + why):
        HELD_OK.add(label)


def main():
    write = "--write-baseline" in sys.argv
    known = json.loads(KNOWN.read_text()) if KNOWN.exists() and not write else {}
    known_notes = (json.loads(KNOWN.read_text()) if KNOWN.exists() else {}).get("_off_frame_notes", {})
    g = rg.load()
    recs = []
    for prov in ("cm", "cr"):
        p = ROOT / "data" / "canonical" / f"{prov}.json"
        if p.exists():
            recs += [dict(r, _prov=prov) for r in json.loads(p.read_text())]
    if not recs:
        print("no canonical data — run importers/import_all.py first")
        return 1
    pinned = [r for r in recs if r.get("lat") is not None and r.get("lng") is not None]

    print("1 · record pins")
    swapped = [r["id"] for r in pinned if 97 <= r["lat"] <= 106 and 5 <= r["lng"] <= 21]
    abroad = [r["id"] for r in pinned if not within(THAILAND, r["lat"], r["lng"])]
    fenced = [r["id"] for r in pinned if not within(FENCE, r["lat"], r["lng"])]
    check("no swapped lat/lng", not swapped, ", ".join(swapped[:5]))
    check("no pin outside Thailand", not abroad, ", ".join(abroad[:5]))
    check("no pin outside the basemap fence", not fenced, ", ".join(fenced[:5]))

    print(f"2 · record pins inside their own province (±{OUTSIDE_KM:g} km)")
    far_prov = {}
    if not g:
        check("regional ground present (importers/build_regional_ground.py)", False)
    else:
        for r in pinned:
            d = outside_km(g, ISO[r["_prov"]], r["lat"], r["lng"])
            if d > OUTSIDE_KM:
                far_prov[r["id"]] = (round(d, 1), r.get("nameTh") or r.get("name") or "")
        if not write:
            ratchet("outside own province", far_prov, known.get("outside_province", []),
                    lambda i, v: f"{i}  {v[0]} km out  {v[1]}")

    print(f"3 · a pin within {STREET_KM:g} km of the street its address names")
    far_street, cross = {}, 0
    streets = json.loads((ROOT / "data" / "streets.json").read_text())["streets"]
    by_id = {r["id"]: r for r in pinned}
    for st in streets:
        if not st.get("geom"):
            continue
        for pl in st.get("places", []):
            if pl.get("via") != "stated":
                continue
            r = by_id.get(pl["id"])
            if not r:
                continue
            if r["_prov"] != st.get("province"):
                cross += 1
                continue
            d = line_km(r["lat"], r["lng"], st["geom"])
            if d > STREET_KM:
                far_street[r["id"]] = (round(d, 1), st["name"])
    if not write:
        ratchet("far from the named street", far_street, known.get("far_from_street", []),
                lambda i, v: f"{i}  {v[0]} km from {v[1]}")
    if cross:
        ADVISE.append(f"{cross} place(s) joined to a same-named street in the other province "
                      "(data/streets.json keys streets by name across both)")

    print("4 · curated map registers on their own ground")
    if g:
        hs = json.loads((ROOT / "data" / "hotsprings.json").read_text())
        iso_of = {k: v.get("iso") for k, v in hs.get("provinces", {}).items()}
        off = []
        for s in hs.get("springs", []):
            if s.get("lat") and s.get("lng") and iso_of.get(s["province"]):
                d = outside_km(g, iso_of[s["province"]], float(s["lat"]), float(s["lng"]))
                if d > OUTSIDE_KM + 2:
                    off.append(f'{s.get("name") or s.get("nameTh")} {d:.1f} km')
        check("hot springs inside their provinces", not off, "; ".join(off[:5]))
        hom = json.loads((ROOT / "data" / "curated" / "hom.json").read_text())
        home = {"xiengkhouang": "LA-XI", "nan": "TH-55", "thunghong": "TH-54",
                "chiangmai": "TH-50"}
        off = [p["key"] for p in hom.get("route", []) if p["key"] in home
               and outside_km(g, home[p["key"]], p["lat"], p["lng"]) > 1]
        check("indigo route points inside their provinces", not off, ", ".join(off))
        carve = json.loads((ROOT / "data" / "curated" / "carve.json").read_text())
        v = carve.get("village") or {}
        check("Ban Tawai inside Chiang Mai",
              bool(v) and outside_km(g, "TH-50", v["lat"], v["lng"]) == 0)

    print("5 · drawn pins inside their frames")
    if not DOCS.is_dir():
        check("docs/ built", False)
    else:
        pages = sorted(DOCS.glob("*.html"))
        # A site built in another repo is hand-drawn page by page, so a sample
        # misses its one bad map: until 2026-10-10 this was a random 400 of
        # ~100,000 pages drawn from an unsorted listing, which caught the loop's
        # off-frame stops on one host and not on the other. Those sites are
        # read whole; the generated pages are sampled from a sorted list, so
        # every host checks the same pages.
        imported = set()
        for a in sorted((ROOT / "assets").iterdir()):
            if a.is_dir() and (DOCS / a.name).is_dir() and any(a.rglob("*.html")):
                imported.update((DOCS / a.name).rglob("*.html"))
        rest = sorted(set(DOCS.glob("*/*.html")) | set(DOCS.glob("*/*/*.html")))
        rest = [f for f in rest if f not in imported]
        random.seed(len(rest))
        pages += sorted(imported) + random.sample(rest, min(SAMPLE, len(rest)))
        pages = [f for f in pages if not holdback.held(f.relative_to(DOCS).as_posix())]
        svg_rx = re.compile(r"<svg\b([^>]*)>(.*?)</svg>", re.S)
        vb_rx = re.compile(r'viewBox="\s*([-\d.]+)[ ,]+([-\d.]+)[ ,]+([-\d.]+)[ ,]+([-\d.]+)"')
        pin_rx = re.compile(r'<circle\b[^>]*?\bcx="([-\d.]+)"[^>]*?\bcy="([-\d.]+)"'
                            r'|data-mdpin="([-\d.]+),([-\d.]+)"')
        mount_rx = re.compile(r'data-mdmap="[^"]*"[^>]*?data-lat="([-\d.]+)" data-lng="([-\d.]+)"')
        draw_rx = re.compile(r'<div class="mdmap-draw">')
        n_svg, off, bad_mount, naked, no_ground = 0, {}, [], [], []
        mount_pages, naked_pages = set(), set()
        import map_shell
        enabled = map_shell.enabled()
        (mw, ms), (me, mn) = map_shell.config().get("bounds") or map_shell.BOUNDS
        for f in pages:
            s = f.read_text(errors="ignore")
            # The mount regions on this page: map_shell.mount() wraps its drawing
            # in <div class="mdmap-draw">…</div>, and an SVG holds no <div>, so the
            # next </div> closes the mount. A drawn map (one carrying data-mdpin
            # marks) that starts outside every one of these is a map no basemap
            # will ever cover — the "pins on a cream rectangle" this shell exists
            # to end. Checked here so a new map built by hand, not via mount(),
            # cannot ship naked.
            draws = []
            for dm in draw_rx.finditer(s):
                end = s.find("</div>", dm.end())
                draws.append((dm.end(), end if end != -1 else len(s)))
            for m in svg_rx.finditer(s):
                vb = vb_rx.search(m.group(1))
                if not vb:
                    continue
                x0, y0, w, h = map(float, vb.groups())
                if w < 100 or 'aria-hidden="true"' in m.group(1):
                    continue
                n_svg += 1
                body = m.group(2)
                if "data-mdpin" in body and not any(a <= m.start() < b for a, b in draws):
                    naked.append(f"{f.relative_to(DOCS)} ({w:.0f}x{h:.0f})")
                    naked_pages.add(f.relative_to(DOCS).as_posix())
                for c in pin_rx.finditer(body):
                    x, y = float(c.group(1) or c.group(3)), float(c.group(2) or c.group(4))
                    if not (x0 - 2 <= x <= x0 + w + 2 and y0 - 2 <= y <= y0 + h + 2):
                        off.setdefault(str(f.relative_to(DOCS)), f"({x:.0f},{y:.0f}) in {w:.0f}x{h:.0f}")
            for m in mount_rx.finditer(s):
                la, ln = float(m.group(1)), float(m.group(2))
                if not (ms <= la <= mn and mw <= ln <= me):
                    bad_mount.append(f"{f.relative_to(DOCS)} {la},{ln}")
                    mount_pages.add(f.relative_to(DOCS).as_posix())
            # A mount present but the basemap script missing is the other half of
            # the same failure (build.page auto-injects map_shell.head on any body
            # holding a mount): the drawing renders and no tiles ever arrive over
            # it. search.html bakes the four urls into a JSON block it loads on the
            # first tap, so the filename appearing anywhere in the page is enough.
            if enabled and 'data-mdmap="1"' in s and "maplibre-gl.js" not in s:
                no_ground.append(str(f.relative_to(DOCS)))
        print(f"  ({n_svg} drawings on {len(pages)} pages, {len(imported)} of them from sites built elsewhere)")
        hold("pins inside the frame: no new rows",
             ratchet("pins inside the frame", off, known.get("off_frame", []),
                     lambda k, d: f"{k} {d}"), "a pin off its frame")
        OFF_FRAME.update(off)
        print("6 · basemap mounts")
        check("every mount centred inside the fence", not bad_mount, "; ".join(bad_mount[:5]))
        hold("every mount centred inside the fence", sorted(mount_pages), "a map centred off the fence")
        print("6b · a basemap under every drawn map")
        check("no drawn map outside a mount (a map that can never get ground)",
              not naked, "; ".join(naked[:5]))
        hold("no drawn map outside a mount (a map that can never get ground)", sorted(naked_pages),
             "a drawn map with no basemap mount")
        if enabled:
            # Keyed by folder: one template draws a folder, so a missing script
            # is a template's fault, not a page's. Ratchets like 2, 3 and 5.
            by_dir = {}
            for g_ in no_ground:
                by_dir.setdefault("/".join(g_.split("/")[:2]), []).append(g_)
            no_ground_rows = {d: f"{len(v)} page(s), e.g. {v[0]}" for d, v in by_dir.items()}
            hold("every mounted map ships its basemap script: no new rows",
                 [d + "/" if not d.endswith(".html") else d for d in
                  ratchet("every mounted map ships its basemap script", no_ground_rows,
                          known.get("no_ground", []), lambda k, d: f"{k}: {d}")],
                 "a map without its basemap script")
            NO_GROUND.update(no_ground_rows)
        else:
            print("  note  basemap disabled (data/basemap.json has no url) — the drawn "
                  "SVG alone is the intended fallback, so script presence is not gated")

        print("7 · served GeoJSON")
        n_pt, bad_pt = 0, []
        for f in sorted((DOCS / "data").glob("*.geojson")):
            try:
                d = json.loads(f.read_text())
            except ValueError:
                bad_pt.append(f"{f.name} unreadable")
                continue
            for ft in d.get("features", []):
                geo = ft.get("geometry") or {}
                if geo.get("type") != "Point":
                    continue
                n_pt += 1
                x, y = geo["coordinates"][:2]
                if not within(FENCE, y, x):
                    bad_pt.append(f"{f.name} {x},{y}")
        check(f"{n_pt:,} GeoJSON points inside the fence", not bad_pt, "; ".join(bad_pt[:5]))

    print("8 · regional ground")
    if g:
        names = [p["th"] for p in g["provinces"] if p["country"] == "THA"]
        dup = sorted({n for n in names if names.count(n) > 1})
        check("Thai province names unique", not dup, ", ".join(dup))

    print(f"9 · a place named for the other province, pinned in this one's city (≤{CITY_KM:g} km)")
    near_city, set_aside = [], 0
    for r in recs:
        prov = r["_prov"]
        # A person's pin, or an OSM node a mapper placed (Solao@Chiangmai
        # stands in Chiang Rai on OSM): the name is not read against those.
        if r.get("confidence") in ("curated", "field", "crawled"):
            continue
        raw = " ".join(dict.fromkeys(x for x in (r.get("name"), r.get("nameTh"), r.get("nameEn")) if x))
        m = re.search(NAMED[OTHER[prov]], raw, re.I)
        if not m:
            continue
        if (re.search(r"สาขา|branch", raw, re.I) or re.search(NAMED[prov], raw, re.I)
                or re.search(r"น้ำเงี้ยว|ข้าวซอย|khao\s*so[iy]", raw, re.I)
                or re.search(r"(?:บ้าน|วัด|สัน|ราช|ประตู|ถนน|ถ\.|ไป|to\s+go\s+to)\s*$", raw[:m.start()], re.I)
                or re.match(r"\s*(?:รำลึก|style|สไตล์)", raw[m.end():], re.I)):
            set_aside += 1
            continue
        if r.get("lat") is None or r.get("geoPrecision") == "needs-pin":
            continue
        la, ln = CITY[prov]
        if math.hypot((r["lat"] - la) * 110.57,
                      (r["lng"] - ln) * 111.32 * math.cos(math.radians(la))) <= CITY_KM:
            near_city.append(f"{r['id']} {raw[:40]}")
    check("no pinned record in one city named for the other province", not near_city,
          f"{len(near_city)}: " + "; ".join(near_city[:5]))
    print(f"        {set_aside} name(s) set aside: a branch, both provinces named, a dish "
          "style, or a village / wat / road / gate compound")
    for rid in PIN_DOUBT_CASES:
        r = next((x for x in recs if x["id"] == rid), None)
        check(f"{rid[:24]}… needs a pin", r is None or (
            r.get("geoPrecision") == "needs-pin" and r.get("lat") is None
            and (r.get("attrs") or {}).get("pinWas")))

    # The moat ring is four แจ่ง pins. The water's opposite sides run within
    # a degree or so of parallel; a corner pinned off the corner shows here.
    try:
        import build
        ring = build.MOAT_POLY
    except Exception:                                   # noqa: BLE001
        ring = None
    if ring:
        def bearing(a, b):
            k = math.cos(math.radians(a[0]))
            return math.degrees(math.atan2((b[1] - a[1]) * k, b[0] - a[0]))
        west, east = bearing(ring[3], ring[0]), bearing(ring[2], ring[1])
        if abs(west - east) > 2:
            ADVISE.append(f"moat ring: west side runs {west:+.1f}°, east {east:+.1f}° off north — "
                          "a corner pin is off its corner (แจ่งหัวลิน is the middle of a "
                          "300 m wall ruin)")

    grid = [r["id"] for r in pinned
            if (r["lng"] * 256) % 1 == 0 or (r["lat"] * 256) % 1 == 0]
    if grid:
        ADVISE.append(f"{len(grid)} pin(s) on a 1/256-degree grid (~430 m) — a geocoder's "
                      f"rounding, e.g. {', '.join(grid[:3])}")

    if write:
        KNOWN.write_text(json.dumps({
            "_readme": "Rows standing when tests/test_map_sanity.py went in (2026-09-25). "
                       "Printed, not failed; a new row fails. Rewritten by "
                       "`python3 tests/test_map_sanity.py --write-baseline`.",
            "outside_province": sorted(far_prov),
            "far_from_street": sorted(far_street),
            "off_frame": sorted(OFF_FRAME),
            "no_ground": sorted(NO_GROUND),
            "_off_frame_notes": known_notes,
        }, ensure_ascii=False, indent=1) + "\n")
        print(f"\nwrote {KNOWN.relative_to(ROOT)} — {len(far_prov)} outside province, "
              f"{len(far_street)} far from their street")

    for a in ADVISE:
        print("  note  " + a)
    print()
    for f in FAILED:
        if f not in HELD_OK:
            holdback.cannot(f)
    if FAILED:
        print(f"{len(FAILED)} failed:")
        for f in FAILED:
            print("  -", f)
        return 1
    print("map sanity: all checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
