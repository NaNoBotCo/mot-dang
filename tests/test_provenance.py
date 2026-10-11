#!/usr/bin/env python3
"""🧾 The provenance contract, held by a test rather than by care.

Per-field provenance exists to answer one question safely: may this fact be
handed to somebody else. A module that answers it wrongly is worse than none,
because a wrong yes looks exactly like a right one and gets uploaded. So most
of what is checked here is REFUSAL, and every case below is a mistake that was
available to make while writing provenance.py.

Two halves. The unit half runs anywhere. The corpus half runs only when
data/canonical is present and SAYS SO when it is not — a green tick over an
absent corpus would be a lie about the thing being checked.

    python3 tests/test_provenance.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import provenance as P  # noqa: E402

failures = []
skipped = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}{'' if ok else ' — ' + detail}")
    if not ok:
        failures.append(label)


def raises(fn, *a, **k):
    try:
        fn(*a, **k)
    except ValueError:
        return True
    except Exception:
        return False
    return False


OSM_SRC = {"type": "osm", "via": "mot-dang overpass"}
GOV_SRC = {"type": "register", "via": "ONAB register",
           "ref": "https://data.go.th/dataset/onab_temples"}
VENUE_SRC = {"type": "web", "ref": "https://example-shop.co.th/"}
OURS_SRC = {"type": "curated", "via": "data/curated/shelves.json"}
DIRTY_SRC = {"type": "directory", "via": "weed.th"}


def rec(*sources, **fields):
    r = {"id": "t1", "province": "cm", "sources": list(sources)}
    r.update(fields)
    return r


def unit():
    print("classes")
    check("osm source reads as osm", P.source_class(OSM_SRC) == P.OSM)
    check("register reads as gov", P.source_class(GOV_SRC) == P.GOV)
    check("a venue's own page reads as venue", P.source_class(VENUE_SRC) == P.VENUE)
    check("curated reads as ours", P.source_class(OURS_SRC) == P.OURS)
    check("a commercial directory reads as not-giveable",
          P.source_class(DIRTY_SRC) == P.NOT_GIVEABLE)
    # The via is checked before the type is trusted: the type is ours to write
    # and the host is not.
    check("not-giveable beats a respectable-looking type",
          P.source_class({"type": "osm", "via": "cmhy import"}) == P.NOT_GIVEABLE,
          "a scraped source labelled osm was read as osm")
    check("a source with no via keys off its host",
          P.source_key({"type": "web", "ref": "https://shop.example.co.th/hours"})
          == "web:shop.example.co.th")

    print("writing")
    r = rec(VENUE_SRC, hours="09:00-21:00")
    P.stamp(r, "hours", VENUE_SRC, P.STATED, at="2026-08-19")
    check("stamp then read round-trips",
          P.of(r, "hours") == {"source": "web:example-shop.co.th",
                               "how": P.STATED, "at": "2026-08-19"})
    # The overlay that FILLS a gap must not erase the receipt for what was
    # there — and the common case is exactly that shape.
    r = rec(VENUE_SRC, OURS_SRC, phone="053 000 000")
    P.stamp(r, "phone", VENUE_SRC, P.STATED)
    P.stamp(r, "phone", OURS_SRC, P.DERIVED)
    check("first writer wins", P.of(r, "phone")["how"] == P.STATED)
    r = rec(VENUE_SRC, phone="1")
    check("stamp refuses an unknown grade", raises(P.stamp, r, "phone", VENUE_SRC, "probably"))
    check("stamp refuses an untracked field", raises(P.stamp, r, "vibes", VENUE_SRC, P.STATED))

    print("the gate")
    r = rec(VENUE_SRC, phone="053 000 000")
    check("unknown provenance is never giveable",
          P.of(r, "phone") is None and P.giveable(r, "phone") is False,
          "a field with no receipt was treated as ours")
    for how, want in ((P.STATED, True), (P.DERIVED, False), (P.INFERRED, False)):
        r = rec(VENUE_SRC, hours="x")
        P.stamp(r, "hours", VENUE_SRC, how)
        check(f"{how} is {'giveable' if want else 'NOT giveable'}",
              P.giveable(r, "hours") is want)
    # The awkward rule, and the one most likely to be softened later. The hours
    # came from the venue's own page and nothing is wrong with them — but the
    # record also carries a scraped directory, and we cannot DEMONSTRATE which
    # of the two gave the value. Not to a reviewer, not to ourselves.
    r = rec(VENUE_SRC, DIRTY_SRC, hours="09:00-21:00")
    P.stamp(r, "hours", VENUE_SRC, P.STATED)
    check("a dirty source anywhere on a record blocks a clean field",
          P.giveable(r, "hours") is False)
    r = rec(OSM_SRC, phone="053 000 000")
    P.stamp(r, "phone", OSM_SRC, P.STATED)
    check("OSM is never handed back its own tag", P.giveable(r, "phone") is False)
    # A register field is not blocked by anything we did; it is waiting on a
    # reply. Confusing the two means nobody can find what the reply unblocks.
    r = rec(GOV_SRC, address="123 Main")
    P.stamp(r, "address", GOV_SRC, P.STATED)
    check("a gov field waits on a licence rather than being refused",
          P.giveable(r, "address") is False
          and P.needs_licence_clearance(r, "address") is True
          and P.waiting_on_licence(r) == ["address"])
    # The letter to DGA promises no upload before a reply. LICENCE_CLEARED is
    # that promise; this is what stops it being kept by accident.
    check("LICENCE_CLEARED still holds the promise made to DGA",
          P.GOV not in P.LICENCE_CLEARED,
          "gov was cleared — only correct with DGA's reply in hand (go/dga-letter)")
    r = rec(VENUE_SRC, hours="x")
    r["provenance"] = {"hours": {"source": "web:somewhere-else.example", "how": P.STATED}}
    check("a key naming no source on the record is unknown, not permission",
          P.class_of_key(r, "web:somewhere-else.example") == P.UNKNOWN
          and P.giveable(r, "hours") is False)

    print("validate")
    r = rec(VENUE_SRC)
    r["provenance"] = {"hours": {"source": "web:example-shop.co.th", "how": P.STATED}}
    check("a receipt for a field that is not there is caught",
          any("empty field" in c for c in P.validate(r)))
    r = rec(VENUE_SRC, hours="09:00-21:00")
    P.stamp(r, "hours", VENUE_SRC, P.STATED)
    check("a clean record draws no complaint", P.validate(r) == [])


def corpus():
    canon = ROOT / "data" / "canonical"
    recs = []
    for p in ("cm", "cr"):
        f = canon / f"{p}.json"
        if f.exists():
            recs += json.loads(f.read_text())
    if not recs:
        msg = ("data/canonical absent or empty — THE CORPUS HALF DID NOT RUN. "
               "A pass above says nothing about what shipped.")
        print(f"  skip  {msg}")
        skipped.append(msg)
        return

    print(f"corpus ({len(recs):,} records)")
    bad = []
    for r in recs:
        bad += P.validate(r)
    check("corpus provenance validates", not bad,
          f"{len(bad)} complaint(s); first three: {bad[:3]}")

    # The catch that matters most, asserted over the whole corpus rather than
    # over a fixture: not one field on a scraped record may leave.
    leaked = [r["id"] for r in recs
              if P.NOT_GIVEABLE in P.classes(r) and P.giveable_fields(r)]
    check("no not-giveable record reports a giveable field", not leaked,
          f"{len(leaked)} leaked: {leaked[:3]}")

    notstated = [(r["id"], f) for r in recs for f in P.giveable_fields(r)
                 if P.of(r, f)["how"] != P.STATED]
    check("nothing derived or inferred is giveable", not notstated, str(notstated[:3]))

    give = sum(len(P.giveable_fields(r)) for r in recs)
    wait = sum(len(P.waiting_on_licence(r)) for r in recs)
    unacc = sum(len(P.unaccounted(r)) for r in recs)
    print(f"  ——  giveable today {give:,} · waiting on a licence {wait:,} · "
          f"unaccounted {unacc:,}")


def main():
    unit()
    corpus()
    if failures:
        print(f"\n{len(failures)} failure(s): {failures}")
        return 1
    print("\nall provenance checks pass"
          + (" (corpus half SKIPPED)" if skipped else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
