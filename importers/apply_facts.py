#!/usr/bin/env python3
"""Approve reader-supplied facts by number, and put them on the records.

    python3 importers/apply_facts.py               # show the queue, numbered
    python3 importers/apply_facts.py --fetch       # pull the queue first (wrangler)
    python3 importers/apply_facts.py --approve 1 3 # write those to facts.json
    python3 importers/apply_facts.py --reject 2    # note it, never apply
    python3 importers/apply_facts.py --canonical   # apply facts.json to canonical now

The queue is _incoming/suggestions.json (importers/sync_suggestions.py); a
typed fact is a row whose `what` starts with "fact:". Each is shown with the
place's name, the field, what the record holds now, and the reader's value.
Approving writes data/curated/facts.json; the fields reach the record through
facts.apply() — in import_all.py and at build time — and a `--canonical` run
applies them to data/canonical/ immediately so the next build (without an
import) carries them. Rejections are kept in _incoming/facts_rejected.json so
the same row is not shown again.

Nothing here talks to the network unless --fetch is given.
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import facts  # noqa: E402

# Overridable so tests/test_facts.py can run the whole loop on scratch files
# without touching the real queue or the real facts.json.
QUEUE = os.environ.get("MD_FACTS_QUEUE") or os.path.join(ROOT, "_incoming", "suggestions.json")
REJECTED = os.environ.get("MD_FACTS_REJECTED") or os.path.join(ROOT, "_incoming", "facts_rejected.json")
FACTS = os.environ.get("MD_FACTS_FILE") or os.path.join(ROOT, "data", "curated", "facts.json")


def load(p, default):
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def save(p, doc):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
        fh.write("\n")


def records():
    out = {}
    for pv in ("cm", "cr"):
        p = os.path.join(ROOT, "data", "canonical", f"{pv}.json")
        for r in load(p, []):
            out[r["id"]] = r
    return out


def name_of(r):
    return r.get("nameEn") or r.get("name") or r.get("id")


def queue():
    rows = load(QUEUE, {}).get("suggestions", [])
    doc = load(FACTS, {"facts": {}})
    rejected = set(load(REJECTED, {}).get("ids", []))
    applied = {f.get("suggestion") for pid in doc["facts"].values() for f in pid.values()}
    items, bad = [], []
    for row in rows:
        if row.get("status") == "done" or row.get("id") in rejected or row.get("id") in applied:
            continue
        fact = facts.parse(row)
        if not fact:
            continue
        (bad if "error" in fact else items).append(fact)
    return items, bad, doc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true", help="run sync_suggestions.py first (wrangler)")
    ap.add_argument("--approve", nargs="*", type=int, metavar="N")
    ap.add_argument("--reject", nargs="*", type=int, metavar="N")
    ap.add_argument("--canonical", action="store_true",
                    help="apply data/curated/facts.json to data/canonical/*.json now")
    args = ap.parse_args()

    if args.fetch:
        subprocess.run([sys.executable, os.path.join(ROOT, "importers", "sync_suggestions.py")],
                       check=False)

    recs = records()
    items, bad, doc = queue()

    if args.approve or args.reject:
        picked = set(args.approve or []) | set(args.reject or [])
        for n in sorted(picked):
            if not 1 <= n <= len(items):
                print(f"   {n}: no such item (1–{len(items)})")
        if args.approve:
            for n in args.approve:
                if 1 <= n <= len(items):
                    f = items[n - 1]
                    doc.setdefault("facts", {}).setdefault(f["placeId"], {})[f["field"]] = {
                        "value": f["value"], "at": date.today().isoformat(),
                        "suggestion": f["suggestion"], "note": f.get("note", "")}
                    print(f"   ✓ {n}. {f['field']} on {name_of(recs.get(f['placeId'], {}))}")
            doc.setdefault("_note", "Reader-supplied facts approved by hand through "
                                    "importers/apply_facts.py. facts.apply() puts them on the "
                                    "records; nothing here is published without that approval.")
            save(FACTS, doc)
            print(f"🐜 written to {os.path.relpath(FACTS, ROOT)}")
        if args.reject:
            rj = load(REJECTED, {"ids": []})
            for n in args.reject:
                if 1 <= n <= len(items):
                    rj["ids"].append(items[n - 1]["suggestion"])
                    print(f"   ✗ {n}. rejected")
            save(REJECTED, rj)
        items, bad, doc = queue()

    if args.canonical:
        total = 0
        for pv in ("cm", "cr"):
            p = os.path.join(ROOT, "data", "canonical", f"{pv}.json")
            text = open(p, encoding="utf-8").read()
            rs = json.loads(text)
            n = facts.apply(rs, doc)
            if n:
                with open(p, "w", encoding="utf-8") as fh:
                    json.dump(rs, fh, ensure_ascii=False, indent=1)
                    fh.write("\n")
            total += n
            print(f"   {pv}: {n} field(s) set")
        print(f"🐜 {total} field(s) on canonical — build.py next")

    print(f"\n🐜 {len(items)} typed fact(s) waiting · {len(bad)} that did not validate")
    for i, f in enumerate(items, 1):
        r = recs.get(f["placeId"]) or {}
        was = facts.current(r, f["field"]) if r else "(record not on this disk)"
        print(f"  {i:>2}. {name_of(r) if r else f['placeId']}")
        print(f"      {f['field']:8} now: {was!r:40.40}  reader: {f['value']!r}"
              + (f"  — {f['note']}" if f.get("note") else ""))
    for f in bad:
        print(f"   ✗  {f.get('placeId', '?')}: {f['error']}  {f.get('raw', '')!r}")
    if items:
        print("\n   approve:  python3 importers/apply_facts.py --approve 1 2 …")
        print("   then:     python3 importers/apply_facts.py --canonical && python3 build.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
