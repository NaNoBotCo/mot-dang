#!/usr/bin/env python3
"""Bake /parking/'s data: every parking place in the catalogue, with answers.

    python3 tools/parking_bake.py            # writes assets/parking/t/<tile>.json + model.json

Reads data/canonical/{cm,cr,pth}.json and data/parking.json. Each place gets
the answers the page shows — vehicle, covered, hours, fee, off-street, no
sign, capacity, attendant, who may use it — and for each answer the kind of
knowledge it rests on:

  m  mapped    a tag on the record (OpenStreetMap, a directory)
  s  seen      bikes seen parked there on one of Nan's rides
  u  usual     the habit of the kind of place it belongs to (data/parking.json)

Readers' reports (full, space, fined, …) come from the worker at page time
and outrank all three.

Two sources of places:
  1. records with sub "parking" (car parks, motorbike parking), bicycle-only dropped;
  2. venues whose kind usually has parking (malls, superstores, hospitals,
     markets, temples, airports, stations, 7-Elevens), matched with the same
     tiers toilets_layer uses. A venue with a mapped lot within 80 m gives that
     lot its name and its habits instead of appearing twice.
"""
import json
import math
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT = ROOT / "assets" / "parking"
MODEL = json.loads((ROOT / "data" / "parking.json").read_text())
PROVS = ("cm", "cr", "pth")

import toilets_layer  # noqa: E402  (tier rules shared with /toilets.html)

TIER_KEY = [t["key"] for t in toilets_layer.TIERS]
CLASSES = MODEL["classes"]


def metres(a, b, c, d):
    k = math.cos(math.radians((a + c) / 2))
    return math.hypot((c - a) * 111_320, (d - b) * 111_320 * k)


def names(r):
    return [str(r.get(k) or "").strip().lower() for k in ("name", "nameTh", "nameEn") if r.get(k)]


def class_of(r):
    """The parking class a venue belongs to, or None."""
    subs = set(r.get("sub") or [])
    ti = toilets_layer.tier_index(r)
    tier = TIER_KEY[ti] if ti is not None else None
    for c in CLASSES:
        if c.get("toilet_tier"):
            if tier != c["toilet_tier"]:
                continue
            if c.get("not_name") and any(w.lower() in n for n in names(r) for w in c["not_name"]):
                continue
            return c["key"]
        if c.get("sub") and not subs & set(c["sub"]):
            continue
        if c.get("not_sub") and subs & set(c["not_sub"]):
            continue
        if c.get("sub_any") and not subs & set(c["sub_any"]):
            continue
        if c.get("cat_any") and not set(r.get("cat") or []) & set(c["cat_any"]):
            continue
        if c.get("name_prefix") and not any(toilets_layer._starts(n, w.lower())
                                            for n in names(r) for w in c["name_prefix"]):
            continue
        if c.get("name_any") and not any(w.lower() in n for n in names(r) for w in c["name_any"]):
            continue
        if c.get("not_name") and any(w.lower() in n for n in names(r) for w in c["not_name"]):
            continue
        return c["key"]
    return None


_H24 = re.compile(r"^\s*24/7\s*$")
_BAHT = re.compile(r"(\d+)\s*(?:thb|baht|บาท|฿)", re.I)


def lot_answers(r):
    """Answers from the record's own tags. Returns (answers, basis)."""
    a = r.get("attrs") or {}
    subs = set(r.get("sub") or [])
    ans, why = {}, {}

    def put(k, v, b):
        if v is None or v == "":
            return
        ans[k], why[k] = v, b

    seen = bool(a.get("bikesSeen"))
    if "motorcycle-parking" in subs or seen:
        put("veh", "m", "s" if seen else "m")
    elif str(a.get("motorcycle") or "").lower() in ("yes", "designated"):
        put("veh", "cm", "m")
    else:
        put("veh", "c", "m")

    pt = str(a.get("parkingType") or "").lower()
    cov = str(a.get("covered") or "").lower()
    if cov in ("yes", "no"):
        put("cov", "yes" if cov == "yes" else "no", "m")
    elif pt in ("multi-storey", "underground", "sheds", "carports") or "parking-entrance" in subs:
        put("cov", "yes", "m")

    if pt in ("street_side", "lane", "on_kerb", "half_on_kerb", "layby") or a.get("setting") == "kerb":
        put("off", False, "s" if a.get("setting") == "kerb" else "m")
    elif pt in ("surface", "multi-storey", "underground", "rooftop", "sheds", "carports") \
            or "parking-entrance" in subs:
        put("off", True, "m")

    h = (r.get("hours") or a.get("openingHours") or "").strip()
    if h:
        put("h24", bool(_H24.match(h)), "m")
        if not _H24.match(h):
            put("hours", h[:60], "m")

    fee = str(a.get("fee") or "").lower()
    charge = str(a.get("charge") or "")
    if fee in ("no", "free"):
        put("fee", "free", "m")
    elif fee in ("yes", "paid") or charge:
        m = _BAHT.search(charge)
        put("fee", ("฿" + m.group(1)) if m else "paid", "m")

    acc = str(a.get("access") or "").lower()
    if acc in ("private", "no"):
        put("acc", "private", "m")
    elif acc in ("customers", "destination", "permit"):
        put("acc", "customers", "m")

    if str(a.get("supervised") or "").lower() == "yes":
        put("att", True, "m")
    try:
        if a.get("capacity"):
            put("cap", int(str(a["capacity"]).split(";")[0]), "m")
    except ValueError:
        pass
    if seen:
        put("gue", True, "s")
        put("bikes", int(a.get("bikesSeen") or 0), "s")
        put("seen", a.get("seen"), "s")
        if a.get("besideSeen"):
            put("beside", a["besideSeen"][:80], "s")
    if a.get("operator"):
        put("op", str(a["operator"])[:60], "m")
    return ans, why


