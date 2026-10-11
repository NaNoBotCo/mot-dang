#!/usr/bin/env python3
"""🐜 Overture Places, folded in two ways — the second witness, and the shops nobody held.

Reads `cache/overture/cmcr.jsonl.gz` (importers/harvest_overture.py puts it
there). Stdlib only; zero network.

    A · ENRICH   a record we already hold gains the contact facts it lacks
    B · ADMIT    a place we do not hold at all becomes a record

Nan asked for both on 2026-09-07. They are one file because they share one
question — is this row the place that record already names — and answering it
twice, in two files, is how two answers start to disagree.

--------------------------------------------------------------------------
THE MATCH RULE, AND THE MEASUREMENT THAT SET IT
--------------------------------------------------------------------------
A name is not an identity. Measured over 3,072 records where our pin is
surveyed and the name matches exactly ONE Overture row in the province:

    median 32 m · 64% inside 100 m · p90 21 km · p95 134 km

The middle of that says the two datasets agree about where a shop is. The tail
says exact name equality across a province is routinely two different shops —
ร้านลาบ, a wat name repeated in four districts, a franchise. So identity here
is NAME **AND** PROXIMITY, never name alone: same normalised name (or one
containing the other, 6 characters or more) within 300 m.

--------------------------------------------------------------------------
WHAT THIS REFUSES TO DO, AND WHY IT IS WRITTEN DOWN
--------------------------------------------------------------------------
**It never moves a pin.** 595 records still have no coordinates and it is
tempting to take Overture's. Measured, under the strictest rule available —
unique name, and the point falling inside the อำเภอ our address names
(WO-73's district witness) — 555 candidates came out at median 62 m but
**p90 5,551 m**, above the ±3,000 m the repo publishes at. Confidence ≥ 0.8
tightened it to p90 3,896 m, still over. So the pin stays absent, which is a
fact, rather than becoming a guess that reads like one. 85 records could have
had a pin today; roughly a quarter of them would have been the wrong place.

**It never overwrites.** Every field is filled only where the record holds
nothing. An owner's claim, a survey, a register and a curated correction all
outrank this and all of them run later.

**It is not giveable to OpenStreetMap, which is a statement about OSM and
nothing else.** The source type is `directory`, so provenance.source_class()
returns NOT_GIVEABLE and go/osm-gate refuses it. The reason is the licence,
not the source: CDLA-Permissive 2.0 is a good licence and it is not ODbL, and
99% of these rows are Meta's, so relicensing them into OSM is not ours to do.
That is a different sentence from the one that applies to a scraped directory,
even though the gate answers both the same way. Everything here is on the site
and in the public Hugging Face export. Cost of the OSM refusal, counted on
2026-09-07 before taking it: no record in the catalogue had a giveable or
licence-waiting field, so nothing was lost.

**It refuses a near-miss rather than settling it.** 6,909 rows sat within
25 m of a record we already hold, on the same shelf, under a name the match
rule did not recognise. Sampling those pairs found both kinds: real duplicates
under two spellings (บ้านกาแฟ / "Ban Coffee", 4 m apart) and real neighbours
(a sushi bar 11 m from an MK). A loose join would merge the second kind; a
blind import would ship the first. So neither: they go to
`cache/overture_review_<prov>.txt` for a person, the same way
importers/import_opendata.py hands its near-misses over. 25 m and not 50 m
because 50 m of a Chiang Mai soi is several shops.

**It admits nothing it cannot file.** A record is only created when the
Overture category maps to a shelf in data/curated/overture_categories.json —
94% of rows do. The rest can still hand a phone number to a record we hold,
because enrichment does not need to know what a place is.
"""
import gzip
import json
import math
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache" / "overture" / "cmcr.jsonl.gz"
MANIFEST = ROOT / "cache" / "overture" / "manifest.json"
CATMAP = ROOT / "data" / "curated" / "overture_categories.json"
SHELVES = ROOT / "data" / "categories.json"

