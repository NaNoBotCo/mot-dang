#!/usr/bin/env python3
"""make_field_seen.py — when NaN's camera last saw each place.

Reads, all read-only:
  _incoming/gopro-*/pass2*/out/seen.json   records a ride read by sign (views like GSAA1911_086_F)
  _incoming/gopro-*/frames.csv             burst,item,local_time,… — turns a view into a time
  data/curated/own_pictures.json           her pictures bound to a record (placeId / places)
  data/curated/own_pictures_meta.json      exact capture times, when make_picture_meta.py has run
  data/curated/additions-*.json, enrich.json   sources of type "field" that name a GoPro ride

Writes data/curated/field_seen.json:
  {"generated": ..., "seen": {record id: {"last": ISO time or date, "first": ..., "n": sightings,
                                         "sign": text read off its sign, or "",
                                         "pic": slug of her newest picture of it, or ""}}}

The record is kept however old it gets, and across passes (a record is never dropped);
pics_layer.seen_row decides what is fresh enough to print.
Rerun after each ride. Deterministic: same inputs, same file.
"""

import csv
import glob
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INC = ROOT / "_incoming"
CUR = ROOT / "data" / "curated"
OUT = CUR / "field_seen.json"

VIEW = re.compile(r"(GS[A-Z]{2}\d{4})_(\d{1,4})")
DATE = re.compile(r"(20\d\d-\d\d-\d\d)")


def frame_times():
    """(burst, item) -> local ISO time, from every ride's frames.csv."""
    t = {}
    for f in sorted(INC.glob("gopro-*/frames.csv")):
        try:
            rows = list(csv.reader(f.open(encoding="utf-8")))
        except OSError:
            continue
        if not rows:
            continue
        head = rows[0]
        if "burst" in head and "local_time" in head:
            b, i, lt = head.index("burst"), head.index("item"), head.index("local_time")
            for r in rows[1:]:
                if len(r) > lt and r[lt]:
                    t[(r[b], int(r[i]))] = r[lt]
        else:
            # 27 Sep shape: GSAA7017_001,2026:09:27 10:01:12,...
            for r in rows:
                m = VIEW.match(r[0] if r else "")
                if m and len(r) > 1 and re.match(r"\d{4}:\d\d:\d\d \d\d:\d\d:\d\d", r[1]):
                    d, h = r[1].split(" ")
                    t[(m.group(1), int(m.group(2)))] = d.replace(":", "-") + "T" + h + "+07:00"
    return t


def main():
    times = frame_times()
    seen = {}

    def add(rid, when, sign="", pic=""):
        if not rid or not when:
            return
        s = seen.setdefault(rid, {"last": "", "first": "", "n": 0, "sign": "", "pic": "", "_pd": ""})
        s["n"] += 1
        if when > s["last"]:
            s["last"] = when
        if not s["first"] or when < s["first"]:
            s["first"] = when
        if sign and len(sign) > len(s["sign"]) and len(sign) <= 60:
            s["sign"] = sign
        if pic and when >= s["_pd"]:
            s["pic"], s["_pd"] = pic, when

    # 1. what the ride readers matched to a record by its sign
    for f in sorted(glob.glob(str(INC / "gopro-*/pass2*/out/seen.json"))):
        if "backup" in f:
            continue
        try:
            d = json.loads(Path(f).read_text())
        except (OSError, ValueError):
            continue
        for rid, v in d.items():
            texts = [x for x in (v.get("texts") or []) if x and len(x.strip()) > 2]
            sign = max(texts, key=lambda x: sum(c.isalpha() for c in x)) if texts else ""
            whens = []
            for view in v.get("views") or []:
                m = VIEW.match(view)
                if m and (m.group(1), int(m.group(2))) in times:
                    whens.append(times[(m.group(1), int(m.group(2)))])
            if whens:
                add(rid, max(whens), sign.strip())

    # 2. her pictures bound to a record
    meta = {}
    mp = CUR / "own_pictures_meta.json"
    if mp.exists():
        try:
            meta = json.loads(mp.read_text())
            meta = meta.get("pictures", meta)
        except ValueError:
            meta = {}
    for p in json.loads((CUR / "own_pictures.json").read_text())["picks"]:
        when = ((meta.get(p["slug"]) or {}).get("taken") or p.get("date") or "")
        for rid in {p.get("placeId"), *(p.get("places") or [])} - {None, ""}:
            add(rid, when, (p.get("signText") or "").strip(), p["slug"])

    # 3. records a ride created or confirmed, from their own field source
    for f in sorted(CUR.glob("additions-*.json")) + [CUR / "enrich.json"]:
        try:
            d = json.loads(f.read_text())
        except (OSError, ValueError):
            continue
        recs = d if isinstance(d, list) else [
            dict(v, id=k) for k, v in (d.items() if isinstance(d, dict) else [])
            if isinstance(v, dict)]
        for r in recs:
            for s in r.get("sources") or []:
                if not isinstance(s, dict) or s.get("type") != "field":
                    continue
                txt = (s.get("ref") or "") + " " + (s.get("via") or "")
                if "GoPro" not in txt:
                    continue
                whens = []
                for m in VIEW.finditer(txt):
                    k = (m.group(1), int(m.group(2)))
                    if k in times:
                        whens.append(times[k])
                if not whens:
                    whens = DATE.findall(s.get("ref") or "")
                if whens:
                    add(r.get("id"), max(whens))

    for s in seen.values():
        s.pop("_pd", None)
    # Keep what an earlier pass recorded. Some ride folders are links onto the
    # Passport drive, which is often unplugged; a pass without it must not
    # forget the places it saw.
    if OUT.exists():
        try:
            old = json.loads(OUT.read_text()).get("seen") or {}
        except ValueError:
            old = {}
        for rid, o in old.items():
            s = seen.get(rid)
            if not s:
                seen[rid] = o
                continue
            if o.get("last", "") > s["last"]:
                s["last"], s["pic"] = o["last"], o.get("pic") or s["pic"]
            if o.get("first") and o["first"] < s["first"]:
                s["first"] = o["first"]
            s["n"] = max(s["n"], o.get("n", 0))
            if len(o.get("sign") or "") > len(s["sign"]):
                s["sign"] = o["sign"]
    out = {"generated": max([s["last"] for s in seen.values()] or [""])[:10],
           "seen": dict(sorted(seen.items()))}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=0, sort_keys=False) + "\n")
    timed = sum(1 for s in seen.values() if "T" in s["last"])
    print(f"field_seen: {len(seen)} records, {timed} with a time of day, "
          f"{sum(1 for s in seen.values() if s['sign'])} with a sign read")
    return 0


if __name__ == "__main__":
    sys.exit(main())
