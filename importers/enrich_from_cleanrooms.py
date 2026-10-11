#!/usr/bin/env python3
"""Phones for the state health facilities, out of the clean-air register. WO-57 item 6.

THE GAP THIS CLOSES. The catalogue holds 124 hospitals and 469 รพ.สต. and
carried a phone number for TEN of the hospitals and NONE of the health
stations — because OSM does not have them and nobody had gone looking. On a
lifeline page a pin with no number is half an answer: it tells somebody where
to drive at three in the morning and not how to ask first.

WHERE THE NUMBERS COME FROM. WO-57 item 4 pulled the Department of Health's
clean-air room register for both provinces, and 1,090 of its rows are
สถานบริการสาธารณสุข — hospitals and health stations — each entered by that
facility's own staff, with a phone. The numbers were already on the disk,
fetched for another purpose. Nothing new is crawled here.

HOW A MATCH IS MADE, and how it refuses. Thai health-facility names are
formulaic: โรงพยาบาลส่งเสริมสุขภาพตำบลบ้านทุ่งแก is รพ.สต. + บ้านทุ่งแก. Both
sides are stripped to that tail, spaces removed, and matched EXACTLY, within
the same province, and only when the tail is unique on both sides. A tail
that names two facilities is skipped rather than guessed at — there are
several บ้านใหม่ in each province and a wrong phone on a health station is
worse than none.

  · one facility, many rooms: a hospital registers every room it has — Wiang
    Chiang Rung put in twenty-one — so the register side is COLLAPSED first.
    Rows sharing a province and a name are one facility when they also agree
    on a phone number, or when their pins all sit inside ONE_SITE_KM of each
    other. Only when they disagree on both is the name called ambiguous. The
    first draft skipped this and threw away 199 names as duplicates, which is
    most of the register's hospitals.
  · pin sanity: a match whose two pins are more than MAX_KM apart is refused.
    Same name, different place — the register's own pins are dirty enough
    that WO-57 had to write a whole check for them, and that check said so.
    The exception is a register row that check ALREADY flagged as misplaced:
    measuring against a coordinate we have declared wrong proves nothing, and
    a bad pin is no reason to doubt the phone beside it. Those eleven are
    taken, and the write says the pins disagreed.
  · never overwrites: a record that already carries a phone keeps it. OSM's
    copy may be older, but it was not written into enrich.json by a match.
  · every write carries its source and the date, like every other row in
    data/curated/enrich.json, so the next crawl cannot silently erase it and
    a reader can see where the number came from.

    python3 importers/enrich_from_cleanrooms.py            # report only
    python3 importers/enrich_from_cleanrooms.py --write    # write enrich.json
"""
import collections
import datetime
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLEAN = ROOT / "data" / "cleanrooms.json"
ENRICH = ROOT / "data" / "curated" / "enrich.json"
MAX_KM = 5.0
ONE_SITE_KM = 1.0
SRC = "https://podfoon.anamai.moph.go.th/"
CREDIT = "ระบบฐานข้อมูลห้องปลอดฝุ่น กรมอนามัย กระทรวงสาธารณสุข"

# Every way these two kinds of facility are written, longest first so the
# long form is stripped before the abbreviation inside it.
PREFIX = [
    "โรงพยาบาลส่งเสริมสุขภาพตำบล", "โรงพยาบาลส่งเสริมสุขภาพ",
    "สถานีอนามัยเฉลิมพระเกียรติ", "สถานีอนามัย",
    "รพ.สต.บ้าน", "รพ.สต.", "รพสต.", "โรงพยาบาล", "รพ.",
]
DROP = re.compile(r"[\s​()（）\"'’.·•\-–—]+")


def tail(name):
    """The part of a Thai facility name that is actually its own.

    บ้าน is left ON: it is part of the village name half the time
    (บ้านทุ่งแก) and stripping it merges ทุ่งแก with a different place
    that is genuinely called ทุ่งแก."""
    s = DROP.sub("", (name or "").strip())
    for p in PREFIX:
        pp = DROP.sub("", p)
        if s.startswith(pp):
            s = s[len(pp):]
            break
    return s


def km(a, b, c, e):
    R, t = 6371.0, math.pi / 180
    x, y = (c - a) * t, (e - b) * t
    return 2 * R * math.asin(math.sqrt(
        math.sin(x / 2) ** 2
        + math.cos(a * t) * math.cos(c * t) * math.sin(y / 2) ** 2))


def unique_by_tail(rows, key_name, key_prov):
    by = collections.defaultdict(list)
    for r in rows:
        t = tail(key_name(r))
        if len(t) >= 3:
            by[(key_prov(r), t)].append(r)
    return {k: v[0] for k, v in by.items() if len(v) == 1}, \
           {k for k, v in by.items() if len(v) > 1}


