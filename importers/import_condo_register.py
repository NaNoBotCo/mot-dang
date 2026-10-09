#!/usr/bin/env python3
"""Fold the Treasury's condominium register into records. WO-27, door 6b.

The register (data/curated/condo_register.json, harvested by
importers/harvest_condo_register.py) names 385 registered อาคารชุด in the two
provinces. The catalogue holds 53 buildings whose own name says condominium,
because that is all OpenStreetMap knows. This closes the gap the way the ONAB
temple register closed the wat one: the official list becomes records, each
carrying its register lineage, and each stating what it does not have.

WHAT THESE RECORDS ARE AND ARE NOT. The register gives a name, an amphoe,
sometimes a tambon, the use categories, and the Treasury's assessed value per
square metre. It gives NO coordinate, NO phone and NO street address — so
every record made here is `geoPrecision: needs-pin` and lands on the pin hunt,
exactly like the 943 register temples that arrived the same way. A building
that cannot be pinned is still worth holding: a reader searching a
condominium by name now finds that it exists, which amphoe it is in, and what
the government assesses it at. That is more than the silence it replaces.

ราคาประเมิน IS NOT A MARKET PRICE. It is the figure transfer fees and taxes
are reckoned from, normally well below what anybody pays. It is stored as a
SPREAD (a building carries a row per use category and floor band) and every
surface that renders it must say what it is. The words are in the register's
own _readme and on /realestate.html.

DEDUPE IS BY EXACT NAME ONLY, and the near-misses go to a person. A loose
join matched นครพิงค์คอนโดมิเนียม to เพชรนครพิงค์ — a different building —
so a loose SKIP would silently drop a real building from the catalogue and a
loose MERGE would put one building's valuation on another. Exact matches are
skipped (the record already exists); everything else is created, and any
near-miss is written to cache/condo_register_review_<prov>.txt where a person
can settle it into data/curated/merges.json. Merging is never automatic here.

THE EXACT JOIN IS BLIND TO HALF THE SHELF (WO-56, 2026-09-04). The register
writes every name in Thai — ปันนา เรสซิเดนซ์ 1 แอท นิมมาน — and 185 of the
353 mapped buildings in Chiang Mai carry no Thai name at all, only the Latin
one on the sign: Punna Residence. Nothing the exact join could ever match, so
one building stood on the shelf three times (two map footprints in English,
a register row in Thai with no pin) and a resident searching for it said the
site did not have it. `loanword_candidates()` reads the register's Thai by
RTGS (translit.py) and compares the CONSONANT SKELETON of the brand words —
ปันนา → Panna → pnn, Punna → pnn — with the generic words (residence, condo,
mansion, @) stripped and the building numbers compared separately. It writes
CANDIDATES to the same review file, tiered by whether the numbers agree, and
merges nothing: the rule above stands, a person settles each pair. What it
adds is that the person now has the list. The same file also names every
building's COMPLEX (attrs.complex — the name with its number and generic
words removed) so a page can point at its siblings: 109 register buildings
sit in 33 numbered complexes, One Plus Suan Dok 1–11 alone being eleven rows
against one map relation.

A REGISTER BUILDING IS A CONDOMINIUM. `settle_sub()` runs after the curated
merges: a record carrying the Treasury's register source files sub `condo`,
and the mapper's `apartment` comes off. Provenance: the register lists
buildings registered under the Condominium Act B.E. 2522 — that registration
is what makes a building an อาคารชุด — while building=apartments describes
the building's form, not its tenure. The state's word on the legal kind beats
the mapper's word on the shape.

    python3 importers/import_condo_register.py --dry-run
    python3 importers/import_condo_register.py            # (called by import_all)
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "data" / "curated" / "condo_register.json"
MERGES = ROOT / "data" / "curated" / "merges.json"
sys.path.insert(0, str(ROOT))
import translit  # noqa: E402  — the RTGS reader, for the loanword join

_GENERIC_TH = ("คอนโดมิเนียม", "คอนโด", "อาคารชุด", "condominium", "condo")


def complex_key(name):
    """The name with its building number and the generic words removed — what
    ปันนาเรสซิเดนซ์ 3, ปันนาเรสซิเดนซ์ 5 and ปันนา เรสซิเดนซ์ 1 แอท นิมมาน do
    NOT share (the qualifier is part of the key), and what วันพลัส คอนโด
    สวนดอก 1 … 11 do. Only a key held by two or more register rows in the same
    province is written to a record; a key of one names nothing."""
    s = unicodedata.normalize("NFC", name or "")
    s = re.sub(r"\s*(อาคาร|ตึก)\s*[A-Za-zก-ฮ0-9]{1,2}\s*$", "", s)
    s = re.sub(r"[\s\-–—_.,()\"']+", " ", s)
    for w in _GENERIC_TH:
        s = re.sub(re.escape(w), " ", s, flags=re.I)
    s = re.sub(r"\s*\d+\s*$", "", s)
    s = re.sub(r"\s*(เฟส|ระยะ)\s*$", "", s)
    return re.sub(r"\s+", " ", s).strip().lower()


# Words that name the KIND of building, not the building. Stripped before the
# skeletons are compared, so "The Chai Condominium" cannot meet "Building C"
# on the strength of a shared "c" — every remaining token has to agree.
_GEN_WORDS = {
    "residence", "residences", "resident", "condo", "condominium",
    "condominiums", "apartment", "apartments", "mansion", "court", "place",
    "tower", "towers", "the", "at", "aet", "a", "and", "park", "plaza",
    "view", "city", "home", "homes", "house", "chiangmai", "chiang", "mai",
    "chiangrai", "rai", "nimman", "nimmana", "nimmanhaemin", "suthep",
    "huaykaew", "bldg", "building", "phase",
}


def _skel(w):
    w = re.sub(r"ph", "f", w)
    w = re.sub(r"th", "t", w)
    w = re.sub(r"ck", "k", w)
    w = w.replace("c", "k").replace("q", "k").replace("x", "ks")
    w = re.sub(r"[aeiouyhw]", "", w)
    return re.sub(r"(.)\1+", r"\1", w)


def _keys(latin):
    """(consonant skeletons of the brand words, the numbers) of a Latin name."""
    s = unicodedata.normalize("NFKC", latin or "").lower()
    s = re.sub(r"[@&]", " ", s)
    toks = re.findall(r"[a-z]+|\d+", s)
    nums = tuple(t for t in toks if t.isdigit())
    words = tuple(_skel(t) for t in toks if t.isalpha() and t not in _GEN_WORDS)
    words = tuple(w for w in words if w)
    return words, nums


def loanword_candidates(reg_rows, records, settled=frozenset()):
    """[(register name, RTGS reading, held name, held id, province, flag)]
    — register rows whose Thai spelling of a Latin name reads like a mapped
    building's Latin name. Strict on purpose: every brand token must agree,
    each at least two consonants long. The floor is TWO consonants in total,
    not four: Punna reduces to `pn` (the doubled n collapses), so a higher
    floor would have missed the building this work order started with. Two is
    only safe because the Latin side is confined to the housing shelf — the
    same skeleton over the whole catalogue offered a temple for a
    condominium. It yields 26 candidates across both provinces, a list a
    person can read in one sitting, and merges none of them. A building number
    on
    one side that the other lacks is reported as `number unconfirmed`; numbers
    that disagree are not a candidate at all. Rows already settled in
    merges.json (by their register id) are left out."""
    latin = []
    for r in records:
        if str(r.get("id", "")).find("condoreg") != -1:
            continue
        # ONLY the housing shelf. A skeleton is a coarse instrument: with the
        # vowels gone เฮือนป้อเลี้ยง reads onto Wat Luang, Doi Lang and a
        # music shop alike, and a candidate list that offers a person a temple
        # for a condominium teaches them to stop reading the list. A
        # registered อาคารชุด is a building on this shelf or it is not here.
        if "realestate" not in (r.get("cat") or []):
            continue
        for nm in (r.get("name"), r.get("nameEn"), r.get("nameTh")):
            if nm and re.search(r"[A-Za-z]{3}", nm):
                w, n = _keys(nm)
                if w and len("".join(w)) >= 2 and all(len(x) >= 2 for x in w):
                    latin.append((w, n, nm, r))
    out, seen = [], set()
    for e in reg_rows:
        name = (e.get("name") or "").strip()
        if e.get("_id") in settled:
            continue
        reading = translit.reading(name) if re.search(r"[ก-๙]", name) else name
        w, n = _keys(reading)
        if not w or len("".join(w)) < 2 or any(len(x) < 2 for x in w):
            continue
        for lw, ln, nm, r in latin:
            if lw != w:
                continue
            if n and ln and n != ln:
                continue
            flag = "number agrees" if n == ln else "number unconfirmed"
            key = (name, r["id"])
            if key in seen:
                continue
            seen.add(key)
            out.append((name, reading, nm, r["id"], e.get("province"), flag))
    return out


def settled_register_ids():
    """Register ids a person has already folded into a map record."""
    if not MERGES.exists():
        return frozenset()
    m = (json.loads(MERGES.read_text()) or {}).get("merges") or {}
    return frozenset(d for drops in m.values() for d in drops if "condoreg" in d)


def settle_sub(records):
    """A record the Treasury's register names is a condominium: sub `condo`,
    and the mapper's `apartment` comes off. Runs after the curated merges, so
    a map footprint a person folded a register row into is re-filed by the
    register's word. See the module docstring for the provenance. Returns
    how many records changed shelf."""
    n = 0
    for r in records:
        srcs = r.get("sources") or []
        if not any(s.get("type") == "register" and "condominium" in str(s.get("ref") or "")
                   for s in srcs):
            continue
        if "realestate" not in (r.get("cat") or []):
            continue
        old = sorted(set(r.get("sub") or []))
        new = sorted((set(old) - {"apartment"}) | {"condo"})
        if new != old:
            r["sub"] = new
            n += 1
    return n


def norm(s):
    """A building name reduced to the part that identifies it. Same rule as
    realestate_layer.join_register — one normalisation, two callers."""
    s = unicodedata.normalize("NFC", (s or "")).lower()
    s = re.sub(r"[\s\-–—_.,()\"']", "", s)
    for w in ("คอนโดมิเนียม", "คอนโด", "condominium", "condo", "อาคารชุด"):
        s = s.replace(w, "")
    return s


def slug(name, province, seen):
    """A stable id from the name. The register has no id of its own that
    survives a re-publish, and a positional index would renumber every record
    the day the Treasury inserts a row — the WO-24 lesson about ids that move."""
    base = re.sub(r"[^0-9a-zA-Zก-๙]+", "-", unicodedata.normalize("NFC", name)).strip("-").lower()
    base = base[:48] or "unnamed"
    sid = f"{province}-condoreg-{base}"
    n = 2
    while sid in seen:
        sid = f"{province}-condoreg-{base}-{n}"
        n += 1
    seen.add(sid)
    return sid


def fold(existing_records):
    """(new_records, review_rows). Never mutates what it is given."""  # stylecheck: allow — code docstring
    if not REG.exists():
        return [], []
    doc = json.loads(REG.read_text())
    src = doc.get("source") or {}
    edition = src.get("edition") or doc.get("generated") or ""

    exact, loose = {}, {}
    # Held ids, so a second run cannot create a building it made on the first.
    # Name matching alone is NOT enough for that: a name that normalises to
    # fewer than four characters (ตุง คอนโด -> ตุง) is created but can never
    # be matched, so it would arrive again on every import and the same id
    # would appear twice in the file. Idempotency is checked on the id itself.
    held_ids = {r.get("id") for r in existing_records}
    for r in existing_records:
        for nm in (r.get("name"), r.get("nameTh"), r.get("nameEn")):
            k = norm(nm)
            if len(k) >= 4:
                exact.setdefault(k, r)
                loose.setdefault(k, r)

    out, review, seen_ids = [], [], set()
    # WO-56: how many register rows share each complex key, per province —
    # a key only means something when two or more buildings carry it.
    ckeys = {}
    for e in doc.get("buildings") or []:
        ck = complex_key(e.get("name"))
        if ck:
            ckeys[(e.get("province"), ck)] = ckeys.get((e.get("province"), ck), 0) + 1
    for e in doc.get("buildings") or []:
        name = (e.get("name") or "").strip()
        k = norm(name)
        if len(k) < 3:
            continue
        if k in exact:
            continue                       # already held; the shelf has it
        # Near-miss: a name that CONTAINS or is contained by one we hold. Not
        # skipped and not merged — written down for a person.
        for kk in loose:
            # Both sides long enough AND of comparable length. Without the
            # ratio, every building with เชียงใหม่ in its name "nearly
            # matches" a record literally called เชียงใหม่, and the review
            # file fills with pairs no person needs to look at twice.
            if (len(kk) >= 6 and len(k) >= 6 and (k in kk or kk in k)
                    and min(len(k), len(kk)) >= 0.6 * max(len(k), len(kk))):
                review.append((name, loose[kk].get("name") or "", loose[kk]["id"],
                               e.get("province")))
                break
        prov = e.get("province")
        rid = slug(name, prov, seen_ids)
        if rid in held_ids:
            continue                       # made on an earlier run
        attrs = {"amphoe": e.get("amphoe") or "", "registerEdition": edition}
        if e.get("tambon"):
            attrs["tambon"] = e["tambon"]
        if e.get("assessed_low"):
            # A spread, never one welded number, and named so no renderer can
            # mistake it for a rent or an asking price.
            attrs["assessedLow"] = e["assessed_low"]
            attrs["assessedHigh"] = e["assessed_high"]
            attrs["assessedUnit"] = "baht/m2"
            attrs["assessedNote"] = ("ราคาประเมินกรมธนารักษ์ ใช้คิดค่าธรรมเนียมการโอน "
                                     "ไม่ใช่ราคาตลาด / Treasury assessed value, the "
                                     "basis for transfer fees — not a market price")
        if e.get("uses"):
            attrs["registerUses"] = e["uses"][:4]
        ck = complex_key(name)
        if ck and ckeys.get((prov, ck), 0) >= 2:
            attrs["complex"] = ck
        addr = " ".join(x for x in (
            ("ตำบล" + e["tambon"]) if e.get("tambon") else "",
            ("อำเภอ" + e["amphoe"]) if e.get("amphoe") else "",
            "จังหวัดเชียงใหม่" if prov == "cm" else "จังหวัดเชียงราย") if x)
        out.append({
            "id": rid,
            "province": prov,
            "cat": ["realestate"], "sub": ["condo"],
            "name": name, "nameTh": name, "nameEn": None,
            "lat": None, "lng": None,
            # No coordinate in the register at all — see the docstring. This
            # is the same state the 943 register temples arrived in.
            "geoPrecision": "needs-pin",
            "address": addr or None,
            "phone": None, "website": None, "hours": None,
            "attrs": attrs,
            "featured": False, "landmark": False,
            "sources": [{
                "type": "register",
                "ref": src.get("dataset_url") or "https://data.go.th/dataset/condominium-valuation",
                "fetched": doc.get("generated") or "",
                "via": "data.go.th",
                "licence": src.get("licence") or "",
                "credit": src.get("publisher") or "กรมธนารักษ์",
                "edition": edition,
            }],
            "confidence": "register",
            "updatedAt": doc.get("generated") or "",
        })
    # WO-56: the loanword tier. Register rows get their would-be id so rows a
    # person already settled in merges.json stay out of the list.
    seen_for_ids = set()
    rows = []
    for e in doc.get("buildings") or []:
        nm = (e.get("name") or "").strip()
        if len(norm(nm)) < 3:
            continue
        rows.append({**e, "_id": slug(nm, e.get("province"), seen_for_ids)})
    loan = loanword_candidates(rows, existing_records, settled_register_ids())
    return out, review, loan


def apply(records, prov):
    """(stamped, unmapped) for one province — the import_opec.apply contract.

    Runs on the MERGED list so it sees everything the catalogue holds before
    deciding a building is missing. `stamped` counts records already held that
    the register also names: those gain the Treasury's assessed spread and its
    edition, because the register IS the authority on its own valuation, and
    they keep every other field they had.
    """
    new, review, loan = fold(records)
    write_review([r for r in review if r[3] == prov],
                 [r for r in loan if r[4] == prov], prov)
    if not REG.exists():
        return 0, []
    doc = json.loads(REG.read_text())
    src = doc.get("source") or {}
    edition = src.get("edition") or doc.get("generated") or ""
    byname = {}
    ckeys = {}
    for e in doc.get("buildings") or []:
        if e.get("province") == prov:
            k = norm(e.get("name"))
            if len(k) >= 4:
                byname.setdefault(k, e)
            ck = complex_key(e.get("name"))
            if ck:
                ckeys[ck] = ckeys.get(ck, 0) + 1
    stamped = 0
    for r in records:
        if r.get("province") != prov:
            continue
        e = None
        for nm in (r.get("name"), r.get("nameTh"), r.get("nameEn")):
            e = byname.get(norm(nm))
            if e:
                break
        if not e or not e.get("assessed_low"):
            continue
        a = r.setdefault("attrs", {})
        a["assessedLow"] = e["assessed_low"]
        a["assessedHigh"] = e["assessed_high"]
        a["assessedUnit"] = "baht/m2"
        a["assessedNote"] = ("ราคาประเมินกรมธนารักษ์ ใช้คิดค่าธรรมเนียมการโอน "
                             "ไม่ใช่ราคาตลาด / Treasury assessed value, the basis "
                             "for transfer fees — not a market price")
        a["registerEdition"] = edition
        ck = complex_key(e.get("name"))
        if ck and ckeys.get(ck, 0) >= 2:
            a["complex"] = ck
        r.setdefault("sources", []).append({
            "type": "register",
            "ref": src.get("dataset_url") or "https://data.go.th/dataset/condominium-valuation",
            "fetched": doc.get("generated") or "", "via": "data.go.th",
            "licence": src.get("licence") or "", "edition": edition,
        })
        stamped += 1
    return stamped, [r for r in new if r["province"] == prov]


def write_review(review, loan=(), prov=None):
    by_prov = {}
    for name, held, hid, pv in review:
        by_prov.setdefault(pv, []).append((name, held, hid))
    if prov and prov not in by_prov:
        by_prov[prov] = []
    for pv, rows in by_prov.items():
        p = ROOT / "cache" / f"condo_register_review_{pv}.txt"
        p.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            f"# {pv}: {len(rows)} register building(s) whose name NEARLY matches a",
            "# record already held. NOT merged and NOT skipped — both were created,",
            "# because a loose join once put นครพิงค์คอนโดมิเนียม onto เพชรนครพิงค์,",
            "# a different building. If a pair here is genuinely one building, settle",
            "# it in data/curated/merges.json, which is human-confirmed by design.",
            "#",
        ]
        for name, held, hid in sorted(rows):
            lines.append(f"{name}\n    ~ held: {held}  [{hid}]")
        lrows = [r for r in loan if r[4] == pv]
        lines += [
            "",
            f"# ---- WO-56: {len(lrows)} loanword candidate(s). The register's Thai spelling of",
            "# a Latin name, read by RTGS, whose brand consonants match a mapped building's",
            "# Latin name (ปันนา → Panna → pnn = Punna). Same rule as above: nothing here",
            "# is merged by the machine. Settle a true pair in data/curated/merges.json",
            "# as {\"<map id>\": [\"<register id>\"]} — the map record keeps the pin and",
            "# the Latin name, the register row lends its Thai name, its complex and its",
            "# assessed spread, and settle_sub() files the result as condo.",
            "# `number unconfirmed`: the register names a building number the map does",
            "# not (or several rows meet one footprint) — a person or a resident decides.",
            "#",
        ]
        for name, reading, held, hid, _, flag in sorted(lrows):
            lines.append(f"{name}  (reads: {reading})\n    ≈ {held}  [{hid}]  {flag}")
        p.write_text("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    recs = []
    for f in ("cm.json", "cr.json"):
        p = ROOT / "data" / "canonical" / f
        if p.exists():
            recs += json.loads(p.read_text())
    new, review, loan = fold(recs)
    print(f"  condo register: {len(new)} building(s) not held "
          f"(cm {sum(1 for r in new if r['province']=='cm')}, "
          f"cr {sum(1 for r in new if r['province']=='cr')}), "
          f"{len(review)} near-miss(es) and {len(loan)} loanword candidate(s) for a person")
    for name, reading, held, hid, pv, flag in loan:
        print(f"      {pv} {name[:30]:32} ≈ {held[:28]:30} {flag}")
    for r in new[:6]:
        a_ = r["attrs"]
        print(f"      {r['name'][:34]:36} {a_.get('amphoe','')[:14]:16} "
              f"{a_.get('assessedLow','—')}–{a_.get('assessedHigh','—')} B/m²")
    if a.dry_run:
        print("  --dry-run: nothing written")
        return
    for pv in ("cm", "cr"):
        write_review([r for r in review if r[3] == pv],
                     [r for r in loan if r[4] == pv], pv)


if __name__ == "__main__":
    main()
