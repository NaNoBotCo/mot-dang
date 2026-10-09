#!/usr/bin/env python3
"""WO-56 — the physiotherapy shelf, filled from the directory's own words.

The measurement (WO-55, 2026-09-04): the medical tree's `physio` child
(facilityType=physio) matched NOTHING — OSM holds no
healthcare=physiotherapist in either province, Mae Ping PT is a curated
clinic, the Doi Saket physio node is amenity=doctors — so the shelf was
hidden and /longcare.html linked a page never built. CMHY.city files the
city's physiotherapy clinics under "other health services" (category 53)
beside hearing-aid centres, nursing homes and wellness shops; this reads
that category (importers/cmhy.py physio) and sorts by what each shop wrote
on itself.

Reads, zero network:  cache/cmhy/physio/places.json · data/canonical/cm.json
Writes:  data/curated/physio.json (the register: every row kept, the picks,
         the refusals, the OSM matches) · additions-chiang-mai.json

TRADE, FROM THE SHOP'S OWN WORDS. A row is physio when its name or its
tags say กายภาพบำบัด / physio / physical therapy. A row that says
เครื่องช่วยฟัง is the hearing register's (WO-58) and is written down here
as such, not filed as physio. Nursing homes (เนอร์สซิ่งโฮม, ดูแลผู้สูงอายุ)
are WO-32's and refused here; wellness / cordyceps / hair shops refused.
A hospital's own physio department is not a shop and is refused — the
care register carries it under its hospital.

facilityType=physio is set on every pick so the shelf child matches;
specialty.py reads กายภาพบำบัด off the name for the "Treats" line.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cmhy  # noqa: E402
import cmhy_records as cr  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TODAY = "2026-09-04"
JOB = "physio"

PHYSIO = ("กายภาพบำบัด", "กายภาพ", "physio", "physical therap", "รีแฮบ", "rehab")
HEARING = ("เครื่องช่วยฟัง", "การได้ยิน", "hearing")
NURSING = ("เนอร์สซิ่งโฮม", "เนอสซิ่งโฮม", "เนิร์สซิ่งโฮม", "ดูแลผู้สูงอายุ", "nursing home", "บ้านพัก")
HOSPITAL = ("โรงพยาบาล", "ศูนย์ตรวจสุขภาพ")
OT_ONLY = ("โอที", "กิจกรรมบำบัด")


def trade_of(row):
    o = cr.own(row)
    if cr.has(o, HOSPITAL):
        return None, "a hospital department — the care register's, under its hospital"
    if cr.has(o, NURSING):
        return None, "a nursing home — WO-32's shelf, not a physio clinic"
    if cr.has(o, HEARING) and not cr.has(o, PHYSIO):
        return "hearing", ""
    if cr.has(o, PHYSIO):
        return "physio", ""
    if cr.has(o, OT_ONLY):
        return None, "occupational therapy — WO-55's register carries it"
    return None, "no physio word in its own name or tags"


def main():
    rows = cmhy.rows_of(JOB)
    if not rows:
        raise SystemExit("run: python3 importers/cmhy.py physio")
    canon = cr.canonical("cm")
    # SAME DOOR MEANS SAME TRADE. The first run matched a physio clinic to a
    # dental clinic 68 m away and to a skin clinic 4 m away and refused to
    # write it; a neighbour is not a duplicate. Only a canonical record that
    # itself says physio (specialty or name) can claim a directory row.
    def says_physio(r):
        spec = (r.get("attrs") or {}).get("specialty") or []
        nm = " ".join(str(r.get(k) or "") for k in ("name", "nameTh", "nameEn")).lower()
        return "physio" in spec or "ot" in spec or cr.has(nm, PHYSIO) or cr.has(nm, OT_ONLY)
    medical = [r for r in canon if "medical" in (r.get("cat") or []) and says_physio(r)]
    register, picks, hearing, refused, matched = [], [], [], [], []
    records = []
    for row in rows:
        trade, why = trade_of(row)
        entry = {"cmhy": row["id"], "name": row["name"], "tags": row["tags"],
                 "phone": row["phone"], "lat": row["lat"], "lng": row["lng"],
                 "amphoe": row["amphoe"], "modified": (row["modified"] or "")[:10],
                 "trade": trade}
        if trade is None:
            entry["refused"] = why
            refused.append(entry); register.append(entry)
            continue
        if trade == "hearing":
            hearing.append(entry); register.append(entry)
            continue
        near = None
        if row["lat"]:
            near, d = cr.near(float(row["lat"]), float(row["lng"]), medical)
        if near is not None:
            entry["osm"] = near["id"]
            entry["osm_name"] = near.get("name")
            entry["metres"] = round(d)
            matched.append(entry); register.append(entry)
            continue
        if not row["lat"] and not (row.get("street") or row.get("amphoe")):
            entry["refused"] = "no published GPS and no address to stand on"
            refused.append(entry); register.append(entry)
            continue
        rid = f"cm-curated-physio-{row['id']}"
        entry["record"] = rid
        picks.append(entry); register.append(entry)
        records.append(cr.record(
            row, rid, "medical", "clinic", "physiotherapy clinic", TODAY, JOB,
            facility="physio",
            blurb_en=f"Physiotherapy clinic in {row.get('amphoe') or 'Chiang Mai'}, read off the cmhy.city directory; ring before going."))
    n_new, n_touched = cr.upsert(records, "cm")
    out = {
        "_readme": [
            "WO-56 — the physiotherapy register behind the physio shelf (medical/physio).",
            "Every cmhy.city row from category 53 is kept (the denominator); `trade` says what",
            "the shop's own name/tags state; `refused` says why a row was not written;",
            "`osm` names the canonical record within 80 m that already IS this door.",
            "Hearing-aid rows are listed under `hearing` for WO-58, not filed as physio.",
            "Records carry facilityType=physio, hours from the directory (_hoursSource),",
            "directory-published GPS, and the directory's dateModified as sourceUpdated.",
        ],
        "_built": TODAY,
        "counts": {"cmhy_rows": len(rows), "physio_records": len(picks), "hearing_rows": len(hearing),
                   "matched_to_catalogue": len(matched), "refused": len(refused),
                   "written_new": n_new, "touched": n_touched},
        "corpus": register,
    }
    (ROOT / "data" / "curated" / "physio.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(rows)} rows → {len(picks)} physio records ({n_new} new), {len(hearing)} hearing rows, "
          f"{len(matched)} already in the catalogue, {len(refused)} refused")
    for e in matched:
        print(f"   matched: {e['name']} ↔ {e['osm_name']} ({e['osm']}, {e['metres']} m)")
    for e in refused[:20]:
        print(f"   refused: {e['name']} — {e['refused']}")


if __name__ == "__main__":
    main()
