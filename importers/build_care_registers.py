#!/usr/bin/env python3
"""WO-57 — the care trades hiding in CMHY's "other health services".

The WO-56 physio read pulled all 110 rows of category 53 and sorted the
physio clinics out of it. The other 81 rows were not noise: they hold the
city's nursing homes, its dialysis clinics, its hearing-aid centres and an
ambulance service, none of which the catalogue carries with a label.
WO-32's long-term-care register holds five mapped rows; this directory
alone names a dozen more, several stating dementia and bed-bound care in
their own tags.

Reads, zero network: cache/cmhy/physio/places.json + canonical.
Writes: additions-chiang-mai.json records, and the counts each register
        page prints. Grades stay the lens's job.

TRADE, FROM THE SHOP'S OWN WORDS, one row one trade:
  elder     เนอร์สซิ่งโฮม · ดูแลผู้สูงอายุ · ผู้ป่วยติดเตียง — WO-32's shelf
  dialysis  ไตเทียม · ฟอกไต · ล้างช่องท้อง
  ambulance รถพยาบาล
A row that says several is filed by the first of those it says, and the
others ride along as tradeTags — the lens reads the tags, not this file.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cmhy  # noqa: E402
import cmhy_records as cr  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TODAY = "2026-09-04"
JOB = "physio"

ELDER = ("เนอร์สซิ่งโฮม", "เนอสซิ่งโฮม", "เนิร์สซิ่งโฮม", "เนอร์ซิ่งโฮม", "nursing home",
         "ดูแลผู้สูงอายุ", "ผู้สูงอายุ", "ผู้ป่วยติดเตียง", "บ้านพักผู้สูงอายุ", "พักฟื้น",
         "ดูแลผู้ป่วย", "แผลกดทับ", "อัลไซเมอร์")
DIALYSIS = ("ไตเทียม", "ฟอกไต", "ฟอกเลือด", "ล้างช่องท้อง", "โรคไต", "ไตวาย")
AMBULANCE = ("รถพยาบาล", "ambulance")
DEMENTIA = ("อัลไซเมอร์", "สมองเสื่อม", "ความจำ", "dementia", "alzheim")
BEDBOUND = ("ติดเตียง", "แผลกดทับ", "ให้อาหารทางสายยาง", "อ๊อกซิเจน", "ออกซิเจน", "เจาะคอ")
# A resort or a property company that states elder care is still elder care;
# the tag it wrote is the evidence. A pharmacy that mentions ผู้สูงอายุ is not
# — it must say a care word, not just the word "old".
CARE_WORD = ("ดูแล", "เนอร์", "เนิร์", "nursing", "พักฟื้น", "ติดเตียง", "บ้านพัก")


def trade_of(row):
    own = cr.own(row)
    # AMBULANCE FIRST. An ambulance service tags itself with every errand it
    # drives to — "ส่งผู้ป่วยฟอกไต", takes dialysis patients — and the first
    # run filed สยามทรานฟอร์เซอร์วิส as a dialysis clinic on that word. What a
    # vehicle carries is not what a clinic does.
    if cr.has(own, AMBULANCE):
        return "ambulance"
    if cr.has(own, DIALYSIS):
        return "dialysis"
    if cr.has(own, ELDER) and cr.has(own, CARE_WORD):
        return "elder"
    return None


SUB = {"elder": ("medical", "long-care", "elder-care home"),
       "dialysis": ("medical", "clinic", "dialysis clinic"),
       "ambulance": ("medical", "clinic", "private ambulance service")}


def main():
    rows = cmhy.rows_of(JOB)
    if not rows:
        raise SystemExit("run: python3 importers/cmhy.py physio")
    canon = cr.canonical("cm")
    out, register = [], []
    tally = {"elder": 0, "dialysis": 0, "ambulance": 0, "matched": 0, "refused": 0}
    for row in rows:
        trade = trade_of(row)
        if trade is None:
            tally["refused"] += 1
            continue
        cat, sub, kind = SUB[trade]
        own = cr.own(row)
        entry = {"cmhy": row["id"], "name": row["name"], "trade": trade,
                 "phone": row["phone"], "modified": (row["modified"] or "")[:10],
                 "tags": row["tags"],
                 "dementia": cr.has(own, DEMENTIA), "bedbound": cr.has(own, BEDBOUND)}
        # Same door means same trade: only a canonical record already on this
        # trade's shelf can claim the row (the WO-56 lesson — a neighbour is
        # not a duplicate).
        near = None
        if row["lat"]:
            same = [r for r in canon
                    if (r.get("attrs") or {}).get("facilityType") == sub
                    or sub in (r.get("sub") or [])]
            near, d = cr.near(float(row["lat"]), float(row["lng"]), same)
        if near is not None:
            entry["osm"] = near["id"]
            entry["metres"] = round(d)
            tally["matched"] += 1
            register.append(entry)
            continue
        rid = f"cm-curated-{trade}-{row['id']}"
        entry["record"] = rid
        attrs = {"facilityType": sub} if sub in ("long-care",) else {}
        if entry["dementia"]:
            attrs["dementia"] = "stated in its own directory tags"
        if entry["bedbound"]:
            attrs["bedbound"] = "stated in its own directory tags"
        out.append(cr.record(row, rid, cat, sub, kind, TODAY, JOB, attrs=attrs,
                             blurb_en={
                                 "elder": "An elder-care home read off the cmhy.city directory; its own tags say what it takes.",
                                 "dialysis": "A dialysis clinic read off the cmhy.city directory; ring for chair times and which scheme it bills.",
                                 "ambulance": "A private ambulance service read off the cmhy.city directory."}[trade]))
        tally[trade] += 1
        register.append(entry)
    n_new, n_touched = cr.upsert(out, "cm")
    reg = {
        "_readme": [
            "WO-57 — the care trades inside CMHY category 53 (other health services), which the",
            "WO-56 physio read had already fetched: elder-care homes, dialysis clinics and one",
            "ambulance service. Trade is decided by the row's OWN name and tags, one row one trade;",
            "`dementia` and `bedbound` are true only where the place's own tags say so.",
            "Records land on medical/long-care (WO-32's shelf) and medical/clinic.",
            "A row within 80 m of a canonical record ALREADY ON THE SAME SHELF is that record.",
        ],
        "_built": TODAY, "counts": tally, "written_new": n_new, "touched": n_touched,
        "rows": register,
    }
    (ROOT / "data" / "curated" / "eldercare.json").write_text(
        json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(rows)} rows → {tally}; {n_new} new records, {n_touched} touched")
    for e in register:
        flags = "".join(x for x in ("D" if e["dementia"] else "", "B" if e["bedbound"] else ""))
        print(f"   {e['trade']:9s} {flags:2s} {e['name'][:44]:46s} {e.get('record') or e.get('osm','')}")


if __name__ == "__main__":
    main()
