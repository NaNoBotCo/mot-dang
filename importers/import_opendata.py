#!/usr/bin/env python3
"""Fold WO-16's open lists into the catalogue — temples, sights, police,
LPG shops, certified muay thai camps. Reads data/curated/datagoth.json and the
ONAB register already on disk; never the network.

THE BIG ONE IS THE TEMPLES. The ONAB register (the same registry.db WO-1
joined) holds 1,486 Chiang Mai and 1,092 Chiang Rai registered temples; the
shelf holds 596 records, 346 of them matched to the register. The rest of the
register — about two thousand temples with a permanent code, a founding year,
a nikaya and a ตำบล/อำเภอ — was sitting on disk with no record to stand on.
This folds them, the same move that took schools 14 → 2,416 and medical
233 → 859. (The provincial CSV that reads "4,462 temples" is the SAME
~1,487 temples stacked three years deep — measured, 1,489 unique — so the
register and the province agree with each other.)

MATCHING, the house discipline: a register row becomes a NEW record only when
NO existing temple record answers to its name key (thairom.matchkey, the same
normaliser WO-1 used) in its province — after setting aside records already
stamped with a different code, which are spoken for. A row that any unstamped
record might be goes to the review file, never to a coin flip. Everything
non-temple deduplicates by a plain normalised-name key and the borderline goes
to the same file.

PINS: geocode_local, from our own ground only — for temples the ตำบล+อำเภอ
pair and the postcode tiers do the work; what cannot be placed says needs-pin
and appears on the pin hunt. A register tells us a temple exists and where it
is filed; only a person or a mapper tells us where it stands.

IDEMPOTENT BY CONSTRUCTION (the import_weedth lesson, paid for once already):
records() re-derives everything from the register and the harvest on every
run, with deterministic ids, and the dedup index EXCLUDES records in this
importer's own namespaces — so run two emits the same set instead of matching
the copies of itself from run one and silently emptying the shelf.

    python3 importers/import_opendata.py --report    # what would land, writes nothing
"""
import json
import os
import re
import sqlite3
import sys
import unicodedata
import zlib
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
PROJECTS = os.path.dirname(ROOT)
REGISTRY_DB = os.path.join(PROJECTS, "wat-registry", "registry.db")
sys.path.insert(0, os.path.join(PROJECTS, "wat-registry"))

# The springs' name rules (WO-23) — one copy, audit_hotsprings owns them.
# The eco/religious lists carry น้ำพุร้อนป่าตึง and บ่อน้ำร้อนแม่ขะจาน with
# no tags to speak for them, so the name is read there and nowhere else.
import audit_hotsprings as _hs  # noqa: E402

DATAGOTH = os.path.join(ROOT, "data", "curated", "datagoth.json")
WAT_JOIN = os.path.join(ROOT, "data", "curated", "wat_registry.json")
VERDICTS = os.path.join(ROOT, "data", "curated", "temple_verdicts.json")
REVIEW = os.path.join(ROOT, "cache", "opendata_review.txt")

ONAB_SOURCE = ("ONAB temple register (ทะเบียนวัด สำนักงานพระพุทธศาสนาแห่งชาติ), "
               "B.E. 2567 — Open Government Data of Thailand")
ONAB_CREDIT = "ทะเบียนวัด สำนักงานพระพุทธศาสนาแห่งชาติ (ONAB)"
PROVINCE_TH = {"cm": "เชียงใหม่", "cr": "เชียงราย"}
IS_TEMPLE = re.compile(r"^\s*(วัด|wat\b)", re.IGNORECASE)
# My id namespaces — the dedup index must never contain them (idempotency).
MINE = re.compile(r"^(cm|cr)-(onab|dgth)-")

try:
    from thairom import matchkey
except ImportError:                      # register absent: temple fold skips
    matchkey = None


def _norm(s):
    """Plain-name key for the non-temple folds: NFC, casefold, no spaces or
    punctuation. ครัวนฤตยะ and ครัวนฤตยะ  (trailing space) are one name."""
    s = unicodedata.normalize("NFC", s or "")
    s = s.replace("\xa0", " ")
    return re.sub(r"[\s\.\-·,()\"'’]+", "", s).casefold()


# Words that say WHAT KIND of shop, not WHICH shop. Stripped before the
# similar-name test, or every one of the 907 pharmacies named ร้านขายยา… is
# reported as "similar" to a held record literally called ร้านขายยา, and a
# review file nobody can finish is one nobody opens (the weed.th lesson: 92
# of 218 → 29 of 722 once the trade words came out).
NEAR_NOISE = re.compile(
    r"ร้านขายยา|ร้านยา|ห้องยา|เภสัชกร|เภสัช|ฟาร์มาซี|ฟาร์มา|ดรักส์|ดรัก|โอสถ|"
    r"drug ?store|pharmacy|ร้านอาหาร|ร้าน|บริษัท|จำกัด|หจก|สาขา|shop|store")
NEAR_MIN = 8


def _stem(k):
    """The distinctive part of a name — what is left when the trade words go."""
    return NEAR_NOISE.sub("", k)



def _sid(prov, src, *parts):
    """Deterministic id from the row's own facts, never its position.

    DECIMAL, not hex: place_slug() builds the page filename from the id's
    digits, and for a Thai-only name the digits are the whole stem — hex ids
    whose letters strip away can collide into one filename and silently
    overwrite each other's pages. Ten decimal digits cannot."""
    return "%s-dgth-%s-%010d" % (prov, src, zlib.crc32("|".join(parts).encode("utf-8")))


def _phone(text):
    m = re.search(r"0[\d\s\-]{7,12}\d", (text or "").replace("โทร.", " ").replace("โทรศัพท์:", " "))
    return re.sub(r"\s+", " ", m.group(0)).strip() if m else None


