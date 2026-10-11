#!/usr/bin/env python3
"""Work the pin gap down with the ground we already hold.

2,116 of 24,159 places carry geoPrecision "needs-pin": real, addressed, and
absent from every map. 2,088 of them HAVE a written address — nobody had ever
run it through importers/geocode_local.py. That module was built, measured and
wired into two importers, and the records that arrived before it (the ONAB
temple register, most of the opendata fold) never went back through it.

This is that pass. It calls no service — geocode_local reads streets.json,
tambon and postcode centroids built from our own surveyed pins, and landmarks
we already hold. Nominatim's terms forbid bulk use and a paid geocoder would
put a third party between a reader and a Chiang Mai shopfront.

Output is an OVERLAY, data/curated/pins.json, applied by import_all.py after
the merge — never a write into data/canonical/*.json, which import_all.py
regenerates. Each pin carries the tier that earned it, how far it might be
wrong, and what it matched, so a reader and the AI can both tell a surveyed
door from a subdistrict centroid.

  importers/geocode_gaps.py                  dry run: what would be pinned
  importers/geocode_gaps.py --write          write data/curated/pins.json
  importers/geocode_gaps.py --only tok-sen   just one sub/cat, for a first look
  importers/geocode_gaps.py --max-uncertainty 800
                                             refuse anything vaguer than this
"""
import argparse, collections, datetime, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "importers"))
OUT = os.path.join(ROOT, "data", "curated", "pins.json")   # --out overrides, for tests

# A pin is only worth having if it lands the reader on the right errand. These
# are the tiers geocode_local returns, in the order it tries them; each is
# kept with the uncertainty it declares, never flattened into "a location".
TIERS = ("landmark", "street", "postcode", "tambon")


def load_canonical():
    out = []
    for prov in ("cm", "cr"):
        p = os.path.join(ROOT, "data", "canonical", f"{prov}.json")
        for r in json.load(open(p, encoding="utf-8")):
            r["_prov"] = prov
            out.append(r)
    return out


def write_pins(doc):
    """Write whole or not at all.

    Being idempotent is not the same as being safe to run twice AT ONCE. Two
    of these overlapped once — one capped at 3 km, one not — and the loser's
    half-written file was what survived: 424 pins on disk while the cap said
    286. A rename is atomic on this filesystem, so a reader sees the old file
    or the new one and never a blend of them.
    """
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    os.replace(tmp, OUT)


