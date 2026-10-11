#!/usr/bin/env python3
"""The culture layer of the doodle map: festivals and rites drawn where they happen.

Nan, 2026-10-03: "add some cultural context to the illustration. Not so generic."
Every word on a scene comes from data/festivals.json or data/shrines.json, the same text
the festival pages carry; the dates come from data/festival_dates.json rows that an
official source announced. The table below holds only where to draw each scene and
which drawing it gets.

    python3 tools/doodle_map_culture.py      writes docs/sites/doodle-map/data/culture.json
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CITY = "cr" if "--cr" in __import__("sys").argv else "cm"
OUT = ROOT / "docs" / "sites" / ("doodle-chiang-rai" if CITY == "cr" else "doodle-map") / "data" / "culture.json"

# id, drawing, points [lat, lng] (two or more = a route), festival id, shrine key
SCENES = [
    ("inthakhin", "pillar-tree", [[18.78735, 98.98610]], "inthakhin", "inthakhin"),
    ("mangrai", "shrine", None, None, "ho-phaya-mangrai"),
    ("katam", "shrine", None, None, "chaeng-katam"),
    ("yipeng", "lanterns", [[18.7880, 99.0028]], "yi-peng-loi-krathong", None),
    ("songkran", "splash", [[18.7915, 98.9936]], "songkran-pi-mai-muang", None),
    ("flowers", "parade", [[18.78764, 99.00060], [18.7905, 98.9935], [18.7855, 98.9830], [18.78229, 98.97927]], "cm-flower-festival", None),
    ("walk", "pilgrims", [[18.81283, 98.94613], [18.8125, 98.9390], [18.8080, 98.9330], [18.8100, 98.9270], [18.80492, 98.9221]], "visakha-doi-suthep-walk", None),
    ("cny", "lion", [[18.7916, 99.0018]], "chinese-new-year", None),
    ("design", "design", [[18.7912, 98.9860]], "cm-design-week", None),
    ("nye", "fireworks", [[18.7888, 98.9952]], "nye-countdown", None),
    ("pusae", "offering", None, "pu-sae-ya-sae", "pu-sae-ya-sae"),
]


# Chiang Rai (python3 tools/doodle_map_culture.py --cr); None points = the shrine record's own pin
SCENES_CR = [
    ("sadue", "shrine", None, None, "sadue-mueang-cr"),
    ("maesai-pillar", "shrine", None, None, "lak-mueang-mae-sai"),
    ("saen-phu", "shrine", None, None, "phaya-saen-phu"),
    ("tham-pla", "shrine", None, None, "tham-pla"),
    ("balloons", "balloons", [[19.8600, 99.7330]], "singha-balloon-fiesta", None),
    ("doi-tung-flowers", "flowerbeds", [[20.2848, 99.8140]], "doi-tung-flower-season", None),
    ("cny-salong", "lion", [[20.1600, 99.6300]], "chinese-new-year", None),
    ("nye-cr", "fireworks", [[19.9085, 99.8325]], "nye-countdown", None),
    ("akha-swing", "swing", [[20.3590, 99.8350]], "akha-swing-festival", None),
    ("mist", "mist", [[19.8501, 100.4541]], "phu-chi-fa-sea-of-mist", None),
]


def main():
    fest = {f["id"]: f for f in json.loads((ROOT / "data" / "festivals.json").read_text())["festivals"]}
    shr = {s["key"]: s for s in json.loads((ROOT / "data" / "shrines.json").read_text())["shrines"]}
    rows = json.loads((ROOT / "data" / "festival_dates.json").read_text())["rows"]
    canon = {r["id"]: r for r in json.loads((ROOT / "data" / "canonical" / (CITY + ".json")).read_text())}
    out = []
    for sid, draw, pts, fid, skey in (SCENES_CR if CITY == "cr" else SCENES):
        f, s = fest.get(fid) if fid else None, shr.get(skey) if skey else None
        if pts is None:
            rec = canon.get((s or {}).get("recordId"))
            if not rec or rec.get("lat") is None:
                print("no pin for", sid); continue
            pts = [[round(rec["lat"], 5), round(rec["lng"], 5)]]
        sc = {"id": sid, "draw": draw, "pts": pts}
        if f:
            sc.update(th=f["name_th"], en=f["name_en"], bth=f["blurb_th"], ben=f["blurb_en"],
                      wth=f.get("window_th") or "", wen=f.get("window_en") or "",
                      months=f.get("months") or [f.get("month")], u=f"/festivals/{fid}.html")
            ann = sorted((r for r in rows if r.get("festival_id") == fid and r.get("status") == "announced"),
                         key=lambda r: r.get("date_start") or "")
            if ann:
                a = ann[-1]
                sc["when"] = {"from": a.get("date_start"), "to": a.get("date_end"), "src": a.get("source_url"),
                              "by_th": a.get("source_name_th"), "by_en": a.get("source_name_en")}
        if s:
            sc.setdefault("th", s["nameTh"]); sc.setdefault("en", s["nameEn"])
            sc["sth"], sc["sen"] = s.get("note_th") or "", s.get("note_en") or ""
        out.append(sc)
    OUT.write_text(json.dumps({"source": "data/festivals.json, data/shrines.json, data/festival_dates.json",
                               "scenes": out}, ensure_ascii=False, separators=(",", ":")))
    print(len(out), "scenes →", OUT)


if __name__ == "__main__":
    main()
