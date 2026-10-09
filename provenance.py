#!/usr/bin/env python3
"""🧾 Per-field provenance — which source gave us THIS fact.

WHY THIS EXISTS
---------------
`sources[]` says where a RECORD came from. Nothing has ever said where a FIELD
came from, and two jobs need exactly that:

  * The OSM give-back (go/osm-gate). OpenStreetMap asks its question one tag at
    a time: what is the source of this phone number. For a record carrying an
    OSM source AND a scraped directory we cannot answer, so 373 records that
    are almost certainly ours to give sit blocked behind 3,303 that are not.
    Record-level provenance makes an honest contributor look like a careless
    one.
  * `offers[]` (Phase 3 of the cure plan). An offer is a claim that a shop
    DOES something, and a claim without a receipt is a rumour. The whole point
    of the offers array is that each item carries where it came from.

Both want the same sentence — "this fact, from that source, in this way" — so
they get one grammar rather than two.

THIS IS NOT A NEW IDEA IN THIS REPO, IT IS AN EXISTING ONE FINISHED
------------------------------------------------------------------
The house already does per-field provenance twice, ad hoc:

  * the pin carries `attrs.pinSource`, `attrs.pinVia`, `attrs.pinFrom` and
    `attrs.pinUncertaintyM` — a full receipt for one field, because that is
    the field somebody got burned on;
  * `facet_bits()` returns `{key: provenance}` rather than a flat true, "so a
    consumer can weigh 'someone stood there' against 'a point sits 22 m away'".

Both were built the same way for the same reason, for one field each. This
generalises them instead of adding a third dialect.

THE SHAPE
---------
    record["provenance"] = {
      "phone": {"source": "opendata:data.go.th", "how": "stated",   "at": "2026-08-20"},
      "hours": {"source": "web:venue-site",      "how": "stated",   "at": "2026-08-19"},
      "lat":   {"source": "derived:curated-pins","how": "inferred", "at": "2026-09-05"},
      "sub":   {"source": "curated:shelves.json","how": "derived",  "at": "2026-09-05"},
    }

`source` is a stable KEY, not an index into `sources[]`. An index looked
tempting and is a trap: `apply_*` passes append to that list after the merge,
so an index written on Tuesday points at a different source on Wednesday. The
key survives reordering, deduplication and a re-import.

THE THREE GRADES, AND WHY THREE
-------------------------------
  stated    the source said this field, in these words. A register printed the
            address; the shop's own page printed the hours.
  derived   we computed it from something the source stated. A shelf read off
            a name is derived: อาหารตามสั่ง in the name → food/made-to-order.
            Nothing was invented, but the source never said the shelf.
  inferred  we filled it within stated bounds and could be wrong. A pin
            geocoded from a written address is the whole example.

Only `stated` is ever giveable to OpenStreetMap. `derived` is our reading and
`inferred` is our guess, and neither is a fact somebody else surveyed. That
distinction is the entire safety mechanism here, so it is one word per field
rather than a paragraph somebody has to remember.

ABSENCE IS ABSENCE — CARRIED IN
-----------------------------------------------
A field with no entry in `provenance` has UNKNOWN provenance. It does not mean
"ours", it does not mean "OSM", and it must never be read as either. Every
consumer here fails closed: `giveable()` returns False for a field it cannot
account for, because the cost of a wrong False is one record left at home and
the cost of a wrong True is an upload we cannot defend.
"""

from __future__ import annotations

# ------------------------------------------------------------------ grades

STATED = "stated"
DERIVED = "derived"
INFERRED = "inferred"
GRADES = (STATED, DERIVED, INFERRED)

# The fields provenance is kept for. Deliberately not "every key on the
# record": `id`, `province` and `slug` are ours by construction and a
# provenance entry for them would be noise pretending to be rigour.
TRACKED = (
    "name", "nameTh", "nameEn", "phone", "website", "hours", "address",
    "lat", "lng", "cat", "sub", "tags", "blurb_th", "blurb_en", "offers",
    # Where the place stands administratively. These live under `attrs`, not on
    # the record, so `unaccounted()` will never name them — they are here so
    # that derive.py can stamp a receipt for a field it wrote, which is the
    # whole point of the table. None of them can ever be giveable: everything
    # that writes them writes DERIVED, and `giveable()` requires STATED.
    "amphoe", "tambon", "postcode", "road", "soi",
    # 2026-09-10 — derive.apply_riverside: the pin within reach of a river line (OSM).
    "riverside",
)

# The subset of TRACKED that lives under `attrs`. Anything asking "does the
# record actually hold this field" has to look in both places or it reads a
# perfectly good value as absent — which is what `validate()` was doing to
# 59,719 receipts before 2026-09-08.
ATTRS_HELD = ("amphoe", "tambon", "postcode", "road", "soi", "riverside")


def held(record: dict, field: str):
    """The value the record holds for `field`, wherever that field lives."""
    if field in ATTRS_HELD:
        return (record.get("attrs") or {}).get(field)
    return record.get(field)

# ------------------------------------------------------------------ classes

