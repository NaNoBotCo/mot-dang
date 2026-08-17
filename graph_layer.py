#!/usr/bin/env python3
"""The Mot Dang graph — every relation the catalogue already holds, with a
receipt on each one.

WHY A GRAPH AT ALL
The directory knows far more than a page shows. It knows which places share a
road, which stand within sight of each other, which pour the same cuisine,
which are branches of one shop, which wat hosts which festival, and which
temple has a page in the wichaa archive. All of that is computed today and
thrown away after it is drawn.

WHAT THIS IS NOT
It is not a framework and it is not a server. It is one module, hooked into
build() in two lines the way festivals_layer and toilets_layer are, writing
static JSONL. Nothing here is inferred from a language model's priors.

THE VOCABULARY, taken whole from manuscript-wiki/cartography.py so the two
properties describe their relations the same way:

    Node  {id, kind, label, ...}
    Edge  {src, dst, type, prov, w, ev}
      prov  authored     a human wrote it
            adjudicated  a written rule decided it, and it fails closed
            computed     the catalogue's own columns or coordinates say so
            derived      a bot noticed it, with the count it noticed
      w     a real count, or metres. NEVER an invented score.
      ev    a receipt a reader can read: "312 m apart", "23 on this road".

Deterministic: nodes sorted by id, edges by (src, type, dst), no timestamps.
An unchanged catalogue rebuilds byte-identical, so a diff of the graph means
something happened.

    docs/api/graph/nodes.jsonl
    docs/api/graph/edges.jsonl
    docs/api/graph/summary.json
    docs/api/graph.jsonld
"""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict

CSS = """.threads{margin:1.2rem 0;padding:.8rem 1rem;background:#fff;
border:1px solid var(--soft);border-radius:.8rem}
.threads h2{margin:.1rem 0 .5rem;font-size:1.02rem}
.threads ul{margin:.2rem 0;padding-left:1.1rem}
.threads li{padding:.22rem 0}
"""

NEAR_M = 400          # a neighbour you can see from the doorway
NEAR_K = 6            # how many of them are worth carrying
MIN_CUISINE = 5       # a cuisine node needs a shelf behind it
MIN_BRAND = 3         # two shops of a name is a coincidence; three is a chain