# The measurement above, as two constants. MATCH_M is where name equality stops
# being identity; MIN_CONFIDENCE is Overture's own score, below which a third
# of the file sits and none of it is worth a record.
MATCH_M = 300
MIN_CONFIDENCE = 0.5
# A name has to be long enough that containment means something. "ร้าน" inside
# "ร้านลาบลำปาง" is not a match, it is the word for shop.
MIN_CONTAIN = 6
# Same shelf, this close, different name: not settled here. See the docstring.
REVIEW_M = 25

_THAI = re.compile(r"[฀-๿]")
# An address, as opposed to a house number somebody typed into a form. Overture
# freeform runs from "1294" to a full Thai address; only the second kind helps.
_ADDRESSY = re.compile(r"ตำบล|อำเภอ|จังหวัด|ถนน|ซอย|หมู่บ้าน|ต\.|อ\.|จ\.|"
                       r"\b(road|rd|soi|moo|tambon|amphoe|district)\b|\d{5}", re.I)
_FB = re.compile(r"^https?://(?:www\.)?facebook\.com/", re.I)
_IG = re.compile(r"^https?://(?:www\.)?instagram\.com/", re.I)
_LINE = re.compile(r"^https?://(?:www\.)?(?:lin\.ee|line\.me)/", re.I)
# A link to somebody else's page ABOUT the place is not the place's website.
# 1,609 of the rows we took carried a maps.app.goo.gl share link and 538 a
# goo.gl; a reader clicking "website" expects the shop's own words, and Google
# ranks last here anyway. Shorteners go with them: a bit.ly cannot be read
# without following it, and this file follows nothing.
_NOT_A_WEBSITE = re.compile(
    r"^https?://(?:www\.)?(?:maps\.app\.goo\.gl|goo\.gl|g\.co|google\.[a-z.]+|"
    r"maps\.google\.[a-z.]+|bit\.ly|tinyurl\.com|t\.co|shorturl\.at)/", re.I)
# An email provider is not a website (Nan, 2026-10-04: "clean up the
# email-domain websites"). 75 rows held one on 2026-10-04, all from Overture:
# a bare http://hotmail.com/ or gmail.com, which says nothing, and four that
# are an address typed with a dot for the @ (nongbuatemple8120.gmail.com),
# which become the email they spell. A Live *Spaces* address is an old website,
# not mail, and stays a website.
_MAIL_HOST = re.compile(
    r"^(?:www\.)?(?:gmail\.com|googlemail\.com|hotmail\.(?:com|co\.th|co\.uk)|"
    r"outlook\.(?:com|co\.th)|live\.com|msn\.com|yahoo\.(?:com|co\.th)|ymail\.com|"
    r"icloud\.com|me\.com|aol\.com|proton\.me|protonmail\.com)$", re.I)
_MAIL_TYPED = re.compile(
    r"^(?:www\.)?([a-z0-9][a-z0-9._-]{2,63})\.(gmail\.com|hotmail\.com|hotmail\.co\.th|"
    r"yahoo\.com|outlook\.com|icloud\.com)$", re.I)


def _host(url):
    m = re.match(r"^(?:[a-z][a-z0-9+.-]*://)?([^/?#]+)", url.strip(), re.I)
    return (m.group(1).split("@")[-1].split(":")[0].lower()) if m else ""


def _norm(s):
    """The comparison key for a name: case, spacing and punctuation removed."""
    if not s:
        return ""
    s = unicodedata.normalize("NFC", str(s)).lower()
    return re.sub(r"[\s\-.()\[\],/'\"·•]+", "", s)


def _metres(lng1, lat1, lng2, lat2):
    p = math.pi / 180
    return 6371000 * math.hypot((lng2 - lng1) * p * math.cos((lat1 + lat2) / 2 * p),
                                (lat2 - lat1) * p)


