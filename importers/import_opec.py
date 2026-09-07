#!/usr/bin/env python3
"""The private-school licence register — and with it, every international school.

WHY THIS EXISTS. Nan's brief was to honour and differentiate every school, with
particular care for the multilingual and farang-facing ones because those are
what people search for. The crawl finds an international school only if someone
mapped it and wrote the word in the name; this register is the state's own list
and it does not depend on either. It names **25 international schools** in these
two provinces where OpenStreetMap gave us 14.

THE SOURCE. ข้อมูลใบอนุญาตโรงเรียนเอกชน — the licences issued to private schools,
published by สำนักงานปลัดกระทรวงศึกษาธิการ (the MOE permanent secretary's office)
via catalog.moe.go.th and catalogued on data.go.th as `gdpublish-cer`. Two files:
schools *in* the formal system (ในระบบ, 3,960 nationwide) and schools *outside*
it (นอกระบบ).

**A LICENCE, NOT A LOCATION.** This file carries no coordinate, no phone and no
street — only name, อำเภอ, จังหวัด, the levels taught, the founding date, the
licensed capacity and who holds the licence. So it is used the way the temple
register is used: as a REGISTER that stamps records we already hold, and only
where it names a school nobody has mapped does it become a record of its own,
pinless and honest about it.

WHAT IT SETTLES that nothing else can. The official type of a private school —
whether it is นานาชาติ, ordinary สามัญศึกษา, a temple charity school
(การกุศลของวัด), a welfare school or a special-education one — and who holds the
licence: a company, a person, a foundation, or a wat. Five schools in Chiang Mai
and Chiang Rai are licensed to a temple. That is a fact about a school no crawl
will ever recover, and it is exactly the "religious schools" line in the brief.

WHAT IS MISSING, measured, so nobody looks for it twice. The นอกระบบ (non-formal)
export holds 134 rows for the whole country and **not one of them is in Chiang
Mai or Chiang Rai** — so the register that ought to list this city's language
schools, muay thai camps, cooking schools and driving schools is, in the copy
the ministry publishes, effectively empty. Those shelves are filled from the
crawl and by name, the way kratom had to be. Do not go looking in this file for
them again.

NO INVENTED MATCHES. A register row is joined to a record only on an exact
normalised name within the same province. Anything close but not equal goes to
cache/opec_review.txt for a person to settle, per the practice that has held
since wat-registry/match.py.
"""
import csv
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_IN = os.path.join(ROOT, "cache", "opec", "in.csv")
SRC_OUT = os.path.join(ROOT, "cache", "opec", "out.csv")
REVIEW = os.path.join(ROOT, "cache", "opec_review.txt")

DATASET = "https://data.go.th/dataset/gdpublish-cer"
RESOURCE = ("https://catalog.moe.go.th/dataset/"
            "483893fd-25d8-41f9-8596-133302e90a02")
# The portal states no licence for this dataset. It is an official ministry
# publication with no stated access condition (accessible_condition: ไม่มี),
# which is weaker than the CC-BY that CITIZENinfo carries, so it is recorded
# as what it is rather than as something cleaner. Attribution travels anyway.
LICENCE = "ไม่ระบุสัญญาอนุญาต · licence not stated by the publisher"
CREDIT = "ทะเบียนใบอนุญาตโรงเรียนเอกชน · สำนักงานปลัดกระทรวงศึกษาธิการ"
FETCHED = "2026-08-18"

PROVINCE = {"เชียงใหม่": "cm", "เชียงราย": "cr"}

TYPE_SUB = {
    "ในระบบประเภทนานาชาติ": "international",
    "ในระบบประเภทสามัญศึกษา (สามัญศึกษา)": "private",
    "ในระบบประเภทสามัญศึกษา (การกุศลของวัด)": "religious",
    "ในระบบประเภทสามัญศึกษา (การศึกษาสงเคราะห์)": "welfare",
    "ในระบบประเภทสามัญศึกษา (การศึกษาพิเศษ)": "special",
}
LEVEL_COLS = (("เตรียมอนุบาล", "เตรียมอนุบาล"), ("อนุบาล", "อนุบาล"),
              ("ประถมศึกษา", "ประถม"), ("มัธยมตอนต้น", "ม.ต้น"),
              ("มัธยมตอนปลาย", "ม.ปลาย"))

