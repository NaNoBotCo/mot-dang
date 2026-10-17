#!/usr/bin/env python3
"""Steve's weekly events email, taken from its public copy.

tiny.cc/stevesemail points at a Google Doc that he overwrites with each issue.
Its plain-text export is the same text the email carries, so the issue no longer
waits for someone to paste it. The morning walk runs this before
harvest_events.py; on most days the doc has not changed and nothing is written.

When the text differs from the newest issue on disk it is saved as
_incoming/newsletter/<today>.txt, one listing per paragraph (the export puts
no blank line between listings, and read_newsletter splits on blank lines). The
newest issue's pins are copied beside it: a venue sends the same release week
after week, so last week's hand-checked corrections still apply. Then the issue
is parsed once; one that yields too few events is renamed .rejected.txt and the
previous issue stands.

    python3 importers/fetch_newsletter.py           # fetch, save if new
    python3 importers/fetch_newsletter.py --dry     # fetch, print, save nothing

Exit 0 = nothing new or a new issue saved; 1 = fetch failed or issue rejected.
"""
import os
import shutil
import sys
import urllib.request
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import read_newsletter as rn

DOC = "15MtcTuLt7biryCT5kFQ0bg4wseXBZ8CIPplIXza8JuA"   # where tiny.cc/stevesemail redirects
EXPORT = "https://docs.google.com/document/d/%s/export?format=txt" % DOC

# The 2026-10-12 issue parsed to 392 events (129 dated). A doc half-written or
# replaced by a holiday notice falls far below both.
MIN_EVENTS, MIN_DATED = 120, 25


def normalise(raw):
    text = raw.lstrip("﻿").replace("\r", "")
    lines = [l.rstrip() for l in text.split("\n") if l.strip()]
    return "\n\n".join(lines) + "\n"


def fetch():
    req = urllib.request.Request(EXPORT, headers={"User-Agent": "motdang.net events (fetch_newsletter.py)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def save_issue(text, dry=False):
    """Save text as today's issue if it differs from the newest one. 0 = saved or
    unchanged, 1 = rejected. Shared with pull_events_mail.py."""
    text = normalise(text)
    last = rn.latest_issue(rn.INCOMING)
    if last and open(last, encoding="utf-8").read() == text:
        print("newsletter: unchanged since %s" % os.path.basename(last))
        return 0
    key = date.today().isoformat()
    path = os.path.join(rn.INCOMING, key + ".txt")
    if dry:
        print("newsletter: new text, %d chars; would save %s" % (len(text), path))
        return 0
    if os.path.exists(path):
        print("newsletter: %s already on disk and differs; left as it is" % os.path.basename(path))
        return 0

    os.makedirs(rn.INCOMING, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    if last:
        prev_pins = last[:-4] + ".pins.json"
        new_pins = path[:-4] + ".pins.json"
        if os.path.exists(prev_pins) and not os.path.exists(new_pins):
            shutil.copy(prev_pins, new_pins)

    try:
        _evs, _leads, st = rn.read_issue(path)
        ok = st["events"] >= MIN_EVENTS and st["events_dated"] >= MIN_DATED
        why = "%d events, %d dated" % (st["events"], st["events_dated"])
    except Exception as ex:
        ok, why = False, "%s: %s" % (type(ex).__name__, ex)
    if not ok:
        os.rename(path, path[:-4] + ".rejected.txt")
        pins = path[:-4] + ".pins.json"
        if os.path.exists(pins):
            os.remove(pins)
        print("newsletter: %s rejected (%s); the last issue stands" % (key, why))
        return 1
    print("newsletter: saved %s (%s)" % (os.path.basename(path), why))
    return 0


def main():
    try:
        text = fetch()
    except Exception as ex:
        print("newsletter: fetch failed (%s: %s); the last issue stands" % (type(ex).__name__, ex))
        return 1
    return save_issue(text, dry="--dry" in sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