def collapse_register(rooms):
    """One row per FACILITY, not per room.

    Rows sharing a province and a name are the same place when they agree on
    a phone, or when every pin among them is within ONE_SITE_KM of the first.
    Anything else is two places with one name and is handed back as
    ambiguous — there are several บ้านใหม่ in each province."""
    by = collections.defaultdict(list)
    for r in rooms:
        t = tail(r["n"])
        if len(t) >= 3:
            by[(r["p"], t)].append(r)
    one, many = {}, set()
    for k, v in by.items():
        if len(v) == 1:
            one[k] = v[0]
            continue
        phones = {r["t"].strip() for r in v if r["t"].strip()}
        a = v[0]
        near = all(km(a["la"], a["ln"], r["la"], r["ln"]) <= ONE_SITE_KM
                   for r in v)
        if len(phones) == 1 or near:
            one[k] = a
        else:
            many.add(k)
    return one, many


def main():
    if not CLEAN.exists():
        sys.exit("data/cleanrooms.json is not here — run "
                 "importers/fetch_cleanrooms.py first")
    reg = json.loads(CLEAN.read_text(encoding="utf-8"))
    rooms = [r for r in reg["rooms"]
             if reg["types"][r["k"]] == "สถานบริการสาธารณสุข"
             and (r.get("t") or "").strip()
             and r.get("doubt") != "outside"]

    places = []
    for p in ("cm", "cr"):
        f = ROOT / "data" / "canonical" / f"{p}.json"
        for r in json.loads(f.read_text(encoding="utf-8")):
            subs = r.get("sub") or []
            if "hospital" in subs or "health-station" in subs:
                places.append(r)

    reg_by, reg_dupe = collapse_register(rooms)
    site_by, site_dupe = unique_by_tail(
        places, lambda r: r.get("name") or r.get("nameTh") or "",
        lambda r: r["province"])

    have = sum(1 for r in places if (r.get("phone") or "").strip())
    matched, far, bad_pin, ambiguous, already = [], [], [], 0, 0
    for key, place in site_by.items():
        room = reg_by.get(key)
        if room is None:
            if key in reg_dupe:
                ambiguous += 1
            continue
        if (place.get("phone") or "").strip():
            already += 1
            continue
        pins_disagree = False
        if place.get("lat") is not None and place.get("lng") is not None:
            d = km(place["lat"], place["lng"], room["la"], room["ln"])
            if d > MAX_KM:
                if room.get("doubt") in ("far", "outside"):
                    pins_disagree = True
                    bad_pin.append((round(d), place.get("name")))
                else:
                    far.append((round(d), place.get("name"), room["n"]))
                    continue
        matched.append((place, room, pins_disagree))

    print(f"catalogue: {len(places):,} hospitals + health stations, "
          f"{have} of them with a phone on this disk")
    print(f"register:  {len(rooms):,} health-facility rows with a phone")
    print(f"unique tails — catalogue {len(site_by):,} "
          f"({len(site_dupe)} names shared), register {len(reg_by):,} "
          f"({len(reg_dupe)} shared)")
    print(f"MATCHED {len(matched):,} places that had no phone")
    print(f"  {already} matched but already carried a number — left alone")
    print(f"  {ambiguous} refused: the register holds that name twice")
    print(f"  {len(bad_pin)} taken anyway: the register's own pin for that row "
          f"was already flagged as misplaced, so only the phone was believed")
    print(f"  {len(far)} refused: same name, pins more than {MAX_KM:g} km apart")
    for d, a, b in sorted(far, reverse=True)[:6]:
        print(f"     {d:4d} km  {a}  ~  {b}")

    if "--write" not in sys.argv:
        print("\nreport only — pass --write to fold these into "
              "data/curated/enrich.json")
        return 0

    doc = json.loads(ENRICH.read_text(encoding="utf-8"))
    today = datetime.date.today().isoformat()
    for place, room, pins_disagree in matched:
        e = doc.get(place["id"]) or {}
        fields = e.get("fields") or {}
        fields["phone"] = room["t"]
        e.update({
            "fetched": today,
            "fields": fields,
            "how": dict(e.get("how") or {},
                        phone="the facility's own entry in the Department of "
                              "Health clean-air room register"
                              + (" (its coordinate there disagrees with ours "
                                 "and was not used)" if pins_disagree else "")),
            "license": "state-register",
            "src": SRC,
            "credit": CREDIT,
        })
        doc[place["id"]] = e
    ENRICH.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n",
                      encoding="utf-8")
    print(f"\nwrote {len(matched):,} phone numbers into "
          f"data/curated/enrich.json ({today})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
