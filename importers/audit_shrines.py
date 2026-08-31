#!/usr/bin/env python3
"""Read what the catalogue holds and drops about the shrines. Zero network.

Same contract as audit_hotsprings.py and audit_views.py: this never edits
canonical data. It reports, and import_overpass.shrines_hit() borrows THIS
FILE's rules (one copy) to file shrine-shaped elements — from the culture
group's historic dragnet it already caught three of, and from the `shrines`
crawl group when Nan gives that group its go. Until then the group is staged
and nothing fetches.

The measurement that asked for this (notes/shrines-proposal-2026-08-27.md):
on 2026-08-27 the wat top shelf — named วัด-สิ่งศักดิ์สิทธิ์ since launch —
held 2,677 of 2,680 records with no sub at all, its one child (ศาลพระภูมิ)
held one record, and no crawl group had ever asked `historic=wayside_shrine`
or any place_of_worship religion. Thirteen real public shrines were in the
catalogue anyway, read out of the names in Thai; ศาลเจ้าปุงเถ่ากง — the
oldest Chinese shrine in Chiang Mai in the municipality's own telling — was
in none of the 20,699 records.

Reports:

  SHELF    what sub=shrine holds today, by province, with pin coverage.
  FILED    records whose own name or cached tag states a shrine, and the
           shelf each one stands on — the thirteen, before and after they
           are seated.
  STRAYS   every fence, each with its witnesses found live in the data:
           ศาลา, the courts, …ไพศาล, เจ้าพ่อหลวงอุปถัมภ์, the locative
           หน้าศาลเจ้า, and the namesakes.
  LIST     the WO-16 data.go.th religious rows read with this file's rules:
           which of the 79 state a shrine, and how many carry a pin.
  NEVER    selectors absent from crawl_overpass.py, and the famous-shrines
           roll probed against the shelf and the register.

What this deliberately does NOT do:

  * Rank a shrine. Nothing is ศักดิ์สิทธิ์ที่สุด on this site; no list
    sorts shrines by power, and what a shrine is said to be good for asking
    renders as the tradition's claim, never as advice.
  * File a household spirit house. A ศาลพระภูมิ inside somebody's compound
    is home practice, not directory material. Public ground only.
  * Guess a kind. The kind is read off the keeper's own name for the place
    (ศาลเจ้า, หลักเมือง, เทวาลัย, หอ); a name that states nothing files
    nothing.
"""
import argparse
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------- the rules
# Shared with import_overpass.shrines_hit() — one copy. Each fence carries a
# witness for why it exists, all of them found live in the 2026-08-27 survey.

# ศาลา is not ศาล: ศาลาธรรม (way/311213404) is a pavilion, ศาลากลาง the
# provincial hall. Every ศาล match below is written ศาล(?!า).
#
# The courts: ศาลแขวงเชียงดาว, ศาลอุทธรณ์ภาค 5, ศาลเยาวชนและครอบครัวฯ (all
# live in cache/overpass/cm/government.json) — and แยกศาลเด็ก, the crossing
# the post office is named for.
COURT = re.compile(r"ศาล(?:จังหวัด|แขวง|อุทธรณ์|ปกครอง|เยาวชน|แรงงาน|ฎีกา"
                   r"|ล้มละลาย|ภาษี|ทหาร|เด็ก|ยุติธรรม|ผู้บริโภค)")

# เจ้าพ่อหลวง is the King: six OBEC schools are named
# โรงเรียนเจ้าพ่อหลวงอุปถัมภ์ / เจ้าแม่หลวงอุปถัมภ์ (royal patronage), one of
# them spelled อุปถัมป์ (node 2556170251) — the fence takes both spellings.
ROYAL_PATRON = re.compile(r"เจ้า(?:พ่อ|แม่)หลวงอุปถัม[ภป]")

# A place BESIDE the shrine borrows its name to give directions: ขาหมูแสนคำ
# (หน้าศาลเจ้าแม่จัน) is a pork-leg stall. Locative words before ศาล mean
# the name is navigating, not naming.
LOCATIVE = re.compile(r"(?:หน้า|ใกล้|ข้าง|ตรงข้าม|หลัง|แถว|ริม)ศาล")