def load(province=None):
    """Every cached Overture row, or those of one province. [] when uncached.

    A silent zero is a bug (the pins.json lesson), so an absent cache says so
    and names the command that fills it.
    """
    if not CACHE.exists():
        print("overture: no cache — run importers/harvest_overture.py")
        return []
    with gzip.open(CACHE, "rt", encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh]
    return [r for r in rows if province is None or r["province"] == province]


def manifest():
    return json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}


def _rules():
    doc = json.loads(CATMAP.read_text())
    return [(re.compile(r["match"]), r["cat"], r.get("sub")) for r in doc["rules"]]


_ATTR_SHELF = None


def _attr_shelf():
    """(cat, sub) -> the attrs key that shelf's child actually reads.

    A child in data/categories.json claims a record three ways — {sub} on
    record.sub, {lens} on attrs.lens, {attr, value} on attrs — and every
    medical child plus essentials/pharmacy claims by
    {attr: "facilityType"}. importers/import_overpass.py mirrors `sub` into
    `facilityType` for exactly that reason, in a comment saying a crawled
    clinic "has to speak the same way or it arrives on the shelf and lands
    under none of its children". This fold did not, and 1,842 rows — 558
    hospitals, 568 clinics, 276 chemists — stood on the medical and
    essentials shelves under no child of either, reachable only by search.

    Read off the tree rather than listed here, so a child that changes its
    match kind and a new child that claims by an attr both arrive the day
    they land, instead of the next time somebody counts the homeless.
    """
    global _ATTR_SHELF
    if _ATTR_SHELF is None:
        doc = json.loads(SHELVES.read_text())
        _ATTR_SHELF = {(c["key"], m["value"]): m["attr"]
                       for c in doc["categories"]
                       for ch in c.get("children", [])
                       for m in [ch.get("match") or {}]
                       if m.get("attr") and m.get("value") is not None}
    return _ATTR_SHELF


_RX = None


def shelf_of(row):
    """(cat, sub) for an Overture row, or None when nothing here files it.

    The alternate categories are consulted after the primary, which is how a
    place Overture calls `spas` and also `massage` lands on the massage shelf
    rather than the beauty one.
    """
    global _RX
    if _RX is None:
        _RX = _rules()
    for cat in [row.get("cat")] + list(row.get("catAlt") or []):
        if not cat:
            continue
        for rx, c, s in _RX:
            if rx.search(cat):
                return c, s
    return None


def _facebook(row):
    for s in row.get("socials") or []:
        if _FB.match(s or ""):
            return s
    return None


def _split_website(url):
    """(the venue's own site, {attr: value}) for one website value.

    Overture's `websites` is whatever the page put in its website box, which in
    Chiang Mai is a Google Maps share link as often as a domain. A social
    address is a real fact and lands in the field that already renders it
    (build.py knows facebook, instagram, lineUrl, email); a link to a map of
    the place is nobody's website and is dropped.
    """
    if not url:
        return None, {}
    if _NOT_A_WEBSITE.match(url):
        return None, {}
    host = _host(url)
    if _MAIL_HOST.match(host):
        return None, {}
    typed = _MAIL_TYPED.match(host)
    if typed and not host.startswith(("spaces.", "www.spaces.")):
        return None, {"email": f"{typed.group(1)}@{typed.group(2)}"}
    if _FB.match(url):
        return None, {"facebook": url}
    if _IG.match(url):
        return None, {"instagram": url}
    if _LINE.match(url):
        return None, {"lineUrl": url}
    return url, {}


def _source(row, m):
    """The receipt. `directory` is deliberate — see the module docstring."""
    return {"type": "directory", "ref": row["id"], "via": "overture",
            "fetched": m.get("fetched", ""), "licence": m.get("licence", ""),
            "dataset": row.get("dataset") or "", "release": m.get("release", "")}


def _index(rows):
    """Rows by ~200 m grid cell, for a nine-cell lookup around a record."""
    grid = defaultdict(list)
    for r in rows:
        grid[(int(r["lng"] / 0.002), int(r["lat"] / 0.002))].append(r)
    return grid


