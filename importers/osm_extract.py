#!/usr/bin/env python3
"""The crawl's groups, answered from a Geofabrik extract instead of Overpass.

    python3 importers/osm_extract.py <thailand-latest.osm.pbf> pth [out_dir]

Needs pyosmium and shapely (on motdang-build: /srv/osm/venv). Writes one file
per group of crawl_overpass.QUERIES into cache/overpass/<province>/ (or
out_dir), in Overpass's own `out center tags` shape, so import_overpass.py
reads it unchanged, plus `wats.json` (amenity=place_of_worship +
religion=buddhist, which CM and CR take from mueang-map) and EXTRACT, the
extract's replication timestamp.

Written 2026-10-12 for Pathum Thani, when overpass-api.de answered every
province-wide query with 504 and kumi.systems did not answer at all. One
download from Geofabrik in place of 43 groups of somebody else's server time.

The element is kept when its centre (the middle of its bounding box, as
Overpass computes `center`) falls inside the province's boundary relation,
ISO3166-2=<code> — the area, not a rectangle, as crawl_overpass.py asks.
"""
import json
import re
import sys
from pathlib import Path

import osmium
from shapely import wkb
from shapely.geometry import Point
from shapely.prepared import prep

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from crawl_overpass import QUERIES, PROVINCE_AREA, BBOX  # noqa: E402

EXTRA = {"wats": ['nwr["amenity"="place_of_worship"]["religion"="buddhist"]']}

PART = re.compile(r'\[([^\]]*)\]')


def compile_selector(sel):
    """nwr[...][...] → a test on a tag dict. The forms the crawl uses:
    ["k"="v"], ["k"], ["k"~"re"], ["k"~"re",i], [~"kre"~"vre"]."""
    tests = []
    for p in PART.findall(sel):
        m = re.fullmatch(r'"([^"]+)"="([^"]*)"', p)
        if m:
            k, v = m.groups()
            tests.append(lambda t, k=k, v=v: t.get(k) == v)
            continue
        m = re.fullmatch(r'"([^"]+)"', p)
        if m:
            k = m.group(1)
            tests.append(lambda t, k=k: k in t)
            continue
        m = re.fullmatch(r'"([^"]+)"~"([^"]*)"(,i)?', p)
        if m:
            k, rx, ci = m.groups()
            r = re.compile(rx, re.I if ci else 0)
            tests.append(lambda t, k=k, r=r: k in t and bool(r.search(t[k])))
            continue
        m = re.fullmatch(r'~"([^"]+)"~"([^"]*)"(,i)?', p)
        if m:
            kx, vx, ci = m.groups()
            kr, vr = re.compile(kx), re.compile(vx, re.I if ci else 0)
            tests.append(lambda t, kr=kr, vr=vr: any(kr.search(k) and vr.search(v)
                                                     for k, v in t.items()))
            continue
        raise ValueError(f"selector part not understood: [{p}] in {sel}")
    return lambda t: all(f(t) for f in tests)


def main():
    pbf, province = sys.argv[1], sys.argv[2]
    out = Path(sys.argv[3]) if len(sys.argv) > 3 else ROOT / "cache" / "overpass" / province
    code = PROVINCE_AREA[province]
    # Each selector filed under the key its first part names, so an object is
    # tested only against selectors whose key it carries; [~"re"~"re"] parts
    # (no key of their own) are always tested.
    by_key, loose = {}, []
    for g, ss in {**QUERIES, **EXTRA}.items():
        for sel in ss:
            f = compile_selector(sel)
            m = re.match(r'nwr\["([^"]+)"', sel)
            (by_key.setdefault(m.group(1), []) if m else loose).append((g, f))
    groups = {g: None for g in {**QUERIES, **EXTRA}}
    S, W, N, E = (float(x) for x in BBOX[province].split(","))

    def boxed(lat, lng):
        return S <= lat <= N and W <= lng <= E

    def wanted(tags):
        out = []
        for k in tags:
            for g, f in by_key.get(k, ()):
                if g not in out and f(tags):
                    out.append(g)
        for g, f in loose:
            if g not in out and f(tags):
                out.append(g)
        return out

    hits = {g: [] for g in groups}
    boundary = None
    seen_way_area = set()
    idx = osmium.index.create_map("sparse_file_array," + str(Path(pbf).with_suffix(".nodes")))
    fp = osmium.FileProcessor(pbf).with_locations(idx).with_areas()
    wkbf = osmium.geom.WKBFactory()
    ts = osmium.io.Reader(pbf, osmium.osm.osm_entity_bits.NOTHING).header().get("osmosis_replication_timestamp")
    for o in fp:
        tags = {t.k: t.v for t in o.tags}
        if not tags:
            continue
        if o.is_area():
            if (not o.from_way() and tags.get("ISO3166-2") == code
                    and tags.get("boundary") == "administrative"):
                boundary = wkb.loads(wkbf.create_multipolygon(o), hex=True)
            if o.from_way():
                continue          # the way itself is handled as a way
            gs = wanted(tags)
            if not gs:
                continue
            try:
                g = wkb.loads(wkbf.create_multipolygon(o), hex=True)
            except Exception:
                continue
            x0, y0, x1, y1 = g.bounds
            el = {"type": "relation", "id": o.orig_id(),
                  "center": {"lat": round((y0 + y1) / 2, 7), "lon": round((x0 + x1) / 2, 7)},
                  "tags": tags}
        elif o.is_node():
            if not o.location.valid() or not boxed(o.location.lat, o.location.lon):
                continue
            gs = wanted(tags)
            if not gs:
                continue
            el = {"type": "node", "id": o.id, "lat": round(o.location.lat, 7),
                  "lon": round(o.location.lon, 7), "tags": tags}
        elif o.is_way():
            if not len(o.nodes) or not o.nodes[0].location.valid() \
                    or not boxed(o.nodes[0].location.lat, o.nodes[0].location.lon):
                continue
            gs = wanted(tags)
            if not gs:
                continue
            locs = [n.location for n in o.nodes if n.location.valid()]
            la = [l.lat for l in locs]
            lo = [l.lon for l in locs]
            el = {"type": "way", "id": o.id,
                  "center": {"lat": round((min(la) + max(la)) / 2, 7),
                             "lon": round((min(lo) + max(lo)) / 2, 7)},
                  "tags": tags}
        else:
            continue
        for g in gs:
            hits[g].append(el)
    if boundary is None:
        sys.exit(f"no boundary relation ISO3166-2={code} in {pbf}")
    inside = prep(boundary)
    out.mkdir(parents=True, exist_ok=True)
    total = 0
    for g, els in hits.items():
        keep = []
        for el in els:
            c = el.get("center") or el
            if inside.contains(Point(c["lon"], c["lat"])):
                keep.append(el)
        (out / f"{g}.json").write_text(json.dumps(
            {"version": 0.6, "generator": f"osm_extract.py from {Path(pbf).name}",
             "osm3s": {"timestamp_osm_base": ts or ""}, "elements": keep},
            ensure_ascii=False))
        total += len(keep)
        print(f"  {province}/{g}: {len(keep)}")
    (out / "EXTRACT").write_text(f"{Path(pbf).name}\t{ts or ''}\tISO3166-2={code}\n")
    print(f"{province}: {total} elements over {len(hits)} groups, extract {ts}")


if __name__ == "__main__":
    main()