# Rows whose FIRST word says they are something else wearing a sacred name —
# the audit_hotsprings NAMED_ELSE arrangement. Witnesses: วัดอินทขีลสะดือเมือง
# is a wat (the pillar's origin temple — the register's business, not a sub);
# พุทธสถานเชียงใหม่ carries "Buddhist Shrine" in its English name and is the
# Buddhist Association hall; ดอยศาลเจ้าศรีสมบูรณ์ is a peak named for the
# shrine on it; บ้านเอื้ออาทรเจ้าแม่กวนอิม is public housing named after the
# temple nearby; ร้านเจกวนอิม is a เจ shop; เตาเม็งราย a kiln shop.
NAMED_ELSE = re.compile(r"^\s*(?:วัด|พุทธสถาน|โบสถ์|มัสยิด|สุเหร่า|ชุมชน"
                        r"|หมู่บ้าน|บ้าน|ดอย|ถ้ำ|น้ำตก|โรงเรียน|โรงพยาบาล"
                        r"|รพ\.?สต|ร้าน|ครัว|ขาหมู|ก๋วยเตี๋ยว|ไปรษณีย์"
                        r"|บริษัท|หจก|ห\.ส\.น|ตลาด|คอนโด|หอพัก|อพาร์"
                        r"|โรงแรม|รีสอร์ท|เกสต์|สภ\.|อบต|เทศบาล|สำนักงาน"
                        r"|ที่ทำการ|ธนาคาร|ศูนย์|สถานี|แยก|ซอย|ถนน)")

# What states a shrine, in the keeper's own words. Order matters: the most
# specific compound wins, so ศาลเจ้าพ่อหลักเมืองแจ่งกระต๊ำ reads as a city
# pillar before it reads as a generic ศาลเจ้า.
SHRINE_RULES = [
    ("lak-mueang", r"ศาลหลักเมือง|เสาหลักเมือง|หลักเมือง|สะดือเมือง|อินทขีล"),
    ("spirit-house", r"ศาลพระภูมิ|ศาลเจ้าที่|ศาลตายาย|ศาลปู่ย่า"),
    ("thewalai", r"เทวาลัย|เทวสถาน|พิฆเนศวร"),
    ("arak", r"หอผี|หอเสื้อ|หออารักษ์|ปู่แสะ|ย่าแสะ|พระสยามเทวาธิราช"),
    ("san-chao", r"ศาลเจ้า(?!า)"),
    # Bare ศาล only at the name's start (…ไพศาล embeds the letters ศ-า-ล:
    # เวชไพศาลฟาร์ม่า is a pharmacy, ไพศาลศาสตร์ a school) and only when it
    # is not ศาลา and not a court. ศาลสมเด็จพระนเรศวรมหาราช enters here.
    ("shrine", r"^ศาล(?!า)"),
]
SHRINE_EN = re.compile(r"\bshrine\b|\bjoss\s*house\b|\bcity\s+pillar\b"
                       r"|\bdevalaya\b", re.I)

# Tag values that state the thing itself (checked before any name rule, the
# natural=hot_spring arrangement): OSM's own wayside_shrine, and a
# place_of_worship whose stated religion is the ศาลเจ้า / เทวาลัย family.
SHRINE_RELIGIONS = {"taoist", "confucian", "chinese_folk", "folk"}


def shrine_kind(name):
    """The kind a NAME states — 'lak-mueang' / 'spirit-house' / 'thewalai' /
    'arak' / 'san-chao' / 'shrine' — or None with the fences' reasons why
    not. Kind granularity is the register's business; the shelf sub is
    always plain 'shrine'."""
    if not name:
        return None
    if NAMED_ELSE.match(name) or COURT.search(name):
        return None
    if ROYAL_PATRON.search(name) or LOCATIVE.search(name):
        return None
    plain = name.replace("ศาลา", "∅")   # ศาลา can never satisfy ศาล(?!า) twice-removed
    for kind, pat in SHRINE_RULES:
        if re.search(pat, plain):
            return kind
    if SHRINE_EN.search(name):
        return "shrine"
    return None


def shrine_fence_reason(name):
    """Why a shrine-flavoured name may NOT file — for the STRAYS report."""
    if not name:
        return None
    if COURT.search(name):
        return "court"
    if ROYAL_PATRON.search(name):
        return "royal-patronage school"
    if LOCATIVE.search(name):
        return "locative — beside the shrine, not the shrine"
    if NAMED_ELSE.match(name):
        return "something else first (" + NAMED_ELSE.match(name).group().strip() + "…)"
    return None


def record_kind(r):
    """The kind a RECORD states, across all three of its names — with a
    fence on ANY name vetoing a match on another. The witness:
    พุทธสถานเชียงใหม่ carries the English name "Chiang Mai Buddhist Shrine",
    and reading the English alone filed the Buddhist Association hall as a
    shrine while the Thai name was saying พุทธสถาน the whole time."""
    names = [str(r.get(k) or "") for k in ("name", "nameTh", "nameEn")]
    if any(shrine_fence_reason(n) for n in names if n):
        return None
    for n in names:
        k = shrine_kind(n)
        if k:
            return k
    return None