def _match(record, grid):
    """The nearest Overture row that is the same place, or None.

    Nearest rather than first: two shops in one building both pass the name
    test often enough to matter, and the closer one is the better answer.
    """
    lat, lng = record.get("lat"), record.get("lng")
    if not (lat and lng):
        return None
    names = {_norm(record.get(k)) for k in ("name", "nameTh", "nameEn")} - {""}
    if not names:
        return None
    gx, gy = int(lng / 0.002), int(lat / 0.002)
    best = None
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for row in grid.get((gx + dx, gy + dy), ()):
                rn = _norm(row["name"])
                if not rn:
                    continue
                same = rn in names or any(
                    len(n) >= MIN_CONTAIN and (n in rn or rn in n) for n in names)
                if not same:
                    continue
                d = _metres(lng, lat, row["lng"], row["lat"])
                if d <= MATCH_M and (best is None or d < best[0]):
                    best = (d, row)
    return best


def _neighbour(row, cat, grid):
    """The held record this row stands on top of, or None.

    Same shelf, within REVIEW_M, and the name rule already said no. That is
    either one place under two spellings or two shops in one building, and
    nothing here can tell which — so it is a question for a person rather than
    an answer from a join.
    """
    gx, gy = int(row["lng"] / 0.002), int(row["lat"] / 0.002)
    best = None
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for other in grid.get((gx + dx, gy + dy), ()):
                if cat not in (other.get("cat") or []):
                    continue
                d = _metres(row["lng"], row["lat"], other["lng"], other["lat"])
                if d <= REVIEW_M and (best is None or d < best[0]):
                    best = (d, other)
    return best


