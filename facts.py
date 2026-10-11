"""Reader-supplied facts: typed fields that reach the record.

Nan, 2026-09-06: "It should be MUCH MUCH easier to add information, have the
bots accept it, and integrate FULLY into the site."

Until tonight a reader's fact was free text in a queue a person read, then
retyped by hand into data/curated/. This module is the typed path:

  suggest.html (a field + a value, from the missing-field drawer)
    → POST /suggest, `what` = "fact:" + {"field","value","note"}
    → importers/sync_suggestions.py brings the queue down (wrangler)
    → importers/apply_facts.py shows the queue as a numbered menu; a person
      approves by number → data/curated/facts.json
    → apply() below puts the field ON THE RECORD — from import_all.py (into
      canonical) and again at build time (so a build without an import still
      carries it). Idempotent: applying twice changes nothing.

Every applied field carries provenance {source: "reader:suggest", how:
"stated", at: date} and a `sources[]` entry to match, so provenance.py's
validator and the give-back gate both see it for what it is. The page shows
a badge: from a reader, checked <date>. Nothing here publishes without the
approval step; a stranger's fact about somebody else's shop is read by a
person first, as the suggestion queue has always been.
"""
import json
import re
from datetime import date

PREFIX = "fact:"
SOURCE = {"type": "reader", "via": "suggest", "ref": "suggest.html"}
SOURCE_KEY = "reader:suggest"

# field -> (where it lives, validator). The validator returns the cleaned
# value or None; None is a rejection the CLI shows and never applies.
_PHONE = re.compile(r"^\+?\d[\d\s\-()]{6,}\d$")


def _phone(v):
    v = v.strip()
    digits = re.sub(r"[^\d+]", "", v)
    if not _PHONE.match(v) or len(re.sub(r"\D", "", digits)) < 9:
        return None
    return digits


def _line(v):
    v = v.strip().lstrip("@")
    return v if re.match(r"^[A-Za-z0-9._\-]{2,40}$", v) else None


def _hours(v):
    v = " ".join(v.split())
    return v if 3 <= len(v) <= 200 else None


def _url(v):
    v = v.strip()
    if not v:
        return None
    if not re.match(r"^https?://", v, re.I):
        v = "https://" + v
    return v if re.match(r"^https?://[^\s/]+\.[^\s/]+", v) else None


def _pin(v):
    m = re.match(r"^\s*(-?\d{1,2}\.\d{3,})\s*[, ]\s*(-?\d{1,3}\.\d{3,})\s*$", v)
    if not m:
        return None
    lat, lng = float(m.group(1)), float(m.group(2))
    # northern Thailand (data/coverage.json, Nan 2026-09-29); anything else is
    # a typo or a joke
    if not (14.8 <= lat <= 20.6 and 97.3 <= lng <= 101.8):
        return None
    return [lat, lng]


def _tags(v):
    tags = [t.strip() for t in re.split(r"[,、·;\n]+", v) if t.strip()]
    tags = [t[:60] for t in tags][:8]
    return tags or None


FIELDS = {
    "phone": ("phone", _phone),
    "line": ("attrs.lineId", _line),
    "hours": ("hours", _hours),
    "website": ("website", _url),
    "pin": ("lat,lng", _pin),
    "tags": ("attrs.tradeTags", _tags),
}


# Building fields, gleaned from what listers send (glean.py). They sit in
# their own table rather than in FIELDS because parse() offers FIELDS to the
# reader suggest form, and widening what a reader can type is a form change
# this module does not make on its own.
def _text(v):
    v = " ".join(str(v).split())
    return v if 2 <= len(v) <= 120 else None


def _year(v):
    # listing-sheet facets.NUMERIC starts year_built at 1900; the ceiling lets a
    # building still under construction state the year it completes.
    try:
        y = int(str(v).strip())
    except ValueError:
        return None
    return y if 1900 <= y <= date.today().year + 5 else None


def _storeys(v):
    # listing-sheet facets.NUMERIC caps `floors` at 60 for the same reason:
    # nothing in either province stands higher, so a bigger number is a typo.
    try:
        n = int(str(v).strip())
    except ValueError:
        return None
    return n if 1 <= n <= 60 else None


