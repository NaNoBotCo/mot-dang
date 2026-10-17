#!/usr/bin/env python3
"""Data files for the Retrace minisite (assets/sites/retrace/data/).

    python3 tools/retrace_data.py [street_photos.json]

street_photos.json is the Mapillary harvest's index, which lives on motdang-server
(/srv/mot-dang/data/street_photos.json); the default is cache/street_photos.json.

Writes, for the old city of Chiang Mai and the ring around it:
  places.json  [[id, kind, lat, lng, th, en, cat], ...]   wats, shrines, spirit houses, gates, corners,
               hotels, cafes and every other published place with a point; kind is a short code
  photos.json  [[placeId, camLat, camLng, heading, file, by, captured, pano, imageId], ...]
               the camera's position is worked back from the place, the distance and the heading
  roads.json   road_graph.json cut to the box, node indexes remapped (same delta coding)
  water.json   the moat and ponds inside the box, from city-live's land.json (same delta coding)
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "sites" / "retrace" / "data"
BOX = (18.7760, 18.8000, 98.9780, 99.0040)     # S, N, W, E
SPIRIT = {"spirit-house", "shrine", "big-tree"}
HOTEL = {"hotel-full", "guesthouse", "hostel", "apartment", "boutique", "resort"}


def inside(la, lo, b=BOX):
    return la is not None and lo is not None and b[0] <= la <= b[1] and b[2] <= lo <= b[3]


def subs(r):
    s = r.get("sub") or []
    return s if isinstance(s, list) else [s]


def kind(r):
    s = set(subs(r))
    cats = set(r.get("cat") or [])
    if "gate" in s:
        return "g"
    if "corner" in s:
        return "b"
    if s & SPIRIT or any(k in r["id"] for k in SPIRIT):
        return "s"
    if "wat" in cats:
        return "w"
    if "cafe" in s:
        return "c"
    if "hotel" in cats or s & HOTEL:
        return "h"
    return "o"


def places():
    d = json.loads((ROOT / "data" / "canonical" / "cm.json").read_text(encoding="utf-8"))
    out = []
    for r in d:
        if not inside(r.get("lat"), r.get("lng")):
            continue
        th = (r.get("nameTh") or r.get("name") or "").strip()
        en = (r.get("nameEn") or "").strip()
        if not (th or en):
            continue
        if " · ห่างประตูท่าแพ" in th or th.startswith("ที่จอดมอเตอร์ไซค์ ·"):
            continue                                    # a parking pin named by its distance
        k = kind(r)
        cat = (r.get("sub") or [""])[0] if k == "o" else ""
        if k == "o" and not cat:
            cat = (r.get("cat") or [""])[0]
        out.append([r["id"], k, round(r["lat"], 5), round(r["lng"], 5), th[:60], en[:60], cat])
    return out


def photos(index, keep):
    p = json.loads(Path(index).read_text(encoding="utf-8"))["photos"]
    rows = []
    for pid, v in p.items():
        if pid not in keep:
            continue
        la, lo = keep[pid]
        h = v.get("bearing")
        dm = v.get("distanceM") or 0
        if h is None:
            continue
        kx = math.cos(math.radians(la)) * 111320
        cla = la - dm * math.cos(math.radians(h)) / 110574
        clo = lo - dm * math.sin(math.radians(h)) / kx
        rows.append([pid, round(cla, 5), round(clo, 5), round(h), v["file"], v.get("by", ""),
                     v.get("captured", ""), 1 if v.get("pano") else 0, str(v.get("imageId", ""))])
    return rows


def roads():
    g = json.loads((ROOT / "data" / "road_graph.json").read_text())
    S = g["scale"]
    nodes = g["nodes"]
    ex = 0.0006
    b = (BOX[0] - ex, BOX[1] + ex, BOX[2] - ex, BOX[3] + ex)
    ok = [inside(n[0] / S, n[1] / S, b) for n in nodes]
    keepE = [e for e in g["edges"] if ok[e[0]] and ok[e[1]]]
    used = sorted({e[0] for e in keepE} | {e[1] for e in keepE})
    remap = {n: i for i, n in enumerate(used)}
    return {"scale": S, "nodes": [nodes[n] for n in used],
            "edges": [[remap[e[0]], remap[e[1]], e[2], e[3], e[4]] for e in keepE]}


def water():
    land = json.loads((ROOT / "assets" / "sites" / "city-live" / "data" / "land.json").read_text())
    S = land["scale"]
    rings = []
    for f in land["feats"]["water"]:
        for ring in f:
            la = lo = 0
            pts = []
            for i in range(0, len(ring), 2):
                la, lo = (ring[0], ring[1]) if i == 0 else (la + ring[i], lo + ring[i + 1])
                pts.append((la / S, lo / S))
            if any(inside(a, o) for a, o in pts):
                rings.append(ring)
    return {"scale": S, "rings": rings}


def main():
    idx = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "cache" / "street_photos.json")
    OUT.mkdir(parents=True, exist_ok=True)
    pl = places()
    keep = {r[0]: (r[2], r[3]) for r in pl}
    ph = photos(idx, keep)
    data = {"places": pl, "photos": ph, "roads": roads(), "water": water()}
    for k, v in data.items():
        (OUT / (k + ".json")).write_text(json.dumps(v, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(k, (OUT / (k + ".json")).stat().st_size)
    from collections import Counter
    print(Counter(r[1] for r in pl), len(ph))


if __name__ == "__main__":
    main()