class _Gaz:
    """geocode_local, opened once, first use."""
    _g = None

    @classmethod
    def locate(cls, address, prov):
        if cls._g is None:
            from geocode_local import Gazetteer
            cls._g = Gazetteer()
        return cls._g.locate(address, prov)


def _pin(rec, address, prov):
    loc = _Gaz.locate(address, prov) if address else None
    if loc:
        rec["lat"], rec["lng"] = loc["lat"], loc["lng"]
        rec["geoPrecision"] = "approx"
        rec["attrs"]["pinVia"] = loc["via"]
        rec["attrs"]["pinUncertaintyM"] = str(loc["uncertainty_m"])
        rec["attrs"]["pinFrom"] = str(loc.get("matched") or "")
    else:
        rec["lat"] = rec["lng"] = None
        rec["geoPrecision"] = "needs-pin"
    return rec


def _canonical():
    out = {}
    for prov in ("cm", "cr"):
        p = os.path.join(ROOT, "data", "canonical", f"{prov}.json")
        out[prov] = json.loads(open(p, encoding="utf-8").read()) if os.path.exists(p) else []
    return out


def _load_datagoth():
    if not os.path.exists(DATAGOTH):
        return {}
    return json.load(open(DATAGOTH, encoding="utf-8")).get("sources") or {}


