#!/usr/bin/env python3
"""THE SECOND AXIS — what a place IS, beside `cat`, which is what it SELLS.

Nan, 2026-09-06, on being shown that Mot Dang admits a place by its counter:
"this is flat wrong. This is not how motdang should find/choose/show data."
She is right, and it was not an attitude — it was three functions in build.py:
place_has_substance() (phone|LINE|hours|web|photo|claimed|address, else
noindex, which 10,449 of 24,059 records fail), the nine ants (4 of 9 a way to
contact a seller, none asking what a place holds or who may use it), and
held() (no pin and two SHOP facts or fewer: out of the ranked index).

The rule she adopted in their place, 2026-09-06:

    ADMITTED  when a source lets us say it exists and what it is for.
    PUBLISHED when the record ANSWERS A QUESTION SOMEONE COULD ASK OF THAT
              KIND OF PLACE.

That second sentence is what this module makes computable. A phone number is
the answer a noodle stall owes. A wat owes its sect, its founding and its
name in the register — 562 wats hold exactly that and are noindex today for
want of a telephone. A reading room owes what it holds and whether you may
walk in. Judging all of them by the shop's answer is the counter rule.

Nothing in data/canonical is rewritten. `kind` is derived here from
data/curated/kinds.json and stamped onto the record in memory; a curated
record that states its own top-level `kind` wins over every rule. `attrs.kind`
is a different thing that was here first — 180 free-text trade glosses — and
is not touched.

    import kind_layer
    kind_layer.load(ROOT)          # once, at the top of a build
    kind_layer.stamp(records)      # sets r["kind"] = [...]
    kind_layer.answers(r)          # the fields that would answer for this kind
    kind_layer.answered(r, bits)   # does it answer anything at all?
"""
import json
import re

DOC = {}
_RULES = []          # (kind, predicate, why)
_ANSWERS = {}
KINDS = {}
UNCLASSIFIED = "unclassified"


def load(ROOT):
    """Read the taxonomy. Idempotent; safe to call from every layer."""
    global DOC, KINDS, _ANSWERS, _RULES
    if _RULES:
        return DOC
    DOC = json.loads((ROOT / "data" / "curated" / "kinds.json").read_text())
    KINDS = DOC["kinds"]
    _ANSWERS = DOC["answers"]
    _RULES = [(r["kind"], _compile(r), r.get("why", "")) for r in DOC["rules"]]
    return DOC


def _compile(rule):
    """One rule → one predicate. Every clause is a NARROWING; a rule with no
    clause would claim the whole corpus, so it is refused at load rather than
    quietly mislabelling 24,000 records."""
    cats = set(rule.get("cat") or [])
    cats_not = set(rule.get("cat_not") or [])
    subs = set(rule.get("sub") or [])
    subs_not = set(rule.get("sub_not") or [])
    name = re.compile(rule["name"], re.I) if rule.get("name") else None
    name_not = re.compile(rule["name_not"], re.I) if rule.get("name_not") else None
    attr = rule.get("attr")
    if not (cats or subs or name or attr):
        raise ValueError("kinds.json: a rule with no clause would claim everything: %r" % rule)

    def pred(r, text):
        rcat = set(r.get("cat") or [])
        if cats and not (cats & rcat):
            return False
        # A shelf can hold a name out where no word in the name could: "Slee
        # Banyan" is a restaurant and nothing it is called says so.
        if cats_not and (cats_not & rcat):
            return False
        rsub = set(r.get("sub") or [])
        if subs and not (subs & rsub):
            return False
        if subs_not and (subs_not & rsub):
            return False
        if attr and (r.get("attrs") or {}).get(attr) in (None, "", [], {}):
            return False
        if name and not name.search(text):
            return False
        if name_not and name_not.search(text):
            return False
        return True
    return pred


def _text(r):
    return " ".join(str(r.get(k) or "") for k in ("name", "nameTh", "nameEn"))


