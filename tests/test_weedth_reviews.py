#!/usr/bin/env python3
"""What may and may not come out of a weed.th review.

Nan on 2026-09-21 asked for the kratom in the reviews, and that narrowed a
refusal rather than lifting it: the product key is read, the wording is not.
This file holds the line where she put it.

    python3 tests/test_weedth_reviews.py
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "importers"))
import harvest_weedth as H          # noqa: E402

failures = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}{'' if ok else ' — ' + detail}")
    if not ok:
        failures.append(label)


STORE = {
    "@type": "Store",
    "name": "A Shop",
    "aggregateRating": {"ratingValue": 5, "ratingCount": 99},
    "review": [
        {"reviewBody": "nice bong, good kratom. cold is cool!!",
         "author": {"name": "Somebody"},
         "reviewRating": {"ratingValue": 5}},
        {"reviewBody": "มีน้ำท่อมขายไหมครับ"},
        {"reviewBody": "no weed worth buying"},
    ],
}


def main():
    st = H._strip_refused(STORE)
    blob = json.dumps(st, ensure_ascii=False)
    for k in ("review", "aggregateRating", "ratingValue", "ratingCount"):
        check(f"_strip_refused drops {k}", f'"{k}"' not in blob)
    check("_strip_refused keeps the name", st.get("name") == "A Shop")

    off = H.offers_from_reviews(STORE)
    check("a visitor saying they bought it is read", off.get("kratom") == 1,
          f"got {off}")
    check("the value is a count, not text",
          all(isinstance(v, int) for v in off.values()), f"got {off}")
    check("no review wording is returned",
          "bong" not in json.dumps(off, ensure_ascii=False))

    # The beauty salon. "มีน้ำท่อมขายไหมครับ" is somebody ASKING whether the
    # shop sells it, and on 2026-09-21 it was the only thing that put
    # ร้าน Color Beauty on the kratom list.
    asking = H.offers_from_reviews(
        {"@type": "Store", "name": "A Salon",
         "review": [{"reviewBody": "มีน้ำท่อมขายไหมครับ"}]})
    check("a question is not evidence of a sale", asking == {}, f"got {asking}")

    check("a shop with no reviews reads as no offers",
          H.offers_from_reviews({"@type": "Store", "name": "x"}) == {})

    # PARSE FIRST, UNESCAPE AFTER. A reviewer typing a double quote used to
    # take the whole block down and the shop with it.
    page = ('<script type="application/ld+json">'
            '{"@type":"Store","name":"Quote Shop","review":'
            '[{"reviewBody":"they said &quot;best kratom&quot; and meant it"}]}'
            '</script>')
    blk = H.store_block_raw(page)
    check("a &quot; in a review does not lose the shop",
          bool(blk) and blk.get("name") == "Quote Shop",
          f"got {blk}")
    check("the quote survives as a quote",
          bool(blk) and '"best kratom"' in (blk["review"][0]["reviewBody"]))

    # And the real harvest output, if it has been written.
    out = ROOT / "data" / "curated" / "weedth.json"
    if out.exists():
        doc = json.loads(out.read_text(encoding="utf-8"))
        ents = [v for v in doc.values() if isinstance(v, dict)]
        bad_key = [e for e in ents
                   if any(k in e for k in ("review", "reviews", "rating",
                                           "aggregateRating"))]
        check("no entry on disk carries a rating or a review", not bad_key,
              f"{len(bad_key)} entries")
        bad_val = [e for e in ents
                   if not all(isinstance(v, int)
                              for v in (e.get("offers") or {}).values())]
        check("every offers value on disk is a count", not bad_val,
              f"{len(bad_val)} entries")
        n = sum(1 for e in ents if e.get("offers"))
        print(f"         · {n} of {len(ents)} entries carry an offers count")
    else:
        print("         · no harvest on disk yet; file checks skipped")

    print()
    if failures:
        print(f"{len(failures)} failure(s): {failures}")
        return 1
    print("all weed.th review checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
