#!/usr/bin/env python3
"""Read what the catalogue holds and drops about views and photo spots. Zero network.

Same contract as audit_elephant.py and audit_culture.py: this never edits
canonical data. It reports, and import_overpass.views_hit() borrows THIS
FILE's name rules (one copy) to file view-shaped elements the WO-19
attraction dragnet already fetched.

The measurement that asked for this (notes/views-proposal-2026-08-20.md):
on 2026-08-20 the viewpoint shelf held 103 records — Chiang Mai 31, Chiang
Rai 72 — and the imbalance is the crawl geometry, not the geography: CR is
in WIDE_PROVINCES and was asked province-wide, CM's `culture` group (the one
carrying tourism=viewpoint) has only ever been asked on the near ring. The
views of Chiang Mai are on the doi by construction — กิ่วแม่ปาน, ดอยอ่างขาง,
แม่กำปอง, ห้วยน้ำดัง — exactly where the near ring is not. Meanwhile the
WO-19 elephants crawl (zoo · theme_park · attraction, WIDE, both provinces,
fetched 2026-08-20 with Nan's go) caught the famous waterfalls — แม่สา,
บัวตอง, วชิรธาร, แม่ยะ, สิริภูมิ — and fenced every non-elephant element
into cache/elephant_review_<prov>.txt, "the ready-made menu for a future
attractions order". No crawl group has ever asked for waterway=waterfall,
natural=peak or natural=cliff, and all 103 viewpoint records carry no photo,
no hours and no fee; OSM's own `direction` and `ele` on their elements are
dropped at import.

Five reports:

  SHELF    what sub=viewpoint holds today, by province, with contact/photo
           coverage and the crawl-geometry receipt.
  DROPPED  tags on cached tourism=viewpoint elements that import does not
           keep (direction, ele, description) — recoverable with no fetch —
           and the nameless count (skipped by the no-shelf-for-the-nameless
           rule; reported so the rule is a decision, not an accident).
  MENU     the WO-19 attraction cache read with this file's rules: which
           elements declare a waterfall or a viewpoint BY NAME and would
           enter through views_hit(); everything else stays in the elephant
           review file, which remains the menu for the rest.
  CLAIMS   places on OTHER shelves whose name claims a view — the census for
           a future cross-shelf `view` tag (WO-15 machinery). Printed with
           the guard visible: วิวัฒน์/วิวาห์ names and the น้ำตก DISH names
           (ลาบ-น้ำตก is lunch, not a waterfall) appear under their fences.
  NEVER    selectors absent from crawl_overpass.py, and famous spots absent
           from the catalogue — the evidence for the wide `views` group.

What this deliberately does NOT do:

  * Rank a vista. No spot is scored, sorted or crowned; sorts stay
    distance and alphabet, the same rule as the temples.
  * Infer sunset from a compass bearing. `direction=270` renders as the
    bearing; whether the horizon is open at dusk is the venue's or the
    door survey's to state.
  * Call anything a "hidden gem" or a "tourist spot" — no line on this
    site sorts places into real and otherwise.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------- the rules
# Shared with import_overpass.views_hit() — one copy. Each pattern carries a
# witness for why it is shaped the way it is.

# น้ำตก anywhere in a name is a waterfall ONLY once food and lodging are
# fenced off: น้ำตกหมู is a grilled-pork laab cousin, and ร้านลาบ-น้ำตก sells
# it. The import fence never sees those (it reads the attraction cache and
# refuses amenity/lodging tags first); the CLAIMS report prints them so the
# guard can be seen working.
WATERFALL_RULES = [
    ("น้ำตก", r"น้ำตก"),
    ("waterfall", r"\bwaterfalls?\b"),
]

# Deliberately NOT bare วิว: วิวัฒน์ is a given name, วิวาห์ is a wedding,
# and every Lake View guesthouse is a venue CLAIMING a view — that is the
# future tag's business (CLAIMS below), not a spot on the sights shelf.
VIEWPOINT_RULES = [
    ("จุดชมวิว", r"จุดชมวิว"),
    ("ลานชมวิว", r"ลานชมวิว"),
    ("ชมวิว", r"ชมวิว"),
    ("viewpoint", r"view\s*point"),
    ("skywalk", r"sky\s*walk|สกายวอล์[คก]"),
]

# The census patterns for the cross-shelf claim tag — a venue whose NAME
# says the view is part of what it sells. Fences inline: วิว not followed by
# the syllables that make it วิวัฒน์/วิวาห์/วิวรณ์; view as its own word so
# "review" and "interview" stay out.
VIEW_CLAIM = re.compile(
    r"วิว(?!ัฒน)(?!าห)(?!รณ)|ชมวิว|\bview\b|\bpanoramas?\b|\bpanoramic\b",
    re.I)
VIEW_CLAIM_FENCED = re.compile(r"วิวัฒน|วิวาห|วิวรณ|\breview\b|\binterview\b", re.I)
NAM_TOK_DISH = re.compile(r"ลาบ|ตำ|หมูย่าง|คอหมู|เนื้อย่าง|อาหาร")

# ---------------------------------------------------------- the full mine
# A name that DECLARES a view spot, a falls, a gorge or a cave — as against a
# name that merely CARRIES one of those words as a toponym. The distinction is
# the whole discipline of this file and it is the ช้าง lesson again: บ้านถ้ำ is
# a cave VILLAGE, so โรงเรียนบ้านถ้ำ is a school and วัดถ้ำ… is a temple; เขื่อนผาก
# is a tambon, so a รพ.สต. in it is a health station. Bare ดอย, ม่อน, ผา and ยอด
# are never matched at all — ดอยเต่า, ดอยสะเก็ด and ดอยหล่อ are อำเภอ names
# (โรงพยาบาลดอยเต่า is a hospital), ม่อนปิ่น and ม่อนจอง are ตำบล, and ผาสุก means
# wellbeing. Only the compounds that say the place IS the thing.
DECLARE_RULES = [
    ("จุดชมวิว", r"จุดชมวิว|ลานชมวิว|ชมวิว"),
    ("ทะเลหมอก", r"ทะเลหมอก"),
    ("น้ำตก", r"น้ำตก"),
    ("waterfall", r"\bwaterfalls?\b"),
    ("viewpoint", r"view\s*point"),
    ("skywalk", r"sky\s*walk|สกายวอล์?[คก]"),
    ("แก่ง", r"แก่ง"),
]

# The shelves a declaring name is ALREADY answerable from. A record here is
# where a reader would find it; anything else is the finding.
ON_SHELF = {"viewpoint", "waterfall"}

# STRAYS — the toponym guard, printed so it can be seen working. Each of these
# holds a declaring word inside a name that is not the thing: a school, a
# temple, a health station or a restaurant named FOR the falls or the cave.
STRAY_KINDS = ("school", "medical", "wat", "food", "hotel")

# Not everything holding น้ำตก in its name on a sights or parks shelf is the
# falls. Three different things arrive together and only the first is a
# candidate for the shelf:
#   spot      — the falls or the viewpoint itself
#   container — the forest park, national park or garden that HOLDS it. Its
#               own place, never a duplicate of the thing inside, and moving
#               it onto the waterfall shelf would say the park is a waterfall.
#   station   — a ranger unit, a village or a community named FOR the falls.
#               หน่วยพิทักษ์อุทยานแห่งชาติ…(น้ำตกขุนกรณ์) is an office at the
#               falls; ชุมชนบ้านแม่ต๋ำน้ำตก is a village. Both are toponym
#               carriers exactly as โรงเรียนบ้านถ้ำ is.
CONTAINER_RE = re.compile(r"วนอุทยาน|อุทยานแห่งชาติ|สวน\S*น้ำตก|national park|forest park", re.I)
STATION_RE = re.compile(r"หน่วยพิทักษ์|ที่ทำการ|ชุมชนบ้าน|หมู่บ้าน|ศูนย์บริการ", re.I)

FAMOUS = [
    # the roll asked against the catalogue in NEVER — each one a name any
    # reader of either province would try first
    "กิ่วแม่ปาน", "อ่างขาง", "แม่กำปอง", "ห้วยน้ำดัง", "ผาช่อ", "ม่อนแจ่ม",
    "บัวตอง", "แม่สา", "วชิรธาร", "แม่ยะ", "ภูชี้ฟ้า", "ดอยตุง", "ผาฮี้",
    "ขุนกรณ์", "ดอยหลวงเชียงดาว",
]


def _match(rules, text):
    for label, pat in rules:
        if re.search(pat, text, re.I):
            return label
    return None


def load_records():
    recs = []
    for f in sorted((ROOT / "data" / "canonical").glob("*.json")):
        d = json.loads(f.read_text())
        recs.extend(d if isinstance(d, list) else d.get("records", []))
    return recs


def name_of(r):
    return " ".join(str(r.get(k) or "") for k in ("name", "nameTh", "nameEn"))


def cached_elements(stem):
    out = {}
    for prov in ("cm", "cr"):
        p = ROOT / "cache" / "overpass" / prov / f"{stem}.json"
        if p.exists():
            out[prov] = json.loads(p.read_text()).get("elements", [])
        else:
            out[prov] = []
    return out


def is_lodging_or_food_tags(t):
    return (t.get("amenity") in ("restaurant", "cafe", "bar", "pub", "fast_food")
            or t.get("tourism") in ("hotel", "guest_house", "hostel"))


def element_name(t):
    return " ".join(v for v in (t.get("name"), t.get("name:th"),
                                t.get("name:en"), t.get("alt_name")) if v)


def band(title, note=""):
    print()
    print("=" * 72)
    print(title + ("  —  " + note if note else ""))
    print("=" * 72)


def report_shelf(recs):
    band("SHELF", "the three view shelves today")
    for sub in ("viewpoint", "waterfall", "peak"):
        rows_all = [r for r in recs if sub in (r.get("sub") or [])]
        print(f"  {sub}  ({len(rows_all)})")
        for prov in ("cm", "cr"):
            rows = [r for r in rows_all if r.get("province") == prov]
            if not rows:
                continue
            photo = sum(1 for r in rows if r.get("photo"))
            ele = sum(1 for r in rows if (r.get("attrs") or {}).get("ele"))
            face = sum(1 for r in rows if (r.get("attrs") or {}).get("direction"))
            bare = sum(1 for r in rows if re.fullmatch(
                r"จุดชมวิว|viewpoint|sunset|waterfall", (r.get("name") or "").strip(),
                re.I))
            print(f"    {prov}: {len(rows):4d} — photo {photo}, elevation {ele}, "
                  f"bearing {face}, bare-named {bare}")
    print("\n  The imbalance this file was written to explain is GONE. It read"
          "\n  cm 31 / cr 74 because cr is in WIDE_PROVINCES while cm's culture"
          "\n  group had only ever been asked on the near ring — and the views"
          "\n  of Chiang Mai are on the doi, which is the one place a near ring"
          "\n  cannot reach. The wide `views` group (2026-08-21, Nan's go) asked"
          "\n  properly: cm now leads on all three shelves.")
    return [r for r in recs if "viewpoint" in (r.get("sub") or [])]


def report_dropped():
    band("DROPPED", "tags on cached view elements that import does not keep")
    culture, views = cached_elements("culture"), cached_elements("views")
    for prov in ("cm", "cr"):
        # BOTH caches, deduplicated by ref. tourism=viewpoint lives in the
        # near-ring `culture` group AND in the province-wide `views` group,
        # and reading only the first undercounted Chiang Mai four-fold.
        byref = {}
        for e in (culture.get(prov) or []) + (views.get(prov) or []):
            byref[f"{e.get('type')}/{e.get('id')}"] = e
        els = list(byref.values())
        vps = [e for e in els if (e.get("tags") or {}).get("tourism") == "viewpoint"
               or (e.get("tags") or {}).get("waterway") == "waterfall"
               or (e.get("tags") or {}).get("natural") == "peak"]
        named = [e for e in vps if element_name(e.get("tags", {}))]
        keys = {}
        for e in vps:
            for k in ("direction", "ele", "description", "description:en", "wikidata"):
                if k in (e.get("tags") or {}):
                    keys[k] = keys.get(k, 0) + 1
        print(f"  {prov}: {len(vps)} view elements cached, {len(named)} named "
              f"({len(vps) - len(named)} nameless — skipped by the "
              f"no-shelf-for-the-nameless rule; a map could still draw them, "
              f"which is a live question for WO-20)")
        if keys:
            print(f"      carried: " + ", ".join(
                f"{k} ×{n}" for k, n in sorted(keys.items())))
            print("      All of these reach the record: direction and ele are"
                  "\n      kept and rendered since WO-21, description since WO-3"
                  "\n      (as the mapper's own sentence, credited to OSM). The"
                  "\n      wikidata ids are the live one — 67 view records cite"
                  "\n      an article, which is exactly what enrich_wikipedia.py"
                  "\n      reads, and it has never been run over this shelf.")


def report_menu():
    band("MENU", "the WO-19 attraction cache, read with this file's rules")
    takes = {}
    for prov, els in cached_elements("elephants").items():
        rows = []
        for e in els:
            t = e.get("tags") or {}
            name = element_name(t)
            if not name or is_lodging_or_food_tags(t):
                continue
            if re.search(r"\(\s*closed\b|ปิดถาวร|ปิดกิจการ", name, re.I):
                continue
            hit = (_match(WATERFALL_RULES, name) and "waterfall") or \
                  (_match(VIEWPOINT_RULES, name) and "viewpoint")
            if hit:
                rows.append((hit, name, f"{e['type']}/{e['id']}"))
        takes[prov] = rows
        print(f"  {prov}: {len(rows)} elements would enter through views_hit()")
        for sub, name, ref in rows:
            print(f"      [{sub}] {name}   ({ref})")
    return takes


def report_claims(recs):
    band("CLAIMS", "names on other shelves that claim a view — the tag census")
    bycat, fenced, dishes = {}, [], []
    for r in recs:
        if "viewpoint" in (r.get("sub") or []):
            continue
        n = name_of(r)
        if VIEW_CLAIM_FENCED.search(n) and not VIEW_CLAIM.search(n):
            fenced.append(n.strip())
            continue
        if VIEW_CLAIM.search(n):
            cat = "+".join(r.get("cat") or ["?"])
            bycat.setdefault(cat, []).append(r.get("name") or r.get("nameEn"))
        if re.search(r"น้ำตก", n) and NAM_TOK_DISH.search(n):
            dishes.append(n.strip())
    total = sum(len(v) for v in bycat.values())
    print(f"  {total} records claim a view by name, by shelf:")
    for cat, names in sorted(bycat.items(), key=lambda kv: -len(kv[1])):
        head = ", ".join(str(x) for x in names[:4])
        more = f" … +{len(names) - 4}" if len(names) > 4 else ""
        print(f"    {cat:24s} {len(names):3d}   {head}{more}")
    if fenced:
        print(f"  guard, working: {len(fenced)} วิวัฒน์/วิวาห์-type names fenced out — "
              + "; ".join(fenced[:3]))
    if dishes:
        print(f"  guard, working: {len(dishes)} น้ำตก dish names left to lunch — "
              + "; ".join(dishes[:3]))
    return bycat


def _shelf(r):
    return "+".join(r.get("cat") or ["?"]) + "/" + ",".join(r.get("sub") or ["-"])


def report_hiding(recs):
    """Every record that DECLARES a view spot by name and sits where nobody
    looking for one would find it. This replaces asking a seed list of famous
    names whether it is present — the shelf's own records answer instead."""
    band("HIDING", "declaring names on shelves a view-seeker never opens")
    found, strays = {}, []
    for r in recs:
        n = name_of(r)
        label = _match(DECLARE_RULES, n)
        if not label:
            continue
        if set(r.get("sub") or []) & ON_SHELF:
            continue
        top = (r.get("cat") or ["?"])[0]
        if top in STRAY_KINDS:
            strays.append((top, r.get("name"), label))
            continue
        kind = ("container" if CONTAINER_RE.search(n)
                else "station" if STATION_RE.search(n) else "spot")
        found.setdefault(kind, []).append(
            (r.get("province"), r.get("name"), r.get("nameEn") or "",
             label, _shelf(r), r.get("id")))
    total = sum(len(v) for v in found.values())
    print(f"  {total} record(s) declare a view, falls or gorge and are shelved "
          f"elsewhere, sorted into what they actually are:")
    for kind in ("spot", "container", "station"):
        rows = found.get(kind) or []
        if not rows:
            continue
        note = {"spot": "candidates for the shelf — a person confirms each",
                "container": "the park that HOLDS a falls; its own place, "
                             "never moved onto the waterfall shelf",
                "station": "an office or a village named FOR the falls; a "
                           "toponym carrier, keeps its shelf"}[kind]
        print(f"    {kind.upper()} ({len(rows)}) — {note}")
        for prov, name, en, label, shelf, _id in sorted(rows):
            print(f"        [{prov}] {shelf:20s} {name} "
                  f"{('| ' + en) if en else ''}  ({label})")
    print(f"\n  STRAYS, the guard working: {len(strays)} name(s) carry a "
          f"declaring word as a TOPONYM and keep their own shelf —")
    bykind = {}
    for top, name, label in strays:
        bykind.setdefault(top, []).append(name)
    for top, names in sorted(bykind.items(), key=lambda kv: -len(kv[1])):
        print(f"    {top:10s} {len(names):3d}   {names[0]}")
    return found


