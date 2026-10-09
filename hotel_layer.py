#!/usr/bin/env python3
"""ที่พัก · Stay — the lodging block on hotel, guesthouse and hostel pages.

NaN, 2026-10-04: "I'd love to enrich hotel pages in many ways, including a
booking link", then "Do everything except 7" from the list, plus four
questions: pool, airport shuttle, bar, food on site; and, in Chiang Mai, inside
the old city or not.

One block below the pictures (her page order, 2026-10-03), in this order:

  quick strip   old city · pool · shuttle · bar · food · air con, one word each,
                only what a source states
  booking       the hotel's own site first ("direct" = the hotel's site, her
                word 2026-08-18); paid links from data/curated/booking_links.json
                under their label; a site motdangify/out/batch.tsv found not
                answering, or moved to another host, drops below phone + LINE
  by road       airport, nearest moat gate, One Nimman, Arcade (CM) · airport,
                clock tower, bus terminals 1 and 2 (CR) — scooter graph
  nearest       7-Eleven and pharmacy on foot, hospital by scooter; the toilet
                line already on the page (loo_road.place_line) is not repeated
  facts         pool / shuttle / bar / food from data/curated/hotel_amenities.json
                with the source and date; air con from aircon_stated.json
  water         the river the pin stands near (derive.py), the Ping gauges
                (/nam.html) and the flood question (/chuai.html)
  around it     wats, markets, cafés within a walk, by road, as net strands

Every distance is by road over cache/road_graph_prov.json (loo_road.Net), never
the crow (her word 2026-09-23). A road figure more than 3× the crow plus 2 km
is a gap in the graph, not a route, and prints nothing.

    prepare(g, data)   once, before the place pages fork
    block(r, h)        the markup for one record ("" for anything else)
    counts()           per-section page counts + median bytes, for the log
"""
import array
import csv
import datetime
import heapq
import json
import math
import re
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BOOKING = ROOT / "data" / "curated" / "booking_links.json"
AMENITIES = ROOT / "data" / "curated" / "hotel_amenities.json"
LANDMARKS = ROOT / "data" / "curated" / "landmarks.json"
SITECHECK = ROOT.parent / "motdangify" / "out" / "batch.tsv"

LODGING_SUBS = {"hotel", "hotel-full", "hostel", "guesthouse", "resort", "homestay", "serviced"}

WALK_M_PER_MIN = 80           # loo_road.WALK_M_PER_MIN
NEAR_FOOT_M = 3000            # 7-Eleven, pharmacy: named within this walk
NEAR_RIDE_M = 40000           # hospital
AROUND_M = 1200               # around it: wats, markets, cafés within this walk
AROUND_EACH = 3
DETOUR = 3.0                  # road > DETOUR × crow + DETOUR_PAD = a graph gap
DETOUR_PAD = 2000.0

FOOT = (1, 2)
RIDE = (4, 8)

# (key, register key in landmarks.json or a record id, code after the name).
# The coordinate and both names are read from the record at build time. The
# airports use the passenger terminal, not the airfield's centre.
TARGETS = {
    "cm": [("airport", "cm-osm-way-58309446", "CNX", "airport"),
           ("nimman", "one-nimman", "", None),
           ("arcade", "arcade", "", None)],
    "cr": [("airport", "cr-osm-way-87458645", "CEI", "cr-airport"),
           ("clock", "clock-tower", "", None),
           ("bus1", "cr-osm-way-105137199", "", None),
           ("bus2", "cr-osm-way-256549552", "", None)],
}
# Hosts that sell rooms for many hotels: never "the hotel's own site".
OTA = ("agoda.", "booking.com", "trip.com", "expedia.", "hotels.com", "airbnb.", "traveloka.",
       "tripadvisor.", "trivago.", "hostelworld.", "ctrip.", "klook.")

AMENITY = (  # key, icon, TH label, EN label
    ("pool", "i-water", "สระว่ายน้ำ", "Pool"),
    ("shuttle", "i-plane", "รถรับส่งสนามบิน", "Airport shuttle"),
    ("bar", "i-beer", "บาร์", "Bar"),
    ("food", "i-food", "อาหาร", "Food"),
)