def _codes(v):
    items = v if isinstance(v, list) else re.split(r"[,\s]+", str(v))
    items = [str(x).strip() for x in items if str(x).strip()]
    ok = [x for x in items if re.match(r"^[a-z][a-z0-9_]{1,30}$", x)]
    return sorted(set(ok)) if ok and len(ok) == len(items) else None


def _short_lets(v):
    v = str(v).strip()
    return v if v in ("allowed", "not_allowed") else None


def _quota(v):
    # A quota statement is only worth holding with its date: the juristic
    # office's register changes with every sale (facets.FOREIGN_QUOTA).
    if isinstance(v, dict):
        status, as_of = v.get("status"), str(v.get("as_of") or "")
    else:
        m = re.match(r"^\s*(open|full)\s+(\d{4}-\d{2}-\d{2})\s*$", str(v))
        status, as_of = (m.group(1), m.group(2)) if m else (None, "")
    if status not in ("open", "full") or not re.match(r"^\d{4}-\d{2}-\d{2}$", as_of):
        return None
    return {"status": status, "as_of": as_of}


BUILDING_FIELDS = {
    "juristic_name": ("attrs.juristicName", _text),
    "juristic_phone": ("attrs.juristicPhone", _phone),
    "year_built": ("attrs.yearBuilt", _year),
    # attrs.buildingLevels is where the OSM import already keeps building:levels
    # (88 real-estate records, 2026-09-27), so a lister's count meets it there.
    "storeys": ("attrs.buildingLevels", _storeys),
    "amenities": ("attrs.buildingAmenities", _codes),
    "short_lets": ("attrs.shortLets", _short_lets),
    "foreign_quota": ("attrs.foreignQuota", _quota),
}
ALL_FIELDS = dict(FIELDS, **BUILDING_FIELDS)


def parse(suggestion):
    """A queue row → {placeId, field, value, note, suggestion, at} or None.

    None means: not a typed fact, or a fact that failed its validator — the
    CLI prints those so a person can answer the reader, never applies them.
    """
    what = (suggestion.get("what") or "").strip()
    if not what.startswith(PREFIX) or not suggestion.get("placeId"):
        return None
    try:
        body = json.loads(what[len(PREFIX):])
    except ValueError:
        return {"error": "not JSON", "raw": what[:80], "suggestion": suggestion.get("id")}
    field = body.get("field")
    spec = FIELDS.get(field)
    if not spec:
        return {"error": f"unknown field {field!r}", "suggestion": suggestion.get("id")}
    value = spec[1](str(body.get("value") or ""))
    if value is None:
        return {"error": f"{field}: value did not validate", "raw": str(body.get("value"))[:80],
                "suggestion": suggestion.get("id"), "placeId": suggestion["placeId"]}
    return {"placeId": suggestion["placeId"], "field": field, "value": value,
            "note": (body.get("note") or "")[:300], "suggestion": suggestion.get("id"),
            "at": (suggestion.get("createdAt") or "")[:10]}


def current(record, field):
    """What the record holds for a field right now, for the menu's 'was'."""
    if field == "line":
        return (record.get("attrs") or {}).get("lineId") or ""
    if field == "pin":
        return [record.get("lat"), record.get("lng")] if record.get("lat") is not None else ""
    if field == "tags":
        return list((record.get("attrs") or {}).get("tradeTags") or [])
    if field in BUILDING_FIELDS:
        v = (record.get("attrs") or {}).get(BUILDING_FIELDS[field][0].split(".", 1)[1])
        if field == "storeys" and v not in (None, ""):
            # OSM writes building:levels as a string ("2")
            return BUILDING_FIELDS[field][1](v) or v
        return v if v not in (None, "") else ""
    return record.get(field) or ""


def _source_of(fact):
    """(provenance key, sources[] entry, date-map attr) for one fact.

    A fact with no `source` is a reader's (the suggest path). A gleaned fact
    names its own, e.g. "lister:ping-valley-property", and its date lands in
    attrs.gleanedFacts so build.py's "from a reader" badge does not claim it.
    """
    key = fact.get("source") or SOURCE_KEY
    if key == SOURCE_KEY:
        return key, dict(SOURCE), "readerFacts"
    kind, _, via = key.partition(":")
    return key, {"type": kind, "via": via, "ref": fact.get("ref") or ""}, "gleanedFacts"


