#!/usr/bin/env python3
"""Find hospitals held twice — once by OpenStreetMap, once by the state register.

The two medical sources cannot merge themselves. `import_all` merges on `id`,
and a CITIZENinfo record is `cm-moph-<code>` while the crawl's is
`cm-osm-node-<id>`, so โรงพยาบาลนครพิงค์ arrives from both and sits on the shelf
twice. Nothing here fixes that automatically, because this catalogue folds
duplicates from data/curated/merges.json and nowhere else — "human-confirmed
pairs only". A directory that quietly decides two hospitals are one is worse
than one that shows a pair and asks.

So this measures and proposes. It writes cache/medical_dupes_<province>.txt
with a ready-to-paste merges.json line for each pair, and says what each side
carries so a person can choose which id to keep:

  the OSM record usually has the phone, the hours and the website
  the register record has the authority, the government code, and a pin the
  state surveyed

Neither is automatically better, which is exactly why a person picks.

    python3 importers/audit_medical_dupes.py
"""
import json
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEAR_M = 300

# Words that say "this is a hospital", not WHICH hospital. โรงพยาบาลส่งเสริม
# สุขภาพตำบลบ้านโป่ง and Ban Pong Health Station share only บ้านโป่ง once these
# are gone, and บ้านโป่ง is the whole answer.
NOISE = re.compile(
    r"โรงพยาบาลส่งเสริมสุขภาพตำบล|โรงพยาบาล|สถานีอนามัย|ศูนย์บริการสาธารณสุข"
    r"|รพ\.สต\.|รพ\.|คลินิก|สาขา|จังหวัด|ตำบล|อำเภอ|บ้าน"
    r"|hospital|health|promoting|station|clinic|centre|center|sub ?district", re.I)


# The same trick for schools. โรงเรียนบ้านสันทราย and Ban San Sai School share
# only สันทราย once the words that merely say "this is a school" are gone —
# and สันทราย is the whole answer. บ้าน has to go for the same reason it does
# above: nearly every village school in both provinces begins with it.
SCHOOL_NOISE = re.compile(
    r"โรงเรียน|รร\.|ร\.ร\.|วิทยาลัย|มหาวิทยาลัย|สถาบัน|ศูนย์|อนุบาล|บ้าน"
    r"|เทศบาล|วัด|สาขา|จังหวัด|ตำบล|อำเภอ|ประชาบาล|วิทยา|ศึกษา"
    r"|school|college|university|academy|institute|campus|international"
    r"|kindergarten|nursery|the", re.I)

KINDS = {
    "medical": {"cat": "medical", "prefix": "moph", "noise": NOISE,
                "register": "the state register (CITIZENinfo)",
                "thing": "facility"},
    # The schools shelf has the same shape and the same reason: a school
    # mapped in OpenStreetMap and listed in the OBEC register arrives as
    # cm-osm-way-… and cm-obec-…, and no merge on id can see they are one
    # place. The crawl usually holds the pin a mapper walked to and sometimes
    # a website; the register holds the phone, the levels, the enrolment and
    # the ministry's own code. Neither is automatically better.
    "school": {"cat": "school", "prefix": "obec", "noise": SCHOOL_NOISE,
               "register": "the OBEC school register",
               "thing": "school"},
}


def _norm(s, noise=None):
    s = (noise or NOISE).sub(" ", s or "")
    s = re.sub(r"[^\w฀-๿]+", " ", s.lower())
    return {w for w in s.split() if len(w) > 1}


def _haversine(a, b):
    r = 6371000.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = math.radians(b[0] - a[0]), math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def _carries(r):
    got = [k for k in ("phone", "hours", "website", "address") if r.get(k)]
    return ", ".join(got) or "nothing but name and pin"


def audit(province, kind="medical"):
    spec = KINDS[kind]
    f = os.path.join(ROOT, "data", "canonical", f"{province}.json")
    if not os.path.exists(f):
        return []
    recs = [r for r in json.load(open(f, encoding="utf-8"))
            if spec["cat"] in (r.get("cat") or []) and r.get("lat")]
    prefix = f"{province}-{spec['prefix']}-"
    moph = [r for r in recs if r["id"].startswith(prefix)]
    other = [r for r in recs if not r["id"].startswith(prefix)]
    pairs = []
    for m in moph:
        mk = _norm(m["name"], spec["noise"])
        if not mk:
            continue
        for o in other:
            d = _haversine((m["lat"], m["lng"]), (o["lat"], o["lng"]))
            if d > NEAR_M:
                continue
            ok = _norm(o.get("name") or "", spec["noise"])
            shared = mk & ok
            if shared:
                pairs.append((int(d), m, o, sorted(shared)))
    pairs.sort(key=lambda p: p[0])
    out = os.path.join(ROOT, "cache", f"{kind}_dupes_{province}.txt")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    lines = [
        f"# {len(pairs)} place(s) that look like the same {spec['thing']} held "
        f"twice —",
        f"# once from OpenStreetMap, once from {spec['register']}.",
        "# Nothing is merged until a person says so. Confirm a pair by adding it",
        "# to data/curated/merges.json as {\"<keep id>\": [\"<drop id>\"]}.",
        "#",
        "# Which to keep is a real choice, not a formality: the OSM record",
        "# usually carries the phone and the hours; the register record carries",
        "# the government code and a pin the state surveyed. Keep the one with",
        "# more to say — the merge unions their shelves either way.",
        "",
    ]
    for d, m, o, shared in pairs:
        lines += [
            f"{d:4d} m apart   shared name: {' '.join(shared)}",
            f"    register  {m['id']}  {m['name']}",
            f"              carries: {_carries(m)}",
            f"    crawled   {o['id']}  {o.get('name')}",
            f"              carries: {_carries(o)}",
            f'    suggested: "{o["id"]}": ["{m["id"]}"]',
            "",
        ]
    open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return pairs


if __name__ == "__main__":
    kinds = [k for k in KINDS if f"--{k}" in sys.argv] or list(KINDS)
    for kind in kinds:
        total = 0
        for prov in ("cm", "cr"):
            pairs = audit(prov, kind)
            total += len(pairs)
            print(f"{kind} {prov}: {len(pairs)} likely duplicate pair(s) "
                  f"-> cache/{kind}_dupes_{prov}.txt")
            for d, m, o, shared in pairs[:6]:
                print(f"    {d:4d}m  {m['name'][:38]:38} "
                      f"== {str(o.get('name'))[:34]}")
        if not total:
            print(f"{kind}: no duplicates found between the register and "
                  f"the crawl")