def write_review_files(found):
    """The SPOT rows, per province, as the menu for a person. Deliberately not
    a shelves.json `--emit`: every other audit here can emit because its rule
    reads a trade off a sign (a salon says เสริมสวย and is one). A falls is a
    place in the landscape, and the same name sits on the park around it, the
    ranger office at its gate and the village down the road — so the sorting
    above is evidence for a person, not a verdict to paste."""
    for prov in ("cm", "cr"):
        rows = [r for r in (found.get("spot") or []) if r[0] == prov]
        held = [r for r in (found.get("container") or [])
                + (found.get("station") or []) if r[0] == prov]
        out = ROOT / "cache" / f"views_review_{prov}.txt"
        with out.open("w") as f:
            f.write(
                f"# {prov}: {len(rows)} record(s) whose NAME declares a view or a\n"
                f"# falls while sitting on a shelf a view-seeker never opens.\n"
                f"# A second shelf via data/curated/shelves.json is the additive\n"
                f"# move (nothing is re-keyed, nothing 404s) — but each row wants\n"
                f"# an eye first: the same name sits on the falls, the park around\n"
                f"# it and the ranger office at its gate.\n"
                f"# Generated by audit_views.py, zero network.\n#\n")
            for prov_, name, en, label, shelf, rid in sorted(rows):
                f.write(f"{rid:34s} [{shelf}] {name} {('| ' + en) if en else ''}"
                        f"   ({label})\n")
            f.write(f"\n# NOT candidates — held here so nobody re-finds them as a\n"
                    f"# gap: {len(held)} container(s) and station(s).\n")
            for prov_, name, en, label, shelf, rid in sorted(held):
                f.write(f"# {rid:32s} [{shelf}] {name}\n")
        print(f"  wrote {out.relative_to(ROOT)} ({len(rows)} candidates)")