# What KIND of source this is, which is the question both consumers actually
# ask. Kept here so the answer is computed once rather than re-derived by each
# caller — it was written twice in one afternoon before this file existed, and
# the two copies had already begun to disagree about `directory`.
OSM = "osm"            # already in OpenStreetMap; nothing to give back
GOV = "gov"            # a Thai state register or open-data set
OURS = "ours"          # our own curation, survey or field work
VENUE = "venue"        # the place's own published words
# NOT_GIVEABLE is about ONE destination: OpenStreetMap. It does not mean the
# data is unusable, unpublishable, or off limits anywhere else — everything in
# this class is on motdang.net and in the public Hugging Face export. It means
# an OSM import review would refuse it, and it covers two different situations
# that happen to have the same answer there:
#
#   * a licence that is perfectly good and is not ODbL. Overture is
#     CDLA-Permissive 2.0 and 99% of its rows are Meta's; relicensing that into
#     OSM is not ours to do.
#   * a commercial directory we read. Their compilation, their terms.
#
# Read it as "not giveable to OSM", never as "forbidden".
NOT_GIVEABLE = "not-giveable-to-osm"
UNKNOWN = "unknown"

# Hosts and vias that put a source in NOT_GIVEABLE whatever else it carries.
# The second situation above: reading them to build our own directory is one
# thing, and pushing their work into somebody else's database under a licence
# they never chose is another.
NOT_GIVEABLE_VIA = (
    "weed.th", "yellowpages", "cmhy", "lemon8", "salehere", "thailandnomads",
    "thaisisterhood", "northspace", "google", "tripadvisor", "wongnai",
    "gowabi", "agoda", "booking.com", "foursquare",
)


def source_key(src: dict) -> str:
    """A stable key for one entry of `sources[]`.

    `type:via`, falling back to the ref's host when a source states no via.
    Two sources that mean the same thing must produce the same key or the
    provenance table will quietly hold two names for one origin.
    """
    t = (src.get("type") or "?").strip().lower()
    via = (src.get("via") or "").strip()
    if not via:
        ref = (src.get("ref") or "").strip()
        if "//" in ref:
            via = ref.split("//", 1)[1].split("/", 1)[0]
        else:
            via = ref[:60] or "?"
    return f"{t}:{via}"


def source_class(src: dict) -> str:
    """osm | gov | ours | venue | not-giveable-to-osm | unknown, for one source.

    The order of the tests is the policy: NOT_GIVEABLE is checked before
    anything else, so a record that is OSM-derived AND read off a directory
    answers not-giveable rather than osm. Failing towards the stricter answer
    is the only safe direction when the two disagree.
    """
    t = (src.get("type") or "").strip().lower()
    hay = f"{src.get('via') or ''} {src.get('ref') or ''}".lower()
    if any(f in hay for f in NOT_GIVEABLE_VIA):
        return NOT_GIVEABLE
    # `directory` is the type Overture carries, and Overture is 96% of what
    # this line catches. Its licence is fine and it is not ODbL; see the
    # NOT_GIVEABLE comment for why those are different sentences.
    if t == "directory":
        return NOT_GIVEABLE
    if t == "osm":
        return OSM
    if t in ("opendata", "register"):
        return GOV
    # Our own work, including somebody standing in the doorway. `field` is the
    # type twelve curated records already carry and the type the ops channel
    # produces; it fell through to UNKNOWN until 2026-09-07, which meant field
    # work ranked below a scrape and could not be given back — the exact
    # inversion this module exists to prevent.
    if t in ("curated", "derived", "field", "survey"):
        return OURS
    # The place's own published words, wherever it published them. `own-site`,
    # `own-facebook` and `official-site` are all in live use and all fell
    # through; the `own-` prefix is the repo saying first-hand out loud.
    if t in ("web", "social", "own-site", "own-facebook", "official-site") or t.startswith("own-"):
        return VENUE
    return UNKNOWN


def classes(record: dict) -> set:
    """Every source class present on a record."""
    return {source_class(s) for s in (record.get("sources") or [])}


def class_of_key(record: dict, key: str) -> str:
    """The class of the source a provenance entry names.

    Returns UNKNOWN when the key names no source the record carries — which
    happens after a merge drops a source, and is exactly the case that must
    not be read as permission.
    """
    for s in (record.get("sources") or []):
        if source_key(s) == key:
            return source_class(s)
    return UNKNOWN


# ------------------------------------------------------------------ writing


def stamp(record: dict, field: str, src, how: str, at: str = "") -> None:
    """Record that `field` came from `src`, in the manner `how`.

    `src` may be a source dict or a key already computed. Called at the moment
    a field is written — in an importer, in an `apply_*` pass, anywhere a
    value lands on a record. That is the only moment the answer is known for
    free; every later attempt to work it out is archaeology.

    First writer wins. A pass that overwrites a field it did not originate
    would otherwise erase the receipt for the value it replaced, and the
    common case — the curated overlay filling a gap the crawl left — is
    exactly that shape.
    """
    if how not in GRADES:
        raise ValueError(f"grade {how!r} is not one of {GRADES}")
    if field not in TRACKED:
        raise ValueError(f"{field!r} is not a tracked field; add it to TRACKED "
                         f"deliberately rather than by accident")
    table = record.setdefault("provenance", {})
    if field in table:
        return
    key = src if isinstance(src, str) else source_key(src)
    entry = {"source": key, "how": how}
    if at:
        entry["at"] = at
    table[field] = entry


