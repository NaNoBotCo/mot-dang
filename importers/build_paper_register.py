#!/usr/bin/env python3
"""WO-54 — turn the paper-trade harvest into the register and the records.

Reads, zero network:
  cache/paper/places.json           read_paper_sites.py — CMHY.city, five categories
  cache/overpass/{cm,cr}/paper.json crawl_overpass.py --group paper — the OSM half
  data/canonical/{cm,cr}.json       to see what the catalogue already holds

Writes:
  data/curated/paper.json                       the register: every CMHY row kept
                                                (the denominator), the picks, the
                                                prices with where each was read,
                                                the refusals
  data/curated/additions-chiang-mai.json        cm-curated-* records for the picks
  data/curated/additions-chiang-rai.json        the one CR record no crawl carries

TWO VOICES, KEPT APART. A copy shop SELLS a copy (sub copyshop / printing);
a translator or visa agent PREPARES a document (sub translation / visa). CMHY
files both kinds under one "Business" heading and a language school under
"translation"; this script sorts by what the shop wrote on itself — its tags
and its name — and a school is refused, not re-shelved.

DEDUPE AGAINST OSM. A CMHY shop within 80 m of an OSM element in the same
trade is treated as the same door and not written again; the OSM record
carries it and the match is recorded in the register so the next pass can
enrich instead of duplicate. Distance, not name: a shop's Thai directory
name and its OSM English name rarely share a character.

  python3 importers/build_paper_register.py
"""
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import read_paper_sites as reader  # noqa: E402 — the cached HTML is re-read here, zero network

DAY = {"Monday": "Mo", "Tueday": "Tu", "Tuesday": "Tu", "Wednesday": "We", "Thursday": "Th",
       "Friday": "Fr", "Saturday": "Sa", "Sunday": "Su"}
ORDER = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


def hours_of(specs):
    """CMHY's openingHoursSpecification → an OSM-style string. 313 of 522
    pages carry one; the directory spells Tuesday 'Tueday' on every one."""
    if not specs:
        return ""
    parts = []
    for spec in specs:
        days = [DAY.get(d) for d in spec.get("dayOfWeek", []) if DAY.get(d)]
        o, c = spec.get("opens", ""), spec.get("closes", "")
        if not days or not o or not c:
            continue
        idx = sorted(ORDER.index(d) for d in set(days))
        runs, start, prev = [], idx[0], idx[0]
        for i in idx[1:]:
            if i == prev + 1:
                prev = i
                continue
            runs.append((start, prev)); start = prev = i
        runs.append((start, prev))
        span = ",".join(ORDER[a] if a == b else f"{ORDER[a]}-{ORDER[b]}" for a, b in runs)
        parts.append(f"{span} {o}-{c}")
    if parts == ["Mo-Su 00:00-23:59"] or parts == ["Mo-Su 00:00-00:00"]:
        return "24/7"
    return "; ".join(parts)


def page_extras(pid):
    """hours + the shop's own description, read off the cached page."""
    f = reader.CACHE / f"place-{pid}.html"
    if not f.exists():
        return "", ""
    html = f.read_text()
    lb = reader.local_business(html) or {}
    return hours_of(lb.get("openingHoursSpecification")), (lb.get("description") or reader.description(html) or "").strip()

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache" / "paper"
TODAY = "2026-09-04"

COPY_TAGS = ("ถ่ายเอกสาร", "ก๊อปปี้", "ก็อปปี้", "copy", "ปริ้น", "ปริ๊น", "print",
             "เข้าเล่ม", "เคลือบ", "สแกน", "แฟกซ์", "fax", "พิมพ์งาน", "รับพิมพ์")
PRINT_TAGS = ("โรงพิมพ์", "สิ่งพิมพ์", "ไวนิล", "ป้าย", "นามบัตร", "สติ๊กเกอร์",
              "สติกเกอร์", "ออฟเซ็ท", "offset", "การพิมพ์", "พิมพ์")
TRANS_TAGS = ("แปล", "translat", "รับรองเอกสาร", "กงสุล", "โนตารี", "notary",
              "ทะเบียนสมรส")
