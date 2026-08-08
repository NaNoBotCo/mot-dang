#!/usr/bin/env python3
"""Fold the existing corpora into Mot Dang canonical records. Zero network.

Sources (all sibling repos under ~/Developer/claude code projects/):
  thai-answers/catalog.db                          316 massage venues   -> cm/massage
  cm-womens-health/data/crawled/osm-health.json    258 health places    -> cm/medical (+essentials for pharmacies)
  mueang-map/data/canonical/osm.json               378 CM lens points   -> cm/wat, cm/food, cm/sights
  mueang-map/data/canonical/osm-chiang-rai.json    289 CR wats          -> cr/wat  (wireframe seed)
  data/curated/featured-chiang-rai.json            hand-entered field truth (never overwritten)
  data/curated/additions-chiang-mai.json           CM places no crawl carries, each with dated sources
  data/curated/names.json                          names a crawl left empty, each with its source
  data/curated/story_hooks.json                    one line of history per marquee place, each with its source
  data/curated/shelves.json                        extra cat/sub for places OSM's one primary tag hid
  data/curated/merges.json                         duplicate records folded, human-confirmed pairs only

Output: data/canonical/cm.json, data/canonical/cr.json
Curated/field records always win over crawled ones with the same source ref.
"""
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT.parent

LENS_TO_CAT = {
    "wat": ["wat"],
    "spirit-house": ["wat"],
    "pad-krapow": ["food"],
    "tattoo": ["sights"],
    "library": ["sights"],
    "art-studio": ["sights"],
    "views": ["sights"],
}


def rec(id, province, cat, name, name_th=None, name_en=None, lat=None, lng=None,
        precision="exact", address=None, phone=None, website=None, hours=None,
        attrs=None, sources=None, confidence="crawled"):
    return {
        "id": id, "province": province, "cat": cat,
        "name": name, "nameTh": name_th, "nameEn": name_en,
        "lat": lat, "lng": lng, "geoPrecision": precision,
        "address": address, "phone": phone, "website": website, "hours": hours,
        "attrs": attrs or {}, "featured": False, "landmark": False,
        "sources": sources or [], "confidence": confidence,
        "updatedAt": "2026-07-27",
    }


def import_thai_answers():
    db = PROJECTS / "thai-answers" / "catalog.db"
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    out = []
    for r in con.execute("select * from venues"):
        ref = f"{r['osm_type']}/{r['osm_id']}"
        name = r["name"] or r["name_en"]
        if not name:  # a directory has no shelf for the nameless; a named re-crawl restores them
            continue
        out.append(rec(
            id=f"cm-osm-{r['osm_type']}-{r['osm_id']}", province="cm", cat=["massage"],
            name=name, name_en=r["name_en"], lat=r["lat"], lng=r["lon"],
            phone=r["phone"], website=r["website"], hours=r["opening_hours"],
            attrs={"inOldCity": bool(r["in_old_city"])},
            sources=[{"type": "osm", "ref": ref, "fetched": (r["fetched_at"] or "")[:10],
                      "via": "thai-answers"}],
        ))
    con.close()
    return out


def import_womens_health():
    data = json.loads((PROJECTS / "cm-womens-health" / "data" / "crawled" / "osm-health.json").read_text())
    out = []
    for r in data:
        a = r.get("attrs", {})
        ftype = a.get("facilityType") or "clinic"
        cat = ["essentials"] if ftype == "pharmacy" else ["medical"]
        src = (r.get("sources") or [{}])[0]
        ref = src.get("ref", f"cmwh/{r['id']}")
        if not (r.get("nameTh") or r.get("name") or r.get("nameEn")):
            continue
        out.append(rec(
            id="cm-osm-" + ref.replace("/", "-"), province="cm", cat=cat,
            name=r.get("nameTh") or r.get("name") or r.get("nameEn"),
            name_th=r.get("nameTh"), name_en=r.get("nameEn"),
            lat=r.get("lat"), lng=r.get("lng"), precision=r.get("geoPrecision", "exact"),
            phone=a.get("phone"), website=a.get("website"), hours=a.get("openingHours"),
            attrs={"facilityType": ftype, "obgyn": a.get("obgyn"), "operator": a.get("operator")},
            sources=[{"type": src.get("type", "osm"), "ref": ref,
                      "fetched": src.get("fetched", ""), "via": "cm-womens-health"}],
        ))
    return out


