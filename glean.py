#!/usr/bin/env python3
"""GLEAN — what people send us, routed to every place on the site it fits.

Nan, 2026-09-27: "we should be gleaning things that people send us for use
EVERYWHERE, not just stovepiped to real estate."

A listing an agency sends the Listing Sheet says more than its price. It names
the building's juristic office and its phone, the year the block went up, how
many storeys it has, whether the building has a lift, a gym, a keycard door,
whether its rules allow short lets. Those are facts about a BUILDING that Mot
Dang holds a record for, and until now they stayed inside one listing row.
This module reads each submission once, turns it into observations, and sends
each observation where it belongs.

    python3 glean.py                    all sources, writes data/ and _incoming/
    python3 glean.py --source listings  one source
    python3 glean.py --dry-run          counts per destination, writes nothing
    python3 glean.py --sample           listing-sheet samples/, scratch dir only
    python3 glean.py --sample --dry-run

ADAPTERS, one per submission source, yield observations:

    {"subject": {"kind": "place"|"building"|"agency"|"area",
                 "id": <Mot Dang record id or None>, "name", "province",
                 "lat", "lng"},
     "field": <a key of ROUTES>,
     "value": ...,
     "at": "YYYY-MM-DD",
     "source": {"kind": "lister"|"owner-claim", "who": <agency slug or
                "owner">, "ref": <what a person can find it by>,
                "licence": <licence string or None>},
     "ctx": {...}}     routing context a destination reads (property kind,
                       bind ground, tambon as written, status); not an identity

Built: `listings` (listing-sheet listings/*.json, bound to buildings by that
repo's resolve.py) and `claims` (data/claims.json). The suggestion queue
(importers/sync_suggestions.py → facts.py) and toilet reports
(data/toilet_reports.json) join the same way: a function taking the context
and yielding observations, a line in ADAPTERS, and their field names in ROUTES.

ROUTES maps a field to its destinations, each with the reason. A destination
can still decline an observation (a conflict, no licence, a cell under three)
and the ledger says which and why.

OUTPUT SHAPES

data/curated/gleaned_facts.json — facts.py's doc shape, one source per fact:
    {"_readme": str,
     "facts": {<record id>: {<facts.BUILDING_FIELDS key or "pin">:
                {"value", "at", "source": "lister:<agency slug>",
                 "ref": "listing:<slug>/<ref>[,...]"}}}}
    facts.load_all() merges it with facts.json; import_all.py applies both.

data/gleaned/prices.json — asking-price aggregates, no single listing:
    {"_readme": str, "min_n": 3,
     "cells": [{"province", "tambon", "tambon_script": "thai"|"latin",
                "kind", "offer": "sale"|"rent", "bedrooms": "studio"|"1"|"2"|
                "3"|"4+"|"unstated"|"n/a", "n", "median", "p25", "p75",
                "from", "to"}],          rent is baht a month, sale is baht
     "withheld": {"cells": int, "properties": int}}

data/gleaned/pictures.json — {<building record id>: [{"src", "credit",
    "licence", "at", "listing"}]}, only from rows whose source.licence is set.

data/gleaned/buildings.json — per building, for the place page:
    {<building record id>: {
        "name": the lister's name for it,
        "facts": {<field>: {"value", "at", "source", "ref"}},
        "pictures": [as in pictures.json],
        "offers": {"live", "lapsed", "sold", "let", "withdrawn": property
                   counts by current state (listing-sheet sheet.group),
                   "sale_thb": [min, max] | None,       live offers only
                   "rent_month_thb": [min, max] | None, live offers only
                   "as_of": latest date any lister stood behind a price}}}

_incoming/glean-review-<date>.json — for a person; nothing in it is applied:
    {"unbound_buildings", "off_shelf_binds", "agencies_off_shelf",
     "tambon_pairs", "brand_candidates", "conflicts", "lister_disagreements"}

data/gleaned/ledger.jsonl — one line per (observation, outcome):
    {"obs", "logged", "source", "subject", "field", "value", "went": [{"to",
     "result", "why"}]}; a line already on disk is not written again.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import statistics
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import facts  # noqa: E402

LS_ROOT = Path(os.environ.get("LS_ROOT", ROOT.parent / "listing-sheet"))

# listing-sheet/samples/*.json carry this in source.cite. They are invented
# offers for exercising filters (listing-sheet sheet.py, LISTINGS comment), so
# a sample row that reached data/ would put a made-up price and a made-up
# juristic office on a real building.
SAMPLE_MARK = "INVENTED SAMPLE ROW"

# Nan's brief for prices, 2026-09-27: aggregates only, and a cell under three
# properties is withheld, because with one or two a reader can read a single
# agency's asking price back out of the "median".
MIN_CELL = 3

# Kinds where the listing is one unit inside a shared building, so the
# building's facts (storeys, year, lift, juristic office) are common to every
# unit. listing-sheet facets.validate checks `floor_level <= floors` on these,
# which is how `floors` reads as the building's storeys and not the unit's.
MULTI = {"condo", "apartment", "room"}
# Kinds that can stand inside a housing estate (หมู่บ้านจัดสรร). The estate has
# a juristic person and shared grounds; the house's own year, storeys and
# fittings are that one owner's, not the estate's.
ESTATE = {"house", "townhouse", "compound"}

# Mot Dang shelves a listing's building facts may land on. resolve.py binds a
# row to ANY register record within 25 m, and in town that can be the 7-Eleven
# next door; a juristic office's phone on a 7-Eleven is the error this avoids.
HOUSING_SUB = {"multi": {"condo", "apartment", "dorm"}, "estate": {"moobaan"}}

# SERVICES in listing-sheet facets.py (72 codes, 2026-09-27), split by whether
# the building or the unit has it. A building fact goes on the Mot Dang record;
# a unit fact stays with the listing. Where a code could be either, it stays
# with the listing: one lister's word about their unit does not describe the
# neighbours'.
SERVICE_SPLIT = {
    # the building's, shared by every unit
    "shared_pool": ("building", "one pool for the block"),
    "lift": ("building", "a lift serves the block"),
    "security": ("building", "the guard is the building's"),
    "cctv": ("building", "cameras cover common areas"),
    "gym": ("building", "a residents' gym"),
    "sauna": ("building", "in a condo, a common-area facility"),
    "rooftop": ("building", "the roof is common property"),
    "coworking": ("building", "a common room"),
    "playground": ("building", "common grounds"),
    "bbq": ("building", "a common-area barbecue"),
    "shuttle": ("building", "run by the juristic office"),
    "ev_charger": ("building", "in the building's car park"),
    "gated": ("building", "the gate is the building's"),
    "library": ("building", "a common room"),
    "games_room": ("building", "a common room"),
    "tennis": ("building", "a common court"),
    "badminton": ("building", "a common court"),
    "clubhouse": ("building", "common property"),
    "reception_24h": ("building", "the lobby desk"),
    "keycard": ("building", "the building's door system"),
    "intercom": ("building", "the building's door system"),
    "sprinkler": ("building", "a building system"),
    "fire_escape": ("building", "a building system"),
    "backup_water": ("building", "the block's tank"),
    "generator": ("building", "in a block, the building's backup"),
    "parking": ("building", "in a block, the building's car park"),
    "motorbike_parking": ("building", "the building's"),
    "bike_parking": ("building", "the building's"),
    "guest_parking": ("building", "the building's"),
    "garden": ("building", "in a block, common grounds"),
    "rubbish": ("building", "collected by the building"),
    "post_box": ("building", "the building's mail room"),
    "fibre": ("building", "the line comes into the building"),
    # the unit's, stays with the listing
    "pool": ("unit", "a private pool is the unit's"),
    "carport": ("unit", "the unit's own"),
    "garage": ("unit", "the unit's own"),
    "aircon": ("unit", "fitted in the unit"),
    "water_heater": ("unit", "fitted in the unit"),
    "kitchen": ("unit", "in the unit"),
    "furnished_kitchen": ("unit", "in the unit"),
    "balcony": ("unit", "the unit's own"),
    "study": ("unit", "a room of the unit"),
    "walk_in_closet": ("unit", "in the unit"),
    "bathtub": ("unit", "in the unit"),
    "washing_machine": ("unit", "in the unit"),
    "dryer": ("unit", "in the unit"),
    "dishwasher": ("unit", "in the unit"),
    "microwave": ("unit", "in the unit"),
    "oven": ("unit", "in the unit"),
    "fridge": ("unit", "in the unit"),
    "tv": ("unit", "in the unit"),
    "desk": ("unit", "in the unit"),
    "safe": ("unit", "in the unit"),
    "smoke_alarm": ("unit", "fitted in the unit"),
    "water_filter": ("unit", "fitted in the unit"),
    "air_purifier": ("unit", "in the unit"),
    "storage": ("unit", "a unit's storeroom"),
    "solar": ("unit", "a house's own panels"),
    "well": ("unit", "a plot's own well"),
    "three_phase": ("unit", "the unit's supply"),
    "mains_water": ("unit", "the plot's supply"),
    "garden_service": ("unit", "a service to one house"),
    "pool_service": ("unit", "a service to one house"),
    "mountain_view": ("unit", "depends on the floor and the side"),
    "river": ("unit", "one unit faces the water, another does not"),
    "wifi": ("unit", "either: some blocks supply it, some units bring their own"),
    "laundry": ("unit", "either: a common laundry room or a machine in the unit"),
    "maid_service": ("unit", "either: a serviced block or one unit's arrangement"),
    "jacuzzi": ("unit", "either: common or in the unit"),
    "wheelchair": ("unit", "either: step-free lobby or step-free unit"),
    "childcare": ("unit", "either: in the building or nearby"),
    "golf": ("unit", "either: in the estate or nearby"),
}
# Building-class services an ESTATE row speaks for: the grounds the estate
# shares. A house row's parking or garden is that house's.
ESTATE_SHARED = {"shared_pool", "security", "cctv", "gated", "clubhouse",
                 "playground", "gym", "tennis", "badminton", "keycard"}

# facet key → (fact field, kinds that speak for the building, reason)
BUILDING_FACETS = {
    "juristic_name": ("juristic_name", MULTI | ESTATE,
                      "the juristic person is the building's or the estate's"),
    "juristic_contact": ("juristic_phone", MULTI | ESTATE,
                         "the juristic office's phone, when it reads as a phone"),
    "year_built": ("year_built", MULTI, "one year for the whole block"),
    "floors": ("storeys", MULTI, "in a block, `floors` is the building's"),
    "short_lets": ("short_lets", MULTI, "a juristic rule for the whole block"),
    # The 49% foreign freehold quota is a Condominium Act (B.E. 2522) matter.
    "foreign_quota": ("foreign_quota", {"condo"}, "the condominium's quota register"),
}

# Destination names used in ROUTES and the ledger.
FACTS, PRICES, PICTURES, BUILDINGS, REVIEW, LISTING = (
    "facts", "prices", "pictures", "buildings", "review", "listing")

ROUTES = {
    "juristic_name": [(FACTS, "the building's juristic office, same for every unit"),
                      (BUILDINGS, "the place page shows it")],
    "juristic_phone": [(FACTS, "the office's phone, same for every unit"),
                       (BUILDINGS, "the place page shows it")],
    "year_built": [(FACTS, "one year for the block"), (BUILDINGS, "the place page shows it")],
    "storeys": [(FACTS, "one height for the block"), (BUILDINGS, "the place page shows it")],
    "short_lets": [(FACTS, "a juristic rule, same for every unit"),
                   (BUILDINGS, "the place page shows it")],
    "foreign_quota": [(FACTS, "dated statement of the condominium's quota"),
                      (BUILDINGS, "the place page shows it")],
    "amenity": [(FACTS, "building-level per SERVICE_SPLIT; unit-level stays with the listing"),
                (BUILDINGS, "the place page shows it")],
    "pin": [(FACTS, "a point for a building with none"),
            (REVIEW, "a point for a building on no register")],
    "asking_price": [(PRICES, "aggregated by tambon, kind, offer, bedrooms"),
                     (BUILDINGS, "live offer ranges for the place page")],
    "offer_status": [(BUILDINGS, "live, let, sold counts for the place page")],
    "photo": [(PICTURES, "a building picture when the row carries a licence"),
              (BUILDINGS, "the place page shows it")],
    "agency": [(REVIEW, "an agency not on the Mot Dang agent shelf")],
    "tambon": [(REVIEW, "a Latin tambon beside the Thai one on the bound building (WO-59 pairs)"),
               (PRICES, "the cell's tambon")],
    "building_name": [(REVIEW, "a Latin name beside the building's Thai one: rtgs_lexicon brand")],
    "unbound": [(REVIEW, "a building on no register, with a point and its precision")],
    "unit_facets": [(LISTING, "the unit's own: bedrooms, furnishing, rent terms")],
    "juristic_contact": [(LISTING, "not a phone number, so not routed as one")],
    # owner claims: build.py reads data/claims.json straight onto the place
    # page (build.py CLAIMS), so the ledger records that the claim arrived.
    "claim": [(LISTING, "build.py renders data/claims.json on the place page")],
    "toilet_report": [(LISTING, "toilets_layer.py bakes it into /toilets.html and "
                                "docs/data/toilets.json, which the fleet search's "
                                "has=toilet filter reads")],
    "reader_fact": [(LISTING, "facts.load_all puts it on the record in import_all.py "
                              "and build.py")],
}


# ---------------------------------------------------------------- helpers


def is_sample(row):
    return SAMPLE_MARK in str(((row or {}).get("source") or {}).get("cite") or "").upper()


class SampleRowRefused(Exception):
    """An invented sample row was about to reach mot-dang data."""


def _inside(child, parent):
    try:
        Path(child).resolve().relative_to(Path(parent).resolve())
        return True
    except ValueError:
        return False


def _fold(s):
    import unicodedata
    s = unicodedata.normalize("NFKC", str(s or "").strip().casefold())
    s = re.sub(r"^(?:ตำบล|ต\.|tambon|t\.|sub-?district)\s*", "", s)
    return re.sub(r"[\s\-_.,/#()&'\"]+", "", s)


def _obs_id(o):
    basis = json.dumps([o["source"]["kind"], o["source"]["ref"],
                        o["subject"].get("id") or o["subject"].get("name"),
                        o["field"], o["value"]], ensure_ascii=False, sort_keys=True,
                       default=str)
    return hashlib.sha1(basis.encode("utf-8")).hexdigest()[:16]


def _dump(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def _write_if_changed(path, text):
    path = Path(path)
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True


def _band(beds, kind):
    if kind in ("land", "commercial"):
        return "n/a"
    if beds is None:
        return "unstated"
    b = int(beds)
    return "studio" if b == 0 else (str(b) if b <= 3 else "4+")


def _is_thai(s):
    return bool(re.search(r"[ก-๙]", s or ""))


# ---------------------------------------------------------------- context


class Context:
    """What the adapters and destinations read: the Mot Dang records, the
    listing-sheet loader, a locator for unpinned rows, and the output paths.

    `records` is a list of Mot Dang records (both provinces). Tests pass a
    handful; the CLI loads data/canonical. `locate(address, province)` is
    importers/geocode_local.Gazetteer().locate unless a test passes its own
    (building the gazetteer reads all of data/canonical again: ~4 min,
    measured 2026-09-27)."""

    def __init__(self, records, listings_dir, out_dir, incoming_dir,
                 curated_dir=None, locate=None, sample=False, today=None,
                 claims_path=None, ls_root=None, photos_dir=None):
        self.records = records
        self.by_id = {r["id"]: r for r in records if r.get("id")}
        self.listings_dir = Path(listings_dir)
        self.out_dir = Path(out_dir)
        self.incoming_dir = Path(incoming_dir)
        self.curated_dir = Path(curated_dir or ROOT / "data" / "curated")
        self.facts_out = self.curated_dir / facts.GLEANED_FILE
        self._locate = locate
        self.sample = sample
        self.today = today or date.today().isoformat()
        self.claims_path = Path(claims_path) if claims_path else ROOT / "data" / "claims.json"
        self.ls_root = Path(ls_root or LS_ROOT)
        self.photos_dir = Path(photos_dir or self.ls_root / "photos")
        self.refused_samples = 0
        self.faults = []
        self.rows = []
        self.groups = []
        self.agent_names = set()
        for r in records:
            if "agent" in (r.get("sub") or []):
                for n in (r.get("name"), r.get("nameTh"), r.get("nameEn")):
                    if n:
                        self.agent_names.add(_agency_fold(n))
        try:
            self.curated_pins = set((json.loads((self.curated_dir / "pins.json").read_text(
                encoding="utf-8")).get("pins") or {}).keys())
        except (OSError, ValueError):
            self.curated_pins = set()
        # Latin tambon → Thai, once a person has confirmed a pair from the
        # review file. Absent until then; cells keep the tambon as written.
        try:
            self.tambon_pairs = json.loads((self.curated_dir / "tambon_pairs.json").read_text(
                encoding="utf-8")).get("pairs") or {}
        except (OSError, ValueError):
            self.tambon_pairs = {}

    def locate(self, address, province):
        if self._locate is None:
            sys.path.insert(0, str(ROOT / "importers"))
            import geocode_local
            self._locate = geocode_local.Gazetteer().locate
        return self._locate(address, province)

    def housing_class(self, ref):
        r = self.by_id.get(ref) or {}
        if "realestate" not in (r.get("cat") or []):
            return None
        sub = set(r.get("sub") or [])
        for cls, subs in HOUSING_SUB.items():
            if sub & subs:
                return cls
        return None


def _agency_fold(name):
    s = _fold(name)
    return re.sub(r"(coltd|companylimited|limited|ltd|co|บจก|บริษัท|จำกัด)", "", s)


def _import_sheet(ctx):
    if str(ctx.ls_root) not in sys.path:
        sys.path.insert(0, str(ctx.ls_root))
    import sheet
    import resolve
    sheet.LISTINGS = ctx.listings_dir
    return sheet, resolve


# ---------------------------------------------------------------- adapters


def adapt_listings(ctx):
    """listing-sheet rows → observations. Rows are loaded and bound by that
    repo's own sheet.load_all + resolve.py, so the building_ref here is the one
    the Listing Sheet renders."""
    sheet, resolve = _import_sheet(ctx)
    reg = resolve.Register(ctx.records)
    rows, faults = sheet.load_all(reg)
    ctx.faults = faults
    kept = []
    for row in rows:
        if is_sample(row) and not ctx.sample:
            ctx.refused_samples += 1
            continue
        kept.append(row)
    if any(is_sample(r) for r in kept) and _inside(ctx.out_dir, ROOT):
        # write_all checks again at the point of writing.
        raise SampleRowRefused("sample rows run only with --sample into a scratch "
                               "dir outside mot-dang")
    ctx.rows = kept
    ctx.groups = sheet.group(kept) if kept else []
    status_of = {}
    for g in ctx.groups:
        for o in g["offers"]:
            status_of[id(o)] = o["_status"]

    import agencies as A
    for row in kept:
        prop, offer, fac = row["property"], row["offer"], row.get("facets") or {}
        slug = A.slug_of(row)
        src = row.get("source") or {}
        res = row.get("_resolved") or {}
        ref = prop.get("building_ref") if res.get("building_ref") else None
        kind = prop.get("kind")
        key = "listing:%s/%s" % row["_key"]
        source = {"kind": "lister", "who": slug, "ref": key,
                  "licence": src.get("licence") or None}
        subject = {"kind": "building", "id": ref, "name": prop.get("name"),
                   "province": prop.get("province"), "lat": prop.get("lat"),
                   "lng": prop.get("lng")}
        ctx_ = {"property_kind": kind, "building_ref": ref, "bound_by": res.get("by"),
                "candidates": res.get("candidates") or [],
                "candidate_count": res.get("candidate_count", 0),
                "housing": ctx.housing_class(ref) if ref else None,
                "tambon": prop.get("tambon") or "", "amphoe": prop.get("amphoe") or "",
                "address": prop.get("address") or "", "property_id": row["_id"],
                "lat": prop.get("lat"), "lng": prop.get("lng"),
                "raw_id": row["_raw_id"], "status": status_of.get(id(row), "live"),
                "offer_type": offer["type"], "agency_name": row["agency"]["name"],
                "agency_contact": row["agency"].get("contact") or "",
                "credit": src.get("credit") or row["agency"]["name"]}
        at = row["_as_of"].isoformat()

        def ob(field, value, subj=subject):
            return {"subject": subj, "field": field, "value": value, "at": at,
                    "source": source, "ctx": ctx_}

        for facet, (field, _kinds, _why) in BUILDING_FACETS.items():
            v = fac.get(facet)
            if v in (None, "", "not_stated"):
                continue
            if facet == "juristic_contact":
                ph = facts.BUILDING_FIELDS["juristic_phone"][1](str(v))
                yield ob("juristic_phone" if ph else "juristic_contact", ph or v)
            elif facet == "foreign_quota":
                yield ob(field, {"status": v, "as_of": at})
            else:
                yield ob(field, v)
        for code in sorted(set(fac.get("services") or [])):
            yield ob("amenity", code)
        unit_keys = sorted(k for k in fac if k not in BUILDING_FACETS and k != "services")
        if unit_keys:
            yield ob("unit_facets", unit_keys)
        if prop.get("lat") is not None and prop.get("lng") is not None:
            yield ob("pin", [float(prop["lat"]), float(prop["lng"])])
        yield ob("asking_price", {"thb": offer["price_thb"], "offer": offer["type"],
                                  "kind": kind, "bedrooms": fac.get("bedrooms")})
        yield ob("offer_status", ctx_["status"])
        for n in prop.get("photos") or []:
            yield ob("photo", n)
        yield ob("agency", row["agency"]["name"],
                 {"kind": "agency", "id": None, "name": row["agency"]["name"],
                  "province": prop.get("province"), "lat": None, "lng": None})
        if prop.get("tambon"):
            yield ob("tambon", prop["tambon"],
                     {"kind": "area", "id": None, "name": prop["tambon"],
                      "province": prop.get("province"), "lat": None, "lng": None})
        if ref:
            yield ob("building_name", prop.get("name"))
        else:
            yield ob("unbound", prop.get("name"))


def adapt_claims(ctx):
    """data/claims.json → one observation per field an owner stated. Values
    stay in claims.json; the ledger records that a field arrived and where."""
    try:
        doc = json.loads(ctx.claims_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    for pid, c in sorted((doc.get("claims") or {}).items()):
        r = ctx.by_id.get(pid) or {}
        at = str(c.get("updatedAt") or c.get("claimedAt") or "")[:10] or ctx.today
        for k in sorted(c):
            if k in ("placeId", "claimedAt", "updatedAt", "confirmedAt", "lineUserId") \
                    or c[k] in (None, "", []):
                continue
            yield {"subject": {"kind": "place", "id": pid, "name": r.get("name"),
                               "province": r.get("province"), "lat": r.get("lat"),
                               "lng": r.get("lng")},
                   "field": "claim", "value": k, "at": at,
                   "source": {"kind": "owner-claim", "who": "owner",
                              "ref": "claim:" + pid, "licence": None},
                   "ctx": {}}


def adapt_toilets(ctx):
    """data/toilet_reports.json (importers/sync_toilets.py) → one observation
    per place a passer-by reported. Ledger only: the report already reaches
    /toilets.html and the search filter."""
    try:
        doc = json.loads((ROOT / "data" / "toilet_reports.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    for pid, rep in sorted((doc.get("reports") or {}).items()):
        r = ctx.by_id.get(pid) or {}
        yield {"subject": {"kind": "place", "id": pid, "name": r.get("name"),
                           "province": r.get("province"), "lat": r.get("lat"),
                           "lng": r.get("lng")},
               "field": "toilet_report", "value": (rep or {}).get("report"),
               "at": str((rep or {}).get("at") or "")[:10] or ctx.today,
               "source": {"kind": "passer-by", "who": "reader", "ref": "toilet:" + pid,
                          "licence": None},
               "ctx": {}}


def adapt_reader_facts(ctx):
    """data/curated/facts.json (approved by hand through apply_facts.py) → one
    observation per field. Ledger only: facts.load_all applies them."""
    try:
        doc = json.loads((ctx.curated_dir / "facts.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    for pid, fields in sorted((doc.get("facts") or {}).items()):
        r = ctx.by_id.get(pid) or {}
        for field, fact in sorted((fields or {}).items()):
            yield {"subject": {"kind": "place", "id": pid, "name": r.get("name"),
                               "province": r.get("province"), "lat": r.get("lat"),
                               "lng": r.get("lng")},
                   "field": "reader_fact", "value": field,
                   "at": str((fact or {}).get("at") or "")[:10] or ctx.today,
                   "source": {"kind": "reader", "who": "reader",
                              "ref": "suggest:" + str((fact or {}).get("suggestion") or ""),
                              "licence": None},
                   "ctx": {}}


ADAPTERS = {"listings": adapt_listings, "claims": adapt_claims,
            "toilets": adapt_toilets, "reader_facts": adapt_reader_facts}


# ---------------------------------------------------------------- routing


class Router:
    def __init__(self, ctx):
        self.ctx = ctx
        self.outcomes = {}          # obs id → [{to, result, why}]
        self.obs = {}               # obs id → observation
        self.proposed = {}          # ref → field → [(value, at, source key, listing ref, oid)]
        self.price_obs = []
        self.photo_obs = []
        self.status_obs = []
        self.review = {"unbound_buildings": [], "off_shelf_binds": [],
                       "agencies_off_shelf": [], "tambon_pairs": [],
                       "brand_candidates": [], "conflicts": [],
                       "lister_disagreements": []}
        self._agencies = {}
        self._pairs = {}
        self._brands = {}
        self._unbound = {}
        self._offshelf = {}
        self._housing_pts = None

    def near_housing(self, lat, lng):
        """Housing records within resolve.COORD_M of a point, tambon ignored.

        resolve.bind refuses a coordinate match whose tambon disagrees, and it
        compares the folded strings: a row's "Su Thep" never equals a
        register building's "สุเทพ". Measured 2026-09-27: 1,614 of 1,682
        real-estate records carry a Thai tambon, so a row written in Latin
        binds by coordinates only to buildings with no tambon at all. These
        are the buildings such a row would bind to once its pair is confirmed.
        """
        if lat is None or lng is None:
            return []
        if self._housing_pts is None:
            self._housing_pts = [r for r in self.ctx.records
                                 if r.get("lat") is not None
                                 and self.ctx.housing_class(r["id"])]
        _sheet, resolve = _import_sheet(self.ctx)
        F = resolve.F
        out = []
        for r in self._housing_pts:
            d = F.haversine(float(lat), float(lng), r["lat"], r["lng"])
            if d <= resolve.COORD_M:
                out.append((round(d), r["id"]))
        return sorted(out)

    def went(self, oid, to, result, why):
        slot = self.outcomes.setdefault(oid, [])
        entry = {"to": to, "result": result, "why": why}
        if entry not in slot:
            slot.append(entry)

    def route(self, o):
        field = o["field"]
        if field not in ROUTES:
            raise KeyError(f"no route for field {field!r}; add it to ROUTES with its reason")
        oid = _obs_id(o)
        self.obs[oid] = o
        getattr(self, "_r_" + field, self._r_default)(oid, o)

    # -- per field

    def _r_default(self, oid, o):
        for to, why in ROUTES[o["field"]]:
            self.went(oid, to, "kept", why)

    def _building_ok(self, oid, o, kinds):
        """True when this observation may speak for its bound building."""
        c = o["ctx"]
        ref = o["subject"]["id"]
        if not ref:
            self.went(oid, FACTS, "declined", "row bound to no building")
            return False
        kind = c["property_kind"]
        housing = c["housing"]
        if kind not in kinds:
            self.went(oid, LISTING, "kept", f"a {kind} row does not speak for its building on this field")
            return False
        if housing is None:
            self.went(oid, REVIEW, "declined", "bound record is not on the housing shelf")
            self._off_shelf(o)
            return False
        want = "multi" if kind in MULTI else "estate"
        if housing != want:
            self.went(oid, LISTING, "kept", f"a {kind} row bound to a {housing} record")
            return False
        return True

    def _propose(self, oid, o, field, value):
        ref = o["subject"]["id"]
        self.proposed.setdefault(ref, {}).setdefault(field, []).append(
            (value, o["at"], "lister:" + o["source"]["who"], o["source"]["ref"], oid))

    def _r_building_fact(self, oid, o):
        field = o["field"]
        facet = next(k for k, v in BUILDING_FACETS.items() if v[0] == field)
        if not self._building_ok(oid, o, BUILDING_FACETS[facet][1]):
            return
        clean = facts.BUILDING_FIELDS[field][1](o["value"])
        if clean is None:
            self.went(oid, FACTS, "declined", "value did not validate (facts.BUILDING_FIELDS)")
            return
        self._propose(oid, o, field, clean)

    _r_juristic_name = _r_juristic_phone = _r_year_built = _r_storeys = \
        _r_short_lets = _r_foreign_quota = _r_building_fact

    def _r_amenity(self, oid, o):
        code = o["value"]
        side, why = SERVICE_SPLIT.get(code, ("unit", "not in SERVICE_SPLIT"))
        if side == "unit":
            self.went(oid, LISTING, "kept", f"unit-level: {why}")
            return
        kind = o["ctx"]["property_kind"]
        if kind in ESTATE and code not in ESTATE_SHARED:
            self.went(oid, LISTING, "kept", "a house's own, not the estate's")
            return
        if not self._building_ok(oid, o, MULTI | ESTATE):
            return
        self._propose(oid, o, "amenities", [code])

    def _r_pin(self, oid, o):
        ref = o["subject"]["id"]
        if not ref:
            self.went(oid, REVIEW, "kept", "the unbound row's own point")
            return
        if not self._building_ok(oid, o, MULTI):
            return
        r = self.ctx.by_id.get(ref) or {}
        if r.get("lat") is not None:
            self.went(oid, FACTS, "declined", "building already has a pin")
            return
        if ref in self.ctx.curated_pins:
            # import_all applies facts before curated pins, and a curated pin
            # only fills an empty one (apply_curated_pins); a lister's pin
            # written first would keep the hand-kept one out.
            self.went(oid, FACTS, "declined", "a curated pin is waiting in pins.json")
            return
        clean = facts._pin("%.6f, %.6f" % tuple(o["value"]))
        if clean is None:
            self.went(oid, FACTS, "declined", "outside northern Thailand")
            return
        self._propose(oid, o, "pin", clean)

    def _r_asking_price(self, oid, o):
        self.price_obs.append((oid, o))

    def _r_offer_status(self, oid, o):
        self.status_obs.append((oid, o))
        if o["subject"]["id"] and o["ctx"]["housing"]:
            self.went(oid, BUILDINGS, "kept", "counted on the building summary")
        else:
            self.went(oid, LISTING, "kept", "no housing building to count it on")

    def _r_photo(self, oid, o):
        self.photo_obs.append((oid, o))

    def _r_agency(self, oid, o):
        name = o["value"]
        if _agency_fold(name) in self.ctx.agent_names:
            self.went(oid, REVIEW, "declined", "already on the agent shelf")
            return
        slug = o["source"]["who"]
        a = self._agencies.setdefault(slug, {"name": name, "slug": slug, "rows": 0,
                                             "provinces": set(),
                                             "contact": o["ctx"]["agency_contact"]})
        a["rows"] += 1
        a["provinces"].add(o["subject"]["province"])
        self.went(oid, REVIEW, "kept", "not on the agent shelf")

    def _r_tambon(self, oid, o):
        self.went(oid, PRICES, "kept", "the cell's tambon")
        ref = o["ctx"]["building_ref"]
        latin = o["value"]
        if _is_thai(latin):
            self.went(oid, REVIEW, "declined", "written in Thai already")
            return
        r = self.ctx.by_id.get(ref) if ref else None
        th = ((r or {}).get("attrs") or {}).get("tambon") if o["ctx"]["housing"] else None
        evidence = f"bound to {ref} ({o['ctx']['bound_by']})" if th else ""
        if not th and not ref:
            near = self.near_housing(o["ctx"]["lat"], o["ctx"]["lng"])
            if len(near) == 1:
                ref = near[0][1]
                r = self.ctx.by_id.get(ref) or {}
                th = (r.get("attrs") or {}).get("tambon")
                evidence = (f"pinned {near[0][0]} m from {ref}; unbound because the "
                            f"tambon is written in another script")
        if not th:
            self.went(oid, REVIEW, "declined", "no housing building to pair with")
            return
        k = (o["subject"]["province"], _fold(latin), th)
        p = self._pairs.setdefault(k, {"province": o["subject"]["province"], "latin": latin,
                                       "thai": th, "amphoe_th": (r.get("attrs") or {}).get("amphoe"),
                                       "rows": 0, "buildings": set(), "evidence": set()})
        p["rows"] += 1
        p["buildings"].add(ref)
        p["evidence"].add(evidence)
        self.went(oid, REVIEW, "kept", "tambon pair")

    def _r_building_name(self, oid, o):
        import namejoin
        ref = o["subject"]["id"]
        r = self.ctx.by_id.get(ref) or {}
        latin = o["value"] or ""
        if not o["ctx"]["housing"]:
            self.went(oid, REVIEW, "declined", "bound record is not on the housing shelf")
            return
        thai = r.get("nameTh") or (r.get("name") if _is_thai(r.get("name")) else "")
        if _is_thai(latin) or not thai or r.get("nameEn"):
            self.went(oid, REVIEW, "declined", "no Thai-only building name to pair with")
            return
        lt = namejoin.token(latin)
        tt = namejoin.token(thai)
        if not lt or not tt or lt == tt:
            self.went(oid, REVIEW, "declined", "reading already matches the sign" if lt == tt
                      else "no identifying word")
            return
        if namejoin.skeleton(lt) != namejoin.skeleton(tt):
            self.went(oid, REVIEW, "declined", "consonants differ; not a spelling of one word")
            return
        thai_word = next((w for w in re.split(r"\s+", thai) if _is_thai(w)
                          and namejoin.token(w) == tt), thai.split()[0])
        k = (thai_word, lt)
        b = self._brands.setdefault(k, {"thai": thai_word, "reads_now": tt, "sign": lt,
                                        "buildings": set(), "listing_names": set()})
        b["buildings"].add(ref)
        b["listing_names"].add(latin)
        self.went(oid, REVIEW, "kept", "rtgs_lexicon brand candidate")

    def _r_unbound(self, oid, o):
        c = o["ctx"]
        if c["property_kind"] not in MULTI:
            # A house or a plot is one owner's home or land; a directory record
            # of it would be a private address (AGENTS.md, "A person's private
            # data does not go on a page").
            self.went(oid, LISTING, "kept", f"a {c['property_kind']} is not a shared building")
            return
        s = o["subject"]
        k = (s["province"], _fold(s["name"]), _fold(c["tambon"]))
        u = self._unbound.get(k)
        if u is None:
            if s["lat"] is not None and s["lng"] is not None:
                point = {"lat": s["lat"], "lng": s["lng"], "precision": "lister-pin",
                         "via": "the row's own coordinates"}
            else:
                hit = self.ctx.locate(c["address"] or c["tambon"], s["province"])
                point = ({k2: hit.get(k2) for k2 in ("lat", "lng", "precision",
                                                     "uncertainty_m", "via", "matched")}
                         if hit else {"precision": "none", "via": "geocode_local found nothing"})
            u = self._unbound[k] = {"name": s["name"], "kind": c["property_kind"],
                                    "province": s["province"], "tambon": c["tambon"],
                                    "amphoe": c["amphoe"], "address": c["address"],
                                    "bind": c["bound_by"] or "nothing matched",
                                    "candidates": c["candidates"], "point": point,
                                    "near_housing": self.near_housing(s["lat"], s["lng"]),
                                    "listings": set()}
        u["listings"].add(o["source"]["ref"])
        self.went(oid, REVIEW, "kept", "a building on no register")

    def _off_shelf(self, o):
        ref = o["subject"]["id"]
        r = self.ctx.by_id.get(ref) or {}
        e = self._offshelf.setdefault(ref, {"record": ref, "record_name": r.get("name"),
                                            "record_shelf": [r.get("cat"), r.get("sub")],
                                            "bind": o["ctx"]["bound_by"],
                                            "listing_name": o["subject"]["name"],
                                            "listings": set()})
        e["listings"].add(o["source"]["ref"])

    # -- resolve what was proposed

    def settle_facts(self):
        """Proposals → gleaned facts, or review. Returns {ref: {field: fact}}."""
        out = {}
        for ref in sorted(self.proposed):
            r = self.ctx.by_id.get(ref) or {}
            glean_stamps = (r.get("attrs") or {}).get("gleanedFacts") or {}
            for field, props in sorted(self.proposed[ref].items()):
                oids = [p[4] for p in props]
                refs = ",".join(sorted({p[3] for p in props}))
                whos = sorted({p[2] for p in props})
                at = max(p[1] for p in props)
                if field == "amenities":
                    value = sorted({c for p in props for c in p[0]})
                elif field == "foreign_quota":
                    value = max((p[0] for p in props), key=lambda v: v["as_of"])
                else:
                    vals = {json.dumps(p[0], sort_keys=True, ensure_ascii=False) for p in props}
                    if len(vals) > 1:
                        self.review["lister_disagreements"].append(
                            {"building": ref, "building_name": r.get("name"), "field": field,
                             "said": sorted(({"value": p[0], "who": p[2], "at": p[1],
                                              "listing": p[3]} for p in props),
                                            key=lambda d: (d["at"], d["who"]))})
                        for oid in oids:
                            self.went(oid, REVIEW, "kept", "listers disagree on this building")
                        continue
                    value = props[0][0]
                had = facts.current(r, field)
                ours = str((glean_stamps.get(field) or {}).get("source", "")).startswith("lister:")
                if field == "amenities":
                    pass
                elif had not in ("", None, []) and had != value and not ours:
                    self.review["conflicts"].append(
                        {"building": ref, "building_name": r.get("name"), "field": field,
                         "record_has": had, "lister_says": value, "who": whos, "at": at,
                         "listing": refs})
                    for oid in oids:
                        self.went(oid, REVIEW, "kept", "disagrees with the record")
                    continue
                elif had == value and not ours:
                    for oid in oids:
                        self.went(oid, FACTS, "declined", "the record already says so")
                    continue
                fact = {"value": value, "at": at, "source": whos[0], "ref": refs}
                if len(whos) > 1:
                    fact["also"] = whos[1:]
                out.setdefault(ref, {})[field] = fact
                for oid in oids:
                    self.went(oid, FACTS, "kept", ROUTES["amenity" if field == "amenities"
                                                         else field][0][1])
                    self.went(oid, BUILDINGS, "kept", "the place page shows it")
        return out

    def settle_prices(self):
        """Distinct properties per cell, the latest price each lister stood
        behind; cells under MIN_CELL withheld and counted."""
        latest = {}
        for oid, o in self.price_obs:
            c, v = o["ctx"], o["value"]
            k = (c["property_id"], v["offer"])
            if k not in latest or (o["at"], -v["thb"]) > (latest[k][1]["at"], -latest[k][1]["value"]["thb"]):
                latest[k] = (oid, o)
        cells = {}
        for (pid, offer), (oid, o) in latest.items():
            c, v, s = o["ctx"], o["value"], o["subject"]
            th = None
            if s["id"] and c["housing"]:
                th = ((self.ctx.by_id.get(s["id"]) or {}).get("attrs") or {}).get("tambon")
            if not th:
                th = self.ctx.tambon_pairs.get("%s|%s" % (s["province"], _fold(c["tambon"])))
            tambon, script = (th, "thai") if th else (_fold(c["tambon"]) or "unstated", "latin")
            key = (s["province"], tambon, script, v["kind"], offer, _band(v["bedrooms"], v["kind"]))
            cells.setdefault(key, []).append((v["thb"], o["at"], oid))
        pub, withheld_cells, withheld_props = [], 0, 0
        for key in sorted(cells):
            pts = cells[key]
            if len(pts) < MIN_CELL:
                withheld_cells += 1
                withheld_props += len(pts)
                for _p, _a, oid in pts:
                    self.went(oid, PRICES, "withheld", f"cell holds {len(pts)} < {MIN_CELL}")
                continue
            prices = sorted(p for p, _a, _o in pts)
            q = statistics.quantiles(prices, n=4, method="inclusive")
            prov, tambon, script, kind, offer, band = key
            pub.append({"province": prov, "tambon": tambon, "tambon_script": script,
                        "kind": kind, "offer": offer, "bedrooms": band, "n": len(pts),
                        "median": round(statistics.median(prices)), "p25": round(q[0]),
                        "p75": round(q[2]), "from": min(a for _p, a, _o in pts),
                        "to": max(a for _p, a, _o in pts)})
            for _p, _a, oid in pts:
                self.went(oid, PRICES, "kept", f"in a cell of {len(pts)}")
        seen = {oid for oid, _o in latest.values()}
        for oid, o in self.price_obs:
            if oid not in seen:
                self.went(oid, PRICES, "declined", "an older price for a property counted once")
            if o["subject"]["id"] and o["ctx"]["housing"]:
                self.went(oid, BUILDINGS, "kept", "live offer ranges for the place page")
        return {"_readme": "Asking-price aggregates from the Listing Sheet, gleaned by "
                           "glean.py. A cell counts distinct properties at the latest price "
                           "a lister stood behind; rent is baht a month. Cells under min_n "
                           "are withheld and counted.",
                "min_n": MIN_CELL, "cells": pub,
                "withheld": {"cells": withheld_cells, "properties": withheld_props}}

    def settle_pictures(self):
        out = {}
        for oid, o in self.photo_obs:
            c, s = o["ctx"], o["subject"]
            lic = o["source"]["licence"]
            if not lic:
                # The lister join form records CC BY 4.0 consent and intake
                # stamps source.licence; a photo without it was sent for the
                # listing only.
                self.went(oid, PICTURES, "declined", "row carries no source.licence")
                continue
            if not (s["id"] and c["housing"]):
                self.went(oid, PICTURES, "declined", "no housing building to show it on")
                continue
            f = self.ctx.photos_dir / c["raw_id"] / o["value"]
            if not f.exists():
                self.went(oid, PICTURES, "declined", "file not in listing-sheet/photos")
                continue
            out.setdefault(s["id"], []).append(
                {"src": "https://motdang.net/listings/photos/%s/%s" % (c["raw_id"], o["value"]),
                 "credit": c["credit"], "licence": lic, "at": o["at"],
                 "listing": o["source"]["ref"]})
            self.went(oid, PICTURES, "kept", "licensed building picture")
            self.went(oid, BUILDINGS, "kept", "the place page shows it")
        for ref in out:
            uniq = {p["src"]: p for p in out[ref]}
            out[ref] = [uniq[k] for k in sorted(uniq)]
        return out

    def settle_buildings(self, gleaned, pictures):
        out = {}
        for g in self.ctx.groups:
            ref = g["property"].get("building_ref")
            if not ref or not self.ctx.housing_class(ref):
                continue
            b = out.setdefault(ref, {"name": g["property"].get("name"), "facts": {},
                                     "pictures": [], "offers": {
                                         "live": 0, "lapsed": 0, "sold": 0, "let": 0,
                                         "withdrawn": 0, "sale_thb": None,
                                         "rent_month_thb": None, "as_of": None}})
            off = b["offers"]
            off[g["status"]] = off.get(g["status"], 0) + 1
            asof = max(o["_as_of"] for o in g["offers"]).isoformat()
            off["as_of"] = max(off["as_of"] or asof, asof)
            if g["status"] == "live":
                for o in g["offers"]:
                    if o["_status"] != "live":
                        continue
                    k = "sale_thb" if o["offer"]["type"] == "sale" else "rent_month_thb"
                    p = o["offer"]["price_thb"]
                    lo, hi = off[k] or (p, p)
                    off[k] = [min(lo, p), max(hi, p)]
        for ref, fs in gleaned.items():
            if ref in out:
                out[ref]["facts"] = fs
        for ref, ps in pictures.items():
            if ref in out:
                out[ref]["pictures"] = ps
        return out

    def settle_review(self):
        rv = self.review
        rv["unbound_buildings"] = sorted(
            (dict(u, listings=sorted(u["listings"])) for u in self._unbound.values()),
            key=lambda u: (u["province"], u["name"] or ""))
        rv["off_shelf_binds"] = sorted(
            (dict(e, listings=sorted(e["listings"])) for e in self._offshelf.values()),
            key=lambda e: e["record"])
        rv["agencies_off_shelf"] = sorted(
            (dict(a, provinces=sorted(p for p in a["provinces"] if p))
             for a in self._agencies.values()), key=lambda a: a["slug"])
        import translit
        pairs = []
        for p in self._pairs.values():
            reading = translit.title(p["thai"])
            pairs.append(dict(p, buildings=sorted(p["buildings"]), reading=reading,
                              evidence=sorted(p["evidence"]),
                              reading_agrees=_fold(reading) == _fold(p["latin"])))
        rv["tambon_pairs"] = sorted(pairs, key=lambda p: (p["province"], p["thai"], p["latin"]))
        rv["brand_candidates"] = sorted(
            (dict(b, buildings=sorted(b["buildings"]), listing_names=sorted(b["listing_names"]))
             for b in self._brands.values()), key=lambda b: (b["thai"], b["sign"]))
        rv["conflicts"].sort(key=lambda c: (c["building"], c["field"]))
        rv["lister_disagreements"].sort(key=lambda c: (c["building"], c["field"]))
        return rv


# ---------------------------------------------------------------- run


def run(ctx, sources=("listings", "claims"), dry_run=False):
    router = Router(ctx)
    n_obs = {}
    for name in sources:
        for o in ADAPTERS[name](ctx):
            n_obs[name] = n_obs.get(name, 0) + 1
            router.route(o)
    gleaned = router.settle_facts()
    prices = router.settle_prices()
    pictures = router.settle_pictures()
    buildings = router.settle_buildings(gleaned, pictures)
    review = router.settle_review()
    for oid in router.obs:
        if oid not in router.outcomes:
            router.went(oid, LISTING, "kept", "no destination took it")
    result = {"observations": n_obs, "facts": gleaned, "prices": prices,
              "pictures": pictures, "buildings": buildings, "review": review,
              "router": router}
    result["written"] = [] if dry_run else write_all(ctx, result)
    return result


def ledger_lines(ctx, router):
    lines = []
    for oid in sorted(router.obs):
        o = router.obs[oid]
        lines.append({"obs": oid, "logged": ctx.today, "source": o["source"],
                      "subject": {k: o["subject"].get(k) for k in ("kind", "id", "name", "province")},
                      "field": o["field"], "value": o["value"], "at": o["at"],
                      "went": sorted(router.outcomes.get(oid, []),
                                     key=lambda w: (w["to"], w["result"], w["why"]))})
    return lines


def _ledger_key(line):
    return json.dumps([line["obs"], line["went"]], sort_keys=True, ensure_ascii=False)


def write_all(ctx, res):
    rows = ctx.rows
    if any(is_sample(r) for r in rows):
        if not ctx.sample or _inside(ctx.out_dir, ROOT) or _inside(ctx.incoming_dir, ROOT) \
                or _inside(ctx.facts_out, ROOT):
            raise SampleRowRefused("invented sample rows may be written only by --sample "
                                   "into a scratch dir outside mot-dang")
    written = []
    readme = ("Building facts stated by listers on the Listing Sheet, gleaned by glean.py. "
              "facts.load_all() merges this with facts.json; a value that disagrees with "
              "the record went to _incoming/glean-review-*.json instead.")
    for path, obj in (
            (ctx.facts_out, {"_readme": readme, "facts": res["facts"]}),
            (ctx.out_dir / "prices.json", res["prices"]),
            (ctx.out_dir / "pictures.json", res["pictures"]),
            (ctx.out_dir / "buildings.json", res["buildings"])):
        if _write_if_changed(path, _dump(obj)):
            written.append(str(path))
    rv = res["review"]
    if any(rv.values()):
        p = ctx.incoming_dir / f"glean-review-{ctx.today}.json"
        if _write_if_changed(p, _dump(dict(rv, _readme=(
                "For a person. Nothing here is applied by glean.py. Confirmed tambon pairs "
                "go to data/curated/tambon_pairs.json {\"pairs\": {\"<prov>|<folded latin>\": "
                "\"<thai>\"}}; brand spellings to rtgs_lexicon.json `brand`.")))):
            written.append(str(p))
    lp = ctx.out_dir / "ledger.jsonl"
    have = set()
    if lp.exists():
        for ln in lp.read_text(encoding="utf-8").splitlines():
            try:
                have.add(_ledger_key(json.loads(ln)))
            except ValueError:
                pass
    new = [ln for ln in ledger_lines(ctx, res["router"]) if _ledger_key(ln) not in have]
    if new:
        lp.parent.mkdir(parents=True, exist_ok=True)
        with open(lp, "a", encoding="utf-8") as fh:
            for ln in new:
                fh.write(json.dumps(ln, ensure_ascii=False, sort_keys=True, default=str) + "\n")
        written.append(f"{lp} (+{len(new)})")
    res["ledger_new"] = len(new)
    return written


def summary(ctx, res):
    r = res["router"]
    counts = {}
    for outs in r.outcomes.values():
        for w in outs:
            k = (w["to"], w["result"])
            counts[k] = counts.get(k, 0) + 1
    rv = res["review"]
    nf = sum(len(v) for v in res["facts"].values())
    out = [f"glean · {ctx.today} · listings from {ctx.listings_dir}"
           + (" (INVENTED SAMPLES, scratch only)" if ctx.sample else "")]
    out.append(f"  rows {len(ctx.rows)} · refused {len(ctx.faults)} by sheet.load_one"
               f" · sample rows refused {ctx.refused_samples}")
    out.append("  observations  " + " · ".join(f"{k} {v}" for k, v in res["observations"].items()))
    out.append(f"  facts         {nf} field(s) on {len(res['facts'])} building(s)")
    out.append(f"  prices        {len(res['prices']['cells'])} cell(s) · withheld "
               f"{res['prices']['withheld']['cells']} cell(s) / "
               f"{res['prices']['withheld']['properties']} propert(ies) under n={MIN_CELL}")
    out.append(f"  pictures      {sum(len(v) for v in res['pictures'].values())} on "
               f"{len(res['pictures'])} building(s) · "
               f"{counts.get((PICTURES, 'declined'), 0)} photo(s) declined")
    out.append(f"  buildings     {len(res['buildings'])} summar(ies)")
    out.append("  review        " + " · ".join(f"{k} {len(v)}" for k, v in rv.items()))
    out.append("  outcomes      " + " · ".join(f"{t}/{s} {n}" for (t, s), n in sorted(counts.items())))
    whys = {}
    for outs in r.outcomes.values():
        for w in outs:
            k = (w["to"], w["result"], w["why"])
            whys[k] = whys.get(k, 0) + 1
    out += [f"    {n:>4}  {t}/{s}: {y}" for (t, s, y), n in sorted(whys.items())]
    if res.get("written"):
        out += ["  wrote " + w for w in res["written"]]
    else:
        out.append("  wrote nothing")
    return "\n".join(out)


def load_records():
    recs = []
    for prov in ("cm", "cr"):
        p = ROOT / "data" / "canonical" / f"{prov}.json"
        if p.exists():
            recs += json.loads(p.read_text(encoding="utf-8"))
    return recs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--source", choices=sorted(ADAPTERS), action="append")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--sample", action="store_true",
                    help="read listing-sheet samples/ and write to a scratch dir")
    ap.add_argument("--listings", help="listings dir (default listing-sheet/listings)")
    ap.add_argument("--out", help="scratch dir for --sample")
    ap.add_argument("--no-register", action="store_true",
                    help="bind against nothing (fast; everything unbound)")
    a = ap.parse_args(argv)
    listings = Path(a.listings or os.environ.get("GLEAN_LISTINGS")
                    or LS_ROOT / ("samples" if a.sample else "listings"))
    if a.sample:
        scratch = Path(a.out or Path(tempfile.gettempdir()) / "glean-sample")
        if _inside(scratch, ROOT):
            raise SampleRowRefused(f"--out {scratch} is inside mot-dang; samples go to scratch")
        out, inc, cur = scratch / "gleaned", scratch / "_incoming", scratch / "curated"
    else:
        out, inc, cur = ROOT / "data" / "gleaned", ROOT / "_incoming", ROOT / "data" / "curated"
    records = [] if a.no_register else load_records()
    ctx = Context(records, listings, out, inc, curated_dir=ROOT / "data" / "curated",
                  sample=a.sample)
    ctx.facts_out = cur / facts.GLEANED_FILE
    res = run(ctx, tuple(a.source or ("listings", "claims")), dry_run=a.dry_run)
    print(summary(ctx, res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