def _haversine(a_lat, a_lng, b_lat, b_lng):
    r = 6371000.0
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    dp = p2 - p1
    dl = math.radians(b_lng - a_lng)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def build_graph(g, data):
    """Return (nodes, edges). Pure — reads the catalogue, writes nothing."""
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    name_text = g["name_text"]
    place_slug = g["place_slug"]

    def node(nid, kind, label, **extra):
        if nid not in nodes:
            nodes[nid] = {"id": nid, "kind": kind, "label": label, **extra}
        return nid

    def edge(src, dst, etype, prov, w, ev):
        edges.append({"src": src, "dst": dst, "type": etype,
                      "prov": prov, "w": w, "ev": ev})

    records = [r for p in g["PROVINCES"] for r in data[p["key"]]]
    by_id = {r["id"]: r for r in records}

    # ---------------------------------------------------------------- places
    for r in records:
        pv = r["province"]
        node(f'place:{r["id"]}', "place", name_text(r),
             href=f'{pv}/p/{place_slug(r)}.html', province=pv)

    # ------------------------------------------------------------- the shelves
    for p in g["PROVINCES"]:
        for r in data[p["key"]]:
            for cat in r.get("cat") or []:
                cfg = (g["CATS"].get(cat) or {})
                cid = node(f"cat:{cat}", "category",
                           f'{cfg.get("th", cat)} · {cfg.get("en", cat)}'.strip(" ·"))
                edge(f'place:{r["id"]}', cid, "in_category", "computed", 1,
                     "filed on this shelf")
            for sub in r.get("sub") or []:
                sid = node(f"sub:{sub}", "subcategory", sub)
                edge(f'place:{r["id"]}', sid, "sub_of", "computed", 1,
                     "filed on this sub-shelf")

    # ------------------------------------------------------------------ roads
    # streets.json publishes HOW a place reached its road, and the receipt says
    # so: an addr:street the place stated, or the nearest line within 30 m.
    for st in (g.get("STREETS") or []):
        sid = node(f'street:{st.get("slug")}', "street",
                   f'{st.get("name") or ""} · {st.get("nameEn") or ""}'.strip(" ·"),
                   href=f'{st.get("province", "cm")}/soi/{st.get("slug", "")}.html')
        for m in st.get("places") or []:
            pid = m.get("id") if isinstance(m, dict) else m
            if f"place:{pid}" not in nodes:
                continue
            via = (m.get("via") if isinstance(m, dict) else "") or "stated"
            d = m.get("d") if isinstance(m, dict) else None
            ev = ("the place states this road" if via == "stated"
                  else f"nearest road line, {int(d)} m" if d is not None
                  else "nearest road line")
            edge(f"place:{pid}", sid, "on_street", "computed",
                 int(d) if d is not None else 1, ev)

    # --------------------------------------------------------------- proximity
    # The same neighbours the place map already draws — now kept, with the
    # distance as the weight and as the receipt.
    grid = defaultdict(list)
    for r in records:
        if r.get("lat") is None or r.get("lng") is None:
            continue
        if (r.get("geoPrecision") or "exact") == "needs-pin":
            continue
        grid[(round(r["lat"], 2), round(r["lng"], 2))].append(r)
    for r in records:
        if r.get("lat") is None or r.get("lng") is None:
            continue
        if (r.get("geoPrecision") or "exact") == "needs-pin":
            continue
        cand = []
        gla, gln = round(r["lat"], 2), round(r["lng"], 2)
        for dla in (-0.01, 0.0, 0.01):
            for dln in (-0.01, 0.0, 0.01):
                for o in grid.get((round(gla + dla, 2), round(gln + dln, 2)), ()):
                    if o["id"] == r["id"]:
                        continue
                    m = _haversine(r["lat"], r["lng"], o["lat"], o["lng"])
                    if m <= NEAR_M:
                        cand.append((m, o["id"]))
        cand.sort()
        for m, oid in cand[:NEAR_K]:
            if r["id"] < oid:   # one edge per pair, not two
                edge(f'place:{r["id"]}', f"place:{oid}", "near", "computed",
                     int(round(m)), f"{int(round(m))} m apart")

    # --------------------------------------------------------------- festivals
    for f in (g.get("FESTIVALS") or []):
        fid = node(f'festival:{f["id"]}', "festival",
                   f'{f.get("name_th", "")} · {f.get("name_en", "")}'.strip(" ·"),
                   href=f'festivals/{f["id"]}.html')
        window = f.get("window_en") or f.get("window_th") or ""
        for v in f.get("venues") or []:
            pid = v.get("place_id")
            if not pid or f"place:{pid}" not in nodes:
                continue
            edge(f"place:{pid}", fid, "hosts_festival", "computed", 1,
                 window[:80] or "the festival year here")

    # ------------------------------------------------------- cuisine and brand
    cuisine_places = defaultdict(list)
    brand_places = defaultdict(list)
    for r in records:
        a = r.get("attrs") or {}
        for c in str(a.get("cuisine") or "").split(";"):
            c = c.strip()
            if c:
                cuisine_places[c].append(r["id"])
        b = (a.get("brand") or "").strip()
        if b:
            brand_places[b].append(r["id"])
    for c, ids in cuisine_places.items():
        if len(ids) < MIN_CUISINE:
            continue
        cid = node(f"cuisine:{c}", "cuisine", c)
        for pid in ids:
            edge(f"place:{pid}", cid, "serves_cuisine", "computed", len(ids),
                 f"{len(ids)} places pour this")
    for b, ids in brand_places.items():
        if len(ids) < MIN_BRAND:
            continue
        bid = node(f"brand:{b}", "brand", b)
        for pid in ids:
            edge(f"place:{pid}", bid, "branch_of", "computed", len(ids),
                 f"{len(ids)} branches on the map")

    # -------------------------------------------------- the register's geography
    for r in records:
        a = r.get("attrs") or {}
        if a.get("amphoe"):
            aid = node(f'amphoe:{a["amphoe"]}', "amphoe", a["amphoe"])
            edge(f'place:{r["id"]}', aid, "in_amphoe", "computed", 1,
                 "the temple register files it here")
        if a.get("tambon"):
            tid = node(f'tambon:{a["tambon"]}', "tambon", a["tambon"])
            edge(f'place:{r["id"]}', tid, "in_tambon", "computed", 1,
                 "the temple register files it here")

    # ------------------------------------------------------- the other property
    # 523 temples matched to wichaa.net by a written rule — exact Thai name AND
    # within 400 m — which is an adjudication, not a computation: it fails
    # closed and reports what it could not settle.
    links = (g.get("WICHAA_LINKS") or {})
    for pid, link in links.items():
        if not isinstance(link, dict) or f"place:{pid}" not in nodes:
            continue
        # data/wichaa_links.json was generated against the Cloudflare Pages
        # host. wichaa.net serves the same paths and is the name the archive
        # goes by, so that is the one 523 public pages point at — a staging
        # subdomain published across the site is the exposure that was cleaned
        # up once already. link_wichaa.py should record wichaa.net at source.
        url = (link.get("url") or "").replace(
            "https://wichaa.pages.dev", "https://wichaa.net")
        wid = node(f'wichaa:{link.get("slug")}', "wichaa_place",
                   link.get("name_th") or link.get("name_roman") or "",
                   href=url)
        m = link.get("metres")
        edge(f"place:{pid}", wid, "same_wat_as_wichaa", "adjudicated", 1,
             f"same Thai name, {int(m)} m apart" if isinstance(m, (int, float))
             else "same Thai name, within 400 m")

    edges.sort(key=lambda e: (e["src"], e["type"], e["dst"]))
    return [nodes[k] for k in sorted(nodes)], edges


