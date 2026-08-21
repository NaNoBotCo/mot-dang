#!/usr/bin/env python3
"""Turn the weed.th harvest into records, with the pin's honesty attached.

Reads data/curated/weedth.json (names and addresses — see harvest_weedth.py for
what is deliberately NOT in there, and why reviews never will be) and
geocode_local.py for a point. Emits records in this catalogue's own shape.

THREE RULES THIS FOLLOWS, none of them mine:

1. NO AUTOMATIC DEDUPE. import_all folds duplicates only from
   data/curated/merges.json, "human-confirmed pairs only". So a weed.th shop
   whose normalised name exactly matches a cannabis record we already hold in
   that province is NOT added and NOT merged — it is recorded as corroboration,
   because the shop we already have came from OpenStreetMap with a surveyed pin
   and that is the better record. Anything short of an exact name match goes to
   a review file for a person. A directory that lists the same shop twice under
   two spellings is worse than one that lists it once.

2. A PIN CARRIES ITS PRECISION. geocode_local returns street-level or
   tambon-level points with a stated uncertainty, never a surveyed pin. Those
   land as geoPrecision "approx" (build.py already prints "(โดยประมาณ) ·
   (approximate)" and opens the place map to a 1,200 m frame for it). A shop we
   could not place at all gets "needs-pin" and no coordinates — it is still a
   real shop with a real address, and the map is simply not the thing that
   knows where it is.

3. PROVENANCE TRAVELS. Every record says it came from weed.th, on what date,
   at what URL, and every inferred pin says which road or tambon put it there
   and how far out it might be.

    python3 importers/import_weedth.py --report     # what would land, writes nothing
"""
import collections
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geocode_local import Gazetteer, _haversine          # noqa: E402

SRC = os.path.join(ROOT, "data", "curated", "weedth.json")
REVIEW = os.path.join(ROOT, "cache", "weedth_review.txt")

# Words that say "cannabis shop" rather than which shop, so that
# "Cannabee" and "Cannabee Cannabis Shop Chiang Mai" fold to one key.
NOISE = {"cannabis", "weed", "shop", "store", "dispensary", "dispensaries",
         "cnx", "chiangmai", "chiang", "mai", "rai", "thailand", "the", "and",
         "by", "co", "ltd", "420", "ร้าน", "กัญชา", "เชียงใหม่", "เชียงราย"}


def norm_name(s):
    s = (s or "").lower()
    s = re.sub(r"[^\w฀-๿]+", " ", s)
    return " ".join(w for w in s.split() if w not in NOISE).strip()


def existing():
    """(province, normalised name) -> the record we already hold FROM ELSEWHERE.

    NOT OUR OWN OUTPUT. import_all rebuilds data/canonical from its importers
    every run, and this reads that same file to decide what is already known —
    so on the second run every shop matched the copy of itself written on the
    first, all 660 were skipped as duplicates, and the rebuild would have
    dropped the entire shelf while reporting "688 already held". The check has
    to ask what OTHER sources know, which is what it was always meant to mean.
    """
    out = {}
    for prov in ("cm", "cr"):
        f = os.path.join(ROOT, "data", "canonical", f"{prov}.json")
        if not os.path.exists(f):
            continue
        for r in json.load(open(f, encoding="utf-8")):
            if any((s or {}).get("via") == "weed.th" for s in (r.get("sources") or [])):
                continue
            k = norm_name(r.get("name"))
            if k:
                out.setdefault((prov, k), r)
    return out


