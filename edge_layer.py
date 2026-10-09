#!/usr/bin/env python3
"""THE EDGE — the city nobody counts.

Nan, decision J, 2026-09-06: "bus shelters, tree shrines, named sois, wells —
love all of these." They are in. Four classes that share one property neither a
shop nor an institution has: NOBODY WILL EVER CLAIM THEM. No proprietor fills in
a bus shelter's opening hours; there is no owner of a tree. The whole enrichment
model the directory was built on — owner-confirmed, a phone to ring, a listing
to claim — is void here, and the only sources left are the map, the survey, the
municipal asset register, and what the neighbourhood knows. data/curated/
kinds.json calls that posture the commons and carries the vernacular for all
four, which is the part that decides whether they can be found at all.

WHAT THIS FILE DOES: it PROJECTS ways into records. It does not import them.

data/streets.json already holds 1,077 named ways for the two provinces — 432 of
them sois — every one Thai-named, 534 with geometry, 508 knowing what they
cross, 6,227 places already placed along them by their own OSM address (stated)
or by sitting within 30 m and nearer than any other way (nearest). None of that
is a record. The ways exist only as a join table serving other pages: no id, no
kind, no page, not in the search index. A reader who types ซอยวัดอุโมงค์ finds
nothing, and the catalogue has known the answer since WO-6.

That is the empty-shelves Cause 2 in its largest form — a whole class fully
modelled on disk, invisible because it was never admitted. The fix is not a
crawl. It is a projection, and it is reversible: streets.json stays the truth,
the records are derived every build, and a curated overlay can hang facts a
projection can never know (does it flood, can a car pass, who the donor was)
off the same id.

    import edge_layer
    ways = edge_layer.ways(ROOT)        # [record, …], kind ["way"]
    edge_layer.survey(ROOT)             # what each edge class would yield
"""
import json
import math
import re

# A way is worth a record when somebody could look for it. Two ways in, and both
# have to be honest: it carries something we hold, or it is long enough to be a
# landmark in its own right. A 40 m stub with nothing on it is a line on a map,
# not a place, and minting it would be padding the count.
MIN_PLACES = 1
MIN_LENGTH_M = 120.0


def _slug_id(prov, slug):
    return f"{prov}-way-{slug}"


def _points(geom):
    """Every [lat, lng] in the polyline, in travel order, segments joined."""
    pts = []
    for seg in geom or []:
        for p in seg or []:
            if isinstance(p, (list, tuple)) and len(p) >= 2:
                try:
                    pts.append((float(p[0]), float(p[1])))
                except (TypeError, ValueError):
                    pass
    return pts


def _midpoint(geom):
    """The point at half the polyline's length — where to LOOK for a way, not
    where the way IS. A soi is a line (see the record's geoPrecision); this is
    the spot the map opens on so the whole lane is in view, nothing more.
    Planar over one urban way: the ratio along the line is what is wanted, and
    the longitude scaling that would matter over a province does not move it."""
    pts = _points(geom)
    if not pts:
        return None
    if len(pts) == 1:
        return pts[0]
    seglen = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
    total = sum(seglen)
    if total == 0:
        return pts[0]
    half, acc = total / 2, 0.0
    for (a, b), d in zip(zip(pts, pts[1:]), seglen):
        if acc + d >= half:
            t = (half - acc) / d if d else 0.0
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        acc += d
    return pts[-1]


def _map_target(lat, lng):
    """map.html reads #zoom/lat/lng/shelves (explore_layer.py). z=16 frames the
    lane. This is the href a way's search row carries in `u`, which build.py's
    rowHref sends the reader to instead of a place page a way does not have."""
    return f"map.html#16/{lat:.5f}/{lng:.5f}"