# What the band may say. Everything else the graph knows is already on the
# page in better words, and a thread that repeats the line above it is noise:
# shelf membership is in the breadcrumb, the road and its neighbours are in the
# facts list, the festival has its own band, and the near-by places are the
# dots on the map — which are links now, so the reader can already walk them.
# A thread has to LEAD somewhere, and it must not repeat the page it sits on.
# That empties the band today, on purpose:
#   same_wat_as_wichaa — already a row in "Read more elsewhere", and a band
#       that says it again is the noise this band exists to avoid.
#   branch_of, serves_cuisine — real edges, in the graph file, but a cuisine
#       has no page and search does not match on cuisine yet, so the row would
#       read "thai — 761 places pour this" with no door in it.
# Both are listed here and gated on a reachable destination, so the band lights
# itself the day WO-4 gives cuisine and brand a filtered URL to point at.
BAND_TYPES = ("branch_of", "serves_cuisine")

THREAD_WORDS = {
    "same_wat_as_wichaa": ("อ่านวัดนี้ในคลังใบลาน wichaa",
                           "this temple in the wichaa archive"),
    "branch_of": ("สาขาเดียวกัน", "the same shop, elsewhere"),
    "serves_cuisine": ("ร้านแนวเดียวกัน", "others cooking this"),
}


def threads_for(place_id, edges_by_src, nodes, limit=4):
    """The lateral links worth putting on a page, with their receipts."""
    order = {t: i for i, t in enumerate(BAND_TYPES)}
    out = []
    for e in edges_by_src.get(f"place:{place_id}", ()):
        if e["type"] not in order:
            continue
        dst = nodes.get(e["dst"])
        if not dst:
            continue
        out.append((order[e["type"]], e, dst))
    out.sort(key=lambda x: (x[0], -(x[1].get("w") or 0)))
    return [(e, d) for _r, e, d in out[:limit]]


