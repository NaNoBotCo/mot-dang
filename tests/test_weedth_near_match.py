#!/usr/bin/env python3
"""When a weed.th name that partly matches a held name is a question.

Nan, 2026-09-23: "weed.th lists medileaves but it didn't make it onto
motdang.net." It sat in cache/weedth_review.txt as a possible duplicate of
The Old City, a Thai restaurant. The check compared against every shelf.

    python3 tests/test_weedth_near_match.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "importers"))
import import_weedth as W          # noqa: E402

failures = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}{'' if ok else ' — ' + detail}")
    if not ok:
        failures.append(label)


def rec(name, cat):
    return {"name": name, "cat": [cat]}


HAVE = {
    ("cm", W.norm_name("The Old City")): rec("The Old City", "food"),
    ("cm", W.norm_name("Green Ganesha")): rec("Green Ganesha", "community"),
    ("cm", W.norm_name("Let's Get High")): rec("Let's Get High", "cannabis"),
    ("cm", W.norm_name("Old Town")): rec("Old Town", "cannabis"),
    ("cr", W.norm_name("The Old City")): rec("The Old City", "food"),
}

key = W.norm_name("Medileaves | Weed Shop Dispensary - Old City")
check("medileaves is not a question about a restaurant",
      W.near_matches(key, "cm", HAVE) == [], repr(W.near_matches(key, "cm", HAVE)))

key = W.norm_name("Green Ganesha 2 - Organic Weed Dispensary")
check("a community record named for the trade stays a question",
      W.near_matches(key, "cm", HAVE) == ["green ganesha"])

key = W.norm_name("LET'S GET HIGH CNX Branch2 | cannabis store")
check("a record on the cannabis shelf stays a question",
      W.near_matches(key, "cm", HAVE) == ["let s get high"])

key = W.norm_name("The OT Dispensary - OLD TOWN")
check("two place words on the cannabis shelf stay a question",
      W.near_matches(key, "cm", HAVE) == ["old town"])

key = W.norm_name("Medileaves | Weed Shop Dispensary - Old City")
check("the other province is never consulted",
      W.near_matches(key, "cr", HAVE) == [])

check("could_be_cannabis reads the shelf",
      W.could_be_cannabis(rec("Somewhere", "cannabis")))
check("could_be_cannabis reads the sign",
      W.could_be_cannabis(rec("สวนฅนชอบกัญ", "business")))
check("a restaurant with neither is not",
      not W.could_be_cannabis(rec("The Old City", "food")))

print("FAILED: " + ", ".join(failures) if failures else "all ok")
sys.exit(1 if failures else 0)