CSS = """
/* ---- ที่พัก · Stay (hotel_layer.py) ----------------------------------- */
.stay{margin:1rem 0;padding:.8rem .9rem;background:#fffdf5;border:2px solid #17110c;
border-radius:.8rem;box-shadow:3px 3px 0 #f1c40f}
.stay h2{margin:0 0 .4rem;font-size:1.1rem}
.stay h3{margin:.7rem 0 .2rem;font-size:1rem}
.stay .hq{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 .4rem;padding:0;list-style:none}
.stay .hq li{display:inline-flex;align-items:center;gap:4px;padding:4px 10px;border-radius:999px;
background:#e8f6ff;border:2px solid #0a66c2;font-weight:600;font-size:.92rem}
.stay .hq li.moat{background:#fdebd0;border-color:#c0392b}
.stay ul.rows{list-style:none;margin:.2rem 0;padding:0}
.stay ul.rows li{padding:.25rem 0;line-height:1.5}
.stay .src,.stay .paidnote{display:block;font-size:.82rem;color:var(--muted)}
.stay .book a.own{font-weight:700}
.stay .down{color:var(--muted)}
.stay .net{margin:.6rem 0 0;box-shadow:none}
"""

_DATA = {}          # record id -> prepared facts
_LINKS = {"search": [], "places": {}}
_AMEN = {}
_SITES = {}         # record id or host -> (state, final host)
_SITES_DATE = ""
_COUNTS = {}
_BYTES = []


# ------------------------------------------------------------------ inputs

def is_lodging(r):
    return "hotel" in (r.get("cat") or []) or bool(LODGING_SUBS & set(r.get("sub") or []))


def _load_json(path, empty):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return empty


def load_links(path=BOOKING):
    d = _load_json(path, {})
    return {"search": [x for x in (d.get("search") or []) if x.get("url") and x.get("name")],
            "places": {k: [x for x in v if x.get("url") and x.get("name")]
                       for k, v in (d.get("places") or {}).items() if isinstance(v, list)}}


def _host(url):
    try:
        h = urllib.parse.urlsplit(url if "://" in url else "http://" + url).netloc.lower()
    except ValueError:
        return ""
    h = h.split("@")[-1].split(":")[0]
    return h[4:] if h.startswith("www.") else h


def _reg(host):
    p = (host or "").split(".")
    if len(p) > 2 and len(p[-1]) == 2 and p[-2] in ("co", "ac", "go", "or", "in", "net", "com", "org", "mi"):
        return ".".join(p[-3:])
    return ".".join(p[-2:])


def site_state(status, moved, host, final_host):
    """'down', 'moved' or None (answering, or turned a robot away) for one
    batch.tsv row. 401/403/429 are a server answering and refusing a robot,
    so they say nothing about a guest's browser."""
    try:
        code = int(status or 0)
    except ValueError:
        code = 0
    if code == 0 or (400 <= code < 600 and code not in (401, 403, 429)):
        return "down"
    if (moved or "").strip() == "yes" and final_host and _reg(_host(final_host)) != _reg(host):
        return "moved"
    return None


def load_sites(path=SITECHECK):
    """motdangify's website check: {record id: (state, final host)} and the
    same by host, plus the file's date."""
    out = {}
    try:
        fh = path.open(encoding="utf-8", newline="")
    except OSError:
        return out, ""
    csv.field_size_limit(1 << 30)
    with fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            host = _host(row.get("host") or "")
            st = site_state(row.get("status"), row.get("moved"), host, row.get("final_host"))
            val = (st, row.get("final_host") or "")
            if host:
                out["@" + host] = val
            for rid in (row.get("ids") or "").split():
                out[rid] = val
    when = datetime.date.fromtimestamp(path.stat().st_mtime).isoformat()
    return out, when


SOURCES = ("own-site", "osm", "overture", "own-name")


def amenity(a, key):
    """(word, source) for one amenity row of hotel_amenities.json, or None.

    word: yes · no · free · paid (shuttle). A row renders only with a value
    the file states and a source it names; an empty, unknown or unsourced row
    is left off the page. "no" comes only from a page or an OSM tag that says
    so (the file's own method), never from a missing fact."""
    x = (a or {}).get(key)
    if not isinstance(x, dict):
        return None
    src = x.get("source")
    url = x.get("url") or ""
    if src not in SOURCES and not url.startswith("http"):
        return None
    v = x.get("value")
    s = str(v).strip().lower() if v is not None else ""
    if v is True or s in ("yes", "y", "true", "มี"):
        word = "yes"
        cost = str(x.get("cost") or "").lower()
        if key == "shuttle" and cost in ("free", "paid"):
            word = cost
    elif v is False or s in ("no", "false", "ไม่มี"):
        if src not in ("own-site", "osm") or not url.startswith("http"):
            return None
        word = "no"
    else:
        return None
    return word, {"url": url if url.startswith("http") else "", "source": src,
                  "fetched": str(x.get("fetched") or "")[:10]}


