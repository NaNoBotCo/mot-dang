#!/usr/bin/env python3
"""Give every place a street, and every street a page. รู้ทุกซอย, made literal.

The directory walks จังหวัด → อำเภอ → ตำบล → place and skips the rung people
actually use to say where something is: the road, and the soi off it. This
builds that rung.

Two ways a place gets a street, and the difference is published rather than
smoothed over:

  stated   the place's own OSM addr:street. The shop says which road it is on.
  nearest  the place sits inside the crawled road box and the closest named way
           is within CAP metres. Evidence, not testimony — the metres ride along
           on the record so a reader can weigh it.

Same discipline as `venue_from` in the events layer and `precision` on a pinned
venue: an inference is labelled as one, every time. Nothing here invents an
address. A place near a road is near a road; the page says อยู่ริมถนน (on this
road), never a house number it does not have.

Sois are the interesting half. OSM names 508 of 748 roads here with ซอย or Soi
in the name, but hundreds are bare — "ซอย 1", "ซอย 12" — and a bare soi number
is meaningless without its parent road. So the parent is recovered from the
junction: a soi meets the road it belongs to, and that shared node is the
statement of belonging. Where a bare soi meets nothing named, it keeps its own
page and says plainly that the parent is unknown.

  python3 importers/crawl_roads.py       # first, if cache/roads is empty
  python3 importers/build_streets.py     # then this
  python3 build.py                       # renders the tier

Writes data/streets.json. Reads cache/roads/*.json + data/canonical/*.json.
"""
import json
import math
import re
import sys
import zlib
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache" / "roads"
OUT = ROOT / "data" / "streets.json"

# How far a place may sit from a named way and still be called "on" it. Chosen
# from the measured distribution (see --stats): the knee is around 25 m, which
# is a shop set back behind its own parking rather than one on the next block.
# Past that the guess starts crossing property lines, so it declines instead.
CAP = 30.0

# Ways that carry a name but are not a street anybody gives as an address.
NOT_A_STREET = {"motorway_link", "trunk_link", "primary_link", "secondary_link",
                "tertiary_link", "construction", "proposed", "raceway", "escape",
                "bus_guideway", "platform", "elevator", "corridor"}

SOI_RE = re.compile(
    r"^(?P<parent>.*?)\s*(?:ซ\.|ซอย|soi|lane)\s*(?P<num>[0-9]+[/\-]?[0-9]*)\s*(?P<tail>.*)$",
    re.IGNORECASE)
ROAD_WORD = re.compile(r"^(?:ถนน|ถ\.|thanon|road|rd\.?)\s*", re.IGNORECASE)