def of(record: dict, field: str) -> dict | None:
    """The provenance entry for one field, or None when we do not know.

    None means UNKNOWN and never means anything else. Callers that treat a
    None as "ours" are the failure this module exists to prevent.
    """
    return (record.get("provenance") or {}).get(field)


# ------------------------------------------------------------------ reading


# Source classes whose LICENCE has been cleared for export. Empty of GOV on
# purpose: the DGA Open Government License reads as permitting it (go/osm-gate)
# but DGA has not been asked yet, and the letter that asks promises no upload
# before a reply (go/dga-letter). Add GOV here on the day that reply arrives,
# and not one hour earlier — this constant is the promise, held in code.
LICENCE_CLEARED = (OURS, VENUE)


def needs_licence_clearance(record: dict, field: str) -> bool:
    """True when provenance is fine but the licence question is still open.

    Split out from `giveable` because conflating them is how a promise gets
    broken by a helper function. These fields are not blocked by anything we
    did wrong; they are waiting on somebody else's letter.
    """
    entry = of(record, field)
    if not entry or entry.get("how") != STATED:
        return False
    if NOT_GIVEABLE in classes(record):
        return False
    return class_of_key(record, entry["source"]) not in LICENCE_CLEARED + (OSM,)


def giveable(record: dict, field: str) -> bool:
    """May this one field be contributed to OpenStreetMap TODAY?

    Five conditions, all of them necessary:

      1. We know where it came from. No entry means no.
      2. It is STATED. Our readings and our guesses are not somebody else's
         survey, and OSM asks for facts, not for our opinion of the facts.
      3. No source on the record is NOT_GIVEABLE — not this one, and not any
         other. That second half is the one worth being awkward about: a
         phone number honestly read off a venue's own page, sitting on a
         record that also carries a commercial directory, cannot be shown to
         have come from the first rather than the second — not to a reviewer,
         and not to us. It stays home.
      4. The source is not OSM. Handing OSM back its own tag is a round trip,
         not a gift, and it is how an import review learns to distrust the rest
         of the upload.
      5. The source's LICENCE is cleared — see LICENCE_CLEARED. Provenance
         answers "whose fact is this"; it does not answer "may we relicense
         it". A government register can be perfectly accounted for and still
         be waiting on a reply. `needs_licence_clearance()` names that set so
         it is visible rather than merely excluded.
    """
    entry = of(record, field)
    if not entry or entry.get("how") != STATED:
        return False
    if NOT_GIVEABLE in classes(record):
        return False
    return class_of_key(record, entry["source"]) in LICENCE_CLEARED


def giveable_fields(record: dict) -> list:
    """Every field on this record that clears `giveable`, in TRACKED order."""
    return [f for f in TRACKED if giveable(record, f)]


def waiting_on_licence(record: dict) -> list:
    """Fields held back only by an unanswered licence question."""
    return [f for f in TRACKED if needs_licence_clearance(record, f)]


def unaccounted(record: dict) -> list:
    """Fields the record holds that provenance cannot account for.

    The backlog, stated as a number rather than felt as a worry. A record with
    an empty list here is fully explained; the rest is the work.
    """
    return [f for f in TRACKED
            if record.get(f) not in (None, "", [], {}) and not of(record, f)]


# ------------------------------------------------------------------ checking


def validate(record: dict) -> list:
    """Every complaint about one record's provenance table, as plain strings.

    Used by tests/test_provenance.py and safe to call in a build: it reads and
    never writes. An empty list is a clean record.
    """
    out = []
    table = record.get("provenance") or {}
    if not isinstance(table, dict):
        return [f"{record.get('id')}: provenance is {type(table).__name__}, want dict"]
    keys = {source_key(s) for s in (record.get("sources") or [])}
    for field, entry in table.items():
        where = f"{record.get('id')}.{field}"
        if field not in TRACKED:
            out.append(f"{where}: not a tracked field")
        if not isinstance(entry, dict):
            out.append(f"{where}: entry is {type(entry).__name__}, want dict")
            continue
        if entry.get("how") not in GRADES:
            out.append(f"{where}: how={entry.get('how')!r} not in {GRADES}")
        if not entry.get("source"):
            out.append(f"{where}: no source")
        elif entry["source"] not in keys:
            # Not fatal on its own — a merge can drop a source — but it must
            # be visible, because `giveable` reads it as UNKNOWN and the field
            # silently stops being contributable.
            out.append(f"{where}: source {entry['source']!r} is not on the record")
        # Provenance for a field the record does not hold is a receipt for a
        # purchase nobody made. It is always a bug in whoever wrote it.
        if held(record, field) in (None, "", [], {}):
            out.append(f"{where}: provenance for an empty field")
    return out