def _is_gap(r, prior):
    """A record with no pin of its OWN.

    Three ways to be one, and the second is the one that was missing: a record
    still marked needs-pin; a record whose only pin came from the curated
    overlay (attrs.pinSource), which is inferred and must be re-derived under
    today's cap; or one simply listed in the overlay file we are about to
    rewrite. The first two are facts about the record and hold no matter where
    the output file is, which is what makes a re-run reproduce rather than
    shrink.
    """
    if (r.get("geoPrecision") or "exact") == "needs-pin" and not (r.get("lat") and r.get("lng")):
        return True
    if (r.get("attrs") or {}).get("pinSource") == "curated-pins":
        return True
    return r["id"] in prior


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--only", default="", help="a cat or sub slug to limit to")
    ap.add_argument("--max-uncertainty", type=int, default=0,
                    help="refuse a pin declaring more than this many metres")
    ap.add_argument("--show", type=int, default=8)
    ap.add_argument("--out", default="", help="write/read somewhere else (tests)")
    ap.add_argument("--check", action="store_true",
                    help="derive the pins and compare them to the file on disk; "
                         "exit 1 on any drift. This is the idempotence test: a "
                         "second run must say exactly what the first one said.")
    a = ap.parse_args()
    if a.out:
        global OUT
        OUT = a.out

    from geocode_local import Gazetteer
    g = Gazetteer()

    recs = load_canonical()
    # IDEMPOTENT ON PURPOSE. "The gap" cannot be defined as `needs-pin` alone:
    # once this script's own pins have been applied by import_all, those records
    # are `approx` and drop out of the gap, so a second run measures a smaller
    # problem and writes a smaller file. That is how a capped run and an
    # uncapped run once raced and left 424 pins on disk when the cap said 286.
    # A record already in pins.json is therefore still a gap, and gets re-derived
    # under whatever cap is in force today.
    prior = set()
    if os.path.exists(OUT):
        try:
            prior = set((json.load(open(OUT, encoding="utf-8")) or {}).get("pins") or {})
        except Exception:
            prior = set()
    gaps = [r for r in recs if _is_gap(r, prior)]
    if a.only:
        gaps = [r for r in gaps
                if a.only in (r.get("cat") or []) or a.only in (r.get("sub") or [])]

    today = datetime.date.today().isoformat()
    pins, by_tier, refused, noaddr, samples = {}, collections.Counter(), 0, 0, []
    for r in gaps:
        addr = r.get("address")
        if not addr:
            noaddr += 1
            continue
        loc = g.locate(addr, r["_prov"])
        if not loc:
            by_tier["none"] += 1
            continue
        if a.max_uncertainty and loc["uncertainty_m"] > a.max_uncertainty:
            refused += 1
            continue
        by_tier[loc["precision"]] += 1
        pins[r["id"]] = {
            "lat": loc["lat"], "lng": loc["lng"],
            "tier": loc["precision"],
            "uncertainty_m": int(loc["uncertainty_m"]),
            "via": loc["via"],
            "from": str(loc.get("matched") or ""),
            "source": "geocode_local",
            "fetched": today,
        }
        if len(samples) < a.show:
            samples.append((r.get("name"), loc["precision"], loc["uncertainty_m"],
                            str(loc.get("matched"))[:28], addr[:52]))

    print(f"{len(gaps)} records with no pin"
          + (f" (--only {a.only})" if a.only else "")
          + f"; {noaddr} of them carry no address at all")
    for t in TIERS:
        if by_tier[t]:
            print(f"  {t:9s} {by_tier[t]:5d}")
    print(f"  {'no match':9s} {by_tier['none']:5d}  (returns None; nothing invented)")
    if refused:
        print(f"  refused   {refused:5d}  (vaguer than {a.max_uncertainty} m)")
    print(f"\n-> {len(pins)} pins ({100 * len(pins) / max(1, len(gaps)):.0f}% of the gap)")
    for n, p, u, m, ad in samples:
        print(f"   [{p:8s} ±{u:6d} m] {str(n)[:30]:30} matched {m:28} | {ad}")

    if a.check:
        on_disk = {}
        if os.path.exists(OUT):
            on_disk = (json.load(open(OUT, encoding="utf-8")) or {}).get("pins") or {}
        # Only the pins THIS pass owns; pin_from_osm's OSM rows live in the
        # same file and are not this run's to reproduce.
        mine = {k: v for k, v in on_disk.items() if v.get("source") == "geocode_local"}
        drift = []
        for k in set(mine) | set(pins):
            was, now = mine.get(k), pins.get(k)
            if not was:
                drift.append(f"  + {k} would be added ({now['tier']} ±{now['uncertainty_m']} m)")
            elif not now:
                drift.append(f"  - {k} is on disk but would not be derived ({was['tier']})")
            elif (was["lat"], was["lng"], was["tier"]) != (now["lat"], now["lng"], now["tier"]):
                drift.append(f"  ~ {k} moved: {was['tier']} -> {now['tier']}")
        if not drift:
            print(f"\nidempotent: {len(pins)} pins derived, {len(mine)} on disk, no drift")
            return
        print(f"\nDRIFT: {len(drift)} difference(s) between what is on disk and "
              f"what this run derives")
        for line in drift[:20]:
            print(line)
        sys.exit(1)

    if not a.write:
        print("\ndry run. --write to save", os.path.relpath(OUT, ROOT))
        return
    doc = {
        "_note": ("Pins inferred from a written address by importers/geocode_gaps.py, "
                  "using importers/geocode_local.py and this catalogue's own ground "
                  "(streets.json, tambon and postcode centroids, landmarks we hold). "
                  "No geocoding service was called. Applied by import_all.py ONLY to "
                  "records that still have no pin: a surveyed pin always wins. Each "
                  "entry carries the tier that earned it and how far it may be wrong; "
                  "a walked pin should replace it and this row should then be deleted."),
        "generated": today,
        "pins": pins,
    }
    write_pins(doc)
    print("\nwrote", os.path.relpath(OUT, ROOT), f"({len(pins)} pins)")


if __name__ == "__main__":
    main()
