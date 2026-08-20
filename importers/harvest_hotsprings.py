#!/usr/bin/env python3
"""The whole north's hot springs — the fifteen-province harvest and the
register assembly. WO-23, Nan's go 2026-08-20: "BIGLY … the whole north is ok."

Chiang Mai and Chiang Rai are fetched by crawl_overpass.py (`--group
hotsprings`) into cache/overpass/<prov>/hotsprings.json, where the fenced
import files them as full catalogue records. THIS file asks the SAME
selectors — imported from crawl_overpass.QUERIES, one copy — in the other
fifteen provinces of ภาคเหนือ, register-only: a reader soaking is a reader
on a day trip, and the springs she weighs against สันกำแพง are ท่าปาย,
แจ้ซ้อน and ภูซาง, none of which this directory will ever hold as records.

Manners are the crawler's own, imported not copied: area-clipped ISO 3166-2
provinces (never a bounding box — a rectangle round แม่ฮ่องสอน is somebody
else's country), one selector per query, 12 s pauses, mirror rotation,
OverpassRemark, the asked-twice zero. Snapshot-first: nothing is fetched if
a province's cache file exists.

  python3 importers/harvest_hotsprings.py             # fetch what's missing, then assemble
  python3 importers/harvest_hotsprings.py --fetch     # refresh every province (slow, on purpose)
  python3 importers/harvest_hotsprings.py --assemble  # zero network: rebuild data/hotsprings.json from cache

ASSEMBLY reads five shelves of truth and folds them by name, curated
outranking everything (the house rule):

  1. data/canonical/cm.json + cr.json — records with sub=hot-spring (the
     directory's own, already fenced);
  2. cache/hotsprings/<prov>.json — the fifteen provinces' OSM elements,
     read with audit_hotsprings' rules (the fence holds here too);
  3. cache/hotsprings/sources/mhs_hot_spring.csv — Mae Hong Son province's
     own hot-spring list, eight springs with coordinates (Open Data Common,
     fetched 2026-08-20);
  4. cache/hotsprings/sources/dnp_np_attractions.csv — the national-parks
     department's attraction register, its น้ำพุร้อน/บ่อน้ำแร่ rows in the
     northern parks, with coordinates (Open Data Common, fetched 2026-08-20);
  5. cache/hotsprings/sources/dmr_table.json — the Department of Mineral
     Resources' national hot-spring inventory (66 northern rows), MEASURED
     temperature and pH per spring, no coordinates (dmr.go.th, fetched
     2026-08-20). A DMR temperature joins a folded entry only when name (or
     village) and province agree and districts do not disagree; everything
     unmatched stands as its own register row rather than being forced onto
     a neighbour.
  6. data/curated/hotsprings.json — what each spring states, hand-kept,
     with fetched sources; `unverified` leads never render.

Folding is by normalised name key WITHIN a province, with a district guard:
two entries whose keys agree but whose stated districts differ stay two
springs (ลำปาง keeps three distinct บ้านโป่งน้ำร้อน in three อำเภอ). The
alias table carries only witnessed spelling wobbles between the agencies —
DMR's เทพนม is the ออบหลวง เทพพนม, DMR's ป่าแป๋ is โป่งเดือด (the geyser
sits in ต.ป่าแป๋), DMR's โปร่งพระบาท is โป่งพระบาท — never a guess.

→ data/hotsprings.json, the register the board (/namphuron.html) renders.
"""
import csv
import io
import json
import re
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "importers"))

from crawl_overpass import QUERIES, PAUSE, fetch_wide  # noqa: E402 — one copy of manners
import audit_hotsprings as _hs                         # noqa: E402 — one copy of rules

CACHE = ROOT / "cache" / "hotsprings"
SRC = CACHE / "sources"
CURATED = ROOT / "data" / "curated" / "hotsprings.json"
OUT = ROOT / "data" / "hotsprings.json"

