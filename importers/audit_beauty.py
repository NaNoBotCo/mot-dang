#!/usr/bin/env python3
"""Read the beauty records' own names for what they declare. Zero network.

Same contract as audit_muaythai.py, audit_massage.py and audit_cooking.py:
this never edits canonical data. It reports, and --emit prints shelves.json-
ready entries for a human to look at before pasting. Every proposed entry
carries `source: "osm name: <name>"` — the claim is the shop's own, read off
the sign it chose.

The measurement that asked for this (notes/beauty-proposal-2026-08-20.md):

  THE BARBER SHELF HELD SIX SHOPS AND THE CITY HAS SIXTY. `hairdresser=barber`
  is set on 6 of the 371 hairdresser/beauty elements in the snapshot, so 6 is
  what the classifier filed under ตัดผมชาย. Fifty-three more shops put the word
  BARBER on their own shopfront — สุเทพบาร์เบอร์, Sweeney Todds, Backstreet
  Barber Shop, เมืองใหม่บาร์เบอร์, Cutlers, Loft Barber shop — and every one of
  them sat on ร้านทำผม, indistinguishable from a blow-dry counter. A reader
  looking for a men's shop with a chair and a razor was shown six.

  THE SALON SHELF HELD NONE AT ALL, and was on KNOWN_EMPTY with the reason
  "no OSM signal separates a salon from a hairdresser". True of OSM's tags and
  false of the shops: เสริมสวย is THE Thai word for a women's salon and it is
  in sixty-two names — เสริมสวยดาว, เสริมสวยอิงอร, ณัฏฐ์บิวตี้ซาลอน, มะซาลอน. The
  signal was never in the tag. It was on the sign, in Thai, sixty-two times.

Seven reports:

  BARBER      names that say barber / บาร์เบอร์ / ตัดผมชาย. Six on the shelf today.
  SALON       ร้านเสริมสวย / ซาลอน / beauty salon. Zero on the shelf today.
  EXTENSIONS  ต่อผม, ถักเปีย, dreadlocks, wigs — the braiding and extension trade.
  NAILS       ทำเล็บ / nail, already a live shelf; run for completeness.

ต่อขนตา was looked for and is deliberately not a report. Eyelash extension is a
real and separate trade here, usually sharing a room with nails — but ZERO shop
names in either province say it, and OSM carries `beauty=eyelash` on exactly one
element (inside `hair;eyelash;nails`). A shelf for that is a shelf for nobody,
and this repo forbids one. It stays a door question until somebody has stood at
enough doors to fill a shelf honestly.
  PERM        ดัดดิจิตอล, ยืดผม, รีบอนดิ้ง. Expected ZERO — see below.
  TEXTURED    ผมหยิก, แอฟโฟร, curly, afro. Expected ZERO — see below.
  MOBILE      ช่างไปหาถึงที่, home service, นอกสถานที่. Expected ZERO — see below.

The three expected-zero reports are the point of running them, not a failure
of the rules. Across ALL 18,686 records in both provinces, not one name says
perm, updo, afro, textured, or house call. That is a true measurement of what
a shopfront chooses to say, and it means those four questions can only ever
be answered by the shop's own site or by somebody standing at the door — they
are the `beauty` facet set and data/curated/beauty.json, never a name rule.
Printed each run so the hole stays visible instead of being quietly forgotten.
Same discipline as GEAR in audit_muaythai.py, which is also expected zero.

STRAYS — the เปีย guard, and why it exists. เปีย on its own means a braid, and
a bare เปีย rule files FIFTEEN places in this catalogue as braiding salons:
บ้านเปียง, ยางเปียง and เปียงหลวง are Northern Thai village names, so the rule
would have caught five health stations (โรงพยาบาลส่งเสริมสุขภาพตำบลบ้านเปียง…),
four temples (วัดยางเปียง, วัดเปียงหลวง, วัดบ้านเปียง, วัดถ้ำปากเปียง), three
schools and a bakery (ซีเปียวพาณิชย์). Only the compound ถักเปีย is ever a rule.
Same shape as the หมวย/มวย guard and the กระท่อม hut guard: the strays are
printed every run so the guard can be seen working.

What this deliberately does NOT do:

  * Guess. A name that declares nothing produces nothing. Absent is not false.
  * Sort shops into good and bad, cheap and dear, farang and Thai. What a
    chair is like is a door question and always was.
  * Decide a barber is not also a salon. shelves.json ADDS; Robin Beauty &
    Barber says both words on its own sign and reaches both shelves.
  * Infer a price, a service or who a shop will cut for. Those are the shop's
    own statements and live in data/curated/beauty.json with a source each.

Usage:
  python3 importers/audit_beauty.py               # all seven reports
  python3 importers/audit_beauty.py --only barber
  python3 importers/audit_beauty.py --emit        # shelves.json-ready JSON
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANON = ROOT / "data" / "canonical"
SHELVES = ROOT / "data" / "curated" / "shelves.json"

# Thai needs no word boundary; Latin does. Every Thai term that could be a
# toponym or an ordinary word is a compound — see the เปีย guard above.
RULES = {
    "barber": (
        "barber", "beauty",
        r"barber|บาร์เบอร์|บาเบอร์|บาร์เบอ|ตัดผมชาย|ช่างตัดผมชาย|\bbarbershop\b"),
    "salon": (
        "salon", "beauty",
        r"\bsalon\b|ซาลอน|ซาลูน|ซาลอง|เสริมสวย|บิวตี้\s*ซาลอน|beauty\s*salon"),
    "extensions": (
        "extensions", "beauty",
        r"ต่อผม|ถักเปีย|เปียผม|ผมเปีย|\bbraid|braiding|\bdread|เดรดล็อค|เดรด|"
        r"corn\s*row|cornrow|hair\s*extension|extensions?\s*hair|วิกผม|ร้านวิก|\bwigs?\b"),
    "nails": (
        "nails", "beauty",
        r"\bnails?\b|ทำเล็บ|ร้านเล็บ|เพ้นท์เล็บ|ต่อเล็บ|เนลอาร์ต|nail\s*art"),
    # --- the three that are expected to find nothing ----------------------
    "perm": (
        "perm", "beauty",
        r"\bperm\b|ดัดผม|ดัดดิจิ|digital\s*perm|ยืดผม|รีบอนด|rebond|เซ็ตผม|เกล้าผม|\bupdo\b"),
    "textured": (
        "textured", "beauty",
        r"\bafro\b|แอฟโฟร|แอฟริกัน|african\s*hair|ผมหยิก|kinky\s*hair|coily|"
        r"textured\s*hair|type\s*4\s*hair"),
    "mobile": (
        "mobile", "beauty",
        r"ช่างไปหา|ไปทำถึงบ้าน|ทำผมถึงบ้าน|home\s*service|mobile\s*(hair|barber|stylist)|"
        r"นอกสถานที่|ถึงที่พัก|hair\s*at\s*home"),
}

# Names that hold เปีย only because they hold a village name — shown, never
# matched. บ้านเปียง / ยางเปียง / เปียงหลวง are places; ซีเปียว is a shophouse
# surname. The rules above never contain a bare เปีย, and this proves it.
STRAY_RE = re.compile(r"เปียง|ซีเปีย|เปียโน")

EXPECTED_ZERO = {"perm", "textured", "mobile"}

# Which facet actually carries each expected-zero axis. This report used to name
# its own RULES key, and two of those three keys do not exist in facets.json
# under that name — a report pointing at a facet nobody can find is one more
# thing to chase down at midnight.
FACETS_FOR = {
    "perm": "`digiperm` / `rebond` / `updo`",
    "textured": "`textured` / `braids`",
    "mobile": "`housecall`",
}


def load():
    recs = []
    for f in ("cm.json", "cr.json"):
        p = CANON / f
        if p.exists():
            recs += json.loads(p.read_text())
    return recs


def name_of(r):
    """Every name the record carries, joined — a shop declares in any of them."""
    return " ".join(x for x in (r.get("name"), r.get("nameTh"), r.get("nameEn")) if x)


def is_beauty(r):
    return "beauty" in (r.get("cat") or [])


def existing():
    if not SHELVES.exists():
        return {}
    return json.loads(SHELVES.read_text()).get("shelves", {})


def scan(key):
    """Records whose own name declares `key`. Beauty-cat records only.

    The cat fence matters: `extension` catches Lanna Hospital Extension and
    `wig` would catch a costume shop. A shop that is not on the beauty shelf
    at all is not re-filed by a word — it is a LEAD for a person, printed
    separately, never proposed.
    """
    sub, cat, pat = RULES[key]
    rx = re.compile(pat, re.I)
    hits, leads = [], []
    for r in load():
        n = name_of(r)
        if not n or not rx.search(n):
            continue
        (hits if is_beauty(r) else leads).append((r, n))
    return sub, cat, hits, leads


def report(key, quiet_empty=False):
    sub, cat, hits, leads = scan(key)
    have = sum(1 for r, _ in hits if sub in (r.get("sub") or []))
    new = [(r, n) for r, n in hits if sub not in (r.get("sub") or [])]
    print(f"\n=== {key.upper()}  →  {cat}/{sub}")
    if not hits and key in EXPECTED_ZERO:
        print(f"    0 names in {len(load()):,} records. EXPECTED, and the reason this")
        print("    report exists: no shopfront in either province says this word. It is")
        print(f"    a door question, not a name rule — see {FACETS_FOR[key]} in the")
        print("    `beauty` set of data/facets.json, and data/curated/beauty.json.")
        return sub, []
    print(f"    {len(hits)} names declare it · {have} already on the shelf · {len(new)} NEW")
    for r, n in new[:200]:
        prov = r.get("province", "?")
        on = "/".join(r.get("sub") or []) or "—"
        print(f"      {prov}  {n[:56]:58} (today: {on})")
    if leads:
        print(f"    -- {len(leads)} LEADS outside the beauty shelf, for a person, never proposed:")
        for r, n in leads[:12]:
            print(f"      {n[:56]:58} [{','.join(r.get('cat') or [])}]")
    return sub, new


def strays():
    """The เปีย guard, shown working."""
    hit = [name_of(r) for r in load() if STRAY_RE.search(name_of(r))]
    print(f"\n=== STRAYS — names holding เปีย that are NOT a braid: {len(hit)}")
    print("    A bare เปีย rule would file every one of these as a braiding salon.")
    for n in hit[:16]:
        print(f"      {n[:70]}")


def emit():
    """shelves.json-ready entries. Names only — never a price, never a service."""
    have = existing()
    out = {}
    for key in RULES:
        sub, cat, hits, _ = scan(key)
        for r, n in hits:
            if sub in (r.get("sub") or []):
                continue
            e = out.setdefault(r["id"], {
                "note": f"{n} — filed {'/'.join(r.get('sub') or []) or 'unfiled'} by the crawl; "
                        f"the shop's own sign says {sub}",
                "add_cat": [], "add_sub": [],
                "source": f"osm name: {n}", "fetched": "2026-08-20",
            })
            if cat not in (r.get("cat") or []) and cat not in e["add_cat"]:
                e["add_cat"].append(cat)
            if sub not in e["add_sub"]:
                e["add_sub"].append(sub)
    fresh = {k: v for k, v in out.items() if k not in have}
    print(json.dumps(fresh, ensure_ascii=False, indent=1))
    print(f"\n// {len(out)} entries, {len(fresh)} new to shelves.json", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=sorted(RULES))
    ap.add_argument("--emit", action="store_true",
                    help="print shelves.json-ready entries instead of a report")
    a = ap.parse_args()
    if a.emit:
        return emit()
    keys = [a.only] if a.only else list(RULES)
    for k in keys:
        report(k)
    if not a.only:
        strays()
        print("\nNothing above has been written. --emit prints the shelves.json entries.")


if __name__ == "__main__":
    main()