def shrines_hit(t, name=""):
    """'shrine' if the element states a shrine, else None — the one-copy
    fence import_overpass borrows when the staged `shrines` group runs.

    historic=wayside_shrine states the thing itself and is checked before
    every fence (Kuan Imm Palace, way/38487629, carries it with a name no
    Thai rule could read). A place_of_worship files only when its stated
    religion is in the ศาลเจ้า family — Buddhist ones are wats and belong
    to the register fold, Christian and Muslim ones are the church-and-
    mosque order this one deliberately is not. Everything else answers to
    the name rules, fences first.
    """
    t = t or {}
    if t.get("historic") == "wayside_shrine":
        return "shrine"
    if t.get("amenity") == "place_of_worship":
        return "shrine" if t.get("religion") in SHRINE_RELIGIONS else None
    if t.get("shop") == "religion":
        return None          # the trade is real and is NOT a shrine — its
                             # shelf waits for records (proposal, doors)
    return "shrine" if shrine_kind(name) else None


# The famous roll — names a reader of either province would try first, probed
# against shrine-named records and the register. Each is a question, not a
# claim: ABSENT is a finding either way.
FAMOUS = [
    ("cm", "ปุงเถ่ากง"), ("cm", "ทับทิม"), ("cm", "กวนอู"),
    ("cm", "อินทขีล"), ("cm", "แจ่งกระต๊ำ"), ("cm", "ปู่แสะ"),
    ("cm", "เทวาลัย"), ("cm", "เมืองงาย"), ("cm", "เจ้าหลวงคำแดง"),
    ("cm", "ข้อมือเหล็ก"), ("cm", "กวนอิม"),
    ("cr", "สะดือเมือง"), ("cr", "แม่สาย"), ("cr", "พญาแสนภู"),
    ("cr", "จี้กง"), ("cr", "แม่จัน"), ("cr", "ห้วยปลากั้ง"),
    ("cr", "มังราย"), ("cr", "แม่สลอง"),
]


def load_records():
    recs = []
    for f in sorted((ROOT / "data" / "canonical").glob("*.json")):
        d = json.loads(f.read_text())
        recs.extend(d if isinstance(d, list) else d.get("records", []))
    return recs


def name_of(r):
    return " ".join(str(r.get(k) or "") for k in ("name", "nameTh", "nameEn"))


def cached_wayside():
    """Elements any past crawl already fetched that carry
    historic=wayside_shrine — the culture dragnet's three, read back out of
    the cache the way audit_culture reads museum=*."""
    out = []
    for p in sorted((ROOT / "cache" / "overpass").glob("*/*.json")):
        try:
            els = json.loads(p.read_text()).get("elements", [])
        except Exception:
            continue
        for e in els:
            t = e.get("tags") or {}
            if t.get("historic") == "wayside_shrine":
                out.append((p.parent.name, f"{e['type']}/{e['id']}",
                            t.get("name") or t.get("name:en") or "(no name)"))
    return sorted(set(out))


def band(title, note=""):
    print()
    print("=" * 72)
    print(title + ("  —  " + note if note else ""))
    print("=" * 72)


def report_shelf(recs):
    sh = [r for r in recs if "shrine" in (r.get("sub") or [])]
    band("SHELF", "sub=shrine today")
    for prov in ("cm", "cr"):
        rows = [r for r in sh if r.get("province") == prov]
        pinned = sum(1 for r in rows if r.get("lat") is not None)
        print(f"  {prov}: {len(rows)} records — pinned {pinned}")
        for r in rows:
            print(f"      {r['id']:44s} {r.get('name')}")
    if not sh:
        print("  (nothing stands on the shelf — the measurement this order opens with)")
    return sh


def report_filed(recs):
    band("FILED", "records whose name or cached tag states a shrine, and where each stands")
    wayside = {ref.split("/", 1)[1] if False else ref: nm
               for _, ref, nm in cached_wayside()}
    wayside_ids = {f"{prov}-osm-{ref.replace('/', '-')}"
                   for prov, ref, _ in cached_wayside()}
    rows = []
    for r in recs:
        kind = record_kind(r)
        if not kind and r["id"] in wayside_ids:
            kind = "shrine (cached historic=wayside_shrine)"
        if kind:
            rows.append((r, kind))
    for r, kind in sorted(rows, key=lambda x: x[0]["id"]):
        shelf = "+".join(r.get("cat") or []) + "/" + "+".join(r.get("sub") or ["—"])
        lens = (r.get("attrs") or {}).get("lens")
        note = "  lens=" + ",".join(lens) if lens else ""
        print(f"  {r['id']:44s} {kind:14s} on {shelf:22s} {r.get('name') or r.get('nameEn')}{note}")
    print(f"  ({len(rows)} records)")
    return rows