def kinds_of(r):
    """Every kind this record answers to, in rule order. A place can be more
    than one: the wat with a cremation ground is wat AND memory, and a reader
    looking for either should find it."""
    stated = r.get("kind")
    if stated:
        return list(stated) if isinstance(stated, list) else [stated]
    text = _text(r)
    out = []
    for kind, pred, _why in _RULES:
        if kind not in out and pred(r, text):
            out.append(kind)
    return out or [UNCLASSIFIED]


def stamp(records):
    """Set r['kind'] in place. Returns a count per kind, for the build log."""
    tally = {}
    for r in records:
        ks = kinds_of(r)
        r["kind"] = ks
        for k in ks:
            tally[k] = tally.get(k, 0) + 1
    return tally


def answers(r):
    """The answer-set for this record's FIRST kind — merged with any further
    kind it carries, because a place that is two things may answer as either."""
    got = {"fields": [], "attrs": [], "ants": [], "future": []}
    for k in (r.get("kind") or [UNCLASSIFIED]):
        a = _ANSWERS.get(k) or _ANSWERS[UNCLASSIFIED]
        for slot in got:
            for v in (a.get(slot) or []):
                if v not in got[slot]:
                    got[slot].append(v)
    return got


def says(r):
    """The bilingual sentence naming what this kind of place is asked. Shown to
    a reader beside an unanswered record, so 'we don't know yet' is specific:
    a wat is missing its sect, not its telephone."""
    for k in (r.get("kind") or []):
        a = _ANSWERS.get(k)
        if a and a.get("say_en"):
            return a.get("say_th", ""), a["say_en"]
    a = _ANSWERS[UNCLASSIFIED]
    return a.get("say_th", ""), a.get("say_en", "")


def answered(r, bits=None):
    """THE SECOND GATE. True if this record answers a question its own kind
    invites. Replaces place_has_substance()'s seven ways to contact a seller.

    `bits` is build.py's ant_bits(r) when there is one — photo and
    owner-confirmed live nowhere else. Without it the test falls back to the
    record's own fields and attrs, which is what every other caller has.
    """
    want = answers(r)
    for f in want["fields"]:
        if r.get(f) not in (None, "", [], {}):
            return True
    attrs = r.get("attrs") or {}
    for a in want["attrs"]:
        if attrs.get(a) not in (None, "", [], {}):
            return True
    for f in want["future"]:          # holds/access/parent — ready before they land
        if r.get(f) not in (None, "", [], {}):
            return True
    if bits:
        for a in want["ants"]:
            if bits.get(a):
                return True
    return False


# ── the nine ants, re-cut ────────────────────────────────────────────────
# Five slots are universal; four are the kind's own. See kinds.json _ants_doc.
UNIVERSAL_ANTS = ["nameTh", "nameEn", "photo", "claimed", "fresh"]


def ant_slots(r):
    """The four kind-slots for this record, as [(key, th, en)…].

    A record carrying two kinds is asked as its FIRST kind — the wat with a
    cremation ground is asked for its sect, not for who keeps the graves, and
    a strip that changed shape depending on which of two lists you arrived
    from would be unreadable."""
    for k in (r.get("kind") or []):
        got = (DOC.get("ant_slots") or {}).get(k)
        if got:
            return [tuple(s) for s in got]
    return [tuple(s) for s in DOC["ant_slots"][UNCLASSIFIED]]


def slot_value(r, key, bits=None):
    """Is this slot filled? `bits` carries the four channel-resolved ant keys
    (phone·line·hours·web) and photo/claimed/fresh, which only build.py can
    compute — a website that 404s is not a website."""
    for one in key.split("|"):
        one = one.strip()
        if one.startswith("attrs."):
            if (r.get("attrs") or {}).get(one[6:]) not in (None, "", [], {}):
                return True
        elif bits is not None and one in bits:
            if bits[one]:
                return True
        elif r.get(one) not in (None, "", [], {}):
            return True
    return False