def import_mueang_map(fname, province):
    data = json.loads((PROJECTS / "mueang-map" / "data" / "canonical" / fname).read_text())
    out = []
    for r in data:
        lenses = r.get("lens", [])
        cats = sorted({c for l in lenses for c in LENS_TO_CAT.get(l, [])}) or ["sights"]
        src = (r.get("sources") or [{}])[0]
        ref = src.get("ref", f"mm/{r['id']}")
        if not (r.get("name") or r.get("nameRoman")):
            continue
        out.append(rec(
            id=f"{province}-osm-" + ref.replace("/", "-"), province=province, cat=cats,
            name=r.get("name") or r.get("nameRoman"),
            name_en=r.get("nameRoman"),
            lat=r.get("lat"), lng=r.get("lng"), precision=r.get("geoPrecision", "exact"),
            address=r.get("address"),
            attrs=dict(r.get("attrs", {}), lens=lenses),
            sources=[{"type": src.get("type", "osm"), "ref": ref,
                      "fetched": src.get("fetched", ""), "via": "mueang-map"}],
            confidence=r.get("confidence", "crawled"),
        ))
    return out


def apply_curated_shelves(records):
    """Extra shelves from data/curated/shelves.json, applied after the merge.

    OSM allows one primary tag per place, so the crawl files Hub 53 under
    hotel/guesthouse and never sees the coworking floor that is the other half
    of its name. Entries here union cat/sub onto an existing record by id and
    append their source to its provenance. They add shelves only — a curated
    shelf never removes or argues with a crawled one.
    """
    path = ROOT / "data" / "curated" / "shelves.json"
    if not path.exists():
        return 0
    fixes = (json.loads(path.read_text()) or {}).get("shelves") or {}
    by_id = {r["id"]: r for r in records}
    n = 0
    for rid, fix in fixes.items():
        r = by_id.get(rid)
        if not r:
            continue
        before = (set(r.get("cat") or []), set(r.get("sub") or []),
                  dict(r.get("attrs") or {}))
        r["cat"] = sorted(set(r.get("cat") or []) | set(fix.get("add_cat") or []))
        r["sub"] = sorted(set(r.get("sub") or []) | set(fix.get("add_sub") or []))
        # set_attrs is for shelves that match on an attr (medical/dentist and
        # essentials/pharmacy match attrs.facilityType, not sub). Curated truth
        # wins over a crawled value — same tier rule as the record merge — and
        # the appended source line says where the new value came from.
        for k, v in (fix.get("set_attrs") or {}).items():
            r.setdefault("attrs", {})[k] = v
        after = (set(r["cat"]), set(r["sub"]), dict(r.get("attrs") or {}))
        if after != before:
            r.setdefault("sources", []).append(
                {"type": "curated", "ref": fix.get("source", ""),
                 "fetched": fix.get("fetched", ""), "via": "data/curated/shelves.json"})
            n += 1
    return n


def apply_curated_merges(records):
    """Fold duplicate records from data/curated/merges.json: {keep_id: [drop_ids]}.

    The crawl can hold one venue twice — mapped as both a node and a way, or
    caught by two groups (The Social Club: one record filed hotel, one filed
    coworking). Each merge keeps keep_id's record, unions the dropped record's
    shelves and sources into it, and fills only fields keep_id lacks. Merging
    is a curated decision because near-same-name-nearby is not proof: a
    restaurant inside its hotel is two honest records, not a dupe.
    """
    path = ROOT / "data" / "curated" / "merges.json"
    if not path.exists():
        return records, 0
    merges = (json.loads(path.read_text()) or {}).get("merges") or {}
    drop_to_keep = {d: k for k, drops in merges.items() for d in drops}
    by_id = {r["id"]: r for r in records}
    n = 0
    for drop_id, keep_id in drop_to_keep.items():
        dr, kr = by_id.get(drop_id), by_id.get(keep_id)
        if not dr or not kr:
            continue
        kr["cat"] = sorted(set(kr.get("cat") or []) | set(dr.get("cat") or []))
        kr["sub"] = sorted(set(kr.get("sub") or []) | set(dr.get("sub") or []))
        for k in ("nameTh", "nameEn", "phone", "website", "hours", "address"):
            kr[k] = kr.get(k) or dr.get(k)
        kr["attrs"] = {**(dr.get("attrs") or {}), **(kr.get("attrs") or {})}
        kr["sources"] = (kr.get("sources") or []) + (dr.get("sources") or []) + [
            {"type": "curated", "ref": f"merged duplicate {drop_id}",
             "fetched": "", "via": "data/curated/merges.json"}]
        del by_id[drop_id]
        n += 1
    return sorted(by_id.values(), key=lambda r: r["id"]), n


