#!/usr/bin/env python3
"""Check one reader question's records before the entry leaves draft.

    python3 asked_check.py khat-khi-khlai
    python3 asked_check.py khat-khi-khlai --no-net     # provenance flags only
    python3 asked_check.py khat-khi-khlai --recheck    # ignore the 30-day link cache

Step 3 of the daily loop. Three things, in order:

  1. Every URL the question stands on — each record's website and every
     http source ref — through importers/check_links.py, same cache
     (cache/linkhealth/), same verdicts (ok / tls / dns / down / gone /
     social …). A source that is already dead the day we cite it is not a
     source.
  2. Provenance flags on each record: no dated source; a price with no
     `_pricesVerified` (the unwalked label is not optional); a pin whose
     `geoPrecision` is coarse or missing; no phone on a question that lists
     only phoned places.
  3. Unresolved leads from the note (`- [ ]` bullets under `## Leads`),
     printed so they are looked at once more before the answer ships.

Read-only: it edits nothing, and it holds the entry to the same rule the
records were written under — publish what a venue declares and a passer-by
can see, and label everything weaker than that.
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "importers"))

import asked_layer  # noqa: E402

COARSE = {"landmark", "street", "postcode", "needs-pin"}


def urls_of(records):
    seen, out = set(), []
    for r in records:
        for u in [r.get("website")] + [s.get("ref") for s in r.get("sources", [])]:
            if u and str(u).startswith("http") and u not in seen:
                seen.add(u)
                out.append((u, r["id"]))
    return out


def flags_of(r, entry):
    a = r.get("attrs") or {}
    f = []
    dated = [s for s in r.get("sources", []) if s.get("fetched")]
    if not dated:
        f.append("no dated source")
    if (a.get("priceHeard") or a.get("priceBoard")) and "_pricesVerified" not in a:
        f.append("price without _pricesVerified")
    prec = r.get("geoPrecision")
    if r.get("lat") is None:
        f.append("no pin")
    elif prec in COARSE:
        f.append(f"pin is {prec}")
    if entry.get("show") == "phone" and not r.get("phone"):
        f.append("no phone (question lists phoned places only)")
    return f


def leads_of(key):
    notes = sorted(ROOT.glob(f"notes/asked-{key}-*.md")) + \
        sorted(ROOT.glob(f"notes/{key}-*.md"))
    open_, seen = [], False
    for p in notes:
        for line in p.read_text().splitlines():
            if line.startswith("## "):
                seen = line.lower().startswith("## lead") or line.lower().startswith("## open lead")
                continue
            if seen and re.match(r"\s*-\s*\[ \]", line):
                open_.append((p.name, line.strip()[5:].strip()))
            elif seen and re.match(r"\s*[-*] ", line) and "[x]" not in line.lower() \
                    and not re.match(r"\s*-\s*\[", line):
                open_.append((p.name, line.strip()[2:]))
    return open_


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("key")
    ap.add_argument("--no-net", action="store_true")
    ap.add_argument("--recheck", action="store_true")
    args = ap.parse_args()

    entries = {e["key"]: e for e in asked_layer.load(include_drafts=True)}
    if args.key not in entries:
        sys.exit(f"no such question: {args.key}")
    entry = entries[args.key]

    import build
    data = build.load()
    shown, counts = asked_layer.select(entry, data)
    print(f"{args.key}: {len(shown)} record(s) shown, {counts['n']} found"
          + (" — GAP entry" if entry.get("gap") else ""))

    if not args.no_net and shown:
        import check_links
        print("\nlinks:")
        for url, rid in urls_of(shown):
            v = check_links.cached(url, args.recheck)
            if v is None:
                v = check_links.check(url)
                check_links.save(v)
            mark = "  " if v.get("status") in ("ok", "social") else "!!"
            print(f"  {mark} {v.get('status','?'):8} {rid:34} {url[:80]}")

    print("\nrecords:")
    bad = 0
    for r in shown:
        fl = flags_of(r, entry)
        bad += bool(fl)
        print(f"  {'!!' if fl else '  '} {r['id']:34} {r.get('name','')[:40]}"
              + (f"  ← {'; '.join(fl)}" if fl else ""))

    leads = leads_of(args.key)
    if leads:
        print("\nunresolved leads:")
        for src, text in leads:
            print(f"  ?  {text[:110]}   ({src})")

    print(f"\n{bad} record(s) flagged · {len(leads)} lead(s) open"
          + (" · draft" if entry.get("draft") else ""))


if __name__ == "__main__":
    main()
