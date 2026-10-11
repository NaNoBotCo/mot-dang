#!/usr/bin/env python3
"""WO-74 — THE DRESS-HIRE SHELF. Zero network.

Nan, 2026-09-07, on a search for "thai clothing rentals photoshoot" that
returned som tam and a pharmacy chain:

    "We should have a better answer for this query. I'm pretty sure the
    information is available to us, but tags and discoverability not there."

She was right, and the measurement is the whole of this file's reason to
exist. WO-49 read CMHY's category 197-Rental-Dress-Shop on 2026-08-31 and
wrote all THIRTY-EIGHT rental houses into data/curated/tailor.json, each
with its own GPS, its phone, its hashtags and the directory's own
last-updated date. FOUR of them ever became records. The other thirty-four
have been sitting inside a research file that no page renders, no importer
reads and no index touches — held, not published, for seven days.

So the query did not fail for want of data. It failed three times over:

  1. THE RECORDS WERE NEVER ADMITTED. 34 shops with pins and phones,
     unreachable by any search, on any shelf, in the API, or on the map.
  2. THE SHELF DID NOT EXIST. The four that were admitted went on `tailor`
     — "ร้านตัดสูท-ตัดชุด · Tailors" — which is where you go to have a
     thing MADE. For anything worn once, this city rents; tailor.json's own
     note says so. A reader who wants to rent was being shelved with a
     trade that cuts.
  3. THE WORDS WERE THAI-ONLY. เช่าชุดไทย carried the paired English
     "Thai dress hire" on exactly two records. The four Lanna-costume photo
     studios carry ถ่ายภาพชุดล้านนา with NO gloss at all, so the index holds
     only the Thai and the RTGS reading "Thai Phap Chutlanna" — and an
     English speaker cannot reach a single one of them. Meanwhile the
     thesaurus has no group for `dress`, none for `costume`, none for
     `outfit`, and files ชุด (an outfit, a set) with "suite" and "unit".

FOUR TRADES SHARE ONE ENGLISH PHRASE, exactly as WO-49 found for `tailor`,
and this file keeps them apart on the same principle: a gown-and-uniform
house is not an answer to a Lanna-costume question, and a cabaret costumier
is not an answer to a wedding. The strands are `thai-lanna`,
`bridal-evening`, `gown-uniform` and `fancy-stage`, assigned from the
shop's OWN hashtags and from nothing else.

WHAT THIS FILE WILL NOT DO. It does not rank the shops. It does not carry a
price into a record — the prices in the register are quoted to their source
and marked unverified, because this directory has walked none of it. It does
not delete the nine shops CMHY marks "อาจจะปิดกิจการ" (may have closed or
moved): that is the directory's own sentence, it is carried as the
directory's own sentence, and a shop is not declared shut by a directory
note. And it invents no stall: the costume trade at Wat Ton Kwen's gate is
real and externally attested, but nobody has read a shop's name off it, so
it is a VENUE in the register and not a row of places with pins.

    python3 importers/build_dresshire_register.py            # report only
    python3 importers/build_dresshire_register.py --write    # register + records

Then: importers/import_all.py · importers/build_trade_lexicon.py · build.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TAILOR = ROOT / "data" / "curated" / "tailor.json"
PAPER = ROOT / "cache" / "paper" / "places.json"
ADDS = ROOT / "data" / "curated" / "additions-chiang-mai.json"
OUT = ROOT / "data" / "curated" / "dresshire.json"
CANON = ROOT / "data" / "canonical" / "cm.json"
TODAY = "2026-09-07"

# The words the trade writes on itself, with the English a reader would type.
# Each is a dictionary equivalence, not a description of a shop: เช่า is to
# rent, ชุด is an outfit, and ชุดไทย is the national formal dress. Where the
# gloss is a judgement rather than a translation it is not made here at all.
GLOSS = {
    "เช่าชุด": "dress hire",
    "ชุดเช่า": "dress hire",
    "ร้านเช่าชุด": "dress hire shop",
    "ร้านชุดเช่า": "dress hire shop",
    "เช่าชุดไทย": "Thai dress hire",
    "ชุดไทยเช่า": "Thai dress hire",
    "เช่าชุดล้านนา": "Lanna dress hire",
    "ชุดไทย": "Thai formal dress",
    "ชุดล้านนา": "Lanna dress",
    "ชุดพื้นเมือง": "northern local dress",
    "ชุดลูกทุ่ง": "luk thung stage dress",
    "ชุดราตรี": "evening gown",
    "เช่าชุดราตรี": "evening gown hire",
    "บริการเช่าชุดราตรี": "evening gown hire",
    "ชุดราตรีเช่า": "evening gown hire",
    "ราตรี": "evening gown",
    "ชุดออกงาน": "occasion wear",
    "ชุดแต่งงาน": "wedding dress",
    "เช่าชุดแต่งงาน": "wedding dress hire",
    "ให้เช่าชุดแต่งงาน": "wedding dress hire",
    "เช่าตัดชุดแต่งงาน": "wedding dress, hire or made",
    "ชุดพรีเวดดิ้ง": "pre-wedding shoot dress",
    "ชุดเพื่อนเจ้าสาว": "bridesmaid dress",
    "ชุดเพื่อเจ้าสาว": "bridesmaid dress",
    "เช่าชุดเพื่อนเจ้าสาว": "bridesmaid dress hire",
    "ชุดเพื่อนเจ้าบ่าว": "groomsman suit",
    "อุปกรณ์งานแต่งงาน": "wedding equipment",
    "ตั่งรดน้ำสังข์": "the water-pouring dais",
    "จัดงานแต่ง": "wedding organising",
    "ชุดครุย": "academic gown",
    "ตัดชุดครุย": "academic gowns, made",
    "ชุดข้าราชการ": "civil-service uniform",
    "ชุดราชการ": "civil-service uniform",
    "ชุดสูท": "suit",
    "สูท": "suit",
    "เช่าชุดสูท": "suit hire",
    "ร้านเช่าสูท": "suit hire shop",
    "ขายสูท": "sells suits",
    "ตัดสูท": "suits, made",
    "ร้านตัดสูท": "suit tailor",
    "ร้านสูท": "suit shop",
    "ใช้เช่าชุดทักซิโด": "tuxedo hire",
    "ให้เช่าชุดเดรส": "dress hire",
    "ชุดแฟนซี": "fancy dress",
    "ร้านเช่าชุดแฟนซี": "fancy dress hire shop",
    "เช่าชุดแฟนตาซี": "fancy dress hire",
    "ชุดการแสดง": "stage and performance dress",
    "ชุดเจ้าหญิง": "princess costume",
    "ชุดเจ้าชาย": "prince costume",
    "ชุดหลีด": "cheerleader kit",
    "ชุดลีดเดอร์": "cheerleader kit",
    "เชียร์ลึดเดอร์": "cheerleader kit",
    "เช่าชุดพรอม": "prom dress hire",
    "เช่าชุดงานพรอม": "prom dress hire",
    "งานพรอม": "prom",
    "รับจัดขบวนกีฬาสี": "sports-day parade outfitting",
    "รับเหมาขบวน": "parade outfitting, whole",
    "จัดขบวนแห่": "procession organising",
    "ชุดผู้หญิงเช่า": "women's dress hire",
    "ชุดสตรีเช่า": "women's dress hire",
    "เครื่องประดับ": "jewellery",
    "เครื่องประดับเช่า": "jewellery hire",
    "เชาเครื่องประดับ": "jewellery hire",
    "รับแต่งหน้า": "make-up done",
    "แต่งหน้าเจ้าสาว": "bridal make-up",
    "ช่างแต่งหน้า": "make-up artist",
    "ช่างถ่ายภาพ": "photographer",
    "สตูดิโอถ่ายภาพ": "photo studio",
    "ออกแบบทรงผม": "hair design",
    "สระไดร์": "wash and blow-dry",
    "ออกแบบท่าเต้น": "choreography",
    "ออกแบบเสื้อผ้า": "clothing design",
    "สอนรำไทย": "teaches Thai dance",
    "รำไทย": "Thai dance",
    "สอนดนตรีไทย": "teaches Thai music",
    "เสื้อผ้าแฟชั่น": "fashion clothing",
    "เสื้อผ้าสตรี": "women's clothing",
    "เสื้อผ้าผู้หญิง": "women's clothing",
    # the four costume photo studios' own tags, which had no gloss at all
    "ถ่ายภาพชุดล้านนา": "photographed in Lanna dress",
    "ถ่ายรูปชุดไทย": "photographed in Thai dress",
    "ถ่ายภาพล้านนา": "Lanna photography",
    "ถ่ายภาพย้อนยุค": "period photography",
    "ถ่ายภาพรูปครอบครัว": "family portraits",
    "ถ่ายรูปครอบครัว": "family portraits",
    "ถ่ายภาพหมู่คณะ": "group portraits",
    "ถ่ายภาพแต่งงาน": "wedding photography",
    "ถ่ายภาพรูปชุดถ่ายภาพข้าราชการ": "civil-service uniform portraits",
    "ถ่ายรูปชุดราชการ": "civil-service uniform portraits",
}

# Which strand a shop stands in, decided by its own hashtags, most specific
# first. A shop may stand in more than one — several do, and that is the
# truth about them rather than a filing error.
STRANDS = [
    ("thai-lanna", ["ชุดไทย", "ล้านนา", "ไทยเช่า", "พื้นเมือง", "ลูกทุ่ง", "รำไทย", "ไทยใหญ่"]),
    ("bridal-evening", ["ราตรี", "แต่งงาน", "เจ้าสาว", "เจ้าบ่าว", "ออกงาน", "พรอม",
                        "เวดดิ้ง", "ทักซิโด", "เดรส"]),
    ("gown-uniform", ["ครุย", "ข้าราชการ", "ราชการ", "สูท"]),
    ("fancy-stage", ["แฟนซี", "แฟนตาซี", "การแสดง", "หลีด", "ลีดเดอร์", "ลึดเดอร์",
                     "เจ้าหญิง", "เจ้าชาย", "ขบวน", "คาร์บาเร่"]),
]
STRAND_LABEL = {
    "thai-lanna": ("ชุดไทย · ชุดล้านนา", "Thai and Lanna dress"),
    "bridal-evening": ("ชุดแต่งงาน · ชุดราตรี", "Bridal and evening"),
    "gown-uniform": ("ชุดครุย · ชุดข้าราชการ · สูท", "Gowns, uniform and suits"),
    "fancy-stage": ("ชุดแฟนซี · ชุดการแสดง", "Fancy dress and stage"),
}
CLOSED_NOTE = "สถานที่นี้อาจจะปิดกิจการ หรือ ย้ายสถานที่"


def slugify(name):
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "x"


def clean_tag(t):
    return t.lstrip("#").replace("\r", " ").replace("\n", " ").strip()


def strands_of(tags, name):
    hay = " ".join(tags) + " " + name
    out = [k for k, words in STRANDS if any(w in hay for w in words)]
    return out or ["other"]


def facets_of(tags, name):
    hay = " ".join(tags) + " " + name
    f = {"rental": True}
    if any(w in hay for w in ("ชุดไทย", "ล้านนา", "พื้นเมือง", "ไทยใหญ่")):
        f["thaiformal"] = True
    if any(w in hay for w in ("แต่งงาน", "เจ้าสาว", "เวดดิ้ง")):
        f["bridal"] = True
    if any(w in hay for w in ("ราตรี", "ออกงาน", "พรอม", "เดรส")):
        f["eveningwear"] = True
    if any(w in hay for w in ("ครุย", "ข้าราชการ", "ราชการ")):
        f["uniform"] = True
    return f


def shop_id(s):
    """The CMHY place id is stable and already in the source URL."""
    m = re.search(r"/place/(\d+)-", s.get("src") or "")
    return f"cm-curated-dresshire-{m.group(1)}" if m else None


def read_shops():
    doc = json.loads(TAILOR.read_text())
    return doc["rent_or_cut"]["shops"], doc["rent_or_cut"], doc["corpus"]


def read_studios():
    """The photo studios whose own tags say they shoot you in Lanna dress."""
    if not PAPER.exists():
        return []
    rows = json.loads(PAPER.read_text())
    out = []
    for r in rows:
        if "95" not in (r.get("cats") or []):
            continue
        tags = [clean_tag(t) for t in (r.get("tags") or [])]
        if any(("ชุดล้านนา" in t or "ชุดไทย" in t or "ล้านนา" in t or "ย้อนยุค" in t)
               for t in tags):
            out.append({"cmhyId": r["id"], "name": r["name"], "tags": tags,
                        "tel": [x.strip() for x in (r.get("phone") or "").split(",") if x.strip()],
                        "addr": r.get("street") or "", "src": r.get("url"),
                        "gps": [float(r["lat"]), float(r["lng"])] if r.get("lat") else None,
                        "cmhy_updated": r.get("modified") or None})
    return out


def main():
    write = "--write" in sys.argv
    shops, block, corpus = read_shops()
    studios = read_studios()
    canon = {r["id"] for r in json.loads(CANON.read_text())}
    adds = json.loads(ADDS.read_text())
    # The four already admitted, matched on the CMHY place id in their source.
    already = {}
    for r in adds:
        for s in r.get("sources") or []:
            m = re.search(r"cmhy\.city/place/(\d+)-", s.get("ref") or "")
            if m:
                already[m.group(1)] = r["id"]

    rows, new = [], []
    for s in shops:
        cid = re.search(r"/place/(\d+)-", s.get("src") or "")
        cid = cid.group(1) if cid else None
        tags = [clean_tag(t) for t in (s.get("tags") or [])]
        tags = [t for t in tags if t]
        st = strands_of(tags, s["name"])
        addr = (s.get("addr") or "").replace(CLOSED_NOTE, "").strip()
        addr = re.sub(r"^ช่วยเราปรับปรุงข้อมูล\s*", "", addr).strip()
        flagged = CLOSED_NOTE in (s.get("addr") or "")
        row = {"name": s["name"], "strands": st, "tags": tags,
               "tagsEn": [GLOSS[t] for t in tags if t in GLOSS],
               "tel": s.get("tel") or [], "addr": addr, "gps": s.get("gps"),
               "src": s.get("src"), "cmhyUpdated": s.get("cmhy_updated"),
               "directorySaysMayHaveClosed": flagged,
               "placeId": already.get(cid) or shop_id(s)}
        rows.append(row)
        if cid in already or not cid:
            continue
        rid = shop_id(s)
        if rid in canon:
            continue
        rec = {
            "id": rid, "province": "cm", "cat": ["shopping"], "sub": ["dresshire"],
            "name": s["name"], "nameEn": None,
            "address": addr, "phone": (s.get("tel") or [None])[0],
            "website": "", "hours": "",
            "attrs": {
                "kind": "dress and costume hire",
                "facets": facets_of(tags, s["name"]),
                "tradeTags": tags,
                "tradeTagsEn": [GLOSS[t] for t in tags if t in GLOSS],
                "dressStrands": st,
                "pinVia": "directory-published-gps",
            },
            "featured": False, "landmark": False,
            "sources": [{"type": "directory", "ref": s["src"],
                         "fetched": "2026-08-31",
                         **({"sourceUpdated": s["cmhy_updated"]} if s.get("cmhy_updated") else {})}],
            "confidence": "curated", "updatedAt": TODAY,
        }
        if flagged:
            rec["attrs"]["directoryNoteTh"] = CLOSED_NOTE
            rec["attrs"]["directoryNoteEn"] = (
                "The directory itself marks this entry 'may have closed or moved' "
                "and asks readers to correct it. Carried as the directory's own "
                "sentence; nobody here has walked past to check.")
        if s.get("gps"):
            rec["lat"], rec["lng"] = s["gps"][0], s["gps"][1]
            rec["geoPrecision"] = "approx"
        else:
            rec["lat"] = rec["lng"] = None
            rec["geoPrecision"] = "needs-pin"
        new.append(rec)

    reg = {
        "_readme": [
            "WO-74 — the dress-hire shelf. Asked by Nan 2026-09-07 off a search for",
            '"thai clothing rentals photoshoot" that returned som tam, noodles and a',
            "pharmacy chain, with the line: I'm pretty sure the information is",
            "available to us, but tags and discoverability not there.",
            "",
            "It was available. WO-49 read all 38 of CMHY's rental houses on 2026-08-31",
            "into data/curated/tailor.json — GPS, phone, hashtags, the directory's own",
            "last-updated date — and 4 of them became records. The other 34 sat in a",
            "research file no page reads. This file admits them, on a shelf of their",
            "own, with the English words that make them reachable.",
            "",
            "FOUR TRADES, ONE ENGLISH PHRASE. A gown-and-uniform house is not an",
            "answer to a Lanna-costume question and a cabaret costumier is not an",
            "answer to a wedding, so the strands are kept apart and every shop is",
            "assigned from its OWN hashtags.",
            "",
            "NOT RANKED. NOT PRICED INTO A RECORD. The price bands below are quoted",
            "to their sources and unverified — nobody here has hired a costume. The",
            "nine shops CMHY marks 'may have closed or moved' are carried with that",
            "sentence attached, not deleted: a directory note is not a closure.",
        ],
        "asked_by": "Nan, 2026-09-07",
        "built": TODAY,
        "corpus": {
            "cmhy_rental_cm": corpus["cmhy_rental_cm"],
            "read_on": "2026-08-31 (WO-49)",
            "were_records_before_this": sum(1 for r in rows if r["placeId"] and not str(r["placeId"]).startswith("cm-curated-dresshire-")),
            "records_added_here": len(new),
            "with_directory_gps": sum(1 for r in rows if r["gps"]),
            "with_a_phone": sum(1 for r in rows if r["tel"]),
            "directory_says_may_have_closed": sum(1 for r in rows if r["directorySaysMayHaveClosed"]),
            "updated_2025_or_2026": sum(1 for r in rows if (r["cmhyUpdated"] or "") >= "2025"),
            "lanna_costume_photo_studios": len(studios),
            "note_en": ("The gap was never a gap in the corpus. Thirty-four shops with "
                        "pins and phone numbers were unreachable by any search, on any "
                        "shelf, in the API and on the map, because nothing had ever "
                        "carried them out of a research file."),
            "note_th": ("ข้อมูลมีอยู่แล้ว ร้านเช่าชุด 34 ร้านพร้อมพิกัดและเบอร์โทรอยู่ในไฟล์วิจัย "
                        "ไม่เคยถูกนำออกมาเป็นรายการ จึงค้นไม่เจอทั้งในเว็บ ในแผนที่ และใน API"),
        },
        "why_the_search_failed": {
            "query": "thai clothing rentals photoshoot",
            "measured": TODAY,
            "words": [
                {"word": "thai", "matched": 3321,
                 "note": ("Noise, and worse than noise: ถ่าย ('to take a photograph') "
                          "romanises to THAI under RTGS, so the reading of ถ่ายภาพ is "
                          "'Thai Phap' and every photo studio in the corpus matches the "
                          "word 'thai' for a reason that has nothing to do with Thailand.")},
                {"word": "clothing", "matched": 140,
                 "note": ("The thesaurus has no group for `dress`. Ban Or Jao's English "
                          "is 'Thai dress hire', so the reader's word never reached it.")},
                {"word": "rentals", "matched": 164,
                 "note": ("`rent`/`rental`/`hire`/`เช่า` ARE one thesaurus group — but the "
                          "group is the CAR one, and every rental house in this file was "
                          "off the shelf it would have ranked on.")},
                {"word": "photoshoot", "matched": 0,
                 "note": ("Zero in the corpus, zero in the thesaurus. The rarest word is "
                          "the question (go/guitar-bug); here the rarest word was also "
                          "the unanswerable one, so the AND collapsed and the page fell "
                          "back to ranking on 'thai'.")},
            ],
            "thesaurus_gaps_found": [
                "`dress` — no group at all",
                "`costume` — no group at all, 2 records anywhere",
                "`outfit` — no group at all",
                "`photoshoot`, `photo session` — no group at all",
                "ชุด (an outfit, a set) is grouped with `suite` and `unit` — a hotel word",
            ],
        },
        "words": {
            "note_en": ("The gloss column is what makes a Thai-only tag findable in "
                        "English. Before this file the four Lanna-costume studios "
                        "carried ถ่ายภาพชุดล้านนา with NO gloss, so the index held the "
                        "Thai and the reading 'Thai Phap Chutlanna' and nothing an "
                        "English speaker would ever type."),
            "list": [{"th": k, "en": v} for k, v in GLOSS.items()],
        },
        "strands": [{"key": k, "th": STRAND_LABEL[k][0], "en": STRAND_LABEL[k][1],
                     "n": sum(1 for r in rows if k in r["strands"])}
                    for k in STRAND_LABEL],
        "shops": rows,
        "studios": {
            "note_en": ("A rental house and a studio are two halves of the same "
                        "afternoon, and the reader who typed 'photoshoot' wanted both. "
                        "These stand on the `photo` shelf beside the passport-photo "
                        "trade, because that is the CMHY category they were read from "
                        "(95-Photo-Center, WO-54). ลานา ลานนา สตูดิโอ is both at once — "
                        "it hires the dress and takes the photograph — and was filed "
                        "only as a rental house."),
            "rows": studios,
        },
        "venues": {
            "note_en": ("Where people actually wear it. No stall here is a record: "
                        "nobody has read a shop's name off any of these pavements, and "
                        "this directory does not invent a pin. Listed so the register "
                        "does not pretend the trade is only the shops with doors."),
            "rows": [
                {"key": "wat-ton-kwen",
                 "placeIds": ["cm-osm-node-624114779", "cm-onab-03501509003"],
                 "th": "วัดต้นเกว๋น (วัดอินทราวาส) ต.หนองควาย อ.หางดง",
                 "en": "Wat Ton Kwen (Wat Inthrawat), Nong Khwai, Hang Dong",
                 "what_en": ("Costume stalls at the lane mouth and in front of the "
                             "temple. Thai-language reviews from 2025 and 2026 put a "
                             "Lanna outfit at about 150 baht with hair and jewellery "
                             "included, and a photographer as a separate half-hour "
                             "add-on. The temple became the city's costume-photograph "
                             "place after the drama กลิ่นกาสะลอง was filmed there."),
                 "grade": "listed",
                 "src": ["https://mgronline.com/local/detail/9690000036563",
                         "https://th.trip.com/moments/detail/hang-dong-14934-138402756/",
                         "https://www.lemon8-app.com/@euroanddollar0/7599949081254887937"],
                 "fetched": TODAY},
                {"key": "old-city-temples",
                 "placeIds": [],
                 "th": "วัดในเวียง — วัดเจดีย์หลวง วัดพระสิงห์ ประตูท่าแพ",
                 "en": "The old-city temples — Wat Chedi Luang, Wat Phra Singh, Tha Phae Gate",
                 "what_en": ("Where the packaged trade shoots. Booking platforms list "
                             "Chiang Mai costume-and-photographer packages from about "
                             "450–490 baht for the outfit with dressing and accessories, "
                             "half-day or full-day, with a photographer and make-up as "
                             "add-ons and two days' notice asked for the photographer."),
                 "grade": "listed",
                 "src": ["https://www.kkday.com/en-hk/category/th-chiang-mai/costume-rental/list",
                         "https://www.klook.com/en-IN/activity/87523-1-day-thai-costume-rental-rental-chiang-mai/",
                         "https://www.ticket2attraction.com/discount-tickets/thai-costume-dress-rental-chiang-mai/"],
                 "fetched": TODAY},
                {"key": "warorot",
                 "placeIds": [],
                 "th": "ตลาดวโรรส (กาดหลวง) — ผ้าและชุดพื้นเมือง",
                 "en": "Warorot Market (Kat Luang) — cloth and northern dress",
                 "what_en": ("The cloth end of the same trade: local cotton, phasin and "
                             "ready-made northern dress sold rather than hired, upstairs "
                             "in the market. Named here because a reader who wants to "
                             "OWN one is asking a different question from a reader who "
                             "wants one for an afternoon."),
                 "grade": "listed",
                 "src": ["https://www.wongnai.com/reviews/6fe306ade96c4f409c38eb4a789c9bc5"],
                 "fetched": TODAY},
            ],
        },
        "prices": {
            "_verified": False,
            "note_en": ("Quoted to whoever published them, never averaged, never put in "
                        "a record. Three price worlds sit in one trade and a reader "
                        "shown only one of them draws the wrong conclusion — the same "
                        "finding WO-49 recorded for gown hire."),
            "rows": [
                {"what_en": "Lanna outfit at the Wat Ton Kwen stalls, hair and jewellery included",
                 "baht": "~150", "who": "Thai-language reviews, 2025–2026",
                 "src": "https://th.trip.com/moments/detail/hang-dong-14934-138402756/"},
                {"what_en": "Photographer at Wat Ton Kwen, 30 minutes",
                 "baht": "~850", "who": "Thai-language review, 2026",
                 "src": "https://www.lemon8-app.com/@euroanddollar0/7599949081254887937"},
                {"what_en": "Old-city costume package, outfit with dressing and accessories",
                 "baht": "450–490 from", "who": "booking platforms, 2026",
                 "src": "https://www.kkday.com/en-hk/category/th-chiang-mai/costume-rental/list"},
                {"what_en": "White suit hire / civil-service uniform hire (The Great, Nimman Soi 3)",
                 "baht": "550 (dep. 1,000) / 650 (dep. 1,500)", "who": "the shop's own sheet, read 2026-08-31",
                 "src": "https://www.cmhy.city/place/13237-The-Great-Chiangmai"},
            ],
        },
        "asks": [
            {"th": "ชุดล้านนามีไหมคะ/ครับ เช่าครึ่งวันเท่าไหร่",
             "en": "Do you have Lanna dress? How much for half a day?"},
            {"th": "รวมแต่งหน้าทำผมด้วยไหมคะ/ครับ",
             "en": "Does that include hair and make-up?"},
            {"th": "เครื่องประดับรวมอยู่ในราคาไหมคะ/ครับ",
             "en": "Is the jewellery included in the price?"},
            {"th": "มัดจำเท่าไหร่ ขอใบรับด้วยได้ไหมคะ/ครับ",
             "en": "How much is the deposit — could I have a receipt?"},
            {"th": "คืนชุดกี่โมงคะ/ครับ เลยเวลาคิดเพิ่มเท่าไหร่",
             "en": "What time do I bring it back, and what's the late charge?"},
            {"th": "ใส่ไปถ่ายที่วัดได้ไหมคะ/ครับ ต้องคลุมไหล่ไหม",
             "en": "Can I wear it into a temple — do I need to cover my shoulders?"},
            {"th": "มีชุดผู้ชายไหมคะ/ครับ",
             "en": "Do you have men's outfits?"},
            {"th": "มีไซซ์ใหญ่ไหมคะ/ครับ",
             "en": "Do you carry larger sizes?"},
            {"th": "ถ่ายเองได้ไหม หรือต้องจ้างช่างของร้าน",
             "en": "May I take my own photographs, or must I hire your photographer?"},
        ],
        "refused": [
            {"what_en": "Ranking the shops, or naming a best costume-hire in Chiang Mai.",
             "why_en": ("WO-49's rule, and it holds harder here: every English 'top ten' "
                        "page in this trade is a booking platform's own inventory.")},
            {"what_en": "Declaring the nine 'may have closed' shops closed.",
             "why_en": ("That is CMHY's own note asking readers to correct it, not a "
                        "finding. It is carried with its Thai wording attached. Absence "
                        "of evidence is not evidence of absence.")},
            {"what_en": "Giving the Wat Ton Kwen stalls names, pins or records.",
             "why_en": ("The trade there is well attested and no stall's own name has "
                        "been read. A venue with citations is honest; six invented "
                        "pins would not be.")},
            {"what_en": "Putting any price on a place record.",
             "why_en": "Nobody here has hired a costume. The prices are quoted and flagged unverified.",
             },
            {"what_en": "Offering a gown-and-uniform house as an answer to a Lanna-dress question.",
             "why_en": "Four trades, one English phrase. Kept apart, as WO-49 kept the four tailoring trades apart.",
             },
        ],
        "unread": [
            {"name": "The Wat Ton Kwen stalls",
             "ref": "on the ground, ต.หนองควาย อ.หางดง",
             "reason": ("Named by reviewers, never by themselves. Needs a walk; there is "
                        "no page to read and no phone to call.")},
            {"name": "The Facebook and Instagram costume houses",
             "ref": "the old-city trade around Ratchadamnoen and Tha Phae",
             "reason": ("The visitor-facing half of this trade lives on Facebook and IG, "
                        "which CMHY does not index and a logged-out fetch does not "
                        "read. go/osm-not-first-truth: the blocker is mechanism.")},
            {"name": "cm-osm-node-624114779 vs cm-onab-03501509003",
             "ref": "data/canonical/cm.json",
             "reason": ("The same temple twice — วัดต้นเกว๋น from OSM at 18.7228/98.9253, "
                        "วัดอินทราวาส from the ONAB register at 18.7374/98.9151, which is "
                        "the pin of a pharmacy 1.6 km away. Neither record carries the "
                        "other's name, so half the readers looking for this temple find "
                        "a record that cannot tell them they have arrived. Found here, "
                        "not fixed here — it belongs with the shared-pin work.")},
        ],
        "sources": [
            {"type": "directory", "ref": "https://www.cmhy.city/category/33-Personal/197-Rental-Dress-Shop/",
             "fetched": "2026-08-31", "via": "WO-49, data/curated/tailor.json"},
            {"type": "directory", "ref": "https://www.cmhy.city/category/71-Business/95-Photo-Center/",
             "fetched": "2026-09-04", "via": "WO-54, cache/paper/places.json"},
            {"type": "press", "ref": "https://mgronline.com/local/detail/9690000036563",
             "fetched": TODAY, "note": "Songkran 2026 crowds hiring Lanna dress at Wat Ton Kwen"},
            {"type": "platform", "ref": "https://www.kkday.com/en-hk/category/th-chiang-mai/costume-rental/list",
             "fetched": TODAY, "note": "packaged costume-and-photographer prices"},
        ],
    }

    print(f"rental houses in the register : {len(rows)}")
    for k in STRAND_LABEL:
        print(f"   {k:16s} {sum(1 for r in rows if k in r['strands']):3d}  {STRAND_LABEL[k][1]}")
    print(f"   other            {sum(1 for r in rows if 'other' in r['strands']):3d}")
    print(f"already records before this   : {sum(1 for r in rows if r['placeId'] and not str(r['placeId']).startswith('cm-curated-dresshire-'))}")
    print(f"records this run would add    : {len(new)}")
    print(f"   with a directory pin       : {sum(1 for r in new if r.get('lat') is not None)}")
    print(f"   with a phone               : {sum(1 for r in new if r.get('phone'))}")
    print(f"   directory says may be shut : {sum(1 for r in new if 'directoryNoteTh' in r['attrs'])}")
    print(f"lanna-costume photo studios   : {len(studios)}")
    print(f"glosses                       : {len(GLOSS)}")

    if not write:
        print("\n(dry run — pass --write to write the register and the records)")
        return
    OUT.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    adds.extend(new)
    ADDS.write_text(json.dumps(adds, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(ROOT)}")
    print(f"wrote {len(new)} records into {ADDS.relative_to(ROOT)}  (now {len(adds)})")
    print("next: importers/import_all.py · importers/build_trade_lexicon.py · build.py")


if __name__ == "__main__":
    main()
