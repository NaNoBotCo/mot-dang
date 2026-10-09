#!/usr/bin/env python3
"""Every event the harvest has ever seen, kept after its day has passed.

data/events.json is what is on: build.py drops a one-off the day after it
happens, so until 2026-10-04 a venue that hosted forty evenings over the
summer showed nothing once they were over, and search could not tell a busy
stage from a shop that had never held one. Nan, 2026-10-04: "Prior events and
future events should add to a place's richness and placement in our internal
search results."

This file is the memory. One entry per event, or per weekly series:

  data/event_ledger.json
    events.<key>   title, venue_name, sources[], url, cost, recurring,
                   weekday, dates[] (each date it was listed for),
                   end, first_seen, last_seen

  key   a one-off: its harvest uid (stable across issues — the uid is the
        date plus the title).
        a weekly series: "w:<title>:<weekday>", because each instance of a
        weekly arrives with its own dated uid and twenty Fridays are one thing.

The venue is kept as the string the source printed, not a place id. build.py
matches it at build time with the same match_venue() the live events use, so a
venue alias added next month reaches every past event at that venue too.

Nothing is ever removed. A later sighting of the same key adds its dates and
moves last_seen; it never overwrites a field it lacks.

  importers/event_ledger.py               fold data/events.json in (the walk)
  importers/event_ledger.py --backfill    also every committed data/events.json
                                          and every newsletter issue on disk
"""
import argparse
import json
import os
import re
import subprocess
import sys
import unicodedata
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "importers"))
EVENTS = os.path.join(ROOT, "data", "events.json")
OUT = os.path.join(ROOT, "data", "event_ledger.json")
NEWSLETTERS = os.path.join(ROOT, "_incoming", "newsletter")
DATES_MAX = 120          # a weekly series listed for two years is still one row


def norm_title(t):
    """build.py's _ev_norm_title: cross-posted copies compare equal."""
    t = unicodedata.normalize("NFKC", t or "").casefold()
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def key_of(e):
    if e.get("recurring") and e.get("weekday") is not None:
        return "w:%s:%s" % (norm_title(e.get("title")), e["weekday"])
    return e.get("uid") or "d:%s:%s" % ((e.get("start") or "")[:10], norm_title(e.get("title")))


def load(path=OUT):
    try:
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, ValueError):
        doc = {}
    doc.setdefault("events", {})
    return doc


def fold(doc, events, seen_on):
    """Add one harvest's events. Returns (new keys, updated keys)."""
    led = doc["events"]
    new = upd = 0
    for e in events:
        if not (e.get("title") and e.get("start")):
            continue
        k = key_of(e)
        day = (e.get("start") or "")[:10]
        cur = led.get(k)
        if cur is None:
            cur = led[k] = {"title": e["title"], "venue_name": e.get("venue_name") or "",
                            "sources": [], "url": e.get("url"), "cost": e.get("cost"),
                            "recurring": bool(e.get("recurring")), "weekday": e.get("weekday"),
                            "dates": [], "end": e.get("end"),
                            "first_seen": seen_on, "last_seen": seen_on}
            new += 1
        else:
            upd += 1
        for f in ("venue_name", "url", "cost", "end"):
            if e.get(f) and not cur.get(f):
                cur[f] = e[f]
        for s in (e.get("sources") or [e.get("source")]):
            if s and s not in cur["sources"]:
                cur["sources"].append(s)
        if day and day not in cur["dates"]:
            cur["dates"] = sorted(cur["dates"] + [day])[-DATES_MAX:]
        cur["first_seen"] = min(cur["first_seen"], seen_on)
        cur["last_seen"] = max(cur["last_seen"], seen_on)
    return new, upd


def save(doc, path=OUT):
    doc["_note"] = ("Every event the harvest has seen, kept after its day. Written by "
                    "importers/event_ledger.py; read by build.py, which matches each venue "
                    "string to a place at build time.")
    doc["generated"] = date.today().isoformat()
    doc["count"] = len(doc["events"])
    doc["events"] = dict(sorted(doc["events"].items()))
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=0, separators=(",", ":"))
        f.write("\n")
    os.replace(tmp, path)


def _committed_snapshots():
    """(commit date, events[]) for each committed version of data/events.json."""
    try:
        log = subprocess.run(["git", "log", "--format=%h %ad", "--date=short", "--",
                              "data/events.json"], cwd=ROOT, capture_output=True,
                             text=True, check=True).stdout.split("\n")
    except (OSError, subprocess.CalledProcessError):
        return []
    out = []
    for line in log:
        if not line.strip():
            continue
        sha, day = line.split()
        try:
            raw = subprocess.run(["git", "show", f"{sha}:data/events.json"], cwd=ROOT,
                                 capture_output=True, text=True, check=True).stdout
            d = json.loads(raw)
        except (OSError, subprocess.CalledProcessError, ValueError):
            continue
        out.append((day, d.get("events", d) if isinstance(d, dict) else d))
    return out


def _issues():
    """(issue date, events[]) for each newsletter issue on disk."""
    import read_newsletter
    out = []
    if not os.path.isdir(NEWSLETTERS):
        return out
    for f in sorted(os.listdir(NEWSLETTERS)):
        if re.match(r"^\d{4}-\d{2}-\d{2}\.txt$", f):
            try:
                evs, _leads, _st = read_newsletter.read_issue(os.path.join(NEWSLETTERS, f))
            except Exception as ex:      # noqa: BLE001 — one bad issue never stops the rest
                print(f"  issue {f}: {type(ex).__name__}: {ex}")
                continue
            out.append((f[:10], evs))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--backfill", action="store_true")
    a = ap.parse_args(argv)
    doc = load()
    before = len(doc["events"])
    if a.backfill:
        for day, evs in _committed_snapshots():
            n, _ = fold(doc, evs, day)
            print(f"  events.json @ {day}: {len(evs)} events, {n} new")
        for day, evs in _issues():
            n, _ = fold(doc, evs, day)
            print(f"  newsletter {day}: {len(evs)} events, {n} new")
    try:
        with open(EVENTS, encoding="utf-8") as f:
            cur = json.load(f)
        evs = cur.get("events", []) if isinstance(cur, dict) else cur
        day = (cur.get("generated") or date.today().isoformat())[:10] if isinstance(cur, dict) else date.today().isoformat()
        n, u = fold(doc, evs, day)
        print(f"  events.json now: {len(evs)} events, {n} new, {u} seen again")
    except (OSError, ValueError) as ex:
        print(f"  events.json unreadable ({ex}); ledger kept as it was")
    save(doc)
    print(f"event ledger: {before} -> {len(doc['events'])} entries · {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