def ways(ROOT, include_all=False):
    """Every named way as a record. `kind` is set here rather than inferred,
    because a way is not a thing any rule over cat/sub could ever reach — it has
    no cat and no sub, having never been a record before."""
    doc = json.loads((ROOT / "data" / "streets.json").read_text())
    by_slug = _by_slug(doc)
    pcoords = _place_coords(ROOT)
    out = []
    for st in doc.get("streets") or []:
        places = st.get("places") or []
        length = st.get("length")
        if not include_all and not (
                len(places) >= MIN_PLACES or (length and length >= MIN_LENGTH_M)):
            continue
        prov = st.get("province") or "cm"
        name = st.get("name") or ""
        if not name:
            continue
        crosses = st.get("crosses") or []
        attrs = {
            "wayKind": "soi" if st.get("soi") else "road",
            "alongCount": len(places),
        }
        if length:
            attrs["length"] = round(length)
        if st.get("parent"):
            attrs["parentWay"] = st["parent"]
            attrs["parentVia"] = st.get("parentVia")
        if crosses:
            attrs["crosses"] = crosses
        if st.get("soi"):
            attrs["soiNumber"] = st["soi"]
        if st.get("aliases") or st.get("alsoSpelled"):
            attrs["altNames"] = [a for a in (st.get("aliases") or []) if a]
        # The map-centring point. It is NOT the way's location — the record
        # stays a line (lat/lng None below) — but the spot the map opens on so
        # a reader who finds the soi can see it. Exact from the way's own or its
        # parent's polyline; approximate from a crossed way when neither exists,
        # flagged so a later exact pin overrides it and nothing reads as precise.
        loc = _locate(st, by_slug, pcoords)
        if loc:
            attrs["mapPoint"] = {"lat": loc["lat"], "lng": loc["lng"],
                                 "approx": loc["approx"]}
        rec = {
            "id": _slug_id(prov, st["slug"]),
            "province": prov,
            "cat": [],                     # a way stands on no shopping shelf
            "kind": ["way"],
            "name": name,
            "nameTh": name,
            "nameEn": st.get("nameEn") or None,
            "lat": None, "lng": None,
            "geoPrecision": "line",        # NOT a point, and it must not pretend to be
            "address": None, "phone": None, "website": None, "hours": None,
            "attrs": attrs,
            "featured": False, "landmark": False,
            "sources": [{"type": "derived", "ref": f"streets.json:{st['slug']}",
                         "via": "edge_layer.ways"}],
            "confidence": "derived",
            "provenance": {
                "name": {"source": "osm:mueang-map", "how": "stated"},
                "attrs.alongCount": {"source": "streets.json", "how": "derived"},
            },
        }
        # `runsFrom` is the honest half of "where does it come out": we know
        # what it crosses, so we know its junctions; we do not know which end is
        # which without walking it, and the record must not imply that we do.
        if crosses:
            rec["runsFrom"] = crosses[:4]
        if loc:
            entry = {"source": loc["source"], "how": "derived"}
            if loc.get("note"):
                entry["note"] = loc["note"]
            rec["provenance"]["attrs.mapPoint"] = entry
        out.append(rec)
    return out


def _by_slug(doc):
    return {s["slug"]: s for s in (doc.get("streets") or []) if s.get("slug")}


def _way_point(st, by_slug, depth=0):
    """A way's map point: its own polyline midpoint, or its parent's when the
    way has no geometry of its own (a numbered soi often carries none, but the
    road it hangs off does). Returns None when neither is on disk."""
    mp = _midpoint(st.get("geom"))
    if mp:
        return mp
    par = st.get("parent")
    if depth < 4 and par and par != st.get("slug") and par in by_slug:
        return _way_point(by_slug[par], by_slug, depth + 1)
    return None


# The basemap fence: the cm-cr.pmtiles extract W,S,E,N = 97.3,17.0,100.6,20.5
# (map_shell.py:66), the box the tiles are actually drawn for and the one
# tests/test_map_sanity.py fences every pin against. map_shell exposes no
# constant for it — its BOUNDS is the looser maxBounds pan limit — so the
# documented extract is mirrored here. A pin outside it has no ground to sit on.
FENCE_S, FENCE_W, FENCE_N, FENCE_E = 17.0, 97.3, 20.5, 100.6


def _in_fence(lat, lng):
    return FENCE_S <= lat <= FENCE_N and FENCE_W <= lng <= FENCE_E


def _median(xs):
    xs = sorted(xs)
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def _place_coords(ROOT):
    """id -> (lat, lng) for every canonical record that carries a coordinate.
    The one cross-file read: a way's `places` are place-ids, and their pins live
    in data/canonical, not in streets.json."""
    coords = {}
    for p in ("cm", "cr"):
        fp = ROOT / "data" / "canonical" / f"{p}.json"
        if not fp.exists():
            continue
        for r in json.loads(fp.read_text()):
            if r.get("lat") is not None and r.get("lng") is not None and r.get("id"):
                coords[r["id"]] = (r["lat"], r["lng"])
    return coords