def own_site(r, norm_url, url_kind):
    """The hotel's own website: the first one that is neither a social page
    nor a room-selling site."""
    a = r.get("attrs") or {}
    for raw in (r.get("website"), a.get("website")):
        u = norm_url(raw)
        if not u or url_kind(u):
            continue
        if any(o in _host(u) for o in OTA):
            continue
        return u
    return None


# ------------------------------------------------------------------ geometry

def point_in_poly(lat, lng, poly):
    """Ray casting; poly [[lat, lng], ...] (bearings_layer.point_in_poly)."""
    inside, j = False, len(poly) - 1
    for i in range(len(poly)):
        yi, xi = poly[i]
        yj, xj = poly[j]
        if (xi > lng) != (xj > lng) and lat < (yj - yi) * (lng - xi) / ((xj - xi) or 1e-12) + yi:
            inside = not inside
        j = i
    return inside


def _hav(a_lat, a_lng, b_lat, b_lng):
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    h = (math.sin(math.radians(b_lat - a_lat) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(b_lng - a_lng) / 2) ** 2)
    return 2 * 6371000.0 * math.asin(math.sqrt(h))


# The hospital, market and wat shelves also hold clinics, shops and shrines;
# the name has to say hospital, market or wat for the row to call it one.
HOSPITAL_NAME = re.compile(r"โรงพยาบาล|hospital|รพ\.", re.I)
ANIMAL = re.compile(r"สัตว์|animal|\bpet|\bvet", re.I)
WAT_NAME = re.compile(r"วัด|\bwat\b|temple", re.I)
MARKET_NAME = re.compile(r"ตลาด|กาด|market|bazaar|ถนนคนเดิน|walking street|\bkad\b|thalat|talat", re.I)


def _names(x):
    return " ".join(str(x.get(k) or "") for k in ("name", "nameTh", "nameEn"))


def _sane(road, crow):
    return road <= DETOUR * crow + DETOUR_PAD


# ------------------------------------------------------------------ road searches

def _search_to(net, targets, mode, cap):
    """Reversed multi-source search: every junction learns its road metres TO
    the nearest of `targets` [(lat, lng, payload)] and which one. Returns
    (dist array, who list, per-edge targets)."""
    fwd, back = FOOT if mode == "foot" else RIDE
    radj = net.adjacency(mode, reverse=True)
    n = len(net.nodes)
    dist = array.array("d", [math.inf]) * n
    who = array.array("i", [-1]) * n
    on_edge = {}
    pq = []
    for i, (lat, lng, _) in enumerate(targets):
        p = net.project(lat, lng, fwd | back)
        if p is None:
            continue
        k, at, off = p
        a, b, m, f, _ = net.edges[k]
        on_edge.setdefault(k, []).append((at, off, i))
        if f & fwd and off + at < dist[a]:
            dist[a], who[a] = off + at, i
            heapq.heappush(pq, (dist[a], a))
        if f & back and off + (m - at) < dist[b]:
            dist[b], who[b] = off + (m - at), i
            heapq.heappush(pq, (dist[b], b))
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u] or d > cap:
            continue
        for v, w in radj[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v], who[v] = nd, who[u]
                heapq.heappush(pq, (nd, v))
    return dist, who, on_edge


def _from(net, sr, lat, lng, mode, cap):
    """(metres, target index) from a point to the nearest target of a search
    made by _search_to, or None."""
    dist, who, on_edge = sr
    fwd, back = FOOT if mode == "foot" else RIDE
    p = net.project(lat, lng, fwd | back)
    if p is None:
        return None
    k, at, off = p
    a, b, m, f, _ = net.edges[k]
    best = None
    if f & back and who[a] >= 0:
        best = (off + at + dist[a], who[a])
    if f & fwd and who[b] >= 0:
        c = off + (m - at) + dist[b]
        if best is None or c < best[0]:
            best = (c, who[b])
    for t_at, t_off, i in on_edge.get(k, ()):          # the same stretch of road
        if (t_at >= at and f & fwd) or (t_at <= at and f & back):
            c = off + abs(t_at - at) + t_off
            if best is None or c < best[0]:
                best = (c, i)
    if best is None or best[0] > cap:
        return None
    return best