def records(report=False):
    if not os.path.exists(SRC):
        print(f"no {SRC} yet — run importers/harvest_weedth.py first")
        return []
    doc = json.load(open(SRC, encoding="utf-8"))
    gaz = Gazetteer()
    have = existing()
    out, review = [], []
    # Counted by whatever tiers geocode_local offers, not a hand-typed list —
    # adding the landmark and postcode tiers made this KeyError, which is a
    # silly way to lose a run.
    stats = collections.Counter()

    for uuid, e in sorted(doc.items()):
        if uuid.startswith("_"):
            continue
        name, prov = e.get("name"), e.get("province")
        if not name or prov not in ("cm", "cr"):
            continue
        key = norm_name(name)
        if not key:
            continue

        # Rule 1: an exact name match is the shop we already have.
        if (prov, key) in have:
            stats["corroborated"] += 1
            continue
        # A partial match is a question, not an answer — but only if it is
        # actually a question. Substring matching on these keys sent 92 of 218
        # shops to review, because stripping the trade words leaves stubs like
        # "high" that appear inside half the names on the shelf, and a review
        # file nobody can finish is a review file nobody opens. A near-match
        # now means one name's WORDS are all present in the other's, with at
        # least two words or one long one to carry it.
        ktok = set(key.split())
        near = []
        if ktok:
            for (p, k) in have:
                if p != prov or not k:
                    continue
                otok = set(k.split())
                small, big = (ktok, otok) if len(ktok) <= len(otok) else (otok, ktok)
                if not small <= big:
                    continue
                if len(small) >= 2 or (len(small) == 1 and len(next(iter(small))) >= 8):
                    near.append(k)
        if near:
            stats["near"] += 1
            review.append((name, prov, near[0], e.get("address") or "", e["src"]))
            continue

        loc = gaz.locate(e.get("address"), prov) if e.get("address") else None
        attrs = {}
        if loc:
            stats[loc["precision"]] += 1
            attrs["pinVia"] = loc["via"]
            attrs["pinUncertaintyM"] = loc["uncertainty_m"]
            if loc.get("matched"):
                attrs["pinFrom"] = loc["matched"]
            if loc.get("street_slug"):
                attrs["pinStreet"] = loc["street_slug"]
        else:
            stats["needs-pin"] += 1
        if e.get("photoRef"):
            # A pointer at their picture on their CDN. Never downloaded, never
            # rehosted, never published as schema.org `image` — that would tell
            # a crawler this shop's photograph is ours.
            attrs["photoRefExternal"] = e["photoRef"]

        out.append({
            "id": f"{prov}-weedth-{uuid.split('-')[0]}",
            "province": prov, "cat": ["cannabis"], "sub": ["dispensary"],
            "name": name, "nameTh": None, "nameEn": None,
            "lat": loc["lat"] if loc else None,
            "lng": loc["lng"] if loc else None,
            "geoPrecision": "approx" if loc else "needs-pin",
            "address": e.get("address"), "phone": None, "website": None,
            "hours": None, "attrs": attrs,
            "featured": False, "landmark": False,
            "sources": [{"type": "directory", "ref": e["src"],
                         "fetched": e.get("fetched", ""), "via": "weed.th"}],
            "confidence": "third-party", "updatedAt": e.get("fetched", ""),
        })
        stats["new"] += 1

    _write_review(review)
    print(f"weed.th -> {stats['new']} new record(s); "
          f"{stats['corroborated']} already held (exact name match, not added); "
          f"{stats['near']} near-matches sent to review")
    tiers = ", ".join(f"{k} {stats[k]}" for k in
                      ("landmark", "street", "postcode", "tambon", "needs-pin")
                      if stats[k])
    print(f"   pins: {tiers}")
    if report:
        for r in out[:15]:
            a = r["attrs"]
            pin = (f"{r['lat']},{r['lng']} ±{a.get('pinUncertaintyM')}m "
                   f"via {a.get('pinFrom')}") if r["lat"] else "no pin"
            print(f"   {r['province']}  {r['name'][:34]:34} {pin}")
    return out


def _write_review(review):
    os.makedirs(os.path.dirname(REVIEW), exist_ok=True)
    lines = [
        f"# {len(review)} weed.th shops whose name PARTLY matches one we already",
        "# hold. Partly is not the same as does — 'Green Land' and 'Green Land",
        "# CNX' may be one shop or two doors apart. Nothing is merged and nothing",
        "# is added until a person says which.",
        "#   same shop  -> add the pair to data/curated/merges.json",
        "#   different  -> nothing to do; it will be added on the next run once",
        "#                 its name is distinct, or leave it out deliberately",
        "",
    ]
    for name, prov, match, addr, src in sorted(review):
        lines.append(f"{prov}\t{name}\n\tlooks like: {match}\n\t{addr}\n\t{src}")
    open(REVIEW, "w", encoding="utf-8").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    records(report="--report" in sys.argv)