VISA_TAGS = ("วีซ่า", "visa")
SCHOOL_TAGS = ("สอนภาษา", "โรงเรียน", "สถาบัน", "เรียนต่อ", "คอร์ส", "ติว")
PHOTO_TAGS = ("รูปติดบัตร", "ถ่ายรูปติดบัตร", "รูปวีซ่า", "ถ่ายรูปด่วน", "รูปพาสปอร์ต",
              "ถ่ายรูปวีซ่า", "ภาพติดบัตร", "ถ่ายภาพติดบัตร", "ติดพาสปอร์ต")

FACET_OF = {
    "printphone": ("ไลน์", "line", "มือถือ", "ปริ้นออนไลน์", "ออนไลน์"),
    "binding": ("เข้าเล่ม", "เข้าห่วง", "สันกาว", "สันห่วง", "หุ้มปก", "อัดกาว"),
    "laminate": ("เคลือบ",),
    "scan": ("สแกน", "scan"),
    "bigformat": ("แบบแปลน", "พล๊อต", "พล็อต", "plot", "a3", "เอ3", "a2", "กระดาษไข"),
    "idphoto": PHOTO_TAGS,
    "certtrans": ("รับรองคำแปล", "ตราประทับ", "ประทับตรา", "แปลเอกสาร"),
    "mfarun": ("กงสุล", "กระทรวง", "นิติกรณ์", "สถานทูต"),
    "visaagent": ("รับยื่นวีซ่า", "ยื่นวีซ่า", "ทำวีซ่า", "บริการทำวีซ่า", "ต่อวีซ่า"),
    "open24": ("24 ชม", "24ชม", "24 ชั่วโมง", "24 hours"),
}


def dist_m(a, b, c, d):
    """Metres between two lat/lng pairs — good enough at 80 m."""
    r = 6371000.0
    p1, p2 = math.radians(a), math.radians(c)
    dp, dl = math.radians(c - a), math.radians(d - b)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def slug(name):
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s[:40] or "x"


def trade_of(row):
    """Which of the two voices this shop speaks, from its own words. None = refuse."""
    blob = (" ".join(row["tags"]) + " " + row["name"] + " " + row.get("desc", "")).lower()
    own = (" ".join(row["tags"]) + " " + row["name"]).lower()   # what it calls itself
    if "78" in row["cats"] and any(t in own for t in SCHOOL_TAGS) and "แปล" not in row["name"]:
        return None, "language school, not a translation counter"
    # A copy shop that also lists #แปลเอกสาร is a copy shop with a translation
    # facet, not a translation counter — the trade is what the shop is FOR.
    if "78" not in row["cats"] and any(t in own for t in COPY_TAGS) and any(t in own for t in TRANS_TAGS):
        return "copyshop", ""
    if "78" in row["cats"] or any(t in own for t in TRANS_TAGS):
        if any(t in blob for t in VISA_TAGS) and not any(t in blob for t in ("แปล", "translat")):
            return "visa", ""
        return "translation", ""
    if "95" in row["cats"]:
        # WO-54b: the photo shelf. The 4×6 immigration wants is made here, and
        # a camera shop that sells lenses is the same category on CMHY — the
        # idphoto facet (from the shop's own tags) is what separates them.
        return "photo", ""
    if any(t in blob for t in COPY_TAGS) or "79" in row["cats"] or "73" in row["cats"]:
        return "copyshop", ""
    if "80" in row["cats"] or any(t in blob for t in PRINT_TAGS):
        return "printing", ""
    return None, "no trade word on the record"


def facets_of(row):
    blob = (" ".join(row["tags"]) + " " + row["name"] + " " + row.get("desc", "")).lower()
    out = {}
    for key, words in FACET_OF.items():
        if any(w.lower() in blob for w in words):
            out[key] = True
    return out


def osm_doors(prov):
    f = ROOT / "cache" / "overpass" / prov / "paper.json"
    if not f.exists():
        return []
    out = []
    for e in json.loads(f.read_text()).get("elements", []):
        t = e.get("tags") or {}
        lat = e.get("lat") or (e.get("center") or {}).get("lat")
        lng = e.get("lon") or (e.get("center") or {}).get("lon")
        if lat is None:
            continue
        out.append({"id": f'{prov}-osm-{e["type"]}-{e["id"]}', "name": t.get("name", ""),
                    "lat": lat, "lng": lng,
                    "tag": t.get("shop") or t.get("craft") or t.get("office") or t.get("amenity") or ""})
    return out