def apply(final, prov):
    """A and B, in one pass. Returns (enriched, [new records]).

    Called on the MERGED list, like import_opec.apply and
    import_condo_register.apply and for the same reason: it joins by name and
    has to see everything we hold before it decides a place is missing.
    """
    rows = [r for r in load(prov) if r.get("name") and r.get("lat") and r.get("lng")]
    if not rows:
        return 0, []
    m = manifest()
    grid = _index(rows)
    try:
        import provenance as P
    except ImportError:                                       # pragma: no cover
        import sys
        sys.path.insert(0, str(ROOT))
        import provenance as P

    # ---------------------------------------------------------------- A
    taken = set()
    enriched = 0
    for rec in final:
        hit = _match(rec, grid)
        if not hit:
            continue
        _, row = hit
        taken.add(row["id"])
        src = _source(row, m)
        key = P.source_key(src)
        filled = []
        if row.get("phone") and not rec.get("phone"):
            rec["phone"] = row["phone"]
            P.stamp(rec, "phone", key, P.STATED, m.get("fetched", ""))
            filled.append("phone")
        site, extra = _split_website(row.get("website"))
        if site and not rec.get("website"):
            rec["website"] = site
            P.stamp(rec, "website", key, P.STATED, m.get("fetched", ""))
            filled.append("website")
        addr = row.get("address")
        if addr and not rec.get("address") and _ADDRESSY.search(addr):
            rec["address"] = addr
            P.stamp(rec, "address", key, P.STATED, m.get("fetched", ""))
            filled.append("address")
        attrs = rec.setdefault("attrs", {})
        for k, v in (extra or {}).items():
            if v and not attrs.get(k):
                attrs[k] = v
                filled.append(k)
        fb = _facebook(row)
        if fb and not attrs.get("facebook"):
            attrs["facebook"] = fb
            filled.append("facebook")
        if row.get("email") and not attrs.get("email"):
            attrs["email"] = row["email"]
            filled.append("email")
        if not filled:
            continue
        # The source is appended only when something was taken. A record that
        # gained nothing keeps its provenance clean, and its give-back status
        # with it.
        rec.setdefault("sources", []).append(src)
        rec["confidence"] = rec.get("confidence") or "third-party"
        enriched += 1

    # ---------------------------------------------------------------- B
    # Everything the match rule did not claim, filed by category, deduplicated
    # against itself: Overture carries the same shop twice often enough that
    # importing it raw would ship visible pairs.
    near = _index([r for r in final if r.get("lat") and r.get("lng")])
    review = []
    seen = {}
    new = []
    for row in rows:
        if row["id"] in taken:
            continue
        if (row.get("confidence") or 0) < MIN_CONFIDENCE:
            continue
        shelf = shelf_of(row)
        if not shelf:
            continue
        cat, sub = shelf
        close = _neighbour(row, cat, near)
        if close:
            d, other = close
            review.append(f"{round(d):3d} m  {row['name']}  [{cat}]  "
                          f"overture:{row['id']}\n        stands beside  "
                          f"{other.get('name')}  {other['id']}")
            continue
        key = (_norm(row["name"]), round(row["lat"], 3), round(row["lng"], 3))
        if key in seen:
            continue
        seen[key] = row["id"]
        name = row["name"].strip()
        is_thai = bool(_THAI.search(name))
        attrs = {"overtureConfidence": round(row["confidence"], 2),
                 "overtureCategory": row.get("cat") or ""}
        if _facebook(row):
            attrs["facebook"] = _facebook(row)
        if row.get("email"):
            attrs["email"] = row["email"]
        if row.get("brand"):
            attrs["brand"] = row["brand"]
        site, extra = _split_website(row.get("website"))
        for k, v in (extra or {}).items():
            attrs.setdefault(k, v)
        # Say the shelf's own word for this reading as well as ours. It is the
        # same reading either way — stamped DERIVED below as `sub` — so this
        # states nothing the record was not already claiming.
        attr = _attr_shelf().get((cat, sub))
        if attr:
            attrs.setdefault(attr, sub)
        addr = row.get("address") or ""
        rec = {
            "id": f"{prov}-ovt-{row['id']}",
            "province": prov,
            "cat": [cat], "sub": [sub] if sub else [],
            "name": name,
            "nameTh": name if is_thai else None,
            "nameEn": None if is_thai else name,
            "lat": row["lat"], "lng": row["lng"],
            "geoPrecision": "exact",
            "address": addr if _ADDRESSY.search(addr) else None,
            "phone": row.get("phone"), "website": site,
            "hours": None,
            "attrs": attrs, "featured": False, "landmark": False,
            "sources": [_source(row, m)],
            "confidence": "third-party",
            "updatedAt": m.get("fetched", ""),
        }
        src_key = P.source_key(rec["sources"][0])
        for field in ("name", "nameTh", "nameEn", "phone", "website", "address",
                      "lat", "lng"):
            if rec.get(field):
                P.stamp(rec, field, src_key, P.STATED, m.get("fetched", ""))
        # The shelf is OUR reading of their category, not their claim.
        P.stamp(rec, "cat", src_key, P.DERIVED, m.get("fetched", ""))
        if rec["sub"]:
            P.stamp(rec, "sub", src_key, P.DERIVED, m.get("fetched", ""))
        new.append(rec)
    if review:
        path = ROOT / "cache" / f"overture_review_{prov}.txt"
        path.write_text(
            f"{len(review)} Overture rows standing within {REVIEW_M} m of a "
            f"record we already hold, on the same shelf, under a name the "
            f"match rule did not recognise.\nEach is either one place spelled "
            f"two ways or two shops in one building. Neither was settled here.\n"
            f"\n" + "\n".join(review) + "\n", encoding="utf-8")
        print(f"{prov}: {len(review)} near-miss(es) → "
              f"cache/overture_review_{prov}.txt")
    return enriched, new


if __name__ == "__main__":
    import sys
    m = manifest()
    print(f"overture release {m.get('release')} fetched {m.get('fetched')}")
    for prov in ("cm", "cr"):
        rows = load(prov)
        mapped = sum(1 for r in rows if shelf_of(r))
        print(f"{prov}: {len(rows)} rows, {mapped} filed by category "
              f"({mapped / max(len(rows), 1):.0%})")
    sys.exit(0)