def short_name(r, lang):
    n = r.get("nameEn" if lang == "en" else "nameTh") or r.get("name") or ""
    return n.strip()


def bake(prov):
    recs = json.loads((ROOT / "data" / "canonical" / f"{prov}.json").read_text())
    lots, venues = [], []
    for r in recs:
        if r.get("lat") is None:
            continue
        subs = set(r.get("sub") or [])
        if "parking" in subs:
            if subs & {"bicycle-parking"} and not subs & {"motorcycle-parking"}:
                continue
            lots.append(r)
            continue
        c = class_of(r)
        if c:
            venues.append((c, r))

    # A mapped lot near a venue takes the venue's name and habits.
    grid = {}
    for i, r in enumerate(lots):
        grid.setdefault((round(r["lat"], 3), round(r["lng"], 3)), []).append(i)

    def near_lots(la, ln, within):
        out = []
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                for i in grid.get((round(la + dy * .001, 3), round(ln + dx * .001, 3)), []):
                    d = metres(la, ln, lots[i]["lat"], lots[i]["lng"])
                    if d <= within:
                        out.append((d, i))
        return sorted(out)

    # One row per venue: a mall's shops and a hospital's Thai and English
    # records sit at one door. Same class within SAME_M is the same place;
    # the shortest name stands for it.
    SAME_M = {"seven": 30, "wat": 60, "market": 120}
    venues.sort(key=lambda cv: len(short_name(cv[1], "en") or short_name(cv[1], "th")))
    kept = []
    for c, v in venues:
        lim = SAME_M.get(c, 250)
        if any(k[0] == c and metres(v["lat"], v["lng"], k[1]["lat"], k[1]["lng"]) <= lim for k in kept):
            continue
        kept.append((c, v))

    lot_at = {}
    rows = []
    for c, v in kept:
        hit = near_lots(v["lat"], v["lng"], 80) if c != "seven" else []
        if hit:
            for _, i in hit:
                if i not in lot_at:
                    lot_at[i] = (c, v)
            continue
        rows.append({"id": v["id"], "th": short_name(v, "th"), "en": short_name(v, "en"),
                     "la": round(v["lat"], 6), "ln": round(v["lng"], 6), "c": c, "k": "v"})

    for i, r in enumerate(lots):
        ans, why = lot_answers(r)
        row = {"id": r["id"], "th": short_name(r, "th"), "en": short_name(r, "en"),
               "la": round(r["lat"], 6), "ln": round(r["lng"], 6), "k": "l"}
        if i in lot_at:
            c, v = lot_at[i]
            row["c"] = c
            row["at"] = [short_name(v, "th"), short_name(v, "en"), v["id"]]
        if r.get("geoPrecision") == "approx":
            row["approx"] = 1
        row.update(ans)
        b = "".join(f"{k}:{why[k]}" for k in sorted(why) if why[k] != "m")
        if b:
            row["b"] = {k: why[k] for k in why if why[k] != "m"}
        rows.append(row)

    for row in rows:
        if row.get("en") == row.get("th"):
            row.pop("en", None)
        if row.get("at") and row["at"][1] == row["at"][0]:
            row["at"][1] = ""
    rows.sort(key=lambda x: (x["la"], x["ln"]))
    return rows


def landmarks():
    try:
        import bearings_layer
        cx = bearings_layer.ctx()
    except Exception as e:  # the page names lots by distance without them
        print("  landmarks skipped:", e)
        return {}
    out = {}
    for p, ls in cx.landmarks.items():
        out[p] = [[e.get("th") or e.get("name_th") or e.get("key"),
                   e.get("en") or e.get("name_en") or e.get("key"),
                   round(e["lat"], 6), round(e["lng"], 6)] for e in ls]
    return out


def tile_of(la, ln):
    """0.05° squares (about 5.5 km): the page loads the few around the reader."""
    return f"{math.floor(la * 20)}_{math.floor(ln * 20)}"


def main():
    import shutil
    tdir = OUT / "t"
    if tdir.exists():
        shutil.rmtree(tdir)
    tdir.mkdir(parents=True)
    for old in OUT.glob("lots-*.json"):
        old.unlink()
    total, tiles = 0, {}
    for p in PROVS:
        rows = bake(p)
        total += len(rows)
        for r in rows:
            r["p"] = p
            tiles.setdefault(tile_of(r["la"], r["ln"]), []).append(r)
        kinds = {}
        for r in rows:
            kinds[r.get("c") or r["k"]] = kinds.get(r.get("c") or r["k"], 0) + 1
        print(f"  {p}: {len(rows)} places · " + ", ".join(f"{k} {v}" for k, v in sorted(kinds.items())))
    for t, rows in tiles.items():
        (tdir / f"{t}.json").write_text(json.dumps(rows, ensure_ascii=False, separators=(",", ":")))
    model = {k: MODEL[k] for k in ("classes", "zones", "kerb", "reports")}
    model["landmarks"] = landmarks()
    model["tiles"] = sorted(tiles)
    model["tile"] = 20
    (OUT / "model.json").write_text(json.dumps(model, ensure_ascii=False, separators=(",", ":")))
    print(f"  {total} places in {len(tiles)} tiles → {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
