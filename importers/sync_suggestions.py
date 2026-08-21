#!/usr/bin/env python3
"""Bring the suggestion queue down to this machine, to be read by a person.

Readers tell the ants things through POST /suggest on the claims Worker: a name
that is wrong, a place we do not have, a phone for a listing with none, a photo
they are offering, a corner worth crawling. Unlike a claim, none of it
publishes itself — a claim is a shop's account of its own contact details, this
is a stranger's account of somebody else's place, so a person reads it first.

There is no public GET for the queue and there should not be: it carries the
sender's own phone or email, given so we could ask a follow-up question. So
this reads KV directly with wrangler, which is already authenticated as her,
and writes to _incoming/ — gitignored, so a contributor's email can never ride
into a public commit by accident.

    python3 importers/sync_suggestions.py            # fetch new ones
    python3 importers/sync_suggestions.py --all      # including ones already seen
    python3 importers/sync_suggestions.py --done ID  # mark one handled
    python3 importers/sync_suggestions.py --offline --kind question
                                                     # triage from the file on
                                                     # disk, no wrangler round-trip

The `question` kind is the ถามมด intake (asked_layer.py): a reader asking where
to find something. Triage prints the question and whether a reply address was
left — never the address itself, for the same reason the file is gitignored.

WRANGLER GOTCHA: every kv command needs --remote. Without it wrangler talks to
a LOCAL simulated namespace and silently succeeds against nothing — the same
trap noted in this repo's claim-testing notes.
"""
import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "_incoming")
OUT = os.path.join(OUT_DIR, "suggestions.json")
NS = "ec8e8043f8304f35a3fb01d5cfbefa31"      # MD_KV, same id as worker/wrangler.toml
WORKER = os.path.join(ROOT, "worker")


def wrangler(*args):
    proc = subprocess.run(["npx", "wrangler", *args, "--remote", "--namespace-id", NS],
                          cwd=WORKER, capture_output=True, text=True, timeout=180)
    if proc.returncode:
        raise RuntimeError(proc.stderr.strip()[-400:] or "wrangler failed")
    return proc.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="include ones already marked handled")
    ap.add_argument("--done", metavar="ID", help="mark a suggestion handled")
    ap.add_argument("--kind", help="show only this kind (e.g. question)")
    ap.add_argument("--offline", action="store_true",
                    help="read _incoming/suggestions.json instead of KV")
    args = ap.parse_args()

    if args.done:
        key = f"sug:{args.done}"
        raw = wrangler("kv", "key", "get", key)
        doc = json.loads(raw)
        doc["status"] = "done"
        subprocess.run(["npx", "wrangler", "kv", "key", "put", key, json.dumps(doc),
                        "--remote", "--namespace-id", NS], cwd=WORKER, check=True)
        print(f"🐜 {args.done} marked handled")
        return 0

    if args.offline:
        if not os.path.exists(OUT):
            sys.exit(f"nothing on disk yet — run without --offline first ({OUT})")
        with open(OUT, encoding="utf-8") as fh:
            rows = json.load(fh).get("suggestions", [])
    else:
        listing = json.loads(wrangler("kv", "key", "list", "--prefix", "sug:"))
        rows = []
        for k in listing:
            try:
                rows.append(json.loads(wrangler("kv", "key", "get", k["name"])))
            except Exception as e:
                print(f"   could not read {k['name']}: {e}")
        if not args.all:
            rows = [r for r in rows if r.get("status") != "done"]
        rows.sort(key=lambda r: r.get("createdAt") or "")

        os.makedirs(OUT_DIR, exist_ok=True)
        with open(OUT, "w", encoding="utf-8") as fh:
            json.dump({"fetched": len(rows), "suggestions": rows}, fh,
                      ensure_ascii=False, indent=1)

    if args.kind:
        rows = [r for r in rows if r.get("kind") == args.kind]
    if not args.all:
        rows = [r for r in rows if r.get("status") != "done"]

    print(f"🐜 {len(rows)} suggestion(s) waiting -> {OUT}")
    for r in rows[:40]:
        if r.get("kind") == "question":
            # the triage line for ถามมด: id to pass to asked_new.py, when,
            # language, the question — and whether we CAN reply, never to whom
            print(f"   {r.get('id','')[:8]}  {(r.get('createdAt') or '')[:10]}  "
                  f"{r.get('lang','?'):2}  reply-to: {'yes' if r.get('from') else 'no '}  "
                  f"{(r.get('what') or '')[:100]}")
        else:
            where = r.get("placeId") or "(no place)"
            print(f"   [{r.get('kind','?'):10}] {where:28} {(r.get('what') or '')[:60]}")
    if len(rows) > 40:
        print(f"   … and {len(rows) - 40} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