# The directory's own two provinces, records not register-harvest.
HOME = {
    "cm": ("TH-50", "เชียงใหม่", "Chiang Mai"),
    "cr": ("TH-57", "เชียงราย", "Chiang Rai"),
}
# The other fifteen of ภาคเหนือ in its everyday seventeen-province reading,
# ordered ก→ฮ — the board prints them after the home two, and a dict's order
# is the presentation order (sorts stay province and alphabet).
NORTH = {
    "kamphaengphet": ("TH-62", "กำแพงเพชร", "Kamphaeng Phet"),
    "tak":           ("TH-63", "ตาก", "Tak"),
    "nakhonsawan":   ("TH-60", "นครสวรรค์", "Nakhon Sawan"),
    "nan":           ("TH-55", "น่าน", "Nan"),
    "phayao":        ("TH-56", "พะเยา", "Phayao"),
    "phichit":       ("TH-66", "พิจิตร", "Phichit"),
    "phitsanulok":   ("TH-65", "พิษณุโลก", "Phitsanulok"),
    "phetchabun":    ("TH-67", "เพชรบูรณ์", "Phetchabun"),
    "phrae":         ("TH-54", "แพร่", "Phrae"),
    "mhs":           ("TH-58", "แม่ฮ่องสอน", "Mae Hong Son"),
    "lampang":       ("TH-52", "ลำปาง", "Lampang"),
    "lamphun":       ("TH-51", "ลำพูน", "Lamphun"),
    "sukhothai":     ("TH-64", "สุโขทัย", "Sukhothai"),
    "uttaradit":     ("TH-53", "อุตรดิตถ์", "Uttaradit"),
    "uthaithani":    ("TH-61", "อุทัยธานี", "Uthai Thani"),
}
PROV_BY_TH = {th: k for k, (iso, th, en) in {**HOME, **NORTH}.items()}

FETCHED = "2026-08-20"
DMR_URL = ("https://www.dmr.go.th/ด้านธรณีวิทยา/ธรณีวิทยาพื้นฐาน/น้ำพุร้อน/")
DNP_URL = ("https://catalog.dnp.go.th/dataset/bacc3899-0b64-4d6e-a8bc-c6c6a5c28ce7/"
           "resource/92abcd14-38ca-45da-8f7a-8853029b7e5d/download/"
           "typesofattractionsinnp020566.csv")
MHS_URL = ("https://maehongson.gdcatalog.go.th/dataset/c830856e-dedb-48c6-80f5-"
           "2f212e93be7d/resource/d17b93c7-f478-47ad-9e68-a47c8ce883c7/download/"
           "hot-spring.csv")

# DNP's park column → the province its spring rows stand in, witnessed by the
# rows' own coordinates. Parks outside the north are simply absent, so their
# rows fall away without a blocklist. ห้วยน้ำดัง straddles the Chiang Mai /
# Mae Hong Son line: its โป่งเดือด row (19.24, 98.68) is อ.แม่แตง and stays
# cm; its ท่าปาย row (19.31, 98.47) is อ.ปาย and belongs to แม่ฮ่องสอน — the
# province's own hot-spring CSV pins the same spring 350 m away.
DNP_PARK_PROV = {
    "แม่ยม": "phrae", "แจ้ซ้อน": "lampang", "น้ำตกพาเจริญ (เตรียมการฯ)": "tak",
    "ลำน้ำกก (เตรียมการฯ)": "cr", "ผาแดง": "cm", "ดอยผ้าห่มปก": "cm",
    "ห้วยน้ำดัง": "cm", "ออบหลวง": "cm", "ขุนขาน": "cm",
}

THAI = re.compile(r"[ก-๛]")
TONE_MARKS = "่้๊๋์"   # ่ ้ ๊ ๋ ์
NAME_PREFIXES = ("สวนสาธารณะ", "สวน", "บ่อน้ำพุร้อน", "น้ำพุร้อน", "น้ำพร้อน",
                 "โป่งน้ำร้อน", "บ่อน้ำร้อน", "ธารน้ำร้อน", "บ่อน้ำอุ่น",
                 "น้ำแร่ร้อน", "บ้าน", "หมู่บ้าน")
# Witnessed spelling wobbles between agencies, in POST-normalised key space
# (tone marks stripped; Latin lowercased with the spring words dropped).
# The Latin rows are OSM elements mapped with English-only names — the same
# springs DMR lists in Thai — and each pair below is witnessed by village +
# district agreement, never by sound-alike alone.
KEY_ALIASES = {
    "เทพนม": "เทพพนม",          # DMR CM5 = ออบหลวง's เทพพนม, both อ.แม่แจ่ม
    "ปาแป": "โปงเดือด",          # DMR CM4 ป่าแป๋ = โป่งเดือด, ต.ป่าแป๋ อ.แม่แตง
    "โปรงพระบาท": "โปงพระบาท",   # DMR CR8's โปร่ง- = บ้านโป่งพระบาท อ.เมือง
    "สันกำแพง": "สันกำแพง",
    "phasoet": "ผาเสริฐ",        # OSM way 325837628 @ บ้านผาเสริฐ = DMR CR3
    "pongprabaht": "โปงพระบาท",  # OSM node 4342096790 @ บ้านโป่งพระบาท = DMR CR8
    "malika": "มะลิกา",          # OSM node 12765555302 อ.แม่อาย = DMR CM16
    "huaimakliam": "หวยหมากเลียม",  # OSM node 2624422801 = DNP ลำน้ำกก row
    "pongkum": "โปงกุม",         # OSM "Ban Pong Kum" @ บ้านโป่งกุ่ม ดอยสะเก็ด
}


