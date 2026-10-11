#!/usr/bin/env python3
"""Tie NaN's own pictures to places, and make the place when there is none.

Her word 2026-10-11: her photographs belong on place pages, and "if there isn't
a placeid, make one urgently and solve the problem that causes a lack of
placeid generation going forward". 118 frames of the Kamthieng amulet market
sat unplaced because the market's record (OSM's "Antique Market") was filed
under shopping, not market, and nothing tied a picture to a market whose stalls
share its pin.

Reads data/curated/own_pictures.json and data/canonical/{cm,cr}.json. For each
picture with coordinates and no placeId, in this order:

  1. name    its sign text names a record within 60 m, or its title or
             description names one within 30 m
             (harvest_commons.identifies / names_agree, the Commons test)
  2. inside  the nearest record within 35 m is a container — a market, or a
             record other records name in attrs.insideOfId or share a pin
             with — and the picture is of a place-like subject. placeId is the
             container; `places` adds up to MEMBER_CAP of its stalls, dealt
             round-robin so each stall page gets different frames
  3. wat     a temple picture with exactly one wat within 55 m
  4. new     what is left is clustered: one day, within 40 m, at least
             MIN_CLUSTER frames of a place-like subject, and no record within
             50 m. Each cluster becomes a record in
             data/curated/additions-<province>.json with a provisional name
             (the subject and the nearest listed place), attrs.provisionalName
             true, and a line in PHOTOS — ASK so she can name it.

Each placed picture carries `placedBy` saying which rule and how far. Street
views (topic city / transport / nature / view only) are left alone: a road is
not a place.

    python3 importers/place_own_pictures.py            # report only
    python3 importers/place_own_pictures.py --write    # apply

The standing walk runs it with --write before import_all.py, so a record made
here is imported the same round.
"""
import argparse
import collections
import datetime
import hashlib
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "importers"))
import harvest_commons as hc  # noqa: E402

OWN = ROOT / "data" / "curated" / "own_pictures.json"
ADD = {"cm": ROOT / "data" / "curated" / "additions-chiang-mai.json",
       "cr": ROOT / "data" / "curated" / "additions-chiang-rai.json"}
ASK = Path.home() / "Desktop" / "1 — NEXT UP" / "PHOTOS — ASK" / "ASK.txt"

NAME_M, DESC_M, INSIDE_M, WAT_M, CLUSTER_M, CLEAR_M = 60, 30, 35, 55, 40, 50
MIN_CLUSTER = 4
MEMBER_CAP = 4
PLACE_TOPICS = {"market", "amulets", "shop", "food", "arts", "craft", "textile",
                "faith", "wat", "history", "stay"}
TEMPLE = re.compile(r"\b(wat|temple|viharn|vihara|wihan|ubosot|chedi|gable|gate|hall|mandir|shrine)\b", re.I)
# Words that match a record's name without picking out which place it is.
WEAK = {"the", "and", "parking", "gate", "house", "spirit", "shop", "market", "star",
        "amulet", "amulets", "coffee", "cafe", "hotel", "car", "park", "road", "bank", "atm"}
LABEL = {  # subject -> (th, en) for a provisional name
    "amulets": ("แผงพระเครื่อง", "Amulet stalls"), "market": ("ตลาด", "Market"),
    "food": ("ร้านอาหาร", "Food stall"), "wat": ("วัด", "Temple"), "faith": ("ศาลเจ้า", "Shrine"),
    "craft": ("ร้านงานฝีมือ", "Craft workshop"), "textile": ("ร้านผ้า", "Textile shop"),
    "arts": ("ร้านศิลปะ", "Art shop"), "shop": ("ร้านค้า", "Shop"), "history": ("โบราณสถาน", "Old site"),
    "stay": ("ที่พัก", "Lodging"),
}


def metres(a1, o1, a2, o2):
    return hc.haversine(a1, o1, a2, o2)


def names_of(r):
    return [n for n in (r.get("name"), r.get("nameEn"), r.get("nameTh")) if n]


def place_like(p):
    return bool(PLACE_TOPICS & set(p.get("topic") or []))


