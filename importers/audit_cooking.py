#!/usr/bin/env python3
"""Read the cooking-class records' own names for what they declare. Zero network.

Same contract as audit_muaythai.py, audit_culture.py and audit_massage.py: this
never edits canonical data. It reports, and --emit prints shelves.json-ready
entries for a human to look at before pasting. Every proposed entry carries
`source: "osm name: <name>"` or `source: "osm sub: cooking"` — the claim is the
place's own, read off the sign it chose, or the crawl's own reading of that sign.

The measurement that asked for this (notes/cooking-classes-proposal-2026-08-19.md):
Thai cooking classes lived on SEVEN shelves, split by how a mapper tagged the
door — nine on school/cooking (found by NAME: the OSM tag amenity=cooking_school
is on ZERO elements in both provinces, census 2026-08-07, and the schools crawl
group never asks for it), nine on food/thai between the restaurants (Siam
Garden Cooking School, Zabb-E-Lee Thai Cooking School, Thai Akha Cooking
School…), two on food/vegetarian (May Kaidee), three on school/training, one on
school/music-art (Gap's Thai CULINARY ART School, sent there by "art school"),
one on repair/auto (Siam Rice — Thai cookery school), and Chiang Rai held none
at all. WO-14 adds a `cooking` cat with nine children and a record reaches it by
gaining a SECOND cat through shelves.json. Nothing is re-keyed; nothing 404s.

Reports, one per child that a NAME can fill, then the guards:

  CLASS     cooking school / cookery / culinary / สอนทำอาหาร — plus everything the
            crawl already filed as school/cooking, which is the same claim made
            by the classifier rather than by this script. A Latin name whose
            own word is "Cooking" (Cooking Love, Pantawan Cooking) counts: a
            restaurant calls itself kitchen or cuisine, a class calls itself
            cooking — the muay analogue of a gym whose sign says Boxing.
  FARM      organic / farm / garden / ฟาร์ม / ออร์แกนิก — only on a record that
            is a class. A farm that teaches nothing is a farm.
  HOME      home / @home — only on a class. บ้าน is NEVER a rule: it opens
            several thousand Thai business names (BaanThai Cookery School is
            a school, not a home), the same discipline as bare มวย.
  VEGAN     vegan / vegetarian / มังสวิรัติ / วีแกน / อาหารเจ — only on a class.
            Bare เจ is never a rule (เจ๊, เจริญ, เจดีย์).
  NORTHERN  northern / lanna / ล้านนา / อาหารเหนือ / akha อาข่า / shan ไทใหญ่ /
            karen กะเหรี่ยง / hmong ม้ง / lahu ลาหู่ / lisu ลีซู — only on a class.
  DESSERT   ขนมไทย / dessert — only on a class. Expected near zero by name: a
            dessert course is a line on a school's menu, not on its sign.
  CARVING   แกะสลัก / carving — only on a class. Wood's Carving College Home
            Stay and the Ban Tawai wood-carving village are carving and not
            cooking; the class-only guard keeps them off.
  VOCATIONAL สารพัดช่าง / อาชีวศึกษา / คหกรรม / พัฒนาฝีมือแรงงาน / polytechnic /
            vocational — reported, NEVER proposed. A polytechnic's name says
            "all trades", not "food"; whether its short courses include อาหาร
            is its own page's word, and that page is what enters.
  HOTEL     no name rule at all. A hotel whose own site states a cooking school
            reaches the shelf through shelves.json with that site as source.
  STRAYS    names holding cook/carving that are NOT classes — Cooked Shrimp,
            Little Cook Cafe, "Cook Dee Guesthouse" (a typo for Chok Dee),
            the bakeries — printed so the guard can be seen working.
  LEADS     a name that says only "Cook" (Smart Cook, Cook with Love,
            B Samcook), or a mapper's description that says cooking class
            while the name does not. Listed for a person; never proposed.

What this deliberately does NOT do:

  * Guess. A name that declares nothing produces nothing. Absent is not false.
  * Sort classes into tourist and real, school and activity. A kitchen whose
    sign says Cooking School is a cooking school; what its licence says is a
    door question (the `cooking` facet set asks it, nobody infers it).
  * Infer sessions, prices or pickup. Those are the school's own statements
    and live on the record (attrs.classSessions etc., via enrich.json) or in
    data/curated/cooking_classes.json, each with its source and date.

Usage:
  python3 importers/audit_cooking.py             # all reports
  python3 importers/audit_cooking.py --only farm
  python3 importers/audit_cooking.py --emit      # shelves.json-ready JSON
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANON = ROOT / "data" / "canonical"
SHELVES = ROOT / "data" / "curated" / "shelves.json"

# Thai needs no word boundary; Latin does. Every Thai term is a compound.
CLASS_RULES = [
    ("class", r"cooking\s+(?:school|class|classes|studio|centre|center|course|academy)"
              r"|\bcookery\b|\bculinary\b|สอนทำอาหาร|สอนอาหาร|โรงเรียนอาหาร"
              r"|คลาสทำอาหาร|เรียนทำอาหาร|คุ้กกิ้งสคูล|คุกกิ้งสคูล"
              # A business whose own word is Cooking. Not "cook", not "cooked",
              # not "cooking" inside another word — "Cooking Love" yes,
              # "Little Cook Cafe" no, "B Samcook" no.
              r"|\bcooking\b"),
]
FARM_RULES = [("farm", r"\borganic\b|\bfarm\b|\bgarden\b|ฟาร์ม|ออร์แกนิก|ออร์แกนิค")]
HOME_RULES = [("home", r"\bhome\b|@home")]
VEGAN_RULES = [("vegan", r"\bvegan\b|\bvegetarian\b|มังสวิรัติ|วีแกน|อาหารเจ")]
NORTHERN_RULES = [("northern", r"\bnorthern\b|\blanna\b|ล้านนา|อาหารเหนือ|\bakha\b|อาข่า"
                               r"|\bshan\b|ไทใหญ่|ไทยใหญ่|\bkaren\b|กะเหรี่ยง|ปกาเกอะญอ"
                               r"|\bhmong\b|ม้ง|\blahu\b|ลาหู่|\blisu\b|ลีซู")]
DESSERT_RULES = [("dessert", r"ขนมไทย|\bdesserts?\b|\bsweets\b")]
CARVING_RULES = [("carving", r"แกะสลัก|\bcarving\b")]
VOCATIONAL_RE = re.compile(r"สารพัดช่าง|อาชีวศึกษา|คหกรรม|พัฒนาฝีมือแรงงาน|\bpolytechnic\b"
                           r"|\bvocational\b", re.I)
# A name that holds the word cook (Smart Cook, Cook with Love, B Samcook)
# without saying cooking — shown as a lead, never matched. "Cooked" and
# "cookie" are neither.
LEAD_RE = re.compile(r"\bcook\b|cook\b", re.I)
STRAY_RE = re.compile(r"cook|carving|แกะสลัก", re.I)


def load():
    recs = []
    for f in ("cm.json", "cr.json"):
        recs += json.loads((CANON / f).read_text())
    return recs


def name_of(r):
    return " ".join(str(x) for x in (r.get("name"), r.get("nameTh"), r.get("nameEn")) if x)


def read_name(rules, r):
    """Keys the record's own name declares. Empty is a fine answer."""
    n = name_of(r).lower()
    return [k for k, pat in rules if re.search(pat, n, re.I)]