def apply_curated_names(records):
    """Hand-filled names from data/curated/names.json, applied last.

    A crawl can leave a place with a name in one language and nothing in the
    other. On the ไหว้พระ ๙ วัด rounds that included Wat Chedi Luang, Wat
    Chiang Man and Wat Phan Tao carrying no Thai at all on a Thai-first site —
    while the Thai name sat unused in each record's own attrs.summary, the
    title of the th.wikipedia article already fetched for it.

    Only the `names` block is applied, and only over an empty field: a curated
    name fills a gap, it never argues with a crawled one. Leads live in
    `unverified` and are never rendered, for the same reason honours.json keeps
    its own — a name is the thing on the page that most has to be right.
    """
    path = ROOT / "data" / "curated" / "names.json"
    if not path.exists():
        return 0
    fixes = (json.loads(path.read_text()) or {}).get("names") or {}
    by_id = {r["id"]: r for r in records}
    n = 0
    for rid, fix in fixes.items():
        r = by_id.get(rid)
        if not r:
            continue
        for field in ("nameTh", "nameEn", "name"):
            if fix.get(field) and not r.get(field):
                r[field] = fix[field]
                r.setdefault("sources", []).append(
                    {"type": "curated", "ref": fix.get("source", ""),
                     "fetched": "", "via": "data/curated/names.json"})
                n += 1
    return n


def apply_curated_story_hooks(records):
    """Hand-written story hooks from data/curated/story_hooks.json.

    A marquee place — the Three Kings, the wat that held the city pillar —
    reaches the crawl as a bare name and a pin, when the one thing a reader
    wants from it is the line of history that makes it matter. Hooks land as
    blurb_th/blurb_en, the fields the place page and its meta description
    already render, and only over an empty field: a curated story fills a
    gap, it never argues with a blurb already on the record. Same sourcing
    rule as names.json — every hook carries a fetched URL, and a story a
    chronicle carries but primary documents do not is worded as tradition.
    """
    path = ROOT / "data" / "curated" / "story_hooks.json"
    if not path.exists():
        return 0
    fixes = (json.loads(path.read_text()) or {}).get("hooks") or {}
    by_id = {r["id"]: r for r in records}
    n = 0
    for rid, fix in fixes.items():
        r = by_id.get(rid)
        if not r:
            continue
        filled = False
        for field in ("blurb_th", "blurb_en"):
            if fix.get(field) and not r.get(field):
                r[field] = fix[field]
                filled = True
        if filled:
            r.setdefault("sources", []).append(
                {"type": "curated", "ref": fix.get("source", ""),
                 "fetched": fix.get("fetched", ""),
                 "via": "data/curated/story_hooks.json"})
            n += 1
    return n


def main():
    import import_overpass
    import import_fixtures
    cm, cr = [], []
    cm += import_thai_answers()
    cm += import_womens_health()
    cm += import_mueang_map("osm.json", "cm")
    cm += import_overpass.records("cm")
    cm += json.loads((ROOT / "data" / "curated" / "additions-chiang-mai.json").read_text())
    cr += import_mueang_map("osm-chiang-rai.json", "cr")
    cr += import_overpass.records("cr")
    cr += json.loads((ROOT / "data" / "curated" / "featured-chiang-rai.json").read_text())

    outdir = ROOT / "data" / "canonical"
    outdir.mkdir(parents=True, exist_ok=True)
    for prov, records in (("cm", cm), ("cr", cr)):
        # field/curated truth wins over crawled truth; same place from two
        # sources keeps the stronger record and unions its shelves
        tier = {"crawled": 0, "curated": 1, "field": 2}
        by_id = {}
        for r in sorted(records, key=lambda r: tier[r["confidence"]]):
            ex = by_id.get(r["id"])
            if ex:
                r["cat"] = sorted(set(ex["cat"]) | set(r["cat"]))
                r["sub"] = sorted(set(ex.get("sub", [])) | set(r.get("sub", [])))
                for k in ("phone", "website", "hours", "address"):
                    r[k] = r.get(k) or ex.get(k)
                r["attrs"] = {**ex.get("attrs", {}), **r.get("attrs", {})}
            by_id[r["id"]] = r
        final = sorted(by_id.values(), key=lambda r: r["id"])
        # Facets last, on the merged records: the ATM join needs the final
        # coordinates, and the tag lift needs whichever source ref survived.
        facets = import_fixtures.apply(final, prov)
        named = apply_curated_names(final)
        if named:
            print(f"{prov}: {named} curated name(s) filled in")
        storied = apply_curated_story_hooks(final)
        if storied:
            print(f"{prov}: {storied} curated story hook(s) filled in")
        shelved = apply_curated_shelves(final)
        if shelved:
            print(f"{prov}: {shelved} curated shelf addition(s) applied")
        final, merged = apply_curated_merges(final)
        if merged:
            print(f"{prov}: {merged} duplicate record(s) folded")
        (outdir / f"{prov}.json").write_text(
            json.dumps(final, ensure_ascii=False, indent=1), encoding="utf-8")
        got = sum(1 for r in final if (r.get("attrs") or {}).get("facets"))
        extra = (f" · {got} with facets ("
                 + ", ".join(f"{k} {v}" for k, v in sorted(facets.items())) + ")") if got else ""
        print(f"{prov}: {len(final)} records{extra}")


if __name__ == "__main__":
    main()
