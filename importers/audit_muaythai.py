#!/usr/bin/env python3
"""Read the muay thai records' own names for what they declare. Zero network.

Same contract as audit_culture.py and audit_massage.py: this never edits
canonical data. It reports, and --emit prints shelves.json-ready entries for a
human to look at before pasting. Every proposed entry carries `source: "osm
name: <name>"` or `source: "osm sub: muaythai"` — the claim is the place's own,
read off the sign it chose, or the crawl's own reading of that sign.

The measurement that asked for this (notes/muay-thai-proposal-2026-08-19.md):
muay thai lived on TWO shelves, split by how a mapper tagged the door —
school/muaythai (ค่ายมวย, 14, found by name because sport=muay_thai is ZERO in
OpenStreetMap across both provinces) and learn/gym (มวยไทย-ยิม, where Hong Thong
and Santai sit between fitness centres) — with one stadium filed as a camp and
no stadium shelf to be empty on. WO-12 adds a `muaythai` cat with three
children, stadium / camp / gear, and a record reaches it by gaining a SECOND cat
through shelves.json. Nothing is re-keyed; nothing 404s.

Five reports:

  STADIUM  names that say stadium / สนามมวย / เวทีมวย. One today (Kawila), on
           the camps shelf, which is why the report exists.
  CAMP     ค่ายมวย, มวยไทย, muay thai, boxing gym/camp/club — plus everything the
           crawl already filed as school/muaythai, which is the same claim made
           by the classifier rather than by this script.
  GEAR     นวม, กางเกงมวย, the glove brands. Expected ZERO: no shelf has ever
           asked, so the only gear shop that can exist today is one crawled
           under some other tag.
  STRAYS   names holding มวย that are NOT muay — หมวย is an ordinary nickname
           (เจ๊หมวย ผัดไทย, ก๋วยเตี๋ยวเรือพี่หมวย) — printed so the guard can be
           seen working. Same discipline as the กระท่อม hut guard.
  LEADS    a mapper's description says muay thai, the name does not (Go gym
           on Huay Kaew). Listed for a person; never proposed.

What this deliberately does NOT do:

  * Guess. A name that declares nothing produces nothing. Absent is not false.
  * Sort camps into real and touristic, fighters' gyms and fitness gyms. A gym
    whose own sign says Boxing offers boxing; what its ring is like is a door
    question.
  * Infer fight nights, prices or drop-in rules. Those are the venue's own
    statements and live on the record (attrs.fightNights etc.) or in
    data/curated/fight_nights.json, each with its source.

Usage:
  python3 importers/audit_muaythai.py             # all five reports
  python3 importers/audit_muaythai.py --only camp
  python3 importers/audit_muaythai.py --emit      # shelves.json-ready JSON
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANON = ROOT / "data" / "canonical"
SHELVES = ROOT / "data" / "curated" / "shelves.json"

# Thai needs no word boundary; Latin does. Bare มวย is NEVER a rule: หมวย is a
# nickname and มวยผม is a hair bun. Every Thai term is a compound.
STADIUM_RULES = [
    ("stadium", r"boxing\s+stadium|muay\s*thai\s+stadium|สนามมวย|เวทีมวย"),
]
CAMP_RULES = [
    ("camp", r"muay\s*thai|muaythai|มวยไทย|ค่ายมวย|ยิมมวย|"
             r"\bboxing\s+(gym|camp|club|school)\b|\bkick\s*boxing\b|\bboxing\b"),
]
GEAR_RULES = [
    ("gear", r"ร้านนวม|กางเกงมวย|อุปกรณ์มวย|muay\s*thai\s+shop|boxing\s+shop|"
             r"\bfairtex\b|\btwins\s+special\b|\btop\s+king\b|\byokkao\b"),
]
# A name that holds มวย only because it holds หมวย — shown, never matched.
STRAY_RE = re.compile(r"หมวย")


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


def is_stadium(r):
    return bool(read_name(STADIUM_RULES, r))


def is_camp(r):
    # The stadium rule wins: Kawila Boxing Stadium says boxing, and is not a camp.
    if is_stadium(r):
        return False
    if "muaythai" in (r.get("sub") or []):
        return True
    return bool(read_name(CAMP_RULES, r))


def is_gear(r):
    return bool(read_name(GEAR_RULES, r))


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


def report_stadium(recs):
    hits = [r for r in recs if is_stadium(r)]
    band(f"STADIUM — {len(hits)} record(s) whose name says stadium",
         "A stadium on the camps shelf is a misfile the additive move cannot undo;\n"
         "it can only give the place a second, right shelf. The curated stadiums\n"
         "(data/curated/additions-chiang-mai.json) arrive already on muaythai/stadium.")
    for r in hits:
        line(r, "" if "muaythai" in (r.get("cat") or []) else "   ← not yet on muaythai")


def report_camp(recs):
    hits = [r for r in recs if is_camp(r)]
    band(f"CAMP — {len(hits)} record(s): ค่ายมวย / muay thai / boxing gym by name or by the crawl's sub",
         "Two shelves today, split by the mapper's tag. The Muay Thai shelf is the\n"
         "second cat each gains; school/muaythai and learn/gym keep every record.")
    by = {}
    for r in hits:
        by.setdefault(shelf_of(r), []).append(r)
    for shelf in sorted(by):
        print(f"\n  on {shelf} ({len(by[shelf])}):")
        for r in by[shelf]:
            why = "sub" if "muaythai" in (r.get("sub") or []) else "name"
            line(r, f"   [{why}]")
    contactable = sum(1 for r in hits if r.get("phone") or (r.get("attrs") or {}).get("lineId"))
    print(f"\n  contactable {contactable}/{len(hits)} — the door survey's first errand.")


def report_gear(recs):
    hits = [r for r in recs if is_gear(r)]
    band(f"GEAR — {len(hits)} record(s) whose name says gloves, shorts or a glove brand",
         "No crawl group has ever asked for a muay thai shop, so zero here means\n"
         "'never looked', not 'none in town'. The shelf fills by name and by walk.")
    for r in hits:
        line(r)


def report_strays(recs):
    hits = [r for r in recs if STRAY_RE.search(name_of(r)) and not is_camp(r) and not is_stadium(r)]
    band(f"STRAYS — {len(hits)} record(s) holding มวย only because they hold หมวย",
         "Printed so the guard is visible. None of these is proposed for anything.")
    for r in hits:
        line(r)


def report_leads(recs):
    """Records whose mapper-written description says muay thai while the name
    does not. A description is the mapper's sentence, not the sign, so nothing
    here is proposed — it is the list a person checks before the shelf fills
    by name. Go gym is the example: the name says gym, the description says
    muay thai, and only a look at the door settles which shelf."""
    desc_re = re.compile(r"muay\s*thai|มวยไทย|ค่ายมวย|kick\s*boxing", re.I)
    hits = [r for r in recs
            if not is_camp(r) and not is_stadium(r)
            and desc_re.search(str((r.get("attrs") or {}).get("description") or "")
                               + " " + str((r.get("attrs") or {}).get("descriptionTh") or ""))]
    band(f"LEADS — {len(hits)} record(s) whose description says muay thai and whose name does not",
         "Not proposed. A description is the mapper's sentence; the sign decides.")
    for r in hits:
        line(r)


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
    owner = sub_to_cat()
    out = {}

    def add(r, subs, why, src):
        if not subs:
            return
        prior = already.get(r["id"]) or {}
        # Already on the shelf with this sub: nothing to propose.
        if set(subs) <= set(prior.get("add_sub") or []):
            return
        e = out.setdefault(r["id"], {"note": f"{r.get('name')} — {why}",
                                     "add_cat": [], "add_sub": [], "source": src,
                                     "fetched": r.get("updatedAt", "")})
        e["add_sub"] = sorted(set(e["add_sub"]) | set(subs))
        want = {owner[s] for s in subs if s in owner} - set(r.get("cat") or [])
        e["add_cat"] = sorted(set(e["add_cat"]) | want)

    for r in recs:
        if "muaythai" in (r.get("cat") or []) and not is_stadium(r):
            continue  # curated muay thai records arrive on the shelf already
        if is_stadium(r):
            add(r, ["stadium"], "a stadium, read off its own name", f"osm name: {name_of(r)}")
        elif is_camp(r):
            why = ("the crawl's own sub muaythai" if "muaythai" in (r.get("sub") or [])
                   else "muay thai / boxing read off its own name")
            src = ("osm sub: muaythai" if "muaythai" in (r.get("sub") or [])
                   else f"osm name: {name_of(r)}")
            add(r, ["camp"], why, src)
        if is_gear(r):
            add(r, ["gear"], "gear read off its own name", f"osm name: {name_of(r)}")

    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit", action="store_true",
                    help="print shelves.json-ready entries instead of a report")
    ap.add_argument("--only", choices=("stadium", "camp", "gear", "strays", "leads"),
                    help="run one report")
    args = ap.parse_args()

    recs = load()
    if args.emit:
        emit(recs)
        return

    print(f"muay thai audit — {len(recs)} records in cm + cr")
    run = args.only
    if run in (None, "stadium"):
        report_stadium(recs)
    if run in (None, "camp"):
        report_camp(recs)
    if run in (None, "gear"):
        report_gear(recs)
    if run in (None, "strays"):
        report_strays(recs)
    if run in (None, "leads"):
        report_leads(recs)
    print()
    print("Nothing above has been written anywhere. --emit proposes; a human pastes.")


if __name__ == "__main__":
    main()
