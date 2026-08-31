#!/usr/bin/env python3
"""What the corpus says about long-term care, counted — WO-32.

The four questions people bring to this door — a place for an ageing parent
(บ้านพักคนชรา · nursing home), somewhere to recover after a hospital
(พักฟื้น · convalescence), a door out of an addiction (บำบัด), and the
retirement that is a LIFE and not a bed (active retirement) — and what the
catalogue actually held when somebody counted, 2026-08-26:

  บ้านพักคนชรา 0 · พักฟื้น 0 · hospice 0 · convalescence 0 · detox 0 ·
  addiction 0 · dementia 0 · assisted living 0 in any record's own words —
  and the records that DO exist (a nursing home, an assisted-living garden,
  the best-known residential rehab in the province) were filed under
  community/volunteer, because import_overpass.py filed every
  amenity=social_facility as "Volunteering" and threw the
  social_facility=nursing_home|assisted_living|rehabilitation subtag away.

This file owns the rules, one copy (the audit_elephant arrangement):
  longcare_hit(t)     raw OSM tags -> True if the element states residential
                      or long-stay care in its TAGS (a mapper's statement)
  NURSING_NAME_RX     a name that says elder care itself
  ADDICTION_NAME_RX   a name that says addiction medicine itself
import_overpass.py borrows longcare_hit for classify(); longcare_layer.py
borrows both regexes for the page's own sentences; this audit re-counts all
three against canonical so the page and the count cannot drift.

Fences, each witnessed in cache/overpass/cm/community.json:
  social_facility:for=orphan    มูลนิธิบ้านร่มไทร, บ้านกิ่งแก้ว — children's
                                homes, volunteer shelf is right for them
  social_facility:for=disabled  Skill Center Chiang Mai — a training centre
  social_facility=outreach      Projects For Asia — an office, not a bed
  social_facility=ambulatory_care  Baan dol sook — care that VISITS; left on
                                its shelf until somebody reads its door
  bare ผู้สูงอายุ is never a rule — it is in the name of every senior CLUB
  (ชมรมผู้สูงอายุ) and the elephant namesakes wear "retirement" (Elephant
  retirement park, WO-19 fence): a word about the old is not a bed for them.
  \brehab\b(?!ilitat) states addiction here (Dawn Rehab, The River Rehab)
  but "Rehabilitation" alone does not — McKean Rehabilitation Center and
  ศูนย์ฟื้นฟูสมรรถภาพคนงานภาค 3 (the SSO workers' centre) are not addiction
  medicine, and neither is กายภาพบำบัด.

Run:  python3 importers/audit_longcare.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# A name that states elder/residential care itself. เนอร์สซิ่งโฮม with and
# without ร์ — both spellings are on real signs (พีดีเนอร์สซิ่งโฮม).
NURSING_NAME_RX = re.compile(
    r"บ้านพักคนชรา|สถานสงเคราะห์คนชรา|เนอร์?สซิ่งโฮม|ดูแลผู้สูงอายุ"
    r"|ดูแลผู้ป่วย|บ้านพักฟื้น|\bnursing\s*home\b|\bassisted\s*living\b"
    r"|\belder(?:ly)?\s*care\b|\bhospice\b|ฮอสพิซ", re.I)

# A name that states addiction medicine itself. ธัญญารักษ์ is the Department
# of Medical Services' own addiction-treatment hospital network — the name IS
# the institution. \brehab\b fenced from Rehabilitation (McKean, the SSO
# centre) and from กายภาพ entirely.
ADDICTION_NAME_RX = re.compile(
    r"บำบัดยาเสพติด|ยาเสพติด|เลิกเหล้า|เลิกยา|ธัญญารักษ์"
    r"|\bdetox\b|\baddiction\b|\bsober\b|\brehab\b(?!ilitat)", re.I)


def longcare_hit(t):
    """Raw OSM tags -> True if the element's TAGS state residential or
    long-stay care. The mapper's statement, nothing read off a name except
    where group_home needs the sign to say who it is for."""
    sf = t.get("social_facility")
    sfor = t.get("social_facility:for") or ""
    if sf in ("nursing_home", "assisted_living", "rehabilitation"):
        return True
    if sf == "group_home":
        if "senior" in sfor:
            return True
        name = " ".join(v for k, v in t.items() if k.startswith("name"))
        return bool(NURSING_NAME_RX.search(name))
    if t.get("amenity") == "nursing_home":
        return True
    if t.get("healthcare") in ("nursing_home", "hospice"):
        return True
    return False


def names_of(r):
    return " ".join(str(v) for v in
                    (r.get("name"), r.get("nameTh"), r.get("nameEn")) if v)


def main():
    recs = []
    for prov in ("cm", "cr"):
        for r in json.loads((ROOT / "data" / "canonical" / f"{prov}.json").read_text()):
            recs.append((prov, r))
    by_id = {r["id"]: (p, r) for p, r in recs}
    bad = 0

    print(f"== 1 · the long-care shelf — {len(recs):,} records ==")
    shelf = [(p, r) for p, r in recs
             if r.get("attrs", {}).get("facilityType") == "long-care"]
    print(f"   {len(shelf)} record(s) stand on medical/long-care")
    for p, r in shelf:
        print(f"   {p} | {names_of(r)[:64]} | {r['id']}")
    if not shelf:
        print("   ZERO — the classify() rule is not running; the shelf child "
              "in categories.json now matches nothing")
        bad = 1

    print("\n== 2 · the elder-care name scan ==")
    hits = [(p, r) for p, r in recs if NURSING_NAME_RX.search(names_of(r))]
    print(f"   {len(hits)} record(s) state elder care in their own sign")
    for p, r in hits:
        onshelf = "on-shelf" if (p, r) in shelf else "OFF-SHELF"
        print(f"   {p} | {onshelf} | {names_of(r)[:58]} | {r['id']}")

    print("\n== 3 · the addiction name scan ==")
    hits = [(p, r) for p, r in recs if ADDICTION_NAME_RX.search(names_of(r))]
    print(f"   {len(hits)} record(s) state addiction medicine in their own sign")
    for p, r in hits:
        spec = (r.get("attrs", {}).get("specialty") or [])
        print(f"   {p} | specialty={','.join(spec) or '—'} | "
              f"{names_of(r)[:52]} | {r['id']}")

    print("\n== 4 · the register — data/curated/longcare.json ==")
    reg = json.loads((ROOT / "data" / "curated" / "longcare.json").read_text())
    rows = reg.get("rows") or []
    grades = {}
    for row in rows:
        grades[row.get("grade", "?")] = grades.get(row.get("grade", "?"), 0) + 1
        for pid in row.get("placeIds") or []:
            if pid not in by_id:
                print(f"   UNRESOLVED place id {pid} in row "
                      f"{row.get('key')} — a page row silently missing")
                bad = 1
        if not row.get("grade"):
            print(f"   row {row.get('key')} carries NO GRADE — the grade is "
                  "the point and rides every row")
            bad = 1
        if row.get("grade") in ("stated",) and not row.get("src"):
            print(f"   row {row.get('key')} is graded `stated` with no "
                  "source — a stated row cites where it was read")
            bad = 1
    print(f"   {len(rows)} row(s): " +
          " · ".join(f"{k} {v}" for k, v in sorted(grades.items())))

    print("\n== 5 · the census of silences (what no record says) ==")
    for label, rx in [
            ("พักฟื้น (convalescence)", r"พักฟื้น|convalescen"),
            ("dementia / memory care", r"dementia|อัลไซเมอร์|ความจำเสื่อม|memory care"),
            ("palliative / hospice", r"palliative|ประคับประคอง|hospice|ฮอสพิซ"),
            ("home care ที่บ้าน", r"ดูแลที่บ้าน|home care|homecare"),
            ("เลิกเหล้า-เลิกบุหรี่ (quit lines)", r"เลิกเหล้า|เลิกบุหรี่"),
    ]:
        n = sum(1 for p, r in recs if re.search(rx, names_of(r), re.I))
        print(f"   {label}: {n}")

    sys.exit(bad)


if __name__ == "__main__":
    main()