def _around(net, adj, lat, lng, grid, cap):
    """Forward walk from one point, bounded at `cap` metres; road metres to
    each candidate in `grid` cells near it. Returns {kind: [(m, rec)]}."""
    fwd, back = FOOT
    p = net.project(lat, lng, fwd | back)
    if p is None:
        return {}
    k0, at0, off0 = p
    a, b, m, f, _ = net.edges[k0]
    dist = {}
    pq = []
    if f & back:
        dist[a] = off0 + at0
        pq.append((dist[a], a))
    if f & fwd and off0 + (m - at0) < dist.get(b, math.inf):
        dist[b] = off0 + (m - at0)
        pq.append((dist[b], b))
    heapq.heapify(pq)
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist.get(u, math.inf) or d > cap:
            continue
        for v, w in adj[u]:
            nd = d + w
            if nd <= cap and nd < dist.get(v, math.inf):
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    out = {}
    c = _GRID_CELL
    cy0, cx0 = int(math.floor(lat / c)), int(math.floor(lng / c))
    for cy in range(cy0 - 1, cy0 + 2):
        for cx in range(cx0 - 1, cx0 + 2):
            for kind, rec, (k, at, off) in grid.get((cy, cx), ()):
                ea, eb, em, ef, _ = net.edges[k]
                best = math.inf
                if ef & fwd and ea in dist:
                    best = dist[ea] + at + off
                if ef & back and eb in dist:
                    best = min(best, dist[eb] + (em - at) + off)
                if k == k0 and ((at >= at0 and ef & fwd) or (at <= at0 and ef & back)):
                    best = min(best, off0 + abs(at - at0) + off)
                if best <= cap:
                    out.setdefault(kind, []).append((best, rec))
    return out


_GRID_CELL = 0.012     # ~1.3 km: a 3×3 block of cells covers the walk


# ------------------------------------------------------------------ prepare

def _fmt(m):
    if m < 1000:
        v = int(round(m / 10.0) * 10)
        return f"{v} ม.", f"{v} m"
    return f"{m / 1000:.1f} กม.", f"{m / 1000:.1f} km"


def _register(prov):
    d = _load_json(LANDMARKS, {})
    return {x["key"]: x for x in d.get(prov) or [] if x.get("key")}


def _name_pair(rec, reg_entry=None):
    if reg_entry:
        return reg_entry.get("th") or "", reg_entry.get("en") or ""
    return (rec.get("nameTh") or rec.get("name") or ""), (rec.get("nameEn") or "")


# build.py's link verdict, kept by prepare() for _src_line: a source the link
# checker has found dead is named without a link, as reach_block does.
_LINK = {"verdict": None, "broken": ()}