def report_dupes(recs, write=False):
    """Two records for one waterfall, PROPOSED and never folded — the house
    rule from the school and medical registers. A container is not a
    duplicate of the thing inside it: วนอุทยานน้ำตกบัวตอง is the forest park
    that HOLDS น้ำตกบัวตอง, and folding them would lose one of two real
    places. Those are reported as neighbours, for a person to link."""
    band("DUPES", "waterfall records within 1.5 km — proposed, never folded")
    import math

    def metres(a, b):
        R = 6371000
        p1, p2 = math.radians(a[0]), math.radians(b[0])
        dp, dl = p2 - p1, math.radians(b[1] - a[1])
        x = (math.sin(dp / 2) ** 2
             + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2)
        return 2 * R * math.asin(math.sqrt(x))

    onshelf = [r for r in recs
               if "waterfall" in (r.get("sub") or []) and r.get("lat")]
    pairs = []
    for i, a in enumerate(onshelf):
        for b in onshelf[i + 1:]:
            if a.get("province") != b.get("province"):
                continue
            d = metres((a["lat"], a["lng"]), (b["lat"], b["lng"]))
            if d < 1500:
                pairs.append((d, a, b))
    print(f"  {len(pairs)} pair(s) on the waterfall shelf itself:")
    for d, a, b in sorted(pairs):
        print(f"    {d:6.0f} m  {a.get('name')}  [{a['id']}]")
        print(f"             {b.get('name')}  [{b['id']}]")
    if write:
        for prov in ("cm", "cr"):
            rows = [(d, a, b) for d, a, b in pairs if a.get("province") == prov]
            out = ROOT / "cache" / f"views_dupes_{prov}.txt"
            with out.open("w") as f:
                f.write(
                    f"# {prov}: {len(rows)} candidate duplicate pair(s) on the\n"
                    f"# waterfall shelf, within 1.5 km. PROPOSED, NEVER FOLDED —\n"
                    f"# which id to keep is a real choice (one side may hold the\n"
                    f"# Thai name, the other the English one or the better pin),\n"
                    f"# and it is human-confirmed pairs only. Paste a\n"
                    f"# settled pair into data/curated/merges.json.\n"
                    f"# A CONTAINER IS NOT A DUPLICATE: a forest park that holds a\n"
                    f"# falls is its own place. Generated by audit_views.py.\n#\n")
                for d, a, b in sorted(rows):
                    f.write(f'{{"keep": "{a["id"]}", "fold": "{b["id"]}"}}'
                            f'   # {d:.0f} m — {a.get("name")} / {b.get("name")}\n')
            print(f"  wrote {out.relative_to(ROOT)} ({len(rows)} pairs)")
    return pairs


