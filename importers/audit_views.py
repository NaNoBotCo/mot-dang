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
    vp = [r for r in recs if "viewpoint" in (r.get("sub") or [])]
    band("SHELF", "sub=viewpoint today")
    for prov in ("cm", "cr"):
        rows = [r for r in vp if r.get("province") == prov]
        contact = sum(1 for r in rows if r.get("phone") or r.get("website"))
        photo = sum(1 for r in rows if r.get("photo"))
        hours = sum(1 for r in rows if r.get("hours"))
        bare = sum(1 for r in rows if re.fullmatch(
            r"จุดชมวิว|viewpoint|sunset", (r.get("name") or "").strip(), re.I))
        print(f"  {prov}: {len(rows)} records — contactable {contact}, "
              f"photo {photo}, hours {hours}, bare-named {bare}")
    print("  The imbalance is crawl geometry: cr is in WIDE_PROVINCES (asked"
          "\n  province-wide); cm's culture group has only ever been asked on"
          "\n  the near ring, and the views of Chiang Mai are on the doi.")
    return vp


def report_dropped():
    band("DROPPED", "tags on cached tourism=viewpoint elements import does not keep")
    for prov, els in cached_elements("culture").items():
        vps = [e for e in els if (e.get("tags") or {}).get("tourism") == "viewpoint"]
        named = [e for e in vps if element_name(e.get("tags", {}))]
        keys = {}
        for e in vps:
            for k in ("direction", "ele", "description", "description:en", "wikidata"):
                if k in (e.get("tags") or {}):
                    keys[k] = keys.get(k, 0) + 1
        print(f"  {prov}: {len(vps)} viewpoint elements cached, {len(named)} named "
              f"({len(vps) - len(named)} nameless — skipped by the "
              f"no-shelf-for-the-nameless rule)")
        if keys:
            print(f"      recoverable: " + ", ".join(
                f"{k} ×{n}" for k, n in sorted(keys.items())))


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


def report_never(recs):
    band("NEVER", "what no crawl has asked and who is absent because of it")
    qtext = (ROOT / "importers" / "crawl_overpass.py").read_text()
    for sel in ('waterway"="waterfall', 'natural"="peak', 'natural"="cliff',
                'natural"="stone', 'mountain_pass'):
        state = "asked" if sel in qtext else "NEVER ASKED"
        print(f"  {sel:28s} {state}")
    print()
    names = {name_of(r): r for r in recs}
    joined = " ".join(names)
    for f in FAMOUS:
        if f in joined:
            hit = next((r for n, r in names.items() if f in n), None)
            where = "+".join(hit.get("cat") or []) if hit else "?"
            print(f"  {f:18s} present  ({where})")
        else:
            print(f"  {f:18s} ABSENT")


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
    args = ap.parse_args()
    recs = load_records()
    print(f"catalogue: {len(recs)} records")
    report_shelf(recs)
    report_dropped()
    report_menu()
    bycat = report_claims(recs)
    report_never(recs)
    if args.claims:
        band("WRITE")
        write_claims_files(bycat, recs)


if __name__ == "__main__":
    sys.exit(main())
