#!/usr/bin/env python3
"""Air-con by Nan's word — data/curated/aircon_stated.json onto the records.

Every 7-Eleven, Central mall, Big C, Makro and Rimping, and every hotel of
three stars and up, is air-conditioned (Nan, 2026-09-28). A record one of
those kinds matches gets attrs.facets.aircon = "said", which the air-con tag,
its page and the search filter already read. A facet a record already holds
(an OSM tag, a person at the door) is left as it is.

Called by import_all.py after import_fixtures.apply. Zero network.

    python3 importers/aircon_stated.py        # counts per kind, both provinces
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATED = json.loads((ROOT / "data" / "curated" / "aircon_stated.json").read_text())
KINDS = STATED["kinds"]
PLACES = {p["id"] for p in STATED.get("places") or []}


def _starts(name, w):
    """`name` begins with `w` as a word: a Latin prefix may not run on into
    another Latin letter ("big c" is not "big coffee"); Thai has no spaces, so
    a Thai prefix only has to begin the name. Twin of toilets_layer._starts."""
    if not name.startswith(w):
        return False
    nxt = name[len(w):len(w) + 1]
    return not (nxt and w[-1].isascii() and w[-1].isalpha()
                and nxt.isascii() and nxt.isalpha())


def _stars(v):
    """Every star figure the record gives; a record saying "2,5" is 2 and 5."""
    return [float(x) for x in re.findall(r"\d+(?:\.\d+)?", str(v or ""))]


def kind_of(r):
    """The key of the first stated kind this record meets, else None. A place
    she named by itself comes first."""
    if r.get("id") in PLACES:
        return "place"
    a = r.get("attrs") or {}
    names = [str(r.get(k) or "").strip().lower() for k in ("name", "nameTh", "nameEn")]
    names = [n for n in names if n]
    brands = [str(a.get(k) or "").strip().lower() for k in ("brand", "brandEn", "brandTh")]
    brands = [b for b in brands if b]
    subs = set(r.get("sub") or [])
    for k in KINDS:
        m = k["match"]
        if m.get("sub") and not subs & set(m["sub"]):
            continue
        if m.get("sub_any") and not subs & set(m["sub_any"]):
            continue
        if m.get("not_sub") and subs & set(m["not_sub"]):
            continue
        if m.get("not_name") and any(w.lower() in n for n in names for w in m["not_name"]):
            continue
        if m.get("brand_prefix") or m.get("name_prefix"):
            by_brand = any(_starts(b, w.lower()) for b in brands for w in m.get("brand_prefix") or [])
            by_name = any(_starts(n, w.lower()) for n in names for w in m.get("name_prefix") or [])
            if not (by_brand or by_name):
                continue
        if m.get("stars_min") is not None:
            st = _stars(a.get("stars"))
            if not st or min(st) < m["stars_min"]:
                continue
        return k["key"]
    return None


def apply(records):
    """Mutates in place. Returns {kind key: records newly marked}."""
    counts = {}
    for r in records:
        key = kind_of(r)
        if not key:
            continue
        fac = r.setdefault("attrs", {}).setdefault("facets", {})
        if "aircon" in fac:
            continue
        fac["aircon"] = "said"
        counts[key] = counts.get(key, 0) + 1
    return counts


if __name__ == "__main__":
    import copy
    for prov in ("cm", "cr"):
        recs = json.loads((ROOT / "data" / "canonical" / f"{prov}.json").read_text())
        print(prov, apply(copy.deepcopy(recs)))
