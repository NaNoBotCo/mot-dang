#!/usr/bin/env python3
"""Turn the weed.th harvest into records, with the pin's uncertainty attached.

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
   a review file for a person — when the record it resembles could itself be a
   cannabis shop. A dispensary called "Medileaves - Old City" resembling a Thai
   restaurant called "The Old City" is not a question about a duplicate; it is
   a shop that shares two words with a restaurant, and it sat in the review
   file for two days on that alone, with 74 others (2026-09-23, Nan: "weed.th
   lists medileaves but it didn't make it onto motdang.net"). A directory that
   lists the same shop twice under two spellings is worse than one that lists
   it once, and a directory that lists a shop nowhere is worse than both.
   The person's two verdicts on the review file:
     same shop  -> data/curated/merges.json  (import_all folds the pair)
     different  -> data/curated/weedth_distinct.json  (lands on the next run)

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
DISTINCT = os.path.join(ROOT, "data", "curated", "weedth_distinct.json")

# What a cannabis shop tends to put on its own sign. A record on another shelf
# whose name carries one of these might be the same door under OSM's one
# primary tag (Green Ganesha is shelved `community`, Greenhead Clinic
# `medical`), so a near-match against it stays a question. A record with none
# of these, on none of the cannabis shelves, is a restaurant, a hotel or a
# post office that happens to share a phrase — not a question. The list errs
# long on purpose: a false hit parks a shop for a person, a miss prints a
# duplicate.
TRADE_WORDS = ("cannabis", "weed", "ganja", "marijuana", "กัญชา", "กัญชง",
               "กัญ", "cbd", "cbg", "hemp", "kratom", "กระท่อม", "dispensary",
               "420", "grow", "bud", "haze", "high", "herb", "สมุนไพร", "smoke",
               "roll", "green", "club", "relax", "flower", "chill", "og")

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


def could_be_cannabis(rec):
    """Could this record, held from elsewhere, be a cannabis shop?

    Yes if it stands on the cannabis shelf, or its own name carries a word of
    the trade (TRADE_WORDS). Otherwise no — and then a weed.th shop sharing a
    phrase with it is a new shop, not a possible duplicate.
    """
    if "cannabis" in (rec.get("cat") or []):
        return True
    low = (rec.get("name") or "").lower()
    return any(w in low for w in TRADE_WORDS)


def near_matches(key, prov, have):
    """Normalised names in `have` (same province) that this key partly matches.

    A near-match means one name's WORDS are all present in the other's, with
    at least two words or one long one to carry it — and the other record
    could be a cannabis shop (could_be_cannabis). Pure, so tests can feed it
    a hand-made `have`.
    """
    ktok = set(key.split())
    near = []
    if not ktok:
        return near
    for (p, k), rec in have.items():
        if p != prov or not k:
            continue
        otok = set(k.split())
        small, big = (ktok, otok) if len(ktok) <= len(otok) else (otok, ktok)
        if not small <= big:
            continue
        if not (len(small) >= 2 or (len(small) == 1 and len(next(iter(small))) >= 8)):
            continue
        if not could_be_cannabis(rec):
            continue
        near.append(k)
    return near


def distinct():
    """weed.th uuids a person has said are NOT the record they resemble."""
    if not os.path.exists(DISTINCT):
        return set()
    doc = json.load(open(DISTINCT, encoding="utf-8")) or {}
    return set((doc.get("distinct") or {}).keys())


def records(report=False):
    if not os.path.exists(SRC):
        print(f"no {SRC} yet — run importers/harvest_weedth.py first")
        return []
    doc = json.load(open(SRC, encoding="utf-8"))
    gaz = Gazetteer()
    have = existing()
    settled = distinct()
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
        # means one name's WORDS are all present in the other's, with at
        # least two words or one long one to carry it, AND the other record
        # could be a cannabis shop — matching against every shelf parked 75
        # of 89 shops beside restaurants and hotels (near_matches). A person's
        # "different" verdict in weedth_distinct.json ends the question.
        near = [] if uuid in settled else near_matches(key, prov, have)
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
            # rehosted, and not published as schema.org `image` — that would tell
            # a crawler this shop's photograph is ours.
            attrs["photoRefExternal"] = e["photoRef"]

        # WHAT THE SHOP CALLS ITSELF, ON TOP OF THE SHELF THE SOURCE IMPLIES.
        # Every weed.th row came in as `dispensary` because that is what the
        # directory lists, and two children of the cannabis shelf sat at zero
        # for it: farm and clinic. Their KNOWN_EMPTY reasons were both written
        # about OpenStreetMap — "OSM maps a grow as landuse=farmland with no
        # crop", "a คลินิกกัญชา carries amenity=clinic and nothing that says
        # cannabis" — and both were true of OSM and false of this source,
        # which arrived afterwards. 24 rows say farm on their own sign and 5
        # say clinic. A KNOWN_EMPTY reason has to be re-read against every
        # source that lands after it was written; that is how these two rotted.
        # The dispensary sub is KEPT: a farm with a counter is both, and the
        # directory's claim is not withdrawn by the shop's own name.
        low = name.lower()
        sub = ["dispensary"]
        if any(w in low for w in ("cannabis farm", "weed farm", "ฟาร์มกัญชา",
                                  "กัญชาฟาร์ม", "cannabis-farm", "grow farm")):
            sub.append("farm")
        if any(w in low for w in ("cannabis clinic", "คลินิกกัญชา",
                                  "กัญชาทางการแพทย์", "medical cannabis",
                                  "medical clinic", "เวชกรรมกัญชา")):
            sub.append("clinic")
        # Kratom, on the same terms, and it was the third one missing. The
        # kratom shelf held two records in both provinces on 2026-09-21 while
        # nine shops in THIS source put ใบกระท่อม or Kratom on their own sign
        # and reached the reader as "dispensary" alone.
        #
        # WHY THE NAME IS SAFE TO READ HERE AND ALMOST NOWHERE ELSE. กระท่อม is
        # two words: the leaf, and a hut. Overpass, 2026-09-21: 37 elements in
        # the two provinces carry it in the name and 35 are farm shelters —
        # a hut in a longan orchard, a hut at the bus stop. Read the name on
        # the open corpus and the shelf fills with cottages. Every row here
        # already arrived as cat=["cannabis"] from a cannabis directory, so
        # the shelf calibrates the word, which is the same guard
        # tags_mine.earn_by_name() uses.
        if any(w in low for w in ("kratom", "krathom", "กระท่อม", "น้ำท่อม")):
            sub.append("kratom")

        # WHAT A VISITOR SAID THEY BOUGHT (Nan, 2026-09-21: "if the reviews
        # mention kratom, please add it"). harvest_weedth.offers_from_reviews()
        # carries product keys and a mention count; no review text, author,
        # date or rating exists on this side to leak.
        #
        # This states an OFFER, never the shelf. `sub` is what a place IS and
        # the shop's own sign is what says that; a customer writing "they have
        # kratom too" is evidence of what is on sale, which is exactly the
        # split attrs.offers was built for. So a shop that already earned the
        # kratom sub from its own name takes no offer row — it would print the
        # same word twice, once on weaker evidence.
        for k, n in sorted((e.get("offers") or {}).items()):
            if k in sub or not n:
                continue
            attrs.setdefault("offers", []).append(
                {"k": k, "via": "visitor-review", "seen": e.get("fetched")})
        out.append({
            "id": f"{prov}-weedth-{uuid.split('-')[0]}",
            "province": prov, "cat": ["cannabis"], "sub": sorted(sub),
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
        "#   different  -> add its uuid to data/curated/weedth_distinct.json;",
        "#                 it lands on the next run",
        "",
    ]
    for name, prov, match, addr, src in sorted(review):
        lines.append(f"{prov}\t{name}\n\tlooks like: {match}\n\t{addr}\n\t{src}")
    open(REVIEW, "w", encoding="utf-8").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    records(report="--report" in sys.argv)