def report_never(recs):
    band("NEVER", "what no crawl has asked and who is absent because of it")
    qtext = (ROOT / "importers" / "crawl_overpass.py").read_text()
    for sel in ('waterway"="waterfall', 'natural"="peak', 'natural"="cliff',
                'natural"="stone', 'mountain_pass'):
        state = "asked" if sel in qtext else "NEVER ASKED"
        print(f"  {sel:28s} {state}")
    print()
    print("  A ROLL, not a census — the census is HIDING above. Kept because a"
          "\n  name every reader of these provinces would try first is worth"
          "\n  asking about by hand."
          "\n\n  PRESENT IS NOT FINDABLE, and this roll said so wrongly at first:"
          "\n  ภูชี้ฟ้า read `present` while being two register rows with no pin"
          "\n  and no shelf child between them — a reader searching the name gets"
          "\n  it, a reader browsing viewpoints never does. So each name reports"
          "\n  what it would actually take to walk there.")
    for f in FAMOUS:
        hits = [r for r in recs if f in name_of(r)]
        if not hits:
            print(f"  {f:18s} ABSENT")
            continue
        shelved = [r for r in hits if set(r.get("sub") or []) & ON_SHELF]
        pinned = [r for r in hits if r.get("lat")]
        best = (shelved or hits)[0]
        where = "+".join(best.get("cat") or [])
        marks = []
        if not shelved:
            marks.append("on no view shelf")
        if not pinned:
            marks.append("NO PIN")
        if len(hits) > 1:
            marks.append(f"{len(hits)} records")
        tail = ("  — " + ", ".join(marks)) if marks else ""
        state = "findable" if (shelved and pinned) else "present"
        print(f"  {f:18s} {state:9s} ({where}){tail}")


