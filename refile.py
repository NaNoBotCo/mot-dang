#!/usr/bin/env python3
"""Places filed where a reader would not look, moved to where they would.

Nan, 2026-10-17: "continue sorting the shelves until it's very intuitive", after
the Pantip read (pantip-coverage/shelf-plan-2026-10-16.txt) found shops Thai
readers ask about sitting on shelves nobody asking would open:

  gold     ~200 ร้านทอง / ห้างทอง on shopping/crafts, the Lanna crafts shelf,
           because Overture calls a gold shop jewelry_store. They move to
           shopping/gold. Silver, gem and watch shops stay where they are.
  parcel   courier branches (Flash, Kerry/KEX, J&T, SPX, Best, Nim, DHL) on the
           bus shelf, because Overture calls them `transportation`, and on
           business/professional and community/centre for the same reason.
           They move to essentials/parcel. Thailand Post stays on post.
  internet AIS, True, dtac, 3BB and NT shops on "Drinking Water & Cooking Gas"
           (essentials/utilities) and on phone repair. They join
           essentials/internet; utilities is taken away, phone repair stays.
  cinema   Major Cineplex in Big C and Central Chiang Rai, at Central Festival
           and Airport Plaza, filed as events venues or malls. They move to
           whats-on/cinema, the shelf a reader opens to find a film.
  trades   repair/home holds builders, building materials, electricians and
           air-con fitters in one list. Each also joins its own shelf; `home`
           stays on them, because the trades question set (data/facets.json)
           reads repair/home.

Each rule reads the record's own NAME first and its directory category second,
writes `attrs.refiled` {shelf: "field: word"} as the receipt, and stamps cat
and sub as derived. Deterministic and idempotent; called from derive.PASSES.
"""
from __future__ import annotations

import re

SRC = "derived:refile-words"
_L, _R = r"(?<![a-z])", r"(?![a-z])"
_FIELDS = ("name", "nameTh", "nameEn")


def _words(r):
    return [(k, str(r.get(k))) for k in _FIELDS if r.get(k)]


def _first(rx, texts, skip=None):
    for k, t in texts:
        if skip is not None:
            t = skip.sub(" ", t)
        m = rx.search(t)
        if m:
            return f"{k}: {m.group(0).strip()}"
    return None


# ------------------------------------------------------------------- gold
# A gold shop says so in its name. ทอง alone is a common word (มังกรทอง a dragon,
# ทองหล่อ a road, จอมทอง a district), so the bare word counts only on a record
# a directory already calls a jewellery shop.
_GOLD = re.compile(rf"ห้าง\s*ทอง|ร้าน\s*ทอง|ห้าง\s*เพชร\s*ทอง|ร้าน\s*เพชร\s*ทอง|ทองคำ|ทอง\s*เยาวราช|"
                   rf"ทำทอง|ค้าทอง|ทองแท่ง|{_L}goldsmith{_R}|{_L}gold\s*shop{_R}", re.I)
_GOLD_SOFT = re.compile(rf"^ทอง|เยาวราช|ทอง|{_L}gold{_R}|โกลด์", re.I)
_JEWELLERY = {"jewelry_store", "jewelry_and_watches_manufacturer", "fashion_accessories_store"}
# A watch shop with ทอง in its name, a silver shop on Wualai, a district name.
_NOT_GOLD = re.compile(rf"นาฬิกา|{_L}watch|เครื่องเงิน|{_L}silver", re.I)
# Markets, roads and farm shops that carry ทองคำ or ทองดี as a name.
_NOT_GOLD_EVER = re.compile(rf"ตลาด|กาด|{_L}market|เกษตร|ยนต์|ถนน|ซอย", re.I)


def gold(r):
    texts = _words(r)
    words = " ".join(t for _, t in texts)
    if _NOT_GOLD_EVER.search(words):
        return None
    if _NOT_GOLD.search(words) and not re.search(r"ห้าง\s*ทอง|ร้าน\s*ทอง", words):
        return None
    why = _first(_GOLD, texts)
    if why:
        return why
    if (r.get("attrs") or {}).get("overtureCategory") in _JEWELLERY:
        return _first(_GOLD_SOFT, texts)
    return None


# ----------------------------------------------------------------- parcel
_COURIER = re.compile(
    rf"flash\s*(?:express|home)|แฟลช\s*(?:โฮม|เอ็กซ์)|{_L}kerry{_R}|เคอรี่|{_L}kex{_R}|"
    rf"{_L}j\s*&\s*t{_R}|เจ\s*แอนด์\s*ที|{_L}spx{_R}|shopee\s*x?press|best\s*express|เบสท์\s*เอ็กซ์|"
    rf"ninja\s*van|นินจา\s*แวน|{_L}dhl{_R}|นิ่ม\s*เอ็กซ์|nim\s*express|ไปรษณีย์เอกชน|"
    rf"รับ\s*-?\s*ส่ง\s*พัสดุ|ส่งพัสดุ|ขนส่งพัสดุ|จัดส่งพัสดุ", re.I)