class Catalogue:
    def __init__(self):
        self.recs = []
        for pv in ("cm", "cr"):
            for r in json.loads((ROOT / "data" / "canonical" / f"{pv}.json").read_text()):
                if r.get("lat") is not None and r.get("lng") is not None:
                    self.recs.append(r)
        self.by_id = {r["id"]: r for r in self.recs}
        self.grid = collections.defaultdict(list)
        for r in self.recs:
            self.grid[self.key(r["lat"], r["lng"])].append(r)
        # containers: named by another record's insideOfId, or holding a pin others share
        self.members = collections.defaultdict(list)
        pins = collections.defaultdict(list)
        for r in self.recs:
            inside = (r.get("attrs") or {}).get("insideOfId")
            if inside in self.by_id:
                self.members[inside].append(r["id"])
            pins[(r["lat"], r["lng"])].append(r)
        for group in pins.values():
            if len(group) < 3:
                continue
            heads = [r for r in group if "market" in (r.get("cat") or [])
                     or r["id"] in self.members or "-osm-" in r["id"]]
            if len(heads) == 1:
                h = heads[0]
                for r in group:
                    if r["id"] != h["id"] and r["id"] not in self.members[h["id"]]:
                        self.members[h["id"]].append(r["id"])

    @staticmethod
    def key(lat, lng):
        return (int(lat / 0.002), int(lng / 0.002))

    def near(self, lat, lng, m):
        k = self.key(lat, lng)
        out = []
        for a in (-1, 0, 1):
            for b in (-1, 0, 1):
                for r in self.grid.get((k[0] + a, k[1] + b), []):
                    d = metres(lat, lng, r["lat"], r["lng"])
                    if d <= m:
                        out.append((d, r))
        return sorted(out, key=lambda x: x[0])

    def is_container(self, r):
        return "market" in (r.get("cat") or []) or bool(self.members.get(r["id"]))


def by_name(cat, p):
    """A read sign may name a place up to NAME_M away; a description, which
    also mentions the shop next door and the road ahead, only up to DESC_M."""
    hay_title = " ".join(x for x in (p.get("signText"), p.get("title")) if x)
    desc = p.get("description") or ""
    reach = NAME_M if (p.get("signText") or "").strip() else DESC_M
    for d, r in cat.near(p["lat"], p["lng"], reach):
        nm = names_of(r)
        ok, why = hc.identifies(nm, hay_title, desc)
        if ok and not set((why or "").split(",")) - WEAK:
            ok = False      # "amulet", "parking", "spirit house" name a kind, not a place
        if not ok:
            why = hc.names_agree(nm, hay_title, desc)
            ok = why is not None
        if ok:
            return r, d
    return None, None


def by_container(cat, p):
    if not place_like(p):
        return None, None
    for d, r in cat.near(p["lat"], p["lng"], INSIDE_M):
        if cat.is_container(r):
            return r, d
        container = (r.get("attrs") or {}).get("insideOfId")
        if container in cat.by_id:
            return cat.by_id[container], d
    return None, None


def by_wat(cat, p):
    if not ({"wat", "faith"} & set(p.get("topic") or [])):
        return None, None
    if not TEMPLE.search(p.get("title") or "") or re.search(r"spirit house", p.get("title") or "", re.I):
        return None, None
    wats = [(d, r) for d, r in cat.near(p["lat"], p["lng"], WAT_M) if "wat" in (r.get("cat") or [])]
    return (wats[0][1], wats[0][0]) if len(wats) == 1 else (None, None)


def clusters(picks):
    """Same day, chained within CLUSTER_M."""
    by_day = collections.defaultdict(list)
    for p in picks:
        by_day[p.get("date") or ""].append(p)
    out = []
    for day, ps in by_day.items():
        left = list(ps)
        while left:
            group = [left.pop()]
            grew = True
            while grew:
                grew = False
                for q in list(left):
                    if any(metres(q["lat"], q["lng"], g["lat"], g["lng"]) <= CLUSTER_M for g in group):
                        group.append(q)
                        left.remove(q)
                        grew = True
            out.append((day, group))
    return out