def prepare(g, data, net=None, h=None, log=print):
    """Every number the block prints, worked out once in the parent before
    the place pages fork. g: build globals (MOAT_POLY, _moat_crossings,
    PLACE_HREF, norm_url, url_kind). data: {prov: [records]}."""
    global _LINKS, _AMEN, _SITES, _SITES_DATE
    _DATA.clear()
    _LINKS = load_links(BOOKING)
    _AMEN = {k: v for k, v in _load_json(AMENITIES, {}).items() if isinstance(v, dict)}
    _SITES, _SITES_DATE = load_sites(SITECHECK)
    try:
        import importers.aircon_stated as _ac
    except Exception:                                   # noqa: BLE001
        _ac = None

    by_id = {r["id"]: r for recs in data.values() for r in recs}
    href = g.get("PLACE_HREF") or {}
    norm_url, url_kind = g["norm_url"], g["url_kind"]
    _LINK["verdict"], _LINK["broken"] = g.get("verdict"), tuple(g.get("BROKEN") or ())
    moat = g.get("MOAT_POLY")
    gates = [x for x in (g["_moat_crossings"]() if g.get("_moat_crossings") else []) if x[4] == "gate"]

    hotels = []
    for prov, recs in data.items():
        for r in recs:
            if not is_lodging(r):
                continue
            hotels.append((prov, r))
            a = r.get("attrs") or {}
            f = {"prov": prov}
            site = own_site(r, norm_url, url_kind)
            if site:
                st = _SITES.get(r["id"]) or _SITES.get("@" + _host(site))
                f["site"] = site
                v = g["verdict"](site) if g.get("verdict") else {}
                if st and st[0]:
                    f["site_state"], f["site_to"], f["site_when"] = st[0], _host(st[1]), _SITES_DATE
                elif v.get("status") in (g.get("BROKEN") or ()):
                    # check_links.py found it dead; reach_block retires it the same way
                    f["site_state"] = "down"
                    f["site_when"] = str(v.get("checkedAt") or g.get("LINK_HEALTH_DATE") or "")[:10]
            if ((a.get("facets") or {}).get("aircon") == "said"
                    or (_ac is not None and _ac.kind_of(r))):
                f["aircon"] = True
            am = {}
            for key, *_ in AMENITY:
                got = amenity(_AMEN.get(r["id"]), key)
                if got:
                    am[key] = got
            if am:
                f["amen"] = am
            if a.get("riverName") and a.get("riverM") is not None and r.get("geoPrecision") == "exact":
                f["river"] = (str(a["riverName"]), float(a["riverM"]))
            if prov == "cm" and moat and r.get("lat") is not None and r.get("geoPrecision") in ("exact", "approx"):
                f["inside"] = point_in_poly(r["lat"], r["lng"], moat)
            _DATA[r["id"]] = f

    if net is None:
        log("  hotel_layer: no road graph — no road distances")
        return _tally(by_id, h)

    pinned = [(p, r) for p, r in hotels if r.get("lat") is not None
              and r.get("geoPrecision") in ("exact", "approx")]
    exact = [(p, r) for p, r in pinned if r.get("geoPrecision") == "exact"]

    # 1 · by road to the places people ride to (scooter graph)
    for prov, items in TARGETS.items():
        reg = _register(prov)
        for key, ref, code, reg_key in items:
            entry = reg.get(ref) or (reg.get(reg_key) if reg_key else None)
            rec = by_id.get(entry["id"] if ref in reg else ref)
            if rec is None or rec.get("lat") is None:
                log(f"  hotel_layer: {prov} {key} not on record ({ref})")
                continue
            th, en = _name_pair(rec, entry)
            if code:
                th, en = f"{th} ({code})", f"{en} ({code})"
            sr = _search_to(net, [(rec["lat"], rec["lng"], None)], "ride", math.inf)
            for p, r in pinned:
                if p != prov:
                    continue
                hit = _from(net, sr, r["lat"], r["lng"], "ride", math.inf)
                if hit and _sane(hit[0], _hav(r["lat"], r["lng"], rec["lat"], rec["lng"])):
                    _DATA[r["id"]].setdefault("road", []).append((key, th, en, hit[0], href.get(rec["id"])))
            del sr
    #   the nearest moat gate, CM, for places outside the moat
    if gates:
        sr = _search_to(net, [(x[0], x[1], x) for x in gates], "ride", math.inf)
        for p, r in pinned:
            if p != "cm" or _DATA[r["id"]].get("inside"):
                continue
            hit = _from(net, sr, r["lat"], r["lng"], "ride", math.inf)
            if hit:
                gx = gates[hit[1]]
                if _sane(hit[0], _hav(r["lat"], r["lng"], gx[0], gx[1])):
                    _DATA[r["id"]]["gate"] = (gx[2], gx[3], hit[0])
        del sr
    net.adj.pop(("ride", True), None)

    # 3 · nearest by road: 7-Eleven, pharmacy (on foot), hospital (scooter)
    sets = {"seven": [], "pharmacy": [], "hospital": []}
    for recs in data.values():
        for x in recs:
            if x.get("lat") is None or x.get("geoPrecision") != "exact":
                continue
            subs = x.get("sub") or []
            if "convenience" in subs and (x.get("attrs") or {}).get("brand") == "7-Eleven":
                sets["seven"].append(x)
            if "pharmacy" in subs:
                sets["pharmacy"].append(x)
            if "hospital" in subs and HOSPITAL_NAME.search(_names(x)) and not ANIMAL.search(_names(x)):
                sets["hospital"].append(x)
    for kind, mode, cap in (("seven", "foot", NEAR_FOOT_M), ("pharmacy", "foot", NEAR_FOOT_M),
                            ("hospital", "ride", NEAR_RIDE_M)):
        rows = sets[kind]
        sr = _search_to(net, [(x["lat"], x["lng"], None) for x in rows], mode, cap)
        for p, r in exact:
            hit = _from(net, sr, r["lat"], r["lng"], mode, cap)
            if not hit:
                continue
            x = rows[hit[1]]
            if x["id"] == r["id"] or not _sane(hit[0], _hav(r["lat"], r["lng"], x["lat"], x["lng"])):
                continue
            _DATA[r["id"]].setdefault("near", []).append((kind, x, hit[0], mode))
        del sr
    net.adj.pop(("ride", True), None)

    # 9 · around it: wats, markets, cafés within a walk
    grid = {}
    for recs in data.values():
        for x in recs:
            if x.get("lat") is None or x.get("geoPrecision") != "exact" or x["id"] not in href:
                continue
            cats, subs = x.get("cat") or [], x.get("sub") or []
            kind = ("wat" if "wat" in cats and WAT_NAME.search(_names(x))
                    else "market" if "market" in cats and MARKET_NAME.search(_names(x))
                    else "cafe" if "cafe" in subs else None)
            if not kind:
                continue
            p = net.project(x["lat"], x["lng"], 3)
            if p is None:
                continue
            cell = (int(math.floor(x["lat"] / _GRID_CELL)), int(math.floor(x["lng"] / _GRID_CELL)))
            grid.setdefault(cell, []).append((kind, x, p))
    adj = net.adjacency("foot")
    for p, r in exact:
        got = _around(net, adj, r["lat"], r["lng"], grid, AROUND_M)
        keep = {}
        for kind, rows in got.items():
            rows = sorted(((m, x) for m, x in rows if x["id"] != r["id"]
                           and _sane(m, _hav(r["lat"], r["lng"], x["lat"], x["lng"]))),
                          key=lambda t: t[0])
            seen, pick = set(), []
            for m, x in rows:
                if x["id"] in seen:
                    continue
                seen.add(x["id"])
                pick.append((m, x))
                if len(pick) == AROUND_EACH:
                    break
            if pick:
                keep[kind] = pick
        if keep:
            _DATA[r["id"]]["around"] = keep
    net.adj.pop(("foot", False), None)
    return _tally(by_id, h)


