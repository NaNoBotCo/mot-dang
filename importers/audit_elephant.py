#!/usr/bin/env python3
"""Read the catalogue's own names for what they declare about elephants. Zero network.

Same contract as audit_muaythai.py and audit_massage.py: this never edits
canonical data. It reports, and --emit prints shelves.json-ready entries for a
human to look at before pasting. Every proposed entry carries `source: "osm
name: <name>"` — the claim is the place's own, read off the sign it chose.

The measurement that asked for this (notes/elephant-proposal-2026-08-19.md):
on 2026-08-19, of 16,268 records, 66 carried ช้าง or "elephant" in their name
and NOT ONE was an elephant camp — no query group in crawl_overpass.py had
ever asked for tourism=zoo, tourism=attraction or tourism=theme_park, so
Maesa, Elephant Nature Park, Patara and the Mae Taeng and Mae Wang valleys —
the busiest elephant country in the kingdom — had never been fetched. The 66
were the city's elephant NAMES (ช้างเผือก, ช้างคลาน, ช้างม่อย, ล่ามช้าง,
ดอยช้าง…), one poo-paper park, a resort named for a sanctuary, and a handful
of restaurants called Golden Elephant. WO-19 added a `chang` cat with three
children, camp / care / craft; a camp reaches it through data/curated/ (its
own page, dated), through shelves.json (its own name), or — since the
`elephants` crawl group landed on 2026-08-20 (Nan's go) — through
import_overpass.chang_hit(), which reads THIS FILE's name rules against that
one group's elements and sends everything else the attraction dragnet caught
to cache/elephant_review_<prov>.txt. Nothing is re-keyed; nothing 404s.

Five reports:

  CAMP     names that say ปางช้าง / elephant camp / sanctuary / park / farm /
           rescue / nature park — AND whose crawled shelf is not lodging,
           food or drink. A hostel called Elephant Home is a hostel; a resort
           "and Elephant Sanctuary" is a resort with a camp beside it (a lead,
           below), and the camp enters from its own page or, since the
           2026-08-20 crawl, from the `elephants` group via chang_hit().
  CARE     elephant hospital / clinic / โรงพยาบาลช้าง / สถาบันคชบาล by name.
           Expected zero inside the two provinces: the hospital and the
           institute are in Lampang.
  CRAFT    of-the-elephant, not with-the-elephant: poo-paper, Elephant Parade,
           elephant carving named as such.
  NAMES    every record whose name holds ช้าง / elephant that is NONE of the
           above, grouped by the name-element it holds — ช้างเผือก (the white
           elephant: gate, quarter, hospital, hotel), ช้างคลาน (the kneeling
           elephant: the Night Bazaar quarter), ช้างม่อย, ล่ามช้าง (the
           tethered elephants), ช้างค้ำ/ช้างคำ, พวกช้าง (the elephant corps),
           ดอยช้าง, เกาะช้าง, กื้ดช้าง, แช่ช้าง, โรงช้าง, หนองอาบช้าง (the
           elephant-bathing pond)… This is the map of where elephants WERE,
           and it is data for /chang.html, not a mistake to clean up. A place
           called Golden Elephant or Uncle Chang (ลุงช้าง is a nickname) is
           printed here too, so the guard can be seen working.
  LEADS    a description says elephant and the name does not; or the name says
           sanctuary/camp and the mapper filed a hotel or guesthouse. Listed
           for a person; never proposed.

What this deliberately does NOT do:

  * Guess. A name that declares nothing produces nothing. Absent is not false.
  * Sort camps into ethical and unethical, sanctuary and show. Those words are
    a venue's own and render as the venue's own, on the record, with a date.
  * Infer riding, bathing, hooks, chains, numbers or prices. Those are the
    venue's own statements and live on the record (attrs.elephantProgram etc.)
    or in data/curated/elephants.json, each with its source.

Usage:
  python3 importers/audit_elephant.py             # all five reports
  python3 importers/audit_elephant.py --only names
  python3 importers/audit_elephant.py --emit      # shelves.json-ready JSON
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANON = ROOT / "data" / "canonical"
SHELVES = ROOT / "data" / "curated" / "shelves.json"

# Thai needs no word boundary; Latin does. Bare ช้าง is NEVER a rule: it is a
# nickname (ลุงช้าง), a beer, half the city's quarter names, and — with the
# other tone mark — ช่าง, a craftsman. Every rule is a compound. Note ช้าง
# (mai tho) and ช่าง (mai ek) are different strings, so the craftsman never
# matches; the guard that matters is the place-name one.
# `adventure`, `pride` and ศูนย์ฝึกช้าง joined on 2026-08-20, each against a
# named witness from the first `elephants` crawl — Elephant Adventure
# Sanctuary (node 6251299685), Elephant Pride Sanctuary (node 5794234254) and
# ศูนย์ฝึกช้างเชียงดาว (way 348496839, which is the Chiang Dao centre the
# curated shelf already held as needs-pin). Verified the way an alias is
# ([[project-wichaa-article-pass]]): by listing the rows each new word
# matches, not by watching a count go up. "Maetaman Elephant Adventure" is
# the other real match for `adventure`; neither word reaches any lodging or
# food name in canonical.
CAMP_RULES = [
    ("elephant-camp",
     r"ปางช้าง|ศูนย์ช้าง|หมู่บ้านช้าง|ค่ายช้าง|ศูนย์อนุรักษ์ช้าง|ศูนย์ฝึกช้าง|"
     r"\belephant\s+(camp|sanctuary|park|farm|rescue|retirement|nature\s+park|"
     r"jungle|valley|experience|village|haven|freedom|kingdom|care|home|hill|"
     r"highlands?|discovery|conservation|project|centre|center|"
     r"adventure|pride)\b|"
     r"\b(sanctuary|camp)\s+(for|of)\s+elephants?\b|\bmahout\b"),
]
# โรงพยาบาลช้างเผือก is Chang Phueak Hospital — a hospital for PEOPLE in the
# white-elephant quarter — and it begins with the letters โรงพยาบาลช้าง. The
# fence is เผือก, the same shape as the จังหวัด/วัด trap in audit_culture.py.
CARE_RULES = [
    ("elephant-care", r"โรงพยาบาลช้าง(?!เผือก)|คลินิกช้าง|สถาบันคชบาล|\belephant\s+(hospital|clinic)\b"),
]
CRAFT_RULES = [
    ("elephant-craft", r"poo\s*poo\s*paper|poopoopaper|elephant\s+parade|elephant\s+dung|"
                       r"กระดาษมูลช้าง|กระดาษขี้ช้าง|แกะสลักช้าง|elephant\s+carving"),
]
# A hostel called Elephant Home is a hostel. The mapper's own tag is the
# reading we keep; the name goes to LEADS, not to the camp shelf.
LODGING_OR_FOOD = {"hotel", "food", "cannabis"}
ELE_RE = re.compile(r"elephant|ช้าง", re.I)
NAME_ELEMENTS = [
    ("ช้างเผือก", r"ช้างเผือก|chang\s*ph?ueak|chang\s*puak|chang\s*phuak|white\s+elephant"),
    ("ช้างคลาน", r"ช้างคลาน|chang\s*kh?lan|chiang\s*khlan"),
    ("ช้างม่อย", r"ช้างม่อย|chang\s*moi"),
    ("ล่ามช้าง", r"ล่ามช้าง|lam\s*chang"),
    ("ช้างค้ำ / ช้างคำ", r"ช้างค้ำ|ช้างคำ|chang\s*kham"),
    ("พวกช้าง", r"พวกช้าง|puak\s*chang"),
    ("หนานช้าง", r"หนานช้าง|nan\s*chang"),
    ("ช้างน้ำ", r"ช้างน้ำ|chang\s*nam"),
    ("ดอยช้าง", r"ดอยช้าง|doi\s*chaa?ng"),
    ("เกาะช้าง", r"เกาะช้าง|ko\s*chang"),
    ("กื้ดช้าง", r"กื้ดช้าง|kuet\s*chang|kued\s*chang"),
    ("แช่ช้าง", r"แช่ช้าง|chae\s*chang"),
    ("โรงช้าง", r"โรงช้าง|rong\s*chang"),
    ("หนองอาบช้าง", r"หนองอาบช้าง|nong\s*ap\s*chang"),
    ("บ้านช้าง / ช้างใน", r"บ้านช้าง|ช้างใน|ban\s*chang\b"),
    ("แม่ตาช้าง / โป่งช้าง / ช้างคด", r"แม่ตาช้าง|โป่งช้าง|ช้างคด|pong\s*chang"),
    ("ลุงช้าง (a nickname)", r"ลุงช้าง|พี่ช้าง|น้องช้าง|ป้าช้าง"),
    ("golden / black / white elephant (a shop name)", r"\b(golden|black|white|green|blue|red|silver)\s+elephant\b"),
]


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


def shelf_of(r):
    return "/".join(((r.get("cat") or ["?"])[0], (r.get("sub") or ["-"])[0]))


def top_cat(r):
    return (r.get("cat") or ["?"])[0]


def is_lodging_or_food(r):
    return top_cat(r) in LODGING_OR_FOOD


LODGING_WORD = re.compile(r"guest\s*house|hotel|hostel|resort|apartment|อพาร์ท|โรงแรม|รีสอร์ท", re.I)


def is_craft(r):
    # "Elephant parade guesthouse" (shop=crafts, east of the moat) may be the
    # Elephant Parade shop, a guesthouse, or both; the name holds a lodging word
    # and the sign is ambiguous, so it is a LEAD for a person, not a proposal.
    if LODGING_WORD.search(name_of(r)):
        return False
    return bool(read_name(CRAFT_RULES, r))


def is_craft_name_on_lodging_word(r):
    return bool(LODGING_WORD.search(name_of(r))) and bool(read_name(CRAFT_RULES, r))


def is_care(r):
    return bool(read_name(CARE_RULES, r))


def is_camp(r):
    # Craft wins (a poo-paper PARK is not a camp); the mapper's lodging/food
    # tag wins (the name goes to LEADS instead).
    if is_craft(r) or is_lodging_or_food(r):
        return False
    return bool(read_name(CAMP_RULES, r))


def is_camp_name_on_lodging(r):
    return is_lodging_or_food(r) and bool(read_name(CAMP_RULES, r))


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
    print(f"  {reach}{web} {r['id']:<34} {shelf_of(r):<22} {name_of(r)[:52]}{extra}")


def report_camp(recs):
    hits = [r for r in recs if is_camp(r)]
    band(f"CAMP — {len(hits)} record(s) whose name says elephant camp / sanctuary / park",
         "Two doors in: the venue's own page (data/curated/additions-chiang-mai.json,\n"
         "with a register row in elephants.json) and, since 2026-08-20, the `elephants`\n"
         "crawl group via chang_hit() — an OSM camp has a surveyed pin and no register\n"
         "row until somebody reads its pages. ← not-yet-on-chang below is the worklist.")
    for r in hits:
        line(r, "" if "chang" in (r.get("cat") or []) else "   ← not yet on chang")


def report_care(recs):
    hits = [r for r in recs if is_care(r)]
    band(f"CARE — {len(hits)} record(s) whose name says elephant hospital / clinic",
         "The national hospital (FAE, Hang Chat) and the institute (สถาบันคชบาลแห่งชาติ)\n"
         "are in Lampang, outside both provinces. A Chiang Mai camp that states a clinic\n"
         "on its own page enters through data/curated/ with that sub.")
    for r in hits:
        line(r)


def report_craft(recs):
    hits = [r for r in recs if is_craft(r)]
    band(f"CRAFT — {len(hits)} record(s) that are OF the elephant, not WITH it",
         "Poo-paper, Elephant Parade, carving named as such. These gain a second cat\n"
         "through shelves.json; the museum / crafts shelf keeps them.")
    for r in hits:
        line(r, "" if "chang" in (r.get("cat") or []) else "   ← not yet on chang")


def report_names(recs):
    hits = [r for r in recs if ELE_RE.search(name_of(r))
            and not is_camp(r) and not is_care(r) and not is_craft(r)]
    band(f"NAMES — {len(hits)} record(s) whose name holds ช้าง / elephant and is not a venue",
         "The city's elephant names. Grouped by the element each holds; data for\n"
         "/chang.html (the place-name section), never a shelf proposal.")
    by, rest = {}, []
    for r in hits:
        n = name_of(r)
        for label, pat in NAME_ELEMENTS:
            if re.search(pat, n, re.I):
                by.setdefault(label, []).append(r)
                break
        else:
            rest.append(r)
    for label, _ in NAME_ELEMENTS:
        if label in by:
            print(f"\n  {label} ({len(by[label])}):")
            for r in by[label]:
                line(r)
    if rest:
        print(f"\n  other ({len(rest)}):")
        for r in rest:
            line(r)


def report_leads(recs):
    """Records a person should look at before the shelf fills: a description
    that says elephant while the name does not; a name that says camp or
    sanctuary while the mapper filed lodging or food (Anantara's resort IS
    beside a camp; Baan Elephant Home is a hostel in Chang Khlan). The sign
    decides, and for these the sign is ambiguous."""
    desc_re = re.compile(r"elephant|ปางช้าง|ช้าง", re.I)
    by_desc = [r for r in recs
               if not is_camp(r) and not is_care(r) and not is_craft(r)
               and not ELE_RE.search(name_of(r))
               and desc_re.search(str((r.get("attrs") or {}).get("description") or "")
                                  + " " + str((r.get("attrs") or {}).get("descriptionTh") or ""))]
    on_lodging = [r for r in recs if is_camp_name_on_lodging(r)]
    craft_amb = [r for r in recs if is_craft_name_on_lodging_word(r)]
    band(f"LEADS — {len(by_desc)} by description, {len(on_lodging)} camp-named on a lodging/food shelf, "
         f"{len(craft_amb)} craft-named with a lodging word",
         "Not proposed. A description is the mapper's sentence; a resort's name may\n"
         "carry its camp's. Each enters, if at all, from its own page.")
    for r in by_desc:
        line(r, "   [description]")
    for r in on_lodging:
        line(r, "   [name says camp; mapper says " + top_cat(r) + "]")
    for r in craft_amb:
        line(r, "   [name says Elephant Parade AND a lodging word; which is it?]")


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
    """shelves.json-ready entries. Names only."""
    already = json.loads(SHELVES.read_text())["shelves"]
    owner = sub_to_cat()
    out = {}

    def add(r, subs, why, src):
        if not subs:
            return
        prior = already.get(r["id"]) or {}
        if set(subs) <= set(prior.get("add_sub") or []):
            return
        e = out.setdefault(r["id"], {"note": f"{r.get('name')} — {why}",
                                     "add_cat": [], "add_sub": [], "source": src,
                                     "fetched": r.get("updatedAt", "")})
        e["add_sub"] = sorted(set(e["add_sub"]) | set(subs))
        want = {owner[s] for s in subs if s in owner} - set(r.get("cat") or [])
        e["add_cat"] = sorted(set(e["add_cat"]) | want)

    for r in recs:
        if "chang" in (r.get("cat") or []):
            continue  # curated elephant records arrive on the shelf already
        if is_craft(r):
            add(r, ["elephant-craft"], "of the elephant, read off its own name", f"osm name: {name_of(r)}")
        elif is_care(r):
            add(r, ["elephant-care"], "elephant hospital / clinic, read off its own name", f"osm name: {name_of(r)}")
        elif is_camp(r):
            add(r, ["elephant-camp"], "elephant camp / sanctuary, read off its own name", f"osm name: {name_of(r)}")

    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit", action="store_true",
                    help="print shelves.json-ready entries instead of a report")
    ap.add_argument("--only", choices=("camp", "care", "craft", "names", "leads"),
                    help="run one report")
    args = ap.parse_args()

    recs = load()
    if args.emit:
        emit(recs)
        return

    print(f"elephant audit — {len(recs)} records in cm + cr")
    run = args.only
    if run in (None, "camp"):
        report_camp(recs)
    if run in (None, "care"):
        report_care(recs)
    if run in (None, "craft"):
        report_craft(recs)
    if run in (None, "names"):
        report_names(recs)
    if run in (None, "leads"):
        report_leads(recs)
    print()
    print("Nothing above has been written anywhere. --emit proposes; a human pastes.")


if __name__ == "__main__":
    main()