# A noodle shop in front of the post office, a box seller, an ECU remap.
_NOT_PARCEL = re.compile(r"หน้า\s*(?:ไปรษณีย์|ปณ)|หลัง\s*(?:ไปรษณีย์|ปณ)|ข้าง\s*(?:ไปรษณีย์|ปณ)|"
                         r"กล่องไปรษณีย์|กล่องพัสดุ|reflash|remap", re.I)
_POST = re.compile(r"ไปรษณีย์|thailand\s*post|ปณ\.|{0}ems{1}".format(_L, _R), re.I)
# Shelves the directory gave a courier for want of a better word. The move
# takes these away; any other shelf (a café that also takes parcels) stays.
_GENERIC = {("transport", "bus"), ("transport", None), ("business", "professional"),
            ("community", "centre"), ("shopping", "mall")}
_GENERIC_DIR = {"transportation", "professional_services", "party_and_event_planning",
                "community_services_non_profits", "shopping", "rental_service",
                "freight_and_cargo_service", "shipping_center", "courier_and_delivery_services",
                None}


def parcel(r):
    texts = _words(r)
    words = " ".join(t for _, t in texts)
    if _NOT_PARCEL.search(words):
        return None
    return _first(_COURIER, texts)


# --------------------------------------------------------------- internet
_TELCO = re.compile(
    rf"{_L}ais{_R}|เอไอเอส|true\s*(?:shop|move|online)|ทรู\s*(?:ช็อป|ชอป|มูฟ|ออนไลน์)|"
    rf"{_L}dtac{_R}|ดีแทค|(?<![a-z0-9])3bb{_R}|ทรีบีบี|โทรคมนาคมแห่งชาติ|ทีโอที|{_L}tot{_R}|"
    rf"cat\s*telecom|^nt{_R}|{_L}nt\s*(?:shop|สาขา|broadband)", re.I)
_TELCO_DIR = {"telecommunications_company", "internet_service_provider",
              "television_service_providers", "mobile_phone_store", "electronics", None, "shopping"}
_NOT_TELCO = re.compile(rf"{_L}(?:villa|house|garage|cafe|playground|oyster|computer){_R}|คาเฟ่|อาคาร|"
                        rf"เกสท์|ลานจอด|กสทช", re.I)


def internet(r):
    texts = _words(r)
    words = " ".join(t for _, t in texts)
    if _NOT_TELCO.search(words):
        return None
    if (r.get("attrs") or {}).get("overtureCategory") not in _TELCO_DIR:
        return None
    return _first(_TELCO, texts)


# ----------------------------------------------------------------- cinema
_CINEMA = re.compile(rf"cineplex|ซีนีเพล็ก|ซีนีเพล็กซ์|{_L}sf\s*(?:cinema|x){_R}|{_L}sfx{_R}|"
                     rf"เอส\s*เอฟ\s*(?:ซีเนม่า|เอ็กซ์)|โรงภาพยนตร์|โรงหนัง|{_L}cinemas?{_R}", re.I)
_NOT_CINEMA = re.compile(r"ร้าน|คาเฟ่|{0}cafe{1}|ลานจอด|parking|ป้ายรถ".format(_L, _R), re.I)


def cinema(r):
    texts = _words(r)
    if _NOT_CINEMA.search(" ".join(t for _, t in texts)):
        return None
    return _first(_CINEMA, texts)


# ----------------------------------------------------------------- trades
_TRADES = {
    "builder": (re.compile(r"รับเหมา|รับสร้างบ้าน|สร้างบ้าน|ต่อเติม|ก่อสร้าง(?!.*วัสดุ)(?<!วัสดุก่อสร้าง)|"
                           rf"{_L}(?:contractor|construction|builders?){_R}", re.I),
                {"construction_services", "contractor", "masonry_concrete", "roofing", "carpenter"}),
    "materials": (re.compile(r"วัสดุก่อสร้าง|ค้าวัสดุ|วัสดุภัณฑ์|ฮาร์ดแวร์|กระเบื้อง|ไทวัสดุ|โกลบอล\s*เฮ้าส์|"
                             r"โฮมโปร|ดูโฮม|บุญถาวร|ค้าเหล็ก|เหล็กเส้น|ค้าไม้|โรงไม้|ซีเมนต์|ปูนซีเมนต์|เครื่องมือช่าง|"
                             rf"{_L}(?:hardware|global\s*house|thai\s*watsadu|homepro|dohome|boonthavorn){_R}", re.I),
                  {"building_supply_store", "hardware_store", "home_improvement_store",
                   "lumber_store", "metal_supplier"}),
    # Name only: Overture's `electrician` holds a café and a college department.
    "electric-plumbing": (re.compile(r"ช่างไฟ|ซ่อมไฟ|งานไฟฟ้า|ระบบไฟฟ้า|ไฟฟ้า\s*-?\s*ประปา|ประปา|ปั๊มน้ำ|"
                                     rf"{_L}(?:electrician|plumb\w*){_R}", re.I),
                          set()),
    "aircon": (re.compile(rf"แอร์|{_L}air\s*-?\s*con\w*|{_L}hvac{_R}", re.I),
               {"hvac_services", "commercial_refrigeration"}),
}
# The electricity authority's own offices are on utilities, not trades.
_NOT_TRADE = re.compile(r"การไฟฟ้า|การประปา|เครื่องใช้ไฟฟ้า|วิทยาลัย|โรงเรียน|กาแฟ|{0}cafe{1}|{0}coffee{1}|{0}pea{1}|{0}pwa{1}|แอร์พอร์ต|airport".format(_L, _R), re.I)