def hav(a, b):
    R = 6371000.0
    dla, dlo = math.radians(b[0] - a[0]), math.radians(b[1] - a[1])
    h = (math.sin(dla / 2) ** 2
         + math.cos(math.radians(a[0])) * math.cos(math.radians(b[0]))
         * math.sin(dlo / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(h))


def norm(s):
    """One spelling for matching on. Strips the road word, folds ซอย1/ซอย 1,
    drops punctuation and case — so addr:street 'ถ.มหิดล' finds way 'ถนนมหิดล'."""
    if not s:
        return ""
    s = s.strip()
    s = ROAD_WORD.sub("", s)
    s = re.sub(r"\s*(?:ซ\.|ซอย)\s*", " ซอย ", s)
    s = re.sub(r"\s*\b(?:soi|lane)\b\s*", " ซอย ", s, flags=re.IGNORECASE)
    s = re.sub(r"[\s,\.\-–—_]+", " ", s)
    s = re.sub(r"\b(?:road|rd|street|st)\b", "", s, flags=re.IGNORECASE)
    return " ".join(s.split()).lower()


def slugify(name_en, name, key, used):
    """An ASCII filename stem, for the same reason place_slug() is ASCII: git on
    macOS can silently renormalize a Unicode filename between NFC and NFD, and
    the mismatch surfaces after deploy as a 404 with no visible cause. A Thai
    road name in the path would hit that on every soi page at once.

    So: the road's own English name when OSM carries one, plus a short stable
    digest of the normalized Thai name — stable because it is derived, not
    counted, so yesterday's URL survives tomorrow's new road appearing. Roads
    with no Latin name at all get the digest alone. The Thai name is still the
    <title>, the <h1> and the og:title.
    """
    # name:en when OSM carries one; otherwise the display name, which for a good
    # many roads here is already Latin (an addr:street written 'Loi Kroh Road').
    # A Thai-only name strips to nothing and falls through to the digest.
    stem = ""
    for candidate in (name_en, name):
        stem = re.sub(r"[^a-z0-9]+", "-", (candidate or "").strip().lower()).strip("-")[:48]
        stem = stem.rstrip("-")
        if stem:
            break
    digest = "%06x" % (zlib.crc32(key.encode("utf-8")) & 0xFFFFFF)
    slug = ("%s-%s" % (stem, digest)) if stem else "soi-%s" % digest
    # A collision needs two roads whose normalized names differ but whose crc32
    # low bits do not. Vanishingly unlikely, but a silent overwrite would be a
    # page quietly serving another road's shops, so it is handled rather than
    # assumed away.
    base, n = slug, 2
    while slug in used:
        slug = "%s-%d" % (base, n)
        n += 1
    used.add(slug)
    return slug


def parse_soi(name):
    """('ถนนนิมมานเหมินทร์ ซอย 5') → ('ถนนนิมมานเหมินทร์', '5').
    ('ซอย 5') → (None, '5'). Not a soi → (None, None)."""
    m = SOI_RE.match(name.strip())
    if not m:
        return None, None
    parent = (m.group("parent") or "").strip(" ,-")
    num = m.group("num")
    tail = (m.group("tail") or "").strip()
    # "ซอย 10 บ้านช่างทอง หมู่ที่ 7" — the tail is a place name, not part of the
    # number, but it does distinguish two ซอย 10s, so it stays in the label.
    label = num if not tail else "%s %s" % (num, tail)
    return (parent or None), label


def load_ways():
    tiles = sorted(CACHE.glob("*.json"))
    if not tiles:
        print("no tiles in cache/roads/ — run importers/crawl_roads.py first",
              file=sys.stderr)
        return None, None
    ways, coords = {}, {}
    for t in tiles:
        for e in json.loads(t.read_text())["elements"]:
            if e["type"] == "way":
                ways.setdefault(e["id"], e)
            elif e["type"] == "node":
                coords.setdefault(e["id"], (e["lat"], e["lon"]))
    return ways, coords


def chain(segments):
    """Thread a street's ways into as few continuous runs as possible.

    A road arrives as a dozen ways split at bridges, name changes and tile
    edges. Ordering places along it means walking one line, not twelve, so the
    ways get joined end to end wherever they share a node. What will not join
    stays a separate run — a road with a gap in it has a gap in it, and pretending
    otherwise would order the far side of town into the middle of the list."""
    segs = [list(s) for s in segments if len(s) > 1]
    runs = []
    while segs:
        run = segs.pop(0)
        joined = True
        while joined:
            joined = False
            for i, s in enumerate(segs):
                if run[-1] == s[0]:
                    run += s[1:]
                elif run[-1] == s[-1]:
                    run += s[::-1][1:]
                elif run[0] == s[-1]:
                    run = s[:-1] + run
                elif run[0] == s[0]:
                    run = s[::-1][:-1] + run
                else:
                    continue
                segs.pop(i)
                joined = True
                break
        runs.append(run)
    return runs


def to_seg(p, a, b):
    """Metres from p to segment ab, and how far along ab the foot of the
    perpendicular falls. Flat local projection: over one segment of road the
    curvature of the earth is not the error that matters."""
    kx = math.cos(math.radians(p[0])) * 111320.0
    ky = 110540.0
    ax, ay = (a[1] - p[1]) * kx, (a[0] - p[0]) * ky
    bx, by = (b[1] - p[1]) * kx, (b[0] - p[0]) * ky
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if not L else max(0.0, min(1.0, (-ax * dx - ay * dy) / L))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(cx, cy), t, math.sqrt(L)


def main():
    ways, coords = load_ways()
    if ways is None:
        return 1

    # ---------------------------------------------------------------- streets
    named = []
    for w in ways.values():
        t = w.get("tags") or {}
        hw = t.get("highway")
        name = t.get("name") or t.get("name:th")
        if not hw or not name or hw in NOT_A_STREET:
            continue
        if any(n not in coords for n in w["nodes"]):
            continue
        named.append((w, name, t))

    by_name = defaultdict(list)
    for w, name, t in named:
        by_name[norm(name)].append((w, name, t))

    # Which node belongs to which street, for the junction work below.
    node_streets = defaultdict(set)
    for key, items in by_name.items():
        for w, _, _ in items:
            for n in w["nodes"]:
                node_streets[n].add(key)

    streets = {}
    used_slugs = set()
    for key, items in sorted(by_name.items()):
        # The most-used spelling wins as the display name; the rest become
        # aliases so a stated addr:street in any of them still lands here.
        spellings = Counter(name for _, name, _ in items)
        display = spellings.most_common(1)[0][0]
        en = None
        for _, _, t in items:
            if t.get("name:en"):
                en = t["name:en"]
                break
        runs = chain([w["nodes"] for w, _, _ in items])
        geom = [[list(coords[n]) for n in run] for run in runs]
        length = sum(hav(run[i], run[i + 1])
                     for run in geom for i in range(len(run) - 1))
        parent_name, soi = parse_soi(display)
        streets[key] = {
            "key": key,
            "name": display,
            "nameEn": en,
            "aliases": sorted(set(spellings) - {display}),
            "soi": soi,
            "parentName": parent_name,
            "parent": None,
            "parentVia": None,
            "geom": geom,
            "length": round(length, 1),
            "nodes": set(n for w, _, _ in items for n in w["nodes"]),
            "crosses": set(),
            "places": [],
        }

    # ------------------------------------------------------- soi → parent road
    # A soi belongs to the road it comes off. Where the name says so, believe
    # the name; where it does not, the junction is the evidence.
    for key, st in streets.items():
        if st["soi"] is None:
            continue
        if st["parentName"]:
            pk = norm(st["parentName"])
            if pk in streets:
                st["parent"], st["parentVia"] = pk, "name"
                continue
        # Bare "ซอย 12": look at what it touches. A soi off a soi is real and
        # common, so a soi parent is allowed — but a road parent wins, because
        # that is how anybody gives the address out loud.
        touch = Counter()
        for n in st["nodes"]:
            for other in node_streets.get(n, ()):
                if other != key:
                    touch[other] += 1
        if touch:
            def rank(k):
                o = streets[k]
                return (o["soi"] is not None, -touch[k], -o["length"])
            best = sorted(touch, key=rank)[0]
            st["parent"], st["parentVia"] = best, "junction"

    # --------------------------------------------------------------- crossings
    for n, keys in node_streets.items():
        if len(keys) < 2:
            continue
        for a in keys:
            for b in keys:
                if a != b:
                    streets[a]["crosses"].add(b)

    # ----------------------------------------------------------- place → street
    places = []
    for prov in ("cm", "cr"):
        f = ROOT / "data" / "canonical" / ("%s.json" % prov)
        if f.exists():
            places += json.loads(f.read_text())

    # Index every segment once, in a coarse grid, so 10,463 places do not each
    # walk 2,000 polylines. Cell is ~1.1 km; a 30 m cap never leaves one ring.
    GRID = 0.01
    cells = defaultdict(list)
    for key, st in streets.items():
        for ri, run in enumerate(st["geom"]):
            run_at = 0.0
            for i in range(len(run) - 1):
                a, b = run[i], run[i + 1]
                seg = (key, ri, i, run_at)
                run_at += hav(a, b)
                for cy in range(int(min(a[0], b[0]) / GRID), int(max(a[0], b[0]) / GRID) + 1):
                    for cx in range(int(min(a[1], b[1]) / GRID), int(max(a[1], b[1]) / GRID) + 1):
                        cells[(cy, cx)].append(seg)

    stated_hit = stated_miss = near_hit = far = bare_soi = 0
    # Where a record both states a street and sits near one, the two methods can
    # be checked against each other. That is the only ground truth available, so
    # it is collected here rather than in a throwaway script, and the verdict
    # ships in the file so the page can print it.
    trials = []
    dists = []
    orphan_streets = {}
    for r in places:
        lat, lng = r.get("lat"), r.get("lng")
        stated = (r.get("attrs") or {}).get("street")
        best = None

        if lat is not None:
            p = (lat, lng)
            cy0, cx0 = int(lat / GRID), int(lng / GRID)
            seen = set()
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    for seg in cells.get((cy0 + dy, cx0 + dx), ()):
                        if seg in seen:
                            continue
                        seen.add(seg)
                        key, ri, i, run_at = seg
                        run = streets[key]["geom"][ri]
                        d, t, L = to_seg(p, run[i], run[i + 1])
                        if best is None or d < best[0]:
                            best = (d, key, ri, run_at + t * L)

        # A bare soi number is not an address. "ซอย 4" written on twenty shops
        # across the city means twenty different lanes, and believing it lands
        # them all on whichever single way happens to carry that name. Only a
        # soi with something else in it — a parent road, a หมู่บ้าน — identifies
        # itself; the rest fall through to the geometry, which does know where
        # the shop is standing.
        if stated:
            par, soi_n = parse_soi(stated)
            if soi_n and not par and re.fullmatch(r"[0-9]+", soi_n or ""):
                stated = None
                bare_soi += 1

        # Testimony first. A stated street that also has geometry gets its
        # position along the road from that geometry; one that does not still
        # earns a page, because a road outside the crawled box is still a road.
        if stated:
            sk = norm(stated)
            if sk in streets:
                if best and best[0] <= CAP:
                    trials.append((sk, best[1]))
                if best and best[1] == sk:
                    run_i, at = best[2], best[3]
                elif lat is not None:
                    run_i, at = position_on(streets[sk], (lat, lng))
                else:
                    run_i, at = 0, 0.0
                streets[sk]["places"].append(
                    {"id": r["id"], "prov": r["province"], "run": run_i,
                     "at": round(at, 1), "via": "stated"})
                stated_hit += 1
                continue
            stated_miss += 1
            o = orphan_streets.setdefault(sk, {
                "key": sk, "name": stated.strip(), "nameEn": None, "aliases": [],
                "soi": parse_soi(stated)[1], "parentName": parse_soi(stated)[0],
                "parent": None, "parentVia": None, "geom": [], "length": 0.0,
                "nodes": set(), "crosses": set(), "places": [], "offmap": True})
            o["places"].append({"id": r["id"], "prov": r["province"], "run": 0,
                                "at": 0.0, "via": "stated"})
            continue

        if best and best[0] <= CAP:
            d, key, ri, at = best
            streets[key]["places"].append(
                {"id": r["id"], "prov": r["province"], "run": ri,
                 "at": round(at, 1), "via": "nearest", "d": round(d, 1)})
            near_hit += 1
            dists.append(d)
        elif best:
            far += 1

    # An orphan soi still wants its parent, and the name is all there is to go on.
    for key, o in orphan_streets.items():
        if o["parentName"]:
            pk = norm(o["parentName"])
            if pk in streets or pk in orphan_streets:
                o["parent"], o["parentVia"] = pk, "name"
    streets.update(orphan_streets)

    # ------------------------------------------------- one road, two spellings
    # OSM holds ถนนสิงห์ราช and ถนนสิงหราช, ถนนนิมมานเหมินท์ and
    # ถนนนิมมานเหมินทร์ — the same road entered twice by two mappers. They are
    # NOT merged here: a merge that is wrong puts a shop on another road, and
    # nothing in the data says which spelling the sign outside actually bears.
    # Instead each page points at the other, and a human can settle it.
    #
    # Edit distance alone is not enough and the near-misses show why: ซอย 1 and
    # ซอย 2 are one character apart and could not be more different. So the
    # numbers must match exactly and only the words may differ.
    def unnumbered(k):
        return re.sub(r"[0-9]+", "", k).strip()

    def numbers(k):
        return re.findall(r"[0-9]+", k)

    def edit(a, b):
        if abs(len(a) - len(b)) > 1:
            return 9
        prev = list(range(len(b) + 1))
        for i, ca in enumerate(a, 1):
            cur = [i]
            for j, cb in enumerate(b, 1):
                cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
            prev = cur
        return prev[-1]

    keys = list(streets)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            if numbers(a) != numbers(b):
                continue
            ua, ub = unnumbered(a), unnumbered(b)
            if not ua or not ub or edit(ua, ub) > 1:
                continue
            # Two roads that never meet, both mapped, are two roads.
            both_mapped = streets[a]["geom"] and streets[b]["geom"]
            if both_mapped and not (streets[a]["nodes"] & streets[b]["nodes"]):
                continue
            streets[a].setdefault("alsoSpelled", set()).add(b)
            streets[b].setdefault("alsoSpelled", set()).add(a)


    # ---------------------------------------------------- how good is nearest?
    # 477 records both state a street and stand near one. Where the two methods
    # name the same road, the guess is vindicated; where they name a road and
    # its own soi, or one road under two spellings, the place is on a corner and
    # neither answer is wrong. What is left over is the error rate, and it is
    # the number that belongs on the page — not a claim that this is addressing.
    def same_family(a, b):
        if a == b or b in streets[a].get("alsoSpelled", ()) \
                or a in streets[b].get("alsoSpelled", ()):
            return True
        pa, pb = streets[a]["parent"], streets[b]["parent"]
        if pa == b or pb == a:
            return True
        return bool(pa) and pa == pb

    agree = sum(1 for a, b in trials if a == b)
    family = sum(1 for a, b in trials if same_family(a, b))
    check = {
        "n": len(trials),
        "exact": agree,
        "same_road_family": family,
        "wrong": len(trials) - family,
        "pct_exact": round(100.0 * agree / len(trials), 1) if trials else None,
        "pct_family": round(100.0 * family / len(trials), 1) if trials else None,
        "how": ("Measured on the records that both state a street and stand "
                "within the cap of one, which is the only ground truth here. "
                "'Same road family' counts a road matched to its own soi, two "
                "sois of one road, or one road under two spellings — a corner, "
                "not a mistake."),
    }

    # ------------------------------------------------------------------ output
    out = []
    slugs = {}
    for key in sorted(streets, key=lambda k: (-len(streets[k]["places"]), k)):
        st = streets[key]
        if not st["places"]:
            continue
        slugs[key] = slugify(st.get("nameEn"), st["name"], key, used_slugs)
    for key, slug in slugs.items():
        st = streets[key]
        st["places"].sort(key=lambda pl: (pl["run"], pl["at"]))
        prov = Counter(pl["prov"] for pl in st["places"]).most_common(1)[0][0]
        rec = {
            "slug": slug,
            "key": key,
            "name": st["name"],
            "nameEn": st.get("nameEn"),
            "aliases": st["aliases"],
            "soi": st["soi"],
            "province": prov,
            "length": st["length"],
            "offmap": bool(st.get("offmap")),
            "parent": slugs.get(st["parent"]) if st["parent"] else None,
            "parentVia": st["parentVia"] if st["parent"] in slugs else None,
            "crosses": sorted(slugs[k] for k in st["crosses"] if k in slugs),
            "alsoSpelled": sorted(slugs[k] for k in st.get("alsoSpelled", ())
                                  if k in slugs),
            "geom": [[[round(c[0], 6), round(c[1], 6)] for c in run]
                     for run in st["geom"]],
            "places": [{k: v for k, v in pl.items() if k != "prov"}
                       for pl in st["places"]],
        }
        out.append(rec)

    out.sort(key=lambda s: (-len(s["places"]), s["name"]))
    payload = {
        "generated": None,      # stamped by the caller, never by a clock in here
        "cap_m": CAP,
        "note": ("A place is on a street either because its own OSM address says "
                 "so (via=stated) or because it sits within %d m of that named "
                 "way and no nearer one (via=nearest, d=metres). Neither is a "
                 "postal address." % int(CAP)),
        "counts": {
            "streets": len(out),
            "with_geometry": sum(1 for s in out if s["geom"]),
            "offmap": sum(1 for s in out if s["offmap"]),
            "sois": sum(1 for s in out if s["soi"]),
            "placed": stated_hit + near_hit,
            "stated": stated_hit,
            "nearest": near_hit,
            "stated_offmap": stated_miss,
            "too_far": far,
            "bare_soi_declined": bare_soi,
            "places_total": len(places),
        },
        "check": check,
        "streets": out,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))

    size = OUT.stat().st_size / 1e6
    print("streets: %d with places  (%d have geometry, %d off the road map)"
          % (len(out), payload["counts"]["with_geometry"], payload["counts"]["offmap"]))
    print("  sois %d · parents by name %d, by junction %d"
          % (payload["counts"]["sois"],
             sum(1 for s in out if s["parentVia"] == "name"),
             sum(1 for s in out if s["parentVia"] == "junction")))
    print("  placed %d of %d places  (stated %d · nearest %d · stated but off the "
          "road map %d · too far %d)"
          % (payload["counts"]["placed"], len(places), stated_hit, near_hit,
             stated_miss, far))
    if bare_soi:
        print("  declined %d bare soi numbers as addresses (fell through to geometry)"
              % bare_soi)
    if dists:
        dists.sort()
        q = lambda f: dists[int(f * (len(dists) - 1))]
        print("  nearest-match distance: median %.0f m · 90th %.0f m · max %.0f m"
              % (q(.5), q(.9), dists[-1]))
    if check["n"]:
        print("  checked against %d records that state their own street: "
              "%.1f%% exact, %.1f%% same road family, %d wrong"
              % (check["n"], check["pct_exact"], check["pct_family"], check["wrong"]))
    print("  → %s  (%.2f MB)" % (OUT.relative_to(ROOT), size))
    return 0


def position_on(st, p):
    """(run, metres along it) for the point on this street nearest p. Used when a
    place states a street it is not closest to — believe the statement, but put
    the pin where the geometry says it falls. A street in two runs needs both
    numbers: 40 m along the second run is not 40 m along the first."""
    best = None
    for ri, run in enumerate(st["geom"]):
        run_at = 0.0
        for i in range(len(run) - 1):
            d, t, L = to_seg(p, run[i], run[i + 1])
            if best is None or d < best[0]:
                best = (d, ri, run_at + t * L)
            run_at += L
    return (best[1], best[2]) if best else (0, 0.0)


if __name__ == "__main__":
    sys.exit(main())