def _key(name):
    """Normalised join key: tone marks off, spaces and parentheses off, the
    spring-word prefixes peeled from the front until none is left. Empty
    means the name WAS only the spring word (ลำปาง's three บ้านโป่งน้ำร้อน)
    and the caller falls back to the village. A Latin-only name — an OSM
    element mapped in English — is lowercased with its own spring words
    (hot spring / geyser / ban) dropped, so the alias table can hand it to
    the Thai row it names."""
    s = re.sub(f"[{TONE_MARKS}]", "", name or "")
    s = re.sub(r"\(.*?\)|\s+", "", s)
    if s and not THAI.search(s):
        s = re.sub(r"(?i)hotsprings?|geyser|^ban", "", s.lower())
        return KEY_ALIASES.get(s, s)
    changed = True
    while changed:
        changed = False
        for pre in NAME_PREFIXES:
            p = re.sub(f"[{TONE_MARKS}]", "", pre)
            if s.startswith(p) and len(s) > len(p):
                s = s[len(p):]
                changed = True
    return KEY_ALIASES.get(s, s)


# A key that is only the generic spring word joins NOTHING: the record named
# bare น้ำพุร้อน near Chiang Dao once folded into รุ่งอรุณน้ำพุร้อน sixty km
# away because นำพุรอน is contained in half the register's keys. The guard
# `len(s) > len(p)` keeps a whole-name prefix from being peeled, so the
# generic forms are enumerated here and refused as keys — a bare-worded
# spring joins by its village or stands alone.
GENERIC_KEYS = {re.sub(f"[{TONE_MARKS}]", "", p) for p in NAME_PREFIXES} | {
    "", "นำรอน", "hotspring", "hotsprings"}


def _keys_of(entry):
    ks = []
    for f in ("nameTh", "name", "village_th"):
        v = entry.get(f)
        if v:
            k = _key(v)
            if len(k) >= 3 and k not in GENERIC_KEYS:
                ks.append(k)
    return ks


def _dist_key(d):
    """District names as the agencies actually write them: DMR shortens
    อ.เมืองแม่ฮ่องสอน to เมือง, writes กิ่งเมืองปาน for เมืองปาน and กแม่ออน
    (stray ก) for แม่ออน. Agreement below is containment, so the short form
    meets the long one."""
    s = re.sub(f"[{TONE_MARKS}]", "", d or "")
    s = re.sub(r"\s+", "", s)
    return re.sub(r"^(?:อำเภอ|อ\.|กิ่ง|ก(?=แม่))", "", s)


def _same_spring(a, b):
    """Same province, keys agree (equal or one contains the other), and the
    stated districts do not disagree. Containment needs both keys ≥3 chars
    (already enforced) so ฝาง can meet โป่งน้ำร้อนฝาง without บ meeting บ้าน.
    District agreement is containment too — DMR's เมือง must meet the CSV's
    เมืองแม่ฮ่องสอน — which is safe here because the NAME key has to agree
    first and a district is only ever asked to veto."""
    if a["province"] != b["province"]:
        return False
    da, db = _dist_key(a.get("amphoe_th")), _dist_key(b.get("amphoe_th"))
    if da and db and da != db and da not in db and db not in da:
        return False
    for ka in _keys_of(a):
        for kb in _keys_of(b):
            if ka == kb or (len(ka) >= 3 and ka in kb) or (len(kb) >= 3 and kb in ka):
                return True
    return False