def _temples(canonical, review):
    """The register fold. Both provinces — the register is one source and the
    schools/medical folds were both-province moves; a Chiang Rai temple is not
    less real for the order having counted Chiang Mai's rows."""
    if matchkey is None or not os.path.exists(REGISTRY_DB):
        print("opendata: no ONAB register on disk — temple fold skipped")
        return [], set()
    joined_codes = set()
    if os.path.exists(WAT_JOIN):
        for reg in (json.load(open(WAT_JOIN, encoding="utf-8")).get("wats") or {}).values():
            joined_codes.add(reg.get("code"))
    # Rows a held record's own pin has REFUTED — proven to stand in a district
    # the held record is nowhere near, so they are separate temples and the
    # name collision was a coincidence. See importers/audit_temple_review.py
    # for the test and its measured error rate; it never picks, only refutes.
    released = {}
    if os.path.exists(VERDICTS):
        released = json.load(open(VERDICTS, encoding="utf-8")).get("released") or {}
    # Existing temple records by name key, minus mine; remember stamped codes.
    key_index = {"cm": {}, "cr": {}}
    for prov in ("cm", "cr"):
        for r in canonical[prov]:
            if MINE.match(r.get("id") or ""):
                continue
            names = [r.get("name") or "", r.get("nameTh") or "", r.get("nameEn") or ""]
            if not any(IS_TEMPLE.search(n) for n in names if n):
                continue
            k = matchkey(names[1] or names[0] or names[2])
            if not k:
                continue
            code = (r.get("attrs") or {}).get("watCode")
            key_index[prov].setdefault(k, []).append((r["id"], code))
    con = sqlite3.connect(f"file:{REGISTRY_DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    out, keys_out = [], set()
    reviewed = 0
    for prov, th in PROVINCE_TH.items():
        rows = con.execute(
            "SELECT code, name_th, name_key, rank, sect, reg_type, founded_be,"
            "       founded_ce, wisung, wisung_date, tambon_th, amphoe_th,"
            "       postcode, phone, website"
            "  FROM temples WHERE changwat_th = ? ORDER BY code", (th,)).fetchall()
        n_new = n_held = n_review = n_released = 0
        for t in rows:
            if t["code"] in joined_codes:
                n_held += 1              # already one of our stamped records
                continue
            k = t["name_key"] or matchkey(t["name_th"] or "")
            cands = key_index[prov].get(k) or []
            # a record stamped with a DIFFERENT code is spoken for — it is not
            # this temple, and it cannot make this row ambiguous
            open_cands = [c for c in cands if not (c[1] and c[1] != t["code"])]
            if open_cands and t["code"] in released:
                # A held record answers to this name, and its own pin says it
                # stands nowhere near this temple's district. Fold it.
                open_cands = []
                n_released += 1
            if open_cands:
                n_review += 1
                review.append(
                    f"[temple] {prov} {t['code']} วัด{t['name_th']} "
                    f"ต.{t['tambon_th'] or '?'} อ.{t['amphoe_th'] or '?'} — "
                    f"a held record answers to this name: "
                    + ", ".join(c[0] for c in open_cands[:4])
                    + "  → settle by อำเภอ, then add to merges.json or leave both")
                continue
            name = t["name_th"] or ""
            if not IS_TEMPLE.search(name):
                name = "วัด" + name
            addr_bits = []
            if t["tambon_th"]:
                addr_bits.append(f"ตำบล{t['tambon_th']}")
            if t["amphoe_th"]:
                addr_bits.append(f"อำเภอ{t['amphoe_th']}")
            addr_bits.append(f"จังหวัด{th}")
            if t["postcode"]:
                addr_bits.append(str(t["postcode"]))
            address = " ".join(addr_bits)
            attrs = {"watCode": t["code"], "status": "active"}
            for src_f, dest in (("rank", "watRank"), ("sect", "sect"),
                                ("founded_be", "foundedBE"), ("founded_ce", "foundedCE"),
                                ("wisung", "wisung"), ("wisung_date", "wisungDate"),
                                ("tambon_th", "tambon"), ("amphoe_th", "amphoe"),
                                ("postcode", "postcode"), ("name_th", "watRegisterName")):
                v = t[src_f]
                if v not in (None, ""):
                    attrs[dest] = str(v) if src_f == "postcode" else v
            if t["reg_type"] and t["reg_type"] != "ตั้งวัด":
                attrs["regType"] = t["reg_type"]
            rec = {
                "id": f"{prov}-onab-{t['code']}",
                "province": prov, "cat": ["wat"], "sub": [],
                "name": name, "nameTh": None, "nameEn": None,
                "address": address,
                "phone": t["phone"] or None, "website": t["website"] or None,
                "hours": None, "attrs": attrs,
                "featured": False, "landmark": False,
                "sources": [{"type": "register", "ref": "https://data.go.th/dataset/onab_temples",
                             "fetched": "พ.ศ. 2567", "via": "ONAB register",
                             "credit": ONAB_CREDIT, "note": ONAB_SOURCE}],
                "confidence": "official", "updatedAt": "2024-01-01",
            }
            _pin(rec, address, prov)
            out.append(rec)
            keys_out.add((prov, k))
            n_new += 1
        print(f"opendata: temples {prov} — {n_new} new ({n_released} released by "
              f"the pin test), {n_held} already held (stamped), {n_review} to review")
        reviewed += n_review
    con.close()
    return out, keys_out


def _dedup_index(canonical, prov):
    idx = {}
    for r in canonical[prov]:
        if MINE.match(r.get("id") or ""):
            continue
        for n in (r.get("name"), r.get("nameTh"), r.get("nameEn")):
            k = _norm(n)
            if k:
                idx.setdefault(k, []).append(r["id"])
    return idx


def _fold_rows(src_key, rows, prov, make, canonical, review, temple_keys=None,
               run_keys=None):
    """The shared fold: exact-name match → held (skip); otherwise a new record
    via make(row) — and every new record is also written to the review file
    beside any same-name-ish records, the audit_medical_dupes posture: fold,
    but hand the human the eyes-on list.

    run_keys is the run-wide (province, name-key) set: the CR eco and
    religious lists both carry ดอยแม่สลอง, and the second list to fold must
    treat the first fold's records as held, or one place lands twice in one
    run."""
    idx = _dedup_index(canonical, prov)
    out, held = [], 0
    emitted = set()                     # a source can list one place twice
    for row in rows:
        name = row.get("name") or ""
        k = _norm(name)
        if not k:
            continue
        if k in idx or (run_keys is not None and (prov, k) in run_keys):
            held += 1
            continue
        if temple_keys is not None and matchkey is not None and IS_TEMPLE.search(name):
            tk = matchkey(name)
            if (prov, tk) in temple_keys:
                held += 1               # the register fold already carries it
                continue
        rec = make(row)
        if rec is None or rec["id"] in emitted:
            continue
        emitted.add(rec["id"])
        if run_keys is not None:
            run_keys.add((prov, k))
        ks = _stem(k)
        near = [i for kk, ids in idx.items()
                if len(ks) >= NEAR_MIN and len(_stem(kk)) >= NEAR_MIN
                and (ks in _stem(kk) or _stem(kk) in ks) for i in ids][:3]
        if near:
            review.append(f"[{src_key}] {prov} {name} — folded as {rec['id']}; "
                          f"similar held names: {', '.join(near)} — merge via "
                          f"merges.json if the same door")
        out.append(rec)
    return out, held


def records():
    """New records for import_all — derived fresh every run."""
    canonical = _canonical()
    data = _load_datagoth()
    today = date.today().isoformat()
    review = []
    out = []
    run_keys = set()                    # (province, name-key) folded this run

    temples, temple_keys = _temples(canonical, review)
    out += temples

    def src_meta(key, type_="opendata"):
        m = data.get(key) or {}
        return {"type": type_, "ref": m.get("dataset_url") or "",
                "fetched": m.get("fetched") or today,
                "via": "data.go.th",
                "licence": m.get("licence") or "not specified",
                "credit": m.get("publisher") or "data.go.th"}

    # --- Chiang Rai attractions with phone numbers -------------------------
    eco = data.get("cr-eco")
    if eco and eco.get("rows"):
        H = {h: i for i, h in enumerate(eco["rows"][0])}
        rows = []
        for r in eco["rows"][1:]:
            def col(h):
                i = H.get(h)
                return r[i] if i is not None and i < len(r) else ""
            if col("ชื่อสถานที่"):
                rows.append({"name": col("ชื่อสถานที่"), "kind": col("ประเภทแหล่งท่องเที่ยว"),
                             "addr": col("ที่อยู่"), "amphoe": col("อำเภอ"),
                             "tambon": col("ตำบล"), "contact": col("ติดต่อ"),
                             "credit": col("ที่มา")})

        def mk(row):
            addr = " ".join(x for x in (
                row["addr"], f"ตำบล{row['tambon']}" if row["tambon"] else "",
                f"อำเภอ{row['amphoe']}" if row["amphoe"] else "", "จังหวัดเชียงราย") if x)
            rec = {"id": _sid("cr", "eco", row["name"], row["amphoe"]),
                   "province": "cr", "cat": ["sights"],
                   # A list row whose name states a hot spring lands under
                   # the น้ำพุร้อน child (WO-23) instead of subless limbo.
                   "sub": (["hot-spring"] if _hs.named_spring(row["name"]) else []),
                   "name": row["name"], "nameTh": None, "nameEn": None,
                   "address": addr or None, "phone": _phone(row["contact"]),
                   "website": None, "hours": None,
                   "attrs": {"kind": row["kind"] or "แหล่งท่องเที่ยว",
                             **({"tambon": row["tambon"]} if row["tambon"] else {}),
                             **({"amphoe": row["amphoe"]} if row["amphoe"] else {})},
                   "featured": False, "landmark": False,
                   "sources": [{**src_meta("cr-eco"),
                                "credit": row["credit"] or (data.get("cr-eco") or {}).get("publisher", "")}],
                   "confidence": "official", "updatedAt": today}
            return _pin(rec, addr, "cr")
        recs, held = _fold_rows("cr-eco", rows, "cr", mk, canonical, review, run_keys=run_keys)
        print(f"opendata: cr attractions — {len(recs)} new, {held} already held")
        out += recs

    # --- Chiang Rai religious/arts + community-tourism sites ---------------
    for key, kind_th in (("cr-religious", "แหล่งท่องเที่ยวเชิงศาสนา ศิลปะ วัฒนธรรม"),
                         ("cr-community", "ชุมชนท่องเที่ยว")):
        src = data.get(key)
        if not (src and src.get("rows")):
            continue
        rows = [{"name": r[0], "amphoe": r[1] if len(r) > 1 else "",
                 "credit": r[2] if len(r) > 2 else ""}
                for r in src["rows"][1:] if r and r[0] and r[0] != "แหล่งท่องเที่ยว"]

        def mk(row, _key=key, _kind=kind_th):
            addr = " ".join(x for x in (
                f"อำเภอ{row['amphoe']}" if row["amphoe"] else "", "จังหวัดเชียงราย") if x)
            rec = {"id": _sid("cr", _key.split("-")[1], row["name"], row["amphoe"]),
                   "province": "cr", "cat": ["sights"],
                   # Same WO-23 rule as the eco list: the religious/community
                   # lists carry บ่อน้ำร้อนแม่ขะจาน too, and ชุมชนบ้านโป่งน้ำร้อน
                   # stays the community it says it is (the NAMED_ELSE fence).
                   "sub": (["hot-spring"] if _hs.named_spring(row["name"]) else []),
                   "name": row["name"], "nameTh": None, "nameEn": None,
                   "address": addr or None, "phone": None, "website": None, "hours": None,
                   "attrs": {"kind": _kind,
                             **({"amphoe": row["amphoe"]} if row["amphoe"] else {})},
                   "featured": False, "landmark": False,
                   "sources": [{**src_meta(_key),
                                "credit": row["credit"] or (data.get(_key) or {}).get("publisher", "")}],
                   "confidence": "official", "updatedAt": today}
            return _pin(rec, addr, "cr")
        recs, held = _fold_rows(key, rows, "cr", mk, canonical, review,
                                temple_keys=temple_keys, run_keys=run_keys)
        print(f"opendata: {key} — {len(recs)} new, {held} already held")
        out += recs

    # --- Chiang Mai police stations, with phone numbers --------------------
    pol = data.get("cm-police")
    if pol and pol.get("rows"):
        rows = []
        for r in pol["rows"][1:]:
            if len(r) < 5 or not r[4]:
                continue
            raw = r[4]
            name = re.split(r"โทรศัพท์", raw)[0].strip(" :-")
            rows.append({"name": name, "phone": _phone(raw), "amphoe": r[3],
                         "year": r[1]})

        def mk(row):
            addr = f"อำเภอ{row['amphoe']} จังหวัดเชียงใหม่" if row["amphoe"] else None
            rec = {"id": _sid("cm", "police", row["name"]),
                   "province": "cm", "cat": ["essentials"], "sub": ["gov"],
                   "name": row["name"], "nameTh": None, "nameEn": None,
                   "address": addr, "phone": row["phone"], "website": None, "hours": None,
                   "attrs": {"facilityType": "police",
                             **({"amphoe": row["amphoe"]} if row["amphoe"] else {})},
                   "featured": False, "landmark": False,
                   "sources": [src_meta("cm-police")],
                   "confidence": "official", "updatedAt": "2024-01-01"}
            return _pin(rec, addr, "cm")
        recs, held = _fold_rows("cm-police", rows, "cm", mk, canonical, review, run_keys=run_keys)
        print(f"opendata: cm police — {len(recs)} new, {held} already held, "
              f"{sum(1 for r in recs if r['phone'])} with a phone")
        out += recs

    # --- Chiang Mai LPG shops ---------------------------------------------
    lpg = data.get("cm-lpg")
    if lpg and lpg.get("rows"):
        rows = []
        seen = set()
        for r in lpg["rows"][1:]:
            if len(r) < 5 or not r[4]:
                continue
            name = re.sub(r"\s+", " ", r[4].replace("\xa0", " ")).strip()
            k = (_norm(name), r[3])
            if k in seen:               # the file repeats years, like the wats one
                continue
            seen.add(k)
            rows.append({"name": name, "amphoe": r[2], "tambon": r[3]})

        def mk(row):
            addr = " ".join(x for x in (
                f"ตำบล{row['tambon']}" if row["tambon"] else "",
                f"อำเภอ{row['amphoe']}" if row["amphoe"] else "", "จังหวัดเชียงใหม่") if x)
            rec = {"id": _sid("cm", "lpg", row["name"], row["tambon"]),
                   "province": "cm", "cat": ["essentials"], "sub": [],
                   "name": row["name"], "nameTh": None, "nameEn": None,
                   "address": addr or None, "phone": None, "website": None, "hours": None,
                   "attrs": {"facilityType": "lpg-shop", "fuel": ["lpg"],
                             **({"tambon": row["tambon"]} if row["tambon"] else {}),
                             **({"amphoe": row["amphoe"]} if row["amphoe"] else {})},
                   "featured": False, "landmark": False,
                   "sources": [src_meta("cm-lpg")],
                   "confidence": "official", "updatedAt": today}
            return _pin(rec, addr, "cm")
        recs, held = _fold_rows("cm-lpg", rows, "cm", mk, canonical, review, run_keys=run_keys)
        print(f"opendata: cm lpg — {len(recs)} new, {held} already held")
        out += recs

    # --- Chiang Rai's ธงฟ้า budget restaurants ------------------------------
    # 33 government-listed cheap-eats shops; ZERO of them matched anything
    # held (measured — they are exactly the tiny rice-curry shops OSM never
    # meets). The commerce office's list carries the OPERATOR'S PERSONAL NAME,
    # which is deliberately NOT taken — the shop is public, the person is not.
    tf = data.get("cr-thongfah")
    if tf and tf.get("rows"):
        rows = []
        for r in tf["rows"][1:]:
            if not r or not r[0] or r[0] == "ชื่อร้าน":
                continue
            rows.append({"name": r[0],
                         "amphoe": r[2] if len(r) > 2 else "",
                         "tambon": r[3] if len(r) > 3 else "",
                         "cuisine": r[4] if len(r) > 4 else "",
                         "grade": (r[6] if len(r) > 6 else "").strip()})

        def mk(row):
            addr = " ".join(x for x in (
                f"ตำบล{row['tambon']}" if row["tambon"] else "",
                f"อำเภอ{row['amphoe']}" if row["amphoe"] else "", "จังหวัดเชียงราย") if x)
            rec = {"id": _sid("cr", "thongfah", row["name"]),
                   "province": "cr", "cat": ["food"], "sub": [],
                   "name": row["name"], "nameTh": None, "nameEn": None,
                   "address": addr or None, "phone": None, "website": None, "hours": None,
                   "attrs": {"thongfah": row["grade"] or "yes",
                             **({"kind": row["cuisine"]} if row["cuisine"] else {}),
                             **({"tambon": row["tambon"]} if row["tambon"] else {}),
                             **({"amphoe": row["amphoe"]} if row["amphoe"] else {})},
                   "featured": False, "landmark": False,
                   "sources": [src_meta("cr-thongfah")],
                   "confidence": "official", "updatedAt": today}
            return _pin(rec, addr, "cr")
        recs, held = _fold_rows("cr-thongfah", rows, "cr", mk, canonical, review, run_keys=run_keys)
        print(f"opendata: cr thongfah — {len(recs)} new, {held} already held")
        out += recs

    # --- FDA retail-pharmacy licences ---------------------------------------
    # The register names 702 licensed pharmacies in Chiang Mai and 230 in
    # Chiang Rai; the crawl found ~202 and ~20. This is the same gap the
    # temple register filled, in the shelf where being wrong matters most, so
    # it takes ONLY what the register states — the shop's name, the district
    # it is licensed in, its licence number and the date that licence issued —
    # and never implies opening hours, a phone or a pin it does not have.
    # `ขายยาแผนปัจจุบัน` alone is the ordinary retail licence (ขย.1): the
    # บรรจุเสร็จ variants are limited licences and the วัตถุออกฤทธิ์ /
    # ยาเสพติด ones are permissions a pharmacy holds ON TOP of it, not extra
    # shops. `คงอยู่` = the licence is extant; anything else is not published.
    fda = data.get("fda-drug")
    if fda and fda.get("rows"):
        H = {h: i for i, h in enumerate(fda["rows"][0])}
        need = ("thanm", "thachngwtnm", "lcntpcd", "thaamphrnm", "thathmblnm")
        if all(k in H for k in need):
            for prov_th, prov in (("เชียงใหม่", "cm"), ("เชียงราย", "cr")):
                rows = []
                for r in fda["rows"][1:]:
                    if len(r) <= max(H.values()):
                        continue
                    if r[H["thachngwtnm"]] != prov_th:
                        continue
                    if r[H["lcntpcd"]] != "ขายยาแผนปัจจุบัน":
                        continue
                    if "cncnm" in H and r[H["cncnm"]] not in ("คงอยู่", ""):
                        continue
                    if not r[H["thanm"]]:
                        continue
                    rows.append({"name": re.sub(r"\s+", " ", r[H["thanm"]]).strip(),
                                 "tambon": r[H["thathmblnm"]], "amphoe": r[H["thaamphrnm"]],
                                 "zip": r[H["zipcode"]] if "zipcode" in H else "",
                                 "lic": r[H["lcnno_no"]] if "lcnno_no" in H else "",
                                 "since": r[H["appdate"]] if "appdate" in H else ""})

                def mk(row, _prov=prov, _th=prov_th):
                    addr = " ".join(x for x in (
                        f"ตำบล{row['tambon']}" if row["tambon"] else "",
                        f"อำเภอ{row['amphoe']}" if row["amphoe"] else "",
                        f"จังหวัด{_th}", row["zip"]) if x)
                    attrs = {"facilityType": "pharmacy", "sector": "private"}
                    if row["lic"]:
                        attrs["licenceNo"] = row["lic"]
                    if row["tambon"]:
                        attrs["tambon"] = row["tambon"]
                    if row["amphoe"]:
                        attrs["amphoe"] = row["amphoe"]
                    if row["zip"]:
                        attrs["postcode"] = row["zip"]
                    rec = {"id": _sid(_prov, "fda", row["name"], row["amphoe"], row["tambon"]),
                           "province": _prov,
                           # Dual-shelved, the WO-9 rule: a pharmacy is both an
                           # everyday errand and a medical door.
                           "cat": ["essentials", "medical"], "sub": ["pharmacy"],
                           "name": row["name"], "nameTh": None, "nameEn": None,
                           "address": addr or None, "phone": None, "website": None,
                           "hours": None, "attrs": attrs,
                           "featured": False, "landmark": False,
                           "sources": [src_meta("fda-drug", "register")],
                           "confidence": "official",
                           "updatedAt": (row["since"] or today)[:10]}
                    return _pin(rec, addr, _prov)
                recs, held = _fold_rows("fda-drug", rows, prov, mk, canonical, review,
                                        run_keys=run_keys)
                print(f"opendata: {prov} pharmacies — {len(recs)} new, {held} already held "
                      f"(register lists {len(rows)} extant retail licences)")
                out += recs

    # --- โรงเรียนพระปริยัติธรรม — the monastic schools, and the temple each
    # --- one stands in ------------------------------------------------------
    # The shelf child `school/monastic` has been deliberately empty since the
    # schools shelf was built, with a written reason: OSM has no tag for a
    # monastic school, and the register that names them had not been fetched.
    # This is that register. It carries the one column that makes it worth
    # more than a list of names — **วัด**, the temple the school stands in —
    # so a school can be pinned AT ITS TEMPLE and the temple can say which
    # school it hosts. That join only became possible when the ONAB fold
    # landed 2,600 temples three days ago; four of the matches below are to
    # records that did not exist before it.
    #
    # The file stacks two academic years (2568 and 2569) of the same ~28
    # schools, exactly like the provincial temple CSV stacks three. Only the
    # newest year is taken.
    mon = data.get("cm-monastic")
    if mon and mon.get("rows"):
        MH = {h: i for i, h in enumerate(mon["rows"][0])}
        need = ("ชื่อโรงเรียน", "วัด", "อำเภอ", "ตำบล", "ปีการศึกษา")
        if all(k in MH for k in need):
            body = [r for r in mon["rows"][1:] if len(r) > max(MH[k] for k in need)]
            years = [r[MH["ปีการศึกษา"]] for r in body if r[MH["ปีการศึกษา"]]]
            newest = max(years) if years else None
            seen_m = set()
            rows = []
            for r in body:
                if newest and r[MH["ปีการศึกษา"]] != newest:
                    continue
                name = r[MH["ชื่อโรงเรียน"]].strip()
                if not name or _norm(name) in seen_m:
                    continue
                seen_m.add(_norm(name))
                rows.append({"name": name, "wat": r[MH["วัด"]].strip(),
                             "amphoe": r[MH["อำเภอ"]].strip(),
                             "tambon": r[MH["ตำบล"]].strip(), "year": newest})
            # Temples we hold, by name — including the ones the ONAB fold added.
            wat_idx = {}
            for rec in canonical["cm"]:
                if "wat" not in (rec.get("cat") or []):
                    continue
                for n in (rec.get("name"), rec.get("nameTh")):
                    if n:
                        wat_idx.setdefault(_norm(n), rec)

            def _wat_of(written):
                """The register writes the temple's FULL ceremonial name —
                'วัดเจดีย์หลวง วรวิหาร' — while the catalogue holds 'วัดเจดีย์หลวง'.
                The rank suffix is a rank, not part of the name, so it comes
                off before matching and nothing else is touched."""
                base = re.sub(r"\s*(ราชวรมหาวิหาร|ราชวรวิหาร|วรมหาวิหาร|วรวิหาร|"
                              r"พระอารามหลวง).*$", "", written).strip()
                return wat_idx.get(_norm(base)) or wat_idx.get(_norm(written))

            def mk(row):
                w = _wat_of(row["wat"])
                addr = " ".join(x for x in (
                    f"ตำบล{row['tambon']}" if row["tambon"] else "",
                    f"อำเภอ{row['amphoe']}" if row["amphoe"] else "",
                    "จังหวัดเชียงใหม่") if x)
                attrs = {"schoolSector": "monastic", "officialType": "โรงเรียนพระปริยัติธรรม แผนกสามัญศึกษา",
                         "watName": row["wat"]}
                if row["tambon"]:
                    attrs["tambon"] = row["tambon"]
                if row["amphoe"]:
                    attrs["amphoe"] = row["amphoe"]
                rec = {"id": _sid("cm", "monastic", row["name"], row["wat"]),
                       "province": "cm", "cat": ["school"], "sub": ["monastic"],
                       "name": row["name"], "nameTh": None, "nameEn": None,
                       "address": addr or None, "phone": None, "website": None,
                       "hours": None, "attrs": attrs,
                       "featured": False, "landmark": False,
                       "sources": [src_meta("cm-monastic")],
                       "confidence": "official",
                       "updatedAt": today}
                if w and w.get("lat") is not None:
                    # AT the temple, because that is what the register says —
                    # a far better pin than a tambon centroid, and still not a
                    # surveyed pin of the school's own gate.
                    #
                    # A BORROWED PIN INHERITS THE LENDER'S ERROR BAR. Caught
                    # before it shipped: วัดโขงขาว is itself placed by postcode
                    # centroid at ±12.5 km, and stamping its school ±150 m
                    # would have declared a twelve-kilometre guess as a
                    # hundred-and-fifty-metre fact. The grounds of a temple are
                    # ~150 m across, so that is the FLOOR, never the answer.
                    wa = w.get("attrs") or {}
                    try:
                        lender = int(wa.get("pinUncertaintyM") or 0)
                    except (TypeError, ValueError):
                        lender = 0
                    if not lender:
                        # exact = surveyed; block = a building outline, ~120 m
                        # by this site's own map scale (build.PLACE_MAP_SPAN).
                        lender = 120 if w.get("geoPrecision") == "block" else 0
                    rec["lat"], rec["lng"] = w["lat"], w["lng"]
                    rec["geoPrecision"] = "approx"
                    attrs["pinVia"] = "at-the-temple-the-school-belongs-to"
                    attrs["pinUncertaintyM"] = str(max(150, lender))
                    attrs["pinFrom"] = w.get("name") or row["wat"]
                    attrs["watId"] = w["id"]
                    attrs["watPinPrecision"] = w.get("geoPrecision") or "exact"
                    return rec
                return _pin(rec, addr, "cm")
            recs, held = _fold_rows("cm-monastic", rows, "cm", mk, canonical, review,
                                    run_keys=run_keys)
            pinned = sum(1 for r in recs if (r.get("attrs") or {}).get("watId"))
            print(f"opendata: monastic schools — {len(recs)} new, {held} already held; "
                  f"{pinned} pinned at their own temple")
            out += recs

    # --- สถาบันอุดมศึกษา — the higher-education register --------------------
    # Name and province and nothing else (2563 edition, and the year rides on
    # every record). Only the institutions nobody has mapped are added, and
    # they are added PINLESS and saying so — the import_opec posture.
    #
    # THE TRAP, caught before it landed: the register files
    # "มหาวิทยาลัยรามคำแหง สาขาวิทยบริการฯ จังหวัดแพร่" under เชียงใหม่. A row
    # whose NAME names a different จังหวัด is about that province, whatever
    # the column says — the same rule import_citizeninfo keeps for addresses.
    uni = data.get("universities")
    if uni and uni.get("rows"):
        UH = {h: i for i, h in enumerate(uni["rows"][0])}
        if "UNIV_NAME" in UH and "PROVINCE_UNIV_NAME_TH" in UH:
            body = [r for r in uni["rows"][1:] if len(r) > max(UH.values())]
            yrs = [r[UH["ACADEMIC_YEAR"]] for r in body] if "ACADEMIC_YEAR" in UH else []
            newest = max(yrs) if yrs else None
            for prov_th, prov in (("เชียงใหม่", "cm"), ("เชียงราย", "cr")):
                rows = []
                for r in body:
                    if newest and "ACADEMIC_YEAR" in UH and r[UH["ACADEMIC_YEAR"]] != newest:
                        continue
                    if r[UH["PROVINCE_UNIV_NAME_TH"]] != prov_th:
                        continue
                    nm = re.sub(r"\s+", " ", r[UH["UNIV_NAME"]]).strip()
                    if not nm:
                        continue
                    other = re.search(r"จังหวัด([ก-๙]+)", nm)
                    if other and other.group(1) != prov_th:
                        review.append(f"[universities] {prov} {nm} — filed under {prov_th} "
                                      f"but its name says จังหวัด{other.group(1)}; not added")
                        continue
                    rows.append({"name": nm, "year": newest})

                def mk(row, _prov=prov, _th=prov_th):
                    sub = "college" if row["name"].startswith("วิทยาลัย") else "university"
                    rec = {"id": _sid(_prov, "mhesi", row["name"]),
                           "province": _prov, "cat": ["school"], "sub": [sub],
                           "name": row["name"], "nameTh": None, "nameEn": None,
                           "address": f"จังหวัด{_th}", "phone": None, "website": None,
                           "hours": None,
                           "attrs": {"schoolSector": "higher-education",
                                     "mhesiRegistered": True,
                                     **({"yearBE": row["year"]} if row["year"] else {})},
                           "featured": False, "landmark": False,
                           "sources": [src_meta("universities", "register")],
                           "confidence": "official", "updatedAt": today}
                    # Province only — the register carries no address at all,
                    # so there is nothing to geocode and nothing is invented.
                    rec["lat"] = rec["lng"] = None
                    rec["geoPrecision"] = "needs-pin"
                    return rec
                recs, held = _fold_rows("universities", rows, prov, mk, canonical, review,
                                        run_keys=run_keys)
                print(f"opendata: {prov} higher-education — {len(recs)} new, "
                      f"{held} already held (register lists {len(rows)})")
                out += recs

    # --- SAT-certified muay thai camps not on the shelf --------------------
    sat = data.get("sat-camps")
    if sat and sat.get("rows"):
        rows = []
        for r in sat["rows"][1:]:
            if len(r) > 7 and r[7] in ("เชียงใหม่", "เชียงราย") and r[0]:
                rows.append({"name": r[0].strip(), "year": r[1],
                             "standard": r[3],
                             "prov": "cm" if r[7] == "เชียงใหม่" else "cr"})
        for prov in ("cm", "cr"):
            prows = [r for r in rows if r["prov"] == prov]
            if not prows:
                continue

            def mk(row, _prov=prov):
                rec = {"id": _sid(_prov, "sat", row["name"]),
                       "province": _prov, "cat": ["muaythai"], "sub": ["camp"],
                       "name": row["name"], "nameTh": None, "nameEn": None,
                       "address": None, "phone": None, "website": None, "hours": None,
                       "attrs": {"satCertified": True,
                                 "satStandard": row["standard"] or None,
                                 "satYearBE": row["year"] or None},
                       "featured": False, "landmark": False,
                       "sources": [{**src_meta("sat-camps", "register"),
                                    "licence": "CC-BY"}],
                       "confidence": "official",
                       "updatedAt": "2021-01-01"}
                rec["attrs"] = {k: v for k, v in rec["attrs"].items() if v}
                rec["geoPrecision"] = "needs-pin"
                rec["lat"] = rec["lng"] = None
                return rec
            recs, held = _fold_rows("sat-camps", prows, prov, mk, canonical, review, run_keys=run_keys)
            print(f"opendata: sat camps {prov} — {len(recs)} new, {held} matched the shelf")
            out += recs

    os.makedirs(os.path.dirname(REVIEW), exist_ok=True)
    with open(REVIEW, "w", encoding="utf-8") as f:
        f.write("# WO-16 open-lists fold — what a person should look at.\n"
                "# A [temple] line is a register row a held record MIGHT be: "
                "settle it by อำเภอ and either merge or let both stand.\n"
                "# Other lines are records that WERE folded beside similar held "
                "names — confirm with your eyes; merges go in "
                "data/curated/merges.json (human-confirmed pairs only).\n\n")
        f.write("\n".join(review) + ("\n" if review else "(nothing to review)\n"))
    print(f"opendata: {len(out)} records in all; {len(review)} review line(s) "
          f"→ cache/opendata_review.txt")
    return out


def enrich(final, prov):
    """Let a government list fill contact fields a held record leaves EMPTY.

    Nan's call, 2026-08-20: government directories may enrich records we
    already hold. The fence is narrow and matches the claim worker's: only
    phone / website / hours, only where the record has none, never over a
    value already there — and an owner's claim still wins over all of it,
    because claims are applied later, at build time, by channels().

    Matched by exact normalised name inside one province, the same key the
    fold dedups on: a list that says "สิงห์ปาร์ค เชียงราย, โทร 053160636" and
    a record we hold under that exact name are the same place, and refusing
    to carry the number across would be pedantry with a phone number in it.
    Anything short of exact stays unmatched — near-matches are for people.
    """
    data = _load_datagoth()
    today = date.today().isoformat()
    rows = []
    eco = data.get("cr-eco")
    if eco and eco.get("rows") and prov == "cr":
        H = {h: i for i, h in enumerate(eco["rows"][0])}
        for r in eco["rows"][1:]:
            def col(h, _r=r):
                i = H.get(h)
                return _r[i] if i is not None and i < len(_r) else ""
            if col("ชื่อสถานที่") and _phone(col("ติดต่อ")):
                rows.append((col("ชื่อสถานที่"), {"phone": _phone(col("ติดต่อ"))},
                             "cr-eco"))
    pol = data.get("cm-police")
    if pol and pol.get("rows") and prov == "cm":
        for r in pol["rows"][1:]:
            if len(r) > 4 and r[4] and _phone(r[4]):
                rows.append((re.split(r"โทรศัพท์", r[4])[0].strip(" :-"),
                             {"phone": _phone(r[4])}, "cm-police"))
    if not rows:
        return 0
    idx = {}
    for r in final:
        if MINE.match(r.get("id") or ""):
            continue
        for n in (r.get("name"), r.get("nameTh"), r.get("nameEn")):
            k = _norm(n)
            if k:
                idx.setdefault(k, r)
    n = 0
    for name, fields, src_key in rows:
        r = idx.get(_norm(name))
        if not r:
            continue
        filled = False
        for k, v in fields.items():
            if v and not r.get(k):
                r[k] = v
                filled = True
        if not filled:
            continue
        m = (data.get(src_key) or {})
        r.setdefault("sources", []).append(
            {"type": "opendata", "ref": m.get("dataset_url") or "",
             "fetched": m.get("fetched") or today, "via": "data.go.th",
             "licence": m.get("licence") or "not specified",
             "credit": m.get("publisher") or "data.go.th",
             "note": "contact filled from the open list; the record is otherwise ours"})
        n += 1
    return n


def apply_monastic(final, prov):
    """Tell the TEMPLE which monastic school it hosts.

    The register names the wat for every โรงเรียนพระปริยัติธรรม, so the link
    runs both ways and only one direction was being used. A temple that
    teaches the ordinary curriculum to its novices is a fact about that
    temple — and it is the fact no other directory of either province can
    state, because nothing else holds the temples and the schools together.
    Nan's 2026-08-20 rule covers it: a government register may fill a field a
    held record leaves empty; it never overwrites one.
    """
    if prov != "cm":
        return 0                       # the register is Chiang Mai's
    n = 0
    by_id = {r["id"]: r for r in final}
    for r in final:
        a = r.get("attrs") or {}
        wid = a.get("watId")
        if not wid or "monastic" not in (r.get("sub") or []):
            continue
        w = by_id.get(wid)
        if not w:
            continue
        wa = w.setdefault("attrs", {})
        if wa.get("monasticSchool"):
            continue
        wa["monasticSchool"] = r.get("name")
        wa["monasticSchoolId"] = r["id"]
        n += 1
    return n


def apply(final, prov):
    """Stamp SAT certification onto camps the shelf already holds (matched by
    normalised Thai name). Returns how many were stamped."""
    data = _load_datagoth()
    sat = data.get("sat-camps")
    if not (sat and sat.get("rows")):
        return 0
    prov_th = PROVINCE_TH[prov]
    rows = [r for r in sat["rows"][1:]
            if len(r) > 7 and r[7] == prov_th and r[0]]
    if not rows:
        return 0
    idx = {}
    for r in final:
        if "muaythai" not in (r.get("cat") or []):
            continue
        for n in (r.get("name"), r.get("nameTh"), r.get("nameEn")):
            k = _norm(n)
            if k:
                idx.setdefault(k, r)
    n = 0
    for row in rows:
        r = idx.get(_norm(row[0]))
        if not r or MINE.match(r["id"]):
            continue
        attrs = r.setdefault("attrs", {})
        if attrs.get("satCertified"):
            continue
        attrs["satCertified"] = True
        if row[3]:
            attrs["satStandard"] = row[3]
        if row[1]:
            attrs["satYearBE"] = row[1]
        r.setdefault("sources", []).append(
            {"type": "register", "ref": (data.get("sat-camps") or {}).get("dataset_url", ""),
             "fetched": (data.get("sat-camps") or {}).get("fetched", ""),
             "via": "data.go.th", "licence": "CC-BY",
             "credit": "การกีฬาแห่งประเทศไทย (SAT)"})
        n += 1
    return n


if __name__ == "__main__":
    import collections
    recs = records()
    c = collections.Counter((r["province"], r["cat"][0]) for r in recs)
    for k, v in sorted(c.items()):
        print(" ", k, v)
    pins = collections.Counter(r.get("geoPrecision") for r in recs)
    print("  pins:", dict(pins))