def apply(records, doc, today=None):
    """Put approved facts on the records. Returns the number of fields set.

    `doc` is data/curated/facts.json: {"facts": {placeId: {field: {"value",
    "at", "suggestion"}}}}, or gleaned_facts.json in the same shape with a
    `source` and `ref` on each fact. Idempotent — a field already carrying
    this value with the same provenance is left alone.

    A gleaned fact that meets a different value already on the record, one no
    earlier gleaned fact wrote, is skipped, not written over: glean.py sends that disagreement to a person
    (_incoming/glean-review-*.json), and a record can change between a glean
    and a build.
    """
    today = today or date.today().isoformat()
    facts = (doc or {}).get("facts") or {}
    if not facts:
        return 0
    by_id = {r["id"]: r for r in records}
    n = 0
    for pid, fields in facts.items():
        r = by_id.get(pid)
        if not r:
            continue
        for field, fact in fields.items():
            if field not in ALL_FIELDS:
                continue
            value = fact.get("value")
            at = (fact.get("at") or today)[:10]
            key, src_entry, datemap = _source_of(fact)
            gleaned = datemap == "gleanedFacts"
            a = r.setdefault("attrs", {})
            old = current(r, field)
            # a value an earlier gleaned fact put there may be updated by a later one
            ours = bool((a.get("gleanedFacts") or {}).get(field))
            if gleaned and old and old != value and field != "amenities" and not ours:
                continue
            rf = a.setdefault(datemap, {})
            stamp = at if not gleaned else {"at": at, "source": key}
            if rf.get(field) == stamp and (old == value or (
                    field == "amenities" and set(value) <= set(old or []))):
                continue
            if old and old != value and not gleaned:
                a.setdefault("_replaced", {})[field] = old
            if field == "line":
                a["lineId"] = value
            elif field == "pin":
                r["lat"], r["lng"] = value
                r["geoPrecision"] = "approx"
                a["pinVia"] = "lister-supplied" if gleaned else "reader-supplied"
            elif field == "tags":
                a["tradeTags"] = list(dict.fromkeys(list(a.get("tradeTags") or []) + value))
            elif field == "amenities":
                a["buildingAmenities"] = sorted(set(a.get("buildingAmenities") or []) | set(value))
            elif field in BUILDING_FIELDS:
                a[BUILDING_FIELDS[field][0].split(".", 1)[1]] = value
            else:
                r[field] = value
            rf[field] = stamp
            # provenance for the tracked fields; a sources[] entry so the key resolves
            prov = r.setdefault("provenance", {})
            for pf in {"phone": ["phone"], "hours": ["hours"], "website": ["website"],
                       "pin": ["lat", "lng"]}.get(field, []):
                prov[pf] = {"source": key, "how": "stated", "at": at}
            srcs = r.setdefault("sources", [])
            if not any((s.get("type") == src_entry["type"] and s.get("via") == src_entry["via"])
                       for s in srcs):
                note = ("reader-submitted fact, approved by hand" if not gleaned
                        else "stated by a lister on the Listing Sheet, gleaned by glean.py")
                srcs.append(dict(src_entry, fetched=at, note=note))
            n += 1
    return n


def load_doc(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {"facts": {}}


GLEANED_FILE = "gleaned_facts.json"


def load_all(curated_dir):
    """facts.json (readers, approved by hand) and gleaned_facts.json (glean.py)
    as one doc for apply(). Both can speak about one place; on the same field
    the reader's approved fact is kept and the gleaned one is dropped here,
    because a person read the reader's."""
    from pathlib import Path
    d = Path(curated_dir)
    merged = {}
    for name in ("facts.json", GLEANED_FILE):
        for pid, fields in ((load_doc(d / name) or {}).get("facts") or {}).items():
            slot = merged.setdefault(pid, {})
            for field, fact in (fields or {}).items():
                slot.setdefault(field, fact)
    return {"facts": merged}
