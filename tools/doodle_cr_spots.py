#!/usr/bin/env python3
"""The spots on the Chiang Rai doodle map (docs/sites/doodle-chiang-rai/).

Nan, 2026-10-03: "Can you make one of these for Chiang Rai?" with the cave, the friendship
bridges, the clock tower, the hill villages, the Golden Triangle, Kings Romans across the
Mekong, both opium museums, the Black House, the Blue and White temples, the Mangrai
monument, the walking street, the bus station, the airport and the indoor market.

Her landmarks come from data/curated/doodle_cr_points.json (each pinned, each with its
source); a short ranked pick of wats, markets and sights comes from the canonical record.
As in Chiang Mai: a spot needs its name in both languages, chains stay off, and quality
comes before quantity.

    python3 tools/doodle_cr_spots.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import build  # noqa: E402

OUT = ROOT / "docs" / "sites" / "doodle-chiang-rai" / "data" / "spots.json"
POINTS = ROOT / "data" / "curated" / "doodle_cr_points.json"
REGION = (19.70, 20.48, 99.58, 100.46)
KIND = {"tham-luang": "green", "friendship-1": "go", "friendship-2": "go", "friendship-lao": "go", "clock-tower": "see",
        "golden-triangle": "see", "golden-buddha": "wat", "kings-romans": "see", "hall-of-opium": "see",
        "house-of-opium": "see", "black-house": "art", "blue-temple": "wat", "white-temple": "wat",
        "mangrai-monument": "see", "walking-street": "market", "walking-street-sun": "market", "bus-1": "go",
        "bus-2": "go", "indoor-market": "market", "night-bazaar": "market", "mae-sai-market": "market",
        "guanyin": "wat", "doi-chom-thong": "wat", "phra-kaew": "wat", "doi-tung": "green", "chiang-saen": "see",
        "singha-park": "green"}
MORE = {"tham-luang": {"u": "https://nanobotco.github.io/tham-luang/", "th": "ถ้ำหลวง วาดเล่า ↗", "en": "Tham Luang, Drawn ↗"},
        "golden-triangle": {"u": "https://nanobotco.github.io/golden-triangle/", "th": "สามเหลี่ยมทองคำ มินิไซต์ ↗", "en": "The Golden Triangle minisite ↗"}}
PEOPLE = [("akha", r"akha|อาข่า"), ("lahu", r"lahu|มูเซอ|ลาหู่"), ("karen", r"karen|กะเหรี่ยง"), ("yao", r"yao|mien|เมี่ยน|เย้า"),
          ("lisu", r"lisu|ลีซู"), ("hmong", r"hmong|ม้ง"), ("yunnan", r"yunnan|kmt|chinese|จีน|ยูนนาน")]
CHAINS = re.compile(r"7-eleven|lotus|big c|makro|central|kfc|mcdonald|starbucks|amazon|black canyon|tesco|mk\b|swensen", re.I)


def main():
    cr = json.loads((ROOT / "data" / "canonical" / "cr.json").read_text())
    byid = {r["id"]: r for r in cr}
    clash = build._slug_clash()
    imgs = json.loads((ROOT / "data" / "commons_images.json").read_text())["images"]
    url = lambda r: f"/{r['province']}/p/{clash.get(r['id']) or build._slug_stem(r)}.html"
    pts = json.loads(POINTS.read_text())
    out, seen = [], set()

    def add(s):
        k = s["en"].lower()
        if k in seen or not s["th"] or not s["en"]:
            return
        seen.add(k); out.append(s)

    for p in pts.get("landmarks", []):
        key = p["key"]
        if key == "airport" or key not in KIND:
            continue                                  # the airport is drawn by the page's own config
        s = {"id": p.get("record") or "cr-" + key, "k": KIND[key], "look": key, "w": "sheet", "en": p["en"], "th": p["th"],
             "lat": round(p["lat"], 5), "lng": round(p["lng"], 5), "ne": p.get("note_en", ""), "nt": p.get("note_th", ""), "src": p.get("src", "")}
        r = byid.get(p.get("record") or "")
        if r:
            s["u"] = url(r)
            im = imgs.get(r["id"])
            if im:
                s.update(img=im["thumb"], imc=f"{im.get('artist', '')} · {im.get('licence', '')}", imu=im["full"])
        if key in MORE:
            s["more"] = MORE[key]
        add(s)
    for p in pts.get("villages", []):
        people = (p.get("people_en") or "") + " " + (p.get("people_th") or "") + " " + p["en"]
        look = next((f"village-{k}" for k, rx in PEOPLE if re.search(rx, people, re.I)), "village-lahu")
        ne = " · ".join(x for x in [p.get("people_en"), p.get("note_en")] if x)
        nt = " · ".join(x for x in [p.get("people_th"), p.get("note_th")] if x)
        s = {"id": p.get("record") or "village-" + re.sub(r"\W+", "-", p["en"].lower()), "k": "village", "look": look, "w": "sheet",
             "en": p["en"], "th": p["th"], "lat": round(p["lat"], 5), "lng": round(p["lng"], 5), "ne": ne, "nt": nt, "src": p.get("src", "")}
        r = byid.get(p.get("record") or "")
        if r:
            s["u"] = url(r)
        add(s)

    # a short pick from the record: old wats and markets with a picture, in or near the towns
    picks = {"wat": [], "market": [], "see": []}
    for r in cr:
        la, ln = r.get("lat"), r.get("lng")
        if la is None or not (REGION[0] < la < REGION[1] and REGION[2] < ln < REGION[3]):
            continue
        if not (r.get("nameEn") and r.get("nameTh")) or CHAINS.search(r.get("nameEn") or "") or (r.get("attrs") or {}).get("brand"):
            continue
        cats, a = set(r["cat"]), r.get("attrs") or {}
        k = "wat" if "wat" in cats else "market" if "market" in cats else "see" if cats & {"sights", "museums-galleries"} else None
        if not k or not (r["id"] in imgs or a.get("foundedCE") or r.get("landmark")):
            continue
        score = (30 if r["id"] in imgs else 0) + (20 if r.get("landmark") else 0) + (max(0, 30 - (a["foundedCE"] - 1250) // 20) if a.get("foundedCE") else 0)
        ne, nt = (f"founded {a['foundedCE']}", f"สร้าง พ.ศ. {a.get('foundedBE') or a['foundedCE'] + 543}") if a.get("foundedCE") else ("", "")
        s = {"id": r["id"], "k": k, "w": "sheet", "en": re.sub(r"\s*\(.*?\)\s*$", "", r["nameEn"]), "th": r["nameTh"],
             "lat": round(la, 5), "lng": round(ln, 5), "ne": ne, "nt": nt, "u": url(r)}
        im = imgs.get(r["id"])
        if im:
            s.update(img=im["thumb"], imc=f"{im.get('artist', '')} · {im.get('licence', '')}", imu=im["full"])
        picks[k].append((score, s))
    for k, cap in (("wat", 14), ("market", 4), ("see", 8)):
        for _, s in sorted(picks[k], key=lambda t: -t[0])[:cap]:
            add(s)

    counts = {}
    for s in out:
        counts[s["k"]] = counts.get(s["k"], 0) + 1
    print(len(out), counts, "looks:", sum(1 for s in out if s.get("look")))
    OUT.write_text(json.dumps({"source": "data/curated/doodle_cr_points.json (each row's src); Mot Dang canonical record (data/canonical/cr.json); photos Wikimedia Commons",
                               "spots": out}, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