def write_claims_files(bycat, recs):
    for prov in ("cm", "cr"):
        rows = []
        for r in recs:
            if "viewpoint" in (r.get("sub") or []) or r.get("province") != prov:
                continue
            n = name_of(r)
            # same selection as report_claims: VIEW_CLAIM self-fences วิวัฒน์
            # by lookahead, so one test is the whole rule
            if VIEW_CLAIM.search(n):
                rows.append((r.get("id"), r.get("name") or r.get("nameEn"),
                             "+".join(r.get("cat") or [])))
        out = ROOT / "cache" / f"views_claims_{prov}.txt"
        with out.open("w") as f:
            f.write(f"# {prov}: {len(rows)} records whose NAME claims a view, for the\n"
                    f"# future cross-shelf `view` tag (WO-15 machinery). A name is the\n"
                    f"# venue's own claim; the tag would say so (ชื่อบอกวิว) and never\n"
                    f"# verify it. Generated by audit_views.py, zero network.\n#\n")
            for rid, name, cat in sorted(rows, key=lambda x: x[2]):
                f.write(f"{rid:40s} [{cat}] {name}\n")
        print(f"  wrote {out.relative_to(ROOT)} ({len(rows)} rows)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--claims", action="store_true",
                    help="also write cache/views_claims_<prov>.txt")
    ap.add_argument("--dupes", action="store_true",
                    help="also write cache/views_dupes_<prov>.txt")
    args = ap.parse_args()
    recs = load_records()
    print(f"catalogue: {len(recs)} records")
    report_shelf(recs)
    report_dropped()
    report_menu()
    found = report_hiding(recs)
    report_dupes(recs, write=args.dupes)
    bycat = report_claims(recs)
    report_never(recs)
    if args.claims or args.dupes:
        band("WRITE")
        write_review_files(found)
        if args.claims:
            write_claims_files(bycat, recs)


if __name__ == "__main__":
    sys.exit(main())
