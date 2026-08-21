#!/usr/bin/env python3
"""Read the tattoo records' own names for what they declare. Zero network.

Same contract as audit_muaythai.py, audit_culture.py and audit_massage.py:
this never edits canonical data. It reports, and --emit prints shelves.json-
ready entries for a person to look at before pasting. Every proposed entry
carries `source: "osm name: <name>"` — the claim is the place's own, read off
the sign it chose.

The measurement that asked for this (notes/sakyant-proposal-2026-08-19.md):
thirty-four shop=tattoo points, every one filed tattoo/studio, and three of
the four sub-shelves empty on the live site — สักยันต์ because its rule
matched a lens no record carried, เจาะ and ลบรอยสัก because OpenStreetMap has
no tag for either. WO-14 adds a fifth child, สักคิ้ว-สักปาก (cosmetic-tattoo),
for the trade that had no shelf at all.

Three things are sold under one word, and the reports keep them apart:

  SAMNAK    the trade's own word — สักยันต์ / sak yant / สำนักสัก. A name that
            says the TRADE is proposed for sub sak-yant. A name that says a
            DESIGN (เก้ายอด, gao yord, ห้าแถว) is a studio until its own page
            says an ajarn works there — those go to LEADS, never proposed.
  STUDIO    everything the crawl filed tattoo/studio, with reach — the shelf
            as it stands, and the contact errand it implies.
  COSMETIC  สักคิ้ว / สักปาก / ฝังสีคิ้ว / คิ้ว 3 มิติ / microblading / PMU /
            semi-permanent — proposed for sub cosmetic-tattoo. A bare คิ้ว
            (eyebrow) counts only on a record ALREADY on the tattoo shelf:
            a threading salon says คิ้ว too and is not a tattoo shop.
  REMOVAL   ลบรอยสัก / tattoo removal / laser tattoo — proposed for
            sub tattoo-removal. Expected zero from OSM; fills by name and walk.
  MISFILES  records on the tattoo shelf whose names declare another trade
            (มินิกอล์ฟ, golf…). Listed for data/curated/retags.json, which
            needs an evidence line a person writes — never emitted here.
  STRAYS    names holding สัก that are not tattoo — สัก is teak (ไม้สัก, สวนสัก)
            and "a single" (สักแห่ง) — and ยันต์ inside สุริยันต์. Printed so
            the guard is visible. Same discipline as the หมวย guard.
  LEADS     design names, bamboo / hand-poke, a mapper's description that says
            sak yant — for a person to read from the venue's own page.
  NAMELESS  the stubs ("Tattoo", "Tattoo Studio", "Forever") — the needs-love
            list for the walk, nothing proposed.

What this deliberately does NOT do:

  * Guess. A name that declares nothing produces nothing. Absent is not false.
  * Sort studios into real and touristic, or rank anyone's ajarn.
  * Infer prices, blessings or what a door charges. Those are the venue's own
    statements and live on the record with their source and date.

Usage:
  python3 importers/audit_tattoo.py             # all reports
  python3 importers/audit_tattoo.py --only cosmetic
  python3 importers/audit_tattoo.py --emit      # shelves.json-ready JSON
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANON = ROOT / "data" / "canonical"
SHELVES = ROOT / "data" / "curated" / "shelves.json"

# Thai needs no word boundary; Latin does. Bare สัก is NEVER a rule (teak,
# "a single"); bare ยันต์ is not either (สุริยันต์ is a personal name). Every
# Thai term is a compound; ยันต์ counts only after สัก or at a word start.
SAMNAK_RE = re.compile(
    r"สักยันต์|สำนักสัก|(?:^|[\s(·/-])ยันต์|sak\s*yant|sakyant|yantra\s+tattoo", re.I)
DESIGN_RE = re.compile(
    r"เก้ายอด|ห้าแถว|gao\s*yord|kao\s*yot|hah?\s*taew|ha\s*thaeo|"
    r"bamboo\s+tattoo|สักมือ|สักไม้|hand[\s-]*poke", re.I)
BAMBOO_RE = re.compile(r"\bbamboo\b", re.I)         # only on the tattoo shelf
COSMETIC_RE = re.compile(
    r"สักคิ้ว|สักปาก|สักไรผม|ฝังสีคิ้ว|ฝังสี|คิ้ว\s*[36๓๖]\s*มิติ|คิ้วสไลด์|คิ้วลายเส้น|"
    r"microblad|micro\s*blad|\bpmu\b|semi[\s-]*permanent|permanent\s+make[\s-]*up|"
    r"eyebrow\s+tattoo|brow\s+tattoo|lip\s+tattoo", re.I)
BROW_RE = re.compile(r"คิ้ว|\bbrow", re.I)          # only on the tattoo shelf
REMOVAL_RE = re.compile(r"ลบรอยสัก|tattoo\s+removal|laser\s+tattoo|remove\s+tattoo", re.I)
MISFILE_RE = re.compile(r"มินิกอล์ฟ|minigolf|mini\s*golf|\bgolf\b|ร้านอาหาร|restaurant|"
                        r"hostel|guest\s*house|โรงแรม|hotel", re.I)
STRAY_RE = re.compile(r"ไม้สัก|สวนสัก|บ้านสัก|สักทอง|สักแห่ง|สักครั้ง|สุริยันต์")
NAMELESS = {"tattoo", "tattoo studio", "tattoo shop", "forever", "solitary", "ganesha", "ink"}


def load():
    recs = []
    for f in ("cm.json", "cr.json"):
        p = CANON / f
        if p.exists():
            recs += json.loads(p.read_text())
    return recs


def name_of(r):
    return " ".join(str(x) for x in (r.get("name"), r.get("nameTh"), r.get("nameEn")) if x)


def on_tattoo(r):
    return "tattoo" in (r.get("cat") or [])


def is_samnak(r):
    return bool(SAMNAK_RE.search(name_of(r)))


def is_cosmetic(r):
    n = name_of(r)
    if COSMETIC_RE.search(n):
        return True
    return on_tattoo(r) and bool(BROW_RE.search(n))


def is_removal(r):
    return bool(REMOVAL_RE.search(name_of(r)))


def is_misfile(r):
    return on_tattoo(r) and bool(MISFILE_RE.search(name_of(r)))


def is_nameless(r):
    return on_tattoo(r) and (r.get("name") or "").strip().lower() in NAMELESS


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


def report_samnak(recs):
    hits = [r for r in recs if is_samnak(r)]
    band(f"SAMNAK — {len(hits)} record(s) whose name says the trade: สักยันต์ / sak yant / สำนักสัก",
         "The trade's own word is the claim. A design name (เก้ายอด, gao yord) is\n"
         "NOT — see LEADS. Sak Yant Chiang Mai arrives curated, already on the shelf.")
    for r in hits:
        line(r, "" if "sak-yant" in (r.get("sub") or []) else "   ← not yet on สักยันต์")


def report_studio(recs):
    hits = [r for r in recs if on_tattoo(r) and "studio" in (r.get("sub") or [])]
    band(f"STUDIO — {len(hits)} record(s) the crawl filed tattoo/studio",
         "The shelf as it stands. ☎ = a phone or LINE on the record; 🌐 = a website.")
    for r in hits:
        line(r)
    contactable = sum(1 for r in hits if r.get("phone") or (r.get("attrs") or {}).get("lineId"))
    print(f"\n  contactable {contactable}/{len(hits)} — the door survey's first errand.")


def report_cosmetic(recs):
    hits = [r for r in recs if is_cosmetic(r)]
    band(f"COSMETIC — {len(hits)} record(s) whose name says brow / lip / semi-permanent",
         "OSM records a beauty shop as shop=beauty and stops, so zero from the crawl\n"
         "means 'never asked', not 'none in town'. The shelf fills by name and by walk.")
    for r in hits:
        line(r, "" if "cosmetic-tattoo" in (r.get("sub") or []) else "   ← not yet on สักคิ้ว-สักปาก")


def report_removal(recs):
    hits = [r for r in recs if is_removal(r)]
    band(f"REMOVAL — {len(hits)} record(s) whose name says ลบรอยสัก / tattoo removal",
         "Expected zero from OSM. A clinic that removes tattoos is mapped as a clinic.")
    for r in hits:
        line(r)


def report_misfiles(recs):
    hits = [r for r in recs if is_misfile(r)]
    band(f"MISFILES — {len(hits)} record(s) on the tattoo shelf whose name declares another trade",
         "For data/curated/retags.json, which needs an evidence line a person writes.\n"
         "Nothing here is emitted; a shelf is not taken away without a receipt.")
    for r in hits:
        line(r)


def report_strays(recs):
    hits = [r for r in recs if STRAY_RE.search(name_of(r)) and not is_samnak(r)]
    band(f"STRAYS — {len(hits)} record(s) holding สัก or ยันต์ for another reason (teak, a name, 'a single')",
         "Printed so the guard is visible. None of these is proposed for anything.")
    for r in hits[:40]:
        line(r)
    if len(hits) > 40:
        print(f"  … and {len(hits) - 40} more")


def report_leads(recs):
    # The description rule is the trade's word only. อาจารย์ is every teacher
    # in the province and would list the art galleries; a blessing is every
    # wat. Bare "bamboo" counts only on the tattoo shelf — otherwise it is a
    # guesthouse in every soi.
    desc_re = re.compile(r"สักยันต์|sak\s*yant|yantra", re.I)
    hits = []
    for r in recs:
        if is_samnak(r):
            continue
        n = name_of(r)
        a = r.get("attrs") or {}
        desc = str(a.get("description") or "") + " " + str(a.get("descriptionTh") or "")
        if DESIGN_RE.search(n) or (on_tattoo(r) and BAMBOO_RE.search(n)):
            hits.append((r, "design or bamboo in the name"))
        elif desc_re.search(desc):
            hits.append((r, "mapper's description says sak yant"))
    band(f"LEADS — {len(hits)} record(s) a person reads from the venue's own page before any shelf moves",
         "A design name is branding until the page says an ajarn works there and a\n"
         "katha is given. Not proposed.")
    for r, why in hits:
        line(r, f"   [{why}]")


def report_nameless(recs):
    hits = [r for r in recs if is_nameless(r)]
    band(f"NAMELESS — {len(hits)} stub(s) on the tattoo shelf — the needs-love list",
         "Real mapped points with generic names. Nothing proposed; the walk fills them.")
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
    """shelves.json-ready entries. Names only — the trade's own word."""
    already = json.loads(SHELVES.read_text())["shelves"]
    owner = sub_to_cat()
    out = {}

    def add(r, subs, why, src):
        if not subs:
            return
        if set(subs) <= set(r.get("sub") or []):
            return  # already carries it (curated record or a prior paste)
        prior = already.get(r["id"]) or {}
        if set(subs) <= set(prior.get("add_sub") or []):
            return
        e = out.setdefault(r["id"], {"note": f"{r.get('name')} — {why}",
                                     "add_cat": [], "add_sub": [], "source": src,
                                     "fetched": r.get("updatedAt", ""),
                                     "via": "importers/audit_tattoo.py --emit"})
        e["add_sub"] = sorted(set(e["add_sub"]) | set(subs))
        want = {owner[s] for s in subs if s in owner} - set(r.get("cat") or [])
        e["add_cat"] = sorted(set(e["add_cat"]) | want)

    for r in recs:
        if is_misfile(r):
            continue
        if is_samnak(r):
            add(r, ["sak-yant"], "the trade's own word, read off its own name", f"osm name: {name_of(r)}")
        if is_cosmetic(r):
            add(r, ["cosmetic-tattoo"], "brow / lip tattoo read off its own name", f"osm name: {name_of(r)}")
        if is_removal(r):
            add(r, ["tattoo-removal"], "removal read off its own name", f"osm name: {name_of(r)}")

    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit", action="store_true",
                    help="print shelves.json-ready entries instead of a report")
    ap.add_argument("--only", choices=("samnak", "studio", "cosmetic", "removal",
                                       "misfiles", "strays", "leads", "nameless"),
                    help="run one report")
    args = ap.parse_args()

    recs = load()
    if args.emit:
        emit(recs)
        return

    print(f"tattoo audit — {len(recs)} records in cm + cr")
    run = args.only
    for key, fn in (("samnak", report_samnak), ("studio", report_studio),
                    ("cosmetic", report_cosmetic), ("removal", report_removal),
                    ("misfiles", report_misfiles), ("strays", report_strays),
                    ("leads", report_leads), ("nameless", report_nameless)):
        if run in (None, key):
            fn(recs)
    print()
    print("Nothing above has been written anywhere. --emit proposes; a person pastes.")


if __name__ == "__main__":
    main()