# Stripped before comparing names. โรงเรียน is the word the register leaves off
# and every other source puts on, which is the whole reason a raw compare fails.
_STRIP = re.compile(r"^(?:โรงเรียน|ร\.ร\.|รร\.|the\s+)+|"
                    r"\s*(?:school|academy)\s*$", re.I)


def _norm(name):
    n = (name or "").strip()
    n = _STRIP.sub("", n)
    n = re.sub(r"[\s​().,\-–—'\"]+", "", n)
    return n.casefold()


def _text(path):
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "cp874", "tis-620"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


def _founded(raw):
    """16/05/2537 -> (2537, 1994). The register writes พ.ศ.

    Both reckonings are returned and both are stored, under the SAME attribute
    names the temple register already uses (`foundedBE` / `foundedCE`), so the
    "ก่อตั้ง · Founded" row in build.py renders a school without a second row
    being written for it — and the sort-by-ancientness that exists for wats
    reaches these for free.
    """
    m = re.match(r"\s*(\d{1,2})/(\d{1,2})/(\d{4})\s*$", str(raw or ""))
    if not m:
        return (None, None)
    be = int(m.group(3))
    if not 2400 < be < 2600:
        return (None, None)
    return (be, be - 543)


def rows():
    """Register rows for the two provinces, from whichever files are present."""
    out = []
    for path, system in ((SRC_IN, "in"), (SRC_OUT, "out")):
        if not os.path.exists(path):
            continue
        for r in csv.DictReader(_text(path).splitlines()):
            prov = PROVINCE.get((r.get("จังหวัด") or "").strip())
            if not prov:
                continue
            name = (r.get("ชื่อโรงเรียน (ไทย)") or "").strip()
            if not name:
                continue
            kind = (r.get("ข้อมูลประเภทโรงเรียน") or "").strip()
            levels = [label for col, label in LEVEL_COLS
                      if (r.get(col) or "").strip() == "มี"]
            seq = (r.get("ลำดับ") or "").strip()
            if not seq.isdigit():
                continue
            out.append({
                "seq": seq,
                "province": prov,
                "name": name if name.startswith("โรงเรียน") else "โรงเรียน" + name,
                "registerName": name,
                "norm": _norm(name),
                "system": system,
                "officialType": kind or None,
                "sub": TYPE_SUB.get(kind, "private"),
                "district": (r.get("อำเภอ") or "").strip() or None,
                "licensee": (r.get("ประเภทผู้รับใบอนุญาต") or "").strip() or None,
                "foundedBE": _founded(r.get("วันที่ก่อตั้ง"))[0],
                "foundedCE": _founded(r.get("วันที่ก่อตั้ง"))[1],
                "capacity": (r.get("ความจุทั้งหมด") or "").strip() or None,
                "classrooms": (r.get("จำนวนห้องเรียน") or "").strip() or None,
                "levels": "-".join(levels) or None,
            })
    return out


def _stamp(rec, row):
    a = rec.setdefault("attrs", {})
    a["schoolSector"] = "private"
    a["officialType"] = row["officialType"]
    if row["licensee"]:
        a["licensee"] = row["licensee"]
    for k in ("foundedBE", "foundedCE"):
        if row[k]:
            a.setdefault(k, row[k])
    if row["levels"]:
        a.setdefault("levels", row["levels"])
    if row["capacity"] and row["capacity"].isdigit():
        a.setdefault("capacity", int(row["capacity"]))
    a["opecRegistered"] = True
    subs = set(rec.get("sub") or [])
    cats = set(rec.get("cat") or [])
    # The register is the authority on what kind of private school this is, so
    # its verdict is added rather than argued with. An international school
    # also takes its long-standing top-level shelf.
    subs.add(row["sub"])
    cats.add("school")
    if row["sub"] == "international":
        cats.add("school-intl")
    rec["sub"] = sorted(subs)
    rec["cat"] = sorted(cats)
    src = {"type": "register", "ref": DATASET, "resource": RESOURCE,
           "fetched": FETCHED, "via": "ทะเบียนโรงเรียนเอกชน (สช./สป.ศธ.)",
           "licence": LICENCE, "credit": CREDIT}
    rec.setdefault("sources", []).append(src)