def _fetch_missing(force=False):
    CACHE.mkdir(parents=True, exist_ok=True)
    todo = [k for k in NORTH if force or not (CACHE / f"{k}.json").exists()]
    if not todo:
        print("harvest: every province cached — nothing to fetch "
              "(--fetch to refresh)")
        return
    sels = QUERIES["hotsprings"]
    for n, key in enumerate(todo):
        iso, th, en = NORTH[key]
        print(f"[{n + 1}/{len(todo)}] {key} — {th} ({iso}), "
              f"{len(sels)} selectors, one a query", flush=True)
        data = fetch_wide(f"hotsprings/{key}", sels, ("area", iso))
        data["province"] = key
        data["fetched"] = date.today().isoformat()
        (CACHE / f"{key}.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=1))
        print(f"    wrote cache/hotsprings/{key}.json "
              f"({len(data.get('elements', []))} elements)", flush=True)
        if n < len(todo) - 1:
            time.sleep(PAUSE)


def _names_of(t):
    """(name, nameTh, nameEn) resolved the way import_overpass resolves them."""
    name = t.get("name") or t.get("name:th") or t.get("name:en")
    th = t.get("name:th") or (name if name and THAI.search(name) else None)
    en = t.get("name:en") or (name if name and not THAI.search(name) else None)
    return name, th, en


def _element_entries(key, doc):
    fetched = doc.get("fetched") or FETCHED
    out = []
    for el in doc.get("elements", []):
        t = el.get("tags") or {}
        name, name_th, name_en = _names_of(t)
        joined = " ".join(v for v in (t.get("name"), t.get("name:th"),
                                      t.get("name:en"), t.get("alt_name")) if v)
        if not name or not _hs.spring_hit_tags(t, joined):
            continue
        if re.search(r"\(\s*closed\b|ปิดถาวร|ปิดกิจการ", joined, re.I):
            continue
        lat = el.get("lat") or (el.get("center") or {}).get("lat")
        lng = el.get("lon") or (el.get("center") or {}).get("lon")
        out.append({
            "id": f"hs-{key}-{el['type']}-{el['id']}",
            "province": key,
            "name": name, "nameTh": name_th, "nameEn": name_en,
            "lat": lat, "lng": lng,
            "phone": t.get("phone") or t.get("contact:phone"),
            "website": t.get("website") or t.get("contact:website"),
            "hours": t.get("opening_hours"),
            "tempC": t.get("temperature"),
            "operator": t.get("operator"),
            "sources": [{"type": "osm", "ref": f"{el['type']}/{el['id']}",
                         "fetched": fetched, "via": "harvest_hotsprings"}],
        })
    return out


def _record_entries():
    out = []
    for prov in HOME:
        p = ROOT / "data" / "canonical" / f"{prov}.json"
        if not p.exists():
            continue
        d = json.loads(p.read_text())
        recs = d if isinstance(d, list) else d.get("records", [])
        for r in recs:
            if "hot-spring" not in (r.get("sub") or []):
                continue
            a = r.get("attrs") or {}
            out.append({
                "id": r["id"], "recordId": r["id"],
                "province": prov,
                "name": r.get("name"), "nameTh": r.get("nameTh"),
                "nameEn": r.get("nameEn"),
                "lat": r.get("lat"), "lng": r.get("lng"),
                "phone": r.get("phone"), "website": r.get("website"),
                "hours": r.get("hours"),
                "tempC": a.get("temperature"),
                "operator": a.get("operator"),
                "amphoe_th": a.get("amphoe"),
                "sources": r.get("sources") or [],
            })
    return out


def _mhs_entries():
    p = SRC / "mhs_hot_spring.csv"
    if not p.exists():
        return []
    rows = list(csv.reader(io.StringIO(p.read_bytes().decode("utf-8-sig"))))
    out = []
    for r in rows[1:]:
        if len(r) < 8 or not r[5]:
            continue
        out.append({
            "id": f"hs-mhs-csv-{r[0]}",
            "province": "mhs",
            "name": r[5], "nameTh": r[5], "nameEn": None,
            "lat": float(r[6]), "lng": float(r[7]),
            "amphoe_th": r[4],
            "sources": [{"type": "opendata", "ref": MHS_URL,
                         "fetched": FETCHED, "via": "data.go.th",
                         "licence": "Open Data Common",
                         "credit": "สำนักงานจังหวัดแม่ฮ่องสอน — แหล่งท่องเที่ยวน้ำพุร้อน"}],
        })
    return out


def _dnp_entries():
    p = SRC / "dnp_np_attractions.csv"
    if not p.exists():
        return []
    rows = list(csv.reader(io.StringIO(p.read_bytes().decode("cp874"))))
    pat = re.compile(r"น้ำพุร้อน|บ่อน้ำแร่")
    out = []
    for i, r in enumerate(rows[1:]):
        if len(r) < 6 or not pat.search(r[2] or ""):
            continue
        park = (r[1] or "").strip()
        prov = DNP_PARK_PROV.get(park)
        if not prov:
            continue
        name = (r[3] or "").strip()
        if "ท่าปาย" in name:
            prov = "mhs"
        try:
            lat, lng = float(r[4]), float(r[5])
        except ValueError:
            lat = lng = None
        out.append({
            "id": f"hs-dnp-{i}",
            "province": prov,
            "name": name, "nameTh": name, "nameEn": None,
            "lat": lat, "lng": lng,
            "park_th": f"อุทยานแห่งชาติ{park.split(' (')[0]}",
            "sources": [{"type": "opendata", "ref": DNP_URL,
                         "fetched": FETCHED, "via": "data.go.th",
                         "licence": "Open Data Common",
                         "credit": "กรมอุทยานแห่งชาติ สัตว์ป่า และพันธุ์พืช — "
                                   "แหล่งท่องเที่ยวในอุทยานแห่งชาติ (02/2566)"}],
        })
    return out


def _dmr_enrich(entries):
    """The measured temperatures. A DMR row joins one folded entry when
    _same_spring says so; everything unmatched becomes its own register row
    with district-level location and no pin — a spring the inventory knows
    and no map or list has reached yet is exactly what the board's
    tell-the-ants line is for."""
    p = SRC / "dmr_table.json"
    if not p.exists():
        return entries, 0, 0
    rows = json.loads(p.read_text())
    dmr_src = {"type": "survey", "ref": DMR_URL, "fetched": FETCHED,
               "via": "dmr.go.th",
               "credit": "กรมทรัพยากรธรณี — แหล่งน้ำพุร้อนในประเทศไทย"}
    joined = added = 0
    for r in rows:
        if len(r) < 7 or r[0] == "ที่" or r[5] not in PROV_BY_TH:
            continue
        code, name, village, amphoe, prov_th = r[1], r[2], r[3], r[4], r[5]
        temp = (r[6] or "").strip()
        temp = temp if temp not in ("", "0", "-") else None
        ph = (r[7] or "").strip() if len(r) > 7 else None
        ph = ph if ph not in ("", "-", "nd") else None
        probe = {"province": PROV_BY_TH[prov_th], "name": name,
                 "nameTh": name, "village_th": village,
                 "amphoe_th": amphoe}
        hit = next((e for e in entries if _same_spring(e, probe)), None)
        if hit is not None:
            if temp and not hit.get("tempC"):
                hit["tempC"] = temp
                hit["temp_by"] = "กรมทรัพยากรธรณี (DMR)"
            if ph and not hit.get("ph"):
                hit["ph"] = ph
            hit.setdefault("dmr_code", code)
            if not hit.get("amphoe_th"):
                hit["amphoe_th"] = amphoe
            hit["sources"] = (hit.get("sources") or []) + [dmr_src]
            joined += 1
        else:
            springy = re.search(r"โป่ง|น้ำร้อน|น้ำพุ|น้ำอุ่น", name)
            display = name if springy else f"น้ำพุร้อน{name}"
            entries.append({
                "id": f"hs-dmr-{code}",
                "province": PROV_BY_TH[prov_th],
                "name": display, "nameTh": display, "nameEn": None,
                "lat": None, "lng": None,
                "village_th": (f"บ้าน{village}" if village and
                               not village.startswith(("บ้าน", "หมู่", "อุทยาน",
                                                       "สำนักสงฆ์")) else village) or None,
                "amphoe_th": amphoe,
                "tempC": temp, "temp_by": ("กรมทรัพยากรธรณี (DMR)" if temp else None),
                "ph": ph, "dmr_code": code,
                "sources": [dmr_src],
            })
            added += 1
    return entries, joined, added


def _fold(entries):
    """Same spring, several agencies: fold to one row. The first arrival
    keeps id and name (records come first, so a catalogue spring keeps its
    recordId); later arrivals fill empty fields and append their sources.
    The drop is printed, never silent."""
    kept = []
    for e in entries:
        hit = next((k for k in kept if _same_spring(k, e)), None)
        if hit is None:
            kept.append(e)
            continue
        for f in ("lat", "lng", "phone", "website", "hours", "tempC",
                  "operator", "amphoe_th", "village_th", "park_th", "nameEn"):
            if not hit.get(f) and e.get(f):
                hit[f] = e[f]
        hit["sources"] = (hit.get("sources") or []) + (e.get("sources") or [])
        print(f"  folded: {e.get('name')} ({e['province']}) → {hit.get('name')}")
    return kept


def _apply_curated(springs):
    """data/curated/hotsprings.json outranks everything else, the house rule.

    Shape: {"springs": {<register id>: {fields…}}, "additions": [...],
    "unverified": [...]}. An addition needs `province` and at least one
    source, the same bar the harvest meets. `unverified` is leads, never
    rendered; it rides along so the register file documents what is still
    unread.
    """
    if not CURATED.exists():
        return springs, []
    cur = json.loads(CURATED.read_text())
    by_id = {s["id"]: s for s in springs}
    for sid, fields in (cur.get("springs") or {}).items():
        s = by_id.get(sid)
        if not s:
            print(f"  curated: {sid} matches no register entry — left for "
                  f"a person (id drift, or the crawl lost it)")
            continue
        for k, v in fields.items():
            if k == "sources":
                s["sources"] = (s.get("sources") or []) + v
            else:
                s[k] = v
        s["curated"] = True
    adds = []
    for entry in (cur.get("additions") or []):
        if not entry.get("province") or not entry.get("sources"):
            raise SystemExit(f"curated addition needs province + sources: "
                             f"{entry.get('name') or entry}")
        adds.append({**entry, "curated": True})
    return springs + adds, cur.get("unverified") or []


def assemble():
    entries = []
    entries += _record_entries()
    # A province whose fetch lost selectors is short, not done — fetch_wide
    # writes the failures into the file, and the register repeats them so no
    # page built on it can quietly read "asked" as "answered". Re-run
    # `harvest_hotsprings.py --fetch` when the mirrors are calmer.
    short = {}
    for key in NORTH:
        p = CACHE / f"{key}.json"
        if p.exists():
            doc = json.loads(p.read_text())
            entries += _element_entries(key, doc)
            if doc.get("incomplete"):
                short[key] = len(doc["incomplete"])
    entries += _mhs_entries()
    entries += _dnp_entries()
    # A way that crosses a province line answers both areas' queries; the
    # first listing keeps it and the drop is said out loud, never silent.
    seen_refs, unique = {}, []
    for s in entries:
        ref = next((src.get("ref") for src in (s.get("sources") or [])
                    if src.get("type") == "osm"), None)
        if ref and ref in seen_refs and seen_refs[ref] != s["province"]:
            print(f"  dropped duplicate across provinces: {s['name']} "
                  f"({s['province']}) — kept in {seen_refs[ref]}")
            continue
        if ref:
            seen_refs[ref] = s["province"]
        unique.append(s)
    folded = _fold(unique)
    folded, dmr_joined, dmr_added = _dmr_enrich(folded)
    springs, unverified = _apply_curated(folded)
    order = {k: i for i, k in enumerate(list(HOME) + list(NORTH))}
    springs.sort(key=lambda s: (order.get(s["province"], 99),
                                (s.get("nameTh") or s.get("name") or "")))
    provinces = {}
    for k, (iso, th, en) in {**HOME, **NORTH}.items():
        n = sum(1 for s in springs if s["province"] == k)
        if n:
            provinces[k] = {"iso": iso, "th": th, "en": en, "count": n}
    doc = {
        "_readme": ("The northern hot-springs register (WO-23). CM/CR rows "
                    "carry recordId and are the catalogue's own records; the "
                    "other provinces are register-only, harvested area-clipped "
                    "per ISO 3166-2 province from OSM plus the DNP park list, "
                    "Mae Hong Son's own CSV and the DMR inventory (measured "
                    "temperature + pH, district-level, no pins). Curated "
                    "fields outrank harvested ones and carry their own "
                    "sources; prices are posted spreads, temperatures are "
                    "somebody's measurement (temp_by says whose), and nothing "
                    "here ranks a soak."),
        "generated": date.today().isoformat(),
        "provinces": provinces,
        "springs": springs,
        "unverified": unverified,
    }
    if short:
        doc["incomplete_provinces"] = short
        print(f"  short fetches (selectors lost, refetch when calmer): {short}")
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1))
    pinned = sum(1 for s in springs if s.get("lat"))
    temps = sum(1 for s in springs if s.get("tempC"))
    print(f"register: {len(springs)} springs / {len(provinces)} provinces "
          f"({pinned} pinned, {temps} with a stated temperature; "
          f"DMR joined {dmr_joined}, added {dmr_added}) → data/hotsprings.json")
    for k, meta in provinces.items():
        print(f"    {meta['th']:14s} {meta['count']}")


def main():
    args = sys.argv[1:]
    if "--assemble" not in args:
        _fetch_missing(force="--fetch" in args)
    assemble()


if __name__ == "__main__":
    main()
