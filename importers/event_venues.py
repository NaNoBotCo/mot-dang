#!/usr/bin/env python3
"""Event venues the catalogue does not match yet, each with the records it may be.

Step 3 of the newsletter route: before a venue gets an alias or a new
cm-newsletter-* record, look here. On 2026-10-04, 25 newsletter records turned
out to be places the catalogue already held under another spelling (the
Marriott, the Gymkhana Club, Gaj Kitchen, Alt_PingRiver…); their events had sat
on a pinless copy while the real record showed none of them. They were folded
by data/curated/merges.json.

Reads data/event_ledger.json (every venue string ever listed) and the built
catalogue through build.py's own match_venue(), so "unmatched" here means
unmatched on the site. Candidates share all but one distinctive word of the
venue's name. A candidate is a lead, not a match: check the address and the
pin, then add an alias to data/curated/venue_aliases.json or a merge.

    python3 importers/event_venues.py            unmatched venues and candidates
    python3 importers/event_venues.py --stubs    also: cm-newsletter-* records that
                                                 may duplicate an existing record
"""
import argparse
import collections
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

EXTRA_STOP = {"hotel", "club", "house", "cafe", "coffee", "studio", "market", "garden",
              "chiangmai", "resort", "road", "school", "center", "centre", "park"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--stubs", action="store_true")
    a = ap.parse_args(argv)
    import build
    data = {p["key"]: json.load(open(os.path.join(ROOT, "data", "canonical", p["key"] + ".json"),
                                     encoding="utf-8")) for p in build.PROVINCES}
    idx = build._venue_index(data)
    _by_name, entries, _by_id = idx
    stop = build.VENUE_STOP | EXTRA_STOP

    def toks(s):
        return {t for t in build._vnorm(s).split() if t not in stop and len(t) > 2}

    by_tok = collections.defaultdict(list)
    for _t, r in entries:
        for t in toks(r.get("name")) | toks(r.get("nameEn")) | toks(r.get("nameTh")):
            by_tok[t].append(r)

    def candidates(name, skip=()):
        vt, out = toks(name), {}
        for t in vt:
            if len(by_tok.get(t, [])) > 200:
                continue
            for r in by_tok[t]:
                if r["id"] in skip:
                    continue
                ov = len(vt & (toks(r.get("name")) | toks(r.get("nameEn")) | toks(r.get("nameTh"))))
                if ov >= max(1, len(vt) - 1):
                    out[r["id"]] = (ov, r)
        return sorted(out.values(), key=lambda x: (-x[0], x[1].get("lat") is None))[:4]

    def line(ov, r):
        pin = f"{r['lat']:.4f},{r['lng']:.4f}" if r.get("lat") is not None else "no pin"
        return (f"      {ov} {r['id']} | {r.get('name')} | {r.get('nameEn') or ''} | {pin} | "
                f"{(r.get('address') or '')[:50]}")

    try:
        led = json.load(open(os.path.join(ROOT, "data", "event_ledger.json"), encoding="utf-8"))["events"]
    except (OSError, ValueError, KeyError):
        led = {}
    count = collections.Counter(x["venue_name"] for x in led.values() if x.get("venue_name"))
    miss = [(v, n) for v, n in count.items() if not build.match_venue(v, idx)[0]]
    print(f"{len(count)} venue strings in the ledger, {len(miss)} unmatched")
    for v, n in sorted(miss, key=lambda x: -x[1]):
        print(f"{n:4d}  {v}")
        for ov, r in candidates(v):
            print(line(ov, r))
    if a.stubs:
        print("\nnewsletter records that may already exist:")
        for recs in data.values():
            for r in recs:
                if "-newsletter-" not in r["id"]:
                    continue
                c = [x for x in candidates(r.get("nameEn") or r.get("name"), skip={r["id"]})
                     if x[0] >= 2]
                if c:
                    pin = "pin" if r.get("lat") is not None else "no pin"
                    print(f"  {r['id']} ({pin}) | {r.get('name')}")
                    for ov, x in c:
                        print(line(ov, x))
    return 0


if __name__ == "__main__":
    sys.exit(main())