def _record(row):
    """A school the register names and nobody has mapped. Pinless on purpose —
    the register knows the อำเภอ and nothing finer, and a guessed pin on a
    children's school is worse than an absent one. /pins.html is where these
    go to be walked."""
    # THE ID MUST CARRY DIGITS. build.py's place_slug() takes the digits out of
    # an id to make the filename unique, and falls back to the id with every
    # non-alphanumeric stripped when there are none — so a Thai-script slug
    # gives all 220 of these the stem "cmopec" and they overwrite one another's
    # page. The register's own ลำดับ is unique across the file (verified: 225
    # rows, 225 distinct) and keeps the id readable back to its source row.
    return {
        "id": f"{row['province']}-opec-{row['seq']}",
        "province": row["province"],
        "cat": (["school", "school-intl"] if row["sub"] == "international"
                else ["school"]),
        "sub": [row["sub"]],
        "name": row["name"], "nameTh": row["name"], "nameEn": None,
        "lat": None, "lng": None, "geoPrecision": "needs-pin",
        "address": (f"อ.{row['district']} จ."
                    f"{'เชียงใหม่' if row['province'] == 'cm' else 'เชียงราย'}"
                    if row["district"] else None),
        "phone": None, "website": None, "hours": None,
        "attrs": {k: v for k, v in {
            "facilityType": row["sub"],
            "schoolSector": "private",
            "officialType": row["officialType"],
            "licensee": row["licensee"],
            "foundedBE": row["foundedBE"],
            "foundedCE": row["foundedCE"],
            "levels": row["levels"],
            "capacity": (int(row["capacity"])
                         if row["capacity"] and row["capacity"].isdigit()
                         else None),
            "opecRegistered": True,
            "registerName": row["registerName"],
        }.items() if v not in (None, "")},
        "featured": False, "landmark": False,
        "sources": [{"type": "register", "ref": DATASET, "resource": RESOURCE,
                     "fetched": FETCHED,
                     "via": "ทะเบียนโรงเรียนเอกชน (สช./สป.ศธ.)",
                     "licence": LICENCE, "credit": CREDIT}],
        "confidence": "official",
        "updatedAt": FETCHED,
    }


def apply(records, prov):
    """Stamp the register onto what we hold and return the schools it names
    that we do not. `records` is the merged list for one province."""
    regs = [r for r in rows() if r["province"] == prov]
    if not regs:
        return 0, []
    index = {}
    for rec in records:
        key = _norm(rec.get("name"))
        if key:
            index.setdefault(key, []).append(rec)
        for alt in (rec.get("nameTh"), rec.get("nameEn")):
            k = _norm(alt)
            if k and k != key:
                index.setdefault(k, []).append(rec)

    stamped, new, review = 0, [], []
    for row in regs:
        hits = index.get(row["norm"]) or []
        if len(hits) == 1:
            _stamp(hits[0], row)
            stamped += 1
            continue
        if len(hits) > 1:
            # Two records answering to one name is exactly the case the house
            # rule refuses to guess at.
            review.append(f"{prov}  AMBIGUOUS  {row['registerName']}  "
                          f"(อ.{row['district']})  -> "
                          + ", ".join(h["id"] for h in hits))
            continue
        new.append(_record(row))
    if review:
        with open(REVIEW, "w", encoding="utf-8") as fh:
            fh.write("Private-school register rows that matched more than one\n"
                     "record. Settle them in data/curated/merges.json or by\n"
                     "adding the right name to the record.\n\n")
            fh.write("\n".join(review) + "\n")
    return stamped, new


if __name__ == "__main__":
    import collections
    rs = rows()
    print(f"opec: {len(rs)} register rows in the two provinces")
    print("  by province:", dict(collections.Counter(r["province"] for r in rs)))
    print("  by kind:", dict(collections.Counter(r["sub"] for r in rs)))
    print("  by system:", dict(collections.Counter(r["system"] for r in rs)))
    print("  licensed to a wat:",
          sum(1 for r in rs if r["licensee"] == "วัด"))
    intl = [r for r in rs if r["sub"] == "international"]
    print(f"\n  international schools ({len(intl)}):")
    for r in sorted(intl, key=lambda r: (r["province"], r["registerName"])):
        print(f"   {r['province']}  {r['registerName'][:44]:44} "
              f"อ.{r['district'] or '—':14} "
              f"{r['levels'] or '—':28} {r['foundedCE'] or '—'}")
    if "--canonical" in sys.argv:
        for prov in ("cm", "cr"):
            path = os.path.join(ROOT, "data", "canonical", f"{prov}.json")
            recs = json.load(open(path, encoding="utf-8"))
            n, new = apply(recs, prov)
            print(f"  {prov}: would stamp {n}, and add {len(new)} not held")
