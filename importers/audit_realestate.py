#!/usr/bin/env python3
"""Read the residential records' own names for what they declare. Zero network.

Same contract as audit_beauty.py and audit_muaythai.py: this never edits
canonical data. It reports. Unlike audit_beauty there is no --emit, and the
absence is deliberate: the correction this audit exists to watch happened at
classify() (importers/import_overpass.py, realestate_sub — receipt in
data/fixes.json, 2026-08-21), and everything else it finds is either a lead
for a person or a silence no shelves.json entry could fill.

The measurement that asked for this (notes/realestate-proposal-2026-08-21.md):

  THE CONDO SHELF HELD 316 BUILDINGS AND THE NAMES SAY CONDO ON 53. Every
  named building=apartments in both provinces was filed as sub "condo" and
  the shelf label read Condo Buildings. The other 263 are แมนชั่น, คอร์ท,
  อพาร์ตเมนต์ and หอพัก — the city's monthly buildings, which a reader
  hunting a condominium does not mean, and which the reader hunting a
  ห้องเช่า could not see under a condo label. Same class of error as the
  barber shelf (6 of 62): the truth was on the buildings' own signs, most
  of it in Thai.

  THE AGENT SHELF IS FIVE RECORDS IN A CITY FULL OF AGENCIES. OSM carries
  office=estate_agent on six elements in Chiang Mai (one was a building —
  retagged with its receipt). The census (cache/census/cm-office.csv) says
  that is all there is to crawl: the brokerage trade here lives on Facebook
  and LINE, not in OpenStreetMap. Growing this shelf is door work and
  curated records with sources, never a wider selector.

Reports:

  SPLIT       the four shelves after the 2026-08-21 correction, and the count
              of buildings whose name states nothing (filed apartment because
              that is the tag's own word — building=apartments — and it
              claims less than "condo" did). Recomputed against classify()'s
              own realestate_sub, so this report and the import cannot drift.
  AGENT       all agent rows, whole, every run — the shelf is small enough to
              read and two rows deserve a person's eye (below).
  MOOBAAN     หมู่บ้านจัดสรร names across the whole catalogue. The shelf is a
              NAMED SLOT without a match rule, on purpose — a rule matching
              zero records is the silently-empty-cafe bug and test_facets
              forbids it; the one-line wiring waits for records. This report
              says why there are none: the crawl never asked for
              landuse=residential, and the estate trade here does not put
              จัดสรร on OSM points. The names that DO carry หมู่บ้าน are
              villages — see STRAYS.
  HOTELSIDE   residence / mansion / court / apartment / serviced words on the
              hotel shelf. Counted, printed, never proposed: tourism=* is the
              venue stating a nightly trade, and a monthly word in the name
              is not evidence enough to argue with it. Chiang Mai is full of
              buildings that genuinely sell both. A person or the venue's own
              site settles each one; a rule cannot.
  LANDOFFICE  สำนักงานที่ดิน anywhere in the catalogue. Expected ZERO, and
              printed for the same reason audit_beauty prints its zeros: the
              one office every farang condo purchase walks through is not in
              the directory at all. That is a crawl-selector question
              (office=government) awaiting a numbered go, not a name rule.
  SILENCES    the words no building's sign can say: furnished, pets, the
              per-unit electric rate, the common fee. Counted across all
              records, expected zero-or-near, and answered only by the
              `realestate` facet set, an owner's claim, or a person at the
              door — never by a crawl.

STRAYS — the บ้าน / หมู่บ้าน / เช่า / คอร์ท guards, shown working every run.
บ้าน is in thousands of names (villages, restaurants, museums: บ้านเชียงรุ้ง
is an apartment building, พิพิธภัณฑ์บ้านคำอูน is not) — never a rule. หมู่บ้าน
names real villages eighteen times in this catalogue (หมู่บ้านป่าไผ่…) and a
housing estate zero times — only the จัดสรร compound is ever a rule. เช่า
alone catches the motorbike-rental trade (เช่ารถ, มอเตอร์ไซค์ให้เช่า) — only
ห้องเช่า / บ้านเช่า are rules. คอร์ท names apartment buildings AND sport
courts (แบดมินตันคอร์ท) — safe inside building=apartments, never outside it.

Usage:
  python3 importers/audit_realestate.py               # all reports
  python3 importers/audit_realestate.py --only split
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANON = ROOT / "data" / "canonical"

sys.path.insert(0, str(ROOT / "importers"))


def _io():
    """classify()'s own realestate_sub, imported LAZILY.

    import_overpass imports this module for the moobaan fence, so importing
    it back at module level makes a cycle: it happens to work (Python hands
    back the half-built module and nothing here touches it at import time),
    but it works by luck, and a future line at module scope would turn that
    luck into an AttributeError nobody expects. Imported inside the one
    function that needs it instead.
    """
    import import_overpass
    return import_overpass

# Thai needs no word boundary; Latin does. Compounds only, per the guards.
RES_WORDS = re.compile(
    r"แมนชั่น|คอร์ท|คอร์ต|อพาร์ท|อพาร์ต|เรสซิเด|ห้องเช่า|บ้านเช่า|หอพัก|คอนโด|"
    r"\b(apartments?|mansions?|courts?|residences?|flats?|condo(minium)?s?|"
    r"dorm(itor(y|ies))?|serviced)\b", re.I)
MOOBAAN_ESTATE = re.compile(r"หมู่บ้านจัดสรร|บ้านจัดสรร|จัดสรร")
LANDOFFICE = re.compile(r"สำนักงานที่ดิน|ที่ดินจังหวัด|ที่ดินอำเภอ|land\s*office", re.I)
SILENCE = {
    "furnished": re.compile(r"เฟอร์ครบ|เฟอร์นิเจอร์ครบ|\bfully\s*furnished\b", re.I),
    "pets": re.compile(r"เลี้ยงสัตว์ได้|สัตว์เลี้ยง|\bpet[-\s]?friendly\b", re.I),
    "rate": re.compile(r"ค่าไฟหน่วยละ|ค่าส่วนกลาง|\bcommon\s*fee\b", re.I),
}
STRAY_RE = re.compile(r"หมู่บ้าน|เช่ารถ|ให้เช่า|คอร์ท")


# --- the moobaan fence (WO-27 door 3) --------------------------------------
# `landuse=residential["name"]` is a dragnet: in this province the named
# residential areas are overwhelmingly VILLAGES (บ้านสันทราย, บ้านป่าไผ่ —
# หมู่บ้าน is the ordinary word for one), and filing a village as a gated
# housing estate is a falsehood about where somebody lives. So only two
# things declare an estate, and both are the developer's own word:
#
#   จัดสรร   — "allotted", the legal/administrative word for a housing
#              development. Not a word a village wears.
#   a named developer — the brands that build them here, each of which puts
#              its own name on the entrance arch.
#
# Everything else goes to cache/moobaan_review_<prov>.txt where a person can
# read it, exactly as the elephants and springs dragnets are fenced. A real
# estate hiding under a name these rules do not read enters through a curated
# addition with a source — never a wider regex on a guess.
DEVELOPERS = re.compile(
    r"ศุภาลัย|พฤกษา|แลนด์\s*แอนด์\s*เฮ้าส์|แสนสิริ|ควอลิตี้\s*เฮ้าส์|เอพี\s|"
    r"อารียา|ลลิล|สิวารมณ์|กัลปพฤกษ์|เดอะ\s*คอนเนค|"
    r"\b(supalai|pruksa|land\s*(and|&)\s*houses?|sansiri|quality\s*houses?|"
    r"areeya|lalin|sivarom|perfect\s*(place|park)|the\s*connect)\b", re.I)
ESTATE_WORD = re.compile(r"จัดสรร")


CONDO_WORD = re.compile(r"คอนโด|condominium|\bcondo\b", re.I)
APARTMENT_WORD = re.compile(r"อพาร์ตเมนต์|อพาร์ทเม|แมนชั่น|แมนชัน|apartment|mansion", re.I)
DORM_WORD = re.compile(r"หอพัก|\bdorm", re.I)


def moobaan_hit(t):
    """'moobaan' if a landuse=residential element declares a housing ESTATE
    by its own name, else None. Only ever consulted for elements of
    cache/overpass/<prov>/moobaan.json — see the fence in records().

    หมู่บ้าน alone is not a rule here: it is the ordinary
    Thai word for a village, and this catalogue already holds eighteen real
    villages wearing it (audit_realestate's STRAYS report prints them every
    run). The เปีย guard's shape, applied to somebody's home address.
    """
    name = " ".join(v for v in (t.get("name"), t.get("name:th"), t.get("name:en"),
                                t.get("alt_name")) if v)
    if not name:
        return None
    # A village mapped as an administrative place is a village whatever its
    # name says — the mapper's other tag wins, the same way the elephant
    # fence lets a hotel keep its hotel record.
    if t.get("place") in ("village", "hamlet", "neighbourhood", "suburb", "quarter"):
        return None
    if ESTATE_WORD.search(name) or DEVELOPERS.search(name):
        return "moobaan"
    # A BUILDING THAT NAMES ITSELF SOMETHING ELSE IS STILL SOMETHING.
    # This fence only ever asked "is it a housing estate?", so a residential
    # element whose own sign says คอนโด or หอพัก was refused outright and
    # written to cache/moobaan_review_<prov>.txt — 24 of them, on a shelf tree
    # that already has children for all three. The condo shelf holds 427 and
    # dcondo hyde ดีคอนโด ไฮด์, Arise Condo At Mahidol, Airport Home
    # Condominium and หอพักชาย มช. were sitting in the refusal file next to
    # the villages. The village guard above still runs first, and "residence"
    # is deliberately NOT a word here: Staff Residence Chiang Mai Airport and
    # บ้านพักพนักงานท่าอากาศยาน are staff housing, not a building anybody rents.
    if CONDO_WORD.search(name):
        return "condo"
    if APARTMENT_WORD.search(name):
        return "apartment"
    if DORM_WORD.search(name):
        return "dorm"
    return None


def load():
    recs = []
    for f in ("cm.json", "cr.json"):
        p = CANON / f
        if p.exists():
            recs += json.loads(p.read_text())
    return recs


def name_of(r):
    """Every name the record carries, joined — a building declares in any."""
    return " ".join(x for x in (r.get("name"), r.get("nameTh"), r.get("nameEn")) if x)


def is_re(r):
    return "realestate" in (r.get("cat") or [])


def on(recs, sub):
    return [r for r in recs if sub in (r.get("sub") or [])]


def split_census(recs=None):
    """The four shelves, plus the buildings whose name states nothing.

    Uses classify()'s own realestate_sub on the record's names, so the count
    here and the shelf the import filed cannot disagree — the WO-23 rule that
    two implementations of one judgement must be one implementation.
    """
    recs = load() if recs is None else recs
    mine = [r for r in recs if is_re(r)]
    out = {s: len(on(mine, s)) for s in ("condo", "apartment", "dorm", "agent", "moobaan")}
    defaulted = []
    io = _io()
    for r in on(mine, "apartment"):
        t = {"name:th": r.get("nameTh"), "name:en": r.get("nameEn"),
             "description": (r.get("attrs") or {}).get("description")}
        if io.realestate_sub(t, r.get("name") or "") == "apartment" \
                and not RES_WORDS.search(name_of(r)):
            defaulted.append(r)
    out["defaulted"] = len(defaulted)
    out["total"] = len(mine)
    return out, defaulted


def silences(recs=None):
    """The counts the facet set exists for. Expected zero-or-near."""
    recs = load() if recs is None else recs
    return {k: sum(1 for r in recs if rx.search(name_of(r)))
            for k, rx in SILENCE.items()}


def moobaan_estate(recs=None):
    recs = load() if recs is None else recs
    return [(r, name_of(r)) for r in recs if MOOBAAN_ESTATE.search(name_of(r))]


def landoffice(recs=None):
    recs = load() if recs is None else recs
    return [(r, name_of(r)) for r in recs if LANDOFFICE.search(name_of(r))]


def hotel_overlap(recs=None):
    recs = load() if recs is None else recs
    return [(r, name_of(r)) for r in recs
            if "hotel" in (r.get("cat") or []) and not is_re(r)
            and RES_WORDS.search(name_of(r))]


def rep_split():
    out, defaulted = split_census()
    print("\n=== SPLIT — the four shelves after the 2026-08-21 correction")
    print(f"    condo {out['condo']} · apartment {out['apartment']} · dorm {out['dorm']}"
          f" · agent {out['agent']} · moobaan {out['moobaan']} · total {out['total']}")
    print(f"    {out['defaulted']} buildings state nothing in their name and file as")
    print("    apartment because that is the tag's own word (building=apartments).")
    print("    They are the read queue for the doors, not a rule waiting to be written.")
    for r in defaulted[:10]:
        print(f"      {r.get('province','?')}  {name_of(r)[:56]}")


def rep_agent():
    mine = on([r for r in load() if is_re(r)], "agent")
    print(f"\n=== AGENT — all {len(mine)} rows, whole; the shelf is small enough to read")
    for r in mine:
        marks = " ".join(x for x in (r.get("phone"), r.get("website")) if x)
        print(f"      {r.get('province','?')}  {name_of(r)[:44]:46} {marks[:40]}")
    print("    Two rows deserve a person's eye, and neither is retagged on a guess:")
    print("      · is Sara — a person's name, not a shopfront. The unlisted-by-default")
    print("        question (AGENTS.md, standing debt 2) is Nan's call, not an audit's.")
    print("      · อคิน ลิสซิ่ง — the Facebook slug reads akinleasing; a leasing desk is")
    print("        the vehicle-finance trade, not brokerage. A URL slug is thinner than")
    print("        a sign, and a login wall is not a first-hand read: a LEAD, not a retag.")


def rep_moobaan():
    hits = moobaan_estate()
    print(f"\n=== MOOBAAN — names saying จัดสรร across the whole catalogue: {len(hits)}")
    for r, n in hits[:8]:
        print(f"      {n[:56]:58} [{','.join(r.get('cat') or [])}]")
    print("    Note what this report does NOT count: the shelf is filled from named")
    print("    landuse=residential areas (the 2026-08-21 door), fenced by developer")
    print("    name or จัดสรร — and 590 named residential areas were held back as the")
    print("    villages they are. The three rows above are the จัดสรร word appearing")
    print("    in a health station's and a school's village NAME, which is exactly why")
    print("    bare หมู่บ้าน is never a rule here.")


def rep_hotelside():
    rows = hotel_overlap()
    print(f"\n=== HOTELSIDE — monthly words on the hotel shelf: {len(rows)}")
    print("    Counted, never proposed. tourism=* is the venue stating a nightly trade;")
    print("    a monthly word in the name is not evidence enough to argue with it —")
    print("    this city is full of buildings that truly sell both. Door work.")
    for r, n in rows[:12]:
        print(f"      {r.get('province','?')}  {n[:60]}")


def rep_landoffice():
    hits = landoffice()
    print(f"\n=== LANDOFFICE — สำนักงานที่ดิน anywhere in the catalogue: {len(hits)}")
    if not hits:
        print("    ZERO, in both provinces. Every condo transfer in the north walks")
        print("    through an office this directory does not hold. A crawl-selector")
        print("    question (office=government), not a name rule; printed every run")
        print("    so the hole stays visible until the door gets its go.")
    for r, n in hits[:6]:
        print(f"      {n[:70]}")


def rep_silences():
    z = silences()
    total = len(load())
    print(f"\n=== SILENCES — what no building's sign says, in {total:,} records")
    print(f"    furnished {z['furnished']} · pets {z['pets']} · rates/fees {z['rate']}")
    print("    Answered by the `realestate` facet set, an owner's claim, or a person")
    print("    at the door — never by a crawl. Printed so the hole cannot be quietly")
    print("    forgotten (the audit_beauty discipline).")


def rep_strays():
    recs = load()
    hits = [name_of(r) for r in recs
            if STRAY_RE.search(name_of(r)) and not is_re(r)]
    print(f"\n=== STRAYS — บ้าน / หมู่บ้าน / เช่า / คอร์ท guard, names shown not matched: {len(hits)}")
    print("    A bare หมู่บ้าน rule files villages as housing estates; a bare เช่า rule")
    print("    files the motorbike-rental trade as landlords. Compounds only, and the")
    print("    catch is printed so the guard can be seen working.")
    for n in hits[:12]:
        print(f"      {n[:70]}")


REPORTS = {
    "split": rep_split, "agent": rep_agent, "moobaan": rep_moobaan,
    "hotelside": rep_hotelside, "landoffice": rep_landoffice,
    "silences": rep_silences,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=sorted(REPORTS))
    a = ap.parse_args()
    keys = [a.only] if a.only else list(REPORTS)
    for k in keys:
        REPORTS[k]()
    if not a.only:
        rep_strays()
        print("\nNothing above has been written. The split lives in classify()"
              " (import_overpass.realestate_sub); the rest is door work.")


if __name__ == "__main__":
    main()
