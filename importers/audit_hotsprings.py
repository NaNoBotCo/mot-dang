#!/usr/bin/env python3
"""Read what the catalogue holds and drops about hot springs. Zero network.

Same contract as audit_views.py and audit_elephant.py: this never edits
canonical data. It reports, and import_overpass.springs_hit() borrows THIS
FILE's name rules (one copy) to file spring-shaped elements — from the WO-19
attraction cache it already holds, and from the `hotsprings` crawl group when
that lands.

The measurement that asked for this (notes/hotsprings-proposal-2026-08-20.md):
on 2026-08-20 Chiang Mai's 12,951 records held ZERO hot springs — สันกำแพง,
โป่งเดือด, เทพพนม all absent — because `natural=hot_spring` was in no crawl
group. Chiang Rai held three from WO-16's eco list, phones but no pins and no
sub, so no child shelf could show them. The WO-19 dragnet had already caught
the famous ones by name and fenced them into cache/elephant_review_<prov>.txt;
the views order took the waterfalls off that menu, and this order takes the
springs. Nan's go, and the widening past the two provinces, 2026-08-20:
"BIGLY … the whole north is ok."

Reports:

  SHELF    what sub=hot-spring holds today, by province, with contact/pin
           coverage.
  MENU     the WO-19 attraction cache and the `hotsprings` cache (when it
           exists) read with this file's rules: what would enter through
           springs_hit(), what the fences hold back and why.
  NORTH    cache/hotsprings/<prov>.json per northern province — the register
           harvest's raw counts, named.
  CLAIMS   places on OTHER shelves whose name claims the spring or the soak —
           resorts, onsen bath houses, ร้านโป่งน้ำร้อน the shop. A name is
           the venue's own claim (ชื่อบอกน้ำพุร้อน); the shelf it earned by
           its tags is the shelf it keeps.
  NEVER    selectors absent from crawl_overpass.py, and the famous-springs
           roll probed against what actually stands on the shelf.

What this deliberately does NOT do:

  * Rank a soak. No spring is scored or crowned; sorts stay distance,
    province and alphabet, the same rule as the temples.
  * Turn a temperature into a superlative. 105 °C renders as 105 °C with
    who measured it; "very hot" is nobody's measurement.
  * Repeat a cure. What the water is said to be good for is the operator's
    or the tradition's claim and renders as a claim. No health advice.
  * Sort springs into natural and commercial, hidden and touristy — no line
    on this site sorts places into real and otherwise.
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------- the rules
# Shared with import_overpass.springs_hit() — one copy. Each pattern carries
# a witness for why it is shaped the way it is.
#
# Bare โป่ง is NEVER matched. A โป่ง is any mineral lick or seep, and half the
# north is named after one — บ้านโป่ง, โป่งแยง, ทุ่งโป่ง, โป่งกุ่ม — so the
# bare word is a village-name generator, not a spring detector. Only the
# compounds that state hot water: โป่งน้ำร้อน and โป่งเดือด. Same discipline
# as กระท่อม (the hut), หมวย (the nickname) and bare วิว (วิวัฒน์) before it.
#
# น้ำพร้อน — พุ dropped — is kept deliberately: it is how the mapper spelled
# น้ำพร้อนเทพพนม (node 1268221687), the Mae Chaem springs, and the variant
# recurs in field spellings. It cannot collide: no ordinary word contains it.
SPRING_RULES = [
    ("น้ำพุร้อน", r"น้ำพุร้อน"),          # the standard compound; covers บ่อน้ำพุร้อน, สวนน้ำพุร้อน
    ("น้ำพร้อน", r"น้ำพร้อน"),            # field spelling, เทพพนม's own element
    ("บ่อน้ำร้อน", r"บ่อน้ำร้อน"),
    ("โป่งน้ำร้อน", r"โป่งน้ำร้อน"),
    ("โป่งเดือด", r"โป่งเดือด"),          # the geyser compound — Pong Duet
    ("ธารน้ำร้อน", r"ธารน้ำร้อน"),
    ("hot spring", r"hot\s*springs?\b"),
]

# The soak as a SERVICE in a name — onsen bath houses, spring-water spas.
# These are businesses and keep the shelf their tags earned; the census below
# counts them (ชื่อบอกออนเซ็น) the way the views census counts Lake View
# guesthouses. Never a filing rule on its own.
ONSEN_CLAIM = re.compile(r"\bonsen\b|ออนเซ็นต?์?|ออนเซน|น้ำแร่ร้อน", re.I)
SPRING_CLAIM = re.compile("|".join(p for _, p in SPRING_RULES), re.I)

# Tags that state the element is something else wearing the spring's name.
# Each line is a witness, not a guess:
#   lodging/food    Hot Spring House Resort (cr node 4395590136) is a hotel.
#   place           บ้านโป่งน้ำร้อน the village is not the spring it is named
#                   for; the spring, where mapped, is its own element.
#   school family   โรงเรียนบ้านโป่งน้ำร้อน (Fang) is a school.
#   place_of_worship วัดโป่งน้ำร้อน is a temple.
#   transit         a bus stop named น้ำพุร้อนสันกำแพง is where you get off
#                   FOR the spring, and filing it would pin the spring to the
#                   roadside.
#   spa/massage     a spring-water spa is a treatment business (beauty shelf's
#                   trade), and CLAIMS is where it shows.
LODGING_FOOD = ("restaurant", "cafe", "bar", "pub", "fast_food")
SCHOOLISH = ("school", "kindergarten", "college", "university", "childcare",
             "language_school", "music_school", "driving_school", "training",
             "prep_school")

# For rows that arrive with NO tags at all (the data.go.th lists): the name
# is the only witness, so the fence is the name's own first word. ชุมชน
# บ้านโป่งน้ำร้อน is the community named for the spring; the spring, where
# listed, is its own row.
NAMED_ELSE = re.compile(r"^\s*(?:ชุมชน|หมู่บ้าน|บ้าน|วัด|โรงเรียน|โรงพยาบาล"
                        r"|รพ\.?สต|อบต|เทศบาล|ตลาด|ร้าน|ครัว|คลินิก"
                        r"|ป้อม|ศูนย์|สถานี|ที่ทำการ|ที่ว่าการ|สหกรณ์|ธนาคาร"
                        r"|สำนัก|องค์การ|ตำบล|อ่างเก็บน้ำ)")


def named_spring(name):
    """True when a tagless row's NAME states a hot spring — the opendata
    importer's one-copy way to hand น้ำพุร้อนป่าตึง its sub without a
    guessed regex of its own."""
    return bool(name) and not NAMED_ELSE.match(name) and bool(SPRING_CLAIM.search(name))


def spring_fence(t):
    """The reason this element may NOT file as a spring, or None if clear.

    Mirrors the audit-owns-the-rules arrangement: import_overpass reads this
    so the fence cannot drift between the audit and the import.
    """
    if t.get("tourism") in ("hotel", "guest_house", "hostel"):
        return "lodging"
    # The springs' own campground: พื้นที่กางเต็นท์น้ำพุร้อนสันกำแพง entered
    # on the first CM crawl (2026-08-20) wearing the complex's name. A place
    # to pitch a tent beside a spring is a campsite, not the spring.
    if t.get("tourism") in ("camp_site", "caravan_site", "camp_pitch"):
        return "camping"
    if t.get("amenity") in LODGING_FOOD:
        return "food"
    if t.get("amenity") in SCHOOLISH:
        return "school"
    if t.get("amenity") == "place_of_worship":
        return "temple"
    # The rest of a village's public plant wears the village's name too: the
    # CR crawl (2026-08-20) brought ศูนย์สาธารณสุขมูลฐานชุมชน บ้านโป่งน้ำร้อน
    # (a health post) and ป้อมยามตำรวจ...โป่งน้ำร้อน (a police box).
    if (t.get("healthcare")
            or t.get("amenity") in ("clinic", "doctors", "hospital",
                                    "dentist", "pharmacy")):
        return "clinic"
    if t.get("amenity") in ("police", "townhall", "fire_station",
                            "community_centre", "post_office"):
        return "civic"
    # Kamphaeng Phet's crawl brought องค์การบริหารส่วนตำบลโป่งน้ำร้อน — the
    # sub-district OFFICE of a village named for its spring. An office is an
    # office whatever its village is named after.
    if t.get("office"):
        return "office"
    if t.get("place"):
        return "village"
    if t.get("highway") or t.get("public_transport") or t.get("railway"):
        return "transit"
    if (t.get("leisure") == "spa" or t.get("shop") in ("massage", "beauty")
            or t.get("amenity") == "spa"):
        return "spa"
    return None


def spring_hit_tags(t, name):
    """'hot-spring' if the element states a hot spring, else None.

    `natural=hot_spring` is checked BEFORE the fence: the tag states the
    thing itself, and a developed spring often also carries the tag of a
    service it runs — Pha Soet (way 325837628) is natural=hot_spring AND
    amenity=spa, and the spa fence must not hold the spring off its own
    shelf. The fence then speaks for everything tag-known; a NAME-only
    element (the CR crawl brought a health post and a police box wearing
    บ้านโป่งน้ำร้อน's name with NO tags at all) must also clear NAMED_ELSE,
    the institution-word guard, before a bare name can file.
    amenity=public_bath files only when its bath:type or its name says hot
    water — a public bath is otherwise a shower block.
    """
    if t.get("natural") == "hot_spring":
        return "hot-spring"
    if spring_fence(t):
        return None
    if t.get("amenity") == "public_bath":
        if "hot_spring" in (t.get("bath:type") or "") or SPRING_CLAIM.search(name):
            return "hot-spring"
        return None
    if NAMED_ELSE.match(name):
        return None
    if SPRING_CLAIM.search(name):
        return "hot-spring"
    return None


# The famous-springs roll, probed in NEVER against what actually stands on
# the shelf and in the register — each one a name a reader of the north would
# try first. Probed against SPRING names only, not the whole catalogue: the
# question is "is the spring filed", and สันกำแพง matching a noodle shop is
# not an answer.
FAMOUS = [
    ("cm", "สันกำแพง"), ("cm", "โป่งเดือด"), ("cm", "เทพพนม"),
    ("cm", "ฝาง"), ("cm", "โป่งกุ่ม"), ("cm", "ยางปู่โต๊ะ"),
    ("cr", "แม่ขะจาน"), ("cr", "ป่าตึง"), ("cr", "ห้วยทรายขาว"),
    ("cr", "โป่งพระบาท"), ("cr", "ผาเสริฐ"), ("cr", "ทุ่งเทวี"),
    ("mhs", "ท่าปาย"), ("mhs", "ไทรงาม"), ("mhs", "ผาบ่อง"), ("mhs", "เมืองแปง"),
    ("lampang", "แจ้ซ้อน"), ("phayao", "ภูซาง"), ("tak", "แม่กาษา"),
    ("phrae", "แม่จอก"), ("nan", "โป่งกิ"),
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
        out[prov] = (json.loads(p.read_text()).get("elements", [])
                     if p.exists() else [])
    return out


def element_name(t):
    return " ".join(v for v in (t.get("name"), t.get("name:th"),
                                t.get("name:en"), t.get("alt_name")) if v)


def band(title, note=""):
    print()
    print("=" * 72)
    print(title + ("  —  " + note if note else ""))
    print("=" * 72)


def report_shelf(recs):
    sp = [r for r in recs if "hot-spring" in (r.get("sub") or [])]
    band("SHELF", "sub=hot-spring today")
    for prov in ("cm", "cr"):
        rows = [r for r in sp if r.get("province") == prov]
        contact = sum(1 for r in rows if r.get("phone") or r.get("website"))
        pinned = sum(1 for r in rows if r.get("lat") is not None)
        temp = sum(1 for r in rows if (r.get("attrs") or {}).get("temperature"))
        print(f"  {prov}: {len(rows)} records — contactable {contact}, "
              f"pinned {pinned}, temperature stated {temp}")
        for r in rows:
            print(f"      {r['id']:42s} {r.get('name')}")
    if not sp:
        print("  (nothing stands on the shelf — the measurement this order opens with)")
    return sp


def report_menu():
    band("MENU", "the WO-19 attraction cache + the hotsprings cache, read with this file's rules")
    for stem in ("elephants", "hotsprings"):
        for prov, els in cached_elements(stem).items():
            enter, fenced = [], []
            for e in els:
                t = e.get("tags") or {}
                name = element_name(t)
                if not name:
                    continue
                if re.search(r"\(\s*closed\b|ปิดถาวร|ปิดกิจการ", name, re.I):
                    continue
                why = spring_fence(t)
                hit = spring_hit_tags(t, name)
                if hit:
                    enter.append((name, f"{e['type']}/{e['id']}"))
                elif why and (SPRING_CLAIM.search(name) or ONSEN_CLAIM.search(name)):
                    fenced.append((why, name))
            if not els and stem == "hotsprings":
                print(f"  {stem}/{prov}: no cache yet — the crawl group has not run")
                continue
            print(f"  {stem}/{prov}: {len(enter)} would enter through springs_hit()")
            for name, ref in enter:
                print(f"      {name}   ({ref})")
            for why, name in fenced:
                print(f"      fence, working [{why}]: {name}")


def report_north():
    band("NORTH", "cache/hotsprings/<prov>.json — the fifteen-province harvest")
    d = ROOT / "cache" / "hotsprings"
    if not d.exists():
        print("  (no harvest yet — harvest_hotsprings.py has not run)")
        return
    for f in sorted(d.glob("*.json")):
        els = json.loads(f.read_text()).get("elements", [])
        named = []
        for e in els:
            t = e.get("tags") or {}
            name = element_name(t)
            if name and spring_hit_tags(t, name):
                named.append(name)
        print(f"  {f.stem}: {len(els)} elements cached, {len(named)} state a spring")
        for n in named[:12]:
            print(f"      {n}")
        if len(named) > 12:
            print(f"      … +{len(named) - 12}")


def report_claims(recs):
    band("CLAIMS", "names on other shelves that claim the spring or the soak")
    bycat = {}
    for r in recs:
        if "hot-spring" in (r.get("sub") or []):
            continue
        n = name_of(r)
        if SPRING_CLAIM.search(n) or ONSEN_CLAIM.search(n):
            cat = "+".join(r.get("cat") or ["?"])
            bycat.setdefault(cat, []).append(r.get("name") or r.get("nameEn"))
    total = sum(len(v) for v in bycat.values())
    print(f"  {total} records claim the spring/soak by name, by shelf:")
    for cat, names in sorted(bycat.items(), key=lambda kv: -len(kv[1])):
        head = ", ".join(str(x) for x in names[:4])
        more = f" … +{len(names) - 4}" if len(names) > 4 else ""
        print(f"    {cat:24s} {len(names):3d}   {head}{more}")
    return bycat


def report_never(recs, register=None):
    band("NEVER", "what no crawl has asked, and the famous roll against the shelf")
    qtext = (ROOT / "importers" / "crawl_overpass.py").read_text()
    for sel in ('natural"="hot_spring', 'amenity"="public_bath'):
        state = "asked" if sel in qtext else "NEVER ASKED"
        print(f"  {sel:28s} {state}")
    print()
    spring_names = " ".join(
        name_of(r) for r in recs if "hot-spring" in (r.get("sub") or []))
    reg_names = ""
    reg_path = ROOT / "data" / "hotsprings.json"
    if reg_path.exists():
        reg = json.loads(reg_path.read_text())
        reg_names = " ".join(
            f"{e.get('nameTh') or ''} {e.get('nameEn') or ''} {e.get('name') or ''} "
            f"{e.get('village_th') or ''}"
            for e in reg.get("springs", []))
    joined = spring_names + " " + reg_names
    for prov, f in FAMOUS:
        where = ("shelf" if f in spring_names
                 else "register" if f in reg_names else "ABSENT")
        print(f"  {prov:8s} {f:16s} {where}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.parse_args()
    recs = load_records()
    print(f"catalogue: {len(recs)} records")
    report_shelf(recs)
    report_menu()
    report_north()
    report_claims(recs)
    report_never(recs)


if __name__ == "__main__":
    main()
