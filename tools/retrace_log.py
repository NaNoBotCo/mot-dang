#!/usr/bin/env python3
"""A plain log of what Retrace testers did and said (Nan, 2026-10-13: "live user testing and feedback").

    python3 tools/retrace_log.py            pull new feedback events, then write the log
    python3 tools/retrace_log.py --offline  write it from the events already on disk

Reads _incoming/feedback/events.jsonl (importers/sync_feedback.py fills it) and writes
_incoming/feedback/retrace-log.txt: per tester, newest first, the short log of taps the page sent
(retrace:did), their thumbs and their notes, then a tally by item. Testers show as the first six
characters of their reader id.

A tap code reads: 12s tab wats = twelve seconds in, opened the Wats tab; wat+2 = second wat added;
clue h = a hotel clue (c cafe, s shrine, w wat, o other, ? = maybe); house brahma = shape picked;
date / hour = sun set; face eyes = sun in my eyes; walk 3/9 2019 = third of nine photos, taken 2019;
found@photo / found@tap = a pin dropped; not-here = a photo marked no; field-job = street sent for photos;
hard <k> = a chip in Say.
"""
import argparse
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVENTS = ROOT / "_incoming" / "feedback" / "events.jsonl"
OUT = ROOT / "_incoming" / "feedback" / "retrace-log.txt"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args()
    if not a.offline:
        subprocess.run([sys.executable, str(ROOT / "importers" / "sync_feedback.py")], check=False)
    ev = []
    if EVENTS.exists():
        for ln in EVENTS.read_text(encoding="utf-8").splitlines():
            if ln.strip():
                e = json.loads(ln)
                if str(e.get("item", "")).startswith("retrace:"):
                    ev.append(e)
    ev.sort(key=lambda e: (e["at"], e["k"]))
    who = defaultdict(list)
    for e in ev:
        who[e.get("who", "?")].append(e)
    lines = [f"RETRACE testers: {len(who)} reader(s), {len(ev)} event(s)", ""]
    order = sorted(who, key=lambda w: who[w][-1]["at"], reverse=True)
    for w in order:
        es = who[w]
        lines.append(f"{w[:6]}  {es[0]['at'][:16]} to {es[-1]['at'][:16]} UTC  {es[0].get('lang', '')}")
        for e in es:
            it = e["item"].split(":", 1)[1]
            if e["k"].startswith("fb-vote:"):
                lines.append(f"    {e['at'][11:16]} {'thumb up' if e.get('x') == 1 else 'thumb down' if e.get('x') == -1 else 'thumb off'} on {it}")
            elif it == "did":
                lines.append(f"    {e['at'][11:16]} did: {' '.join(e['note'].split())}")
            elif it == "fieldjob":
                lines.append(f"    {e['at'][11:16]} FIELD JOB: {' '.join(e['note'].split())[:400]}")
            else:
                lines.append(f"    {e['at'][11:16]} said ({it}): {' '.join(e['note'].split())[:600]}")
        lines.append("")
    tally = defaultdict(lambda: [0, 0, 0])
    latest = {}
    for e in ev:
        if e["k"].startswith("fb-vote:"):
            latest[(e["item"], e.get("who"))] = e.get("x", 0)
        elif e.get("note") and e["item"] != "retrace:did":
            tally[e["item"]][2] += 1
            if e.get("x") in (1, -1):
                latest[(e["item"], e.get("who"))] = e["x"]
    for (it, _w), x in latest.items():
        if x == 1:
            tally[it][0] += 1
        elif x == -1:
            tally[it][1] += 1
    lines.append("BY ITEM   up / down / notes")
    for it in sorted(tally):
        u, d, n = tally[it]
        lines.append(f"    {it:24} {u} / {d} / {n}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(who)} tester(s), {len(ev)} event(s) -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
