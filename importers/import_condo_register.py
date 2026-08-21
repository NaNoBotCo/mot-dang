#!/usr/bin/env python3
"""Fold the Treasury's condominium register into records. WO-27, door 6b.

The register (data/curated/condo_register.json, harvested by
importers/harvest_condo_register.py) names 385 registered อาคารชุด in the two
provinces. The catalogue holds 53 buildings whose own name says condominium,
because that is all OpenStreetMap knows. This closes the gap the way the ONAB
temple register closed the wat one: the official list becomes records, each
carrying its register lineage, and each honest about what it does not have.

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

    python3 importers/import_condo_register.py --dry-run
    python3 importers/import_condo_register.py            # (called by import_all)
"""
import argparse
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "data" / "curated" / "condo_register.json"


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
    """(new_records, review_rows). Never mutates what it is given."""
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
            # is the same honest state the 943 register temples arrived in.
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
    return out, review


def apply(records, prov):
    """(stamped, unmapped) for one province — the import_opec.apply contract.

    Runs on the MERGED list so it sees everything the catalogue holds before
    deciding a building is missing. `stamped` counts records already held that
    the register also names: those gain the Treasury's assessed spread and its
    edition, because the register IS the authority on its own valuation, and
    they keep every other field they had.
    """
    new, review = fold(records)
    write_review([r for r in review if r[3] == prov])
    if not REG.exists():
        return 0, []
    doc = json.loads(REG.read_text())
    src = doc.get("source") or {}
    edition = src.get("edition") or doc.get("generated") or ""
    byname = {}
    for e in doc.get("buildings") or []:
        if e.get("province") == prov:
            k = norm(e.get("name"))
            if len(k) >= 4:
                byname.setdefault(k, e)
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
        r.setdefault("sources", []).append({
            "type": "register",
            "ref": src.get("dataset_url") or "https://data.go.th/dataset/condominium-valuation",
            "fetched": doc.get("generated") or "", "via": "data.go.th",
            "licence": src.get("licence") or "", "edition": edition,
        })
        stamped += 1
    return stamped, [r for r in new if r["province"] == prov]


def write_review(review):
    by_prov = {}
    for name, held, hid, prov in review:
        by_prov.setdefault(prov, []).append((name, held, hid))
    for prov, rows in by_prov.items():
        p = ROOT / "cache" / f"condo_register_review_{prov}.txt"
        p.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            f"# {prov}: {len(rows)} register building(s) whose name NEARLY matches a",
            "# record already held. NOT merged and NOT skipped — both were created,",
            "# because a loose join once put นครพิงค์คอนโดมิเนียม onto เพชรนครพิงค์,",
            "# a different building. If a pair here is genuinely one building, settle",
            "# it in data/curated/merges.json, which is human-confirmed by design.",
            "#",
        ]
        for name, held, hid in sorted(rows):
            lines.append(f"{name}\n    ~ held: {held}  [{hid}]")
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
    new, review = fold(recs)
    print(f"  condo register: {len(new)} building(s) not held "
          f"(cm {sum(1 for r in new if r['province']=='cm')}, "
          f"cr {sum(1 for r in new if r['province']=='cr')}), "
          f"{len(review)} near-miss(es) for a person")
    for r in new[:6]:
        a_ = r["attrs"]
        print(f"      {r['name'][:34]:36} {a_.get('amphoe','')[:14]:16} "
              f"{a_.get('assessedLow','—')}–{a_.get('assessedHigh','—')} B/m²")
    if a.dry_run:
        print("  --dry-run: nothing written")
        return
    write_review(review)


if __name__ == "__main__":
    main()
