#!/usr/bin/env python3
"""The bearings census — what the site can now say about where things are,
and the address relations the pin refused. WO-64. Reads data/canonical and
data/curated/landmarks.json only; writes one report and nothing else.

    python3 importers/audit_bearings.py            # prints + writes the report
    python3 importers/audit_bearings.py --quiet    # report only

THE TWO NUMBERS THAT MATTER. (1) How many pinned places get at least one
line that is not the zone — that is the coverage of the secret sauce. (2) How
many address relations the pin CONTRADICTED — each of those is a wrong parse
or a wrong pin, and the report guesses which by the size of the miss: under
2 km with an approx pin, suspect the pin; an exact pin 10 km from the
landmark the address names, suspect the parse (or the address).
"""
import collections
import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import bearings_layer as B  # noqa: E402

OUT = ROOT / "_incoming" / f"bearings-audit-{datetime.date.today().isoformat()}.txt"


def main():
    quiet = "--quiet" in sys.argv
    c = B.ctx(force=True)
    B.CONTRADICTIONS.clear()
    recs = list(c.by_id.values())
    lines_out = []

    def say(s=""):
        lines_out.append(s)
        if not quiet:
            print(s)

    say(f"BEARINGS AUDIT — {datetime.datetime.now():%Y-%m-%d %H:%M}")
    say(f"records {len(recs):,}")
    for p, ls in c.landmarks.items():
        say(f"  {p}: {len(ls)} landmarks resolved, origin = {(c.origin.get(p) or {}).get('key')}")
    for u in c.unresolved:
        say(f"  UNRESOLVED {u}")
    say(f"  moat polygon: {'yes' if c.moat_poly else 'NO'}")

    kinds = collections.Counter()
    per_prov = collections.Counter()
    covered = collections.Counter()
    pinned = collections.Counter()
    approx_only = collections.Counter()
    addr_parsed = collections.Counter()
    addr_only = collections.Counter()
    samples = collections.defaultdict(list)
    lm_use = collections.Counter()
    for r in recs:
        prov = r.get("province") or r["id"][:2]
        per_prov[prov] += 1
        has_pin = r.get("lat") is not None and (r.get("geoPrecision") or "exact") != "needs-pin"
        if has_pin:
            pinned[prov] += 1
        ls = B.bearings(r, c)
        ks = [x["kind"] for x in ls]
        for x in ls:
            kinds[(prov, x["kind"])] += 1
            if x.get("landmark"):
                lm_use[(prov, x["landmark"])] += 1
        if has_pin and any(k != "zone" for k in ks):
            covered[prov] += 1
        if ls and all(x["approx"] or x["kind"] == "zone" for x in ls):
            approx_only[prov] += 1
        if "address" in ks:
            addr_parsed[prov] += 1
            if not has_pin:
                addr_only[prov] += 1
        for x in ls:
            if len(samples[(prov, x["kind"])]) < 6 and (x["kind"] != "zone"):
                samples[(prov, x["kind"])].append((r["id"], r.get("name") or r.get("nameEn"), x["th"], x["en"]))

    say()
    say("COVERAGE (a line that is not merely the zone)")
    for p in sorted(per_prov):
        say(f"  {p}: {covered[p]:,} of {pinned[p]:,} pinned ({100.0 * covered[p] / max(1, pinned[p]):.0f}%)"
            f" · {approx_only[p]:,} approximate-only · address relation parsed {addr_parsed[p]:,}"
            f" (of which pin-less {addr_only[p]:,}) · records {per_prov[p]:,}")
    say()
    say("LINES BY KIND")
    for (p, k), n in sorted(kinds.items()):
        say(f"  {p} {k:8s} {n:,}")
    say()
    say("LANDMARKS MOST NAMED (top 25)")
    for (p, k), n in lm_use.most_common(25):
        say(f"  {p} {k:24s} {n:,}")
    say()
    say("SAMPLES, one per kind")
    for (p, k), rows in sorted(samples.items()):
        say(f"  -- {p} {k}")
        for rid, nm, th, en in rows:
            say(f"     {rid}  {str(nm)[:40]}")
            say(f"        {th}")
            say(f"        {en}")
    say()
    say(f"CONTRADICTIONS — address names a landmark the pin refuses: {len(B.CONTRADICTIONS):,}")
    say("  (guess: 'pin?' = approx pin within 2 km, the pin is the likelier fault;"
        " 'parse?' = the address or the parse)")
    for x in sorted(B.CONTRADICTIONS, key=lambda x: -x["m"])[:60]:
        guess = "pin?  " if (x["unc"] or 0) >= 400 and x["m"] <= 2000 else "parse?"
        say(f"  {guess} {x['id']:44s} says {x['landmark']:22s} via {x['alias']!r:24s}"
            f" pin {x['m']:>6,} m away (±{int(x['unc'] or 0):,})  | {str(x['address'])[:70]}")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(lines_out) + "\n")
    print(f"\nreport -> {OUT}")


if __name__ == "__main__":
    main()