def report_strays(recs):
    band("STRAYS", "every fence, with its witnesses live in the data")
    groups = {}
    for r in recs:
        n = name_of(r)
        if "ศาล" not in n.replace("ศาลา", "") and not SHRINE_EN.search(n) \
                and "กวนอิม" not in n and "เจ้าพ่อ" not in n and "เจ้าแม่" not in n:
            continue
        if record_kind(r):
            continue
        why = (shrine_fence_reason(r.get("name") or "")
               or shrine_fence_reason(r.get("nameTh") or "")
               or shrine_fence_reason(r.get("nameEn") or ""))
        if why is None and ("ไพศาล" in n or "ศาล" not in n):
            why = "namesake / embedded letters"
        if why:
            groups.setdefault(why, []).append(r.get("name") or r.get("nameEn"))
    for why, names in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        head = ", ".join(str(x)[:36] for x in names[:3])
        more = f" … +{len(names) - 3}" if len(names) > 3 else ""
        print(f"  {why:44s} {len(names):3d}   {head}{more}")


def report_list(recs):
    band("LIST", "the WO-16 data.go.th religious rows, read with this file's rules")
    rel = [r for r in recs if "-dgth-religious-" in r["id"]]
    hits = [(r, shrine_kind(r.get("name") or "")) for r in rel]
    hits = [(r, k) for r, k in hits if k]
    pinned = sum(1 for r, _ in hits if r.get("lat") is not None)
    print(f"  {len(rel)} rows on the list; {len(hits)} state a shrine; {pinned} of those pinned")
    for r, k in hits:
        print(f"      {r['id']:44s} {k:12s} {r.get('name')}")


def report_never(recs, register_names=""):
    band("NEVER", "what no crawl has asked, and the famous roll against the shelf")
    qtext = (ROOT / "importers" / "crawl_overpass.py").read_text()
    for sel in ('historic"="wayside_shrine', 'religion"="taoist',
                'shop"="religion'):
        state = "asked" if sel in qtext else "NEVER ASKED"
        print(f"  {sel:32s} {state}")
    print()
    shrine_names = " ".join(
        name_of(r) for r in recs
        if "shrine" in (r.get("sub") or []) or record_kind(r))
    reg_path = ROOT / "data" / "shrines.json"
    reg_names = ""
    if reg_path.exists():
        reg = json.loads(reg_path.read_text())
        reg_names = " ".join(
            f"{e.get('nameTh') or ''} {e.get('nameEn') or ''} {e.get('note_th') or ''}"
            for e in reg.get("shrines", []))
    for prov, f in FAMOUS:
        where = ("catalogue" if f in shrine_names
                 else "register" if f in reg_names else "ABSENT")
        print(f"  {prov:4s} {f:18s} {where}")


def emit_shelves(recs):
    """Print data/curated/shelves.json entries seating the found records on
    sub=shrine — the WO-22 arrangement: the source is the sign itself (or
    the open list that carries the row). Never applied automatically; a
    person reads every line before it enters curated."""
    wayside_ids = {f"{prov}-osm-{ref.replace('/', '-')}": ref
                   for prov, ref, _ in cached_wayside()}
    out = {}
    today = date.today().isoformat()
    for r in recs:
        if "shrine" in (r.get("sub") or []):
            continue
        lens = (r.get("attrs") or {}).get("lens") or []
        if "spirit-house" in lens:
            continue          # the ศาลพระภูมิ child already holds it
        kind = record_kind(r)
        via_tag = r["id"] in wayside_ids
        if not kind and not via_tag:
            continue
        cats = r.get("cat") or []
        # A shrine-flavoured name on a shelf that is neither wat nor sights
        # is a LEAD, not a seat: Roi Dvarapala Ban Devalaya sits on
        # community/clubs, and its tags outrank its name until somebody
        # reads its door. The staged crawl and the review file are for it.
        if not set(cats) & {"wat", "sights"}:
            continue
        entry = {"note": f"{r.get('name') or r.get('nameEn')} — "
                         f"{kind or 'shrine'}; WO-39 seat on the shrine shelf",
                 "add_sub": ["shrine"]}
        if "wat" not in cats:
            entry["add_cat"] = ["wat"]
        if via_tag:
            entry["source"] = f"osm historic=wayside_shrine ({wayside_ids[r['id']]})"
        elif "-dgth-" in r["id"]:
            entry["source"] = "data.go.th religious/attraction list (WO-16 fold; see data/curated/datagoth.json)"
        else:
            entry["source"] = f"osm name: {r.get('name') or r.get('nameEn')}"
        entry["fetched"] = today
        out[r["id"]] = entry
    print(json.dumps(out, ensure_ascii=False, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--emit", action="store_true",
                    help="print shelves.json entries for the found records")
    args = ap.parse_args()
    recs = load_records()
    if args.emit:
        emit_shelves(recs)
        return
    print(f"catalogue: {len(recs)} records")
    report_shelf(recs)
    report_filed(recs)
    report_strays(recs)
    report_list(recs)
    report_never(recs)


if __name__ == "__main__":
    main()
