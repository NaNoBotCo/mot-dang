#!/usr/bin/env python3
"""The spots on the Pathum Thani and Phnom Penh doodle maps.

Nan, 2026-10-13: "Can you make it a doodle map and calendar?" of Pathum Thani, then "I want PT
to have its own homepage", "Maybe just show me the PT view for when I'm there", and "Do the same
thing for Phnom Penh". The ground of both maps is their tile archive (tiles/pth.pmtiles,
tiles/pp.pmtiles), drawn in the browser as the North's is; this writes only the spots.

Pathum Thani: a hand-picked list of Mot Dang records (data/canonical/pth.json), each by id.
Phnom Penh: the twenty landmarks of Psar Phnom Penh (../phnom-penh/data/landmarks.json), words
and photographs as that site carries them.

    python3 tools/doodle_city_spots.py              both
    python3 tools/doodle_city_spots.py pth          one
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
PP = ROOT.parent / "phnom-penh"
PP_SITE = "https://nanobotco.github.io/phnom-penh/"

# record id → (kind, English name where the record's own is missing or wrong, Thai where it is wrong)
PTH = {
    "pth-osm-way-378350905": ("wat", "Wat Chinwararam", None),
    "pth-osm-node-4571891590": ("wat", None, None),
    "pth-osm-way-219056070": ("wat", None, None),
    "pth-osm-way-221187143": ("wat", "Wat Bot, Sam Khok", None),
    "pth-osm-way-221195258": ("wat", None, None),
    "pth-osm-way-225697159": ("wat", "Wat Sing", None),
    "pth-osm-way-41291954": ("wat", None, None),
    "pth-osm-node-14112408468": ("wat", None, None),
    "pth-osm-node-3658633281": ("wat", "Wat Rangsit", None),
    "pth-osm-way-219965365": ("wat", None, None),
    "pth-osm-way-255439479": ("wat", "Wat Khian Khet", None),
    "pth-osm-way-219584100": ("wat", None, None),
    "pth-osm-way-219056069": ("wat", None, None),
    "pth-osm-way-1528487490": ("wat", None, None),
    "pth-osm-node-891271924": ("spirit", "Pathum Thani City Pillar Shrine", None),
    "pth-osm-way-1394942608": ("spirit", "Rangsit City Pillar Shrine", None),
    "pth-osm-way-455981220": ("market", None, None),
    "pth-osm-node-2373599662": ("market", None, None),
    "pth-osm-way-1467500069": ("market", None, None),
    "pth-osm-way-1215821149": ("market", None, None),
    "pth-osm-way-371442592": ("market", None, None),
    "pth-osm-way-1203025125": ("market", None, None),
    "pth-osm-way-253429082": ("see", None, None),
    "pth-osm-way-141654246": ("see", None, None),
    "pth-osm-way-1418913270": ("see", "Ong Ang Kiln ruins", None),
    "pth-osm-way-217893777": ("see", None, None),
    "pth-osm-relation-19851397": ("see", "Futurium", None),
    "pth-osm-node-891273702": ("see", "Old Provincial Hall", None),
    "pth-osm-way-702369013": ("see", None, None),
    "pth-osm-way-547541949": ("see", None, None),
    "pth-osm-node-4650839709": ("see", "Dream World", "ดรีมเวิลด์"),
    "pth-osm-way-910037483": ("see", "Rangsit Planetarium", None),
    "pth-osm-way-37761202": ("green", None, None),
    "pth-osm-way-1441990308": ("green", "Bueng Kham Phroi Park", None),
    "pth-osm-way-1383747525": ("green", "Tha Khlong Park", None),
    "pth-osm-way-1154795667": ("green", "Thotsamin Thraphirom Park", None),
    "pth-osm-way-544325883": ("green", "Pathum Thani Health Park", None),
}
PP_KIND = {"sights": "see", "wat": "wat", "mart": "market", "food": "eat", "stay": "see"}


def pth():
    import build
    recs = {r["id"]: r for r in json.loads((ROOT / "data" / "canonical" / "pth.json").read_text())}
    clash = build._slug_clash()
    out = []
    for rid, (k, en, th) in PTH.items():
        r = recs.get(rid)
        if not r:
            print("  not in the record:", rid)
            continue
        th = th or r.get("nameTh") or r.get("name")
        en = en or r.get("nameEn") or build.name_roman(r)
        out.append({"id": rid, "k": k, "w": "sheet", "en": en, "th": th, "lat": round(r["lat"], 5), "lng": round(r["lng"], 5),
                    "ne": "", "nt": "", "u": f"/pth/p/{clash.get(rid) or build._slug_stem(r)}.html"})
    return {"source": "Mot Dang canonical record (data/canonical/pth.json), picked by hand", "spots": out}


def pp():
    picks = json.loads((PP / "data" / "photos" / "picks.json").read_text())
    cred = json.loads((PP / "data" / "photos" / "credits.json").read_text())
    out = []
    for L in json.loads((PP / "data" / "landmarks.json").read_text()):
        s = {"id": "pp-" + L["id"], "k": PP_KIND.get(L["shelf"], "see"), "w": "sheet", "en": L["en"], "th": L["th"],
             "lat": round(L["lat"], 5), "lng": round(L["lng"], 5), "ne": L.get("t_en", ""), "nt": L.get("t_th", ""),
             "more": {"u": PP_SITE, "th": "ตลาดพนมเปญ ↗", "en": "Psar Phnom Penh ↗"}}
        img = PP / "docs" / "img" / (L["id"] + ".jpg")
        c = cred.get(L["id"]) or cred.get((picks.get(L["id"]) or [""])[0])
        if img.exists() and c:
            s.update(img=PP_SITE + "img/" + img.name, imc=f"{c.get('author', '')} · {c.get('licence', '')}", imu=c.get("page", ""))
        out.append(s)
    return {"source": "Psar Phnom Penh landmarks (nanobotco.github.io/phnom-penh); photos Wikimedia Commons", "spots": out}


def main():
    want = sys.argv[1:] or ["pth", "pp"]
    for key, slug, fn in (("pth", "doodle-pathum-thani", pth), ("pp", "doodle-phnom-penh", pp)):
        if key not in want:
            continue
        d = fn()
        f = ROOT / "assets" / "sites" / slug / "data" / "spots.json"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")))
        print(key, len(d["spots"]), "spots →", f.relative_to(ROOT))


if __name__ == "__main__":
    main()