def main():
    rows = json.loads((CACHE / "places.json").read_text())
    cm_osm = osm_doors("cm")
    cm_add_p = ROOT / "data" / "curated" / "additions-chiang-mai.json"
    cm_add = json.loads(cm_add_p.read_text())
    have = {r["id"] for r in cm_add}

    register, picks, refused, matched = [], [], [], []
    tally = {"copyshop": 0, "printing": 0, "translation": 0, "visa": 0, "photo": 0}
    pinless = 0
    # Two counters already have first-hand records (their own sites, prices);
    # the CMHY row lends them its pin and is not written a second time.
    FIRST_HAND = {"18975": "cm-curated-centa-care-translation",
                  "8483": "cm-curated-chiangmai-translation-service"}
    for row in rows:
        if row["id"] in FIRST_HAND and row["lat"]:
            for r in cm_add:
                if r["id"] == FIRST_HAND[row["id"]] and not r.get("lat"):
                    r["lat"], r["lng"] = float(row["lat"]), float(row["lng"])
                    r["geoPrecision"] = "approx"
                    r["attrs"]["pinVia"] = "directory-published-gps"
                    r["sources"].append({"type": "directory", "ref": row["url"], "fetched": TODAY,
                                         "note": "pin only"})
            continue
        trade, why = trade_of(row)
        entry = {"cmhy": row["id"], "name": row["name"], "tags": row["tags"],
                 "cats": row["cats"], "phone": row["phone"],
                 "lat": row["lat"], "lng": row["lng"], "amphoe": row["amphoe"],
                 "modified": row["modified"][:10], "trade": trade, "hits": row["hits"]}
        if trade is None:
            entry["refused"] = why
            refused.append(entry)
            register.append(entry)
            continue
        near = None
        # Same DOOR means same trade: a translation counter 60 m from a copy
        # shop is a different shop, not a duplicate of it.
        family = {"copyshop": ("copyshop", "printer", "printing", "paint"),
                  "printing": ("copyshop", "printer", "printing"),
                  "translation": ("translation", "translator", "visa"),
                  "visa": ("translation", "translator", "visa"),
                  "photo": ("photo", "photo_studio")}[trade]
        if row["lat"]:
            for o in cm_osm:
                if o["tag"] in family and dist_m(float(row["lat"]), float(row["lng"]), o["lat"], o["lng"]) < 80:
                    near = o
                    break
        if near:
            entry["osm"] = near["id"]
            matched.append(entry)
            register.append(entry)
            continue
        needs_pin = False
        if not row["lat"]:
            if not (row.get("street") or row.get("amphoe")) or not row["phone"]:
                entry["refused"] = "no published GPS and no address+phone to stand on"
                refused.append(entry)
                register.append(entry)
                continue
            # WO-54b: the CR-tailor shape — a tambon-level address, a phone,
            # and `needs-pin` so the map draws nothing rather than a guess.
            needs_pin = True
            pinless += 1
        tally[trade] += 1
        rid = f"cm-curated-paper-{row['id']}"
        entry["record"] = rid
        register.append(entry)
        picks.append(entry)
        hours, desc = page_extras(row["id"])
        tags_th = [t for t in row["tags"] if t]
        street = row.get("street") or ""
        if rid in have:
            # Second pass: hours and the shop's own paragraph, read off the
            # cached page; nothing else on an existing record is touched.
            for r in cm_add:
                if r["id"] == rid:
                    if hours and not r.get("hours"):
                        r["hours"] = hours
                    if desc:
                        r["attrs"]["desc"] = desc[:300]
                    r["attrs"]["facets"] = facets_of(row) or r["attrs"].get("facets", {})
            continue
        rec = {
            "id": rid, "province": "cm", "cat": ["essentials"], "sub": [trade],
            "name": row["name"], "nameEn": "",
            "address": ", ".join(x for x in (street, row.get("amphoe", ""), row.get("postcode", "")) if x),
            "phone": row["phone"], "website": row.get("site", ""), "hours": hours,
            "attrs": {"kind": {"copyshop": "copy & print counter", "printing": "print house",
                               "translation": "translation counter",
                               "visa": "visa agent", "photo": "photo studio"}[trade],
                      **({"desc": desc[:300]} if desc else {}),
                      "facets": facets_of(row), "tradeTags": tags_th,
                      "pinVia": "directory-published-gps"},
            "featured": False, "landmark": False,
            "blurb_th": "",   # no blurbs — Nan, 2026-09-06; tags carry the trade
            "blurb_en": "",
            "sources": [{"type": "directory", "ref": row["url"], "fetched": TODAY,
                         "sourceUpdated": row["modified"][:10]}],
            "confidence": "curated", "updatedAt": TODAY,
            "lat": None if needs_pin else float(row["lat"]),
            "lng": None if needs_pin else float(row["lng"]),
            "geoPrecision": "needs-pin" if needs_pin else "approx",
        }
        if needs_pin:
            rec["attrs"]["pinVia"] = "directory publishes no GPS — address only"
        cm_add.append(rec)
        have.add(rid)

    # The one Chiang Rai door no crawl carries: the immigration branch inside
    # Central Chiang Rai, "G floor, next to the Passport Office" in the
    # office's own words (moved 2023-09-18). Pinned at the passport office
    # OSM already holds, which is why it is `approx` and not `needs-pin`.
    cr_add_p = ROOT / "data" / "curated" / "additions-chiang-rai.json"
    cr_add = json.loads(cr_add_p.read_text())
    if not any(r["id"] == "cr-curated-immigration-central-chiangrai" for r in cr_add):
        cr_add.append({
            "id": "cr-curated-immigration-central-chiangrai", "province": "cr",
            "cat": ["essentials"], "sub": ["gov"],
            "name": "ตรวจคนเข้าเมืองจังหวัดเชียงราย ส่วนแยกเซ็นทรัล เชียงราย",
            "nameEn": "Chiang Rai Immigration — Central Chiang Rai branch",
            "address": "ชั้น G ศูนย์การค้าเซ็นทรัล เชียงราย (ฝั่งโรบินสัน ข้างสำนักงานหนังสือเดินทาง) ตำบลรอบเวียง อำเภอเมือง เชียงราย 57000",
            "phone": "053-731008 ต่อ 14", "website": "https://chiangrai.immigration.go.th/",
            "hours": "Mo-Fr 08:30-16:30",
            "attrs": {"kind": "immigration branch office",
                      "services": ["ต่อวีซ่า", "re-entry permit", "แจ้งที่พัก ตม.30", "รายงาน 90 วัน"],
                      "moved": "2023-09-18", "pinVia": "beside the passport office OSM holds"},
            "featured": False, "landmark": False,
            "blurb_th": "ต่อวีซ่า re-entry แจ้งที่พัก และรายงาน 90 วัน — ชั้น G เซ็นทรัล เชียงราย ข้างสำนักงานหนังสือเดินทาง ย้ายมาจาก อบจ. 18 ก.ย. 2566",
            "blurb_en": "Extensions, re-entry, TM30 and 90-day reports on the G floor of Central Chiang Rai, next to the passport office; moved here from the PAO on 18 Sep 2023. The main office stays in Mae Sai.",
            "sources": [{"type": "official", "ref": "https://chiangrai.immigration.go.th/ตม-จว-เชียงราย-ย้ายที่ทำ/",
                         "fetched": TODAY}],
            "confidence": "curated", "updatedAt": TODAY,
            "lat": 19.9300453, "lng": 99.8652225, "geoPrecision": "approx",
        })

    cm_add_p.write_text(json.dumps(cm_add, ensure_ascii=False, indent=1) + "\n")
    cr_add_p.write_text(json.dumps(cr_add, ensure_ascii=False, indent=1) + "\n")

    reg = json.loads((ROOT / "data" / "curated" / "paper.json").read_text()) \
        if (ROOT / "data" / "curated" / "paper.json").exists() else {}
    reg.update({
        "_built": TODAY,
        "counts": {"cmhy_rows": len(rows), "records_written": tally,
                   "matched_to_osm": len(matched), "refused": len(refused),
                   "osm_cm": len(cm_osm), "osm_cr": len(osm_doors("cr"))},
        "corpus": register,
    })
    (ROOT / "data" / "curated" / "paper.json").write_text(
        json.dumps(reg, ensure_ascii=False, indent=1) + "\n")
    reg["counts"]["needs_pin"] = pinless
    (ROOT / "data" / "curated" / "paper.json").write_text(
        json.dumps(reg, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(rows)} CMHY rows → records {tally} ({pinless} needs-pin); {len(matched)} already on the map "
          f"(OSM within 80 m); {len(refused)} refused")
    for e in refused[:12]:
        print(f"   refused: {e['name']} — {e['refused']}")


if __name__ == "__main__":
    main()