def is_class(r):
    if "cooking" in (r.get("sub") or []):
        return True
    if "cooking" in (r.get("cat") or []):
        return True  # curated records arrive on the shelf already
    return bool(read_name(CLASS_RULES, r))


def child_subs(r):
    """Every child the NAME earns, on a record that is a class. The class-only
    guard is the whole point: Ban Tawai carves wood and teaches nobody."""
    if not is_class(r):
        return []
    subs = ["class"]
    for rules in (FARM_RULES, HOME_RULES, VEGAN_RULES, NORTHERN_RULES,
                  DESSERT_RULES, CARVING_RULES):
        subs += read_name(rules, r)
    return subs


def shelf_of(r):
    return "/".join(((r.get("cat") or ["?"])[0], (r.get("sub") or ["-"])[0]))


def band(title, note=""):
    print()
    print("=" * 72)
    print(title)
    if note:
        print(note)
    print("=" * 72)


def line(r, extra=""):
    a = r.get("attrs") or {}
    reach = "☎" if (r.get("phone") or a.get("lineId")) else "·"
    web = "🌐" if r.get("website") else "·"
    print(f"  {reach}{web} {r['id']:<34} {shelf_of(r):<18} {name_of(r)[:50]}{extra}")


def report_child(recs, key, title, note):
    hits = [r for r in recs if key in child_subs(r)]
    band(f"{title} — {len(hits)} record(s)", note)
    by = {}
    for r in hits:
        by.setdefault(shelf_of(r), []).append(r)
    for shelf in sorted(by):
        print(f"\n  on {shelf} ({len(by[shelf])}):")
        for r in by[shelf]:
            why = "sub" if "cooking" in (r.get("sub") or []) else "name"
            line(r, f"   [{why}]" + ("" if "cooking" in (r.get("cat") or []) else "   ← not yet on cooking"))
    if key == "class":
        contactable = sum(1 for r in hits if r.get("phone") or (r.get("attrs") or {}).get("lineId"))
        print(f"\n  contactable {contactable}/{len(hits)} — the door survey's first errand.")


def report_vocational(recs):
    hits = [r for r in recs if VOCATIONAL_RE.search(name_of(r))]
    band(f"VOCATIONAL — {len(hits)} record(s) whose name says polytechnic / อาชีวะ / คหกรรม / DSD",
         "Reported, never proposed: the name says 'all trades', not 'food'. Each\n"
         "reaches the shelf only through its own page saying it teaches อาหาร.")
    for r in hits:
        line(r)


