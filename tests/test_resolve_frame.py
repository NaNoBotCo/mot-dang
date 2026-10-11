#!/usr/bin/env python3
"""A photo's pin comes from its neighbours, and a lonely sign must not get one.

Three defects and one capability, each pinned here so it stays fixed:

  1. BUG-0001, reported in the ops room on 2026-09-07: a photo was filed under
     a record named "This is" at 92% because the sentence naming the shop
     contained the words "this is". A name made only of stop words is not a
     name and must match nothing.

  2. Counting shared WORDS made "P Place" a half-match for "Johns Place" and
     "Top Charoen Optical" a half-match for "Roof top", because `place` and
     `top` are everywhere. Matches are scored in information, not word count.

  3. Counting the subject toward its own corroboration let a chain name plus
     one coincidence resolve. On a 400-frame validation that was 11 of 17
     confidently-wrong answers. Two corroborating signs are required.

  4. The capability itself: "Pharma Choice" alone is 19 branches and must
     refuse; the same name with three neighbours read out of the same frame
     resolves to one branch, and it is the right one.

    python3 tests/test_resolve_frame.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "importers"))

import resolve_frame as RF  # noqa: E402

FAIL = []


def check(cond, msg):
    if not cond:
        FAIL.append(msg)


# A tiny catalogue with the shape that matters: one chain with three branches,
# distinctive neighbours around exactly one of them, and a common word planted
# on the other side of town.
def rec(s, e, lat, lng, p="cm"):
    return {"s": s, "e": e, "n": e, "p": p, "lat": lat, "lng": lng}


FIXTURE = [
    # the real block
    rec("chain-a", "Pharma Choice", 18.785733, 98.992920),
    rec("johns", "Johns Place: Daughter and Son", 18.786200, 98.993300),
    rec("thc", "THC Roof top bar", 18.786800, 98.992100),
    rec("sleepmai", "Sleep Mai", 18.786400, 98.992500),
    # same chain, far away, with one generic lookalike beside it
    rec("chain-b", "Pharma Choice", 18.844157, 99.038339),
    rec("ptop", "Top Charoen Optical", 18.844300, 99.038500),
    # same chain again, nothing near it
    rec("chain-c", "Pharma Choice", 18.756752, 99.010231),
    # a common word planted elsewhere entirely
    rec("pplace", "P Place", 18.700000, 98.900000),
    rec("stopword", "This is", 18.700100, 98.900100),
]

R = RF.FrameResolver(records=FIXTURE)


def A(text, role="neighbour", kind="name"):
    return {"text": text, "role": role, "kind": kind}


# ---- 1. a name of stop words is not a name (BUG-0001) ----
check(R.candidates("This is") == [],
      "a stop-word-only anchor must match nothing, however literal the record")
check(R.candidates("the") == [], "'the' is not a name")
out = R.resolve([A("This is", "subject"), A("the")])
check(not out["resolved"], f"BUG-0001 frame must refuse, got {out}")

# ---- 2. matches are scored in information, not word count ----
by_slug = {FIXTURE[i]["s"]: s for i, s in R.candidates("Johns Place")}
check(by_slug.get("johns", 0) > 0.9,
      f"'Johns Place' must strongly match Johns Place: {by_slug}")
check("pplace" not in by_slug or by_slug["pplace"] < 0.5,
      f"sharing only the common word 'place' is not a match: {by_slug}")
top = {FIXTURE[i]["s"]: s for i, s in R.candidates("Roof top")}
check(top.get("thc", 0) > 0.9, f"'Roof top' must match THC Roof top bar: {top}")
check("ptop" not in top or top["ptop"] < 0.5,
      f"sharing only 'top' is not a match: {top}")

# ---- 3. two corroborating signs, not two anchors ----
one = R.resolve([A("Pharma Choice", "subject"), A("Top Charoen Optical")])
check(not one["resolved"],
      f"a chain name plus ONE coincidental neighbour must refuse: {one}")

# ---- 4. the capability ----
lonely = R.resolve([A("Pharma Choice", "subject")])
check(not lonely["resolved"], f"a chain name alone must refuse: {lonely}")

frame = R.resolve([A("Pharma Choice", "subject"), A("Johns Place"),
                   A("Roof top"), A("Sleep")])
check(frame["resolved"], f"three neighbours in one frame must resolve: {frame}")
check(frame.get("subject_record") == "chain-a",
      f"must pick the branch the neighbours stand beside: {frame.get('subject_record')}")
check(frame.get("precision") == "record",
      f"a held subject gives a record pin, not a block: {frame.get('precision')}")

# a subject we do NOT hold still gets a block pin off its neighbours —
# this is the case that matters: a new shop, photographed once.
newshop = R.resolve([A("Get Er to the Greek", "subject"), A("Johns Place"),
                     A("Roof top"), A("Sleep")])
check(newshop["resolved"], f"a new shop with known neighbours must resolve: {newshop}")
check(newshop.get("precision") == "block",
      f"an unheld subject gives a block pin: {newshop.get('precision')}")
check(newshop.get("subject_record") is None,
      "an unheld subject must not be given somebody else's record id")
check(newshop.get("uncertainty_m", 0) > 0,
      "a block pin must state a non-zero uncertainty")

# ---- 5. a house number is matched whole, never tokenised ----
check(R.candidates("29/3", kind="housenumber") == [],
      "a house number nothing holds must match nothing, not everything with a 29")

# ---- 6. the generated bearing tail never matches ----
check(RF._fold("Car park · 570 m from Tha Phae Gate") == "car park",
      f"the bearing tail must be stripped: {RF._fold('Car park · 570 m from Tha Phae Gate')}")

if FAIL:
    print("FAIL —", len(FAIL), "problem(s):")
    for f in FAIL:
        print("  *", f)
    sys.exit(1)
print("OK — frame resolver: neighbours pin a photo, a lonely sign gets nothing")