def trades(r):
    texts = _words(r)
    words = " ".join(t for _, t in texts)
    if _NOT_TRADE.search(words):
        return {}
    oc = (r.get("attrs") or {}).get("overtureCategory")
    got = {}
    for sub, (rx, dirs) in _TRADES.items():
        why = _first(rx, texts)
        if not why and oc in dirs:
            why = f"overtureCategory: {oc}"
        if why:
            got[sub] = why
    return got


# ------------------------------------------------------------------ apply

def apply(records: list, prov: str, counts: dict | None = None, today: str = "") -> int:
    import provenance
    c = counts if counts is not None else {}
    written = 0

    def bump(k):
        c[k] = c.get(k, 0) + 1

    def receipt(r, fields):
        if not any(provenance.source_key(s) == SRC for s in r.get("sources") or []):
            r.setdefault("sources", []).append(
                {"type": "derived", "via": "refile-words", "fetched": today})
        for f in fields:
            if f in provenance.TRACKED and r.get(f):
                provenance.stamp(r, f, SRC, provenance.DERIVED, today)

    def file(r, cat, sub, why, drop=()):
        cats, subs = list(r.get("cat") or []), list(r.get("sub") or [])
        for dc, ds in drop:
            if ds is None:
                continue
            if ds in subs:
                subs.remove(ds)
        for dc, ds in drop:
            # A category goes only when none of its own shelves is left.
            if dc in cats and dc != cat and not _keeps(dc, subs):
                cats.remove(dc)
        if cat not in cats:
            cats.append(cat)
        if sub not in subs:
            subs.append(sub)
        changed = cats != (r.get("cat") or []) or subs != (r.get("sub") or [])
        r["cat"], r["sub"] = cats, subs
        attrs = r.setdefault("attrs", {})
        ref = dict(attrs.get("refiled") or {})
        key = f"{cat}/{sub}"
        if ref.get(key) != why:
            ref[key] = why
            attrs["refiled"] = ref
            changed = True
        if changed:
            receipt(r, ("cat", "sub"))
        return changed

    for r in records:
        cats = set(r.get("cat") or [])
        subs = set(r.get("sub") or [])
        oc = (r.get("attrs") or {}).get("overtureCategory")
        if not cats:
            continue

        if cats & {"shopping", "market"} or oc in _JEWELLERY:
            why = gold(r)
            if why:
                written += file(r, "shopping", "gold", why, drop=[("shopping", "crafts")])
                bump("refile/gold")

        why = parcel(r)
        if why:
            drop = [p for p in _GENERIC if oc in _GENERIC_DIR]
            written += file(r, "essentials", "parcel", why, drop=drop)
            bump("refile/parcel")
            if not _POST.search(" ".join(t for _, t in _words(r))) and "post" in (r.get("sub") or []):
                r["sub"] = [s for s in r["sub"] if s != "post"]
                receipt(r, ("sub",))

        if cats & {"whats-on", "shopping"} and "cinema" not in subs:
            why = cinema(r)
            if why:
                written += file(r, "whats-on", "cinema", why,
                                drop=[("whats-on", "events-venue"), ("shopping", "mall")])
                bump("refile/cinema")

        if cats & {"essentials", "repair", "shopping"}:
            why = internet(r)
            if why:
                written += file(r, "essentials", "internet", why,
                                drop=[("essentials", "utilities"), ("shopping", "mall")])
                bump("refile/internet")

        if "repair" in cats and "home" in subs:
            for sub, why in trades(r).items():
                written += file(r, "repair", sub, why)
                bump(f"refile/{sub}")
    return written


# Which category each sub a record can be left holding belongs to, for the
# question "does this category still have a shelf on this record". Read once
# from data/categories.json.
_SUBS_OF = None


def _keeps(cat, subs):
    global _SUBS_OF
    if _SUBS_OF is None:
        import json
        from pathlib import Path
        doc = json.loads((Path(__file__).resolve().parent / "data" / "categories.json").read_text())
        _SUBS_OF = {c["key"]: {(ch.get("match") or {}).get("sub") for ch in c.get("children", [])}
                    for c in doc["categories"]}
    return bool(_SUBS_OF.get(cat, set()) & set(subs))
