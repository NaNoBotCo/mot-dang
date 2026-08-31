#!/usr/bin/env python3
"""Read the convenience records' own names for what they declare. Zero network.

Same contract as audit_beauty.py and its siblings: this never edits canonical
data. It reports. The one rule it WITNESSES (rather than proposes) already
runs at import — seven_from_name in import_overpass.py, which brands a
convenience record named 7-Eleven off its own sign — so this audit is that
rule's receipt printer, plus the census around it.

The measurement that asked for this (notes/seven-proposal-2026-08-27.md):

  THE SHELF HELD 404 SEVENS AND THE SIGNS SAY 463. Fifty-nine records NAMED
  7-Eleven / เซเว่น carried no `brand` tag — the mapper typed the name and
  skipped the tag — so they sat off the brand tag page and out of every
  count, indistinguishable from an unnamed minimart. The barber lie, on the
  convenience shelf.

Six reports:

  BY-SIGN    the records seven_from_name branded, with the sign it read.
  REFUSED    records named seven that the rule would NOT brand — a mapper's
             denial (not:brand:wikidata, way/544559166) or a sign that says
             more than the brand ("7-11 หลอด biers Bier Stube", the beer
             stall in 7-Eleven livery). The fences, shown holding.
  CANDIDATES no-brand names that say Lotus / Big C / CJ. NOT auto-filled:
             the chain renamed itself over the years (Tesco Lotus → Lotus's)
             and which era's string a sign carries is a call for Nan, not a
             regex.
  DUPES      same-brand pairs closer than 25 m — one shop mapped twice.
             The two closest "twins" in the snapshot are 1 m and 6 m apart;
             they are merge candidates, and the twin line in build.py
             (SEVEN_DUP_M, same number, kept in step by tests/test_seven.py)
             refuses to call them doubles.
  STRAYS     เซเว่น-named records that are NOT convenience stores, printed so
             the sub fence can be seen working. เซเว่น สตาร์ is a condominium
             in ช้างเผือก; a name rule without the fence would have made it
             a shop.
  NO-BRAND   the 196 no-brand rows read in Thai: มินิมาร์ท, ของชำ, โชห่วย —
             the neighbourhood shops with names of their own. A census, not
             a problem list: no brand is not a data gap.

Run: python3 importers/audit_convenience.py
"""
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Kept equal to build.py's SEVEN_DUP_M — tests/test_seven.py holds the pair
# together, the same arrangement routing.py has with the plan JS.
DUP_M = 25

SEVEN_RX = re.compile(r"7[\s‐-]?eleven|7-11\b|เซเว่น|เซเวน", re.I)
CAND_RX = [
    ("lotus", re.compile(r"โลตัส|lotus", re.I)),
    ("big-c", re.compile(r"บิ๊กซี|big\s*c", re.I)),
    ("cj", re.compile(r"ซีเจ|\bcj\b", re.I)),
]
NOBRAND_WORDS = ["มินิมาร์ท", "มินิมาร์ต", "minimart", "mini mart",
                 "โชห่วย", "ของชำ", "ร้านค้า", "เซเว่น"]


def names_of(r):
    return " ".join(filter(None, (r.get("name"), r.get("nameTh"),
                                  r.get("nameEn"))))


def hav_m(a, b):
    p1, p2 = math.radians(a["lat"]), math.radians(b["lat"])
    dp = math.radians(b["lat"] - a["lat"])
    dl = math.radians(b["lng"] - a["lng"])
    h = (math.sin(dp / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2)
    return 2 * 6371000 * math.asin(math.sqrt(h))


def main():
    recs = []
    for prov in ("cm", "cr"):
        f = ROOT / "data" / "canonical" / f"{prov}.json"
        if f.exists():
            recs.extend(json.loads(f.read_text()))
    conv = [r for r in recs if "convenience" in (r.get("sub") or [])]
    print(f"records {len(recs)} · convenience {len(conv)}")

    # ---- BY-SIGN --------------------------------------------------------
    by_sign = [r for r in conv
               if (r.get("attrs") or {}).get("brandFrom") == "osm-name"]
    print(f"\nBY-SIGN — branded off the shop's own sign: {len(by_sign)}")
    for r in by_sign:
        print(f"  {r['id']}  osm name: {names_of(r)}")

    # ---- REFUSED --------------------------------------------------------
    denied = [r for r in conv
              if SEVEN_RX.search(names_of(r))
              and not (r.get("attrs") or {}).get("brand")]
    print(f"\nREFUSED — named seven, brand withheld "
          f"(a mapper's denial, or a sign that says more than the brand): "
          f"{len(denied)}")
    for r in denied:
        src = (r.get("sources") or [{}])[0].get("ref", "")
        print(f"  {r['id']}  ({src})  {names_of(r)}")

    # ---- CANDIDATES -----------------------------------------------------
    print("\nCANDIDATES — no-brand names that say a chain "
          "(a call for Nan, never a regex):")
    n_cand = 0
    for key, rx in CAND_RX:
        hits = [r for r in conv
                if not (r.get("attrs") or {}).get("brand")
                and rx.search(names_of(r))]
        n_cand += len(hits)
        print(f"  {key}: {len(hits)}")
        for r in hits:
            print(f"    {r['id']}  osm name: {names_of(r)}")
    if not n_cand:
        print("  (none — every chain-worded name already carries its brand)")

    # ---- DUPES ----------------------------------------------------------
    print(f"\nDUPES — same-brand pairs under {DUP_M} m (one shop mapped twice):")
    pins = [r for r in conv if r.get("lat") is not None
            and (r.get("attrs") or {}).get("brand")]
    seen, n_dupe = set(), 0
    for i, a in enumerate(pins):
        for b in pins[i + 1:]:
            if (a.get("attrs") or {}).get("brand") != (b.get("attrs") or {}).get("brand"):
                continue
            if abs(a["lat"] - b["lat"]) > 0.0005 or abs(a["lng"] - b["lng"]) > 0.0005:
                continue
            d = hav_m(a, b)
            if d < DUP_M:
                key = tuple(sorted((a["id"], b["id"])))
                if key in seen:
                    continue
                seen.add(key)
                n_dupe += 1
                print(f"  {int(d)} m  {a['id']}  ↔  {b['id']}"
                      f"  ({(a.get('attrs') or {}).get('brand')})")
    if not n_dupe:
        print("  (none)")

    # ---- STRAYS ---------------------------------------------------------
    strays = [r for r in recs
              if SEVEN_RX.search(names_of(r))
              and "convenience" not in (r.get("sub") or [])]
    print(f"\nSTRAYS — เซเว่น-named, not a convenience store "
          f"(the sub fence, shown working): {len(strays)}")
    for r in strays:
        print(f"  {r['id']}  [{'/'.join(r.get('sub') or r.get('cat') or [])}]"
              f"  {names_of(r)}")

    # ---- NO-BRAND -------------------------------------------------------
    nob = [r for r in conv if not (r.get("attrs") or {}).get("brand")]
    print(f"\nNO-BRAND — the neighbourhood rows, read in Thai: {len(nob)}")
    for w in NOBRAND_WORDS:
        n = sum(1 for r in nob if w.lower() in names_of(r).lower())
        if n:
            print(f"  {w}: {n}")

    # ---- FACETS ---------------------------------------------------------
    fc = {}
    for r in conv:
        for k in ((r.get("attrs") or {}).get("facets") or {}):
            fc[k] = fc.get(k, 0) + 1
    print("\nFACETS on the shelf: "
          + ", ".join(f"{k} {v}" for k, v in sorted(fc.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