def _tally(by_id, h):
    """Count what renders, by section, and the bytes each block adds."""
    _COUNTS.clear()
    _BYTES.clear()
    for rid, f in _DATA.items():
        for k in ("site", "aircon", "amen", "river", "road", "gate", "near", "around"):
            if f.get(k):
                _COUNTS[k] = _COUNTS.get(k, 0) + 1
        if f.get("inside"):
            _COUNTS["inside"] = _COUNTS.get("inside", 0) + 1
        if f.get("site_state"):
            _COUNTS["site_" + f["site_state"]] = _COUNTS.get("site_" + f["site_state"], 0) + 1
        if h and rid in by_id:
            _BYTES.append(len(block(by_id[rid], h).encode()))
    _COUNTS["pages"] = len(_DATA)
    return counts()


def counts():
    b = sorted(_BYTES)
    med = b[len(b) // 2] if b else 0
    return dict(_COUNTS, median_bytes=med, links_search=len(_LINKS["search"]),
                links_places=len(_LINKS["places"]), sites_checked=_SITES_DATE)


# ------------------------------------------------------------------ markup

def _src_line(src, site, h):
    when = src.get("fetched") or ""
    url = src.get("url") or ""
    kind = src.get("source")
    if kind == "own-name":
        th, en = "ที่มา: ชื่อของที่นี่", "from its own name"
    elif kind == "overture":
        th, en = "ที่มา: หมวดในเพจเฟซบุ๊กของที่นี่ (Overture Maps)", "from its Facebook page category (Overture Maps)"
    elif kind == "osm":
        th, en = "ที่มา: OpenStreetMap", "from OpenStreetMap"
    elif site and url and _reg(_host(url)) == _reg(_host(site)):
        th, en = "ที่มา: เว็บของโรงแรม " + when, "from the hotel's site, " + when
    else:
        th, en = "ที่มา: " + _host(url) + " " + when, "from " + _host(url) + ", " + when
    words = h["bi"](th.strip(), en.strip(" ,"))
    if url and _LINK["verdict"] and (_LINK["verdict"](url) or {}).get("status") in _LINK["broken"]:
        url = ""
    if url:
        words = f'<a href="{h["att"](url)}" rel="nofollow noopener">{words}</a>'
    return f'<span class="src">{words}</span>'


def _paid(r, h):
    att, esc = h["att"], h["esc"]
    links = list(_LINKS["places"].get(r["id"]) or [])
    if _LINKS["search"]:
        q = urllib.parse.quote(" ".join(x for x in ((r.get("nameEn") or r.get("name") or ""),
                                                    {"cm": "Chiang Mai", "cr": "Chiang Rai"}.get(r.get("province"), ""))
                                        if x))
        for t in _LINKS["search"]:
            links.append({"name": t["name"], "url": t["url"].replace("{q}", q)})
    if not links:
        return ""
    a = " · ".join(f'<a href="{att(x["url"])}" rel="sponsored nofollow noopener">{esc(x["name"])}</a>'
                   for x in links)
    return (f'<li>{a}<span class="paidnote">'
            + h["bi"]("ลิงก์มีค่าตอบแทน: มดแดงได้ค่าแนะนำเมื่อคุณจองผ่านลิงก์นี้",
                      "Paid links: Mot Dang earns a fee if you book.")
            + "</span></li>")


def _booking(r, f, h):
    bi, esc, att = h["bi"], h["esc"], h["att"]
    own = bi("เว็บของโรงแรม", "Hotel's own site")
    when = f.get("site_when") or ""
    rows = []
    reach = []
    if f.get("site_state"):
        for c in h["reach"](r):
            if c["kind"] == "phone":
                reach.append(f'<a href="{att(h["tel_href"](c["text"]))}">{esc(h["fmt_tel"](c["text"]))}</a>')
            elif c["kind"] == "line":
                reach.append(f'<a href="{att(c["href"])}" rel="nofollow noopener">LINE {esc(c["text"])}</a>')
        if reach:
            rows.append(f'<li>{bi("จองทางโทรหรือ LINE", "Book by phone or LINE")}: {" · ".join(reach)}</li>')
    site = f.get("site")
    if site:
        dom = esc(_host(site))
        if f.get("site_state") == "down":
            rows.append(f'<li class="down">{own}: {dom} — '
                        + bi(f"ไม่ตอบ ตรวจเมื่อ {when}", f"not answering on {when}") + "</li>")
        elif f.get("site_state") == "moved":
            to = esc(f.get("site_to") or "")
            rows.append(f'<li class="down">{own}: {dom} — '
                        + bi(f"ตอนนี้พาไปที่ {to} ตรวจเมื่อ {when}", f"now goes to {to}, checked {when}")
                        + "</li>")
        else:
            rows.append(f'<li>{own}: '
                        f'<a class="own" href="{att(site)}" rel="noopener">{dom}</a></li>')
    paid = _paid(r, h)
    if paid:
        rows.append(paid)
    if not rows:
        return ""
    return f'<h3>{bi("จอง", "Booking")}</h3><ul class="rows book">{"".join(rows)}</ul>'


def _strip(f, h):
    bi, icon = h["bi"], h["icon"]
    out = []
    if "inside" in f:
        if f["inside"]:
            out.append(f'<li class="moat">{icon("i-moat", 18)} {bi("ในคูเมือง", "Inside the old city (moat)")}</li>')
        elif f.get("gate"):
            th, en = _fmt(f["gate"][2])
            out.append(f'<li class="moat">{icon("i-moat", 18)} {bi(f"คูเมือง {th}", f"Old city {en}")}</li>')
    for key, ic, th, en in AMENITY:
        got = (f.get("amen") or {}).get(key)
        if not got or got[0] == "no":
            continue
        w = {"yes": ("", ""), "free": (" ฟรี", " free"), "paid": (" มีค่าบริการ", " paid")}[got[0]]
        out.append(f'<li>{icon(ic, 18)} {bi(th + w[0], en + w[1])}</li>')
    if f.get("aircon"):
        out.append(f'<li>{icon("i-air", 18)} {bi("แอร์", "Air con")}</li>')
    return f'<ul class="hq">{"".join(out)}</ul>' if out else ""


def _facts(f, h):
    bi = h["bi"]
    rows = []
    for key, ic, th, en in AMENITY:
        got = (f.get("amen") or {}).get(key)
        if not got:
            continue
        val = {"yes": ("มี", "yes"), "no": ("ไม่มี", "no"), "free": ("ฟรี", "free"),
               "paid": ("มีค่าบริการ", "paid")}[got[0]]
        rows.append(f'<li>{bi(th, en)}: <b>{bi(*val)}</b>{_src_line(got[1], f.get("site"), h)}</li>')
    if not rows:
        return ""
    return f'<ul class="rows">{"".join(rows)}</ul>'


def _road(f, h):
    bi, esc, att = h["bi"], h["esc"], h["att"]
    rows = []
    if f.get("gate"):
        gth, gen, m = f["gate"]
        th, en = _fmt(m)
        rows.append(f'<li>{bi(gth, gen)} · <b>{bi(th, en)}</b></li>')
    for key, nth, nen, m, hr in f.get("road") or []:
        th, en = _fmt(m)
        nm = bi(nth, nen)
        if hr:
            nm = f'<a href="../../{att(hr)}.html">{nm}</a>'
        rows.append(f'<li>{nm} · <b>{bi(th, en)}</b></li>')
    if not rows:
        return ""
    return f'<h3>{bi("ระยะทางตามถนน", "By road")}</h3><ul class="rows">{"".join(rows)}</ul>'


NEAR_LABEL = {"seven": ("เซเว่น", "7-Eleven"), "pharmacy": ("ร้านขายยา", "Pharmacy"),
              "hospital": ("โรงพยาบาล", "Hospital")}


def _near(f, h):
    bi, att = h["bi"], h["att"]
    rows = []
    for kind, x, m, mode in f.get("near") or []:
        kth, ken = NEAR_LABEL[kind]
        th, en = _fmt(m)
        hr = h["href"](x["id"])
        nm = h["name_bi"](x)
        if hr:
            nm = f'<a href="../../{att(hr)}.html">{nm}</a>'
        tail = ""
        if mode == "foot":
            mins = max(1, round(m / WALK_M_PER_MIN))
            tail = " · " + bi(f"เดิน ~{mins} นาที", f"~{mins} min walk")
        rows.append(f'<li>{bi(kth, ken)}: {nm} · <b>{bi(th, en)}</b>{tail}</li>')
    if not rows:
        return ""
    return f'<h3>{bi("ใกล้สุดตามถนน", "Nearest by road")}</h3><ul class="rows">{"".join(rows)}</ul>'


def _water(f, h):
    bi, esc = h["bi"], h["esc"]
    if not f.get("river"):
        return ""
    name, m = f["river"]
    th, en = _fmt(m)
    rd = h["reading"](name) if h.get("reading") else ""
    links = []
    if f.get("prov") == "cm":
        links.append(f'<a href="../../nam.html">{bi("ระดับน้ำปิง", "Ping river level")}</a>')
    links.append(f'<a href="../../chuai.html">{bi("น้ำท่วม", "Flood")}</a>')
    return (f'<h3>{bi("น้ำ", "Water")}</h3><ul class="rows"><li>'
            f'<span class="th solo" lang="th">{esc(name)}</span>'
            + (f' <span class="en roman" lang="en">{esc(rd)}</span>' if rd else "")
            + f' · {bi(th + " จากหมุด", en + " from the pin")} · {" · ".join(links)}</li></ul>')


AROUND = (("wat", "i-wat", "วัด", "Wats"), ("market", "i-market", "ตลาด", "Markets"),
          ("cafe", "i-coffee", "คาเฟ่", "Cafés"))


def _around_html(f, h):
    bi, att = h["bi"], h["att"]
    got = f.get("around") or {}
    parts = []
    for kind, ic, th, en in AROUND:
        rows = got.get(kind)
        if not rows:
            continue
        lis = []
        for m, x in rows:
            mth, men = _fmt(m)
            hr = h["href"](x["id"])
            nm = h["name_bi"](x)
            lis.append(f'<li><a href="../../{att(hr)}.html">{nm}</a> · {bi(mth, men)}</li>' if hr
                       else f"<li>{nm} · {bi(mth, men)}</li>")
        parts.append(f'<details><summary>{h["icon"](ic, 16)} {bi(th, en)} ({len(lis)})</summary>'
                     f'<ul>{"".join(lis)}</ul></details>')
    if not parts:
        return ""
    return (f'<div class="net"><h3>{bi("รอบ ๆ ที่พัก", "Around it")} '
            f'<span class="src">{bi("เดินตามถนน", "on foot, by road")}</span></h3>{"".join(parts)}</div>')


def block(r, h):
    """h: bi, esc, att, icon, name_bi, href, reach, fmt_tel, tel_href, reading."""
    f = _DATA.get(r.get("id"))
    if f is None:
        return ""
    inner = (_strip(f, h) + _booking(r, f, h) + _facts(f, h) + _road(f, h) + _near(f, h)
             + _water(f, h) + _around_html(f, h))
    if not inner:
        return ""
    return f'<section class="stay"><h2>{h["icon"]("i-bed", 20)} {h["bi"]("ที่พัก", "Stay")}</h2>{inner}</section>'