def threads_band(place_id, edges_by_src, nodes, g, depth=2):
    """The band itself — each thread named, linked, and carrying its receipt."""
    mine = threads_for(place_id, edges_by_src, nodes)
    if not mine:
        return ""
    bi, esc = g["bi"], g["esc"]
    up = "../" * depth
    rows = []
    for e, dst in mine:
        th, en = THREAD_WORDS.get(e["type"], (e["type"], e["type"]))
        href = dst.get("href") or ""
        if not href:
            continue          # no door, no thread
        # A link off the site keeps its host; everything else is ours.
        target = href if href.startswith("http") else up + href
        rows.append(f'<li>{bi(th, en)} — '
                    f'<a href="{target}">{esc(dst.get("label") or "")}</a> '
                    f'<span class="tinynote">{esc(e["ev"])}</span></li>')
    if not rows:
        return ""
    return (f'<div class="threads"><h2>{bi("เส้นทางต่อจากที่นี่", "Threads from here")}</h2>'
            f'<ul>{"".join(rows)}</ul></div>')


def emit(g, data):
    """Write the graph. Two lines in build(), the layer discipline."""
    nodes, edges = build_graph(g, data)
    out = g["DOCS"] / "api" / "graph"
    out.mkdir(parents=True, exist_ok=True)

    (out / "nodes.jsonl").write_text(
        "".join(json.dumps(n, ensure_ascii=False, sort_keys=True) + "\n"
                for n in nodes), encoding="utf-8")
    (out / "edges.jsonl").write_text(
        "".join(json.dumps(e, ensure_ascii=False, sort_keys=True) + "\n"
                for e in edges), encoding="utf-8")

    kinds = Counter(n["kind"] for n in nodes)
    types = Counter(e["type"] for e in edges)
    provs = Counter(e["prov"] for e in edges)
    summary = {
        "schema": "motdang-graph/1",
        "nodes": len(nodes), "edges": len(edges),
        "byKind": dict(sorted(kinds.items())),
        "byType": dict(sorted(types.items())),
        "byProvenance": dict(sorted(provs.items())),
        "note": ("Every edge carries a real count or a distance in metres and a "
                 "receipt in plain words. Nothing here is inferred from a "
                 "language model's priors. Provenance: computed = the "
                 "catalogue's own columns or coordinates; adjudicated = a "
                 "written rule that fails closed; authored = a person wrote it."),
        "licence": "CC BY 4.0 · map-derived fields © OpenStreetMap contributors (ODbL)",
    }
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")

    base = g["BASE"]
    jsonld = {
        "@context": {"@vocab": "https://schema.org/",
                     "md": "https://motdang.net/api/graph#"},
        "@graph": [
            {"@id": base + (n.get("href") or ""), "@type":
             "Place" if n["kind"] == "place" else
             "Event" if n["kind"] == "festival" else "Thing",
             "name": n["label"]}
            for n in nodes if n.get("href")],
    }
    (g["DOCS"] / "api" / "graph.jsonld").write_text(
        json.dumps(jsonld, ensure_ascii=False), encoding="utf-8")

    # The band on a place page, written by post-processing for the same reason
    # festivals_layer does it: this layer stays one file and the place pages
    # keep exactly one owner. Only pages that actually have a thread are
    # reopened — an empty band is worse than no band.
    edges_by_src = defaultdict(list)
    for e in edges:
        if e["type"] in BAND_TYPES:
            edges_by_src[e["src"]].append(e)
    nodes_by_id = {n["id"]: n for n in nodes}
    by_id = {r["id"]: r for p in g["PROVINCES"] for r in data[p["key"]]}
    touched = 0
    for src in sorted(edges_by_src):
        pid = src.split(":", 1)[1]
        rec = by_id.get(pid)
        if not rec:
            continue
        path = g["DOCS"] / rec["province"] / "p" / f'{g["place_slug"](rec)}.html'
        if not path.exists():
            continue
        band = threads_band(pid, edges_by_src, nodes_by_id, g, depth=2)
        if not band:
            continue
        html = path.read_text()
        if "<footer>" not in html:
            continue
        html = html.replace(
            "</head>", '<link rel="stylesheet" href="../../graph.css"></head>', 1)
        path.write_text(html.replace("<footer>", band + "<footer>", 1))
        touched += 1
    (g["DOCS"] / "graph.css").write_text(CSS, encoding="utf-8")

    return {"nodes": len(nodes), "edges": len(edges), "types": len(types),
            "adjudicated": provs.get("adjudicated", 0), "bands": touched}