def _locate(st, by_slug, place_coords=None):
    """Where a way goes on the map, and how sure. EXACT: the way's own polyline
    midpoint, or its parent's. APPROXIMATE, in order: a point on a way it crosses
    that has geometry (the reader lands on the road the soi joins), then — for an
    offmap way with neither geometry nor a crossing — the CENTROID of the places
    that sit along it, kept only when it lands inside the basemap fence. Returns
    {lat, lng, approx, source[, note]}, or None when nothing on disk places it in
    the mapped area.

    Nan approved the approximate pins (junction 2026-09-25, in-fence centroid
    2026-09-25 option B). The crossing is picked by the MEDIAN crossed-way slug
    (sorted): deterministic, and it spreads pins across a way's junctions rather
    than piling every soi on whichever sorts first. The centroid is the MEDIAN of
    the place lats and lngs, not the mean — one stray place cannot drag it."""
    mp = _way_point(st, by_slug)
    if mp:
        return {"lat": round(mp[0], 5), "lng": round(mp[1], 5),
                "approx": False, "source": "streets.json:geom"}
    cands = []
    for cs in (st.get("crosses") or []):
        c = by_slug.get(cs)
        if not c or cs == st.get("slug"):
            continue
        cp = _way_point(c, by_slug)
        if cp:
            cands.append((cs, c, cp))
    if cands:
        cands.sort(key=lambda x: x[0])
        cs, c, cp = cands[len(cands) // 2]
        return {"lat": round(cp[0], 5), "lng": round(cp[1], 5), "approx": True,
                "source": f"streets.json:{cs}",
                "note": f"junction of {c.get('name') or cs}"}
    if place_coords:
        pts = [place_coords[pl["id"]] for pl in (st.get("places") or [])
               if isinstance(pl, dict) and pl.get("id") in place_coords]
        if pts:
            lat = round(_median([p[0] for p in pts]), 5)
            lng = round(_median([p[1] for p in pts]), 5)
            if _in_fence(lat, lng):
                return {"lat": lat, "lng": lng, "approx": True,
                        "source": "data/canonical (place centroid)",
                        "note": f"place centroid ({len(pts)} places)"}
    return None


def search_rows(ROOT):
    """The ways as SEARCH-INDEX rows, in build.py's own compact shape, ready to
    fold into `search_index` (search_index += edge_layer.search_rows(ROOT)) so
    they reach both the page's index.json and the edge shards emit_edge_index.js
    writes from it. The row is the twin of what build.py mints for a place:

        id  the way's stable id        s   its streets.json slug
        n   the Thai name (shown)      r   the romanised name (shown, matched)
        p   province                   c   [] — a way is on no shopping shelf
        kd  ["way"] — the second axis  k   match-only words, off the screen
        lat/lng  the map-centring point (index2.json / the 📍)
        u   map.html#… — the href rowHref uses in place of a place page

    A way _locate() cannot place on the map is NOT minted: its row would link to
    a place page it does not have and drop a 📍 with no coordinate. The point is
    the own/parent midpoint where there is one, else an approximate junction pin
    (see _locate). `k` carries what a reader might type that is not in the name —
    the soi/road words, the number, alt spellings, and the names of the ways it
    crosses — matched at shelf weight so a real place on the same word still
    outranks it."""
    doc = json.loads((ROOT / "data" / "streets.json").read_text())
    by_slug = _by_slug(doc)
    pcoords = _place_coords(ROOT)
    rows = []
    for st in doc.get("streets") or []:
        places = st.get("places") or []
        length = st.get("length")
        if not (len(places) >= MIN_PLACES or (length and length >= MIN_LENGTH_M)):
            continue
        name = st.get("name") or ""
        slug = st.get("slug")
        if not name or not slug:
            continue
        loc = _locate(st, by_slug, pcoords)
        if not loc:
            continue
        prov = st.get("province") or "cm"
        lat, lng = loc["lat"], loc["lng"]
        row = {"id": _slug_id(prov, slug), "s": slug, "n": name, "e": None,
               "p": prov, "c": [], "kd": ["way"],
               "lat": lat, "lng": lng, "u": _map_target(lat, lng)}
        en = st.get("nameEn")
        if en:
            row["r"] = en
        k = []
        if st.get("soi"):
            k += ["ซอย", "soi", str(st["soi"])]
        else:
            k += ["ถนน", "road", "street"]
        for a in (st.get("aliases") or []) + (st.get("alsoSpelled") or []):
            if a:
                k.append(a)
        for cs in (st.get("crosses") or [])[:6]:
            c = by_slug.get(cs)
            if c:
                if c.get("name"):
                    k.append(c["name"])
                if c.get("nameEn"):
                    k.append(c["nameEn"])
        blob = " ".join(dict.fromkeys(x for x in k if x))
        if blob:
            row["k"] = blob
        rows.append(row)
    return rows


def survey(ROOT):
    """What each of the four edge classes would yield, counted rather than
    guessed. Absence here is absence ON THIS DISK — never a claim about the city.
    """
    doc = json.loads((ROOT / "data" / "curated" / "kinds.json").read_text())
    recs = []
    for p in ("cm", "cr"):
        recs += json.loads((ROOT / "data" / "canonical" / f"{p}.json").read_text())
    text = [" ".join(str(r.get(k) or "") for k in ("name", "nameTh", "nameEn"))
            for r in recs]
    out = {}
    w = ways(ROOT)
    out["way"] = {"held": 0, "projectable": len(w),
                  "sois": sum(1 for r in w if r["attrs"]["wayKind"] == "soi"),
                  "needs": "nothing — it is on disk"}
    for key in ("shelter", "sacred", "water"):
        e = doc["edge"][key]
        pat = "|".join(re.escape(t[0].split(" · ")[0]) for t in e["terms"])
        rx = re.compile(pat)
        hits = sum(1 for t in text if rx.search(t))
        out[key] = {"held": e.get("held_today"), "name_matches_in_corpus": hits,
                    "needs": e["source"].split(";")[0]}
    return out
