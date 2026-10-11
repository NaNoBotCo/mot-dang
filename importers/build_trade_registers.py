#!/usr/bin/env python3
"""WO-57/58 — the CMHY trades, turned into shelf records. One table, many trades.

WO-54 wrote this once for the paper trades and WO-56 again for physio. The
third time it is a table: each job names the categories already read by
importers/cmhy.py, the shelf a record lands on, the words that put it
there, and the words that refuse it. Everything else is shared —
snapshot-first reads, same-shelf dedupe by distance, hours from the
directory marked `_hoursSource`, the directory's dateModified as
sourceUpdated, `needs-pin` where the directory publishes no GPS.

  python3 importers/build_trade_registers.py dental vets mend …
  python3 importers/build_trade_registers.py --all

Writes data/curated/<job>.json (the register: every row kept, so the page
can print the denominator, the refusals and the matches) and appends
records to additions-chiang-mai.json.

A DIRECTORY IS NOT A FIRST-HAND SOURCE. Its service tags stay in the
register and are printed at the `listed` grade; they never enter
enrich.json, which is reserved for a place's own site (that file says so
itself). The trade decision uses the row's OWN name and tags — never the
directory's category alone, because CMHY files a language school under
translation and a camera shop under photo studio.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cmhy  # noqa: E402
import cmhy_records as cr  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TODAY = "2026-09-04"

# job -> {trade: (cat, sub, kind, words)}, plus `refuse` words checked first
# and `facility` where the shelf child matches on attrs.facilityType.
JOBS = {
    "dental": {
        # NOT "โรงพยาบาล". The first run refused โรงพยาบาลทันตกรรม
        # (คณะทันตแพทยศาสตร์) — the dental faculty's own dental hospital, the
        # largest dental facility in the north — for having the word hospital
        # in its name. The trade words below already require a dental word, so
        # a general hospital cannot reach them anyway.
        "refuse": [("แล็บ", "a dental laboratory — it makes the appliance, it does not treat"),
                   ("ทันตกรรมประดิษฐ์แล็บ", "a prosthetics lab")],
        "trades": {
            "dentist": ("medical", "dentist", "dental clinic",
                        ("ทันตกรรม", "ทันตแพทย์", "ทำฟัน", "หมอฟัน", "จัดฟัน", "อุดฟัน",
                         "ถอนฟัน", "ขูดหินปูน", "รากฟัน", "ฟันปลอม", "ฟันเทียม", "ครอบฟัน",
                         "วีเนียร์", "ฟอกสีฟัน", "dental", "dentist", "invisalign", "สไมล์", "smile")),
        },
        "facility": {"dentist": "dentist"},
        "facets": {"ortho": ("จัดฟัน", "invisalign", "จัดฟันใส", "retainer"),
                   "implant": ("รากฟันเทียม", "รากเทียม", "implant"),
                   "veneer": ("วีเนียร์", "veneer", "ฟอกสีฟัน", "whitening"),
                   "rootcanal": ("รักษารากฟัน", "root canal"),
                   "wisdom": ("ผ่าฟันคุด", "ฟันคุด"),
                   "denture": ("ฟันปลอม", "ฟันเทียม", "ใส่ฟัน", "ครอบฟัน"),
                   "kids": ("ทันตกรรมเด็ก", "หมอฟันเด็ก", "ฟันเด็ก"),
                   "xray3d": ("x-ray3d", "3d x-ray", "ct scan", "เอกซเรย์ 3 มิติ")},
    },
    "vets": {
        "refuse": [("โรงพยาบาลคน", "a people hospital")],
        "trades": {
            "vet": ("pets", "vet", "veterinary clinic",
                    ("สัตวแพทย์", "คลินิกสัตว์", "โรงพยาบาลสัตว์", "รักษาสัตว์", "หมอสัตว์",
                     "vet", "animal clinic", "animal hospital", "สัตวแพทยศาสตร์")),
            "grooming": ("pets", "grooming", "pet grooming",
                         ("อาบน้ำตัดขน", "ตัดขน", "อาบน้ำ", "groom", "สปาสัตว์")),
            # The sub was None from this rule's first day, because `pets` had
            # only vet and grooming children and there was nowhere to put a
            # shop. That left 64 records carrying attrs.kind "pet shop", ids
            # reading cm-curated-petshop-*, and no shelf — the trade named
            # itself in three places and reached a reader in none. The shelf
            # went up 2026-09-05 (pets/pet-shop) and the sub with it.
            "petshop": ("pets", "pet-shop", "pet shop",
                        ("ร้านสัตว์เลี้ยง", "อาหารสัตว์", "pet shop", "อุปกรณ์สัตว์เลี้ยง")),
        },
        "facets": {"exotic": ("สัตว์เอ็กโซติก", "exotic", "นก", "กระต่าย", "สัตว์เลื้อยคลาน"),
                   "open24": ("24 ชม", "24ชม", "24 ชั่วโมง", "24 hours"),
                   "housecall": ("ถึงบ้าน", "นอกสถานที่", "house call")},
    },
    # The first run refused 331 of 453 rows here for having "no trade word",
    # and the refusals were themselves trades: 31 rows say เปลี่ยนซิบ and 28
    # say แก้ทรง (that is WO-49's alterations shelf, not a mender), 14 say
    # อลูมิเนียม and 11 กระจก (the building trades repair/home was drawn for),
    # 9 ซ่อมทีวี, 8 หุ้มเบาะ, and a knife-sharpener trade nobody had a word
    # for. A refusal list that reads like a trade directory is a missing rule,
    # not a clean refusal — so each got the shelf a reader would look under.
    # ORDER MATTERS: alterations before mend (ซ่อมผ้า is cloth, not a shoe),
    # bicycle before motorbike words, and tech before the generic ซ่อม.
    "mend": {
        "refuse": [("ขายอลูมิเนียม", "sells aluminium by the length; not a fitter"),
                   ("จำหน่ายอุปกรณ์", "sells the part, does not fit it")],
        "trades": {
            "alterations": ("shopping", "alterations", "clothing alterations — zips, hems, taking in",
                            ("เปลี่ยนซิบ", "เปลี่ยนซิป", "แก้ทรง", "ซ่อมผ้า", "รับซ่อมผ้า", "ตัดขา",
                             "สอยขา", "ซ่อมกางเกง", "ซ่อมกระโปรง", "แก้เสื้อ", "ย้อมผ้า", "ปักเสื้อ",
                             "ปักโลโก้", "เย็บผ้า", "alteration")),
            "bicycle": ("transport", "bicycle", "bicycle shop and repair",
                        ("จักรยาน", "bicycle", "bike shop", "เสือภูเขา", "ซ่อมจักรยาน")),
            "sharpen": ("repair", "mend", "knife and clipper sharpening",
                        ("ลับคม", "ลับมีด", "ลับกรรไกร", "ลับปัตตาเลี่ยน", "ลับบัตเตอร์เลี่ยน", "sharpen")),
            "upholstery": ("repair", "home", "upholstery — sofas, seats, cushions",
                           ("หุ้มเบาะ", "ทำเบาะ", "ซ่อมโซฟา", "ซ่อมเบาะ", "upholster")),
            "tech": ("repair", "tech", "electronics repair — TVs, computers, CCTV",
                     ("ซ่อมทีวี", "ซ่อมคอมพิวเตอร์", "ซ่อมโน้ตบุ๊ก", "กล้องวงจรปิด", "cctv",
                      "ซ่อมมือถือ", "ซ่อมเครื่องเสียง", "ซ่อมปริ้นเตอร์")),
            "home": ("repair", "home", "home trades — aluminium, glass, steel, screens, roofing",
                     ("อลูมิเนียม", "กระจก", "มุ้งลวด", "บานเลื่อน", "บานสวิง", "งานเหล็ก",
                      "สแตนเลส", "สเตนเลส", "รางน้ำฝน", "กันสาด", "ประตูม้วน", "โรงกลึง",
                      "ปล่องดูดควัน", "ช่างเชื่อม", "หลังคา", "ระบบประปา", "ไฟฟ้า",
                      # The second refusal list was five air-con words deep:
                      # installing and washing a house air-conditioner is the
                      # single most-called home trade in this city, and it was
                      # refused for saying ล้าง (wash) rather than ซ่อม (mend).
                      "แอร์", "ล้างแอร์", "ติดตั้งแอร์", "เจาะบาดาล", "น้ำบาดาล",
                      "นั่งร้าน", "รับเหมา", "งานช่าง", "ตกแต่ง", "ปั๊มน้ำ", "แทงค์น้ำ")),
            "mend": ("repair", "mend", "mender — shoes, sewing machines, appliances, watches",
                     ("ซ่อมรองเท้า", "ซ่อมกระเป๋า", "ซ่อมจักร", "จักรเย็บผ้า", "ซ่อมเครื่องใช้ไฟฟ้า",
                      "ซ่อมแอร์", "ซ่อมตู้เย็น", "ซ่อมพัดลม", "ซ่อมนาฬิกา", "ซ่อมเครื่องมือ",
                      "ซ่อมร่ม", "ชุบรองเท้า", "ซ่อมมอเตอร์", "ซ่อมคอมเพสเซอร์", "repair")),
        },
        "facets": {"pickup": ("รับ-ส่ง", "บริการรับส่ง", "ถึงบ้าน"),
                   "sharpening": ("ลับคม", "ลับมีด", "ลับกรรไกร"),
                   "zip": ("เปลี่ยนซิบ", "เปลี่ยนซิป"),
                   "hem": ("ตัดขา", "สอยขา", "แก้ทรง")},
    },
    "laundry": {
        "refuse": [("ขายเครื่องซักผ้า", "sells washing machines, does not wash")],
        "trades": {
            "laundry": ("essentials", "laundry", "laundry — drop-off, coin or dry cleaning",
                        ("ซักรีด", "ซักอบรีด", "สะดวกซัก", "ซักผ้า", "รีดผ้า", "ซักแห้ง",
                         "laundry", "laundromat", "dry clean", "หยอดเหรียญ")),
        },
        "facets": {"coin": ("หยอดเหรียญ", "สะดวกซัก", "coin", "self service"),
                   "dryclean": ("ซักแห้ง", "dry clean"),
                   "pickup": ("รับ-ส่ง", "บริการรับส่ง", "delivery", "ถึงบ้าน"),
                   "open24": ("24 ชม", "24ชม", "24 ชั่วโมง", "24 hours")},
    },
    "motorbike": {
        "refuse": [("รถยนต์มือสอง", "used cars, not motorbikes")],
        "trades": {
            "motorbike": ("transport", "motorbike", "motorbike dealer or repair shop",
                          ("มอเตอร์ไซค์", "จักรยานยนต์", "รถมอไซค์", "motorcycle", "บิ๊กไบค์",
                           "ซ่อมมอเตอร์ไซค์", "ศูนย์บริการมอเตอร์ไซค์")),
            "rental": ("transport", "rental", "vehicle rental",
                       ("เช่ารถ", "รถเช่า", "car rental", "เช่ามอเตอร์ไซค์", "rent")),
        },
        "facets": {"bigbike": ("บิ๊กไบค์", "big bike"),
                   "ev": ("มอเตอร์ไซค์ไฟฟ้า", "ev", "ไฟฟ้า")},
    },
    "water-gas": {
        "refuse": [("ร้านอาหาร", "a restaurant that happens to sell gas cylinders")],
        "trades": {
            "utilities": ("essentials", "utilities", "drinking water or cooking-gas supplier",
                          ("น้ำดื่ม", "น้ำแร่", "ส่งน้ำ", "ตู้น้ำ", "แก๊สหุงต้ม", "ส่งแก๊ส",
                           "ร้านแก๊ส", "แก๊ส lpg", "ปั๊มแก๊ส", "gas", "water")),
        },
        "facets": {"delivery": ("ส่งถึงบ้าน", "ส่งน้ำ", "ส่งแก๊ส", "delivery", "ถึงบ้าน"),
                   "coin": ("หยอดเหรียญ", "ตู้น้ำ", "coin")},
    },
    "coworking": {
        "refuse": [("ร้านกาแฟ", None)],
        "trades": {
            "coworking": ("business", "coworking", "co-working space",
                          ("โคเวิร์กกิ้ง", "coworking", "co-working", "พื้นที่ทำงาน", "office space",
                           "ออฟฟิศให้เช่า", "meeting room", "ห้องประชุมให้เช่า")),
            "professional": ("business", "professional", "lawyer, accountant or notarial office",
                             ("ทนายความ", "สำนักงานกฎหมาย", "law", "lawyer", "บัญชี", "accounting",
                              "ตรวจสอบบัญชี", "จดทะเบียนบริษัท", "โนตารี", "notary", "วีซ่า")),
        },
        "facets": {"open24": ("24 ชม", "24ชม", "24 ชั่วโมง"),
                   "meeting": ("ห้องประชุม", "meeting room"),
                   "visaagent": ("วีซ่า", "visa", "work permit", "ใบอนุญาตทำงาน")},
    },
    "funeral": {
        "refuse": [],
        "trades": {
            "funeral": ("essentials", "funeral", "funeral supplies or services",
                        ("โลงศพ", "จัดงานศพ", "ฌาปนกิจ", "ฌาปนสถาน", "สังฆภัณฑ์", "หรีด",
                         "พวงหรีด", "งานศพ", "funeral", "coffin", "สุสาน", "ฮวงซุ้ย")),
        },
        "facets": {"wreath": ("หรีด", "พวงหรีด", "wreath"),
                   "cremation": ("ฌาปนสถาน", "เมรุ", "เผา", "crematorium"),
                   "chinese": ("ฮวงซุ้ย", "กงเต๊ก", "จีน")},
    },
}


def decide(job, row):
    spec = JOBS[job]
    own = cr.own(row)
    for word, why in spec["refuse"]:
        if word.lower() in own and why:
            return None, why
    for trade, (cat, sub, kind, words) in spec["trades"].items():
        if cr.has(own, words):
            return trade, ""
    return None, "no trade word in its own name or tags"


def facets_of(job, row):
    blob = cr.blob(row)
    return {k: True for k, words in (JOBS[job].get("facets") or {}).items()
            if cr.has(blob, words)}


def run(job):
    rows = cmhy.rows_of(job)
    if not rows:
        print(f"  {job}: nothing read — run python3 importers/cmhy.py {job}")
        return
    spec = JOBS[job]
    canon = cr.canonical("cm")
    register, out = [], []
    tally = {t: 0 for t in spec["trades"]}
    tally.update({"matched": 0, "refused": 0, "needs_pin": 0})
    for row in rows:
        trade, why = decide(job, row)
        entry = {"cmhy": row["id"], "name": row["name"], "tags": row["tags"],
                 "phone": row["phone"], "amphoe": row["amphoe"],
                 "modified": (row["modified"] or "")[:10], "trade": trade,
                 "facets": facets_of(job, row)}
        if trade is None:
            entry["refused"] = why
            tally["refused"] += 1
            register.append(entry)
            continue
        cat, sub, kind, _ = spec["trades"][trade]
        facility = (spec.get("facility") or {}).get(trade)
        near = None
        if row["lat"]:
            same = [r for r in canon
                    if (sub and sub in (r.get("sub") or []))
                    or (facility and (r.get("attrs") or {}).get("facilityType") == facility)]
            near, d = cr.near(float(row["lat"]), float(row["lng"]), same)
        if near is not None:
            entry["osm"] = near["id"]
            entry["metres"] = round(d)
            tally["matched"] += 1
            register.append(entry)
            continue
        if not row["lat"] and not (row.get("street") or row.get("amphoe")):
            entry["refused"] = "no published GPS and no address to stand on"
            tally["refused"] += 1
            register.append(entry)
            continue
        if not row["lat"]:
            tally["needs_pin"] += 1
        rid = f"cm-curated-{trade}-{row['id']}"
        entry["record"] = rid
        attrs = {"facets": entry["facets"]} if entry["facets"] else {}
        if facility:
            attrs["facilityType"] = facility
        out.append(cr.record(row, rid, cat, sub, kind, TODAY, job, attrs=attrs))
        tally[trade] += 1
        register.append(entry)
    n_new, n_touched = cr.upsert(out, "cm")
    reg = {
        "_readme": [
            f"WO-57/58 — the {job} register, from the CMHY.city read in cache/cmhy/{job}/.",
            "EVERY row is kept so the page can print the denominator, not just the hits.",
            "`trade` is decided by the row's OWN name and tags, never by the directory's",
            "category alone; `refused` says why a row is not a record; `osm` names the",
            "canonical record ALREADY ON THE SAME SHELF within 80 m that is this door.",
            "A DIRECTORY IS NOT A FIRST-HAND SOURCE: its service tags live here and print",
            "at the `listed` grade. They never enter enrich.json, which is for a place's",
            "own site. Hours carry `_hoursSource`; a row with no GPS is `needs-pin`.",
        ],
        "_built": TODAY, "counts": {**tally, "cmhy_rows": len(rows),
                                    "written_new": n_new, "touched": n_touched},
        "rows": register,
    }
    (ROOT / "data" / "curated" / f"{job}.json").write_text(
        json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"  {job}: {len(rows)} rows → " +
          " · ".join(f"{k} {v}" for k, v in tally.items() if v) +
          f" ({n_new} new records)")
    for e in register:
        if e.get("refused") and e["refused"] != "no trade word in its own name or tags":
            print(f"     refused: {e['name'][:40]} — {e['refused']}")


def main():
    jobs = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--all" in sys.argv:
        jobs = list(JOBS)
    for job in jobs:
        if job not in JOBS:
            print(f"  unknown job {job!r}; known: {', '.join(JOBS)}")
            continue
        run(job)


if __name__ == "__main__":
    main()