def provisional_record(cat, day, group):
    lat = sum(p["lat"] for p in group) / len(group)
    lng = sum(p["lng"] for p in group) / len(group)
    pv = "cr" if lat > 19.5 else "cm"
    topics = collections.Counter(t for p in group for t in (p.get("topic") or []) if t in LABEL)
    subject = topics.most_common(1)[0][0] if topics else "shop"
    th, en = LABEL[subject]
    near = next(((d, r) for d, r in cat.near(lat, lng, 400)
                 if names_of(r) and not (r.get("attrs") or {}).get("provisionalName")), None)
    if near:
        r = near[1]
        th += " ใกล้" + (r.get("nameTh") or r.get("name") or r.get("nameEn"))
        en += " near " + (r.get("nameEn") or r.get("name") or r.get("nameTh"))
    h = hashlib.sha1(("%.5f,%.5f,%s" % (lat, lng, day)).encode()).hexdigest()[:8]
    rid = "%s-own-%s-%s" % (pv, (day or "undated").replace("-", ""), h)
    cats = {"market": ["market"], "amulets": ["shopping"], "food": ["food"], "wat": ["wat"],
            "faith": ["wat"], "stay": ["hotel"]}.get(subject, ["shopping"])
    slugs = [p["slug"] for p in group]
    return pv, {
        "id": rid, "province": pv, "cat": cats, "sub": [],
        "name": th, "nameTh": th, "nameEn": en,
        "lat": round(lat, 7), "lng": round(lng, 7), "geoPrecision": "approx",
        "address": None, "phone": None, "website": None, "hours": None,
        "attrs": {"provisionalName": True,
                  "nameNote": "named for what NaN's photographs show and the nearest listed place; "
                              "waiting for her to name it (PHOTOS — ASK)",
                  "pinVia": "the middle of her %d photographs, %s" % (len(group), day)},
        "featured": False, "landmark": False,
        "sources": [{"type": "field", "ref": "NaN's own photographs " + ", ".join(slugs[:6])
                     + (" and %d more" % (len(slugs) - 6) if len(slugs) > 6 else ""),
                     "fetched": day, "via": "importers/place_own_pictures.py"}],
        "confidence": "field",
        "updatedAt": datetime.date.today().isoformat(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    cat = Catalogue()
    own = json.loads(OWN.read_text())
    picks = own["picks"]
    todo = [p for p in picks if not p.get("placeId") and p.get("lat") is not None and p.get("lng") is not None]
    n = collections.Counter()
    dealt = collections.defaultdict(int)       # member id -> frames given
    rr = collections.defaultdict(int)          # container id -> round-robin position
    rest = []
    for p in todo:
        for rule, fn in (("name", by_name), ("inside", by_container), ("wat", by_wat)):
            r, d = fn(cat, p)
            if r:
                p["placeId"] = r["id"]
                p["placedBy"] = "%s, %d m, %s" % (rule, round(d), datetime.date.today().isoformat())
                if rule == "inside":
                    mem = [m for m in cat.members.get(r["id"], []) if dealt[m] < MEMBER_CAP]
                    if mem:
                        m = mem[rr[r["id"]] % len(mem)]
                        rr[r["id"]] += 1
                        dealt[m] += 1
                        p["places"] = sorted(set(p.get("places") or []) | {m})
                n[rule] += 1
                break
        else:
            rest.append(p)

    new = []
    for day, group in clusters([p for p in rest if place_like(p)]):
        if len(group) < MIN_CLUSTER:
            continue
        lat = sum(p["lat"] for p in group) / len(group)
        lng = sum(p["lng"] for p in group) / len(group)
        if cat.near(lat, lng, CLEAR_M):
            continue
        pv, rec = provisional_record(cat, day, group)
        new.append((pv, rec, group))
        for p in group:
            p["placeId"] = rec["id"]
            p["placedBy"] = "new place %s, %s" % (rec["id"], datetime.date.today().isoformat())
        n["new"] += len(group)

    print("unplaced with coordinates: %d · placed by name %d, inside %d, wat %d · "
          "%d new place(s) holding %d" % (len(todo), n["name"], n["inside"], n["wat"], len(new), n["new"]))
    for pv, rec, group in new:
        print("  new %s  %s / %s  (%d photos)" % (rec["id"], rec["nameTh"], rec["nameEn"], len(group)))
    if not a.write:
        print("report only; --write applies it")
        return
    if not (n["name"] or n["inside"] or n["wat"] or new):
        return
    for pv in ("cm", "cr"):
        mine = [rec for p, rec, _ in new if p == pv]
        if mine:
            recs = json.loads(ADD[pv].read_text())
            have = {r["id"] for r in recs}
            recs += [r for r in mine if r["id"] not in have]
            ADD[pv].write_text(json.dumps(recs, ensure_ascii=False, indent=1) + "\n")
    OWN.write_text(json.dumps(own, ensure_ascii=False, indent=1))
    if new and ASK.parent.exists():
        with ASK.open("a") as fh:
            for pv, rec, group in new:
                fh.write("\n%s — a place from your photographs (%d, %s), named for now \"%s\". "
                         "What is it called? → \n" % (rec["id"], len(group), group[0].get("date"),
                                                      rec["nameEn"]))


if __name__ == "__main__":
    main()