def report_strays(recs):
    hits = [r for r in recs if STRAY_RE.search(name_of(r)) and not is_class(r)
            and not LEAD_RE.search(name_of(r))]
    band(f"STRAYS — {len(hits)} record(s) holding cook/carving that are not classes",
         "Printed so the guard is visible. None of these is proposed for anything.")
    for r in hits:
        line(r)


def report_leads(recs):
    """Names that say only Cook, and descriptions that say cooking class while
    the name does not. A description is the mapper's sentence, not the sign,
    so nothing here is proposed — it is the list a person checks."""
    desc_re = re.compile(r"cooking (?:class|school|course)|สอนทำอาหาร|คลาสทำอาหาร", re.I)
    hits = []
    for r in recs:
        if is_class(r):
            continue
        n = name_of(r)
        a = r.get("attrs") or {}
        if LEAD_RE.search(n) and not re.search(r"\bcooked\b|cookie", n, re.I):
            hits.append((r, "name says Cook"))
        elif desc_re.search(str(a.get("description") or "") + " " + str(a.get("descriptionTh") or "")):
            hits.append((r, "description says cooking class"))
    band(f"LEADS — {len(hits)} record(s) a person should look at",
         "Not proposed. A bare Cook is a cafe as often as a school; the sign decides.")
    for r, why in hits:
        line(r, f"   [{why}]")


def sub_to_cat():
    """{sub -> cat} read off data/categories.json, never hardcoded here."""
    cats = json.loads((ROOT / "data" / "categories.json").read_text())
    out = {}
    for c in cats["categories"]:
        for ch in c.get("children", []):
            sub = (ch.get("match") or {}).get("sub")
            if sub:
                out.setdefault(sub, c["key"])
    return out


def emit(recs):
    """shelves.json-ready entries. Names and the crawl's own sub only."""
    already = json.loads(SHELVES.read_text())["shelves"]
    out = {}
    for r in recs:
        if "cooking" in (r.get("cat") or []):
            continue  # curated cooking records arrive on the shelf already
        subs = child_subs(r)
        if not subs:
            continue
        prior = already.get(r["id"]) or {}
        if set(subs) <= set(prior.get("add_sub") or []) and "cooking" in (prior.get("add_cat") or []):
            continue
        by_sub = "cooking" in (r.get("sub") or [])
        why = ("the crawl's own sub cooking" if by_sub else "a cooking class, read off its own name")
        extra = [s for s in subs if s != "class"]
        if extra:
            why += " — " + ", ".join(extra) + " by name"
        out[r["id"]] = {
            "note": f"{r.get('name')} — {why}",
            "add_cat": ["cooking"],
            "add_sub": sorted(set(subs)),
            "source": ("osm sub: cooking" if by_sub else f"osm name: {name_of(r)}"),
            "fetched": r.get("updatedAt", ""),
        }
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()


REPORTS = ["class", "farm", "home", "vegan", "northern", "dessert", "carving",
           "vocational", "strays", "leads"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit", action="store_true",
                    help="print shelves.json-ready entries instead of a report")
    ap.add_argument("--only", choices=REPORTS, help="run one report")
    args = ap.parse_args()

    recs = load()
    if args.emit:
        emit(recs)
        return

    print(f"cooking-class audit — {len(recs)} records in cm + cr")
    run = args.only
    titles = {
        "class": ("CLASS — cooking school / cookery / culinary / Cooking by name, or the crawl's sub",
                  "Seven shelves today, split by the mapper's tag. The cooking shelf is the\n"
                  "second cat each gains; school/cooking and food/thai keep every record."),
        "farm": ("FARM — organic / farm / garden, on a class", "A farm that teaches nothing is a farm and stays off."),
        "home": ("HOME — home / @home, on a class", "บ้าน is never a rule."),
        "vegan": ("VEGAN — vegan / vegetarian / มังสวิรัติ, on a class", "Bare เจ is never a rule."),
        "northern": ("NORTHERN — northern / lanna / akha / shan…, on a class", ""),
        "dessert": ("DESSERT — ขนมไทย / dessert, on a class",
                    "Expected near zero by name; a dessert course is a menu line, not a sign."),
        "carving": ("CARVING — แกะสลัก / carving, on a class",
                    "Wood carving is carving and not cooking; the class-only guard keeps it off."),
    }
    for key in REPORTS[:7]:
        if run in (None, key):
            report_child(recs, key, *titles[key])
    if run in (None, "vocational"):
        report_vocational(recs)
    if run in (None, "strays"):
        report_strays(recs)
    if run in (None, "leads"):
        report_leads(recs)
    print()
    print("Nothing above has been written anywhere. --emit proposes; a human pastes.")


if __name__ == "__main__":
    main()
